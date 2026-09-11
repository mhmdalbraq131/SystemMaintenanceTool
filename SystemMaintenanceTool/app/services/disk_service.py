"""Real-time disk / storage data collection service.

Uses psutil for I/O stats, shutil/psutil for partition info, and
Windows APIs / WMI for SSD/HDD identification and SMART.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


@dataclass
class PartitionInfo:
    """Info about a single partition/drive."""
    letter: str = ""
    volume_name: str = ""
    fs_type: str = ""
    total_gb: float = 0.0
    used_gb: float = 0.0
    free_gb: float = 0.0
    usage_percent: float = 0.0
    drive_type: str = ""  # SSD / HDD / NVMe / Removable / Unknown
    mount_point: str = ""


@dataclass
class DiskIOData:
    """Disk I/O counters."""
    read_bytes_sec: float = 0.0
    write_bytes_sec: float = 0.0
    read_count_sec: float = 0.0
    write_count_sec: float = 0.0
    active_time_percent: float | None = None


@dataclass
class DiskData:
    """Full disk data snapshot."""
    partitions: list[PartitionInfo] = field(default_factory=list)
    io: DiskIOData = field(default_factory=DiskIOData)
    smart_available: bool = False
    smart_data: dict | None = None


def collect_disk_data(prev_io: dict | None = None, interval: float = 1.0) -> DiskData:
    """Gather disk metrics from the live system.

    prev_io: previous psutil disk_io_counters() for rate calculation.
    interval: seconds between prev and current sample.
    """
    if psutil is None:
        return DiskData()

    data = DiskData()

    # Partitions
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            p = PartitionInfo(
                letter=part.mountpoint,
                volume_name=_get_volume_name(part.mountpoint),
                fs_type=part.fstype,
                total_gb=round(usage.total / (1024 ** 3), 2),
                used_gb=round(usage.used / (1024 ** 3), 2),
                free_gb=round(usage.free / (1024 ** 3), 2),
                usage_percent=usage.percent,
                mount_point=part.mountpoint,
                drive_type=_get_drive_type(part.mountpoint),
            )
            data.partitions.append(p)
        except (PermissionError, OSError):
            continue

    # I/O counters
    io = psutil.disk_io_counters(perdisk=False)
    if io and prev_io:
        data.io = DiskIOData(
            read_bytes_sec=round((io.read_bytes - prev_io.get("read_bytes", 0)) / interval, 2),
            write_bytes_sec=round((io.write_bytes - prev_io.get("write_bytes", 0)) / interval, 2),
            read_count_sec=round((io.read_count - prev_io.get("read_count", 0)) / interval, 2),
            write_count_sec=round((io.write_count - prev_io.get("write_count", 0)) / interval, 2),
        )

    # SMART availability check
    data.smart_available, data.smart_data = _check_smart()

    return data


def get_disk_io_counters() -> dict | None:
    """Return current cumulative disk I/O counters."""
    if psutil is None:
        return None
    io = psutil.disk_io_counters(perdisk=False)
    if io:
        return {"read_bytes": io.read_bytes, "write_bytes": io.write_bytes,
                "read_count": io.read_count, "write_count": io.write_count}
    return None


def _get_volume_name(mountpoint: str) -> str:
    """Try to read volume label."""
    try:
        import win32file  # type: ignore
        return win32file.GetVolumeNameForVolumeMountPoint(mountpoint) or ""
    except Exception:
        try:
            result = shutil.disk_usage(mountpoint)
            return ""
        except Exception:
            return ""


def _get_drive_type(mountpoint: str) -> str:
    """Determine SSD / HDD / NVMe / Removable via WMI."""
    try:
        import wmi  # type: ignore
        w = wmi.WMI()
        for disk in w.Win32_DiskDrive():
            media = getattr(disk, "MediaType", "") or ""
            if "SSD" in media.upper() or "NVME" in (getattr(disk, "Model", "") or "").upper():
                return "SSD"
            if "Fixed" in media or "Hard" in media:
                return "HDD"
            if "Removable" in media:
                return "Removable"
        return "غير معروف"
    except Exception:
        return "غير معروف"


def _check_smart() -> tuple[bool, dict | None]:
    """Check SMART availability via WMI.

    Returns (available, data_dict).
    Never invents SMART percentages.
    """
    try:
        import wmi  # type: ignore
        w = wmi.WMI(namespace=r"root\WMI")
        for item in w.MSStorageDriver_ATAPISmartData():
            return True, {"instance": item.InstanceName}
    except Exception:
        return False, None


# ── Disk Cleanup ─────────────────────────────────────────────────────────

cleanup_categories = {
    "temp_user": {
        "label": "ملفات المستخدم المؤقتة",
        "path": os.environ.get("TEMP", ""),
    },
    "temp_windows": {
        "label": "ملفات Windows المؤقتة",
        "path": os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Temp"),
    },
    "recycle_bin": {
        "label": "سلة المحذوفات",
        "path": "RECYCLE:BIN",  # special marker – handled via win32
    },
    "update_cache": {
        "label": "ذاكرة تحديثات Windows",
        "path": os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "SoftwareDistribution", "Download"),
    },
    "windows_logs": {
        "label": "سجلات Windows القديمة",
        "path": os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Logs"),
    },
    "dump_files": {
        "label": "ملفات Dump",
        "path": os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Minidump"),
    },
}


def calculate_cleanup_size() -> dict[str, int]:
    """Calculate size (bytes) for each cleanup category."""
    sizes: dict[str, int] = {}
    for key, info in cleanup_categories.items():
        p = info["path"]
        if key == "recycle_bin":
            sizes[key] = _get_recycle_bin_size()
            continue
        if not p:
            sizes[key] = 0
            continue
        path = Path(p)
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
        except (PermissionError, OSError):
            pass
        sizes[key] = total
    return sizes


def execute_cleanup(selected: list[str]) -> dict[str, bool]:
    """Delete files in selected categories. Returns per-key success."""
    results: dict[str, bool] = {}
    for key in selected:
        info = cleanup_categories.get(key)
        if not info:
            results[key] = False
            continue
        p = info["path"]
        if key == "recycle_bin":
            results[key] = _empty_recycle_bin()
            continue
        if not p:
            results[key] = False
            continue
        path = Path(p)
        try:
            for f in path.rglob("*"):
                if f.is_file():
                    try:
                        f.unlink()
                    except (PermissionError, OSError):
                        pass
            results[key] = True
        except Exception:
            results[key] = False
    return results


def _get_recycle_bin_size() -> int:
    """Get recycle bin size via win32."""
    try:
        import win32api  # type: ignore
        _, _, size = win32api.SHQueryRecycleBin()
        return size
    except Exception:
        return 0


def _empty_recycle_bin() -> bool:
    """Empty the recycle bin via win32."""
    try:
        import win32api  # type: ignore
        win32api.SHEmptyRecycleBin()
        return True
    except Exception:
        return False
