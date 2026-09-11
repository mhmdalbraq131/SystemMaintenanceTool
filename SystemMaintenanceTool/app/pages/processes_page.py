"""Processes Page — Full process table with search, kill, priority controls.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSortFilterProxyModel, QThread, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableView, QHeaderView, QPushButton, QLabel,
    QFrame, QScrollArea, QMessageBox, QComboBox,
    QAbstractItemView, QStyledItemDelegate,
)

from PySide6.QtCore import QAbstractTableModel, QModelIndex

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_PRIMARY, ACCENT_RED, ACCENT_ORANGE, STATUS_HEALTHY,
    STATUS_WARNING, STATUS_CRITICAL, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.services.process_service import get_process_list, kill_process, set_process_priority
from app.exporters.export_service import export_data


class ProcessTableModel(QAbstractTableModel):
    """Model holding process data for QTableView."""

    COLUMNS = ["PID", "الاسم", "المستخدم", "المعالج %", "الذاكرة (م.ب)", "الحالة", "الأولوية"]

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
        col = index.column()
        keys = ["pid", "name", "username", "cpu_percent", "memory_mb", "status", "priority"]
        val = row.get(keys[col], "")
        if isinstance(val, float):
            return f"{val:.1f}"
        return str(val)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def update_data(self, processes: list[dict]) -> None:
        self.beginResetModel()
        self._data = processes
        self.endResetModel()

    def get_row_data(self, row: int) -> dict | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None


class ProcessLoadWorker(QThread):
    """Background worker for loading process list."""
    data_ready = Signal(list)

    def run(self) -> None:
        try:
            processes = get_process_list()
            self.data_ready.emit(processes)
        except Exception:
            self.data_ready.emit([])


class ProcessesPage(QWidget):
    """Process management page with table, search, actions."""

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
        self._search.setPlaceholderText("بحث عن عملية...")
        self._search.setObjectName("searchInput")
        self._search.setFixedHeight(34)
        self._search.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self._search, stretch=1)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.setObjectName("btnAccent")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(refresh_btn)

        kill_btn = QPushButton("إنهاء العملية")
        kill_btn.setObjectName("btnDanger")
        kill_btn.setCursor(Qt.PointingHandCursor)
        kill_btn.clicked.connect(self._kill_selected)
        toolbar.addWidget(kill_btn)

        layout.addLayout(toolbar)

        # Process table
        self._model = ProcessTableModel()
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setStyleSheet(f"""
            QTableView {{
                background: {BG_CARD};
                color: {TEXT_PRIMARY};
                gridline-color: transparent;
                selection-background-color: {ACCENT_PRIMARY}33;
                alternate-background-color: {BG_DARKEST};
                border: none;
                font-size: 13px;
            }}
            QHeaderView::section {{
                background: {BG_DARKEST};
                color: {TEXT_ACCENT};
                padding: 6px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self._table)

        # Priority controls
        prio_row = QHBoxLayout()
        prio_row.setSpacing(SPACING_MD)
        prio_label = QLabel("تغيير الأولوية:")
        prio_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        prio_row.addWidget(prio_label)

        self._prio_combo = QComboBox()
        self._prio_combo.addItems(["منخفض", "أقل من العادي", "عادي", "أعلى من العادي", "مرتفع", "حقيقي"])
        self._prio_combo.setFixedHeight(30)
        self._prio_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        prio_row.addWidget(self._prio_combo)

        set_prio_btn = QPushButton("تطبيق")
        set_prio_btn.setObjectName("btnOutline")
        set_prio_btn.setCursor(Qt.PointingHandCursor)
        set_prio_btn.clicked.connect(self._set_priority)
        prio_row.addWidget(set_prio_btn)
        prio_row.addStretch()
        layout.addLayout(prio_row)

        # Export
        export_btn = QPushButton("تصدير قائمة العمليات")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _refresh(self) -> None:
        self._worker = ProcessLoadWorker()
        self._worker.data_ready.connect(self._on_data)
        self._worker.start()

    def _on_data(self, processes: list) -> None:
        self._model.update_data(processes)

    def _apply_filter(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)

    def _kill_selected(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return

        source_idx = self._proxy.mapToSource(indexes[0])
        row_data = self._model.get_row_data(source_idx.row())
        if not row_data:
            return

        pid = row_data.get("pid", 0)
        name = row_data.get("name", "")

        reply = QMessageBox.warning(
            self, "تأكيد إنهاء العملية",
            f"هل أنت متأكد من إنهاء العملية:\n{name} (PID: {pid})؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            success = kill_process(pid)
            if success:
                self._activity.log(f"تم إنهاء العملية: {name} (PID: {pid})")
                self._logger.info(f"Process killed: {name} PID={pid}")
                self._refresh()
            else:
                QMessageBox.critical(self, "خطأ", f"فشل إنهاء العملية. قد تحتاج صلاحيات مسؤول.")

    def _set_priority(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return

        source_idx = self._proxy.mapToSource(indexes[0])
        row_data = self._model.get_row_data(source_idx.row())
        if not row_data:
            return

        pid = row_data.get("pid", 0)
        prio_map = {0: "low", 1: "below_normal", 2: "normal", 3: "above_normal", 4: "high", 5: "realtime"}
        prio = prio_map.get(self._prio_combo.currentIndex(), "normal")

        if prio == "realtime":
            reply = QMessageBox.warning(
                self, "تحذير",
                "أولوية 'حقيقي' قد تسبب عدم استقرار في النظام. هل تريد المتابعة؟",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        success = set_process_priority(pid, prio)
        if success:
            self._activity.log(f"تم تغيير أولوية PID={pid} إلى {prio}")
            self._refresh()

    def _export(self) -> None:
        export_data(self._model._data, filename_stem="processes_export")
