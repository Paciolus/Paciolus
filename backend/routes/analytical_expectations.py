"""
Paciolus API — Analytical Expectations Routes (Sprint 728a, ISA 520).

CRUD endpoints for the AnalyticalExpectation engagement-layer entity.
Mirrors the follow_up_items route layout: engagement-scoped list/create,
item-scoped fetch/update/delete.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from analytical_expectations_manager import AnalyticalExpectationsManager
from analytical_expectations_model import ExpectationResultStatus, ExpectationTargetType
from auth import require_current_user
from database import get_db
from models import User
from schemas.analytical_expectation_schemas import (
    AnalyticalExpectationCreate,
    AnalyticalExpectationResponse,
    AnalyticalExpectationUpdate,
)
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.pagination import PaginatedResponse, PaginationParams
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

router = APIRouter(tags=["analytical_expectations"])


def _to_response(expectation: Any) -> AnalyticalExpectationResponse:
    d = expectation.to_dict()

    def _to_float(v: Optional[str]) -> Optional[float]:
        return float(v) if v is not None else None

    return AnalyticalExpectationResponse(
        id=d["id"],
        engagement_id=d["engagement_id"],
        procedure_target_type=d["procedure_target_type"],  # type: ignore[arg-type]
        procedure_target_label=d["procedure_target_label"],
        expected_value=_to_float(d["expected_value"]),
        expected_range_low=_to_float(d["expected_range_low"]),
        expected_range_high=_to_float(d["expected_range_high"]),
        precision_threshold_amount=_to_float(d["precision_threshold_amount"]),
        precision_threshold_percent=d["precision_threshold_percent"],
        corroboration_basis_text=d["corroboration_basis_text"],
        corroboration_tags=d["corroboration_tags"],
        cpa_notes=d["cpa_notes"],
        result_actual_value=_to_float(d["result_actual_value"]),
        result_variance_amount=_to_float(d["result_variance_amount"]),
        result_status=d["result_status"],  # type: ignore[arg-type]
        created_by=d["created_by"],
        created_at=d["created_at"] or "",
        updated_by=d["updated_by"],
        updated_at=d["updated_at"] or "",
    )


@router.post(
    "/engagements/{engagement_id}/analytical-expectations",
    response_model=AnalyticalExpectationResponse,
    status_code=201,
)
@limiter.limit(RATE_LIMIT_WRITE)
def create_expectation(
    request: Request,
    engagement_id: int,
    data: AnalyticalExpectationCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> AnalyticalExpectationResponse:
    """Create an analytical expectation for an engagement."""
    log_secure_operation(
        "analytical_expectation_create",
        f"User {current_user.id} creating expectation for engagement {engagement_id}",
    )

    manager = AnalyticalExpectationsManager(db)
    try:
        expectation = manager.create_expectation(
            user_id=current_user.id,
            engagement_id=engagement_id,
            procedure_target_type=data.procedure_target_type,
            procedure_target_label=data.procedure_target_label,
            corroboration_basis_text=data.corroboration_basis_text,
            corroboration_tags=data.corroboration_tags,
            expected_value=data.expected_value,
            expected_range_low=data.expected_range_low,
            expected_range_high=data.expected_range_high,
            precision_threshold_amount=data.precision_threshold_amount,
            precision_threshold_percent=data.precision_threshold_percent,
            cpa_notes=data.cpa_notes,
        )
        return _to_response(expectation)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="analytical_expectation_validation", allow_passthrough=True),
        )


@router.get(
    "/engagements/{engagement_id}/analytical-expectations",
    response_model=PaginatedResponse[AnalyticalExpectationResponse],
)
def list_expectations(
    engagement_id: int,
    result_status: Optional[str] = Query(default=None),
    target_type: Optional[str] = Query(default=None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AnalyticalExpectationResponse]:
    """List analytical expectations for an engagement."""
    manager = AnalyticalExpectationsManager(db)
    try:
        status_enum = ExpectationResultStatus(result_status) if result_status else None
        target_enum = ExpectationTargetType(target_type) if target_type else None

        items, total = manager.list_expectations(
            user_id=current_user.id,
            engagement_id=engagement_id,
            result_status=status_enum,
            target_type=target_enum,
            limit=pagination.page_size,
            offset=pagination.offset,
        )
        return PaginatedResponse[AnalyticalExpectationResponse](
            items=[_to_response(e) for e in items],
            total_count=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="analytical_expectation_validation", allow_passthrough=True),
        )


@router.get(
    "/analytical-expectations/{expectation_id}",
    response_model=AnalyticalExpectationResponse,
)
def get_expectation(
    expectation_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> AnalyticalExpectationResponse:
    """Fetch a single analytical expectation."""
    manager = AnalyticalExpectationsManager(db)
    expectation = manager.get_expectation(current_user.id, expectation_id)
    if not expectation:
        raise HTTPException(status_code=404, detail="Analytical expectation not found")
    return _to_response(expectation)


@router.patch(
    "/analytical-expectations/{expectation_id}",
    response_model=AnalyticalExpectationResponse,
)
@limiter.limit(RATE_LIMIT_WRITE)
def update_expectation(
    request: Request,
    expectation_id: int,
    data: AnalyticalExpectationUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> AnalyticalExpectationResponse:
    """Update an analytical expectation. Captures result_actual_value triggers status recompute."""
    log_secure_operation(
        "analytical_expectation_update",
        f"User {current_user.id} updating expectation {expectation_id}",
    )

    manager = AnalyticalExpectationsManager(db)
    try:
        expectation = manager.update_expectation(
            user_id=current_user.id,
            expectation_id=expectation_id,
            procedure_target_label=data.procedure_target_label,
            expected_value=data.expected_value,
            expected_range_low=data.expected_range_low,
            expected_range_high=data.expected_range_high,
            precision_threshold_amount=data.precision_threshold_amount,
            precision_threshold_percent=data.precision_threshold_percent,
            corroboration_basis_text=data.corroboration_basis_text,
            corroboration_tags=data.corroboration_tags,
            cpa_notes=data.cpa_notes,
            result_actual_value=data.result_actual_value,
            clear_result=data.clear_result,
        )
        if expectation is None:
            raise HTTPException(status_code=404, detail="Analytical expectation not found")
        return _to_response(expectation)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, log_label="analytical_expectation_validation", allow_passthrough=True),
        )


@router.delete(
    "/analytical-expectations/{expectation_id}",
    status_code=204,
)
@limiter.limit(RATE_LIMIT_WRITE)
def archive_expectation(
    request: Request,
    expectation_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Soft-delete (archive) an analytical expectation."""
    log_secure_operation(
        "analytical_expectation_archive",
        f"User {current_user.id} archiving expectation {expectation_id}",
    )

    manager = AnalyticalExpectationsManager(db)
    expectation = manager.archive_expectation(current_user.id, expectation_id)
    if expectation is None:
        raise HTTPException(status_code=404, detail="Analytical expectation not found")
