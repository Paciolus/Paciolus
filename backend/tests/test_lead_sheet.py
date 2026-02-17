"""
Tests for Lead Sheet Mapping Module.

Sprint 50: Lead Sheet Mapping

Tests cover:
- Lead sheet assignment from keywords
- Category fallback mapping
- Account grouping by lead sheet
- Override functionality
"""

import pytest

from classification_rules import AccountCategory
from lead_sheet_mapping import (
    LEAD_SHEET_CATEGORY,
    LEAD_SHEET_NAMES,
    LeadSheet,
    assign_lead_sheet,
    get_lead_sheet_options,
    group_by_lead_sheet,
    lead_sheet_grouping_to_dict,
)

# =============================================================================
# LEAD SHEET ASSIGNMENT TESTS
# =============================================================================

class TestLeadSheetAssignment:
    """Tests for assign_lead_sheet function."""

    # -------------------------------------------------------------------------
    # A: Cash and Cash Equivalents
    # -------------------------------------------------------------------------
    def test_cash_maps_to_A(self):
        result = assign_lead_sheet("Cash")
        assert result.lead_sheet == LeadSheet.A
        assert result.confidence >= 0.9

    def test_petty_cash_maps_to_A(self):
        result = assign_lead_sheet("Petty Cash")
        assert result.lead_sheet == LeadSheet.A

    def test_bank_checking_maps_to_A(self):
        result = assign_lead_sheet("Bank - Checking Account")
        assert result.lead_sheet == LeadSheet.A

    def test_savings_account_maps_to_A(self):
        result = assign_lead_sheet("Savings Account")
        assert result.lead_sheet == LeadSheet.A

    # -------------------------------------------------------------------------
    # B: Receivables
    # -------------------------------------------------------------------------
    def test_accounts_receivable_maps_to_B(self):
        result = assign_lead_sheet("Accounts Receivable")
        assert result.lead_sheet == LeadSheet.B
        assert result.confidence >= 0.9

    def test_ar_maps_to_B(self):
        result = assign_lead_sheet("A/R - Trade")
        assert result.lead_sheet == LeadSheet.B

    def test_allowance_doubtful_maps_to_B(self):
        result = assign_lead_sheet("Allowance for Doubtful Accounts")
        assert result.lead_sheet == LeadSheet.B

    def test_notes_receivable_maps_to_B(self):
        result = assign_lead_sheet("Notes Receivable")
        assert result.lead_sheet == LeadSheet.B

    # -------------------------------------------------------------------------
    # C: Inventory
    # -------------------------------------------------------------------------
    def test_inventory_maps_to_C(self):
        result = assign_lead_sheet("Inventory")
        assert result.lead_sheet == LeadSheet.C

    def test_raw_materials_maps_to_C(self):
        result = assign_lead_sheet("Raw Material Inventory")
        assert result.lead_sheet == LeadSheet.C

    def test_wip_maps_to_C(self):
        result = assign_lead_sheet("Work in Progress")
        assert result.lead_sheet == LeadSheet.C

    def test_finished_goods_maps_to_C(self):
        result = assign_lead_sheet("Finished Goods Inventory")
        assert result.lead_sheet == LeadSheet.C

    # -------------------------------------------------------------------------
    # D: Prepaid Expenses
    # -------------------------------------------------------------------------
    def test_prepaid_expense_maps_to_D(self):
        result = assign_lead_sheet("Prepaid Expense")
        assert result.lead_sheet == LeadSheet.D

    def test_prepaid_insurance_maps_to_D(self):
        result = assign_lead_sheet("Prepaid Insurance")
        assert result.lead_sheet == LeadSheet.D

    def test_security_deposit_maps_to_D(self):
        result = assign_lead_sheet("Security Deposit")
        assert result.lead_sheet == LeadSheet.D

    # -------------------------------------------------------------------------
    # E: Property, Plant & Equipment
    # -------------------------------------------------------------------------
    def test_equipment_maps_to_E(self):
        result = assign_lead_sheet("Office Equipment")
        assert result.lead_sheet == LeadSheet.E

    def test_building_maps_to_E(self):
        result = assign_lead_sheet("Building")
        assert result.lead_sheet == LeadSheet.E

    def test_land_maps_to_E(self):
        result = assign_lead_sheet("Land")
        assert result.lead_sheet == LeadSheet.E

    def test_accumulated_depreciation_maps_to_E(self):
        result = assign_lead_sheet("Accumulated Depreciation - Equipment")
        assert result.lead_sheet == LeadSheet.E

    def test_vehicle_maps_to_E(self):
        result = assign_lead_sheet("Vehicle - Delivery Truck")
        assert result.lead_sheet == LeadSheet.E

    # -------------------------------------------------------------------------
    # F: Other Assets / Intangibles
    # -------------------------------------------------------------------------
    def test_goodwill_maps_to_F(self):
        result = assign_lead_sheet("Goodwill")
        assert result.lead_sheet == LeadSheet.F

    def test_patent_maps_to_F(self):
        result = assign_lead_sheet("Patent")
        assert result.lead_sheet == LeadSheet.F

    def test_software_maps_to_F(self):
        result = assign_lead_sheet("Software License")
        assert result.lead_sheet == LeadSheet.F

    def test_investment_maps_to_F(self):
        result = assign_lead_sheet("Long-term Investment")
        assert result.lead_sheet == LeadSheet.F

    # -------------------------------------------------------------------------
    # G: Accounts Payable
    # -------------------------------------------------------------------------
    def test_accounts_payable_maps_to_G(self):
        result = assign_lead_sheet("Accounts Payable")
        assert result.lead_sheet == LeadSheet.G

    def test_ap_maps_to_G(self):
        result = assign_lead_sheet("A/P - Trade")
        assert result.lead_sheet == LeadSheet.G

    def test_accrued_expense_maps_to_G(self):
        result = assign_lead_sheet("Accrued Expenses")
        assert result.lead_sheet == LeadSheet.G

    def test_wages_payable_maps_to_G(self):
        result = assign_lead_sheet("Wages Payable")
        assert result.lead_sheet == LeadSheet.G

    # -------------------------------------------------------------------------
    # H: Other Current Liabilities
    # -------------------------------------------------------------------------
    def test_unearned_revenue_maps_to_H(self):
        result = assign_lead_sheet("Unearned Revenue")
        assert result.lead_sheet == LeadSheet.H

    def test_deferred_revenue_maps_to_H(self):
        result = assign_lead_sheet("Deferred Revenue")
        assert result.lead_sheet == LeadSheet.H

    def test_sales_tax_payable_maps_to_H(self):
        result = assign_lead_sheet("Sales Tax Payable")
        assert result.lead_sheet == LeadSheet.H

    # -------------------------------------------------------------------------
    # I: Long-term Debt
    # -------------------------------------------------------------------------
    def test_long_term_debt_maps_to_I(self):
        result = assign_lead_sheet("Long-term Debt")
        assert result.lead_sheet == LeadSheet.I

    def test_mortgage_maps_to_I(self):
        result = assign_lead_sheet("Mortgage Payable")
        assert result.lead_sheet == LeadSheet.I

    def test_bank_loan_maps_to_I(self):
        result = assign_lead_sheet("Bank Loan")
        assert result.lead_sheet == LeadSheet.I

    # -------------------------------------------------------------------------
    # J: Other Long-term Liabilities
    # -------------------------------------------------------------------------
    def test_deferred_tax_liability_maps_to_J(self):
        result = assign_lead_sheet("Deferred Tax Liability")
        assert result.lead_sheet == LeadSheet.J

    def test_pension_liability_maps_to_J(self):
        result = assign_lead_sheet("Pension Liability")
        assert result.lead_sheet == LeadSheet.J

    # -------------------------------------------------------------------------
    # K: Equity
    # -------------------------------------------------------------------------
    def test_common_stock_maps_to_K(self):
        result = assign_lead_sheet("Common Stock")
        assert result.lead_sheet == LeadSheet.K

    def test_retained_earnings_maps_to_K(self):
        result = assign_lead_sheet("Retained Earnings")
        assert result.lead_sheet == LeadSheet.K

    def test_paid_in_capital_maps_to_K(self):
        result = assign_lead_sheet("Additional Paid-in Capital")
        assert result.lead_sheet == LeadSheet.K

    def test_treasury_stock_maps_to_K(self):
        result = assign_lead_sheet("Treasury Stock")
        assert result.lead_sheet == LeadSheet.K

    # -------------------------------------------------------------------------
    # L: Revenue
    # -------------------------------------------------------------------------
    def test_revenue_maps_to_L(self):
        result = assign_lead_sheet("Revenue")
        assert result.lead_sheet == LeadSheet.L

    def test_sales_maps_to_L(self):
        result = assign_lead_sheet("Sales")
        assert result.lead_sheet == LeadSheet.L

    def test_service_revenue_maps_to_L(self):
        result = assign_lead_sheet("Service Revenue")
        assert result.lead_sheet == LeadSheet.L

    # -------------------------------------------------------------------------
    # M: Cost of Goods Sold
    # -------------------------------------------------------------------------
    def test_cogs_maps_to_M(self):
        result = assign_lead_sheet("Cost of Goods Sold")
        assert result.lead_sheet == LeadSheet.M

    def test_cost_of_sales_maps_to_M(self):
        result = assign_lead_sheet("Cost of Sales")
        assert result.lead_sheet == LeadSheet.M

    def test_direct_labor_maps_to_M(self):
        result = assign_lead_sheet("Direct Labor")
        assert result.lead_sheet == LeadSheet.M

    # -------------------------------------------------------------------------
    # N: Operating Expenses
    # -------------------------------------------------------------------------
    def test_salary_expense_maps_to_N(self):
        result = assign_lead_sheet("Salary Expense")
        assert result.lead_sheet == LeadSheet.N

    def test_rent_expense_maps_to_N(self):
        result = assign_lead_sheet("Rent Expense")
        assert result.lead_sheet == LeadSheet.N

    def test_depreciation_expense_maps_to_N(self):
        result = assign_lead_sheet("Depreciation Expense")
        assert result.lead_sheet == LeadSheet.N

    def test_utilities_maps_to_N(self):
        result = assign_lead_sheet("Utilities Expense")
        assert result.lead_sheet == LeadSheet.N

    # -------------------------------------------------------------------------
    # O: Other Income/Expense
    # -------------------------------------------------------------------------
    def test_interest_income_maps_to_O(self):
        result = assign_lead_sheet("Interest Income")
        assert result.lead_sheet == LeadSheet.O

    def test_interest_expense_maps_to_O(self):
        result = assign_lead_sheet("Interest Expense")
        assert result.lead_sheet == LeadSheet.O

    def test_gain_on_sale_maps_to_O(self):
        result = assign_lead_sheet("Gain on Sale of Equipment")
        assert result.lead_sheet == LeadSheet.O

    def test_income_tax_expense_maps_to_O(self):
        result = assign_lead_sheet("Income Tax Expense")
        assert result.lead_sheet == LeadSheet.O


