"""Sprint 886 / 11F (review OUT-15): the AR memo's column confidence means what the screen's does.

The shared Proof Summary read ``result["column_detection"]``; AR carries
``tb_column_detection`` and ``sl_column_detection`` instead, so every AR memo
printed "Column Confidence 0%". The screen shows the mean of the two
detections (0.8 and 1.0 → 0.90); the memo now prints the same figure, and a
run that carried no detection prints "Not available".
"""

from __future__ import annotations

import io
import re

import httpx
import pytest

from tests.test_sprint886_supplemental_schedules import AR_SL, AR_TB


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


async def _screen(with_subledger: bool = True) -> dict:
    files = {"tb_file": ("tb.csv", AR_TB, "text/csv")}
    data = {}
    if with_subledger:
        files["subledger_file"] = ("sl.csv", AR_SL, "text/csv")
        data["as_of_date"] = "2025-02-14"
    response = await _post("/audit/ar-aging", files=files, data=data)
    assert response.status_code == 200, response.text
    return response.json()


def _column_confidence(text: str) -> str:
    match = re.search(r"Column Confidence\s+(\S+(?: available)?)", text)
    assert match, "no Column Confidence line"
    return match.group(1)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestARColumnConfidence:
    async def test_mean_of_tb_and_subledger_as_on_screen(self):
        screen = await _screen()
        screen["tb_column_detection"]["overall_confidence"] = 0.8
        screen["sl_column_detection"]["overall_confidence"] = 1.0

        text = _pdf_text((await _post("/export/ar-aging-memo", json={**screen, "filename": "ar"})).content)
        assert _column_confidence(text) == "90%"

    async def test_tb_only_run_uses_the_tb_detection(self):
        screen = await _screen(with_subledger=False)
        assert screen["sl_column_detection"] is None
        screen["tb_column_detection"]["overall_confidence"] = 0.8

        text = _pdf_text((await _post("/export/ar-aging-memo", json={**screen, "filename": "ar"})).content)
        assert _column_confidence(text) == "80%"

    async def test_no_detection_prints_not_available_not_zero(self):
        screen = await _screen()
        screen["tb_column_detection"] = None
        screen["sl_column_detection"] = None

        text = _pdf_text((await _post("/export/ar-aging-memo", json={**screen, "filename": "ar"})).content)
        assert _column_confidence(text) == "Not available"
