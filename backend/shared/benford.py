"""
Shared Benford's Law Analysis — Sprint 153

Extracted from je_testing_engine.py and payroll_testing_engine.py.
Provides pure statistical Benford analysis (engine-agnostic).

Engines call analyze_benford() with raw amounts, then use the
BenfordAnalysis result to create domain-specific flagged entries.

NOT used by revenue_testing_engine.py (structurally different:
chi-squared only, no MAD/conformity, different precision).

References:
- Nigrini, M.J. (2012). Benford's Law: Applications for Forensic
  Accounting, Auditing, and Fraud Detection.
- ISA 530: Audit Sampling (Benford's Law as analytical procedure)
"""

from dataclasses import dataclass, field
from typing import Optional
import math


# Benford's Law expected first-digit distribution (Newcomb-Benford)
BENFORD_EXPECTED: dict[int, float] = {
    1: 0.30103,
    2: 0.17609,
    3: 0.12494,
    4: 0.09691,
    5: 0.07918,
    6: 0.06695,
    7: 0.05799,
    8: 0.05115,
    9: 0.04576,
}

# MAD (Mean Absolute Deviation) thresholds per Nigrini (2012)
BENFORD_MAD_CONFORMING = 0.006
BENFORD_MAD_ACCEPTABLE = 0.012
BENFORD_MAD_MARGINALLY_ACCEPTABLE = 0.015
# Above 0.015 = nonconforming


def get_first_digit(value: float) -> Optional[int]:
    """Extract the first significant digit (1-9) from a number.

    Returns None for zero or values with no significant digit.
    """
    if value == 0:
        return None
    abs_val = abs(value)
    s = f"{abs_val:.10f}".lstrip("0").lstrip(".")
    for ch in s:
        if ch.isdigit() and ch != "0":
            return int(ch)
    return None


@dataclass
class BenfordAnalysis:
    """Results of Benford's Law first-digit analysis.

    Pure statistical result — no domain-specific entry types.
    Identical field names and to_dict() output to the former
    je_testing_engine.BenfordResult for backward compatibility.
    """
    passed_prechecks: bool
    precheck_message: Optional[str] = None
    eligible_count: int = 0
    total_count: int = 0
    expected_distribution: dict[int, float] = field(default_factory=dict)
    actual_distribution: dict[int, float] = field(default_factory=dict)
    actual_counts: dict[int, int] = field(default_factory=dict)
    deviation_by_digit: dict[int, float] = field(default_factory=dict)
    mad: float = 0.0
    chi_squared: float = 0.0
    conformity_level: str = ""
    most_deviated_digits: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed_prechecks": self.passed_prechecks,
            "precheck_message": self.precheck_message,
            "eligible_count": self.eligible_count,
            "total_count": self.total_count,
            "expected_distribution": {str(k): round(v, 5) for k, v in self.expected_distribution.items()},
            "actual_distribution": {str(k): round(v, 5) for k, v in self.actual_distribution.items()},
            "actual_counts": {str(k): v for k, v in self.actual_counts.items()},
            "deviation_by_digit": {str(k): round(v, 5) for k, v in self.deviation_by_digit.items()},
            "mad": round(self.mad, 5),
            "chi_squared": round(self.chi_squared, 3),
            "conformity_level": self.conformity_level,
            "most_deviated_digits": self.most_deviated_digits,
        }


def analyze_benford(
    amounts: list[float],
    *,
    total_count: int,
    min_entries: int = 500,
    min_amount: float = 1.0,
    min_magnitude_range: float = 2.0,
) -> BenfordAnalysis:
    """Run Benford's Law first-digit analysis on a list of amounts.

    Args:
        amounts: Pre-filtered list of absolute amounts (>= min_amount).
        total_count: Total entry count (for reporting; may differ from len(amounts)).
        min_entries: Minimum eligible entries required.
        min_amount: Minimum amount threshold (used in precheck message only;
            caller should pre-filter amounts).
        min_magnitude_range: Minimum orders of magnitude range required.

    Returns:
        BenfordAnalysis with statistical results. Does NOT create flagged
        entries — that is the caller's responsibility.
    """
    eligible_count = len(amounts)

    # Pre-check 1: Minimum entry count
    if eligible_count < min_entries:
        return BenfordAnalysis(
            passed_prechecks=False,
            precheck_message=f"Insufficient data: {eligible_count} eligible entries (minimum {min_entries} required).",
            eligible_count=eligible_count,
            total_count=total_count,
        )

    # Pre-check 2: Magnitude range
    min_amt = min(amounts)
    max_amt = max(amounts)
    if min_amt > 0 and max_amt > 0:
        magnitude_range = math.log10(max_amt) - math.log10(min_amt)
    else:
        magnitude_range = 0.0

    if magnitude_range < min_magnitude_range:
        return BenfordAnalysis(
            passed_prechecks=False,
            precheck_message=f"Insufficient magnitude range: {magnitude_range:.1f} orders (minimum {min_magnitude_range} required).",
            eligible_count=eligible_count,
            total_count=total_count,
        )

    # Calculate first-digit distribution
    digit_counts: dict[int, int] = {d: 0 for d in range(1, 10)}
    for amt in amounts:
        digit = get_first_digit(amt)
        if digit and 1 <= digit <= 9:
            digit_counts[digit] += 1

    counted_total = sum(digit_counts.values())
    if counted_total == 0:
        return BenfordAnalysis(
            passed_prechecks=False,
            precheck_message="No valid first digits found.",
            eligible_count=eligible_count,
            total_count=total_count,
        )

    # Actual distribution
    actual_dist: dict[int, float] = {
        d: digit_counts[d] / counted_total for d in range(1, 10)
    }

    # Deviation by digit
    deviation: dict[int, float] = {
        d: actual_dist[d] - BENFORD_EXPECTED[d] for d in range(1, 10)
    }

    # MAD
    mad = math.fsum(abs(deviation[d]) for d in range(1, 10)) / 9

    # Chi-squared
    chi_sq = sum(
        ((digit_counts[d] - BENFORD_EXPECTED[d] * counted_total) ** 2)
        / (BENFORD_EXPECTED[d] * counted_total)
        for d in range(1, 10)
    )

    # Conformity level
    if mad < BENFORD_MAD_CONFORMING:
        conformity = "conforming"
    elif mad < BENFORD_MAD_ACCEPTABLE:
        conformity = "acceptable"
    elif mad < BENFORD_MAD_MARGINALLY_ACCEPTABLE:
        conformity = "marginally_acceptable"
    else:
        conformity = "nonconforming"

    # Most deviated digits (top 3 with deviation > MAD)
    sorted_deviations = sorted(
        range(1, 10), key=lambda d: abs(deviation[d]), reverse=True
    )
    most_deviated = [d for d in sorted_deviations[:3] if abs(deviation[d]) > mad]

    return BenfordAnalysis(
        passed_prechecks=True,
        eligible_count=eligible_count,
        total_count=total_count,
        expected_distribution=dict(BENFORD_EXPECTED),
        actual_distribution=actual_dist,
        actual_counts=digit_counts,
        deviation_by_digit=deviation,
        mad=mad,
        chi_squared=chi_sq,
        conformity_level=conformity,
        most_deviated_digits=most_deviated,
    )
