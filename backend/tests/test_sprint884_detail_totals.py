"""Sprint 884 / 9C (review OUT-05): a total equals the detail printed above it.

The accrual completeness engine rounded each account balance and, separately,
the unrounded total: two balances of 0.014 printed as 0.01 each over a total of
0.03. Rule (CEO, 2026-11-18): half-up to cents, and a total shown beneath
detail is computed from the detail as displayed. The same check covers the
expense-category table and the financial statements.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO

import pytest

from accrual_completeness_engine import compute_accrual_completeness
from expense_category_engine import compute_expense_categories
from financial_statement_builder import FinancialStatementBuilder

# (balances, expected displayed rows, expected displayed total)
CASES = {
    "sub_cent": (["0.014", "0.014"], ["0.01", "0.01"], "0.02"),
    "half_cent": (["0.005", "0.005", "0.005"], ["0.01", "0.01", "0.01"], "0.03"),
    "mixed_sign": (["100.006", "-0.004", "-50.005"], ["100.01", "0.00", "-50.01"], "50.00"),
    "negative_half_cent": (["-1.005", "-2.005"], ["-1.01", "-2.01"], "-3.02"),
}


def _pdf_text(pdf_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def _money(value) -> str:
    v = Decimal(str(value))
    return f"${v:,.2f}" if v >= 0 else f"$-{-v:,.2f}"


# ─────────────────────────── Accrual completeness ───────────────────────────


def _accrual_report(balances: list[str]):
    # Liabilities are credit-normal: balance = credit - debit.
    names = [f"Accrued Wages {i}" for i in range(len(balances))]
    account_balances = {n: {"debit": 0.0, "credit": float(b)} for n, b in zip(names, balances)}
    classified = {n: "liability" for n in names}
    return compute_accrual_completeness(account_balances, classified)


@pytest.mark.parametrize("case", CASES)
def test_accrual_total_is_the_sum_of_the_rows_shown(case):
    balances, rows, total = CASES[case]
    d = _accrual_report(balances).to_dict()
    shown = sorted(Decimal(str(a["balance"])) for a in d["accrual_accounts"])
    assert shown == sorted(Decimal(r) for r in rows)
    assert Decimal(str(d["total_accrued_balance"])) == Decimal(total)
    assert sum(shown, Decimal("0")) == Decimal(str(d["total_accrued_balance"]))


@pytest.mark.parametrize("case", CASES)
def test_accrual_memo_total_row_matches_its_rows(case):
    from accrual_completeness_memo import generate_accrual_completeness_memo

    balances, rows, total = CASES[case]
    text = _pdf_text(generate_accrual_completeness_memo(_accrual_report(balances).to_dict()))
    assert f"TOTAL {_money(total)}" in text


def test_accrual_memo_totals_what_it_prints_even_from_an_inconsistent_payload():
    """A client-sent payload whose total disagrees with its rows still prints a total of the rows."""
    from accrual_completeness_memo import generate_accrual_completeness_memo

    payload = {
        "accrual_accounts": [
            {"account_name": "Accrued A", "balance": 0.014, "matched_keyword": "accrued"},
            {"account_name": "Accrued B", "balance": 0.014, "matched_keyword": "accrued"},
        ],
        "total_accrued_balance": 0.028,
        "accrual_account_count": 2,
    }
    text = _pdf_text(generate_accrual_completeness_memo(payload))
    assert "TOTAL $0.02" in text
    assert "$0.03" not in text


# ─────────────────────────── Expense categories ───────────────────────────

CATEGORY_ACCOUNTS = ["Salaries Expense", "Depreciation Expense", "Interest Expense", "Office Supplies"]


@pytest.mark.parametrize("case", CASES)
def test_expense_total_is_the_sum_of_the_categories_shown(case):
    balances, _rows, _total = CASES[case]
    names = CATEGORY_ACCOUNTS[: len(balances)]
    account_balances = {n: {"debit": float(b), "credit": 0.0} for n, b in zip(names, balances)}
    d = compute_expense_categories(account_balances, {n: "expense" for n in names}, total_revenue=1000.0).to_dict()
    shown = [Decimal(str(c["amount"])) for c in d["categories"]]
    assert all(s == s.quantize(Decimal("0.01")) for s in shown)
    assert sum(shown, Decimal("0")) == Decimal(str(d["total_expenses"]))


def test_expense_category_rounds_half_up():
    d = compute_expense_categories(
        {"Office Supplies": {"debit": 0.005, "credit": 0.0}}, {"Office Supplies": "expense"}, total_revenue=0.0
    ).to_dict()
    other = next(c for c in d["categories"] if Decimal(str(c["amount"])) != 0)
    assert Decimal(str(other["amount"])) == Decimal("0.01")


# ─────────────────────────── Financial statements ───────────────────────────


def _fs(balances: dict[str, str]):
    grouping = {"summaries": [{"lead_sheet": k, "net_balance": float(v)} for k, v in balances.items()]}
    return FinancialStatementBuilder(grouping).build()


def _shown(amount) -> Decimal:
    return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@pytest.mark.parametrize("case", CASES)
def test_current_assets_subtotal_is_the_sum_of_the_lines_shown(case):
    balances, _rows, _total = CASES[case]
    fs = _fs(dict(zip("ABCD", balances)))
    bs = {li.label: li for li in fs.balance_sheet}
    lines = ["Cash and Cash Equivalents", "Receivables", "Inventory", "Prepaid Expenses"]
    detail = sum((_shown(bs[label].amount) for label in lines), Decimal("0"))
    assert _shown(bs["Total Current Assets"].amount) == detail
    assert _shown(fs.total_assets) == detail


def test_income_statement_totals_are_built_from_the_lines_shown():
    fs = _fs({"L": "-0.014", "M": "0.004", "N": "0.004", "O": "-0.005"})
    by = {li.label: li for li in fs.income_statement}
    revenue, cogs = _shown(by["Revenue"].amount), _shown(by["Cost of Goods Sold"].amount)
    assert _shown(by["GROSS PROFIT"].amount) == revenue - cogs
    assert _shown(fs.net_income) == _shown(by["NET INCOME"].amount)
    # 0.01 - 0.00 - 0.00 + 0.01 (other income 0.005 → 0.01)
    assert _shown(fs.net_income) == Decimal("0.02")
