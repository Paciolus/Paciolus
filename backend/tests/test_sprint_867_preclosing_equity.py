"""Sprint 867: a balanced, pre-closing trial balance must produce a balanced balance sheet.

Reproduced on production 2026-11-15: a balanced TB (debits = credits) showed
"OUT OF BALANCE by -$4,699.50", which was exactly the period's net loss. The
revenue and expense accounts had not been closed to retained earnings, so the
equity accounts excluded the period's result. A balance sheet presents equity
including it; the statement now does so as its own line.
"""

import io

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

from excel_generator import generate_financial_statements_excel
from financial_statement_builder import UNCLOSED_EARNINGS_LABEL, FinancialStatementBuilder
from pdf_generator import generate_financial_statements_pdf


def _summary(letter: str, net: float) -> dict:
    return {
        "lead_sheet": letter,
        "name": letter,
        "category": "",
        "total_debit": max(net, 0.0),
        "total_credit": max(-net, 0.0),
        "net_balance": net,
        "account_count": 1,
        "accounts": [],
    }


def _grouping(**balances: float) -> dict:
    """Lead-sheet grouping from {letter: net_balance} (debit positive)."""
    summaries = [_summary(letter, net) for letter, net in balances.items()]
    debits = sum(s["total_debit"] for s in summaries)
    credits = sum(s["total_credit"] for s in summaries)
    return {"summaries": summaries, "total_debits": debits, "total_credits": credits, "unclassified_count": 0}


# Pre-closing, profit: cash 100,000 Dr; equity 80,000 Cr; revenue 50,000 Cr; opex 30,000 Dr.
# Debits 130,000 = credits 130,000. Net income 20,000 sits outside equity.
PRE_CLOSING_PROFIT = _grouping(A=100_000.0, K=-80_000.0, L=-50_000.0, N=30_000.0)
# Pre-closing, loss (the production shape): equity 110,000 Cr; revenue 20,000 Cr; opex 30,000 Dr.
PRE_CLOSING_LOSS = _grouping(A=100_000.0, K=-110_000.0, L=-20_000.0, N=30_000.0)


def _equity_line(statements):
    return [item for item in statements.balance_sheet if item.label == UNCLOSED_EARNINGS_LABEL]


def _line(statements, label: str):
    [item] = [item for item in statements.balance_sheet if item.label == label]
    return item


@pytest.mark.parametrize(
    ("grouping", "net_income", "equity_accounts"),
    [(PRE_CLOSING_PROFIT, 20_000.0, 80_000.0), (PRE_CLOSING_LOSS, -10_000.0, 110_000.0)],
    ids=["profit", "loss"],
)
def test_balanced_pre_closing_tb_balances(grouping, net_income, equity_accounts):
    assert grouping["total_debits"] == grouping["total_credits"]
    result = FinancialStatementBuilder(grouping).build()

    assert result.net_income == net_income
    assert result.is_balanced is True
    assert abs(result.balance_difference) < 0.01
    assert result.total_equity == equity_accounts + net_income
    [line] = _equity_line(result)
    assert line.amount == net_income
    assert line.lead_sheet_ref == ""  # not a lead sheet; the mapping trace stays K-only
    assert _line(result, "TOTAL LIABILITIES & EQUITY").amount == _line(result, "TOTAL ASSETS").amount
    assert result.is_pre_closing is True
    assert f"${abs(net_income):,.2f}" in result.pre_closing_note
    assert ("net loss" if net_income < 0 else "net income") in result.pre_closing_note
    assert "-$" not in result.pre_closing_note


def test_closed_books_get_no_line():
    # Equity already includes the period's result: A = L + E without the income accounts.
    closed = _grouping(A=100_000.0, K=-100_000.0, L=-50_000.0, N=30_000.0)
    result = FinancialStatementBuilder(closed).build()
    assert _equity_line(result) == []
    assert result.is_balanced is True
    assert result.total_equity == 100_000.0
    assert result.is_pre_closing is False
    assert result.pre_closing_note == ""


def test_no_income_statement_balances_get_no_line():
    result = FinancialStatementBuilder(_grouping(A=100_000.0, K=-100_000.0)).build()
    assert _equity_line(result) == []
    assert result.is_pre_closing is False


def test_genuinely_unbalanced_tb_still_reports_what_remains():
    # Same open earnings, but equity is 20,000 short: the TB itself does not balance.
    off = _grouping(A=100_000.0, K=-60_000.0, L=-50_000.0, N=30_000.0)
    assert off["total_debits"] != off["total_credits"]
    result = FinancialStatementBuilder(off).build()
    [line] = _equity_line(result)
    assert line.amount == 20_000.0
    assert result.is_balanced is False
    assert result.balance_difference == 20_000.0


