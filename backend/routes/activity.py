"""
Paciolus API — Activity Logging & Dashboard Routes

Sprint 579: Multi-tool activity tracking, unified dashboard stats,
user tool preferences (favorites).
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import case, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from shared.error_messages import sanitize_error

logger = logging.getLogger(__name__)
from auth import require_current_user, require_verified_user
from database import get_db
from models import ActivityLog, Client, ToolActivity, User
from shared.audit_chain import GENESIS_HASH, compute_chain_hash, verify_audit_chain
from shared.filenames import (
    get_filename_display,
    hash_filename,
)
from shared.rate_limits import RATE_LIMIT_WRITE, limiter
from shared.soft_delete import soft_delete_bulk

router = APIRouter(tags=["activity"])


class ActivityLogCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=500)
    record_count: int
    total_debits: float
    total_credits: float
    materiality_threshold: float
    was_balanced: bool
    anomaly_count: int = 0
    material_count: int = 0
    immaterial_count: int = 0
    is_consolidated: bool = False
    sheet_count: Optional[int] = None


class ActivityLogResponse(BaseModel):
    id: int
    filename_hash: str
    filename_display: Optional[str]
    timestamp: str
    record_count: int
    total_debits: float
    total_credits: float
    materiality_threshold: float
    was_balanced: bool
    anomaly_count: int
    material_count: int
    immaterial_count: int
    is_consolidated: bool
    sheet_count: Optional[int]
    chain_hash: Optional[str] = None


from shared.pagination import PaginatedResponse, PaginationParams

# Backward compat alias
ActivityHistoryResponse = PaginatedResponse[ActivityLogResponse]


class ChainVerifyResponse(BaseModel):
    is_valid: bool
    records_checked: int
    first_broken_id: Optional[int] = None
    error_message: Optional[str] = None


class DashboardStatsResponse(BaseModel):
    total_clients: int
    assessments_today: int
    last_assessment_date: Optional[str]
    total_assessments: int
    # Sprint 579: Multi-tool stats
    tool_runs_today: int = 0
    total_tool_runs: int = 0
    active_workspaces: int = 0
    tools_used: int = 0


class ToolActivityResponse(BaseModel):
    """Unified tool activity entry for the dashboard feed."""

    id: int
    tool_name: str
    tool_label: str
    filename: Optional[str] = None
    record_count: Optional[int] = None
    summary: Optional[dict[str, Any]] = None
    created_at: str


class UserPreferencesResponse(BaseModel):
    """User tool preferences (favorites, etc.)."""

    favorite_tools: list[str] = Field(default_factory=list)


class UserPreferencesInput(BaseModel):
    """Input for updating user preferences."""

    favorite_tools: list[str] = Field(default_factory=list, max_length=15)


@router.post("/activity/log", response_model=ActivityLogResponse, status_code=201)
@limiter.limit(RATE_LIMIT_WRITE)
def log_activity(
    request: Request,
    activity: ActivityLogCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ActivityLogResponse:
    """Log audit activity. Stores only aggregate metadata, filename is hashed."""
    log_secure_operation("activity_log_create", f"User {current_user.id} logging audit activity")

    db_activity = ActivityLog(
        user_id=current_user.id,
        filename_hash=hash_filename(activity.filename),
        filename_display=get_filename_display(activity.filename),
        record_count=activity.record_count,
        total_debits=activity.total_debits,
        total_credits=activity.total_credits,
        materiality_threshold=activity.materiality_threshold,
        was_balanced=activity.was_balanced,
        anomaly_count=activity.anomaly_count,
        material_count=activity.material_count,
        immaterial_count=activity.immaterial_count,
        is_consolidated=activity.is_consolidated,
        sheet_count=activity.sheet_count,
    )

    try:
        db.add(db_activity)
        db.flush()  # Assigns ID + timestamp before chain hash computation

        # Sprint 461: Compute cryptographic chain hash (SOC 2 CC7.4)
        previous_record = (
            db.query(ActivityLog)
            .filter(
                ActivityLog.id < db_activity.id,
                ActivityLog.archived_at.is_(None),
                ActivityLog.chain_hash.isnot(None),
            )
            .order_by(ActivityLog.id.desc())
            .first()
        )
        previous_hash = previous_record.chain_hash if previous_record else GENESIS_HASH
        db_activity.chain_hash = compute_chain_hash(previous_hash or GENESIS_HASH, db_activity)

        db.commit()
        db.refresh(db_activity)
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error creating activity log")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_activity_create"))

    log_secure_operation("activity_log_created", f"Activity {db_activity.id} created for user {current_user.id}")

    return ActivityLogResponse(
        id=db_activity.id,
        filename_hash=db_activity.filename_hash,
        filename_display=db_activity.filename_display,
        timestamp=db_activity.timestamp.isoformat(),
        record_count=db_activity.record_count,
        total_debits=db_activity.total_debits,
        total_credits=db_activity.total_credits,
        materiality_threshold=db_activity.materiality_threshold,
        was_balanced=db_activity.was_balanced,
        anomaly_count=db_activity.anomaly_count,
        material_count=db_activity.material_count,
        immaterial_count=db_activity.immaterial_count,
        is_consolidated=db_activity.is_consolidated,
        sheet_count=db_activity.sheet_count,
        chain_hash=db_activity.chain_hash,
    )


class RecentActivityResponse(BaseModel):
    """Lightweight activity entry for dashboard recent-history widget."""

    id: int
    filename: Optional[str]
    created_at: str
    was_balanced: bool
    record_count: int
    anomaly_count: int


@router.get("/activity/recent", response_model=list[RecentActivityResponse])
def get_recent_activity(
    limit: int = Query(default=5, ge=1, le=50),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[RecentActivityResponse]:
    """Get the most recent activity entries for the dashboard.

    Returns a flat JSON array (not paginated) of the N most recent
    activity log entries for the authenticated user.
    """
    activities = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.archived_at.is_(None),
        )
        .order_by(ActivityLog.timestamp.desc(), ActivityLog.id.desc())
        .limit(limit)
        .all()
    )

    return [
        RecentActivityResponse(
            id=a.id,
            filename=a.filename_display,
            created_at=a.timestamp.isoformat(),
            was_balanced=a.was_balanced,
            record_count=a.record_count,
            anomaly_count=a.anomaly_count,
        )
        for a in activities
    ]


@router.get("/activity/history", response_model=PaginatedResponse[ActivityLogResponse])
def get_activity_history(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ActivityLogResponse]:
    """Get the authenticated user's audit activity history."""
    log_secure_operation(
        "activity_history_fetch", f"User {current_user.id} fetching activity history (page {pagination.page})"
    )

    results = (
        db.query(ActivityLog, func.count(ActivityLog.id).over().label("total_count"))
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.archived_at.is_(None),
        )
        .order_by(ActivityLog.timestamp.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
        .all()
    )

    if not results:
        return PaginatedResponse[ActivityLogResponse](
            items=[],
            total_count=0,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    total_count = results[0][1]
    activities = [row[0] for row in results]

    return PaginatedResponse[ActivityLogResponse](
        items=[
            ActivityLogResponse(
                id=a.id,
                filename_hash=a.filename_hash,
                filename_display=a.filename_display,
                timestamp=a.timestamp.isoformat(),
                record_count=a.record_count,
                total_debits=a.total_debits,
                total_credits=a.total_credits,
                materiality_threshold=a.materiality_threshold,
                was_balanced=a.was_balanced,
                anomaly_count=a.anomaly_count,
                material_count=a.material_count,
                immaterial_count=a.immaterial_count,
                is_consolidated=a.is_consolidated,
                sheet_count=a.sheet_count,
                chain_hash=a.chain_hash,
            )
            for a in activities
        ],
        total_count=total_count,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.delete("/activity/clear", status_code=204)
@limiter.limit(RATE_LIMIT_WRITE)
def clear_activity_history(
    request: Request, current_user: User = Depends(require_current_user), db: Session = Depends(get_db)
) -> None:
    """Clear all activity history for the user (soft-delete: sets archived_at)."""
    log_secure_operation("activity_clear_request", f"User {current_user.id} requesting activity history archival")

    try:
        archived_count = soft_delete_bulk(
            db,
            db.query(ActivityLog).filter(
                ActivityLog.user_id == current_user.id,
                ActivityLog.archived_at.is_(None),
            ),
            user_id=current_user.id,
            reason="user_clear_history",
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error archiving activity history")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_activity_clear"))

    log_secure_operation(
        "activity_clear_complete", f"Archived {archived_count} activity entries for user {current_user.id}"
    )


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_user: User = Depends(require_current_user), db: Session = Depends(get_db)
) -> DashboardStatsResponse:
    """Get dashboard statistics — includes multi-tool activity (Sprint 579)."""
    log_secure_operation("dashboard_stats_fetch", f"User {current_user.id} fetching dashboard stats")

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    total_clients = db.query(func.count(Client.id)).filter(Client.user_id == current_user.id).scalar() or 0

    # Legacy TB-only stats (backward compat)
    activity_stats = (
        db.query(
            func.count(ActivityLog.id).label("total_assessments"),
            func.sum(case((ActivityLog.timestamp >= today_start, 1), else_=0)).label("assessments_today"),
            func.max(ActivityLog.timestamp).label("last_assessment_date"),
        )
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.archived_at.is_(None),
        )
        .first()
    )

    total_assessments = activity_stats.total_assessments or 0 if activity_stats else 0
    assessments_today = activity_stats.assessments_today or 0 if activity_stats else 0
    last_assessment_date = None
    if activity_stats and activity_stats.last_assessment_date:
        last_assessment_date = activity_stats.last_assessment_date.isoformat()

    # Sprint 579: Multi-tool stats from ToolActivity
    tool_stats = (
        db.query(
            func.count(ToolActivity.id).label("total_tool_runs"),
            func.sum(case((ToolActivity.timestamp >= today_start, 1), else_=0)).label("tool_runs_today"),
            func.count(func.distinct(ToolActivity.tool_name)).label("tools_used"),
        )
        .filter(ToolActivity.user_id == current_user.id)
        .first()
    )

    total_tool_runs = tool_stats.total_tool_runs or 0 if tool_stats else 0
    tool_runs_today = tool_stats.tool_runs_today or 0 if tool_stats else 0
    tools_used = tool_stats.tools_used or 0 if tool_stats else 0

    # Use ToolActivity last timestamp if newer than ActivityLog
    tool_last = db.query(func.max(ToolActivity.timestamp)).filter(ToolActivity.user_id == current_user.id).scalar()
    if tool_last and (not last_assessment_date or tool_last.isoformat() > last_assessment_date):
        last_assessment_date = tool_last.isoformat()

    # Active workspaces count (Engagement uses status enum, not SoftDeleteMixin)
    from engagement_model import Engagement, EngagementStatus

    active_workspaces = (
        db.query(func.count(Engagement.id))
        .filter(
            Engagement.created_by == current_user.id,
            Engagement.status == EngagementStatus.ACTIVE,
        )
        .scalar()
    ) or 0

    return DashboardStatsResponse(
        total_clients=total_clients,
        assessments_today=assessments_today,
        last_assessment_date=last_assessment_date,
        total_assessments=total_assessments,
        tool_runs_today=tool_runs_today,
        total_tool_runs=total_tool_runs,
        active_workspaces=active_workspaces,
        tools_used=tools_used,
    )


