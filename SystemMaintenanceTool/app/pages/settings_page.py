"""Settings Page — App configuration: appearance, monitoring, security, notifications.

Arabic RTL, dark futuristic theme.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QMessageBox, QSlider,
)

from app.core.theme import (
    BG_DARKEST, BG_CARD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ACCENT,
    ACCENT_PRIMARY, SPACING_SM, SPACING_MD, SPACING_LG,
)
from app.core.logging_config import get_app_logger
from app.models.activity_log import ActivityLog
from app.widgets.custom_widgets import CardWidget
from app.core.config_manager import load_config, save_config, update_config, get_config, AppConfig


class SettingsPage(QWidget):
    """Application settings page."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._logger = get_app_logger()
        self._activity = ActivityLog()
        self._config = get_config()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: {BG_DARKEST};")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(SPACING_LG, SPACING_LG, SPACING_LG, SPACING_LG)
        layout.setSpacing(SPACING_LG)
        layout.setAlignment(Qt.AlignTop)

        # ── Appearance ───────────────────────────────────────────────────
        app_card = CardWidget("المظهر")
        app_inner = QVBoxLayout(app_card.get_layout())
        app_inner.setSpacing(SPACING_MD)

        # Theme
        theme_row = QHBoxLayout()
        theme_lbl = QLabel("السمة:")
        theme_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        theme_row.addWidget(theme_lbl)
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["داكن مستقبلي", "داكن كلاسيكي", "فاتح"])
        self._theme_combo.setFixedHeight(30)
        self._theme_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        theme_row.addWidget(self._theme_combo)
        theme_row.addStretch()
        app_inner.addLayout(theme_row)

        # Font size
        font_row = QHBoxLayout()
        font_lbl = QLabel("حجم الخط:")
        font_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        font_row.addWidget(font_lbl)
        self._font_spin = QSpinBox()
        self._font_spin.setRange(9, 20)
        self._font_spin.setValue(12)
        self._font_spin.setSuffix(" pt")
        self._font_spin.setFixedHeight(30)
        self._font_spin.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        font_row.addWidget(self._font_spin)
        font_row.addStretch()
        app_inner.addLayout(font_row)

        # Density
        density_row = QHBoxLayout()
        density_lbl = QLabel("كثافة الواجهة:")
        density_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        density_row.addWidget(density_lbl)
        self._density_combo = QComboBox()
        self._density_combo.addItems(["مريحة", "عادية", "مضغوطة"])
        self._density_combo.setCurrentIndex(1)
        self._density_combo.setFixedHeight(30)
        self._density_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        density_row.addWidget(self._density_combo)
        density_row.addStretch()
        app_inner.addLayout(density_row)

        layout.addWidget(app_card)

        # ── Monitoring ────────────────────────────────────────────────────
        mon_card = CardWidget("المراقبة")
        mon_inner = QVBoxLayout(mon_card.get_layout())
        mon_inner.setSpacing(SPACING_MD)

        # Refresh rate
        refresh_row = QHBoxLayout()
        refresh_lbl = QLabel("فترة التحديث (ثانية):")
        refresh_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        refresh_row.addWidget(refresh_lbl)
        self._refresh_spin = QSpinBox()
        self._refresh_spin.setRange(1, 30)
        self._refresh_spin.setValue(2)
        self._refresh_spin.setSuffix(" ث")
        self._refresh_spin.setFixedHeight(30)
        self._refresh_spin.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        refresh_row.addWidget(self._refresh_spin)
        refresh_row.addStretch()
        mon_inner.addLayout(refresh_row)

        # Auto refresh
        self._auto_refresh = QCheckBox("تحديث تلقائي للمراقبة")
        self._auto_refresh.setChecked(True)
        self._auto_refresh.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        mon_inner.addWidget(self._auto_refresh)

        # Chart history
        hist_row = QHBoxLayout()
        hist_lbl = QLabel("سجل الرسم البياني (نقاط):")
        hist_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        hist_row.addWidget(hist_lbl)
        self._history_spin = QSpinBox()
        self._history_spin.setRange(20, 300)
        self._history_spin.setValue(60)
        self._history_spin.setSingleStep(10)
        self._history_spin.setFixedHeight(30)
        self._history_spin.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        hist_row.addWidget(self._history_spin)
        hist_row.addStretch()
        mon_inner.addLayout(hist_row)

        layout.addWidget(mon_card)

        # ── Security ──────────────────────────────────────────────────────
        sec_card = CardWidget("الأمان")
        sec_inner = QVBoxLayout(sec_card.get_layout())
        sec_inner.setSpacing(SPACING_MD)

        self._confirm_dangerous = QCheckBox("تأكيد قبل العمليات الخطرة")
        self._confirm_dangerous.setChecked(True)
        self._confirm_dangerous.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        sec_inner.addWidget(self._confirm_dangerous)

        self._check_admin = QCheckBox("التحقق من صلاحيات المسؤول")
        self._check_admin.setChecked(True)
        self._check_admin.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        sec_inner.addWidget(self._check_admin)

        self._protect_system = QCheckBox("حماية ملفات النظام الحساسة")
        self._protect_system.setChecked(True)
        self._protect_system.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        sec_inner.addWidget(self._protect_system)

        layout.addWidget(sec_card)

        # ── Notifications ──────────────────────────────────────────────────
        notif_card = CardWidget("الإشعارات")
        notif_inner = QVBoxLayout(notif_card.get_layout())
        notif_inner.setSpacing(SPACING_SM)

        self._notif_cpu = QCheckBox("تنبيهات استخدام المعالج")
        self._notif_cpu.setChecked(True)
        self._notif_cpu.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        notif_inner.addWidget(self._notif_cpu)

        self._notif_ram = QCheckBox("تنبيهات الذاكرة")
        self._notif_ram.setChecked(True)
        self._notif_ram.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        notif_inner.addWidget(self._notif_ram)

        self._notif_disk = QCheckBox("تنبيهات التخزين")
        self._notif_disk.setChecked(True)
        self._notif_disk.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        notif_inner.addWidget(self._notif_disk)

        self._notif_security = QCheckBox("تنبيهات الأمان")
        self._notif_security.setChecked(True)
        self._notif_security.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        notif_inner.addWidget(self._notif_security)

        # Alert thresholds
        thresh_row = QHBoxLayout()
        thresh_lbl = QLabel("عتبة التنبيه (المعالج/الذاكرة %):")
        thresh_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        thresh_row.addWidget(thresh_lbl)
        self._thresh_slider = QSlider(Qt.Horizontal)
        self._thresh_slider.setRange(50, 99)
        self._thresh_slider.setValue(80)
        self._thresh_slider.setStyleSheet(f"QSlider::groove:horizontal {{ background: {BG_CARD}; height: 6px; border-radius: 3px; }} QSlider::handle:horizontal {{ background: {ACCENT_PRIMARY}; width: 16px; margin: -5px 0; border-radius: 8px; }}")
        thresh_row.addWidget(self._thresh_slider, stretch=1)
        self._thresh_value = QLabel("80%")
        self._thresh_value.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: 13px; font-weight: bold;")
        thresh_row.addWidget(self._thresh_value)
        self._thresh_slider.valueChanged.connect(lambda v: self._thresh_value.setText(f"{v}%"))
        notif_inner.addLayout(thresh_row)

        layout.addWidget(notif_card)

        # ── Export Defaults ────────────────────────────────────────────────
        export_card = CardWidget("التصدير")
        export_inner = QVBoxLayout(export_card.get_layout())
        export_inner.setSpacing(SPACING_MD)

        export_row = QHBoxLayout()
        export_lbl = QLabel("صيغة التصدير الافتراضية:")
        export_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        export_row.addWidget(export_lbl)
        self._export_combo = QComboBox()
        self._export_combo.addItems(["JSON", "CSV", "TXT", "HTML"])
        self._export_combo.setFixedHeight(30)
        self._export_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        export_row.addWidget(self._export_combo)
        export_row.addStretch()
        export_inner.addLayout(export_row)

        layout.addWidget(export_card)

        # ── Startup ───────────────────────────────────────────────────────
        startup_card = CardWidget("بدء التشغيل")
        startup_inner = QVBoxLayout(startup_card.get_layout())
        startup_inner.setSpacing(SPACING_MD)

        self._start_with_windows = QCheckBox("تشغيل مع بدء تشغيل ويندوز")
        self._start_with_windows.setChecked(False)
        self._start_with_windows.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        startup_inner.addWidget(self._start_with_windows)

        self._start_minimized = QCheckBox("بدء في شريط المهام")
        self._start_minimized.setChecked(False)
        self._start_minimized.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        startup_inner.addWidget(self._start_minimized)

        layout.addWidget(startup_card)

        # ── Language ──────────────────────────────────────────────────────
        lang_card = CardWidget("اللغة")
        lang_inner = QVBoxLayout(lang_card.get_layout())
        lang_inner.setSpacing(SPACING_MD)

        lang_row = QHBoxLayout()
        lang_lbl = QLabel("لغة الواجهة:")
        lang_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        lang_row.addWidget(lang_lbl)
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["العربية", "الإنجليزية"])
        self._lang_combo.setFixedHeight(30)
        self._lang_combo.setStyleSheet(f"color: {TEXT_PRIMARY}; background: {BG_CARD}; border: 1px solid #3a3f4b; border-radius: 4px; padding: 4px 8px;")
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()
        lang_inner.addLayout(lang_row)

        layout.addWidget(lang_card)

        # ── Action Buttons ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_MD)

        save_btn = QPushButton("حفظ الإعدادات")
        save_btn.setObjectName("btnAccent")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setMinimumHeight(38)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)

        reset_btn = QPushButton("استعادة الافتراضي")
        reset_btn.setObjectName("btnOutline")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setMinimumHeight(38)
        reset_btn.clicked.connect(self._reset_settings)
        btn_row.addWidget(reset_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _load_settings(self) -> None:
        cfg = load_config()
        self._theme_combo.setCurrentIndex({"dark": 0, "dark_classic": 1, "light": 2}.get(cfg.theme, 0))
        self._font_spin.setValue(cfg.font_size)
        self._density_combo.setCurrentIndex({"comfortable": 0, "default": 1, "compact": 2}.get(cfg.density, 1))
        self._refresh_spin.setValue(cfg.refresh_interval_ms // 1000)
        self._auto_refresh.setChecked(cfg.auto_refresh)
        self._history_spin.setValue(cfg.chart_history_seconds)
        self._confirm_dangerous.setChecked(cfg.require_confirmation)
        self._check_admin.setChecked(cfg.admin_operations)
        self._protect_system.setChecked(True)
        self._notif_cpu.setChecked(cfg.notifications_high_cpu)
        self._notif_ram.setChecked(cfg.notifications_high_ram)
        self._notif_disk.setChecked(cfg.notifications_low_disk)
        self._notif_security.setChecked(cfg.notifications_defender)
        self._thresh_slider.setValue(80)  # threshold stored separately
        self._export_combo.setCurrentIndex({"json": 0, "csv": 1, "txt": 2, "html": 3}.get(cfg.export_default_format, 0))
        self._start_with_windows.setChecked(cfg.start_with_windows)
        self._start_minimized.setChecked(False)
        self._lang_combo.setCurrentIndex(0 if cfg.language == "ar" else 1)

    def _save_settings(self) -> None:
        theme_map = {0: "dark_futuristic", 1: "dark_classic", 2: "light"}
        fmt_map = {0: "json", 1: "csv", 2: "txt", 3: "html"}
        lang_map = {0: "ar", 1: "en"}

        update_config(
            theme=theme_map.get(self._theme_combo.currentIndex(), "dark"),
            font_size=self._font_spin.value(),
            density=density_map.get(self._density_combo.currentIndex(), "default"),
            refresh_interval_ms=self._refresh_spin.value() * 1000,
            auto_refresh=self._auto_refresh.isChecked(),
            chart_history_seconds=self._history_spin.value(),
            require_confirmation=self._confirm_dangerous.isChecked(),
            admin_operations=self._check_admin.isChecked(),
            notifications_high_cpu=self._notif_cpu.isChecked(),
            notifications_high_ram=self._notif_ram.isChecked(),
            notifications_low_disk=self._notif_disk.isChecked(),
            notifications_defender=self._notif_security.isChecked(),
            export_default_format=fmt_map.get(self._export_combo.currentIndex(), "json"),
            start_with_windows=self._start_with_windows.isChecked(),
            language=lang_map.get(self._lang_combo.currentIndex(), "ar"),
        )
        self._activity.log("تم حفظ إعدادات التطبيق")
        QMessageBox.information(self, "تم", "تم حفظ الإعدادات بنجاح ✅")

    def _reset_settings(self) -> None:
        confirm = QMessageBox.question(
            self, "تأكيد", "هل تريد استعادة الإعدادات الافتراضية؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            load_config()  # reload defaults
            self._load_settings()
            self._activity.log("تم استعادة الإعدادات الافتراضية")
