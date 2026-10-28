"""Cash flow projector generators (Sprint 823 item 3) — 4 generators.

Checks read the ``base`` scenario. Baseline: $500,000 opening cash, $200,000
current AR, $100,000 current AP, a $60,000 monthly payroll, $100,000 minimum
safe cash — positive throughout, no breach, no deferrable AP.
"""

from decimal import Decimal

from cash_flow_projector_engine import AgingBuckets, RecurringFlow, project_cash_flow
from tests.anomaly_framework.fixtures.base_config_tools import cash_flow_baseline
from tests.anomaly_framework.generators.config_tool_base import ConfigGenerator, ToolHarness

CASH_FLOW_HARNESS = ToolHarness(
    tool="cash_flow_projector",
    engine="cash_flow_projector_engine.project_cash_flow",
    baseline=cash_flow_baseline,
    run=lambda config: project_cash_flow(config).to_dict(),
)


def _base(result: dict) -> dict:
    return result["scenarios"]["base"]


class CashFlowGoesNegativeGenerator(ConfigGenerator):
    """A weekly $100,000 outflow exhausts cash inside the horizon."""

    name = "cf_goes_negative"
    target = "scenarios.base.goes_negative"
    injected_at = "weekly recurring outflow of $100,000 from the start date"

    def mutate(self, config):
        config.recurring_flows.append(RecurringFlow("Debt service", Decimal("-100000"), "weekly", config.start_date))

    def detected(self, result):
        base = _base(result)
        return base["goes_negative"] and base["first_negative_day"] is not None


class CashFlowMinSafeCashBreachGenerator(ConfigGenerator):
    """Cash dips under the minimum safe balance without going negative."""

    name = "cf_min_safe_cash_breach"
    target = "scenarios.base.breach_min_safe_cash"
    injected_at = "opening balance cut to $150,000 (minimum safe cash $100,000)"

    def mutate(self, config):
        config.opening_balance = Decimal("150000")

    def detected(self, result):
        base = _base(result)
        return base["breach_min_safe_cash"] and not base["goes_negative"]


class CashFlowAgedReceivablesGenerator(ConfigGenerator):
    """Receivables over 90 days carry the most cash at risk, so they rank first."""

    name = "cf_aged_ar_priority"
    target = "scenarios.base.collection_priorities[0]"
    injected_at = "$150,000 of the AR moved to over-90"

    def mutate(self, config):
        config.ar_aging = AgingBuckets(current=Decimal("50000"), days_over_90=Decimal("150000"))

    def detected(self, result):
        priorities = _base(result)["collection_priorities"]
        return bool(priorities) and priorities[0]["bucket"] == "over-90"


class CashFlowAgedPayablesGenerator(ConfigGenerator):
    """Base-scenario assumptions pay over-90 AP at 80%, so it is a deferral candidate."""

    name = "cf_aged_ap_deferral"
    target = "scenarios.base.ap_deferral_candidates"
    injected_at = "all $100,000 of AP moved to over-90"

    def mutate(self, config):
        config.ap_aging = AgingBuckets(days_over_90=Decimal("100000"))

    def detected(self, result):
        return any(c["bucket"] == "over-90" for c in _base(result)["ap_deferral_candidates"])


CASH_FLOW_REGISTRY = [
    CashFlowGoesNegativeGenerator(),
    CashFlowMinSafeCashBreachGenerator(),
    CashFlowAgedReceivablesGenerator(),
    CashFlowAgedPayablesGenerator(),
]
