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
- Sprint 879 (DH-03): every record is scrubbed where it is created
  (``install_safe_log_records``) — exception objects become type names and
  tracebacks become type + innermost frame, at every level and in every
  environment. Upload routes and parsers log fixed event names, exception type
  names and counts only — never filenames, cell values or file metadata.
"""

import json
import logging
import sys
from collections.abc import Mapping
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from config import DEBUG, ENV_MODE, LOKI_ENABLED, LOKI_TOKEN, LOKI_URL, LOKI_USER

# Context variable for request ID correlation
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Inject request_id from contextvars into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def _exception_summary(exc: BaseException) -> str:
    """Type name and the innermost frame — never the exception's message.

    Exception messages routinely quote the input that broke them ("could not
    convert 'Acme Holdings 4,210.55' to float"), so the text is never logged.
    """
    frame = ""
    tb = exc.__traceback__
    while tb is not None and tb.tb_next is not None:
        tb = tb.tb_next
    if tb is not None:
        code = tb.tb_frame.f_code
        module = tb.tb_frame.f_globals.get("__name__", "?")
        frame = f" at {module}:{code.co_name}:{tb.tb_lineno}"
    return f"{type(exc).__name__}{frame}"


def _scrub_value(value: object) -> object:
    if isinstance(value, BaseException):
        return f"[{type(value).__name__}]"
    return value


def _scrub_record(record: logging.LogRecord) -> None:
    """Sprint 879 (DH-03): applied to every record when it is created."""
    if isinstance(record.msg, BaseException):
        record.msg = f"[{type(record.msg).__name__}]"
    elif not isinstance(record.msg, str):
        record.msg = f"[{type(record.msg).__name__}]"
        record.args = None
    if isinstance(record.args, tuple):
        record.args = tuple(_scrub_value(a) for a in record.args)
    elif isinstance(record.args, Mapping):
        record.args = {k: _scrub_value(v) for k, v in record.args.items()}
    if record.exc_info:
        # Keep exc_info (Sentry reads it for stack frames; its scrubber blanks the
        # message) but pre-fill exc_text: logging.Formatter renders a pre-set
        # exc_text instead of formatting the traceback, so no log line carries
        # the exception message.
        exc = record.exc_info[1] if isinstance(record.exc_info, tuple) else None
        if exc is None:
            record.exc_info = None
        else:
            record.exc_text = f"exception: {_exception_summary(exc)}"


def install_safe_log_records() -> None:
    """Scrub every log record where it is made (Sprint 879, DH-03).

    The data statement says uploads are not kept; a log line is kept. Handler
    filters only run on the handlers they are attached to, and Sentry's logging
    hook reads records before any handler — so the rule is enforced in the
    record factory, which every logger, level, handler and environment shares:

    - an exception object passed as the message or an argument becomes its type
      name; any other non-string message becomes its type name;
    - for ``exc_info`` (``logger.exception``, ``exc_info=True``) the rendered text
      is the type and the innermost frame, never the message or the traceback.
      ``exc_info`` itself stays on the record for Sentry, whose scrubber
      (``shared/sentry_scrubber.py``) removes the message and frame variables.

    Call sites must still log only fixed event names, type names and counts —
    a value formatted into a string before logging cannot be recognised here.
    Idempotent.
    """
    current = logging.getLogRecordFactory()
    if getattr(current, "_paciolus_safe", False):
        return

    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = current(*args, **kwargs)
        _scrub_record(record)
        return record

    factory._paciolus_safe = True  # type: ignore[attr-defined]
    logging.setLogRecordFactory(factory)


install_safe_log_records()


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
        if record.exc_text:
            log_entry["exception"] = record.exc_text
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
    install_safe_log_records()
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
    from loki_handler import LokiHandler

    handler = LokiHandler(
        url=LOKI_URL,
        user=LOKI_USER,
        token=LOKI_TOKEN,
        labels={"service": "paciolus-api", "env": ENV_MODE},
    )
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
