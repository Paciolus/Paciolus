"""
Internal metrics routes — Sprint 589: Founder Ops dashboard API.

Read-only endpoints for MRR, ARR, churn, trial funnel, and revenue history.
All endpoints gated to platform superadmins (Sprint 840 — previously any org
owner or paying solo user could read company-wide revenue figures).

Route group prefix: /internal/metrics
"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from auth import require_superadmin
from database import get_db
from models import User
from schemas.internal_metrics_schemas import (
    ChurnMetricsResponse,
    RevenueHistoryPoint,
    RevenueMetricsResponse,
    TrialFunnelResponse,
)
from shared.rate_limits import RATE_LIMIT_DEFAULT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/metrics", tags=["internal-metrics"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/revenue", response_model=RevenueMetricsResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_revenue_metrics(
    request: Request,
    user: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """MRR, ARR, subscriber counts, and 30-day MRR movements."""
    from billing.internal_metrics import compute_revenue_metrics

    return compute_revenue_metrics(db)


@router.get("/churn", response_model=ChurnMetricsResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_churn_metrics(
    request: Request,
    user: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Logo churn, revenue churn, and involuntary churn metrics (trailing 30 days)."""
    from billing.internal_metrics import compute_churn_metrics

    return compute_churn_metrics(db)


@router.get("/trial-funnel", response_model=TrialFunnelResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_trial_funnel(
    request: Request,
    user: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Trial funnel metrics: signups → first upload → report → conversion (trailing 30 days)."""
    from billing.internal_metrics import compute_trial_funnel

    return compute_trial_funnel(db)


@router.get("/revenue/history", response_model=list[RevenueHistoryPoint])
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_revenue_history(
    request: Request,
    user: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
    granularity: str = Query(default="monthly", pattern="^(daily|weekly|monthly)$"),
    start_date: str | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
) -> list[dict[str, Any]]:
    """Historical revenue snapshots for time series charting."""
    from billing.internal_metrics import compute_revenue_history

    parsed_start = None
    parsed_end = None

    if start_date:
        try:
            parsed_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")

    if end_date:
        try:
            parsed_end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")

    try:
        return compute_revenue_history(db, granularity=granularity, start_date=parsed_start, end_date=parsed_end)
    except ValueError as exc:  # Sprint 821: bounded range
        raise HTTPException(status_code=400, detail=str(exc))
