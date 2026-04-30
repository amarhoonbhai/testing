"""
Structured logging with sensitive data sanitization.

Creates rotating file handlers for service logs and errors.
Automatically strips phone numbers, OTPs, and session strings from output.
"""

import os
import re
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")


class SensitiveDataFilter(logging.Filter):
    """Filter that redacts sensitive information from log records."""

    # Patterns to redact
    PATTERNS = [
        # Phone numbers (international format)
        (re.compile(r"\+\d{10,15}"), "[PHONE_REDACTED]"),
        # OTP codes (4-6 digit sequences that look like codes)
        (re.compile(r"\b\d{5,6}\b"), "[CODE_REDACTED]"),
        # Session strings (long base64-like strings)
        (re.compile(r"[A-Za-z0-9+/=]{50,}"), "[SESSION_REDACTED]"),
        # Fernet encrypted strings
        (re.compile(r"gAAAAA[A-Za-z0-9_-]+={0,2}"), "[ENCRYPTED_REDACTED]"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


def setup_logging(
    service_name: str = "kurup_ads",
    *,
    level: int = logging.INFO,
    console: bool = True,
) -> logging.Logger:
    """
    Configure structured logging for the application.

    Creates:
      - logs/{service_name}.log   (all INFO+ messages, 10 MB rotating × 5)
      - logs/errors.log           (ERROR+ shared)
      - Console handler           (if console=True)
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if root.handlers:
        return root

    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()

    # ── Service-specific file handler
    service_fh = RotatingFileHandler(
        os.path.join(LOG_DIR, f"{service_name}.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    service_fh.setLevel(level)
    service_fh.setFormatter(fmt)
    service_fh.addFilter(sensitive_filter)
    root.addHandler(service_fh)

    # ── Shared error log
    error_fh = RotatingFileHandler(
        os.path.join(LOG_DIR, "errors.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_fh.setLevel(logging.ERROR)
    error_fh.setFormatter(fmt)
    error_fh.addFilter(sensitive_filter)
    root.addHandler(error_fh)

    # ── Console handler
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(fmt)
        ch.addFilter(sensitive_filter)
        root.addHandler(ch)

    # Silence noisy third-party loggers
    for noisy in (
        "telethon", "telethon.network", "telethon.crypto",
        "telethon.extensions", "httpx", "asyncio",
        "httpcore", "hpack",
    ):
        logging.getLogger(noisy).setLevel(logging.ERROR)

    return root
