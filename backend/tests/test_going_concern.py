"""
Tests for Going Concern Indicator Profile Engine — Sprint 360

ISA 570 going concern indicator detection from TB category totals.

Covers:
- Net liability position (negative equity)
- Current ratio below 1.0
- Negative working capital
- Recurring losses (with and without prior period)
- Revenue decline (with prior period)
- High leverage (debt-to-equity > 3.0)
- Full computation with various financial profiles
- Edge cases: all zeros, zero equity, zero prior revenue
- Narrative and disclaimer
"""

from going_concern_engine import (
    CURRENT_RATIO_THRESHOLD,
    DISCLAIMER,
    LEVERAGE_THRESHOLD,
    GoingConcernIndicator,
    GoingConcernReport,
    _test_current_ratio,
    _test_high_leverage,
    _test_negative_working_capital,
    _test_net_liability_position,
    _test_recurring_losses,
    _test_revenue_decline,
    compute_going_concern_profile,
)


# =============================================================================
# TEST 1: NET LIABILITY POSITION
# =============================================================================


class TestNetLiabilityPosition:
    """Tests for _test_net_liability_position()."""

    def test_positive_equity_not_triggered(self):
        ind = _test_net_liability_position(500000, 300000, 200000)
        assert ind.triggered is False
        assert ind.severity == "low"

    def test_negative_equity_triggered(self):
        ind = _test_net_liability_position(400000, 500000, -100000)
        assert ind.triggered is True
        assert ind.severity == "high"
        assert "$500,000.00" in ind.description
        assert "$400,000.00" in ind.description

    def test_zero_equity_not_triggered(self):
        ind = _test_net_liability_position(500000, 500000, 0.0)
        assert ind.triggered is False

    def test_metric_value_is_equity(self):
        ind = _test_net_liability_position(300000, 400000, -100000)
        assert ind.metric_value == -100000


# =============================================================================
# TEST 2: CURRENT RATIO
# =============================================================================


class TestCurrentRatio:
    """Tests for _test_current_ratio()."""

    def test_healthy_ratio_not_triggered(self):
        ind = _test_current_ratio(200000, 100000)
        assert ind.triggered is False
        assert ind.metric_value == 2.0

    def test_below_one_triggered(self):
        ind = _test_current_ratio(80000, 100000)
        assert ind.triggered is True
        assert ind.metric_value == 0.8
        assert ind.severity == "medium"

    def test_very_low_ratio_high_severity(self):
        ind = _test_current_ratio(40000, 100000)
        assert ind.triggered is True
        assert ind.severity == "high"  # < 0.5

    def test_exact_one_not_triggered(self):
        ind = _test_current_ratio(100000, 100000)
        assert ind.triggered is False

    def test_zero_liabilities_not_triggered(self):
        ind = _test_current_ratio(100000, 0.0)
        assert ind.triggered is False
        assert "not calculable" in ind.description

    def test_threshold_value(self):
        ind = _test_current_ratio(80000, 100000)
        assert ind.threshold == CURRENT_RATIO_THRESHOLD


# =============================================================================
# TEST 3: NEGATIVE WORKING CAPITAL
# =============================================================================


class TestNegativeWorkingCapital:
    """Tests for _test_negative_working_capital()."""

    def test_positive_wc_not_triggered(self):
        ind = _test_negative_working_capital(150000, 100000)
        assert ind.triggered is False
        assert ind.metric_value == 50000

    def test_negative_wc_triggered(self):
        ind = _test_negative_working_capital(80000, 120000)
        assert ind.triggered is True
        assert ind.metric_value == -40000

    def test_high_severity_large_deficit(self):
        """Large deficit relative to current assets → high severity."""
        ind = _test_negative_working_capital(50000, 200000)
        assert ind.severity == "high"  # deficit 150000 > 50000 * 0.5

    def test_medium_severity_small_deficit(self):
        ind = _test_negative_working_capital(100000, 110000)
        assert ind.severity == "medium"  # deficit 10000 < 100000 * 0.5

    def test_zero_wc_not_triggered(self):
        ind = _test_negative_working_capital(100000, 100000)
        assert ind.triggered is False


# =============================================================================
# TEST 4: RECURRING LOSSES
# =============================================================================


