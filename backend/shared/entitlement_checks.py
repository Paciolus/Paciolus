"""
FastAPI dependency functions for tier-based entitlement enforcement.

Sprint 363: Phase L — Pricing Strategy & Billing Infrastructure.

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


def check_diagnostic_limit(
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> User:
    """Check that the user hasn't exceeded their monthly diagnostic limit.

    Counts ActivityLog entries for the current calendar month.
    Returns the user if allowed, raises 403 if limit exceeded.
    """
    entitlements = get_entitlements(UserTier(user.tier.value))

    if entitlements.diagnostics_per_month == 0:
        return user  # unlimited

    # Count diagnostics this month
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

    if count >= entitlements.diagnostics_per_month:
        _raise_or_log(
            user,
            "diagnostics",
            f"Monthly diagnostic limit reached ({count}/{entitlements.diagnostics_per_month}). "
            f"Upgrade your plan for more diagnostics.",
        )

    return user


def check_client_limit(
    user: Annotated[User, Depends(require_current_user)],
    db: Session = Depends(get_db),
) -> User:
    """Check that the user hasn't exceeded their client limit.

    Counts active (non-archived) clients owned by the user.
    Returns the user if allowed, raises 403 if limit exceeded.
    """
    entitlements = get_entitlements(UserTier(user.tier.value))

    if entitlements.max_clients == 0:
        return user  # unlimited

    count = (
        db.query(func.count(Client.id))
        .filter(Client.user_id == user.id)
        .scalar()
    ) or 0

    if count >= entitlements.max_clients:
        _raise_or_log(
            user,
            "clients",
            f"Client limit reached ({count}/{entitlements.max_clients}). "
            f"Upgrade your plan to add more clients.",
        )

    return user


def check_tool_access(tool_name: str):
    """Factory that returns a dependency checking tool access for the given tool.

    Usage:
        @router.post("/je-testing/run")
        def run_je_testing(
            user: User = Depends(check_tool_access("journal_entry_testing")),
            ...
        ):
    """
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
                f"Tool '{tool_name}' is not available on your current plan. "
                f"Upgrade to access this tool.",
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
            "Engagement workspace is not available on your current plan. "
            "Upgrade to Professional or higher.",
        )

    return user
