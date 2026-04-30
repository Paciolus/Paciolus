"""Paciolus shared helpers — small native utilities.

Owns:
    - ``try_parse_risk`` / ``try_parse_risk_band``: defaulted enum coercion
    - ``parse_json_list`` / ``parse_json_mapping``: defensive JSON parsing

Sprint 754 (per ADR-018-style relocation): client-access helpers
(``is_authorized_for_client`` / ``get_accessible_client`` /
``require_client`` / ``require_client_owner``) moved to
``shared.client_access`` and all 6 callers migrated. The deferred-items
entry in ``tasks/todo.md`` (2026-04-20) said "revisit only if a fourth
helper joins them"; Sprint 735's ``require_client_owner`` was the
fourth, and Sprint 754 made the move.

Sprint 724 removed re-export shims for ``shared.upload_pipeline``,
``shared.filenames``, ``shared.background_email``, and
``shared.tool_run_recorder``. Those symbols live only at their owning
module. Don't extend this module casually — the
``test_no_helpers_reexports`` guardrail is the contract.
"""

from __future__ import annotations

from typing import Optional

from flux_engine import FluxRisk
from recon_engine import RiskBand
from security_utils import log_secure_operation


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


__all__ = [
    "try_parse_risk",
    "try_parse_risk_band",
    "parse_json_list",
    "parse_json_mapping",
]
