"""
Engagement analytics routes — convergence index, tool-run trends, workpaper index.

Split from engagements.py (Sprint 539).
"""

from datetime import UTC, datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from domain_config.tool_taxonomy import CONVERGENCE_EXCLUDED, CONVERGENCE_TOOLS
from engagement_manager import EngagementManager
from models import User
from shared.error_messages import sanitize_error
from workpaper_index_generator import WorkpaperIndexGenerator

router = APIRouter(tags=["engagements"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class MaterialityResponse(BaseModel):
    overall_materiality: float
    performance_materiality: float
    trivial_threshold: float
    materiality_basis: Optional[str] = None
    materiality_percentage: Optional[float] = None
    performance_materiality_factor: float
    trivial_threshold_factor: float


class ToolRunResponse(BaseModel):
    id: int
    engagement_id: int
    tool_name: str
    run_number: int
    status: str
    composite_score: Optional[float] = None
    run_at: str


class WorkpaperDocumentResponse(BaseModel):
    tool_name: str
    tool_label: str
    run_count: int
    last_run_date: Optional[str] = None
    status: Literal["completed", "not_started"]
    lead_sheet_refs: list[str]


class WorkpaperFollowUpSummaryResponse(BaseModel):
    total_count: int
    by_severity: dict[str, int]
    by_disposition: dict[str, int]
    by_tool_source: dict[str, int]


class WorkpaperSignOffResponse(BaseModel):
    prepared_by: str
    reviewed_by: str
    date: str


class WorkpaperIndexResponse(BaseModel):
    engagement_id: int
    client_name: str
    period_start: str
    period_end: str
    generated_at: str
    document_register: list[WorkpaperDocumentResponse]
    follow_up_summary: WorkpaperFollowUpSummaryResponse
    sign_off: WorkpaperSignOffResponse


class ConvergenceItemResponse(BaseModel):
    account: str
    tools_flagging_it: list[str]
    convergence_count: int


class ConvergenceResponse(BaseModel):
    engagement_id: int
    total_accounts: int
    tools_covered: list[str]
    tools_excluded: list[str]
    items: list[ConvergenceItemResponse]
    generated_at: str


class ToolRunTrendResponse(BaseModel):
    tool_name: str
    latest_score: float
    previous_score: Optional[float] = None
    score_delta: Optional[float] = None
    direction: Optional[Literal["improving", "stable", "degrading"]] = None
    run_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/engagements/{engagement_id}/materiality", response_model=MaterialityResponse)
def get_materiality(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> MaterialityResponse:
    """Compute materiality cascade for an engagement."""
    manager = EngagementManager(db)
    engagement = manager.get_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    result = manager.compute_materiality(engagement)
    return MaterialityResponse(**result)


@router.get(
    "/engagements/{engagement_id}/tool-runs",
    response_model=list[ToolRunResponse],
)
def get_tool_runs(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[ToolRunResponse]:
    """List tool runs for an engagement."""
    manager = EngagementManager(db)
    engagement = manager.get_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    runs = manager.get_tool_runs(engagement_id)

    return [
        ToolRunResponse(
            id=r.id,
            engagement_id=r.engagement_id,
            tool_name=r.tool_name.value if r.tool_name else "",
            run_number=r.run_number,
            status=r.status.value if r.status else "",
            composite_score=r.composite_score,
            run_at=r.run_at.isoformat() if r.run_at else "",
        )
        for r in runs
    ]


@router.get("/engagements/{engagement_id}/workpaper-index", response_model=WorkpaperIndexResponse)
def get_workpaper_index(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> WorkpaperIndexResponse:
    """Generate workpaper index for an engagement."""
    generator = WorkpaperIndexGenerator(db)

    try:
        index = generator.generate(current_user.id, engagement_id)
        return index
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="engagement_validation", allow_passthrough=True),
        )


@router.get(
    "/engagements/{engagement_id}/convergence",
    response_model=ConvergenceResponse,
)
def get_convergence_index(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> ConvergenceResponse:
    """Get cross-tool account convergence index for an engagement."""
    manager = EngagementManager(db)
    engagement = manager.get_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    items = manager.get_convergence_index(engagement_id)

    return ConvergenceResponse(
        engagement_id=engagement_id,
        total_accounts=len(items),
        tools_covered=CONVERGENCE_TOOLS,
        tools_excluded=CONVERGENCE_EXCLUDED,
        items=[ConvergenceItemResponse(**item) for item in items],
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.get(
    "/engagements/{engagement_id}/tool-run-trends",
    response_model=list[ToolRunTrendResponse],
)
def get_tool_run_trends(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[ToolRunTrendResponse]:
    """Get per-tool score trends for an engagement."""
    manager = EngagementManager(db)
    engagement = manager.get_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    trends = manager.get_tool_run_trends(engagement_id)

    return [ToolRunTrendResponse(**t) for t in trends]
