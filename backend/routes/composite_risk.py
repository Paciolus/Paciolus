"""
Paciolus API — Composite Risk Scoring Routes

ISA 315 (Revised 2019): Structured risk assessment combining auditor-provided
inherent/control risk inputs with automated diagnostic data.

POST /composite-risk/profile — Build composite risk profile from auditor inputs
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from auth import require_verified_user
from composite_risk_engine import (
    VALID_ASSERTIONS,
    AccountRiskAssessment,
    build_composite_risk_profile,
)
from database import get_db
from models import User
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["composite-risk"])


# ═══════════════════════════════════════════════════════════════
# Pydantic request/response schemas
# ═══════════════════════════════════════════════════════════════

_VALID_RISK_LEVELS = {"low", "moderate", "elevated", "high"}


class AccountRiskAssessmentInput(BaseModel):
    """Single auditor-provided risk assessment for an account/assertion pair."""

    account_name: str = Field(..., min_length=1, max_length=200, description="Account name")
    assertion: str = Field(
        ...,
        description="Financial statement assertion: existence, completeness, valuation, rights, presentation",
    )
    inherent_risk: str = Field(..., description="Auditor-assessed inherent risk: low, moderate, elevated, high")
    control_risk: str = Field(..., description="Auditor-assessed control risk: low, moderate, elevated, high")
    fraud_risk_factor: bool = Field(default=False, description="Whether fraud risk factors are present")
    auditor_notes: str = Field(default="", max_length=1000, description="Optional auditor notes")

    @field_validator("assertion")
    @classmethod
    def validate_assertion(cls, v: str) -> str:
        v_lower = v.strip().lower()
        if v_lower not in VALID_ASSERTIONS:
            raise ValueError(f"Invalid assertion '{v}'. Must be one of: {', '.join(sorted(VALID_ASSERTIONS))}")
        return v_lower

    @field_validator("inherent_risk", "control_risk")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        v_lower = v.strip().lower()
        if v_lower not in _VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk level '{v}'. Must be one of: {', '.join(sorted(_VALID_RISK_LEVELS))}")
        return v_lower


class CompositeRiskProfileRequest(BaseModel):
    """Request body for building a composite risk profile."""

    account_assessments: list[AccountRiskAssessmentInput] = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Auditor-provided risk assessments (at least one required)",
    )

    # Optional automated data integration
    tb_diagnostic_score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="TB diagnostic anomaly density score (0-100)",
    )
    tb_diagnostic_tier: Optional[str] = Field(
        default=None,
        max_length=50,
        description="TB diagnostic tier label",
    )
    testing_scores: Optional[dict[str, float]] = Field(
        default=None,
        description="Tool composite scores keyed by tool name",
    )
    going_concern_indicators_triggered: int = Field(
        default=0,
        ge=0,
        le=20,
        description="Count of triggered going concern indicators",
    )


class AccountRiskAssessmentResponse(BaseModel):
    account_name: str
    assertion: str
    inherent_risk: str
    control_risk: str
    combined_risk: str
    fraud_risk_factor: bool
    auditor_notes: Optional[str] = None


class CompositeRiskProfileResponse(BaseModel):
    account_assessments: list[AccountRiskAssessmentResponse]
    tb_diagnostic_score: Optional[int] = None
    tb_diagnostic_tier: Optional[str] = None
    testing_scores: dict[str, float]
    going_concern_indicators_triggered: int
    high_risk_accounts: int
    fraud_risk_accounts: int
    total_assessments: int
    risk_distribution: dict[str, int]
    overall_risk_tier: Optional[str] = None
    disclaimer: str


# ═══════════════════════════════════════════════════════════════
# Endpoint
# ═══════════════════════════════════════════════════════════════


@router.post(
    "/composite-risk/profile",
    response_model=CompositeRiskProfileResponse,
)
@limiter.limit(RATE_LIMIT_AUDIT)
async def build_risk_profile(
    request: Request,
    body: CompositeRiskProfileRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Build a composite risk profile from auditor-provided risk assessments.

    ISA 315 (Revised 2019): Combines auditor-assessed inherent risk and
    control risk per account/assertion with optional automated diagnostic
    data. The composite profile STRUCTURES auditor inputs — it does not
    algorithmically determine risk classifications.

    Returns a structured risk matrix with distribution summary, overall
    risk tier (derived from auditor inputs), and mandatory disclaimer.
    """
    try:
        # Convert Pydantic models to engine dataclasses
        assessments = [
            AccountRiskAssessment(
                account_name=a.account_name,
                assertion=a.assertion,
                inherent_risk=a.inherent_risk,  # type: ignore[arg-type]
                control_risk=a.control_risk,  # type: ignore[arg-type]
                fraud_risk_factor=a.fraud_risk_factor,
                auditor_notes=a.auditor_notes,
            )
            for a in body.account_assessments
        ]

        profile = build_composite_risk_profile(
            account_assessments=assessments,
            tb_diagnostic_score=body.tb_diagnostic_score,
            tb_diagnostic_tier=body.tb_diagnostic_tier,
            testing_scores=body.testing_scores,
            going_concern_indicators_triggered=body.going_concern_indicators_triggered,
        )

        return profile.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("Composite risk profile build failed")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while building the composite risk profile.",
        )
