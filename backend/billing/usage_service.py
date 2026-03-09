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

    Resolves uploads from subscription counter (preferred) or ActivityLog fallback.
    """
    from datetime import UTC, datetime

    from sqlalchemy import func

    from models import ActivityLog, Client, UserTier
    from shared.entitlements import get_entitlements
    from subscription_model import Subscription

    entitlements = get_entitlements(UserTier(user_tier_value))

    # Count uploads this period (try subscription counter, fallback to ActivityLog)
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub and sub.uploads_used_current_period is not None:
        uploads_used = sub.uploads_used_current_period
    else:
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        uploads_used = (
            db.query(func.count(ActivityLog.id))
            .filter(
                ActivityLog.user_id == user_id,
                ActivityLog.timestamp >= month_start,
                ActivityLog.archived_at.is_(None),
            )
            .scalar()
        ) or 0

    # Count clients
    clients_used = (db.query(func.count(Client.id)).filter(Client.user_id == user_id).scalar()) or 0

    return UsageStats(
        uploads_used=uploads_used,
        uploads_limit=entitlements.uploads_per_month,
        clients_used=clients_used,
        clients_limit=entitlements.max_clients,
        tier=user_tier_value,
    )
