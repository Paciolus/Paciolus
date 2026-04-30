"""
Sprint 764 — Intercompany counterparty mapping resolver.

Resolves the active counterparty mapping for an intercompany detection
run using a request → engagement → none cascade (mirrors the materiality
cascade in ``shared.materiality_resolver``).

Precedence (first match wins):
1. **Manual override** — caller supplies ``request_mapping`` directly on
   the diagnostic request body.  Source = "request".
2. **Engagement default** — ``Engagement.intercompany_counterparties``
   stored from a prior planning step.  Source = "engagement".
3. **None** — no mapping; the detection layer falls back to the
   heuristic separator parser.  Source = "none".

The function is intentionally framework-light: it returns the resolved
mapping dict (case-folded keys) plus the source tag.  Callers (route
handlers, the streaming auditor) thread both into
``detect_intercompany_imbalances()`` so findings carry an explicit
``detection_method`` field.

See ``docs/04-compliance/variance-formula-policy.md`` for the analogous
materiality cascade pattern.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MappingSource = str  # Literal["request", "engagement", "none"] — typed at call site


def _normalize_mapping(raw: dict[str, str]) -> dict[str, str]:
    """Case-fold both account-name keys and counterparty values.

    Account names are stored verbatim in the trial balance, but matching
    happens case-insensitively to absorb capitalization variance.
    """
    return {str(k).strip().lower(): str(v).strip() for k, v in raw.items() if k and v}


def resolve_counterparty_mapping(
    request_mapping: Optional[dict[str, str]],
    engagement_id: Optional[int],
    db: Optional[Session],
) -> tuple[dict[str, str], MappingSource]:
    """Resolve the active counterparty mapping for a detection run.

    Args:
        request_mapping: Mapping supplied on the request body, if any.
            ``{"account_name": "counterparty", ...}``.  Wins over
            engagement defaults.
        engagement_id: Optional engagement to look up for stored mapping.
            Ignored when ``request_mapping`` is provided.
        db: SQLAlchemy session.  Required when looking up the engagement.

    Returns:
        Tuple of (mapping, source) where:
            - mapping is a (possibly empty) dict with case-folded keys.
            - source ∈ ``{"request", "engagement", "none"}``.

    Empty dicts are treated as "no mapping" — they pass through as
    ``({}, "none")`` rather than ``({}, "request")`` so downstream
    findings reflect the practical absence of an override.
    """
    if request_mapping:
        return _normalize_mapping(request_mapping), "request"

    if engagement_id is not None and db is not None:
        # Local import to avoid circular dependency: engagement_model
        # imports from shared modules.
        from engagement_model import Engagement

        eng = db.query(Engagement).filter(Engagement.id == engagement_id).first()
        if eng and eng.intercompany_counterparties:
            try:
                stored = json.loads(eng.intercompany_counterparties)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "Engagement %s has malformed intercompany_counterparties JSON; falling back to heuristic detection",
                    engagement_id,
                )
                return {}, "none"
            if isinstance(stored, dict) and stored:
                return _normalize_mapping(stored), "engagement"

    return {}, "none"


def detection_method_label(used_metadata: bool, separator_parsed: bool) -> str:
    """Classify how a counterparty was identified for explainability.

    Args:
        used_metadata: True when the resolver supplied a non-empty
            mapping AND the account in question was found in it.
        separator_parsed: True when the heuristic separator parser
            (em-dash / hyphen / etc.) extracted a counterparty.

    Returns:
        - ``"metadata_exact"`` when metadata supplied the counterparty.
        - ``"heuristic_separator"`` when the separator parser succeeded.
        - ``"heuristic_keyword"`` when neither produced a counterparty
          but the keyword scan still flagged the account as IC.
    """
    if used_metadata:
        return "metadata_exact"
    if separator_parsed:
        return "heuristic_separator"
    return "heuristic_keyword"
