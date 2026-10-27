"""
Segregation of Duties Routes (Sprint 630).

Form/upload-input only — zero-storage compliant. Analyzes a user-role and
role-permission matrix against a hardcoded SoD rule library and returns a
ranked conflict matrix.

Tier access (Sprint 789): standard entitlement gating, same as the other five
tools promoted in Sprint 689b–g. This route previously carried a bespoke
``require_enterprise_tier`` dependency that 403'd Solo and Professional — the
only hardcoded tier comparison in any route module — while the entitlements
table, the tool catalog, the Terms of Service tier table and the pricing page
all sold Segregation of Duties to both. See Sprint 789 for the full surface list.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import User, require_verified_user
from database import get_db
from shared.export_helpers import MEDIA_CSV, attachment_response
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_route import enforce_tool_access, run_json_tool
from sod_engine import (
    DEFAULT_SOD_RULES,
    RolePermission,
    SodResult,
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
    # Sprint 787b: optional engagement link so a run lands in the workpaper trail.
    engagement_id: Optional[int] = Field(None, description="Optional engagement to link this run to")


class SodAnalysisResponse(BaseModel):
    conflicts: list[dict]
    user_summaries: list[dict]
    rules_evaluated: int
    users_evaluated: int
    users_with_conflicts: int
    high_risk_users: int
    unmatched_permissions: list[str] = []


# =============================================================================
# Helpers
# =============================================================================


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
    current_user: User = Depends(require_verified_user),
) -> dict:
    """Return the hardcoded SoD rule library so the frontend can render a
    rule reference card.

    Reference data, so no entitlement check — it exposes the rule library, not
    an analysis of customer data. Mirrors ``/audit/book-to-tax/standard-adjustments``.
    """
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
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> SodAnalysisResponse:
    """Run the SoD checker against the supplied matrices."""

    # Sprint 789: standard tier + upload-quota gating, matching 689c–g.
    # Sprint 787b: unlike 689c–g this route maps no exception to a 400 itself,
    # because the engine does not raise on bad input — _build_extra_rule does,
    # as a 400 for an unrecognised severity. That is still a failed run from the
    # engagement's point of view, so it is recorded and re-raised unchanged.
    # Sprint 819: the sequence lives in shared/testing_route.py::run_json_tool.
    def _analyze() -> SodResult:
        users, roles, extra = _build_inputs(payload)
        return analyze_segregation_of_duties(users, roles, extra_rules=extra or None)

    result = run_json_tool(
        db=db,
        current_user=current_user,
        tool_name="sod_checker",
        engagement_id=payload.engagement_id,
        compute=_analyze,
        unexpected_errors=(),
        reraise_errors=(HTTPException, ValueError, KeyError, TypeError),
    )
    return SodAnalysisResponse(**result.to_dict())


@router.post("/audit/sod/analyze.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def analyze_sod_csv(
    request: Request,
    payload: SodAnalysisRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> Response:
    """CSV export of the SoD analysis."""
    # Sprint 789: export mirrors the analyze-route gating, minus the quota
    # increment — the same split 689c–g use for their export.csv endpoints.
    enforce_tool_access(current_user, "sod_checker", db)

    users, roles, extra = _build_inputs(payload)
    result = analyze_segregation_of_duties(users, roles, extra_rules=extra or None)
    csv_text = sod_result_to_csv(result)
    return attachment_response(csv_text, "sod_analysis.csv", MEDIA_CSV, quote_filename=False)
