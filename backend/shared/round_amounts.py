"""
Shared Round Amount Detection — Sprint 90

Extracted from JE/AP/Payroll testing engines.
Common 4-tier pattern for detecting suspiciously round dollar amounts.

Used by:
- je_testing_engine.py (T4: Round Dollar Amounts)
- ap_testing_engine.py (AP-T4: Round Dollar Amounts)
- revenue_testing_engine.py (RT-03: Round Revenue Amounts)
- payroll_testing_engine.py (PR-T3: Round Salary Amounts)

Sprint 819 item 3: the matching loop and the "count all, keep the most severe
then the largest" cap (decided 2026-10-24, applied in Sprint 831) were still
copied into all four tests; they now live here as ``match_round_amount`` and
``keep_most_severe``. Each test keeps its own threshold check and its own
flag construction, because those differ (and are part of the JSON output).
"""

from collections.abc import Callable, Sequence
from decimal import Decimal
from typing import TypeVar

from shared.testing_enums import SEVERITY_WEIGHTS, Severity

_T = TypeVar("_T")

# Standard round amount patterns: (divisor, name, severity)
# JE engine uses 3-tier (no $25K), AP/Payroll use 4-tier (with $25K)
ROUND_AMOUNT_PATTERNS_3TIER: list[tuple[float, str, Severity]] = [
    (100000.0, "hundred_thousand", Severity.HIGH),
    (50000.0, "fifty_thousand", Severity.MEDIUM),
    (10000.0, "ten_thousand", Severity.LOW),
]

ROUND_AMOUNT_PATTERNS_4TIER: list[tuple[float, str, Severity]] = [
    (100000.0, "hundred_thousand", Severity.HIGH),
    (50000.0, "fifty_thousand", Severity.HIGH),
    (25000.0, "twenty_five_thousand", Severity.MEDIUM),
    (10000.0, "ten_thousand", Severity.LOW),
]


def match_round_amount(
    amount: Decimal,
    patterns: Sequence[tuple[float, str, Severity]],
) -> tuple[float, str, Severity] | None:
    """Return the first (largest) ``(divisor, name, severity)`` that ``amount`` is a multiple of.

    Decimal arithmetic throughout: a float modulo can miss an exact multiple
    that arrived as text (or report one that is not). ``amount`` is the
    already-absolute value; the caller applies its own threshold first.
    """
    for divisor, name, severity in patterns:
        d = Decimal(str(divisor))
        if amount >= d and amount % d == 0:
            return divisor, name, severity
    return None


def keep_most_severe(
    flagged: list[_T],
    *,
    severity_of: Callable[[_T], Severity],
    amount_of: Callable[[_T], Decimal],
    cap: int,
) -> tuple[list[_T], int]:
    """Count every flag, then keep the ``cap`` most severe (ties: largest first).

    Returns ``(kept, total_flagged)``. Most severe first, then largest, so a
    large LOW match can never push a HIGH one out of the kept list — the
    severity floors read only the kept flags (Sprint 831, PR #225 review). The
    sort is stable, so equal flags keep their input (file) order.
    """
    flagged.sort(key=lambda f: (SEVERITY_WEIGHTS[severity_of(f)], amount_of(f)), reverse=True)
    return flagged[:cap], len(flagged)


def detect_round_amount(
    amount: float,
    threshold: float = 10000.0,
    use_4tier: bool = False,
) -> tuple[Severity, str, float] | None:
    """Check if an amount matches a round dollar pattern.

    Args:
        amount: Absolute amount to check.
        threshold: Minimum amount to consider.
        use_4tier: Use 4-tier patterns (AP/Payroll) vs 3-tier (JE).

    Returns:
        (severity, pattern_name, divisor) if round, else None.
    """
    if amount < threshold:
        return None

    patterns = ROUND_AMOUNT_PATTERNS_4TIER if use_4tier else ROUND_AMOUNT_PATTERNS_3TIER
    match = match_round_amount(Decimal(str(amount)), patterns)
    if match is None:
        return None
    divisor, name, severity = match
    return (severity, name, divisor)
