"""
Sprint 96.5: Tests for shared export helper functions.
Validates StreamingResponse builders produce correct headers and content.
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.export_helpers import (
    streaming_pdf_response,
    streaming_excel_response,
    streaming_csv_response,
    MEDIA_PDF,
    MEDIA_EXCEL,
    MEDIA_CSV,
)


def _collect_body(resp) -> bytes:
    """Synchronously collect all bytes from a StreamingResponse body_iterator."""
    async def _read():
        chunks = []
        async for chunk in resp.body_iterator:
            chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode())
        return b"".join(chunks)
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_read())
    finally:
        loop.close()


class TestStreamingPdfResponse:
    """Tests for streaming_pdf_response."""

    def test_media_type(self):
        resp = streaming_pdf_response(b"%PDF-fake", "report.pdf")
        assert resp.media_type == MEDIA_PDF

    def test_content_disposition(self):
        resp = streaming_pdf_response(b"%PDF-fake", "audit_report.pdf")
        assert resp.headers["content-disposition"] == 'attachment; filename="audit_report.pdf"'

    def test_content_length(self):
        data = b"x" * 100
        resp = streaming_pdf_response(data, "test.pdf")
        assert resp.headers["content-length"] == "100"

    def test_streaming_chunks(self):
        data = b"x" * 20000
        resp = streaming_pdf_response(data, "big.pdf", chunk_size=8192)
        body = _collect_body(resp)
        assert body == data
        assert len(data) == 20000

    def test_small_file_single_chunk(self):
        data = b"small"
        resp = streaming_pdf_response(data, "small.pdf")
        body = _collect_body(resp)
        assert body == data


class TestStreamingExcelResponse:
    """Tests for streaming_excel_response."""

    def test_media_type(self):
        resp = streaming_excel_response(b"PK-fake-xlsx", "workbook.xlsx")
        assert resp.media_type == MEDIA_EXCEL

    def test_content_disposition(self):
        resp = streaming_excel_response(b"PK-fake", "workpaper.xlsx")
        assert resp.headers["content-disposition"] == 'attachment; filename="workpaper.xlsx"'

    def test_content_length(self):
        data = b"x" * 50
        resp = streaming_excel_response(data, "test.xlsx")
        assert resp.headers["content-length"] == "50"

    def test_body_readable(self):
        data = b"excel-content"
        resp = streaming_excel_response(data, "test.xlsx")
        body = _collect_body(resp)
        assert body == data


class TestStreamingCsvResponse:
    """Tests for streaming_csv_response."""

    def test_media_type(self):
        resp = streaming_csv_response(b"col1,col2\n", "data.csv")
        assert resp.media_type == MEDIA_CSV

    def test_content_disposition(self):
        resp = streaming_csv_response(b"data", "export.csv")
        assert resp.headers["content-disposition"] == 'attachment; filename="export.csv"'

    def test_content_length(self):
        data = b"a,b,c\n1,2,3\n"
        resp = streaming_csv_response(data, "test.csv")
        assert resp.headers["content-length"] == str(len(data))

    def test_body_content(self):
        data = b"header\nrow1\nrow2\n"
        resp = streaming_csv_response(data, "test.csv")
        body = _collect_body(resp)
        assert body == data


class TestMediaTypeConstants:
    """Verify media type constants are correct."""

    def test_pdf_type(self):
        assert MEDIA_PDF == "application/pdf"

    def test_excel_type(self):
        assert MEDIA_EXCEL == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_csv_type(self):
        assert MEDIA_CSV == "text/csv; charset=utf-8"
