"""Sprint 886 / 11I (review comparison table): the fixed-asset memo prints only what the engine computes.

The roll-forward, depreciation-rate and category-composition sections read
top-level fields the fixed-asset engine never emits (register totals,
additions, disposals, TB PP&E, depreciation expense, prior-period rate,
category summary, period label), and the export model drops them, so they
never printed for a customer — only in the sample memo, with an "FY2025"
fallback label. The tool has no data for them: removed, with the hard-coded year.
"""

from __future__ import annotations

import io

import httpx
import pytest

from fixed_asset_testing_memo_generator import generate_fixed_asset_testing_memo
from tests.test_fixed_asset_testing_memo import _make_fa_result

ENGINE_NEVER_EMITS = {
    "register_total_cost": 3_420_000.00,
    "register_total_accum_depr": 1_180_000.00,
    "tb_ppe_gross": 3_420_000.00,
    "tb_accum_depr": 1_180_000.00,
    "additions": 420_000.00,
    "depreciation_expense": 285_000.00,
    "period_label": "FY2025",
    "category_summary": [{"category": "Equipment", "count": 30, "gross_cost": 1_500_000.0, "accum_depr": 600_000.0}],
}
GONE = ("Roll-Forward", "FY2025", "Depreciation Rate", "Asset Register Composition")


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def test_sections_without_a_data_source_are_gone():
    text = _pdf_text(generate_fixed_asset_testing_memo({**_make_fa_result(), **ENGINE_NEVER_EMITS}))
    for phrase in GONE:
        assert phrase not in text, phrase


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
async def test_route_memo_has_no_hard_coded_year():
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/export/fixed-asset-memo", json={**_make_fa_result(), "filename": "fa"})
    assert response.status_code == 200, response.text
    text = _pdf_text(response.content)
    for phrase in GONE:
        assert phrase not in text, phrase
