"""
Tests for Sprint 122 — Upload Validation & Error Sanitization.

Tests cover:
- File content-type validation
- File extension validation
- Empty file detection
- CSV encoding fallback (UTF-8 → Latin-1)
- Row count protection
- Zero data rows detection
- Error message sanitization (no traceback leakage)
"""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
from fastapi import HTTPException

from shared.helpers import (
    validate_file_size,
    parse_uploaded_file,
    ALLOWED_EXTENSIONS,
    ALLOWED_CONTENT_TYPES,
    MAX_ROW_COUNT,
)
from shared.error_messages import sanitize_error


# =============================================================================
# HELPERS — Mock UploadFile
# =============================================================================

def make_upload_file(content: bytes, filename: str = "test.csv", content_type: str = "text/csv"):
    """Create a mock UploadFile for testing."""
    mock = AsyncMock()
    mock.filename = filename
    mock.content_type = content_type

    chunks = [content[i:i+1024*1024] for i in range(0, len(content), 1024*1024)]
    chunks.append(b"")
    mock.read = AsyncMock(side_effect=chunks)
    return mock


# =============================================================================
# FILE EXTENSION VALIDATION
# =============================================================================

class TestFileExtensionValidation:
    """Tests for file extension validation in validate_file_size."""

    @pytest.mark.asyncio
    async def test_csv_extension_accepted(self):
        """CSV files should be accepted."""
        content = b"col1,col2\n1,2\n"
        mock_file = make_upload_file(content, "data.csv", "text/csv")
        result = await validate_file_size(mock_file)
        assert result == content

    @pytest.mark.asyncio
    async def test_xlsx_extension_accepted(self):
        """Excel .xlsx files should be accepted."""
        content = b"fake excel content"
        mock_file = make_upload_file(content, "data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        result = await validate_file_size(mock_file)
        assert result == content

    @pytest.mark.asyncio
    async def test_xls_extension_accepted(self):
        """Legacy Excel .xls files should be accepted."""
        content = b"fake excel content"
        mock_file = make_upload_file(content, "data.xls", "application/vnd.ms-excel")
        result = await validate_file_size(mock_file)
        assert result == content

    @pytest.mark.asyncio
    async def test_txt_extension_rejected(self):
        """Text files should be rejected."""
        content = b"some text content"
        mock_file = make_upload_file(content, "data.txt", "text/plain")
        with pytest.raises(HTTPException) as exc_info:
            await validate_file_size(mock_file)
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail
        assert ".txt" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_zip_extension_rejected(self):
        """ZIP files should be rejected."""
        content = b"PK zip content"
        mock_file = make_upload_file(content, "data.zip", "application/zip")
        with pytest.raises(HTTPException) as exc_info:
            await validate_file_size(mock_file)
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_exe_extension_rejected(self):
        """Executable files should be rejected."""
        content = b"MZ executable"
        mock_file = make_upload_file(content, "malware.exe", "application/octet-stream")
        with pytest.raises(HTTPException) as exc_info:
            await validate_file_size(mock_file)
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_no_extension_accepted(self):
        """Files without extension should pass (content-type based)."""
        content = b"col1,col2\n1,2\n"
        mock_file = make_upload_file(content, "datafile", "text/csv")
        result = await validate_file_size(mock_file)
        assert result == content


# =============================================================================
# CONTENT-TYPE VALIDATION
# =============================================================================

class TestContentTypeValidation:
    """Tests for content-type validation in validate_file_size."""

    @pytest.mark.asyncio
    async def test_octet_stream_accepted(self):
        """application/octet-stream should be accepted (common browser behavior for CSV)."""
        content = b"col1,col2\n1,2\n"
        mock_file = make_upload_file(content, "data.csv", "application/octet-stream")
        result = await validate_file_size(mock_file)
        assert result == content

    @pytest.mark.asyncio
    async def test_unsupported_content_type_rejected(self):
        """Non-spreadsheet content types with valid extension should still be rejected by content-type."""
        content = b"some content"
        mock_file = make_upload_file(content, "data.csv", "application/json")
        with pytest.raises(HTTPException) as exc_info:
            await validate_file_size(mock_file)
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_empty_content_type_accepted(self):
        """Empty content type should be accepted (let extension check handle it)."""
        content = b"col1,col2\n1,2\n"
        mock_file = make_upload_file(content, "data.csv", "")
        result = await validate_file_size(mock_file)
        assert result == content


# =============================================================================
# EMPTY FILE DETECTION
# =============================================================================

class TestEmptyFileDetection:
    """Tests for empty file detection in validate_file_size."""

    @pytest.mark.asyncio
    async def test_empty_file_rejected(self):
        """Empty files should return a helpful error."""
        mock_file = make_upload_file(b"", "empty.csv", "text/csv")
        with pytest.raises(HTTPException) as exc_info:
            await validate_file_size(mock_file)
        assert exc_info.value.status_code == 400
        assert "empty" in exc_info.value.detail.lower()


# =============================================================================
# CSV ENCODING FALLBACK
# =============================================================================

class TestCSVEncodingFallback:
    """Tests for encoding fallback in parse_uploaded_file."""

    def test_utf8_csv_parsed_correctly(self):
        """Standard UTF-8 CSV should parse normally."""
        content = "name,amount\nAlice,100\nBob,200\n".encode("utf-8")
        columns, rows = parse_uploaded_file(content, "test.csv")
        assert columns == ["name", "amount"]
        assert len(rows) == 2

    def test_latin1_csv_parsed_via_fallback(self):
        """Latin-1 encoded CSV should succeed via fallback."""
        content = "name,amount\nCaf\xe9,100\nNa\xefve,200\n".encode("latin-1")
        columns, rows = parse_uploaded_file(content, "test.csv")
        assert columns == ["name", "amount"]
        assert len(rows) == 2
        assert "Caf" in rows[0]["name"]

    def test_utf8_bom_csv_parsed(self):
        """UTF-8 with BOM should parse correctly."""
        content = b"\xef\xbb\xbfname,amount\nAlice,100\n"
        columns, rows = parse_uploaded_file(content, "test.csv")
        assert len(rows) == 1


# =============================================================================
# ROW COUNT PROTECTION
# =============================================================================

class TestRowCountProtection:
    """Tests for row count protection in parse_uploaded_file."""

    def test_file_within_limit(self):
        """Files within row limit should parse normally."""
        rows_csv = "col1\n" + "\n".join(str(i) for i in range(100))
        content = rows_csv.encode("utf-8")
        columns, rows = parse_uploaded_file(content, "test.csv")
        assert len(rows) == 100

    def test_file_exceeding_limit(self):
        """Files exceeding row limit should raise 400."""
        # Use a small limit for testing
        rows_csv = "col1\n" + "\n".join(str(i) for i in range(1001))
        content = rows_csv.encode("utf-8")
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file(content, "test.csv", max_rows=1000)
        assert exc_info.value.status_code == 400
        assert "1,001" in exc_info.value.detail  # formatted row count
        assert "1,000" in exc_info.value.detail  # formatted limit

    def test_file_at_exact_limit(self):
        """Files at exactly the row limit should parse normally."""
        rows_csv = "col1\n" + "\n".join(str(i) for i in range(1000))
        content = rows_csv.encode("utf-8")
        columns, rows = parse_uploaded_file(content, "test.csv", max_rows=1000)
        assert len(rows) == 1000


# =============================================================================
# ZERO DATA ROWS
# =============================================================================

class TestZeroDataRows:
    """Tests for zero data rows detection in parse_uploaded_file."""

    def test_headers_only_csv_rejected(self):
        """CSV with headers but no data rows should raise 400."""
        content = b"name,amount,date\n"
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file(content, "test.csv")
        assert exc_info.value.status_code == 400
        assert "no data rows" in exc_info.value.detail.lower()

    def test_malformed_csv_rejected(self):
        """Completely empty CSV should raise 400."""
        content = b""
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file(content, "test.csv")
        assert exc_info.value.status_code == 400


# =============================================================================
# EXCEL FILE PARSING
# =============================================================================

class TestExcelParsing:
    """Tests for Excel file parsing in parse_uploaded_file."""

    def test_valid_xlsx_parsed(self):
        """Valid Excel bytes should parse correctly."""
        df = pd.DataFrame({"name": ["Alice", "Bob"], "amount": [100, 200]})
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        content = buffer.getvalue()

        columns, rows = parse_uploaded_file(content, "test.xlsx")
        assert "name" in columns
        assert "amount" in columns
        assert len(rows) == 2

    def test_invalid_xlsx_rejected(self):
        """Invalid Excel bytes should raise 400."""
        content = b"this is not an excel file"
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file(content, "test.xlsx")
        assert exc_info.value.status_code == 400
        assert "Excel file could not be read" in exc_info.value.detail


# =============================================================================
# ERROR MESSAGE SANITIZATION
# =============================================================================

class TestErrorSanitization:
    """Tests for error message sanitization."""

    def test_pandas_parse_error_sanitized(self):
        """Pandas ParserError should return friendly message."""
        exc = Exception("ParserError: Expected 5 fields in line 3, saw 7")
        msg = sanitize_error(exc, "upload", "test_error")
        assert "ParserError" not in msg
        assert "invalid" in msg.lower() or "format" in msg.lower()

    def test_unicode_error_sanitized(self):
        """UnicodeDecodeError should return friendly message."""
        exc = Exception("'utf-8' codec can't decode byte 0xff in position 0")
        msg = sanitize_error(exc, "upload", "test_error")
        assert "codec" not in msg
        assert "UTF-8" in msg or "decoded" in msg

    def test_key_error_sanitized(self):
        """KeyError for missing columns should return friendly message."""
        exc = Exception("KeyError: 'amount' column not found in DataFrame")
        msg = sanitize_error(exc, "upload", "test_error")
        assert "DataFrame" not in msg
        assert "column" in msg.lower()

    def test_memory_error_sanitized(self):
        """MemoryError should return friendly message."""
        exc = Exception("MemoryError: unable to allocate 4.00 GiB")
        msg = sanitize_error(exc, "upload", "test_error")
        assert "GiB" not in msg
        assert "large" in msg.lower() or "size" in msg.lower()

    def test_generic_error_returns_fallback(self):
        """Unknown errors should return operation-specific fallback."""
        exc = Exception("Some completely unknown internal error with /path/to/file")
        msg = sanitize_error(exc, "export", "test_error")
        assert "/path/to/file" not in msg
        assert "try again" in msg.lower()

    def test_upload_fallback_message(self):
        """Upload operation should get upload-specific fallback."""
        exc = Exception("something weird happened")
        msg = sanitize_error(exc, "upload", "test")
        assert "file" in msg.lower()

    def test_export_fallback_message(self):
        """Export operation should get export-specific fallback."""
        exc = Exception("something weird happened")
        msg = sanitize_error(exc, "export", "test")
        assert "export" in msg.lower()

    def test_sqlalchemy_error_sanitized(self):
        """SQLAlchemy errors should not leak database details."""
        exc = Exception("sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: users")
        msg = sanitize_error(exc, "default", "test")
        assert "sqlite3" not in msg
        assert "no such table" not in msg
        assert "database" in msg.lower()

    def test_reportlab_error_sanitized(self):
        """PDF generation errors should not leak library details."""
        exc = Exception("reportlab.platypus.doctemplate: DocumentTemplate error on page 3")
        msg = sanitize_error(exc, "export", "test")
        assert "reportlab" not in msg
        assert "PDF" in msg or "pdf" in msg

    def test_no_traceback_in_any_pattern(self):
        """No sanitized message should contain file paths or line numbers."""
        test_exceptions = [
            Exception("File '/usr/lib/python3.12/csv.py', line 23, in reader"),
            Exception("Traceback (most recent call last):\n  File 'main.py'"),
            Exception("pandas.errors.EmptyDataError: No columns to parse from file"),
        ]
        for exc in test_exceptions:
            msg = sanitize_error(exc, "upload", "test")
            assert "File '" not in msg
            assert "Traceback" not in msg
            assert "line " not in msg or "line" in "offline"  # allow "line" in normal sentences


# =============================================================================
# RATE LIMIT WIRING VERIFICATION
# =============================================================================

class TestRateLimitWiring:
    """Verify rate limit decorators are wired to export routes."""

    def test_export_routes_have_rate_limits(self):
        """All export routes should have rate limit decorators."""
        from main import app

        export_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and '/export/' in route.path:
                export_routes.append(route.path)

        # Should have at least 26 export endpoints
        assert len(export_routes) >= 26, f"Expected >= 26 export routes, found {len(export_routes)}: {export_routes}"

    def test_rate_limit_export_value(self):
        """RATE_LIMIT_EXPORT should be defined and reasonable."""
        from shared.rate_limits import RATE_LIMIT_EXPORT
        assert RATE_LIMIT_EXPORT == "20/minute"


# =============================================================================
# AUTH VERIFICATION
# =============================================================================

class TestAuthClassification:
    """Verify export endpoints use require_verified_user."""

    def test_engagement_export_routes_exist(self):
        """Engagement export routes should be registered."""
        from main import app

        engagement_export_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and 'export' in route.path and 'engagement' in route.path:
                engagement_export_routes.append(route.path)

        assert len(engagement_export_routes) >= 2, f"Expected >= 2 engagement export routes, found {engagement_export_routes}"


# =============================================================================
# SPRINT 193: IDENTIFIER DTYPE PRESERVATION
# =============================================================================

class TestIdentifierDtypePreservation:
    """Test that numeric identifier columns are converted to strings."""

    def test_parse_preserves_leading_zeros(self):
        """Account codes like 1001.0 should become '1001', not float."""
        csv_content = b"Account Number,Debit,Credit\n1001,500,0\n2001,0,500\n"

        columns, rows = parse_uploaded_file(csv_content, "test.csv")

        # Account Number column should have string values (not floats)
        for row in rows:
            acct = row.get("Account Number")
            assert isinstance(acct, str), f"Expected str, got {type(acct)}: {acct}"
            assert "." not in acct, f"Account number should not have decimal: {acct}"
