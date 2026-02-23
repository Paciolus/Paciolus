"""
Tests for shared.iif_parser — IIF (Intuit Interchange Format) File Parser.

Tests cover:
- Encoding (UTF-8, Latin-1 fallback)
- Presence validation (no !TRNS -> error, !ACCNT only -> error)
- Section parsing (single block, multi-block, separate TRNS/SPL headers)
- Transaction extraction (amounts, dates, column mapping)
- Date parsing (MM/DD/YYYY, M/D/YYYY, MM/DD/YY, edge cases)
- Metadata extraction (section types, counts, date range, duplicates)
- Block integrity (missing ENDTRNS, malformed row width)
- End-to-end parse_iif (column names, row count, dtypes)
- Security (binary content rejection via presence validation)
"""

import pytest
from fastapi import HTTPException

from shared.iif_parser import (
    IifMetadata,
    _decode_iif,
    _parse_iif_date,
    _parse_sections,
    _project_transactions,
    _validate_iif_presence,
    parse_iif,
)

# =============================================================================
# FIXTURES
# =============================================================================

MINIMAL_IIF = """\
!TRNS\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME
!SPL\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME
!ENDTRNS
TRNS\tGENERAL JOURNAL\t01/15/2024\tCash\t1000.00\t1001\tJanuary rent\tAcme Corp
SPL\tGENERAL JOURNAL\t01/15/2024\tRent Expense\t-1000.00\t1001\tJanuary rent\tAcme Corp
ENDTRNS
"""

MULTI_BLOCK_IIF = """\
!TRNS\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME
!SPL\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME
!ENDTRNS
TRNS\tGENERAL JOURNAL\t01/15/2024\tCash\t1000.00\t1001\tJanuary rent\tAcme Corp
SPL\tGENERAL JOURNAL\t01/15/2024\tRent Expense\t-1000.00\t1001\tJanuary rent\tAcme Corp
ENDTRNS
TRNS\tINVOICE\t02/20/2024\tAccounts Receivable\t5000.00\t2001\tFeb invoice\tWidget Co
SPL\tINVOICE\t02/20/2024\tRevenue\t-5000.00\t2001\tFeb invoice\tWidget Co
ENDTRNS
TRNS\tCHECK\t03/10/2024\tAccounts Payable\t-750.50\t3001\tSupplier payment\tSupply Inc
SPL\tCHECK\t03/10/2024\tCash\t750.50\t3001\tSupplier payment\tSupply Inc
ENDTRNS
"""

ACCNT_ONLY_IIF = """\
!ACCNT\tNAME\tACCNTTYPE\tDESC
ACCNT\tCash\tBANK\tMain checking account
ACCNT\tRent Expense\tEXP\tOffice rent
"""

MALFORMED_IIF = """\
!TRNS\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME
!SPL\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME
!ENDTRNS
TRNS\tGENERAL JOURNAL\t01/15/2024\tCash\t1000.00\t1001\tJanuary rent\tAcme Corp
SPL\tGENERAL JOURNAL\t01/15/2024\tRent Expense
ENDTRNS
TRNS\tCHECK\t02/01/2024\tCash\t-500.00\t2001\tPayment\tVendor
SPL\tCHECK\t02/01/2024\tExpenses\t500.00\t2001\tPayment\tVendor
ENDTRNS
"""


# =============================================================================
# ENCODING
# =============================================================================


class TestIifEncoding:
    """Tests for _decode_iif encoding detection."""

    def test_utf8_decoded(self):
        content = "!TRNS\tDATE\nTRNS\t01/01/2024\n".encode("utf-8")
        text, enc = _decode_iif(content, "test.iif")
        assert "!TRNS" in text
        assert enc == "utf-8"

    def test_latin1_fallback(self):
        content = "!TRNS\tDATE\nTRNS\tCaf\xe9\n".encode("latin-1")
        text, enc = _decode_iif(content, "test.iif")
        assert "Caf" in text
        assert enc == "latin-1"

    def test_utf8_bom_decoded(self):
        content = b"\xef\xbb\xbf!TRNS\tDATE\nTRNS\t01/01/2024\n"
        text, enc = _decode_iif(content, "test.iif")
        assert "!TRNS" in text
        assert enc == "utf-8"


# =============================================================================
# PRESENCE VALIDATION
# =============================================================================


