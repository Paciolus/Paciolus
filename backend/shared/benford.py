"""
Shared Benford's Law Analysis — Sprint 153

Extracted from je_testing_engine.py and payroll_testing_engine.py.
Provides pure statistical Benford analysis (engine-agnostic).

Engines call analyze_benford() with raw amounts, then use the
BenfordAnalysis result to create domain-specific flagged entries.

Sprint 628 extension: `digit_position` parameter selects first-digit (default,
1–9), second-digit (0–9), or first-two-digit (10–99) analysis. Second-digit
catches round-number manipulation invisible to first-digit tests.
First-two-digit gives finer-grained detection at the cost of needing a much
larger sample.

NOT used by revenue_testing_engine.py (structurally different:
chi-squared only, no MAD/conformity, different precision).

References:
- Nigrini, M.J. (2012). Benford's Law: Applications for Forensic
  Accounting, Auditing, and Fraud Detection.
- ISA 520: Analytical Procedures (Benford's Law as analytical procedure)
"""

import math
from dataclasses import dataclass, field
from typing import Literal, Optional

DigitPosition = Literal["first", "second", "first_two"]

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


def _build_second_digit_expected() -> dict[int, float]:
    """Second-digit distribution: P(d) = sum_{k=1..9} log10(1 + 1/(10k+d))
    for d in 0..9. Each digit value's contribution from each two-digit prefix.
    """
    expected: dict[int, float] = {}
    for d in range(0, 10):
        expected[d] = sum(math.log10(1 + 1 / (10 * k + d)) for k in range(1, 10))
    return expected


def _build_first_two_digit_expected() -> dict[int, float]:
    """First-two-digit distribution: P(d) = log10(1 + 1/d) for d in 10..99."""
    return {d: math.log10(1 + 1 / d) for d in range(10, 100)}


BENFORD_SECOND_DIGIT_EXPECTED: dict[int, float] = _build_second_digit_expected()
BENFORD_FIRST_TWO_EXPECTED: dict[int, float] = _build_first_two_digit_expected()


# MAD (Mean Absolute Deviation) thresholds per Nigrini (2012)
# First digit
BENFORD_MAD_CONFORMING = 0.006
BENFORD_MAD_ACCEPTABLE = 0.012
BENFORD_MAD_MARGINALLY_ACCEPTABLE = 0.015
# Above 0.015 = nonconforming

# Second digit (Nigrini, 2012)
BENFORD_MAD_2ND_CONFORMING = 0.008
BENFORD_MAD_2ND_ACCEPTABLE = 0.010
BENFORD_MAD_2ND_MARGINALLY = 0.012

# First-two-digit (Nigrini, 2012)
BENFORD_MAD_F2D_CONFORMING = 0.0012
BENFORD_MAD_F2D_ACCEPTABLE = 0.0018
BENFORD_MAD_F2D_MARGINALLY = 0.0022


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


def get_second_digit(value: float) -> Optional[int]:
    """Extract the second significant digit (0-9). The first significant
    digit is skipped, then the next digit position is returned.

    Returns None for zero or values with fewer than 2 significant digits.
    """
    if value == 0:
        return None
    abs_val = abs(value)
    s = f"{abs_val:.12f}".lstrip("0").lstrip(".")
    found_first = False
    for ch in s:
        if not ch.isdigit():
            continue
        if not found_first:
            if ch != "0":
                found_first = True
            continue
        return int(ch)
    return None


def get_first_two_digits(value: float) -> Optional[int]:
    """Extract the first two significant digits (10-99) as a single integer."""
    if value == 0:
        return None
    abs_val = abs(value)
    s = f"{abs_val:.12f}".lstrip("0").lstrip(".")
    digits: list[str] = []
    started = False
    for ch in s:
        if not ch.isdigit():
            continue
        if not started and ch == "0":
            continue
        started = True
        digits.append(ch)
        if len(digits) == 2:
            break
    if len(digits) < 2:
        return None
    value_int = int("".join(digits))
    if not (10 <= value_int <= 99):
        return None
    return value_int


