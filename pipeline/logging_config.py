"""Structured logging configuration for the pipeline.

Provides JSON-formatted log output to stdout and suppresses
noisy third-party libraries at WARNING level.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


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


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured JSON logging for the 'pipeline' namespace.

    Args:
        level: Minimum log level for pipeline loggers.

    Returns:
        The configured 'pipeline' root logger.
    """
    # Configure pipeline namespace
    pipeline_logger = logging.getLogger("pipeline")
    pipeline_logger.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if not pipeline_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        pipeline_logger.addHandler(handler)

    # Suppress noisy libraries
    for lib_name in _NOISY_LIBRARIES:
        logging.getLogger(lib_name).setLevel(logging.WARNING)

    return pipeline_logger
