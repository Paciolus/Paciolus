"""Paciolus shared helpers — small native utilities.

This module owns a handful of small cross-cutting helpers that don't justify
a dedicated module of their own:

    - ``try_parse_risk`` / ``try_parse_risk_band``: defaulted enum coercion
    - ``parse_json_list`` / ``parse_json_mapping``: defensive JSON parsing
    - ``is_authorized_for_client`` / ``get_accessible_client`` / ``require_client``:
      direct-ownership + organization-scoped client access policy

Sprint 724 removed the re-export shim that previously re-published symbols from
``shared.upload_pipeline``, ``shared.filenames``, ``shared.background_email``,
and ``shared.tool_run_recorder``. Those symbols now live only at their owning
module. The deferred-items decision (see ``tasks/todo.md`` 2026-04-20 entry)
keeps the small client-access helpers here rather than spawning a new module
for three functions — revisit only if a fourth helper joins them.
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
# Native helpers (do not extend this module casually — see Sprint 724 docstring)
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
