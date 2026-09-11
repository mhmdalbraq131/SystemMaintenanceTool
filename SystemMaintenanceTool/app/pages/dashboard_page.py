"""Dashboard Page — Overview with gauges, sparklines, health score, alerts.

Arabic RTL layout, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QPushButton, QMessageBox,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_PRIMARY, ACCENT_CYAN, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED,
    STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL,
    SPACING_SM, SPACING_MD, SPACING_LG, CARD_RADIUS,
)
from app.core.config_manager import get_config
from app.core.logging_config import get_app_logger
from app.widgets.custom_widgets import CardWidget, ProgressRing, SparklineWidget, MetricCard, StatusBadge
from app.monitors.system_monitor import (
    CpuMonitor, RamMonitor, DiskMonitor, GpuMonitor,
    NetworkMonitor, SystemSummaryMonitor,
)
from app.models.notification import NotificationManager
from app.services.diagnostic_service import run_diagnostics
from app.exporters.export_service import export_data
from config.settings import DEFAULT_REFRESH_INTERVAL_MS


class DashboardPage(QWidget):
    """Main dashboard with health score ring, CPU/RAM/GPU/Disk gauges, sparklines, alerts."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._notif = NotificationManager()
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
        main_layout.setSpacing(SPACING_LG)
        main_layout.setAlignment(Qt.AlignTop)

        # ── Top: Health Score + Quick Metrics ─────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(SPACING_LG)

        # Health Score Ring
        health_card = CardWidget("مؤشر الصحة العامة")
        health_inner = QHBoxLayout(health_card.get_layout())
        self._health_ring = ProgressRing(size=160, line_width=14)
        self._health_ring.set_color("auto")
        self._health_ring.set_sub_label("مؤشر تقديري")
        health_inner.addWidget(self._health_ring, alignment=Qt.AlignCenter)

        health_info = QVBoxLayout()
        health_info.setSpacing(SPACING_SM)
        self._health_label = QLabel("جاري الفحص...")
        self._health_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        health_info.addWidget(self._health_label)

        disclaimer = QLabel("مؤشر تقديري مبني على الفحوصات المتاحة — وليس تشخيصاً رسمياً من ويندوز")
        disclaimer.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        disclaimer.setWordWrap(True)
        health_info.addWidget(disclaimer)

        self._run_diag_btn = QPushButton("إجراء فحص شامل")
        self._run_diag_btn.setObjectName("btnAccent")
        self._run_diag_btn.setCursor(Qt.PointingHandCursor)
        self._run_diag_btn.clicked.connect(self._run_diagnostic)
        health_info.addWidget(self._run_diag_btn)

        health_inner.addLayout(health_info, stretch=1)
        top_row.addWidget(health_card, stretch=2)

        # Quick metrics grid
        metrics_card = CardWidget("المقاييس السريعة")
        metrics_grid = QGridLayout(metrics_card.get_layout())
        metrics_grid.setSpacing(SPACING_MD)

        self._metric_cpu = MetricCard("المعالج", "0%", "", ACCENT_PRIMARY)
        self._metric_ram = MetricCard("الذاكرة", "0%", "", ACCENT_CYAN)
        self._metric_disk = MetricCard("القرص", "0%", "", ACCENT_GREEN)
        self._metric_gpu = MetricCard("الكرافيك", "N/A", "", ACCENT_ORANGE)
        self._metric_net = MetricCard("الشبكة", "0", "حمل", TEXT_ACCENT)
        self._metric_uptime = MetricCard("مدة التشغيل", "0", "ساعة", TEXT_SECONDARY)

        for i, w in enumerate([self._metric_cpu, self._metric_ram, self._metric_disk,
                                self._metric_gpu, self._metric_net, self._metric_uptime]):
            metrics_grid.addWidget(w, i // 3, i % 3)

        top_row.addWidget(metrics_card, stretch=3)
        main_layout.addLayout(top_row)

        # ── Middle: Sparklines ────────────────────────────────────────────
        spark_row = QHBoxLayout()
        spark_row.setSpacing(SPACING_LG)

        cpu_card = CardWidget("المعالج — آخر 60 قراءة")
        self._cpu_spark = SparklineWidget(points=60, height=80)
        self._cpu_spark.set_color(ACCENT_PRIMARY)
        cpu_card.get_layout().addWidget(self._cpu_spark)
        spark_row.addWidget(cpu_card)

        ram_card = CardWidget("الذاكرة — آخر 60 قراءة")
        self._ram_spark = SparklineWidget(points=60, height=80)
        self._ram_spark.set_color(ACCENT_CYAN)
        ram_card.get_layout().addWidget(self._ram_spark)
        spark_row.addWidget(ram_card)

        net_card = CardWidget("الشبكة — آخر 60 قراءة")
        self._net_spark = SparklineWidget(points=60, height=80)
        self._net_spark.set_color(ACCENT_GREEN)
        net_card.get_layout().addWidget(self._net_spark)
        spark_row.addWidget(net_card)

        main_layout.addLayout(spark_row)

        # ── Bottom: Alerts & System Summary ───────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(SPACING_LG)

        alerts_card = CardWidget("التنبيهات النشطة")
        self._alerts_layout = QVBoxLayout(alerts_card.get_layout())
        self._alerts_layout.setSpacing(SPACING_SM)
        self._alerts_layout.setAlignment(Qt.AlignTop)
        self._no_alerts = QLabel("لا توجد تنبيهات حالياً ✅")
        self._no_alerts.setStyleSheet(f"color: {STATUS_HEALTHY}; font-size: 13px;")
        self._alerts_layout.addWidget(self._no_alerts)
        bottom_row.addWidget(alerts_card, stretch=1)

        summary_card = CardWidget("ملخص النظام")
        self._summary_layout = QVBoxLayout(summary_card.get_layout())
        self._summary_layout.setSpacing(SPACING_SM)
        self._summary_layout.setAlignment(Qt.AlignTop)
        bottom_row.addWidget(summary_card, stretch=1)

        # Export button
        export_btn = QPushButton("تصدير لوحة المعلومات")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export_dashboard)
        main_layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Monitors ────────────────────────────────────────────────────────────

    def _start_monitors(self) -> None:
        config = get_config()
        interval = config.refresh_interval_ms

        self._cpu_mon = CpuMonitor(interval_ms=interval)
        self._cpu_mon.data_ready.connect(self._on_cpu_data)
        self._cpu_mon.start()

        self._ram_mon = RamMonitor(interval_ms=interval)
        self._ram_mon.data_ready.connect(self._on_ram_data)
        self._ram_mon.start()

        self._disk_mon = DiskMonitor(interval_ms=interval * 5)
        self._disk_mon.data_ready.connect(self._on_disk_data)
        self._disk_mon.start()

        self._gpu_mon = GpuMonitor(interval_ms=interval * 10)
        self._gpu_mon.data_ready.connect(self._on_gpu_data)
        self._gpu_mon.start()

        self._net_mon = NetworkMonitor(interval_ms=interval * 2)
        self._net_mon.data_ready.connect(self._on_net_data)
        self._net_mon.start()

        self._sys_mon = SystemSummaryMonitor()
        self._sys_mon.data_ready.connect(self._on_system_summary)
        self._sys_mon.start()

        # Refresh health score periodically
        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._refresh_health_score)
        self._health_timer.start(30000)  # every 30s
        QTimer.singleShot(3000, self._refresh_health_score)

    def _on_cpu_data(self, data: dict) -> None:
        pct = data.get("usage_percent", 0)
        self._metric_cpu.set_value(f"{pct:.0f}%")
        self._metric_cpu.set_color(
            STATUS_HEALTHY if pct < 50 else STATUS_WARNING if pct < 85 else STATUS_CRITICAL
        )
        self._cpu_spark.add_point(pct)
        self._notif.check_thresholds("cpu", pct)

    def _on_ram_data(self, data: dict) -> None:
        pct = data.get("usage_percent", 0)
        self._metric_ram.set_value(f"{pct:.0f}%")
        self._metric_ram.set_color(
            STATUS_HEALTHY if pct < 60 else STATUS_WARNING if pct < 90 else STATUS_CRITICAL
        )
        self._ram_spark.add_point(pct)
        self._notif.check_thresholds("ram", pct)

    def _on_disk_data(self, data: dict) -> None:
        partitions = data.get("partitions", [])
        if partitions:
            first = partitions[0]
            pct = first.get("usage_percent", 0)
            self._metric_disk.set_value(f"{pct:.0f}%")

    def _on_gpu_data(self, data: dict) -> None:
        load = data.get("load_percent", "N/A")
        if isinstance(load, (int, float)):
            self._metric_gpu.set_value(f"{load:.0f}%")
        else:
            self._metric_gpu.set_value("غير متاح")

    def _on_net_data(self, data: dict) -> None:
        total = data.get("total_bytes_sent", 0) + data.get("total_bytes_recv", 0)
        self._metric_net.set_value(f"{total / (1024**2):.1f}")
        self._net_spark.add_point(total / (1024**2))

    def _on_system_summary(self, data: dict) -> None:
        # Clear old labels
        while self._summary_layout.count():
            item = self._summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        fields = [
            ("اسم الجهاز", data.get("hostname", "N/A")),
            ("نظام التشغيل", data.get("os_version", "N/A")),
            ("مدة التشغيل", data.get("uptime", "N/A")),
            ("عدد العمليات", str(data.get("process_count", "N/A"))),
        ]
        for label, val in fields:
            lbl = QLabel(f"{label}: {val}")
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
            self._summary_layout.addWidget(lbl)

        uptime_h = data.get("uptime_hours", 0)
        if uptime_h:
            self._metric_uptime.set_value(f"{uptime_h:.0f}")

    def _refresh_health_score(self) -> None:
        try:
            results = run_diagnostics()
            score = results.get("health_score", 0)
            self._health_ring.set_value(score)
            self._health_ring.set_label("")
            if score >= 80:
                self._health_label.setText("النظام في حالة جيدة ✅")
                self._health_label.setStyleSheet(f"color: {STATUS_HEALTHY}; font-size: 16px; font-weight: bold;")
            elif score >= 50:
                self._health_label.setText("النظام يحتاج انتباه ⚠️")
                self._health_label.setStyleSheet(f"color: {STATUS_WARNING}; font-size: 16px; font-weight: bold;")
            else:
                self._health_label.setText("النظام بحاجة لصيانة 🔴")
                self._health_label.setStyleSheet(f"color: {STATUS_CRITICAL}; font-size: 16px; font-weight: bold;")

            # Update alerts
            issues = results.get("issues", [])
            while self._alerts_layout.count():
                item = self._alerts_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if issues:
                for issue in issues[:5]:
                    severity = issue.get("severity", "warning")
                    badge = StatusBadge(issue.get("message", ""), severity)
                    self._alerts_layout.addWidget(badge)
            else:
                lbl = QLabel("لا توجد تنبيهات حالياً ✅")
                lbl.setStyleSheet(f"color: {STATUS_HEALTHY}; font-size: 13px;")
                self._alerts_layout.addWidget(lbl)

        except Exception as e:
            self._logger.error(f"Health score refresh failed: {e}")

    def _run_diagnostic(self) -> None:
        self._run_diag_btn.setEnabled(False)
        self._run_diag_btn.setText("جاري الفحص...")
        self._refresh_health_score()
        self._run_diag_btn.setEnabled(True)
        self._run_diag_btn.setText("إجراء فحص شامل")

    def _export_dashboard(self) -> None:
        data = {
            "page": "dashboard",
            "health_score": getattr(self._health_ring, "_value", 0),
        }
        export_data(data, filename_stem="dashboard_export")

    def cleanup(self) -> None:
        for mon in [self._cpu_mon, self._ram_mon, self._disk_mon,
                    self._gpu_mon, self._net_mon]:
            mon.stop()
