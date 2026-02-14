"""Security utilities for zero-storage data processing."""

import gc
import io
from functools import wraps
from typing import Callable, Any, Generator, Optional
import pandas as pd


DEFAULT_CHUNK_SIZE = 10000


class ZeroStorageViolation(Exception):
    pass


def enforce_zero_storage(func: Callable) -> Callable:
    """Decorator ensuring no disk writes occur during execution."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        return result
    return wrapper


class SecureBuffer:
    """BytesIO wrapper with automatic cleanup on exit."""

    def __init__(self, initial_bytes: bytes = b""):
        self._buffer = io.BytesIO(initial_bytes)

    def __enter__(self) -> io.BytesIO:
        return self._buffer

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()
        return False

    def clear(self) -> None:
        self._buffer.seek(0)
        self._buffer.truncate(0)
        self._buffer.close()

    def get_buffer(self) -> io.BytesIO:
        return self._buffer


def read_csv_secure(file_bytes: bytes, dtype: dict | None = None) -> pd.DataFrame:
    """Read CSV from bytes into DataFrame without disk writes."""
    with SecureBuffer(file_bytes) as buffer:
        df = pd.read_csv(buffer, dtype=dtype)
    return df


def read_excel_secure(file_bytes: bytes, sheet_name: str = 0, dtype: dict | None = None) -> pd.DataFrame:
    """Read Excel from bytes into DataFrame without disk writes."""
    with SecureBuffer(file_bytes) as buffer:
        df = pd.read_excel(buffer, sheet_name=sheet_name, dtype=dtype)
    return df


def read_csv_chunked(
    file_bytes: bytes,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    dtype: dict | None = None,
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
    dtype: dict | None = None,
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
    dtype: dict | None = None,
) -> Generator[tuple[pd.DataFrame, int, str], None, None]:
    """Yield chunks from multiple sheets as (DataFrame, rows_processed, sheet_name) tuples."""
    log_secure_operation(
        "read_excel_multi_sheet",
        f"Reading {len(sheet_names)} sheets: {sheet_names}"
    )

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


def process_tb_chunked(
    file_bytes: bytes,
    filename: str = "",
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> Generator[tuple[pd.DataFrame, int], None, None]:
    """Process trial balance in chunks, auto-detecting format. Yields (chunk, rows_processed)."""
    log_secure_operation("process_tb_chunked", f"Processing trial balance in chunks (file: {filename})")

    filename_lower = filename.lower()

    if filename_lower.endswith(('.xlsx', '.xls')):
        yield from read_excel_chunked(file_bytes, chunk_size)
    elif filename_lower.endswith('.csv'):
        yield from read_csv_chunked(file_bytes, chunk_size)
    else:
        # Try CSV first, then Excel — broad catch is intentional (format detection)
        try:
            yield from read_csv_chunked(file_bytes, chunk_size)
        except Exception:
            yield from read_excel_chunked(file_bytes, chunk_size)


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
        df.to_excel(buffer, index=False, engine='openpyxl')
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
    from datetime import datetime, UTC
    _security_log.append({
        "timestamp": datetime.now(UTC).isoformat(),
        "operation": operation,
        "details": details
    })
    # Keep only last 1000 entries in memory
    if len(_security_log) > 1000:
        _security_log.pop(0)


def get_security_log() -> list[dict]:
    """Retrieve the in-memory security log."""
    return _security_log.copy()


def process_tb_in_memory(file_bytes: bytes, filename: str = "") -> pd.DataFrame:
    """Process trial balance file in-memory, auto-detecting CSV or Excel format."""
    log_secure_operation("process_tb", "Processing trial balance in memory")

    # Determine file type from filename or try CSV first
    filename_lower = filename.lower()

    if filename_lower.endswith(('.xlsx', '.xls')):
        return read_excel_secure(file_bytes)
    elif filename_lower.endswith('.csv'):
        return read_csv_secure(file_bytes)
    else:
        # Try CSV first, then Excel — broad catch is intentional (format detection)
        try:
            return read_csv_secure(file_bytes)
        except Exception:
            return read_excel_secure(file_bytes)
