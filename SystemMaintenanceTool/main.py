"""System Maintenance Tool Professional — Entry Point.

Arabic RTL PySide6 desktop application for Windows system monitoring,
management, maintenance, diagnostics, and repair.
"""

from __future__ import annotations

import sys
import os

# Ensure project root is on sys.path so relative imports work
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.core.logging_config import setup_logging, get_app_logger
from app.core.config_manager import load_config
from app.core.theme import build_stylesheet
from app.ui.main_window import MainWindow

# ── Page imports ────────────────────────────────────────────────────────────
from app.pages.dashboard_page import DashboardPage
from app.pages.performance_page import PerformancePage
from app.pages.processes_page import ProcessesPage
from app.pages.storage_page import StoragePage
from app.pages.network_page import NetworkPage
from app.pages.security_page import SecurityPage
from app.pages.maintenance_page import MaintenancePage
from app.pages.cmd_center_page import CmdCenterPage
from app.pages.services_page import ServicesPage
from app.pages.startup_page import StartupPage
from app.pages.system_info_page import SystemInfoPage
from app.pages.diagnostics_page import DiagnosticsPage
from app.pages.event_logs_page import EventLogsPage
from app.pages.reports_page import ReportsPage
from app.pages.settings_page import SettingsPage


def create_app() -> tuple[QApplication, MainWindow]:
    """Build and return the QApplication + MainWindow."""
    # ── Logging ────────────────────────────────────────────────────────────
    setup_logging()
    logger = get_app_logger()

    # ── Qt Application ─────────────────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("System Maintenance Tool Professional")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SMT Professional")

    # ── Load config & apply theme ──────────────────────────────────────────
    cfg = load_config()
    app.setStyleSheet(build_stylesheet(font_size=cfg.font_size))

    # ── Main Window ────────────────────────────────────────────────────────
    window = MainWindow()

    # ── Register all 15 pages ──────────────────────────────────────────────
    page_map = {
        "dashboard": DashboardPage,
        "performance": PerformancePage,
        "processes": ProcessesPage,
        "storage": StoragePage,
        "network": NetworkPage,
        "security": SecurityPage,
        "maintenance": MaintenancePage,
        "cmd": CmdCenterPage,
        "services": ServicesPage,
        "startup": StartupPage,
        "system_info": SystemInfoPage,
        "diagnostics": DiagnosticsPage,
        "event_logs": EventLogsPage,
        "reports": ReportsPage,
        "settings": SettingsPage,
    }

    for pid, cls in page_map.items():
        window.register_page(pid, cls(parent=window))

    # ── Navigate to dashboard by default ──────────────────────────────────
    window._navigate_to("dashboard")

    # ── Show window ────────────────────────────────────────────────────────
    window.show()
    logger.info("Application initialized successfully")

    return app, window


def main() -> int:
    """Application entry point."""
    app, window = create_app()

    exit_code = app.exec()

    # Clean shutdown — stop any internal monitors in pages that have cleanup
    for page_id, page_widget in window._page_map.items():
        if hasattr(page_widget, "cleanup"):
            page_widget.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
