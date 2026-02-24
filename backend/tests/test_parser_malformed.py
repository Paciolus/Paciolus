"""
Tests for cross-format malformed file handling — Sprint 433.

Every malformed input must raise HTTPException(400) or HTTPException(422)
with an actionable error message. No unhandled crashes.

Covers: TSV, TXT, QBO/OFX, IIF, PDF, ODS (3 fixtures each).
"""

import io
import zipfile

import pytest
from fastapi import HTTPException

from shared.helpers import (
    _parse_tsv,
    _parse_txt,
    parse_uploaded_file_by_format,
)

# =============================================================================
# TSV Malformed (3 tests)
# =============================================================================


class TestTsvMalformed:
    """Malformed TSV inputs."""

    def test_mixed_tabs_and_spaces(self):
        """TSV where some rows use spaces instead of tabs — should still parse (pandas handles it)
        or raise a clean error."""
        content = b"Col1\tCol2\nval1\tval2\nval3 val4\n"
        # This may parse with mangled data, but should not crash
        try:
            df = _parse_tsv(content, "mixed.tsv")
            assert df is not None
        except HTTPException as e:
            assert e.status_code == 400

    def test_no_tab_chars_at_all(self):
        """File with .tsv extension but no tab delimiters — parses as single-column."""
        content = b"col1,col2\nval1,val2\nval3,val4\n"
        df = _parse_tsv(content, "notabs.tsv")
        # pandas will parse it as single column (the whole line)
        assert df is not None
        assert len(df) == 2

    def test_bom_with_inconsistent_columns(self):
        """UTF-8 BOM + varying column counts."""
        content = b"\xef\xbb\xbfA\tB\tC\n1\t2\n3\t4\t5\t6\n"
        # pandas handles BOM and uneven columns (fills with NaN)
        try:
            df = _parse_tsv(content, "bom.tsv")
            assert df is not None
        except HTTPException as e:
            assert e.status_code == 400


# =============================================================================
# TXT Malformed (3 tests)
# =============================================================================


class TestTxtMalformed:
    """Malformed TXT inputs."""

    def test_header_only_no_data(self):
        """File with just a header row and no data."""
        content = b"Account\tDescription\tBalance\n"
        with pytest.raises(HTTPException) as exc_info:
            _parse_txt(content, "headeronly.txt")
        assert exc_info.value.status_code == 400
        assert "too few lines" in exc_info.value.detail.lower()

    def test_delimiter_changes_mid_file(self):
        """First half tab-delimited, second half comma-delimited."""
        lines = [
            b"A\tB\tC",
            b"1\t2\t3",
            b"4\t5\t6",
            # Switch delimiter
            b"7,8,9",
            b"10,11,12",
        ]
        content = b"\n".join(lines) + b"\n"
        # Delimiter detection looks at first 20 lines — tab should win
        try:
            df = _parse_txt(content, "mixed_delim.txt")
            assert df is not None
        except HTTPException as e:
            assert e.status_code == 400

    def test_line_over_100k_chars(self):
        """A line exceeding 100K characters."""
        header = b"Col1\tCol2\n"
        long_line = b"x" * 120_000 + b"\tvalue\n"
        content = header + long_line
        # Should parse (cell length check is in _validate_and_convert_df, not the parser)
        try:
            df = _parse_txt(content, "longline.txt")
            assert df is not None
        except HTTPException as e:
            assert e.status_code in (400, 422)


# =============================================================================
# QBO/OFX Malformed (3 tests)
# =============================================================================


class TestOfxMalformed:
    """Malformed QBO/OFX inputs."""

    def test_truncated_mid_tag(self):
        """OFX content truncated in the middle of an XML tag."""
        content = b"""OFXHEADER:100
DATA:OFXSGML
<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS><CODE>0</CODE></STATUS>
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>2024010"""  # Truncated
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "truncated.qbo")
        assert exc_info.value.status_code == 400

    def test_valid_header_no_transactions(self):
        """OFX with valid header structure but zero STMTTRN entries."""
        content = b"""OFXHEADER:100
DATA:OFXSGML
<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS><CODE>0</CODE></STATUS>
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<BANKTRANLIST>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "empty.qbo")
        assert exc_info.value.status_code == 400

    def test_invalid_date_format(self):
        """OFX with malformed DTPOSTED dates."""
        content = b"""OFXHEADER:100
