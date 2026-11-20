"""Sprint 887 / 12B (review OUT-08): the accrual memo says above or below the threshold, and where it came from.

The memo said a ratio at or above the 50% default "meets the ... minimum
threshold, indicating accrual balances are within a reasonable range relative
to operating activity levels", and below it "suggesting accrual balances may
require additional completeness procedures". The 50% is a Paciolus setting, not
a standard, and a ratio says nothing about reasonableness or completeness. The
memo now states only the comparison and the threshold's origin.
"""

from __future__ import annotations

import io

import httpx
import pytest

# Accrued liabilities total 40,000.
TB_CSV = (
    "Account Name,Debit,Credit\n"
    "Cash,90000.00,0\n"
    "Accrued Wages,0,30000.00\n"
    "Accrued Interest Payable,0,10000.00\n"
    "Common Stock,0,50000.00\n"
    "Sales Revenue,0,100000.00\n"
    "Rent Expense,100000.00,0\n"
).encode()

# Statements about the balances, not the ratio, that the memo must never make.
JUDGMENTS = (
    "reasonable range",
    "within a reasonable",
    "may require additional",
    "should perform additional",
    "completeness procedures",
    "indicating accrual balances",
)


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


def _assert_no_judgment(text: str) -> None:
    lowered = text.lower()
    for phrase in JUDGMENTS:
        assert phrase not in lowered, phrase


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestAccrualThresholdWording:
    async def _screen(self, prior_opex: float, threshold: float | None = None) -> dict:
        data = {"prior_operating_expenses": str(prior_opex)}
        if threshold is not None:
            data["threshold_pct"] = str(threshold)
        response = await _post("/audit/accrual-completeness", files={"file": ("tb.csv", TB_CSV, "text/csv")}, data=data)
        assert response.status_code == 200, response.text
        return response.json()

    async def _memo(self, screen: dict) -> str:
        response = await _post("/export/accrual-completeness-memo", json={**screen, "filename": "tb"})
        assert response.status_code == 200, response.text
        return _pdf_text(response.content)

    async def test_above_default_threshold(self):
        # 40,000 / (600,000 / 12) = 80%.
        screen = await self._screen(600_000)
        assert screen["meets_threshold"] is True
        assert screen["threshold_source"] == "default"
        text = await self._memo(screen)
        _assert_no_judgment(text)
        assert "80.0%, at or above the 50% threshold" in text
        assert "Threshold source: Paciolus default (a software setting, not a professional standard)" in text

    async def test_below_default_threshold(self):
        # 40,000 / (1,200,000 / 12) = 40%.
        screen = await self._screen(1_200_000)
        assert screen["meets_threshold"] is False
        text = await self._memo(screen)
        _assert_no_judgment(text)
        assert "40.0%, below the 50% threshold" in text

    async def test_threshold_entered_for_the_run(self):
        screen = await self._screen(1_200_000, threshold=30)
        assert screen["threshold_source"] == "entered"
        text = await self._memo(screen)
        _assert_no_judgment(text)
        assert "40.0%, at or above the 30% threshold" in text
        assert "Threshold source: entered for this run" in text
        # The label carries the threshold applied, not a hard-coded 50%.
        assert "(≥30%)" in text and "(≥50%)" not in text

    async def test_source_not_sent_prints_not_available(self):
        screen = await self._screen(600_000)
        del screen["threshold_source"]
        text = await self._memo(screen)
        assert "Threshold source: Not available" in text
