"""Billing / analytics access policy.

Small helpers that centralize the access rules for billing-sensitive endpoints
so route handlers can stay focused on request/response shaping.

Security sprint: ``require_billing_analytics_access`` restricts weekly-review
data to org owners/admins, or — for solo users — to those with an active
subscription (they're viewing their own billing history, not a peer's).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import User


def require_billing_analytics_access(db: Session, user: User) -> None:
    """Raise 403 unless ``user`` may read the weekly-review / billing-analytics feed.

    Rules:
      - Org member: must be OWNER or ADMIN.
      - Solo user (no org): must have an active subscription.
    """
    if user.organization_id:
        from organization_model import OrganizationMember, OrgRole

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
        return

    # Solo user — allow only if they own an active subscription
    from billing.subscription_manager import get_subscription

    sub = get_subscription(db, user.id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required to access billing analytics.",
        )
