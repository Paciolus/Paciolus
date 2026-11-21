"""Sprint 890 (CEO brief 15D, review ST-11): the trial balance's automatic currency conversion runs.

The conversion step began ``if "accounts" not in result: return``, but the pipeline emits
``all_accounts`` and never ``accounts``, and the response model had no ``currency_conversion``
field — so it never ran. Renaming the key was not enough: ``all_accounts`` carried no currency.

CEO decision 2026-11-20: one closing rate for every account (the latest rate in the user's table
for each currency), labelled a convenience conversion — not translation under ASC 830 or IAS 21 —
with the rate, its date and its source beside every converted figure.

Hand-worked: EUR 1,000.00 debit at 1.10 = USD 1,100.00; GBP 500.00 credit at 1.25 = USD -625.00
(net balance, debit positive). The EUR table also holds an older 1.05 rate, which must not be used.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import httpx
import pytest

TB_CSV = (
    "Account Name,Debit,Credit,Currency\n"
    "Cash - Euro Account,1000.00,0,EUR\n"
    "Accounts Payable - UK,0,500.00,GBP\n"
    "Retained Earnings,0,500.00,EUR\n"
).encode()


@pytest.fixture
def stored_rates(override_auth_verified, db_session):
    from currency_engine import CurrencyRateTable, ExchangeRate
    from shared.currency_rate_store import set_user_rate_table

    table = CurrencyRateTable(
        rates=[
            ExchangeRate(
                effective_date=date(2026, 9, 30), from_currency="EUR", to_currency="USD", rate=Decimal("1.05")
            ),
            ExchangeRate(
                effective_date=date(2026, 10, 31), from_currency="EUR", to_currency="USD", rate=Decimal("1.10")
            ),
            ExchangeRate(
                effective_date=date(2026, 10, 31), from_currency="GBP", to_currency="USD", rate=Decimal("1.25")
            ),
        ],
        uploaded_at=datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc),
        presentation_currency="USD",
    )
    set_user_rate_table(db_session, override_auth_verified.id, table)
    db_session.flush()
    return table


async def _analyse() -> dict:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/audit/trial-balance", files={"file": ("tb.csv", TB_CSV, "text/csv")}, data={"force_resubmit": "true"}
        )
    assert r.status_code == 200, r.text[:600]
    return r.json()


def _row(conv: dict, account: str) -> dict:
    (row,) = [r for r in conv["rows"] if r["account"] == account]
    return row


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_conversion_runs_with_rate_date_and_source_beside_each_figure(stored_rates):
    conv = (await _analyse())["currency_conversion"]
    assert conv is not None
    assert conv["method"] == "convenience_single_closing_rate"
    assert "not translation under ASC 830 or IAS 21" in conv["label"]
    assert conv["presentation_currency"] == "USD"

    eur = _row(conv, "Cash - Euro Account")
    assert (eur["currency"], eur["original_amount"], eur["rate"], eur["rate_date"]) == (
        "EUR",
        1000.0,
        "1.10",
        "2026-10-31",
    )
    assert eur["converted_amount"] == 1100.0
    assert "rate table" in eur["rate_source"].lower() and "2026-11-01" in eur["rate_source"]

    gbp = _row(conv, "Accounts Payable - UK")
    assert (gbp["original_amount"], gbp["rate"], gbp["converted_amount"]) == (-500.0, "1.25", -625.0)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_a_currency_without_a_rate_is_listed_not_converted(override_auth_verified, db_session):
    from currency_engine import CurrencyRateTable, ExchangeRate
    from shared.currency_rate_store import set_user_rate_table

    set_user_rate_table(
        db_session,
        override_auth_verified.id,
        CurrencyRateTable(
            rates=[
                ExchangeRate(
                    effective_date=date(2026, 10, 31), from_currency="EUR", to_currency="USD", rate=Decimal("1.10")
                )
            ],
            presentation_currency="USD",
        ),
    )
    db_session.flush()
    conv = (await _analyse())["currency_conversion"]
    gbp = _row(conv, "Accounts Payable - UK")
    assert gbp["converted_amount"] is None
    assert gbp["rate"] is None
    assert gbp["issue"] == "missing_rate"


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_no_rate_table_means_no_conversion(override_auth_verified):
    assert (await _analyse()).get("currency_conversion") is None