@dataclass
class BenfordAnalysis:
    """Results of Benford's Law digit analysis.

    Pure statistical result — no domain-specific entry types.
    Field names preserved for backward compatibility with first-digit callers.
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
    digit_position: DigitPosition = "first"

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
            "digit_position": self.digit_position,
        }


def _digit_extractor(position: DigitPosition):
    """Return the (extractor function, expected distribution dict, valid digit
    range) for the requested digit position.
    """
    if position == "first":
        return get_first_digit, BENFORD_EXPECTED, range(1, 10)
    if position == "second":
        return get_second_digit, BENFORD_SECOND_DIGIT_EXPECTED, range(0, 10)
    if position == "first_two":
        return get_first_two_digits, BENFORD_FIRST_TWO_EXPECTED, range(10, 100)
    raise ValueError(f"Unsupported digit_position: {position}")


def _conformity_level(mad: float, position: DigitPosition) -> str:
    """Map MAD to conformity tier using position-specific Nigrini thresholds."""
    if position == "first":
        if mad < BENFORD_MAD_CONFORMING:
            return "conforming"
        if mad < BENFORD_MAD_ACCEPTABLE:
            return "acceptable"
        if mad < BENFORD_MAD_MARGINALLY_ACCEPTABLE:
            return "marginally_acceptable"
        return "nonconforming"
    if position == "second":
        if mad < BENFORD_MAD_2ND_CONFORMING:
            return "conforming"
        if mad < BENFORD_MAD_2ND_ACCEPTABLE:
            return "acceptable"
        if mad < BENFORD_MAD_2ND_MARGINALLY:
            return "marginally_acceptable"
        return "nonconforming"
    # first_two
    if mad < BENFORD_MAD_F2D_CONFORMING:
        return "conforming"
    if mad < BENFORD_MAD_F2D_ACCEPTABLE:
        return "acceptable"
    if mad < BENFORD_MAD_F2D_MARGINALLY:
        return "marginally_acceptable"
    return "nonconforming"


def analyze_benford(
    amounts: list[float],
    *,
    total_count: int,
    min_entries: int = 500,
    min_amount: float = 1.0,
    min_magnitude_range: float = 2.0,
    digit_position: DigitPosition = "first",
) -> BenfordAnalysis:
    """Run Benford's Law digit analysis on a list of amounts.

    Args:
        amounts: Pre-filtered list of absolute amounts (>= min_amount).
        total_count: Total entry count (for reporting; may differ from len(amounts)).
        min_entries: Minimum eligible entries required.
        min_amount: Minimum amount threshold (used in precheck message only;
            caller should pre-filter amounts).
        min_magnitude_range: Minimum orders of magnitude range required.
        digit_position: "first" (default, 1–9), "second" (0–9), or
            "first_two" (10–99). First-two-digit needs ≥1000 entries to be
            statistically meaningful — the caller should raise `min_entries`
            accordingly.

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
            digit_position=digit_position,
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
            digit_position=digit_position,
        )

    extractor, expected_dist, digit_range = _digit_extractor(digit_position)

    # Calculate digit distribution
    digit_counts: dict[int, int] = {d: 0 for d in digit_range}
    for amt in amounts:
        digit = extractor(amt)
        if digit is not None and digit in digit_counts:
            digit_counts[digit] += 1

    counted_total = sum(digit_counts.values())
    if counted_total == 0:
        return BenfordAnalysis(
            passed_prechecks=False,
            precheck_message=f"No valid {digit_position}-digit values found.",
            eligible_count=eligible_count,
            total_count=total_count,
            digit_position=digit_position,
        )

    # Actual distribution
    actual_dist: dict[int, float] = {d: digit_counts[d] / counted_total for d in digit_range}

    # Deviation by digit
    deviation: dict[int, float] = {d: actual_dist[d] - expected_dist[d] for d in digit_range}

    # MAD
    n_buckets = len(digit_range)
    mad = math.fsum(abs(deviation[d]) for d in digit_range) / n_buckets

    # Chi-squared (skip buckets with expected_count == 0 to avoid div-by-zero
    # — only happens if a caller passes a malformed expected dict)
    chi_sq = 0.0
    for d in digit_range:
        expected_count = expected_dist[d] * counted_total
        if expected_count > 0:
            chi_sq += ((digit_counts[d] - expected_count) ** 2) / expected_count

    conformity = _conformity_level(mad, digit_position)

    # Most deviated digits (top 3 with deviation >= MAD)
    sorted_deviations = sorted(digit_range, key=lambda d: abs(deviation[d]), reverse=True)
    most_deviated = [d for d in sorted_deviations[:3] if abs(deviation[d]) >= mad]

    return BenfordAnalysis(
        passed_prechecks=True,
        eligible_count=eligible_count,
        total_count=total_count,
        expected_distribution=dict(expected_dist),
        actual_distribution=actual_dist,
        actual_counts=digit_counts,
        deviation_by_digit=deviation,
        mad=mad,
        chi_squared=chi_sq,
        conformity_level=conformity,
        most_deviated_digits=most_deviated,
        digit_position=digit_position,
    )
