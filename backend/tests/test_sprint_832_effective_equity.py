"""Sprint 832 — equity-based ratios use equity including unclosed current-period earnings.

CEO-approved methodology change. Closing entries transfer net income to
retained earnings; on a trial balance that has not been closed, the period's
profit or loss still sits in revenue and expense accounts, so the equity
accounts alone exclude it. Before this sprint debt-to-equity, return on equity,
the equity ratio and the DuPont equity multiplier all used the equity accounts
alone (discovery TB: D/E 0.56 vs a true 0.48, ROE 16.5% vs 14.1%).

Fixture shapes (one balanced TB each, liabilities 300k, equity accounts 500k):
- profitable unclosed: revenue 600k, expenses 500k (+100k) -> assets 900k
- loss-making unclosed: revenue 400k, expenses 500k (-100k) -> assets 700k
- closed: earnings already in equity (600k), revenue/expense zero -> assets 900k
"""

from decimal import Decimal

import pytest

from audit.classification import validate_balance_sheet_equation
from ratio_engine import (
    CategoryTotals,
    RatioEngine,
    calculate_analytics,
    effective_equity,
    equity_basis_disclosure,
    extract_category_totals,
    unclosed_current_period_earnings,
)


def _profitable_unclosed() -> CategoryTotals:
    return CategoryTotals(
        total_assets=900_000,
        current_assets=400_000,
        total_liabilities=300_000,
        current_liabilities=150_000,
        total_equity=500_000,
        total_revenue=600_000,
        total_expenses=500_000,
    )


def _loss_unclosed() -> CategoryTotals:
    return CategoryTotals(
        total_assets=700_000,
        current_assets=300_000,
        total_liabilities=300_000,
        current_liabilities=150_000,
        total_equity=500_000,
        total_revenue=400_000,
        total_expenses=500_000,
    )


def _closed() -> CategoryTotals:
    return CategoryTotals(
        total_assets=900_000,
        current_assets=400_000,
        total_liabilities=300_000,
        current_liabilities=150_000,
        total_equity=600_000,
    )


# ── Profitable unclosed TB ───────────────────────────────────────────


class TestProfitableUnclosedTB:
    def test_debt_to_equity_includes_current_earnings(self):
        # Old: 300k / 500k = 0.60. New: 300k / (500k + 100k) = 0.50.
        assert RatioEngine(_profitable_unclosed()).calculate_debt_to_equity().value == pytest.approx(0.50)

    def test_return_on_equity_includes_current_earnings(self):
        # Old: 100k / 500k = 20.0%. New: 100k / 600k = 16.7%.
        assert RatioEngine(_profitable_unclosed()).calculate_return_on_equity().value == pytest.approx(16.7)

    def test_equity_ratio_includes_current_earnings(self):
        # Old: 500k / 900k = 0.56. New: 600k / 900k = 0.67.
        assert RatioEngine(_profitable_unclosed()).calculate_equity_ratio().value == pytest.approx(0.67)

    def test_dupont_equity_multiplier_includes_current_earnings(self):
        dupont = RatioEngine(_profitable_unclosed()).calculate_dupont()
        assert dupont is not None
        # Old: 900k / 500k = 1.8. New: 900k / 600k = 1.5.
        assert float(dupont.equity_multiplier) == pytest.approx(1.5)
        # Decomposition still reconciles to ROE on the same (ending, effective) basis.
        assert dupont.verification_matches is True
        assert float(dupont.decomposed_roe) == pytest.approx(100_000 / 600_000, abs=1e-4)

    def test_common_size_equity_pct_matches_equity_ratio(self):
        analytics = calculate_analytics(_profitable_unclosed())
        bs = analytics["common_size"]["balance_sheet"]
        assert bs["total_equity_pct"] == pytest.approx(66.7)
        assert bs["total_liabilities_pct"] + bs["total_equity_pct"] == pytest.approx(100.0, abs=0.1)

    def test_analytics_discloses_the_adjustment(self):
        analytics = calculate_analytics(_profitable_unclosed())
        assert analytics["equity_includes_current_earnings"] == 100_000.0
        assert analytics["effective_equity"] == 600_000.0
        assert "$100,000.00" in analytics["equity_basis_note"]
        assert "unclosed current-period earnings" in analytics["equity_basis_note"]
        # The public CategoryTotals field keeps its meaning: equity accounts as they stand.
        assert Decimal(analytics["category_totals"]["total_equity"]) == Decimal("500000.00")


