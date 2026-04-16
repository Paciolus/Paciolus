"""Tests for loan_amortization_engine (Sprint 625)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from loan_amortization_engine import (
    ExtraPayment,
    LoanConfig,
    LoanInputError,
    LoanMethod,
    RateChange,
    generate_amortization_schedule,
)

# =============================================================================
# Standard amortization
# =============================================================================


class TestStandardAmortization:
    def test_thirty_year_fixed_known_payment(self):
        """$200,000 @ 6% for 30 years monthly = $1,199.10/mo (industry-standard)."""
        config = LoanConfig(
            principal=Decimal("200000"),
            annual_rate=Decimal("0.06"),
            term_periods=360,
            frequency="monthly",
        )
        result = generate_amortization_schedule(config)

        assert len(result.schedule) == 360
        first = result.schedule[0]
        # Within $0.05 of the published $1,199.10 monthly payment
        assert abs(first.scheduled_payment - Decimal("1199.10")) <= Decimal("0.05")
        # Final balance must be exactly zero
        assert result.schedule[-1].ending_balance == Decimal("0.00")
        # Total interest should be roughly $231,676 for this textbook loan
        assert Decimal("231600") <= result.total_interest <= Decimal("231700")

    def test_zero_rate_loan(self):
        """A 0% loan amortizes evenly, no interest."""
        config = LoanConfig(
            principal=Decimal("12000"),
            annual_rate=Decimal("0"),
            term_periods=12,
            frequency="monthly",
        )
        result = generate_amortization_schedule(config)
        assert all(p.interest == Decimal("0.00") for p in result.schedule)
        assert all(p.scheduled_payment == Decimal("1000.00") for p in result.schedule)
        assert result.total_interest == Decimal("0.00")
        assert result.schedule[-1].ending_balance == Decimal("0.00")

    def test_quarterly_frequency(self):
        """Quarterly payments cover 4 periods per year."""
        config = LoanConfig(
            principal=Decimal("100000"),
            annual_rate=Decimal("0.08"),
            term_periods=20,  # 5 years quarterly
            frequency="quarterly",
        )
        result = generate_amortization_schedule(config)
        assert len(result.schedule) == 20
        assert len(result.annual_summary) == 5
        assert result.schedule[-1].ending_balance == Decimal("0.00")


# =============================================================================
# Interest-only & balloon
# =============================================================================


class TestInterestOnly:
    def test_interest_only_payments_constant_until_balloon(self):
        config = LoanConfig(
            principal=Decimal("100000"),
            annual_rate=Decimal("0.06"),
            term_periods=12,
            frequency="monthly",
            method=LoanMethod.INTEREST_ONLY,
        )
        result = generate_amortization_schedule(config)
        # Each period interest = 100000 * 0.06/12 = 500
        for entry in result.schedule[:-1]:
            assert entry.interest == Decimal("500.00")
            assert entry.principal == Decimal("0.00")
            assert entry.scheduled_payment == Decimal("500.00")
            assert entry.ending_balance == Decimal("100000.00")
        # Final period repays principal
        final = result.schedule[-1]
        assert final.principal == Decimal("100000.00")
        assert final.scheduled_payment == Decimal("100500.00")
        assert final.ending_balance == Decimal("0.00")


class TestBalloon:
    def test_balloon_loan_pays_lump_sum_at_end(self):
        config = LoanConfig(
            principal=Decimal("500000"),
            annual_rate=Decimal("0.05"),
            term_periods=60,  # 5-year balloon
            frequency="monthly",
            method=LoanMethod.BALLOON,
            balloon_amount=Decimal("400000"),
        )
        result = generate_amortization_schedule(config)
        assert len(result.schedule) == 60
        # Final payment must clear the balance
        assert result.schedule[-1].ending_balance == Decimal("0.00")
        # Final payment is significantly larger than the level payment
        level = result.schedule[0].scheduled_payment
        assert result.schedule[-1].scheduled_payment > level * Decimal("10")


# =============================================================================
# Extra payments
# =============================================================================


class TestExtraPayments:
    def test_extra_payment_reduces_balance_and_total_interest(self):
        baseline = generate_amortization_schedule(
            LoanConfig(
                principal=Decimal("100000"),
                annual_rate=Decimal("0.06"),
                term_periods=120,
                frequency="monthly",
            )
        )
        with_extra = generate_amortization_schedule(
            LoanConfig(
                principal=Decimal("100000"),
                annual_rate=Decimal("0.06"),
                term_periods=120,
                frequency="monthly",
                extra_payments=[
                    ExtraPayment(period_number=12, amount=Decimal("10000")),
                ],
            )
        )
        # Extra payment shortens the loan and lowers total interest
        assert len(with_extra.schedule) < len(baseline.schedule)
        assert with_extra.total_interest < baseline.total_interest
        # All ends at zero
        assert with_extra.schedule[-1].ending_balance == Decimal("0.00")


# =============================================================================
# Variable rate
# =============================================================================


class TestRateChanges:
    def test_rate_increase_raises_remaining_payments(self):
        config = LoanConfig(
            principal=Decimal("200000"),
            annual_rate=Decimal("0.04"),
            term_periods=60,
            frequency="monthly",
            rate_changes=[RateChange(period_number=37, new_annual_rate=Decimal("0.08"))],
        )
        result = generate_amortization_schedule(config)
        assert len(result.schedule) == 60
        before = result.schedule[35].scheduled_payment
        after = result.schedule[36].scheduled_payment
        assert after > before
        assert result.schedule[-1].ending_balance == Decimal("0.00")


# =============================================================================
# Date handling, summaries, journal entries
# =============================================================================


class TestPayoffDate:
    def test_payment_dates_advance_by_frequency(self):
        config = LoanConfig(
            principal=Decimal("10000"),
            annual_rate=Decimal("0.05"),
            term_periods=12,
            frequency="monthly",
            start_date=date(2026, 1, 15),
        )
        result = generate_amortization_schedule(config)
        # First payment is one month after start date
        assert result.schedule[0].payment_date == date(2026, 2, 15)
        assert result.schedule[-1].payment_date == date(2027, 1, 15)
        assert result.payoff_date == date(2027, 1, 15)


class TestAnnualSummary:
    def test_annual_summary_aggregates_periods(self):
        config = LoanConfig(
            principal=Decimal("60000"),
            annual_rate=Decimal("0.06"),
            term_periods=24,
            frequency="monthly",
            start_date=date(2026, 1, 1),
        )
        result = generate_amortization_schedule(config)
        assert len(result.annual_summary) == 2
        assert result.annual_summary[0].calendar_year == 2026
        assert result.annual_summary[1].calendar_year == 2027
        assert result.annual_summary[1].ending_balance == Decimal("0.00")


class TestJournalEntries:
    def test_journal_entry_templates_balance(self):
        config = LoanConfig(
            principal=Decimal("50000"),
            annual_rate=Decimal("0.05"),
            term_periods=12,
            frequency="monthly",
        )
        result = generate_amortization_schedule(config)
        templates = result.journal_entry_templates
        assert len(templates) == 2
        for tmpl in templates:
            total_dr = sum(amt for _, amt in tmpl.debits)
            total_cr = sum(amt for _, amt in tmpl.credits)
            assert total_dr == total_cr


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_negative_principal_rejected(self):
        with pytest.raises(LoanInputError):
            generate_amortization_schedule(
                LoanConfig(principal=Decimal("-1"), annual_rate=Decimal("0.05"), term_periods=12)
            )

    def test_negative_rate_rejected(self):
        with pytest.raises(LoanInputError):
            generate_amortization_schedule(
                LoanConfig(principal=Decimal("1000"), annual_rate=Decimal("-0.01"), term_periods=12)
            )

    def test_balloon_without_amount_rejected(self):
        with pytest.raises(LoanInputError):
            generate_amortization_schedule(
                LoanConfig(
                    principal=Decimal("1000"),
                    annual_rate=Decimal("0.05"),
                    term_periods=12,
                    method=LoanMethod.BALLOON,
                )
            )

    def test_balloon_exceeding_principal_rejected(self):
        with pytest.raises(LoanInputError):
            generate_amortization_schedule(
                LoanConfig(
                    principal=Decimal("1000"),
                    annual_rate=Decimal("0.05"),
                    term_periods=12,
                    method=LoanMethod.BALLOON,
                    balloon_amount=Decimal("2000"),
                )
            )

    def test_term_cap_enforced(self):
        with pytest.raises(LoanInputError):
            generate_amortization_schedule(
                LoanConfig(principal=Decimal("1000"), annual_rate=Decimal("0.05"), term_periods=601)
            )

    def test_rate_change_outside_term_rejected(self):
        with pytest.raises(LoanInputError):
            generate_amortization_schedule(
                LoanConfig(
                    principal=Decimal("1000"),
                    annual_rate=Decimal("0.05"),
                    term_periods=12,
                    rate_changes=[RateChange(period_number=20, new_annual_rate=Decimal("0.07"))],
                )
            )

    def test_extra_payment_outside_term_rejected(self):
        with pytest.raises(LoanInputError):
            generate_amortization_schedule(
                LoanConfig(
                    principal=Decimal("1000"),
                    annual_rate=Decimal("0.05"),
                    term_periods=12,
                    extra_payments=[ExtraPayment(period_number=15, amount=Decimal("100"))],
                )
            )


# =============================================================================
# Serialization
# =============================================================================


class TestSerialization:
    def test_to_dict_round_trip(self):
        config = LoanConfig(
            principal=Decimal("10000"),
            annual_rate=Decimal("0.05"),
            term_periods=6,
            frequency="monthly",
        )
        result = generate_amortization_schedule(config)
        payload = result.to_dict()
        assert "schedule" in payload
        assert "annual_summary" in payload
        assert "journal_entry_templates" in payload
        assert payload["total_interest"] == str(result.total_interest)
        assert len(payload["schedule"]) == 6
