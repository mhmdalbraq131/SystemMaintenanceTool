"""Notification system for system alerts.

Monitors thresholds and generates alerts.
Never fabricates alerts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from config.settings import (
    CPU_ALERT_THRESHOLD,
    RAM_ALERT_THRESHOLD,
    DISK_ALERT_THRESHOLD,
    DISK_SPACE_WARNING_GB,
)

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


class NotificationLevel(str, Enum):
    INFO = "معلومات"
    WARNING = "تحذير"
    CRITICAL = "حرج"


@dataclass
class Notification:
    """A single notification."""
    timestamp: str = ""
    level: NotificationLevel = NotificationLevel.INFO
    title: str = ""
    message: str = ""
    dismissed: bool = False


# Notification store
_notifications: list[Notification] = []
MAX_NOTIFICATIONS = 100
_enabled_categories: dict[str, bool] = {
    "high_cpu": True,
    "high_ram": True,
    "low_disk": True,
    "disk_warning": True,
    "defender_disabled": True,
    "firewall_disabled": True,
    "network_disconnected": True,
    "service_failure": True,
    "repair_failure": True,
}


def check_alerts() -> list[Notification]:
    """Check current system status and generate new alerts if thresholds exceeded."""
    if psutil is None:
        return []

    new_alerts: list[Notification] = []
    ts = datetime.now().strftime("%H:%M:%S")

    # CPU
    if _enabled_categories.get("high_cpu", True):
        cpu_pct = psutil.cpu_percent(interval=0)
        if cpu_pct > CPU_ALERT_THRESHOLD:
            new_alerts.append(Notification(
                timestamp=ts,
                level=NotificationLevel.WARNING,
                title="استخدام المعالج مرتفع",
                message=f"الاستخدام الحالي: {cpu_pct:.1f}%",
            ))

    # RAM
    if _enabled_categories.get("high_ram", True):
        ram_pct = psutil.virtual_memory().percent
        if ram_pct > RAM_ALERT_THRESHOLD:
            new_alerts.append(Notification(
                timestamp=ts,
                level=NotificationLevel.WARNING,
                title="استخدام الذاكرة مرتفع",
                message=f"الاستخدام الحالي: {ram_pct:.1f}%",
            ))

    # Disk space
    if _enabled_categories.get("low_disk", True):
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                if usage.percent > DISK_ALERT_THRESHOLD:
                    new_alerts.append(Notification(
                        timestamp=ts,
                        level=NotificationLevel.CRITICAL,
                        title=f"القرص {part.mountpoint} ممتلئ تقريبًا",
                        message=f"الاستخدام: {usage.percent:.1f}% | الحرة: {usage.free / (1024**3):.1f} GB",
                    ))
                elif usage.free / (1024**3) < DISK_SPACE_WARNING_GB:
                    new_alerts.append(Notification(
                        timestamp=ts,
                        level=NotificationLevel.WARNING,
                        title=f"مساحة القرص {part.mountpoint} منخفضة",
                        message=f"المساحة الحرة: {usage.free / (1024**3):.1f} GB",
                    ))
            except Exception:
                continue

    for n in new_alerts:
        _notifications.append(n)

    # Trim
    while len(_notifications) > MAX_NOTIFICATIONS:
        _notifications.pop(0)

    return new_alerts


def get_notifications(include_dismissed: bool = False) -> list[Notification]:
    """Return all notifications."""
    if include_dismissed:
        return list(_notifications)
    return [n for n in _notifications if not n.dismissed]


def dismiss_all() -> None:
    """Dismiss all notifications."""
    for n in _notifications:
        n.dismissed = True


def set_category_enabled(category: str, enabled: bool) -> None:
    """Enable or disable a notification category."""
    _enabled_categories[category] = enabled


def get_categories() -> dict[str, bool]:
    return dict(_enabled_categories)