class TestLeadSheetFallback:
    """Tests for category-based fallback assignment."""

    def test_unknown_account_uses_category_fallback(self):
        result = assign_lead_sheet("Widget Assembly 12345", AccountCategory.ASSET)
        assert result.lead_sheet == LeadSheet.F  # Other Assets fallback
        assert result.confidence == 0.5

    def test_liability_fallback(self):
        result = assign_lead_sheet("Unknown Obligation", AccountCategory.LIABILITY)
        assert result.lead_sheet == LeadSheet.J  # Other Liabilities fallback

    def test_equity_fallback(self):
        result = assign_lead_sheet("Member Contribution XYZ", AccountCategory.EQUITY)
        assert result.lead_sheet == LeadSheet.K

    def test_revenue_fallback(self):
        result = assign_lead_sheet("Misc Income 2025", AccountCategory.REVENUE)
        assert result.lead_sheet == LeadSheet.L

    def test_expense_fallback(self):
        result = assign_lead_sheet("Random Cost Item", AccountCategory.EXPENSE)
        assert result.lead_sheet == LeadSheet.N

    def test_unknown_category_maps_to_Z(self):
        result = assign_lead_sheet("Totally Unknown Account", AccountCategory.UNKNOWN)
        assert result.lead_sheet == LeadSheet.Z

    def test_no_category_no_match_maps_to_Z(self):
        result = assign_lead_sheet("XYZZY12345")
        assert result.lead_sheet == LeadSheet.Z
        assert result.confidence == 0.0


