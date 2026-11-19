"""Sprint 885 / 10F (review OUT-34): document properties name Paciolus, not the libraries.

Workbooks said "openpyxl" (creator) and "Microsoft Excel Compatible /
Openpyxl 3.1.5" (application); PDFs said "ReportLab PDF Library" (producer)
and "anonymous" (author and creator). Every export now carries a title,
"Paciolus" as creator/application/producer, and an author only when the firm
entered one — never a library name, a path or a machine user name.
"""

from __future__ import annotations

import getpass
import io
import os
import re
import zipfile
from datetime import date
from decimal import Decimal

import pytest
from pypdf import PdfReader

LIBRARY_WORDS = ("openpyxl", "reportlab", "anonymous", "microsoft", "python")


def _no_leaks(text: str) -> None:
    lowered = text.lower()
    for word in LIBRARY_WORDS:
        assert word not in lowered, word
    for private in {getpass.getuser(), os.path.expanduser("~"), os.getcwd()}:
        if private and len(private) > 2:
            assert private.lower() not in lowered, private


def _workbook_props(xlsx: bytes) -> tuple[str, str]:
    with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
        return z.read("docProps/core.xml").decode("utf-8"), z.read("docProps/app.xml").decode("utf-8")


def _check_workbook(xlsx: bytes, title: str) -> None:
    core, app = _workbook_props(xlsx)
    assert re.search(r"<dc:creator[^>]*>Paciolus</dc:creator>", core), core
    assert re.search(rf"<dc:title[^>]*>{re.escape(title)}</dc:title>", core), core
    assert "<Application>Paciolus</Application>" in app
    _no_leaks(core + app)


def _check_pdf(pdf: bytes, title: str, author: str = "") -> None:
    info = PdfReader(io.BytesIO(pdf)).metadata
    assert info.get("/Producer") == "Paciolus"
    assert info.get("/Creator") == "Paciolus"
    assert info.get("/Title") == title
    assert (info.get("/Author") or "") == author
    _no_leaks(" ".join(str(v) for v in info.values()))


_AUDIT = {
    "status": "balanced",
    "balanced": True,
    "total_debits": 100.0,
    "total_credits": 100.0,
    "difference": 0.0,
    "row_count": 1,
    "message": "ok",
    "abnormal_balances": [],
    "has_risk_alerts": False,
    "materiality_threshold": 10.0,
    "material_count": 0,
    "immaterial_count": 0,
    "all_accounts": [{"account": "Cash", "debit": 100.0, "credit": 0.0, "type": "asset"}],
}


class TestWorkbooks:
    def test_diagnostic_workpaper(self):
        from excel_generator import generate_workpaper

        _check_workbook(generate_workpaper(_AUDIT, "tb"), "Trial Balance Diagnostic Workpaper")

    def test_lead_sheets(self):
        from export.serializers.excel import serialize_leadsheets_excel
        from shared.export_schemas import LeadSheetInput

        payload = LeadSheetInput(
            flux={
                "items": [],
                "summary": {
                    "total_items": 0,
                    "high_risk_count": 0,
                    "medium_risk_count": 0,
                    "new_accounts": 0,
                    "removed_accounts": 0,
                    "threshold": 0,
                },
            },
            recon={"scores": [], "stats": {"high": 0, "medium": 0, "low": 0}},
            filename="tb",
        )
        _check_workbook(serialize_leadsheets_excel(payload), "Lead Sheets")

    def test_loan_schedule(self):
        from loan_amortization_engine import LoanConfig, generate_amortization_schedule
        from loan_amortization_excel import build_amortization_workbook

        cfg = LoanConfig(
            principal=Decimal("1000"), annual_rate=Decimal("0.05"), term_periods=2, start_date=date(2026, 1, 1)
        )
        _check_workbook(build_amortization_workbook(generate_amortization_schedule(cfg)), "Loan Amortization Schedule")


class TestPdfs:
    def test_memo_without_an_author(self):
        from je_testing_memo_generator import generate_je_testing_memo
        from tests.test_sprint819_output_snapshots import CASES

        pdf = generate_je_testing_memo(CASES["je"](), filename="gl")
        _check_pdf(pdf, "Journal Entry Testing Memo")

    def test_memo_author_is_what_the_firm_entered(self):
        from je_testing_memo_generator import generate_je_testing_memo
        from tests.test_sprint819_output_snapshots import CASES

        pdf = generate_je_testing_memo(
            CASES["je"](), filename="gl", prepared_by="Jane Auditor, CPA", include_signoff=True
        )
        _check_pdf(pdf, "Journal Entry Testing Memo", author="Jane Auditor, CPA")

    def test_diagnostic_report(self):
        from pdf import generate_audit_report

        _check_pdf(generate_audit_report(_AUDIT, "tb"), "Trial Balance Diagnostic Summary")

    def test_loan_schedule_pdf(self):
        from loan_amortization_engine import LoanConfig, generate_amortization_schedule
        from pdf.sections.loan_amortization import build_amortization_pdf

        cfg = LoanConfig(
            principal=Decimal("1000"), annual_rate=Decimal("0.05"), term_periods=2, start_date=date(2026, 1, 1)
        )
        _check_pdf(build_amortization_pdf(generate_amortization_schedule(cfg)), "Loan Amortization Schedule")


@pytest.mark.parametrize("name", ["anonymous", "ReportLab"])
def test_detector_catches_library_names(name):
    with pytest.raises(AssertionError):
        _no_leaks(f"Producer: {name}")