class TestIifPresenceValidation:
    """Tests for _validate_iif_presence."""

    def test_valid_trns_header(self):
        """File with !TRNS should pass validation."""
        _validate_iif_presence("!TRNS\tDATE\tACCNT\n", "test.iif")

    def test_valid_spl_header(self):
        """File with !SPL should pass validation."""
        _validate_iif_presence("!SPL\tDATE\tACCNT\n", "test.iif")

    def test_no_transaction_headers_rejected(self):
        """File without !TRNS or !SPL should be rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_iif_presence("!ACCNT\tNAME\tTYPE\n", "test.iif")
        assert exc_info.value.status_code == 400
        assert "does not contain transaction data" in exc_info.value.detail

    def test_empty_content_rejected(self):
        """Empty content should be rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_iif_presence("", "test.iif")
        assert exc_info.value.status_code == 400

    def test_case_insensitive(self):
        """Header detection should be case-insensitive."""
        _validate_iif_presence("!trns\tDATE\n", "test.iif")

    def test_accnt_only_rejected(self):
        """File with only !ACCNT (no transactions) should be rejected."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_iif_presence(ACCNT_ONLY_IIF, "test.iif")
        assert exc_info.value.status_code == 400
        assert "QuickBooks" in exc_info.value.detail


# =============================================================================
# DATE PARSING
# =============================================================================


class TestIifDateParsing:
    """Tests for _parse_iif_date."""

    def test_standard_format(self):
        assert _parse_iif_date("01/15/2024") == "2024-01-15"

    def test_single_digit_month_day(self):
        assert _parse_iif_date("1/5/2024") == "2024-01-05"

    def test_two_digit_year_2000s(self):
        assert _parse_iif_date("12/31/24") == "2024-12-31"

    def test_two_digit_year_1900s(self):
        assert _parse_iif_date("06/15/98") == "1998-06-15"

    def test_empty_string(self):
        assert _parse_iif_date("") == ""

    def test_none_like_empty(self):
        assert _parse_iif_date("  ") == ""

    def test_invalid_format_returns_raw(self):
        assert _parse_iif_date("2024-01-15") == "2024-01-15"

    def test_invalid_month_returns_raw(self):
        assert _parse_iif_date("13/01/2024") == "13/01/2024"

    def test_invalid_day_returns_raw(self):
        assert _parse_iif_date("01/32/2024") == "01/32/2024"

    def test_non_numeric_returns_raw(self):
        assert _parse_iif_date("Jan/15/2024") == "Jan/15/2024"


# =============================================================================
# SECTION PARSING
# =============================================================================


class TestIifSectionParsing:
    """Tests for _parse_sections."""

    def test_single_block(self):
        lines = MINIMAL_IIF.splitlines()
        transactions, metadata = _parse_sections(lines)
        assert len(transactions) == 2
        assert metadata.transaction_block_count == 1

    def test_multi_block(self):
        lines = MULTI_BLOCK_IIF.splitlines()
        transactions, metadata = _parse_sections(lines)
        assert len(transactions) == 6
        assert metadata.transaction_block_count == 3

    def test_trns_and_spl_separated(self):
        lines = MINIMAL_IIF.splitlines()
        transactions, _ = _parse_sections(lines)
        assert transactions[0]["_LINE_TYPE"] == "TRNS"
        assert transactions[1]["_LINE_TYPE"] == "SPL"

    def test_block_id_assigned(self):
        lines = MULTI_BLOCK_IIF.splitlines()
        transactions, _ = _parse_sections(lines)
        # First block
        assert transactions[0]["_BLOCK_ID"] == 1
        assert transactions[1]["_BLOCK_ID"] == 1
        # Second block
        assert transactions[2]["_BLOCK_ID"] == 2
        assert transactions[3]["_BLOCK_ID"] == 2
        # Third block
        assert transactions[4]["_BLOCK_ID"] == 3
        assert transactions[5]["_BLOCK_ID"] == 3

    def test_malformed_row_skipped(self):
        lines = MALFORMED_IIF.splitlines()
        transactions, metadata = _parse_sections(lines)
        # SPL row in first block has wrong field count -> skipped
        assert metadata.malformed_row_count == 1
        # Should still parse the valid rows (TRNS from block 1 + both from block 2)
        assert len(transactions) == 3

    def test_section_types_tracked(self):
        lines = MINIMAL_IIF.splitlines()
        _, metadata = _parse_sections(lines)
        assert "TRNS" in metadata.section_types_found
        assert "SPL" in metadata.section_types_found

    def test_accnt_section_tracked(self):
        combined = ACCNT_ONLY_IIF + "\n" + MINIMAL_IIF
        lines = combined.splitlines()
        _, metadata = _parse_sections(lines)
        assert "ACCNT" in metadata.section_types_found
        assert metadata.account_list_count == 2

    def test_no_headers_all_malformed(self):
        """TRNS data without !TRNS header should count as malformed."""
        lines = ["TRNS\tGENERAL JOURNAL\t01/01/2024\tCash\t100"]
        transactions, metadata = _parse_sections(lines)
        assert len(transactions) == 0
        assert metadata.malformed_row_count == 1


# =============================================================================
# TRANSACTION PROJECTION
# =============================================================================


class TestIifTransactionProjection:
    """Tests for _project_transactions."""

    def test_column_mapping(self):
        lines = MINIMAL_IIF.splitlines()
        raw, _ = _parse_sections(lines)
        projected = _project_transactions(raw)
        assert len(projected) == 2
        row = projected[0]
        assert row["Date"] == "2024-01-15"
        assert row["Account"] == "Cash"
        assert row["Amount"] == 1000.00
        assert row["Description"] == "January rent"
        assert row["Reference"] == "1001"
        assert row["Type"] == "GENERAL JOURNAL"
        assert row["Name"] == "Acme Corp"
        assert row["Line_Type"] == "TRNS"
        assert row["Block_ID"] == 1

    def test_negative_amount(self):
        lines = MINIMAL_IIF.splitlines()
        raw, _ = _parse_sections(lines)
        projected = _project_transactions(raw)
        assert projected[1]["Amount"] == -1000.00

    def test_invalid_amount_becomes_none(self):
        raw = [
            {
                "AMOUNT": "not_a_number",
                "DATE": "",
                "ACCNT": "",
                "MEMO": "",
                "DOCNUM": "",
                "TRNSTYPE": "",
                "NAME": "",
                "_LINE_TYPE": "TRNS",
                "_BLOCK_ID": 1,
            }
        ]
        projected = _project_transactions(raw)
        assert projected[0]["Amount"] is None

    def test_missing_fields_default_empty(self):
        raw = [{"_LINE_TYPE": "TRNS", "_BLOCK_ID": 1}]
        projected = _project_transactions(raw)
        assert projected[0]["Date"] == ""
        assert projected[0]["Account"] == ""
        assert projected[0]["Amount"] is None


# =============================================================================
# METADATA EXTRACTION
# =============================================================================


class TestIifMetadataExtraction:
    """Tests for metadata gathered during parsing."""

    def test_date_range(self):
        lines = MULTI_BLOCK_IIF.splitlines()
        _, metadata = _parse_sections(lines)
        assert metadata.date_range_start == "2024-01-15"
        assert metadata.date_range_end == "2024-03-10"

    def test_transaction_counts(self):
        lines = MULTI_BLOCK_IIF.splitlines()
        _, metadata = _parse_sections(lines)
        assert metadata.transaction_block_count == 3
        assert metadata.transaction_row_count == 6

    def test_duplicate_references_detected(self):
        iif_with_dupes = """\
