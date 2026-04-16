"""Sprint 640 — Budget vs Actual favorable / unfavorable classification."""

from multi_period_comparison import (
    BudgetVariance,
    SignificanceTier,
    _classify_variance_direction,
    _commentary_prompt,
)


class TestRevenueVariance:
    def test_actual_exceeds_budget_favorable(self):
        # Revenue is credit-normal. Actual -1200 vs budget -1000 →
        # variance_amount (current - budget) = -200.
        assert _classify_variance_direction(-200.0, "Revenue") == "favorable"

    def test_actual_below_budget_unfavorable(self):
        # Revenue fell short. variance_amount = +200.
        assert _classify_variance_direction(200.0, "Revenue") == "unfavorable"

    def test_on_budget_under_tolerance(self):
        assert _classify_variance_direction(0.005, "Revenue") == "on_budget"


class TestExpenseVariance:
    def test_over_spent_unfavorable(self):
        # Expense is debit-normal. Actual 600 vs budget 500 → variance +100.
        assert _classify_variance_direction(100.0, "Operating Expenses") == "unfavorable"

    def test_under_spent_favorable(self):
        # Spent less than budget.
        assert _classify_variance_direction(-100.0, "Operating Expenses") == "favorable"

    def test_cogs_classified_like_expense(self):
        assert _classify_variance_direction(50.0, "Cost of Goods Sold") == "unfavorable"


class TestBalanceSheetVariance:
    def test_assets_return_neutral(self):
        assert _classify_variance_direction(500.0, "Current Assets") == "neutral"
        assert _classify_variance_direction(-500.0, "Non-Current Assets") == "neutral"

    def test_liabilities_return_neutral(self):
        assert _classify_variance_direction(300.0, "Current Liabilities") == "neutral"

    def test_equity_returns_neutral(self):
        assert _classify_variance_direction(200.0, "Equity") == "neutral"

    def test_unknown_category_returns_neutral(self):
        assert _classify_variance_direction(100.0, "Something Else") == "neutral"


class TestCommentaryPrompt:
    def test_prompt_includes_account_and_category(self):
        prompt = _commentary_prompt("5000 Rent Expense", 15000.0, "unfavorable", "Operating Expenses")
        assert "5000 Rent Expense" in prompt
        assert "Operating Expenses" in prompt
        assert "unfavorable" in prompt

    def test_prompt_mentions_material_driver_categories(self):
        prompt = _commentary_prompt("Revenue", -50000.0, "favorable", "Revenue")
        low = prompt.lower()
        # The prompt should guide the auditor to categorise the driver.
        assert any(tok in low for tok in ("timing", "estimate", "one-time", "run-rate"))


class TestSerialisation:
    def test_to_dict_includes_direction(self):
        bv = BudgetVariance(
            budget_balance=1000.0,
            variance_amount=100.0,
            variance_percent=10.0,
            variance_significance=SignificanceTier.SIGNIFICANT,
            variance_direction="unfavorable",
        )
        d = bv.to_dict()
        assert d["variance_direction"] == "unfavorable"
        # Commentary prompt absent when not supplied.
        assert "commentary_prompt" not in d

    def test_to_dict_includes_commentary_when_set(self):
        bv = BudgetVariance(
            budget_balance=1000.0,
            variance_amount=100.0,
            variance_percent=10.0,
            variance_significance=SignificanceTier.MATERIAL,
            variance_direction="unfavorable",
            commentary_prompt="document driver",
        )
        d = bv.to_dict()
        assert d["commentary_prompt"] == "document driver"
