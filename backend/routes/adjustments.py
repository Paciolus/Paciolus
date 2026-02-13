"""
Paciolus API — Adjusting Entry Routes
"""
import time
from datetime import datetime, UTC
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from pydantic import BaseModel, Field

from security_utils import log_secure_operation
from models import User
from auth import require_verified_user
from adjusting_entries import (
    AdjustingEntry,
    AdjustmentLine,
    AdjustmentSet,
    AdjustmentType,
    AdjustmentStatus,
    apply_adjustments,
)
from shared.rate_limits import limiter, RATE_LIMIT_DEFAULT

router = APIRouter(tags=["adjustments"])


# --- Pydantic Models ---

class AdjustmentLineRequest(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=500, description="Account name to debit/credit")
    debit: float = Field(0.0, ge=0, description="Debit amount")
    credit: float = Field(0.0, ge=0, description="Credit amount")
    description: Optional[str] = Field(None, description="Line description")


class AdjustingEntryRequest(BaseModel):
    reference: str = Field(..., min_length=1, max_length=50, description="Entry reference (e.g., AJE-001)")
    description: str = Field(..., min_length=1, max_length=1000, description="Entry description")
    adjustment_type: AdjustmentType = Field(AdjustmentType.OTHER, description="Type: accrual, deferral, estimate, error_correction, reclassification, other")
    lines: List[AdjustmentLineRequest] = Field(..., min_length=2, description="Entry lines (min 2)")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_reversing: bool = Field(False, description="Whether entry auto-reverses")


class AdjustmentStatusUpdate(BaseModel):
    status: AdjustmentStatus = Field(..., description="New status: proposed, approved, rejected, posted")
    reviewed_by: Optional[str] = Field(None, description="Reviewer name/ID")


class ApplyAdjustmentsRequest(BaseModel):
    trial_balance: List[dict] = Field(..., min_length=1, description="Trial balance accounts with 'account', 'debit', 'credit'")
    adjustment_ids: List[str] = Field(..., min_length=1, description="IDs of adjustments to apply")
    include_proposed: bool = Field(False, description="Include proposed (not yet approved) entries")


class AdjustmentSetResponse(BaseModel):
    entries: List[dict]
    total_adjustments: int
    proposed_count: int
    approved_count: int
    rejected_count: int
    posted_count: int
    total_adjustment_amount: float


class AdjustmentCreateResponse(BaseModel):
    success: bool
    entry_id: str
    reference: str
    is_balanced: bool
    total_amount: float
    status: str


class NextReferenceResponse(BaseModel):
    next_reference: str


class EnumOptionResponse(BaseModel):
    value: str
    label: str


class AdjustmentTypesResponse(BaseModel):
    types: List[EnumOptionResponse]


class AdjustmentStatusesResponse(BaseModel):
    statuses: List[EnumOptionResponse]


class AdjustmentStatusUpdateResponse(BaseModel):
    success: bool
    entry_id: str
    status: str
    reviewed_by: Optional[str] = None


# --- Session Storage (with TTL + eviction) ---

_SESSION_TTL_SECONDS = 3600  # 1 hour
_MAX_SESSIONS = 500

_session_adjustments: dict[str, AdjustmentSet] = {}
_session_timestamps: dict[str, float] = {}


def _cleanup_expired_sessions() -> None:
    """Remove sessions that have exceeded TTL."""
    now = time.monotonic()
    expired = [
        key for key, ts in _session_timestamps.items()
        if now - ts > _SESSION_TTL_SECONDS
    ]
    for key in expired:
        _session_adjustments.pop(key, None)
        _session_timestamps.pop(key, None)


