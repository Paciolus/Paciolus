"""
Paciolus API — Diagnostic Summary Routes
"""
from datetime import date as date_type
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User, Client, DiagnosticSummary, PeriodType
from auth import require_current_user, require_verified_user
from shared.helpers import hash_filename, get_filename_display

router = APIRouter(tags=["diagnostics"])


class BalanceSheetTotals(BaseModel):
    total_assets: float = 0.0
    current_assets: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    total_equity: float = 0.0


class IncomeStatementTotals(BaseModel):
    total_revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    total_expenses: float = 0.0
    operating_expenses: float = 0.0


class FinancialRatios(BaseModel):
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    gross_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None


class DiagnosticSummaryCreate(BaseModel):
    client_id: int
    filename: str = Field(..., min_length=1, max_length=500)
    period_date: Optional[str] = None
    period_type: Optional[str] = None
    balance_sheet: BalanceSheetTotals = BalanceSheetTotals()
    income_statement: IncomeStatementTotals = IncomeStatementTotals()
    ratios: FinancialRatios = FinancialRatios()
    total_debits: float = 0.0
    total_credits: float = 0.0
    was_balanced: bool = True
    anomaly_count: int = 0
    materiality_threshold: float = 0.0
    row_count: int = 0

    @model_validator(mode='before')
    @classmethod
    def accept_flat_format(cls, data: dict) -> dict:
        """Accept flat JSON format for backward compatibility with frontend."""
        if isinstance(data, dict) and 'balance_sheet' not in data:
            bs_keys = ['total_assets', 'current_assets', 'inventory', 'total_liabilities', 'current_liabilities', 'total_equity']
            is_keys = ['total_revenue', 'cost_of_goods_sold', 'total_expenses', 'operating_expenses']
            ratio_keys = ['current_ratio', 'quick_ratio', 'debt_to_equity', 'gross_margin', 'net_profit_margin', 'operating_margin', 'return_on_assets', 'return_on_equity']

            data['balance_sheet'] = {k: data.pop(k) for k in bs_keys if k in data}
            data['income_statement'] = {k: data.pop(k) for k in is_keys if k in data}
            data['ratios'] = {k: data.pop(k) for k in ratio_keys if k in data}
        return data


class DiagnosticSummaryResponse(BaseModel):
    id: int
    client_id: int
    user_id: int
    timestamp: str
    period_date: Optional[str] = None
    period_type: Optional[str] = None
    filename_hash: Optional[str]
    filename_display: Optional[str]
    total_assets: float
    current_assets: float
    inventory: float
    total_liabilities: float
    current_liabilities: float
    total_equity: float
    total_revenue: float
    cost_of_goods_sold: float
    total_expenses: float
    operating_expenses: float = 0.0
    current_ratio: Optional[float]
    quick_ratio: Optional[float]
    debt_to_equity: Optional[float]
    gross_margin: Optional[float]
    net_profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    total_debits: float
    total_credits: float
    was_balanced: bool
    anomaly_count: int
    materiality_threshold: float
    row_count: int


class DiagnosticHistoryResponse(BaseModel):
    client_id: int
    client_name: str
    summaries: List[dict]
    total_count: int


def _summary_to_response(summary: DiagnosticSummary) -> DiagnosticSummaryResponse:
    """Convert a DiagnosticSummary ORM object to response model."""
    return DiagnosticSummaryResponse(
        id=summary.id,
        client_id=summary.client_id,
        user_id=summary.user_id,
        timestamp=summary.timestamp.isoformat(),
        period_date=summary.period_date.isoformat() if summary.period_date else None,
        period_type=summary.period_type.value if summary.period_type else None,
        filename_hash=summary.filename_hash,
        filename_display=summary.filename_display,
        total_assets=summary.total_assets,
        current_assets=summary.current_assets,
        inventory=summary.inventory,
        total_liabilities=summary.total_liabilities,
        current_liabilities=summary.current_liabilities,
        total_equity=summary.total_equity,
        total_revenue=summary.total_revenue,
        cost_of_goods_sold=summary.cost_of_goods_sold,
        total_expenses=summary.total_expenses,
        operating_expenses=summary.operating_expenses or 0.0,
        current_ratio=summary.current_ratio,
        quick_ratio=summary.quick_ratio,
        debt_to_equity=summary.debt_to_equity,
        gross_margin=summary.gross_margin,
        net_profit_margin=summary.net_profit_margin,
        operating_margin=summary.operating_margin,
        return_on_assets=summary.return_on_assets,
        return_on_equity=summary.return_on_equity,
        total_debits=summary.total_debits,
        total_credits=summary.total_credits,
        was_balanced=summary.was_balanced,
        anomaly_count=summary.anomaly_count,
        materiality_threshold=summary.materiality_threshold,
        row_count=summary.row_count,
    )


