"""Maintenance Page — SFC, DISM, CHKDSK repair tools.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QPushButton,
    QMessageBox, QProgressBar, QTextEdit, QComboBox,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_PRIMARY, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.widgets.custom_widgets import CardWidget
from app.maintenance.repair_service import run_sfc, run_dism_check, run_dism_scan, run_dism_restore, run_chkdsk
from app.exporters.export_service import export_data


class RepairWorker(QThread):
    """Worker for running repair commands (SFC/DISM/CHKDSK)."""
    output_ready = Signal(str, str)  # tool_name, output
    finished_signal = Signal(str, str)  # tool_name, result

    def __init__(self, tool_name: str, func):
        super().__init__()
        self._tool_name = tool_name
        self._func = func

    def run(self) -> None:
        try:
            result = self._func()
            self.finished_signal.emit(self._tool_name, result)
        except Exception as e:
            self.finished_signal.emit(self._tool_name, f"خطأ: {e}")


class MaintenancePage(QWidget):
    """System maintenance and repair tools page."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._activity = ActivityLog()
        self._workers: list[RepairWorker] = []
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

        # ── SFC Section ────────────────────────────────────────────────────
        sfc_card = CardWidget("مدقق ملفات النظام (SFC)")
        sfc_inner = QVBoxLayout(sfc_card.get_layout())
        sfc_inner.setSpacing(SPACING_SM)

        sfc_desc = QLabel("يفحص ويصلح ملفات النظام التالفة. يحتاج صلاحيات مسؤول.")
        sfc_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        sfc_desc.setWordWrap(True)
        sfc_inner.addWidget(sfc_desc)

        self._sfc_btn = QPushButton("تشغيل SFC /Scannow")
        self._sfc_btn.setObjectName("btnAccent")
        self._sfc_btn.setCursor(Qt.PointingHandCursor)
        self._sfc_btn.clicked.connect(self._run_sfc)
        sfc_inner.addWidget(self._sfc_btn)

        self._sfc_output = QTextEdit()
        self._sfc_output.setReadOnly(True)
        self._sfc_output.setMaximumHeight(100)
        self._sfc_output.setStyleSheet(f"""
            QTextEdit {{ background: {BG_CARD}; color: {TEXT_PRIMARY}; border: 1px solid #3a3f4b; border-radius: 6px; padding: 8px; font-family: Consolas; font-size: 12px; }}
        """)
        sfc_inner.addWidget(self._sfc_output)

        layout.addWidget(sfc_card)

        # ── DISM Section ──────────────────────────────────────────────────
        dism_card = CardWidget("أداة صيانة صورة النظام (DISM)")
        dism_inner = QVBoxLayout(dism_card.get_layout())
        dism_inner.setSpacing(SPACING_SM)

        dism_desc = QLabel("يفحص ويصلح صورة ويندوز. يمكن تشغيل ثلاثة مستويات:")
        dism_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        dism_desc.setWordWrap(True)
        dism_inner.addWidget(dism_desc)

        dism_levels = QHBoxLayout()
        dism_levels.setSpacing(SPACING_SM)

        self._dism_check_btn = QPushButton("فحص فقط")
        self._dism_check_btn.setObjectName("btnOutline")
        self._dism_check_btn.setCursor(Qt.PointingHandCursor)
        self._dism_check_btn.clicked.connect(lambda: self._run_dism("check"))
        dism_levels.addWidget(self._dism_check_btn)

        self._dism_scan_btn = QPushButton("فحص وصيانة")
        self._dism_scan_btn.setObjectName("btnAccent")
        self._dism_scan_btn.setCursor(Qt.PointingHandCursor)
        self._dism_scan_btn.clicked.connect(lambda: self._run_dism("scan"))
        dism_levels.addWidget(self._dism_scan_btn)

        self._dism_restore_btn = QPushButton("استعادة كاملة")
        self._dism_restore_btn.setObjectName("btnDanger")
        self._dism_restore_btn.setCursor(Qt.PointingHandCursor)
        self._dism_restore_btn.clicked.connect(lambda: self._run_dism("restore"))
        dism_levels.addWidget(self._dism_restore_btn)

        dism_inner.addLayout(dism_levels)

        self._dism_output = QTextEdit()
        self._dism_output.setReadOnly(True)
        self._dism_output.setMaximumHeight(120)
        self._dism_output.setStyleSheet(f"""
            QTextEdit {{ background: {BG_CARD}; color: {TEXT_PRIMARY}; border: 1px solid #3a3f4b; border-radius: 6px; padding: 8px; font-family: Consolas; font-size: 12px; }}
        """)
        dism_inner.addWidget(self._dism_output)

        layout.addWidget(dism_card)

        # ── CHKDSK Section ────────────────────────────────────────────────
        chkdsk_card = CardWidget("مدقق الأقراص (CHKDSK)")
        chkdsk_inner = QVBoxLayout(chkdsk_card.get_layout())
        chkdsk_inner.setSpacing(SPACING_SM)

        chkdsk_desc = QLabel("يفحص ويصلح أخطاء القرص. يتطلب إعادة تشغيل للفحص الكامل.")
        chkdsk_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        chkdsk_desc.setWordWrap(True)
        chkdsk_inner.addWidget(chkdsk_desc)

        drive_row = QHBoxLayout()
        drive_row.setSpacing(SPACING_SM)

        drive_lbl = QLabel("القرص:")
        drive_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        drive_row.addWidget(drive_lbl)

        self._drive_combo = QComboBox()
        self._drive_combo.addItems(["C:", "D:", "E:", "F:"])
        self._drive_combo.setFixedHeight(30)
        self._drive_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        drive_row.addWidget(self._drive_combo)

        self._chkdsk_btn = QPushButton("تشغيل CHKDSK")
        self._chkdsk_btn.setObjectName("btnAccent")
        self._chkdsk_btn.setCursor(Qt.PointingHandCursor)
        self._chkdsk_btn.clicked.connect(self._run_chkdsk)
        drive_row.addWidget(self._chkdsk_btn)
        drive_row.addStretch()

        chkdsk_inner.addLayout(drive_row)

        self._chkdsk_output = QTextEdit()
        self._chkdsk_output.setReadOnly(True)
        self._chkdsk_output.setMaximumHeight(100)
        self._chkdsk_output.setStyleSheet(f"""
            QTextEdit {{ background: {BG_CARD}; color: {TEXT_PRIMARY}; border: 1px solid #3a3f4b; border-radius: 6px; padding: 8px; font-family: Consolas; font-size: 12px; }}
        """)
        chkdsk_inner.addWidget(self._chkdsk_output)

        layout.addWidget(chkdsk_card)

        # Export
        export_btn = QPushButton("تصدير سجل الصيانة")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _run_sfc(self) -> None:
        reply = QMessageBox.warning(
            self, "تأكيد",
            "سيتم تشغيل SFC /Scannow. يحتاج صلاحيات مسؤول. هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        self._sfc_btn.setEnabled(False)
        self._sfc_btn.setText("جاري التشغيل...")
        self._sfc_output.setText("⏳ جاري فحص ملفات النظام...")

        worker = RepairWorker("SFC", run_sfc)
        worker.finished_signal.connect(self._on_tool_done)
        self._workers.append(worker)
        worker.start()

    def _run_dism(self, level: str) -> None:
        func_map = {"check": run_dism_check, "scan": run_dism_scan, "restore": run_dism_restore}
        func = func_map.get(level)
        if not func:
            return

        if level == "restore":
            reply = QMessageBox.warning(
                self, "تحذير",
                "الاستعادة الكاملة لصورة النظام قد تستغرق وقتاً طويلاً. هل تريد المتابعة؟",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        self._dism_output.setText(f"⏳ جاري تشغيل DISM {level}...")
        worker = RepairWorker(f"DISM_{level}", func)
        worker.finished_signal.connect(self._on_tool_done)
        self._workers.append(worker)
        worker.start()

    def _run_chkdsk(self) -> None:
        drive = self._drive_combo.currentText()
        reply = QMessageBox.warning(
            self, "تأكيد",
            f"سيتم تشغيل CHKDSK على القرص {drive}. قد يتطلب إعادة تشغيل. هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        self._chkdsk_output.setText(f"⏳ جاري تشغيل CHKDSK {drive}...")
        worker = RepairWorker(f"CHKDSK_{drive}", lambda d=drive: run_chkdsk(d))
        worker.finished_signal.connect(self._on_tool_done)
        self._workers.append(worker)
        worker.start()

    def _on_tool_done(self, tool_name: str, result: str) -> None:
        self._activity.log(f"اكتمل {tool_name}")
        self._logger.info(f"Repair tool done: {tool_name}")

        if "SFC" in tool_name:
            self._sfc_output.setText(result)
            self._sfc_btn.setEnabled(True)
            self._sfc_btn.setText("تشغيل SFC /Scannow")
        elif "DISM" in tool_name:
            self._dism_output.setText(result)
        elif "CHKDSK" in tool_name:
            self._chkdsk_output.setText(result)

    def _export(self) -> None:
        export_data({"page": "maintenance"}, filename_stem="maintenance_export")
