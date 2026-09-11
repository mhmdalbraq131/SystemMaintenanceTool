"""Windows maintenance and repair commands.

SFC, DISM, CHKDSK – real commands, real output, real exit codes.
Never runs destructive operations without explicit consent.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass


@dataclass
class OperationResult:
    """Result of a maintenance operation."""
    operation: str = ""
    command: str = ""
    started_at: str = ""
    elapsed_seconds: float = 0.0
    exit_code: int = -1
    status: str = "لم يبدأ"
    output: str = ""
    success: bool = False


def run_sfc_scannow() -> OperationResult:
    """Run SFC /SCANNOW – requires admin."""
    return _run_system_command(
        operation="SFC /SCANNOW",
        command=["sfc", "/scannow"],
        timeout=600,
    )


def run_dism_check_health() -> OperationResult:
    """Run DISM /CheckHealth."""
    return _run_system_command(
        operation="DISM CheckHealth",
        command=["dism", "/online", "/cleanup-image", "/checkhealth"],
        timeout=120,
    )


def run_dism_scan_health() -> OperationResult:
    """Run DISM /ScanHealth."""
    return _run_system_command(
        operation="DISM ScanHealth",
        command=["dism", "/online", "/cleanup-image", "/scanhealth"],
        timeout=600,
    )


def run_dism_restore_health() -> OperationResult:
    """Run DISM /RestoreHealth – may take very long."""
    return _run_system_command(
        operation="DISM RestoreHealth",
        command=["dism", "/online", "/cleanup-image", "/restorehealth"],
        timeout=3600,
    )


def run_chkdsk_readonly(drive: str = "C:") -> OperationResult:
    """Run CHKDSK in read-only mode."""
    return _run_system_command(
        operation=f"CHKDSK {drive} (قراءة فقط)",
        command=["chkdsk", drive],
        timeout=600,
    )


def run_chkdsk_repair(drive: str = "C:") -> OperationResult:
    """Run CHKDSK /F – requires admin, may require reboot."""
    return _run_system_command(
        operation=f"CHKDSK {drive} /F (إصلاح)",
        command=["chkdsk", drive, "/f"],
        timeout=600,
        warning="⚠️ هذا الإجراء قد يتطلب إعادة تشغيل الجهاز",
    )


def _run_system_command(
    operation: str,
    command: list[str],
    timeout: int = 600,
    warning: str = "",
) -> OperationResult:
    """Execute a system maintenance command and capture full output."""
    result = OperationResult(
        operation=operation,
        command=" ".join(command),
    )

    start = time.time()
    from datetime import datetime
    result.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if warning:
        result.output = warning + "\n\n"

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="cp1256",
            errors="replace",
        )
        result.exit_code = proc.returncode
        result.output += proc.stdout
        if proc.stderr:
            result.output += "\n" + proc.stderr
        result.status = "مكتمل" if proc.returncode == 0 else "فشل"
        result.success = proc.returncode == 0
    except subprocess.TimeoutExpired:
        result.status = "انتهت المهلة"
        result.output += f"\nانتهت المهلة الزمنية ({timeout}s)"
        result.success = False
    except FileNotFoundError:
        result.status = "الأمر غير متاح"
        result.output += f"\nالأمر غير موجود: {command[0]}"
        result.success = False
    except Exception as e:
        result.status = "خطأ"
        result.output += f"\nخطأ: {e}"
        result.success = False

    result.elapsed_seconds = round(time.time() - start, 2)
    return result
