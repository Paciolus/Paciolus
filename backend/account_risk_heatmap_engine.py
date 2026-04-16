"""
Account Risk Signal Heatmap (Sprint 627).

Aggregates per-account audit signals across multiple diagnostic engines into a
single triage-density view. Auditors currently open five separate views to see
all flags against a given account; this engine collapses them into one ranked
heatmap so the "top 10% by signal density" is one query away.

Design:
- Pure aggregation. Accepts a list of `RiskSignal` records, each tagged with
  account_number / account_name / source / severity / weighted score.
- Adapter functions (build_signals_from_*) translate concrete engine outputs
  into `RiskSignal`s. Each adapter is independently testable and the engine
  can run with any subset of available signals.
- Output is sorted by composite weighted score, then bucketed:
  Top 10% = High priority, next 20% = Moderate, remainder = Low.
- Zero-storage compliant — operates on in-memory engine outputs only.
"""

from __future__ import annotations

import csv
import io
import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any

# =============================================================================
# Constants
# =============================================================================

SEVERITY_WEIGHTS: dict[str, float] = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}

# Source tags (string-typed for flexibility — engines may add their own)
SOURCE_AUDIT_ANOMALY = "audit_anomaly"
SOURCE_CLASSIFICATION = "classification_validator"
SOURCE_CUTOFF = "cutoff_risk"
SOURCE_ACCRUAL = "accrual_completeness"
SOURCE_COMPOSITE_RISK = "composite_risk"
SOURCE_LEASE = "lease_indicator"
SOURCE_GOING_CONCERN = "going_concern"

# Priority tier thresholds (percentile cutoffs)
HIGH_TIER_PERCENTILE = 0.10  # Top 10%
MODERATE_TIER_PERCENTILE = 0.30  # Next 20% (10–30)


# =============================================================================
# Dataclasses
# =============================================================================


@dataclass
class RiskSignal:
    """A single signal flagged against an account by an upstream engine."""

    account_number: str
    account_name: str
    source: str  # one of the SOURCE_* tags
    severity: str  # "high" | "medium" | "low"
    issue: str  # short description
    materiality: Decimal = Decimal("0")  # materiality of the flagged amount
    confidence: float = 1.0  # 0.0–1.0 — multiplier on the weighted score

    def weighted_score(self) -> float:
        """Composite contribution of this signal to its account's heatmap row."""
        sev_weight = SEVERITY_WEIGHTS.get(self.severity, 1.0)
        mat_log = math.log10(float(self.materiality) + 10.0)  # +10 to keep small amounts contributing
        return sev_weight * mat_log * self.confidence


@dataclass
class AccountHeatmapRow:
    account_number: str
    account_name: str
    signal_count: int = 0
    weighted_score: float = 0.0
    sources: list[str] = field(default_factory=list)
    severities: dict[str, int] = field(default_factory=dict)  # high/medium/low counts
    issues: list[str] = field(default_factory=list)
    total_materiality: Decimal = Decimal("0")
    priority_tier: str = "low"  # "high" | "moderate" | "low"
    rank: int = 0  # 1-indexed — 1 = highest score

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["weighted_score"] = round(self.weighted_score, 3)
        d["total_materiality"] = str(self.total_materiality)
        return d


@dataclass
class AccountRiskHeatmapResult:
    rows: list[AccountHeatmapRow]
    total_accounts_with_signals: int
    high_priority_count: int
    moderate_priority_count: int
    low_priority_count: int
    total_signals: int
    sources_active: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": [r.to_dict() for r in self.rows],
            "total_accounts_with_signals": self.total_accounts_with_signals,
            "high_priority_count": self.high_priority_count,
            "moderate_priority_count": self.moderate_priority_count,
            "low_priority_count": self.low_priority_count,
            "total_signals": self.total_signals,
            "sources_active": self.sources_active,
        }


# =============================================================================
# Aggregation
# =============================================================================


