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

import json
from typing import Any, Optional

from fastapi import HTTPException

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


# Sprint 883 (review ST-09): a form field that is not supplied is ``None``; one
# that is supplied but is not valid JSON of the right shape is a 400 naming the
# field. Before, valid JSON of the wrong shape (``[]``, ``null``, ``"text"``)
# reached ``.keys()`` and became a 500, and malformed JSON was silently
# treated as "not supplied".

_TYPE_NAMES: dict[type, str] = {str: "strings"}


def _load_json(raw_json: str) -> object:
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        return _MALFORMED


_MALFORMED = object()


def parse_json_list(
    raw_json: Optional[str],
    log_label: str,
    *,
    field: str = "value",
    item_type: Optional[type] = None,
) -> Optional[list[Any]]:
    """Parse an optional JSON array form field.

    Returns None when the field is not supplied. Raises a 400 naming ``field``
    when it is not a JSON array, or (with ``item_type``) when any element is
    not of that type.
    """
    if not raw_json:
        return None
    result = _load_json(raw_json)
    if not isinstance(result, list):
        log_secure_operation(f"{log_label}_error", f"{log_label} is not a JSON array")
        raise HTTPException(status_code=400, detail=f"Invalid {field}: expected a JSON array.")
    if item_type is not None and not all(isinstance(item, item_type) for item in result):
        log_secure_operation(f"{log_label}_error", f"{log_label} has elements of the wrong type")
        type_name = _TYPE_NAMES.get(item_type, item_type.__name__)
        raise HTTPException(status_code=400, detail=f"Invalid {field}: expected a JSON array of {type_name}.")
    log_secure_operation(log_label, f"Received {len(result)} {log_label} items")
    return result


def parse_json_mapping(
    raw_json: Optional[str],
    log_label: str,
    *,
    field: str = "column_mapping",
) -> Optional[dict[str, str]]:
    """Parse an optional JSON object form field whose keys and values are strings.

    Returns None when the field is not supplied; raises a 400 naming ``field``
    for anything else that is not such an object.
    """
    if not raw_json:
        return None
    mapping = _load_json(raw_json)
    if not isinstance(mapping, dict) or not all(isinstance(v, str) for v in mapping.values()):
        log_secure_operation(f"{log_label}_mapping_error", "Mapping is not a JSON object of strings")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field}: expected a JSON object whose keys and values are strings.",
        )
    log_secure_operation(f"{log_label}_mapping", f"Received mapping: {list(mapping.keys())}")
    return dict(mapping)


__all__ = [
    "try_parse_risk",
    "try_parse_risk_band",
    "parse_json_list",
    "parse_json_mapping",
]
