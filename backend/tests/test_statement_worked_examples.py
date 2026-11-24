"""
Worked examples for the financial statement builder (Sprint 867).

Review findings TQ-01, TQ-02 and TQ-03 (read-only review at ``ef5e567``).
Every expected figure here is fixed by hand from the example's own
bookkeeping, never computed from the builder's output. The frontend suite
``frontend/src/__tests__/statementWorkedExamples.test.ts`` runs the same
examples against ``useStatementBuilder`` so the two builders cannot drift.

Most trial balances uploaded to Paciolus are pre-closing: revenue and
expense accounts still hold the period's activity. A balanced pre-closing
trial balance must produce a balanced balance sheet, with the period's
result shown in equity on its own line.
"""

import re
from decimal import Decimal
from io import BytesIO

from financial_statement_builder import UNCLOSED_EARNINGS_LABEL, FinancialStatementBuilder

# Exact statement wording under review — the frontend suite asserts the same string.
EARNINGS_LABEL = "Current-Period Earnings (Not Yet Closed)"


def test_label_is_the_reviewed_wording():
    assert UNCLOSED_EARNINGS_LABEL == EARNINGS_LABEL


def make_grouping(rows: list[tuple[str, str, float, float]]) -> dict:
    """Build a serialized lead sheet grouping from (letter, account, debit, credit) rows.

    Same shape ``lead_sheet_mapping.lead_sheet_grouping_to_dict`` produces:
    accounts carry ``account``/``debit``/``credit``; the summary's
    ``net_balance`` is total debit less total credit.
    """
    by_letter: dict[str, dict] = {}
    for letter, account, debit, credit in rows:
        summary = by_letter.setdefault(
            letter,
            {
                "lead_sheet": letter,
                "name": letter,
                "category": "",
                "total_debit": 0.0,
                "total_credit": 0.0,
                "net_balance": 0.0,
                "account_count": 0,
                "accounts": [],
            },
        )
        summary["total_debit"] += debit
        summary["total_credit"] += credit
        summary["net_balance"] = summary["total_debit"] - summary["total_credit"]
        summary["account_count"] += 1
        summary["accounts"].append({"account": account, "debit": debit, "credit": credit})
    total_debits = sum(r[2] for r in rows)
    total_credits = sum(r[3] for r in rows)
    assert abs(total_debits - total_credits) < 0.005, "worked example must be a balanced trial balance"
    return {
        "summaries": [by_letter[k] for k in sorted(by_letter)],
        "total_debits": total_debits,
        "total_credits": total_credits,
        "unclassified_count": 0,
    }


def _line(lines, label):
    matches = [item for item in lines if item.label == label]
    assert len(matches) == 1, f"expected exactly one {label!r} line, got {[i.label for i in lines]}"
    return matches[0]


# =============================================================================
# TQ-01 — equity leaves out the period's earnings
# =============================================================================

# Cash 900 Dr; Expenses 300 Dr; Accounts payable 300 Cr; Opening equity 500 Cr; Revenue 400 Cr.
PROFIT_TB = [
    ("A", "Cash", 900.0, 0.0),
    ("N", "Operating Expenses", 300.0, 0.0),
    ("G", "Accounts Payable", 0.0, 300.0),
    ("K", "Opening Equity", 0.0, 500.0),
    ("L", "Revenue", 0.0, 400.0),
]

# Cash 700 Dr; Expenses 300 Dr; Accounts payable 300 Cr; Opening equity 500 Cr; Revenue 200 Cr.
LOSS_TB = [
    ("A", "Cash", 700.0, 0.0),
    ("N", "Operating Expenses", 300.0, 0.0),
    ("G", "Accounts Payable", 0.0, 300.0),
    ("K", "Opening Equity", 0.0, 500.0),
    ("L", "Revenue", 0.0, 200.0),
]


