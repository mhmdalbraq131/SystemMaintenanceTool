"""Reports Page — Generate various system reports in multiple formats.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QPushButton,
    QComboBox, QMessageBox, QCheckBox, QTextEdit,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_PRIMARY, SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.widgets.custom_widgets import CardWidget
from app.reports.report_generator import generate_report
from app.exporters.export_service import export_data


class ReportGenWorker(QThread):
    """Worker for generating reports."""
    done = Signal(str, str)  # report_type, filepath_or_error

    def __init__(self, report_type: str, fmt: str = "json"):
        super().__init__()
        self._report_type = report_type
        self._fmt = fmt

    def run(self) -> None:
        try:
            data = generate_report(self._report_type)
            filepath = export_data(data, filename_stem=f"report_{self._report_type}", fmt=self._fmt)
            self.done.emit(self._report_type, filepath or "تم الإنشاء")
        except Exception as e:
            self.done.emit(self._report_type, f"خطأ: {e}")


class ReportsPage(QWidget):
    """Report generation page."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._activity = ActivityLog()
        self._setup_ui()

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

        # ── Report Configuration ──────────────────────────────────────────
        config_card = CardWidget("إعدادات التقرير")
        config_inner = QVBoxLayout(config_card.get_layout())
        config_inner.setSpacing(SPACING_MD)

        # Report type
        type_row = QHBoxLayout()
        type_row.setSpacing(SPACING_SM)
        type_lbl = QLabel("نوع التقرير:")
        type_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        type_row.addWidget(type_lbl)

        self._type_combo = QComboBox()
        self._type_combo.addItems([
            "تقرير النظام",
            "تقرير الأداء",
            "تقرير الأمان",
            "تقرير الصيانة",
            "تقرير التشخيص",
            "تقرير شامل",
        ])
        self._type_combo.setFixedHeight(32)
        self._type_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        type_row.addWidget(self._type_combo)
        type_row.addStretch()
        config_inner.addLayout(type_row)

        # Format
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(SPACING_SM)
        fmt_lbl = QLabel("صيغة التصدير:")
        fmt_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        fmt_row.addWidget(fmt_lbl)

        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(["JSON", "TXT", "CSV", "HTML"])
        self._fmt_combo.setFixedHeight(32)
        self._fmt_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        fmt_row.addWidget(self._fmt_combo)
        fmt_row.addStretch()
        config_inner.addLayout(fmt_row)

        layout.addWidget(config_card)

        # ── Generate Button ───────────────────────────────────────────────
        self._gen_btn = QPushButton("إنشاء التقرير")
        self._gen_btn.setObjectName("btnAccent")
        self._gen_btn.setCursor(Qt.PointingHandCursor)
        self._gen_btn.setMinimumHeight(42)
        self._gen_btn.clicked.connect(self._generate_report)
        layout.addWidget(self._gen_btn)

        # ── Output Preview ────────────────────────────────────────────────
        preview_card = CardWidget("معاينة التقرير")
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMinimumHeight(300)
        self._preview.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_CARD}; color: {TEXT_PRIMARY};
                border: 1px solid #3a3f4b; border-radius: 6px;
                padding: 10px; font-family: Consolas; font-size: 12px;
            }}
        """)
        preview_card.get_layout().addWidget(self._preview)
        layout.addWidget(preview_card)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _generate_report(self) -> None:
        type_map = {
            0: "system", 1: "performance", 2: "security",
            3: "maintenance", 4: "diagnostic", 5: "full",
        }
        fmt_map = {0: "json", 1: "txt", 2: "csv", 3: "html"}

        report_type = type_map.get(self._type_combo.currentIndex(), "system")
        fmt = fmt_map.get(self._fmt_combo.currentIndex(), "json")

        self._gen_btn.setEnabled(False)
        self._gen_btn.setText("جاري الإنشاء...")
        self._preview.setText("⏳ جاري تجميع البيانات وإنشاء التقرير...")

        self._worker = ReportGenWorker(report_type, fmt)
        self._worker.done.connect(self._on_report_done)
        self._worker.start()

    def _on_report_done(self, report_type: str, result: str) -> None:
        self._gen_btn.setEnabled(True)
        self._gen_btn.setText("إنشاء التقرير")

        if result.startswith("خطأ"):
            self._preview.setText(result)
            QMessageBox.critical(self, "خطأ", result)
        else:
            try:
                data = generate_report(report_type)
                import json
                self._preview.setText(json.dumps(data, ensure_ascii=False, indent=2) if isinstance(data, dict) else str(data))
            except Exception:
                self._preview.setText(f"تم إنشاء التقرير بنجاح ✅\n{result}")

            self._activity.log(f"تم إنشاء تقرير {report_type}")
            QMessageBox.information(self, "تم", "تم إنشاء التقرير بنجاح ✅")
