"""Sprint 886 / 11A (review OUT-09): the trial balance export shows what the screen showed.

``AuditResultInput`` declared no ``going_concern``, ``analytics`` or
``materiality_source``, and Pydantic dropped them. The PDF then read the missing
going-concern data as "nothing triggered" and printed "No going concern
indicators identified" while the screen showed a triggered indicator; the
Excel ratios tab printed "Insufficient data" and $0 category totals; and the
workbook guessed whether a ratio was a percentage by whether it exceeded 1, so
a 0.5% gross margin was written as 50%.

Every test drives a real trial balance through ``/audit/trial-balance`` (the
response is what the screen renders) and posts that response, unchanged, to
the export routes.
"""

from __future__ import annotations

import copy
import io
import re

import httpx
import pytest

# Assets 15,000; liabilities 40,000 (net liability: a going-concern indicator);
# current ratio 15,000 / 40,000; gross margin (100,000 - 99,500) / 100,000 = 0.5%.
TB_CSV = (
    "Account Name,Debit,Credit\n"
    "Cash,10000.00,0\n"
    "Inventory,5000.00,0\n"
    "Accounts Payable,0,40000.00\n"
    "Common Stock,0,1000.00\n"
    "Retained Earnings,26000.00,0\n"
    "Sales Revenue,0,100000.00\n"
    "Cost of Goods Sold,99500.00,0\n"
    "Rent Expense,500.00,0\n"
).encode()


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def _workbook(data: bytes):
    from openpyxl import load_workbook

    return load_workbook(io.BytesIO(data))


def _row_by_label(ws, label: str) -> int:
    for row in ws.iter_rows(min_col=1, max_col=1):
        cell = row[0]
        if cell.value == label:
            return cell.row
    raise AssertionError(f"{label!r} not found in {ws.title}")


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


@pytest.fixture
def engagement(override_auth_verified, make_engagement):
    from engagement_model import MaterialityBasis

    # Overall 2,000 → performance materiality 1,500 (factor 0.75).
    return make_engagement(
        user=override_auth_verified,
        materiality_basis=MaterialityBasis.MANUAL,
        materiality_amount=2000.0,
    )


async def _analyse(engagement_id: int | None = None) -> dict:
    data = {"force_resubmit": "true"}
    if engagement_id is not None:
        data["engagement_id"] = str(engagement_id)
    response = await _post("/audit/trial-balance", files={"file": ("tb.csv", TB_CSV, "text/csv")}, data=data)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
class TestScreenPdfExcelAgree:
    async def test_triggered_going_concern_indicator_is_in_the_pdf(self, engagement):
        screen = await _analyse(engagement.id)
        triggered = [i for i in screen["going_concern"]["indicators"] if i["triggered"]]
        assert triggered, "fixture must trigger a going-concern indicator on screen"

        response = await _post("/export/pdf", json=screen)
        assert response.status_code == 200, response.text
        text = _pdf_text(response.content)

        assert "No going concern indicators identified" not in text
        for indicator in triggered:
            assert indicator["indicator_name"] in text
        checked = screen["going_concern"]["indicators_checked"]
        assert re.search(rf"Indicators Triggered\s*\.*\s*{len(triggered)}\b", text)
        assert re.search(rf"Indicators Evaluated\s*\.*\s*{checked}\b", text)

    async def test_materiality_amount_and_source_are_in_the_pdf_and_excel(self, engagement):
        screen = await _analyse(engagement.id)
        assert screen["materiality_threshold"] == 1500.0
        assert screen["materiality_source"] == "engagement"

        pdf = _pdf_text((await _post("/export/pdf", json=screen)).content)
        assert "$1,500.00" in pdf
        assert "Performance materiality — Engagement" in pdf

        wb = _workbook((await _post("/export/excel", json=screen)).content)
        summary_text = " ".join(
            str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None
        )
        assert "Performance materiality — Engagement" in summary_text

    async def test_excel_ratios_match_the_screen(self, engagement):
        screen = await _analyse(engagement.id)
        ratios = screen["analytics"]["ratios"]
        assert ratios["gross_margin"]["display_value"] == "0.5%"
        assert ratios["current_ratio"]["is_calculable"] is True

        response = await _post("/export/excel", json=screen)
        assert response.status_code == 200, response.text
        ws = _workbook(response.content)["Key Ratios"]

        gm = ws.cell(row=_row_by_label(ws, "Gross Margin"), column=2)
        assert gm.value == pytest.approx(0.005)  # 0.5%, not 50%
        assert gm.number_format == "0.0%"

        cr = ws.cell(row=_row_by_label(ws, "Current Ratio"), column=2)
        assert cr.value == pytest.approx(ratios["current_ratio"]["value"])
        assert cr.number_format == "0.00"

        # Category totals come from the analysis, not $0.
        assets = ws.cell(row=_row_by_label(ws, "Total Assets"), column=2).value
        assert float(assets) == pytest.approx(15000.0)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
class TestNotSuppliedIsNotNone:
    async def test_going_concern_not_supplied_says_not_evaluated(self, engagement):
        screen = await _analyse(engagement.id)
        screen.pop("going_concern")

        text = _pdf_text((await _post("/export/pdf", json=screen)).content)
        assert "No going concern indicators identified" not in text
        assert "Going concern indicators were not evaluated" in text

    async def test_evaluated_and_none_triggered_says_none_identified(self, engagement):
        screen = await _analyse(engagement.id)
        gc = copy.deepcopy(screen["going_concern"])
        for indicator in gc["indicators"]:
            indicator["triggered"] = False
        gc["indicators_triggered"] = 0
        screen["going_concern"] = gc

        text = _pdf_text((await _post("/export/pdf", json=screen)).content)
        assert "No going concern indicators identified" in text
        assert "not evaluated" not in text

    async def test_materiality_source_not_supplied_says_not_available(self, engagement):
        screen = await _analyse(engagement.id)
        screen.pop("materiality_source")
        screen.pop("materiality_basis")  # Sprint 886 / 11G: the structured basis

        text = _pdf_text((await _post("/export/pdf", json=screen)).content)
        assert "Performance materiality — Engagement" not in text
        assert re.search(r"Materiality Source\s*\.*\s*Not available", text)

    async def test_analytics_not_supplied_says_not_available_not_zero(self, engagement):
        screen = await _analyse(engagement.id)
        screen.pop("analytics")

        ws = _workbook((await _post("/export/excel", json=screen)).content)["Key Ratios"]
        gm_row = _row_by_label(ws, "Gross Margin")
        assert ws.cell(row=gm_row, column=2).value == "Not available"
        assert ws.cell(row=_row_by_label(ws, "Total Assets"), column=2).value == "Not available"

    async def test_inconsistent_going_concern_counts_are_refused(self, engagement):
        screen = await _analyse(engagement.id)
        screen["going_concern"]["indicators_triggered"] = 0  # one is triggered

        response = await _post("/export/pdf", json=screen)
        assert response.status_code == 422, response.text

    async def test_ratio_without_a_unit_is_written_as_the_screen_text(self, engagement):
        """A ratio from an analysis made before units existed: no guessing from its size."""
        screen = await _analyse(engagement.id)
        for ratio in screen["analytics"]["ratios"].values():
            ratio.pop("unit", None)

        ws = _workbook((await _post("/export/excel", json=screen)).content)["Key Ratios"]
        assert ws.cell(row=_row_by_label(ws, "Gross Margin"), column=2).value == "0.5%"
