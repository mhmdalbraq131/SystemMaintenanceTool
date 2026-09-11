"""System-level information collection.

Uptime, process count, hostname, OS version, battery, etc.
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from datetime import timedelta

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


@dataclass
class SystemData:
    """General system snapshot."""
    uptime: str = ""
    process_count: int = 0
    hostname: str = ""
    username: str = ""
    os_name: str = ""
    os_version: str = ""
    os_build: str = ""
    os_arch: str = ""
    battery_percent: int | None = None
    battery_plugged: bool | None = None
    is_admin: bool = False


def collect_system_data() -> SystemData:
    """Gather system-level metrics from the live system."""
    if psutil is None:
        return SystemData()

    data = SystemData()

    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = psutil.time.time() - boot_time if hasattr(psutil, "time") else 0
    try:
        import time
        uptime_seconds = time.time() - boot_time
    except Exception:
        pass
    data.uptime = str(timedelta(seconds=int(uptime_seconds)))

    # Process count
    data.process_count = len(psutil.pids())

    # Host & user
    data.hostname = platform.node()
    data.username = psutil.users()[0].name if psutil.users() else "غير معروف"

    # OS info
    data.os_name = platform.system()
    data.os_version = platform.version()
    data.os_build = platform.build if hasattr(platform, "build") else ""
    data.os_arch = platform.machine()

    # Windows specific
    try:
        out = subprocess.run(
            ["cmd", "/c", "ver"],
            capture_output=True, text=True, timeout=5, encoding="cp1256", errors="replace"
        ).stdout
        if "Windows" in out:
            parts = out.strip().replace("\n", " ").split()
            for p in parts:
                if p.startswith("10.") or p.startswith("11."):
                    data.os_build = p
    except Exception:
        pass

    # Battery
    if hasattr(psutil, "sensors_battery"):
        try:
            bat = psutil.sensors_battery()
            if bat:
                data.battery_percent = int(bat.percent)
                data.battery_plugged = bat.power_plugged
        except Exception:
            pass

    # Admin check
    try:
        import ctypes  # type: ignore
        data.is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        data.is_admin = False

    return data
