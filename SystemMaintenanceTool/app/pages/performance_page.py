"""Performance Page — CPU / RAM / GPU / Disk tabs with real-time charts.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QScrollArea, QPushButton, QGridLayout,
    QProgressBar,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_PRIMARY, ACCENT_CYAN, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.config_manager import get_config
from app.core.logging_config import get_app_logger
from app.widgets.custom_widgets import CardWidget, ProgressRing, SparklineWidget, MetricCard
from app.monitors.system_monitor import CpuMonitor, RamMonitor, GpuMonitor, DiskMonitor
from app.exporters.export_service import export_data


class PerformancePage(QWidget):
    """Tabbed performance view: CPU, RAM, GPU, Disk."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._setup_ui()
        self._start_monitors()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {BG_DARKEST};")

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        main_layout.setSpacing(SPACING_MD)
        main_layout.setAlignment(Qt.AlignTop)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setObjectName("perfTabs")

        self._tabs.addTab(self._build_cpu_tab(), "المعالج")
        self._tabs.addTab(self._build_ram_tab(), "الذاكرة")
        self._tabs.addTab(self._build_gpu_tab(), "كرافيك")
        self._tabs.addTab(self._build_disk_tab(), "القرص")

        main_layout.addWidget(self._tabs)

        export_btn = QPushButton("تصدير بيانات الأداء")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        main_layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── CPU Tab ─────────────────────────────────────────────────────────────

    def _build_cpu_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        # Gauges row
        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(SPACING_LG)

        self._cpu_ring = ProgressRing(size=140, line_width=12)
        self._cpu_ring.set_color(ACCENT_PRIMARY)
        self._cpu_ring.set_label("الاستخدام")
        gauges_row.addWidget(self._cpu_ring)

        cpu_metrics = QVBoxLayout()
        cpu_metrics.setSpacing(SPACING_SM)
        self._cpu_freq_lbl = MetricCard("التردد", "0", "ميغاهرتز", ACCENT_CYAN)
        self._cpu_cores_lbl = MetricCard("الأنوية", "0", "", TEXT_SECONDARY)
        self._cpu_temp_lbl = MetricCard("الحرارة", "N/A", "°م", ACCENT_ORANGE)
        for w in [self._cpu_freq_lbl, self._cpu_cores_lbl, self._cpu_temp_lbl]:
            cpu_metrics.addWidget(w)
        gauges_row.addLayout(cpu_metrics, stretch=1)

        layout.addLayout(gauges_row)

        # Sparkline
        spark_card = CardWidget("الاستخدام عبر الوقت")
        self._cpu_perf_spark = SparklineWidget(points=120, height=100)
        self._cpu_perf_spark.set_color(ACCENT_PRIMARY)
        spark_card.get_layout().addWidget(self._cpu_perf_spark)
        layout.addWidget(spark_card)

        layout.addStretch()
        return page

    # ── RAM Tab ──────────────────────────────────────────────────────────────

    def _build_ram_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        gauges_row = QHBoxLayout()
        gauges_row.setSpacing(SPACING_LG)

        self._ram_ring = ProgressRing(size=140, line_width=12)
        self._ram_ring.set_color(ACCENT_CYAN)
        self._ram_ring.set_label("الاستخدام")
        gauges_row.addWidget(self._ram_ring)

        ram_metrics = QVBoxLayout()
        ram_metrics.setSpacing(SPACING_SM)
        self._ram_total_lbl = MetricCard("الإجمالي", "0", "غيغابايت", TEXT_SECONDARY)
        self._ram_used_lbl = MetricCard("المستخدم", "0", "غيغابايت", ACCENT_CYAN)
        self._ram_swap_lbl = MetricCard("الSwap", "0", "غيغابايت", ACCENT_ORANGE)
        for w in [self._ram_total_lbl, self._ram_used_lbl, self._ram_swap_lbl]:
            ram_metrics.addWidget(w)
        gauges_row.addLayout(ram_metrics, stretch=1)

        layout.addLayout(gauges_row)

        spark_card = CardWidget("الاستخدام عبر الوقت")
        self._ram_perf_spark = SparklineWidget(points=120, height=100)
        self._ram_perf_spark.set_color(ACCENT_CYAN)
        spark_card.get_layout().addWidget(self._ram_perf_spark)
        layout.addWidget(spark_card)

        layout.addStretch()
        return page

    # ── GPU Tab ──────────────────────────────────────────────────────────────

    def _build_gpu_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        self._gpu_info_card = CardWidget("معلومات كرت الشاشة")
        self._gpu_name = QLabel("جاري التحميل...")
        self._gpu_name.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: bold;")
        self._gpu_info_card.get_layout().addWidget(self._gpu_name)

        self._gpu_load_lbl = QLabel("التحميل: N/A")
        self._gpu_load_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        self._gpu_info_card.get_layout().addWidget(self._gpu_load_lbl)

        self._gpu_temp_lbl = QLabel("الحرارة: N/A")
        self._gpu_temp_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        self._gpu_info_card.get_layout().addWidget(self._gpu_temp_lbl)

        self._gpu_mem_lbl = QLabel("الذاكرة: N/A")
        self._gpu_mem_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        self._gpu_info_card.get_layout().addWidget(self._gpu_mem_lbl)

        layout.addWidget(self._gpu_info_card)

        not_avail = QLabel("بيانات كرت الشاشة تعتمد على دعم gpuinfo أو WMI")
        not_avail.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        not_avail.setWordWrap(True)
        layout.addWidget(not_avail)

        layout.addStretch()
        return page

    # ── Disk Tab ──────────────────────────────────────────────────────────────

    def _build_disk_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        self._disk_partitions_card = CardWidget("الأقراص والأقسام")
        self._disk_layout = QVBoxLayout(self._disk_partitions_card.get_layout())
        self._disk_layout.setSpacing(SPACING_SM)
        layout.addWidget(self._disk_partitions_card)

        io_card = CardWidget("إحصائيات الإدخال/الإخراج")
        self._disk_io_lbl = QLabel("جاري التحميل...")
        self._disk_io_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        io_card.get_layout().addWidget(self._disk_io_lbl)
        layout.addWidget(io_card)

        layout.addStretch()
        return page

    # ── Monitors ─────────────────────────────────────────────────────────────

    def _start_monitors(self) -> None:
        config = get_config()
        interval = config.refresh_interval_ms

        self._cpu_mon = CpuMonitor(interval_ms=interval)
        self._cpu_mon.data_ready.connect(self._on_cpu)
        self._cpu_mon.start()

        self._ram_mon = RamMonitor(interval_ms=interval)
        self._ram_mon.data_ready.connect(self._on_ram)
        self._ram_mon.start()

        self._gpu_mon = GpuMonitor(interval_ms=interval * 10)
        self._gpu_mon.data_ready.connect(self._on_gpu)
        self._gpu_mon.start()

        self._disk_mon = DiskMonitor(interval_ms=interval * 5)
        self._disk_mon.data_ready.connect(self._on_disk)
        self._disk_mon.start()

    def _on_cpu(self, data: dict) -> None:
        pct = data.get("usage_percent", 0)
        self._cpu_ring.set_value(pct)
        self._cpu_ring.set_color("auto")
        self._cpu_perf_spark.add_point(pct)

        freq = data.get("frequency_current", 0)
        self._cpu_freq_lbl.set_value(f"{freq:.0f}")

        cores = data.get("physical_cores", 0)
        self._cpu_cores_lbl.set_value(str(cores))

        temp = data.get("temperature", "N/A")
        self._cpu_temp_lbl.set_value(str(temp))

    def _on_ram(self, data: dict) -> None:
        pct = data.get("usage_percent", 0)
        self._ram_ring.set_value(pct)
        self._ram_perf_spark.add_point(pct)

        total = data.get("total_gb", 0)
        used = data.get("used_gb", 0)
        swap = data.get("swap_used_gb", 0)

        self._ram_total_lbl.set_value(f"{total:.1f}")
        self._ram_used_lbl.set_value(f"{used:.1f}")
        self._ram_swap_lbl.set_value(f"{swap:.1f}")

    def _on_gpu(self, data: dict) -> None:
        self._gpu_name.setText(data.get("name", "غير متاح"))
        load = data.get("load_percent", "N/A")
        self._gpu_load_lbl.setText(f"التحميل: {load}")
        self._gpu_temp_lbl.setText(f"الحرارة: {data.get('temperature', 'N/A')}")
        self._gpu_mem_lbl.setText(f"الذاكرة: {data.get('memory_total', 'N/A')}")

    def _on_disk(self, data: dict) -> None:
        partitions = data.get("partitions", [])

        # Clear old widgets
        while self._disk_layout.count():
            item = self._disk_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for part in partitions:
            device = part.get("device", "?")
            pct = part.get("usage_percent", 0)
            total = part.get("total_gb", 0)
            used = part.get("used_gb", 0)
            free = part.get("free_gb", 0)

            row = QHBoxLayout()
            row.setSpacing(SPACING_SM)

            dev_lbl = QLabel(device)
            dev_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; min-width: 40px;")
            row.addWidget(dev_lbl)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(int(pct))
            bar.setTextVisible(True)
            bar.setFormat(f"{pct:.0f}%")
            bar.setFixedHeight(18)
            bar.setStyleSheet(f"""
                QProgressBar {{ background: {BG_CARD}; border: none; border-radius: 4px; }}
                QProgressBar::chunk {{ background: {ACCENT_GREEN if pct < 70 else ACCENT_ORANGE if pct < 90 else ACCENT_RED}; border-radius: 4px; }}
            """)
            row.addWidget(bar, stretch=1)

            info_lbl = QLabel(f"{used:.1f} / {total:.1f} غيغابايت")
            info_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            row.addWidget(info_lbl)

            container = QWidget()
            container.setLayout(row)
            self._disk_layout.addWidget(container)

        # IO stats
        io_text = data.get("io_text", "N/A")
        if not io_text:
            read_bytes = data.get("read_bytes", 0)
            write_bytes = data.get("write_bytes", 0)
            io_text = f"قراءة: {read_bytes / (1024**2):.1f} ميغابايت | كتابة: {write_bytes / (1024**2):.1f} ميغابايت"
        self._disk_io_lbl.setText(io_text)

    def _export(self) -> None:
        data = {"page": "performance", "info": "see individual service exports"}
        export_data(data, filename_stem="performance_export")

    def cleanup(self) -> None:
        for mon in [self._cpu_mon, self._ram_mon, self._gpu_mon, self._disk_mon]:
            mon.stop()
