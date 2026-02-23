"""
Integration tests for PDF upload pipeline — format wiring + preview endpoint.
"""

import io

import pytest
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from shared.file_formats import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    FORMAT_PROFILES,
    FileFormat,
    FileValidationErrorCode,
    detect_format,
    get_active_extensions_display,
)


def _make_financial_pdf() -> bytes:
    """Generate a simple financial table PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)

    data = [
        ["Account", "Debit", "Credit", "Balance"],
        ["1000 Cash", "50,000.00", "10,000.00", "40,000.00"],
        ["2000 AP", "3,000.00", "18,000.00", "(15,000.00)"],
        ["3000 Equity", "0.00", "45,000.00", "(45,000.00)"],
    ]

    table = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )

    doc.build([table])
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────
# Format Profile Wiring
# ─────────────────────────────────────────────────────────────────────


class TestPdfFormatProfile:
    """Verify PDF is wired into the format registry."""

    def test_pdf_parse_supported(self):
        profile = FORMAT_PROFILES[FileFormat.PDF]
        assert profile.parse_supported is True

    def test_pdf_extension_in_allowed(self):
        assert ".pdf" in ALLOWED_EXTENSIONS

    def test_pdf_content_type_in_allowed(self):
        assert "application/pdf" in ALLOWED_CONTENT_TYPES

    def test_pdf_label(self):
        profile = FORMAT_PROFILES[FileFormat.PDF]
        assert profile.label == "PDF"

    def test_pdf_magic_bytes(self):
        profile = FORMAT_PROFILES[FileFormat.PDF]
        assert b"%PDF" in profile.magic_bytes

    def test_detect_format_by_extension(self):
        result = detect_format(filename="report.pdf")
        assert result.format == FileFormat.PDF
        assert result.confidence == "high"

    def test_detect_format_by_magic_bytes(self):
        pdf_bytes = _make_financial_pdf()
        result = detect_format(file_bytes=pdf_bytes)
        assert result.format == FileFormat.PDF

    def test_detect_format_by_content_type(self):
        result = detect_format(content_type="application/pdf")
        assert result.format == FileFormat.PDF

    def test_extensions_display_includes_pdf(self):
        display = get_active_extensions_display()
        assert "PDF" in display
        assert ".pdf" in display


class TestPdfErrorCodes:
    """Verify new error codes exist."""

    def test_extraction_quality_low_exists(self):
        assert FileValidationErrorCode.EXTRACTION_QUALITY_LOW == "extraction_quality_low"

    def test_table_detection_failed_exists(self):
        assert FileValidationErrorCode.TABLE_DETECTION_FAILED == "table_detection_failed"


# ─────────────────────────────────────────────────────────────────────
# Parse Dispatch
# ─────────────────────────────────────────────────────────────────────


class TestPdfParseDispatch:
    """Verify PDF dispatch branch in helpers.py."""

    def test_pdf_dispatch_exists(self):
        """Verify the PDF dispatch branch is wired in parse_uploaded_file_by_format."""
        from shared.helpers import parse_uploaded_file_by_format

        pdf_bytes = _make_financial_pdf()
        # Should succeed (or raise 422 for quality gate — both indicate dispatch works)
        try:
            columns, rows = parse_uploaded_file_by_format(pdf_bytes, "test.pdf")
            assert len(columns) > 0
            assert len(rows) > 0
        except Exception as e:
            # HTTPException 422 means dispatch worked but quality gate tripped
            if hasattr(e, "status_code"):
                assert e.status_code in (400, 422)
            else:
                raise

    def test_pdf_magic_byte_guard(self):
        """Verify .pdf extension with non-PDF content is rejected in validate_file_size."""
        from unittest.mock import AsyncMock, MagicMock

        from shared.helpers import validate_file_size

        fake_file = MagicMock()
        fake_file.filename = "test.pdf"
        fake_file.content_type = "application/pdf"
        fake_file.read = AsyncMock(side_effect=[b"PK\x03\x04not-a-pdf-content", b""])

        import asyncio

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(validate_file_size(fake_file))
        assert exc_info.value.status_code == 400
        assert "PDF" in str(exc_info.value.detail)


# ─────────────────────────────────────────────────────────────────────
# Preview Endpoint Schema
# ─────────────────────────────────────────────────────────────────────


class TestPdfPreviewResponseSchema:
    """Verify the PdfPreviewResponse Pydantic model is importable and valid."""

    def test_response_model_exists(self):
        from routes.audit import PdfPreviewResponse

        # Verify all fields
        fields = PdfPreviewResponse.model_fields
        assert "filename" in fields
        assert "page_count" in fields
        assert "tables_found" in fields
        assert "extraction_confidence" in fields
        assert "header_confidence" in fields
        assert "numeric_density" in fields
        assert "row_consistency" in fields
        assert "column_names" in fields
        assert "sample_rows" in fields
        assert "remediation_hints" in fields
        assert "passes_quality_gate" in fields

    def test_response_model_validation(self):
        from routes.audit import PdfPreviewResponse

        data = PdfPreviewResponse(
            filename="test.pdf",
            page_count=1,
            tables_found=1,
            extraction_confidence=0.85,
            header_confidence=0.9,
            numeric_density=0.7,
            row_consistency=0.95,
            column_names=["A", "B"],
            sample_rows=[{"A": "1", "B": "2"}],
            remediation_hints=[],
            passes_quality_gate=True,
        )
        assert data.passes_quality_gate is True
        assert data.extraction_confidence == 0.85
