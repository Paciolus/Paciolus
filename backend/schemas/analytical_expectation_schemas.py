"""
Analytical Expectation API schemas — Sprint 728a (ISA 520).

Pydantic surface for routes/analytical_expectations.py.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from analytical_expectations_model import ExpectationTargetType


class AnalyticalExpectationCreate(BaseModel):
    procedure_target_type: ExpectationTargetType
    procedure_target_label: str = Field(..., min_length=1, max_length=200)

    # Either expected_value OR expected_range_low + expected_range_high.
    # XOR enforced by the manager.
    expected_value: Optional[float] = None
    expected_range_low: Optional[float] = None
    expected_range_high: Optional[float] = None

    # Either precision_threshold_amount OR precision_threshold_percent.
    # XOR enforced by the manager.
    precision_threshold_amount: Optional[float] = Field(default=None, ge=0)
    precision_threshold_percent: Optional[float] = Field(default=None, gt=0, le=10000)

    corroboration_basis_text: str = Field(..., min_length=1, max_length=4000)
    corroboration_tags: list[str] = Field(..., min_length=1)

    cpa_notes: Optional[str] = Field(default=None, max_length=4000)


class AnalyticalExpectationUpdate(BaseModel):
    procedure_target_label: Optional[str] = Field(default=None, min_length=1, max_length=200)

    expected_value: Optional[float] = None
    expected_range_low: Optional[float] = None
    expected_range_high: Optional[float] = None

    precision_threshold_amount: Optional[float] = Field(default=None, ge=0)
    precision_threshold_percent: Optional[float] = Field(default=None, gt=0, le=10000)

    corroboration_basis_text: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    corroboration_tags: Optional[list[str]] = Field(default=None, min_length=1)

    cpa_notes: Optional[str] = Field(default=None, max_length=4000)

    # Result management
    result_actual_value: Optional[float] = None
    clear_result: bool = False


class AnalyticalExpectationResponse(BaseModel):
    id: int
    engagement_id: int
    procedure_target_type: Literal["account", "balance", "ratio", "flux_line"]
    procedure_target_label: str

    expected_value: Optional[float] = None
    expected_range_low: Optional[float] = None
    expected_range_high: Optional[float] = None

    precision_threshold_amount: Optional[float] = None
    precision_threshold_percent: Optional[float] = None

    corroboration_basis_text: str
    corroboration_tags: list[str]

    cpa_notes: Optional[str] = None

    result_actual_value: Optional[float] = None
    result_variance_amount: Optional[float] = None
    result_status: Literal["not_evaluated", "within_threshold", "exceeds_threshold"]

    created_by: int
    created_at: str
    updated_by: Optional[int] = None
    updated_at: str
