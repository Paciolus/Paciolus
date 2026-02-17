"""
Paciolus API — Trend Analysis & Industry Ratios Routes
"""
from datetime import date as date_type
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from models import Client, DiagnosticSummary, PeriodType, User
from ratio_engine import (
    CategoryTotals,
    PeriodSnapshot,
    RollingWindowAnalyzer,
    TrendAnalyzer,
)
from security_utils import log_secure_operation

router = APIRouter(tags=["trends"])


class ClientTrendsResponse(BaseModel):
    client_id: int
    client_name: str
    analysis: dict
    periods_analyzed: int
    period_type_filter: Optional[str] = None


class IndustryRatiosResponse(BaseModel):
    client_id: int
    client_name: str
    industry: str
    industry_display: str
    industry_type: str
    ratios: dict
    summary_date: Optional[str] = None
    available_industries: list


class RollingAnalysisResponse(BaseModel):
    client_id: int
    client_name: str
    analysis: dict
    periods_analyzed: int
    window_filter: Optional[int] = None
    period_type_filter: Optional[str] = None


def _summaries_to_snapshots(summaries) -> list[PeriodSnapshot]:
    """Convert DiagnosticSummary list to PeriodSnapshot list."""
    snapshots = []
    for summary in summaries:
        if summary.period_date:
            snapshot_date = summary.period_date
        else:
            snapshot_date = summary.timestamp.date() if summary.timestamp else date_type.today()

        snapshot_period_type = summary.period_type.value if summary.period_type else "monthly"

        totals = CategoryTotals(
            total_assets=summary.total_assets or 0.0,
            current_assets=summary.current_assets or 0.0,
            inventory=summary.inventory or 0.0,
            total_liabilities=summary.total_liabilities or 0.0,
            current_liabilities=summary.current_liabilities or 0.0,
            total_equity=summary.total_equity or 0.0,
            total_revenue=summary.total_revenue or 0.0,
            cost_of_goods_sold=summary.cost_of_goods_sold or 0.0,
            total_expenses=summary.total_expenses or 0.0,
            operating_expenses=summary.operating_expenses or 0.0,
        )

        ratios = {}
        if summary.current_ratio is not None:
            ratios["current_ratio"] = summary.current_ratio
        if summary.quick_ratio is not None:
            ratios["quick_ratio"] = summary.quick_ratio
        if summary.debt_to_equity is not None:
            ratios["debt_to_equity"] = summary.debt_to_equity
        if summary.gross_margin is not None:
            ratios["gross_margin"] = summary.gross_margin
        if summary.net_profit_margin is not None:
            ratios["net_profit_margin"] = summary.net_profit_margin
        if summary.operating_margin is not None:
            ratios["operating_margin"] = summary.operating_margin
        if summary.return_on_assets is not None:
            ratios["return_on_assets"] = summary.return_on_assets
        if summary.return_on_equity is not None:
            ratios["return_on_equity"] = summary.return_on_equity

        snapshot = PeriodSnapshot(
            period_date=snapshot_date,
            period_type=snapshot_period_type,
            category_totals=totals,
            ratios=ratios,
        )
        snapshots.append(snapshot)
    return snapshots


def _get_client_summaries(db: Session, client_id: int, user_id: int, period_type: str | None = None, limit: int = 36) -> list:
    """Query historical summaries for a client."""
    query = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == user_id
    )

    if period_type:
        try:
            pt = PeriodType(period_type)
            query = query.filter(DiagnosticSummary.period_type == pt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid period_type. Must be one of: monthly, quarterly, annual"
            )

    return query.order_by(
        DiagnosticSummary.period_date.asc().nullslast(),
        DiagnosticSummary.timestamp.asc()
    ).limit(limit).all()


