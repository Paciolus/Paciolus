"""
Paciolus API — Uncorrected Misstatements Routes (Sprint 729a, ISA 450).

CRUD + SUM-schedule aggregation endpoints. Mirrors the analytical-
expectations route layout: engagement-scoped list/create, item-scoped
fetch/update/delete, plus a `/engagements/{id}/sum-schedule` aggregation.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from models import User
from schemas.uncorrected_misstatement_schemas import (
    SumScheduleResponse,
    UncorrectedMisstatementCreate,
    UncorrectedMisstatementResponse,
    UncorrectedMisstatementUpdate,
)
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.pagination import PaginatedResponse, PaginationParams
from shared.rate_limits import RATE_LIMIT_WRITE, limiter
from uncorrected_misstatements_manager import UncorrectedMisstatementsManager
from uncorrected_misstatements_model import (
    MisstatementClassification,
    MisstatementDisposition,
    MisstatementSourceType,
)

router = APIRouter(tags=["uncorrected_misstatements"])


def _to_response(m: Any) -> UncorrectedMisstatementResponse:
    d = m.to_dict()
    return UncorrectedMisstatementResponse(
        id=d["id"],
        engagement_id=d["engagement_id"],
        source_type=d["source_type"],  # type: ignore[arg-type]
        source_reference=d["source_reference"],
        description=d["description"],
        accounts_affected=d["accounts_affected"],
        classification=d["classification"],  # type: ignore[arg-type]
        fs_impact_net_income=float(d["fs_impact_net_income"]),
        fs_impact_net_assets=float(d["fs_impact_net_assets"]),
        cpa_disposition=d["cpa_disposition"],  # type: ignore[arg-type]
        cpa_notes=d["cpa_notes"],
        created_by=d["created_by"],
        created_at=d["created_at"] or "",
        updated_by=d["updated_by"],
        updated_at=d["updated_at"] or "",
    )


@router.post(
    "/engagements/{engagement_id}/uncorrected-misstatements",
    response_model=UncorrectedMisstatementResponse,
    status_code=201,
)
@limiter.limit(RATE_LIMIT_WRITE)
def create_misstatement(
    request: Request,
    engagement_id: int,
    data: UncorrectedMisstatementCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> UncorrectedMisstatementResponse:
    """Create an uncorrected-misstatement row on the SUM schedule."""
    log_secure_operation(
        "uncorrected_misstatement_create",
        f"User {current_user.id} creating misstatement for engagement {engagement_id}",
    )

    manager = UncorrectedMisstatementsManager(db)
    try:
        m = manager.create_misstatement(
            user_id=current_user.id,
            engagement_id=engagement_id,
            source_type=data.source_type,
            source_reference=data.source_reference,
            description=data.description,
            accounts_affected=[a.model_dump() for a in data.accounts_affected],
            classification=data.classification,
            fs_impact_net_income=data.fs_impact_net_income,
            fs_impact_net_assets=data.fs_impact_net_assets,
            cpa_disposition=data.cpa_disposition,
            cpa_notes=data.cpa_notes,
        )
        return _to_response(m)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="uncorrected_misstatement_validation", allow_passthrough=True),
        )


@router.get(
    "/engagements/{engagement_id}/uncorrected-misstatements",
    response_model=PaginatedResponse[UncorrectedMisstatementResponse],
)
def list_misstatements(
    engagement_id: int,
    classification: Optional[str] = Query(default=None),
    source_type: Optional[str] = Query(default=None),
    disposition: Optional[str] = Query(default=None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UncorrectedMisstatementResponse]:
    """List uncorrected misstatements for an engagement."""
    manager = UncorrectedMisstatementsManager(db)
    try:
        cls_enum = MisstatementClassification(classification) if classification else None
        src_enum = MisstatementSourceType(source_type) if source_type else None
        disp_enum = MisstatementDisposition(disposition) if disposition else None

        items, total = manager.list_misstatements(
            user_id=current_user.id,
            engagement_id=engagement_id,
            classification=cls_enum,
            source_type=src_enum,
            disposition=disp_enum,
            limit=pagination.page_size,
            offset=pagination.offset,
        )
        return PaginatedResponse[UncorrectedMisstatementResponse](
            items=[_to_response(m) for m in items],
            total_count=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="uncorrected_misstatement_validation", allow_passthrough=True),
        )


@router.get(
    "/engagements/{engagement_id}/sum-schedule",
    response_model=SumScheduleResponse,
)
def get_sum_schedule(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> SumScheduleResponse:
    """SUM aggregation: subtotals + aggregate + materiality bucket."""
    manager = UncorrectedMisstatementsManager(db)
    try:
        payload = manager.compute_sum_schedule(current_user.id, engagement_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    items_resp = []
    for d in payload["items"]:
        items_resp.append(
            UncorrectedMisstatementResponse(
                id=d["id"],
                engagement_id=d["engagement_id"],
                source_type=d["source_type"],
                source_reference=d["source_reference"],
                description=d["description"],
                accounts_affected=d["accounts_affected"],
                classification=d["classification"],
                fs_impact_net_income=float(d["fs_impact_net_income"]),
                fs_impact_net_assets=float(d["fs_impact_net_assets"]),
                cpa_disposition=d["cpa_disposition"],
                cpa_notes=d["cpa_notes"],
                created_by=d["created_by"],
                created_at=d["created_at"] or "",
                updated_by=d["updated_by"],
                updated_at=d["updated_at"] or "",
            )
        )

    return SumScheduleResponse(
        engagement_id=payload["engagement_id"],
        items=items_resp,
        subtotals={k: float(v) for k, v in payload["subtotals"].items()},  # type: ignore[arg-type]
        aggregate={k: float(v) for k, v in payload["aggregate"].items()},  # type: ignore[arg-type]
        materiality={k: float(v) for k, v in payload["materiality"].items()},  # type: ignore[arg-type]
        bucket=payload["bucket"],
        unreviewed_count=payload["unreviewed_count"],
    )


@router.get(
    "/uncorrected-misstatements/{misstatement_id}",
    response_model=UncorrectedMisstatementResponse,
)
def get_misstatement(
    misstatement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> UncorrectedMisstatementResponse:
    manager = UncorrectedMisstatementsManager(db)
    m = manager.get_misstatement(current_user.id, misstatement_id)
    if not m:
        raise HTTPException(status_code=404, detail="Misstatement not found")
    return _to_response(m)


@router.patch(
    "/uncorrected-misstatements/{misstatement_id}",
    response_model=UncorrectedMisstatementResponse,
)
@limiter.limit(RATE_LIMIT_WRITE)
def update_misstatement(
    request: Request,
    misstatement_id: int,
    data: UncorrectedMisstatementUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> UncorrectedMisstatementResponse:
    log_secure_operation(
        "uncorrected_misstatement_update",
        f"User {current_user.id} updating misstatement {misstatement_id}",
    )
    manager = UncorrectedMisstatementsManager(db)
    try:
        m = manager.update_misstatement(
            user_id=current_user.id,
            misstatement_id=misstatement_id,
            source_reference=data.source_reference,
            description=data.description,
            accounts_affected=(
                [a.model_dump() for a in data.accounts_affected] if data.accounts_affected is not None else None
            ),
            classification=data.classification,
            fs_impact_net_income=data.fs_impact_net_income,
            fs_impact_net_assets=data.fs_impact_net_assets,
            cpa_disposition=data.cpa_disposition,
            cpa_notes=data.cpa_notes,
        )
        if m is None:
            raise HTTPException(status_code=404, detail="Misstatement not found")
        return _to_response(m)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="uncorrected_misstatement_validation", allow_passthrough=True),
        )


@router.delete(
    "/uncorrected-misstatements/{misstatement_id}",
    status_code=204,
)
@limiter.limit(RATE_LIMIT_WRITE)
def archive_misstatement(
    request: Request,
    misstatement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> None:
    log_secure_operation(
        "uncorrected_misstatement_archive",
        f"User {current_user.id} archiving misstatement {misstatement_id}",
    )
    manager = UncorrectedMisstatementsManager(db)
    m = manager.archive_misstatement(current_user.id, misstatement_id)
    if m is None:
        raise HTTPException(status_code=404, detail="Misstatement not found")
