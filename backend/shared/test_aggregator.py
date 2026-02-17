"""
Shared Test Aggregator — Sprint 152

Parameterized composite score calculation used by all testing engines.
Replaces ~70-80 lines of near-identical scoring logic in each engine.

Supports two normalization modes:
- "max_possible": score = (weighted_flag_rates / max_severity_weights) * 100
  Used by JE, AP, Revenue, FA, Inventory, AR Aging
- "total_entries": score = (total_severity_weighted_flags / total_entries) * 100
  Used by Payroll

NOT used by: Three-Way Match (no composite score function)
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

from shared.testing_enums import SEVERITY_WEIGHTS, RiskTier, score_to_risk_tier

# String-keyed severity weights for engines using string severities (Payroll)
_SEVERITY_WEIGHTS_STR: dict[str, float] = {s.value: w for s, w in SEVERITY_WEIGHTS.items()}


def _get_weight(severity_str: str) -> float:
    """Look up severity weight from string value."""
    return _SEVERITY_WEIGHTS_STR.get(severity_str, 1.0)


@dataclass
class CompositeScoreResult:
    """Result of composite score calculation."""
    score: float  # 0-100
    risk_tier: RiskTier
    tests_run: int
    total_entries: int
    total_flagged: int
    flag_rate: float
    flags_by_severity: dict[str, int] = field(default_factory=dict)
    top_findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "risk_tier": self.risk_tier.value,
            "tests_run": self.tests_run,
            "total_entries": self.total_entries,
            "total_flagged": self.total_flagged,
            "flag_rate": round(self.flag_rate, 4),
            "flags_by_severity": self.flags_by_severity,
            "top_findings": self.top_findings,
        }


def calculate_composite_score(
    test_results: list[Any],
    total_entries: int,
    *,
    multi_flag_threshold: int = 3,
    row_accessor: Optional[Callable] = None,
    severity_accessor: Optional[Callable] = None,
    test_severity_accessor: Optional[Callable] = None,
    normalization: str = "max_possible",
    top_n: int = 5,
    entity_label: str = "entries",
) -> CompositeScoreResult:
    """Calculate composite risk score from test results.

    Algorithm (canonical — used identically by 7 engines):
    1. Collect flagged entries, count by severity
    2. Track row→test count mapping for multi-flag detection
    3. Weighted base score via chosen normalization
    4. Multi-flag multiplier: 1.0 + (multi_flag_ratio * 0.25)
    5. Score capped at 100.0
    6. Top findings: sorted by flag_rate, "{test}: N entities flagged (X%)"

    Args:
        test_results: List of test result objects (domain-specific)
        total_entries: Total number of entries tested
        multi_flag_threshold: Min tests per entry for multi-flag multiplier (default 3)
        row_accessor: Extract row identifier from flagged entry. Default: fe.entry.row_number
        severity_accessor: Extract severity string from flagged entry. Default: fe.severity.value
        test_severity_accessor: Extract severity string from test result. Default: tr.severity.value
        normalization: "max_possible" or "total_entries"
        top_n: Max number of top findings to include
        entity_label: Label for entries in top_findings (e.g., "entries", "payments")

    Returns:
        CompositeScoreResult with score, risk tier, flags, and findings
    """
    if row_accessor is None:
        row_accessor = lambda fe: fe.entry.row_number
    if severity_accessor is None:
        severity_accessor = lambda fe: fe.severity.value
    if test_severity_accessor is None:
        test_severity_accessor = lambda tr: tr.severity.value

    if total_entries == 0:
        return CompositeScoreResult(
            score=0.0,
            risk_tier=RiskTier.LOW,
            tests_run=len(test_results),
            total_entries=0,
            total_flagged=0,
            flag_rate=0.0,
        )

    # Collect flagged entry info
    entry_test_counts: dict[int, int] = {}
    all_flagged_rows: set[int] = set()
    flags_by_severity: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for tr in test_results:
        for fe in tr.flagged_entries:
            row = row_accessor(fe)
            entry_test_counts[row] = entry_test_counts.get(row, 0) + 1
            all_flagged_rows.add(row)
            sev_str = severity_accessor(fe)
            flags_by_severity[sev_str] = flags_by_severity.get(sev_str, 0) + 1

    # Base score calculation
    if normalization == "max_possible":
        # Standard: per-test flag_rate * severity weight, normalized by max possible
        weighted_sum = 0.0
        for tr in test_results:
            weight = _get_weight(test_severity_accessor(tr))
            weighted_sum += tr.flag_rate * weight

        max_possible = sum(_get_weight(test_severity_accessor(tr)) for tr in test_results)
        base_score = (weighted_sum / max_possible) * 100 if max_possible > 0 else 0.0
    elif normalization == "total_entries":
        # Payroll: individual flag weights / total entries
        weighted_sum = 0.0
        for tr in test_results:
            for fe in tr.flagged_entries:
                weighted_sum += _get_weight(severity_accessor(fe))
        base_score = (weighted_sum / total_entries) * 100 if total_entries > 0 else 0.0
    else:
        raise ValueError(f"Unknown normalization: {normalization}")

    # Multi-flag multiplier
    multi_flag_count = sum(1 for c in entry_test_counts.values() if c >= multi_flag_threshold)
    multi_flag_ratio = multi_flag_count / max(total_entries, 1)
    multiplier = 1.0 + (multi_flag_ratio * 0.25)

    score = min(base_score * multiplier, 100.0)

    # Top findings (sorted by flag_rate, descending)
    top_findings: list[str] = []
    for tr in sorted(test_results, key=lambda t: t.flag_rate, reverse=True):
        if tr.entries_flagged > 0:
            top_findings.append(
                f"{tr.test_name}: {tr.entries_flagged} {entity_label} flagged ({tr.flag_rate:.1%})"
            )

    total_flagged = len(all_flagged_rows)
    flag_rate = total_flagged / max(total_entries, 1)

    return CompositeScoreResult(
        score=score,
        risk_tier=score_to_risk_tier(score),
        tests_run=len(test_results),
        total_entries=total_entries,
        total_flagged=total_flagged,
        flag_rate=flag_rate,
        flags_by_severity=flags_by_severity,
        top_findings=top_findings[:top_n],
    )
