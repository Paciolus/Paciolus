"""
Account Risk Heatmap Routes (Sprint 627).

Aggregates per-account audit signals across multiple diagnostic engines into a
single triage-density view. Two endpoints:

- POST /audit/account-risk-heatmap        → JSON heatmap from caller-supplied
                                             signals or upstream engine outputs
- POST /audit/account-risk-heatmap/export.csv → CSV export of the same

Zero-storage: nothing persisted. Operates on in-memory signal records.
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from account_risk_heatmap_engine import (
    AccountRiskHeatmapResult,
    RiskSignal,
    build_signals_from_accrual_findings,
    build_signals_from_audit_anomalies,
    build_signals_from_classification_issues,
    build_signals_from_composite_risk,
    build_signals_from_cutoff_flags,
    compute_account_heatmap,
    heatmap_to_csv,
)
from auth import User, require_verified_user
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["account-risk-heatmap"])


# =============================================================================
# Schemas
# =============================================================================


class RawSignalRequest(BaseModel):
    """A direct RiskSignal record — caller has already normalized."""

    account_number: str = Field(default="", max_length=64)
    account_name: str = Field(..., min_length=1, max_length=200)
    source: str = Field(..., min_length=1, max_length=64)
    severity: str = Field(default="medium", max_length=16)
    issue: str = Field(..., min_length=1, max_length=500)
    materiality: str = Field(default="0", max_length=20)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class HeatmapRequest(BaseModel):
    """Signals can be passed either pre-normalized (`signals`) or as upstream
    engine outputs in their native dict shape (the adapter functions translate).
    All fields are optional — the engine runs against whatever subset is given.
    """

    signals: list[RawSignalRequest] = Field(default_factory=list)
    audit_anomalies: list[dict] = Field(default_factory=list)
    classification_issues: list[dict] = Field(default_factory=list)
    cutoff_flags: list[dict] = Field(default_factory=list)
    accrual_findings: list[dict] = Field(default_factory=list)
    composite_risk_profile: Optional[dict] = None


class HeatmapRowResponse(BaseModel):
    account_number: str
    account_name: str
    signal_count: int
    weighted_score: float
    sources: list[str]
    severities: dict[str, int]
    issues: list[str]
    total_materiality: str
    priority_tier: str
    rank: int


class HeatmapResponse(BaseModel):
    rows: list[HeatmapRowResponse]
    total_accounts_with_signals: int
    high_priority_count: int
    moderate_priority_count: int
    low_priority_count: int
    total_signals: int
    sources_active: list[str]


# =============================================================================
# Aggregation
# =============================================================================


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


def _build_all_signals(payload: HeatmapRequest) -> list[RiskSignal]:
    signals: list[RiskSignal] = [
        RiskSignal(
            account_number=s.account_number,
            account_name=s.account_name,
            source=s.source,
            severity=s.severity,
            issue=s.issue,
            materiality=_to_decimal("materiality", s.materiality),
            confidence=s.confidence,
        )
        for s in payload.signals
    ]
    signals.extend(build_signals_from_audit_anomalies(payload.audit_anomalies))
    signals.extend(build_signals_from_classification_issues(payload.classification_issues))
    signals.extend(build_signals_from_cutoff_flags(payload.cutoff_flags))
    signals.extend(build_signals_from_accrual_findings(payload.accrual_findings))
    signals.extend(build_signals_from_composite_risk(payload.composite_risk_profile))
    return signals


def _result_to_response(result: AccountRiskHeatmapResult) -> HeatmapResponse:
    return HeatmapResponse(
        rows=[HeatmapRowResponse(**r.to_dict()) for r in result.rows],
        total_accounts_with_signals=result.total_accounts_with_signals,
        high_priority_count=result.high_priority_count,
        moderate_priority_count=result.moderate_priority_count,
        low_priority_count=result.low_priority_count,
        total_signals=result.total_signals,
        sources_active=result.sources_active,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/audit/account-risk-heatmap", response_model=HeatmapResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
def generate_heatmap(
    request: Request,
    payload: HeatmapRequest,
    current_user: User = Depends(require_verified_user),
) -> HeatmapResponse:
    """Aggregate signals into a per-account heatmap with priority tiers."""
    signals = _build_all_signals(payload)
    result = compute_account_heatmap(signals)
    return _result_to_response(result)


@router.post("/audit/account-risk-heatmap/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_heatmap_csv(
    request: Request,
    payload: HeatmapRequest,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """CSV export of the heatmap."""
    signals = _build_all_signals(payload)
    result = compute_account_heatmap(signals)
    csv_text = heatmap_to_csv(result)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=account_risk_heatmap.csv"},
    )
