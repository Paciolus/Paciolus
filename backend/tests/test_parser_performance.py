"""
Tests for parser performance baselines — Sprint 434.

Marked with @pytest.mark.slow for CI filtering.
Asserts parse time < threshold for each format.
"""

import io
import time

import pandas as pd
import pytest

from shared.helpers import parse_uploaded_file_by_format


def _build_csv_fixture(rows: int = 1000) -> bytes:
    """Build a CSV fixture with the given number of rows."""
    header = "Account,Description,Debit,Credit\n"
    lines = [f"{1000 + i},Line item {i},{i * 10.5},{i * 5.25}\n" for i in range(rows)]
    return (header + "".join(lines)).encode()


def _build_tsv_fixture(rows: int = 1000) -> bytes:
    """Build a TSV fixture with the given number of rows."""
    header = "Account\tDescription\tDebit\tCredit\n"
    lines = [f"{1000 + i}\tLine item {i}\t{i * 10.5}\t{i * 5.25}\n" for i in range(rows)]
    return (header + "".join(lines)).encode()


def _build_xlsx_fixture(rows: int = 1000) -> bytes:
    """Build an XLSX fixture with the given number of rows."""
    df = pd.DataFrame(
        {
            "Account": [f"{1000 + i}" for i in range(rows)],
            "Description": [f"Line item {i}" for i in range(rows)],
            "Debit": [i * 10.5 for i in range(rows)],
            "Credit": [i * 5.25 for i in range(rows)],
        }
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def _build_ods_fixture(rows: int = 1000) -> bytes:
    """Build an ODS fixture with the given number of rows."""
    from tests.test_ods_parser import _build_ods_zip

    df = pd.DataFrame(
        {
            "Account": [f"{1000 + i}" for i in range(rows)],
            "Description": [f"Line item {i}" for i in range(rows)],
            "Debit": [i * 10.5 for i in range(rows)],
            "Credit": [i * 5.25 for i in range(rows)],
        }
    )
    return _build_ods_zip({"Sheet1": df})


@pytest.mark.slow
class TestParserPerformance:
    """Performance baseline tests — parse 1000-row fixtures under threshold."""

    def test_csv_performance(self):
        """CSV 1000 rows should parse in < 5 seconds."""
        content = _build_csv_fixture(1000)
        start = time.perf_counter()
        cols, rows = parse_uploaded_file_by_format(content, "perf.csv")
        elapsed = time.perf_counter() - start
        assert len(rows) == 1000
        assert elapsed < 5.0, f"CSV parse took {elapsed:.2f}s (threshold: 5s)"

    def test_tsv_performance(self):
        """TSV 1000 rows should parse in < 5 seconds."""
        content = _build_tsv_fixture(1000)
        start = time.perf_counter()
        cols, rows = parse_uploaded_file_by_format(content, "perf.tsv")
        elapsed = time.perf_counter() - start
        assert len(rows) == 1000
        assert elapsed < 5.0, f"TSV parse took {elapsed:.2f}s (threshold: 5s)"

    def test_txt_performance(self):
        """TXT (tab-delimited) 1000 rows should parse in < 5 seconds."""
        content = _build_tsv_fixture(1000)  # tab-delimited content
        start = time.perf_counter()
        cols, rows = parse_uploaded_file_by_format(content, "perf.txt")
        elapsed = time.perf_counter() - start
        assert len(rows) == 1000
        assert elapsed < 5.0, f"TXT parse took {elapsed:.2f}s (threshold: 5s)"

    def test_xlsx_performance(self):
        """XLSX 1000 rows should parse in < 10 seconds."""
        content = _build_xlsx_fixture(1000)
        start = time.perf_counter()
        cols, rows = parse_uploaded_file_by_format(content, "perf.xlsx")
        elapsed = time.perf_counter() - start
        assert len(rows) == 1000
        assert elapsed < 10.0, f"XLSX parse took {elapsed:.2f}s (threshold: 10s)"

    @pytest.fixture(autouse=True)
    def _enable_ods(self, monkeypatch):
        """Enable ODS format for performance tests."""
        monkeypatch.setattr("config.FORMAT_ODS_ENABLED", True)

    def test_ods_performance(self):
        """ODS 1000 rows should parse in < 10 seconds."""
        content = _build_ods_fixture(1000)
        start = time.perf_counter()
        cols, rows = parse_uploaded_file_by_format(content, "perf.ods")
        elapsed = time.perf_counter() - start
        assert len(rows) == 1000
        assert elapsed < 10.0, f"ODS parse took {elapsed:.2f}s (threshold: 10s)"
