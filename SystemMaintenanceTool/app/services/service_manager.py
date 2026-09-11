"""Windows Services management service.

Reads and controls Windows services via psutil / pywin32.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


@dataclass
class ServiceInfo:
    """Info about a Windows service."""
    name: str = ""
    display_name: str = ""
    description: str = ""
    status: str = ""
    start_type: str = ""
    pid: int | None = None
    account: str = ""


def collect_services() -> list[ServiceInfo]:
    """List all Windows services via psutil."""
    if psutil is None:
        return []

    services: list[ServiceInfo] = []
    try:
        for svc in psutil.win_service_iter():
            try:
                info = svc.info()
                s = ServiceInfo(
                    name=info.get("name", ""),
                    display_name=info.get("display_name", ""),
                    description=info.get("description", "") or "",
                    status=info.get("status", ""),
                    start_type=info.get("start_type", ""),
                    pid=info.get("pid"),
                    account=info.get("username", ""),
                )
                services.append(s)
            except Exception:
                continue
    except Exception:
        pass

    return services


# ── Service Control ────────────────────────────────────────────────────────

def start_service(name: str) -> tuple[bool, str]:
    """Start a Windows service."""
    return _sc_cmd("start", name)


def stop_service(name: str) -> tuple[bool, str]:
    """Stop a Windows service."""
    return _sc_cmd("stop", name)


def restart_service(name: str) -> tuple[bool, str]:
    """Restart a Windows service."""
    ok1, msg1 = stop_service(name)
    if not ok1:
        return ok1, msg1
    ok2, msg2 = start_service(name)
    return ok2, f"إعادة تشغيل: {msg2}" if ok2 else f"فشل بعد الإيقاف: {msg2}"


def set_service_start_type(name: str, start_type: str) -> tuple[bool, str]:
    """Set service startup type (auto/manual/disabled)."""
    type_map = {"auto": "auto", "manual": "demand", "disabled": "disabled"}
    sc_type = type_map.get(start_type, "demand")
    return _sc_cmd("config", name, f"start={sc_type}")


def _sc_cmd(action: str, name: str, extra: str = "") -> tuple[bool, str]:
    """Execute an sc command."""
    cmd = ["sc", action, name]
    if extra:
        cmd.append(extra)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            encoding="cp1256", errors="replace"
        )
        success = result.returncode == 0
        msg = result.stdout.strip() if success else result.stderr.strip()
        return success, msg or ("تم بنجاح" if success else "فشل الأمر")
    except subprocess.TimeoutExpired:
        return False, "انتهت المهلة الزمنية"
    except FileNotFoundError:
        return False, "أمر sc غير متاح"
    except Exception as e:
        return False, f"خطأ: {e}"
