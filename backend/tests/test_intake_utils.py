"""Tests for shared.intake_utils (Sprint 666).

Covers:
- count_raw_data_rows for CSV / TSV / TXT / non-text formats
- detect_totals_row heuristic
- IntakeSummary reconciliation invariant
"""

from __future__ import annotations

from shared.intake_utils import (
    IntakeSummary,
    count_raw_data_rows,
    detect_totals_row,
    exclude_totals_row,
)


class TestCountRawDataRows:
    """count_raw_data_rows returns total non-empty lines for text formats."""

    def test_csv_counts_header_and_data(self):
        data = b"Account,Debit,Credit\n1010,100,\n1020,200,\n2010,,300\n"
        assert count_raw_data_rows(data, "test.csv") == 4

    def test_csv_skips_blank_lines(self):
        data = b"Account,Debit,Credit\n\n1010,100,\n\n\n2010,,300\n\n"
        assert count_raw_data_rows(data, "test.csv") == 3

    def test_tsv_counted(self):
        data = b"Account\tDebit\tCredit\n1010\t100\t\n"
        assert count_raw_data_rows(data, "test.tsv") == 2

    def test_txt_counted(self):
        data = b"Account|Debit|Credit\n1010|100|\n"
        assert count_raw_data_rows(data, "test.txt") == 2

    def test_xlsx_returns_none(self):
        # Raw byte count is not meaningful for binary formats.
        data = b"PK\x03\x04garbage"
        assert count_raw_data_rows(data, "test.xlsx") is None

    def test_pdf_returns_none(self):
        assert count_raw_data_rows(b"%PDF-1.4", "test.pdf") is None

    def test_docx_returns_none(self):
        assert count_raw_data_rows(b"PK\x03\x04", "test.docx") is None

    def test_missing_filename_returns_none(self):
        assert count_raw_data_rows(b"anything", None) is None

    def test_filename_without_extension_returns_none(self):
        assert count_raw_data_rows(b"anything", "noext") is None

    def test_empty_file_returns_zero(self):
        assert count_raw_data_rows(b"", "test.csv") == 0

    def test_latin_1_fallback(self):
        # Latin-1 encoded non-ASCII bytes should decode via the fallback.
        data = "Account,Debit,Credit\nCafé,100,\n".encode("latin-1")
        assert count_raw_data_rows(data, "test.csv") == 2


