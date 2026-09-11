"""Background system monitoring workers (QThread-based).

Each worker polls a specific subsystem at a configurable interval
and emits signals with real data for the UI to consume.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal, QMutex

from app.services.cpu_service import get_cpu_info
from app.services.ram_service import get_ram_info
from app.services.disk_service import get_disk_info
from app.services.gpu_service import get_gpu_info
from app.services.network_service import get_network_stats
from app.services.system_service import get_system_summary
from config.settings import DEFAULT_REFRESH_INTERVAL_MS


class CpuMonitor(QThread):
    """Polls CPU usage, freq, temp every interval."""

    data_ready = Signal(dict)

    def __init__(self, interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS, parent=None):
        super().__init__(parent)
        self._interval = interval_ms / 1000.0
        self._running = True
        self._mutex = QMutex()

    def run(self) -> None:
        while self._running:
            try:
                data = get_cpu_info()
                self.data_ready.emit(data)
            except Exception:
                pass
            self.msleep(int(self._interval * 1000))

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class RamMonitor(QThread):
    """Polls RAM usage every interval."""

    data_ready = Signal(dict)

    def __init__(self, interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS, parent=None):
        super().__init__(parent)
        self._interval = interval_ms / 1000.0
        self._running = True

    def run(self) -> None:
        while self._running:
            try:
                data = get_ram_info()
                self.data_ready.emit(data)
            except Exception:
                pass
            self.msleep(int(self._interval * 1000))

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class DiskMonitor(QThread):
    """Polls disk partitions and I/O every interval."""

    data_ready = Signal(dict)

    def __init__(self, interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS * 5, parent=None):
        super().__init__(parent)
        self._interval = interval_ms / 1000.0
        self._running = True

    def run(self) -> None:
        while self._running:
            try:
                data = get_disk_info()
                self.data_ready.emit(data)
            except Exception:
                pass
            self.msleep(int(self._interval * 1000))

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class GpuMonitor(QThread):
    """Polls GPU data every interval (slower, WMI call)."""

    data_ready = Signal(dict)

    def __init__(self, interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS * 10, parent=None):
        super().__init__(parent)
        self._interval = interval_ms / 1000.0
        self._running = True

    def run(self) -> None:
        while self._running:
            try:
                data = get_gpu_info()
                self.data_ready.emit(data)
            except Exception:
                pass
            self.msleep(int(self._interval * 1000))

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class NetworkMonitor(QThread):
    """Polls network stats every interval."""

    data_ready = Signal(dict)

    def __init__(self, interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS * 2, parent=None):
        super().__init__(parent)
        self._interval = interval_ms / 1000.0
        self._running = True

    def run(self) -> None:
        while self._running:
            try:
                data = get_network_stats()
                self.data_ready.emit(data)
            except Exception:
                pass
            self.msleep(int(self._interval * 1000))

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class SystemSummaryMonitor(QThread):
    """One-shot worker that loads system summary (uptime, hostname, etc.)."""

    data_ready = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self) -> None:
        try:
            data = get_system_summary()
            self.data_ready.emit(data)
        except Exception:
            pass


class OneShotWorker(QThread):
    """Generic one-shot worker that runs a callable and emits the result."""

    data_ready = Signal(object)
    error = Signal(str)

    def __init__(self, func, parent=None):
        super().__init__(parent)
        self._func = func

    def run(self) -> None:
        try:
            result = self._func()
            self.data_ready.emit(result)
        except Exception as e:
            self.error.emit(str(e))