@router.get("/clients/{client_id}/trends", response_model=ClientTrendsResponse)
def get_client_trends(
    client_id: int,
    period_type: Optional[str] = Query(default=None, description="Filter by period type: monthly, quarterly, annual"),
    limit: int = Query(default=12, ge=2, le=36, description="Number of periods to analyze"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Get trend analysis for a client's historical diagnostic data."""
    log_secure_operation(
        "trend_analysis_request",
        f"User {current_user.id} requesting trends for client {client_id}"
    )

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    summaries = _get_client_summaries(db, client_id, current_user.id, period_type, limit)

    if len(summaries) < 2:
        raise HTTPException(
            status_code=422,
            detail=f"Need at least 2 diagnostic summaries for trend analysis, found {len(summaries)}"
        )

    snapshots = _summaries_to_snapshots(summaries)
    analyzer = TrendAnalyzer(snapshots)
    analysis = analyzer.get_full_analysis()

    log_secure_operation(
        "trend_analysis_complete",
        f"Analyzed {len(snapshots)} periods for client {client_id}"
    )

    return {
        "client_id": client_id,
        "client_name": client.name,
        "analysis": analysis,
        "periods_analyzed": len(snapshots),
        "period_type_filter": period_type,
    }


@router.get("/clients/{client_id}/industry-ratios", response_model=IndustryRatiosResponse)
def get_client_industry_ratios(
    client_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Get industry-specific ratios for a client."""
    from industry_ratios import calculate_industry_ratios, get_available_industries

    log_secure_operation(
        "industry_ratios_request",
        f"User {current_user.id} requesting industry ratios for client {client_id}"
    )

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    latest_summary = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id
    ).order_by(
        DiagnosticSummary.timestamp.desc()
    ).first()

    if not latest_summary:
        raise HTTPException(
            status_code=422,
            detail="Run a diagnostic assessment first to calculate industry ratios"
        )

    totals_dict = {
        "total_assets": latest_summary.total_assets or 0.0,
        "current_assets": latest_summary.current_assets or 0.0,
        "inventory": latest_summary.inventory or 0.0,
        "total_liabilities": latest_summary.total_liabilities or 0.0,
        "current_liabilities": latest_summary.current_liabilities or 0.0,
        "total_equity": latest_summary.total_equity or 0.0,
        "total_revenue": latest_summary.total_revenue or 0.0,
        "cost_of_goods_sold": latest_summary.cost_of_goods_sold or 0.0,
        "total_expenses": latest_summary.total_expenses or 0.0,
        "operating_expenses": latest_summary.operating_expenses or 0.0,
    }

    industry = client.industry.value if client.industry else "other"
    industry_result = calculate_industry_ratios(industry, totals_dict)

    log_secure_operation(
        "industry_ratios_complete",
        f"Calculated {industry_result['industry']} ratios for client {client_id}"
    )

    return {
        "client_id": client_id,
        "client_name": client.name,
        "industry": industry,
        "industry_display": industry_result["industry"],
        "industry_type": industry_result["industry_type"],
        "ratios": industry_result["ratios"],
        "summary_date": latest_summary.timestamp.isoformat() if latest_summary.timestamp else None,
        "available_industries": get_available_industries(),
    }


@router.get("/clients/{client_id}/rolling-analysis", response_model=RollingAnalysisResponse)
def get_client_rolling_analysis(
    client_id: int,
    window: Optional[int] = Query(default=None, description="Specific window size (3, 6, or 12 months)"),
    period_type: Optional[str] = Query(default=None, description="Filter by period type: monthly, quarterly, annual"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Get rolling window analysis for a client's historical data."""
    log_secure_operation(
        "rolling_analysis_request",
        f"User {current_user.id} requesting rolling analysis for client {client_id}"
    )

    if window is not None and window not in [3, 6, 12]:
        raise HTTPException(
            status_code=400,
            detail="Invalid window size. Must be 3, 6, or 12 months."
        )

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    summaries = _get_client_summaries(db, client_id, current_user.id, period_type, 36)

    if len(summaries) < 2:
        raise HTTPException(
            status_code=422,
            detail=f"Need at least 2 diagnostic summaries for rolling analysis, found {len(summaries)}"
        )

    snapshots = _summaries_to_snapshots(summaries)
    analyzer = RollingWindowAnalyzer(snapshots)
    analysis = analyzer.get_full_analysis()

    if window is not None:
        for key in analysis.get("category_rolling", {}):
            metric = analysis["category_rolling"][key]
            if "rolling_averages" in metric:
                filtered = {k: v for k, v in metric["rolling_averages"].items() if k == str(window)}
                metric["rolling_averages"] = filtered

        for key in analysis.get("ratio_rolling", {}):
            metric = analysis["ratio_rolling"][key]
            if "rolling_averages" in metric:
                filtered = {k: v for k, v in metric["rolling_averages"].items() if k == str(window)}
                metric["rolling_averages"] = filtered

    log_secure_operation(
        "rolling_analysis_complete",
        f"Analyzed {len(snapshots)} periods for client {client_id}"
    )

    return {
        "client_id": client_id,
        "client_name": client.name,
        "analysis": analysis,
        "periods_analyzed": len(snapshots),
        "window_filter": window,
        "period_type_filter": period_type,
    }
