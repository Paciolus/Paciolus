"""
Tests for shared.file_formats — File Format Detection & Validation Profiles.

Tests cover:
- FileFormat enum membership and string equality
- FormatProfile immutability and structure
- ALLOWED_EXTENSIONS / ALLOWED_CONTENT_TYPES derived sets (regression)
- detect_format() priority chain (extension > magic > content_type)
- FileValidationErrorCode enum
- Display helper functions
"""

import pytest

from shared.file_formats import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    FORMAT_PROFILES,
    XLS_MAGIC,
    XLSX_MAGIC,
    FileFormat,
    FileValidationErrorCode,
    FormatDetectionResult,
    detect_format,
    get_active_extensions_display,
    get_active_format_labels,
)

# =============================================================================
# FileFormat Enum
# =============================================================================


class TestFileFormatEnum:
    """FileFormat enum membership and string behavior."""

    def test_csv_value(self):
        assert FileFormat.CSV == "csv"
        assert FileFormat.CSV.value == "csv"

    def test_all_members_present(self):
        expected = {"csv", "xlsx", "xls", "tsv", "txt", "qbo", "ofx", "iif", "pdf", "ods", "unknown"}
        actual = {f.value for f in FileFormat}
        assert actual == expected

    def test_str_equality(self):
        """FileFormat members should be comparable to plain strings."""
        assert FileFormat.XLSX == "xlsx"
        assert FileFormat.UNKNOWN == "unknown"


# =============================================================================
# FormatProfile
# =============================================================================


class TestFormatProfile:
    """FormatProfile dataclass structure and immutability."""

    def test_csv_profile_exists(self):
        profile = FORMAT_PROFILES[FileFormat.CSV]
        assert profile.format == FileFormat.CSV
        assert ".csv" in profile.extensions
        assert profile.parse_supported is True

    def test_xlsx_profile_has_magic_bytes(self):
        profile = FORMAT_PROFILES[FileFormat.XLSX]
        assert XLSX_MAGIC in profile.magic_bytes

    def test_xls_profile_has_magic_bytes(self):
        profile = FORMAT_PROFILES[FileFormat.XLS]
        assert XLS_MAGIC in profile.magic_bytes

    def test_profile_is_frozen(self):
        profile = FORMAT_PROFILES[FileFormat.CSV]
        with pytest.raises(AttributeError):
            profile.label = "Modified"  # type: ignore[misc]

    def test_unsupported_formats_not_parseable(self):
        """QBO, OFX etc. should have parse_supported=False."""
        for fmt in (FileFormat.QBO, FileFormat.OFX, FileFormat.IIF, FileFormat.PDF, FileFormat.ODS):
            assert FORMAT_PROFILES[fmt].parse_supported is False, f"{fmt} should not be parse_supported"


# =============================================================================
# Derived constants (regression tests)
# =============================================================================


class TestAllowedSets:
    """ALLOWED_EXTENSIONS and ALLOWED_CONTENT_TYPES must match helpers.py originals."""

    def test_allowed_extensions_match(self):
        """Must contain exactly the 5 active extensions."""
        assert ALLOWED_EXTENSIONS == {".csv", ".tsv", ".txt", ".xlsx", ".xls"}

    def test_allowed_content_types_match(self):
        """Must contain the 7 MIME types from all active profiles."""
        expected = {
            "text/csv",
            "application/csv",
            "text/tab-separated-values",
            "text/plain",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream",
        }
        assert ALLOWED_CONTENT_TYPES == expected


# =============================================================================
# detect_format()
# =============================================================================


