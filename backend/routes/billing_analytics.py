"""
Billing analytics routes — usage analytics and weekly review metrics for the
founder/admin dashboard. Restricted to org owners/admins or solo subscribers.
Extracted from the monolithic billing.py during Refactor 4 (bounded-domain split).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from schemas.billing_schemas import WeeklyReviewResponse
from shared.rate_limits import RATE_LIMIT_DEFAULT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Analytics (Phase LX — post-launch control)
# ---------------------------------------------------------------------------


@router.get("/analytics/weekly-review", response_model=WeeklyReviewResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_weekly_review_endpoint(
    request: Request,
    user: Annotated[User, Depends(require_verified_user)],
    db: Session = Depends(get_db),
) -> WeeklyReviewResponse:
    """Weekly pricing review — 5 decision metrics with period-over-period deltas.

    Metrics: trial starts, trial->paid rate, paid by plan, avg seats, cancellations by reason.
    Security Sprint: Restricted to org owner/admin to prevent sensitive billing data leakage.
    """
    from organization_model import OrganizationMember, OrgRole

    # Security: Only org owner/admin can access billing analytics
    if user.organization_id:
        member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == user.organization_id,
            )
            .first()
        )
        if not member or member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or owner role required to access billing analytics.",
            )
    else:
        # Solo user — only allow if they have an active subscription (they're viewing their own data)
        from billing.subscription_manager import get_subscription

        sub = get_subscription(db, user.id)
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active subscription required to access billing analytics.",
            )

    from billing.analytics import get_weekly_review

    review = get_weekly_review(db, user_id=user.id, org_id=user.organization_id)
    return WeeklyReviewResponse(**review)
