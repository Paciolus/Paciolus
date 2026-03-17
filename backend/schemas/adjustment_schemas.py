"""
Adjusting Entry Schemas — extracted from routes/adjustments.py (Sprint 544).
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from adjusting_entries import AdjustmentStatus, AdjustmentType


class AdjustmentLineRequest(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=500, description="Account name to debit/credit")
    debit: float = Field(0.0, ge=0, description="Debit amount")
    credit: float = Field(0.0, ge=0, description="Credit amount")
    description: Optional[str] = Field(None, description="Line description")


class AdjustingEntryRequest(BaseModel):
    reference: str = Field(..., min_length=1, max_length=50, description="Entry reference (e.g., AJE-001)")
    description: str = Field(..., min_length=1, max_length=1000, description="Entry description")
    adjustment_type: AdjustmentType = Field(
        AdjustmentType.OTHER, description="Type: accrual, deferral, estimate, error_correction, reclassification, other"
    )
    lines: list[AdjustmentLineRequest] = Field(..., min_length=2, description="Entry lines (min 2)")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_reversing: bool = Field(False, description="Whether entry auto-reverses")


class AdjustmentStatusUpdate(BaseModel):
    status: AdjustmentStatus = Field(..., description="New status: proposed, approved, rejected, posted")
    reviewed_by: Optional[str] = Field(None, description="Reviewer name/ID")


class ApplyAdjustmentsRequest(BaseModel):
    trial_balance: list[dict] = Field(
        ..., min_length=1, description="Trial balance accounts with 'account', 'debit', 'credit'"
    )
    adjustment_ids: list[str] = Field(..., min_length=1, description="IDs of adjustments to apply")
    mode: Literal["official", "simulation"] = Field(
        "official", description="official excludes proposed entries; simulation includes them"
    )


class AdjustmentSetResponse(BaseModel):
    entries: list[dict]
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
    types: list[EnumOptionResponse]


class AdjustmentStatusesResponse(BaseModel):
    statuses: list[EnumOptionResponse]


class AdjustmentStatusUpdateResponse(BaseModel):
    success: bool
    entry_id: str
    status: str
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
