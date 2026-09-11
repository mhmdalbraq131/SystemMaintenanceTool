"""Centralized logging configuration with rotation.

Creates three log files:
  - app.log        : General application flow
  - errors.log     : Errors and exceptions only
  - operations.log : User-initiated operations
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import (
    LOGS_DIR,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
)


def setup_logging() -> None:
    """Initialize all loggers."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # ── Root / app logger ────────────────────────────────────────────────
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG)

    _app_handler = RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    _app_handler.setFormatter(formatter)
    app_logger.addHandler(_app_handler)

    # Also stream to console during development
    _console = logging.StreamHandler(sys.stdout)
    _console.setFormatter(formatter)
    _console.setLevel(logging.INFO)
    app_logger.addHandler(_console)

    # ── Errors logger ─────────────────────────────────────────────────────
    err_logger = logging.getLogger("errors")
    err_logger.setLevel(logging.ERROR)

    _err_handler = RotatingFileHandler(
        LOGS_DIR / "errors.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    _err_handler.setFormatter(formatter)
    err_logger.addHandler(_err_handler)

    # ── Operations logger ────────────────────────────────────────────────
    ops_logger = logging.getLogger("operations")
    ops_logger.setLevel(logging.INFO)

    _ops_handler = RotatingFileHandler(
        LOGS_DIR / "operations.log",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    _ops_handler.setFormatter(formatter)
    ops_logger.addHandler(_ops_handler)


def get_app_logger() -> logging.Logger:
    return logging.getLogger("app")


def get_error_logger() -> logging.Logger:
    return logging.getLogger("errors")


def get_operations_logger() -> logging.Logger:
    return logging.getLogger("operations")