class TestRecurringLosses:
    """Tests for _test_recurring_losses()."""

    def test_profitable_not_triggered(self):
        ind = _test_recurring_losses(500000, 400000)
        assert ind.triggered is False
        assert ind.metric_value == 100000

    def test_current_loss_triggered(self):
        ind = _test_recurring_losses(300000, 500000)
        assert ind.triggered is True
        assert ind.severity == "medium"
        assert ind.metric_value == -200000

    def test_consecutive_losses_high_severity(self):
        ind = _test_recurring_losses(300000, 500000, 400000, 600000)
        assert ind.triggered is True
        assert ind.severity == "high"
        assert "Prior period also recorded" in ind.description

    def test_current_loss_prior_profit_medium(self):
        ind = _test_recurring_losses(300000, 500000, 400000, 300000)
        assert ind.triggered is True
        assert ind.severity == "medium"

    def test_current_profit_prior_loss_not_triggered(self):
        ind = _test_recurring_losses(500000, 400000, 300000, 500000)
        assert ind.triggered is False

    def test_no_prior_data(self):
        ind = _test_recurring_losses(300000, 500000, None, None)
        assert ind.triggered is True
        assert ind.severity == "medium"  # No prior → can't be high


# =============================================================================
# TEST 5: REVENUE DECLINE
# =============================================================================


class TestRevenueDeline:
    """Tests for _test_revenue_decline()."""

    def test_revenue_increase_not_triggered(self):
        ind = _test_revenue_decline(600000, 500000)
        assert ind.triggered is False
        assert "increased" in ind.description

    def test_small_decline_not_triggered(self):
        """5% decline is below the 10% threshold."""
        ind = _test_revenue_decline(475000, 500000)
        assert ind.triggered is False

    def test_large_decline_triggered(self):
        ind = _test_revenue_decline(400000, 500000)
        assert ind.triggered is True
        assert ind.severity == "medium"
        assert "20.0%" in ind.description

    def test_severe_decline_high_severity(self):
        """>25% decline is high severity."""
        ind = _test_revenue_decline(300000, 500000)
        assert ind.triggered is True
        assert ind.severity == "high"

    def test_zero_prior_revenue_not_triggered(self):
        ind = _test_revenue_decline(500000, 0.0)
        assert ind.triggered is False
        assert "not calculable" in ind.description

    def test_stable_revenue(self):
        ind = _test_revenue_decline(500000, 500000)
        assert ind.triggered is False
        assert "remained stable" in ind.description

    def test_metric_value_is_percentage(self):
        ind = _test_revenue_decline(400000, 500000)
        assert ind.metric_value == -20.0


# =============================================================================
# TEST 6: HIGH LEVERAGE
# =============================================================================


class TestHighLeverage:
    """Tests for _test_high_leverage()."""

    def test_low_leverage_not_triggered(self):
        ind = _test_high_leverage(200000, 500000)
        assert ind.triggered is False
        assert ind.metric_value == 0.4

    def test_high_leverage_triggered(self):
        ind = _test_high_leverage(400000, 100000)
        assert ind.triggered is True
        assert ind.metric_value == 4.0
        assert ind.severity == "medium"

    def test_very_high_leverage_high_severity(self):
        ind = _test_high_leverage(600000, 100000)
        assert ind.triggered is True
        assert ind.severity == "high"  # > 5.0

    def test_zero_equity_with_liabilities(self):
        ind = _test_high_leverage(300000, 0.0)
        assert ind.triggered is True
        assert ind.severity == "high"
        assert "not calculable" in ind.description

    def test_zero_equity_zero_liabilities(self):
        ind = _test_high_leverage(0.0, 0.0)
        assert ind.triggered is False

    def test_negative_equity_triggered(self):
        ind = _test_high_leverage(500000, -100000)
        assert ind.triggered is True
        assert ind.severity == "high"
        assert "negative" in ind.description

    def test_threshold_value(self):
        ind = _test_high_leverage(400000, 100000)
        assert ind.threshold == LEVERAGE_THRESHOLD


# =============================================================================
# FULL COMPUTATION
# =============================================================================