!TRNS\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME
!SPL\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME
!ENDTRNS
TRNS\tGENERAL JOURNAL\t01/15/2024\tCash\t100\t1001\tTest\tVendor
SPL\tGENERAL JOURNAL\t01/15/2024\tExpense\t-100\t1001\tTest\tVendor
ENDTRNS
TRNS\tGENERAL JOURNAL\t01/16/2024\tCash\t200\t1001\tDupe ref\tVendor
SPL\tGENERAL JOURNAL\t01/16/2024\tExpense\t-200\t1001\tDupe ref\tVendor
ENDTRNS
"""
        lines = iif_with_dupes.splitlines()
        _, metadata = _parse_sections(lines)
        assert "1001" in metadata.duplicate_references

    def test_expected_duplicates_in_multi_block(self):
        """In IIF, TRNS and SPL rows in same block share DOCNUM — these are expected duplicates."""
        lines = MULTI_BLOCK_IIF.splitlines()
        _, metadata = _parse_sections(lines)
        # Each block has TRNS+SPL sharing the same DOCNUM, so all refs appear twice
        assert "1001" in metadata.duplicate_references
        assert "2001" in metadata.duplicate_references
        assert "3001" in metadata.duplicate_references

    def test_metadata_is_frozen(self):
        metadata = IifMetadata()
        with pytest.raises(AttributeError):
            metadata.encoding = "ascii"  # type: ignore[misc]


# =============================================================================
# END-TO-END parse_iif
# =============================================================================


class TestParseIifEndToEnd:
    """Tests for the parse_iif entry point."""

    def test_minimal_iif_columns(self):
        df = parse_iif(MINIMAL_IIF.encode("utf-8"), "test.iif")
        expected_cols = [
            "Date",
            "Account",
            "Amount",
            "Description",
            "Reference",
            "Type",
            "Name",
            "Line_Type",
            "Block_ID",
        ]
        assert list(df.columns) == expected_cols

    def test_minimal_iif_row_count(self):
        df = parse_iif(MINIMAL_IIF.encode("utf-8"), "test.iif")
        assert len(df) == 2

    def test_multi_block_row_count(self):
        df = parse_iif(MULTI_BLOCK_IIF.encode("utf-8"), "test.iif")
        assert len(df) == 6

    def test_amount_values(self):
        df = parse_iif(MINIMAL_IIF.encode("utf-8"), "test.iif")
        amounts = df["Amount"].tolist()
        assert 1000.00 in amounts
        assert -1000.00 in amounts

    def test_date_values(self):
        df = parse_iif(MINIMAL_IIF.encode("utf-8"), "test.iif")
        dates = df["Date"].tolist()
        assert "2024-01-15" in dates

    def test_metadata_attached(self):
        df = parse_iif(MINIMAL_IIF.encode("utf-8"), "test.iif")
        metadata = df.attrs.get("iif_metadata")
        assert metadata is not None
        assert isinstance(metadata, IifMetadata)
        assert metadata.transaction_block_count == 1
        assert metadata.transaction_row_count == 2

    def test_no_transactions_rejected(self):
        """IIF with headers but no data rows should raise."""
        content = "!TRNS\tDATE\tACCNT\n!SPL\tDATE\tACCNT\n!ENDTRNS\n"
        with pytest.raises(HTTPException) as exc_info:
            parse_iif(content.encode("utf-8"), "empty.iif")
        assert exc_info.value.status_code == 400
        assert "no transaction data" in exc_info.value.detail.lower()

    def test_accnt_only_rejected(self):
        """File with only account list (no transactions) should raise."""
        with pytest.raises(HTTPException) as exc_info:
            parse_iif(ACCNT_ONLY_IIF.encode("utf-8"), "accounts.iif")
        assert exc_info.value.status_code == 400

    def test_latin1_file_parsed(self):
        content = "!TRNS\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME\n"
        content += "!SPL\tTRNSTYPE\tDATE\tACCNT\tAMOUNT\tDOCNUM\tMEMO\tNAME\n"
        content += "!ENDTRNS\n"
        content += "TRNS\tGENERAL JOURNAL\t01/01/2024\tCaf\xe9\t100\t1\tTest\tV\n"
        content += "ENDTRNS\n"
        df = parse_iif(content.encode("latin-1"), "latin.iif")
        assert len(df) == 1
        assert "Caf" in df.iloc[0]["Account"]

    def test_malformed_rows_still_parses_valid(self):
        df = parse_iif(MALFORMED_IIF.encode("utf-8"), "malformed.iif")
        metadata = df.attrs.get("iif_metadata")
        assert metadata.malformed_row_count == 1
        assert len(df) == 3  # 1 TRNS from block 1 + 2 from block 2

    def test_block_id_in_dataframe(self):
        df = parse_iif(MULTI_BLOCK_IIF.encode("utf-8"), "test.iif")
        block_ids = df["Block_ID"].unique().tolist()
        assert 1 in block_ids
        assert 2 in block_ids
        assert 3 in block_ids

    def test_line_type_in_dataframe(self):
        df = parse_iif(MINIMAL_IIF.encode("utf-8"), "test.iif")
        line_types = df["Line_Type"].tolist()
        assert "TRNS" in line_types
        assert "SPL" in line_types


# =============================================================================
# SECURITY
# =============================================================================


class TestIifSecurity:
    """Tests for security-related validations."""

    def test_binary_content_rejected(self):
        """Binary file content (no IIF headers) should be rejected."""
        content = b"\x00\x01\x02\x03\x04\x05" * 100
        with pytest.raises(HTTPException) as exc_info:
            parse_iif(content, "binary.iif")
        assert exc_info.value.status_code == 400

    def test_empty_file_rejected(self):
        """Empty file should be rejected."""
        with pytest.raises(HTTPException) as exc_info:
            parse_iif(b"", "empty.iif")
        assert exc_info.value.status_code == 400
