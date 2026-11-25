"""Sprint 898 (council 2026-11-25, Accounting Expert): A-F3, A-F6, A-F8, A-F9, A-F10.

Each class pins one defect the council reported and that was confirmed in the code:

- A-F3: ISA 530 requirement paragraphs end at 15. The memo cited "ISA 530.17" (no such
  paragraph), "ISA 530.14" for evaluation (14 is projection; 15 is evaluation),
  "ISA 320.11" for tolerable misstatement (defined in ISA 530), and "ISA 530.A4"
  (not verified, so dropped).
- A-F6: the memo said MUS "was applied in accordance with ISA 530 and PCAOB AS 2315";
  the tool cannot attest compliance.
- A-F8: going concern counted negative equity twice, and called one loss "recurring".
- A-F9: a profitable entity with negative equity got "Negative ROE - equity generating losses".
- A-F10: the SOCE keyword "oci" matched inside "Associates' Capital".
"""

from __future__ import annotations

import inspect

import pytest

import sampling_memo_generator
from financial_statement_builder import FinancialStatementBuilder
from going_concern_engine import compute_going_concern_profile
from ratio_engine import CategoryTotals, RatioEngine


class TestSamplingMemoCitations:
    SOURCE = inspect.getsource(sampling_memo_generator)

    @pytest.mark.parametrize("bad", ["ISA 530.17", "ISA 530.14", "ISA 320.11", "ISA 530.A4"])
    def test_wrong_paragraphs_gone(self, bad):
        assert bad not in self.SOURCE

    def test_evaluation_cites_530_15(self):
        assert "ISA 530.15" in self.SOURCE

    def test_no_compliance_attestation(self):
        assert "in accordance with ISA" not in self.SOURCE
        assert "designed with reference to" in self.SOURCE

    def test_tolerable_misstatement_attributed_to_isa_530(self):
        assert "ISA 530 defines" in self.SOURCE


def _gc(**overrides):
    base = dict(
        total_assets=300_000.0,
        total_liabilities=500_000.0,
        total_equity=-200_000.0,
        current_assets=100_000.0,
        current_liabilities=50_000.0,
        total_revenue=400_000.0,
        total_expenses=350_000.0,
    )
    base.update(overrides)
    return compute_going_concern_profile(**base)


def _ind(report, name):
    found = [i for i in report.indicators if i.indicator_name == name]
    return found[0] if found else None


class TestGoingConcernNoDoubleCount:
    def test_negative_equity_counted_once(self):
        report = _gc()
        assert _ind(report, "Net Liability Position").triggered is True
        leverage = _ind(report, "High Leverage")
        assert leverage.triggered is False
        assert "Net Liability Position" in leverage.description
        assert report.indicators_triggered == sum(1 for i in report.indicators if i.triggered)
        assert "High Leverage" not in report.narrative

    def test_leverage_still_fires_on_positive_equity(self):
        report = _gc(total_assets=1_000_000.0, total_liabilities=900_000.0, total_equity=100_000.0)
        assert _ind(report, "High Leverage").triggered is True
        assert _ind(report, "Net Liability Position").triggered is False


class TestSinglePeriodLossIsNotRecurring:
    def test_single_period_loss_is_net_loss(self):
        report = _gc(
            total_assets=1_000_000.0,
            total_liabilities=400_000.0,
            total_equity=600_000.0,
            total_revenue=300_000.0,
            total_expenses=500_000.0,
        )
        assert _ind(report, "Recurring Losses") is None
        loss = _ind(report, "Net Loss")
        assert loss.triggered is True
        assert loss.threshold_proximity == "medium"
        assert "recurrence cannot be assessed" in loss.description

    def test_loss_after_profitable_prior_is_net_loss(self):
        report = _gc(
            total_assets=1_000_000.0,
            total_liabilities=400_000.0,
            total_equity=600_000.0,
            total_revenue=300_000.0,
            total_expenses=500_000.0,
            prior_revenue=600_000.0,
            prior_expenses=500_000.0,
        )
        assert _ind(report, "Recurring Losses") is None
        assert _ind(report, "Net Loss").triggered is True

    def test_two_period_loss_is_recurring(self):
        report = _gc(
            total_assets=1_000_000.0,
            total_liabilities=400_000.0,
            total_equity=600_000.0,
            total_revenue=300_000.0,
            total_expenses=500_000.0,
            prior_revenue=400_000.0,
            prior_expenses=600_000.0,
        )
        rec = _ind(report, "Recurring Losses")
        assert rec.triggered is True and rec.threshold_proximity == "high"


class TestRoeOnNegativeEquity:
    def _roe(self, revenue, expenses):
        # Closed books: assets - liabilities = equity.
        totals = CategoryTotals(
            total_assets=300_000.0,
            total_liabilities=500_000.0,
            total_equity=-200_000.0,
            total_revenue=revenue,
            total_expenses=expenses,
        )
        return RatioEngine(totals).calculate_return_on_equity()

    def test_profitable_entity_not_called_loss_making(self):
        result = self._roe(400_000.0, 350_000.0)
        assert "generating losses" not in result.interpretation
        assert result.interpretation.startswith("Not meaningful: net income on negative equity")
        assert result.threshold_status == "below_threshold"

    def test_loss_making_entity(self):
        result = self._roe(300_000.0, 350_000.0)
        assert result.interpretation.startswith("Not meaningful: net loss on negative equity")


class TestSoceOciWordBoundary:
    @pytest.mark.parametrize(
        "name",
        ["Associates' Capital", "Social Club Reserve", "Associates Capital Account"],
    )
    def test_oci_inside_a_word_is_not_aoci(self, name):
        component, _label, _explicit = FinancialStatementBuilder._classify_equity_account(name)
        assert component != "aoci"

    @pytest.mark.parametrize(
        "name",
        [
            "OCI - Translation Reserve",
            "Accumulated OCI",
            "AOCI",
            "Reserve (OCI)",
            "Accumulated other comprehensive income",
        ],
    )
    def test_real_oci_accounts_still_map(self, name):
        component, _label, explicit = FinancialStatementBuilder._classify_equity_account(name)
        assert component == "aoci" and explicit is True

    def test_apic_abbreviation_whole_word(self):
        assert FinancialStatementBuilder._classify_equity_account("APIC")[0] == "additional_paid_in_capital"