def test_prior_period_pre_closing_is_presented_too():
    prior = _grouping(A=90_000.0, K=-80_000.0, L=-40_000.0, N=30_000.0)  # prior NI 10,000, unclosed
    result = FinancialStatementBuilder(PRE_CLOSING_PROFIT, prior_lead_sheet_grouping=prior).build()
    [line] = _equity_line(result)
    assert line.prior_amount == 10_000.0
    assert result.prior_total_equity == 90_000.0
    assert _line(result, "TOTAL LIABILITIES & EQUITY").prior_amount == 90_000.0


def _retained_earnings(soce):
    [re] = [c for c in soce.components if c.component_type == "retained_earnings"]
    return re


def test_soce_ending_equity_equals_the_balance_sheet_without_a_plug():
    # Review finding: retained earnings got the NI allocation but its ending
    # balance excluded it, so other_movement plugged -NI and SOCE ending equity
    # disagreed with the balance sheet by NI.
    result = FinancialStatementBuilder(PRE_CLOSING_PROFIT).build()
    soce = result.statement_of_changes_in_equity
    assert soce is not None
    assert soce.ending_total_equity == result.total_equity == 100_000.0
    re = _retained_earnings(soce)
    assert re.net_income_allocation == 20_000.0
    assert re.other_movement == 0.0


def test_soce_with_unclosed_prior_period_rolls_forward():
    prior = _grouping(A=90_000.0, K=-80_000.0, L=-40_000.0, N=30_000.0)  # prior NI 10,000, unclosed
    result = FinancialStatementBuilder(PRE_CLOSING_PROFIT, prior_lead_sheet_grouping=prior).build()
    soce = result.statement_of_changes_in_equity
    assert soce.beginning_total_equity == 90_000.0
    assert soce.ending_total_equity == 100_000.0
    assert _retained_earnings(soce).beginning_balance == 10_000.0


def _real_grouping(rows: list[tuple[str, float, float, str]]) -> dict:
    """A grouping produced by the real serializer, as uploads and export payloads carry it."""
    from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict

    accounts = [
        {"account": name, "debit": debit, "credit": credit, "type": acct_type, "type_supplied": True}
        for name, debit, credit, acct_type in rows
    ]
    return lead_sheet_grouping_to_dict(group_by_lead_sheet(accounts))


def test_soce_reads_equity_accounts_from_real_serialized_groupings():
    # Found during the 867 review: the SOCE read `name` / `net_balance`, which
    # serialized accounts do not carry, so it skipped every real equity account.
    grouping = _real_grouping(
        [
            ("Cash - Operating", 100_000.0, 0.0, "asset"),
            ("Common Stock", 0.0, 50_000.0, "equity"),
            ("Retained Earnings", 0.0, 30_000.0, "equity"),
            ("Sales Revenue", 0.0, 50_000.0, "revenue"),
            ("Rent Expense", 30_000.0, 0.0, "expense"),
        ]
    )
    result = FinancialStatementBuilder(grouping).build()
    assert result.is_balanced is True
    soce = result.statement_of_changes_in_equity
    by_type = {c.component_type: c for c in soce.components}
    assert by_type["common_stock"].ending_balance == 50_000.0
    assert by_type["retained_earnings"].ending_balance == 50_000.0  # 30,000 + 20,000 unclosed
    assert by_type["retained_earnings"].net_income_allocation == 20_000.0
    # No prior period, so the 30,000 already in retained earnings has no beginning
    # balance to come from and is shown as other movement — not a plug of -NI.
    assert by_type["retained_earnings"].other_movement == 30_000.0
    assert soce.ending_total_equity == result.total_equity == 100_000.0
    assert sum(c.ending_balance for c in soce.components) == 100_000.0


def test_closed_books_soce_is_unchanged():
    closed = _real_grouping([("Cash - Operating", 100_000.0, 0.0, "asset"), ("Common Stock", 0.0, 100_000.0, "equity")])
    soce = FinancialStatementBuilder(closed).build().statement_of_changes_in_equity
    assert soce.ending_total_equity == 100_000.0
    assert sum(c.ending_balance for c in soce.components) == 100_000.0


def test_pdf_shows_the_line_and_no_out_of_balance_badge():
    result = FinancialStatementBuilder(PRE_CLOSING_LOSS).build()
    pdf = generate_financial_statements_pdf(result)
    text = " ".join(" ".join((p.extract_text() or "").split()) for p in PdfReader(io.BytesIO(pdf)).pages)
    assert UNCLOSED_EARNINGS_LABEL in text
    assert "OUT OF BALANCE" not in text


def test_excel_shows_the_line_and_no_out_of_balance_marker():
    result = FinancialStatementBuilder(PRE_CLOSING_LOSS).build()
    wb = load_workbook(io.BytesIO(generate_financial_statements_excel(result)))
    cells = [str(c.value).strip() for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None]
    assert UNCLOSED_EARNINGS_LABEL in cells
    assert not any("OUT OF BALANCE" in c for c in cells)