class TestPreClosingEquity:
    """TQ-01: a balanced pre-closing TB produces a balanced balance sheet."""

    def test_profit_is_included_in_equity_and_the_statement_balances(self):
        result = FinancialStatementBuilder(make_grouping(PROFIT_TB)).build()

        assert result.net_income == 100.0
        assert result.total_equity == 600.0
        assert result.total_liabilities + result.total_equity == 900.0
        assert result.balance_difference == 0.0
        assert result.is_balanced is True

    def test_loss_is_included_in_equity_and_the_statement_balances(self):
        result = FinancialStatementBuilder(make_grouping(LOSS_TB)).build()

        assert result.net_income == -100.0
        assert result.total_equity == 400.0
        assert result.total_liabilities + result.total_equity == 700.0
        assert result.balance_difference == 0.0
        assert result.is_balanced is True

    def test_the_period_result_is_its_own_labelled_line(self):
        result = FinancialStatementBuilder(make_grouping(PROFIT_TB)).build()
        bs = result.balance_sheet

        assert _line(bs, "Stockholders' Equity").amount == 500.0
        earnings = _line(bs, EARNINGS_LABEL)
        assert earnings.amount == 100.0
        assert earnings.lead_sheet_ref == ""  # computed, not a lead sheet
        assert earnings.indent_level == 1  # renders as a line item, not a header
        assert _line(bs, "TOTAL LIABILITIES & EQUITY").amount == 900.0

        labels = [i.label for i in bs]
        assert labels.index("Stockholders' Equity") + 1 == labels.index(EARNINGS_LABEL)
        assert labels.index(EARNINGS_LABEL) + 1 == labels.index("TOTAL LIABILITIES & EQUITY")

    def test_a_loss_is_shown_as_a_negative_amount_on_the_same_line(self):
        result = FinancialStatementBuilder(make_grouping(LOSS_TB)).build()
        assert _line(result.balance_sheet, EARNINGS_LABEL).amount == -100.0
        assert _line(result.balance_sheet, "TOTAL LIABILITIES & EQUITY").amount == 700.0

    def test_closed_trial_balance_has_no_unclosed_earnings_line(self):
        closed = [
            ("A", "Cash", 900.0, 0.0),
            ("G", "Accounts Payable", 0.0, 300.0),
            ("K", "Opening Equity", 0.0, 600.0),
        ]
        result = FinancialStatementBuilder(make_grouping(closed)).build()
        assert EARNINGS_LABEL not in [i.label for i in result.balance_sheet]
        assert result.total_equity == 600.0
        assert result.is_balanced is True

    def test_serialized_result_carries_the_line_and_the_totals(self):
        d = FinancialStatementBuilder(make_grouping(PROFIT_TB)).build().to_dict()
        assert d["total_equity"] == 600.0
        assert d["is_balanced"] is True
        assert d["balance_difference"] == 0.0
        earnings = [i for i in d["balance_sheet"] if i["label"] == EARNINGS_LABEL]
        assert len(earnings) == 1 and earnings[0]["amount"] == 100.0

    def test_prior_period_equity_carries_its_own_unclosed_earnings(self):
        result = FinancialStatementBuilder(
            make_grouping(PROFIT_TB), prior_lead_sheet_grouping=make_grouping(LOSS_TB)
        ).build()
        assert result.prior_total_equity == 400.0
        assert _line(result.balance_sheet, EARNINGS_LABEL).prior_amount == -100.0
        assert _line(result.balance_sheet, "TOTAL LIABILITIES & EQUITY").prior_amount == 700.0

    def test_pdf_text_shows_the_line_and_a_balanced_statement(self):
        from pypdf import PdfReader

        from pdf_generator import generate_financial_statements_pdf

        statements = FinancialStatementBuilder(make_grouping(PROFIT_TB), entity_name="Worked Example").build()
        reader = PdfReader(BytesIO(generate_financial_statements_pdf(statements)))
        text = re.sub(r"\s+", " ", " ".join(page.extract_text() or "" for page in reader.pages))

        assert EARNINGS_LABEL in text
        assert re.search(re.escape(EARNINGS_LABEL) + r"[ .]*\$100\.00", text)
        assert re.search(r"TOTAL LIABILITIES & EQUITY[ .]*\$900\.00", text)
        assert "OUT OF BALANCE" not in text

    def test_excel_cells_show_the_line_and_a_balanced_statement(self):
        from openpyxl import load_workbook

        from excel_generator import generate_financial_statements_excel

        statements = FinancialStatementBuilder(make_grouping(PROFIT_TB)).build()
        ws = load_workbook(BytesIO(generate_financial_statements_excel(statements)))["Balance Sheet"]
        cells = {
            str(row[0].value).strip(): row[1].value
            for row in ws.iter_rows(min_col=1, max_col=2)
            if row[0].value is not None
        }

        assert cells[EARNINGS_LABEL] == 100.0
        assert cells["TOTAL LIABILITIES & EQUITY"] == 900.0
        assert "✓ BALANCED" in cells
        assert not any(str(label).startswith("⚠ OUT OF BALANCE") for label in cells)

    def test_statement_equity_equals_ratio_engine_equity(self):
        """Statement equity and the equity every equity-based ratio uses are one figure."""
        from ratio_engine import RatioEngine, extract_category_totals

        for tb, expected in ((PROFIT_TB, 600.0), (LOSS_TB, 400.0)):
            categories = {"A": "asset", "N": "expense", "G": "liability", "K": "equity", "L": "revenue"}
            balances = {account: {"debit": dr, "credit": cr} for _l, account, dr, cr in tb}
            classified = {account: categories[letter] for letter, account, _dr, _cr in tb}
            ratio_equity = RatioEngine(extract_category_totals(balances, classified)).equity

            statement_equity = FinancialStatementBuilder(make_grouping(tb)).build().total_equity

            assert ratio_equity == Decimal(str(expected))
            assert statement_equity == expected