class TestDetectTotalsRow:
    """detect_totals_row identifies end-of-file summary rows."""

    def test_detects_blank_name_with_both_sides(self):
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": None},
            {"Account Name": "AP", "Debit": None, "Credit": 1000},
            {"Account Name": "", "Debit": 1000, "Credit": 1000},  # totals
        ]
        cols = ["Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, "Debit", "Credit") == 2

    def test_rejects_blank_name_with_one_side(self):
        # Row with blank name but only debit populated is a legitimate
        # data row (e.g. an account identified only by its number).
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": None},
            {"Account Name": "", "Debit": 500, "Credit": None},
        ]
        cols = ["Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, "Debit", "Credit") is None

    def test_rejects_populated_name_with_both_sides(self):
        # Legitimate two-sided accounts (contra-accounts) have non-blank
        # names and must not be flagged as totals rows.
        rows = [
            {"Account Name": "Accumulated Depreciation", "Debit": 500, "Credit": 1000},
        ]
        cols = ["Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, "Debit", "Credit") is None

    def test_scans_only_last_three_rows(self):
        # A totals-shaped row buried mid-file must not be detected —
        # real TBs don't put summary rows in the middle of data.
        rows = [
            {"Account Name": "", "Debit": 1000, "Credit": 1000},  # idx 0
            {"Account Name": "Cash", "Debit": 500, "Credit": None},
            {"Account Name": "AP", "Debit": None, "Credit": 500},
            {"Account Name": "Equity", "Debit": None, "Credit": 500},
            {"Account Name": "Revenue", "Debit": None, "Credit": 500},
        ]
        cols = ["Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, "Debit", "Credit") is None

    def test_handles_multiple_account_id_columns(self):
        # When both Account No and Account Name are present, BOTH must be
        # blank for a row to qualify as totals. A row with blank name but
        # populated account code is a legitimate data row.
        rows = [
            {"Account No": 1010, "Account Name": "Cash", "Debit": 1000, "Credit": None},
            {"Account No": 6055, "Account Name": "", "Debit": 4800, "Credit": None},
            {"Account No": "", "Account Name": "", "Debit": 5000, "Credit": 5800},
        ]
        cols = ["Account No", "Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, "Debit", "Credit") == 2

    def test_nan_treated_as_blank(self):
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": None},
            {"Account Name": float("nan"), "Debit": 1000, "Credit": 1000},
        ]
        cols = ["Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, "Debit", "Credit") == 1

    def test_string_nan_treated_as_blank(self):
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": None},
            {"Account Name": "nan", "Debit": 1000, "Credit": 1000},
        ]
        cols = ["Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, "Debit", "Credit") == 1

    def test_empty_rows_returns_none(self):
        assert detect_totals_row([], [], "Debit", "Credit") is None

    def test_missing_columns_returns_none(self):
        rows = [{"Account Name": "", "Debit": 100, "Credit": 100}]
        cols = ["Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, None, "Credit") is None
        assert detect_totals_row(rows, cols, "Debit", None) is None

    def test_no_id_columns_returns_none(self):
        # Column layout with no account-identifier column is ambiguous;
        # we refuse to guess what's a totals row.
        rows = [{"Col1": "", "Col2": 100, "Col3": 100}]
        cols = ["Col1", "Col2", "Col3"]
        assert detect_totals_row(rows, cols, "Col2", "Col3") is None

    def test_handles_string_currency_values(self):
        rows = [
            {"Account Name": "Cash", "Debit": "1,000.00", "Credit": None},
            {"Account Name": "", "Debit": "$1,000.00", "Credit": "$1,000.00"},
        ]
        cols = ["Account Name", "Debit", "Credit"]
        assert detect_totals_row(rows, cols, "Debit", "Credit") == 1


class TestExcludeTotalsRow:
    """exclude_totals_row removes the detected row and returns the filtered list."""

    def test_excludes_when_detected(self):
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": None},
            {"Account Name": "AP", "Debit": None, "Credit": 1000},
            {"Account Name": "", "Debit": 1000, "Credit": 1000},
        ]
        filtered, idx = exclude_totals_row(rows, ["Account Name", "Debit", "Credit"], "Debit", "Credit")
        assert idx == 2
        assert len(filtered) == 2
        # Original list unchanged
        assert len(rows) == 3

    def test_passthrough_when_not_detected(self):
        rows = [{"Account Name": "Cash", "Debit": 1000, "Credit": None}]
        filtered, idx = exclude_totals_row(rows, ["Account Name", "Debit", "Credit"], "Debit", "Credit")
        assert idx is None
        assert filtered is rows


class TestIntakeSummary:
    """IntakeSummary.reconciles enforces the submitted = accepted + rejected + excluded invariant."""

    def test_reconciles_trivial(self):
        s = IntakeSummary(rows_submitted=40, rows_accepted=40)
        assert s.reconciles() is True

    def test_reconciles_with_totals_exclusion(self):
        s = IntakeSummary(rows_submitted=41, rows_accepted=40, rows_excluded=1)
        assert s.reconciles() is True

    def test_reconciles_with_header_loss(self):
        s = IntakeSummary(rows_submitted=40, rows_accepted=39, rows_rejected=1)
        assert s.reconciles() is True

    def test_does_not_reconcile_on_mismatch(self):
        s = IntakeSummary(rows_submitted=40, rows_accepted=38, rows_rejected=1, rows_excluded=0)
        assert s.reconciles() is False

    def test_to_dict_round_trip(self):
        s = IntakeSummary(
            rows_submitted=41,
            rows_accepted=40,
            rows_excluded=1,
            notes=["Row 41 excluded as totals row"],
        )
        d = s.to_dict()
        assert d["rows_submitted"] == 41
        assert d["rows_accepted"] == 40
        assert d["rows_excluded"] == 1
        assert d["rows_rejected"] == 0
        assert d["reconciles"] is True
        assert d["notes"] == ["Row 41 excluded as totals row"]
