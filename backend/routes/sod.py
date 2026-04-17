"""
Segregation of Duties Routes (Sprint 630).

Form/upload-input only — zero-storage compliant. Analyzes a user-role and
role-permission matrix against a hardcoded SoD rule library and returns a
ranked conflict matrix. Enterprise-tier gated.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import User, require_verified_user
from shared.entitlements import UserTier
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from sod_engine import (
    DEFAULT_SOD_RULES,
    RolePermission,
    SodRule,
    SodSeverity,
    UserRoleAssignment,
    analyze_segregation_of_duties,
    sod_result_to_csv,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["segregation-of-duties"])


# =============================================================================
# Schemas
# =============================================================================


class UserAssignmentRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    user_name: str = Field(..., min_length=1, max_length=200)
    role_codes: list[str] = Field(default_factory=list, max_length=100)


class RolePermissionRequest(BaseModel):
    role_code: str = Field(..., min_length=1, max_length=100)
    permissions: list[str] = Field(default_factory=list, max_length=200)


class CustomRuleRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=32)
    title: str = Field(..., min_length=1, max_length=200)
    severity: str = Field(default="medium")  # high | medium | low
    permissions_required: list[str] = Field(default_factory=list, max_length=20)
    permissions_alternate: list[str] = Field(default_factory=list, max_length=20)
    mitigation: str = Field(default="", max_length=500)
    rationale: str = Field(default="", max_length=500)


class SodAnalysisRequest(BaseModel):
    user_assignments: list[UserAssignmentRequest] = Field(..., max_length=10000)
    role_permissions: list[RolePermissionRequest] = Field(..., max_length=2000)
    extra_rules: list[CustomRuleRequest] = Field(default_factory=list, max_length=200)


class SodAnalysisResponse(BaseModel):
    conflicts: list[dict]
    user_summaries: list[dict]
    rules_evaluated: int
    users_evaluated: int
    users_with_conflicts: int
    high_risk_users: int


# =============================================================================
# Helpers
# =============================================================================


def require_enterprise_tier(
    current_user: User = Depends(require_verified_user),
) -> User:
    """SoD checker is Enterprise-only. Single-place gate."""
    if current_user.tier != UserTier.ENTERPRISE:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tier_locked",
                "feature": "sod_checker",
                "current_tier": current_user.tier.value,
                "message": "Segregation of Duties Checker is available on the Enterprise plan only.",
            },
        )
    return current_user


def _build_inputs(
    payload: SodAnalysisRequest,
) -> tuple[list[UserRoleAssignment], list[RolePermission], list[SodRule]]:
    users = [
        UserRoleAssignment(
            user_id=u.user_id,
            user_name=u.user_name,
            role_codes=list(u.role_codes),
        )
        for u in payload.user_assignments
    ]
    roles = [RolePermission(role_code=r.role_code, permissions=list(r.permissions)) for r in payload.role_permissions]
    extra = [_build_extra_rule(r) for r in payload.extra_rules]
    return users, roles, extra


def _build_extra_rule(req: CustomRuleRequest) -> SodRule:
    sev = req.severity.lower()
    if sev not in {"high", "medium", "low"}:
        raise HTTPException(status_code=400, detail=f"Invalid severity for rule {req.code}: {req.severity!r}")
    return SodRule(
        code=req.code,
        title=req.title,
        severity=SodSeverity(sev),
        permissions_required=frozenset(p.strip().lower().replace(" ", "_") for p in req.permissions_required),
        permissions_alternate=frozenset(p.strip().lower().replace(" ", "_") for p in req.permissions_alternate),
        mitigation=req.mitigation,
        rationale=req.rationale,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/audit/sod/rules")
@limiter.limit(RATE_LIMIT_AUDIT)
def list_default_rules(
    request: Request,
    current_user: User = Depends(require_enterprise_tier),
) -> dict:
    """Return the hardcoded SoD rule library so the frontend can render a
    rule reference card."""
    return {
        "rules": [
            {
                "code": rule.code,
                "title": rule.title,
                "severity": rule.severity.value,
                "permissions_required": sorted(rule.permissions_required),
                "permissions_alternate": sorted(rule.permissions_alternate),
                "mitigation": rule.mitigation,
                "rationale": rule.rationale,
            }
            for rule in DEFAULT_SOD_RULES
        ],
    }


@router.post("/audit/sod/analyze", response_model=SodAnalysisResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
def analyze_sod(
    request: Request,
    payload: SodAnalysisRequest,
    current_user: User = Depends(require_enterprise_tier),
) -> SodAnalysisResponse:
    """Run the SoD checker against the supplied matrices."""
    users, roles, extra = _build_inputs(payload)
    result = analyze_segregation_of_duties(users, roles, extra_rules=extra or None)
    return SodAnalysisResponse(**result.to_dict())  # type: ignore[arg-type]


@router.post("/audit/sod/analyze.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def analyze_sod_csv(
    request: Request,
    payload: SodAnalysisRequest,
    current_user: User = Depends(require_enterprise_tier),
) -> StreamingResponse:
    """CSV export of the SoD analysis."""
    users, roles, extra = _build_inputs(payload)
    result = analyze_segregation_of_duties(users, roles, extra_rules=extra or None)
    csv_text = sod_result_to_csv(result)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sod_analysis.csv"},
    )
