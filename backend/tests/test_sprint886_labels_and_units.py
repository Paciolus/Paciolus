"""Sprint 886 / 11I (review comparison table): labels say what each figure counts.

* The trial balance PDF called ``high_severity`` "Above Materiality" and
  ``low_severity`` "Below Materiality" and left out ``medium_severity``. These
  are severity counts: labelled as such, all three shown.
* Testing tools: ``total_flagged`` counts distinct rows, while the CSV has one
  row per flag and the severity counts count flags. Each figure names its unit.
* The composite score is printed with one decimal everywhere, the tier label
  included (CEO, 2026-11-19).
"""

from __future__ import annotations

import copy
import csv
import io
import re

import httpx
import pytest

from tests.test_sprint886_supplemental_schedules import _ap_csv
from tests.test_sprint886_tb_export_fidelity import TB_CSV


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


async def _tb_screen() -> dict:
    response = await _post(
        "/audit/trial-balance",
        files={"file": ("tb.csv", TB_CSV, "text/csv")},
        data={"force_resubmit": "true", "materiality_threshold": "750", "materiality_origin": "entered"},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestTrialBalanceSeverity:
    async def test_three_severity_counts_labelled_as_severity(self):
        screen = await _tb_screen()
        screen["risk_summary"].update(high_severity=3, medium_severity=2, low_severity=1)
        text = _pdf_text((await _post("/export/pdf", json=screen)).content)

        assert "Above Materiality" not in text.split("Items Flagged", 1)[1][:200]
        assert re.search(r"High Severity\s+Medium Severity\s+Low Severity", text)
        assert re.search(r"\b3\s+2\s+1\b", text)

    async def test_missing_severity_counts_are_not_available(self):
        screen = await _tb_screen()
        screen.pop("risk_summary")
        text = _pdf_text((await _post("/export/pdf", json=screen)).content)
        assert re.search(r"Severity counts\s*\.*\s*Not available", text)

    async def test_score_has_one_decimal_beside_the_tier_too(self):
        screen = await _tb_screen()
        text = _pdf_text((await _post("/export/pdf", json=screen)).content)
        score = re.search(r"Composite Diagnostic Score\s*\.*\s*(\d+\.\d) / 100", text)
        assert score, "score with one decimal"
        assert re.search(rf"Diagnostic Tier\s*\.*\s*[A-Z]+ \({re.escape(score.group(1))}/100\)", text)


async def _ap_screen() -> dict:
    response = await _post("/audit/ap-payments", files={"file": ("ap.csv", _ap_csv(), "text/csv")})
    assert response.status_code == 200, response.text
    return response.json()


def _flags(screen: dict) -> int:
    return sum(len(t.get("flagged_entries") or []) for t in screen["test_results"])


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestTestingToolUnits:
    async def test_fixture_has_entries_with_more_than_one_flag(self):
        screen = await _ap_screen()
        assert _flags(screen) > screen["composite_score"]["total_flagged"]

    async def test_memo_names_each_unit(self):
        screen = await _ap_screen()
        composite = screen["composite_score"]
        text = _pdf_text((await _post("/export/ap-testing-memo", json={**screen, "filename": "ap"})).content)

        assert re.search(rf"Payments Flagged \(distinct payments\)\s*\.*\s*{composite['total_flagged']}\b", text)
        assert re.search(rf"Flags Raised \(one per test per payment\)\s*\.*\s*{_flags(screen)}\b", text)
        sev = composite["flags_by_severity"]
        assert re.search(rf"High Severity Flags\s*\.*\s*{sev['high']}\b", text)
        assert sum(sev.values()) == _flags(screen)
        score = f"{composite['score']:.1f}"
        assert re.search(rf"Diagnostic Tier\s*\.*\s*[A-Z]+ \({re.escape(score)}/100\)", text)

    async def test_csv_names_each_unit_and_its_rows_are_flags(self):
        screen = await _ap_screen()
        composite = screen["composite_score"]
        rows = list(
            csv.reader(
                io.StringIO(
                    (await _post("/export/csv/ap-testing", json=copy.deepcopy(screen))).content.decode("utf-8-sig")
                )
            )
        )
        summary_at = rows.index(["SUMMARY"])
        data_rows = [r for r in rows[1:summary_at] if r]
        summary = {r[0]: r[1] for r in rows[summary_at + 1 :] if len(r) >= 2}

        assert len(data_rows) == _flags(screen)
        assert summary["Flags Raised (one row above per flag)"] == str(_flags(screen))
        assert summary["Payments Flagged (distinct payments)"] == str(composite["total_flagged"])
        assert summary["Composite Score"] == f"{composite['score']:.1f}"
