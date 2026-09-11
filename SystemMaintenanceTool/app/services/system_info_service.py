"""Comprehensive system information collection.

Windows, Hardware, and Drivers info – all from real system sources.
"""

from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass, field


@dataclass
class WindowsInfo:
    edition: str = ""
    version: str = ""
    build: str = ""
    arch: str = ""
    install_date: str = ""
    hostname: str = ""
    username: str = ""


@dataclass
class HardwareInfo:
    cpu: str = ""
    ram_total_gb: float = 0.0
    gpu: list[str] = field(default_factory=list)
    motherboard: str = ""
    bios: str = ""
    disks: list[str] = field(default_factory=list)
    network_adapters: list[str] = field(default_factory=list)


@dataclass
class DriverInfo:
    device: str = ""
    provider: str = ""
    version: str = ""
    date: str = ""
    status: str = ""


@dataclass
class FullSystemInfo:
    windows: WindowsInfo = field(default_factory=WindowsInfo)
    hardware: HardwareInfo = field(default_factory=HardwareInfo)
    drivers: list[DriverInfo] = field(default_factory=list)


def collect_full_info() -> FullSystemInfo:
    """Gather all system information from the live system."""
    info = FullSystemInfo()
    info.windows = _collect_windows_info()
    info.hardware = _collect_hardware_info()
    info.drivers = _collect_driver_info()
    return info


def _collect_windows_info() -> WindowsInfo:
    """Read Windows details."""
    w = WindowsInfo()
    w.hostname = platform.node()
    w.arch = platform.machine()

    try:
        import psutil
        w.username = psutil.users()[0].name if psutil.users() else "غير معروف"
    except Exception:
        w.username = "غير معروف"

    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_OperatingSystem) | "
             "Select-Object Caption, Version, BuildNumber, InstallDate | ConvertTo-Json"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        ).stdout
        import json
        data = json.loads(out.strip()) if out.strip() else {}
        w.edition = data.get("Caption", "")
        w.version = data.get("Version", "")
        w.build = str(data.get("BuildNumber", ""))
        install = data.get("InstallDate", "")
        if isinstance(install, str) and install:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(install.replace("Z", "+00:00"))
                w.install_date = dt.strftime("%Y-%m-%d")
            except Exception:
                w.install_date = install[:10]
    except Exception:
        pass

    return w


def _collect_hardware_info() -> HardwareInfo:
    """Read hardware details via WMI."""
    h = HardwareInfo()

    # CPU
    h.cpu = platform.processor() or "غير معروف"

    # RAM
    try:
        import psutil
        h.ram_total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except Exception:
        pass

    # GPU
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_VideoController | Select-Object Name | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        ).stdout
        import json
        gpus = json.loads(out.strip()) if out.strip() else []
        if isinstance(gpus, dict):
            gpus = [gpus]
        h.gpu = [g.get("Name", "") for g in gpus if g.get("Name")]
    except Exception:
        pass

    # Motherboard
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        ).stdout
        import json
        mb = json.loads(out.strip()) if out.strip() else {}
        h.motherboard = f"{mb.get('Manufacturer', '')} {mb.get('Product', '')}".strip()
    except Exception:
        pass

    # BIOS
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_BIOS | Select-Object SMBIOSBIOSVersion, ReleaseDate | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        ).stdout
        import json
        bios = json.loads(out.strip()) if out.strip() else {}
        h.bios = bios.get("SMBIOSBIOSVersion", "") or ""
    except Exception:
        pass

    # Disk names
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_DiskDrive | Select-Object Model, Size | ConvertTo-Json"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace"
        ).stdout
        import json
        disks = json.loads(out.strip()) if out.strip() else []
        if isinstance(disks, dict):
            disks = [disks]
        for d in disks:
            model = d.get("Model", "")
            size_gb = round(int(d.get("Size", 0)) / (1024 ** 3), 1) if d.get("Size") else 0
            h.disks.append(f"{model} ({size_gb} GB)")
    except Exception:
        pass

    # Network adapters
    try:
        import psutil
        stats = psutil.net_if_stats()
        h.network_adapters = list(stats.keys())
    except Exception:
        pass

    return h


def _collect_driver_info() -> list[DriverInfo]:
    """Read driver information via PowerShell."""
    drivers: list[DriverInfo] = []
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-WmiObject Win32_PnPSignedDriver | "
             "Select-Object DeviceName, DriverProviderName, DriverVersion, DriverDate, Status | "
             "ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace"
        ).stdout
        import json
        data = json.loads(out.strip()) if out.strip() else []
        if isinstance(data, dict):
            data = [data]
        for d in data[:500]:  # limit for performance
            drv = DriverInfo(
                device=d.get("DeviceName", "") or "",
                provider=d.get("DriverProviderName", "") or "",
                version=d.get("DriverVersion", "") or "",
                date=(d.get("DriverDate", "") or "")[:10],
                status=d.get("Status", "") or "",
            )
            if drv.device:
                drivers.append(drv)
    except Exception:
        pass

    return drivers
