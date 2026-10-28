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


@pytest.mark.parametrize("acquired", ["01-Jan-2021", "1-JAN-2021", "01 Jan 2021", "Jan 1, 2021"])
def test_day_month_name_dates_are_tested_not_skipped(acquired):
    """A3 remainder: ``01-Jan-2019`` was outside the shared parser, so FA-T11
    skipped the asset and a planted under-depreciation went unflagged. Sprint
    829 (D-2) added ``%d-%b-%Y`` and friends to the shared ``parse_date`` for
    every caller; this pins that the fixed-asset path relies on it."""
    under = round(100_000 * _years("2021-01-01") / 10 * 0.6, 2)
    assert _fa_recalc([_asset(1, 100_000.0, under, acquired, 10, "Straight-Line")])["entries_flagged"] == 1


def test_contra_negative_accumulated_depreciation_compares_magnitudes():
    """A6: a register carrying accumulated depreciation as (5,000.00) flagged every row."""
    accum = round(100_000 * _years("2021-01-01") / 10, 2)
    assert _fa_recalc([_asset(1, 100_000.0, -accum, "2021-01-01", 10, "Straight-Line")])["entries_flagged"] == 0


def test_planted_under_depreciation_is_still_flagged():
    accum = round(100_000 * _years("2021-01-01") / 10 * 0.6, 2)
    assert _fa_recalc([_asset(1, 100_000.0, accum, "2021-01-01", 10, "Straight-Line")])["entries_flagged"] == 1


# --- SoD: long-format matrices (D1) -------------------------------------------


def _sod(users, roles):
    from sod_engine import RolePermission, UserRoleAssignment, analyze_segregation_of_duties

    return analyze_segregation_of_duties(
        [UserRoleAssignment(*u) for u in users], [RolePermission(*r) for r in roles]
    ).to_dict()


def test_role_split_across_rows_keeps_every_permission():
    """D1: the second row overwrote the first, so AP-02 never fired."""
    result = _sod(
        [("u1", "Pat", ["AP_SUPER"])],
        [("AP_SUPER", ["ap_invoice_create"]), ("AP_SUPER", ["ap_payment_release"])],
    )
    assert "AP-02" in {c["rule_code"] for c in result["conflicts"]}


def test_user_split_across_rows_is_one_user_with_all_roles():
    """D1: two rows for one user were evaluated as two conflict-free users."""
    result = _sod(
        [("x1", "Sam", ["AP_CLERK"]), ("x1", "Sam", ["AP_MANAGER"])],
        [("AP_CLERK", ["ap_invoice_create"]), ("AP_MANAGER", ["ap_payment_release"])],
    )
    assert result["users_evaluated"] == 1
    assert "AP-02" in {c["rule_code"] for c in result["conflicts"]}


# --- Cash flow projector: calendar-month recurrence (C1) ---------------------


@pytest.mark.parametrize(
    "start, first, expected",
    [
        ("2027-01-01", "2027-01-31", ["2027-01-31", "2027-02-28", "2027-03-31"]),
        ("2028-02-01", "2028-02-01", ["2028-02-01", "2028-03-01", "2028-04-01"]),
        ("2027-12-01", "2027-12-15", ["2027-12-15", "2028-01-15", "2028-02-15"]),
    ],
)
def test_monthly_flows_land_on_calendar_months(start, first, expected):
    """C1: 30-day steps put Jan 31 rent on Mar 2 and dropped a payment from the horizon."""
    from datetime import date, timedelta

    from cash_flow_projector_engine import RecurringFlow, _recurring_schedule

    start_date = date.fromisoformat(start)
    flow = RecurringFlow(
        label="Rent", amount=Decimal("-1000"), frequency="monthly", first_date=date.fromisoformat(first)
    )
    schedule = _recurring_schedule([flow], start_date)
    hit_dates = [(start_date + timedelta(days=d)).isoformat() for d, amount in sorted(schedule.items()) if amount]
    assert hit_dates == expected


# --- Intercompany keyword false positives (I4) --------------------------------


