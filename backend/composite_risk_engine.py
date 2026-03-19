"""
Paciolus — Composite Risk Scoring Engine
ISA 315 (Revised 2019) — Understanding the Entity and Its Environment

Combines auditor-provided risk assessments with automated diagnostic data
to produce an engagement-level risk matrix. This engine does NOT replace
auditor judgment — it structures and organizes risk inputs.

Guardrail: The composite score is a STRUCTURING TOOL, not an evaluative
conclusion. All risk classifications remain auditor judgment.

All computation is ephemeral (zero-storage compliance).
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

RiskLevel = Literal["low", "moderate", "elevated", "high"]

VALID_ASSERTIONS = frozenset({"existence", "completeness", "valuation", "rights", "presentation"})

RISK_LEVEL_WEIGHTS: dict[RiskLevel, int] = {
    "low": 1,
    "moderate": 2,
    "elevated": 3,
    "high": 4,
}

DISCLAIMER = (
    "IMPORTANT: This composite risk profile structures auditor-provided risk "
    "assessments alongside automated diagnostic data. Risk classifications are "
    "auditor judgment per ISA 315 and are not algorithmically determined. "
    "This tool does not replace the auditor's independent assessment."
)


# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════


@dataclass
class AccountRiskAssessment:
    """Auditor-provided risk assessment for a single account/assertion."""

    account_name: str
    assertion: str  # existence, completeness, valuation, rights, presentation
    inherent_risk: RiskLevel
    control_risk: RiskLevel
    fraud_risk_factor: bool = False
    auditor_notes: str = ""

    def to_dict(self) -> dict:
        result: dict = {
            "account_name": self.account_name,
            "assertion": self.assertion,
            "inherent_risk": self.inherent_risk,
            "control_risk": self.control_risk,
            "combined_risk": compute_combined_risk_level(self.inherent_risk, self.control_risk),
            "fraud_risk_factor": self.fraud_risk_factor,
        }
        if self.auditor_notes:
            result["auditor_notes"] = self.auditor_notes
        return result


@dataclass
class CompositeRiskProfile:
    """Engagement-level composite risk profile."""

    account_assessments: list[AccountRiskAssessment] = field(default_factory=list)

    # Automated data integration
    tb_diagnostic_score: Optional[int] = None
    tb_diagnostic_tier: Optional[str] = None
    testing_scores: dict[str, float] = field(default_factory=dict)
    going_concern_indicators_triggered: int = 0

    # Computed summaries
    high_risk_accounts: int = 0
    fraud_risk_accounts: int = 0
    total_assessments: int = 0
    risk_distribution: dict[str, int] = field(default_factory=dict)
    overall_risk_tier: Optional[str] = None

    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict:
        return {
            "account_assessments": [a.to_dict() for a in self.account_assessments],
            "tb_diagnostic_score": self.tb_diagnostic_score,
            "tb_diagnostic_tier": self.tb_diagnostic_tier,
            "testing_scores": self.testing_scores,
            "going_concern_indicators_triggered": self.going_concern_indicators_triggered,
            "high_risk_accounts": self.high_risk_accounts,
            "fraud_risk_accounts": self.fraud_risk_accounts,
            "total_assessments": self.total_assessments,
            "risk_distribution": self.risk_distribution,
            "overall_risk_tier": self.overall_risk_tier,
            "disclaimer": self.disclaimer,
        }


# ═══════════════════════════════════════════════════════════════
# Risk combination logic
# ═══════════════════════════════════════════════════════════════


def compute_combined_risk_level(inherent: RiskLevel, control: RiskLevel) -> RiskLevel:
    """Combine inherent and control risk per ISA 315 risk matrix.

    Returns the higher of the two (conservative approach).
    The auditor's own assessment of inherent and control risk determines
    the combined risk — this function simply takes the more conservative
    (higher) of the two inputs.
    """
    if RISK_LEVEL_WEIGHTS[inherent] >= RISK_LEVEL_WEIGHTS[control]:
        return inherent
    return control


# ═══════════════════════════════════════════════════════════════
# Overall risk tier computation
# ═══════════════════════════════════════════════════════════════


def _compute_overall_risk_tier(
    account_assessments: list[AccountRiskAssessment],
) -> Optional[str]:
    """Compute overall risk tier as a SUMMARY of auditor-provided inputs.

    This is NOT an independent assessment — it summarizes the distribution
    of auditor-provided risk levels across all account/assertion pairs.

    Rules:
    - If no assessments, returns None
    - If any combined risk is "high", overall is "high"
    - If >50% of combined risks are "elevated" or above, overall is "elevated"
    - If >50% of combined risks are "moderate" or above, overall is "moderate"
    - Otherwise "low"
    """
    if not account_assessments:
        return None

    combined_levels = [compute_combined_risk_level(a.inherent_risk, a.control_risk) for a in account_assessments]

    total = len(combined_levels)

    # Any high-risk assessment drives overall to high
    if any(level == "high" for level in combined_levels):
        return "high"

    elevated_or_above = sum(1 for level in combined_levels if RISK_LEVEL_WEIGHTS[level] >= 3)
    if elevated_or_above > total / 2:
        return "elevated"

    moderate_or_above = sum(1 for level in combined_levels if RISK_LEVEL_WEIGHTS[level] >= 2)
    if moderate_or_above > total / 2:
        return "moderate"

    return "low"


# ═══════════════════════════════════════════════════════════════
# Main builder
# ═══════════════════════════════════════════════════════════════


def build_composite_risk_profile(
    account_assessments: list[AccountRiskAssessment],
    tb_diagnostic_score: Optional[int] = None,
    tb_diagnostic_tier: Optional[str] = None,
    testing_scores: Optional[dict[str, float]] = None,
    going_concern_indicators_triggered: int = 0,
) -> CompositeRiskProfile:
    """Build a composite risk profile from auditor inputs + automated data.

    This function structures auditor-provided risk assessments alongside
    automated diagnostic data. It does NOT algorithmically override auditor
    judgments — the overall_risk_tier is derived solely from auditor inputs.

    Args:
        account_assessments: Auditor-provided risk assessments per account/assertion
        tb_diagnostic_score: Optional TB diagnostic anomaly density score (0-100)
        tb_diagnostic_tier: Optional TB diagnostic tier label
        testing_scores: Optional dict of tool_name -> composite score
        going_concern_indicators_triggered: Count of triggered going concern indicators

    Returns:
        Fully populated CompositeRiskProfile
    """
    # Count high-risk and fraud-risk accounts
    high_risk_count = 0
    fraud_risk_count = 0
    risk_distribution: dict[str, int] = {
        "low": 0,
        "moderate": 0,
        "elevated": 0,
        "high": 0,
    }

    for assessment in account_assessments:
        combined = compute_combined_risk_level(assessment.inherent_risk, assessment.control_risk)
        risk_distribution[combined] += 1

        if combined == "high":
            high_risk_count += 1

        if assessment.fraud_risk_factor:
            fraud_risk_count += 1

    overall_tier = _compute_overall_risk_tier(account_assessments)

    return CompositeRiskProfile(
        account_assessments=account_assessments,
        tb_diagnostic_score=tb_diagnostic_score,
        tb_diagnostic_tier=tb_diagnostic_tier,
        testing_scores=testing_scores or {},
        going_concern_indicators_triggered=going_concern_indicators_triggered,
        high_risk_accounts=high_risk_count,
        fraud_risk_accounts=fraud_risk_count,
        total_assessments=len(account_assessments),
        risk_distribution=risk_distribution,
        overall_risk_tier=overall_tier,
    )
