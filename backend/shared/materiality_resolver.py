"""
Materiality resolver — Sprint 519 Phase 5

Shared materiality cascade resolution extracted from routes/audit.py.
Priority: explicit manual threshold > engagement cascade > default (0.0).

Materiality cascade (Sprint 692 — explicit naming for memo consumers):

  * Overall materiality — the base amount (typically 5% of net income
    before tax, or 0.5-2% of revenue/assets per industry convention).
  * Performance materiality — default **75% of overall** (ISA 320 ¶11 /
    AU-C 320.A12). Reduces the risk that undetected AND uncorrected
    misstatements aggregate above overall materiality.
  * Clearly-trivial threshold — default **5% of overall** materiality
    (ISA 320 ¶A20 / AU-C 320.18). Below this, the auditor can pass on
    accumulating individual misstatements. Note: this is 5% of
    OVERALL materiality, NOT 5% of performance materiality — the two
    are frequently confused and the memo text must be precise.

This resolver returns performance materiality (not overall) as the
engagement-sourced threshold, because tooling that drives individual-
account testing wants the *tighter* of the two numbers. Memos that
cite "materiality threshold" should clarify whether they mean PM or
overall to avoid ambiguity.
"""

import json
import math
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session


def resolve_materiality(
    materiality_threshold: float,
    engagement_id: Optional[int],
    user_id: int,
    db: Session,
) -> tuple[float, str]:
    """Resolve effective materiality. Priority: explicit > engagement > default.

    Returns (threshold, source) where source is 'manual', 'engagement', or 'none'.
    """
    if materiality_threshold > 0.0:
        return materiality_threshold, "manual"
    if engagement_id is not None:
        from engagement_manager import EngagementManager

        mgr = EngagementManager(db)
        eng = mgr.get_engagement(user_id, engagement_id)
        if eng and eng.materiality_amount:
            cascade = mgr.compute_materiality(eng)
            pm = cascade.get("performance_materiality", 0.0)
            if pm > 0:
                return pm, "engagement"
    return 0.0, "none"


# ─────────────────────────────────────────────────────────────────────
# Sprint 886 (OUT-09, OUT-16): the materiality basis — amount, purpose, origin.
# ─────────────────────────────────────────────────────────────────────

NOT_AVAILABLE = "Not available"

# What the figure is for. The trial balance tool uses it as a flagging threshold;
# it is performance materiality only when it is the engagement's.
PURPOSE_LABELS = {
    "overall_materiality": "Overall materiality",
    "performance_materiality": "Performance materiality",
    "test_threshold": "Test threshold",
}
# Where it came from.
ORIGIN_LABELS = {
    "software_default": "Paciolus default",
    "firm_setting": "Saved firm setting",
    "engagement": "Engagement",
    "entered": "Entered for this run",
}
# What the page may claim about how it set the figure.
CLAIMED_ORIGINS = ("default", "engagement", "entered")


@dataclass(frozen=True)
class MaterialityBasis:
    amount: float
    purpose: str
    origin: str  # an ORIGIN_LABELS key, or "none" when no threshold was set

    def to_dict(self) -> dict[str, Any]:
        return {"amount": self.amount, "purpose": self.purpose, "origin": self.origin}


def software_default_materiality() -> float:
    """The amount the trial balance page starts at (the practice-settings default)."""
    from practice_settings import MaterialityFormula

    return float(MaterialityFormula().value)


def _saved_fixed_materiality(user: Any) -> Optional[float]:
    """The fixed materiality the user saved in practice settings, or None if none was saved.

    The settings API returns a $500 fixed formula even when nothing was saved, so
    only a ``default_materiality`` actually stored on the user counts. The page
    applies only fixed formulas.
    """
    try:
        stored = json.loads(getattr(user, "settings", None) or "{}")
    except (TypeError, ValueError):
        return None
    formula = stored.get("default_materiality") if isinstance(stored, dict) else None
    if not isinstance(formula, dict) or formula.get("type", "fixed") != "fixed":
        return None
    value = formula.get("value")
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 else None


def _engagement_performance_materiality(engagement_id: Optional[int], user_id: int, db: Session) -> Optional[float]:
    if engagement_id is None:
        return None
    from engagement_manager import EngagementManager

    mgr = EngagementManager(db)
    eng = mgr.get_engagement(user_id, engagement_id)
    if not eng or not eng.materiality_amount:
        return None
    pm = mgr.compute_materiality(eng).get("performance_materiality", 0.0)
    return float(pm) if pm and pm > 0 else None


def _same(a: float, b: Optional[float]) -> bool:
    return b is not None and math.isclose(a, b, abs_tol=0.005)


def resolve_materiality_basis(
    materiality_threshold: float,
    engagement_id: Optional[int],
    user: Any,
    db: Session,
    claimed_origin: Optional[str] = None,
) -> MaterialityBasis:
    """Resolve the threshold and say truthfully where it came from (Sprint 886, OUT-16).

    ``claimed_origin`` is how the page says it set a positive amount: "default"
    (pre-filled from the saved firm setting, or the software default when none is
    saved), "engagement" (the engagement's performance materiality) or "entered".
    Each claim is checked against what the server knows; one it cannot confirm,
    or no claim at all, is reported as entered for this run. With no amount the
    engagement's performance materiality applies, as before.
    """
    pm = _engagement_performance_materiality(engagement_id, user.id, db)
    if materiality_threshold > 0.0:
        amount = float(materiality_threshold)
        if claimed_origin == "engagement" and _same(amount, pm):
            return MaterialityBasis(amount, "performance_materiality", "engagement")
        if claimed_origin == "default":
            saved = _saved_fixed_materiality(user)
            if saved is not None and _same(amount, saved):
                return MaterialityBasis(amount, "test_threshold", "firm_setting")
            if saved is None and _same(amount, software_default_materiality()):
                return MaterialityBasis(amount, "test_threshold", "software_default")
        return MaterialityBasis(amount, "test_threshold", "entered")
    if pm is not None:
        return MaterialityBasis(pm, "performance_materiality", "engagement")
    return MaterialityBasis(0.0, "test_threshold", "none")


def materiality_basis_label(basis: Optional[dict], legacy_source: Optional[str] = None) -> str:
    """How every export names the threshold's purpose and origin.

    ``legacy_source`` is the pre-Sprint-886 ``materiality_source`` of an analysis
    made before the basis existed: only "engagement" and "none" were truthful
    there ("manual" was any positive amount), so anything else is "Not available".
    """
    if basis:
        if basis.get("origin") == "none":
            return "No threshold set"
        purpose = PURPOSE_LABELS.get(str(basis.get("purpose")))
        origin = ORIGIN_LABELS.get(str(basis.get("origin")))
        return f"{purpose} — {origin}" if purpose and origin else NOT_AVAILABLE
    if legacy_source == "engagement":
        return f"{PURPOSE_LABELS['performance_materiality']} — {ORIGIN_LABELS['engagement']}"
    if legacy_source == "none":
        return "No threshold set"
    return NOT_AVAILABLE
