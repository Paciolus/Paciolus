"""
Shared Round Amount Detection — Sprint 90

Extracted from JE/AP/Payroll testing engines.
Common 4-tier pattern for detecting suspiciously round dollar amounts.

Used by:
- je_testing_engine.py (T4: Round Dollar Amounts)
- ap_testing_engine.py (AP-T4: Round Dollar Amounts)
- payroll_testing_engine.py (PR-T3: Round Salary Amounts)
"""

from shared.testing_enums import Severity


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
    for divisor, name, severity in patterns:
        if amount >= divisor and amount % divisor == 0:
            return (severity, name, divisor)

    return None
