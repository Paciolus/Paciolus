"""Typed contracts between audit pipeline stages.

Each stage in the audit pipeline produces a strongly typed result object that
the next stage consumes. Using dataclasses ensures that inter-stage interfaces
are explicit, immutable descriptions of data shape rather than opaque dicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClassificationResult:
    """Output of the classification stage.

    Maps every account key to its resolved category and tracks any
    CSV-provided type/subtype information that was used.

    Attributes:
        account_map: Mapping of account key -> category value string.
        account_balances: Per-account debit/credit aggregation dict.
        display_names: account_key -> human display name.
        provided_account_types: Raw CSV account-type values keyed by account.
        provided_account_subtypes: Raw CSV subtype values keyed by account.
        classification_stats: Confidence bucket counts (high/medium/low/unknown).
    """

    account_map: dict[str, str]
    account_balances: dict[str, dict[str, float]]
    display_names: dict[str, str] = field(default_factory=dict)
    provided_account_types: dict[str, str] = field(default_factory=dict)
    provided_account_subtypes: dict[str, str] = field(default_factory=dict)
    classification_stats: dict[str, int] = field(default_factory=dict)


@dataclass
class RiskSummary:
    """Aggregate diagnostic scoring and tier assignment.

    Attributes:
        total_anomalies: Total number of anomaly findings.
        high_severity: Count of high-severity findings.
        medium_severity: Count of medium-severity findings.
        low_severity: Count of low-severity findings.
        informational_count: Count of informational findings.
        anomaly_types: Breakdown by anomaly type string.
        risk_score: Computed numeric diagnostic score (0-100).
        risk_tier: Human label derived from diagnostic score.
        risk_factors: List of (factor_name, points) tuples.
        coverage_pct: Percentage of TB value covered by material findings.
    """

    total_anomalies: int = 0
    high_severity: int = 0
    medium_severity: int = 0
    low_severity: int = 0
    informational_count: int = 0
    anomaly_types: dict[str, int] = field(default_factory=dict)
    risk_score: float = 0.0
    risk_tier: str = "low"
    risk_factors: list[tuple[str, float]] = field(default_factory=list)
    coverage_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the dict shape expected by the existing API."""
        return {
            "total_anomalies": self.total_anomalies,
            "high_severity": self.high_severity,
            "medium_severity": self.medium_severity,
            "low_severity": self.low_severity,
            "informational_count": self.informational_count,
            "anomaly_types": dict(self.anomaly_types),
            "risk_score": self.risk_score,
            "risk_tier": self.risk_tier,
            "risk_factors": [(name, pts) for name, pts in self.risk_factors],
            "coverage_pct": self.coverage_pct,
        }
