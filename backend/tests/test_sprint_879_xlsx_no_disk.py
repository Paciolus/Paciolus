"""Sprint 879e (review DH-06): XLSX exports write nothing to disk.

openpyxl 3.1.5 writes each worksheet's XML through
``NamedTemporaryFile(prefix='openpyxl.', delete=False)`` before zipping it,
even when the workbook is saved into a ``BytesIO``. The file is removed only
on success, or at interpreter exit — never in a killed worker. A failure
mid-export leaves account names and amounts on disk.

A Python audit hook records every file opened for writing while an export
runs. Every XLSX generator runs with marker account names and amounts; then
failures are forced inside worksheet writing and inside packaging. No file
may be created, and no marker may reach any file.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import pytest

M_NAME = "MKRXLSXACCT"
M_AMOUNT = 987654.32

_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
_state = threading.local()


def _hook(event: str, args: tuple[Any, ...]) -> None:
    rec = getattr(_state, "opened", None)
    if rec is None:
        return
    if event == "open":
        path, mode, flags = (args + (None, None, None))[:3]
        writes = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & _WRITE_FLAGS
        )
        if writes and isinstance(path, (str, bytes, os.PathLike)):
            rec.append(os.fsdecode(path))
    elif event in ("os.mkdir", "tempfile.mkstemp", "tempfile.mkdtemp"):
        rec.append(f"{event}:{args[0] if args else ''}")


sys.addaudithook(_hook)

# Import every generator before any watch starts, so Python's own bytecode-cache
# writes (__pycache__/*.pyc) happen here, not inside an export.
for _mod in (
    "excel_generator",
    "financial_statement_builder",
    "flux_engine",
    "leadsheet_generator",
    "loan_amortization_engine",
    "loan_amortization_excel",
    "recon_engine",
    "shared.xlsx_in_memory",
    "openpyxl.reader.excel",
):
    __import__(_mod)


@contextmanager
def _watch_disk(tmp_path) -> Iterator[list[str]]:  # noqa: ANN001
    """Record write-opens on this thread; point tempfile at an empty dir to scan."""
    opened: list[str] = []
    tdir = tmp_path / "tmp"
    tdir.mkdir()
    with patch.object(tempfile, "tempdir", str(tdir)):
        _state.opened = opened
        try:
            yield opened
        finally:
            _state.opened = None
    leftovers = list(tdir.iterdir())
    for p in leftovers:  # read before the assertion so a failure can show content
        opened.append(f"LEFT BEHIND:{p.name}:{M_NAME in p.read_text(errors='ignore')}")


# --- inputs carrying the markers ----------------------------------------------


def _workpaper() -> bytes:
    from excel_generator import generate_workpaper

    result = {
        "status": "success",
        "balanced": False,
        "total_debits": M_AMOUNT,
        "total_credits": 1000.0,
        "difference": M_AMOUNT - 1000.0,
        "row_count": 2,
        "message": "Out of balance",
        "abnormal_balances": [
            {
                "account": f"Cash {M_NAME}",
                "type": "Asset",
                "issue": "Credit balance on asset",
                "amount": M_AMOUNT,
                "materiality": "material",
                "debit": 0.0,
                "credit": M_AMOUNT,
                "category": "asset",
                "confidence": 0.9,
                "matched_keywords": ["cash"],
                "requires_review": True,
                "anomaly_type": "natural_balance_violation",
                "severity": "high",
                "suggestions": [],
            }
        ],
        "has_risk_alerts": True,
        "materiality_threshold": 500.0,
        "material_count": 1,
        "immaterial_count": 0,
    }
    return generate_workpaper(result, "tb.xlsx")


def _financial_statements() -> bytes:
    from excel_generator import generate_financial_statements_excel
    from financial_statement_builder import FinancialStatementBuilder

    def sheet(ref: str, name: str, cat: str, net: float) -> dict[str, Any]:
        return {
            "lead_sheet": ref,
            "name": name,
            "category": cat,
            "total_debit": max(net, 0.0),
            "total_credit": max(-net, 0.0),
            "net_balance": net,
            "account_count": 1,
            "accounts": [],
        }

    grouping = {
        "summaries": [
            sheet("A", f"Cash {M_NAME}", "Current Assets", M_AMOUNT),
            sheet("K", "Equity", "Equity", -M_AMOUNT),
        ],
        "total_debits": M_AMOUNT,
        "total_credits": M_AMOUNT,
    }
    return generate_financial_statements_excel(FinancialStatementBuilder(grouping).build())


def _leadsheets() -> bytes:
    from flux_engine import FluxItem, FluxResult
    from leadsheet_generator import generate_leadsheets
    from recon_engine import ReconEngine

    item = FluxItem(
        account_name=f"Cash {M_NAME}",
        account_type="Asset",
        current_balance=M_AMOUNT,
        prior_balance=1000.0,
        delta_amount=M_AMOUNT - 1000.0,
        delta_percent=50.0,
        is_new_account=False,
        is_removed_account=False,
        has_sign_flip=False,
    )
    flux = FluxResult([item], 1, 0, 0, 0, 0, 1000.0)
    return generate_leadsheets(flux, ReconEngine(materiality_threshold=1000.0).calculate_scores(flux), "tb.xlsx")


def _amortization() -> bytes:
    from datetime import date
    from decimal import Decimal

    from loan_amortization_engine import LoanConfig, generate_amortization_schedule
    from loan_amortization_excel import build_amortization_workbook

    cfg = LoanConfig(
        principal=Decimal(str(M_AMOUNT)),
        annual_rate=Decimal("0.06"),
        term_periods=12,
        frequency="monthly",
        start_date=date(2026, 1, 1),
    )
    return build_amortization_workbook(generate_amortization_schedule(cfg))


EXPORTS: dict[str, Callable[[], bytes]] = {
    "workpaper": _workpaper,
    "financial_statements": _financial_statements,
    "leadsheets": _leadsheets,
    "loan_amortization": _amortization,
}


@pytest.mark.parametrize("name", sorted(EXPORTS))
def test_export_writes_nothing_to_disk(name, tmp_path):  # noqa: ANN001
    with _watch_disk(tmp_path) as opened:
        data = EXPORTS[name]()
    assert data[:2] == b"PK"
    assert opened == [], f"{name} touched disk: {opened}"
    # The markers really are in the workbook (so the check above means something).
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(data))
    cells = " ".join(str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None)
    assert M_NAME in cells or "987654" in cells.replace(",", "")


@pytest.mark.parametrize("name", sorted(EXPORTS))
@pytest.mark.parametrize("stage", ["worksheet", "packaging"])
def test_a_failed_export_leaves_nothing_behind(name, stage, tmp_path):  # noqa: ANN001
    import openpyxl.worksheet._writer as ws_writer
    import openpyxl.writer.excel as excel_writer

    boom = RuntimeError(f"forced failure during {stage}")
    if stage == "worksheet":
        # Fail after the worksheet's XML (with the markers) has been written.
        target, attr = ws_writer.WorksheetWriter, "write_tail"
    else:
        # Fail while the zip is being assembled, right after every sheet was written.
        target, attr = excel_writer.ExcelWriter, "_write_chartsheets"
    original = getattr(target, attr)

    def failing(self, *a, **kw):  # noqa: ANN001, ANN002, ANN003, ANN202
        if stage == "worksheet":
            original(self, *a, **kw)
        raise boom

    with _watch_disk(tmp_path) as opened, patch.object(target, attr, failing):
        with pytest.raises(RuntimeError, match="forced failure"):
            EXPORTS[name]()
    assert opened == [], f"{name} ({stage} failure) touched disk: {opened}"


# --- the guard and the bypass scan --------------------------------------------


def test_the_guard_refuses_openpyxl_temp_files_in_production(monkeypatch):
    """Outside the test session's fixture exemption, any bypassing save raises."""
    import openpyxl.worksheet._writer as ws_writer
    from openpyxl import Workbook

    import shared.xlsx_in_memory as xim

    monkeypatch.setattr(ws_writer, "create_temporary_file", xim._forbid_openpyxl_tempfiles)
    wb = Workbook()
    wb.active.append([f"Cash {M_NAME}", M_AMOUNT])
    with pytest.raises(xim.InMemoryWorksheetError):
        wb.save(io.BytesIO())
    assert xim.workbook_to_bytes(wb)[:2] == b"PK"  # the helper does not need temp files


