"""Process management service – real Task Manager replacement.

Reads live data from psutil. Supports kill, tree-kill, priority change.
"""

from __future__ import annotations

import os
import signal
from dataclasses import dataclass, field
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


@dataclass
class ProcessInfo:
    """Snapshot of a single process."""
    pid: int = 0
    name: str = ""
    username: str = ""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    disk_read_bytes: float = 0.0
    disk_write_bytes: float = 0.0
    net_sent: float | None = None
    net_recv: float | None = None
    threads: int = 0
    status: str = ""
    exe_path: str = ""
    create_time: float = 0.0
    cmdline: str = ""


def collect_processes() -> list[ProcessInfo]:
    """Gather info for all accessible processes."""
    if psutil is None:
        return []

    procs: list[ProcessInfo] = []
    attrs = ["pid", "name", "username", "cpu_percent", "memory_info",
             "memory_percent", "io_counters", "num_threads", "status",
             "exe", "create_time", "cmdline"]

    for p in psutil.process_iter(attrs):
        try:
            info = ProcessInfo(pid=p.pid)
            info.name = p.info.get("name", "") or ""
            info.username = p.info.get("username", "") or ""
            info.cpu_percent = p.info.get("cpu_percent", 0.0) or 0.0
            mem = p.info.get("memory_info")
            if mem:
                info.memory_mb = round(mem.rss / (1024 ** 2), 2)
            info.memory_percent = round(p.info.get("memory_percent", 0.0) or 0.0, 2)
            io = p.info.get("io_counters")
            if io:
                info.disk_read_bytes = io.read_bytes
                info.disk_write_bytes = io.write_bytes
            info.threads = p.info.get("num_threads", 0) or 0
            info.status = p.info.get("status", "") or ""
            info.exe_path = p.info.get("exe", "") or ""
            info.create_time = p.info.get("create_time", 0.0) or 0.0
            cmd = p.info.get("cmdline")
            info.cmdline = " ".join(cmd) if cmd else ""
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return procs


def kill_process(pid: int) -> tuple[bool, str]:
    """Kill a process by PID. Returns (success, message)."""
    try:
        p = psutil.Process(pid)
        p.terminate()
        return True, f"تم إنهاء العملية {p.name()} (PID: {pid})"
    except psutil.NoSuchProcess:
        return False, f"العملية {pid} غير موجودة"
    except psutil.AccessDenied:
        return False, f"تم رفض الوصول لإنهاء العملية {pid}"
    except Exception as e:
        return False, f"خطأ: {e}"


def kill_process_tree(pid: int) -> tuple[bool, str]:
    """Kill a process and all its children."""
    try:
        p = psutil.Process(pid)
        children = p.children(recursive=True)
        terminated = []
        for child in children:
            try:
                child.terminate()
                terminated.append(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        p.terminate()
        terminated.append(pid)
        return True, f"تم إنهاء شجرة العملية (PIDs: {terminated})"
    except psutil.NoSuchProcess:
        return False, f"العملية {pid} غير موجودة"
    except psutil.AccessDenied:
        return False, f"تم رفض الوصول لإنهاء شجرة العملية {pid}"
    except Exception as e:
        return False, f"خطأ: {e}"


def set_priority(pid: int, priority: str) -> tuple[bool, str]:
    """Set process priority. Returns (success, message)."""
    priority_map = {
        "realtime": psutil.REALTIME_PRIORITY_CLASS if hasattr(psutil, "REALTIME_PRIORITY_CLASS") else 256,
        "high": psutil.HIGH_PRIORITY_CLASS if hasattr(psutil, "HIGH_PRIORITY_CLASS") else 128,
        "above_normal": psutil.ABOVE_NORMAL_PRIORITY_CLASS if hasattr(psutil, "ABOVE_NORMAL_PRIORITY_CLASS") else 32768,
        "normal": psutil.NORMAL_PRIORITY_CLASS if hasattr(psutil, "NORMAL_PRIORITY_CLASS") else 32,
        "below_normal": psutil.BELOW_NORMAL_PRIORITY_CLASS if hasattr(psutil, "BELOW_NORMAL_PRIORITY_CLASS") else 16384,
        "low": psutil.IDLE_PRIORITY_CLASS if hasattr(psutil, "IDLE_PRIORITY_CLASS") else 64,
    }
    try:
        p = psutil.Process(pid)
        p.nice(priority_map.get(priority, 32))
        return True, f"تم تغيير أولوية {p.name()} إلى {priority}"
    except psutil.NoSuchProcess:
        return False, f"العملية {pid} غير موجودة"
    except psutil.AccessDenied:
        return False, f"تم رفض الوصول – يتطلب صلاحيات مسؤول"
    except Exception as e:
        return False, f"خطأ: {e}"


def get_process_details(pid: int) -> dict:
    """Return detailed info about a process."""
    try:
        p = psutil.Process(pid)
        with p.oneshot():
            return {
                "pid": p.pid,
                "name": p.name(),
                "exe": p.exe(),
                "cmdline": " ".join(p.cmdline()),
                "status": p.status(),
                "username": p.username(),
                "cpu_percent": p.cpu_percent(),
                "memory_mb": round(p.memory_info().rss / (1024 ** 2), 2),
                "memory_percent": round(p.memory_percent(), 2),
                "threads": p.num_threads(),
                "create_time": p.create_time(),
                "connections": len(p.connections()),
                "open_files": len(p.open_files()),
                "cwd": p.cwd(),
            }
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        return {"error": str(e)}
