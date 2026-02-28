"""
Sprint 293: Cash Conversion Cycle — DPO + DIO + CCC

Tests:
- DPO calculation and thresholds
- DIO calculation and thresholds
- CCC composition (DIO + DSO - DPO)
- AP extraction in extract_category_totals
- Zero COGS guard, negative CCC, edge cases
"""

import pytest

from ratio_engine import (
    CategoryTotals,
    RatioEngine,
    extract_category_totals,
)

# ═══════════════════════════════════════════════════════════════
# DPO Tests
# ═══════════════════════════════════════════════════════════════


class TestDaysPayableOutstanding:
    """Test DPO = (AP / COGS) × 365."""

    def test_dpo_basic(self):
        """Standard DPO calculation."""
        totals = CategoryTotals(accounts_payable=20000, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        result = engine.calculate_dpo()
        assert result.is_calculable is True
        assert result.value == pytest.approx(73.0, abs=0.1)

    def test_dpo_zero_cogs(self):
        """DPO not calculable when COGS is zero."""
        totals = CategoryTotals(accounts_payable=20000, cost_of_goods_sold=0)
        engine = RatioEngine(totals)
        result = engine.calculate_dpo()
        assert result.is_calculable is False
        assert result.value is None

    def test_dpo_zero_ap(self):
        """DPO is 0 when no AP identified."""
        totals = CategoryTotals(accounts_payable=0, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        result = engine.calculate_dpo()
        assert result.is_calculable is True
        assert result.value == 0.0

    def test_dpo_rapid_payment(self):
        """DPO ≤ 30 → 'Rapid payment cycle'."""
        totals = CategoryTotals(accounts_payable=5000, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        result = engine.calculate_dpo()
        assert result.value <= 30
        assert result.threshold_status == "above_threshold"

    def test_dpo_extended(self):
        """DPO > 60 → 'Extended payment cycle'."""
        totals = CategoryTotals(accounts_payable=25000, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        result = engine.calculate_dpo()
        # 25000/100000 * 365 = 91.25
        assert result.value > 60
        assert result.threshold_status in ("at_threshold", "below_threshold")


# ═══════════════════════════════════════════════════════════════
# DIO Tests
# ═══════════════════════════════════════════════════════════════


class TestDaysInventoryOutstanding:
    """Test DIO = (Inventory / COGS) × 365."""

    def test_dio_basic(self):
        """Standard DIO calculation."""
        totals = CategoryTotals(inventory=15000, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        result = engine.calculate_dio()
        assert result.is_calculable is True
        assert result.value == pytest.approx(54.75, abs=0.1)

    def test_dio_zero_cogs(self):
        """DIO not calculable when COGS is zero."""
        totals = CategoryTotals(inventory=15000, cost_of_goods_sold=0)
        engine = RatioEngine(totals)
        result = engine.calculate_dio()
        assert result.is_calculable is False
        assert result.value is None

    def test_dio_zero_inventory(self):
        """DIO is 0 when no inventory."""
        totals = CategoryTotals(inventory=0, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        result = engine.calculate_dio()
        assert result.is_calculable is True
        assert result.value == 0.0

    def test_dio_rapid_turnover(self):
        """DIO ≤ 30 → 'Rapid inventory turnover'."""
        totals = CategoryTotals(inventory=5000, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        result = engine.calculate_dio()
        assert result.value <= 30
        assert result.threshold_status == "above_threshold"

    def test_dio_extended(self):
        """DIO > 90 → 'Significantly extended inventory holding period'."""
        totals = CategoryTotals(inventory=30000, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        result = engine.calculate_dio()
        # 30000/100000 * 365 = 109.5
        assert result.value > 90
        assert result.threshold_status == "below_threshold"


# ═══════════════════════════════════════════════════════════════
# CCC Tests
# ═══════════════════════════════════════════════════════════════


class TestCashConversionCycle:
    """Test CCC = DIO + DSO - DPO."""

    def test_ccc_basic(self):
        """Standard CCC with all components."""
        totals = CategoryTotals(
            accounts_receivable=20000,
            inventory=15000,
            accounts_payable=10000,
            total_revenue=200000,
            cost_of_goods_sold=100000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_ccc()
        # DSO = 20000/200000 * 365 = 36.5
        # DIO = 15000/100000 * 365 = 54.75
        # DPO = 10000/100000 * 365 = 36.5
        # CCC = 54.75 + 36.5 - 36.5 = 54.75
        assert result.is_calculable is True
        assert result.value == pytest.approx(54.75, abs=0.5)

    def test_ccc_negative(self):
        """CCC negative when DPO > DIO + DSO (common in retail)."""
        totals = CategoryTotals(
            accounts_receivable=5000,
            inventory=5000,
            accounts_payable=50000,
            total_revenue=200000,
            cost_of_goods_sold=100000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_ccc()
        # DSO = 5000/200000 * 365 = 9.125
        # DIO = 5000/100000 * 365 = 18.25
        # DPO = 50000/100000 * 365 = 182.5
        # CCC = 18.25 + 9.125 - 182.5 = -155.125
        assert result.is_calculable is True
        assert result.value < 0

    def test_ccc_no_revenue(self):
        """CCC not calculable when no revenue (DSO unavailable)."""
        totals = CategoryTotals(
            inventory=15000,
            accounts_payable=10000,
            total_revenue=0,
            cost_of_goods_sold=100000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_ccc()
        assert result.is_calculable is False

    def test_ccc_display_value(self):
        """CCC display value shows days."""
        totals = CategoryTotals(
            accounts_receivable=20000,
            total_revenue=200000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_ccc()
        assert "days" in result.display_value

    def test_ccc_short_cycle(self):
        """CCC 0-30 days → 'Short cash cycle'."""
        totals = CategoryTotals(
            accounts_receivable=10000,
            inventory=5000,
            accounts_payable=8000,
            total_revenue=200000,
            cost_of_goods_sold=100000,
        )
        engine = RatioEngine(totals)
        result = engine.calculate_ccc()
        # DSO = 10000/200000*365 = 18.25; DIO = 18.25; DPO = 29.2 → CCC ≈ 7.3
        assert result.value is not None
        assert result.value <= 30
        assert "Short" in result.interpretation


# ═══════════════════════════════════════════════════════════════
# AP Extraction Tests
# ═══════════════════════════════════════════════════════════════


class TestAPExtraction:
    """Test accounts payable extraction in extract_category_totals."""

    def test_accounts_payable_extracted(self):
        """'Accounts Payable' should be extracted."""
        balances = {"Accounts Payable": {"debit": 0, "credit": 50000}}
        classified = {"Accounts Payable": "liability"}
        totals = extract_category_totals(balances, classified)
        assert totals.accounts_payable > 0

    def test_trade_payables_extracted(self):
        """'Trade Payables' should be extracted."""
        balances = {"Trade Payables": {"debit": 0, "credit": 30000}}
        classified = {"Trade Payables": "liability"}
        totals = extract_category_totals(balances, classified)
        assert totals.accounts_payable > 0

    def test_notes_payable_excluded(self):
        """'Notes Payable' should NOT be extracted as AP."""
        balances = {"Notes Payable": {"debit": 0, "credit": 100000}}
        classified = {"Notes Payable": "liability"}
        totals = extract_category_totals(balances, classified)
        assert totals.accounts_payable == 0

    def test_ap_in_category_totals_dict(self):
        """accounts_payable should appear in to_dict output."""
        totals = CategoryTotals(accounts_payable=25000)
        d = totals.to_dict()
        assert "accounts_payable" in d
        assert d["accounts_payable"] == 25000

    def test_ap_from_dict_round_trip(self):
        """accounts_payable survives to_dict → from_dict round trip."""
        original = CategoryTotals(accounts_payable=25000)
        d = original.to_dict()
        restored = CategoryTotals.from_dict(d)
        assert restored.accounts_payable == 25000


# ═══════════════════════════════════════════════════════════════
# Integration: New ratios in calculate_all_ratios
# ═══════════════════════════════════════════════════════════════


class TestAllRatiosIncludesNewMetrics:
    """Verify DPO, DIO, CCC appear in calculate_all_ratios."""

    def test_all_ratios_includes_dpo(self):
        totals = CategoryTotals(accounts_payable=10000, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        ratios = engine.calculate_all_ratios()
        assert "dpo" in ratios

    def test_all_ratios_includes_dio(self):
        totals = CategoryTotals(inventory=10000, cost_of_goods_sold=100000)
        engine = RatioEngine(totals)
        ratios = engine.calculate_all_ratios()
        assert "dio" in ratios

    def test_all_ratios_includes_ccc(self):
        totals = CategoryTotals(total_revenue=100000)
        engine = RatioEngine(totals)
        ratios = engine.calculate_all_ratios()
        assert "ccc" in ratios

    def test_ratio_count_now_seventeen(self):
        """Should now have 17 ratios total (12 original + 5 structural)."""
        totals = CategoryTotals()
        engine = RatioEngine(totals)
        ratios = engine.calculate_all_ratios()
        assert len(ratios) == 17
