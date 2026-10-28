"""W-2 / W-3 reconciliation generators (Sprint 823 item 3) — 5 generators.

Injected amounts are chosen against the engine's own statutory table for the
baseline year (``statutory_limits_for_year``), never against a figure typed
here, so the generators stay valid when Sprint 793b changes a value.
"""

from decimal import Decimal

from tests.anomaly_framework.fixtures.base_config_tools import w2_baseline
from tests.anomaly_framework.generators.config_tool_base import ConfigGenerator, ToolHarness
from w2_reconciliation_engine import reconcile_w2, statutory_limits_for_year

W2_HARNESS = ToolHarness(
    tool="w2_reconciliation",
    engine="w2_reconciliation_engine.reconcile_w2",
    baseline=w2_baseline,
    run=lambda config: reconcile_w2(config).to_dict(),
)


def _has_kind(result: dict, kind: str, employee_id: str) -> bool:
    return any(d["kind"] == kind and d["employee_id"] == employee_id for d in result["employee_discrepancies"])


class W2SsWageBaseExceededGenerator(ConfigGenerator):
    """Box 3 reports Social Security wages above the year's wage base."""

    name = "w2_ss_wage_base_exceeded"
    target = "employee_discrepancies[kind=ss_wage_base_exceeded]"
    injected_at = "E1 payroll and Box 3 SS wages set to the wage base + $10,000"

    def mutate(self, config):
        over = statutory_limits_for_year(config.tax_year).ss_wage_base + Decimal("10000")
        config.employees[0].ss_wages = over
        config.w2_drafts[0].box_3_ss_wages = over

    def detected(self, result):
        return _has_kind(result, "ss_wage_base_exceeded", "E1")


class W2HsaOverLimitGenerator(ConfigGenerator):
    """Box 12 code W exceeds the self-only HSA limit."""

    name = "w2_hsa_over_limit"
    target = "employee_discrepancies[kind=hsa_over_limit]"
    injected_at = "E1 HSA contributions set to the self-only limit + $500"

    def mutate(self, config):
        over = statutory_limits_for_year(config.tax_year).hsa_self_only + Decimal("500")
        config.employees[0].hsa_contributions = over
        config.w2_drafts[0].box_12_code_w_hsa = over

    def detected(self, result):
        return _has_kind(result, "hsa_over_limit", "E1")


class W2ElectiveDeferralOverLimitGenerator(ConfigGenerator):
    """A 35-year-old's 401(k) deferral exceeds the elective limit (no catch-up)."""

    name = "w2_401k_over_limit"
    target = "employee_discrepancies[kind=retirement_over_limit]"
    injected_at = "E2 (age 35) 401(k) deferral set to the elective limit + $1,000"

    def mutate(self, config):
        over = statutory_limits_for_year(config.tax_year).limit_401k_elective + Decimal("1000")
        config.employees[1].retirement_401k = over
        config.w2_drafts[1].box_12_code_d_401k = over

    def detected(self, result):
        return _has_kind(result, "retirement_over_limit", "E2")


class W2FederalWithholdingMismatchGenerator(ConfigGenerator):
    """Draft Box 2 disagrees with payroll by $750."""

    name = "w2_federal_withholding_mismatch"
    target = "employee_discrepancies[kind=federal_withholding]"
    injected_at = "E2 Box 2 = payroll federal withholding − $750"

    def mutate(self, config):
        config.w2_drafts[1].box_2_federal_withholding -= Decimal("750")

    def detected(self, result):
        return _has_kind(result, "federal_withholding", "E2")


class W2Form941MismatchGenerator(ConfigGenerator):
    """One quarter's 941 under-reports wages by $5,000."""

    name = "w2_form_941_mismatch"
    target = "form_941_mismatches[kind=federal_wages]"
    injected_at = "Q3 941 line 2 wages − $5,000"

    def mutate(self, config):
        config.form_941_quarters[2].total_federal_wages -= Decimal("5000")

    def detected(self, result):
        return any(
            m["kind"] == "federal_wages" and Decimal(m["difference"]) == Decimal("-5000")
            for m in result["form_941_mismatches"]
        )


W2_REGISTRY = [
    W2SsWageBaseExceededGenerator(),
    W2HsaOverLimitGenerator(),
    W2ElectiveDeferralOverLimitGenerator(),
    W2FederalWithholdingMismatchGenerator(),
    W2Form941MismatchGenerator(),
]
