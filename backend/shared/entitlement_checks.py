"""
FastAPI dependency functions for tier-based entitlement enforcement.

Phase LXIX: Pricing Restructure v3.
- Renamed diagnostic→upload limits
- Added feature-level check functions (export_sharing, admin_dashboard, etc.)
- Updated seat enforcement with org member counting

These are injected as Depends() on routes that need gating.
When ENTITLEMENT_ENFORCEMENT is "soft", violations are logged but not blocked.
When "hard" (default), violations return 403 with upgrade_url.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from models import ActivityLog, Client, User, UserTier
from shared.entitlements import get_entitlements

logger = logging.getLogger(__name__)


def _get_enforcement_mode() -> str:
    """Get entitlement enforcement mode from config (lazy to avoid circular import)."""
    from config import _load_optional

    return _load_optional("ENTITLEMENT_ENFORCEMENT", "hard")


def _raise_or_log(user: User, resource: str, detail: str) -> None:
    """Raise 403 in hard mode, log warning in soft mode."""
    mode = _get_enforcement_mode()
    msg = f"Tier limit ({user.tier.value}): {detail} [user_id={user.id}]"

    if mode == "soft":
        logger.warning("SOFT entitlement block: %s", msg)
        return

    raise HTTPException(
        status_code=403,
        detail={
            "code": "TIER_LIMIT_EXCEEDED",
            "message": detail,
            "resource": resource,
            "current_tier": user.tier.value,
            "upgrade_url": "/pricing",
        },
    )


def check_upload_limit(
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> User:
    """Check that the user hasn't exceeded their monthly upload limit.

    Uses Subscription.uploads_used_current_period if available,
    falls back to ActivityLog counting for free tier.
    Returns the user if allowed, raises 403 if limit exceeded.
    """
    entitlements = get_entitlements(UserTier(user.tier.value))

    if entitlements.uploads_per_month == 0:
        return user  # unlimited

    # Try subscription-based counting first
    from subscription_model import Subscription

    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if sub and sub.uploads_used_current_period is not None:
        count = sub.uploads_used_current_period
    else:
        # Fall back to ActivityLog counting (free tier / no subscription)
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = (
            db.query(func.count(ActivityLog.id))
            .filter(
                ActivityLog.user_id == user.id,
                ActivityLog.timestamp >= month_start,
                ActivityLog.archived_at.is_(None),
            )
            .scalar()
        ) or 0

    if count >= entitlements.uploads_per_month:
        _raise_or_log(
            user,
            "uploads",
            f"Monthly upload limit reached ({count}/{entitlements.uploads_per_month}). "
            f"Upgrade your plan for more uploads.",
        )

    return user


# Backward compatibility alias
check_diagnostic_limit = check_upload_limit


def increment_upload_count(db: Session, user_id: int) -> None:
    """Increment the upload counter on the user's subscription.

    Called after a successful upload/analysis.
    No-op if user has no subscription (free tier uses ActivityLog counting).
    """
    from subscription_model import Subscription

    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub:
        sub.uploads_used_current_period = (sub.uploads_used_current_period or 0) + 1
        db.commit()


def check_client_limit(
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> User:
    """Check that the user hasn't exceeded their client limit."""
    entitlements = get_entitlements(UserTier(user.tier.value))

    if entitlements.max_clients == 0:
        return user  # unlimited

    count = (db.query(func.count(Client.id)).filter(Client.user_id == user.id).scalar()) or 0

    if count >= entitlements.max_clients:
        _raise_or_log(
            user,
            "clients",
            f"Client limit reached ({count}/{entitlements.max_clients}). Upgrade your plan to add more clients.",
        )

    return user


