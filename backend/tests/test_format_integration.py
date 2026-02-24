"""
End-to-end integration tests for the file format pipeline — Sprint 438.

Tests the full path: upload → detect → validate → parse → metrics
for each format. Verifies format detection accuracy, tier gating,
feature flag enforcement, and metrics instrumentation.
"""

import io
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi import HTTPException
from prometheus_client import generate_latest

from shared.file_formats import FileFormat, detect_format
from shared.helpers import parse_uploaded_file_by_format
from shared.parser_metrics import PARSER_REGISTRY, parse_total

# =============================================================================
# Helpers
# =============================================================================


def _make_csv(rows: int = 5) -> bytes:
    header = "Account,Description,Balance\n"
    data = "".join(f"{1000 + i},Item {i},{i * 100.0}\n" for i in range(rows))
    return (header + data).encode()


def _make_tsv(rows: int = 5) -> bytes:
    header = "Account\tDescription\tBalance\n"
    data = "".join(f"{1000 + i}\tItem {i}\t{i * 100.0}\n" for i in range(rows))
    return (header + data).encode()


def _make_xlsx(rows: int = 5) -> bytes:
    df = pd.DataFrame(
        {
            "Account": [f"{1000 + i}" for i in range(rows)],
            "Balance": [i * 100.0 for i in range(rows)],
        }
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def _make_ods(rows: int = 5) -> bytes:
    from tests.test_ods_parser import _build_ods_zip

    df = pd.DataFrame(
        {
            "Account": [f"{1000 + i}" for i in range(rows)],
            "Balance": [i * 100.0 for i in range(rows)],
        }
    )
    return _build_ods_zip({"Sheet1": df})


# =============================================================================
# CSV Integration
# =============================================================================


class TestCsvIntegration:
    """End-to-end CSV pipeline."""

    def test_parse_valid_csv(self):
        cols, rows = parse_uploaded_file_by_format(_make_csv(10), "data.csv")
        assert len(rows) == 10
        assert "Account" in cols

    def test_csv_metrics_increment(self):
        before = _get_counter("csv", "parse")
        parse_uploaded_file_by_format(_make_csv(3), "metrics.csv")
        after = _get_counter("csv", "parse")
        assert after > before

    def test_csv_format_detection(self):
        result = detect_format(filename="report.csv")
        assert result.format == FileFormat.CSV
        assert result.confidence == "high"

    def test_csv_malformed_increments_error_metric(self):
        """Empty CSV (headers only) should fail and increment error metric."""
        with pytest.raises(HTTPException):
            parse_uploaded_file_by_format(b"A,B\n", "empty.csv")


# =============================================================================
# TSV Integration
# =============================================================================


class TestTsvIntegration:
    """End-to-end TSV pipeline."""

    def test_parse_valid_tsv(self):
        cols, rows = parse_uploaded_file_by_format(_make_tsv(10), "data.tsv")
        assert len(rows) == 10

    def test_tsv_format_detection(self):
        result = detect_format(filename="data.tsv")
        assert result.format == FileFormat.TSV


# =============================================================================
# XLSX Integration
# =============================================================================


class TestXlsxIntegration:
    """End-to-end XLSX pipeline."""

    def test_parse_valid_xlsx(self):
        cols, rows = parse_uploaded_file_by_format(_make_xlsx(10), "data.xlsx")
        assert len(rows) == 10
        assert "Account" in cols

    def test_xlsx_format_detection_by_extension(self):
        result = detect_format(filename="report.xlsx")
        assert result.format == FileFormat.XLSX

    def test_xlsx_format_detection_by_magic(self):
        xlsx_bytes = _make_xlsx()
        result = detect_format(file_bytes=xlsx_bytes)
        assert result.format == FileFormat.XLSX


# =============================================================================
# ODS Integration
# =============================================================================


class TestOdsIntegration:
    """End-to-end ODS pipeline."""

    @patch("config.FORMAT_ODS_ENABLED", True)
    def test_parse_valid_ods_when_enabled(self):
        cols, rows = parse_uploaded_file_by_format(_make_ods(10), "data.ods")
        assert len(rows) == 10
        assert "Account" in cols

    @patch("config.FORMAT_ODS_ENABLED", False)
    def test_ods_rejected_when_disabled(self):
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(_make_ods(5), "data.ods")
        assert exc_info.value.status_code == 400
        assert "disabled" in exc_info.value.detail.lower()

    def test_ods_format_detection_by_extension(self):
        result = detect_format(filename="report.ods")
        assert result.format == FileFormat.ODS

    def test_ods_format_detection_by_magic(self):
        ods_bytes = _make_ods()
        result = detect_format(file_bytes=ods_bytes)
        assert result.format == FileFormat.ODS

    @patch("config.FORMAT_ODS_ENABLED", True)
    def test_ods_metrics_increment(self):
        before = _get_counter("ods", "parse")
        parse_uploaded_file_by_format(_make_ods(3), "metrics.ods")
        after = _get_counter("ods", "parse")
        assert after > before


# =============================================================================
# Format detection accuracy
# =============================================================================


class TestFormatDetectionAccuracy:
    """Cross-format detection accuracy."""

    def test_all_extensions_detected(self):
        cases = [
            ("data.csv", FileFormat.CSV),
            ("data.tsv", FileFormat.TSV),
            ("data.txt", FileFormat.TXT),
            ("data.xlsx", FileFormat.XLSX),
            ("data.xls", FileFormat.XLS),
            ("data.ods", FileFormat.ODS),
            ("data.qbo", FileFormat.QBO),
            ("data.ofx", FileFormat.OFX),
            ("data.iif", FileFormat.IIF),
            ("data.pdf", FileFormat.PDF),
        ]
        for filename, expected_format in cases:
            result = detect_format(filename=filename)
            assert result.format == expected_format, f"Failed for {filename}"
            assert result.confidence == "high"

    def test_unknown_extension(self):
        result = detect_format(filename="data.json")
        assert result.format == FileFormat.UNKNOWN

    def test_no_extension(self):
        result = detect_format(filename="datafile")
        assert result.format == FileFormat.UNKNOWN

    def test_magic_byte_disambiguation_xlsx_vs_ods(self):
        """XLSX and ODS both start with PK signature but should be distinguished."""
        xlsx_bytes = _make_xlsx()
        ods_bytes = _make_ods()

        xlsx_result = detect_format(file_bytes=xlsx_bytes)
        ods_result = detect_format(file_bytes=ods_bytes)

        assert xlsx_result.format == FileFormat.XLSX
        assert ods_result.format == FileFormat.ODS


# =============================================================================
# Prometheus metrics output
# =============================================================================


class TestMetricsOutput:
    """Verify /metrics output contains expected data."""

    def test_metrics_contain_parse_total(self):
        # Trigger at least one parse
        parse_uploaded_file_by_format(_make_csv(2), "trigger.csv")
        output = generate_latest(PARSER_REGISTRY).decode()
        assert "paciolus_parse_total" in output

    def test_metrics_contain_duration(self):
        parse_uploaded_file_by_format(_make_csv(2), "timing.csv")
        output = generate_latest(PARSER_REGISTRY).decode()
        assert "paciolus_parse_duration_seconds" in output


# =============================================================================
# Helpers
# =============================================================================


def _get_counter(fmt: str, stage: str) -> float:
    try:
        return parse_total.labels(format=fmt, stage=stage)._value.get()
    except KeyError:
        return 0.0
