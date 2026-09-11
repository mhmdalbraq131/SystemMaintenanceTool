"""Services Page — Windows services list with start/stop/restart controls.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal, QSortFilterProxyModel, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QScrollArea, QPushButton,
    QMessageBox, QTableView, QHeaderView, QAbstractItemView,
    QComboBox,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ACCENT,
    ACCENT_PRIMARY, ACCENT_GREEN, ACCENT_RED, ACCENT_ORANGE,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.services.service_manager import get_services_list, start_service, stop_service, restart_service, change_startup_type
from app.exporters.export_service import export_data


class ServiceTableModel(QAbstractTableModel):
    """Model for Windows services data."""

    COLUMNS = ["الاسم", "العرض", "الحالة", "نوع البدء", "PID"]

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
        keys = ["name", "display_name", "status", "start_type", "pid"]
        return str(row.get(keys[index.column()], ""))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def update_data(self, services: list[dict]) -> None:
        self.beginResetModel()
        self._data = services
        self.endResetModel()

    def get_row_data(self, row: int) -> dict | None:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None


class ServiceLoadWorker(QThread):
    """One-shot worker to load services list."""
    data_ready = Signal(list)

    def run(self) -> None:
        try:
            services = get_services_list()
            self.data_ready.emit(services)
        except Exception:
            self.data_ready.emit([])


class ServiceActionWorker(QThread):
    """Worker for service start/stop/restart actions."""
    done = Signal(str, bool)  # service_name, success

    def __init__(self, action: str, service_name: str, startup_type: str = None):
        super().__init__()
        self._action = action
        self._service_name = service_name
        self._startup_type = startup_type

    def run(self) -> None:
        try:
            if self._action == "start":
                ok = start_service(self._service_name)
            elif self._action == "stop":
                ok = stop_service(self._service_name)
            elif self._action == "restart":
                ok = restart_service(self._service_name)
            elif self._action == "startup":
                ok = change_startup_type(self._service_name, self._startup_type)
            else:
                ok = False
            self.done.emit(self._service_name, ok)
        except Exception:
            self.done.emit(self._service_name, False)


class ServicesPage(QWidget):
    """Windows services management page."""

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
        self._search.setPlaceholderText("بحث عن خدمة...")
        self._search.setObjectName("searchInput")
        self._search.setFixedHeight(34)
        self._search.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self._search, stretch=1)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.setObjectName("btnAccent")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Service table
        self._model = ServiceTableModel()
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
                alternate-background-color: {BG_DARKEST}; border: none; font-size: 13px;
            }}
            QHeaderView::section {{
                background: {BG_DARKEST}; color: {TEXT_ACCENT};
                padding: 6px; border: none; font-weight: bold; font-size: 12px;
            }}
        """)

        layout.addWidget(self._table)

        # Action controls
        action_row = QHBoxLayout()
        action_row.setSpacing(SPACING_MD)

        self._start_btn = QPushButton("تشغيل")
        self._start_btn.setObjectName("btnAccent")
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.clicked.connect(lambda: self._do_action("start"))
        action_row.addWidget(self._start_btn)

        self._stop_btn = QPushButton("إيقاف")
        self._stop_btn.setObjectName("btnDanger")
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.clicked.connect(lambda: self._do_action("stop"))
        action_row.addWidget(self._stop_btn)

        self._restart_btn = QPushButton("إعادة تشغيل")
        self._restart_btn.setObjectName("btnOutline")
        self._restart_btn.setCursor(Qt.PointingHandCursor)
        self._restart_btn.clicked.connect(lambda: self._do_action("restart"))
        action_row.addWidget(self._restart_btn)

        startup_lbl = QLabel("نوع البدء:")
        startup_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        action_row.addWidget(startup_lbl)

        self._startup_combo = QComboBox()
        self._startup_combo.addItems(["تلقائي", "يدوي", "معطل"])
        self._startup_combo.setFixedHeight(30)
        self._startup_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        action_row.addWidget(self._startup_combo)

        set_startup_btn = QPushButton("تطبيق")
        set_startup_btn.setObjectName("btnOutline")
        set_startup_btn.setCursor(Qt.PointingHandCursor)
        set_startup_btn.clicked.connect(self._change_startup)
        action_row.addWidget(set_startup_btn)

        action_row.addStretch()
        layout.addLayout(action_row)

        # Export
        export_btn = QPushButton("تصدير قائمة الخدمات")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _refresh(self) -> None:
        self._load_worker = ServiceLoadWorker()
        self._load_worker.data_ready.connect(self._on_data)
        self._load_worker.start()

    def _on_data(self, services: list) -> None:
        self._model.update_data(services)

    def _apply_filter(self, text: str) -> None:
        self._proxy.setFilterFixedString(text)

    def _get_selected_service(self) -> dict | None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "تنبيه", "اختر خدمة من الجدول أولاً")
            return None
        source_idx = self._proxy.mapToSource(indexes[0])
        return self._model.get_row_data(source_idx.row())

    def _do_action(self, action: str) -> None:
        svc = self._get_selected_service()
        if not svc:
            return

        name = svc.get("name", "")
        display = svc.get("display_name", name)

        reply = QMessageBox.warning(
            self, "تأكيد",
            f"هل تريد {action} الخدمة: {display}؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        self._action_worker = ServiceActionWorker(action, name)
        self._action_worker.done.connect(self._on_action_done)
        self._action_worker.start()

    def _on_action_done(self, service_name: str, success: bool) -> None:
        if success:
            self._activity.log(f"تم تنفيذ الإجراء على الخدمة: {service_name}")
            self._refresh()
        else:
            QMessageBox.critical(self, "خطأ", f"فشل تنفيذ الإجراء. قد تحتاج صلاحيات مسؤول.")

    def _change_startup(self) -> None:
        svc = self._get_selected_service()
        if not svc:
            return

        name = svc.get("name", "")
        type_map = {0: "auto", 1: "demand", 2: "disabled"}
        startup = type_map.get(self._startup_combo.currentIndex(), "demand")

        reply = QMessageBox.warning(
            self, "تأكيد",
            f"هل تريد تغيير نوع بدء الخدمة {name}؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        self._startup_worker = ServiceActionWorker("startup", name, startup)
        self._startup_worker.done.connect(self._on_action_done)
        self._startup_worker.start()

    def _export(self) -> None:
        export_data(self._model._data, filename_stem="services_export")
