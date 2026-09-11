"""Startup Page — Startup entries from registry and startup folder.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QScrollArea, QPushButton,
    QMessageBox, QTableView, QHeaderView, QAbstractItemView,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    ACCENT_PRIMARY, SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.services.startup_service import get_startup_entries, enable_startup_entry, disable_startup_entry
from app.exporters.export_service import export_data


class StartupTableModel(QAbstractTableModel):
    """Model for startup entries data."""

    COLUMNS = ["الاسم", "المسار", "الموقع", "الحالة"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[dict] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self._data[index.row()]
        keys = ["name", "command", "location", "status"]
        return str(row.get(keys[index.column()], ""))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def update_data(self, entries: list[dict]) -> None:
        self.beginResetModel()
        self._data = entries
        self.endResetModel()

    def get_row_data(self, row: int) -> dict | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None


class StartupLoadWorker(QThread):
    """One-shot worker for loading startup entries."""
    data_ready = Signal(list)

    def run(self) -> None:
        try:
            entries = get_startup_entries()
            self.data_ready.emit(entries)
        except Exception:
            self.data_ready.emit([])


class StartupPage(QWidget):
    """Windows startup programs management page."""

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

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(SPACING_MD)

        self._search = QLineEdit()
        self._search.setPlaceholderText("بحث عن برنامج بدء تشغيل...")
        self._search.setObjectName("searchInput")
        self._search.setFixedHeight(34)
        layout.addWidget(self._search)
        toolbar.addWidget(self._search, stretch=1)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.setObjectName("btnAccent")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Table
        self._model = StartupTableModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setStyleSheet(f"""
            QTableView {{
                background: {BG_CARD}; color: {TEXT_PRIMARY};
                gridline-color: transparent; selection-background-color: {ACCENT_PRIMARY}33;
                alternate-background-color: {BG_DARKEST}; border: none; font-size: 13px;
            }}
            QHeaderView::section {{
                background: {BG_DARKEST}; color: {TEXT_ACCENT};
                padding: 6px; border: none; font-weight: bold; font-size: 12px;
            }}
        """)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self._table)

        # Controls
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(SPACING_MD)

        self._enable_btn = QPushButton("تفعيل")
        self._enable_btn.setObjectName("btnAccent")
        self._enable_btn.setCursor(Qt.PointingHandCursor)
        self._enable_btn.clicked.connect(lambda: self._toggle_entry(True))
        ctrl_row.addWidget(self._enable_btn)

        self._disable_btn = QPushButton("تعطيل")
        self._disable_btn.setObjectName("btnDanger")
        self._disable_btn.setCursor(Qt.PointingHandCursor)
        self._disable_btn.clicked.connect(lambda: self._toggle_entry(False))
        ctrl_row.addWidget(self._disable_btn)

        ctrl_row.addStretch()
        layout.addLayout(ctrl_row)

        # Export
        export_btn = QPushButton("تصدير برامج بدء التشغيل")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _refresh(self) -> None:
        self._load_worker = StartupLoadWorker()
        self._load_worker.data_ready.connect(self._on_data)
        self._load_worker.start()

    def _on_data(self, entries: list) -> None:
        self._model.update_data(entries)

    def _get_selected(self) -> dict | None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "تنبيه", "اختر عنصر من الجدول أولاً")
            return None
        return self._model.get_row_data(indexes[0].row())

    def _toggle_entry(self, enable: bool) -> None:
        entry = self._get_selected()
        if not entry:
            return

        name = entry.get("name", "")
        location = entry.get("location", "")

        reply = QMessageBox.warning(
            self, "تأكيد",
            f"هل تريد {'تفعيل' if enable else 'تعطيل'} {name}؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        success = (enable_startup_entry if enable else disable_startup_entry)(name, location)
        if success:
            self._activity.log(f"تم {'تفعيل' if enable else 'تعطيل'} {name}")
            self._refresh()
        else:
            QMessageBox.critical(self, "خطأ", "فشل تغيير الحالة. قد تحتاج صلاحيات مسؤول.")

    def _export(self) -> None:
        export_data(self._model._data, filename_stem="startup_export")
