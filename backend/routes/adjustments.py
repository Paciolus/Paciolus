"""
Paciolus API — Adjusting Entry Routes
Sprint 262: Migrated from in-memory dicts to DB-backed ToolSession.
"""
from datetime import datetime, UTC
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
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
from tool_session_model import load_tool_session, save_tool_session, delete_tool_session
from shared.rate_limits import limiter, RATE_LIMIT_DEFAULT
from shared.error_messages import sanitize_error
from shared.diagnostic_response_schemas import (
    AdjustingEntryResponse,
    AdjustedTrialBalanceResponse,
)

router = APIRouter(tags=["adjustments"])

TOOL_NAME = "adjustments"


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


# --- DB-Backed Session Helpers (Sprint 262) ---

def get_user_adjustments(db: Session, user_id: int) -> AdjustmentSet:
    """Load adjustment set from DB, or return empty set."""
    data = load_tool_session(db, user_id, TOOL_NAME)
    if data is None:
        return AdjustmentSet()
    return AdjustmentSet.from_dict(data)


def save_user_adjustments(db: Session, user_id: int, adj_set: AdjustmentSet) -> None:
    """Persist adjustment set to DB via upsert."""
    save_tool_session(db, user_id, TOOL_NAME, adj_set.to_dict())


# --- Route Handlers ---

@router.post("/audit/adjustments", response_model=AdjustmentCreateResponse, status_code=201)
@limiter.limit("30/minute")
def create_adjusting_entry(
    request: Request,
    entry_data: AdjustingEntryRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
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

        adj_set = get_user_adjustments(db, current_user.id)
        adj_set.add_entry(entry)
        save_user_adjustments(db, current_user.id, adj_set)

        return {
            "success": True,
            "entry_id": entry.id,
            "reference": entry.reference,
            "is_balanced": entry.is_balanced,
            "total_amount": float(entry.entry_total),
            "status": entry.status.value,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=sanitize_error(
            e, log_label="adjustments_validation", allow_passthrough=True,
        ))


@router.get("/audit/adjustments", response_model=AdjustmentSetResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def list_adjusting_entries(
    request: Request,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    adj_type: Optional[str] = Query(None, alias="type", description="Filter by adjustment type"),
):
    """List all adjusting entries in the current session."""
    adj_set = get_user_adjustments(db, current_user.id)

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
    db: Session = Depends(get_db),
):
    """Get the next sequential reference number for adjusting entries."""
    adj_set = get_user_adjustments(db, current_user.id)
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


@router.get("/audit/adjustments/{entry_id}", response_model=AdjustingEntryResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_adjusting_entry(
    request: Request,
    entry_id: str,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Get a specific adjusting entry by ID."""
    adj_set = get_user_adjustments(db, current_user.id)
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
    db: Session = Depends(get_db),
):
    """Update the status of an adjusting entry."""
    adj_set = get_user_adjustments(db, current_user.id)
    entry = adj_set.get_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Adjusting entry not found")

    entry.status = status_update.status
    if status_update.reviewed_by:
        entry.reviewed_by = status_update.reviewed_by
    entry.updated_at = datetime.now(UTC)

    save_user_adjustments(db, current_user.id, adj_set)

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
    db: Session = Depends(get_db),
):
    """Delete an adjusting entry from the session."""
    adj_set = get_user_adjustments(db, current_user.id)
    removed = adj_set.remove_entry(entry_id)

    if not removed:
        raise HTTPException(status_code=404, detail="Adjusting entry not found")

    save_user_adjustments(db, current_user.id, adj_set)

    log_secure_operation("delete_adjustment", f"User {current_user.id} deleted entry {entry_id}")


@router.post("/audit/adjustments/apply", response_model=AdjustedTrialBalanceResponse)
@limiter.limit("10/minute")
def apply_adjustments_to_tb(
    request: Request,
    apply_data: ApplyAdjustmentsRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Apply adjusting entries to a trial balance."""
    adj_set = get_user_adjustments(db, current_user.id)

    entries_to_apply = AdjustmentSet()
    for entry_id in apply_data.adjustment_ids:
        entry = adj_set.get_entry(entry_id)
        if entry:
            entries_to_apply.add_entry(entry)

    if entries_to_apply.total_adjustments == 0:
        raise HTTPException(status_code=400, detail="No valid adjustments found to apply")

    # Packet 2: entries loaded from DB have no line data (sanitized)
    if all(len(e.lines) == 0 for e in entries_to_apply.entries):
        raise HTTPException(
            status_code=400,
            detail="Adjustment entries have no line data. "
                   "Please re-create entries before applying.",
        )

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
    db: Session = Depends(get_db),
):
    """Clear all adjusting entries from the session."""
    delete_tool_session(db, current_user.id, TOOL_NAME)

    log_secure_operation("clear_adjustments", f"User {current_user.id} cleared all adjustments")
