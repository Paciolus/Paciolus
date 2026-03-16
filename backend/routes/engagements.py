"""
Paciolus API — Engagement Routes
Phase X: Engagement Layer (metadata-only, Zero-Storage compliant)

Sprint 539: Decomposed into focused sub-modules:
  - engagements.py (this file) — CRUD operations + sub-router composition
  - engagements_analytics.py — convergence, trends, workpaper index, materiality
  - engagements_exports.py — anomaly summary PDF, package ZIP, convergence CSV
  - config/tool_taxonomy.py — centralized tool classification lists
"""

from datetime import datetime
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from engagement_manager import EngagementManager
from engagement_model import EngagementStatus, InvalidEngagementTransitionError, MaterialityBasis
from models import User
from routes.engagements_analytics import router as analytics_router
from routes.engagements_exports import router as exports_router
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

router = APIRouter(tags=["engagements"])

# Include sub-routers (all paths stay the same since sub-routers have no prefix)
router.include_router(analytics_router)
router.include_router(exports_router)

# Backward-compatible re-exports for any code importing schemas from this module
from routes.engagements_analytics import (  # noqa: F401, E402
    ConvergenceItemResponse,
    ConvergenceResponse,
    MaterialityResponse,
    ToolRunResponse,
    ToolRunTrendResponse,
    WorkpaperDocumentResponse,
    WorkpaperFollowUpSummaryResponse,
    WorkpaperIndexResponse,
    WorkpaperSignOffResponse,
)

# Kept here: convergence tool lists re-exported from canonical config source
from domain_config.tool_taxonomy import CONVERGENCE_EXCLUDED, CONVERGENCE_TOOLS  # noqa: F401, E402


# ---------------------------------------------------------------------------
# Pydantic schemas (CRUD)
# ---------------------------------------------------------------------------


class EngagementCreate(BaseModel):
    client_id: int
    period_start: datetime
    period_end: datetime
    materiality_basis: Optional[MaterialityBasis] = None
    materiality_percentage: Optional[float] = Field(None, ge=0, le=100)
    materiality_amount: Optional[float] = Field(None, ge=0)
    performance_materiality_factor: float = Field(0.75, gt=0, le=1)
    trivial_threshold_factor: float = Field(0.05, gt=0, le=1)


class EngagementUpdate(BaseModel):
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    status: Optional[EngagementStatus] = None
    materiality_basis: Optional[MaterialityBasis] = None
    materiality_percentage: Optional[float] = Field(None, ge=0, le=100)
    materiality_amount: Optional[float] = Field(None, ge=0)
    performance_materiality_factor: Optional[float] = Field(None, gt=0, le=1)
    trivial_threshold_factor: Optional[float] = Field(None, gt=0, le=1)


class EngagementResponse(BaseModel):
    id: int
    client_id: int
    period_start: str
    period_end: str
    status: Literal["active", "completed", "archived"]
    materiality_basis: Optional[Literal["revenue", "assets", "manual"]] = None
    materiality_percentage: Optional[float] = None
    materiality_amount: Optional[float] = None
    performance_materiality_factor: float
    trivial_threshold_factor: float
    completed_at: Optional[str] = None
    completed_by: Optional[int] = None
    created_by: int
    created_at: str
    updated_at: str


class EngagementListResponse(BaseModel):
    engagements: list[EngagementResponse]
    total_count: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _engagement_to_response(eng: Any) -> EngagementResponse:
    d = eng.to_dict()
    return EngagementResponse(
        id=d["id"],
        client_id=d["client_id"],
        period_start=d["period_start"] or "",
        period_end=d["period_end"] or "",
        status=d["status"] or "",
        materiality_basis=d["materiality_basis"],
        materiality_percentage=d["materiality_percentage"],
        materiality_amount=d["materiality_amount"],
        performance_materiality_factor=d["performance_materiality_factor"],
        trivial_threshold_factor=d["trivial_threshold_factor"],
        completed_at=d.get("completed_at"),
        completed_by=d.get("completed_by"),
        created_by=d["created_by"],
        created_at=d["created_at"] or "",
        updated_at=d["updated_at"] or "",
    )


# ---------------------------------------------------------------------------
# CRUD Endpoints
# ---------------------------------------------------------------------------


@router.post("/engagements", response_model=EngagementResponse, status_code=201)
@limiter.limit(RATE_LIMIT_WRITE)
def create_engagement(
    request: Request,
    data: EngagementCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> EngagementResponse:
    """Create a new engagement for a client."""
    log_secure_operation(
        "engagement_create",
        f"User {current_user.id} creating engagement for client {data.client_id}",
    )

    manager = EngagementManager(db)

    try:
        engagement = manager.create_engagement(
            user_id=current_user.id,
            client_id=data.client_id,
            period_start=data.period_start,
            period_end=data.period_end,
            materiality_basis=data.materiality_basis,
            materiality_percentage=data.materiality_percentage,
            materiality_amount=data.materiality_amount,
            performance_materiality_factor=data.performance_materiality_factor,
            trivial_threshold_factor=data.trivial_threshold_factor,
        )

        return _engagement_to_response(engagement)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="engagement_validation", allow_passthrough=True),
        )


@router.get("/engagements", response_model=EngagementListResponse)
def list_engagements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    client_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> EngagementListResponse:
    """List engagements with optional filters."""
    log_secure_operation(
        "engagements_list",
        f"User {current_user.id} listing engagements",
    )

    manager = EngagementManager(db)

    status_enum = EngagementStatus(status) if status else None
    offset = (page - 1) * page_size

    engagements, total = manager.get_engagements_for_user(
        user_id=current_user.id,
        client_id=client_id,
        status=status_enum,
        limit=page_size,
        offset=offset,
    )

    return EngagementListResponse(
        engagements=[_engagement_to_response(e) for e in engagements],
        total_count=total,
        page=page,
        page_size=page_size,
    )


@router.get("/engagements/{engagement_id}", response_model=EngagementResponse)
def get_engagement(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> EngagementResponse:
    """Get a specific engagement with ownership check."""
    manager = EngagementManager(db)
    engagement = manager.get_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return _engagement_to_response(engagement)


@router.put("/engagements/{engagement_id}", response_model=EngagementResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def update_engagement(
    request: Request,
    engagement_id: int,
    data: EngagementUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> EngagementResponse:
    """Update an engagement."""
    log_secure_operation(
        "engagement_update",
        f"User {current_user.id} updating engagement {engagement_id}",
    )

    manager = EngagementManager(db)

    try:
        engagement = manager.update_engagement(
            user_id=current_user.id,
            engagement_id=engagement_id,
            period_start=data.period_start,
            period_end=data.period_end,
            status=data.status,
            materiality_basis=data.materiality_basis,
            materiality_percentage=data.materiality_percentage,
            materiality_amount=data.materiality_amount,
            performance_materiality_factor=data.performance_materiality_factor,
            trivial_threshold_factor=data.trivial_threshold_factor,
        )

        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        return _engagement_to_response(engagement)

    except InvalidEngagementTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="engagement_validation", allow_passthrough=True),
        )


@router.delete("/engagements/{engagement_id}", status_code=204)
@limiter.limit(RATE_LIMIT_WRITE)
def archive_engagement(
    request: Request,
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Archive an engagement (soft delete)."""
    log_secure_operation(
        "engagement_archive",
        f"User {current_user.id} archiving engagement {engagement_id}",
    )

    manager = EngagementManager(db)
    engagement = manager.archive_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
