"""Network Page — Adapters, stats, diagnostic tools (ping, tracert, etc).

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QScrollArea, QPushButton, QTextEdit,
    QMessageBox, QGridLayout, QComboBox,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_PRIMARY, ACCENT_GREEN, ACCENT_RED,
    SPACING_SM, SPACING_MD, SPACING_LG, CARD_RADIUS,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.widgets.custom_widgets import CardWidget, MetricCard, StatusBadge
from app.services.network_service import (
    get_network_adapters, get_network_stats,
    ping_host, tracert_host, nslookup_host,
    netstat_connections, arp_table, route_print,
    flush_dns, release_ip, renew_ip,
)
from app.exporters.export_service import export_data


class NetLoadWorker(QThread):
    """One-shot worker to load network info."""
    adapters_ready = Signal(list)
    stats_ready = Signal(dict)

    def run(self) -> None:
        try:
            adapters = get_network_adapters()
            self.adapters_ready.emit(adapters)
        except Exception:
            self.adapters_ready.emit([])
        try:
            stats = get_network_stats()
            self.stats_ready.emit(stats)
        except Exception:
            self.stats_ready.emit({})


class NetDiagWorker(QThread):
    """Worker for network diagnostic commands."""
    output_ready = Signal(str)

    def __init__(self, func, args: list = None):
        super().__init__()
        self._func = func
        self._args = args or []

    def run(self) -> None:
        try:
            result = self._func(*self._args)
            self.output_ready.emit(result)
        except Exception as e:
            self.output_ready.emit(f"خطأ: {e}")


class NetworkPage(QWidget):
    """Network monitoring and diagnostics page."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._activity = ActivityLog()
        self._setup_ui()
        self._refresh()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {BG_DARKEST};")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_MD)
        layout.setAlignment(Qt.AlignTop)

        # ── Quick Stats ────────────────────────────────────────────────────
        stats_card = CardWidget("إحصائيات الشبكة")
        stats_grid = QGridLayout(stats_card.get_layout())
        stats_grid.setSpacing(SPACING_SM)

        self._stat_sent = MetricCard("الإرسال", "0", "ميغابايت", ACCENT_PRIMARY)
        self._stat_recv = MetricCard("الاستقبال", "0", "ميغابايت", ACCENT_GREEN)
        self._stat_errors = MetricCard("الأخطاء", "0", "", ACCENT_RED)

        for i, w in enumerate([self._stat_sent, self._stat_recv, self._stat_errors]):
            stats_grid.addWidget(w, 0, i)

        layout.addWidget(stats_card)

        # ── Adapters ───────────────────────────────────────────────────────
        adapters_card = CardWidget("محولات الشبكة")
        self._adapters_layout = QVBoxLayout(adapters_card.get_layout())
        self._adapters_layout.setSpacing(SPACING_SM)
        layout.addWidget(adapters_card)

        # ── Diagnostics Tools ──────────────────────────────────────────────
        diag_card = CardWidget("أدوات التشخيص")
        diag_inner = QVBoxLayout(diag_card.get_layout())
        diag_inner.setSpacing(SPACING_MD)

        # Target input
        target_row = QHBoxLayout()
        target_row.setSpacing(SPACING_SM)
        target_lbl = QLabel("الهدف:")
        target_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        target_row.addWidget(target_lbl)

        self._target_input = QLineEdit()
        self._target_input.setPlaceholderText("مثال: google.com أو 8.8.8.8")
        self._target_input.setObjectName("searchInput")
        self._target_input.setFixedHeight(32)
        target_row.addWidget(self._target_input, stretch=1)
        diag_inner.addLayout(target_row)

        # Tool buttons grid
        tools_grid = QGridLayout()
        tools_grid.setSpacing(SPACING_SM)

        tool_defs = [
            ("Ping", lambda: self._run_diag(ping_host, [self._target_input.text() or "google.com"])),
            ("Tracert", lambda: self._run_diag(tracert_host, [self._target_input.text() or "google.com"])),
            ("NSLookup", lambda: self._run_diag(nslookup_host, [self._target_input.text() or "google.com"])),
            ("Netstat", lambda: self._run_diag(netstat_connections)),
            ("ARP", lambda: self._run_diag(arp_table)),
            ("Route", lambda: self._run_diag(route_print)),
            ("Flush DNS", lambda: self._run_diag(flush_dns)),
            ("Release IP", lambda: self._run_diag(release_ip)),
            ("Renew IP", lambda: self._run_diag(renew_ip)),
        ]

        for i, (name, func) in enumerate(tool_defs):
            btn = QPushButton(name)
            btn.setObjectName("btnOutline")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.clicked.connect(func)
            tools_grid.addWidget(btn, i // 3, i % 3)

        diag_inner.addLayout(tools_grid)

        # Output area
        self._output_area = QTextEdit()
        self._output_area.setReadOnly(True)
        self._output_area.setPlaceholderText("ستظهر النتائج هنا...")
        self._output_area.setMinimumHeight(200)
        self._output_area.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_CARD};
                color: {TEXT_PRIMARY};
                border: 1px solid #3a3f4b;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }}
        """)
        diag_inner.addWidget(self._output_area)

        layout.addWidget(diag_card)

        # Export
        export_btn = QPushButton("تصدير بيانات الشبكة")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _refresh(self) -> None:
        self._net_worker = NetLoadWorker()
        self._net_worker.adapters_ready.connect(self._on_adapters)
        self._net_worker.stats_ready.connect(self._on_stats)
        self._net_worker.start()

    def _on_adapters(self, adapters: list) -> None:
        while self._adapters_layout.count():
            item = self._adapters_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for adapter in adapters:
            name = adapter.get("name", "غير معروف")
            status = adapter.get("status", "غير معروف")
            speed = adapter.get("speed", "N/A")
            ip = adapter.get("ip_address", "غير متاح")

            status_badge = StatusBadge(status, "healthy" if status == "Up" else "critical")

            info = QLabel(f"{name} — IP: {ip} — السرعة: {speed}")
            info.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            info.setWordWrap(True)

            row = QHBoxLayout()
            row.addWidget(status_badge)
            row.addWidget(info, stretch=1)

            container = QWidget()
            container.setLayout(row)
            self._adapters_layout.addWidget(container)

    def _on_stats(self, data: dict) -> None:
        sent = data.get("total_bytes_sent", 0) / (1024**2)
        recv = data.get("total_bytes_recv", 0) / (1024**2)
        errors = data.get("total_errors", 0)

        self._stat_sent.set_value(f"{sent:.1f}")
        self._stat_recv.set_value(f"{recv:.1f}")
        self._stat_errors.set_value(str(errors))

    def _run_diag(self, func, args=None) -> None:
        self._output_area.setText("جاري التنفيذ... ⏳")
        self._diag_worker = NetDiagWorker(func, args)
        self._diag_worker.output_ready.connect(self._on_diag_output)
        self._diag_worker.start()

    def _on_diag_output(self, text: str) -> None:
        self._output_area.setText(text)

    def _export(self) -> None:
        export_data({"page": "network"}, filename_stem="network_export")