DATA:OFXSGML
<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS><CODE>0</CODE></STATUS>
</SONRS>
</SIGNONMSGSRSV1>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>NOTADATE
<TRNAMT>-50.00
<NAME>Test
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>"""
        # Should still parse (dates become NaT/string) or raise clean error
        try:
            result = parse_uploaded_file_by_format(content, "baddate.qbo")
            assert result is not None
        except HTTPException as e:
            assert e.status_code in (400, 422)


# =============================================================================
# IIF Malformed (3 tests)
# =============================================================================


class TestIifMalformed:
    """Malformed IIF inputs."""

    def test_trns_header_mismatched_columns(self):
        """!TRNS header with more columns than data rows."""
        content = b"!TRNS\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tNAME\n"
        content += b"TRNS\tCHECK\t01/15/2024\tChecking\n"  # Missing columns
        content += b"!ENDTRNS\n"
        # Should handle gracefully
        try:
            result = parse_uploaded_file_by_format(content, "mismatched.iif")
            assert result is not None
        except HTTPException as e:
            assert e.status_code in (400, 422)

    def test_only_accnt_section(self):
        """IIF file with only !ACCNT section (no transactions)."""
        content = b"!ACCNT\tNAME\tACCNTTYPE\nACCNT\tChecking\tBANK\n"
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "accntonly.iif")
        assert exc_info.value.status_code == 400

    def test_null_bytes_embedded(self):
        """IIF with embedded null bytes."""
        content = b"!TRNS\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\n"
        content += b"TRNS\tCHECK\x00\t01/15/2024\tChecking\t100.00\n"
        content += b"ENDTRNS\n"
        # Should handle gracefully
        try:
            result = parse_uploaded_file_by_format(content, "nullbytes.iif")
            assert result is not None
        except HTTPException as e:
            assert e.status_code in (400, 422)


# =============================================================================
# PDF Malformed (3 tests)
# =============================================================================


class TestPdfMalformed:
    """Malformed PDF inputs."""

    def test_no_tables_text_only(self):
        """Valid PDF with text content but no extractable tables.
        pdfplumber should fail gracefully with 422 (quality gate)."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawString(100, 700, "This is just text with no tables at all.")
        c.save()
        pdf_bytes = buf.getvalue()

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(pdf_bytes, "textonly.pdf")
        assert exc_info.value.status_code in (400, 422)

    def test_corrupt_header_partial_pdf(self):
        """File starting with %PDF but then garbage bytes."""
        content = b"%PDF-1.4 THIS IS NOT A REAL PDF FILE\x00\x00\x00garbage"
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "corrupt.pdf")
        assert exc_info.value.status_code in (400, 422)

    def test_empty_pages(self):
        """Valid PDF with empty pages (no content)."""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.showPage()  # Empty page 1
        c.showPage()  # Empty page 2
        c.save()
        pdf_bytes = buf.getvalue()

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(pdf_bytes, "empty_pages.pdf")
        assert exc_info.value.status_code in (400, 422)


# =============================================================================
# ODS Malformed (3 tests)
# =============================================================================


class TestOdsMalformed:
    """Malformed ODS inputs."""

    def test_truncated_zip(self):
        """ZIP file truncated mid-way — not a valid archive."""
        # Build a real ODS then truncate it
        from tests.test_ods_parser import _build_ods_zip

        full_ods = _build_ods_zip()
        truncated = full_ods[: len(full_ods) // 3]

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(truncated, "truncated.ods")
        assert exc_info.value.status_code == 400

    def test_empty_no_sheets(self):
        """ODS ZIP with ODS mimetype but no actual sheet data."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet")
            # Minimal content.xml with no table data
            zf.writestr(
                "content.xml",
                '<?xml version="1.0"?>'
                '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0">'
                "</office:document-content>",
            )
        ods_bytes = buf.getvalue()

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(ods_bytes, "nosheets.ods")
        assert exc_info.value.status_code == 400

    def test_xml_bomb_pattern_in_content(self):
        """ODS with XML bomb pattern (<!DOCTYPE> in content.xml).
        The archive bomb scanner should catch this since ODS is ZIP-based."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet")
            zf.writestr(
                "content.xml",
                '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe "bomb">]><root>&xxe;</root>',
            )
        ods_bytes = buf.getvalue()

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(ods_bytes, "xmlbomb.ods")
        assert exc_info.value.status_code == 400
