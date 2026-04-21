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

from typing import Optional

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
