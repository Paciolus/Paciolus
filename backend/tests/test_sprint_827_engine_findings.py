"""
Sprint 827 — remediation of Sprint 823 discovery findings (intercompany + the
huge-amount 500 shared by the promoted tools). Each case reproduces the input
the discovery pass used; see reports/sprint-823-discovery-2026-10-23.md.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from intercompany_elimination_engine import (
    EntityAccount,
    EntityTrialBalance,
    IntercompanyConfig,
    run_intercompany_elimination,
)


def _consolidate(parent_accounts: list[EntityAccount], sub_accounts: list[EntityAccount], *, sub_first=False):
    parent = EntityTrialBalance("P", "Parent", parent_accounts)
    sub = EntityTrialBalance("S", "Sub", sub_accounts)
    entities = [sub, parent] if sub_first else [parent, sub]
    return run_intercompany_elimination(IntercompanyConfig(entities=entities)).to_dict()


@pytest.mark.parametrize("sub_first", [False, True])
def test_revenue_expense_elimination_debits_revenue_and_credits_expense(sub_first):
    """I1: it came out Dr expense / Cr revenue — booking it doubles both sides."""
    result = _consolidate(
        [EntityAccount("Intercompany revenue", credit=Decimal("120000"), counterparty_entity="S")],
        [EntityAccount("Intercompany expense", debit=Decimal("120000"), counterparty_entity="P")],
        sub_first=sub_first,
    )
    (je,) = result["elimination_journal_entries"]
    assert (je["debit_entity"], je["debit_account"]) == ("P", "Intercompany revenue")
    assert (je["credit_entity"], je["credit_account"]) == ("S", "Intercompany expense")


@pytest.mark.parametrize("sub_first", [False, True])
def test_receivable_payable_elimination_is_unchanged(sub_first):
    result = _consolidate(
        [EntityAccount("Due from Sub", debit=Decimal("5000"), counterparty_entity="S")],
        [EntityAccount("Due to Parent", credit=Decimal("5000"), counterparty_entity="P")],
        sub_first=sub_first,
    )
    (je,) = result["elimination_journal_entries"]
    assert (je["debit_entity"], je["credit_entity"]) == ("S", "P")


def test_two_balances_each_side_match_one_to_one():
    """I2: 2 x $500 per side became 4 pairs and $2,000 eliminated, "complete"."""
    result = _consolidate(
        [
            EntityAccount("Due from Sub - trade", debit=Decimal("500"), counterparty_entity="S"),
            EntityAccount("Due from Sub - loan", debit=Decimal("500"), counterparty_entity="S"),
        ],
        [
            EntityAccount("Due to Parent - trade", credit=Decimal("500"), counterparty_entity="P"),
            EntityAccount("Due to Parent - loan", credit=Decimal("500"), counterparty_entity="P"),
        ],
    )
    assert result["summary"]["matched_pair_count"] == 2
    assert result["summary"]["elimination_je_count"] == 2
    assert sum(Decimal(je["amount"]) for je in result["elimination_journal_entries"]) == Decimal("1000")
    assert result["summary"]["consolidation_complete"] is True


def test_unequal_balances_pair_by_amount_before_flagging():
    """I2: 600/400 against 400/600 produced two false amount mismatches."""
    result = _consolidate(
        [
            EntityAccount("Due from Sub - trade", debit=Decimal("600"), counterparty_entity="S"),
            EntityAccount("Due from Sub - loan", debit=Decimal("400"), counterparty_entity="S"),
        ],
        [
            EntityAccount("Due to Parent - loan", credit=Decimal("400"), counterparty_entity="P"),
            EntityAccount("Due to Parent - trade", credit=Decimal("600"), counterparty_entity="P"),
        ],
    )
    assert result["summary"]["mismatch_count"] == 0
    assert result["summary"]["reconciling_pair_count"] == 2


def test_explicit_counterparty_makes_a_line_intercompany():
    """I3: no IC keyword in the account name meant nothing was eliminated and
    the consolidation still reported itself complete."""
    result = _consolidate(
        [EntityAccount("Loan receivable - related party", debit=Decimal("50000"), counterparty_entity="S")],
        [EntityAccount("Loan payable - related party", credit=Decimal("50000"), counterparty_entity="P")],
    )
    assert result["summary"]["intercompany_line_count"] == 2
    assert result["summary"]["elimination_je_count"] == 1


def test_one_sided_explicit_counterparty_is_not_silently_complete():
    result = _consolidate(
        [EntityAccount("Loan receivable - related party", debit=Decimal("50000"), counterparty_entity="S")],
        [EntityAccount("Cash", debit=Decimal("10"))],
    )
    assert result["summary"]["consolidation_complete"] is False


def _payloads() -> list[tuple[str, dict, tuple]]:
    from tests.test_book_to_tax_routes import _valid_payload as book_to_tax
    from tests.test_form_1099_routes import _valid_payload as form_1099
    from tests.test_intercompany_elimination_routes import _valid_payload as intercompany

    def with_huge(payload: dict, *path) -> dict:
        target = payload
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = "1e400"
        return payload

    return [
        ("/audit/form-1099", with_huge(form_1099(), "payments", 0, "amount")),
        ("/audit/book-to-tax", with_huge(book_to_tax(), "book_pretax_income")),
        ("/audit/intercompany-elimination", with_huge(intercompany(), "entities", 0, "accounts", 0, "debit")),
    ]


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
@pytest.mark.parametrize("path, payload", _payloads(), ids=lambda v: v if isinstance(v, str) else "")
async def test_huge_but_finite_amount_is_a_400_not_a_500(override_auth_verified, path, payload):
    """F0/I5: "1e400" is finite, so parsing accepts it; quantize() then raised
    InvalidOperation — an ArithmeticError none of these routes caught."""
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(path, json=payload)
    assert response.status_code == 400, f"{path}: {response.status_code} {response.text[:200]}"


# --- Fixed assets: FA-T11 depreciation recalculation (A1, A2, A3, A6) -------

_PERIOD_END = __import__("datetime").date(2025, 12, 31)
_FA_COLUMNS = [
    "Asset ID",
    "Description",
    "Cost",
    "Accumulated Depreciation",
    "Acquisition Date",
    "Useful Life",
    "Depreciation Method",
    "Residual Value",
]


def _fa_recalc(rows: list[dict]) -> dict:
    from fixed_asset_testing_engine import FixedAssetTestingConfig, run_fixed_asset_testing

    config = FixedAssetTestingConfig(reference_date=_PERIOD_END, reference_date_source="as_of_date")
    result = run_fixed_asset_testing(rows=rows, column_names=_FA_COLUMNS, config=config, column_mapping=None).to_dict()
    return next(t for t in result["test_results"] if t["test_key"] == "depreciation_recalc")


def _asset(n, cost, accum, acquired, life, method, residual=0.0):
    return {
        "Asset ID": f"FA{n}",
        "Description": "Equipment",
        "Cost": cost,
        "Accumulated Depreciation": accum,
        "Acquisition Date": acquired,
        "Useful Life": life,
        "Depreciation Method": method,
        "Residual Value": residual,
    }


def _years(acquired: str) -> float:
    from datetime import date

    return (_PERIOD_END - date.fromisoformat(acquired)).days / 365.25


@pytest.mark.parametrize("method, factor", [("Double-Declining Balance", 2.0), ("150% Declining Balance", 1.5)])
def test_correct_declining_balance_assets_are_not_flagged(method, factor):
    """A1: every correct DDB asset was flagged HIGH (66-304% variance)."""
    rows = [
        _asset(n, 10_000.0, round(10_000 * (1 - (1 - factor / life) ** _years(acq)), 2), acq, life, method)
        for n, (acq, life) in enumerate([("2024-01-01", 5), ("2022-07-01", 8), ("2021-01-01", 10)], 1)
    ]
    assert _fa_recalc(rows)["entries_flagged"] == 0


def test_fully_depreciated_asset_inside_the_skip_window_is_not_flagged():
    """A2: between 1.0x and 1.5x life the uncapped expectation exceeded cost."""
    row = _asset(1, 9_180.51, 7_803.43, "2019-01-04", 5, "Straight-Line", residual=1_377.08)
    assert _fa_recalc([row])["entries_flagged"] == 0


@pytest.mark.parametrize("acquired", ["2021-01-01 00:00:00", "2021/01/01"])
def test_excel_and_slash_dates_are_tested_not_skipped(acquired):
    """A3: these were silently skipped — a planted 40% under-depreciation went unflagged."""
    under = round(100_000 * _years("2021-01-01") / 10 * 0.6, 2)
    assert _fa_recalc([_asset(1, 100_000.0, under, acquired, 10, "Straight-Line")])["entries_flagged"] == 1


def test_contra_negative_accumulated_depreciation_compares_magnitudes():
    """A6: a register carrying accumulated depreciation as (5,000.00) flagged every row."""
    accum = round(100_000 * _years("2021-01-01") / 10, 2)
    assert _fa_recalc([_asset(1, 100_000.0, -accum, "2021-01-01", 10, "Straight-Line")])["entries_flagged"] == 0


def test_planted_under_depreciation_is_still_flagged():
    accum = round(100_000 * _years("2021-01-01") / 10 * 0.6, 2)
    assert _fa_recalc([_asset(1, 100_000.0, accum, "2021-01-01", 10, "Straight-Line")])["entries_flagged"] == 1
