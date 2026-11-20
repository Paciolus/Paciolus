"""Sprint 887 / 12G (review OUT-22): the population memo states skew and outliers only from a statistic.

The memo always called the maximum balance "a significant outlier at {max/mean}x
the mean", divided by zero when every balance was zero, and called equal mean
and median "left-skewed". The engine now computes the adjusted Fisher–Pearson
skewness and the Tukey upper fence (P75 + 1.5 × IQR); the memo reports those
results, and plain facts for all-zero and uniform populations.
"""

from __future__ import annotations

import io

import httpx
import pytest


def _tb(balances: list[float]) -> bytes:
    rows = ["Account Name,Debit,Credit"]
    for i, b in enumerate(balances, 1):
        rows.append(f"Expense Account {i:02d},{b:.2f},0")
    return ("\n".join(rows) + "\n").encode()


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


def _narrative(text: str) -> str:
    return text.split("II. Descriptive Statistics", 1)[1].split("Data Quality Score Breakdown", 1)[0]


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestPopulationNarrative:
    async def _run(self, balances: list[float]) -> tuple[dict, str]:
        screen = await _post("/audit/population-profile", files={"file": ("tb.csv", _tb(balances), "text/csv")})
        assert screen.status_code == 200, screen.text
        body = screen.json()
        memo = await _post("/export/population-profile-memo", json={**body, "filename": "tb"})
        assert memo.status_code == 200, memo.text
        return body, _narrative(_pdf_text(memo.content))

    async def test_all_zero_population(self):
        from population_profile_engine import compute_population_profile

        report = compute_population_profile(
            {f"Account {i}": {"debit": 0.0, "credit": 0.0} for i in range(6)}, {}
        ).to_dict()
        memo = await _post("/export/population-profile-memo", json={**report, "filename": "tb"})
        assert memo.status_code == 200, memo.text
        text = _narrative(_pdf_text(memo.content))
        assert "Every account balance in the population is $0.00" in text
        assert "outlier" not in text.lower() and "skew" not in text.lower()

    async def test_uniform_population(self):
        body, text = await self._run([5000.0] * 9)
        assert body["skewness"] is None
        assert "equal $5,000.00" in text and "no dispersion" in text
        assert "outlier" not in text.lower() and "skewed" not in text.lower()

    async def test_symmetric_population(self):
        body, text = await self._run([1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0, 7000.0])
        assert body["skewness"] == 0.0
        assert "left-skewed" not in text and "right-skewed" not in text
        assert "Sample skewness (adjusted Fisher–Pearson) is 0.00" in text
        assert "No balance exceeds the Tukey upper fence" in text
        assert "significant outlier" not in text

    async def test_skewed_population_reports_the_statistics(self):
        body, text = await self._run([100.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 50000.0])
        assert body["skewness"] > 0
        assert body["accounts_above_upper_fence"] >= 1
        assert f"is {body['skewness']:+.2f}" in text
        assert "the longer tail is toward larger balances" in text
        assert "exceed the Tukey upper fence" in text or "exceeds the Tukey upper fence" in text
        assert "significant outlier" not in text

    async def test_old_payload_without_statistics_says_not_available(self):
        body, _ = await self._run([100.0, 200.0, 300.0, 50000.0])
        for key in ("skewness", "upper_fence", "accounts_above_upper_fence"):
            body.pop(key, None)
        memo = await _post("/export/population-profile-memo", json={**body, "filename": "tb"})
        text = _narrative(_pdf_text(memo.content))
        assert "Skewness and outlier statistics: Not available." in text
        assert "outlier at" not in text
