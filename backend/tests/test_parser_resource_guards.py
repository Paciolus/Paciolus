"""
Tests for parser resource guards — Sprint 434.

Verifies that resource limits (row count, column count, cell length,
archive bomb detection) are enforced across all relevant formats.
"""

import io
import zipfile

import pandas as pd
import pytest
from fastapi import HTTPException

from shared.helpers import (
    MAX_CELL_LENGTH,
    MAX_COL_COUNT,
    MAX_ROW_COUNT,
    MAX_ZIP_ENTRIES,
    _validate_and_convert_df,
    _validate_xlsx_archive,
    parse_uploaded_file_by_format,
)

# =============================================================================
# Row count limits
# =============================================================================


class TestRowCountGuard:
    """Row count > MAX_ROW_COUNT should raise 400."""

    def test_csv_row_limit(self):
        """CSV with rows exceeding limit."""
        rows = MAX_ROW_COUNT + 10
        header = "A,B\n"
        data = "1,2\n" * rows
        content = (header + data).encode()

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "big.csv")
        assert exc_info.value.status_code == 400
        assert "rows" in exc_info.value.detail.lower()

    def test_tsv_row_limit(self):
        """TSV with rows exceeding limit."""
        rows = MAX_ROW_COUNT + 10
        header = "A\tB\n"
        data = "1\t2\n" * rows
        content = (header + data).encode()

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "big.tsv")
        assert exc_info.value.status_code == 400
        assert "rows" in exc_info.value.detail.lower()

    def test_validate_and_convert_df_row_limit(self):
        """Direct _validate_and_convert_df with oversized DataFrame."""
        df = pd.DataFrame({"A": range(MAX_ROW_COUNT + 1)})

        with pytest.raises(HTTPException) as exc_info:
            _validate_and_convert_df(df, MAX_ROW_COUNT)
        assert exc_info.value.status_code == 400
        assert "rows" in exc_info.value.detail.lower()


# =============================================================================
# Column count limits
# =============================================================================


class TestColumnCountGuard:
    """Column count > MAX_COL_COUNT should raise 400."""

    def test_csv_column_limit(self):
        """CSV with columns exceeding limit."""
        cols = MAX_COL_COUNT + 10
        header = ",".join(f"C{i}" for i in range(cols))
        data = ",".join("1" for _ in range(cols))
        content = f"{header}\n{data}\n".encode()

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "wide.csv")
        assert exc_info.value.status_code == 400
        assert "columns" in exc_info.value.detail.lower()

    def test_validate_and_convert_df_column_limit(self):
        """Direct _validate_and_convert_df with oversized columns."""
        df = pd.DataFrame({f"C{i}": [1] for i in range(MAX_COL_COUNT + 1)})

        with pytest.raises(HTTPException) as exc_info:
            _validate_and_convert_df(df, MAX_ROW_COUNT)
        assert exc_info.value.status_code == 400
        assert "columns" in exc_info.value.detail.lower()


# =============================================================================
# Cell length limits
# =============================================================================


class TestCellLengthGuard:
    """Cell content > MAX_CELL_LENGTH should raise 400."""

    def test_csv_cell_length_limit(self):
        """CSV with a cell exceeding MAX_CELL_LENGTH."""
        long_value = "x" * (MAX_CELL_LENGTH + 1)
        content = f"Name,Value\nOK,{long_value}\n".encode()

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "longcell.csv")
        assert exc_info.value.status_code == 400
        assert "length" in exc_info.value.detail.lower()

    def test_validate_and_convert_df_cell_length(self):
        """Direct _validate_and_convert_df with oversized cell."""
        df = pd.DataFrame({"Name": ["x" * (MAX_CELL_LENGTH + 1)]})

        with pytest.raises(HTTPException) as exc_info:
            _validate_and_convert_df(df, MAX_ROW_COUNT)
        assert exc_info.value.status_code == 400
        assert "length" in exc_info.value.detail.lower()


# =============================================================================
# Archive bomb detection (ZIP containers — XLSX and ODS)
# =============================================================================


class TestArchiveBombGuard:
    """ZIP containers with bomb indicators should raise 400."""

    def test_too_many_zip_entries(self):
        """ZIP with >10,000 entries."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(MAX_ZIP_ENTRIES + 1):
                zf.writestr(f"file_{i}.txt", "data")

        with pytest.raises(HTTPException) as exc_info:
            _validate_xlsx_archive(buf.getvalue(), "bomb.xlsx")
        assert exc_info.value.status_code == 400
        assert "entries" in exc_info.value.detail.lower()

    def test_high_compression_ratio(self):
        """ZIP with compression ratio > 100:1."""
        buf = io.BytesIO()
        # Highly compressible data — repeated zeros
        big_data = b"\x00" * (10 * 1024 * 1024)  # 10MB of zeros
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("big.xml", big_data)

        # Verify the ratio would trip the guard
        with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as zf:
            entries = zf.infolist()
            total_c = sum(e.compress_size for e in entries)
            total_u = sum(e.file_size for e in entries)
            if total_c > 0 and total_u / total_c > 100:
                with pytest.raises(HTTPException) as exc_info:
                    _validate_xlsx_archive(buf.getvalue(), "highratio.xlsx")
                assert exc_info.value.status_code == 400
            else:
                pytest.skip("Compression ratio not high enough to trigger guard")

    def test_nested_archive_rejected(self):
        """ZIP containing another .zip file."""
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as zf:
            zf.writestr("inner.txt", "data")

        outer = io.BytesIO()
        with zipfile.ZipFile(outer, "w") as zf:
            zf.writestr("nested.zip", inner.getvalue())

        with pytest.raises(HTTPException) as exc_info:
            _validate_xlsx_archive(outer.getvalue(), "nested.xlsx")
        assert exc_info.value.status_code == 400
        assert "nested" in exc_info.value.detail.lower()

    def test_bad_zip_file(self):
        """Not a valid ZIP at all (should raise 400 from BadZipFile handler)."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_xlsx_archive(b"not a zip", "notzip.xlsx")
        assert exc_info.value.status_code == 400

    def test_xml_bomb_in_xlsx(self):
        """XLSX with <!DOCTYPE> in an XML entry."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("xl/workbook.xml", '<?xml version="1.0"?><!DOCTYPE foo><root/>')

        with pytest.raises(HTTPException) as exc_info:
            _validate_xlsx_archive(buf.getvalue(), "xmlbomb.xlsx")
        assert exc_info.value.status_code == 400


# =============================================================================
# Zero data rows check
# =============================================================================


class TestZeroDataRowsGuard:
    """Files with headers but no data should raise 400."""

    def test_csv_headers_only(self):
        """CSV with headers but no data rows."""
        content = b"Account,Balance\n"

        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(content, "headersonly.csv")
        assert exc_info.value.status_code == 400
        assert "no data rows" in exc_info.value.detail.lower()
