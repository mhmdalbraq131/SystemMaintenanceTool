"""Startup programs management service.

Reads startup entries from registry and startup folders.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StartupEntry:
    """A single startup program entry."""
    name: str = ""
    command: str = ""
    location: str = ""
    source: str = ""  # Registry / Folder
    enabled: bool = True


def collect_startup_entries() -> list[StartupEntry]:
    """Gather startup programs from registry and startup folders."""
    entries: list[StartupEntry] = []
    entries.extend(_read_registry_startup(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", True))
    entries.extend(_read_registry_startup(r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", False))
    entries.extend(_read_registry_startup(r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", True))
    entries.extend(_read_startup_folder())
    return entries


def enable_startup_entry(entry: StartupEntry) -> tuple[bool, str]:
    """Re-enable a disabled startup entry."""
    if entry.source == "Registry":
        return _restore_registry_entry(entry)
    elif entry.source == "Folder":
        return _restore_folder_entry(entry)
    return False, "مصدر غير معروف"


def disable_startup_entry(entry: StartupEntry) -> tuple[bool, str]:
    """Disable a startup entry."""
    if entry.source == "Registry":
        return _disable_registry_entry(entry)
    elif entry.source == "Folder":
        return _disable_folder_entry(entry)
    return False, "مصدر غير معروف"


def _read_registry_startup(key_path: str, hklm: bool) -> list[StartupEntry]:
    """Read startup entries from a registry key."""
    entries: list[StartupEntry] = []
    hive = "HKLM" if hklm else "HKCU"
    full_key = f"{hive}\\{key_path}"
    try:
        result = subprocess.run(
            ["reg", "query", full_key],
            capture_output=True, text=True, timeout=10,
            encoding="cp1256", errors="replace"
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "REG_SZ" in line or "REG_EXPAND_SZ" in line:
                    parts = line.split("REG_SZ") if "REG_SZ" in line else line.split("REG_EXPAND_SZ")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        command = parts[1].strip()
                        entries.append(StartupEntry(
                            name=name,
                            command=command,
                            location=full_key,
                            source="Registry",
                            enabled=True,
                        ))
    except Exception:
        pass

    # Also check disabled entries
    disabled_key = full_key.replace("\\Run", "\\Run-")
    try:
        result = subprocess.run(
            ["reg", "query", disabled_key],
            capture_output=True, text=True, timeout=10,
            encoding="cp1256", errors="replace"
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "REG_SZ" in line or "REG_EXPAND_SZ" in line:
                    parts = line.split("REG_SZ") if "REG_SZ" in line else line.split("REG_EXPAND_SZ")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        command = parts[1].strip()
                        entries.append(StartupEntry(
                            name=name,
                            command=command,
                            location=disabled_key,
                            source="Registry",
                            enabled=False,
                        ))
    except Exception:
        pass

    return entries


def _read_startup_folder() -> list[StartupEntry]:
    """Read startup entries from the startup folder."""
    entries: list[StartupEntry] = []
    startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    if startup_dir.exists():
        for item in startup_dir.iterdir():
            if item.is_file() and item.suffix.lower() in {".lnk", ".url", ".exe", ".bat", ".cmd", ".vbs"}:
                entries.append(StartupEntry(
                    name=item.stem,
                    command=str(item),
                    location=str(startup_dir),
                    source="Folder",
                    enabled=True,
                ))
    return entries


def _disable_registry_entry(entry: StartupEntry) -> tuple[bool, str]:
    """Move a registry entry from Run to Run-."""
    disabled_key = entry.location.replace("\\Run", "\\Run-")
    try:
        # Add to disabled key
        subprocess.run(
            ["reg", "add", disabled_key, "/v", entry.name, "/d", entry.command, "/f"],
            capture_output=True, text=True, timeout=10
        )
        # Remove from enabled key
        subprocess.run(
            ["reg", "delete", entry.location, "/v", entry.name, "/f"],
            capture_output=True, text=True, timeout=10
        )
        return True, f"تم تعطيل {entry.name}"
    except Exception as e:
        return False, f"خطأ: {e}"


def _restore_registry_entry(entry: StartupEntry) -> tuple[bool, str]:
    """Move a registry entry from Run- back to Run."""
    enabled_key = entry.location.replace("\\Run-", "\\Run")
    try:
        subprocess.run(
            ["reg", "add", enabled_key, "/v", entry.name, "/d", entry.command, "/f"],
            capture_output=True, text=True, timeout=10
        )
        subprocess.run(
            ["reg", "delete", entry.location, "/v", entry.name, "/f"],
            capture_output=True, text=True, timeout=10
        )
        return True, f"تم تفعيل {entry.name}"
    except Exception as e:
        return False, f"خطأ: {e}"


def _disable_folder_entry(entry: StartupEntry) -> tuple[bool, str]:
    """Disable a folder-based startup entry."""
    try:
        old_path = Path(entry.command)
        new_path = old_path.with_name(old_path.stem + ".disabled")
        old_path.rename(new_path)
        return True, f"تم تعطيل {entry.name}"
    except Exception as e:
        return False, f"خطأ: {e}"


def _restore_folder_entry(entry: StartupEntry) -> tuple[bool, str]:
    """Re-enable a folder-based startup entry."""
    try:
        old_path = Path(entry.command)
        new_path = old_path.with_name(old_path.stem.replace(".disabled", "") + old_path.suffix)
        old_path.rename(new_path)
        return True, f"تم تفعيل {entry.name}"
    except Exception as e:
        return False, f"خطأ: {e}"