def compute_account_heatmap(signals: Iterable[RiskSignal]) -> AccountRiskHeatmapResult:
    """Aggregate signals into a per-account heatmap, ranked and bucketed.

    Bucketing thresholds:
      - High priority: top 10% by weighted_score
      - Moderate: next 20% (10th–30th percentile)
      - Low: remainder

    A single signal is enough to surface an account, but a single low-severity
    signal will not on its own promote an account to High unless it is also
    materially significant relative to peers.
    """
    by_account: dict[str, AccountHeatmapRow] = {}
    sources_active: set[str] = set()
    total_signals = 0

    for signal in signals:
        total_signals += 1
        sources_active.add(signal.source)
        key = signal.account_number or signal.account_name
        if key not in by_account:
            by_account[key] = AccountHeatmapRow(
                account_number=signal.account_number,
                account_name=signal.account_name,
            )
        row = by_account[key]
        row.signal_count += 1
        row.weighted_score += signal.weighted_score()
        if signal.source not in row.sources:
            row.sources.append(signal.source)
        row.severities[signal.severity] = row.severities.get(signal.severity, 0) + 1
        if signal.issue not in row.issues:
            row.issues.append(signal.issue)
        row.total_materiality += signal.materiality

    # Sort by weighted score descending, then by signal count descending
    rows = sorted(
        by_account.values(),
        key=lambda r: (r.weighted_score, r.signal_count),
        reverse=True,
    )

    # Assign ranks and priority tiers
    n = len(rows)
    high_cut = max(1, math.ceil(n * HIGH_TIER_PERCENTILE)) if n else 0
    moderate_cut = max(high_cut, math.ceil(n * MODERATE_TIER_PERCENTILE)) if n else 0

    high_count = 0
    moderate_count = 0
    low_count = 0
    for idx, row in enumerate(rows, start=1):
        row.rank = idx
        if idx <= high_cut:
            row.priority_tier = "high"
            high_count += 1
        elif idx <= moderate_cut:
            row.priority_tier = "moderate"
            moderate_count += 1
        else:
            row.priority_tier = "low"
            low_count += 1

    return AccountRiskHeatmapResult(
        rows=rows,
        total_accounts_with_signals=len(rows),
        high_priority_count=high_count,
        moderate_priority_count=moderate_count,
        low_priority_count=low_count,
        total_signals=total_signals,
        sources_active=sorted(sources_active),
    )


# =============================================================================
# Adapters — translate concrete engine outputs into RiskSignals
# =============================================================================


def build_signals_from_audit_anomalies(
    abnormal_balances: Iterable[dict[str, Any]],
) -> list[RiskSignal]:
    """Adapter for the unified `abnormal_balances` list emitted by
    StreamingAuditor (audit/audit_engine).

    Each entry is expected to have keys: account, type, issue, amount,
    materiality, confidence, anomaly_type, severity.
    """
    signals: list[RiskSignal] = []
    for item in abnormal_balances:
        materiality_raw = item.get("amount") or item.get("materiality") or 0
        try:
            materiality = Decimal(str(materiality_raw))
        except Exception:
            materiality = Decimal("0")
        signals.append(
            RiskSignal(
                account_number=str(item.get("account_number") or item.get("account") or ""),
                account_name=str(item.get("account") or item.get("account_name") or ""),
                source=SOURCE_AUDIT_ANOMALY,
                severity=str(item.get("severity") or "medium").lower(),
                issue=str(item.get("issue") or item.get("anomaly_type") or "Anomaly flagged"),
                materiality=abs(materiality),
                confidence=float(item.get("confidence") or 1.0),
            )
        )
    return signals


def build_signals_from_classification_issues(
    issues: Iterable[Any],
) -> list[RiskSignal]:
    """Adapter for classification_validator.ClassificationIssue entries
    (or their .to_dict() forms). Operates duck-typed on attributes/keys.
    """
    signals: list[RiskSignal] = []
    for issue in issues:
        if isinstance(issue, dict):
            data = issue
        else:
            data = {
                "account_number": getattr(issue, "account_number", ""),
                "account_name": getattr(issue, "account_name", ""),
                "issue_type": getattr(issue, "issue_type", ""),
                "description": getattr(issue, "description", ""),
                "severity": getattr(issue, "severity", "low"),
                "confidence": getattr(issue, "confidence", 0.8),
            }
        # ClassificationIssue values are often enum-typed — coerce
        issue_type = data.get("issue_type")
        issue_label = issue_type.value if hasattr(issue_type, "value") else str(issue_type or "Classification issue")
        signals.append(
            RiskSignal(
                account_number=str(data.get("account_number", "")),
                account_name=str(data.get("account_name", "")),
                source=SOURCE_CLASSIFICATION,
                severity=str(data.get("severity", "low")).lower(),
                issue=str(data.get("description") or issue_label),
                materiality=Decimal("0"),
                confidence=float(data.get("confidence", 0.8)),
            )
        )
    return signals


