"""Sprint 885 / 10B (review OUT-02): every Excel cell goes through one typed writer.

The workpaper wrote ``workpaper_date`` — an unrestricted string — straight into
a cell, so "=1+1" was saved as a live formula; the lead-sheet notes and risk
factors were written the same way, and the nested export inputs were untyped
dicts and lists. Now text is written as text (never a formula), numbers stay
numeric, dates are validated as dates, and the nested inputs are models.

Each test puts formula-starting strings in every text input it can reach and
then inspects the worksheet XML: no ``<f>`` (formula) element may exist.
"""

from __future__ import annotations

import io
import re
import zipfile
from datetime import date
from decimal import Decimal

import httpx
import pytest
from pydantic import ValidationError

HOSTILE = ["=1+1", "+SUM(A1:A2)", "-2+3", "@cmd", '=HYPERLINK("http://x","y")', "|calc", "=cmd|' /C calc'!A0"]


def _sheets_xml(xlsx: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
        return {n: z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("xl/worksheets/sheet")}


def _all_text(xlsx: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
        return "".join(z.read(n).decode("utf-8") for n in z.namelist() if n.endswith(".xml"))


def _assert_no_formulas(xlsx: bytes) -> None:
    for name, xml in _sheets_xml(xlsx).items():
        assert "<f>" not in xml and "<f " not in xml, name


def _assert_hostile_text_present(xlsx: bytes, values: list[str]) -> None:
    from xml.sax.saxutils import escape

    text = _all_text(xlsx)
    for v in values:
        assert escape(v, {'"': "&quot;"}) in text or escape(v) in text, v


def _flag(i: int, text: str, amount: float) -> dict:
    return {
        "account": text,
        "type": text,
        "issue": text,
        "amount": amount,
        "debit": max(amount, 0),
        "credit": max(-amount, 0),
        "materiality": "material" if i % 2 else "immaterial",
        "severity": text,
        "anomaly_type": "abnormal_balance",
    }


def _audit_payload(**overrides) -> dict:
    flags = [_flag(i, t, -125.5 if i % 2 else 80.0) for i, t in enumerate(HOSTILE)]
    base = {
        "status": "balanced",
        "balanced": True,
        "total_debits": 1000.0,
        "total_credits": 1000.0,
        "difference": 0.0,
        "row_count": len(HOSTILE),
        "message": "ok",
        "abnormal_balances": flags,
        "has_risk_alerts": True,
        "materiality_threshold": 100.0,
        "material_count": 3,
        "immaterial_count": 4,
        "filename": "=1+1",
        "all_accounts": [
            {"account": t, "debit": 0.0, "credit": 125.5, "type": t}
            if i % 2
            else {"account": t, "debit": 80.0, "credit": 0.0, "type": t}
            for i, t in enumerate(HOSTILE)
        ],
        "prepared_by": "=1+1",
        "reviewed_by": "@SUM(A1)",
        "workpaper_date": "2026-11-18",
        "include_signoff": True,
    }
    base.update(overrides)
    return base


# ─────────────────────────── the typed writer ───────────────────────────


class TestTypedWriter:
    def _ws(self):
        from openpyxl import Workbook

        return Workbook().active

    def test_text_is_text_even_when_it_starts_with_a_formula_trigger(self):
        from shared.excel_cells import put

        ws = self._ws()
        for i, s in enumerate(HOSTILE, start=1):
            cell = put(ws, i, 1, s)
            assert cell.data_type == "s"
            assert cell.value == s  # exact text, no visible apostrophe
            assert cell.quotePrefix  # Excel keeps it text if the cell is re-entered

    def test_numbers_stay_numeric(self):
        from shared.excel_cells import put

        ws = self._ws()
        for i, v in enumerate([Decimal("-123.45"), -123.45, -7], start=1):
            assert put(ws, i, 1, v).data_type == "n"

    def test_dates_are_dates(self):
        from shared.excel_cells import put

        assert put(self._ws(), 1, 1, date(2026, 11, 18)).is_date

    def test_unknown_types_are_refused(self):
        from shared.excel_cells import put

        with pytest.raises(TypeError):
            put(self._ws(), 1, 1, object())


# ─────────────────────────── the workpaper ───────────────────────────


class TestWorkpaper:
    def test_no_formula_from_any_text_input(self):
        from export.serializers.excel import serialize_audit_excel
        from shared.schemas import AuditResultInput

        xlsx = serialize_audit_excel(AuditResultInput(**_audit_payload()))
        _assert_no_formulas(xlsx)
        _assert_hostile_text_present(xlsx, HOSTILE)

    def test_negative_amounts_are_numeric_cells(self):
        from export.serializers.excel import serialize_audit_excel
        from shared.schemas import AuditResultInput

        xml = "".join(_sheets_xml(serialize_audit_excel(AuditResultInput(**_audit_payload()))).values())
        assert re.search(r'<c r="[A-Z]+\d+"[^>]*><v>-125\.5</v></c>', xml), "negative amount must be a number cell"

    @pytest.mark.parametrize("bad", ["=1+1", "18/11/2026", "2026-13-01", "tomorrow"])
    def test_workpaper_date_must_be_a_date(self, bad):
        from shared.schemas import AuditResultInput

        with pytest.raises(ValidationError):
            AuditResultInput(**_audit_payload(workpaper_date=bad))

    def test_workpaper_date_is_written_as_a_date(self):
        from openpyxl import load_workbook

        from export.serializers.excel import serialize_audit_excel
        from shared.schemas import AuditResultInput

        wb = load_workbook(io.BytesIO(serialize_audit_excel(AuditResultInput(**_audit_payload()))))
        dates = [c for ws in wb.worksheets for row in ws.iter_rows() for c in row if getattr(c, "is_date", False)]
        assert dates and all(c.value.date() == date(2026, 11, 18) for c in dates)

    def test_generator_refuses_a_non_date_string(self):
        from excel_generator import generate_workpaper

        with pytest.raises(ValueError):
            generate_workpaper(_audit_payload(), workpaper_date="=1+1", include_signoff=True)

    def test_nested_inputs_are_models(self):
        from shared.schemas import AuditResultInput

        model = AuditResultInput(**_audit_payload())
        assert type(model.abnormal_balances[0]).__name__ != "dict"
        assert type(model.all_accounts[0]).__name__ != "dict"
        with pytest.raises(ValidationError):
            AuditResultInput(**_audit_payload(abnormal_balances=[{"account": {"nested": "=1+1"}}]))

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_route(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            ok = await client.post("/export/excel", json=_audit_payload())
            bad = await client.post("/export/excel", json=_audit_payload(workpaper_date="=1+1"))
        assert ok.status_code == 200
        _assert_no_formulas(ok.content)
        assert bad.status_code in (400, 422)


# ─────────────────────────── lead sheets ───────────────────────────


def _leadsheet_payload() -> dict:
    return {
        "flux": {
            "items": [
                {
                    "account": t,
                    "type": t,
                    "current": -500.25,
                    "prior": 100.0,
                    "delta_amount": -600.25,
                    "delta_percent": -600.25,
                    "is_new": True,
                    "is_removed": False,
                    "sign_flip": True,
                    "risk_level": "high",
                    "variance_indicators": [t, "=SUM(1)"],
                }
                for t in HOSTILE
            ],
            "summary": {
                "total_items": len(HOSTILE),
                "high_risk_count": len(HOSTILE),
                "medium_risk_count": 0,
                "new_accounts": 0,
                "removed_accounts": 0,
                "threshold": 10.0,
            },
        },
        "recon": {
            "scores": [
                {"account": t, "score": 90, "band": "high", "factors": [t, "+factor"], "action": t} for t in HOSTILE
            ],
            "stats": {"high": len(HOSTILE), "medium": 0, "low": 0},
        },
        "filename": "=1+1",
    }


class TestLeadSheets:
    def test_no_formula_from_names_factors_or_notes(self):
        from export.serializers.excel import serialize_leadsheets_excel
        from shared.export_schemas import LeadSheetInput

        xlsx = serialize_leadsheets_excel(LeadSheetInput(**_leadsheet_payload()))
        _assert_no_formulas(xlsx)
        _assert_hostile_text_present(xlsx, HOSTILE)
        assert "<v>-500.25</v>" in "".join(_sheets_xml(xlsx).values())


# ─────────────────────────── financial statements ───────────────────────────


class TestFinancialStatements:
    def test_no_formula_from_entity_period_or_labels(self):
        from excel_generator import generate_financial_statements_excel
        from financial_statement_builder import FinancialStatementBuilder
        from shared.export_schemas import FinancialStatementsInput

        payload = FinancialStatementsInput(
            lead_sheet_grouping={
                "summaries": [
                    {
                        "lead_sheet": "A",
                        "name": "=1+1",
                        "net_balance": -250.75,
                        "accounts": [{"account": '=HYPERLINK("x")', "debit": 0, "credit": 250.75}],
                    },
                ]
            },
            entity_name="=1+1",
            period_end="+2026",
            workpaper_date="2026-11-18",
            include_signoff=True,
            prepared_by="-2+3",
        )
        statements = FinancialStatementBuilder(
            payload.lead_sheet_grouping.model_dump(exclude_unset=True),
            entity_name=payload.entity_name,
            period_end=payload.period_end,
        ).build()
        xlsx = generate_financial_statements_excel(
            statements,
            prepared_by=payload.prepared_by,
            workpaper_date=payload.workpaper_date,
            include_signoff=True,
        )
        _assert_no_formulas(xlsx)
        _assert_hostile_text_present(xlsx, ["=1+1", "+2026", "-2+3"])

    def test_nested_grouping_is_a_model(self):
        from shared.export_schemas import FinancialStatementsInput

        with pytest.raises(ValidationError):
            FinancialStatementsInput(lead_sheet_grouping={"summaries": [{"lead_sheet": {"x": 1}}]})
        with pytest.raises(ValidationError):
            FinancialStatementsInput(lead_sheet_grouping={"summaries": []}, workpaper_date="=1+1")


# ─────────────────────────── loan workbook ───────────────────────────


class TestLoanWorkbook:
    def test_no_formula_and_numbers_stay_numeric(self):
        from loan_amortization_engine import LoanConfig, generate_amortization_schedule
        from loan_amortization_excel import build_amortization_workbook

        cfg = LoanConfig(
            principal=Decimal("1200"), annual_rate=Decimal("0.05"), term_periods=12, start_date=date(2026, 1, 1)
        )
        xlsx = build_amortization_workbook(generate_amortization_schedule(cfg))
        _assert_no_formulas(xlsx)
        assert "<v>1200" in "".join(_sheets_xml(xlsx).values())


# ─────────────────────────── the guard ───────────────────────────


def test_generators_write_cells_only_through_the_typed_writer():
    """No Excel generator assigns a cell directly — a new column cannot forget the writer."""
    import ast
    from pathlib import Path

    root = Path(__file__).parent.parent
    offenders = []
    for rel in ("excel_generator.py", "leadsheet_generator.py", "loan_amortization_excel.py"):
        tree = ast.parse((root / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and "ws" in t.value.id:
                        offenders.append(f"{rel}:{node.lineno} ws[...] =")
                    if isinstance(t, ast.Attribute) and t.attr == "value":
                        offenders.append(f"{rel}:{node.lineno} .value =")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "cell" and (len(node.args) > 2 or any(k.arg == "value" for k in node.keywords)):
                    offenders.append(f"{rel}:{node.lineno} .cell(value=)")
                if node.func.attr == "append" and isinstance(node.func.value, ast.Name) and "ws" in node.func.value.id:
                    offenders.append(f"{rel}:{node.lineno} ws.append")
    assert offenders == []
