"""Sprint 887 / 12L (review comparison table): expense category — screen, CSV and PDF agree.

The PDF computed its own % changes, assigned HIGH / MODERATE / LOW "Risk Level"
labels and an "Explanation Req." flag from 10% / 20% thresholds in
``_assign_risk()`` — none of which the screen or CSV showed. Decided (CEO,
2026-11-20): the engine computes the % change and a change band; the screen,
CSV and PDF show them with neutral labels and print the thresholds; "Risk
Level" and "Explanation Req." are removed.
"""

from __future__ import annotations

import csv
import io

import httpx
import pytest

TB_CSV = (
    "Account Name,Debit,Credit\n"
    "Cash,500000.00,0\n"
    "Sales Revenue,0,1000000.00\n"
    "Cost of Goods Sold,300000.00,0\n"
    "Salaries Expense,150000.00,0\n"
    "Rent Expense,50000.00,0\n"
).encode()


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestExpenseCategoryFormatsAgree:
    async def _screen(self) -> dict:
        # COGS 300,000 now vs 240,000 prior: +25%, $60,000 over a $10,000 materiality.
        response = await _post(
            "/audit/expense-category-analytics",
            files={"file": ("tb.csv", TB_CSV, "text/csv")},
            data={
                "materiality_threshold": "10000",
                "prior_cogs": "240000",
                "prior_opex": "190000",
                "prior_total_expenses": "430000",
                "prior_revenue": "900000",
            },
        )
        assert response.status_code == 200, response.text
        return response.json()

    async def test_engine_computes_change_and_band(self):
        screen = await self._screen()
        cogs = next(c for c in screen["categories"] if c["prior_amount"] is not None and c["key"] == "cogs")
        assert cogs["pct_change"] == 25.0
        assert cogs["change_band"] == "both"
        assert screen["change_thresholds"] == {"pct_both": 20.0, "pct_either": 10.0, "materiality": 10000.0}

    async def test_csv_shows_the_same_change_band_and_thresholds(self):
        screen = await self._screen()
        response = await _post("/export/csv/expense-category-analytics", json={**screen, "filename": "tb"})
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
        header = next(r for r in rows if r and r[0] == "Category" and "% Change" in r)
        cogs_row = next(r for r in rows if r and r[0] == "Cost of Goods Sold")
        assert cogs_row[header.index("% Change")] == "25.00%"
        assert cogs_row[header.index("Change Band")] == "Change ≥ 20% and over materiality"
        flat = " ".join(" ".join(r) for r in rows)
        assert "10% and 20%" in flat and "Paciolus defaults" in flat

    async def test_pdf_uses_the_engine_figures_and_no_risk_labels(self):
        screen = await self._screen()
        response = await _post("/export/expense-category-memo", json={**screen, "filename": "tb"})
        assert response.status_code == 200, response.text
        text = _pdf_text(response.content)
        assert "Risk Level" not in text and "Explanation Req" not in text
        assert "require management explanation" not in text
        assert "+25.00%" in text
        assert "Change ≥ 20% and over materiality" in text
        assert "10% and 20%" in text and "Paciolus defaults" in text and "$10,000.00" in text


@pytest.mark.parametrize(
    "pct,exceeds,band",
    [
        (25.0, True, "both"),
        (25.0, False, "either"),
        (5.0, True, "either"),
        (12.0, False, "either"),
        (5.0, False, "neither"),
        (None, True, None),
    ],
)
def test_change_band(pct, exceeds, band):
    from expense_category_engine import change_band

    assert change_band(pct, exceeds) == band
