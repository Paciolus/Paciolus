"""
Tests for Financial Statement Builder, PDF, and Excel export.
Sprint 71: Financial Statements — Backend Builder + Export
"""

from decimal import Decimal
from io import BytesIO

import pytest

from financial_statement_builder import (
    FinancialStatementBuilder,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_lead_sheet_grouping():
    """
    Balanced lead sheet grouping fixture.

    Assets: A=$50K, B=$30K, E=$45K, F=$5K → Total Assets = $130K
    Liabilities: G=-$25K, I=-$30K → Total Liabilities = $55K
    Equity: K=-$75K → Total Equity = $75K
    Total L+E = $130K (balanced)

    Revenue: L=-$150K, COGS: M=$60K, OpEx: N=$40K, Other: O=-$5K
    Net Income = $150K - $60K - $40K + $5K = $55K
    """
    return {
        "summaries": [
            {
                "lead_sheet": "A",
                "name": "Cash and Cash Equivalents",
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
                "lead_sheet": "E",
                "name": "Property, Plant & Equipment",
                "category": "Non-Current Assets",
                "total_debit": 45000.0,
                "total_credit": 0.0,
                "net_balance": 45000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "F",
                "name": "Other Assets & Intangibles",
                "category": "Non-Current Assets",
                "total_debit": 5000.0,
                "total_credit": 0.0,
                "net_balance": 5000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "G",
                "name": "Accounts Payable & Accrued Liabilities",
                "category": "Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 25000.0,
                "net_balance": -25000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "I",
                "name": "Long-term Debt",
                "category": "Non-Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 30000.0,
                "net_balance": -30000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "K",
                "name": "Stockholders' Equity",
                "category": "Equity",
                "total_debit": 0.0,
                "total_credit": 75000.0,
                "net_balance": -75000.0,
                "account_count": 2,
                "accounts": [],
            },
            {
                "lead_sheet": "L",
                "name": "Revenue",
                "category": "Revenue",
                "total_debit": 0.0,
                "total_credit": 150000.0,
                "net_balance": -150000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "M",
                "name": "Cost of Goods Sold",
                "category": "Cost of Sales",
                "total_debit": 60000.0,
                "total_credit": 0.0,
                "net_balance": 60000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "N",
                "name": "Operating Expenses",
                "category": "Operating Expenses",
                "total_debit": 40000.0,
                "total_credit": 0.0,
                "net_balance": 40000.0,
                "account_count": 3,
                "accounts": [],
            },
            {
                "lead_sheet": "O",
                "name": "Other Income & Expense",
                "category": "Other",
                "total_debit": 0.0,
                "total_credit": 5000.0,
                "net_balance": -5000.0,
                "account_count": 1,
                "accounts": [],
            },
        ],
        "total_debits": 230000.0,
        "total_credits": 285000.0,
        "unclassified_count": 0,
    }


@pytest.fixture
def unbalanced_lead_sheet_grouping():
    """Lead sheet grouping that does NOT balance (assets != L+E)."""
    return {
        "summaries": [
            {
                "lead_sheet": "A",
                "name": "Cash",
                "category": "Current Assets",
                "total_debit": 100000.0,
                "total_credit": 0.0,
                "net_balance": 100000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "K",
                "name": "Equity",
                "category": "Equity",
                "total_debit": 0.0,
                "total_credit": 80000.0,
                "net_balance": -80000.0,
                "account_count": 1,
                "accounts": [],
            },
        ],
        "total_debits": 100000.0,
        "total_credits": 80000.0,
        "unclassified_count": 0,
    }


@pytest.fixture
def other_expense_grouping():
    """Lead sheet grouping where O has a debit (expense) balance."""
    return {
        "summaries": [
            {
                "lead_sheet": "L",
                "name": "Revenue",
                "category": "Revenue",
                "total_debit": 0.0,
                "total_credit": 100000.0,
                "net_balance": -100000.0,
                "account_count": 1,
                "accounts": [],
            },
            {
                "lead_sheet": "O",
                "name": "Other Income & Expense",
                "category": "Other",
                "total_debit": 8000.0,
                "total_credit": 0.0,
                "net_balance": 8000.0,
                "account_count": 1,
                "accounts": [],
            },
        ],
        "total_debits": 8000.0,
        "total_credits": 100000.0,
        "unclassified_count": 0,
    }


# =============================================================================
# TestFinancialStatementBuilder
# =============================================================================


class TestFinancialStatementBuilder:
    """Tests for the FinancialStatementBuilder class."""

    def test_balance_sheet_current_assets(self, sample_lead_sheet_grouping):
        """A-D grouped as current assets, positive amounts."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        # Find current asset line items
        bs_items = {item.lead_sheet_ref: item for item in result.balance_sheet if item.lead_sheet_ref}
        assert bs_items["A"].amount == 50000.0
        assert bs_items["B"].amount == 30000.0

    def test_balance_sheet_noncurrent_assets(self, sample_lead_sheet_grouping):
        """E-F grouped as non-current assets."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        bs_items = {item.lead_sheet_ref: item for item in result.balance_sheet if item.lead_sheet_ref}
        assert bs_items["E"].amount == 45000.0
        assert bs_items["F"].amount == 5000.0

    def test_balance_sheet_current_liabilities(self, sample_lead_sheet_grouping):
        """G-H grouped, sign-flipped to positive."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        bs_items = {item.lead_sheet_ref: item for item in result.balance_sheet if item.lead_sheet_ref}
        assert bs_items["G"].amount == 25000.0  # Flipped from -25000

    def test_balance_sheet_noncurrent_liabilities(self, sample_lead_sheet_grouping):
        """I-J grouped, sign-flipped."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        bs_items = {item.lead_sheet_ref: item for item in result.balance_sheet if item.lead_sheet_ref}
        assert bs_items["I"].amount == 30000.0  # Flipped from -30000

    def test_balance_sheet_equity(self, sample_lead_sheet_grouping):
        """K sign-flipped."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        bs_items = {item.lead_sheet_ref: item for item in result.balance_sheet if item.lead_sheet_ref}
        assert bs_items["K"].amount == 75000.0  # Flipped from -75000

    def test_balance_sheet_total_assets(self, sample_lead_sheet_grouping):
        """Total assets = current + non-current."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        assert result.total_assets == 130000.0  # 50+30+45+5

    def test_balance_sheet_balanced(self, sample_lead_sheet_grouping):
        """is_balanced=True when assets = L+E."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        assert result.is_balanced is True
        assert abs(result.balance_difference) < 0.01

    def test_balance_sheet_unbalanced(self, unbalanced_lead_sheet_grouping):
        """is_balanced=False, difference reported."""
        builder = FinancialStatementBuilder(unbalanced_lead_sheet_grouping)
        result = builder.build()

        assert result.is_balanced is False
        assert result.balance_difference == 20000.0  # 100K assets - 80K equity

    def test_income_statement_revenue(self, sample_lead_sheet_grouping):
        """L sign-flipped to positive."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        assert result.total_revenue == 150000.0

    def test_income_statement_cogs(self, sample_lead_sheet_grouping):
        """M kept positive (debit balance)."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        is_items = {item.lead_sheet_ref: item for item in result.income_statement if item.lead_sheet_ref}
        assert is_items["M"].amount == 60000.0

    def test_income_statement_gross_profit(self, sample_lead_sheet_grouping):
        """Gross profit = revenue - COGS."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        assert result.gross_profit == 90000.0  # 150K - 60K

    def test_income_statement_operating_expenses(self, sample_lead_sheet_grouping):
        """N kept positive (debit balance)."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        is_items = {item.lead_sheet_ref: item for item in result.income_statement if item.lead_sheet_ref}
        assert is_items["N"].amount == 40000.0

    def test_income_statement_operating_income(self, sample_lead_sheet_grouping):
        """Operating income = gross profit - opex."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        assert result.operating_income == 50000.0  # 90K - 40K

    def test_income_statement_other_income(self, sample_lead_sheet_grouping):
        """O with credit balance → positive (income)."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        is_items = {item.lead_sheet_ref: item for item in result.income_statement if item.lead_sheet_ref}
        assert is_items["O"].amount == 5000.0  # Flipped from -5000

    def test_income_statement_other_expense(self, other_expense_grouping):
        """O with debit balance → negative (expense)."""
        builder = FinancialStatementBuilder(other_expense_grouping)
        result = builder.build()

        is_items = {item.lead_sheet_ref: item for item in result.income_statement if item.lead_sheet_ref}
        assert is_items["O"].amount == -8000.0  # Flipped from +8000 debit

    def test_income_statement_net_income(self, sample_lead_sheet_grouping):
        """Net income = operating + other."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()

        assert result.net_income == 55000.0  # 50K + 5K

    def test_missing_lead_sheets(self):
        """Graceful zero for absent categories."""
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
        builder = FinancialStatementBuilder(grouping)
        result = builder.build()

        assert result.total_assets == 10000.0
        assert result.total_liabilities == 0.0
        assert result.total_equity == 0.0
        assert result.total_revenue == 0.0
        assert result.net_income == 0.0

    def test_empty_grouping(self):
        """Handles empty summaries list."""
        grouping = {
            "summaries": [],
            "total_debits": 0.0,
            "total_credits": 0.0,
            "unclassified_count": 0,
        }
        builder = FinancialStatementBuilder(grouping)
        result = builder.build()

        assert result.total_assets == 0.0
        assert result.is_balanced is True
        assert len(result.balance_sheet) > 0  # Structure still generated
        assert len(result.income_statement) > 0

    def test_to_dict_serialization(self, sample_lead_sheet_grouping):
        """Round-trip serializable."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()
        d = result.to_dict()

        assert isinstance(d, dict)
        assert "balance_sheet" in d
        assert "income_statement" in d
        assert isinstance(d["balance_sheet"], list)
        assert isinstance(d["income_statement"], list)
        assert d["total_assets"] == 130000.0
        assert d["is_balanced"] is True
        assert d["net_income"] == 55000.0

        # Verify each line item is a dict
        for item in d["balance_sheet"]:
            assert "label" in item
            assert "amount" in item
            assert "indent_level" in item

    def test_zero_revenue_no_division_error(self):
        """Gross margin calculation handles zero revenue."""
        grouping = {
            "summaries": [
                {
                    "lead_sheet": "M",
                    "name": "COGS",
                    "category": "Cost of Sales",
                    "total_debit": 5000.0,
                    "total_credit": 0.0,
                    "net_balance": 5000.0,
                    "account_count": 1,
                    "accounts": [],
                },
            ],
            "total_debits": 5000.0,
            "total_credits": 0.0,
            "unclassified_count": 0,
        }
        builder = FinancialStatementBuilder(grouping)
        result = builder.build()

        assert result.total_revenue == 0.0
        assert result.gross_profit == -5000.0
        assert result.net_income == -5000.0

    def test_entity_name_and_period(self, sample_lead_sheet_grouping):
        """Metadata fields passed through."""
        builder = FinancialStatementBuilder(
            sample_lead_sheet_grouping,
            entity_name="Acme Corp",
            period_end="2025-12-31",
        )
        result = builder.build()

        assert result.entity_name == "Acme Corp"
        assert result.period_end == "2025-12-31"

        d = result.to_dict()
        assert d["entity_name"] == "Acme Corp"
        assert d["period_end"] == "2025-12-31"


# =============================================================================
# TestFinancialStatementPDF
# =============================================================================


class TestFinancialStatementPDF:
    """Tests for financial statement PDF generation."""

    def test_pdf_bytes_nonempty(self, sample_lead_sheet_grouping):
        """Generate PDF, assert non-empty bytes."""
        from pdf_generator import generate_financial_statements_pdf

        builder = FinancialStatementBuilder(sample_lead_sheet_grouping, entity_name="Test Corp")
        statements = builder.build()

        pdf_bytes = generate_financial_statements_pdf(statements)
        assert len(pdf_bytes) > 0

    def test_pdf_bytes_type(self, sample_lead_sheet_grouping):
        """Assert PDF output is bytes."""
        from pdf_generator import generate_financial_statements_pdf

        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        statements = builder.build()

        pdf_bytes = generate_financial_statements_pdf(statements)
        assert isinstance(pdf_bytes, bytes)

    def test_pdf_with_workpaper_fields(self, sample_lead_sheet_grouping):
        """PDF generates with workpaper signoff fields."""
        from pdf_generator import generate_financial_statements_pdf

        builder = FinancialStatementBuilder(sample_lead_sheet_grouping, entity_name="Acme Corp")
        statements = builder.build()

        pdf_bytes = generate_financial_statements_pdf(
            statements,
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
        )
        assert len(pdf_bytes) > 100


# =============================================================================
# TestFinancialStatementExcel
# =============================================================================


class TestFinancialStatementExcel:
    """Tests for financial statement Excel generation."""

    def test_excel_bytes_nonempty(self, sample_lead_sheet_grouping):
        """Generate Excel, assert non-empty bytes."""
        from excel_generator import generate_financial_statements_excel

        builder = FinancialStatementBuilder(sample_lead_sheet_grouping, entity_name="Test Corp")
        statements = builder.build()

        excel_bytes = generate_financial_statements_excel(statements)
        assert len(excel_bytes) > 0

    def test_excel_has_balance_sheet_tab(self, sample_lead_sheet_grouping):
        """Load workbook, check sheet names."""
        from openpyxl import load_workbook

        from excel_generator import generate_financial_statements_excel

        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        statements = builder.build()

        excel_bytes = generate_financial_statements_excel(statements)
        wb = load_workbook(BytesIO(excel_bytes))
        assert "Balance Sheet" in wb.sheetnames

    def test_excel_has_income_statement_tab(self, sample_lead_sheet_grouping):
        """Load workbook, check sheet names."""
        from openpyxl import load_workbook

        from excel_generator import generate_financial_statements_excel

        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        statements = builder.build()

        excel_bytes = generate_financial_statements_excel(statements)
        wb = load_workbook(BytesIO(excel_bytes))
        assert "Income Statement" in wb.sheetnames


# =============================================================================
# MAPPING TRACE FIXTURES
# =============================================================================


@pytest.fixture
def grouping_with_accounts():
    """
    Lead sheet grouping with populated accounts arrays for mapping trace tests.

    A: 2 accounts (Cash at Bank $30K, Petty Cash $20K) → $50K
    B: 2 accounts (Trade Receivables $20K, Other Receivables $10K) → $30K
    G: 2 accounts (Trade Payables $15K cr, Accrued Expenses $10K cr) → -$25K
    K: 2 accounts (Common Stock $50K cr, Retained Earnings $25K cr) → -$75K
    L: 2 accounts (Product Revenue $100K cr, Service Revenue $50K cr) → -$150K
    N: 3 accounts (Salaries $20K, Rent $10K, Depreciation $10K) → $40K
    """
    return {
        "summaries": [
            {
                "lead_sheet": "A",
                "name": "Cash and Cash Equivalents",
                "category": "Current Assets",
                "total_debit": 50000.0,
                "total_credit": 0.0,
                "net_balance": 50000.0,
                "account_count": 2,
                "accounts": [
                    {
                        "account": "Cash at Bank",
                        "debit": 30000.0,
                        "credit": 0.0,
                        "confidence": 0.95,
                        "matched_keywords": ["cash", "bank"],
                    },
                    {
                        "account": "Petty Cash",
                        "debit": 20000.0,
                        "credit": 0.0,
                        "confidence": 0.90,
                        "matched_keywords": ["cash"],
                    },
                ],
            },
            {
                "lead_sheet": "B",
                "name": "Receivables",
                "category": "Current Assets",
                "total_debit": 30000.0,
                "total_credit": 0.0,
                "net_balance": 30000.0,
                "account_count": 2,
                "accounts": [
                    {
                        "account": "Trade Receivables",
                        "debit": 20000.0,
                        "credit": 0.0,
                        "confidence": 0.85,
                        "matched_keywords": ["receivable"],
                    },
                    {
                        "account": "Other Receivables",
                        "debit": 10000.0,
                        "credit": 0.0,
                        "confidence": 0.80,
                        "matched_keywords": ["receivable"],
                    },
                ],
            },
            {
                "lead_sheet": "G",
                "name": "AP & Accrued Liabilities",
                "category": "Current Liabilities",
                "total_debit": 0.0,
                "total_credit": 25000.0,
                "net_balance": -25000.0,
                "account_count": 2,
                "accounts": [
                    {
                        "account": "Trade Payables",
                        "debit": 0.0,
                        "credit": 15000.0,
                        "confidence": 0.90,
                        "matched_keywords": ["payable"],
                    },
                    {
                        "account": "Accrued Expenses",
                        "debit": 0.0,
                        "credit": 10000.0,
                        "confidence": 0.85,
                        "matched_keywords": ["accrued"],
                    },
                ],
            },
            {
                "lead_sheet": "K",
                "name": "Stockholders' Equity",
                "category": "Equity",
                "total_debit": 0.0,
                "total_credit": 75000.0,
                "net_balance": -75000.0,
                "account_count": 2,
                "accounts": [
                    {
                        "account": "Common Stock",
                        "debit": 0.0,
                        "credit": 50000.0,
                        "confidence": 1.0,
                        "matched_keywords": ["stock"],
                    },
                    {
                        "account": "Retained Earnings",
                        "debit": 0.0,
                        "credit": 25000.0,
                        "confidence": 1.0,
                        "matched_keywords": ["retained"],
                    },
                ],
            },
            {
                "lead_sheet": "L",
                "name": "Revenue",
                "category": "Revenue",
                "total_debit": 0.0,
                "total_credit": 150000.0,
                "net_balance": -150000.0,
                "account_count": 2,
                "accounts": [
                    {
                        "account": "Product Revenue",
                        "debit": 0.0,
                        "credit": 100000.0,
                        "confidence": 0.95,
                        "matched_keywords": ["revenue"],
                    },
                    {
                        "account": "Service Revenue",
                        "debit": 0.0,
                        "credit": 50000.0,
                        "confidence": 0.90,
                        "matched_keywords": ["revenue"],
                    },
                ],
            },
            {
                "lead_sheet": "N",
                "name": "Operating Expenses",
                "category": "Operating Expenses",
                "total_debit": 40000.0,
                "total_credit": 0.0,
                "net_balance": 40000.0,
                "account_count": 3,
                "accounts": [
                    {
                        "account": "Salaries",
                        "debit": 20000.0,
                        "credit": 0.0,
                        "confidence": 0.90,
                        "matched_keywords": ["salary"],
                    },
                    {
                        "account": "Rent Expense",
                        "debit": 10000.0,
                        "credit": 0.0,
                        "confidence": 0.85,
                        "matched_keywords": ["rent"],
                    },
                    {
                        # Sprint 803: was keyed "name" — the only account in this
                        # fixture keyed differently from its siblings, and the one
                        # account the depreciation test reads. That mismatch is why
                        # finding A-5 passed its own test while returning 0.0 in
                        # production, where the key is always "account".
                        "account": "Depreciation Expense",
                        "debit": 10000.0,
                        "credit": 0.0,
                        "confidence": 0.95,
                        "matched_keywords": ["depreciation"],
                    },
                ],
            },
        ],
        "total_debits": 120000.0,
        "total_credits": 250000.0,
        "unclassified_count": 0,
    }


# =============================================================================
# TestMappingTrace
# =============================================================================


class TestMappingTrace:
    """Tests for Account-to-Statement Mapping Trace (Sprint 284)."""

    def test_mapping_trace_populated(self, grouping_with_accounts):
        """Verify non-empty list with entries for populated lead sheets."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        result = builder.build()

        assert len(result.mapping_trace) == 15  # A-O
        refs = {e.lead_sheet_ref for e in result.mapping_trace}
        for letter in ["A", "B", "G", "K", "L", "N"]:
            assert letter in refs

    def test_mapping_trace_accounts_match(self, grouping_with_accounts):
        """Verify account names and amounts in trace entries."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        result = builder.build()

        entry_map = {e.lead_sheet_ref: e for e in result.mapping_trace}

        # Cash (A): 2 accounts, $30K + $20K
        a_entry = entry_map["A"]
        assert a_entry.account_count == 2
        names = [acct.account_name for acct in a_entry.accounts]
        assert "Cash at Bank" in names
        assert "Petty Cash" in names
        assert a_entry.accounts[0].debit == 30000.0
        assert a_entry.accounts[1].debit == 20000.0

    def test_mapping_trace_tie_out(self, grouping_with_accounts):
        """Verify is_tied=True when account sums match net_balance."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        result = builder.build()

        entry_map = {e.lead_sheet_ref: e for e in result.mapping_trace}
        for ref in ["A", "B", "G", "K", "L", "N"]:
            entry = entry_map[ref]
            assert entry.is_tied is True, f"Entry {ref} should be tied"
            assert entry.tie_difference < 0.01

    def test_mapping_trace_empty_lead_sheet(self, grouping_with_accounts):
        """Letters with no accounts have account_count=0, is_tied=True."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        result = builder.build()

        entry_map = {e.lead_sheet_ref: e for e in result.mapping_trace}
        # C (Inventory) not in fixture → empty
        c_entry = entry_map["C"]
        assert c_entry.account_count == 0
        assert c_entry.is_tied is True
        assert c_entry.tie_difference == 0.0

    def test_mapping_trace_in_to_dict(self, grouping_with_accounts):
        """Verify serialization includes mapping_trace key."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        result = builder.build()
        d = result.to_dict()

        assert "mapping_trace" in d
        assert isinstance(d["mapping_trace"], list)
        assert len(d["mapping_trace"]) == 15

        # Verify first entry structure
        first = d["mapping_trace"][0]
        assert "statement" in first
        assert "line_label" in first
        assert "lead_sheet_ref" in first
        assert "accounts" in first
        assert "is_tied" in first

    def test_mapping_trace_account_name_fallback(self, grouping_with_accounts):
        """Accounts using 'name' key instead of 'account' are handled."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        result = builder.build()

        entry_map = {e.lead_sheet_ref: e for e in result.mapping_trace}
        n_entry = entry_map["N"]
        # Third account in N uses "name" key instead of "account"
        names = [acct.account_name for acct in n_entry.accounts]
        assert "Depreciation Expense" in names


class TestMappingTracePDF:
    """Tests for mapping trace in PDF generation."""

    def test_pdf_with_mapping_trace(self, grouping_with_accounts):
        """PDF generates with populated accounts, bytes > 0."""
        from pdf_generator import generate_financial_statements_pdf

        builder = FinancialStatementBuilder(grouping_with_accounts, entity_name="Trace Corp")
        statements = builder.build()
        assert len(statements.mapping_trace) > 0

        pdf_bytes = generate_financial_statements_pdf(statements)
        assert len(pdf_bytes) > 100
        assert isinstance(pdf_bytes, bytes)


# =============================================================================
# TestSprint488Enhancements
# =============================================================================


class TestSprint488Ratios:
    """Tests for Sprint 488: new ratio fields and prior period support."""

    def test_depreciation_extraction(self, grouping_with_accounts):
        """Depreciation detected from account names in lead sheet N."""
        builder = FinancialStatementBuilder(grouping_with_accounts)
        result = builder.build()
        # grouping_with_accounts has "Depreciation Expense" in N with debit=10K
        assert result.depreciation_amount == 10000.0

    def test_depreciation_zero_when_absent(self, sample_lead_sheet_grouping):
        """No depreciation accounts → 0.0."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()
        assert result.depreciation_amount == 0.0

    def test_interest_expense_extraction(self):
        """Interest expense detected from account names in lead sheet O."""
        grouping = {
            "summaries": [
                {
                    "lead_sheet": "O",
                    "name": "Other Income & Expense",
                    "net_balance": 3000.0,
                    "account_count": 2,
                    "accounts": [
                        {"name": "Interest Expense", "debit": 5000.0, "credit": 0.0, "net_balance": 5000.0},
                        {"name": "Other Income", "debit": 0.0, "credit": 2000.0, "net_balance": -2000.0},
                    ],
                },
            ],
        }
        builder = FinancialStatementBuilder(grouping)
        result = builder.build()
        assert result.interest_expense == 5000.0

    def test_interest_expense_zero_when_absent(self, sample_lead_sheet_grouping):
        """No interest accounts → 0.0."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()
        assert result.interest_expense == 0.0

    def test_has_prior_period_false_by_default(self, sample_lead_sheet_grouping):
        """No prior grouping → has_prior_period=False."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()
        assert result.has_prior_period is False

    def test_has_prior_period_true_with_prior(self, sample_lead_sheet_grouping):
        """Prior grouping provided → has_prior_period=True."""
        prior = {
            "summaries": [
                {"lead_sheet": "A", "name": "Cash", "net_balance": 40000.0, "accounts": []},
            ],
        }
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping, prior_lead_sheet_grouping=prior)
        result = builder.build()
        assert result.has_prior_period is True

    def test_prior_amounts_on_balance_sheet(self, sample_lead_sheet_grouping):
        """Balance sheet items have prior_amount when prior data provided."""
        prior = {
            "summaries": [
                {"lead_sheet": "A", "name": "Cash", "net_balance": 40000.0, "accounts": []},
                {"lead_sheet": "B", "name": "Receivables", "net_balance": 25000.0, "accounts": []},
            ],
        }
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping, prior_lead_sheet_grouping=prior)
        result = builder.build()
        bs_items = {item.lead_sheet_ref: item for item in result.balance_sheet if item.lead_sheet_ref}
        assert bs_items["A"].prior_amount == 40000.0
        assert bs_items["B"].prior_amount == 25000.0

    def test_prior_amounts_none_without_prior(self, sample_lead_sheet_grouping):
        """Balance sheet items have prior_amount=None without prior data."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()
        for item in result.balance_sheet:
            assert item.prior_amount is None

    def test_prior_income_statement_amounts(self, sample_lead_sheet_grouping):
        """Income statement items have prior_amount when prior data provided."""
        prior = {
            "summaries": [
                {"lead_sheet": "L", "name": "Revenue", "net_balance": -120000.0, "accounts": []},
                {"lead_sheet": "M", "name": "COGS", "net_balance": 50000.0, "accounts": []},
            ],
        }
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping, prior_lead_sheet_grouping=prior)
        result = builder.build()
        is_items = {item.lead_sheet_ref: item for item in result.income_statement if item.lead_sheet_ref}
        assert is_items["L"].prior_amount == 120000.0  # sign-flipped
        assert is_items["M"].prior_amount == 50000.0

    def test_to_dict_includes_new_fields(self, sample_lead_sheet_grouping):
        """to_dict includes depreciation_amount, interest_expense, has_prior_period."""
        builder = FinancialStatementBuilder(sample_lead_sheet_grouping)
        result = builder.build()
        d = result.to_dict()
        assert "depreciation_amount" in d
        assert "interest_expense" in d
        assert "has_prior_period" in d
        assert d["has_prior_period"] is False

    def test_pdf_with_prior_period(self, sample_lead_sheet_grouping):
        """PDF generates without error when prior data is provided."""
        from pdf_generator import generate_financial_statements_pdf

        prior = {
            "summaries": [
                {"lead_sheet": "A", "name": "Cash", "net_balance": 40000.0, "accounts": []},
                {"lead_sheet": "B", "name": "Receivables", "net_balance": 25000.0, "accounts": []},
                {"lead_sheet": "L", "name": "Revenue", "net_balance": -120000.0, "accounts": []},
                {"lead_sheet": "M", "name": "COGS", "net_balance": 50000.0, "accounts": []},
            ],
        }
        builder = FinancialStatementBuilder(
            sample_lead_sheet_grouping,
            entity_name="Prior Test Corp",
            prior_lead_sheet_grouping=prior,
        )
        statements = builder.build()
        pdf_bytes = generate_financial_statements_pdf(statements)
        assert len(pdf_bytes) > 100
        assert isinstance(pdf_bytes, bytes)


class TestMappingTraceExcel:
    """Tests for mapping trace in Excel generation."""

    def test_excel_has_mapping_trace_tab(self, grouping_with_accounts):
        """Excel has 'Mapping Trace' in sheetnames."""
        from openpyxl import load_workbook

        from excel_generator import generate_financial_statements_excel

        builder = FinancialStatementBuilder(grouping_with_accounts, entity_name="Trace Corp")
        statements = builder.build()

        excel_bytes = generate_financial_statements_excel(statements)
        wb = load_workbook(BytesIO(excel_bytes))
        assert "Mapping Trace" in wb.sheetnames


# =============================================================================
# Sprint 803 — finding A-5: the depreciation add-back and EBITDA
# =============================================================================


def _production_grouping(accounts: list[dict]) -> dict:
    """
    Build a grouping dict the way production does.

    Every test below goes through `group_by_lead_sheet` →
    `lead_sheet_grouping_to_dict` rather than hand-writing the dict, because
    finding A-5 survived for the life of the product behind a hand-written
    fixture: `grouping_with_accounts` keys its depreciation account `name`
    while both of its siblings are keyed `account`, so the one account the
    old depreciation test read was the only one in the fixture keyed the way
    production never emits. The test passed; the product returned 0.0.
    """
    from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict

    return lead_sheet_grouping_to_dict(group_by_lead_sheet(accounts))


def _tb(*rows: tuple[str, float, float]) -> list[dict]:
    return [{"account": name, "debit": Decimal(str(dr)), "credit": Decimal(str(cr))} for name, dr, cr in rows]


class TestSprint803DepreciationAddBack:
    """A-5: `_extract_depreciation` read a key the serialized grouping never carries."""

    def test_add_back_appears_on_a_production_shaped_grouping(self):
        """The regression pin: a TB with a depreciation account produces an add-back."""
        grouping = _production_grouping(
            _tb(
                ("Cash - Operating", 120000, 0),
                ("Equipment", 200000, 0),
                ("Common Stock", 0, 100000),
                ("Sales Revenue", 0, 500000),
                ("Rent Expense", 90000, 0),
                ("Depreciation Expense", 30000, 0),
            )
        )
        builder = FinancialStatementBuilder(grouping)

        assert builder._extract_depreciation() == 30000.0

        statements = builder.build()
        assert statements.depreciation_amount == 30000.0

        labels = [item.label for item in statements.cash_flow_statement.operating.items]
        assert "Depreciation & Amortization" in labels
        # The hedging note must not fire when the add-back was found.
        assert "Depreciation not separately identified in trial balance" not in statements.cash_flow_statement.notes

    def test_ebitda_exceeds_operating_income_when_depreciation_is_present(self):
        """
        `pdf/sections/ratios.py` computes `ebitda = operating_income + depreciation_amount`.
        While A-5 was live that term was always 0.0, so every exported ratio PDF
        reported EBITDA equal to operating income.
        """
        grouping = _production_grouping(
            _tb(
                ("Cash - Operating", 120000, 0),
                ("Common Stock", 0, 100000),
                ("Sales Revenue", 0, 500000),
                ("Rent Expense", 90000, 0),
                ("Depreciation Expense", 30000, 0),
            )
        )
        statements = FinancialStatementBuilder(grouping).build()

        ebitda = statements.operating_income + statements.depreciation_amount
        assert statements.depreciation_amount == 30000.0
        assert ebitda > statements.operating_income
        assert ebitda == pytest.approx(statements.operating_income + 30000.0)

    def test_accumulated_depreciation_alone_adds_back_nothing(self):
        """
        Pins the contra guard. With the key fixed, lead sheet E matches
        `accumulated depreciation` — a cumulative contra-asset. Adding that
        back would be a worse number than the 0.0 the defect produced.
        """
        grouping = _production_grouping(
            _tb(
                ("Cash - Operating", 120000, 0),
                ("Equipment", 200000, 0),
                ("Accumulated Depreciation", 0, 60000),
                ("Common Stock", 0, 100000),
                ("Sales Revenue", 0, 500000),
                ("Rent Expense", 90000, 0),
            )
        )
        builder = FinancialStatementBuilder(grouping)

        assert builder._extract_depreciation() == 0.0
        statements = builder.build()
        assert statements.depreciation_amount == 0.0
        # With nothing to add back, the data-quality note is now a truthful
        # observation about the input rather than a disguised defect.
        assert "Depreciation not separately identified in trial balance" in statements.cash_flow_statement.notes

    def test_accumulated_is_excluded_while_the_expense_line_is_added_back(self):
        """Both present: the expense is added back, the contra-asset is not."""
        grouping = _production_grouping(
            _tb(
                ("Equipment", 200000, 0),
                ("Accumulated Depreciation", 0, 60000),
                ("Sales Revenue", 0, 500000),
                ("Depreciation Expense", 30000, 0),
            )
        )
        assert FinancialStatementBuilder(grouping)._extract_depreciation() == 30000.0

    def test_depreciation_and_amortization_are_both_added_back(self):
        """
        The defect returned on first match. A trial balance carrying separate
        depreciation and amortization lines must add back both.
        """
        grouping = _production_grouping(
            _tb(
                ("Sales Revenue", 0, 500000),
                ("Depreciation Expense", 30000, 0),
                ("Amortization Expense", 10000, 0),
            )
        )
        assert FinancialStatementBuilder(grouping)._extract_depreciation() == 40000.0

    def test_the_serialized_grouping_carries_account_and_not_name(self):
        """
        The root cause, asserted directly. If a future change to
        `lead_sheet_grouping_to_dict` renames this key, this test says so
        rather than letting the add-back silently return to 0.0.
        """
        grouping = _production_grouping(_tb(("Depreciation Expense", 30000, 0)))
        account = grouping["summaries"][0]["accounts"][0]

        assert "account" in account
        assert "name" not in account
