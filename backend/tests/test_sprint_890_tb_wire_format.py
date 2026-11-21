"""Sprint 890 (CEO brief 15C, review ST-10): the trial balance wire format is what the frontend declares.

Top-level amounts serialized as JSON numbers, but ``all_accounts`` and ``account_balances`` were
untyped dictionaries, so their Decimal amounts went out as strings ("1234.50") while
``frontend/src/types/diagnostic.ts`` declares numbers. They now use typed models with the same
exact-number serializer as the top-level amounts. These tests assert the JSON value *types*, not
just numerical equality after conversion.
"""

from __future__ import annotations

import json

import httpx
import pytest

TB_CSV = (
    "Account Name,Debit,Credit\nCash,1234.50,0\nAccounts Receivable,0.10,0\nAccounts Payable,0,1234.60\n"
).encode()


async def _analyse() -> tuple[dict, str]:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/audit/trial-balance",
            files={"file": ("tb.csv", TB_CSV, "text/csv")},
            data={"force_resubmit": "true"},
        )
    assert r.status_code == 200, r.text
    return r.json(), r.text


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_all_accounts_amounts_are_json_numbers(override_auth_verified):
    body, _ = await _analyse()
    accounts = {a["account"]: a for a in body["all_accounts"]}
    cash = accounts["Cash"]
    assert _is_number(cash["debit"]) and _is_number(cash["credit"]), cash
    assert cash["debit"] == 1234.5
    assert cash["credit"] == 0
    assert accounts["Accounts Receivable"]["debit"] == 0.1
    assert isinstance(cash["type"], str)
    assert isinstance(cash["type_supplied"], bool)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_account_balances_amounts_are_json_numbers(override_auth_verified):
    body, _ = await _analyse()
    payable = body["account_balances"]["Accounts Payable"]
    assert _is_number(payable["debit"]) and _is_number(payable["credit"]), payable
    assert payable["credit"] == 1234.6


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_no_nested_amount_is_sent_as_a_string(override_auth_verified):
    _, text = await _analyse()
    raw = json.loads(text)
    for a in raw["all_accounts"]:
        for key in ("debit", "credit"):
            assert not isinstance(a[key], str), (a["account"], key, a[key])
    for name, bal in raw["account_balances"].items():
        for key in ("debit", "credit"):
            assert not isinstance(bal[key], str), (name, key, bal[key])
