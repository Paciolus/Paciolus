"""Sprint 890 (found during 15D): the multi-sheet trial balance route returned 500 on every request.

``TrialBalanceResponse`` requires ``classification_summary``; the consolidated multi-sheet result
never carried one, so FastAPI's response validation failed for every multi-sheet analysis.
"""

import httpx
import pytest


def _two_sheet_xlsx() -> bytes:
    import io

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["Account Name", "Debit", "Credit"])
    ws.append(["Cash", 1000, 0])
    ws.append(["Common Stock", 0, 1000])
    ws2 = wb.create_sheet("Sheet2")
    ws2.append(["Account Name", "Debit", "Credit"])
    ws2.append(["Inventory", 500, 0])
    ws2.append(["Accounts Payable", 0, 500])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_multi_sheet_analysis_returns_200_with_a_classification_summary(override_auth_verified):
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/audit/trial-balance",
            files={
                "file": (
                    "tb.xlsx",
                    _two_sheet_xlsx(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
            data={"force_resubmit": "true", "selected_sheets": '["Sheet1", "Sheet2"]'},
        )
    assert r.status_code == 200, r.text[:500]
    body = r.json()
    assert body["is_consolidated"] is True
    assert isinstance(body["classification_summary"], dict)
    assert sum(body["classification_summary"].values()) >= 1
