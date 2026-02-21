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
    """Composite risk tier for testing results."""
    LOW = "low"                  # Score 0-9
    ELEVATED = "elevated"        # Score 10-24
    MODERATE = "moderate"        # Score 25-49
    HIGH = "high"                # Score 50-74
    CRITICAL = "critical"        # Score 75+


class TestTier(str, Enum):
    """Test classification tier."""
    STRUCTURAL = "structural"    # Tier 1: Basic structural checks
    STATISTICAL = "statistical"  # Tier 2: Statistical analysis
    ADVANCED = "advanced"        # Tier 3: Advanced patterns / fraud indicators
    CONTRACT = "contract"        # Tier 4: Standards-compliance checks (ASC 606 / IFRS 15)


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

    Used by all testing engines for consistent tier assignment.
    """
    if score < 10:
        return RiskTier.LOW
    elif score < 25:
        return RiskTier.ELEVATED
    elif score < 50:
        return RiskTier.MODERATE
    elif score < 75:
        return RiskTier.HIGH
    else:
        return RiskTier.CRITICAL


def zscore_to_severity(z: float) -> Severity:
    """Map a z-score to severity level.

    Standard thresholds used across testing engines:
    - z > 5: HIGH
    - z > 4: MEDIUM
    - otherwise: LOW
    """
    if z > 5:
        return Severity.HIGH
    elif z > 4:
        return Severity.MEDIUM
    else:
        return Severity.LOW
