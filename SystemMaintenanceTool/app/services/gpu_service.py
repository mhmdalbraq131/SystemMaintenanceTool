"""GPU data collection service – best effort.

Tries WMI and gpuinfo. If nothing works, marks everything as N/A.
Never invents GPU metrics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GPUData:
    """Snapshot of GPU metrics."""
    name: str = "غير متاح"
    utilization_percent: float | None = None
    vram_total_mb: float | None = None
    vram_used_mb: float | None = None
    vram_free_mb: float | None = None
    temperature: float | None = None
    freq_core_mhz: float | None = None
    available: bool = False


def collect_gpu_data() -> GPUData:
    """Gather GPU metrics if available."""
    data = GPUData()

    # Try gpuinfo first
    try:
        import gpuinfo  # type: ignore
        info = gpuinfo.get_gpu_info()
        if info:
            data.available = True
            data.name = info.get("name", "غير معروف")
            data.utilization_percent = info.get("utilization")
            data.temperature = info.get("temperature")
            data.vram_total_mb = info.get("vram_total")
            data.vram_used_mb = info.get("vram_used")
            data.vram_free_mb = info.get("vram_free")
            data.freq_core_mhz = info.get("core_clock")
            return data
    except (ImportError, Exception):
        pass

    # Try WMI
    try:
        import wmi  # type: ignore
        w = wmi.WMI()
        for gpu in w.Win32_VideoController():
            data.available = True
            data.name = gpu.Name or "غير معروف"
            data.vram_total_mb = round(float(gpu.AdapterRAM) / (1024 ** 2)) if gpu.AdapterRAM else None
            return data
    except (ImportError, Exception):
        pass

    return data
