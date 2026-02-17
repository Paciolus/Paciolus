"""
Tests for Financial Statement Builder, PDF, and Excel export.
Sprint 71: Financial Statements — Backend Builder + Export
"""

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
