"""Application configuration manager with persistence.

Saves/loads user preferences (theme, refresh rate, notifications, etc.).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

from config.settings import (
    CONFIG_DIR,
    DEFAULT_THEME,
    FONT_SIZE_DEFAULT,
    DEFAULT_REFRESH_INTERVAL_MS,
    CHART_HISTORY_SECONDS,
)


@dataclass
class AppConfig:
    """Persisted application settings."""
    theme: str = DEFAULT_THEME
    font_size: int = FONT_SIZE_DEFAULT
    density: str = "default"  # default / compact / comfortable
    refresh_interval_ms: int = DEFAULT_REFRESH_INTERVAL_MS
    chart_history_seconds: int = CHART_HISTORY_SECONDS
    auto_refresh: bool = True
    require_confirmation: bool = True
    admin_operations: bool = True
    notifications_high_cpu: bool = True
    notifications_high_ram: bool = True
    notifications_low_disk: bool = True
    notifications_defender: bool = True
    notifications_firewall: bool = True
    notifications_network: bool = True
    export_default_format: str = "json"
    start_with_windows: bool = False
    language: str = "ar"


_config_path = CONFIG_DIR / "user_config.json"
_current_config: AppConfig | None = None


def load_config() -> AppConfig:
    """Load config from disk or return defaults."""
    global _current_config
    if _current_config is not None:
        return _current_config

    if _config_path.exists():
        try:
            data = json.loads(_config_path.read_text(encoding="utf-8"))
            _current_config = AppConfig(**{k: v for k, v in data.items() if k in AppConfig.__dataclass_fields__})
        except Exception:
            _current_config = AppConfig()
    else:
        _current_config = AppConfig()

    return _current_config


def save_config() -> bool:
    """Save current config to disk."""
    global _current_config
    if _current_config is None:
        return False

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        _config_path.write_text(
            json.dumps(asdict(_current_config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def update_config(**kwargs) -> AppConfig:
    """Update config fields and save."""
    global _current_config
    config = load_config()
    for k, v in kwargs.items():
        if hasattr(config, k):
            setattr(config, k, v)
    save_config()
    return config


def get_config() -> AppConfig:
    """Get current config (load if needed)."""
    return load_config()
