"""System Info Page — Windows, hardware, and drivers information tabs.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QPushButton,
    QTabWidget, QTextEdit, QGridLayout,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.widgets.custom_widgets import CardWidget, MetricCard
from app.services.system_info_service import get_windows_info, get_hardware_info, get_driver_info
from app.exporters.export_service import export_data


class InfoLoadWorker(QThread):
    """One-shot worker to load system info."""
    windows_ready = Signal(dict)
    hardware_ready = Signal(dict)
    drivers_ready = Signal(list)

    def run(self) -> None:
        try:
            self.windows_ready.emit(get_windows_info())
        except Exception:
            self.windows_ready.emit({})
        try:
            self.hardware_ready.emit(get_hardware_info())
        except Exception:
            self.hardware_ready.emit({})
        try:
            self.drivers_ready.emit(get_driver_info())
        except Exception:
            self.drivers_ready.emit([])


class SystemInfoPage(QWidget):
    """System information page with Windows, hardware, and driver tabs."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
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
        self._tabs.setObjectName("infoTabs")
        self._tabs.addTab(self._build_windows_tab(), "ويندوز")
        self._tabs.addTab(self._build_hardware_tab(), "الأجهزة")
        self._tabs.addTab(self._build_drivers_tab(), "التعريفات")

        layout.addWidget(self._tabs)

        export_btn = QPushButton("تصدير معلومات النظام")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _build_windows_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        self._win_card = CardWidget("معلومات نظام ويندوز")
        self._win_layout = QGridLayout(self._win_card.get_layout())
        self._win_layout.setSpacing(SPACING_SM)
        self._win_labels: dict[str, QLabel] = {}
        self._hw_labels: dict[str, QLabel] = {}
        layout.addWidget(self._win_card)
        layout.addStretch()
        return page

    def _build_hardware_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        self._hw_card = CardWidget("معلومات الأجهزة")
        self._hw_layout = QGridLayout(self._hw_card.get_layout())
        self._hw_layout.setSpacing(SPACING_SM)
        layout.addWidget(self._hw_card)
        layout.addStretch()
        return page

    def _build_drivers_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING_MD)

        self._drv_card = CardWidget("التعريفات المثبتة")
        self._drv_text = QTextEdit()
        self._drv_text.setReadOnly(True)
        self._drv_text.setMinimumHeight(300)
        self._drv_text.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_CARD}; color: {TEXT_PRIMARY};
                border: 1px solid #3a3f4b; border-radius: 6px;
                padding: 8px; font-family: Consolas; font-size: 12px;
            }}
        """)
        self._drv_card.get_layout().addWidget(self._drv_text)
        layout.addWidget(self._drv_card)
        layout.addStretch()
        return page

    def _refresh(self) -> None:
        self._info_worker = InfoLoadWorker()
        self._info_worker.windows_ready.connect(self._on_windows_info)
        self._info_worker.hardware_ready.connect(self._on_hardware_info)
        self._info_worker.drivers_ready.connect(self._on_drivers_info)
        self._info_worker.start()

    def _populate_grid(self, grid: QGridLayout, data: dict, labels: dict) -> None:
        row = 0
        for key, val in data.items():
            if key not in labels:
                k_lbl = QLabel(f"{key}:")
                k_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; min-width: 160px;")
                grid.addWidget(k_lbl, row, 0)

                v_lbl = QLabel(str(val) if val is not None else "غير متاح")
                v_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px;")
                v_lbl.setWordWrap(True)
                grid.addWidget(v_lbl, row, 1)

                labels[key] = v_lbl
            else:
                labels[key].setText(str(val) if val is not None else "غير متاح")
            row += 1

    def _on_windows_info(self, data: dict) -> None:
        self._populate_grid(self._win_layout, data, self._win_labels)

    def _on_hardware_info(self, data: dict) -> None:
        self._populate_grid(self._hw_layout, data, self._hw_labels)

    def _on_drivers_info(self, drivers: list) -> None:
        text_lines = []
        for drv in drivers:
            name = drv.get("name", "غير معروف")
            version = drv.get("version", "N/A")
            date = drv.get("date", "N/A")
            provider = drv.get("provider", "N/A")
            text_lines.append(f"{name} | الإصدار: {version} | التاريخ: {date} | المزود: {provider}")

        self._drv_text.setText("\n".join(text_lines) if text_lines else "لا تتوفر معلومات عن التعريفات")

    def _export(self) -> None:
        export_data({"page": "system_info"}, filename_stem="system_info_export")
