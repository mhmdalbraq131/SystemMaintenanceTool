"""Real-time RAM / memory data collection service.

Uses psutil. Returns structured data; None when unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


@dataclass
class RAMData:
    """Snapshot of memory metrics."""
    total_gb: float = 0.0
    used_gb: float = 0.0
    available_gb: float = 0.0
    usage_percent: float = 0.0
    cached_gb: float | None = None
    swap_total_gb: float | None = None
    swap_used_gb: float | None = None
    swap_percent: float | None = None
    page_file_gb: float | None = None


def collect_ram_data() -> RAMData:
    """Gather RAM metrics from the live system."""
    if psutil is None:
        return RAMData()

    mem = psutil.virtual_memory()
    data = RAMData()

    data.total_gb = round(mem.total / (1024 ** 3), 2)
    data.used_gb = round(mem.used / (1024 ** 3), 2)
    data.available_gb = round(mem.available / (1024 ** 3), 2)
    data.usage_percent = mem.percent

    # On Windows, "cached" may be available in some psutil builds
    if hasattr(mem, "cached"):
        data.cached_gb = round(mem.cached / (1024 ** 3), 2) if mem.cached else None

    # Swap / page file
    swap = psutil.swap_memory()
    data.swap_total_gb = round(swap.total / (1024 ** 3), 2)
    data.swap_used_gb = round(swap.used / (1024 ** 3), 2)
    data.swap_percent = swap.percent

    # Page file (best-effort via WMI)
    data.page_file_gb = _get_page_file_size()

    return data


def _get_page_file_size() -> float | None:
    """Read current page-file usage via WMI."""
    try:
        import wmi  # type: ignore
        w = wmi.WMI()
        for pf in w.query("SELECT * FROM Win32_PageFileUsage"):
            return round(float(pf.AllocatedBaseSize), 2) if pf.AllocatedBaseSize else None
    except Exception:
        return None
