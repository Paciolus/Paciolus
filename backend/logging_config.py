"""
Paciolus Logging Configuration

Structured logging infrastructure with request ID correlation.
- Development: human-readable format with colors
- Production: JSON format for log aggregation
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

from config import DEBUG, ENV_MODE

# Context variable for request ID correlation
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Inject request_id from contextvars into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data
        return json.dumps(log_entry)


class DevFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | [%(request_id)s] %(message)s"

    def __init__(self) -> None:
        super().__init__(self.FORMAT, datefmt="%H:%M:%S")


def setup_logging() -> None:
    """Configure application-wide logging.

    Call once at startup before any loggers are used.
    """
    root_logger = logging.getLogger()

    # Clear any existing handlers (prevents duplicate logs on reload)
    root_logger.handlers.clear()

    # Set root level based on environment
    root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if ENV_MODE == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(DevFormatter())

    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)

    # Confirm logging is active
    logger = logging.getLogger("paciolus.startup")
    logger.info("Logging initialized (env=%s, level=%s)",
                ENV_MODE, "DEBUG" if DEBUG else "INFO")
