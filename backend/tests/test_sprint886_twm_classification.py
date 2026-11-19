"""Sprint 886 / 11C (review OUT-11): three-way match shows the engine's own classification.

The memo read ``composite.get("score", 0)``, but the three-way match engine emits
no composite score and the export model declares none (``compute_twm_diagnostic_score``
had no caller). So every memo printed "(0/100)" and "Composite Diagnostic Score:
0.0/100", and renamed the engine's MEDIUM to MODERATE and HIGH to ELEVATED.

Decided (CEO, 2026-11-19): no score; the engine's Low / Medium / High
classification and wording on screen, PDF and CSV.
"""

from __future__ import annotations

import csv
import io
import re

import httpx
import pytest

_PO_HEAD = "PO Number,Vendor,Description,Quantity,Unit Price,Total Amount,Order Date,Expected Delivery"
_INV_HEAD = "Invoice Number,PO Reference,Vendor,Description,Quantity,Unit Price,Total Amount,Invoice Date"
_REC_HEAD = "Receipt Number,PO Reference,Invoice Reference,Vendor,Description,Quantity Received,Receipt Date"


def _files(pos: int, matched: int, overbilled: int = 0) -> dict:
    """``pos`` POs; the first ``matched`` have an invoice and a receipt; the first
    ``overbilled`` of those are invoiced at 120 instead of 100 (a material variance)."""
    po = [_PO_HEAD]
    inv = [_INV_HEAD]
    rec = [_REC_HEAD]
    for i in range(1, pos + 1):
        po.append(f"PO-{i},Vendor {i},Widgets,10,100.00,1000.00,2025-01-01,2025-01-10")
        if i <= matched:
            price = 120 if i <= overbilled else 100
            inv.append(f"INV-{i},PO-{i},Vendor {i},Widgets,10,{price}.00,{price * 10}.00,2025-01-12")
            rec.append(f"GRN-{i},PO-{i},INV-{i},Vendor {i},Widgets,10,2025-01-11")
    return {
        "po_file": ("po.csv", "\n".join(po).encode(), "text/csv"),
        "invoice_file": ("inv.csv", "\n".join(inv).encode(), "text/csv"),
        "receipt_file": ("rec.csv", "\n".join(rec).encode(), "text/csv"),
    }


FIXTURES = {
    "low": _files(pos=10, matched=10),
    "medium": _files(pos=10, matched=10, overbilled=1),
    "high": _files(pos=10, matched=3),
}


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
@pytest.mark.parametrize("level", ["low", "medium", "high"])
class TestOneClassificationEverywhere:
    async def _screen(self, level: str) -> dict:
        response = await _post("/audit/three-way-match", files=FIXTURES[level])
        assert response.status_code == 200, response.text
        screen = response.json()
        assert screen["summary"]["risk_assessment"] == level  # the fixture hits the level
        return screen

    async def test_memo_prints_the_engine_classification_and_no_score(self, level):
        screen = await self._screen(level)
        response = await _post("/export/three-way-match-memo", json=screen)
        assert response.status_code == 200, response.text
        text = _pdf_text(response.content)

        assert re.search(rf"Risk Assessment\s*\.*\s*{level.upper()}\b", text)
        assert "/100" not in text and "/ 100" not in text
        assert "Composite Diagnostic Score" not in text
        assert "MODERATE" not in text and "ELEVATED" not in text
        assert re.search(rf"returned a {level.upper()} risk assessment", text)

    async def test_csv_prints_the_same_classification(self, level):
        screen = await self._screen(level)
        response = await _post("/export/csv/three-way-match", json=screen)
        assert response.status_code == 200, response.text
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
        assert ["Risk Assessment", level.upper()] in rows


def test_the_uncomputed_scoring_function_is_gone():
    import three_way_match_memo_generator as twm

    assert not hasattr(twm, "compute_twm_diagnostic_score")
    assert not hasattr(twm, "compute_twm_risk_score")
