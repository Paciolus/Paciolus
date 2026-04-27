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

from shared.upload_pipeline import (
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
        """ZIP with compression ratio > 100:1 must trip the guard.

        Sprint 655: previously wrapped in `pytest.skip` when zlib didn't
        produce a high-enough ratio — which silently hid the guard in
        constrained CI envs. Now we patch the central directory's
        `file_size` field to a value guaranteed to exceed the 100:1
        threshold, so the test is deterministic regardless of the host
        compression library's behaviour.
        """
        buf = io.BytesIO()
        # Minimal deflate-compressed entry — the actual payload is small
        # but we overwrite the central directory size in the next step.
        real_data = b"\x00" * 256
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("big.xml", real_data)

        raw = bytearray(buf.getvalue())

        # End-of-central-directory signature: 0x06054b50 (little-endian).
        eocd_sig = b"\x50\x4b\x05\x06"
        eocd_offset = raw.rfind(eocd_sig)
        assert eocd_offset != -1, "EOCD signature not found — malformed ZIP fixture"

        # EOCD layout: the central directory start offset lives at
        # bytes 16-20 (unsigned 32-bit little-endian) of the EOCD record.
        cd_offset = int.from_bytes(raw[eocd_offset + 16 : eocd_offset + 20], "little")

        # Central directory header layout (first entry):
        #   bytes  0- 3  signature 0x02014b50
        #   bytes 20-24  compressed size      (uint32 LE)
        #   bytes 24-28  uncompressed size    (uint32 LE)
        cd_sig = b"\x50\x4b\x01\x02"
        assert bytes(raw[cd_offset : cd_offset + 4]) == cd_sig, "central directory header mismatch"

        # Overwrite uncompressed size with a 10 MB value so the ratio is
        # guaranteed >> 100:1 whatever the real compressed size is.
        ten_megabytes = (10 * 1024 * 1024).to_bytes(4, "little")
        raw[cd_offset + 24 : cd_offset + 28] = ten_megabytes

        patched = bytes(raw)

        # Sanity check the patched bytes produce the ratio we expect.
        with zipfile.ZipFile(io.BytesIO(patched)) as zf:
            entries = zf.infolist()
            total_c = sum(e.compress_size for e in entries)
            total_u = sum(e.file_size for e in entries)
            assert total_c > 0, "deflate stream should have non-zero compressed size"
            assert total_u / total_c > 100, (
                f"synthetic fixture produced ratio {total_u / total_c:.1f}:1, "
                "but the test requires >100:1 to exercise the guard"
            )

        with pytest.raises(HTTPException) as exc_info:
            _validate_xlsx_archive(patched, "highratio.xlsx")
        assert exc_info.value.status_code == 400
        assert "compression ratio" in exc_info.value.detail.lower()

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
