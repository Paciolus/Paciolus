"""
Paciolus API — Shared Helper Functions
"""
import hashlib
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
