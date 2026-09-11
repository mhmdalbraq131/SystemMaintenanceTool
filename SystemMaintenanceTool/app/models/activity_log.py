"""Global Activity Log model.

Records every user-initiated operation with timestamp, action, result, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ActivityEntry:
    """A single activity log entry."""
    timestamp: str = ""
    user: str = ""
    action: str = ""
    command: str = ""
    result: str = ""
    exit_code: int | None = None
    duration_seconds: float | None = None
    status: str = ""  # completed / failed / cancelled


# In-memory activity log (also persisted to operations.log)
_activity_log: list[ActivityEntry] = []
MAX_ACTIVITY_LOG = 500


def add_entry(
    action: str,
    command: str = "",
    result: str = "",
    exit_code: int | None = None,
    duration_seconds: float | None = None,
    status: str = "completed",
) -> ActivityEntry:
    """Add an entry to the activity log."""
    entry = ActivityEntry(
        timestamp=datetime.now().strftime("%H:%M:%S"),
        user=_get_current_user(),
        action=action,
        command=command,
        result=result,
        exit_code=exit_code,
        duration_seconds=duration_seconds,
        status=status,
    )
    _activity_log.append(entry)
    if len(_activity_log) > MAX_ACTIVITY_LOG:
        _activity_log.pop(0)
    return entry


def get_all_entries() -> list[ActivityEntry]:
    """Return all activity log entries."""
    return list(_activity_log)


def clear_log() -> None:
    """Clear the activity log."""
    _activity_log.clear()


def _get_current_user() -> str:
    """Get current OS user."""
    try:
        import os
        return os.getlogin()
    except Exception:
        return "غير معروف"