# =============================================================================
# TQ-02 — unclosed income creates a financing cash flow that didn't happen
# =============================================================================

# Opening: cash 100, equity 100.
OPENING_100 = [
    ("A", "Cash", 100.0, 0.0),
    ("K", "Owner's Capital", 0.0, 100.0),
]
# In the period, services are sold for 50 cash. Revenue is not yet closed.
SOLD_SERVICES_FOR_50 = [
    ("A", "Cash", 150.0, 0.0),
    ("K", "Owner's Capital", 0.0, 100.0),
    ("L", "Service Revenue", 0.0, 50.0),
]


def _cash_flow(current, prior):
    return FinancialStatementBuilder(make_grouping(current), prior_lead_sheet_grouping=make_grouping(prior)).build()


class TestUnclosedIncomeCashFlow:
    """TQ-02: earnings still on L-O never moved through the equity accounts."""

    def test_cash_sale_is_operating_and_nothing_is_financing(self):
        cf = _cash_flow(SOLD_SERVICES_FOR_50, OPENING_100).cash_flow_statement

        assert cf.operating.subtotal == 50.0
        assert cf.investing.subtotal == 0.0
        assert cf.financing.subtotal == 0.0
        assert cf.financing.items == []
        assert cf.net_change == 50.0
        assert cf.beginning_cash == 100.0
        assert cf.ending_cash == 150.0
        assert cf.reconciliation_difference == 0.0
        assert cf.is_reconciled is True

    def test_prior_year_earnings_closed_into_equity_are_not_financing(self):
        # Prior year-end TB, pre-closing: equity accounts 70 + revenue 30 open.
        # Closing moved the 30 into equity, so this year's equity accounts hold 100.
        prior = [
            ("A", "Cash", 100.0, 0.0),
            ("K", "Owner's Capital", 0.0, 70.0),
            ("L", "Service Revenue", 0.0, 30.0),
        ]
        cf = _cash_flow(SOLD_SERVICES_FOR_50, prior).cash_flow_statement

        assert cf.operating.subtotal == 50.0
        assert cf.financing.subtotal == 0.0
        assert cf.net_change == 50.0
        assert cf.ending_cash == 150.0
        assert cf.is_reconciled is True

    def test_a_real_owner_distribution_is_still_financing(self):
        # Same period, plus a 20 cash distribution to the owner.
        current = [
            ("A", "Cash", 130.0, 0.0),
            ("K", "Owner's Capital", 0.0, 100.0),
            ("K", "Owner Distributions", 20.0, 0.0),
            ("L", "Service Revenue", 0.0, 50.0),
        ]
        cf = _cash_flow(current, OPENING_100).cash_flow_statement

        assert cf.operating.subtotal == 50.0
        assert cf.financing.subtotal == -20.0
        assert [(i.label, i.amount) for i in cf.financing.items] == [
            ("Equity Changes (excl. Retained Earnings)", -20.0)
        ]
        assert cf.net_change == 30.0
        assert cf.ending_cash == 130.0
        assert cf.reconciliation_difference == 0.0
        assert cf.is_reconciled is True


# =============================================================================
# TQ-03 — depreciation is shown as cash from investing
# =============================================================================

