"""
Paciolus API — Shared Pydantic Schemas
"""

from typing import Optional

from pydantic import BaseModel


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
