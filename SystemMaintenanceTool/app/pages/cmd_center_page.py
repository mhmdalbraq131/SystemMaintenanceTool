"""CMD Center Page — Command library, terminal, run history.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QFrame, QScrollArea, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter, QComboBox,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_PRIMARY, ACCENT_CYAN,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.widgets.custom_widgets import CardWidget
from app.commands.cmd_library import get_all_commands, get_command_by_id
from app.commands.cmd_runner import run_command
from app.exporters.export_service import export_data


class CmdRunWorker(QThread):
    """Worker for executing commands."""
    output_ready = Signal(str, str, str)  # cmd_id, output, error

    def __init__(self, cmd_id: str, cmd_str: str, shell: str = "cmd"):
        super().__init__()
        self._cmd_id = cmd_id
        self._cmd_str = cmd_str
        self._shell = shell

    def run(self) -> None:
        try:
            output, error = run_command(self._cmd_str, shell_type=self._shell, timeout=60)
            self.output_ready.emit(self._cmd_id, output, error)
        except Exception as e:
            self.output_ready.emit(self._cmd_id, "", str(e))


class CmdCenterPage(QWidget):
    """Command center with library, terminal, and history."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._activity = ActivityLog()
        self._history: list[dict] = []
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

        splitter = QSplitter(Qt.Horizontal)

        # ── Left: Command Library ─────────────────────────────────────────
        lib_widget = QWidget()
        lib_layout = QVBoxLayout(lib_widget)
        lib_layout.setContentsMargins(0, 0, 0, 0)
        lib_layout.setSpacing(SPACING_SM)

        lib_title = QLabel("مكتبة الأوامر")
        lib_title.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: 15px; font-weight: bold;")
        lib_layout.addWidget(lib_title)

        self._cmd_list = QListWidget()
        self._cmd_list.setStyleSheet(f"""
            QListWidget {{
                background: {BG_CARD};
                color: {TEXT_PRIMARY};
                border: 1px solid #3a3f4b;
                border-radius: 6px;
                font-size: 12px;
            }}
            QListWidget::item {{ padding: 6px; }}
            QListWidget::item:selected {{ background: {ACCENT_PRIMARY}33; }}
            QListWidget::item:hover {{ background: {BG_CARD}cc; }}
        """)

        commands = get_all_commands()
        for cmd in commands:
            item = QListWidgetItem(f"{cmd.get('icon', '⚡')} {cmd.get('name_ar', cmd.get('name', ''))}")
            item.setData(Qt.UserRole, cmd.get("id", ""))
            self._cmd_list.addItem(item)

        self._cmd_list.currentItemChanged.connect(self._on_cmd_selected)
        lib_layout.addWidget(self._cmd_list)

        self._cmd_desc = QLabel("")
        self._cmd_desc.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        self._cmd_desc.setWordWrap(True)
        lib_layout.addWidget(self._cmd_desc)

        self._run_lib_btn = QPushButton("تشغيل الأمر")
        self._run_lib_btn.setObjectName("btnAccent")
        self._run_lib_btn.setCursor(Qt.PointingHandCursor)
        self._run_lib_btn.clicked.connect(self._run_selected_cmd)
        lib_layout.addWidget(self._run_lib_btn)

        splitter.addWidget(lib_widget)

        # ── Right: Terminal + History ───────────────────────────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(SPACING_SM)

        # Terminal area
        term_card = CardWidget("الطرفية")
        term_inner = QVBoxLayout(term_card.get_layout())
        term_inner.setSpacing(SPACING_SM)

        input_row = QHBoxLayout()
        input_row.setSpacing(SPACING_SM)

        self._shell_combo = QComboBox()
        self._shell_combo.addItems(["CMD", "PowerShell"])
        self._shell_combo.setFixedHeight(30)
        self._shell_combo.setFixedWidth(110)
        self._shell_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        input_row.addWidget(self._shell_combo)

        self._cmd_input = QLineEdit()
        self._cmd_input.setPlaceholderText("أدخل الأمر هنا...")
        self._cmd_input.setObjectName("searchInput")
        self._cmd_input.setFixedHeight(32)
        self._cmd_input.returnPressed.connect(self._run_custom_cmd)
        input_row.addWidget(self._cmd_input, stretch=1)

        run_btn = QPushButton("تشغيل")
        run_btn.setObjectName("btnAccent")
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.clicked.connect(self._run_custom_cmd)
        input_row.addWidget(run_btn)

        term_inner.addLayout(input_row)

        self._term_output = QTextEdit()
        self._term_output.setReadOnly(True)
        self._term_output.setMinimumHeight(250)
        self._term_output.setStyleSheet(f"""
            QTextEdit {{
                background: #0d1117;
                color: {ACCENT_CYAN};
                border: 1px solid #1a2332;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }}
        """)
        term_inner.addWidget(self._term_output)

        right_layout.addWidget(term_card)

        # History
        hist_card = CardWidget("سجل الأوامر")
        self._history_list = QListWidget()
        self._history_list.setMaximumHeight(150)
        self._history_list.setStyleSheet(f"""
            QListWidget {{
                background: {BG_CARD};
                color: {TEXT_SECONDARY};
                border: 1px solid #3a3f4b;
                border-radius: 6px;
                font-size: 12px;
            }}
        """)
        hist_card.get_layout().addWidget(self._history_list)
        right_layout.addWidget(hist_card)

        splitter.addWidget(right_widget)

        splitter.setSizes([300, 600])
        layout.addWidget(splitter)

        # Export
        export_btn = QPushButton("تصدير سجل الأوامر")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _on_cmd_selected(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if not current:
            return
        cmd_id = current.data(Qt.UserRole)
        cmd = get_command_by_id(cmd_id)
        if cmd:
            self._cmd_desc.setText(cmd.get("description_ar", cmd.get("description", "")))

    def _run_selected_cmd(self) -> None:
        current = self._cmd_list.currentItem()
        if not current:
            return
        cmd_id = current.data(Qt.UserRole)
        cmd = get_command_by_id(cmd_id)
        if not cmd:
            return

        cmd_str = cmd.get("command", "")
        shell = cmd.get("shell", "cmd")
        self._execute(cmd_id, cmd_str, shell)

    def _run_custom_cmd(self) -> None:
        cmd_str = self._cmd_input.text().strip()
        if not cmd_str:
            return
        shell = "powershell" if self._shell_combo.currentIndex() == 1 else "cmd"
        self._execute("custom", cmd_str, shell)
        self._cmd_input.clear()

    def _execute(self, cmd_id: str, cmd_str: str, shell: str) -> None:
        self._term_output.setText(f"⏳ جاري التنفيذ: {cmd_str}")
        worker = CmdRunWorker(cmd_id, cmd_str, shell)
        worker.output_ready.connect(self._on_output)
        self._worker = worker
        worker.start()

    def _on_output(self, cmd_id: str, output: str, error: str) -> None:
        display = output if output else error
        self._term_output.setText(display)

        # Add to history
        self._history.append({"id": cmd_id, "output": display})
        self._history_list.addItem(f"[{cmd_id}] {display[:80]}...")
        self._activity.log(f"تم تشغيل أمر: {cmd_id}")

    def _export(self) -> None:
        export_data(self._history, filename_stem="cmd_history")
