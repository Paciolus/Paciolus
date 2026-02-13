"""
Paciolus API — Shared Helper Functions
"""
import hashlib
import io
import json
from contextlib import contextmanager
from datetime import datetime, UTC
from typing import Optional

import pandas as pd
from fastapi import HTTPException, UploadFile, Depends, Path as PathParam
from sqlalchemy.orm import Session

from security_utils import log_secure_operation, clear_memory
from database import get_db
from models import User, Client
from auth import require_current_user
from client_manager import ClientManager
from flux_engine import FluxRisk
from recon_engine import RiskBand

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
MAX_FILE_SIZE_MB = 100
MAX_ROW_COUNT = 500_000
MAX_COL_COUNT = 1_000
MAX_CELL_LENGTH = 100_000

# Characters that trigger formula execution in spreadsheet software (CWE-1236)
_FORMULA_TRIGGERS = frozenset(("=", "+", "-", "@", "\t", "\r"))

ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",  # Many browsers send this for CSV
}

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def sanitize_csv_value(value) -> str:
    """Escape formula injection in CSV/Excel cell values (CWE-1236).

    Spreadsheet software interprets cells starting with =, +, -, @, tab, or CR
    as formulas. Prefixing with a single quote neutralizes this.
    """
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in _FORMULA_TRIGGERS:
        return "'" + s
    return s


async def validate_file_size(file: UploadFile) -> bytes:
    """Read uploaded file with size, content-type, and extension validation."""
    # Validate file extension
    filename = (file.filename or "").lower()
    import os
    ext = os.path.splitext(filename)[1]
    if ext and ext not in ALLOWED_EXTENSIONS:
        log_secure_operation(
            "file_type_rejected",
            f"Rejected file with extension: {ext}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file."
        )

    # Validate content type (lenient — many browsers misreport)
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        log_secure_operation(
            "content_type_rejected",
            f"Rejected content type: {content_type} for file: {file.filename}"
        )
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file."
        )

    # Read with size validation
    contents = bytearray()
    chunk_size = 1024 * 1024

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        contents.extend(chunk)

        if len(contents) > MAX_FILE_SIZE_BYTES:
            log_secure_operation(
                "file_size_exceeded",
                f"File {file.filename} exceeds {MAX_FILE_SIZE_MB}MB limit"
            )
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB. "
                       f"Please reduce file size or split into smaller files."
            )

    file_bytes = bytes(contents)

    # Check for empty file
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty. Please select a file with data."
        )

    return file_bytes


@contextmanager
def memory_cleanup():
    """Context manager guaranteeing gc.collect() after CPU-bound file processing.

    Replaces manual try/except/clear_memory() pairs in route handlers.
    Usage:
        with memory_cleanup():
            result = await asyncio.to_thread(_analyze)
            return result.to_dict()
    """
    try:
        yield
    finally:
        clear_memory()


def require_client(
    client_id: int = PathParam(..., description="The ID of the client"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
) -> Client:
    """Validate client ownership. Raises 404 if not found or not owned by user."""
    manager = ClientManager(db)
    client = manager.get_client(current_user.id, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def hash_filename(filename: str) -> str:
    """SHA-256 hash of filename for privacy-preserving storage."""
    return hashlib.sha256(filename.encode('utf-8')).hexdigest()


def get_filename_display(filename: str, max_length: int = 12) -> str:
    """Truncated filename preview for display."""
    if len(filename) <= max_length:
        return filename
    return filename[:max_length - 3] + "..."


def try_parse_risk(risk_str: str) -> FluxRisk:
    try:
        return FluxRisk(risk_str)
    except ValueError:
        return FluxRisk.LOW


def try_parse_risk_band(band_str: str) -> RiskBand:
    try:
        return RiskBand(band_str)
    except ValueError:
        return RiskBand.LOW


def parse_uploaded_file(
    file_bytes: bytes,
    filename: str,
    max_rows: int = MAX_ROW_COUNT,
) -> tuple[list[str], list[dict]]:
    """Parse CSV or Excel file bytes into column names and row dicts.

    Features:
    - CSV encoding fallback: UTF-8 → Latin-1
    - Row count protection (default 500K)
    - Zero data rows detection
    Caller must del result when done.
    """
    filename_lower = (filename or "").lower()

    if filename_lower.endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail="The Excel file could not be read. Please verify it is a valid .xlsx or .xls file."
            )
    else:
        # CSV with encoding fallback
        df = None
        for encoding in ("utf-8", "latin-1"):
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file appears to be empty or has no readable columns."
                )
            except pd.errors.ParserError:
                raise HTTPException(
                    status_code=400,
                    detail="The CSV file format is invalid. Please verify it is a properly formatted CSV file."
                )
        if df is None:
            raise HTTPException(
                status_code=400,
                detail="The file contains characters that could not be decoded. "
                       "Try saving the file as UTF-8 CSV."
            )

    # Row count protection
    if len(df) > max_rows:
        row_count = len(df)
        del df
        raise HTTPException(
            status_code=400,
            detail=f"The file contains {row_count:,} rows, which exceeds the maximum of "
                   f"{max_rows:,}. Please reduce the file size or split into smaller files."
        )

    # Column count protection
    if len(df.columns) > MAX_COL_COUNT:
        col_count = len(df.columns)
        del df
        raise HTTPException(
            status_code=400,
            detail=f"The file contains {col_count:,} columns, which exceeds the maximum of "
                   f"{MAX_COL_COUNT:,}. Please reduce the number of columns."
        )

    # Zero data rows check
    if len(df) == 0:
        del df
        raise HTTPException(
            status_code=400,
            detail="The file has column headers but contains no data rows. "
                   "Please upload a file with at least one row of data."
        )

    # Cell content length protection (prevent OOM from oversized string operations)
    for col in df.columns:
        if df[col].dtype == object:
            max_len = df[col].astype(str).str.len().max()
            if pd.notna(max_len) and max_len > MAX_CELL_LENGTH:
                del df
                raise HTTPException(
                    status_code=400,
                    detail=f"A cell in column '{col}' exceeds the maximum length of "
                           f"{MAX_CELL_LENGTH:,} characters. Please reduce cell content size."
                )

    # Preserve leading zeros in identifier columns (account codes, IDs)
    _IDENTIFIER_HINTS = {'account', 'acct', 'code', 'id', 'number', 'no', 'num', 'gl'}
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if any(hint in col_lower for hint in _IDENTIFIER_HINTS):
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].apply(
                    lambda x: str(int(x)) if pd.notna(x) and float(x) == int(float(x)) else (str(x) if pd.notna(x) else '')
                )

    column_names = list(df.columns.astype(str))
    rows = df.to_dict('records')
    del df
    return column_names, rows


