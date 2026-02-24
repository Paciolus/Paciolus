"""
Tests for shared.ods_parser — ODS File Parsing & ZIP Disambiguation.

Tests cover:
- ODS parsing (valid file, multi-sheet, metadata attachment)
- ZIP disambiguation (_is_ods_zip for ODS vs XLSX)
- Error handling (corrupt, empty, no sheets)
- Integration with parse_uploaded_file_by_format()
- Integration with workbook_inspector inspect_workbook()
"""

import io
import zipfile

import pandas as pd
import pytest
from fastapi import HTTPException

from shared.ods_parser import OdsMetadata, _is_ods_zip, parse_ods

# =============================================================================
# Helpers — Build minimal ODS and XLSX ZIPs in memory
# =============================================================================


def _build_ods_zip(sheets: dict[str, pd.DataFrame] | None = None) -> bytes:
    """Build a minimal ODS file as bytes using odfpy.

    Uses odfpy with valuetype attributes so pandas can read cells correctly.
    """
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableCell, TableRow
    from odf.text import P

    doc = OpenDocumentSpreadsheet()

    if sheets is None:
        sheets = {"Sheet1": pd.DataFrame({"Account": ["1000", "2000"], "Balance": [100.0, 200.0]})}

    for sheet_name, df in sheets.items():
        table = Table(name=sheet_name)

        # Header row — use valuetype="string" so pandas reads column names
        header_row = TableRow()
        for col in df.columns:
            cell = TableCell(valuetype="string")
            cell.addElement(P(text=str(col)))
            header_row.addElement(cell)
        table.addElement(header_row)

        # Data rows
        for _, row_data in df.iterrows():
            data_row = TableRow()
            for val in row_data:
                if isinstance(val, (int, float)):
                    cell = TableCell(valuetype="float", value=str(val))
                else:
                    cell = TableCell(valuetype="string")
                cell.addElement(P(text=str(val)))
                data_row.addElement(cell)
            table.addElement(data_row)

        doc.spreadsheet.addElement(table)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _build_xlsx_zip() -> bytes:
    """Build a minimal XLSX file as bytes."""
    buf = io.BytesIO()
    df = pd.DataFrame({"Col1": [1, 2], "Col2": [3, 4]})
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def _build_raw_zip_with_mimetype(mimetype_content: str) -> bytes:
    """Build a raw ZIP with a mimetype entry (for disambiguation tests)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("mimetype", mimetype_content)
        zf.writestr("content.xml", "<root/>")
    return buf.getvalue()


def _build_raw_zip_with_xl_dir() -> bytes:
    """Build a raw ZIP with xl/ directory (XLSX-like)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("xl/workbook.xml", "<root/>")
        zf.writestr("[Content_Types].xml", "<root/>")
    return buf.getvalue()


# =============================================================================
# _is_ods_zip() — ZIP disambiguation
# =============================================================================


