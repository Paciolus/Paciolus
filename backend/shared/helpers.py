"""
Paciolus API — Shared Helper Functions
"""
import hashlib
import io
import json
from datetime import datetime, UTC
from typing import Optional

import pandas as pd
from fastapi import HTTPException, UploadFile, Depends, Path as PathParam
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User, Client
from auth import require_current_user
from client_manager import ClientManager
from flux_engine import FluxRisk
from recon_engine import RiskBand

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
MAX_FILE_SIZE_MB = 100


async def validate_file_size(file: UploadFile) -> bytes:
    """Read uploaded file with size validation. Raises 413 if too large."""
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

    return bytes(contents)


async def require_client(
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


def parse_uploaded_file(file_bytes: bytes, filename: str) -> tuple[list[str], list[dict]]:
    """Parse CSV or Excel file bytes into column names and row dicts. Caller must del result when done."""
    filename_lower = (filename or "").lower()
    if filename_lower.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        df = pd.read_csv(io.BytesIO(file_bytes))
    column_names = list(df.columns.astype(str))
    rows = df.to_dict('records')
    del df
    return column_names, rows


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