def test_ordinary_accounts_are_not_intercompany():
    """I4: substring matching made these one-sided IC lines that blocked completion."""
    result = _consolidate(
        [
            EntityAccount("Electric expense", debit=Decimal("900")),
            EntityAccount("Clinic revenue", credit=Decimal("5000")),
            EntityAccount("Basic apparel", debit=Decimal("200")),
            EntityAccount("Due to officers", credit=Decimal("1500")),
            EntityAccount("Interest receivable from bank", debit=Decimal("75")),
        ],
        [EntityAccount("Cash", debit=Decimal("10"))],
    )
    assert result["summary"]["intercompany_line_count"] == 0
    assert result["summary"]["consolidation_complete"] is True


def test_counterparty_names_resolve_from_dash_and_suffix_forms():
    """I4: "- Dublin Ltd" yielded "Ltd" (the "in" inside "Dublin"); "IC AR - Beta" yielded none."""
    from intercompany_elimination_engine import _parse_counterparty

    assert _parse_counterparty("Intercompany receivable - Dublin Ltd") == "Dublin Ltd"
    assert _parse_counterparty("IC AR - Beta") == "Beta"
    assert _parse_counterparty("Management fee revenue - Sub A") == "Sub A"


def test_generic_phrase_naming_a_consolidated_entity_is_still_intercompany():
    result = _consolidate(
        [EntityAccount("Due from Sub", debit=Decimal("700"))],
        [EntityAccount("Due to Parent", credit=Decimal("700"))],
    )
    assert result["summary"]["elimination_je_count"] == 1


def test_permissions_no_rule_recognises_are_reported():
    """D2: unrecognised spellings produced a clean result with no warning."""
    result = _sod(
        [("u1", "Pat", ["AP_SUPER"])],
        [("AP_SUPER", ["AP-INVOICE-CREATE", "ap.payment.release", "ap_invoice_create"])],
    )
    assert result["unmatched_permissions"] == ["ap-invoice-create", "ap.payment.release"]


def test_direction_less_pair_is_oriented_by_balance():
    """PR #206 review: with no direction in either name the JE followed entity
    order — Dr receivable / Cr payable, doubling both balances."""
    for sub_first in (False, True):
        result = _consolidate(
            [EntityAccount("Loan receivable - related party", debit=Decimal("50000"), counterparty_entity="S")],
            [EntityAccount("Loan payable - related party", credit=Decimal("50000"), counterparty_entity="P")],
            sub_first=sub_first,
        )
        (je,) = result["elimination_journal_entries"]
        assert (je["debit_entity"], je["debit_account"]) == ("S", "Loan payable - related party")
        assert (je["credit_entity"], je["credit_account"]) == ("P", "Loan receivable - related party")


def test_short_life_declining_balance_asset_is_recalculated_not_skipped():
    """PR #206 review: a 2-year DDB asset (rate 1.0) with nothing depreciated was skipped."""
    test = _fa_recalc([_asset(1, 10_000.0, 0.0, "2024-01-01", 2, "Double-Declining Balance")])
    assert test["entries_flagged"] == 1
    fully = _fa_recalc([_asset(1, 10_000.0, 10_000.0, "2024-01-01", 2, "Double-Declining Balance")])
    assert fully["entries_flagged"] == 0


def test_lowest_balance_is_a_projected_balance_not_the_opening_one():
    """C4: with inflows only, the "lowest balance" was the opening balance on
    day 0 — a figure no projected day ever ended at."""
    from datetime import date

    from cash_flow_projector_engine import AgingBuckets, CashFlowConfig, project_cash_flow

    forecast = project_cash_flow(
        CashFlowConfig(
            opening_balance=Decimal("100000"),
            start_date=date(2027, 1, 4),
            ar_aging=AgingBuckets(current=Decimal("50000")),
        )
    )
    for scenario in forecast.scenarios.values():
        assert scenario.horizon[30].lowest_balance == scenario.daily[0].ending_balance
        assert scenario.horizon[30].lowest_balance > Decimal("100000")
