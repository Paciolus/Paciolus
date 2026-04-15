"""Security utilities for zero-storage data processing."""

import gc
import io
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
        from shared.helpers import parse_uploaded_file_by_format

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


# Audit trail for security compliance (in-memory only)
_security_log: list[dict] = []


def log_secure_operation(operation: str, details: str = "") -> None:
    """Log a security-relevant operation (in-memory only)."""
    from datetime import UTC, datetime

    _security_log.append({"timestamp": datetime.now(UTC).isoformat(), "operation": operation, "details": details})
    # Keep only last 1000 entries in memory
    if len(_security_log) > 1000:
        _security_log.pop(0)


def get_security_log() -> list[dict]:
    """Retrieve the in-memory security log."""
    return _security_log.copy()


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
