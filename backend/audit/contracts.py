"""Typed contracts between audit pipeline stages.

Each stage in the audit pipeline produces a strongly typed result object that
the next stage consumes. Using dataclasses ensures that inter-stage interfaces
are explicit, immutable descriptions of data shape rather than opaque dicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from column_detector import ColumnDetectionResult


@dataclass
class IngestionResult:
    """Output of the ingestion stage: a normalized DataFrame plus metadata.

    Attributes:
        df: Normalized trial-balance DataFrame with stripped column names
            and numeric debit/credit columns.
        filename: Original upload filename (for logging/error messages).
        row_count: Total rows ingested (across all chunks).
        column_detection: Column mapping metadata discovered during parsing.
        account_col: Resolved account-name column header.
        debit_col: Resolved debit column header.
        credit_col: Resolved credit column header.
    """

    df: pd.DataFrame
    filename: str
    row_count: int
    column_detection: ColumnDetectionResult | None = None
    account_col: str | None = None
    debit_col: str | None = None
    credit_col: str | None = None


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
class AnomalyFinding:
    """A single anomaly finding dictionary wrapper.

    The underlying dict matches the existing API contract shape. This wrapper
    is provided for forward-compatible typing without breaking consumers that
    expect plain dicts.
    """

    data: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


@dataclass
class AnomalyResult:
    """Output of the anomaly detection stage.

    Attributes:
        findings: Merged list of all anomaly findings (abnormal balances,
            suspense, concentration, rounding, related-party, intercompany,
            equity signals, revenue/expense concentration).
        material_count: Number of findings with materiality == 'material'.
        immaterial_count: Number of findings below materiality.
        informational_count: Number of informational-tier findings.
    """

    findings: list[dict[str, Any]]
    material_count: int = 0
    immaterial_count: int = 0
    informational_count: int = 0


@dataclass
class RiskSummary:
    """Aggregate risk scoring and tier assignment.

    Attributes:
        total_anomalies: Total number of anomaly findings.
        high_severity: Count of high-severity findings.
        medium_severity: Count of medium-severity findings.
        low_severity: Count of low-severity findings.
        informational_count: Count of informational findings.
        anomaly_types: Breakdown by anomaly type string.
        risk_score: Computed numeric risk score (0-100).
        risk_tier: Human label derived from risk_score.
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
