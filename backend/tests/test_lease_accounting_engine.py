"""Tests for lease_accounting_engine (Sprint 629)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from lease_accounting_engine import (
    LeaseClassification,
    LeaseConfig,
    LeaseInputError,
    compute_lease_accounting,
)

# =============================================================================
# Classification (ASC 842-10-25-2)
# =============================================================================


class TestClassification:
    def test_no_criteria_triggered_is_operating(self):
        config = LeaseConfig(
            lease_name="Office Lease",
            payment_amount=Decimal("5000"),
            term_periods=36,  # 3 years monthly
            annual_discount_rate=Decimal("0.05"),
            asset_useful_life_years=10,  # 3/10 = 30% — well below 75%
            asset_fair_value=Decimal("500000"),  # PV will be much less than 90%
        )
        result = compute_lease_accounting(config)
        assert result.classification_result.classification == LeaseClassification.OPERATING

    def test_transfers_ownership_forces_finance(self):
        config = LeaseConfig(
            lease_name="Equipment",
            payment_amount=Decimal("1000"),
            term_periods=12,
            annual_discount_rate=Decimal("0.05"),
            transfers_ownership=True,
        )
        result = compute_lease_accounting(config)
        assert result.classification_result.classification == LeaseClassification.FINANCE

    def test_bargain_purchase_forces_finance(self):
        config = LeaseConfig(
            lease_name="Vehicle",
            payment_amount=Decimal("500"),
            term_periods=24,
            annual_discount_rate=Decimal("0.06"),
            bargain_purchase_option=True,
        )
        result = compute_lease_accounting(config)
        assert result.classification_result.classification == LeaseClassification.FINANCE

    def test_long_term_relative_to_useful_life_forces_finance(self):
        # 8 years lease on 10-year-life asset = 80% → triggers (c)
        config = LeaseConfig(
            lease_name="Crane",
            payment_amount=Decimal("10000"),
            term_periods=96,  # 8 years monthly
            annual_discount_rate=Decimal("0.05"),
            asset_useful_life_years=10,
        )
        result = compute_lease_accounting(config)
        assert result.classification_result.classification == LeaseClassification.FINANCE
        # Criterion (c) should be the triggered one
        c_crit = next(c for c in result.classification_result.criteria if c.code == "c")
        assert c_crit.triggered

    def test_pv_exceeds_90pct_of_fv_forces_finance(self):
        # 60 monthly $5k / 5% rate / FV $250k → PV ≈ $264k (>90% of $250k)
        config = LeaseConfig(
            lease_name="Building",
            payment_amount=Decimal("5000"),
            term_periods=60,
            annual_discount_rate=Decimal("0.05"),
            asset_fair_value=Decimal("250000"),
        )
        result = compute_lease_accounting(config)
        assert result.classification_result.classification == LeaseClassification.FINANCE
        d_crit = next(c for c in result.classification_result.criteria if c.code == "d")
        assert d_crit.triggered

    def test_specialized_nature_forces_finance(self):
        config = LeaseConfig(
            lease_name="Custom Robot",
            payment_amount=Decimal("2000"),
            term_periods=24,
            annual_discount_rate=Decimal("0.05"),
            specialized_nature=True,
        )
        result = compute_lease_accounting(config)
        assert result.classification_result.classification == LeaseClassification.FINANCE

    def test_all_five_criteria_returned_regardless(self):
        config = LeaseConfig(
            lease_name="Office",
            payment_amount=Decimal("1000"),
            term_periods=12,
            annual_discount_rate=Decimal("0.05"),
        )
        result = compute_lease_accounting(config)
        codes = sorted(c.code for c in result.classification_result.criteria)
        assert codes == ["a", "b", "c", "d", "e"]


# =============================================================================
# Initial measurement
# =============================================================================


class TestInitialMeasurement:
    def test_initial_liability_equals_pv_of_payments(self):
        # 12 monthly payments of $1,000 at 6%, payments in advance
        # PV = 1000 + 1000 * (1 - (1.005)^-11) / 0.005 = ~11,716.55
        config = LeaseConfig(
            lease_name="Test",
            payment_amount=Decimal("1000"),
            term_periods=12,
            annual_discount_rate=Decimal("0.06"),
            payments_in_advance=True,
        )
        result = compute_lease_accounting(config)
        # PV must be less than total undiscounted payments ($12,000)
        assert result.initial_lease_liability < Decimal("12000")
        # And at least 95% of total — short term, low discount
        assert result.initial_lease_liability > Decimal("11600")

    def test_zero_rate_pv_equals_undiscounted(self):
        config = LeaseConfig(
            lease_name="Free",
            payment_amount=Decimal("1000"),
            term_periods=12,
            annual_discount_rate=Decimal("0"),
        )
        result = compute_lease_accounting(config)
        assert result.initial_lease_liability == Decimal("12000.00")

    def test_rou_includes_idc_and_prepaid_minus_incentives(self):
        config = LeaseConfig(
            lease_name="Office",
            payment_amount=Decimal("1000"),
            term_periods=12,
            annual_discount_rate=Decimal("0.06"),
            initial_direct_costs=Decimal("500"),
            prepaid_lease_payments=Decimal("200"),
            lease_incentives=Decimal("300"),
        )
        result = compute_lease_accounting(config)
        # ROU = liability + 200 + 500 - 300 = liability + 400
        assert result.initial_rou_asset == result.initial_lease_liability + Decimal("400.00")


# =============================================================================
# Liability schedule
# =============================================================================


class TestLiabilitySchedule:
    def test_liability_amortizes_to_zero(self):
        config = LeaseConfig(
            lease_name="Test",
            payment_amount=Decimal("1000"),
            term_periods=24,
            annual_discount_rate=Decimal("0.06"),
        )
        result = compute_lease_accounting(config)
        assert result.liability_schedule[-1].ending_liability == Decimal("0.00")
        assert len(result.liability_schedule) == 24

    def test_total_payments_equals_principal_plus_interest(self):
        config = LeaseConfig(
            lease_name="Test",
            payment_amount=Decimal("1000"),
            term_periods=12,
            annual_discount_rate=Decimal("0.06"),
        )
        result = compute_lease_accounting(config)
        total_payments = sum(e.payment for e in result.liability_schedule)
        total_principal = sum(e.principal for e in result.liability_schedule)
        # Sum of principal reductions equals the initial liability (within
        # one cent of rounding drift across 12 quantized rows).
        assert abs(total_principal - result.initial_lease_liability) <= Decimal("0.01")
        # Total interest is the difference between payments and principal
        assert abs((total_payments - total_principal) - result.total_interest_expense) <= Decimal("0.05")


# =============================================================================
# Operating ROU schedule (straight-line lease cost)
# =============================================================================


class TestOperatingRou:
    def test_operating_lease_cost_is_straight_line(self):
        config = LeaseConfig(
            lease_name="Office",
            payment_amount=Decimal("1000"),
            term_periods=24,
            annual_discount_rate=Decimal("0.06"),
        )
        result = compute_lease_accounting(config)
        # Operating expected
        assert result.classification_result.classification == LeaseClassification.OPERATING
        # Every period_lease_cost is the same SL value
        first_cost = result.rou_schedule[0].period_lease_cost
        for entry in result.rou_schedule:
            assert entry.period_lease_cost == first_cost
        # SL value = total payments / 24 = 1000
        assert first_cost == Decimal("1000.00")

    def test_operating_rou_amortizes_to_zero(self):
        config = LeaseConfig(
            lease_name="Office",
            payment_amount=Decimal("1500"),
            term_periods=12,
            annual_discount_rate=Decimal("0.04"),
        )
        result = compute_lease_accounting(config)
        assert result.rou_schedule[-1].ending_rou_balance == Decimal("0.00")


# =============================================================================
# Finance ROU schedule (separate amortization + interest)
# =============================================================================


class TestFinanceRou:
    def test_finance_rou_is_straight_line_amortization(self):
        config = LeaseConfig(
            lease_name="Equipment",
            payment_amount=Decimal("1000"),
            term_periods=12,
            annual_discount_rate=Decimal("0.06"),
            transfers_ownership=True,  # forces finance
        )
        result = compute_lease_accounting(config)
        assert result.classification_result.classification == LeaseClassification.FINANCE
        # All ROU amortization periods (except possibly final) are equal
        first = result.rou_schedule[0].rou_amortization
        for entry in result.rou_schedule[:-1]:
            assert entry.rou_amortization == first
        # Final balance is zero
        assert result.rou_schedule[-1].ending_rou_balance == Decimal("0.00")

    def test_finance_period_cost_includes_interest(self):
        """For a finance lease, period cost is amortization + interest, NOT
        a single straight-line number."""
        config = LeaseConfig(
            lease_name="Equipment",
            payment_amount=Decimal("1000"),
            term_periods=24,
            annual_discount_rate=Decimal("0.10"),
            transfers_ownership=True,
        )
        result = compute_lease_accounting(config)
        # Period 1 cost should be larger than later periods (interest is
        # front-loaded under effective interest).
        first_cost = result.rou_schedule[0].period_lease_cost
        last_cost = result.rou_schedule[-2].period_lease_cost
        assert first_cost > last_cost


# =============================================================================
# Disclosures
# =============================================================================


class TestDisclosures:
    def test_maturity_buckets_year1_through_thereafter(self):
        config = LeaseConfig(
            lease_name="LongTerm",
            payment_amount=Decimal("1000"),
            term_periods=120,  # 10 years monthly
            annual_discount_rate=Decimal("0.05"),
        )
        result = compute_lease_accounting(config)
        labels = [b.label for b in result.disclosure_tables.maturity_analysis]
        assert labels == ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5", "Thereafter"]
        # Years 1-5 should each be 12,000; thereafter = 60,000
        for bucket in result.disclosure_tables.maturity_analysis[:5]:
            assert bucket.undiscounted_payments == Decimal("12000.00")
        thereafter = result.disclosure_tables.maturity_analysis[5]
        assert thereafter.undiscounted_payments == Decimal("60000.00")

    def test_total_payments_minus_pv_equals_imputed_interest(self):
        config = LeaseConfig(
            lease_name="Test",
            payment_amount=Decimal("1000"),
            term_periods=24,
            annual_discount_rate=Decimal("0.06"),
        )
        result = compute_lease_accounting(config)
        d = result.disclosure_tables
        # Total - PV = imputed interest
        assert d.total_undiscounted_payments - d.present_value_of_lease_liability == d.less_imputed_interest

    def test_weighted_avg_term_for_uniform_payments(self):
        """For uniform payments, weighted-avg term is roughly half the lease
        term (more precisely: (n+1)/2 periods → ((n+1)/2)/periods_per_year years)."""
        config = LeaseConfig(
            lease_name="Test",
            payment_amount=Decimal("1000"),
            term_periods=24,  # 2 years monthly
            annual_discount_rate=Decimal("0.06"),
        )
        result = compute_lease_accounting(config)
        # Expected: ((24+1)/2) / 12 = 1.04 years
        weighted = result.disclosure_tables.weighted_average_remaining_term_years
        assert Decimal("1.0") <= weighted <= Decimal("1.1")


# =============================================================================
# Escalation
# =============================================================================


class TestEscalation:
    def test_annual_escalation_increases_payments(self):
        config = LeaseConfig(
            lease_name="Office",
            payment_amount=Decimal("1000"),
            term_periods=36,  # 3 years
            annual_discount_rate=Decimal("0.05"),
            annual_escalation_rate=Decimal("0.03"),  # 3% annual escalation
        )
        result = compute_lease_accounting(config)
        # Year 1 (periods 1-12) = 1000
        # Year 2 (periods 13-24) = 1000 * 1.03 = 1030
        # Year 3 (periods 25-36) = 1000 * 1.03^2 = 1060.90
        assert result.liability_schedule[0].payment == Decimal("1000.00")
        assert result.liability_schedule[12].payment == Decimal("1030.00")
        assert result.liability_schedule[24].payment == Decimal("1060.90")


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    def test_negative_payment_rejected(self):
        with pytest.raises(LeaseInputError):
            compute_lease_accounting(
                LeaseConfig(
                    lease_name="x",
                    payment_amount=Decimal("-1"),
                    term_periods=12,
                    annual_discount_rate=Decimal("0.05"),
                )
            )

    def test_zero_term_rejected(self):
        with pytest.raises(LeaseInputError):
            compute_lease_accounting(
                LeaseConfig(
                    lease_name="x",
                    payment_amount=Decimal("100"),
                    term_periods=0,
                    annual_discount_rate=Decimal("0.05"),
                )
            )

    def test_negative_rate_rejected(self):
        with pytest.raises(LeaseInputError):
            compute_lease_accounting(
                LeaseConfig(
                    lease_name="x",
                    payment_amount=Decimal("100"),
                    term_periods=12,
                    annual_discount_rate=Decimal("-0.01"),
                )
            )


# =============================================================================
# Serialization
# =============================================================================


class TestSerialization:
    def test_to_dict_round_trip(self):
        config = LeaseConfig(
            lease_name="Test",
            payment_amount=Decimal("1000"),
            term_periods=12,
            annual_discount_rate=Decimal("0.06"),
            start_date=date(2026, 1, 1),
        )
        result = compute_lease_accounting(config)
        payload = result.to_dict()
        assert "classification" in payload
        assert "liability_schedule" in payload
        assert "rou_schedule" in payload
        assert "disclosure_tables" in payload
        assert payload["classification"]["classification"] in {"operating", "finance"}
