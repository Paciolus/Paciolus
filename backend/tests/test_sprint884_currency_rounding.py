"""Sprint 884 / 9A (review TQ-13): the currency engine uses the shared half-up rule.

``shared/monetary.py`` rounds half-up to cents. The currency engine rounded
half-even, so EUR 1.00 at 1.005 was USD 1.00 in the exposure table and 1.01
everywhere else in the product.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO

import httpx
import pytest
from fastapi.encoders import jsonable_encoder

from currency_engine import CurrencyRateTable, ExchangeRate, convert_trial_balance
from shared.monetary import quantize_monetary


def _table(rate: str) -> CurrencyRateTable:
    return CurrencyRateTable(
        rates=[ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal(rate))],
        presentation_currency="USD",
    )


def _convert(amounts: list[str], rate: str = "1.005"):
    rows = [{"Account": str(1000 + i), "Currency": "EUR", "Amount": a} for i, a in enumerate(amounts)]
    return convert_trial_balance(rows, _table(rate), "Amount", currency_column="Currency")


def _eur_exposure(result):
    return next(e for e in result.currency_exposure if e.currency == "EUR")


def _pdf_text(pdf_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


class TestExposureRoundsHalfUp:
    def test_half_cent_rounds_up(self):
        assert _eur_exposure(_convert(["1.00"])).usd_equivalent == Decimal("1.01")

    def test_negative_half_cent_rounds_away_from_zero(self):
        assert _eur_exposure(_convert(["-1.00"])).usd_equivalent == Decimal("-1.01")

    def test_converted_row_is_rounded_half_up_to_cents(self):
        result = _convert(["1.00", "-1.00"])
        assert [r["converted_amount_usd"] for r in result.converted_rows] == [Decimal("1.01"), Decimal("-1.01")]

    def test_no_double_rounding_through_an_intermediate_precision(self):
        # 1.00 x 1.004950 = 1.00495 exactly → 1.00. Rounding to 4dp first
        # (1.0050) and then to cents would give 1.01.
        assert _eur_exposure(_convert(["1.00"], rate="1.004950")).usd_equivalent == Decimal("1.00")

    def test_total_of_several_rows_agrees_with_its_rows(self):
        result = _convert(["1.00", "1.00", "1.00", "-3.00", "2.50"])
        rows = [quantize_monetary(r["converted_amount_usd"]) for r in result.converted_rows]
        assert _eur_exposure(result).usd_equivalent == sum(rows, Decimal("0"))
        assert sum(rows, Decimal("0")) == Decimal("2.52")  # 1.01*3 - 3.02 (−3.015) + 2.51 (2.5125)

    def test_percent_of_total_rounds_half_up(self):
        # USD 0.25 (exact, 1:1) + EUR → USD 0.15: EUR is 37.5% → 37.5; USD 62.5%.
        rows = [
            {"Account": "1", "Currency": "USD", "Amount": "0.25"},
            {"Account": "2", "Currency": "EUR", "Amount": "0.15"},
        ]
        result = convert_trial_balance(rows, _table("1"), "Amount", currency_column="Currency")
        pcts = {e.currency: e.pct_of_total for e in result.currency_exposure}
        assert pcts == {"EUR": Decimal("37.5"), "USD": Decimal("62.5")}

    def test_pct_half_tenth_rounds_up(self):
        # 1 of 8 = 12.5%; 1/16 = 6.25% → 6.3 half-up (6.2 half-even).
        rows = [
            {"Account": "1", "Currency": "USD", "Amount": "15.00"},
            {"Account": "2", "Currency": "EUR", "Amount": "1.00"},
        ]
        result = convert_trial_balance(rows, _table("1"), "Amount", currency_column="Currency")
        pcts = {e.currency: e.pct_of_total for e in result.currency_exposure}
        assert pcts["EUR"] == Decimal("6.3")


@pytest.mark.usefixtures("bypass_csrf")
class TestMemoShowsHalfUp:
    @pytest.mark.asyncio
    async def test_memo_pdf_shows_rows_and_a_total_built_from_them(self, override_auth_verified):
        from main import app

        result = _convert(["1.00", "1.00", "1.00"])
        negative = _convert(["-1.00"])
        payload = jsonable_encoder(result.to_dict())
        payload["currency_exposure"].append(
            {**jsonable_encoder(_eur_exposure(negative).to_dict()), "currency": "GBP", "rate": "1.005"}
        )
        payload["filename"] = "fx"
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/currency-conversion-memo", json=payload)
        assert response.status_code == 200, response.text
        text = _pdf_text(response.content)
        assert "$3.03" in text  # EUR row: 1.01 x 3
        assert "-$1.01" in text  # GBP row
        assert "$2.02" in text  # total of the two displayed rows

    def test_memo_total_uses_displayed_rows_not_floats(self):
        from currency_memo_generator import generate_currency_conversion_memo

        exposure = [
            {"currency": c, "account_count": 1, "foreign_total": "0.10", "rate": "1", "usd_equivalent": "0.10"}
            for c in ("EUR", "GBP", "CAD")
        ]
        text = _pdf_text(
            generate_currency_conversion_memo(
                {"conversion_performed": True, "presentation_currency": "USD", "currency_exposure": exposure}
            )
        )
        assert "$0.30" in text

    def test_large_amounts_keep_their_cents_so_the_total_adds_up(self):
        from currency_memo_generator import generate_currency_conversion_memo

        exposure = [
            {
                "currency": c,
                "account_count": 1,
                "foreign_total": "1000000.50",
                "rate": "1",
                "usd_equivalent": "1000000.50",
            }
            for c in ("EUR", "GBP")
        ]
        text = _pdf_text(
            generate_currency_conversion_memo(
                {"conversion_performed": True, "presentation_currency": "USD", "currency_exposure": exposure}
            )
        )
        assert "$1,000,000.50" in text
        assert "$2,000,001.00" in text
