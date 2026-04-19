"""Structured logging configuration for the pipeline.

Provides JSON-formatted log output to stdout AND a daily-rotated file under
LOG_DIR (default ``/app/logs`` inside the container, bind-mounted to the
host's ``./logs/pipeline`` so entries survive container rebuilds).
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        # Include extra_data if provided via extra={"extra_data": {...}}
        extra_data = getattr(record, "extra_data", None)
        if extra_data and isinstance(extra_data, dict):
            log_entry["data"] = extra_data

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


# Libraries to suppress at WARNING level
_NOISY_LIBRARIES = [
    "pdfminer",
    "pdfminer.pdfpage",
    "pdfminer.pdfinterp",
    "pdfminer.converter",
    "pdfminer.pdfdocument",
    "pdfminer.pdfparser",
    "urllib3",
    "urllib3.connectionpool",
    "PIL",
    "chardet",
    "charset_normalizer",
]


def _resolve_log_dir() -> str:
    """Return a writable log directory, falling back to ./logs/pipeline locally."""
    candidate = os.environ.get("LOG_DIR", "/app/logs")
    try:
        os.makedirs(candidate, exist_ok=True)
        # Probe writability: open for append and immediately close.
        probe = os.path.join(candidate, ".write_probe")
        with open(probe, "a", encoding="utf-8"):
            pass
        try:
            os.remove(probe)
        except OSError:
            pass
        return candidate
    except (OSError, PermissionError):
        fallback = os.path.join(os.getcwd(), "logs", "pipeline")
        os.makedirs(fallback, exist_ok=True)
        return fallback


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured JSON logging for the 'pipeline' namespace.

    Attaches two handlers: a StreamHandler on stdout (captured by Docker)
    and a TimedRotatingFileHandler rotated at UTC midnight with 7 days
    of backups (``pipeline.log``, ``pipeline.log.2026-04-19`` etc.).

    Args:
        level: Minimum log level for pipeline loggers.

    Returns:
        The configured 'pipeline' root logger.
    """
    pipeline_logger = logging.getLogger("pipeline")
    pipeline_logger.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if not pipeline_logger.handlers:
        formatter = StructuredFormatter()

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        pipeline_logger.addHandler(stdout_handler)

        log_dir = _resolve_log_dir()
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "pipeline.log"),
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
            utc=True,
        )
        file_handler.setFormatter(formatter)
        pipeline_logger.addHandler(file_handler)

    # Suppress noisy libraries
    for lib_name in _NOISY_LIBRARIES:
        logging.getLogger(lib_name).setLevel(logging.WARNING)

    return pipeline_logger
