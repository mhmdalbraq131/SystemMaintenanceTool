"""Main Application Window for System Maintenance Tool Professional.

Layout:
  Header
  Sidebar | Content Area (QStackedWidget)
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QScrollArea, QFrame, QSizePolicy,
    QPushButton, QSpacerItem,
)

from app.core.theme import build_stylesheet, BG_DARKEST, BG_SIDEBAR, TEXT_ACCENT, TEXT_MUTED
from app.core.config_manager import load_config, get_config
from app.core.logging_config import setup_logging, get_app_logger
from app.widgets.custom_widgets import SidebarButton
from config.settings import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, MIN_WIDTH, MIN_HEIGHT,
    SIDEBAR_WIDTH, HEADER_HEIGHT, APP_NAME_AR, APP_VERSION,
    FONT_FAMILY, FONT_SIZE_DEFAULT,
)


class MainWindow(QMainWindow):
    """Main application shell with sidebar navigation and stacked pages."""

    def __init__(self) -> None:
        super().__init__()
        self._logger = get_app_logger()
        self._config = load_config()

        self.setWindowTitle(f"{APP_NAME_AR} — v{APP_VERSION}")
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        # Build UI
        self._build_ui()
        self._apply_theme()

        self._logger.info("Application started")

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header
        root_layout.addWidget(self._build_header())

        # Body: Sidebar + Content
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_content_area(), stretch=1)
        root_layout.addLayout(body, stretch=1)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("appHeader")
        header.setFixedHeight(HEADER_HEIGHT)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel(APP_NAME_AR)
        title.setObjectName("headerTitle")
        layout.addWidget(title)

        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("headerVersion")
        layout.addWidget(version)

        layout.addStretch()

        # Notification bell placeholder
        notif_btn = QPushButton(" الإشعارات ")
        notif_btn.setObjectName("btnOutline")
        notif_btn.setCursor(Qt.PointingHandCursor)
        notif_btn.setFixedHeight(32)
        self._notif_btn = notif_btn
        layout.addWidget(notif_btn)

        return header

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebarWidget")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(2)
        sidebar_layout.setAlignment(Qt.AlignTop)

        # Scroll area for sidebar buttons
        scroll = QScrollArea()
        scroll.setObjectName("sidebarScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(2)

        # Navigation items
        self._nav_items: list[tuple[str, SidebarButton]] = []
        pages = [
            ("dashboard", "لوحة المعلومات", "📊"),
            ("performance", "الأداء", "⚡"),
            ("processes", "العمليات", "🔧"),
            ("storage", "التخزين", "💾"),
            ("network", "الشبكة", "🌐"),
            ("security", "الأمان", "🛡️"),
            ("maintenance", "الصيانة", "🔨"),
            ("cmd", "مركز الأوامر", "⌨️"),
            ("services", "الخدمات", "⚙️"),
            ("startup", "بدء التشغيل", "🚀"),
            ("system_info", "معلومات النظام", "ℹ️"),
            ("diagnostics", "التشخيص", "🔍"),
            ("event_logs", "سجل الأحداث", "📋"),
            ("reports", "التقارير", "📄"),
            ("settings", "الإعدادات", "⚙️"),
        ]

        for page_id, label, icon in pages:
            btn = SidebarButton(label, icon)
            btn.clicked.connect(lambda checked=False, pid=page_id: self._navigate_to(pid))
            btn_layout.addWidget(btn)
            self._nav_items.append((page_id, btn))

        btn_layout.addStretch()
        scroll.setWidget(btn_container)
        sidebar_layout.addWidget(scroll)

        self._sidebar = sidebar
        return sidebar

    def _build_content_area(self) -> QWidget:
        content = QFrame()
        content.setObjectName("contentArea")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("contentScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._stack = QStackedWidget()
        scroll.setWidget(self._stack)
        layout.addWidget(scroll)

        return content

    # ── Navigation ──────────────────────────────────────────────────────────

    def _navigate_to(self, page_id: str) -> None:
        for pid, btn in self._nav_items:
            btn.set_checked(pid == page_id)

        # Switch to the page in the stack
        if page_id in self._page_map:
            self._stack.setCurrentWidget(self._page_map[page_id])
            self._logger.info(f"Navigated to: {page_id}")

    def register_page(self, page_id: str, widget: QWidget) -> None:
        """Register a page widget with the navigation system."""
        self._page_map: dict[str, QWidget] = getattr(self, "_page_map", {})
        self._page_map[page_id] = widget
        self._stack.addWidget(widget)

        # Default to dashboard
        if page_id == "dashboard" and self._stack.count() == 1:
            self._navigate_to("dashboard")

    # ── Theme ────────────────────────────────────────────────────────────────

    def _apply_theme(self) -> None:
        config = get_config()
        stylesheet = build_stylesheet(font_size=config.font_size)
        self.setStyleSheet(stylesheet)

    def get_notification_button(self) -> QPushButton:
        return self._notif_btn
