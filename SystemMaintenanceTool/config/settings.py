"""Central configuration for System Maintenance Tool Professional.

All magic numbers and defaults live here.
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports_output"
ICONS_DIR = ASSETS_DIR / "icons"
FONTS_DIR = ASSETS_DIR / "fonts"
IMAGES_DIR = ASSETS_DIR / "images"

# ── Application ───────────────────────────────────────────────────────────
APP_NAME = "System Maintenance Tool Professional"
APP_NAME_AR = "أداة صيانة النظام الاحترافية"
APP_VERSION = "1.0.0"
APP_ORG = "SMT Professional"

# ── Window Defaults ───────────────────────────────────────────────────────
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
MIN_WIDTH = 1024
MIN_HEIGHT = 600

# ── Theme / Appearance ────────────────────────────────────────────────────
THEME_DARK = "dark"
THEME_LIGHT = "light"
DEFAULT_THEME = THEME_DARK

FONT_FAMILY_AR = "Segoe UI"
FONT_FAMILY_EN = "Segoe UI"
FONT_SIZE_DEFAULT = 14
FONT_SIZE_SMALL = 12
FONT_SIZE_LARGE = 16
FONT_SIZE_TITLE = 22
FONT_SIZE_HEADER = 18

# ── Monitoring ────────────────────────────────────────────────────────────
DEFAULT_REFRESH_INTERVAL_MS = 2000        # 2 seconds
MIN_REFRESH_INTERVAL_MS = 500
MAX_REFRESH_INTERVAL_MS = 10000
CHART_HISTORY_SECONDS = 60
CHART_POINTS = 60
PROCESS_REFRESH_MS = 3000
SERVICE_REFRESH_MS = 10000
NETWORK_REFRESH_MS = 2000

# ── Health Score ───────────────────────────────────────────────────────────
HEALTH_WEIGHT_CPU = 0.25
HEALTH_WEIGHT_RAM = 0.25
HEALTH_WEIGHT_DISK = 0.20
HEALTH_WEIGHT_NETWORK = 0.10
HEALTH_WEIGHT_SECURITY = 0.15
HEALTH_WEIGHT_TEMPS = 0.05

# ── Alerts / Notifications ────────────────────────────────────────────────
CPU_ALERT_THRESHOLD = 90
RAM_ALERT_THRESHOLD = 90
DISK_ALERT_THRESHOLD = 95
DISK_SPACE_WARNING_GB = 10
TEMP_ALERT_THRESHOLD = 85

# ── Export ─────────────────────────────────────────────────────────────────
EXPORT_FORMATS = ["txt", "json", "csv", "html"]

# ── Logging ───────────────────────────────────────────────────────────────
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── CMD Center ────────────────────────────────────────────────────────────
CMD_MAX_HISTORY = 200
CMD_MAX_OUTPUT_CHARS = 100_000

# ── Security ─────────────────────────────────────────────────────────────
REQUIRE_CONFIRMATION_DESTRUCTIVE = True
REQUIRE_ADMIN_FOR_SYSTEM_OPS = True

# ── Windows Compatibility ────────────────────────────────────────────────
SUPPORTED_WINDOWS = ["10", "11"]
