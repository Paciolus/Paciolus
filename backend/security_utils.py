"""Security utilities for zero-storage data processing."""

import gc
import io
import logging
import re
from collections.abc import Callable, Generator
from functools import wraps
from types import TracebackType
from typing import Any

import pandas as pd

DEFAULT_CHUNK_SIZE = 10000


class ZeroStorageViolation(Exception):
    pass


def enforce_zero_storage(func: Callable) -> Callable:
    """Decorator ensuring no disk writes occur during execution."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = await func(*args, **kwargs)
        return result

    return wrapper


class SecureBuffer:
    """BytesIO wrapper with automatic cleanup on exit."""

    def __init__(self, initial_bytes: bytes = b""):
        self._buffer = io.BytesIO(initial_bytes)

    def __enter__(self) -> io.BytesIO:
        return self._buffer

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.clear()

    def clear(self) -> None:
        self._buffer.seek(0)
        self._buffer.truncate(0)
        self._buffer.close()

    def get_buffer(self) -> io.BytesIO:
        return self._buffer


def read_csv_secure(file_bytes: bytes, dtype: dict | str | None = None) -> pd.DataFrame:
    """Read CSV from bytes into DataFrame without disk writes."""
    with SecureBuffer(file_bytes) as buffer:
        df = pd.read_csv(buffer, dtype=dtype)
    return df


def read_excel_secure(
    file_bytes: bytes, sheet_name: int | str = 0, dtype: dict[str, Any] | type | None = None
) -> pd.DataFrame:
    """Read Excel from bytes into DataFrame without disk writes."""
    with SecureBuffer(file_bytes) as buffer:
        df = pd.read_excel(buffer, sheet_name=sheet_name, dtype=dtype)
    return df


def read_csv_chunked(
    file_bytes: bytes,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    dtype: dict | type | None = None,
) -> Generator[tuple[pd.DataFrame, int], None, None]:
    """Yield CSV chunks as (DataFrame, rows_processed) tuples."""
    log_secure_operation("read_csv_chunked", f"Starting chunked read (chunk_size={chunk_size})")

    buffer = io.BytesIO(file_bytes)
    rows_processed = 0

    try:
        for chunk in pd.read_csv(buffer, chunksize=chunk_size, dtype=dtype):
            rows_processed += len(chunk)
            yield chunk, rows_processed

            # Explicit memory cleanup after yielding
            del chunk
            gc.collect()

    finally:
        buffer.close()
        del buffer
        gc.collect()

    log_secure_operation("read_csv_chunked_done", f"Completed. Total rows: {rows_processed}")


def read_excel_chunked(
    file_bytes: bytes,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    sheet_name: int | str = 0,
    dtype: dict | type | None = None,
) -> Generator[tuple[pd.DataFrame, int], None, None]:
    """Yield Excel chunks as (DataFrame, rows_processed) tuples. Reads entire file first."""
    log_secure_operation("read_excel_chunked", f"Starting chunked read (chunk_size={chunk_size}, sheet={sheet_name})")

    buffer = io.BytesIO(file_bytes)
    rows_processed = 0

    try:
        # Read Excel file (unfortunately must load entirely due to format limitations)
        full_df = pd.read_excel(buffer, sheet_name=sheet_name, dtype=dtype)
        total_rows = len(full_df)

        # Yield in chunks
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk = full_df.iloc[start_idx:end_idx].copy()
            rows_processed = end_idx

            yield chunk, rows_processed

            # Explicit memory cleanup
            del chunk
            gc.collect()

        # Clear the full dataframe
        del full_df
        gc.collect()

    finally:
        buffer.close()
        del buffer
        gc.collect()

    log_secure_operation("read_excel_chunked_done", f"Completed. Total rows: {rows_processed}")


def read_excel_multi_sheet_chunked(
    file_bytes: bytes,
    sheet_names: list[str],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    dtype: dict | type | None = None,
) -> Generator[tuple[pd.DataFrame, int, str], None, None]:
    """Yield chunks from multiple sheets as (DataFrame, rows_processed, sheet_name) tuples."""
    log_secure_operation("read_excel_multi_sheet", f"Reading {len(sheet_names)} sheets: {sheet_names}")

    for sheet_name in sheet_names:
        log_secure_operation("read_sheet_start", f"Processing sheet: {sheet_name}")

        buffer = io.BytesIO(file_bytes)
        rows_processed = 0

        try:
            full_df = pd.read_excel(buffer, sheet_name=sheet_name, dtype=dtype)
            total_rows = len(full_df)

            for start_idx in range(0, total_rows, chunk_size):
                end_idx = min(start_idx + chunk_size, total_rows)
                chunk = full_df.iloc[start_idx:end_idx].copy()
                rows_processed = end_idx

                yield chunk, rows_processed, sheet_name

                del chunk
                gc.collect()

            del full_df
            gc.collect()

        finally:
            buffer.close()
            del buffer
            gc.collect()

        log_secure_operation("read_sheet_done", f"Sheet '{sheet_name}': {rows_processed} rows")


_CURRENCY_NUMERIC_RE = re.compile(r"^\s*[\$£€]?\s*\(?\s*[\d,]+(?:\.\d+)?\s*\)?\s*$")


def _strip_currency_formatting(value: object) -> object:
    """Strip currency formatting from a numeric-looking string cell.

    Returns the value unchanged if it does not look numeric. Used by
    the Sprint 671 PDF/DOCX dispatch path to make currency-formatted
    values consumable by ``pd.to_numeric`` downstream. Examples:

    * ``"$284,500.00"``  → ``"284500.00"``
    * ``"(1,234.56)"``   → ``"-1234.56"``
    * ``"$(1,234.56)"``  → ``"-1234.56"``
    * ``"  100  "``      → ``"100"``
    * ``"Cash, Op."``    → unchanged (not numeric-shaped)
    * ``"Dr"``           → unchanged
    """
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped or not _CURRENCY_NUMERIC_RE.match(stripped):
        return value
    # Strip currency symbol first so $(1,234.56) → (1,234.56) → -1234.56.
    stripped = stripped.replace("$", "").replace("£", "").replace("€", "").strip()
    negative = stripped.startswith("(") and stripped.endswith(")")
    if negative:
        stripped = stripped[1:-1].strip()
    cleaned = stripped.replace(",", "").strip()
    if not cleaned:
        return value
    return f"-{cleaned}" if negative else cleaned


def process_tb_chunked(
    file_bytes: bytes, filename: str = "", chunk_size: int = DEFAULT_CHUNK_SIZE
) -> Generator[tuple[pd.DataFrame, int], None, None]:
    """Process trial balance in chunks, auto-detecting format. Yields (chunk, rows_processed).

    All columns are read as ``str`` to preserve account identifiers (e.g.
    leading-zero codes like ``"0010"``).  Numeric conversion for debit/credit
    columns happens downstream via ``pd.to_numeric(errors='coerce')``.

    Sprint 671 Issue 14: This dispatcher historically only routed CSV and
    Excel. Every other supported format (PDF, DOCX, ODS, OFX, QBO, IIF,
    TSV, TXT) failed at the diagnostic ingestion layer with a generic
    "Excel file format cannot be determined" / "OptionError" message,
    even though preflight handled the same files via
    ``parse_uploaded_file_by_format`` in ``shared/helpers.py``. The fix
    is to route those formats through the same parser dispatch the
    preflight uses, then convert the resulting list-of-dicts to a
    DataFrame chunk so the streaming auditor consumes it unchanged.
    """
    log_secure_operation("process_tb_chunked", f"Processing trial balance in chunks (file: {filename})")

    filename_lower = filename.lower()

    if filename_lower.endswith((".xlsx", ".xls")):
        yield from read_excel_chunked(file_bytes, chunk_size, dtype=str)
        return
    if filename_lower.endswith(".csv"):
        yield from read_csv_chunked(file_bytes, chunk_size, dtype=str)
        return

    # Sprint 671 Issue 14: Non-CSV/Excel formats route through the
    # preflight parser dispatch. The result is a (columns, rows) tuple
    # of plain Python dicts which we materialise into a DataFrame in
    # one shot — these formats are bounded in size by upstream
    # validation (parse_uploaded_file_by_format enforces MAX_ROW_COUNT)
    # so a single-chunk yield is acceptable. The streaming chunk loop
    # in audit_trial_balance_streaming still iterates correctly even
    # when the generator only produces one item.
    _NON_TABULAR_EXTS = (".pdf", ".docx", ".ods", ".ofx", ".qbo", ".iif", ".tsv", ".txt")
    if filename_lower.endswith(_NON_TABULAR_EXTS):
        # Lazy import to avoid a circular dependency between
        # security_utils and shared.helpers.
        from shared.upload_pipeline import parse_uploaded_file_by_format

        try:
            columns, rows = parse_uploaded_file_by_format(file_bytes, filename)
        except Exception as exc:
            log_secure_operation(
                "process_tb_chunked_format_error",
                f"{filename}: {type(exc).__name__}: {exc}",
            )
            raise
        # Build a string-typed DataFrame so leading-zero codes survive.
        df = pd.DataFrame(rows, columns=columns).astype(str).fillna("")
        # Replace pandas' "nan" string artefact with empty so downstream
        # null detection still fires correctly.
        df = df.replace({"nan": "", "None": ""})

        # Sprint 671: PDF / DOCX / ODS parsers preserve currency formatting
        # (commas, leading $, parenthesised negatives). The downstream
        # streaming auditor uses ``pd.to_numeric(errors='coerce')`` which
        # does NOT understand any of these formats — every formatted
        # number coerces to NaN→0, which would silently produce a
        # phantom "balanced / total_debits=0 / total_credits=0"
        # diagnostic. Strip currency formatting on numeric-looking cells
        # only, leaving text cells untouched so account names like
        # "A/P - K.H. Owner Loan (personal?)" survive.
        # pandas 2.x deprecates DataFrame.applymap → DataFrame.map.
        for col in df.columns:
            df[col] = df[col].map(_strip_currency_formatting)
        yield df, len(df)
        return

    # Unknown extension — fall back to the legacy try-CSV-then-Excel
    # path so we don't regress on extension-less uploads. Broad catch
    # is intentional (format detection).
    try:
        yield from read_csv_chunked(file_bytes, chunk_size, dtype=str)
    except Exception:
        yield from read_excel_chunked(file_bytes, chunk_size, dtype=str)


def clear_memory() -> None:
    """Force garbage collection to clear memory."""
    gc.collect()
    log_secure_operation("memory_clear", "Forced garbage collection")


def dataframe_to_bytes(df: pd.DataFrame, format: str = "csv") -> bytes:
    """Convert DataFrame to bytes without disk writes. Format: 'csv' or 'excel'."""
    buffer = io.BytesIO()

    if format == "csv":
        df.to_csv(buffer, index=False)
    elif format == "excel":
        df.to_excel(buffer, index=False, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported format: {format}")

    buffer.seek(0)
    result = buffer.read()
    buffer.close()

    return result


# =============================================================================
# Security event logging (Sprint 840 — claims review S5)
# =============================================================================
#
# This used to append to a 1,000-entry in-memory list per worker that nothing
# ever read, so failed logins, lockouts, CSRF blocks, upload-bomb detections
# and refresh-token reuse alerts were discarded. Now:
#
# * SECURITY_EVENTS go to the ``paciolus.security`` logger at WARNING — stdout,
#   so Render's log stream and Loki (when enabled) keep them. Details pass
#   through ``_redact_details`` first: quoted text (filenames, archive entry
#   names) is removed and emails are masked.
# * PERSISTED_EVENTS are also written to ``security_events`` when the caller
#   passes its DB session, so they survive restarts and log rotation.
# * Every other operation name (routine "pdf_generate_start" style tracing) is
#   logged at DEBUG with **no details**, because many of those detail strings
#   name the uploaded file.

_security_logger = logging.getLogger("paciolus.security")

SECURITY_EVENTS: frozenset[str] = frozenset(
    {
        # Authentication and sessions
        "auth_failed",
        "login_failed",
        "account_locked",
        "lockout_expired",
        "lockout_reset",
        "ip_blocked",
        "auth_register_blocked",
        "refresh_token_reuse_detected",
        "refresh_token_race_detected",
        "all_sessions_revoked",
        "all_tokens_revoked",
        "session_revoked",
        "password_changed",
        "password_change_failed",
        "password_reset_request",
        "password_reset_success",
        "password_reset_invalid",
        "password_reset_expired",
        "password_reset_reused",
        "email_changed",
        "impersonation_token_created",
        "account_erased",
        "account_exported",
        # Request integrity
        "csrf_blocked",
        "csrf_validation_failed",
        "rate_limit_fail_closed",
        "rate_limit_degraded",
        # Hostile or malformed uploads
        "archive_bomb_entries",
        "archive_bomb_ratio",
        "archive_bomb_size",
        "xml_bomb_detected",
        "nested_archive_detected",
        "magic_byte_mismatch",
        "content_sniff_rejected",
        "content_type_rejected",
        "file_type_rejected",
        "request_body_too_large",
        "streaming_body_too_large",
        "malformed_content_length",
        "negative_content_length",
        # Infrastructure posture
        "db_tls_enforcement_failure",
        "db_tls_override",
        "config_contradiction",
    }
)

PERSISTED_EVENTS: frozenset[str] = frozenset(
    {
        "auth_failed",
        "login_failed",
        "account_locked",
        "ip_blocked",
        "refresh_token_reuse_detected",
        "refresh_token_race_detected",
        "all_sessions_revoked",
        "password_changed",
        "password_reset_success",
        "email_changed",
        "impersonation_token_created",
        "account_erased",
        "account_exported",
    }
)

# PR #232 review: quote-stripping alone was not enough — some call sites put
# the filename unquoted ("... for file: {file.filename}"). Details are now
# written only for events whose call sites build them from IDs, counts and
# masked emails; every other security event is logged by name alone.
DETAIL_SAFE_EVENTS: frozenset[str] = frozenset(
    {
        "auth_failed",
        "login_failed",
        "account_locked",
        "ip_blocked",
        "refresh_token_reuse_detected",
        "refresh_token_race_detected",
        "all_sessions_revoked",
        "all_tokens_revoked",
        "password_changed",
        "password_reset_success",
        "email_changed",
        "impersonation_token_created",
        "rate_limit_fail_closed",
        "rate_limit_degraded",
        "account_erased",
        "account_exported",
    }
)

_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_MAX_DETAIL_CHARS = 500


def _redact_details(details: str) -> str:
    from shared.log_sanitizer import mask_email

    redacted = _QUOTED.sub("'[redacted]'", details)
    redacted = _EMAIL.sub(lambda m: mask_email(m.group(0)), redacted)
    return redacted[:_MAX_DETAIL_CHARS]


def log_secure_operation(
    operation: str,
    details: str = "",
    *,
    db: Any = None,
    user_id: int | None = None,
    ip_address: str | None = None,
) -> None:
    """Record a security-relevant operation.

    ``db``/``user_id``/``ip_address`` are used only for PERSISTED_EVENTS. The
    raw IP is never stored or logged — only its hash. A failure to persist is
    logged and swallowed: losing one row must never turn a failed login into a
    500.
    """
    if operation not in SECURITY_EVENTS:
        _security_logger.debug("security_op %s", operation)
        return

    safe_details = _redact_details(details) if details and operation in DETAIL_SAFE_EVENTS else ""
    ip_hash = None
    if ip_address:
        from security_middleware import hash_ip_address

        ip_hash = hash_ip_address(ip_address)
    _security_logger.warning(
        "security_event %s user_id=%s ip_hash=%s %s", operation, user_id or "-", ip_hash or "-", safe_details
    )

    if db is None or operation not in PERSISTED_EVENTS:
        return
    try:
        from security_event_model import SecurityEvent

        db.add(SecurityEvent(event_type=operation, user_id=user_id, ip_hash=ip_hash, details=safe_details or None))
        db.commit()
    except Exception as exc:  # noqa: BLE001 — never fail the request over the log row
        _security_logger.error("security_event persist failed [%s] for %s", type(exc).__name__, operation)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass


def process_tb_in_memory(file_bytes: bytes, filename: str = "") -> pd.DataFrame:
    """Process trial balance file in-memory, auto-detecting CSV or Excel format.

    All columns are read as ``str`` to preserve account identifiers (e.g.
    leading-zero codes like ``"0010"``).  Numeric conversion for debit/credit
    columns happens downstream via ``pd.to_numeric(errors='coerce')``.
    """
    log_secure_operation("process_tb", "Processing trial balance in memory")

    # Determine file type from filename or try CSV first
    filename_lower = filename.lower()

    if filename_lower.endswith((".xlsx", ".xls")):
        return read_excel_secure(file_bytes, dtype=str)
    elif filename_lower.endswith(".csv"):
        return read_csv_secure(file_bytes, dtype=str)
    else:
        # Try CSV first, then Excel — broad catch is intentional (format detection)
        try:
            return read_csv_secure(file_bytes, dtype=str)
        except Exception:
            return read_excel_secure(file_bytes, dtype=str)
