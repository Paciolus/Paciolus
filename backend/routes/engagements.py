"""
Paciolus API — Engagement Routes
Phase X: Engagement Layer (metadata-only, Zero-Storage compliant)
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User
from auth import require_current_user, require_verified_user
from fastapi.responses import StreamingResponse
from shared.rate_limits import limiter, RATE_LIMIT_EXPORT

from engagement_model import EngagementStatus, MaterialityBasis
from engagement_manager import EngagementManager
from workpaper_index_generator import WorkpaperIndexGenerator
from anomaly_summary_generator import AnomalySummaryGenerator
from engagement_export import EngagementExporter

router = APIRouter(tags=["engagements"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class EngagementCreate(BaseModel):
    client_id: int
    period_start: datetime
    period_end: datetime
    materiality_basis: Optional[str] = None
    materiality_percentage: Optional[float] = None
    materiality_amount: Optional[float] = None
    performance_materiality_factor: float = 0.75
    trivial_threshold_factor: float = 0.05


class EngagementUpdate(BaseModel):
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    status: Optional[str] = None
    materiality_basis: Optional[str] = None
    materiality_percentage: Optional[float] = None
    materiality_amount: Optional[float] = None
    performance_materiality_factor: Optional[float] = None
    trivial_threshold_factor: Optional[float] = None


class EngagementResponse(BaseModel):
    id: int
    client_id: int
    period_start: str
    period_end: str
    status: str
    materiality_basis: Optional[str] = None
    materiality_percentage: Optional[float] = None
    materiality_amount: Optional[float] = None
    performance_materiality_factor: float
    trivial_threshold_factor: float
    created_by: int
    created_at: str
    updated_at: str


class EngagementListResponse(BaseModel):
    engagements: List[EngagementResponse]
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

@router.post("/engagements", response_model=EngagementResponse)
async def create_engagement(
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
        basis = MaterialityBasis(data.materiality_basis) if data.materiality_basis else None

        engagement = manager.create_engagement(
            user_id=current_user.id,
            client_id=data.client_id,
            period_start=data.period_start,
            period_end=data.period_end,
            materiality_basis=basis,
            materiality_percentage=data.materiality_percentage,
            materiality_amount=data.materiality_amount,
            performance_materiality_factor=data.performance_materiality_factor,
            trivial_threshold_factor=data.trivial_threshold_factor,
        )

        return _engagement_to_response(engagement)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/engagements", response_model=EngagementListResponse)
async def list_engagements(
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
async def get_engagement(
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
async def update_engagement(
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
        status_enum = EngagementStatus(data.status) if data.status else None
        basis = MaterialityBasis(data.materiality_basis) if data.materiality_basis else None

        engagement = manager.update_engagement(
            user_id=current_user.id,
            engagement_id=engagement_id,
            period_start=data.period_start,
            period_end=data.period_end,
            status=status_enum,
            materiality_basis=basis,
            materiality_percentage=data.materiality_percentage,
            materiality_amount=data.materiality_amount,
            performance_materiality_factor=data.performance_materiality_factor,
            trivial_threshold_factor=data.trivial_threshold_factor,
        )

        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        return _engagement_to_response(engagement)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/engagements/{engagement_id}")
async def archive_engagement(
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

    return {
        "success": True,
        "message": "Engagement archived",
        "engagement_id": engagement_id,
    }


@router.get("/engagements/{engagement_id}/materiality", response_model=MaterialityResponse)
async def get_materiality(
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
    response_model=List[ToolRunResponse],
)
async def get_tool_runs(
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


@router.get("/engagements/{engagement_id}/workpaper-index")
async def get_workpaper_index(
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
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/engagements/{engagement_id}/export/anomaly-summary")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_anomaly_summary(
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
        raise HTTPException(status_code=400, detail=str(e))

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
async def export_engagement_package(
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
        raise HTTPException(status_code=400, detail=str(e))

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
