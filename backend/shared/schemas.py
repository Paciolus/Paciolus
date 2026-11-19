"""
Paciolus API — Shared Pydantic Schemas
"""

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

# An amount as it arrives in an export request: a JSON number stays the Python
# type it parsed as (int, float, or Decimal where the route parses Decimals).
ExportAmount = Optional[int | float | Decimal]


class _ExportItem(BaseModel):
    """Base for nested export items (Sprint 885, OUT-02).

    The fields the exports read are typed; a nested object or list where text
    is expected is refused. Other keys the analysis response carries are kept
    (``extra="allow"``) because the PDF exports read them; every exporter
    writes them through its typed cell writer. A number sent for a text field
    (an account named 1000) becomes the text "1000".
    """

    model_config = ConfigDict(extra="allow", coerce_numbers_to_str=True)


class FlaggedAccountInput(_ExportItem):
    """One entry of ``abnormal_balances`` (a flag raised against an account)."""

    account: str = "Unknown"
    type: Optional[str] = None
    issue: str = ""
    amount: ExportAmount = None
    debit: ExportAmount = None
    credit: ExportAmount = None
    materiality: Optional[str] = None
    severity: Optional[str] = None
    anomaly_type: Optional[str] = None
    category: Optional[str] = None
    sheet_name: Optional[str] = None


class TrialBalanceAccountInput(_ExportItem):
    """One entry of ``all_accounts`` (every account in the trial balance)."""

    account: str = "Unknown"
    type: Optional[str] = None
    debit: ExportAmount = None
    credit: ExportAmount = None


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
    detail: Optional[str | list[dict[str, Any]]] = None


class AuditResultInput(BaseModel):
    """Input model for PDF/Excel/CSV export - accepts audit result JSON."""

    status: str
    balanced: bool
    total_debits: float
    total_credits: float
    difference: float
    row_count: int
    message: str
    abnormal_balances: list[FlaggedAccountInput]
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
    selected_sheets: Optional[list[str]] = None
    sheet_results: Optional[dict] = None
    lead_sheet_grouping: Optional[dict] = None
    # Sprint 884 (OUT-04): every account from the analysis response. Required by
    # the trial balance exports, which list each account once (not only the flagged).
    all_accounts: Optional[list[TrialBalanceAccountInput]] = None
    # Workpaper signoff fields (deprecated Sprint 7 — ignored unless include_signoff=True)
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    # Sprint 885 (OUT-02): a date (YYYY-MM-DD), never free text written into a cell.
    workpaper_date: Optional[date] = None
    include_signoff: bool = False

    def export_dict(self) -> dict[str, Any]:
        """The payload as the exporters read it: nested items hold only the keys the client sent.

        ``model_dump()`` would add ``None`` for every unsent field, which defeats
        the exporters' ``item.get(key, default)``.
        """
        data = self.model_dump()
        data["abnormal_balances"] = [a.model_dump(exclude_unset=True) for a in self.abnormal_balances]
        if self.all_accounts is not None:
            data["all_accounts"] = [a.model_dump(exclude_unset=True) for a in self.all_accounts]
        return data
