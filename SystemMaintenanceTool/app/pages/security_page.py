"""Security Page — Windows Defender, firewall, scan controls.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QPushButton,
    QMessageBox, QGridLayout, QTextEdit,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.widgets.custom_widgets import CardWidget, StatusBadge, MetricCard
from app.services.security_service import (
    get_defender_status, get_firewall_status,
    quick_scan, full_scan, get_protection_history,
)
from app.exporters.export_service import export_data


class SecurityLoadWorker(QThread):
    """One-shot worker to load security info."""
    defender_ready = Signal(dict)
    firewall_ready = Signal(dict)

    def run(self) -> None:
        try:
            defender = get_defender_status()
            self.defender_ready.emit(defender)
        except Exception:
            self.defender_ready.emit({})
        try:
            fw = get_firewall_status()
            self.firewall_ready.emit(fw)
        except Exception:
            self.firewall_ready.emit({})


class ScanWorker(QThread):
    """Worker for running antivirus scans."""
    scan_done = Signal(str, str)  # scan_type, result

    def __init__(self, scan_type: str):
        super().__init__()
        self._scan_type = scan_type

    def run(self) -> None:
        try:
            if self._scan_type == "quick":
                result = quick_scan()
            else:
                result = full_scan()
            self.scan_done.emit(self._scan_type, result)
        except Exception as e:
            self.scan_done.emit(self._scan_type, f"خطأ: {e}")


class SecurityPage(QWidget):
    """Security monitoring and action page."""

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

        # ── Defender Status ────────────────────────────────────────────────
        defender_card = CardWidget("حالة Windows Defender")
        self._defender_layout = QVBoxLayout(defender_card.get_layout())
        self._defender_layout.setSpacing(SPACING_SM)
        layout.addWidget(defender_card)

        # ── Firewall Status ────────────────────────────────────────────────
        firewall_card = CardWidget("جدار الحماية")
        self._firewall_layout = QVBoxLayout(firewall_card.get_layout())
        self._firewall_layout.setSpacing(SPACING_SM)
        layout.addWidget(firewall_card)

        # ── Scan Controls ──────────────────────────────────────────────────
        scan_card = CardWidget("أدوات الفحص")
        scan_inner = QHBoxLayout(scan_card.get_layout())
        scan_inner.setSpacing(SPACING_MD)

        self._quick_scan_btn = QPushButton("فحص سريع")
        self._quick_scan_btn.setObjectName("btnAccent")
        self._quick_scan_btn.setCursor(Qt.PointingHandCursor)
        self._quick_scan_btn.clicked.connect(lambda: self._run_scan("quick"))
        scan_inner.addWidget(self._quick_scan_btn)

        self._full_scan_btn = QPushButton("فحص كامل")
        self._full_scan_btn.setObjectName("btnAccent")
        self._full_scan_btn.setCursor(Qt.PointingHandCursor)
        self._full_scan_btn.clicked.connect(lambda: self._run_scan("full"))
        scan_inner.addWidget(self._full_scan_btn)

        self._scan_status_lbl = QLabel("")
        self._scan_status_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        scan_inner.addWidget(self._scan_status_lbl, stretch=1)

        layout.addWidget(scan_card)

        # ── Protection History ────────────────────────────────────────────
        history_card = CardWidget("سجل الحماية")
        self._history_text = QTextEdit()
        self._history_text.setReadOnly(True)
        self._history_text.setMaximumHeight(200)
        self._history_text.setStyleSheet(f"""
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
        history_card.get_layout().addWidget(self._history_text)
        layout.addWidget(history_card)

        # Export
        export_btn = QPushButton("تصدير تقرير الأمان")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _refresh(self) -> None:
        self._sec_worker = SecurityLoadWorker()
        self._sec_worker.defender_ready.connect(self._on_defender)
        self._sec_worker.firewall_ready.connect(self._on_firewall)
        self._sec_worker.start()

        # Load protection history
        try:
            history = get_protection_history()
            self._history_text.setText(history if history else "لا توجد سجلات حماية متاحة")
        except Exception:
            self._history_text.setText("فشل تحميل سجل الحماية")

    def _on_defender(self, data: dict) -> None:
        while self._defender_layout.count():
            item = self._defender_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        fields = [
            ("الحالة", data.get("antivirus_enabled", "غير معروف")),
            ("الحماية الفورية", data.get("realtime_protection", "غير معروف")),
            ("تحديثات التوقيعات", data.get("signature_up_to_date", "غير معروف")),
        ]
        for label, val in fields:
            status = "healthy" if val in ("True", True, "مفعل") else "warning" if val != "غير معروف" else "unknown"
            row = QHBoxLayout()
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; min-width: 120px;")
            row.addWidget(lbl)
            badge = StatusBadge(str(val), status)
            row.addWidget(badge)
            row.addStretch()
            container = QWidget()
            container.setLayout(row)
            self._defender_layout.addWidget(container)

    def _on_firewall(self, data: dict) -> None:
        while self._firewall_layout.count():
            item = self._firewall_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        profiles = data.get("profiles", {})
        for profile_name, status in profiles.items():
            is_on = status in ("True", True, "مفعل", "Enabled")
            row = QHBoxLayout()
            lbl = QLabel(f"ملف {profile_name}:")
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; min-width: 120px;")
            row.addWidget(lbl)
            badge = StatusBadge("مفعل" if is_on else "معطل", "healthy" if is_on else "critical")
            row.addWidget(badge)
            row.addStretch()
            container = QWidget()
            container.setLayout(row)
            self._firewall_layout.addWidget(container)

        if not profiles:
            lbl = QLabel("غير قادر على قراءة حالة جدار الحماية")
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            self._firewall_layout.addWidget(lbl)

    def _run_scan(self, scan_type: str) -> None:
        reply = QMessageBox.question(
            self, "تأكيد الفحص",
            f"هل تريد بدء فحص {'سريع' if scan_type == 'quick' else 'كامل'}؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes,
        )
        if reply == QMessageBox.No:
            return

        self._quick_scan_btn.setEnabled(False)
        self._full_scan_btn.setEnabled(False)
        self._scan_status_lbl.setText("جاري الفحص... ⏳")

        self._scan_worker = ScanWorker(scan_type)
        self._scan_worker.scan_done.connect(self._on_scan_done)
        self._scan_worker.start()

    def _on_scan_done(self, scan_type: str, result: str) -> None:
        self._quick_scan_btn.setEnabled(True)
        self._full_scan_btn.setEnabled(True)
        self._scan_status_lbl.setText("اكتمل الفحص ✅")
        self._activity.log(f"اكتمل فحص {scan_type}: {result}")
        QMessageBox.information(self, "نتيجة الفحص", result)

    def _export(self) -> None:
        export_data({"page": "security"}, filename_stem="security_export")
