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


def test_multi_sheet_reader_yields_the_same_frames_as_reading_each_sheet():
    import pandas as pd

    from security_utils import read_excel_multi_sheet_chunked

    wb = Workbook()
    ws = wb.active
    ws.title = "A"
    ws.append(["Account Number", "Debit"])
    for i in range(7):
        ws.append([f"{i:05d}", i * 1.5])
    ws2 = wb.create_sheet("B")
    ws2.append(["Account Number", "Credit"])
    for i in range(4):
        ws2.append([f"{i:05d}", i * 2.25])
    buf = io.BytesIO()
    wb.save(buf)
    data = buf.getvalue()

    got = list(read_excel_multi_sheet_chunked(data, ["A", "B"], chunk_size=3, dtype=str))
    assert [(len(c), n, s) for c, n, s in got] == [(3, 3, "A"), (3, 6, "A"), (1, 7, "A"), (3, 3, "B"), (1, 4, "B")]
    for sheet in ("A", "B"):
        expected = pd.read_excel(io.BytesIO(data), sheet_name=sheet, dtype=str)
        combined = pd.concat([c for c, _, s in got if s == sheet])
        pd.testing.assert_frame_equal(combined, expected)
    assert got[0][0]["Account Number"].iloc[0] == "00000"  # leading zeros kept


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("name", "content_type", "body"),
    [
        ("tb.exe", "application/octet-stream", b"MZ"),
        ("tb.csv", "text/csv", b""),
        ("tb.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"not a zip"),
        ("tb.csv", "text/csv", b"Account,Debit,Credit\nCash,1,0\n"),
    ],
)
async def test_bytes_variant_answers_exactly_like_the_reading_validator(name, content_type, body):
    """Step 3: the TB route validates the bytes it read for hashing instead of reading again."""
    from starlette.datastructures import Headers, UploadFile

    from shared.upload_pipeline import validate_file_size, validate_upload_contents

    def upload():
        return UploadFile(io.BytesIO(body), filename=name, headers=Headers({"content-type": content_type}))

    async def outcome(fn):
        try:
            return ("ok", await fn())
        except HTTPException as e:
            return (e.status_code, e.detail)

    reading = await outcome(lambda: validate_file_size(upload()))
    given = await outcome(lambda: validate_upload_contents(upload(), body))
    assert reading == given