# ── Loss-making unclosed TB ──────────────────────────────────────────


class TestLossMakingUnclosedTB:
    def test_debt_to_equity_goes_up(self):
        old_value = 300_000 / 500_000  # 0.60 — equity accounts alone overstate equity by the loss
        value = RatioEngine(_loss_unclosed()).calculate_debt_to_equity().value
        assert value == pytest.approx(0.75)  # 300k / (500k − 100k)
        assert value > old_value

    def test_return_on_equity_uses_reduced_equity(self):
        # Old: −100k / 500k = −20.0%. New: −100k / 400k = −25.0%.
        assert RatioEngine(_loss_unclosed()).calculate_return_on_equity().value == pytest.approx(-25.0)

    def test_equity_ratio_goes_down(self):
        # Old: 500k / 700k = 0.71. New: 400k / 700k = 0.57.
        assert RatioEngine(_loss_unclosed()).calculate_equity_ratio().value == pytest.approx(0.57)

    def test_disclosure_is_negative(self):
        analytics = calculate_analytics(_loss_unclosed())
        assert analytics["equity_includes_current_earnings"] == -100_000.0
        assert analytics["effective_equity"] == 400_000.0
        assert "-$100,000.00" in analytics["equity_basis_note"]

    def test_loss_exceeding_equity_is_reported_as_negative_equity(self):
        # Equity accounts 50k, unclosed loss 150k: balance-sheet equity is −100k.
        totals = CategoryTotals(
            total_assets=200_000,
            total_liabilities=300_000,
            total_equity=50_000,
            total_revenue=100_000,
            total_expenses=250_000,
        )
        result = RatioEngine(totals).calculate_debt_to_equity()
        assert result.value == pytest.approx(-3.0)
        assert result.threshold_status == "below_threshold"
        assert "Negative equity" in result.interpretation


# ── Closed TB (idempotency) ──────────────────────────────────────────


class TestClosedTB:
    def test_closed_tb_ratios_unchanged(self):
        engine = RatioEngine(_closed())
        assert engine.unclosed_earnings == 0
        assert engine.calculate_debt_to_equity().value == pytest.approx(0.50)
        assert engine.calculate_equity_ratio().value == pytest.approx(0.67)

    def test_closed_tb_has_no_disclosure(self):
        analytics = calculate_analytics(_closed())
        assert analytics["equity_includes_current_earnings"] == 0.0
        assert analytics["effective_equity"] == 600_000.0
        assert analytics["equity_basis_note"] is None

    def test_closed_equity_supplied_with_income_statement_figures_is_not_double_counted(self):
        """Paciolus convention: A = L + E already holds, so earnings are inside equity."""
        totals = CategoryTotals(
            total_assets=900_000,
            total_liabilities=300_000,
            total_equity=600_000,
            total_revenue=600_000,
            total_expenses=500_000,
        )
        assert unclosed_current_period_earnings(totals) == 0
        engine = RatioEngine(totals)
        assert engine.calculate_debt_to_equity().value == pytest.approx(0.50)
        assert engine.calculate_return_on_equity().value == pytest.approx(16.7)

    def test_unclosed_and_closed_forms_of_the_same_books_agree(self):
        unclosed = RatioEngine(_profitable_unclosed()).to_dict()
        closed_with_is = RatioEngine(
            CategoryTotals(
                total_assets=900_000,
                current_assets=400_000,
                total_liabilities=300_000,
                current_liabilities=150_000,
                total_equity=600_000,
                total_revenue=600_000,
                total_expenses=500_000,
            )
        ).to_dict()
        for key in ("debt_to_equity", "return_on_equity", "equity_ratio"):
            assert unclosed[key]["value"] == closed_with_is[key]["value"], key

    def test_disclosure_helper_returns_none_for_zero(self):
        assert equity_basis_disclosure(0) is None
        assert equity_basis_disclosure(Decimal("0")) is None


# ── One derivation shared with the accounting-equation check ─────────


