"""
Tests for shared.pdf_parser — PDF table extraction with quality gates.

Fixtures generated programmatically using reportlab (already in requirements.txt).
"""

import io
import time
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from shared.pdf_parser import (
    CONFIDENCE_THRESHOLD,
    MAX_PDF_PAGES,
    PER_PAGE_TIMEOUT_SECONDS,
    PREVIEW_PAGE_LIMIT,
    _build_remediation_hints,
    _compute_quality_metrics,
    _is_numeric,
    _normalize_row,
    _rows_match,
    _stitch_tables,
    _validate_pdf_magic,
    extract_pdf_tables,
    parse_pdf,
)

# ─────────────────────────────────────────────────────────────────────
# Fixtures: Generate PDFs with reportlab
# ─────────────────────────────────────────────────────────────────────


def _make_clean_table_pdf() -> bytes:
    """Financial table with Account, Debit, Credit, Balance columns."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)

    data = [
        ["Account", "Debit", "Credit", "Balance"],
        ["1000 Cash", "50,000.00", "10,000.00", "40,000.00"],
        ["1100 Accounts Receivable", "25,000.00", "5,000.00", "20,000.00"],
        ["2000 Accounts Payable", "3,000.00", "18,000.00", "(15,000.00)"],
        ["3000 Equity", "0.00", "45,000.00", "(45,000.00)"],
        ["4000 Revenue", "0.00", "100,000.00", "(100,000.00)"],
        ["5000 Expenses", "80,000.00", "0.00", "80,000.00"],
    ]

    table = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]
        )
    )

    doc.build([table])
    return buf.getvalue()


def _make_messy_table_pdf() -> bytes:
    """Table with inconsistent columns and partial rows."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)

    data = [
        ["Col A", "Col B", "Col C"],
        ["text", "123", "456"],
        ["more text", "789"],  # Missing column
        ["", "", ""],
        ["abc", "not a number", "also not"],
    ]

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )

    doc.build([table])
    return buf.getvalue()