def get_user_adjustments(user_id: int) -> AdjustmentSet:
    """Get or create adjustment set for user session."""
    key = str(user_id)

    # Periodic cleanup of expired sessions
    _cleanup_expired_sessions()

    # Enforce max sessions — evict oldest if at capacity
    if key not in _session_adjustments and len(_session_adjustments) >= _MAX_SESSIONS:
        oldest_key = min(_session_timestamps, key=_session_timestamps.get)  # type: ignore[arg-type]
        _session_adjustments.pop(oldest_key, None)
        _session_timestamps.pop(oldest_key, None)

    if key not in _session_adjustments:
        _session_adjustments[key] = AdjustmentSet()

    # Update access timestamp
    _session_timestamps[key] = time.monotonic()

    return _session_adjustments[key]


# --- Route Handlers ---

@router.post("/audit/adjustments", response_model=AdjustmentCreateResponse, status_code=201)
@limiter.limit("30/minute")
def create_adjusting_entry(
    request: Request,
    entry_data: AdjustingEntryRequest,
    current_user: User = Depends(require_verified_user),
):
    """Create a new adjusting journal entry."""
    from decimal import Decimal

    log_secure_operation("create_adjustment", f"User {current_user.id} creating entry {entry_data.reference}")

    try:
        lines = [
            AdjustmentLine(
                account_name=line.account_name,
                debit=Decimal(str(line.debit)),
                credit=Decimal(str(line.credit)),
                description=line.description,
            )
            for line in entry_data.lines
        ]

        entry = AdjustingEntry(
            reference=entry_data.reference,
            description=entry_data.description,
            adjustment_type=entry_data.adjustment_type,
            lines=lines,
            prepared_by=current_user.email,
            notes=entry_data.notes,
            is_reversing=entry_data.is_reversing,
        )

        adj_set = get_user_adjustments(current_user.id)
        adj_set.add_entry(entry)

        return {
            "success": True,
            "entry_id": entry.id,
            "reference": entry.reference,
            "is_balanced": entry.is_balanced,
            "total_amount": float(entry.entry_total),
            "status": entry.status.value,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/audit/adjustments", response_model=AdjustmentSetResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def list_adjusting_entries(
    request: Request,
    current_user: User = Depends(require_verified_user),
    status: Optional[str] = Query(None, description="Filter by status"),
    adj_type: Optional[str] = Query(None, alias="type", description="Filter by adjustment type"),
):
    """List all adjusting entries in the current session."""
    adj_set = get_user_adjustments(current_user.id)

    entries = adj_set.entries

    if status:
        try:
            status_filter = AdjustmentStatus(status)
            entries = [e for e in entries if e.status == status_filter]
        except ValueError:
            pass

    if adj_type:
        try:
            type_filter = AdjustmentType(adj_type)
            entries = [e for e in entries if e.adjustment_type == type_filter]
        except ValueError:
            pass

    return {
        "entries": [e.to_dict() for e in entries],
        "total_adjustments": len(entries),
        "proposed_count": sum(1 for e in entries if e.status == AdjustmentStatus.PROPOSED),
        "approved_count": sum(1 for e in entries if e.status == AdjustmentStatus.APPROVED),
        "rejected_count": sum(1 for e in entries if e.status == AdjustmentStatus.REJECTED),
        "posted_count": sum(1 for e in entries if e.status == AdjustmentStatus.POSTED),
        "total_adjustment_amount": float(adj_set.total_adjustment_amount),
    }


