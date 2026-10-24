"""
Usage service — Sprint 519 Phase 5

Extracts usage/entitlement calculation from the billing route layer.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class UsageStats:
    """Current usage stats for a user's billing period."""

    uploads_used: int
    uploads_limit: int
    clients_used: int
    clients_limit: int
    tier: str


def get_usage_stats(db: Session, user_id: int, user_tier_value: str) -> UsageStats:
    """Calculate current usage stats for entitlement display.

    Sprint 790: uploads come from the same function the quota gate uses
    (``shared.entitlement_checks.uploads_used_this_period``), so the number a
    user is shown is the number they are blocked on.
    """
    from sqlalchemy import func

    from models import Client, UserTier
    from shared.entitlement_checks import uploads_used_this_period
    from shared.entitlements import get_entitlements

    entitlements = get_entitlements(UserTier(user_tier_value))

    uploads_used = uploads_used_this_period(db, user_id)

    # Count clients
    clients_used = (db.query(func.count(Client.id)).filter(Client.user_id == user_id).scalar()) or 0

    return UsageStats(
        uploads_used=uploads_used,
        uploads_limit=entitlements.uploads_per_month,
        clients_used=clients_used,
        clients_limit=entitlements.max_clients,
        tier=user_tier_value,
    )
