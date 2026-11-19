"""Sprint 886 / 11E (review OUT-14): payroll completeness is on the 0–100 scale.

``assess_payroll_data_quality`` returned ``completeness_score / 100`` (0–1)
while every other tool, the shared quality badge, the proof extractor and the
memo builders use 0–100 — so a fully complete register showed as 1%.
"""

from __future__ import annotations

import io
import re

import httpx
import pytest
from pydantic import ValidationError


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


def _register(blank_every: int = 0) -> bytes:
    rows = ["Employee ID,Employee Name,Department,Pay Date,Gross Pay,Check Number"]
    for i in range(1, 21):
        dept = "" if blank_every and i % blank_every == 0 else f"Dept {i % 3}"
        rows.append(f"E{i:03d},Employee Number{i},{dept},2025-03-14,{3000 + i * 23}.18,{5000 + i}")
    return ("\n".join(rows) + "\n").encode()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestScale:
    async def test_complete_register_reports_100_not_1(self):
        response = await _post("/audit/payroll-testing", files={"file": ("pr.csv", _register(), "text/csv")})
        assert response.status_code == 200, response.text
        assert response.json()["data_quality"]["completeness_score"] == 100.0

    async def test_partly_blank_register_is_a_percentage_not_a_fraction(self):
        response = await _post("/audit/payroll-testing", files={"file": ("pr.csv", _register(4), "text/csv")})
        score = response.json()["data_quality"]["completeness_score"]
        assert 1 < score < 100

    @pytest.mark.parametrize("pct", [0, 50, 100])
    async def test_memo_prints_exactly_the_percentage(self, pct):
        response = await _post("/audit/payroll-testing", files={"file": ("pr.csv", _register(), "text/csv")})
        screen = response.json()
        screen["data_quality"]["completeness_score"] = float(pct)

        memo = await _post("/export/payroll-testing-memo", json=screen)
        assert memo.status_code == 200, memo.text
        text = _pdf_text(memo.content)
        assert re.search(rf"Data Quality Score\s*\.*\s*{pct}%", text)
        assert re.search(rf"Data Completeness\s+{pct}%", text)

    async def test_out_of_range_completeness_is_refused(self):
        response = await _post("/audit/payroll-testing", files={"file": ("pr.csv", _register(), "text/csv")})
        screen = response.json()
        screen["data_quality"]["completeness_score"] = 150.0
        memo = await _post("/export/payroll-testing-memo", json=screen)
        assert memo.status_code == 422


def test_response_model_refuses_out_of_range_completeness():
    from shared.testing_response_schemas import DataQualityResponse

    with pytest.raises(ValidationError):
        DataQualityResponse(completeness_score=100.5, field_fill_rates={}, detected_issues=[], total_rows=1)
