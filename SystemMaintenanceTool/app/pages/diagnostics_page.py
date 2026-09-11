"""Diagnostics Page — Run diagnostic checks, view issues, suggested actions.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QPushButton,
    QMessageBox, QProgressBar, QGridLayout,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL,
    ACCENT_PRIMARY, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_RED,
    SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.widgets.custom_widgets import CardWidget, ProgressRing, StatusBadge
from app.diagnostics.diagnostic_service import run_full_diagnostic, calculate_health_score, DiagnosticStatus
from app.exporters.export_service import export_data


class DiagnosticWorker(QThread):
    """Worker for running full diagnostics."""
    progress = Signal(int)
    done = Signal(dict)

    def run(self) -> None:
        try:
            self.progress.emit(10)
            check_results = run_full_diagnostic()
            health_score = calculate_health_score(check_results)
            self.progress.emit(100)
            issues = [r for r in check_results if r.status != DiagnosticStatus.PASSED]
            self.done.emit({"health_score": health_score, "issues": [{"message": r.details or r.category, "severity": r.status.value} for r in issues], "checks": {r.category: {"passed": r.status == DiagnosticStatus.PASSED, "message": r.details, "severity": r.status.value} for r in check_results}})
        except Exception as e:
            self.done.emit({"health_score": 0, "issues": [{"message": str(e), "severity": "critical"}]})


class DiagnosticsPage(QWidget):
    """System diagnostics page with health score, issues list, and actions."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._activity = ActivityLog()
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

        # ── Run Diagnostics Section ───────────────────────────────────────
        run_card = CardWidget("تشغيل التشخيص")
        run_inner = QVBoxLayout(run_card.get_layout())
        run_inner.setSpacing(SPACING_SM)

        disclaimer = QLabel("مؤشر تقديري مبني على الفحوصات المتاحة — وليس تشخيصاً رسمياً من ويندوز")
        disclaimer.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        disclaimer.setWordWrap(True)
        run_inner.addWidget(disclaimer)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_MD)

        self._run_btn = QPushButton("تشغيل فحص شامل")
        self._run_btn.setObjectName("btnAccent")
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.clicked.connect(self._run_diagnostics)
        btn_row.addWidget(self._run_btn)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(20)
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{ background: {BG_CARD}; border: none; border-radius: 4px; text-align: center; color: {TEXT_SECONDARY}; }}
            QProgressBar::chunk {{ background: {ACCENT_PRIMARY}; border-radius: 4px; }}
        """)
        btn_row.addWidget(self._progress_bar, stretch=1)

        run_inner.addLayout(btn_row)
        layout.addWidget(run_card)

        # ── Health Score ──────────────────────────────────────────────────
        score_card = CardWidget("مؤشر الصحة")
        score_inner = QHBoxLayout(score_card.get_layout())

        self._health_ring = ProgressRing(size=130, line_width=12)
        self._health_ring.set_color("auto")
        self._health_ring.set_sub_label("مؤشر تقديري")
        score_inner.addWidget(self._health_ring, alignment=Qt.AlignCenter)

        self._score_label = QLabel("لم يتم الفحص بعد")
        self._score_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 15px; font-weight: bold;")
        score_inner.addWidget(self._score_label, stretch=1)

        layout.addWidget(score_card)

        # ── Issues List ───────────────────────────────────────────────────
        issues_card = CardWidget("المشاكل المكتشفة")
        self._issues_layout = QVBoxLayout(issues_card.get_layout())
        self._issues_layout.setSpacing(SPACING_SM)
        self._issues_layout.setAlignment(Qt.AlignTop)

        self._no_issues = QLabel("قم بتشغيل الفحص لعرض النتائج")
        self._no_issues.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        self._issues_layout.addWidget(self._no_issues)

        layout.addWidget(issues_card)

        # ── Check Results ─────────────────────────────────────────────────
        results_card = CardWidget("نتائج الفحوصات")
        self._results_grid = QGridLayout(results_card.get_layout())
        self._results_grid.setSpacing(SPACING_SM)
        self._result_widgets: dict[str, StatusBadge] = {}
        layout.addWidget(results_card)

        # Export
        export_btn = QPushButton("تصدير تقرير التشخيص")
        export_btn.setObjectName("btnOutline")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn, alignment=Qt.AlignLeft)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _run_diagnostics(self) -> None:
        self._run_btn.setEnabled(False)
        self._run_btn.setText("جاري الفحص...")
        self._progress_bar.setValue(0)

        self._diag_worker = DiagnosticWorker()
        self._diag_worker.progress.connect(self._progress_bar.setValue)
        self._diag_worker.done.connect(self._on_diag_done)
        self._diag_worker.start()

    def _on_diag_done(self, results: dict) -> None:
        self._run_btn.setEnabled(True)
        self._run_btn.setText("تشغيل فحص شامل")

        score = results.get("health_score", 0)
        self._health_ring.set_value(score)

        if score >= 80:
            self._score_label.setText("النظام في حالة جيدة ✅")
            self._score_label.setStyleSheet(f"color: {STATUS_HEALTHY}; font-size: 15px; font-weight: bold;")
        elif score >= 50:
            self._score_label.setText("النظام يحتاج انتباه ⚠️")
            self._score_label.setStyleSheet(f"color: {STATUS_WARNING}; font-size: 15px; font-weight: bold;")
        else:
            self._score_label.setText("النظام بحاجة لصيانة 🔴")
            self._score_label.setStyleSheet(f"color: {STATUS_CRITICAL}; font-size: 15px; font-weight: bold;")

        # Clear old issues
        while self._issues_layout.count():
            item = self._issues_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        issues = results.get("issues", [])
        if issues:
            for issue in issues:
                severity = issue.get("severity", "warning")
                msg = issue.get("message", "")
                badge = StatusBadge(msg, severity)
                self._issues_layout.addWidget(badge)
        else:
            lbl = QLabel("لا توجد مشاكل مكتشفة ✅")
            lbl.setStyleSheet(f"color: {STATUS_HEALTHY}; font-size: 13px;")
            self._issues_layout.addWidget(lbl)

        # Check results
        checks = results.get("checks", {})
        row = 0
        for check_name, check_result in checks.items():
            if check_name not in self._result_widgets:
                name_lbl = QLabel(check_name)
                name_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
                self._results_grid.addWidget(name_lbl, row, 0)

                status = "healthy" if check_result.get("passed", False) else "critical"
                badge = StatusBadge("نجاح" if check_result.get("passed") else "فشل", status)
                self._result_widgets[check_name] = badge
                self._results_grid.addWidget(badge, row, 1)
            else:
                status = "healthy" if check_result.get("passed", False) else "critical"
                self._result_widgets[check_name].set_status(status)
                self._result_widgets[check_name].setText("نجاح" if check_result.get("passed") else "فشل")
            row += 1

        self._activity.log(f"اكتمل الفحص التشخيصي — مؤشر الصحة: {score}")

    def _export(self) -> None:
        export_data({"page": "diiagnostics"}, filename_stem="diagnostics_export", fmt="json")
