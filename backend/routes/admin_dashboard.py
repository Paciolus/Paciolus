"""
Admin Dashboard Routes — Phase LXIX: Pricing v3 (Phase 7).

Team activity overview, member usage, and activity export.
Gated to Professional+ tiers with admin_dashboard entitlement.

Route group prefix: /admin
"""

import csv
import io
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from models import ActivityLog, User
from organization_model import Organization, OrganizationMember
from shared.entitlement_checks import check_admin_dashboard_access
from shared.filenames import sanitize_csv_value
from shared.organization_schemas import (
    AdminOverviewResponse,
    TeamActivityEntryResponse,
    UsageByMemberResponse,
)
from shared.rate_limits import RATE_LIMIT_DEFAULT, RATE_LIMIT_EXPORT, limiter
from team_activity_model import TeamActivityLog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_admin_org(db: Session, user: User) -> Organization:
    """Get the user's org and verify admin_dashboard access."""
    # AUDIT-08: pass db so subscription status is checked (not sessionless fallback)
    check_admin_dashboard_access(user, db)

    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="No organization found.")

    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    # Only owner/admin can access dashboard
    from organization_model import OrgRole

    if member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        logger.warning("403 access denied: user_id=%s, required_role=admin_or_owner", user.id)
        raise HTTPException(status_code=403, detail="Access denied.")

    return org


def _org_member_ids(db: Session, org_id: int) -> list[int]:
    """Get all user IDs in an organization."""
    members = db.query(OrganizationMember.user_id).filter(OrganizationMember.organization_id == org_id).all()
    return [m.user_id for m in members]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/overview", response_model=AdminOverviewResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
async def get_overview(
    request: Any = None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Overview: seats, uploads this month, active members."""
    org = _get_admin_org(db, user)
    member_ids = _org_member_ids(db, org.id)

    # Seat count
    total_members = len(member_ids)

    # Uploads this month (from ActivityLog — uses .timestamp, not .created_at)
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    uploads_this_month = (
        db.query(func.count(ActivityLog.id))
        .filter(
            ActivityLog.user_id.in_(member_ids),
            ActivityLog.timestamp >= month_start,
        )
        .scalar()
        or 0
    )

    # Active members (any activity in last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    active_members = (
        db.query(func.count(func.distinct(TeamActivityLog.user_id)))
        .filter(
            TeamActivityLog.organization_id == org.id,
            TeamActivityLog.created_at >= thirty_days_ago,
        )
        .scalar()
        or 0
    )

    # Tool usage distribution (TeamActivityLog has tool_name; ActivityLog does not)
    tool_usage = (
        db.query(TeamActivityLog.tool_name, func.count(TeamActivityLog.id))
        .filter(
            TeamActivityLog.organization_id == org.id,
            TeamActivityLog.created_at >= month_start,
        )
        .group_by(TeamActivityLog.tool_name)
        .all()
    )

    return {
        "total_members": total_members,
        "uploads_this_month": uploads_this_month,
        "active_members_30d": active_members,
        "tool_usage": {name: count for name, count in tool_usage if name},
        "organization_name": org.name,
    }


@router.get("/team-activity", response_model=list[TeamActivityEntryResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
async def get_team_activity(
    request: Any = None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=90),
    tool_name: str | None = Query(default=None),
    member_id: int | None = Query(default=None),
) -> list[dict[str, Any]]:
    """Filterable team activity log."""
    org = _get_admin_org(db, user)

    query = db.query(TeamActivityLog).filter(
        TeamActivityLog.organization_id == org.id,
        TeamActivityLog.created_at >= datetime.now(UTC) - timedelta(days=days),
    )

    if tool_name:
        query = query.filter(TeamActivityLog.tool_name == tool_name)
    if member_id:
        query = query.filter(TeamActivityLog.user_id == member_id)

    activities = query.order_by(TeamActivityLog.created_at.desc()).limit(500).all()

    # Enrich with user names
    member_ids = _org_member_ids(db, org.id)
    users = {u.id: u for u in db.query(User).filter(User.id.in_(member_ids)).all()}

    results = []
    for act in activities:
        d = act.to_dict()
        u = users.get(act.user_id)
        d["user_name"] = u.name or u.email if u else "Unknown"
        results.append(d)

    return results


@router.get("/usage-by-member", response_model=list[UsageByMemberResponse])
@limiter.limit(RATE_LIMIT_DEFAULT)
async def get_usage_by_member(
    request: Any = None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Per-member upload counts for the current month."""
    org = _get_admin_org(db, user)
    member_ids = _org_member_ids(db, org.id)

    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    usage = (
        db.query(ActivityLog.user_id, func.count(ActivityLog.id))
        .filter(
            ActivityLog.user_id.in_(member_ids),
            ActivityLog.timestamp >= month_start,
        )
        .group_by(ActivityLog.user_id)
        .all()
    )

    users = {u.id: u for u in db.query(User).filter(User.id.in_(member_ids)).all()}

    return [
        {
            "user_id": uid,
            "user_name": users[uid].name or users[uid].email if uid in users else "Unknown",
            "uploads": count,
        }
        for uid, count in usage
    ]


@router.get("/export-activity-csv")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_activity_csv(
    request: Any = None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
    days: int = Query(default=90, ge=1, le=90),
) -> StreamingResponse:
    """Export team activity as CSV."""
    org = _get_admin_org(db, user)

    activities = (
        db.query(TeamActivityLog)
        .filter(
            TeamActivityLog.organization_id == org.id,
            TeamActivityLog.created_at >= datetime.now(UTC) - timedelta(days=days),
        )
        .order_by(TeamActivityLog.created_at.desc())
        .all()
    )

    member_ids = _org_member_ids(db, org.id)
    users = {u.id: u for u in db.query(User).filter(User.id.in_(member_ids)).all()}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "User", "Action", "Tool"])

    for act in activities:
        u = users.get(act.user_id)
        writer.writerow(
            [
                act.created_at.isoformat() if act.created_at else "",
                sanitize_csv_value(u.name or u.email if u else "Unknown"),
                sanitize_csv_value(act.action_type.value if act.action_type else ""),
                sanitize_csv_value(act.tool_name or ""),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=team-activity.csv"},
    )
