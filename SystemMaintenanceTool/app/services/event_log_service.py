"""Windows Event Log reading service.

Reads real events from System, Application, Security logs via WMI / PowerShell.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EventEntry:
    """A single event log entry."""
    time: str = ""
    level: str = ""
    event_id: int = 0
    provider: str = ""
    message: str = ""


def collect_events(
    log_name: str = "System",
    level: str | None = None,
    max_events: int = 200,
) -> list[EventEntry]:
    """Read events from a Windows event log."""
    ps_filter = ""
    if level:
        level_map = {
            "critical": "1", "error": "2", "warning": "3", "information": "4"
        }
        ps_level = level_map.get(level.lower(), "")
        if ps_level:
            ps_filter = f" | Where-Object {{$_.Level -eq {ps_level}}}"

    ps_cmd = (
        f'Get-WinEvent -LogName "{log_name}" -MaxEvents {max_events}{ps_filter} '
        f'| Select-Object TimeCreated, LevelDisplayName, Id, ProviderName, Message '
        f'| ConvertTo-Json -Compress'
    )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace"
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        import json
        events = json.loads(result.stdout)
        if isinstance(events, dict):
            events = [events]

        entries: list[EventEntry] = []
        for e in events:
            time_val = e.get("TimeCreated", "")
            if isinstance(time_val, str):
                try:
                    dt = datetime.fromisoformat(time_val.replace("Z", "+00:00"))
                    time_val = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

            level_ar = {
                "Critical": "حرج", "Error": "خطأ",
                "Warning": "تحذير", "Information": "معلومات"
            }.get(e.get("LevelDisplayName", ""), e.get("LevelDisplayName", ""))

            entries.append(EventEntry(
                time=time_val,
                level=level_ar,
                event_id=e.get("Id", 0),
                provider=e.get("ProviderName", ""),
                message=(e.get("Message") or "")[:500],
            ))

        return entries

    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []
