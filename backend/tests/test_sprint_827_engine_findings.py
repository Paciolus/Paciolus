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
