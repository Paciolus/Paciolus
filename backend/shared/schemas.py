"""
Paciolus API — Shared Pydantic Schemas
"""

from typing import Any, Optional, Union

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Unified error envelope returned by all exception handlers.

    Every error response carries the same top-level shape so the frontend
    can parse errors with a single code path.

    Fields:
        code:       Machine-readable error code (e.g. "VALIDATION_ERROR", "INTERNAL_ERROR").
        message:    Human-readable summary safe for UI display.
        request_id: Correlation ID for log tracing.
        detail:     Optional — validation error list (422) or contextual string.
    """

    code: str
    message: str
    request_id: str
    detail: Optional[Union[str, list[dict[str, Any]]]] = None


class AuditResultInput(BaseModel):
    """Input model for PDF/Excel/CSV export - accepts audit result JSON."""

    status: str
    balanced: bool
    total_debits: float
    total_credits: float
    difference: float
    row_count: int
    message: str
    abnormal_balances: list
    has_risk_alerts: bool
    materiality_threshold: float
    material_count: int
    immaterial_count: int
    filename: str = "audit"
    # Optional fields
    classification_summary: Optional[dict] = None
    column_detection: Optional[dict] = None
    risk_summary: Optional[dict] = None
    is_consolidated: Optional[bool] = None
    sheet_count: Optional[int] = None
    selected_sheets: Optional[list] = None
    sheet_results: Optional[dict] = None
    lead_sheet_grouping: Optional[dict] = None
    # Workpaper signoff fields (deprecated Sprint 7 — ignored unless include_signoff=True)
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None
    include_signoff: bool = False
