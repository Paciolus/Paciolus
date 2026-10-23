"""
As-of date resolution for tests that measure elapsed time (Sprint 816).

Fixed-asset depreciation recalculation (FA-T11) and slow-moving inventory
(IN-06) compare dates in the upload against a reference date. Both used the
day the file was processed, but the data is stated as of period end — so a
correctly depreciated register tested ten months after year-end had every
asset flagged. The reference date now resolves like materiality does:
explicit form value, then the linked engagement's period end, then the
processing date — and the source is stated in each test's description.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # the engines import the label helper; keep them framework-free
    from sqlalchemy.orm import Session

_AS_OF_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y")

_SOURCE_LABELS = {
    "as_of_date": "as-of date supplied",
    "engagement_period_end": "engagement period end",
    "processing_date": "processing date — link an engagement or supply as_of_date to measure to period end",
}


def reference_date_label(source: str) -> str:
    return _SOURCE_LABELS.get(source, source)


def resolve_reference_date(
    as_of_date: Optional[str],
    engagement_id: Optional[int],
    user_id: int,
    db: Session,
) -> tuple[Optional[date], str]:
    """Priority: explicit ``as_of_date`` > engagement period end > processing date.

    Returns ``(reference_date, source)``; ``reference_date`` is None for the
    processing-date fallback, which the engines resolve at run time. An
    unparseable ``as_of_date`` is a 400 — silently falling back would measure
    to the wrong date without saying so.
    """
    if as_of_date and as_of_date.strip():
        for fmt in _AS_OF_FORMATS:
            try:
                return datetime.strptime(as_of_date.strip(), fmt).date(), "as_of_date"
            except ValueError:
                continue
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail="as_of_date must be YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY.",
        )
    if engagement_id is not None:
        from engagement_manager import EngagementManager

        engagement = EngagementManager(db).get_engagement(user_id, engagement_id)
        if engagement is not None and engagement.period_end is not None:
            return engagement.period_end.date(), "engagement_period_end"
    return None, "processing_date"
