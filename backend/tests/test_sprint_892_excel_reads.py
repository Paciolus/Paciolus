"""Sprint 892 (CEO brief 17A, review ST-15): Excel files are opened once; behaviour unchanged.

The XLSX pre-parse row check opened the workbook a second time just to read its recorded
dimensions. It now runs on the parser's own open, with the same log event and the same message.
"""

import io

import pytest
from fastapi import HTTPException
from openpyxl import Workbook

from shared.upload_pipeline import parse_uploaded_file_by_format


def _sized_workbook(rows: int) -> bytes:
    wb = Workbook()  # a normal workbook records its dimensions
    ws = wb.active
    ws.append(["Account Name", "Debit", "Credit"])
    for i in range(rows):
        ws.append([f"Account {i}", 100, 0])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_sized_workbook_over_the_limit_is_refused_before_parsing_with_the_same_message():
    with pytest.raises(HTTPException) as exc:
        parse_uploaded_file_by_format(_sized_workbook(30), "tb.xlsx", max_rows=10)
    assert exc.value.status_code == 400
    assert exc.value.detail == (
        "File appears to exceed the maximum row limit of 10 rows (estimated 31 rows). Please reduce the file size."
    )


def test_workbook_within_the_limit_parses():
    columns, rows = parse_uploaded_file_by_format(_sized_workbook(5), "tb.xlsx", max_rows=10)
    assert list(columns) == ["Account Name", "Debit", "Credit"]
    assert len(rows) == 5