class TestLeadSheetOverride:
    """Tests for manual lead sheet override."""

    def test_override_takes_precedence(self):
        # Cash would normally map to A, but override to K
        result = assign_lead_sheet("Cash", override=LeadSheet.K)
        assert result.lead_sheet == LeadSheet.K
        assert result.confidence == 1.0
        assert result.is_override is True

    def test_override_with_unknown_account(self):
        result = assign_lead_sheet("Unknown XYZ", override=LeadSheet.B)
        assert result.lead_sheet == LeadSheet.B
        assert result.is_override is True


# =============================================================================
# LEAD SHEET GROUPING TESTS
# =============================================================================

class TestLeadSheetGrouping:
    """Tests for group_by_lead_sheet function."""

    @pytest.fixture
    def sample_accounts(self):
        return [
            {'account': 'Cash', 'debit': 10000, 'credit': 0, 'type': 'asset'},
            {'account': 'Accounts Receivable', 'debit': 5000, 'credit': 0, 'type': 'asset'},
            {'account': 'Inventory', 'debit': 8000, 'credit': 0, 'type': 'asset'},
            {'account': 'Accounts Payable', 'debit': 0, 'credit': 3000, 'type': 'liability'},
            {'account': 'Common Stock', 'debit': 0, 'credit': 10000, 'type': 'equity'},
            {'account': 'Retained Earnings', 'debit': 0, 'credit': 5000, 'type': 'equity'},
            {'account': 'Sales', 'debit': 0, 'credit': 20000, 'type': 'revenue'},
            {'account': 'Salary Expense', 'debit': 15000, 'credit': 0, 'type': 'expense'},
        ]

    def test_grouping_creates_summaries(self, sample_accounts):
        result = group_by_lead_sheet(sample_accounts)
        assert len(result.summaries) > 0

    def test_grouping_calculates_totals(self, sample_accounts):
        result = group_by_lead_sheet(sample_accounts)
        assert result.total_debits == 38000  # 10000+5000+8000+15000
        assert result.total_credits == 38000  # 3000+10000+5000+20000

    def test_grouping_separates_lead_sheets(self, sample_accounts):
        result = group_by_lead_sheet(sample_accounts)
        lead_sheets = [s.lead_sheet for s in result.summaries]

        # Should have at least A (Cash), B (Receivables), C (Inventory), G (Payables), K (Equity), L (Revenue), N (Expenses)
        assert LeadSheet.A in lead_sheets
        assert LeadSheet.B in lead_sheets
        assert LeadSheet.C in lead_sheets
        assert LeadSheet.G in lead_sheets
        assert LeadSheet.K in lead_sheets
        assert LeadSheet.L in lead_sheets
        assert LeadSheet.N in lead_sheets

    def test_grouping_summary_has_correct_counts(self, sample_accounts):
        result = group_by_lead_sheet(sample_accounts)

        # Find equity summary (K)
        equity_summary = next(s for s in result.summaries if s.lead_sheet == LeadSheet.K)
        assert equity_summary.account_count == 2  # Common Stock + Retained Earnings

    def test_grouping_calculates_net_balance(self, sample_accounts):
        result = group_by_lead_sheet(sample_accounts)

        # Cash should have positive net balance (debit - credit)
        cash_summary = next(s for s in result.summaries if s.lead_sheet == LeadSheet.A)
        assert cash_summary.net_balance == 10000

    def test_grouping_with_overrides(self, sample_accounts):
        # Override Cash to go to lead sheet F instead of A
        overrides = {'Cash': LeadSheet.F}
        result = group_by_lead_sheet(sample_accounts, overrides)

        # Cash should now be in F, not A
        lead_sheets = {s.lead_sheet: s for s in result.summaries}

        if LeadSheet.A in lead_sheets:
            # A shouldn't have Cash
            a_accounts = [acc['account'] for acc in lead_sheets[LeadSheet.A].accounts]
            assert 'Cash' not in a_accounts

        # F should have Cash
        assert LeadSheet.F in lead_sheets
        f_accounts = [acc['account'] for acc in lead_sheets[LeadSheet.F].accounts]
        assert 'Cash' in f_accounts

    def test_empty_accounts_returns_empty_summaries(self):
        result = group_by_lead_sheet([])
        assert result.summaries == []
        assert result.total_debits == 0
        assert result.total_credits == 0


