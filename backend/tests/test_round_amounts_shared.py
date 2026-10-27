"""Sprint 819 item 3: the shared round-amount helpers used by JE, AP, Revenue and Payroll."""

from dataclasses import dataclass
from decimal import Decimal

from shared.round_amounts import (
    ROUND_AMOUNT_PATTERNS_3TIER,
    ROUND_AMOUNT_PATTERNS_4TIER,
    detect_round_amount,
    keep_most_severe,
    match_round_amount,
)
from shared.testing_enums import Severity


class TestMatchRoundAmount:
    def test_largest_pattern_wins(self):
        assert match_round_amount(Decimal("200000"), ROUND_AMOUNT_PATTERNS_4TIER) == (
            100000.0,
            "hundred_thousand",
            Severity.HIGH,
        )
        assert match_round_amount(Decimal("75000"), ROUND_AMOUNT_PATTERNS_4TIER)[1] == "twenty_five_thousand"

    def test_three_tier_has_no_25k(self):
        assert match_round_amount(Decimal("75000"), ROUND_AMOUNT_PATTERNS_3TIER) is None

    def test_not_round(self):
        assert match_round_amount(Decimal("10000.01"), ROUND_AMOUNT_PATTERNS_4TIER) is None
        assert match_round_amount(Decimal("5000"), ROUND_AMOUNT_PATTERNS_4TIER) is None

    def test_decimal_exact(self):
        # Trailing zeros after the point are still an exact multiple.
        assert match_round_amount(Decimal("30000.00"), ROUND_AMOUNT_PATTERNS_4TIER)[1] == "ten_thousand"

    def test_detect_round_amount_unchanged(self):
        assert detect_round_amount(50000.0, use_4tier=True) == (Severity.HIGH, "fifty_thousand", 50000.0)
        assert detect_round_amount(50000.0) == (Severity.MEDIUM, "fifty_thousand", 50000.0)
        assert detect_round_amount(9000.0) is None


@dataclass
class _Flag:
    severity: Severity
    amount: Decimal
    order: int


class TestKeepMostSevere:
    def test_counts_all_keeps_most_severe_then_largest(self):
        flags = [
            _Flag(Severity.LOW, Decimal("900000"), 0),
            _Flag(Severity.HIGH, Decimal("100000"), 1),
            _Flag(Severity.MEDIUM, Decimal("25000"), 2),
            _Flag(Severity.HIGH, Decimal("200000"), 3),
        ]
        kept, total = keep_most_severe(flags, severity_of=lambda f: f.severity, amount_of=lambda f: f.amount, cap=2)
        assert total == 4
        assert [f.order for f in kept] == [3, 1]

    def test_ties_keep_input_order(self):
        flags = [_Flag(Severity.LOW, Decimal("10000"), i) for i in range(5)]
        kept, total = keep_most_severe(flags, severity_of=lambda f: f.severity, amount_of=lambda f: f.amount, cap=3)
        assert total == 5
        assert [f.order for f in kept] == [0, 1, 2]
