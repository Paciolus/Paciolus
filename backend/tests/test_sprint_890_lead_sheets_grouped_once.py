"""Sprint 890 (CEO brief 15D, review ST-11): lead sheets are grouped in one place.

The single-sheet engine grouped lead sheets, then the route's post-processor
(``shared/tb_post_processor.apply_lead_sheet_grouping``) grouped them again; the multi-sheet engine
did not group at all and relied on the post-processor. The engine now groups in both paths, and
the post-processor only adds the section density it needs.
"""

from __future__ import annotations

import io
from unittest.mock import patch

import httpx
import pytest

TB_CSV = ("Account Name,Debit,Credit\nCash,1000.00,0\nAccounts Payable,0,400.00\nCommon Stock,0,600.00\n").encode()


def _two_sheet_xlsx() -> bytes:
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


def _counting_grouper():
    import lead_sheet_mapping

    real = lead_sheet_mapping.group_by_lead_sheet
    calls = []

    def counted(accounts, *a, **k):
        calls.append(len(accounts))
        return real(accounts, *a, **k)

    return patch.object(lead_sheet_mapping, "group_by_lead_sheet", side_effect=counted), calls


async def _post(**kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post("/audit/trial-balance", **kwargs)


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_single_sheet_groups_once(override_auth_verified):
    patcher, calls = _counting_grouper()
    with patcher:
        r = await _post(files={"file": ("tb.csv", TB_CSV, "text/csv")}, data={"force_resubmit": "true"})
    assert r.status_code == 200, r.text
    assert calls == [3]
    assert r.json()["lead_sheet_grouping"]["summaries"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_multi_sheet_groups_once_in_the_engine(override_auth_verified):
    xlsx = _two_sheet_xlsx()
    patcher, calls = _counting_grouper()
    with patcher:
        r = await _post(
            files={"file": ("tb.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"force_resubmit": "true", "selected_sheets": '["Sheet1", "Sheet2"]'},
        )
    assert r.status_code == 200, r.text
    assert calls == [4]
    assert r.json()["lead_sheet_grouping"]["summaries"]


def test_multi_sheet_engine_returns_its_own_grouping():
    from audit.pipeline import audit_trial_balance_multi_sheet

    result = audit_trial_balance_multi_sheet(
        file_bytes=_two_sheet_xlsx(), filename="tb.xlsx", selected_sheets=["Sheet1", "Sheet2"]
    )
    assert result["lead_sheet_grouping"]["summaries"]


def test_post_processor_no_longer_imports_from_a_route_module():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "shared" / "tb_post_processor.py").read_text(encoding="utf-8")
    assert "from routes." not in source
