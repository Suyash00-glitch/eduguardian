"""
Centralized logging configuration for EduGuardian AI Chatbot.

Provides structured logging setup and safety filters to ensure
sensitive data (passwords, JWT tokens, API keys) are never logged.
"""
from __future__ import annotations

import logging
import re
import sys

# Regex pattern to identify and redact sensitive values in log messages
_SENSITIVE_PATTERNS = [
    re.compile(r"(bearer\s+)[a-zA-Z0-9\-_.]+", re.IGNORECASE),
    re.compile(r"(password['\":\s=]+)[^\s,}\"']+", re.IGNORECASE),
    re.compile(r"(api[-_]?key['\":\s=]+)[^\s,}\"']+", re.IGNORECASE),
    re.compile(r"(secret['\":\s=]+)[^\s,}\"']+", re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    """Logging filter that scrubs tokens, passwords, and API keys from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern in _SENSITIVE_PATTERNS:
                msg = pattern.sub(r"\1[REDACTED]", msg)
            record.msg = msg
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configures root logger with clean formatting and sensitive data scrubbing."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
