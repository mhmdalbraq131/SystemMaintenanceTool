"""Event Logs Page — Read Windows event logs with filters and export.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal, QSortFilterProxyModel, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QScrollArea, QPushButton,
    QComboBox, QSpinBox, QTableView, QHeaderView,
    QAbstractItemView, QMessageBox,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    ACCENT_PRIMARY, ACCENT_ORANGE, ACCENT_RED,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.services.event_log_service import get_event_logs
from app.exporters.export_service import export_data


class EventLogModel(QAbstractTableModel):
    """Model for event log data."""

    COLUMNS = ["الوقت", "المصدر", "المعرف", "المستوى", "الرسالة"]

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
        keys = ["time_created", "provider_name", "id", "level", "message"]
        val = row.get(keys[index.column()], "")
        msg = str(val)
        if index.column() == 4 and len(msg) > 120:
            msg = msg[:120] + "..."
        return msg

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def update_data(self, events: list[dict]) -> None:
        self.beginResetModel()
        self._data = events
        self.endResetModel()


class EventLogLoadWorker(QThread):
    """Worker for loading event logs."""
    data_ready = Signal(list)

    def __init__(self, log_name: str = "System", max_events: int = 200):
        super().__init__()
        self._log_name = log_name
        self._max_events = max_events

    def run(self) -> None:
        try:
            events = get_event_logs(self._log_name, self._max_events)
            self.data_ready.emit(events)
        except Exception:
            self.data_ready.emit([])


class EventLogsPage(QWidget):
    """Windows Event Logs reader page."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._activity = ActivityLog()
        self._setup_ui()
        self._load_logs()

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

        # ── Filters ──────────────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(SPACING_MD)

        log_name_lbl = QLabel("سجل الأحداث:")
        log_name_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        filter_row.addWidget(log_name_lbl)

        self._log_combo = QComboBox()
        self._log_combo.addItems(["System", "Application", "Security", "Setup", "Forwarded Events"])
        self._log_combo.setFixedHeight(30)
        self._log_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        filter_row.addWidget(self._log_combo)

        max_lbl = QLabel("العدد:")
        max_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        filter_row.addWidget(max_lbl)

        self._max_spin = QSpinBox()
        self._max_spin.setRange(10, 1000)
        self._max_spin.setValue(200)
        self._max_spin.setSingleStep(50)
        self._max_spin.setFixedHeight(30)
        self._max_spin.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        filter_row.addWidget(self._max_spin)

        load_btn = QPushButton("تحميل")
        load_btn.setObjectName("btnAccent")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._load_logs)
        filter_row.addWidget(load_btn)

        self._search = QLineEdit()
        self._search.setPlaceholderText("بحث في الأحداث...")
        self._search.setObjectName("searchInput")
        self._search.setFixedHeight(34)
        self._search.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self._search, stretch=1)

        layout.addLayout(filter_row)

        # ── Table ────────────────────────────────────────────────────────
        self._model = EventLogModel()
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
                background: {BG_CARD}; color: {TEXT_PRIMARY};
                gridline-color: transparent; selection-background-color: {ACCENT_PRIMARY}33;
                alternate-background-color: {BG_DARKEST}; border: none; font-size: 12px;
            }}
            QHeaderView::section {{
                background: {BG_DARKEST}; color: {TEXT_ACCENT};
                padding: 6px; border: none; font-weight: bold; font-size: 12px;
            }}
        """)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        layout.addWidget(self._table)

        # Export
        export_btn = QPushButton("تصدير سجل الأحداث")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load_logs(self) -> None:
        log_name = self._log_combo.currentText()
        max_events = self._max_spin.value()

        self._worker = EventLogLoadWorker(log_name, max_events)
        self._worker.data_ready.connect(self._on_data)
        self._worker.start()

    def _on_data(self, events: list) -> None:
        self._model.update_data(events)

    def _apply_filter(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)

    def _export(self) -> None:
        export_data(self._model._data, filename_stem="event_logs_export", fmt="json")
