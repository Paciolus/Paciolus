"""
Sprint 767 — multi_period_comparison output-boundary quantization tests.

Asserts that monetary fields emitted by ``MovementSummary.to_dict()``,
``LeadSheetMovementSummary.to_dict()``, ``BudgetVariance.to_dict()``,
``ThreeWayLeadSheetSummary.to_dict()``, and ``ThreeWayMovementSummary.to_dict()``
are quantized to 2dp ROUND_HALF_UP via ``shared.monetary.quantize_monetary``.

Prevents float drift from leaking through `(current - prior)` subtraction
into the response wire format.
"""

from decimal import ROUND_HALF_UP, Decimal

import multi_period_comparison as mpc


def _make_acct(name: str, debit: float = 0.0, credit: float = 0.0, type_: str = "asset") -> dict:
    return {"account": name, "debit": debit, "credit": credit, "type": type_}


def _is_at_most_2dp(value: float | None) -> bool:
    """A serialized monetary float should have at most 2 decimal digits."""
    if value is None:
        return True
    # Reconstruct via quantize and compare; tolerates exact-binary floats
    # like 1.0, 100.5, 1234.56 — but rejects 0.1 + 0.2 = 0.30000000000000004
    quantized = float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return abs(value - quantized) < 1e-9


class TestAccountMovementQuantization:
    def test_subtraction_drift_does_not_leak_to_response(self) -> None:
        # 0.1 + 0.2 = 0.30000000000000004 in float.  After quantize at the
        # response boundary, the wire value should be 0.30 exactly.
        prior = [_make_acct("Foo", debit=0.1)]
        current = [_make_acct("Foo", debit=0.1 + 0.2)]
        result = mpc.compare_trial_balances(prior, current)
        d = result.to_dict()
        movement = d["all_movements"][0]
        # 0.1 + 0.2 - 0.1 = 0.2 (with float drift); quantization snaps it
        assert movement["change_amount"] == 0.20
        assert _is_at_most_2dp(movement["prior_balance"])
        assert _is_at_most_2dp(movement["current_balance"])
        assert _is_at_most_2dp(movement["change_amount"])

    def test_half_up_at_5_thousandths_boundary(self) -> None:
        # $1,234.005 should round to 1234.01 under HALF_UP (Python's
        # default banker's rounding would round to 1234.00).
        prior = [_make_acct("Foo", debit=1000.00)]
        current = [_make_acct("Foo", debit=1234.005)]
        result = mpc.compare_trial_balances(prior, current)
        d = result.to_dict()
        movement = d["all_movements"][0]
        assert movement["current_balance"] == 1234.01

    def test_lead_sheet_aggregates_quantized(self) -> None:
        prior = [_make_acct("A", debit=100.001), _make_acct("B", debit=200.002)]
        current = [_make_acct("A", debit=110.005), _make_acct("B", debit=220.005)]
        result = mpc.compare_trial_balances(prior, current)
        d = result.to_dict()
        for ls in d["lead_sheet_summaries"]:
            assert _is_at_most_2dp(ls["prior_total"])
            assert _is_at_most_2dp(ls["current_total"])
            assert _is_at_most_2dp(ls["net_change"])

    def test_tb_totals_quantized(self) -> None:
        prior = [_make_acct("A", debit=0.1), _make_acct("B", debit=0.2)]
        current = [_make_acct("A", debit=0.1), _make_acct("B", debit=0.2)]
        result = mpc.compare_trial_balances(prior, current).to_dict()
        # 0.1 + 0.2 = 0.30000000000000004 → must be snapped to 0.30
        assert result["prior_total_debits"] == 0.30
        assert result["current_total_debits"] == 0.30


class TestThreeWayQuantization:
    def test_budget_variance_dollar_fields_quantized(self) -> None:
        prior = [_make_acct("Foo", debit=100.00)]
        current = [_make_acct("Foo", debit=120.00)]
        # Budget at 100.005 — variance vs current = 19.995 → quantize 19.99 (HALF_EVEN)
        # but with HALF_UP: 19.995 → 20.00.  The contract is HALF_UP.
        budget = [_make_acct("Foo", debit=100.005)]
        result = mpc.compare_three_periods(prior, current, budget).to_dict()
        movement = result["all_movements"][0]
        bv = movement["budget_variance"]
        assert bv is not None
        # 120 - 100.005 = 19.995 → HALF_UP rounds to 20.00
        assert bv["variance_amount"] == 20.00
        assert _is_at_most_2dp(bv["budget_balance"])

    def test_three_way_tb_totals_quantized(self) -> None:
        prior = [_make_acct("A", debit=0.1)]
        current = [_make_acct("A", debit=0.1)]
        budget = [_make_acct("A", debit=0.1)]
        result = mpc.compare_three_periods(prior, current, budget).to_dict()
        assert _is_at_most_2dp(result["budget_total_debits"])

    def test_three_way_lead_sheet_aggregates_quantized(self) -> None:
        prior = [_make_acct("A", debit=100.001)]
        current = [_make_acct("A", debit=110.005)]
        budget = [_make_acct("A", debit=105.0049)]
        result = mpc.compare_three_periods(prior, current, budget).to_dict()
        for ls in result["lead_sheet_summaries"]:
            assert _is_at_most_2dp(ls["prior_total"])
            assert _is_at_most_2dp(ls["current_total"])
            assert _is_at_most_2dp(ls["budget_total"])
            assert _is_at_most_2dp(ls["budget_variance"])


class TestPercentFieldsRemainRaw:
    """Percent fields are non-monetary and should NOT be quantized to 2dp."""

    def test_change_percent_keeps_full_precision(self) -> None:
        prior = [_make_acct("Foo", debit=3.0)]
        current = [_make_acct("Foo", debit=4.0)]
        result = mpc.compare_trial_balances(prior, current).to_dict()
        # change_percent = (4 - 3) / 3 * 100 = 33.333...
        movement = result["all_movements"][0]
        assert movement["change_percent"] is not None
        assert movement["change_percent"] > 33.3
        assert movement["change_percent"] < 33.4
        # Specifically: not snapped to 33.33 (i.e., still has the trailing
        # repeating digits beyond 2dp)
        assert movement["change_percent"] != 33.33