PURCHASES_LABEL = "Purchases of Property, Plant & Equipment"
NOT_SEPARABLE_LABEL = "Net Change in Property, Plant & Equipment (Purchases and Disposals Not Separable)"

# Opening: cash 100, gross fixed assets 100, accumulated depreciation 20, equity 180.
FIXED_ASSET_OPENING = [
    ("A", "Cash", 100.0, 0.0),
    ("E", "Equipment", 100.0, 0.0),
    ("E", "Accumulated Depreciation", 0.0, 20.0),
    ("K", "Owner's Capital", 0.0, 180.0),
]
# In the period, depreciation of 10 and nothing else.
DEPRECIATION_ONLY = [
    ("A", "Cash", 100.0, 0.0),
    ("E", "Equipment", 100.0, 0.0),
    ("E", "Accumulated Depreciation", 0.0, 30.0),
    ("K", "Owner's Capital", 0.0, 180.0),
    ("N", "Depreciation Expense", 10.0, 0.0),
]
# Same, plus a cash purchase of fixed assets for 20.
DEPRECIATION_AND_PURCHASE = [
    ("A", "Cash", 80.0, 0.0),
    ("E", "Equipment", 120.0, 0.0),
    ("E", "Accumulated Depreciation", 0.0, 30.0),
    ("K", "Owner's Capital", 0.0, 180.0),
    ("N", "Depreciation Expense", 10.0, 0.0),
]


class TestDepreciationIsNotInvestingCash:
    """TQ-03: investing cash comes from gross fixed assets, not net."""

    def test_depreciation_alone_moves_no_cash(self):
        cf = _cash_flow(DEPRECIATION_ONLY, FIXED_ASSET_OPENING).cash_flow_statement

        add_backs = [i for i in cf.operating.items if i.label == "Depreciation & Amortization"]
        assert [i.amount for i in add_backs] == [10.0]
        assert cf.operating.subtotal == 0.0
        assert cf.investing.subtotal == 0.0
        assert cf.investing.items == []
        assert cf.financing.subtotal == 0.0
        assert cf.net_change == 0.0
        assert cf.ending_cash == 100.0
        assert cf.reconciliation_difference == 0.0
        assert cf.is_reconciled is True

    def test_a_cash_purchase_is_the_only_investing_flow(self):
        cf = _cash_flow(DEPRECIATION_AND_PURCHASE, FIXED_ASSET_OPENING).cash_flow_statement

        assert cf.operating.subtotal == 0.0
        assert [(i.label, i.amount) for i in cf.investing.items] == [(PURCHASES_LABEL, -20.0)]
        assert cf.investing.subtotal == -20.0
        assert cf.financing.subtotal == 0.0
        assert cf.net_change == -20.0
        assert cf.ending_cash == 80.0
        assert cf.reconciliation_difference == 0.0
        assert cf.is_reconciled is True

    def test_a_disposal_is_reported_as_a_limitation_not_a_capital_expenditure(self):
        # Equipment costing 30 with 15 accumulated depreciation is sold for 15 cash
        # (no gain or loss); depreciation of 10 is charged. Gross PPE falls 100 -> 70,
        # accumulated depreciation 20 + 10 - 15 = 15. Cash 100 + 15 = 115.
        current = [
            ("A", "Cash", 115.0, 0.0),
            ("E", "Equipment", 70.0, 0.0),
            ("E", "Accumulated Depreciation", 0.0, 15.0),
            ("K", "Owner's Capital", 0.0, 180.0),
            ("N", "Depreciation Expense", 10.0, 0.0),
        ]
        cf = _cash_flow(current, FIXED_ASSET_OPENING).cash_flow_statement

        assert [(i.label, i.amount) for i in cf.investing.items] == [(NOT_SEPARABLE_LABEL, 15.0)]
        assert PURCHASES_LABEL not in [i.label for i in cf.investing.items]
        assert any("cannot be told apart" in n for n in cf.notes)
        assert cf.operating.subtotal == 0.0
        assert cf.net_change == 15.0
        assert cf.ending_cash == 115.0
        assert cf.is_reconciled is True

    def test_no_line_is_labelled_capital_expenditures(self):
        for current in (DEPRECIATION_ONLY, DEPRECIATION_AND_PURCHASE):
            cf = _cash_flow(current, FIXED_ASSET_OPENING).cash_flow_statement
            assert not any("Capital Expenditures" in i.label for i in cf.investing.items)
