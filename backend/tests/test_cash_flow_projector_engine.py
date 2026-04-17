"""Sprint 633 — Cash Flow Projector engine tests."""

from datetime import date
from decimal import Decimal

from cash_flow_projector_engine import (
    FORECAST_DAYS,
    HORIZON_BUCKETS,
    SCENARIOS,
    AgingBuckets,
    CashFlowConfig,
    CashFlowInputError,
    RecurringFlow,
    ScenarioName,
    project_cash_flow,
)


def _basic_config(**overrides) -> CashFlowConfig:
    defaults = dict(
        opening_balance=Decimal("100000"),
        start_date=date(2026, 1, 1),
        ar_aging=AgingBuckets(
            current=Decimal("50000"),
            days_1_30=Decimal("20000"),
            days_31_60=Decimal("10000"),
            days_61_90=Decimal("5000"),
            days_over_90=Decimal("2000"),
        ),
        ap_aging=AgingBuckets(
            current=Decimal("30000"),
            days_1_30=Decimal("15000"),
            days_31_60=Decimal("5000"),
        ),
        recurring_flows=[
            RecurringFlow("Payroll", Decimal("-8000"), "biweekly", date(2026, 1, 7)),
            RecurringFlow("Rent", Decimal("-3000"), "monthly", date(2026, 1, 1)),
        ],
    )
    defaults.update(overrides)
    return CashFlowConfig(**defaults)


class TestProjectionShape:
    def test_forecast_spans_ninety_days_for_each_scenario(self):
        forecast = project_cash_flow(_basic_config())
        assert set(forecast.scenarios) == {"base", "stress", "best"}
        for scenario in forecast.scenarios.values():
            assert len(scenario.daily) == FORECAST_DAYS
            assert set(scenario.horizon.keys()) == set(HORIZON_BUCKETS)

    def test_horizon_buckets_reflect_cumulative_values(self):
        forecast = project_cash_flow(_basic_config())
        base = forecast.scenarios["base"]
        d30 = base.horizon[30]
        d60 = base.horizon[60]
        d90 = base.horizon[90]
        # Cumulative inflow is monotonically non-decreasing.
        assert Decimal(d30.cumulative_inflow) <= Decimal(d60.cumulative_inflow)
        assert Decimal(d60.cumulative_inflow) <= Decimal(d90.cumulative_inflow)


class TestScenarioOrdering:
    def test_best_ends_higher_than_base_which_ends_higher_than_stress(self):
        forecast = project_cash_flow(_basic_config())
        best_end = forecast.scenarios["best"].horizon[90].ending_balance
        base_end = forecast.scenarios["base"].horizon[90].ending_balance
        stress_end = forecast.scenarios["stress"].horizon[90].ending_balance
        assert Decimal(best_end) > Decimal(base_end) > Decimal(stress_end)


class TestOpeningBalanceEffect:
    def test_lower_opening_pushes_stress_negative(self):
        tight = _basic_config(opening_balance=Decimal("5000"))
        forecast = project_cash_flow(tight)
        assert forecast.scenarios["stress"].goes_negative is True
        assert forecast.scenarios["stress"].first_negative_day is not None

    def test_healthy_opening_stays_positive_on_base_scenario(self):
        flush = _basic_config(opening_balance=Decimal("500000"))
        forecast = project_cash_flow(flush)
        assert forecast.scenarios["base"].goes_negative is False


class TestCollectionPriorities:
    def test_highest_at_risk_bucket_ranks_first(self):
        config = _basic_config()
        forecast = project_cash_flow(config)
        priorities = forecast.scenarios["base"].collection_priorities
        assert priorities, "expected at least one priority bucket"
        # The over-90 bucket collects only 20% so the delta
        # outstanding - expected is the largest fraction.
        top = priorities[0]
        at_risk_top = Decimal(top.amount_outstanding) - Decimal(top.expected_collection)
        for other in priorities[1:]:
            assert at_risk_top >= (Decimal(other.amount_outstanding) - Decimal(other.expected_collection))


class TestAPDeferral:
    def test_stress_scenario_returns_no_deferral_candidates(self):
        forecast = project_cash_flow(_basic_config())
        assert forecast.scenarios["stress"].ap_deferral_candidates == []

    def test_best_scenario_surfaces_deferrable_buckets(self):
        forecast = project_cash_flow(_basic_config())
        assert forecast.scenarios["best"].ap_deferral_candidates


class TestMinSafeCashBreach:
    def test_breach_flag_fires_when_balance_dips_below_threshold(self):
        cfg = _basic_config(
            opening_balance=Decimal("10000"),
            min_safe_cash=Decimal("5000"),
        )
        forecast = project_cash_flow(cfg)
        assert forecast.scenarios["stress"].breach_min_safe_cash is True


class TestInputValidation:
    def test_negative_opening_balance_rejected(self):
        try:
            project_cash_flow(_basic_config(opening_balance=Decimal("-1")))
        except CashFlowInputError:
            return
        raise AssertionError("expected CashFlowInputError")


class TestScenarioAssumptions:
    def test_all_scenarios_present(self):
        assert set(SCENARIOS) == {
            ScenarioName.BASE,
            ScenarioName.STRESS,
            ScenarioName.BEST,
        }

    def test_base_ar_current_collection_high(self):
        assert SCENARIOS[ScenarioName.BASE].ar_current_collection >= Decimal("0.9")


class TestSerialisation:
    def test_to_dict_roundtrip(self):
        forecast = project_cash_flow(_basic_config())
        d = forecast.to_dict()
        assert set(d) == {"inputs", "scenarios", "horizon_days"}
        assert "base" in d["scenarios"]
        assert d["horizon_days"] == list(HORIZON_BUCKETS)
        # Daily points serialised as strings.
        first = d["scenarios"]["base"]["daily"][0]
        assert isinstance(first["ending_balance"], str)
