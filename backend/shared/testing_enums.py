"""
Shared Testing Enums — Sprint 90

Extracted from JE/AP/Payroll testing engines.
All three engines had identical enum definitions; this is the single source of truth.

Used by:
- je_testing_engine.py
- ap_testing_engine.py
- payroll_testing_engine.py
- three_way_match_engine.py (Sprint 91+)
"""

from enum import Enum


class RiskTier(str, Enum):
    """Composite risk tier for testing results (4-tier scale)."""

    LOW = "low"  # Score 0-10
    MODERATE = "moderate"  # Score 11-25
    ELEVATED = "elevated"  # Score 26-50
    HIGH = "high"  # Score 51-100


class TestTier(str, Enum):
    """Test classification tier."""
    __test__ = False  # Prevent pytest collection warning

    STRUCTURAL = "structural"  # Tier 1: Basic structural checks
    STATISTICAL = "statistical"  # Tier 2: Statistical analysis
    ADVANCED = "advanced"  # Tier 3: Advanced patterns / fraud indicators
    CONTRACT = "contract"  # Tier 4: Standards-compliance checks (ASC 606 / IFRS 15)


class Severity(str, Enum):
    """Severity of a flagged entry."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


SEVERITY_WEIGHTS: dict[Severity, float] = {
    Severity.HIGH: 3.0,
    Severity.MEDIUM: 2.0,
    Severity.LOW: 1.0,
}


def score_to_risk_tier(score: float) -> RiskTier:
    """Map a composite score (0-100) to a risk tier.

    4-tier scale: 0–10 Low | 11–25 Moderate | 26–50 Elevated | 51–100 High Risk.
    Used by all testing engines for consistent tier assignment.
    """
    if score <= 10:
        return RiskTier.LOW
    elif score <= 25:
        return RiskTier.MODERATE
    elif score <= 50:
        return RiskTier.ELEVATED
    else:
        return RiskTier.HIGH


def zscore_to_severity(z: float) -> Severity:
    """Map a z-score to severity level.

    Thresholds are intentionally conservative to reduce false positives in
    audit diagnostic contexts where over-flagging erodes practitioner trust.

    - z > 5: HIGH  (~0.00003% of normally distributed observations)
    - z > 4: MEDIUM (~0.003% of normally distributed observations)
    - otherwise: LOW

    These thresholds are higher than the conventional z > 3 "unusual" cutoff
    used in general statistics. The elevated floor accounts for the non-normal
    distributions typical in financial data (heavy tails, zero-inflation).
    For small populations (< 1,000 items), practitioners should consider that
    these thresholds may suppress audit-relevant outliers and supplement
    z-score analysis with manual review of the top N items by absolute value.

    Source: Adapted from Nigrini (2012), Benford's Law, ch. 7 —
    z-score thresholds for financial audit populations.
    """
    if z > 5:
        return Severity.HIGH
    elif z > 4:
        return Severity.MEDIUM
    else:
        return Severity.LOW
