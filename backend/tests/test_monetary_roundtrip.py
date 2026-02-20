"""
Monetary Precision Roundtrip Tests — Sprint 343

Integration tests verifying Decimal precision through the full stack:
- 0.1+0.2 class verification
- High-volume summation
- DB roundtrip (Numeric columns)
- Balance equality (monetary_equal)
- Edge cases (negative, zero, trillions, None)
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.monetary import BALANCE_TOLERANCE, monetary_equal, quantize_monetary


# =============================================================================
# 1. Classic Float Precision Tests
# =============================================================================


class TestClassicFloatPrecision:
    """Verify quantize_monetary handles known float-precision edge cases."""

    def test_point_one_plus_point_two(self):
        """0.1 + 0.2 must quantize to exactly Decimal('0.30')."""
        assert quantize_monetary(0.1 + 0.2) == Decimal("0.30")

    def test_point_one_plus_point_two_equality(self):
        """0.1 + 0.2 must be monetarily equal to 0.3."""
        assert monetary_equal(0.1 + 0.2, 0.3) is True

    def test_many_point_ones_sum_to_exact_integer(self):
        """10 × 0.1 must quantize to exactly Decimal('1.00')."""
        total = sum(0.1 for _ in range(10))
        assert quantize_monetary(total) == Decimal("1.00")

    def test_seven_tenths_plus_three_tenths(self):
        """0.7 + 0.3 must be exactly 1.00."""
        assert monetary_equal(0.7 + 0.3, 1.0) is True


# =============================================================================
# 2. High-Volume Summation Tests
# =============================================================================


class TestHighVolumeSummation:
    """Verify precision under high-count aggregation."""

    def test_10000_pennies_decimal_sum(self):
        """Sum 10,000 Decimal('0.01') values → exactly Decimal('100.00')."""
        total = sum(Decimal("0.01") for _ in range(10_000))
        assert quantize_monetary(total) == Decimal("100.00")

    def test_10000_pennies_float_sum(self):
        """Sum 10,000 float 0.01 values → quantize catches drift."""
        float_total = sum(0.01 for _ in range(10_000))
        assert quantize_monetary(float_total) == Decimal("100.00")

    def test_mixed_sign_accumulation(self):
        """Alternating +0.01/-0.01 over 20,000 iterations → exactly 0.00."""
        total = sum(0.01 if i % 2 == 0 else -0.01 for i in range(20_000))
        assert quantize_monetary(total) == Decimal("0.00")


# =============================================================================
# 3. DB Roundtrip Tests (Numeric columns)
# =============================================================================


class TestDBRoundtrip:
    """Verify Decimal survives write → read cycle through Numeric columns."""

    def test_activity_log_monetary_roundtrip(self, db_session):
        """Write Decimal to ActivityLog Numeric columns, read back exact 2dp."""
        from models import ActivityLog

        log = ActivityLog(
            filename_hash="a" * 64,
            record_count=100,
            total_debits=Decimal("1234567.89"),
            total_credits=Decimal("1234567.89"),
            materiality_threshold=Decimal("50000.00"),
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()

        fetched = db_session.query(ActivityLog).filter_by(id=log.id).one()
        # Numeric columns return Decimal on PostgreSQL, may return float on SQLite
        assert monetary_equal(fetched.total_debits, Decimal("1234567.89"))
        assert monetary_equal(fetched.total_credits, Decimal("1234567.89"))
        assert monetary_equal(fetched.materiality_threshold, Decimal("50000.00"))

    def test_diagnostic_summary_monetary_roundtrip(self, db_session):
        """Write Decimal to DiagnosticSummary Numeric columns, verify to_dict()."""
        from models import Client, DiagnosticSummary, Industry, User

        user = User(email="roundtrip@test.com", hashed_password="x" * 60)
        db_session.add(user)
        db_session.flush()

        client = Client(user_id=user.id, name="Roundtrip Corp", industry=Industry.TECHNOLOGY)
        db_session.add(client)
        db_session.flush()

        summary = DiagnosticSummary(
            client_id=client.id,
            user_id=user.id,
            total_assets=Decimal("999999999999.99"),
            total_liabilities=Decimal("500000000000.50"),
            total_equity=Decimal("499999999999.49"),
            total_revenue=Decimal("100000000.00"),
            total_debits=Decimal("1500000000000.49"),
            total_credits=Decimal("1500000000000.49"),
            materiality_threshold=Decimal("10000.00"),
        )
        db_session.add(summary)
        db_session.flush()

        fetched = db_session.query(DiagnosticSummary).filter_by(id=summary.id).one()
        d = fetched.to_dict()

        # to_dict() wraps in float() — verify 2dp preserved
        assert d["total_assets"] == 999999999999.99
        assert d["total_liabilities"] == 500000000000.50
        assert d["total_equity"] == 499999999999.49
        assert d["total_debits"] == 1500000000000.49
        assert d["total_credits"] == 1500000000000.49
        assert d["materiality_threshold"] == 10000.00

    def test_engagement_materiality_roundtrip(self, db_session):
        """Write Decimal materiality_amount, verify to_dict() float output."""
        from datetime import UTC, datetime

        from engagement_model import Engagement, EngagementStatus
        from models import Client, Industry, User

        user = User(email="eng_roundtrip@test.com", hashed_password="x" * 60)
        db_session.add(user)
        db_session.flush()

        client = Client(user_id=user.id, name="Eng Roundtrip Inc", industry=Industry.OTHER)
        db_session.add(client)
        db_session.flush()

        eng = Engagement(
            client_id=client.id,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
            status=EngagementStatus.ACTIVE,
            materiality_amount=Decimal("75000.50"),
            created_by=user.id,
        )
        db_session.add(eng)
        db_session.flush()

        fetched = db_session.query(Engagement).filter_by(id=eng.id).one()
        d = fetched.to_dict()
        assert d["materiality_amount"] == 75000.50

    def test_activity_log_to_dict_json_types(self, db_session):
        """ActivityLog.to_dict() monetary fields should be plain float for JSON."""
        from models import ActivityLog

        log = ActivityLog(
            filename_hash="b" * 64,
            record_count=50,
            total_debits=Decimal("100.00"),
            total_credits=Decimal("100.00"),
            materiality_threshold=Decimal("5000.00"),
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()

        fetched = db_session.query(ActivityLog).filter_by(id=log.id).one()
        d = fetched.to_dict()
        assert isinstance(d["total_debits"], float)
        assert isinstance(d["total_credits"], float)
        assert isinstance(d["materiality_threshold"], float)


# =============================================================================
# 4. Balance Equality Tests
# =============================================================================


class TestBalanceEquality:
    """Verify monetary_equal handles TB balance scenarios."""

    def test_balanced_tb_exact(self):
        """Exact debit/credit equality."""
        assert monetary_equal(1_000_000.00, 1_000_000.00) is True

    def test_balanced_tb_sub_cent_diff(self):
        """Difference of 0.004 (sub-cent) should be equal after quantization."""
        assert monetary_equal(1_000_000.004, 1_000_000.00) is True

    def test_unbalanced_tb_one_cent(self):
        """Difference of exactly 0.01 should NOT be equal."""
        assert monetary_equal(1_000_000.01, 1_000_000.00) is False

    def test_balance_tolerance_is_decimal(self):
        """BALANCE_TOLERANCE should be a Decimal for safe comparisons."""
        assert isinstance(BALANCE_TOLERANCE, Decimal)
        assert BALANCE_TOLERANCE == Decimal("0.01")


# =============================================================================
# 5. Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge cases for monetary operations."""

    def test_negative_amount(self):
        assert quantize_monetary(-12345.678) == Decimal("-12345.68")

    def test_zero(self):
        assert quantize_monetary(0) == Decimal("0.00")

    def test_none(self):
        assert quantize_monetary(None) == Decimal("0.00")

    def test_trillion_amount(self):
        assert quantize_monetary(9_999_999_999_999.99) == Decimal("9999999999999.99")

    def test_very_small_positive(self):
        assert quantize_monetary(0.001) == Decimal("0.00")

    def test_half_cent_rounds_up(self):
        """0.005 rounds UP to 0.01 (HALF_UP), not 0.00 (banker's)."""
        assert quantize_monetary(0.005) == Decimal("0.01")

    def test_negative_half_cent_rounds_away_from_zero(self):
        """-0.005 rounds to -0.01 (away from zero)."""
        assert quantize_monetary(-0.005) == Decimal("-0.01")

    def test_string_decimal_input(self):
        assert quantize_monetary("123456789.12345") == Decimal("123456789.12")

    def test_integer_input(self):
        assert quantize_monetary(42) == Decimal("42.00")


# =============================================================================
# 6. CategoryTotals.to_dict() Quantization
# =============================================================================


class TestCategoryTotalsQuantization:
    """Verify ratio_engine CategoryTotals uses ROUND_HALF_UP via quantize_monetary."""

    def test_to_dict_uses_half_up(self):
        from ratio_engine import CategoryTotals

        totals = CategoryTotals(total_assets=2.225, total_liabilities=2.235)
        d = totals.to_dict()
        # ROUND_HALF_UP: 2.225 → 2.23, 2.235 → 2.24
        assert d["total_assets"] == 2.23
        assert d["total_liabilities"] == 2.24

    def test_to_dict_classic_float_error(self):
        from ratio_engine import CategoryTotals

        totals = CategoryTotals(total_revenue=0.1 + 0.2)
        d = totals.to_dict()
        assert d["total_revenue"] == 0.3
