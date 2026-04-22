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


# ---------------------------------------------------------------------------
# Tier taxonomy normalization (DASH-01 remediation, 2026-04-20)
# ---------------------------------------------------------------------------
#
# Historical tension: different report producers emit different tier
# vocabularies.  Tool-level ``MatchRiskLevel`` (three-way match) uses a
# 3-tier scale (low / medium / high) while the canonical dashboard scale
# ``RiskTier`` is 4-tier (low / moderate / elevated / high).  The engagement
# dashboard was silently mis-aligning — ``medium`` never matched any of the
# 4-tier branches, so three-way-match findings with ``medium`` tier never
# surfaced in the priority action list.
#
# ``normalize_risk_tier`` is the single consumer-side translation point.
# It should be called by any aggregator that ingests tier strings from
# heterogeneous report producers.

_CANONICAL_TIERS: frozenset[str] = frozenset({"low", "moderate", "elevated", "high"})

# Aliases from other producer taxonomies → canonical dashboard tier.
# "medium" is the three-way-match aliasing bug; other entries cover legacy
# spellings that have appeared in older report fixtures.
_TIER_ALIASES: dict[str, str] = {
    "medium": "moderate",
    "med": "moderate",
    "moderate risk": "moderate",
    "elevated risk": "elevated",
    "high risk": "high",
    "low risk": "low",
    "critical": "high",
    "none": "low",
    "minimal": "low",
}


def normalize_risk_tier(tier: object, *, default: str = "low") -> str:
    """Normalize a tier string into the canonical 4-tier dashboard taxonomy.

    Accepts lists/tuples by taking the first element, strings case-insensitively,
    and unknown values fall back to ``default`` (low, by default).  This keeps
    the dashboard defensive: a new producer introducing an unrecognised tier
    cannot silently widen the ``elevated`` priority list.
    """
    if isinstance(tier, (list, tuple)):
        tier = tier[0] if tier else default
    if tier is None:
        return default
    t = str(tier).strip().lower()
    if t in _CANONICAL_TIERS:
        return t
    if t in _TIER_ALIASES:
        return _TIER_ALIASES[t]
    return default


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
