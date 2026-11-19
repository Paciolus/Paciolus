"""Sprint 886 / 11D (review OUT-12): supplemental schedules reach the memo.

The engines emit AP ``duplicate_payment_summary``, payroll
``payroll_register_total`` / ``department_summary`` / ``headcount_rollforward``
and AR ``aging_schedule``, and the memo generators print a section for each —
but the analysis response models did not declare them (so the browser never
received them), the pages did not send them and the export models did not
declare them. No memo ever printed those sections.

Each test runs the real analysis route and posts its response, as the page now
builds it, to the real memo route.
"""

from __future__ import annotations

import io
import re

import httpx
import pytest


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


def _money(value: float) -> str:
    return f"${value:,.2f}"


# ──────────────────────────────── AP ────────────────────────────────


def _ap_csv() -> bytes:
    rows = ["Invoice Number,Invoice Date,Payment Date,Vendor Name,Amount,Check Number,Description"]
    for i in range(1, 31):
        rows.append(
            f"INV{i:04d},2025-03-03,2025-03-{(i % 20) + 5:02d},Vendor {i % 6},{100 + i * 17}.42,{1000 + i},Supplies {i}"
        )
    # An exact duplicate: same vendor, invoice, amount and date, paid twice.
    rows.append("INV0003,2025-03-03,2025-03-08,Vendor 3,151.42,2001,Supplies 3")
    return ("\n".join(rows) + "\n").encode()


# ────────────────────────────── Payroll ──────────────────────────────


def _payroll_csv() -> bytes:
    rows = ["Employee ID,Employee Name,Department,Pay Date,Gross Pay,Hire Date,Termination Date"]
    for i in range(1, 25):
        term = "2025-02-15" if i == 5 else ""
        hire = "2025-01-20" if i == 9 else "2020-01-01"
        for month in ("01", "02", "03"):
            if i == 5 and month == "03":
                continue
            rows.append(f"E{i:03d},Employee Number{i},Dept {i % 3},2025-{month}-28,{3000 + i * 23}.18,{hire},{term}")
    return ("\n".join(rows) + "\n").encode()


# ──────────────────────────────── AR ────────────────────────────────

AR_TB = (
    "Account Name,Account Number,Debit,Credit\n"
    "Accounts Receivable,1200,9000.00,0\n"
    "Allowance for Doubtful Accounts,1210,0,300.00\n"
    "Revenue,4000,0,8700.00\n"
).encode()
AR_SL = (
    "Customer Name,Invoice Number,Invoice Date,Due Date,Amount,Days Past Due\n"
    "Acme,A-1,2025-01-05,2025-02-04,4000.00,10\n"
    "Beta,B-1,2024-11-01,2024-12-01,3000.00,75\n"
    "Gamma,G-1,2024-08-01,2024-08-31,2000.00,150\n"
).encode()


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestSchedulesReachTheMemo:
    async def test_ap_duplicate_payment_summary(self):
        response = await _post("/audit/ap-payments", files={"file": ("ap.csv", _ap_csv(), "text/csv")})
        assert response.status_code == 200, response.text
        screen = response.json()
        dup = screen["duplicate_payment_summary"]  # the response now carries it
        assert dup["exact_duplicate_count"] > 0
        assert dup["recovery_value_total"] > 0

        memo = await _post("/export/ap-testing-memo", json={**screen, "filename": "ap"})
        assert memo.status_code == 200, memo.text
        text = _pdf_text(memo.content)
        assert "Duplicate Payment Recovery Summary" in text
        assert _money(dup["recovery_value_total"]) in text
        for vendor in dup["vendor_rates"]:
            assert vendor["vendor"] in text

    async def test_payroll_register_departments_and_headcount(self):
        response = await _post("/audit/payroll-testing", files={"file": ("pr.csv", _payroll_csv(), "text/csv")})
        assert response.status_code == 200, response.text
        screen = response.json()
        assert screen["payroll_register_total"] > 0
        assert screen["department_summary"]
        hc = screen["headcount_rollforward"]
        assert hc is not None

        memo = await _post("/export/payroll-testing-memo", json={**screen})
        assert memo.status_code == 200, memo.text
        text = _pdf_text(memo.content)
        assert "Payroll Register-to-GL Reconciliation" in text
        assert _money(screen["payroll_register_total"]) in text
        assert "Salary Distribution by Department" in text
        for dept in screen["department_summary"]:
            assert dept["department"] in text
            assert _money(dept["total_gross_pay"]) in text
        assert "Headcount Roll-Forward" in text
        assert re.search(rf"Beginning of Period \({hc['period_start']}\)\s*\.*\s*{hc['beginning_headcount']}\b", text)
        assert re.search(rf"Final Pay Period of Register\s*\.*\s*{hc['final_period_headcount']}\b", text)

    async def test_ar_aging_schedule(self):
        response = await _post(
            "/audit/ar-aging",
            files={
                "tb_file": ("tb.csv", AR_TB, "text/csv"),
                "subledger_file": ("sl.csv", AR_SL, "text/csv"),
            },
            data={"as_of_date": "2025-02-14"},
        )
        assert response.status_code == 200, response.text
        screen = response.json()
        schedule = screen["aging_schedule"]
        assert schedule and sum(b["count"] for b in schedule) == 3

        memo = await _post("/export/ar-aging-memo", json={**screen, "filename": "ar"})
        assert memo.status_code == 200, memo.text
        text = _pdf_text(memo.content)
        assert "Aging Schedule" in text
        for bucket in schedule:
            if bucket["count"]:
                assert bucket["bucket"] in text
                assert _money(bucket["amount"]) in text


@pytest.mark.parametrize(
    ("model", "field", "bad"),
    [
        ("APTestingExportInput", "duplicate_payment_summary", {"exact_duplicate_count": "many"}),
        ("PayrollTestingExportInput", "department_summary", [{"department": "Ops"}]),
        ("PayrollTestingExportInput", "headcount_rollforward", {"beginning_headcount": "x"}),
        ("ARAgingExportInput", "aging_schedule", [{"bucket": "31-60", "count": -1, "amount": 1, "percentage": 1}]),
    ],
)
def test_schedules_are_typed_not_free_form(model, field, bad):
    from pydantic import ValidationError

    import shared.export_schemas as schemas

    base = {"composite_score": {}, "test_results": [], "data_quality": {}}
    with pytest.raises(ValidationError):
        getattr(schemas, model)(**base, **{field: bad})
