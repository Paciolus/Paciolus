"""
Shared Monetary Utility Tests — Sprint 340

Unit tests for quantize_monetary, monetary_equal, and BALANCE_TOLERANCE.
"""

import sys
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.monetary import (
    BALANCE_TOLERANCE,
    MONETARY_PRECISION,
    MONETARY_ZERO,
    monetary_equal,
    quantize_monetary,
)


class TestQuantizeMonetary:
    """Tests for quantize_monetary() — deterministic 2dp ROUND_HALF_UP."""

    def test_float_classic_error(self):
        """0.1 + 0.2 should quantize to 0.30, not 0.30000000000000004."""
        assert quantize_monetary(0.1 + 0.2) == Decimal("0.30")

    def test_round_half_up_not_bankers(self):
        """2.225 should round to 2.23 (HALF_UP), not 2.22 (banker's)."""
        result = quantize_monetary(2.225)
        assert result == Decimal("2.23")
        # Verify banker's rounding would give different result
        bankers = Decimal(str(2.225)).quantize(MONETARY_PRECISION, rounding=ROUND_HALF_EVEN)
        assert bankers == Decimal("2.22")
        assert result != bankers

    def test_round_half_up_2_235(self):
        """2.235 should round to 2.24 (HALF_UP)."""
        assert quantize_monetary(2.235) == Decimal("2.24")

    def test_round_half_up_2_245(self):
        """2.245 should round to 2.25 (HALF_UP)."""
        assert quantize_monetary(2.245) == Decimal("2.25")

    def test_positive_float(self):
        assert quantize_monetary(1234.567) == Decimal("1234.57")

    def test_negative_float(self):
        assert quantize_monetary(-1234.564) == Decimal("-1234.56")

    def test_negative_round_half_up(self):
        """Negative 2.225 should round to -2.23 (away from zero)."""
        assert quantize_monetary(-2.225) == Decimal("-2.23")

    def test_zero_float(self):
        assert quantize_monetary(0.0) == MONETARY_ZERO

    def test_zero_int(self):
        assert quantize_monetary(0) == MONETARY_ZERO

    def test_none(self):
        assert quantize_monetary(None) == MONETARY_ZERO

    def test_decimal_input(self):
        assert quantize_monetary(Decimal("1234.5678")) == Decimal("1234.57")

    def test_string_input(self):
        assert quantize_monetary("9876.543") == Decimal("9876.54")

    def test_int_input(self):
        assert quantize_monetary(42) == Decimal("42.00")

    def test_very_large_amount(self):
        """Trillions should quantize correctly."""
        result = quantize_monetary(1234567890123.456)
        assert result == Decimal("1234567890123.46")

    def test_very_small_amount(self):
        """Fractions of a cent should quantize to 0.00 or 0.01."""
        assert quantize_monetary(0.001) == Decimal("0.00")
        assert quantize_monetary(0.009) == Decimal("0.01")
        assert quantize_monetary(0.005) == Decimal("0.01")  # HALF_UP

    def test_invalid_string(self):
        """Invalid string input should return MONETARY_ZERO."""
        assert quantize_monetary("not_a_number") == MONETARY_ZERO

    def test_exact_two_decimal_places(self):
        """Already-exact 2dp values should pass through unchanged."""
        assert quantize_monetary(100.00) == Decimal("100.00")
        assert quantize_monetary(Decimal("50.25")) == Decimal("50.25")


class TestMonetaryEqual:
    """Tests for monetary_equal() — quantize-then-compare."""

    def test_float_vs_decimal_equal(self):
        assert monetary_equal(100.0, Decimal("100.00")) is True

    def test_float_rounding_equal(self):
        """0.1 + 0.2 should equal 0.3 after quantization."""
        assert monetary_equal(0.1 + 0.2, 0.3) is True

    def test_different_amounts(self):
        assert monetary_equal(100.01, 100.02) is False

    def test_string_vs_float(self):
        assert monetary_equal("99.99", 99.99) is True

    def test_none_vs_zero(self):
        assert monetary_equal(None, 0.0) is True

    def test_none_vs_none(self):
        assert monetary_equal(None, None) is True

    def test_sub_cent_difference(self):
        """Amounts differing by less than 0.005 should be equal after rounding."""
        assert monetary_equal(100.004, 100.00) is True

    def test_half_cent_boundary(self):
        """100.005 rounds to 100.01 (HALF_UP), not equal to 100.00."""
        assert monetary_equal(100.005, 100.00) is False

    def test_negative_equal(self):
        assert monetary_equal(-50.0, Decimal("-50.00")) is True


class TestBalanceTolerance:
    """Tests for BALANCE_TOLERANCE as Decimal."""

    def test_tolerance_is_decimal(self):
        assert isinstance(BALANCE_TOLERANCE, Decimal)

    def test_tolerance_value(self):
        assert BALANCE_TOLERANCE == Decimal("0.01")

    def test_tolerance_comparison_with_decimal(self):
        """Decimal comparison should work directly."""
        diff = Decimal("0.009")
        assert diff < BALANCE_TOLERANCE

    def test_tolerance_comparison_at_boundary(self):
        diff = Decimal("0.01")
        assert not (diff < BALANCE_TOLERANCE)

    def test_tolerance_comparison_above(self):
        diff = Decimal("0.02")
        assert not (diff < BALANCE_TOLERANCE)

    def test_float_to_decimal_comparison(self):
        """Converting float diff to Decimal for comparison."""
        float_diff = 0.005
        assert abs(Decimal(str(float_diff))) < BALANCE_TOLERANCE

    def test_monetary_precision_equals_tolerance(self):
        assert MONETARY_PRECISION == BALANCE_TOLERANCE


class TestHighVolumeSummation:
    """Verify quantize_monetary handles high-volume aggregation correctly."""

    def test_10000_pennies(self):
        """Sum 10,000 values of 0.01 should equal exactly 100.00."""
        total = sum(Decimal("0.01") for _ in range(10_000))
        assert quantize_monetary(total) == Decimal("100.00")

    def test_float_sum_drift(self):
        """Demonstrate that float sum drifts but quantize catches it."""
        # Float sum of 10000 * 0.01 may drift
        float_total = sum(0.01 for _ in range(10_000))
        # quantize_monetary should still produce clean 2dp result
        result = quantize_monetary(float_total)
        assert result == Decimal("100.00")
