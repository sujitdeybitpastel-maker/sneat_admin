"""Centralized logging configuration for the application.

Every log line includes a %(req_hash)s field — the MD5 request hash.
Inside a request context it shows the unique hash for that request;
outside a request context (startup, background jobs) it shows '--------'.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from app.request_hash import RequestHashFilter


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application-wide logging to terminal (stdout) and file."""
    log_format = (
        "[%(asctime)s] %(levelname)-8s [%(req_hash)s] %(name)-30s | %(funcName)s:%(lineno)d | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    hash_filter = RequestHashFilter()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Remove any existing filters to avoid duplicates
    for f in root_logger.filters[:]:
        root_logger.removeFilter(f)

    # Attach the filter at root level (catches most loggers)
    root_logger.addFilter(hash_filter)

    # Console handler — all logs go to terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    # Also attach filter directly to the handler so it runs even when the
    # root-level filter is bypassed (third-party libs, threading, etc.)
    console_handler.addFilter(hash_filter)
    root_logger.addHandler(console_handler)

    # File handler — persist logs to file
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    file_handler.addFilter(hash_filter)
    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