def check_tool_access(tool_name: str):
    """Factory that returns a dependency checking tool access for the given tool."""

    def _dependency(
        user: Annotated[User, Depends(require_current_user)],
    ) -> User:
        entitlements = get_entitlements(UserTier(user.tier.value))

        # Empty set = all tools allowed
        if not entitlements.tools_allowed:
            return user

        if tool_name not in entitlements.tools_allowed:
            _raise_or_log(
                user,
                "tool_access",
                f"Tool '{tool_name}' is not available on your current plan. Upgrade to access this tool.",
            )

        return user

    return _dependency


def check_format_access(format_name: str):
    """Factory that returns a dependency checking format access for the given format."""

    def _dependency(
        user: Annotated[User, Depends(require_current_user)],
    ) -> User:
        entitlements = get_entitlements(UserTier(user.tier.value))

        # Empty set = all formats allowed
        if not entitlements.formats_allowed:
            return user

        if format_name not in entitlements.formats_allowed:
            _raise_or_log(
                user,
                "format_access",
                f"File format '{format_name}' is not available on your current plan. Upgrade to access this format.",
            )

        return user

    return _dependency


def check_workspace_access(
    user: Annotated[User, Depends(require_current_user)],
) -> User:
    """Check that the user's tier includes engagement workspace access."""
    entitlements = get_entitlements(UserTier(user.tier.value))

    if not entitlements.workspace:
        _raise_or_log(
            user,
            "workspace",
            "Engagement workspace is not available on your current plan. Upgrade to Solo or higher.",
        )

    return user


def check_export_access(
    user: Annotated[User, Depends(require_current_user)],
) -> User:
    """Check that the user's tier allows any export (PDF/Excel/CSV).

    Free tier has no export capability (view-only).
    """
    entitlements = get_entitlements(UserTier(user.tier.value))

    if not entitlements.pdf_export and not entitlements.excel_export and not entitlements.csv_export:
        _raise_or_log(
            user,
            "export",
            "Exports are not available on the Free plan. Upgrade to Solo or higher for export access.",
        )

    return user


def check_export_sharing_access(
    user: Annotated[User, Depends(require_current_user)],
) -> User:
    """Check that the user's tier includes export sharing (Professional+)."""
    entitlements = get_entitlements(UserTier(user.tier.value))

    if not entitlements.export_sharing:
        _raise_or_log(
            user,
            "export_sharing",
            "Export sharing is not available on your current plan. Upgrade to Professional or higher.",
        )

    return user


def check_admin_dashboard_access(
    user: Annotated[User, Depends(require_current_user)],
) -> User:
    """Check that the user's tier includes admin dashboard access (Professional+)."""
    entitlements = get_entitlements(UserTier(user.tier.value))

    if not entitlements.admin_dashboard:
        _raise_or_log(
            user,
            "admin_dashboard",
            "Admin dashboard is not available on your current plan. Upgrade to Professional or higher.",
        )

    return user


def check_activity_log_access(
    user: Annotated[User, Depends(require_current_user)],
) -> User:
    """Check that the user's tier includes team activity log access (Professional+)."""
    entitlements = get_entitlements(UserTier(user.tier.value))

    if not entitlements.activity_logs:
        _raise_or_log(
            user,
            "activity_logs",
            "Team activity logs are not available on your current plan. Upgrade to Professional or higher.",
        )

    return user


def check_bulk_upload_access(
    user: Annotated[User, Depends(require_current_user)],
) -> User:
    """Check that the user's tier includes bulk upload (Enterprise only)."""
    entitlements = get_entitlements(UserTier(user.tier.value))

    if not entitlements.bulk_upload:
        _raise_or_log(
            user,
            "bulk_upload",
            "Bulk upload is not available on your current plan. Upgrade to Enterprise for bulk upload.",
        )

    return user


def check_custom_branding_access(
    user: Annotated[User, Depends(require_current_user)],
) -> User:
    """Check that the user's tier includes custom branding (Enterprise only)."""
    entitlements = get_entitlements(UserTier(user.tier.value))

    if not entitlements.custom_branding:
        _raise_or_log(
            user,
            "custom_branding",
            "Custom branding is not available on your current plan. Upgrade to Enterprise for custom branding.",
        )

    return user


