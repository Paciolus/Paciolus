"""
Segregation of Duties (SoD) Engine (Sprint 630).

Analyzes a user-role and role-permission matrix against a hardcoded library of
known SoD conflict rules. Per-user risk ranking with mitigating control
suggestions. Required for SOC 1 / internal-audit engagements.

Form/upload-input only — zero-storage compliant. The engine consumes the two
matrices, runs all rules against the effective per-user permission set, and
returns a ranked conflict matrix without persisting anything.

Scope:
- Single matrix per call. Multi-system role bridging is out-of-scope.
- Hardcoded rule library covers the common AICPA / SOX 404 SoD patterns.
  Custom rules can be passed in via the `extra_rules` argument.
- Mitigating controls are suggested per rule (compensating-control framework
  per COSO 2013) but are not assessed for operating effectiveness — that
  requires auditor judgment.

Tier gating (Enterprise) is enforced at the route layer, not in the engine.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SodSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# Rule library
# =============================================================================


@dataclass(frozen=True)
class SodRule:
    """A single SoD conflict rule. A user holding ALL `permissions_required`
    triggers the rule. `permissions_alternate` represents an OR-group of
    permissions any one of which counts as the second leg of the conflict.
    """

    code: str  # e.g. "AP-01"
    title: str
    severity: SodSeverity
    permissions_required: frozenset[str]
    permissions_alternate: frozenset[str] = frozenset()
    mitigation: str = ""
    rationale: str = ""

    def matches(self, user_permissions: frozenset[str]) -> bool:
        if not self.permissions_required.issubset(user_permissions):
            return False
        if self.permissions_alternate:
            if not self.permissions_alternate.intersection(user_permissions):
                return False
        return True


# Hardcoded SoD rule library. Permission strings are normalized to
# lowercase / underscore form on ingestion.
DEFAULT_SOD_RULES: tuple[SodRule, ...] = (
    SodRule(
        code="AP-01",
        title="AP: vendor master + invoice creation",
        severity=SodSeverity.HIGH,
        permissions_required=frozenset({"vendor_create"}),
        permissions_alternate=frozenset({"ap_invoice_create", "ap_invoice_post"}),
        mitigation="Require independent vendor master review report; quarterly attestation.",
        rationale="Allows insertion of fictitious vendor + corresponding invoice.",
    ),
    SodRule(
        code="AP-02",
        title="AP: invoice creation + payment release",
        severity=SodSeverity.HIGH,
        permissions_required=frozenset({"ap_invoice_create"}),
        permissions_alternate=frozenset({"ap_payment_release", "ap_payment_post"}),
        mitigation="Require dual-signature payment authorization above materiality threshold.",
        rationale="Standard fictitious-invoice fraud pattern.",
    ),
    SodRule(
        code="AP-03",
        title="AP: payment + bank reconciliation",
        severity=SodSeverity.HIGH,
        permissions_required=frozenset({"ap_payment_release"}),
        permissions_alternate=frozenset({"bank_reconciliation_perform"}),
        mitigation="Independent bank reconciliation by treasury or finance director.",
        rationale="Allows concealment of fraudulent payments via reconciling-item adjustments.",
    ),
    SodRule(
        code="JE-01",
        title="JE: create + post",
        severity=SodSeverity.HIGH,
        permissions_required=frozenset({"je_create"}),
        permissions_alternate=frozenset({"je_post", "je_approve"}),
        mitigation="Require independent JE approval workflow with auditor sampling.",
        rationale="Self-approved manual JEs are the highest fraud-risk pathway (PCAOB AS 2401.58).",
    ),
    SodRule(
        code="JE-02",
        title="JE: posting + period close",
        severity=SodSeverity.MEDIUM,
        permissions_required=frozenset({"je_post"}),
        permissions_alternate=frozenset({"period_close_run"}),
        mitigation="Period close performed by controller; reviewed by CFO/finance director.",
        rationale="Allows backdated entries to be posted into a closed period without review.",
    ),
    SodRule(
        code="PR-01",
        title="Payroll: master + payment",
        severity=SodSeverity.HIGH,
        permissions_required=frozenset({"payroll_employee_create"}),
        permissions_alternate=frozenset({"payroll_payment_release"}),
        mitigation="HR adds employees; payroll only processes for active employees on HR roster.",
        rationale="Ghost-employee fraud pattern (BLS 2023: ~17% of payroll fraud cases).",
    ),
    SodRule(
        code="PR-02",
        title="Payroll: rate change + payment",
        severity=SodSeverity.MEDIUM,
        permissions_required=frozenset({"payroll_rate_change"}),
        permissions_alternate=frozenset({"payroll_payment_release"}),
        mitigation="Rate changes require HR approval routed through workflow before payroll processes.",
        rationale="Allows unauthorized self-promotion or bonus.",
    ),
    SodRule(
        code="REV-01",
        title="Revenue: customer create + credit memo",
        severity=SodSeverity.MEDIUM,
        permissions_required=frozenset({"customer_create"}),
        permissions_alternate=frozenset({"credit_memo_issue", "credit_memo_approve"}),
        mitigation="Credit memo approval requires manager sign-off above threshold.",
        rationale="Allows write-off of fraudulent receivables to fictitious customers.",
    ),
    SodRule(
        code="REV-02",
        title="Revenue: invoice + cash receipt application",
        severity=SodSeverity.MEDIUM,
        permissions_required=frozenset({"ar_invoice_create"}),
        permissions_alternate=frozenset({"cash_receipt_apply"}),
        mitigation="Lockbox processing or independent cash application by AR clerk.",
        rationale="Allows lapping fraud — applying customer A's payment to customer B.",
    ),
    SodRule(
        code="INV-01",
        title="Inventory: physical custody + accounting record",
        severity=SodSeverity.MEDIUM,
        permissions_required=frozenset({"inventory_physical_custody"}),
        permissions_alternate=frozenset({"inventory_count_adjust", "inventory_write_off"}),
        mitigation="Cycle counts performed by independent counter; significant adjustments require approval.",
        rationale="Allows concealment of theft through ledger adjustments.",
    ),
    SodRule(
        code="ADM-01",
        title="System: user admin + transactional access",
        severity=SodSeverity.HIGH,
        permissions_required=frozenset({"user_admin"}),
        permissions_alternate=frozenset(
            {
                "ap_invoice_create",
                "je_create",
                "payroll_payment_release",
                "credit_memo_issue",
            }
        ),
        mitigation="System administrators should not hold any transactional permissions in the same instance.",
        rationale="Admin can modify their own access, defeating any other SoD control.",
    ),
)


# =============================================================================
# Inputs / outputs
# =============================================================================


@dataclass
class UserRoleAssignment:
    user_id: str
    user_name: str
    role_codes: list[str]


@dataclass
class RolePermission:
    role_code: str
    permissions: list[str]


@dataclass
class SodConflict:
    user_id: str
    user_name: str
    rule_code: str
    rule_title: str
    severity: SodSeverity
    triggering_permissions: list[str]
    triggering_roles: list[str]
    mitigation: str
    rationale: str

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "rule_code": self.rule_code,
            "rule_title": self.rule_title,
            "severity": self.severity.value,
            "triggering_permissions": sorted(self.triggering_permissions),
            "triggering_roles": sorted(self.triggering_roles),
            "mitigation": self.mitigation,
            "rationale": self.rationale,
        }


@dataclass
class UserSodSummary:
    user_id: str
    user_name: str
    conflict_count: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    risk_score: float  # high*3 + med*2 + low*1
    risk_tier: str  # "high" | "moderate" | "low"

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "conflict_count": self.conflict_count,
            "high_severity_count": self.high_severity_count,
            "medium_severity_count": self.medium_severity_count,
            "low_severity_count": self.low_severity_count,
            "risk_score": round(self.risk_score, 2),
            "risk_tier": self.risk_tier,
        }


@dataclass
class SodResult:
    conflicts: list[SodConflict]
    user_summaries: list[UserSodSummary]
    rules_evaluated: int
    users_evaluated: int
    users_with_conflicts: int
    high_risk_users: int

    def to_dict(self) -> dict:
        return {
            "conflicts": [c.to_dict() for c in self.conflicts],
            "user_summaries": [u.to_dict() for u in self.user_summaries],
            "rules_evaluated": self.rules_evaluated,
            "users_evaluated": self.users_evaluated,
            "users_with_conflicts": self.users_with_conflicts,
            "high_risk_users": self.high_risk_users,
        }


# =============================================================================
# Engine
# =============================================================================


def _normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _build_role_map(role_permissions: Iterable[RolePermission]) -> dict[str, frozenset[str]]:
    result: dict[str, frozenset[str]] = {}
    for rp in role_permissions:
        normalized = frozenset(_normalize(p) for p in rp.permissions if p.strip())
        result[_normalize(rp.role_code)] = normalized
    return result


def _effective_permissions(
    user: UserRoleAssignment,
    role_map: dict[str, frozenset[str]],
) -> tuple[frozenset[str], dict[str, list[str]]]:
    """Resolve the effective permission set for a user across all assigned
    roles. Returns (permissions, permission → roles map).
    """
    permissions: set[str] = set()
    perm_to_roles: dict[str, list[str]] = {}
    for role_code in user.role_codes:
        normalized_role = _normalize(role_code)
        role_perms = role_map.get(normalized_role, frozenset())
        for perm in role_perms:
            permissions.add(perm)
            perm_to_roles.setdefault(perm, []).append(normalized_role)
    return frozenset(permissions), perm_to_roles


def _risk_tier(score: float) -> str:
    if score >= 6:
        return "high"
    if score >= 3:
        return "moderate"
    return "low"


def analyze_segregation_of_duties(
    user_assignments: Iterable[UserRoleAssignment],
    role_permissions: Iterable[RolePermission],
    *,
    extra_rules: Optional[Iterable[SodRule]] = None,
) -> SodResult:
    """Run the SoD checker against the supplied matrices.

    Returns a SodResult with a per-conflict listing and a per-user risk
    ranking. Users with no conflicts are still included in the per-user
    summary with a 'low' risk tier.
    """
    rules: list[SodRule] = list(DEFAULT_SOD_RULES)
    if extra_rules:
        rules.extend(extra_rules)

    role_map = _build_role_map(role_permissions)

    conflicts: list[SodConflict] = []
    summaries: list[UserSodSummary] = []
    users_evaluated = 0
    users_with_conflicts = 0
    high_risk_users = 0

    for user in user_assignments:
        users_evaluated += 1
        permissions, perm_to_roles = _effective_permissions(user, role_map)
        user_conflicts: list[SodConflict] = []
        for rule in rules:
            if not rule.matches(permissions):
                continue
            triggering_perms = sorted(
                rule.permissions_required.union(rule.permissions_alternate.intersection(permissions))
            )
            triggering_roles_set: set[str] = set()
            for perm in triggering_perms:
                for r in perm_to_roles.get(perm, []):
                    triggering_roles_set.add(r)
            user_conflicts.append(
                SodConflict(
                    user_id=user.user_id,
                    user_name=user.user_name,
                    rule_code=rule.code,
                    rule_title=rule.title,
                    severity=rule.severity,
                    triggering_permissions=triggering_perms,
                    triggering_roles=sorted(triggering_roles_set),
                    mitigation=rule.mitigation,
                    rationale=rule.rationale,
                )
            )
        conflicts.extend(user_conflicts)

        high_count = sum(1 for c in user_conflicts if c.severity == SodSeverity.HIGH)
        med_count = sum(1 for c in user_conflicts if c.severity == SodSeverity.MEDIUM)
        low_count = sum(1 for c in user_conflicts if c.severity == SodSeverity.LOW)
        score = high_count * 3.0 + med_count * 2.0 + low_count * 1.0
        tier = _risk_tier(score)

        if user_conflicts:
            users_with_conflicts += 1
        if tier == "high":
            high_risk_users += 1

        summaries.append(
            UserSodSummary(
                user_id=user.user_id,
                user_name=user.user_name,
                conflict_count=len(user_conflicts),
                high_severity_count=high_count,
                medium_severity_count=med_count,
                low_severity_count=low_count,
                risk_score=score,
                risk_tier=tier,
            )
        )

    summaries.sort(key=lambda s: (s.risk_score, s.conflict_count), reverse=True)

    return SodResult(
        conflicts=conflicts,
        user_summaries=summaries,
        rules_evaluated=len(rules),
        users_evaluated=users_evaluated,
        users_with_conflicts=users_with_conflicts,
        high_risk_users=high_risk_users,
    )


# =============================================================================
# CSV export
# =============================================================================


def sod_result_to_csv(result: SodResult) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["USER RISK SUMMARY"])
    writer.writerow(["User ID", "User Name", "Conflicts", "High", "Medium", "Low", "Risk Score", "Risk Tier"])
    for summary in result.user_summaries:
        writer.writerow(
            [
                summary.user_id,
                summary.user_name,
                summary.conflict_count,
                summary.high_severity_count,
                summary.medium_severity_count,
                summary.low_severity_count,
                f"{summary.risk_score:.2f}",
                summary.risk_tier,
            ]
        )

    writer.writerow([])
    writer.writerow(["CONFLICTS"])
    writer.writerow(
        [
            "User ID",
            "User Name",
            "Rule",
            "Title",
            "Severity",
            "Triggering Permissions",
            "Triggering Roles",
            "Mitigation",
        ]
    )
    for conflict in result.conflicts:
        writer.writerow(
            [
                conflict.user_id,
                conflict.user_name,
                conflict.rule_code,
                conflict.rule_title,
                conflict.severity.value,
                ", ".join(conflict.triggering_permissions),
                ", ".join(conflict.triggering_roles),
                conflict.mitigation,
            ]
        )
    return buffer.getvalue()
