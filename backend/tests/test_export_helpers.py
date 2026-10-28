"""
Sprint 96.5: Tests for shared export helper functions.
Validates the download-response builders produce correct headers and content.

Sprint 819 item 7: ``attachment_response`` is the one place every
file-download endpoint builds its response; the body is sent as a single chunk
(the PDF builder no longer streams 8 KB chunks).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.export_helpers import (
    MEDIA_CSV,
    MEDIA_EXCEL,
    MEDIA_PDF,
    MEDIA_ZIP,
    attachment_response,
    csv_response,
    excel_response,
    pdf_response,
)


def _collect_body(resp: object) -> bytes:
    """Collect all bytes from a StreamingResponse body_iterator."""

    async def _read() -> list[bytes]:
        return [c if isinstance(c, bytes) else c.encode() async for c in resp.body_iterator]  # type: ignore[attr-defined]

    return b"".join(asyncio.run(_read()))


def _chunks(resp: object) -> int:
    async def _read() -> int:
        return len([c async for c in resp.body_iterator])  # type: ignore[attr-defined]

    return asyncio.run(_read())


class TestPdfResponse:
    """Tests for pdf_response."""

    def test_media_type(self):
        resp = pdf_response(b"%PDF-fake", "report.pdf")
        assert resp.media_type == MEDIA_PDF

    def test_content_disposition(self):
        resp = pdf_response(b"%PDF-fake", "audit_report.pdf")
        assert resp.headers["content-disposition"] == 'attachment; filename="audit_report.pdf"'

    def test_content_length(self):
        data = b"x" * 100
        resp = pdf_response(data, "test.pdf")
        assert resp.headers["content-length"] == "100"

    def test_large_body_intact(self):
        data = b"x" * 20000
        assert _collect_body(pdf_response(data, "big.pdf")) == data

    def test_sent_as_one_chunk(self):
        assert _chunks(pdf_response(b"x" * 20000, "big.pdf")) == 1

    def test_small_file(self):
        assert _collect_body(pdf_response(b"small", "small.pdf")) == b"small"


class TestExcelResponse:
    """Tests for excel_response."""

    def test_media_type(self):
        resp = excel_response(b"PK-fake-xlsx", "workbook.xlsx")
        assert resp.media_type == MEDIA_EXCEL

    def test_content_disposition(self):
        resp = excel_response(b"PK-fake", "workpaper.xlsx")
        assert resp.headers["content-disposition"] == 'attachment; filename="workpaper.xlsx"'

    def test_content_length(self):
        resp = excel_response(b"x" * 50, "test.xlsx")
        assert resp.headers["content-length"] == "50"

    def test_body_readable(self):
        resp = excel_response(b"excel-content", "test.xlsx")
        assert _collect_body(resp) == b"excel-content"


class TestCsvResponse:
    """Tests for csv_response."""

    def test_media_type(self):
        resp = csv_response(b"col1,col2\n", "data.csv")
        assert resp.media_type == MEDIA_CSV
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"

    def test_content_disposition(self):
        resp = csv_response(b"data", "export.csv")
        assert resp.headers["content-disposition"] == 'attachment; filename="export.csv"'

    def test_content_length(self):
        data = b"a,b,c\n1,2,3\n"
        resp = csv_response(data, "test.csv")
        assert resp.headers["content-length"] == str(len(data))

    def test_body_content(self):
        data = b"header\nrow1\nrow2\n"
        assert _collect_body(csv_response(data, "test.csv")) == data


class TestAttachmentResponse:
    def test_str_body_is_utf8_without_bom(self):
        resp = attachment_response("café,1\n", "x.csv", MEDIA_CSV)
        assert _collect_body(resp) == "café,1\n".encode()
        assert resp.headers["content-length"] == str(len("café,1\n".encode()))

    def test_unquoted_filename_form_kept_for_legacy_endpoints(self):
        resp = attachment_response("a\n", "sod_analysis.csv", MEDIA_CSV, quote_filename=False)
        assert resp.headers["content-disposition"] == "attachment; filename=sod_analysis.csv"

    def test_bare_text_csv_gets_charset(self):
        # What the hand-rolled endpoints sent: "text/csv", which Starlette completed.
        resp = attachment_response("a\n", "x.csv", "text/csv")
        assert resp.headers["content-type"] == MEDIA_CSV

    def test_zip(self):
        resp = attachment_response(b"PK\x03\x04", "pkg.zip", MEDIA_ZIP)
        assert resp.headers["content-type"] == "application/zip"
        assert resp.headers["content-disposition"] == 'attachment; filename="pkg.zip"'


class TestMediaTypeConstants:
    """Verify media type constants are correct."""

    def test_pdf_type(self):
        assert MEDIA_PDF == "application/pdf"

    def test_excel_type(self):
        assert MEDIA_EXCEL == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_csv_type(self):
        assert MEDIA_CSV == "text/csv; charset=utf-8"

    def test_zip_type(self):
        assert MEDIA_ZIP == "application/zip"
