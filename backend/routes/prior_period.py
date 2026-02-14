"""
Paciolus API — Prior Period Comparison Routes
"""
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User, Client, DiagnosticSummary, PeriodType
from auth import require_current_user, require_verified_user
from prior_period_comparison import compare_periods
from shared.diagnostic_response_schemas import PeriodComparisonResponse

router = APIRouter(tags=["prior_period"])


class PeriodSaveResponse(BaseModel):
    status: str
    message: str
    period_id: int
    period_label: str


class PeriodSaveRequest(BaseModel):
    """Request to save current audit as a prior period."""
    period_label: str = Field(..., min_length=1, max_length=100, description="Human-readable period label (e.g., 'FY2025', 'Q3 2025')")
    period_date: Optional[date] = Field(None, description="Period end date (YYYY-MM-DD)")
    period_type: Optional[PeriodType] = Field(None, description="Period type: monthly, quarterly, annual")
    total_assets: float = 0.0
    current_assets: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    total_equity: float = 0.0
    total_revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    total_expenses: float = 0.0
    operating_expenses: float = 0.0
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    gross_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    total_debits: float = 0.0
    total_credits: float = 0.0
    was_balanced: bool = True
    anomaly_count: int = 0
    materiality_threshold: float = 0.0
    row_count: int = 0


class PeriodListItemResponse(BaseModel):
    """Summary of a saved period for list display."""
    id: int
    period_label: str
    period_date: Optional[str]
    period_type: Optional[str]
    timestamp: str
    total_assets: float
    total_revenue: float


class CompareRequest(BaseModel):
    """Request to compare current audit to a prior period."""
    prior_period_id: int = Field(..., description="ID of the prior period to compare against")
    current_label: str = Field("Current Period", min_length=1, max_length=100, description="Label for current period")
    total_assets: float = 0.0
    current_assets: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    total_equity: float = 0.0
    total_revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    total_expenses: float = 0.0
    operating_expenses: float = 0.0
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    gross_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    total_debits: float = 0.0
    total_credits: float = 0.0
    anomaly_count: int = 0
    row_count: int = 0


@router.post("/clients/{client_id}/periods", response_model=PeriodSaveResponse, status_code=201)
async def save_prior_period(
    client_id: int,
    period_data: PeriodSaveRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Save current audit data as a prior period for future comparison."""
    log_secure_operation("save_period", f"User {current_user.id} saving period for client {client_id}")

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db_summary = DiagnosticSummary(
        client_id=client_id,
        user_id=current_user.id,
        period_label=period_data.period_label,
        period_date=period_data.period_date,
        period_type=period_data.period_type,
        total_assets=period_data.total_assets,
        current_assets=period_data.current_assets,
        inventory=period_data.inventory,
        total_liabilities=period_data.total_liabilities,
        current_liabilities=period_data.current_liabilities,
        total_equity=period_data.total_equity,
        total_revenue=period_data.total_revenue,
        cost_of_goods_sold=period_data.cost_of_goods_sold,
        total_expenses=period_data.total_expenses,
        operating_expenses=period_data.operating_expenses,
        current_ratio=period_data.current_ratio,
        quick_ratio=period_data.quick_ratio,
        debt_to_equity=period_data.debt_to_equity,
        gross_margin=period_data.gross_margin,
        net_profit_margin=period_data.net_profit_margin,
        operating_margin=period_data.operating_margin,
        return_on_assets=period_data.return_on_assets,
        return_on_equity=period_data.return_on_equity,
        total_debits=period_data.total_debits,
        total_credits=period_data.total_credits,
        was_balanced=period_data.was_balanced,
        anomaly_count=period_data.anomaly_count,
        materiality_threshold=period_data.materiality_threshold,
        row_count=period_data.row_count,
    )

    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)

    return {
        "status": "success",
        "message": f"Period '{period_data.period_label}' saved successfully",
        "period_id": db_summary.id,
        "period_label": db_summary.period_label,
    }


@router.get("/clients/{client_id}/periods", response_model=List[PeriodListItemResponse])
async def list_prior_periods(
    client_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """List saved prior periods for a client."""
    log_secure_operation("list_periods", f"User {current_user.id} listing periods for client {client_id}")

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    periods = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id,
        DiagnosticSummary.period_label.isnot(None)
    ).order_by(
        DiagnosticSummary.period_date.desc().nullslast(),
        DiagnosticSummary.timestamp.desc()
    ).limit(limit).all()

    return [
        PeriodListItemResponse(
            id=p.id,
            period_label=p.period_label or f"Period {p.id}",
            period_date=p.period_date.isoformat() if p.period_date else None,
            period_type=p.period_type.value if p.period_type else None,
            timestamp=p.timestamp.isoformat() if p.timestamp else "",
            total_assets=p.total_assets or 0.0,
            total_revenue=p.total_revenue or 0.0,
        )
        for p in periods
    ]


@router.post("/audit/compare", response_model=PeriodComparisonResponse)
async def compare_to_prior_period(
    compare_data: CompareRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db)
):
    """Compare current audit results to a saved prior period."""
    log_secure_operation("compare_periods", f"User {current_user.id} comparing to period {compare_data.prior_period_id}")

    prior_period = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.id == compare_data.prior_period_id,
        DiagnosticSummary.user_id == current_user.id
    ).first()

    if not prior_period:
        raise HTTPException(status_code=404, detail="Prior period not found")

    current_data = {
        "total_assets": compare_data.total_assets,
        "current_assets": compare_data.current_assets,
        "inventory": compare_data.inventory,
        "total_liabilities": compare_data.total_liabilities,
        "current_liabilities": compare_data.current_liabilities,
        "total_equity": compare_data.total_equity,
        "total_revenue": compare_data.total_revenue,
        "cost_of_goods_sold": compare_data.cost_of_goods_sold,
        "total_expenses": compare_data.total_expenses,
        "operating_expenses": compare_data.operating_expenses,
        "current_ratio": compare_data.current_ratio,
        "quick_ratio": compare_data.quick_ratio,
        "debt_to_equity": compare_data.debt_to_equity,
        "gross_margin": compare_data.gross_margin,
        "net_profit_margin": compare_data.net_profit_margin,
        "operating_margin": compare_data.operating_margin,
        "return_on_assets": compare_data.return_on_assets,
        "return_on_equity": compare_data.return_on_equity,
        "total_debits": compare_data.total_debits,
        "total_credits": compare_data.total_credits,
        "anomaly_count": compare_data.anomaly_count,
        "row_count": compare_data.row_count,
    }

    prior_data = prior_period.to_dict()

    comparison = compare_periods(
        current_data=current_data,
        prior_data=prior_data,
        current_label=compare_data.current_label,
        prior_label=prior_period.period_label,
        prior_id=prior_period.id,
    )

    return comparison.to_dict()