def parse_json_list(raw_json: Optional[str], log_label: str) -> Optional[list]:
    """Parse optional JSON string into list. Returns None on invalid/missing input."""
    if not raw_json:
        return None
    try:
        result = json.loads(raw_json)
        if not isinstance(result, list):
            log_secure_operation(f"{log_label}_error", f"{log_label} must be a JSON array, ignoring")
            return None
        log_secure_operation(log_label, f"Received {len(result)} {log_label} items")
        return result
    except json.JSONDecodeError:
        log_secure_operation(f"{log_label}_error", f"Invalid JSON in {log_label}")
        return None


def parse_json_mapping(raw_json: Optional[str], log_label: str) -> Optional[dict[str, str]]:
    """Parse optional JSON string into dict. Returns None on invalid/missing input."""
    if not raw_json:
        return None
    try:
        mapping = json.loads(raw_json)
        log_secure_operation(f"{log_label}_mapping", f"Received mapping: {list(mapping.keys())}")
        return mapping
    except json.JSONDecodeError:
        log_secure_operation(f"{log_label}_mapping_error", "Invalid JSON in mapping")
        return None


def safe_download_filename(raw_name: str, suffix: str, ext: str) -> str:
    """Generate sanitized timestamped download filename."""
    safe = "".join(c for c in raw_name if c.isalnum() or c in "._-")
    if not safe:
        safe = "Export"
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{safe}_{suffix}_{timestamp}.{ext}"


def safe_background_email(send_func, *, label: str = "email", **kwargs) -> None:
    """Background task wrapper for email sending with error logging.

    Catches all exceptions so background task failures are observable
    but never crash the ASGI server.
    """
    try:
        result = send_func(**kwargs)
        if not result.success:
            log_secure_operation(
                f"background_{label}_failed",
                f"Background email send failed: {getattr(result, 'error', 'unknown')}"
            )
    except Exception as e:
        log_secure_operation(
            f"background_{label}_error",
            f"Background email exception: {str(e)[:200]}"
        )


def maybe_record_tool_run(
    db: Session,
    engagement_id: Optional[int],
    user_id: int,
    tool_name: str,
    success: bool,
    composite_score: Optional[float] = None,
) -> None:
    """
    Record a tool run if engagement_id is provided. No-op otherwise.
    Used by tool routes to optionally link runs to engagements.
    """
    if engagement_id is None:
        return

    from engagement_model import ToolName, ToolRunStatus
    from engagement_manager import EngagementManager

    manager = EngagementManager(db)

    # Verify engagement exists and user has access
    engagement = manager.get_engagement(user_id, engagement_id)
    if not engagement:
        log_secure_operation(
            "tool_run_skip",
            f"Engagement {engagement_id} not found for user {user_id}; skipping tool run",
        )
        return

    manager.record_tool_run(
        engagement_id=engagement_id,
        tool_name=ToolName(tool_name),
        status=ToolRunStatus.COMPLETED if success else ToolRunStatus.FAILED,
        composite_score=composite_score if success else None,
    )
