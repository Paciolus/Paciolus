"""Sprint 671 Issue 14 — format dispatch + currency stripping for non-CSV/Excel."""

from __future__ import annotations

import pandas as pd

from security_utils import _strip_currency_formatting, process_tb_chunked


class TestStripCurrencyFormatting:
    def test_plain_number(self):
        assert _strip_currency_formatting("100") == "100"

    def test_thousands_separator(self):
        assert _strip_currency_formatting("1,234") == "1234"

    def test_decimal_with_thousands(self):
        assert _strip_currency_formatting("284,500.00") == "284500.00"

    def test_dollar_sign(self):
        assert _strip_currency_formatting("$284,500.00") == "284500.00"

    def test_pound_sign(self):
        assert _strip_currency_formatting("£1,234.56") == "1234.56"

    def test_euro_sign(self):
        assert _strip_currency_formatting("€1,234.56") == "1234.56"

    def test_parenthesised_negative(self):
        assert _strip_currency_formatting("(1,234.56)") == "-1234.56"

    def test_parenthesised_negative_with_dollar(self):
        assert _strip_currency_formatting("$(1,234.56)") == "-1234.56"

    def test_text_unchanged(self):
        """Account names with commas survive intact."""
        assert _strip_currency_formatting("Cash, Operating") == "Cash, Operating"

    def test_dr_indicator_unchanged(self):
        """The Dr/Cr indicator column must NOT be stripped."""
        assert _strip_currency_formatting("Dr") == "Dr"
        assert _strip_currency_formatting("Cr") == "Cr"

    def test_blank_returned_as_is(self):
        assert _strip_currency_formatting("") == ""
        assert _strip_currency_formatting("   ") == "   "

    def test_non_string_returned_as_is(self):
        assert _strip_currency_formatting(None) is None
        assert _strip_currency_formatting(42) == 42

    def test_zero_with_formatting(self):
        assert _strip_currency_formatting("$0.00") == "0.00"


class TestProcessTbChunkedFormatDispatch:
    def test_csv_uses_legacy_path(self):
        """CSV files still use the read_csv_chunked path."""
        csv = b"Account,Debit,Credit\nCash,100,\nAR,50,\n"
        chunks = list(process_tb_chunked(csv, "test.csv"))
        assert len(chunks) >= 1
        df, count = chunks[0]
        assert "Account" in df.columns
        assert count == 2

    def test_tsv_dispatches_to_parser(self):
        """TSV files now route through parse_uploaded_file_by_format."""
        tsv = b"Account\tDebit\tCredit\nCash\t100\t\nAR\t50\t\n"
        chunks = list(process_tb_chunked(tsv, "test.tsv"))
        assert len(chunks) == 1
        df, count = chunks[0]
        assert "Account" in df.columns
        assert count == 2

    def test_currency_stripped_in_dispatched_path(self):
        """Currency-formatted values from non-CSV/Excel must be strippable."""
        # Build a TSV with comma-formatted numbers — these would normally
        # break pd.to_numeric without the Sprint 671 stripping step.
        tsv = b"Account\tDebit\tCredit\nCash\t284,500.00\t\nAR\t45,200.00\t\n"
        chunks = list(process_tb_chunked(tsv, "test.tsv"))
        df, _ = chunks[0]
        debits = pd.to_numeric(df["Debit"], errors="coerce")
        assert debits.sum() == 329700.0  # 284,500 + 45,200

    def test_unknown_extension_falls_back(self):
        """Extension-less files still fall back to CSV/Excel try-then-catch."""
        csv_bytes = b"Account,Debit,Credit\nCash,100,\n"
        chunks = list(process_tb_chunked(csv_bytes, "trial_balance"))
        assert len(chunks) >= 1
