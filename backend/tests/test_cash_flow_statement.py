"""
Tests for Cash Flow Statement Builder (Indirect Method).
Sprint 83: Cash Flow Statement — Backend Engine

Tests cover:
- Single period (no prior): net income only, no WC changes
- Dual period: full working capital changes
- Operating section: depreciation add-back, WC change signs
- Investing section: PPE changes, sign convention
- Financing section: debt changes, equity changes
- Reconciliation: balanced vs unbalanced, missing cash
- Edge cases: empty grouping, missing lead sheets, zero balances
- Serialization: to_dict() roundtrip
"""

from decimal import Decimal

import pytest

from financial_statement_builder import (
    DEPRECIATION_KEYWORDS,
    CashFlowLineItem,
    CashFlowSection,
    FinancialStatementBuilder,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def current_grouping():
    """
    Current period lead sheet grouping.

    Assets: A=$60K, B=$35K, C=$20K, D=$5K, E=$50K, F=$10K → Total=$180K
    Liabilities: G=-$30K, H=-$10K, I=-$40K, J=-$5K → Total=$85K
    Equity: K=-$95K → $95K
    Revenue: L=-$200K, COGS: M=$80K, OpEx: N=$50K, Other: O=-$10K
    Net Income = $200K - $80K - $50K + $10K = $80K
    """
    return {
        "summaries": [
            {
                "lead_sheet": "A",
                "name": "Cash",
                "category": "Current Assets",
                "total_debit": 60000.0,
                "total_credit": 0.0,
                "net_balance": 60000.0,
                "account_count": 2,
                "accounts": [],
            },
            {
                "lead_sheet": "B",
                "name": "Receivables",
                "category": "Current Assets",
                "total_debit": 35000.0,
                "total_credit": 0.0,
                "net_balance": 35000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "C",
                "name": "Inventory",
                "category": "Current Assets",
                "total_debit": 20000.0,
                "total_credit": 0.0,
                "net_balance": 20000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "D",
                "name": "Prepaid",
                "category": "Current Assets",
                "total_debit": 5000.0,
                "total_credit": 0.0,
                "net_balance": 5000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "E",
                "name": "PPE",
                "category": "Non-Current Assets",
                "total_debit": 50000.0,
                "total_credit": 0.0,
                "net_balance": 50000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "F",
                "name": "Intangibles",
                "category": "Non-Current Assets",
                "total_debit": 10000.0,
                "total_credit": 0.0,
                "net_balance": 10000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "G",
                "name": "AP",
                "category": "Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 30000.0,
                "net_balance": -30000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "H",
                "name": "Accrued",
                "category": "Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 10000.0,
                "net_balance": -10000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "I",
                "name": "LT Debt",
                "category": "Non-Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 40000.0,
                "net_balance": -40000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "J",
                "name": "Other LT",
                "category": "Non-Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 5000.0,
                "net_balance": -5000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "K",
                "name": "Equity",
                "category": "Equity",
                "total_debit": 0.0,
                "total_credit": 95000.0,
                "net_balance": -95000.0,
                "account_count": 2,
                "accounts": [],
            },
            {
                "lead_sheet": "L",
                "name": "Revenue",
                "category": "Revenue",
                "total_debit": 0.0,
                "total_credit": 200000.0,
                "net_balance": -200000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "M",
                "name": "COGS",
                "category": "Cost of Sales",
                "total_debit": 80000.0,
                "total_credit": 0.0,
                "net_balance": 80000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "N",
                "name": "OpEx",
                "category": "Operating Expenses",
                "total_debit": 50000.0,
                "total_credit": 0.0,
                "net_balance": 50000.0,
                "account_count": 2,
                "accounts": [],
            },
            {
                "lead_sheet": "O",
                "name": "Other",
                "category": "Other",
                "total_debit": 0.0,
                "total_credit": 10000.0,
                "net_balance": -10000.0,
                "account_count": 1,
                "accounts": [],
            },
        ],
        "total_debits": 310000.0,
        "total_credits": 390000.0,
        "unclassified_count": 0,
    }


@pytest.fixture
def prior_grouping():
    """
    Prior period lead sheet grouping.

    Assets: A=$50K, B=$30K, C=$15K, D=$3K, E=$40K, F=$8K
    Liabilities: G=-$25K, H=-$8K, I=-$35K, J=-$5K
    Equity: K=-$73K
    """
    return {
        "summaries": [
            {
                "lead_sheet": "A",
                "name": "Cash",
                "category": "Current Assets",
                "total_debit": 50000.0,
                "total_credit": 0.0,
                "net_balance": 50000.0,
                "account_count": 2,
                "accounts": [],
            },
            {
                "lead_sheet": "B",
                "name": "Receivables",
                "category": "Current Assets",
                "total_debit": 30000.0,
                "total_credit": 0.0,
                "net_balance": 30000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "C",
                "name": "Inventory",
                "category": "Current Assets",
                "total_debit": 15000.0,
                "total_credit": 0.0,
                "net_balance": 15000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "D",
                "name": "Prepaid",
                "category": "Current Assets",
                "total_debit": 3000.0,
                "total_credit": 0.0,
                "net_balance": 3000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "E",
                "name": "PPE",
                "category": "Non-Current Assets",
                "total_debit": 40000.0,
                "total_credit": 0.0,
                "net_balance": 40000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "F",
                "name": "Intangibles",
                "category": "Non-Current Assets",
                "total_debit": 8000.0,
                "total_credit": 0.0,
                "net_balance": 8000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "G",
                "name": "AP",
                "category": "Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 25000.0,
                "net_balance": -25000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "H",
                "name": "Accrued",
                "category": "Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 8000.0,
                "net_balance": -8000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "I",
                "name": "LT Debt",
                "category": "Non-Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 35000.0,
                "net_balance": -35000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "J",
                "name": "Other LT",
                "category": "Non-Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 5000.0,
                "net_balance": -5000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "K",
                "name": "Equity",
                "category": "Equity",
                "total_debit": 0.0,
                "total_credit": 73000.0,
                "net_balance": -73000.0,
                "account_count": 2,
                "accounts": [],
            },
        ],
        "total_debits": 146000.0,
        "total_credits": 179000.0,
        "unclassified_count": 0,
    }


def _summary(letter, accounts):
    """Summary in the serialized shape: accounts carry account/debit/credit."""
    debit = sum(a["debit"] for a in accounts)
    credit = sum(a["credit"] for a in accounts)
    return {
        "lead_sheet": letter,
        "name": letter,
        "category": "",
        "total_debit": debit,
        "total_credit": credit,
        "net_balance": debit - credit,
        "account_count": len(accounts),
        "accounts": accounts,
    }


def _acct(name, debit=0.0, credit=0.0):
    return {"account": name, "debit": debit, "credit": credit}


@pytest.fixture
def grouping_with_depreciation():
    """Current period: a balanced, pre-closing TB with depreciation in OpEx (N).

    Cash 65K Dr; Equipment 60K Dr; Accumulated Depreciation 25K Cr;
    Owner's Capital 85K Cr; Owner Distributions 25K Dr; Revenue 100K Cr;
    Salaries 30K, Depreciation Expense 15K, Rent 15K Dr.
    Debits 210K = credits 210K. Net income 40K (not yet closed).

    Sprint 882 (TQ-02/TQ-03): this fixture used to add back 15K of
    depreciation with no fixed asset to depreciate (debits 110K vs credits
    150K), so the statement it fed could never reconcile.
    """
    summaries = [
        _summary("A", [_acct("Cash", debit=65000.0)]),
        _summary("E", [_acct("Equipment", debit=60000.0), _acct("Accumulated Depreciation", credit=25000.0)]),
        _summary("K", [_acct("Owner's Capital", credit=85000.0), _acct("Owner Distributions", debit=25000.0)]),
        _summary("L", [_acct("Revenue", credit=100000.0)]),
        _summary(
            "N",
            [
                _acct("Salaries Expense", debit=30000.0),
                _acct("Depreciation Expense", debit=15000.0),
                _acct("Rent Expense", debit=15000.0),
            ],
        ),
    ]
    return {"summaries": summaries, "total_debits": 210000.0, "total_credits": 210000.0, "unclassified_count": 0}


@pytest.fixture
def prior_grouping_with_depreciation():
    """Prior period (closed): Cash 35K; Equipment 60K; Accumulated Depreciation 10K; Owner's Capital 85K."""
    summaries = [
        _summary("A", [_acct("Cash", debit=35000.0)]),
        _summary("E", [_acct("Equipment", debit=60000.0), _acct("Accumulated Depreciation", credit=10000.0)]),
        _summary("K", [_acct("Owner's Capital", credit=85000.0)]),
    ]
    return {"summaries": summaries, "total_debits": 95000.0, "total_credits": 95000.0, "unclassified_count": 0}


# =============================================================================
# TestCashFlowFromSinglePeriod
# =============================================================================


class TestCashFlowFromSinglePeriod:
    """Cash flow statement with single period — no working capital changes."""

    def test_cash_flow_exists_single_period(self, current_grouping):
        """Cash flow statement is built even without prior period."""
        builder = FinancialStatementBuilder(current_grouping)
        result = builder.build()
        assert result.cash_flow_statement is not None

    def test_has_prior_period_false(self, current_grouping):
        """has_prior_period is False when no prior provided."""
        builder = FinancialStatementBuilder(current_grouping)
        cf = builder.build().cash_flow_statement
        assert cf.has_prior_period is False

    def test_operating_has_net_income_only(self, current_grouping):
        """Operating section contains net income when no prior period."""
        builder = FinancialStatementBuilder(current_grouping)
        cf = builder.build().cash_flow_statement
        # Net income = 200K - 80K - 50K + 10K = 80K
        assert cf.operating.items[0].label == "Net Income"
        assert cf.operating.items[0].amount == 80000.0

    def test_no_working_capital_items(self, current_grouping):
        """No WC change items without prior period."""
        builder = FinancialStatementBuilder(current_grouping)
        cf = builder.build().cash_flow_statement
        wc_labels = [i.label for i in cf.operating.items if "Change in" in i.label]
        assert len(wc_labels) == 0

    def test_prior_period_note(self, current_grouping):
        """Notes mention prior period requirement."""
        builder = FinancialStatementBuilder(current_grouping)
        cf = builder.build().cash_flow_statement
        assert any("Prior period" in n for n in cf.notes)


# =============================================================================
# TestCashFlowWithPriorPeriod
# =============================================================================


class TestCashFlowWithPriorPeriod:
    """Cash flow statement with both current and prior period."""

    def test_has_prior_period_true(self, current_grouping, prior_grouping):
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        assert cf.has_prior_period is True

    def test_operating_working_capital_changes(self, current_grouping, prior_grouping):
        """WC changes appear in operating section."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        labels = [i.label for i in cf.operating.items]
        assert "Change in Accounts Receivable" in labels
        assert "Change in Inventory" in labels
        assert "Change in Prepaid Expenses" in labels
        assert "Change in Accounts Payable" in labels
        assert "Change in Accrued Liabilities" in labels

    def test_receivable_increase_negative(self, current_grouping, prior_grouping):
        """AR increase (35K-30K=5K) → -5K cash outflow."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        ar_item = next(i for i in cf.operating.items if "Receivable" in i.label)
        assert ar_item.amount == -5000.0

    def test_inventory_increase_negative(self, current_grouping, prior_grouping):
        """Inventory increase (20K-15K=5K) → -5K cash outflow."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        inv_item = next(i for i in cf.operating.items if "Inventory" in i.label)
        assert inv_item.amount == -5000.0

    def test_ap_increase_positive(self, current_grouping, prior_grouping):
        """AP increase (-30K - (-25K) = -5K change → -(-5K) = +5K inflow."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        ap_item = next(i for i in cf.operating.items if "Accounts Payable" in i.label)
        assert ap_item.amount == 5000.0

    def test_investing_ppe_change(self, current_grouping, prior_grouping):
        """PPE increase (50K-40K=10K), no depreciation or disposal → -10K purchases."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        ppe_item = next(i for i in cf.investing.items if i.source == "E")
        assert ppe_item.label == "Purchases of Property, Plant & Equipment"
        assert ppe_item.amount == -10000.0


# =============================================================================
# TestOperatingSection
# =============================================================================


class TestOperatingSection:
    """Detailed operating section tests."""

    def test_depreciation_add_back(self, grouping_with_depreciation):
        """Depreciation detected from account names and added back."""
        builder = FinancialStatementBuilder(grouping_with_depreciation)
        cf = builder.build().cash_flow_statement
        deprec_items = [i for i in cf.operating.items if "Depreciation" in i.label]
        assert len(deprec_items) == 1
        assert deprec_items[0].amount == 15000.0

    def test_no_depreciation_note(self, current_grouping):
        """Note added when depreciation not detected."""
        builder = FinancialStatementBuilder(current_grouping)
        cf = builder.build().cash_flow_statement
        assert any("Depreciation not separately identified" in n for n in cf.notes)

    def test_operating_subtotal(self, current_grouping, prior_grouping):
        """Operating = NI 80K - AR 5K - inventory 5K - prepaid 2K + AP 5K + accrued 2K = 75K."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        assert cf.operating.subtotal == 75000.0

    def test_accrued_liabilities_change(self, current_grouping, prior_grouping):
        """Accrued liabilities increase (-10K - (-8K) = -2K) → +2K inflow."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        accrued = next(i for i in cf.operating.items if "Accrued" in i.label)
        assert accrued.amount == 2000.0


# =============================================================================
# TestInvestingSection
# =============================================================================


class TestInvestingSection:
    """Investing activities tests."""

    def test_investing_empty_no_prior(self, current_grouping):
        """No investing items without prior period."""
        builder = FinancialStatementBuilder(current_grouping)
        cf = builder.build().cash_flow_statement
        assert len(cf.investing.items) == 0
        assert cf.investing.subtotal == 0.0

    def test_other_assets_change(self, current_grouping, prior_grouping):
        """Other non-current assets change (10K-8K=2K) → -2K outflow."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        other_item = next(i for i in cf.investing.items if "Other" in i.label)
        assert other_item.amount == -2000.0

    def test_investing_subtotal(self, current_grouping, prior_grouping):
        """Investing subtotal is sum of PPE + Other Assets changes."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        # PPE: -10K, Other: -2K
        assert cf.investing.subtotal == -12000.0


# =============================================================================
# TestFinancingSection
# =============================================================================


class TestFinancingSection:
    """Financing activities tests."""

    def test_financing_empty_no_prior(self, current_grouping):
        """No financing items without prior period."""
        builder = FinancialStatementBuilder(current_grouping)
        cf = builder.build().cash_flow_statement
        assert len(cf.financing.items) == 0

    def test_debt_increase(self, current_grouping, prior_grouping):
        """LT debt increase (-40K - (-35K) = -5K change) → +5K inflow."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        debt_item = next(i for i in cf.financing.items if "Long-Term Debt" in i.label)
        assert debt_item.amount == 5000.0

    def test_equity_change_excludes_retained_earnings(self, current_grouping, prior_grouping):
        """Equity financing = total equity change - net income.
        Equity: displayed = -(-95K) - (-(-73K)) = 95K - 73K = 22K change
        Net income = 80K
        Financing equity = 22K - 80K = -58K (dividends/distributions)
        """
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        equity_items = [i for i in cf.financing.items if "Equity" in i.label]
        assert len(equity_items) == 1
        # Total equity change = 95K - 73K = 22K
        # Net income = 80K
        # Financing equity = 22K - 80K = -58K
        assert equity_items[0].amount == -58000.0


# =============================================================================
# TestReconciliation
# =============================================================================


class TestReconciliation:
    """Cash flow reconciliation tests."""

    def test_beginning_cash(self, current_grouping, prior_grouping):
        """Beginning cash from prior period lead sheet A."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        assert cf.beginning_cash == 50000.0

    def test_ending_cash(self, current_grouping, prior_grouping):
        """Ending cash from current period lead sheet A."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        assert cf.ending_cash == 60000.0

    def test_net_change_calculation(self, current_grouping, prior_grouping):
        """Operating 75K, investing -12K, financing -53K (debt +5K, equity -58K): net +10K."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        assert cf.operating.subtotal == 75000.0
        assert cf.investing.subtotal == -12000.0
        assert cf.financing.subtotal == -53000.0
        assert cf.net_change == 10000.0

    def test_statement_reconciles_to_the_cash_movement(self, current_grouping, prior_grouping):
        """Cash 50K -> 60K: the +10K net change reconciles exactly."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        assert cf.reconciliation_difference == 0.0
        assert cf.is_reconciled is True


# =============================================================================
# TestEdgeCases
# =============================================================================


class TestEdgeCases:
    """Edge cases for cash flow statement."""

    def test_empty_grouping(self):
        """Empty grouping produces cash flow with zero amounts."""
        grouping = {"summaries": [], "total_debits": 0.0, "total_credits": 0.0, "unclassified_count": 0}
        builder = FinancialStatementBuilder(grouping)
        result = builder.build()
        cf = result.cash_flow_statement
        assert cf is not None
        assert cf.operating.subtotal == 0.0
        assert cf.net_change == 0.0

    def test_missing_lead_sheets(self):
        """Missing lead sheets treated as zero — no errors."""
        grouping = {
            "summaries": [
                {
                    "lead_sheet": "A",
                    "name": "Cash",
                    "category": "Current Assets",
                    "total_debit": 10000.0,
                    "total_credit": 0.0,
                    "net_balance": 10000.0,
                    "account_count": 1,
                    "accounts": [],
                },
            ],
            "total_debits": 10000.0,
            "total_credits": 0.0,
            "unclassified_count": 0,
        }
        prior = {
            "summaries": [
                {
                    "lead_sheet": "A",
                    "name": "Cash",
                    "category": "Current Assets",
                    "total_debit": 8000.0,
                    "total_credit": 0.0,
                    "net_balance": 8000.0,
                    "account_count": 1,
                    "accounts": [],
                },
            ],
            "total_debits": 8000.0,
            "total_credits": 0.0,
            "unclassified_count": 0,
        }
        builder = FinancialStatementBuilder(grouping, prior_lead_sheet_grouping=prior)
        result = builder.build()
        cf = result.cash_flow_statement
        assert cf.beginning_cash == 8000.0
        assert cf.ending_cash == 10000.0

    def test_zero_balance_changes_omitted(self):
        """Zero-change lead sheets don't produce line items."""
        current = {
            "summaries": [
                {
                    "lead_sheet": "A",
                    "name": "Cash",
                    "category": "Current Assets",
                    "total_debit": 10000.0,
                    "total_credit": 0.0,
                    "net_balance": 10000.0,
                    "account_count": 1,
                    "accounts": [],
                },
                {
                    "lead_sheet": "B",
                    "name": "AR",
                    "category": "Current Assets",
                    "total_debit": 5000.0,
                    "total_credit": 0.0,
                    "net_balance": 5000.0,
                    "account_count": 1,
                    "accounts": [],
                },
            ],
            "total_debits": 15000.0,
            "total_credits": 0.0,
            "unclassified_count": 0,
        }
        prior = {
            "summaries": [
                {
                    "lead_sheet": "A",
                    "name": "Cash",
                    "category": "Current Assets",
                    "total_debit": 10000.0,
                    "total_credit": 0.0,
                    "net_balance": 10000.0,
                    "account_count": 1,
                    "accounts": [],
                },
                {
                    "lead_sheet": "B",
                    "name": "AR",
                    "category": "Current Assets",
                    "total_debit": 5000.0,
                    "total_credit": 0.0,
                    "net_balance": 5000.0,
                    "account_count": 1,
                    "accounts": [],
                },
            ],
            "total_debits": 15000.0,
            "total_credits": 0.0,
            "unclassified_count": 0,
        }
        builder = FinancialStatementBuilder(current, prior_lead_sheet_grouping=prior)
        cf = builder.build().cash_flow_statement
        # No WC changes since balances identical
        wc_items = [i for i in cf.operating.items if "Change in" in i.label]
        assert len(wc_items) == 0


# =============================================================================
# TestSerialization
# =============================================================================


class TestSerialization:
    """Cash flow statement serialization tests."""

    def test_cash_flow_in_financial_statements_dict(self, current_grouping, prior_grouping):
        """to_dict() includes cash_flow_statement."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        d = builder.build().to_dict()
        assert "cash_flow_statement" in d
        cf = d["cash_flow_statement"]
        assert "operating" in cf
        assert "investing" in cf
        assert "financing" in cf

    def test_cash_flow_to_dict_roundtrip(self, current_grouping, prior_grouping):
        """CashFlowStatement.to_dict() produces JSON-safe structure."""
        builder = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        cf = builder.build().cash_flow_statement
        d = cf.to_dict()

        assert isinstance(d["operating"]["items"], list)
        assert isinstance(d["investing"]["items"], list)
        assert isinstance(d["financing"]["items"], list)
        assert isinstance(d["net_change"], Decimal)  # Sprint 884: amounts are exact Decimals
        assert isinstance(d["notes"], list)
        assert isinstance(d["is_reconciled"], bool)

    def test_no_cash_flow_when_no_prior_single_period_dict(self, current_grouping):
        """to_dict() still includes cash_flow_statement even for single period."""
        builder = FinancialStatementBuilder(current_grouping)
        d = builder.build().to_dict()
        assert "cash_flow_statement" in d
        assert d["cash_flow_statement"]["has_prior_period"] is False

    def test_section_to_dict(self):
        """CashFlowSection.to_dict() works independently."""
        section = CashFlowSection(
            label="Test Section",
            items=[CashFlowLineItem("Item 1", 100.0, source="A")],
            subtotal=100.0,
        )
        d = section.to_dict()
        assert d["label"] == "Test Section"
        assert len(d["items"]) == 1
        assert d["items"][0]["amount"] == 100.0
        assert d["subtotal"] == 100.0


# =============================================================================
# TestDepreciationDetection
# =============================================================================


class TestDepreciationDetection:
    """Tests for depreciation keyword detection."""

    def test_depreciation_expense_detected(self, grouping_with_depreciation):
        """'Depreciation Expense' keyword detected in N accounts."""
        builder = FinancialStatementBuilder(grouping_with_depreciation)
        cf = builder.build().cash_flow_statement
        deprec = [i for i in cf.operating.items if "Depreciation" in i.label]
        assert len(deprec) == 1
        assert deprec[0].amount == 15000.0

    def test_amortization_keyword(self):
        """'amortization' keyword also detected."""
        grouping = {
            "summaries": [
                {
                    "lead_sheet": "N",
                    "name": "OpEx",
                    "category": "Operating Expenses",
                    "total_debit": 20000.0,
                    "total_credit": 0.0,
                    "net_balance": 20000.0,
                    "account_count": 1,
                    "accounts": [
                        {"name": "Amortization of Intangibles", "net_balance": 8000.0},
                    ],
                },
                {
                    "lead_sheet": "L",
                    "name": "Revenue",
                    "category": "Revenue",
                    "total_debit": 0.0,
                    "total_credit": 50000.0,
                    "net_balance": -50000.0,
                    "account_count": 1,
                    "accounts": [],
                },
            ],
            "total_debits": 20000.0,
            "total_credits": 50000.0,
            "unclassified_count": 0,
        }
        builder = FinancialStatementBuilder(grouping)
        cf = builder.build().cash_flow_statement
        deprec = [i for i in cf.operating.items if "Depreciation" in i.label]
        assert len(deprec) == 1
        assert deprec[0].amount == 8000.0

    def test_no_depreciation_accounts(self, current_grouping):
        """No depreciation detected when accounts have no matching keywords."""
        builder = FinancialStatementBuilder(current_grouping)
        cf = builder.build().cash_flow_statement
        deprec = [i for i in cf.operating.items if "Depreciation" in i.label]
        assert len(deprec) == 0

    def test_depreciation_keywords_constant(self):
        """DEPRECIATION_KEYWORDS is non-empty and well-formed."""
        assert len(DEPRECIATION_KEYWORDS) > 0
        for keyword, is_phrase in DEPRECIATION_KEYWORDS:
            assert isinstance(keyword, str)
            assert isinstance(is_phrase, bool)


# =============================================================================
# TestCashFlowWithDepreciationAndPrior
# =============================================================================


class TestCashFlowWithDepreciationAndPrior:
    """End-to-end test with depreciation + prior period."""

    def test_full_cash_flow_reconciled(self, grouping_with_depreciation, prior_grouping_with_depreciation):
        """Depreciation, a distribution and a prior period: every figure fixed, and it reconciles."""
        builder = FinancialStatementBuilder(
            grouping_with_depreciation,
            prior_lead_sheet_grouping=prior_grouping_with_depreciation,
        )
        result = builder.build()
        cf = result.cash_flow_statement

        # Net income = 100K - 60K = 40K
        assert result.net_income == 40000.0

        # Operating: 40K net income + 15K depreciation add-back = 55K
        assert [(i.label, i.amount) for i in cf.operating.items] == [
            ("Net Income", 40000.0),
            ("Depreciation & Amortization", 15000.0),
        ]
        assert cf.operating.subtotal == 55000.0

        # Investing: gross equipment unchanged at 60K; accumulated depreciation
        # rose by exactly the 15K charge, so no cash moved.
        assert cf.investing.items == []
        assert cf.investing.subtotal == 0.0

        # Financing: equity 85K -> 85K - 25K distributions + 40K unclosed = 100K;
        # change 15K less net income 40K = the 25K distribution.
        assert [(i.label, i.amount) for i in cf.financing.items] == [
            ("Equity Changes (excl. Retained Earnings)", -25000.0)
        ]
        assert cf.financing.subtotal == -25000.0

        # Cash: 35K -> 65K, net change 30K
        assert cf.net_change == 30000.0
        assert cf.beginning_cash == 35000.0
        assert cf.ending_cash == 65000.0
        assert cf.reconciliation_difference == 0.0
        assert cf.is_reconciled is True

    def test_depreciation_not_in_notes(self, grouping_with_depreciation, prior_grouping_with_depreciation):
        """No depreciation note when successfully detected."""
        builder = FinancialStatementBuilder(
            grouping_with_depreciation,
            prior_lead_sheet_grouping=prior_grouping_with_depreciation,
        )
        cf = builder.build().cash_flow_statement
        assert not any("Depreciation not separately" in n for n in cf.notes)


# =============================================================================
# TestBackwardCompatibility
# =============================================================================


class TestBackwardCompatibility:
    """Existing financial statement tests still pass with new code."""

    def test_existing_build_without_prior(self, current_grouping):
        """Builder still works without prior period (backward compatible)."""
        builder = FinancialStatementBuilder(current_grouping)
        result = builder.build()
        # BS and IS still correct
        assert result.total_assets == 180000.0
        assert result.net_income == 80000.0
        assert result.is_balanced is True

    def test_prior_period_does_not_affect_bs_is(self, current_grouping, prior_grouping):
        """Prior period only affects cash flow, not BS/IS."""
        builder_single = FinancialStatementBuilder(current_grouping)
        builder_dual = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior_grouping)
        single = builder_single.build()
        dual = builder_dual.build()

        assert single.total_assets == dual.total_assets
        assert single.net_income == dual.net_income
        assert single.is_balanced == dual.is_balanced
        assert single.total_liabilities == dual.total_liabilities