@router.post("/diagnostics/summary", response_model=DiagnosticSummaryResponse, status_code=201)
async def save_diagnostic_summary(
    summary_data: DiagnosticSummaryCreate,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db)
):
    """Save a diagnostic summary for variance tracking."""
    log_secure_operation(
        "diagnostic_summary_save",
        f"User {current_user.id} saving summary for client {summary_data.client_id}"
    )

    client = db.query(Client).filter(
        Client.id == summary_data.client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    period_date = None
    if summary_data.period_date:
        try:
            period_date = date_type.fromisoformat(summary_data.period_date)
        except ValueError:
            log_secure_operation("period_date_parse_error", f"Invalid date format: {summary_data.period_date}")

    period_type = None
    if summary_data.period_type:
        try:
            period_type = PeriodType(summary_data.period_type)
        except ValueError:
            log_secure_operation("period_type_parse_error", f"Invalid period type: {summary_data.period_type}")

    bs = summary_data.balance_sheet
    inc = summary_data.income_statement
    ratios = summary_data.ratios

    db_summary = DiagnosticSummary(
        client_id=summary_data.client_id,
        user_id=current_user.id,
        period_date=period_date,
        period_type=period_type,
        filename_hash=hash_filename(summary_data.filename),
        filename_display=get_filename_display(summary_data.filename),
        total_assets=bs.total_assets,
        current_assets=bs.current_assets,
        inventory=bs.inventory,
        total_liabilities=bs.total_liabilities,
        current_liabilities=bs.current_liabilities,
        total_equity=bs.total_equity,
        total_revenue=inc.total_revenue,
        cost_of_goods_sold=inc.cost_of_goods_sold,
        total_expenses=inc.total_expenses,
        operating_expenses=inc.operating_expenses,
        current_ratio=ratios.current_ratio,
        quick_ratio=ratios.quick_ratio,
        debt_to_equity=ratios.debt_to_equity,
        gross_margin=ratios.gross_margin,
        net_profit_margin=ratios.net_profit_margin,
        operating_margin=ratios.operating_margin,
        return_on_assets=ratios.return_on_assets,
        return_on_equity=ratios.return_on_equity,
        total_debits=summary_data.total_debits,
        total_credits=summary_data.total_credits,
        was_balanced=summary_data.was_balanced,
        anomaly_count=summary_data.anomaly_count,
        materiality_threshold=summary_data.materiality_threshold,
        row_count=summary_data.row_count,
    )

    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)

    return _summary_to_response(db_summary)


@router.get("/diagnostics/summary/{client_id}/previous", response_model=Optional[DiagnosticSummaryResponse])
async def get_previous_diagnostic_summary(
    client_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Get the most recent diagnostic summary for a client."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    summary = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id
    ).order_by(DiagnosticSummary.timestamp.desc()).first()

    if not summary:
        return None

    return _summary_to_response(summary)


@router.get("/diagnostics/summary/{client_id}/history", response_model=DiagnosticHistoryResponse)
async def get_diagnostic_history(
    client_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Get diagnostic summary history for a client."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    summaries = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id
    ).order_by(DiagnosticSummary.timestamp.desc()).limit(limit).all()

    return {
        "client_id": client_id,
        "client_name": client.name,
        "summaries": [s.to_dict() for s in summaries],
        "total_count": len(summaries),
    }