def test_the_override_matches_the_pinned_openpyxl():
    """The override mirrors ExcelWriter.write_worksheet in this exact version."""
    import shared.xlsx_in_memory as xim

    assert xim.openpyxl_version_is_verified(), (
        "openpyxl changed — re-check shared/xlsx_in_memory._InMemoryExcelWriter against "
        "openpyxl.writer.excel.ExcelWriter.write_worksheet, then update VERIFIED_OPENPYXL_VERSION"
    )


def test_no_production_code_saves_a_workbook_another_way():
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    offenders = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(("venv/", "tests/", "migrations/", "scripts/")) or rel == "shared/xlsx_in_memory.py":
            continue
        if "/site-packages/" in rel:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                name = node.func.attr
                target = ast.unparse(node.func.value)
                if name == "to_excel" or name == "save_workbook" or (name == "save" and "wb" in target.lower()):
                    offenders.append(f"{rel}:{node.lineno} {target}.{name}()")
    assert not offenders, f"serialize workbooks with shared.xlsx_in_memory.workbook_to_bytes: {offenders}"


def test_dataframe_to_bytes_excel_writes_nothing_to_disk(tmp_path):
    import pandas as pd
    from openpyxl import load_workbook

    from security_utils import dataframe_to_bytes

    df = pd.DataFrame({"Account": [f"Cash {M_NAME}"], "Amount": [M_AMOUNT]})
    with _watch_disk(tmp_path) as opened:
        data = dataframe_to_bytes(df, "excel")
    assert opened == []
    ws = load_workbook(io.BytesIO(data)).active
    assert [c.value for c in ws[1]] == ["Account", "Amount"]
    assert ws["A2"].value == f"Cash {M_NAME}"
