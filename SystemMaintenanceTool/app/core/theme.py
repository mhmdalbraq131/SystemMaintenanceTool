"""Unified Design System for System Maintenance Tool Professional.

Dark futuristic professional theme with RTL Arabic support.
All colours, sizes, and style tokens are defined here.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

# ── Colour Palette ─────────────────────────────────────────────────────────

# Background layers
BG_DARKEST      = "#0a0e17"
BG_DARK         = "#0d1321"
BG_CARD         = "#141b2d"
BG_CARD_HOVER   = "#1a2340"
BG_INPUT        = "#111827"
BG_SIDEBAR      = "#0d1321"
BG_HEADER       = "#0d1321"

# Borders
BORDER_DEFAULT  = "#1e293b"
BORDER_LIGHT    = "#2a3a5c"
BORDER_FOCUS    = "#3b82f6"

# Text colours
TEXT_PRIMARY    = "#e2e8f0"
TEXT_SECONDARY  = "#94a3b8"
TEXT_MUTED      = "#64748b"
TEXT_ACCENT     = "#38bdf8"
TEXT_ON_ACCENT  = "#ffffff"
TEXT_DANGER     = "#f87171"
TEXT_WARNING    = "#fbbf24"
TEXT_SUCCESS    = "#4ade80"

# Accent colours
ACCENT_PRIMARY  = "#3b82f6"
ACCENT_SECONDARY= "#8b5cf6"
ACCENT_CYAN     = "#06b6d4"
ACCENT_GREEN    = "#10b981"
ACCENT_ORANGE   = "#f97316"
ACCENT_RED      = "#ef4444"

# Status colours
STATUS_HEALTHY  = "#10b981"
STATUS_WARNING  = "#f59e0b"
STATUS_CRITICAL = "#ef4444"
STATUS_UNKNOWN  = "#6b7280"

# Chart colours
CHART_CPU       = "#3b82f6"
ART_RAM        = "#8b5cf6"
CHART_DISK      = "#06b6d4"
CHART_NETWORK_DL= "#10b981"
CHART_NETWORK_UL= "#f59e0b"
CHART_GPU       = "#ec4899"

# ── Spacing & Sizing ───────────────────────────────────────────────────────

SPACING_XS      = 4
SPACING_SM      = 8
SPACING_MD      = 12
SPACING_LG      = 16
SPACING_XL      = 24
SPACING_2XL     = 32

SIDEBAR_WIDTH   = 220
HEADER_HEIGHT   = 48

CARD_RADIUS     = 10
BUTTON_RADIUS   = 6
DIALOG_RADIUS   = 12

ICON_SIZE_SM    = 16
ICON_SIZE_MD    = 20
ICON_SIZE_LG    = 24
ICON_SIZE_XL    = 32
ICON_SIZE_2XL   = 48

# ── Typography ────────────────────────────────────────────────────────────

FONT_FAMILY     = "Segoe UI"
FONT_MONO       = "Consolas"

# ── Scrollbar Styling ──────────────────────────────────────────────────────
SCROLLBAR_WIDTH  = 8
SCROLLBAR_RADIUS = 4

# ── Build the full QSS stylesheet ─────────────────────────────────────────

def build_stylesheet(font_size: int = 14) -> str:
    """Return the complete QSS for the dark theme."""
    fs = font_size
    fs_sm = max(fs - 2, 10)
    fs_lg = fs + 2
    fs_title = fs + 8

    return f"""
    /* ── Global ────────────────────────────────────────────────────── */
    * {{
        font-family: "{FONT_FAMILY}";
        font-size: {fs}px;
        color: {TEXT_PRIMARY};
        box-sizing: border-box;
    }}

    /* ── Main Window ───────────────────────────────────────────────── */
    QMainWindow {{
        background: {BG_DARKEST};
    }}

    /* ── Header ─────────────────────────────────────────────────────── */
    #appHeader {{
        background: {BG_HEADER};
        border-bottom: 1px solid {BORDER_DEFAULT};
        min-height: {HEADER_HEIGHT}px;
        max-height: {HEADER_HEIGHT}px;
        padding: 0 {SPACING_LG}px;
    }}
    #headerTitle {{
        font-size: {fs_title}px;
        font-weight: bold;
        color: {TEXT_ACCENT};
    }}
    #headerVersion {{
        font-size: {fs_sm}px;
        color: {TEXT_MUTED};
    }}

    /* ── Sidebar ───────────────────────────────────────────────────── */
    #sidebarWidget {{
        background: {BG_SIDEBAR};
        border-right: 1px solid {BORDER_DEFAULT};
        width: {SIDEBAR_WIDTH}px;
        min-width: {SIDEBAR_WIDTH}px;
        max-width: {SIDEBAR_WIDTH}px;
    }}
    #sidebarScroll {{
        background: transparent;
        border: none;
    }}

    /* ── Sidebar Buttons ───────────────────────────────────────────── */
    SidebarButton {{
        background: transparent;
        border: none;
        border-radius: {BUTTON_RADIUS}px;
        padding: {SPACING_SM}px {SPACING_MD}px;
        text-align: right;
        color: {TEXT_SECONDARY};
        font-size: {fs}px;
        min-height: 38px;
    }}
    SidebarButton:hover {{
        background: {BG_CARD_HOVER};
        color: {TEXT_PRIMARY};
    }}
    SidebarButton[checked="true"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_PRIMARY}33, stop:1 transparent);
        color: {TEXT_ACCENT};
        border-right: 3px solid {ACCENT_PRIMARY};
    }}

    /* ── Content Area ──────────────────────────────────────────────── */
    #contentArea {{
        background: {BG_DARKEST};
    }}
    #contentScroll {{
        background: transparent;
        border: none;
    }}

    /* ── Cards ─────────────────────────────────────────────────────── */
    CardWidget {{
        background: {BG_CARD};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {CARD_RADIUS}px;
        padding: {SPACING_LG}px;
    }}
    CardWidget:hover {{
        border-color: {BORDER_LIGHT};
    }}

    /* ── Labels ─────────────────────────────────────────────────────── */
    QLabel {{
        color: {TEXT_PRIMARY};
        background: transparent;
    }}
    .label-title {{
        font-size: {fs_title}px;
        font-weight: bold;
        color: {TEXT_ACCENT};
    }}
    .label-header {{
        font-size: {fs_lg}px;
        font-weight: bold;
    }}
    .label-subtitle {{
        font-size: {fs}px;
        color: {TEXT_SECONDARY};
    }}
    .label-muted {{
        color: {TEXT_MUTED};
        font-size: {fs_sm}px;
    }}
    .label-value {{
        font-weight: bold;
        color: {TEXT_PRIMARY};
    }}
    .label-success {{ color: {TEXT_SUCCESS}; }}
    .label-warning {{ color: {TEXT_WARNING}; }}
    .label-danger  {{ color: {TEXT_DANGER}; }}

    /* ── Buttons ────────────────────────────────────────────────────── */
    QPushButton {{
        background: {ACCENT_PRIMARY};
        color: {TEXT_ON_ACCENT};
        border: none;
        border-radius: {BUTTON_RADIUS}px;
        padding: {SPACING_SM}px {SPACING_LG}px;
        min-height: 32px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background: {ACCENT_PRIMARY}cc;
    }}
    QPushButton:pressed {{
        background: {ACCENT_PRIMARY}99;
    }}
    QPushButton:disabled {{
        background: {BORDER_DEFAULT};
        color: {TEXT_MUTED};
    }}
    QPushButton#btnDanger {{
        background: {ACCENT_RED};
    }}
    QPushButton#btnDanger:hover {{
        background: {ACCENT_RED}cc;
    }}
    QPushButton#btnSecondary {{
        background: {BG_CARD};
        border: 1px solid {BORDER_LIGHT};
        color: {TEXT_PRIMARY};
    }}
    QPushButton#btnSecondary:hover {{
        background: {BG_CARD_HOVER};
    }}
    QPushButton#btnOutline {{
        background: transparent;
        border: 1px solid {BORDER_LIGHT};
        color: {TEXT_SECONDARY};
    }}
    QPushButton#btnOutline:hover {{
        border-color: {ACCENT_PRIMARY};
        color: {TEXT_ACCENT};
    }}

    /* ── Input Fields ──────────────────────────────────────────────── */
    QLineEdit, QTextEdit {{
        background: {BG_INPUT};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {BUTTON_RADIUS}px;
        padding: {SPACING_SM}px {SPACING_MD}px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT_PRIMARY}66;
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {BORDER_FOCUS};
    }}

    /* ── ComboBox ──────────────────────────────────────────────────── */
    QComboBox {{
        background: {BG_INPUT};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {BUTTON_RADIUS}px;
        padding: {SPACING_SM}px {SPACING_MD}px;
        color: {TEXT_PRIMARY};
        min-height: 32px;
    }}
    QComboBox:hover {{ border-color: {BORDER_LIGHT}; }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background: {BG_CARD};
        border: 1px solid {BORDER_DEFAULT};
        selection-background-color: {ACCENT_PRIMARY}33;
        color: {TEXT_PRIMARY};
    }}

    /* ── SpinBox ────────────────────────────────────────────────────── */
    QSpinBox {{
        background: {BG_INPUT};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {BUTTON_RADIUS}px;
        padding: {SPACING_SM}px {SPACING_MD}px;
        color: {TEXT_PRIMARY};
    }}

    /* ── Tables ────────────────────────────────────────────────────── */
    QTableWidget {{
        background: {BG_CARD};
        alternate-background-color: {BG_DARK};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {CARD_RADIUS}px;
        gridline-color: {BORDER_DEFAULT};
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT_PRIMARY}33;
        selection-color: {TEXT_PRIMARY};
    }}
    QTableWidget::item {{
        padding: {SPACING_SM}px {SPACING_MD}px;
        border-bottom: 1px solid {BORDER_DEFAULT};
    }}
    QTableWidget::item:hover {{
        background: {BG_CARD_HOVER};
    }}
    QHeaderView::section {{
        background: {BG_DARK};
        color: {TEXT_SECONDARY};
        border: none;
        border-bottom: 2px solid {BORDER_LIGHT};
        padding: {SPACING_SM}px {SPACING_MD}px;
        font-weight: bold;
        font-size: {fs_sm}px;
    }}

    /* ── TreeView ──────────────────────────────────────────────────── */
    QTreeView {{
        background: {BG_CARD};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {CARD_RADIUS}px;
        color: {TEXT_PRIMARY};
        selection-background-color: {ACCENT_PRIMARY}33;
        alternate-background-color: {BG_DARK};
    }}
    QTreeView::item {{ padding: {SPACING_SM}px; }}
    QHeaderView::section {{
        background: {BG_DARK};
        color: {TEXT_SECONDARY};
        border: none;
        border-bottom: 2px solid {BORDER_LIGHT};
        padding: {SPACING_SM}px {SPACING_MD}px;
        font-weight: bold;
        font-size: {fs_sm}px;
    }}

    /* ── Scrollbars ────────────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: transparent;
        width: {SCROLLBAR_WIDTH}px;
        margin: 2px 0 2px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER_LIGHT};
        border-radius: {SCROLLBAR_RADIUS}px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_MUTED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: {SCROLLBAR_WIDTH}px;
        margin: 0 2px 0 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER_LIGHT};
        border-radius: {SCROLLBAR_RADIUS}px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {TEXT_MUTED};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}

    /* ── Tab Widget ────────────────────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {CARD_RADIUS}px;
        background: {BG_CARD};
    }}
    QTabBar::tab {{
        background: {BG_DARK};
        border: 1px solid {BORDER_DEFAULT};
        border-bottom: none;
        border-top-left-radius: {BUTTON_RADIUS}px;
        border-top-right-radius: {BUTTON_RADIUS}px;
        padding: {SPACING_SM}px {SPACING_LG}px;
        color: {TEXT_SECONDARY};
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {BG_CARD};
        color: {TEXT_ACCENT};
        border-bottom: 2px solid {ACCENT_PRIMARY};
    }}
    QTabBar::tab:hover:!selected {{
        background: {BG_CARD_HOVER};
        color: {TEXT_PRIMARY};
    }}

    /* ── Progress Bar ──────────────────────────────────────────────── */
    QProgressBar {{
        background: {BG_INPUT};
        border: none;
        border-radius: {BUTTON_RADIUS}px;
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {ACCENT_PRIMARY}, stop:1 {ACCENT_CYAN});
        border-radius: {BUTTON_RADIUS}px;
    }}

    /* ── Slider ────────────────────────────────────────────────────── */
    QSlider::groove:horizontal {{
        background: {BG_INPUT};
        height: 6px;
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {ACCENT_PRIMARY};
        width: 16px;
        height: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }}

    /* ── CheckBox ──────────────────────────────────────────────────── */
    QCheckBox {{
        color: {TEXT_PRIMARY};
        spacing: {SPACING_SM}px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {BORDER_LIGHT};
        background: {BG_INPUT};
    }}
    QCheckBox::indicator:checked {{
        background: {ACCENT_PRIMARY};
        border-color: {ACCENT_PRIMARY};
    }}

    /* ── Dialogs ──────────────────────────────────────────────────── */
    QDialog {{
        background: {BG_DARK};
    }}

    /* ── ToolTip ────────────────────────────────────────────────────── */
    QToolTip {{
        background: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER_LIGHT};
        border-radius: {BUTTON_RADIUS}px;
        padding: {SPACING_SM}px {SPACING_MD}px;
        font-size: {fs_sm}px;
    }}

    /* ── Splitter ──────────────────────────────────────────────────── */
    QSplitter::handle {{
        background: {BORDER_DEFAULT};
        width: 2px;
    }}

    /* ── GroupBox ──────────────────────────────────────────────────── */
    QGroupBox {{
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {CARD_RADIUS}px;
        margin-top: 12px;
        padding-top: 16px;
        color: {TEXT_SECONDARY};
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        right: 10;
        padding: 0 {SPACING_SM}px;
    }}

    /* ── List Widget ──────────────────────────────────────────────── */
    QListWidget {{
        background: {BG_CARD};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {CARD_RADIUS}px;
        color: {TEXT_PRIMARY};
        outline: none;
    }}
    QListWidget::item {{
        padding: {SPACING_SM}px {SPACING_MD}px;
        border-bottom: 1px solid {BORDER_DEFAULT};
    }}
    QListWidget::item:hover {{
        background: {BG_CARD_HOVER};
    }}
    QListWidget::item:selected {{
        background: {ACCENT_PRIMARY}33;
        color: {TEXT_ACCENT};
    }}

    /* ── TextEdit (Terminal) ────────────────────────────────────────── */
    QTextEdit#terminalOutput {{
        background: #0c0c0c;
        color: #cccccc;
        font-family: "{FONT_MONO}";
        font-size: {fs_sm}px;
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {CARD_RADIUS}px;
        padding: {SPACING_MD}px;
    }}
    """