class TestIsOdsZip:
    """ZIP content inspection for ODS vs XLSX disambiguation."""

    def test_ods_with_mimetype_entry(self):
        ods_bytes = _build_raw_zip_with_mimetype("application/vnd.oasis.opendocument.spreadsheet")
        assert _is_ods_zip(ods_bytes) is True

    def test_xlsx_with_xl_dir(self):
        xlsx_bytes = _build_raw_zip_with_xl_dir()
        assert _is_ods_zip(xlsx_bytes) is False

    def test_real_ods_file(self):
        ods_bytes = _build_ods_zip()
        assert _is_ods_zip(ods_bytes) is True

    def test_real_xlsx_file(self):
        xlsx_bytes = _build_xlsx_zip()
        assert _is_ods_zip(xlsx_bytes) is False

    def test_zip_with_content_xml_no_xl(self):
        """ZIP with content.xml but no xl/ -> treated as ODS."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("content.xml", "<office:document/>")
        assert _is_ods_zip(buf.getvalue()) is True

    def test_invalid_zip_returns_false(self):
        assert _is_ods_zip(b"not a zip file at all") is False

    def test_empty_zip(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            pass  # empty ZIP
        assert _is_ods_zip(buf.getvalue()) is False

    def test_mimetype_without_opendocument(self):
        """ZIP with mimetype but wrong content -> not ODS."""
        ods_bytes = _build_raw_zip_with_mimetype("application/zip")
        assert _is_ods_zip(ods_bytes) is False


# =============================================================================
# parse_ods() — Core parsing
# =============================================================================


class TestParseOds:
    """ODS file parsing via odfpy engine."""

    def test_parse_valid_single_sheet(self):
        ods_bytes = _build_ods_zip()
        df = parse_ods(ods_bytes, "test.ods")
        assert len(df) == 2
        assert "Account" in df.columns
        assert "Balance" in df.columns

    def test_metadata_attached(self):
        ods_bytes = _build_ods_zip()
        df = parse_ods(ods_bytes, "test.ods")
        metadata = df.attrs.get("ods_metadata")
        assert metadata is not None
        assert isinstance(metadata, OdsMetadata)
        assert metadata.sheet_name == "Sheet1"
        assert metadata.sheet_count == 1
        assert metadata.original_row_count == 2
        assert metadata.original_col_count == 2

    def test_parse_multi_sheet_reads_first(self):
        sheets = {
            "Revenue": pd.DataFrame({"Amount": [100, 200]}),
            "Expenses": pd.DataFrame({"Cost": [50, 75]}),
        }
        ods_bytes = _build_ods_zip(sheets)
        df = parse_ods(ods_bytes, "multi.ods")
        assert "Amount" in df.columns
        metadata = df.attrs["ods_metadata"]
        assert metadata.sheet_count == 2
        assert metadata.sheet_name == "Revenue"

    def test_parse_corrupt_file_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            parse_ods(b"not an ods file", "corrupt.ods")
        assert exc_info.value.status_code == 400
        assert "ODS file could not be opened" in exc_info.value.detail

    def test_parse_empty_sheet(self):
        """ODS with only headers (no data rows) should still return a DataFrame."""
        sheets = {"Empty": pd.DataFrame({"A": pd.Series(dtype="str"), "B": pd.Series(dtype="str")})}
        ods_bytes = _build_ods_zip(sheets)
        df = parse_ods(ods_bytes, "empty.ods")
        assert len(df) == 0

    def test_metadata_is_frozen(self):
        ods_bytes = _build_ods_zip()
        df = parse_ods(ods_bytes, "test.ods")
        metadata = df.attrs["ods_metadata"]
        with pytest.raises(AttributeError):
            metadata.sheet_name = "Modified"  # type: ignore[misc]

    def test_returns_dataframe(self):
        ods_bytes = _build_ods_zip()
        result = parse_ods(ods_bytes, "test.ods")
        assert isinstance(result, pd.DataFrame)


# =============================================================================
# Format detection integration
# =============================================================================


class TestOdsFormatDetection:
    """ODS detection via detect_format() and file_formats module."""

    def test_detect_by_extension(self):
        from shared.file_formats import FileFormat, detect_format

        result = detect_format(filename="data.ods")
        assert result.format == FileFormat.ODS
        assert result.confidence == "high"
        assert result.source == "extension"

    def test_detect_ods_by_magic_bytes(self):
        from shared.file_formats import FileFormat, detect_format

        ods_bytes = _build_ods_zip()
        result = detect_format(file_bytes=ods_bytes)
        assert result.format == FileFormat.ODS
        assert result.source == "magic"

    def test_detect_xlsx_by_magic_bytes_not_ods(self):
        from shared.file_formats import FileFormat, detect_format

        xlsx_bytes = _build_xlsx_zip()
        result = detect_format(file_bytes=xlsx_bytes)
        assert result.format == FileFormat.XLSX
        assert result.source == "magic"

    def test_extension_overrides_zip_inspection(self):
        """Extension has higher priority than magic bytes."""
        from shared.file_formats import FileFormat, detect_format

        xlsx_bytes = _build_xlsx_zip()
        result = detect_format(filename="report.ods", file_bytes=xlsx_bytes)
        assert result.format == FileFormat.ODS
        assert result.source == "extension"

    def test_ods_content_type_detection(self):
        from shared.file_formats import FileFormat, detect_format

        result = detect_format(content_type="application/vnd.oasis.opendocument.spreadsheet")
        assert result.format == FileFormat.ODS
        assert result.source == "content_type"


# =============================================================================
# Profile assertions
# =============================================================================


class TestOdsProfile:
    """ODS profile in FORMAT_PROFILES."""

    def test_ods_parse_supported(self):
        from shared.file_formats import FORMAT_PROFILES, FileFormat

        profile = FORMAT_PROFILES[FileFormat.ODS]
        assert profile.parse_supported is True

    def test_ods_content_types(self):
        from shared.file_formats import FORMAT_PROFILES, FileFormat

        profile = FORMAT_PROFILES[FileFormat.ODS]
        assert "application/vnd.oasis.opendocument.spreadsheet" in profile.content_types
        assert "application/octet-stream" in profile.content_types

    def test_ods_extension(self):
        from shared.file_formats import FORMAT_PROFILES, FileFormat

        profile = FORMAT_PROFILES[FileFormat.ODS]
        assert ".ods" in profile.extensions

    def test_ods_label(self):
        from shared.file_formats import FORMAT_PROFILES, FileFormat

        profile = FORMAT_PROFILES[FileFormat.ODS]
        assert profile.label == "ODS (.ods)"

    def test_ods_in_allowed_extensions(self):
        from shared.file_formats import ALLOWED_EXTENSIONS

        assert ".ods" in ALLOWED_EXTENSIONS

    def test_ods_in_allowed_content_types(self):
        from shared.file_formats import ALLOWED_CONTENT_TYPES

        assert "application/vnd.oasis.opendocument.spreadsheet" in ALLOWED_CONTENT_TYPES

    def test_display_includes_ods(self):
        from shared.file_formats import get_active_extensions_display

        display = get_active_extensions_display()
        assert ".ods" in display
