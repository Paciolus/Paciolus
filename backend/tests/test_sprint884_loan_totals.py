"""Sprint 884 / 9E (review OUT-06): loan totals sit under their own columns.

The workbook's Schedule totals row wrote ``total_payments`` into column 8,
headed "Ending Balance"; the CSV export did the same. Every total must sit
under the column it totals, equal the sum of that column, and agree across
the schedule, the annual summary, the inputs sheet, the PDF and the CSV.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal

import httpx
import pytest
from openpyxl import load_workbook

from loan_amortization_engine import ExtraPayment, LoanConfig, LoanMethod, generate_amortization_schedule
from loan_amortization_excel import build_amortization_workbook

LOANS = {
    "ordinary": {"principal": "25000.00", "annual_rate": "0.065", "term_periods": 36},
    "extra_payments": {
        "principal": "25000.00",
        "annual_rate": "0.065",
        "term_periods": 36,
        "extra_payments": [{"period_number": 3, "amount": "1500.00"}, {"period_number": 10, "amount": "2500.55"}],
    },
    "balloon": {
        "principal": "100000.00",
        "annual_rate": "0.0725",
        "term_periods": 24,
        "method": "balloon",
        "balloon_amount": "40000.00",
    },
}

SCHEDULE_COLUMNS = ["Scheduled Payment", "Interest", "Principal", "Extra Principal"]
ATTRS = {
    "Scheduled Payment": "scheduled_payment",
    "Interest": "interest",
    "Principal": "principal",
    "Extra Principal": "extra_principal",
}


def _config(spec: dict) -> LoanConfig:
    return LoanConfig(
        principal=Decimal(spec["principal"]),
        annual_rate=Decimal(spec["annual_rate"]),
        term_periods=spec["term_periods"],
        method=LoanMethod(spec.get("method", "standard")),
        start_date=date(2026, 1, 1),
        balloon_amount=Decimal(spec["balloon_amount"]) if spec.get("balloon_amount") else None,
        extra_payments=[ExtraPayment(e["period_number"], Decimal(e["amount"])) for e in spec.get("extra_payments", [])],
    )


def _column_sums(result) -> dict[str, Decimal]:
    return {col: sum((getattr(e, ATTRS[col]) for e in result.schedule), Decimal("0")) for col in SCHEDULE_COLUMNS}


def _cents(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _row_by_label(ws, label: str) -> tuple:
    for row in ws.iter_rows(values_only=True):
        if row and row[0] == label:
            return row
    raise AssertionError(f"no row labelled {label!r}")


@pytest.mark.parametrize("loan", LOANS)
def test_workbook_totals_row_sits_under_its_own_columns(loan):
    result = generate_amortization_schedule(_config(LOANS[loan]))
    wb = load_workbook(io.BytesIO(build_amortization_workbook(result)))
    ws = wb["Schedule"]
    headers = [c.value for c in ws[1]]
    totals = dict(zip(headers, _row_by_label(ws, "Totals")))
    sums = _column_sums(result)

    for col in SCHEDULE_COLUMNS:
        assert _cents(totals[col]) == sums[col], col
    assert totals["Ending Balance"] in (None, "")  # a balance is not summed
    assert totals["Beginning Balance"] in (None, "")

    final = dict(zip(headers, _row_by_label(ws, "Final Ending Balance")))
    assert _cents(final["Ending Balance"]) == result.schedule[-1].ending_balance
    assert result.schedule[-1].ending_balance == 0

    # Payments column + extra principal = the engine's total payments; interest agrees too.
    assert sums["Scheduled Payment"] + sums["Extra Principal"] == result.total_payments
    assert sums["Interest"] == result.total_interest
    # Principal retired equals the loan.
    assert sums["Principal"] + sums["Extra Principal"] == Decimal(LOANS[loan]["principal"])


@pytest.mark.parametrize("loan", LOANS)
def test_annual_summary_and_inputs_agree_with_the_schedule(loan):
    result = generate_amortization_schedule(_config(LOANS[loan]))
    wb = load_workbook(io.BytesIO(build_amortization_workbook(result)))
    sums = _column_sums(result)

    annual = list(wb["Annual Summary"].iter_rows(min_row=2, values_only=True))
    annual = [r for r in annual if isinstance(r[0], int)]
    assert sum(_cents(r[2]) for r in annual) == sums["Scheduled Payment"] + sums["Extra Principal"]
    assert sum(_cents(r[3]) for r in annual) == sums["Interest"]
    assert sum(_cents(r[4]) for r in annual) == sums["Principal"] + sums["Extra Principal"]
    assert _cents(annual[-1][5]) == result.schedule[-1].ending_balance

    inputs = {r[0]: r[1] for r in wb["Inputs"].iter_rows(min_row=2, values_only=True) if r[0]}
    assert _cents(inputs["Total Interest"]) == sums["Interest"]
    assert _cents(inputs["Total Payments"]) == sums["Scheduled Payment"] + sums["Extra Principal"]


@pytest.mark.usefixtures("bypass_csrf")
class TestExportsAgree:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("loan", LOANS)
    async def test_csv_totals_sit_under_their_own_columns(self, loan, override_auth_verified):
        from main import app

        result = generate_amortization_schedule(_config(LOANS[loan]))
        sums = _column_sums(result)
        payload = {**LOANS[loan], "start_date": "2026-01-01"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/audit/loan-amortization/export.csv", json=payload)
        assert response.status_code == 200, response.text
        rows = list(csv.reader(io.StringIO(response.text)))
        headers = rows[0]
        totals = dict(zip(headers, next(r for r in rows if r and r[0] == "Totals")))
        for col in SCHEDULE_COLUMNS:
            assert Decimal(totals[col]) == sums[col], col
        assert totals["Ending Balance"] == ""
        final = dict(zip(headers, next(r for r in rows if r and r[0] == "Final Ending Balance")))
        assert Decimal(final["Ending Balance"]) == result.schedule[-1].ending_balance
        # No total is written under a balance column.
        for r in rows:
            if r and r[0] in ("Total Interest", "Total Payments"):
                raise AssertionError(f"stray total row {r}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("loan", LOANS)
    async def test_pdf_shows_the_same_totals(self, loan, override_auth_verified):
        from pypdf import PdfReader

        from main import app

        result = generate_amortization_schedule(_config(LOANS[loan]))
        sums = _column_sums(result)
        payload = {**LOANS[loan], "start_date": "2026-01-01"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/audit/loan-amortization/export.pdf", json=payload)
        assert response.status_code == 200, response.text
        text = " ".join(
            " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(response.content)).pages).split()
        )
        assert f"${sums['Interest']:,.2f}" in text
        assert f"${sums['Scheduled Payment'] + sums['Extra Principal']:,.2f}" in text
        # The schedule table's totals row, column by column.
        expected = " ".join(f"${sums[c]:,.2f}" for c in SCHEDULE_COLUMNS)
        assert f"Totals {expected}" in text