# =============================================================================
# Sprint 579: Multi-Tool Activity Feed & User Preferences
# =============================================================================

# Mapping from backend tool_name to user-friendly label
TOOL_LABELS: dict[str, str] = {
    "trial_balance": "TB Diagnostics",
    "multi_period": "Multi-Period Analysis",
    "journal_entry_testing": "Journal Entry Testing",
    "ap_testing": "AP Testing",
    "bank_reconciliation": "Bank Reconciliation",
    "payroll_testing": "Payroll Testing",
    "three_way_match": "Three-Way Match",
    "revenue_testing": "Revenue Testing",
    "ar_aging": "AR Aging",
    "fixed_asset_testing": "Fixed Assets",
    "inventory_testing": "Inventory Testing",
    "statistical_sampling": "Statistical Sampling",
    "flux_analysis": "Flux Analysis",
}


@router.get("/activity/tool-feed", response_model=list[ToolActivityResponse])
def get_tool_activity_feed(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[ToolActivityResponse]:
    """Get unified tool activity feed across all tools for the dashboard."""
    activities = (
        db.query(ToolActivity)
        .filter(ToolActivity.user_id == current_user.id)
        .order_by(ToolActivity.timestamp.desc())
        .limit(limit)
        .all()
    )

    result = []
    for a in activities:
        summary = None
        if a.summary_json:
            try:
                summary = json.loads(a.summary_json)
            except (json.JSONDecodeError, TypeError):
                summary = None

        result.append(
            ToolActivityResponse(
                id=a.id,
                tool_name=a.tool_name,
                tool_label=TOOL_LABELS.get(a.tool_name, a.tool_name),
                filename=a.filename_display,
                record_count=a.record_count,
                summary=summary,
                created_at=a.timestamp.isoformat(),
            )
        )
    return result


@router.post("/activity/tool-log", response_model=ToolActivityResponse, status_code=201)
@limiter.limit(RATE_LIMIT_WRITE)
def log_tool_activity(
    request: Request,
    tool_name: str = Query(..., min_length=1, max_length=50),
    filename: Optional[str] = Query(default=None, max_length=500),
    record_count: Optional[int] = Query(default=None),
    summary: Optional[str] = Query(default=None, max_length=2000),
    engagement_id: Optional[int] = Query(default=None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ToolActivityResponse:
    """Log a tool execution to the unified activity feed."""
    display_name = get_filename_display(filename) if filename else None

    db_activity = ToolActivity(
        user_id=current_user.id,
        tool_name=tool_name,
        filename_display=display_name,
        record_count=record_count,
        summary_json=summary,
        engagement_id=engagement_id,
    )

    try:
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error creating tool activity")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_tool_activity"))

    parsed_summary = None
    if db_activity.summary_json:
        try:
            parsed_summary = json.loads(db_activity.summary_json)
        except (json.JSONDecodeError, TypeError):
            pass

    return ToolActivityResponse(
        id=db_activity.id,
        tool_name=db_activity.tool_name,
        tool_label=TOOL_LABELS.get(db_activity.tool_name, db_activity.tool_name),
        filename=db_activity.filename_display,
        record_count=db_activity.record_count,
        summary=parsed_summary,
        created_at=db_activity.timestamp.isoformat(),
    )


@router.get("/settings/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    current_user: User = Depends(require_current_user),
) -> UserPreferencesResponse:
    """Get the current user's tool preferences (favorites)."""
    try:
        settings = json.loads(current_user.settings or "{}")
    except (json.JSONDecodeError, TypeError):
        settings = {}

    return UserPreferencesResponse(
        favorite_tools=settings.get("favorite_tools", []),
    )


@router.put("/settings/preferences", response_model=UserPreferencesResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def update_user_preferences(
    request: Request,
    prefs: UserPreferencesInput,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> UserPreferencesResponse:
    """Update user tool preferences (favorites)."""
    try:
        settings = json.loads(current_user.settings or "{}")
    except (json.JSONDecodeError, TypeError):
        settings = {}

    # Validate tool names
    valid_tools = set(TOOL_LABELS.keys())
    for tool in prefs.favorite_tools:
        if tool not in valid_tools:
            raise HTTPException(status_code=422, detail=f"Unknown tool: {tool}")

    settings["favorite_tools"] = prefs.favorite_tools

    try:
        current_user.settings = json.dumps(settings)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error updating user preferences")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_prefs_update"))

    return UserPreferencesResponse(favorite_tools=prefs.favorite_tools)


# =============================================================================
# Audit Chain Verification (Sprint 461 — SOC 2 CC7.4)
# =============================================================================


@router.get("/audit/chain-verify", response_model=ChainVerifyResponse)
def verify_chain(
    start_id: int = Query(..., ge=1),
    end_id: int = Query(..., ge=1),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> ChainVerifyResponse:
    """Verify the integrity of the audit log hash chain between two record IDs.

    Traverses the chain from start_id to end_id and recomputes each HMAC-SHA512
    hash to detect tampering. Requires a verified user account.

    Sprint 461: Cryptographic audit log chaining (SOC 2 CC7.4).
    """
    if end_id < start_id:
        raise HTTPException(
            status_code=422,
            detail="end_id must be greater than or equal to start_id.",
        )

    log_secure_operation(
        "audit_chain_verify",
        f"User {current_user.id} verifying chain integrity (IDs {start_id}-{end_id})",
    )

    result = verify_audit_chain(db, start_id, end_id, user_id=current_user.id)

    return ChainVerifyResponse(
        is_valid=result.is_valid,
        records_checked=result.records_checked,
        first_broken_id=result.first_broken_id,
        error_message=result.error_message,
    )
