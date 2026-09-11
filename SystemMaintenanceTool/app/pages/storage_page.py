"""Storage Page — Partitions, I/O, SMART status, cleanup categories.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QFrame, QScrollArea, QPushButton, QProgressBar,
    QMessageBox, QGridLayout, QCheckBox,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED, ACCENT_PRIMARY,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.widgets.custom_widgets import CardWidget, MetricCard
from app.services.disk_service import get_disk_info, get_cleanup_categories, execute_cleanup
from app.exporters.export_service import export_data


class StorageLoadWorker(QThread):
    """One-shot worker for loading disk info."""
    data_ready = Signal(dict)

    def run(self) -> None:
        try:
            data = get_disk_info()
            self.data_ready.emit(data)
        except Exception:
            self.data_ready.emit({})


class CleanupWorker(QThread):
    """Worker for executing cleanup operations."""
    done = Signal(dict)

    def __init__(self, categories: list[str]):
        super().__init__()
        self._categories = categories

    def run(self) -> None:
        result = execute_cleanup(self._categories)
        self.done.emit(result)


class StoragePage(QWidget):
    """Storage management: partitions, I/O, SMART, cleanup."""

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

        self._tabs = QTabWidget()
        self._tabs.setObjectName("storageTabs")
        self._tabs.addTab(self._build_partitions_tab(), "الأقسام")
        self._tabs.addTab(self._build_io_tab(), "الإدخال/الإخراج")
        self._tabs.addTab(self._build_smart_tab(), "SMART")
        self._tabs.addTab(self._build_cleanup_tab(), "التنظيف")
        layout.addWidget(self._tabs)

        export_btn = QPushButton("تصدير بيانات التخزين")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Partitions Tab ───────────────────────────────────────────────────────

    def _build_partitions_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        self._partitions_card = CardWidget("الأقسام المتصلة")
        self._partitions_layout = QVBoxLayout(self._partitions_card.get_layout())
        self._partitions_layout.setSpacing(SPACING_SM)
        layout.addWidget(self._partitions_card)

        layout.addStretch()
        return page

    # ── IO Tab ────────────────────────────────────────────────────────────────

    def _build_io_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        self._io_card = CardWidget("إحصائيات الإدخال/الإخراج")
        self._io_label = QLabel("جاري التحميل...")
        self._io_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        self._io_label.setWordWrap(True)
        self._io_card.get_layout().addWidget(self._io_label)
        layout.addWidget(self._io_card)

        layout.addStretch()
        return page

    # ── SMART Tab ────────────────────────────────────────────────────────────

    def _build_smart_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        self._smart_card = CardWidget("حالة SMART للأقراص")
        self._smart_label = QLabel("جاري الفحص...")
        self._smart_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        self._smart_label.setWordWrap(True)
        self._smart_card.get_layout().addWidget(self._smart_label)
        layout.addWidget(self._smart_card)

        note = QLabel("فحص SMART يتطلب صلاحيات مسؤول وأداة smartctl")
        note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
        return page

    # ── Cleanup Tab ──────────────────────────────────────────────────────────

    def _build_cleanup_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        card = CardWidget("فئات التنظيف")
        self._cleanup_grid = QGridLayout(card.get_layout())
        self._cleanup_grid.setSpacing(SPACING_SM)

        categories = get_cleanup_categories()
        self._cleanup_checks: list[QCheckBox] = []
        self._cleanup_size_labels: list[QLabel] = []

        for i, cat in enumerate(categories):
            cb = QCheckBox(cat.get("name", ""))
            cb.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px;")
            cb.setChecked(True)
            self._cleanup_checks.append(cb)
            self._cleanup_grid.addWidget(cb, i, 0)

            size_lbl = QLabel(cat.get("size_text", "0 ميغابايت"))
            size_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            self._cleanup_size_labels.append(size_lbl)
            self._cleanup_grid.addWidget(size_lbl, i, 1)

        layout.addWidget(card)

        total_lbl = QLabel()
        total_lbl.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: 14px; font-weight: bold;")
        self._total_cleanup_lbl = total_lbl
        layout.addWidget(total_lbl)

        self._cleanup_btn = QPushButton("تنفيذ التنظيف")
        self._cleanup_btn.setObjectName("btnAccent")
        self._cleanup_btn.setCursor(Qt.PointingHandCursor)
        self._cleanup_btn.clicked.connect(self._execute_cleanup)
        layout.addWidget(self._cleanup_btn)

        layout.addStretch()
        return page

    # ── Data Loading ─────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        self._worker = StorageLoadWorker()
        self._worker.data_ready.connect(self._on_data)
        self._worker.start()

    def _on_data(self, data: dict) -> None:
        partitions = data.get("partitions", [])

        # Clear old
        while self._partitions_layout.count():
            item = self._partitions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for part in partitions:
            device = part.get("device", "?")
            mount = part.get("mountpoint", "")
            fstype = part.get("fstype", "")
            pct = part.get("usage_percent", 0)
            total = part.get("total_gb", 0)
            used = part.get("used_gb", 0)
            free = part.get("free_gb", 0)

            row = QHBoxLayout()
            row.setSpacing(SPACING_SM)

            dev_lbl = QLabel(f"{device} ({mount})")
            dev_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; min-width: 120px;")
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

            info_lbl = QLabel(f"{used:.1f} / {total:.1f} غيغابايت | {fstype}")
            info_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            row.addWidget(info_lbl)

            container = QWidget()
            container.setLayout(row)
            self._partitions_layout.addWidget(container)

        # IO
        read_bytes = data.get("read_bytes", 0)
        write_bytes = data.get("write_bytes", 0)
        self._io_label.setText(
            f"إجمالي القراءة: {read_bytes / (1024**2):.1f} ميغابايت\n"
            f"إجمالي الكتابة: {write_bytes / (1024**2):.1f} ميغابايت"
        )

        # SMART
        smart_status = data.get("smart_status", "N/A")
        smart_color = ACCENT_GREEN if smart_status == "OK" else ACCENT_RED
        self._smart_label.setText(f"حالة SMART: {smart_status}")
        self._smart_label.setStyleSheet(f"color: {smart_color}; font-size: 14px; font-weight: bold;")

    def _execute_cleanup(self) -> None:
        categories = get_cleanup_categories()
        selected = [cat["id"] for i, cat in enumerate(categories)
                    if i < len(self._cleanup_checks) and self._cleanup_checks[i].isChecked()]

        if not selected:
            QMessageBox.information(self, "تنبيه", "لم تختر أي فئة للتنظيف")
            return

        reply = QMessageBox.warning(
            self, "تأكيد التنظيف",
            f"سيتم حذف الملفات في الفئات المحددة. هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        self._cleanup_btn.setEnabled(False)
        self._cleanup_btn.setText("جاري التنظيف...")
        self._cleanup_worker = CleanupWorker(selected)
        self._cleanup_worker.done.connect(self._on_cleanup_done)
        self._cleanup_worker.start()

    def _on_cleanup_done(self, result: dict) -> None:
        freed = result.get("freed_mb", 0)
        self._activity.log(f"تم تنظيف {freed:.1f} ميغابايت")
        QMessageBox.information(self, "تم التنظيف", f"تم تحرير {freed:.1f} ميغابايت")
        self._cleanup_btn.setEnabled(True)
        self._cleanup_btn.setText("تنفيذ التنظيف")
        self._refresh()

    def _export(self) -> None:
        self._worker = StorageLoadWorker()
        self._worker.data_ready.connect(lambda d: export_data(d, filename_stem="storage_export"))
        self._worker.start()
