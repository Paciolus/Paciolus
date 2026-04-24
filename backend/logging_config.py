"""
Paciolus Logging Configuration

Structured logging infrastructure with request ID correlation.
- Development: human-readable format with colors
- Production: JSON format for log aggregation

PII/Token Log Sanitization (Sprint 300):
- ``log_secure_operation()`` (security_utils.py) writes to a 1000-entry
  in-memory circular buffer only — no PII is persisted to disk via this path.
- All exception handlers use ``shared.log_sanitizer.sanitize_exception()``
  so raw ``str(e)`` (which may embed emails, API keys, or URLs from
  third-party libraries like SendGrid) is never recorded.
- Email addresses in log details use ``shared.log_sanitizer.mask_email()``
  (``abc***@domain.com`` format) instead of inline ``[:10]`` slicing.
- Token values use ``shared.log_sanitizer.token_fingerprint()``
  (first 8 chars + SHA-256 prefix) instead of raw values.
- Historical disk logs (if any from pre-Sprint 211 before structured
  logging was introduced) should be rotated/purged in production.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

from config import DEBUG, ENV_MODE, LOKI_ENABLED, LOKI_TOKEN, LOKI_URL, LOKI_USER

# Context variable for request ID correlation
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Inject request_id from contextvars into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


class TracebackRedactionFilter(logging.Filter):
    """Strip full tracebacks from log records, keeping only exception type.

    Prevents internal file paths, line numbers, and stack traces from
    appearing in production log aggregation systems. The exception type
    is appended to the log message for diagnostic value.

    Active by default in production (ENV_MODE=production).
    Opt out via REDACT_LOG_TRACEBACKS=false.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info and record.exc_info[0] is not None:
            exc_type = record.exc_info[0]
            record.msg = f"{record.msg} [{exc_type.__name__}]"
            record.exc_info = None
            record.exc_text = None
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
        # Strip full tracebacks from production logs to prevent internal file
        # paths leaking to log aggregation systems.  Enabled by default in
        # production; opt-out via REDACT_LOG_TRACEBACKS=false.
        import os

        if os.environ.get("REDACT_LOG_TRACEBACKS", "true").lower() != "false":
            handler.addFilter(TracebackRedactionFilter())
    else:
        handler.setFormatter(DevFormatter())

    root_logger.addHandler(handler)

    # Optional Loki HTTPS push handler (Sprint 716) — additive to stdout.
    if LOKI_ENABLED:
        _attach_loki_handler(root_logger)

    # Quiet noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    # Confirm logging is active
    logger = logging.getLogger("paciolus.startup")
    logger.info("Logging initialized (env=%s, level=%s)", ENV_MODE, "DEBUG" if DEBUG else "INFO")


def _attach_loki_handler(root_logger: logging.Logger) -> None:
    """Attach a Loki HTTPS push handler alongside the stdout handler.

    Structured JSON body identical to the stdout handler in production so
    Render's log tail and Loki present the same records.
    """
    import os

    from loki_handler import LokiHandler

    handler = LokiHandler(
        url=LOKI_URL,
        user=LOKI_USER,
        token=LOKI_TOKEN,
        labels={"service": "paciolus-api", "env": ENV_MODE},
    )
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JSONFormatter())
    if os.environ.get("REDACT_LOG_TRACEBACKS", "true").lower() != "false":
        handler.addFilter(TracebackRedactionFilter())
    root_logger.addHandler(handler)
