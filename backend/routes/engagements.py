"""
Paciolus API — Engagement Routes
Phase X: Engagement Layer (metadata-only, Zero-Storage compliant)
"""

import io
from datetime import UTC, datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from anomaly_summary_generator import AnomalySummaryGenerator
from auth import require_current_user, require_verified_user
from database import get_db
from engagement_export import EngagementExporter
from engagement_manager import EngagementManager
from engagement_model import EngagementStatus, MaterialityBasis
from models import User
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_EXPORT, RATE_LIMIT_WRITE, limiter
from workpaper_index_generator import WorkpaperIndexGenerator

router = APIRouter(tags=["engagements"])


# ---------------------------------------------------------------------------
# Pydantic schemas
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
    status: Literal["active", "archived"]
    materiality_basis: Optional[Literal["revenue", "assets", "manual"]] = None
    materiality_percentage: Optional[float] = None
    materiality_amount: Optional[float] = None
    performance_materiality_factor: float
    trivial_threshold_factor: float
    created_by: int
    created_at: str
    updated_at: str


class EngagementListResponse(BaseModel):
    engagements: list[EngagementResponse]
    total_count: int
    page: int
    page_size: int


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
    items: list[ConvergenceItemResponse]
    generated_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _engagement_to_response(eng) -> EngagementResponse:
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
        created_by=d["created_by"],
        created_at=d["created_at"] or "",
        updated_at=d["updated_at"] or "",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/engagements", response_model=EngagementResponse, status_code=201)
@limiter.limit(RATE_LIMIT_WRITE)
def create_engagement(
    request: Request,
    data: EngagementCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
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
        raise HTTPException(status_code=400, detail=sanitize_error(
            e, log_label="engagement_validation", allow_passthrough=True,
        ))


@router.get("/engagements", response_model=EngagementListResponse)
def list_engagements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    client_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
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
):
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
):
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

    except ValueError as e:
        raise HTTPException(status_code=400, detail=sanitize_error(
            e, log_label="engagement_validation", allow_passthrough=True,
        ))


@router.delete("/engagements/{engagement_id}", status_code=204)
@limiter.limit(RATE_LIMIT_WRITE)
def archive_engagement(
    request: Request,
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Archive an engagement (soft delete)."""
    log_secure_operation(
        "engagement_archive",
        f"User {current_user.id} archiving engagement {engagement_id}",
    )

    manager = EngagementManager(db)
    engagement = manager.archive_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")


@router.get("/engagements/{engagement_id}/materiality", response_model=MaterialityResponse)
def get_materiality(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
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
):
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
):
    """Generate workpaper index for an engagement."""
    generator = WorkpaperIndexGenerator(db)

    try:
        index = generator.generate(current_user.id, engagement_id)
        return index
    except ValueError as e:
        raise HTTPException(status_code=400, detail=sanitize_error(
            e, log_label="engagement_validation", allow_passthrough=True,
        ))


@router.post("/engagements/{engagement_id}/export/anomaly-summary")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_anomaly_summary(
    request: Request,
    engagement_id: int,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Generate anomaly summary PDF for an engagement."""
    log_secure_operation(
        "anomaly_summary_export",
        f"User {current_user.id} exporting anomaly summary for engagement {engagement_id}",
    )

    generator = AnomalySummaryGenerator(db)

    try:
        pdf_bytes = generator.generate_pdf(current_user.id, engagement_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=sanitize_error(
            e, log_label="engagement_validation", allow_passthrough=True,
        ))

    def iter_pdf():
        chunk_size = 8192
        for i in range(0, len(pdf_bytes), chunk_size):
            yield pdf_bytes[i:i + chunk_size]

    return StreamingResponse(
        iter_pdf(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="anomaly_summary.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.post("/engagements/{engagement_id}/export/package")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_engagement_package(
    request: Request,
    engagement_id: int,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Generate and stream diagnostic package ZIP for an engagement."""
    log_secure_operation(
        "engagement_package_export",
        f"User {current_user.id} exporting diagnostic package for engagement {engagement_id}",
    )

    exporter = EngagementExporter(db)

    try:
        zip_bytes, filename = exporter.generate_zip(current_user.id, engagement_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=sanitize_error(
            e, log_label="engagement_validation", allow_passthrough=True,
        ))

    def iter_zip():
        chunk_size = 8192
        for i in range(0, len(zip_bytes), chunk_size):
            yield zip_bytes[i:i + chunk_size]

    return StreamingResponse(
        iter_zip(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(zip_bytes)),
        },
    )


@router.get(
    "/engagements/{engagement_id}/convergence",
    response_model=ConvergenceResponse,
)
def get_convergence_index(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get cross-tool account convergence index for an engagement.

    Aggregates flagged GL accounts across the latest completed run of each tool.
    Returns convergence counts only — NO composite score, NO risk classification.
    """
    manager = EngagementManager(db)
    engagement = manager.get_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    items = manager.get_convergence_index(engagement_id)

    return ConvergenceResponse(
        engagement_id=engagement_id,
        total_accounts=len(items),
        items=[ConvergenceItemResponse(**item) for item in items],
        generated_at=datetime.now(UTC).isoformat(),
    )


@router.post("/engagements/{engagement_id}/export/convergence-csv")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_convergence_csv(
    request: Request,
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Export convergence index as CSV."""
    from shared.helpers import sanitize_csv_value

    log_secure_operation(
        "convergence_csv_export",
        f"User {current_user.id} exporting convergence CSV for engagement {engagement_id}",
    )

    manager = EngagementManager(db)
    engagement = manager.get_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    items = manager.get_convergence_index(engagement_id)

    output = io.StringIO()
    output.write("Account,Convergence Count,Tools Flagging It\n")
    for item in items:
        account = sanitize_csv_value(item["account"])
        count = item["convergence_count"]
        tools = sanitize_csv_value("; ".join(item["tools_flagging_it"]))
        output.write(f"{account},{count},{tools}\n")

    csv_bytes = output.getvalue().encode("utf-8")

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="convergence_index_{engagement_id}.csv"',
            "Content-Length": str(len(csv_bytes)),
        },
    )
