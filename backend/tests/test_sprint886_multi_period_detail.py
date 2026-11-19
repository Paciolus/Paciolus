"""Sprint 886 / 11I (review comparison table): the multi-period memo shows what the screen shows, or says what it omits.

The page sent the dormant-account count but not the names, and stripped the
account detail from each lead sheet. Now the names are sent and printed (a
count without names prints "Not available"), and the memo says that each lead
sheet's account detail is on screen and in the movements CSV, not in the memo.
"""

from __future__ import annotations

import io
import re

import httpx
import pytest

PRIOR = [
    {"account": "Cash", "debit": 5000, "credit": 0, "type": "asset"},
    {"account": "Petty Cash Old Branch", "debit": 0, "credit": 0, "type": "asset"},
    {"account": "Suspense Clearing", "debit": 0, "credit": 0, "type": "liability"},
    {"account": "Revenue", "debit": 0, "credit": 5000, "type": "revenue"},
]
CURRENT = [
    {"account": "Cash", "debit": 9000, "credit": 0, "type": "asset"},
    {"account": "Petty Cash Old Branch", "debit": 0, "credit": 0, "type": "asset"},
    {"account": "Suspense Clearing", "debit": 0, "credit": 0, "type": "liability"},
    {"account": "Revenue", "debit": 0, "credit": 9000, "type": "revenue"},
]


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


def _page_body(screen: dict) -> dict:
    """What useMultiPeriodMemoExport sends."""
    return {
        "prior_label": screen["prior_label"],
        "current_label": screen["current_label"],
        "total_accounts": screen["total_accounts"],
        "movements_by_type": screen["movements_by_type"],
        "movements_by_significance": screen["movements_by_significance"],
        "significant_movements": screen["significant_movements"],
        "lead_sheet_summaries": [
            {
                k: ls[k]
                for k in (
                    "lead_sheet",
                    "lead_sheet_name",
                    "account_count",
                    "prior_total",
                    "current_total",
                    "net_change",
                )
            }
            for ls in screen["lead_sheet_summaries"]
        ],
        "dormant_account_count": len(screen["dormant_accounts"]),
        "dormant_accounts": screen["dormant_accounts"],
        "filename": "mp",
    }


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestMultiPeriodMemo:
    async def _screen(self) -> dict:
        response = await _post(
            "/audit/compare-periods",
            json={"prior_accounts": PRIOR, "current_accounts": CURRENT, "prior_label": "FY24", "current_label": "FY25"},
        )
        assert response.status_code == 200, response.text
        screen = response.json()
        assert sorted(screen["dormant_accounts"]) == ["Petty Cash Old Branch", "Suspense Clearing"]
        return screen

    async def test_dormant_names_are_printed(self):
        screen = await self._screen()
        text = _pdf_text((await _post("/export/multi-period-memo", json=_page_body(screen))).content)
        for name in screen["dormant_accounts"]:
            assert name in text

    async def test_dormant_count_without_names_says_not_available(self):
        screen = await self._screen()
        body = _page_body(screen)
        body["dormant_accounts"] = []
        text = _pdf_text((await _post("/export/multi-period-memo", json=body)).content)
        assert re.search(r"Dormant account names\s*\.*\s*Not available", text)

    async def test_lead_sheet_account_detail_is_stated_as_omitted(self):
        screen = await self._screen()
        text = _pdf_text((await _post("/export/multi-period-memo", json=_page_body(screen))).content)
        assert "Account-level detail for each lead sheet is not reproduced in this memo" in text
