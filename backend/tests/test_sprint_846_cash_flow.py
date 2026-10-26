"""Sprint 846 — cash flow projector loose ends from the Sprint 823 register (C2, C3, C5, C6)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from cash_flow_projector_engine import (
    AP_DEFERRAL_DAYS,
    AgingBuckets,
    CashFlowConfig,
    CashFlowInputError,
    RecurringFlow,
    project_cash_flow,
)

START = date.today()


def _sum(values) -> Decimal:
    return sum((Decimal(v) for v in values), Decimal("0"))


def test_ap_left_unpaid_in_a_scenario_is_deferred_not_dropped():
    """C2: base pays 80% of over-90 AP on schedule. The other 20% used to vanish,
    so the projection paid $8,000 of a $10,000 bill and ended $2,000 rich."""
    config = CashFlowConfig(
        opening_balance=Decimal("50000"),
        start_date=START,
        ap_aging=AgingBuckets(days_over_90=Decimal("10000")),
    )
    forecast = project_cash_flow(config)

    for name in ("base", "stress", "best"):
        daily = forecast.scenarios[name].daily
        assert _sum(p.ap_outflow for p in daily) == Decimal("10000.00"), name
        assert daily[-1].ending_balance == Decimal("40000.00"), name

    base = forecast.scenarios["base"]
    # The deferred 20% is paid in the window right after the scheduled one (days 0-4).
    deferred_window = base.daily[5 : 5 + AP_DEFERRAL_DAYS]
    assert _sum(p.ap_outflow for p in deferred_window) == Decimal("2000.00")
    assert base.ap_deferral_rule is not None
    candidate = base.ap_deferral_candidates[0]
    assert candidate["paid_between_days"] == [5, 5 + AP_DEFERRAL_DAYS - 1]
    # Stress defers nothing, so it states no rule.
    assert forecast.scenarios["stress"].ap_deferral_rule is None


def test_displayed_rows_foot_to_the_cent():
    """C3: each field was rounded on its own, so components did not add to the
    net change and the net change did not roll the balance forward."""
    config = CashFlowConfig(
        opening_balance=Decimal("1000.005"),
        start_date=START,
        ar_aging=AgingBuckets(current=Decimal("1000"), days_1_30=Decimal("777.77"), days_over_90=Decimal("333.33")),
        ap_aging=AgingBuckets(current=Decimal("1234.56"), days_31_60=Decimal("999.99")),
        recurring_flows=[
            RecurringFlow("Rent", Decimal("-333.333"), "monthly", START),
            RecurringFlow("Sub", Decimal("10.005"), "weekly", START + timedelta(days=2)),
        ],
    )
    forecast = project_cash_flow(config)
    opening = Decimal(forecast.inputs["opening_balance"])

    for name, scenario in forecast.scenarios.items():
        previous = opening
        cum_in = cum_out = Decimal("0")
        for p in scenario.daily:
            assert p.ar_inflow - p.ap_outflow + p.recurring_net == p.net_change, (name, p.day_index)
            assert previous + p.net_change == p.ending_balance, (name, p.day_index)
            previous = p.ending_balance
            cum_in += p.ar_inflow + max(p.recurring_net, Decimal("0"))
            cum_out += p.ap_outflow + max(-p.recurring_net, Decimal("0"))
            summary = scenario.horizon.get(p.day_index + 1)
            if summary is not None:
                assert summary.cumulative_inflow == cum_in, (name, summary.day)
                assert summary.cumulative_outflow == cum_out, (name, summary.day)
                assert summary.ending_balance == p.ending_balance
                assert opening + cum_in - cum_out == summary.ending_balance


@pytest.mark.parametrize("side", ["ar_aging", "ap_aging"])
def test_negative_aging_bucket_is_refused(side):
    """C5: a negative bucket was netted into ar_total/ap_total but skipped by the
    projection, so the stated total and the projected cash disagreed."""
    kwargs = {side: AgingBuckets(current=Decimal("5000"), days_1_30=Decimal("-500"))}
    with pytest.raises(CashFlowInputError, match="cannot be negative"):
        project_cash_flow(CashFlowConfig(opening_balance=Decimal("1000"), start_date=START, **kwargs))


def test_overdrawn_opening_balance_is_projected():
    """C6: an overdrawn account is exactly when a cash forecast matters."""
    config = CashFlowConfig(
        opening_balance=Decimal("-5000"),
        start_date=START,
        ar_aging=AgingBuckets(current=Decimal("30000")),
    )
    forecast = project_cash_flow(config)
    assert forecast.inputs["opening_balance"] == "-5000.00"
    base = forecast.scenarios["base"]
    assert base.goes_negative is True
    assert base.first_negative_day == 0
    assert base.daily[-1].ending_balance == Decimal("23500.00")
