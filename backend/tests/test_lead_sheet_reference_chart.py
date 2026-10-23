"""
Sprint 804 — findings A-3 and A-4: measure the lead-sheet classifier against a
population, not against spot checks.

The full-spectrum review of 2026-10-22 drove `group_by_lead_sheet` with a chart
of accounts built from standard names and found:

- **19% unclassified** (13 of 68), including the entire compensation block.
  Unclassified accounts are excluded from both statements, so on a balanced
  trial balance carrying `Salaries and Wages Expense` of $300,000 the builder
  returned net income $460,000 against a true $160,000.
- **Four accounts filed to the wrong statement at confidence 0.80-0.90**, which
  is worse, because `unclassified_count` does not count a confident wrong answer.

Both defects had stood since the rules were written, because the rule table was
only ever spot-checked. These tests measure it against
`tests/reference_chart_of_accounts.py` instead, so a gap shows up as a number.
"""

from decimal import Decimal

import pytest

from lead_sheet_mapping import (
    BALANCE_SHEET_LETTERS,
    LeadSheet,
    assign_lead_sheet,
    group_by_lead_sheet,
)

from .reference_chart_of_accounts import REFERENCE_CHART

# The floor the review asked for. The reference chart currently classifies at
# 100%; this is set at 98% so that adding a genuinely hard name to the chart
# does not fail the build, while any *regression* in the rule table does.
CLASSIFICATION_FLOOR = 0.98


class TestReferenceChartClassification:
    """A-3: the population measurement."""

    def test_classification_rate_meets_the_floor(self):
        unclassified = [
            name for name, _expected in REFERENCE_CHART if assign_lead_sheet(name).lead_sheet is LeadSheet.Z
        ]
        rate = (len(REFERENCE_CHART) - len(unclassified)) / len(REFERENCE_CHART)
        assert rate >= CLASSIFICATION_FLOOR, (
            f"classification rate {rate:.1%} is below the {CLASSIFICATION_FLOOR:.0%} floor; "
            f"unclassified: {unclassified}"
        )

    def test_every_account_lands_on_its_expected_lead_sheet(self):
        wrong = [
            (name, expected, assign_lead_sheet(name).lead_sheet.value)
            for name, expected in REFERENCE_CHART
            if assign_lead_sheet(name).lead_sheet.value != expected
        ]
        assert wrong == [], f"{len(wrong)} accounts on the wrong lead sheet: {wrong}"

    @pytest.mark.parametrize(
        "account_name",
        [
            # The compensation block. Every one of these was lead sheet Z before
            # Sprint 804 — the largest expense line in a service business.
            "Salaries and Wages Expense",
            "Salaries Expense",
            "Wages Expense",
            "Officer Compensation",
            "Employee Benefits",
            "Commissions Expense",
            "Contract Labor",
            # The rest of the measured unclassified set.
            "Legal and Accounting",
            "Charitable Contributions",
            "Postage and Delivery",
        ],
    )
    def test_the_measured_unclassified_expenses_now_reach_operating_expenses(self, account_name):
        assert assign_lead_sheet(account_name).lead_sheet is LeadSheet.N

    def test_lease_liability_reaches_a_liability_lead_sheet(self):
        """A bare "Lease Liability" matched nothing, in a product that ships a lease engine."""
        assert assign_lead_sheet("Lease Liability").lead_sheet is LeadSheet.H

    def test_owners_draw_reaches_equity(self):
        """Exists in every S-corp and partnership; matched nothing."""
        assert assign_lead_sheet("Owner's Draw").lead_sheet is LeadSheet.K

    def test_consulting_income_reaches_revenue(self):
        assert assign_lead_sheet("Consulting Income").lead_sheet is LeadSheet.L