class TestSharedDerivation:
    @pytest.mark.parametrize("factory", [_profitable_unclosed, _loss_unclosed, _closed])
    def test_balance_sheet_check_and_ratios_use_the_same_earnings(self, factory):
        totals = factory()
        validation = validate_balance_sheet_equation(totals)
        analytics = calculate_analytics(totals)
        assert validation["is_balanced"] is True
        assert validation["current_period_earnings"] == analytics["equity_includes_current_earnings"]
        assert validation["liabilities_plus_equity"] == pytest.approx(
            float(totals.total_liabilities) + analytics["effective_equity"]
        )

    def test_prior_period_average_uses_effective_equity_at_both_ends(self):
        prior = _closed()  # prior year-end, closed: 600k
        current = CategoryTotals(
            total_assets=1_000_000,
            total_liabilities=300_000,
            total_equity=600_000,
            total_revenue=500_000,
            total_expenses=400_000,  # +100k unclosed -> effective 700k
        )
        roe = RatioEngine(current, prior_period_totals=prior).calculate_return_on_equity()
        # 100k / ((600k + 700k) / 2) = 15.4%
        assert roe.value == pytest.approx(15.4)
        assert effective_equity(current) == Decimal("700000")


# ── End to end from account balances (the TB path) ───────────────────


def test_extract_category_totals_signs_feed_the_adjustment():
    balances = {
        "Cash": {"debit": 900_000, "credit": 0},
        "Notes Payable": {"debit": 0, "credit": 300_000},
        "Common Stock": {"debit": 0, "credit": 500_000},
        "Sales Revenue": {"debit": 0, "credit": 600_000},
        "Operating Expenses": {"debit": 500_000, "credit": 0},
    }
    classes = {
        "Cash": "asset",
        "Notes Payable": "liability",
        "Common Stock": "equity",
        "Sales Revenue": "revenue",
        "Operating Expenses": "expense",
    }
    totals = extract_category_totals(balances, classes)
    analytics = calculate_analytics(totals)
    assert analytics["ratios"]["debt_to_equity"]["value"] == pytest.approx(0.50)
    assert analytics["equity_includes_current_earnings"] == 100_000.0


def test_full_pipeline_ratios_and_going_concern_leverage_use_effective_equity():
    from audit.pipeline import audit_trial_balance_streaming

    csv_bytes = (
        "Account,Debit,Credit\n"
        "Cash,900000,0\n"
        "Notes Payable,0,300000\n"
        "Common Stock,0,500000\n"
        "Sales Revenue,0,600000\n"
        "Operating Expenses,500000,0\n"
    ).encode()
    result = audit_trial_balance_streaming(file_bytes=csv_bytes, filename="unclosed.csv")

    analytics = result["analytics"]
    assert analytics["equity_includes_current_earnings"] == 100_000.0
    assert analytics["ratios"]["debt_to_equity"]["value"] == pytest.approx(0.50)
    assert result["balance_sheet_validation"]["is_balanced"] is True

    leverage = [i for i in result["going_concern"]["indicators"] if i["indicator_name"] == "High Leverage"]
    assert leverage, result["going_concern"]["indicators"]
    assert leverage[0]["metric_value"] == pytest.approx(0.50)  # was 0.60 on equity accounts alone


# ── Financial-statements PDF ratio section ───────────────────────────


def test_financial_statements_pdf_debt_to_equity_and_disclosure():
    from types import SimpleNamespace

    from pdf.sections.ratios import render_ratios
    from pdf.styles import create_classical_styles

    statements = SimpleNamespace(
        balance_sheet=[],
        total_assets=700_000.0,
        total_liabilities=300_000.0,
        total_equity=500_000.0,
        total_revenue=400_000.0,
        gross_profit=None,
        operating_income=None,
        net_income=-100_000.0,
        depreciation_amount=0.0,
        interest_expense=0.0,
        has_prior_period=False,
    )
    story: list = []
    assert render_ratios(story, create_classical_styles(), statements) is True
    text = " ".join(getattr(f, "text", "") for f in story)
    assert "0.75x" in text  # 300k / (500k − 100k); the old value was 0.60x
    assert "Equity includes -$100,000.00 of unclosed current-period earnings" in text