def build_signals_from_cutoff_flags(
    flags: Iterable[Any],
) -> list[RiskSignal]:
    """Adapter for cutoff_risk_engine.CutoffFlag entries."""
    signals: list[RiskSignal] = []
    for flag in flags:
        if isinstance(flag, dict):
            data = flag
        else:
            data = {
                "account_number": getattr(flag, "account_number", ""),
                "account_name": getattr(flag, "account_name", ""),
                "issue": getattr(flag, "issue", "Cutoff risk"),
                "severity": getattr(flag, "severity", "medium"),
                "amount": getattr(flag, "amount", 0),
                "confidence": getattr(flag, "confidence", 0.7),
            }
        try:
            amount = Decimal(str(data.get("amount") or 0))
        except Exception:
            amount = Decimal("0")
        signals.append(
            RiskSignal(
                account_number=str(data.get("account_number", "")),
                account_name=str(data.get("account_name", "")),
                source=SOURCE_CUTOFF,
                severity=str(data.get("severity", "medium")).lower(),
                issue=str(data.get("issue", "Cutoff risk")),
                materiality=abs(amount),
                confidence=float(data.get("confidence", 0.7)),
            )
        )
    return signals


def build_signals_from_accrual_findings(
    findings: Iterable[Any],
) -> list[RiskSignal]:
    """Adapter for accrual_completeness_engine.Finding entries."""
    signals: list[RiskSignal] = []
    for finding in findings:
        if isinstance(finding, dict):
            data = finding
        else:
            data = {
                "account_number": getattr(finding, "account_number", ""),
                "account_name": getattr(finding, "account_name", "Accrual"),
                "title": getattr(finding, "title", "Accrual finding"),
                "severity": getattr(finding, "severity", "medium"),
                "amount": getattr(finding, "amount", 0),
            }
        try:
            amount = Decimal(str(data.get("amount") or 0))
        except Exception:
            amount = Decimal("0")
        signals.append(
            RiskSignal(
                account_number=str(data.get("account_number", "")),
                account_name=str(data.get("account_name", "Accrual")),
                source=SOURCE_ACCRUAL,
                severity=str(data.get("severity", "medium")).lower(),
                issue=str(data.get("title") or data.get("issue") or "Accrual finding"),
                materiality=abs(amount),
                confidence=0.85,
            )
        )
    return signals


def build_signals_from_composite_risk(
    profile: Any,
) -> list[RiskSignal]:
    """Adapter for composite_risk_engine.CompositeRiskProfile.

    Each AccountRiskAssessment yields a signal with severity == combined risk
    level. Only accounts where combined >= 'moderate' contribute (low risk
    accounts do not add noise to the heatmap).
    """
    if profile is None:
        return []
    if isinstance(profile, dict):
        assessments = profile.get("account_assessments", [])
    else:
        assessments = getattr(profile, "account_assessments", [])
    signals: list[RiskSignal] = []
    for assessment in assessments:
        if isinstance(assessment, dict):
            data = assessment
        else:
            data = assessment.to_dict() if hasattr(assessment, "to_dict") else {}
        combined = data.get("combined_risk", "low")
        if combined == "low":
            continue
        # Map composite risk level → severity
        sev_map = {"high": "high", "elevated": "high", "moderate": "medium"}
        severity = sev_map.get(str(combined), "medium")
        signals.append(
            RiskSignal(
                account_number="",
                account_name=str(data.get("account_name", "")),
                source=SOURCE_COMPOSITE_RISK,
                severity=severity,
                issue=f"ISA 315 combined risk: {combined} ({data.get('assertion', 'unknown assertion')})",
                materiality=Decimal("0"),
                confidence=1.0,
            )
        )
    return signals


# =============================================================================
# CSV export
# =============================================================================


def heatmap_to_csv(result: AccountRiskHeatmapResult) -> str:
    """Render the heatmap as a CSV string for export."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Rank",
            "Priority",
            "Account Number",
            "Account Name",
            "Signal Count",
            "Weighted Score",
            "High",
            "Medium",
            "Low",
            "Total Materiality",
            "Sources",
            "Issues",
        ]
    )
    for row in result.rows:
        writer.writerow(
            [
                row.rank,
                row.priority_tier,
                row.account_number,
                row.account_name,
                row.signal_count,
                f"{row.weighted_score:.3f}",
                row.severities.get("high", 0),
                row.severities.get("medium", 0),
                row.severities.get("low", 0),
                str(row.total_materiality),
                "; ".join(row.sources),
                " | ".join(row.issues[:5]),  # cap to first 5 to keep CSV readable
            ]
        )
    return buffer.getvalue()
