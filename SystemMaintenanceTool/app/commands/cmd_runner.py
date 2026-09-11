"""Command execution engine for CMD Center.

Supports both CMD and PowerShell execution with real output capture.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from datetime import datetime

from config.settings import CMD_MAX_OUTPUT_CHARS


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str = ""
    shell: str = "cmd"
    started_at: str = ""
    elapsed_seconds: float = 0.0
    exit_code: int = -1
    output: str = ""
    success: bool = False


def execute_command(
    command: str,
    shell: str = "cmd",
    timeout: int = 60,
    working_dir: str | None = None,
) -> CommandResult:
    """Execute a command in CMD or PowerShell and return the result."""
    result = CommandResult(command=command, shell=shell)
    result.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    start = time.time()

    try:
        if shell == "powershell":
            cmd_args = ["powershell", "-NoProfile", "-Command", command]
        else:
            cmd_args = ["cmd", "/c", command]

        proc = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="cp1256",
            errors="replace",
            cwd=working_dir,
        )

        result.exit_code = proc.returncode
        result.output = (proc.stdout + proc.stderr)[:CMD_MAX_OUTPUT_CHARS]
        result.success = proc.returncode == 0

    except subprocess.TimeoutExpired:
        result.output = f"انتهت المهلة الزمنية ({timeout}s)"
        result.success = False
    except FileNotFoundError:
        result.output = f"المترجم غير متاح: {shell}"
        result.success = False
    except Exception as e:
        result.output = f"خطأ: {e}"
        result.success = False

    result.elapsed_seconds = round(time.time() - start, 2)
    return result
