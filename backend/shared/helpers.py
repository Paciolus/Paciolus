"""Paciolus shared helpers — compatibility facade.

This module used to be a ~1,100-line grab bag. It was decomposed into
cohesive modules during the 2026-04-20 refactor pass:

    shared.upload_pipeline   — validate_file_size, parse_uploaded_file[_by_format],
                               memory_cleanup, and related limits/magic-byte/archive
                               inspection helpers.
    shared.filenames         — hash_filename, get_filename_display,
                               safe_download_filename, sanitize_csv_value,
                               escape_like_wildcards.
    shared.background_email  — safe_background_email (BackgroundTasks wrapper).
    shared.tool_run_recorder — maybe_record_tool_run (engagement + ToolActivity).

Existing ``from shared.helpers import X`` call sites continue to resolve via
re-exports in this module. New code should import from the target module
directly.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException
from fastapi import Path as PathParam
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from flux_engine import FluxRisk
from models import Client, User
from recon_engine import RiskBand
from security_utils import log_secure_operation

# ---------------------------------------------------------------------------
# Re-exports for back-compat (preserve existing ``from shared.helpers import X``)
# ---------------------------------------------------------------------------
from shared.background_email import safe_background_email  # noqa: F401
from shared.filenames import (  # noqa: F401
    escape_like_wildcards,
    get_filename_display,
    hash_filename,
    safe_download_filename,
    sanitize_csv_value,
)
from shared.tool_run_recorder import (  # noqa: F401
    _log_tool_activity,
    maybe_record_tool_run,
)
from shared.upload_pipeline import (  # noqa: F401
    _XLS_MAGIC,
    _XLSX_MAGIC,
    MAX_CELL_LENGTH,
    MAX_COL_COUNT,
    MAX_COMPRESSION_RATIO,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    MAX_ROW_COUNT,
    MAX_ZIP_ENTRIES,
    MAX_ZIP_UNCOMPRESSED_BYTES,
    _detect_delimiter,
    _estimate_csv_row_count,
    _estimate_xlsx_row_count,
    _parse_csv,
    _parse_docx,
    _parse_excel,
    _parse_iif,
    _parse_ods,
    _parse_ofx,
    _parse_pdf,
    _parse_tsv,
    _parse_txt,
    _scan_xlsx_xml_for_bombs,
    _sniff_text_format,
    _validate_and_convert_df,
    _validate_xlsx_archive,
    memory_cleanup,
    parse_uploaded_file,
    parse_uploaded_file_by_format,
    validate_file_size,
)

# ---------------------------------------------------------------------------
# Small helpers that remain co-located with the shim
# ---------------------------------------------------------------------------


def try_parse_risk(risk_str: str) -> FluxRisk:
    """Coerce a string to ``FluxRisk``, defaulting to LOW on unknown values."""
    try:
        return FluxRisk(risk_str)
    except ValueError:
        return FluxRisk.LOW


def try_parse_risk_band(band_str: str) -> RiskBand:
    """Coerce a string to ``RiskBand``, defaulting to LOW on unknown values."""
    try:
        return RiskBand(band_str)
    except ValueError:
        return RiskBand.LOW


def parse_json_list(raw_json: Optional[str], log_label: str) -> Optional[list]:
    """Parse an optional JSON string into a list; return None on invalid input."""
    import json

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
    """Parse an optional JSON string into a dict; return None on invalid input."""
    import json

    if not raw_json:
        return None
    try:
        mapping = json.loads(raw_json)
        log_secure_operation(f"{log_label}_mapping", f"Received mapping: {list(mapping.keys())}")
        return dict(mapping)
    except json.JSONDecodeError:
        log_secure_operation(f"{log_label}_mapping_error", "Invalid JSON in mapping")
        return None


# ---------------------------------------------------------------------------
# Client access policy (direct ownership + organization membership)
# ---------------------------------------------------------------------------


def is_authorized_for_client(user: User, client: Client, db: Session) -> bool:
    """Check whether ``user`` may access ``client``.

    Returns True if:
      (a) ``client.user_id == user.id`` (direct ownership), or
      (b) both ``user`` and the client's owner are active members of the
          same organization (organization-scoped sharing).
    """
    if client.user_id == user.id:
        return True

    if user.organization_id:
        from organization_model import OrganizationMember

        owner_membership = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == client.user_id,
                OrganizationMember.organization_id == user.organization_id,
            )
            .first()
        )
        if owner_membership:
            return True

    return False


def get_accessible_client(user: User, client_id: int, db: Session) -> Client | None:
    """Return ``Client`` if ``user`` may access it, else None."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        return None
    if is_authorized_for_client(user, client, db):
        return client
    return None


def require_client(
    client_id: int = PathParam(..., description="The ID of the client"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Client:
    """FastAPI dependency: resolve a ``Client`` by id or raise 404."""
    client = get_accessible_client(current_user, client_id, db)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