class TestStatementClassArbitration:
    """A-4: an expense must not be filed to the balance sheet."""

    def test_no_expense_suffixed_account_lands_on_a_balance_sheet_lead_sheet(self):
        """
        The structural assertion. The two exemptions below are real balance-sheet
        accounts that happen to end in "Expense"; everything else ending in an
        income-statement word belongs on the income statement.
        """
        exempt = {"Prepaid Expense", "Accrued Expenses"}
        offenders = [
            (name, assign_lead_sheet(name).lead_sheet.value, assign_lead_sheet(name).confidence)
            for name, _expected in REFERENCE_CHART
            if name not in exempt
            and name.lower().split()[-1] in ("expense", "expenses")
            and assign_lead_sheet(name).lead_sheet.value in BALANCE_SHEET_LETTERS
        ]
        assert offenders == [], f"expenses filed to the balance sheet: {offenders}"

    @pytest.mark.parametrize(
        "account_name",
        [
            "Payroll Tax Expense",  # was H — Current Liabilities, confidence 0.90
            "Bank Service Charges",  # was A — Current Assets,      confidence 0.90
            "Software Expense",  # was F — Non-Current Assets,  confidence 0.80
            "Vehicle Expense",  # was E — Non-Current Assets,  confidence 0.90
        ],
    )
    def test_the_four_measured_misfiles_now_reach_operating_expenses(self, account_name):
        assert assign_lead_sheet(account_name).lead_sheet is LeadSheet.N

    def test_notes_payable_bank_reaches_long_term_debt(self):
        """
        A fifth misfile, found by the reference-chart measurement rather than by
        the review: the single-word "bank" rule (0.90) outweighed the
        "notes payable" phrase (0.85), so long-term debt was filed as cash.
        """
        assignment = assign_lead_sheet("Notes Payable - Bank")
        assert assignment.lead_sheet is LeadSheet.I

    @pytest.mark.parametrize(
        ("account_name", "expected"),
        [
            # The exemptions. These end in an income-statement word and are
            # balance-sheet accounts anyway; the arbitration must leave them alone.
            ("Prepaid Expense", LeadSheet.D),
            ("Prepaid Expenses", LeadSheet.D),
            ("Accrued Expenses", LeadSheet.G),
            ("Accrued Expense", LeadSheet.G),
            ("Unearned Revenue", LeadSheet.H),
            ("Deferred Revenue", LeadSheet.H),
            # A balance-sheet marker anywhere in the name settles it, even when
            # no rule is written about this exact account.
            ("Accrued Payroll Expense", LeadSheet.G),
            ("Deferred Compensation", LeadSheet.J),
        ],
    )
    def test_balance_sheet_accounts_ending_in_an_income_statement_word_are_left_alone(self, account_name, expected):
        assert assign_lead_sheet(account_name).lead_sheet is expected

    def test_an_unnamed_expense_falls_back_to_operating_expenses_not_unclassified(self):
        """
        The structural backstop: a name nobody enumerated, ending in "Expense",
        reaches the income statement at reduced confidence rather than dropping
        out of the statements entirely.
        """
        assignment = assign_lead_sheet("Zymurgy Expense")
        assert assignment.lead_sheet is LeadSheet.N
        assert assignment.confidence == pytest.approx(0.70)

    def test_accrued_wages_remains_a_liability(self):
        """
        The new bare "wages" rule (0.80) must not outrank "accrued" (0.85).
        Sprint 804 added single-word compensation rules; this pins the ordering.
        """
        assert assign_lead_sheet("Accrued Wages").lead_sheet is LeadSheet.G
        assert assign_lead_sheet("Wages Payable").lead_sheet is LeadSheet.G
        assert assign_lead_sheet("Salaries Payable").lead_sheet is LeadSheet.G


class TestNetIncomeOnTheReferenceChart:
    """
    A-3 downstream: the measured consequence was a wrong net income, because
    unclassified accounts are excluded from both statements.
    """

    def test_a_salary_line_reaches_the_income_statement(self):
        """
        The review's measurement: a balanced TB containing
        `Salaries and Wages Expense` of $300,000 returned net income $460,000
        against a true $160,000 — overstated by exactly the dropped salary line.
        """
        from financial_statement_builder import FinancialStatementBuilder
        from lead_sheet_mapping import lead_sheet_grouping_to_dict

        accounts = [
            {"account": "Cash - Operating", "debit": Decimal("500000"), "credit": Decimal("0")},
            {"account": "Common Stock", "debit": Decimal("0"), "credit": Decimal("340000")},
            {"account": "Sales Revenue", "debit": Decimal("0"), "credit": Decimal("500000")},
            {"account": "Rent Expense", "debit": Decimal("40000"), "credit": Decimal("0")},
            {"account": "Salaries and Wages Expense", "debit": Decimal("300000"), "credit": Decimal("0")},
        ]
        grouping = group_by_lead_sheet(accounts)
        assert grouping.unclassified_count == 0

        statements = FinancialStatementBuilder(lead_sheet_grouping_to_dict(grouping)).build()
        # 500,000 revenue − 40,000 rent − 300,000 salaries = 160,000
        assert statements.net_income == pytest.approx(160000.0)

    def test_the_whole_reference_chart_classifies_with_nothing_unclassified(self):
        accounts = [
            {"account": name, "debit": Decimal("1000"), "credit": Decimal("0")} for name, _expected in REFERENCE_CHART
        ]
        grouping = group_by_lead_sheet(accounts)
        assert grouping.unclassified_count == 0
