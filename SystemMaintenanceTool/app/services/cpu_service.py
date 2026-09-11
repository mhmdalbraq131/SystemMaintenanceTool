"""Real-time CPU data collection service.

Uses psutil as primary source. WMI / win32 API as fallback for temperature.
Never invents data – returns None / 'N/A' when unavailable.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass, field

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


@dataclass
class CPUData:
    """Snapshot of CPU metrics."""
    usage_percent: float = 0.0
    per_core_usage: list[float] = field(default_factory=list)
    physical_cores: int | None = None
    logical_cores: int | None = None
    freq_current: float | None = None
    freq_min: float | None = None
    freq_max: float | None = None
    temperature: float | None = None  # Celsius – may be None
    cpu_name: str = ""
    arch: str = ""


def collect_cpu_data() -> CPUData:
    """Gather CPU metrics from the live system."""
    if psutil is None:
        return CPUData(cpu_name="psutil غير متاح")

    data = CPUData()

    # Core counts
    data.physical_cores = psutil.cpu_count(logical=False)
    data.logical_cores = psutil.cpu_count(logical=True)

    # Overall usage
    data.usage_percent = psutil.cpu_percent(interval=0)

    # Per-core usage
    data.per_core_usage = psutil.cpu_percent(interval=0, percpu=True)

    # Frequency
    freq = psutil.cpu_freq()
    if freq:
        data.freq_current = freq.current
        data.freq_min = freq.min
        data.freq_max = freq.max

    # Temperature (best-effort via WMI / psutil.sensors on Linux)
    data.temperature = _get_cpu_temperature()

    # CPU name & arch
    data.cpu_name = platform.processor() or "غير معروف"
    data.arch = platform.machine()

    return data


def _get_cpu_temperature() -> float | None:
    """Attempt to read CPU temperature.

    Returns None if not available – never invents a value.
    """
    try:
        import wmi  # type: ignore
        w = wmi.WMI(namespace=r"root\OpenHardwareMonitor")
        for sensor in w.Sensor():
            if sensor.SensorType == "Temperature" and "CPU" in (sensor.Name or ""):
                return float(sensor.Value) if sensor.Value is not None else None
    except Exception:
        pass

    try:
        temps = psutil.sensors_temperatures()  # Linux only on Windows returns {}
        if temps and "coretemp" in temps:
            return temps["coretemp"][0].current
    except (AttributeError, Exception):
        pass

    return None