def _get_seat_enforcement_mode() -> str:
    """Get seat enforcement mode from config (lazy to avoid circular import)."""
    from config import _load_optional

    return _load_optional("SEAT_ENFORCEMENT_MODE", "hard")


# Default free-tier seat cap applied when no org subscription exists
_FREE_TIER_SEAT_CAP = 1


def _resolve_org_subscription(db: Session, org_id: int):
    """Resolve the authoritative subscription for an organization.

    Looks up via org.subscription_id first. Falls back to the org owner's
    active subscription if subscription_id is null (org-first lifecycle).
    Returns (Subscription | None, TierEntitlements).
    """
    from organization_model import Organization
    from subscription_model import Subscription, SubscriptionStatus

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None, get_entitlements(UserTier.FREE)

    sub = None
    if org.subscription_id:
        sub = db.query(Subscription).filter(Subscription.id == org.subscription_id).first()

    # Fallback: resolve from org owner's active subscription
    if sub is None and org.owner_user_id:
        sub = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == org.owner_user_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]),
            )
            .first()
        )
        # Backfill the linkage if found
        if sub is not None:
            org.subscription_id = sub.id
            db.flush()

    if sub is None:
        return None, get_entitlements(UserTier.FREE)

    tier = UserTier(sub.tier) if sub.tier else UserTier.FREE
    return sub, get_entitlements(tier)


def check_seat_limit_for_org(db: Session, org_id: int, exclude_invite_id: int | None = None) -> None:
    """Check seat limit against the org's subscription (not the caller's).

    Raises HTTPException 403 if the org has exceeded its seat allocation.
    If no org subscription exists, enforces a default free-tier seat cap.

    Args:
        exclude_invite_id: If provided, subtract 1 from the pending invite count.
            Used during invite acceptance to avoid double-counting the invite being
            consumed (it converts from pending to accepted, not adding a new seat).
    """
    from organization_model import OrganizationMember

    sub, entitlements = _resolve_org_subscription(db, org_id)

    if sub is not None:
        total_seats = sub.total_seats
    else:
        # No subscription — enforce free-tier default cap
        total_seats = _FREE_TIER_SEAT_CAP

    if total_seats <= 0:
        return

    member_count = (
        db.query(func.count(OrganizationMember.id)).filter(OrganizationMember.organization_id == org_id).scalar()
    ) or 0

    # Include pending invites in count to prevent over-invitation
    from organization_model import InviteStatus, OrganizationInvite

    pending_invites = (
        db.query(func.count(OrganizationInvite.id))
        .filter(
            OrganizationInvite.organization_id == org_id,
            OrganizationInvite.status == InviteStatus.PENDING,
        )
        .scalar()
    ) or 0

    # When accepting an invite, exclude the invite being accepted from the
    # pending count — it's being converted, not adding a new seat.
    if exclude_invite_id is not None and pending_invites > 0:
        pending_invites -= 1

    effective_count = member_count + pending_invites

    mode = _get_seat_enforcement_mode()
    if effective_count >= total_seats:
        tier_label = sub.tier if sub else "free"
        detail = f"Organization seat limit reached ({effective_count}/{total_seats}). Add more seats or remove members."
        msg = f"Seat limit ({tier_label}): {detail} [org_id={org_id}]"
        if mode == "soft":
            logger.warning("SOFT seat enforcement: %s", msg)
        else:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "TIER_LIMIT_EXCEEDED",
                    "message": detail,
                    "resource": "seats",
                    "current_tier": tier_label,
                    "upgrade_url": "/pricing",
                },
            )


def check_seat_limit(
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> User:
    """Check that the user's organization hasn't exceeded its seat allocation.

    Delegates to check_seat_limit_for_org using the user's org context,
    ensuring enforcement runs against the org subscription regardless of
    who the caller is.
    """
    if not user.organization_id:
        return user

    check_seat_limit_for_org(db, user.organization_id)

    return user