class TestDetectFormat:
    """detect_format() priority chain: extension > magic > content_type."""

    # — Extension-based —

    def test_csv_by_extension(self):
        result = detect_format(filename="data.csv")
        assert result.format == FileFormat.CSV
        assert result.confidence == "high"
        assert result.source == "extension"

    def test_xlsx_by_extension(self):
        result = detect_format(filename="report.xlsx")
        assert result.format == FileFormat.XLSX
        assert result.source == "extension"

    def test_xls_by_extension(self):
        result = detect_format(filename="legacy.xls")
        assert result.format == FileFormat.XLS
        assert result.source == "extension"

    def test_tsv_by_extension(self):
        result = detect_format(filename="data.tsv")
        assert result.format == FileFormat.TSV

    def test_pdf_by_extension(self):
        result = detect_format(filename="document.pdf")
        assert result.format == FileFormat.PDF

    def test_case_insensitive_extension(self):
        result = detect_format(filename="DATA.CSV")
        assert result.format == FileFormat.CSV

    def test_unknown_extension(self):
        result = detect_format(filename="data.json")
        assert result.format == FileFormat.UNKNOWN

    # — Magic byte-based —

    def test_xlsx_by_magic_bytes(self):
        result = detect_format(file_bytes=XLSX_MAGIC + b"\x00" * 100)
        assert result.format == FileFormat.XLSX
        assert result.confidence == "high"
        assert result.source == "magic"

    def test_xls_by_magic_bytes(self):
        result = detect_format(file_bytes=XLS_MAGIC + b"\x00" * 100)
        assert result.format == FileFormat.XLS
        assert result.source == "magic"

    def test_pdf_by_magic_bytes(self):
        result = detect_format(file_bytes=b"%PDF-1.4" + b"\x00" * 100)
        assert result.format == FileFormat.PDF
        assert result.source == "magic"

    # — Content-type based —

    def test_csv_by_content_type(self):
        result = detect_format(content_type="text/csv")
        assert result.format == FileFormat.CSV
        assert result.confidence == "medium"
        assert result.source == "content_type"

    def test_octet_stream_is_unknown(self):
        """application/octet-stream is too generic — should not match alone."""
        result = detect_format(content_type="application/octet-stream")
        assert result.format == FileFormat.UNKNOWN

    # — Priority chain —

    def test_extension_overrides_magic(self):
        """Extension should win even if magic bytes suggest different format."""
        result = detect_format(filename="data.csv", file_bytes=XLSX_MAGIC + b"\x00" * 100)
        assert result.format == FileFormat.CSV
        assert result.source == "extension"

    def test_magic_overrides_content_type(self):
        """Magic bytes should win over content_type when no extension."""
        result = detect_format(content_type="text/csv", file_bytes=XLSX_MAGIC + b"\x00" * 100)
        assert result.format == FileFormat.XLSX
        assert result.source == "magic"

    # — Edge cases —

    def test_no_inputs_returns_unknown(self):
        result = detect_format()
        assert result.format == FileFormat.UNKNOWN
        assert result.confidence == "low"
        assert result.source == "none"

    def test_empty_filename(self):
        result = detect_format(filename="")
        assert result.format == FileFormat.UNKNOWN

    def test_filename_no_extension(self):
        result = detect_format(filename="datafile")
        assert result.format == FileFormat.UNKNOWN

    def test_short_file_bytes(self):
        """Fewer than 4 bytes should not crash magic detection."""
        result = detect_format(file_bytes=b"PK")
        assert result.format == FileFormat.UNKNOWN

    def test_result_is_named_tuple(self):
        result = detect_format(filename="x.csv")
        assert isinstance(result, FormatDetectionResult)
        fmt, conf, src = result  # unpack
        assert fmt == FileFormat.CSV


# =============================================================================
# FileValidationErrorCode
# =============================================================================


class TestFileValidationErrorCode:
    """FileValidationErrorCode enum membership."""

    def test_all_codes_present(self):
        expected = {
            "unsupported_format",
            "content_type_rejected",
            "magic_byte_mismatch",
            "file_empty",
            "file_too_large",
            "archive_bomb",
            "xml_bomb",
            "row_limit_exceeded",
            "column_limit_exceeded",
            "cell_length_exceeded",
            "parse_failed",
            "delimiter_ambiguous",
        }
        actual = {c.value for c in FileValidationErrorCode}
        assert actual == expected

    def test_str_equality(self):
        assert FileValidationErrorCode.FILE_EMPTY == "file_empty"


# =============================================================================
# Display helpers
# =============================================================================


class TestHelpers:
    """get_active_format_labels() and get_active_extensions_display()."""

    def test_active_labels_include_csv_and_excel(self):
        labels = get_active_format_labels()
        assert "CSV" in labels
        assert any("xlsx" in lbl.lower() for lbl in labels)

    def test_extensions_display_string(self):
        display = get_active_extensions_display()
        assert ".csv" in display
        assert ".tsv" in display
        assert ".txt" in display
        assert ".xlsx" in display
        assert ".xls" in display

    def test_active_labels_include_tsv_and_txt(self):
        labels = get_active_format_labels()
        assert any("tsv" in lbl.lower() for lbl in labels)
        assert any("txt" in lbl.lower() for lbl in labels)


# =============================================================================
# TSV / TXT Profile Assertions (Sprint 422)
# =============================================================================


class TestTsvTxtProfiles:
    """Verify TSV and TXT profiles are now parse_supported=True."""

    def test_tsv_parse_supported(self):
        profile = FORMAT_PROFILES[FileFormat.TSV]
        assert profile.parse_supported is True

    def test_tsv_content_types(self):
        profile = FORMAT_PROFILES[FileFormat.TSV]
        assert "text/tab-separated-values" in profile.content_types
        assert "application/octet-stream" in profile.content_types

    def test_tsv_extension(self):
        profile = FORMAT_PROFILES[FileFormat.TSV]
        assert ".tsv" in profile.extensions

    def test_txt_parse_supported(self):
        profile = FORMAT_PROFILES[FileFormat.TXT]
        assert profile.parse_supported is True

    def test_txt_content_types(self):
        profile = FORMAT_PROFILES[FileFormat.TXT]
        assert "text/plain" in profile.content_types
        assert "application/octet-stream" in profile.content_types

    def test_txt_extension(self):
        profile = FORMAT_PROFILES[FileFormat.TXT]
        assert ".txt" in profile.extensions

    def test_txt_label(self):
        profile = FORMAT_PROFILES[FileFormat.TXT]
        assert profile.label == "Text (.txt)"