class TestComputeGoingConcernProfile:
    """Tests for compute_going_concern_profile()."""

    def test_healthy_company(self):
        report = compute_going_concern_profile(
            total_assets=1000000,
            total_liabilities=400000,
            total_equity=600000,
            current_assets=300000,
            current_liabilities=150000,
            total_revenue=800000,
            total_expenses=700000,
        )
        assert report.indicators_triggered == 0
        assert report.indicators_checked == 5  # No prior → 5 tests (skips revenue decline)
        assert report.prior_period_available is False
        assert "No going concern indicators triggered" in report.narrative

    def test_distressed_company(self):
        report = compute_going_concern_profile(
            total_assets=300000,
            total_liabilities=500000,
            total_equity=-200000,
            current_assets=50000,
            current_liabilities=200000,
            total_revenue=200000,
            total_expenses=400000,
        )
        assert report.indicators_triggered >= 4  # Net liability, current ratio, neg WC, losses, leverage
        assert report.indicators_checked == 5

    def test_with_prior_period(self):
        report = compute_going_concern_profile(
            total_assets=1000000,
            total_liabilities=400000,
            total_equity=600000,
            current_assets=300000,
            current_liabilities=150000,
            total_revenue=800000,
            total_expenses=700000,
            prior_revenue=900000,
            prior_expenses=800000,
        )
        assert report.prior_period_available is True
        assert report.indicators_checked == 6  # All 6 tests run

    def test_revenue_decline_with_prior(self):
        report = compute_going_concern_profile(
            total_assets=1000000,
            total_liabilities=400000,
            total_equity=600000,
            current_assets=300000,
            current_liabilities=150000,
            total_revenue=600000,
            total_expenses=500000,
            prior_revenue=900000,
            prior_expenses=800000,
        )
        rev_ind = [i for i in report.indicators if i.indicator_name == "Revenue Decline"]
        assert len(rev_ind) == 1
        assert rev_ind[0].triggered is True

    def test_all_zeros_empty_report(self):
        report = compute_going_concern_profile(
            total_assets=0, total_liabilities=0, total_equity=0,
            current_assets=0, current_liabilities=0,
            total_revenue=0, total_expenses=0,
        )
        assert "No financial data" in report.narrative
        assert report.indicators_checked == 0

    def test_to_dict_serialization(self):
        report = compute_going_concern_profile(
            total_assets=1000000,
            total_liabilities=400000,
            total_equity=600000,
            current_assets=300000,
            current_liabilities=150000,
            total_revenue=800000,
            total_expenses=700000,
        )
        d = report.to_dict()
        assert "indicators" in d
        assert "indicators_triggered" in d
        assert "indicators_checked" in d
        assert "narrative" in d
        assert "disclaimer" in d
        assert isinstance(d["indicators"], list)

    def test_disclaimer_present(self):
        report = compute_going_concern_profile(
            total_assets=1000000,
            total_liabilities=400000,
            total_equity=600000,
            current_assets=300000,
            current_liabilities=150000,
            total_revenue=800000,
            total_expenses=700000,
        )
        assert report.disclaimer == DISCLAIMER
        assert "ISA 570" in report.disclaimer
        assert "professional judgment" in report.disclaimer

    def test_narrative_with_triggered_indicators(self):
        report = compute_going_concern_profile(
            total_assets=300000,
            total_liabilities=500000,
            total_equity=-200000,
            current_assets=50000,
            current_liabilities=200000,
            total_revenue=200000,
            total_expenses=400000,
        )
        assert "indicator(s) triggered" in report.narrative
        assert "Net Liability Position" in report.narrative

    def test_narrative_without_prior_period(self):
        report = compute_going_concern_profile(
            total_assets=1000000,
            total_liabilities=400000,
            total_equity=600000,
            current_assets=300000,
            current_liabilities=150000,
            total_revenue=800000,
            total_expenses=700000,
        )
        assert "Prior period data not available" in report.narrative

    def test_consecutive_losses_high_severity(self):
        report = compute_going_concern_profile(
            total_assets=1000000,
            total_liabilities=400000,
            total_equity=600000,
            current_assets=300000,
            current_liabilities=150000,
            total_revenue=300000,
            total_expenses=500000,
            prior_revenue=400000,
            prior_expenses=600000,
        )
        loss_ind = [i for i in report.indicators if i.indicator_name == "Recurring Losses"]
        assert len(loss_ind) == 1
        assert loss_ind[0].triggered is True
        assert loss_ind[0].severity == "high"

    def test_indicator_to_dict_structure(self):
        report = compute_going_concern_profile(
            total_assets=300000,
            total_liabilities=500000,
            total_equity=-200000,
            current_assets=50000,
            current_liabilities=200000,
            total_revenue=200000,
            total_expenses=400000,
        )
        d = report.to_dict()
        ind = d["indicators"][0]
        assert "indicator_name" in ind
        assert "triggered" in ind
        assert "severity" in ind
        assert "description" in ind
