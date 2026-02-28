"""
Paciolus API — Activity Logging & Dashboard Routes
"""

import logging
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import case, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from shared.audit_chain import stamp_chain_hash, verify_chain
from shared.error_messages import sanitize_error

logger = logging.getLogger(__name__)
from auth import require_current_user
from database import get_db
from models import ActivityLog, Client, User
from shared.helpers import get_filename_display, hash_filename
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


class ActivityHistoryResponse(BaseModel):
    activities: list[ActivityLogResponse]
    total_count: int
    page: int
    page_size: int


class DashboardStatsResponse(BaseModel):
    total_clients: int
    assessments_today: int
    last_assessment_date: Optional[str]
    total_assessments: int


@router.post("/activity/log", response_model=ActivityLogResponse, status_code=201)
@limiter.limit(RATE_LIMIT_WRITE)
def log_activity(
    request: Request,
    activity: ActivityLogCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
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
        db.flush()  # Populate id + timestamp before chain hash computation
        stamp_chain_hash(db, db_activity)
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


@router.get("/activity/history", response_model=ActivityHistoryResponse)
def get_activity_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's audit activity history."""
    log_secure_operation("activity_history_fetch", f"User {current_user.id} fetching activity history (page {page})")

    offset = (page - 1) * page_size
    results = (
        db.query(ActivityLog, func.count(ActivityLog.id).over().label("total_count"))
        .filter(
            ActivityLog.user_id == current_user.id,
            ActivityLog.archived_at.is_(None),
        )
        .order_by(ActivityLog.timestamp.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    if not results:
        return ActivityHistoryResponse(
            activities=[],
            total_count=0,
            page=page,
            page_size=page_size,
        )

    total_count = results[0][1]
    activities = [row[0] for row in results]

    return ActivityHistoryResponse(
        activities=[
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
        page=page,
        page_size=page_size,
    )


@router.delete("/activity/clear", status_code=204)
@limiter.limit(RATE_LIMIT_WRITE)
def clear_activity_history(
    request: Request, current_user: User = Depends(require_current_user), db: Session = Depends(get_db)
):
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
def get_dashboard_stats(current_user: User = Depends(require_current_user), db: Session = Depends(get_db)):
    """Get dashboard statistics for workspace header."""
    log_secure_operation("dashboard_stats_fetch", f"User {current_user.id} fetching dashboard stats")

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    total_clients = db.query(func.count(Client.id)).filter(Client.user_id == current_user.id).scalar() or 0

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

    return DashboardStatsResponse(
        total_clients=total_clients,
        assessments_today=assessments_today,
        last_assessment_date=last_assessment_date,
        total_assessments=total_assessments,
    )


# --- Chain Verification ---


class ChainLinkResponse(BaseModel):
    record_id: int
    expected_chain_hash: str
    actual_chain_hash: Optional[str]
    content_hash_matches: bool
    chain_valid: bool


class ChainVerificationResponse(BaseModel):
    user_id: int
    total_records: int
    verified_records: int
    first_broken_id: Optional[int]
    is_intact: bool
    links: list[ChainLinkResponse]


@router.get("/audit/chain-verify", response_model=ChainVerificationResponse)
def verify_audit_chain(
    start_id: Optional[int] = Query(default=None, ge=1),
    end_id: Optional[int] = Query(default=None, ge=1),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Verify the cryptographic integrity of the user's audit log chain.

    Walks the chain sequentially and checks that each record's chain_hash
    matches the expected HMAC-SHA256(previous_chain_hash + content_hash).
    Detects modifications, deletions, and insertions.
    """
    log_secure_operation(
        "chain_verify_request",
        f"User {current_user.id} verifying audit chain (start={start_id}, end={end_id})",
    )

    result = verify_chain(db, current_user.id, start_id, end_id)

    if not result.is_intact:
        log_secure_operation(
            "chain_integrity_failure",
            f"Chain break at record {result.first_broken_id} for user {current_user.id}",
        )

    return ChainVerificationResponse(
        user_id=result.user_id,
        total_records=result.total_records,
        verified_records=result.verified_records,
        first_broken_id=result.first_broken_id,
        is_intact=result.is_intact,
        links=[
            ChainLinkResponse(
                record_id=link.record_id,
                expected_chain_hash=link.expected_chain_hash,
                actual_chain_hash=link.actual_chain_hash,
                content_hash_matches=link.content_hash_matches,
                chain_valid=link.chain_valid,
            )
            for link in result.links
        ],
    )