@router.get("/audit/adjustments/reference/next", response_model=NextReferenceResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_next_reference(
    request: Request,
    prefix: str = Query("AJE", description="Reference prefix"),
    current_user: User = Depends(require_verified_user),
):
    """Get the next sequential reference number for adjusting entries."""
    adj_set = get_user_adjustments(current_user.id)
    next_ref = adj_set.generate_next_reference(prefix)
    return {"next_reference": next_ref}


@router.get("/audit/adjustments/types", response_model=AdjustmentTypesResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_adjustment_types(request: Request, response: Response):
    """Get available adjustment types for UI dropdowns."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    return {
        "types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in AdjustmentType
        ]
    }


@router.get("/audit/adjustments/statuses", response_model=AdjustmentStatusesResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_adjustment_statuses(request: Request, response: Response):
    """Get available adjustment statuses for UI dropdowns."""
    response.headers["Cache-Control"] = "public, max-age=3600"
    return {
        "statuses": [
            {"value": s.value, "label": s.value.title()}
            for s in AdjustmentStatus
        ]
    }


@router.get("/audit/adjustments/{entry_id}", response_model=dict)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_adjusting_entry(
    request: Request,
    entry_id: str,
    current_user: User = Depends(require_verified_user),
):
    """Get a specific adjusting entry by ID."""
    adj_set = get_user_adjustments(current_user.id)
    entry = adj_set.get_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Adjusting entry not found")

    return entry.to_dict()


@router.put("/audit/adjustments/{entry_id}/status", response_model=AdjustmentStatusUpdateResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def update_adjustment_status(
    request: Request,
    entry_id: str,
    status_update: AdjustmentStatusUpdate,
    current_user: User = Depends(require_verified_user),
):
    """Update the status of an adjusting entry."""
    adj_set = get_user_adjustments(current_user.id)
    entry = adj_set.get_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Adjusting entry not found")

    entry.status = status_update.status
    if status_update.reviewed_by:
        entry.reviewed_by = status_update.reviewed_by
    entry.updated_at = datetime.now(UTC)

    log_secure_operation(
        "update_adjustment_status",
        f"User {current_user.id} updated entry {entry_id} to {status_update.status.value}"
    )

    return {
        "success": True,
        "entry_id": entry.id,
        "status": entry.status.value,
        "reviewed_by": entry.reviewed_by,
    }


@router.delete("/audit/adjustments/{entry_id}", status_code=204)
@limiter.limit(RATE_LIMIT_DEFAULT)
def delete_adjusting_entry(
    request: Request,
    entry_id: str,
    current_user: User = Depends(require_verified_user),
):
    """Delete an adjusting entry from the session."""
    adj_set = get_user_adjustments(current_user.id)
    removed = adj_set.remove_entry(entry_id)

    if not removed:
        raise HTTPException(status_code=404, detail="Adjusting entry not found")

    log_secure_operation("delete_adjustment", f"User {current_user.id} deleted entry {entry_id}")


@router.post("/audit/adjustments/apply", response_model=dict)
@limiter.limit("10/minute")
def apply_adjustments_to_tb(
    request: Request,
    apply_data: ApplyAdjustmentsRequest,
    current_user: User = Depends(require_verified_user),
):
    """Apply adjusting entries to a trial balance."""
    adj_set = get_user_adjustments(current_user.id)

    entries_to_apply = AdjustmentSet()
    for entry_id in apply_data.adjustment_ids:
        entry = adj_set.get_entry(entry_id)
        if entry:
            entries_to_apply.add_entry(entry)

    if entries_to_apply.total_adjustments == 0:
        raise HTTPException(status_code=400, detail="No valid adjustments found to apply")

    adjusted_tb = apply_adjustments(
        trial_balance=apply_data.trial_balance,
        adjustments=entries_to_apply,
        include_proposed=apply_data.include_proposed,
    )

    log_secure_operation(
        "apply_adjustments",
        f"User {current_user.id} applied {adjusted_tb.adjustment_count} adjustments"
    )

    return adjusted_tb.to_dict()


@router.delete("/audit/adjustments", status_code=204)
@limiter.limit(RATE_LIMIT_DEFAULT)
def clear_all_adjustments(
    request: Request,
    current_user: User = Depends(require_verified_user),
):
    """Clear all adjusting entries from the session."""
    key = str(current_user.id)
    if key in _session_adjustments:
        del _session_adjustments[key]
    _session_timestamps.pop(key, None)

    log_secure_operation("clear_adjustments", f"User {current_user.id} cleared all adjustments")