class TestLeadSheetSerialization:
    """Tests for serialization functions."""

    def test_grouping_to_dict(self):
        accounts = [
            {'account': 'Cash', 'debit': 1000, 'credit': 0, 'type': 'asset'},
            {'account': 'Revenue', 'debit': 0, 'credit': 1000, 'type': 'revenue'},
        ]
        grouping = group_by_lead_sheet(accounts)
        result = lead_sheet_grouping_to_dict(grouping)

        assert 'summaries' in result
        assert 'total_debits' in result
        assert 'total_credits' in result
        assert result['total_debits'] == 1000
        assert result['total_credits'] == 1000

    def test_summary_dict_has_required_fields(self):
        accounts = [{'account': 'Cash', 'debit': 100, 'credit': 0, 'type': 'asset'}]
        grouping = group_by_lead_sheet(accounts)
        result = lead_sheet_grouping_to_dict(grouping)

        summary = result['summaries'][0]
        assert 'lead_sheet' in summary
        assert 'name' in summary
        assert 'category' in summary
        assert 'total_debit' in summary
        assert 'total_credit' in summary
        assert 'net_balance' in summary
        assert 'account_count' in summary
        assert 'accounts' in summary


class TestLeadSheetOptions:
    """Tests for get_lead_sheet_options function."""

    def test_returns_all_lead_sheets(self):
        options = get_lead_sheet_options()
        assert len(options) == len(LeadSheet)

    def test_options_have_required_fields(self):
        options = get_lead_sheet_options()
        for opt in options:
            assert 'value' in opt
            assert 'label' in opt
            assert 'category' in opt

    def test_options_are_sorted_by_letter(self):
        options = get_lead_sheet_options()
        values = [opt['value'] for opt in options]
        assert values == sorted(values)


class TestLeadSheetConstants:
    """Tests for lead sheet constants."""

    def test_all_lead_sheets_have_names(self):
        for ls in LeadSheet:
            assert ls in LEAD_SHEET_NAMES
            assert LEAD_SHEET_NAMES[ls] != ""

    def test_all_lead_sheets_have_categories(self):
        for ls in LeadSheet:
            assert ls in LEAD_SHEET_CATEGORY
            assert LEAD_SHEET_CATEGORY[ls] != ""