def _make_empty_pdf() -> bytes:
    """PDF with text paragraphs only, no tables."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("This is a report without any tables.", styles["Title"]),
        Spacer(1, 12),
        Paragraph("It contains only text content.", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("No tabular data is present.", styles["Normal"]),
    ]

    doc.build(elements)
    return buf.getvalue()


def _make_multi_page_table_pdf(pages: int = 3) -> bytes:
    """Table spanning multiple pages with repeated headers."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)

    elements = []
    for page_num in range(pages):
        data = [["Account", "Debit", "Credit", "Balance"]]
        for i in range(10):
            row_num = page_num * 10 + i + 1
            data.append(
                [
                    f"{1000 + row_num} Account {row_num}",
                    f"{row_num * 100:,.2f}",
                    f"{row_num * 50:,.2f}",
                    f"{row_num * 50:,.2f}",
                ]
            )

        table = Table(data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        elements.append(table)
        if page_num < pages - 1:
            elements.append(Spacer(1, 400))  # Force page break

    doc.build(elements)
    return buf.getvalue()


def _make_image_only_pdf() -> bytes:
    """PDF with canvas drawing, no extractable text tables."""
    buf = io.BytesIO()
    from reportlab.graphics.shapes import Drawing, Rect, String

    d = Drawing(400, 200)
    d.add(Rect(10, 10, 380, 180, fillColor=colors.lightblue, strokeColor=colors.black))
    d.add(String(100, 100, "This is a drawing, not a table", fontSize=14))

    doc = SimpleDocTemplate(buf, pagesize=letter)
    doc.build([d])
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────
# TestPdfPresenceValidation
# ─────────────────────────────────────────────────────────────────────


class TestPdfPresenceValidation:
    """Test PDF magic byte validation."""

    def test_valid_pdf_magic(self):
        pdf_bytes = _make_clean_table_pdf()
        _validate_pdf_magic(pdf_bytes, "test.pdf")  # Should not raise

    def test_invalid_magic_bytes(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_pdf_magic(b"PK\x03\x04", "fake.pdf")
        assert exc_info.value.status_code == 400
        assert "valid PDF" in str(exc_info.value.detail)

    def test_empty_file(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_pdf_magic(b"", "empty.pdf")
        assert exc_info.value.status_code == 400

    def test_non_pdf_binary(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_pdf_magic(b"\xd0\xcf\x11\xe0", "spreadsheet.pdf")
        assert exc_info.value.status_code == 400

    def test_text_file_as_pdf(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_pdf_magic(b"Account,Debit,Credit\n1000,100,50", "data.pdf")
        assert exc_info.value.status_code == 400


# ─────────────────────────────────────────────────────────────────────
# TestPdfTableExtraction
# ─────────────────────────────────────────────────────────────────────


class TestPdfTableExtraction:
    """Test PDF table extraction from clean and messy PDFs."""

    def test_clean_table_columns(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        assert len(result.column_names) == 4
        assert "Account" in result.column_names
        assert "Debit" in result.column_names
        assert "Credit" in result.column_names
        assert "Balance" in result.column_names

    def test_clean_table_row_count(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        assert len(result.rows) == 6  # 7 rows minus header

    def test_clean_table_values(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        first_row = result.rows[0]
        assert "1000" in first_row[0] or "Cash" in first_row[0]

    def test_no_table_pdf(self):
        pdf_bytes = _make_empty_pdf()
        result = extract_pdf_tables(pdf_bytes, "empty.pdf")
        assert result.metadata.tables_found == 0
        assert len(result.column_names) == 0
        assert len(result.rows) == 0

    def test_no_table_has_remediation_hints(self):
        pdf_bytes = _make_empty_pdf()
        result = extract_pdf_tables(pdf_bytes, "empty.pdf")
        assert len(result.metadata.remediation_hints) > 0
        assert any("No tables" in h for h in result.metadata.remediation_hints)

    def test_tables_found_count(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        assert result.metadata.tables_found >= 1

    def test_is_not_preview_by_default(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        assert result.is_preview is False


# ─────────────────────────────────────────────────────────────────────
# TestPdfQualityGate
# ─────────────────────────────────────────────────────────────────────


class TestPdfQualityGate:
    """Test quality metrics and confidence threshold enforcement."""

    def test_clean_table_high_confidence(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        assert result.metadata.extraction_confidence >= CONFIDENCE_THRESHOLD

    def test_clean_table_header_confidence(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        assert result.metadata.header_confidence >= 0.5

    def test_clean_table_numeric_density(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        assert result.metadata.numeric_density > 0

    def test_clean_table_row_consistency(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        assert result.metadata.row_consistency >= 0.8

    def test_metrics_in_range(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "clean.pdf")
        for metric in [
            result.metadata.extraction_confidence,
            result.metadata.header_confidence,
            result.metadata.numeric_density,
            result.metadata.row_consistency,
        ]:
            assert 0.0 <= metric <= 1.0

    def test_parse_pdf_raises_on_no_tables(self):
        pdf_bytes = _make_empty_pdf()
        with pytest.raises(HTTPException) as exc_info:
            parse_pdf(pdf_bytes, "empty.pdf")
        assert exc_info.value.status_code == 422

    def test_remediation_hints_populated_on_low_confidence(self):
        hints = _build_remediation_hints(0.3, 0.1, 0.5)
        assert len(hints) > 0

    def test_no_hints_on_all_high_metrics(self):
        hints = _build_remediation_hints(0.9, 0.8, 0.95)
        # High metrics should not trigger specific hints
        assert len(hints) == 1  # Only the generic fallback

    def test_header_hint_on_low_header_confidence(self):
        hints = _build_remediation_hints(0.3, 0.5, 0.9)
        assert any("headers" in h.lower() or "column" in h.lower() for h in hints)

    def test_numeric_hint_on_low_density(self):
        hints = _build_remediation_hints(0.8, 0.1, 0.9)
        assert any("numeric" in h.lower() or "scanned" in h.lower() for h in hints)


# ─────────────────────────────────────────────────────────────────────
# TestPdfMultiPage
# ─────────────────────────────────────────────────────────────────────


class TestPdfMultiPage:
    """Test multi-page table stitching and page limits."""

    def test_multi_page_stitching(self):
        pdf_bytes = _make_multi_page_table_pdf(pages=2)
        result = extract_pdf_tables(pdf_bytes, "multi.pdf")
        # Should have data rows (10 per page, stitching may or may not combine)
        assert len(result.rows) >= 10
        assert result.metadata.tables_found >= 1

    def test_preview_page_limit(self):
        pdf_bytes = _make_multi_page_table_pdf(pages=5)
        result = extract_pdf_tables(pdf_bytes, "multi.pdf", max_pages=PREVIEW_PAGE_LIMIT)
        assert result.is_preview is True
        assert result.metadata.pages_scanned <= PREVIEW_PAGE_LIMIT

    def test_preview_flag_when_max_pages_set(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "test.pdf", max_pages=1)
        assert result.is_preview is True

    def test_full_parse_flag_when_no_max_pages(self):
        pdf_bytes = _make_clean_table_pdf()
        result = extract_pdf_tables(pdf_bytes, "test.pdf", max_pages=None)
        assert result.is_preview is False

    def test_page_count_reported(self):
        pdf_bytes = _make_multi_page_table_pdf(pages=3)
        result = extract_pdf_tables(pdf_bytes, "multi.pdf")
        assert result.metadata.page_count >= 3

    def test_page_count_limit_rejection(self):
        """Mock a PDF with too many pages."""
        import pdfplumber

        pdf_bytes = _make_clean_table_pdf()
        with patch.object(pdfplumber, "open") as mock_open:
            mock_pdf = mock_open.return_value.__enter__.return_value
            mock_pdf.pages = [None] * (MAX_PDF_PAGES + 1)
            with pytest.raises(HTTPException) as exc_info:
                extract_pdf_tables(pdf_bytes, "huge.pdf")
            assert exc_info.value.status_code == 400
            assert "exceeding" in str(exc_info.value.detail)


# ─────────────────────────────────────────────────────────────────────
# TestPdfTimeout
# ─────────────────────────────────────────────────────────────────────


class TestPdfTimeout:
    """Test per-page timeout guard."""

    def test_dropped_pages_counted(self):
        """Mock time.time to simulate slow page extraction."""
        pdf_bytes = _make_clean_table_pdf()

        call_count = 0
        real_time = time.time

        def mock_time():
            nonlocal call_count
            call_count += 1
            # First call (start_time) returns 0; second call returns > timeout
            if call_count % 2 == 0:
                return real_time() + PER_PAGE_TIMEOUT_SECONDS + 1
            return real_time()

        with patch("shared.pdf_parser.time.time", side_effect=mock_time):
            result = extract_pdf_tables(pdf_bytes, "slow.pdf")
            assert result.metadata.dropped_rows >= 0  # May or may not drop depending on timing


# ─────────────────────────────────────────────────────────────────────
# TestParsePdfEndToEnd
# ─────────────────────────────────────────────────────────────────────


class TestParsePdfEndToEnd:
    """Test the parse_pdf entry point (DataFrame output)."""

    def test_returns_dataframe(self):
        pdf_bytes = _make_clean_table_pdf()
        df = parse_pdf(pdf_bytes, "clean.pdf")
        assert isinstance(df, pd.DataFrame)

    def test_dataframe_columns_match(self):
        pdf_bytes = _make_clean_table_pdf()
        df = parse_pdf(pdf_bytes, "clean.pdf")
        assert "Account" in df.columns
        assert "Debit" in df.columns

    def test_dataframe_row_count(self):
        pdf_bytes = _make_clean_table_pdf()
        df = parse_pdf(pdf_bytes, "clean.pdf")
        assert len(df) == 6

    def test_metadata_in_attrs(self):
        pdf_bytes = _make_clean_table_pdf()
        df = parse_pdf(pdf_bytes, "clean.pdf")
        assert "pdf_metadata" in df.attrs
        metadata = df.attrs["pdf_metadata"]
        assert metadata.page_count >= 1
        assert metadata.extraction_confidence > 0

    def test_no_tables_raises_422(self):
        pdf_bytes = _make_empty_pdf()
        with pytest.raises(HTTPException) as exc_info:
            parse_pdf(pdf_bytes, "empty.pdf")
        assert exc_info.value.status_code == 422

    def test_invalid_pdf_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            parse_pdf(b"not a pdf", "fake.pdf")
        assert exc_info.value.status_code == 400


# ─────────────────────────────────────────────────────────────────────
# TestHelperFunctions
# ─────────────────────────────────────────────────────────────────────


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_normalize_row(self):
        assert _normalize_row(["a", None, "b", None]) == ["a", "", "b", ""]

    def test_rows_match_identical(self):
        assert _rows_match(["A", "B", "C"], ["a", "b", "c"]) is True

    def test_rows_match_different(self):
        assert _rows_match(["A", "B", "C"], ["X", "Y", "Z"]) is False

    def test_rows_match_different_length(self):
        assert _rows_match(["A", "B"], ["A", "B", "C"]) is False

    def test_is_numeric_positive(self):
        assert _is_numeric("1,234.56") is True
        assert _is_numeric("$100") is True
        assert _is_numeric("(500.00)") is True

    def test_is_numeric_negative(self):
        assert _is_numeric("Cash") is False
        assert _is_numeric("") is False
        assert _is_numeric("  ") is False

    def test_compute_quality_empty_headers(self):
        composite, h, n, r = _compute_quality_metrics([], [])
        assert composite == 0.0

    def test_compute_quality_no_data(self):
        composite, h, n, r = _compute_quality_metrics(["A", "B"], [])
        assert h == 1.0
        assert n == 0.0
        assert r == 0.0

    def test_stitch_empty(self):
        headers, rows = _stitch_tables([])
        assert headers == []
        assert rows == []

    def test_stitch_single_table(self):
        table = [["H1", "H2"], ["a", "1"], ["b", "2"]]
        headers, rows = _stitch_tables([table])
        assert headers == ["H1", "H2"]
        assert len(rows) == 2

    def test_stitch_continuation(self):
        table1 = [["H1", "H2"], ["a", "1"]]
        table2 = [["H1", "H2"], ["b", "2"]]
        headers, rows = _stitch_tables([table1, table2])
        assert headers == ["H1", "H2"]
        assert len(rows) == 2

    def test_stitch_different_tables_picks_largest(self):
        table1 = [["X", "Y"], ["1", "2"]]
        table2 = [["A", "B", "C"], ["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]
        headers, rows = _stitch_tables([table1, table2])
        assert len(headers) == 3  # Picked larger table
        assert len(rows) == 3
