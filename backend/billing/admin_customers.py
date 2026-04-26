"""
Admin customer service — Sprint 590: Internal admin console.

Read-only queries for customer list/detail, plus admin action execution
functions. All mutation functions create AdminAuditLog entries.
"""

import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from admin_audit_model import AdminActionType, AdminAuditLog
from billing.price_config import (
    ENTERPRISE_SEAT_PRICE,
    PRICE_TABLE,
    PROFESSIONAL_SEAT_PRICE,
)
from models import ActivityLog, DiagnosticSummary, RefreshToken, User
from organization_model import Organization, OrganizationMember
from shared.filenames import escape_like_wildcards
from subscription_model import (
    BillingEvent,
    Subscription,
    SubscriptionStatus,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _subscription_mrr(sub: Subscription) -> float:
    """Calculate monthly revenue for a subscription."""
    tier = sub.tier or "free"
    interval = sub.billing_interval.value if sub.billing_interval else "monthly"
    base_cents = PRICE_TABLE.get(tier, {}).get(interval, 0)
    additional = sub.additional_seats or 0
    seat_cents = 0
    if additional > 0:
        if tier == "professional":
            seat_cents = additional * PROFESSIONAL_SEAT_PRICE.get(interval, 0)
        elif tier == "enterprise":
            seat_cents = additional * ENTERPRISE_SEAT_PRICE.get(interval, 0)
    total_cents = base_cents + seat_cents
    if interval == "annual":
        return round(total_cents / 12.0 / 100.0, 2)
    return round(total_cents / 100.0, 2)


def _create_audit_entry(
    db: Session,
    admin_user_id: int,
    action_type: AdminActionType,
    *,
    target_org_id: int | None = None,
    target_user_id: int | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> AdminAuditLog:
    """Create an admin audit log entry. Returns the entry for ID reference."""
    entry = AdminAuditLog(
        admin_user_id=admin_user_id,
        action_type=action_type,
        target_org_id=target_org_id,
        target_user_id=target_user_id,
        details_json=json.dumps(details) if details else None,
        ip_address=ip_address,
    )
    db.add(entry)
    db.flush()
    return entry


# ---------------------------------------------------------------------------
# Customer List
# ---------------------------------------------------------------------------


def get_customer_list(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 50,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    plan: str | None = None,
    status: str | None = None,
    search: str | None = None,
    signup_after: datetime | None = None,
    signup_before: datetime | None = None,
) -> dict:
    """Paginated, sortable, filterable customer list.

    Returns {items: [...], total: int, offset: int, limit: int}.
    Each item is a customer summary dict.
    """
    # Base query: all non-free users OR users with subscriptions
    query = db.query(User).filter(User.is_active == True)  # noqa: E712

    # Filters
    if search:
        search_pattern = f"%{escape_like_wildcards(search)}%"
        org_ids_matching = (
            db.query(Organization.id).filter(Organization.name.ilike(search_pattern, escape="\\")).subquery()
        )
        query = query.filter(
            or_(
                User.email.ilike(search_pattern, escape="\\"),
                User.name.ilike(search_pattern, escape="\\"),
                User.organization_id.in_(db.query(org_ids_matching)),
            )
        )

    if signup_after:
        query = query.filter(User.created_at >= signup_after)
    if signup_before:
        query = query.filter(User.created_at < signup_before)

    # Plan/status filtering requires join to subscription
    if plan or status:
        query = query.join(Subscription, Subscription.user_id == User.id)
        if plan:
            query = query.filter(Subscription.tier == plan)
        if status:
            query = query.filter(Subscription.status == status)

    # Total count (before pagination)
    total = query.count()

    # Sorting
    sort_col = {
        "created_at": User.created_at,
        "last_login": User.last_login,
        "email": User.email,
    }.get(sort_by, User.created_at)

    if sort_dir == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Pagination
    users = query.offset(offset).limit(limit).all()

    # Build summaries
    items = []
    for user in users:
        items.append(_build_customer_summary(db, user))

    return {"items": items, "total": total, "offset": offset, "limit": limit}


def _build_customer_summary(db: Session, user: User) -> dict:
    """Build a customer summary dict for the list view."""
    # Get subscription
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    # Get org
    org = None
    if user.organization_id:
        org = db.query(Organization).filter(Organization.id == user.organization_id).first()

    # Upload count this period
    uploads = sub.uploads_used_current_period if sub else 0

    # Total reports
    total_reports = (
        db.query(func.count(DiagnosticSummary.id)).filter(DiagnosticSummary.user_id == user.id).scalar() or 0
    )

    mrr = (
        _subscription_mrr(sub)
        if sub and sub.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)
        else 0.0
    )

    return {
        "user_id": user.id,
        "org_id": user.organization_id,
        "org_name": org.name if org else None,
        "owner_email": user.email,
        "owner_name": user.name,
        "plan": sub.tier if sub else user.tier.value if user.tier else "free",
        "status": sub.status.value if sub and sub.status else "active",
        "billing_interval": sub.billing_interval.value if sub and sub.billing_interval else None,
        "mrr": mrr,
        "signup_date": user.created_at.isoformat() if user.created_at else "",
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "uploads_this_period": uploads,
        "total_reports_generated": total_reports,
        "is_verified": user.is_verified,
    }


# ---------------------------------------------------------------------------
# Customer Detail
# ---------------------------------------------------------------------------


def get_customer_detail(db: Session, org_id: int) -> dict | None:
    """Full customer account profile for the detail view.

    Accepts org_id. For users without an org, also supports user_id lookup
    by passing it as org_id (falls back to user lookup).
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()

    if org:
        owner = db.query(User).filter(User.id == org.owner_user_id).first()
    else:
        # Fallback: treat org_id as user_id for solo users
        owner = db.query(User).filter(User.id == org_id).first()

    if not owner:
        return None

    # Members
    members = []
    if org:
        member_rows = (
            db.query(OrganizationMember, User)
            .join(User, OrganizationMember.user_id == User.id)
            .filter(OrganizationMember.organization_id == org.id)
            .all()
        )
        for member, u in member_rows:
            members.append(
                {
                    "user_id": u.id,
                    "email": u.email,
                    "name": u.name,
                    "role": member.role.value if member.role else "member",
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                }
            )

    # Subscription
    sub = db.query(Subscription).filter(Subscription.user_id == owner.id).first()
    sub_detail = None
    if sub:
        sub_detail = {
            "id": sub.id,
            "tier": sub.tier,
            "status": sub.status.value if sub.status else "active",
            "billing_interval": sub.billing_interval.value if sub.billing_interval else None,
            "seat_count": sub.seat_count or 1,
            "additional_seats": sub.additional_seats or 0,
            "total_seats": sub.total_seats,
            "uploads_used_current_period": sub.uploads_used_current_period or 0,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "stripe_customer_id": sub.stripe_customer_id,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
        }

    # Billing events (all for this user, chronological)
    user_ids = [m["user_id"] for m in members] if members else [owner.id]
    billing_events = (
        db.query(BillingEvent)
        .filter(BillingEvent.user_id.in_(user_ids))
        .order_by(BillingEvent.created_at.desc())
        .limit(100)
        .all()
    )

    # Recent activity (last 50)
    recent_activity = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id.in_(user_ids))
        .order_by(ActivityLog.timestamp.desc())
        .limit(50)
        .all()
    )

    # Usage stats
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)
    uploads_30d = (
        db.query(func.count(ActivityLog.id))
        .filter(ActivityLog.user_id.in_(user_ids), ActivityLog.timestamp >= thirty_days_ago)
        .scalar()
        or 0
    )
    total_reports = (
        db.query(func.count(DiagnosticSummary.id)).filter(DiagnosticSummary.user_id.in_(user_ids)).scalar() or 0
    )

    # Active sessions
    active_sessions = (
        db.query(func.count(RefreshToken.id))
        .filter(
            RefreshToken.user_id.in_(user_ids),
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .scalar()
        or 0
    )

    return {
        "user_id": owner.id,
        "org_id": org.id if org else None,
        "org_name": org.name if org else None,
        "owner_email": owner.email,
        "owner_name": owner.name,
        "is_verified": owner.is_verified,
        "signup_date": owner.created_at.isoformat() if owner.created_at else "",
        "last_login": owner.last_login.isoformat() if owner.last_login else None,
        "members": members,
        "subscription": sub_detail,
        "billing_events": [
            {
                "id": e.id,
                "event_type": e.event_type.value if e.event_type else "",
                "tier": e.tier,
                "interval": e.interval,
                "metadata_json": e.metadata_json,
                "created_at": e.created_at.isoformat() if e.created_at else "",
            }
            for e in billing_events
        ],
        "recent_activity": [
            {
                "id": a.id,
                "filename_display": a.filename_display,
                "record_count": a.record_count or 0,
                "timestamp": a.timestamp.isoformat() if a.timestamp else "",
            }
            for a in recent_activity
        ],
        "usage_stats": {
            "uploads_30d": uploads_30d,
            "total_reports": total_reports,
        },
        "active_session_count": active_sessions,
        "dunning": _get_dunning_info(db, sub) if sub else None,
    }


# ---------------------------------------------------------------------------
# Admin Actions
# ---------------------------------------------------------------------------


def admin_plan_override(
    db: Session,
    org_id: int,
    new_plan: str,
    reason: str,
    effective_immediately: bool,
    admin_user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Override a customer's plan. Updates local DB (Stripe sync deferred to webhook)."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    owner = (
        db.query(User).filter(User.id == org.owner_user_id).first()
        if org
        else db.query(User).filter(User.id == org_id).first()
    )
    if not owner:
        raise ValueError("Customer not found")

    sub = db.query(Subscription).filter(Subscription.user_id == owner.id).first()
    old_plan = sub.tier if sub else owner.tier.value

    if sub:
        sub.tier = new_plan
        db.flush()
    # Update user tier
    from models import UserTier

    owner.tier = UserTier(new_plan)
    db.flush()

    entry = _create_audit_entry(
        db,
        admin_user_id,
        AdminActionType.PLAN_OVERRIDE,
        target_org_id=org.id if org else None,
        target_user_id=owner.id,
        details={"old_plan": old_plan, "new_plan": new_plan, "reason": reason, "immediate": effective_immediately},
        ip_address=ip_address,
    )

    return {"success": True, "message": f"Plan changed from {old_plan} to {new_plan}", "audit_log_id": entry.id}


def admin_extend_trial(
    db: Session,
    org_id: int,
    days: int,
    reason: str,
    admin_user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Extend a customer's trial period."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    owner = db.query(User).filter(User.id == (org.owner_user_id if org else org_id)).first()
    if not owner:
        raise ValueError("Customer not found")

    sub = db.query(Subscription).filter(Subscription.user_id == owner.id).first()
    if not sub:
        raise ValueError("No subscription found")

    # Extend current_period_end
    if sub.current_period_end:
        sub.current_period_end = sub.current_period_end + timedelta(days=days)
    else:
        sub.current_period_end = datetime.now(UTC) + timedelta(days=days)

    # If not already trialing, set to trialing
    if sub.status != SubscriptionStatus.TRIALING:
        sub.status = SubscriptionStatus.TRIALING

    db.flush()

    entry = _create_audit_entry(
        db,
        admin_user_id,
        AdminActionType.TRIAL_EXTENSION,
        target_org_id=org.id if org else None,
        target_user_id=owner.id,
        details={"days": days, "reason": reason, "new_period_end": sub.current_period_end.isoformat()},
        ip_address=ip_address,
    )

    return {"success": True, "message": f"Trial extended by {days} days", "audit_log_id": entry.id}


def admin_issue_credit(
    db: Session,
    org_id: int,
    amount_cents: int,
    reason: str,
    admin_user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Issue a credit to a customer's Stripe balance."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    owner = db.query(User).filter(User.id == (org.owner_user_id if org else org_id)).first()
    if not owner:
        raise ValueError("Customer not found")

    sub = db.query(Subscription).filter(Subscription.user_id == owner.id).first()
    if not sub or not sub.stripe_customer_id:
        raise ValueError("No Stripe customer found — cannot issue credit")

    # Stripe API call
    from billing.stripe_client import get_stripe, is_stripe_enabled

    if is_stripe_enabled():
        stripe = get_stripe()
        stripe.Customer.modify(
            sub.stripe_customer_id,
            balance=-amount_cents,  # Negative = credit to customer
        )

    entry = _create_audit_entry(
        db,
        admin_user_id,
        AdminActionType.CREDIT_ISSUED,
        target_org_id=org.id if org else None,
        target_user_id=owner.id,
        details={"amount_cents": amount_cents, "reason": reason},
        ip_address=ip_address,
    )

    return {
        "success": True,
        "message": f"Credit of ${amount_cents / 100:.2f} issued",
        "audit_log_id": entry.id,
    }


def admin_issue_refund(
    db: Session,
    org_id: int,
    payment_intent_id: str,
    amount_cents: int,
    reason: str,
    admin_user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Issue a partial or full refund via Stripe."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    owner = db.query(User).filter(User.id == (org.owner_user_id if org else org_id)).first()
    if not owner:
        raise ValueError("Customer not found")

    from billing.stripe_client import get_stripe, is_stripe_enabled

    if is_stripe_enabled():
        stripe = get_stripe()
        stripe.Refund.create(
            payment_intent=payment_intent_id,
            amount=amount_cents,
            reason="requested_by_customer",
        )

    entry = _create_audit_entry(
        db,
        admin_user_id,
        AdminActionType.REFUND_ISSUED,
        target_org_id=org.id if org else None,
        target_user_id=owner.id,
        details={"payment_intent_id": payment_intent_id, "amount_cents": amount_cents, "reason": reason},
        ip_address=ip_address,
    )

    return {
        "success": True,
        "message": f"Refund of ${amount_cents / 100:.2f} issued",
        "audit_log_id": entry.id,
    }


def admin_force_cancel(
    db: Session,
    org_id: int,
    reason: str,
    immediate: bool,
    admin_user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Force cancel a customer's subscription."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    owner = db.query(User).filter(User.id == (org.owner_user_id if org else org_id)).first()
    if not owner:
        raise ValueError("Customer not found")

    sub = db.query(Subscription).filter(Subscription.user_id == owner.id).first()
    if not sub:
        raise ValueError("No subscription found")

    old_status = sub.status.value if sub.status else "unknown"

    if immediate:
        sub.status = SubscriptionStatus.CANCELED
        from models import UserTier

        owner.tier = UserTier.FREE
    else:
        sub.cancel_at_period_end = True

    db.flush()

    entry = _create_audit_entry(
        db,
        admin_user_id,
        AdminActionType.FORCE_CANCEL,
        target_org_id=org.id if org else None,
        target_user_id=owner.id,
        details={"reason": reason, "immediate": immediate, "old_status": old_status},
        ip_address=ip_address,
    )

    mode = "immediately" if immediate else "at period end"
    return {"success": True, "message": f"Subscription canceled {mode}", "audit_log_id": entry.id}


def admin_revoke_sessions(
    db: Session,
    org_id: int,
    admin_user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Revoke all active sessions for an org's users."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org:
        member_ids = [
            m.user_id
            for m in db.query(OrganizationMember.user_id).filter(OrganizationMember.organization_id == org.id).all()
        ]
    else:
        member_ids = [org_id]  # Solo user — org_id is user_id

    now = datetime.now(UTC)
    revoked_count = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id.in_(member_ids),
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .update({"revoked_at": now}, synchronize_session="fetch")
    )
    db.flush()

    entry = _create_audit_entry(
        db,
        admin_user_id,
        AdminActionType.SESSION_REVOKE,
        target_org_id=org.id if org else None,
        details={"revoked_count": revoked_count},
        ip_address=ip_address,
    )

    return {"success": True, "message": f"Revoked {revoked_count} active sessions", "audit_log_id": entry.id}


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------


def get_admin_audit_log(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 50,
    action_type: str | None = None,
    admin_user_id: int | None = None,
    target_org_id: int | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> dict:
    """Paginated admin audit log with filters."""
    query = db.query(AdminAuditLog)

    if action_type:
        query = query.filter(AdminAuditLog.action_type == action_type)
    if admin_user_id:
        query = query.filter(AdminAuditLog.admin_user_id == admin_user_id)
    if target_org_id:
        query = query.filter(AdminAuditLog.target_org_id == target_org_id)
    if since:
        query = query.filter(AdminAuditLog.created_at >= since)
    if until:
        query = query.filter(AdminAuditLog.created_at < until)

    total = query.count()

    entries = query.order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit).all()

    # Enrich with admin emails
    admin_ids = {e.admin_user_id for e in entries}
    admins = {u.id: u.email for u in db.query(User).filter(User.id.in_(admin_ids)).all()} if admin_ids else {}

    items = [
        {
            "id": e.id,
            "admin_user_id": e.admin_user_id,
            "admin_email": admins.get(e.admin_user_id),
            "action_type": e.action_type.value if e.action_type else "",
            "target_org_id": e.target_org_id,
            "target_user_id": e.target_user_id,
            "details_json": e.details_json,
            "ip_address": e.ip_address,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        }
        for e in entries
    ]

    return {"items": items, "total": total, "offset": offset, "limit": limit}


# ---------------------------------------------------------------------------
# Dunning helpers (Sprint 591)
# ---------------------------------------------------------------------------


def _get_dunning_info(db: Session, sub: Subscription) -> dict | None:
    """Get active dunning episode info for a subscription."""
    from dunning_model import DunningEpisode, DunningState

    episode = (
        db.query(DunningEpisode)
        .filter(
            DunningEpisode.subscription_id == sub.id,
            DunningEpisode.state.notin_([DunningState.CANCELED, DunningState.RESOLVED]),
        )
        .first()
    )

    if not episode:
        return None

    days_until_suspension = None
    if episode.state == DunningState.THIRD_ATTEMPT_FAILED and episode.last_failed_at:
        from billing.dunning_engine import GRACE_PERIOD_DAYS

        suspension_date = episode.last_failed_at + timedelta(days=GRACE_PERIOD_DAYS)
        days_until_suspension = max(0, (suspension_date - datetime.now(UTC)).days)

    return {
        "episode_id": episode.id,
        "state": episode.state.value,
        "failure_count": episode.failure_count,
        "first_failed_at": episode.first_failed_at.isoformat() if episode.first_failed_at else None,
        "last_failed_at": episode.last_failed_at.isoformat() if episode.last_failed_at else None,
        "next_retry_at": episode.next_retry_at.isoformat() if episode.next_retry_at else None,
        "days_until_suspension": days_until_suspension,
    }


def admin_resolve_dunning(
    db: Session,
    episode_id: int,
    reason: str,
    admin_user_id: int,
    ip_address: str | None = None,
) -> dict:
    """Manually resolve a dunning episode (admin action)."""
    from billing.dunning_engine import resolve_manually

    episode = resolve_manually(db, episode_id, reason)
    if not episode:
        raise ValueError("Dunning episode not found or already resolved")

    entry = _create_audit_entry(
        db,
        admin_user_id,
        AdminActionType.PLAN_OVERRIDE,
        target_org_id=episode.org_id,
        details={"action": "dunning_resolved", "episode_id": episode_id, "reason": reason},
        ip_address=ip_address,
    )

    return {"success": True, "message": "Dunning episode resolved", "audit_log_id": entry.id}
