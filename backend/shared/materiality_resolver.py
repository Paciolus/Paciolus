"""
Materiality resolver — Sprint 519 Phase 5

Shared materiality cascade resolution extracted from routes/audit.py.
Priority: explicit manual threshold > engagement cascade > default (0.0).
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
