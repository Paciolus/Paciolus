"""
Tests for Bank Reconciliation Engine — Sprint 77

Covers: date parsing, safe float, column detection, transaction parsing,
exact matching, summary calculation, CSV export, main entry, API route.

38 tests across 9 test classes.
"""

from datetime import date

import pytest

from bank_reconciliation import (
    BANK_DATE_PATTERNS,
    BankColumnDetectionResult,
    BankRecConfig,
    BankRecResult,
    BankTransaction,
    LedgerTransaction,
    MatchType,
    ReconciliationMatch,
    ReconciliationSummary,
    calculate_summary,
    detect_bank_columns,
    export_reconciliation_csv,
    match_transactions,
    parse_bank_transactions,
    parse_ledger_transactions,
    reconcile_bank_statement,
)
from shared.column_detector import match_column as _match_bank_column
from shared.parsing_helpers import parse_date as _parse_date
from shared.parsing_helpers import safe_float as _safe_float

# =============================================================================
# DATE PARSING
# =============================================================================

class TestDateParsing:
    """Tests for _parse_date helper."""

    def test_iso_format(self):
        assert _parse_date("2025-01-15") == date(2025, 1, 15)

    def test_us_format(self):
        assert _parse_date("01/15/2025") == date(2025, 1, 15)

    def test_us_dash_format(self):
        assert _parse_date("01-15-2025") == date(2025, 1, 15)

    def test_iso_with_time(self):
        assert _parse_date("2025-01-15 10:30:00") == date(2025, 1, 15)

    def test_iso_with_t_time(self):
        assert _parse_date("2025-01-15T10:30:00") == date(2025, 1, 15)

    def test_invalid_returns_none(self):
        assert _parse_date("not a date") is None

    def test_none_returns_none(self):
        assert _parse_date(None) is None

    def test_empty_returns_none(self):
        assert _parse_date("") is None


# =============================================================================
# SAFE FLOAT
# =============================================================================

class TestSafeFloat:
    """Tests for _safe_float helper."""

    def test_plain_number(self):
        assert _safe_float(1234.56) == 1234.56

    def test_string_number(self):
        assert _safe_float("1234.56") == 1234.56

    def test_currency_format(self):
        assert _safe_float("$1,234.56") == 1234.56

    def test_parentheses_negative(self):
        result = _safe_float("(1234.56)")
        assert result == -1234.56

    def test_empty_string(self):
        assert _safe_float("") == 0.0

    def test_non_numeric(self):
        assert _safe_float("abc") == 0.0

    def test_none(self):
        assert _safe_float(None) == 0.0


# =============================================================================
# COLUMN DETECTION
# =============================================================================

class TestColumnDetection:
    """Tests for detect_bank_columns."""

    def test_standard_headers(self):
        result = detect_bank_columns(["Date", "Description", "Amount", "Reference", "Balance"])
        assert result.date_column == "Date"
        assert result.amount_column == "Amount"
        assert result.description_column == "Description"
        assert result.reference_column == "Reference"
        assert result.balance_column == "Balance"
        assert result.overall_confidence >= 0.90

    def test_alternate_headers(self):
        result = detect_bank_columns(["Transaction Date", "Memo", "Transaction Amount", "Ref No", "Running Balance"])
        assert result.date_column == "Transaction Date"
        assert result.amount_column == "Transaction Amount"
        assert result.description_column == "Memo"
        assert result.reference_column == "Ref No"
        assert result.balance_column == "Running Balance"

    def test_minimal_headers(self):
        """Date and Amount are the required columns."""
        result = detect_bank_columns(["Date", "Amount"])
        assert result.date_column == "Date"
        assert result.amount_column == "Amount"
        assert result.description_column is None
        assert result.overall_confidence >= 0.90

    def test_low_confidence_unrecognized(self):
        result = detect_bank_columns(["Col A", "Col B", "Col C"])
        assert result.overall_confidence < 0.70
        assert result.requires_mapping is True

    def test_to_dict(self):
        result = detect_bank_columns(["Date", "Amount"])
        d = result.to_dict()
        assert "date_column" in d
        assert "amount_column" in d
        assert "overall_confidence" in d
        assert "requires_mapping" in d
        assert "all_columns" in d

    def test_greedy_no_double_assign(self):
        """Ensure each column is assigned only once."""
        result = detect_bank_columns(["Date", "Posting Date", "Amount", "Balance"])
        # Both Date and Posting Date match DATE, but only one should be assigned
        assert result.date_column is not None
        # The other date-like column should not steal amount or balance
        assert result.amount_column == "Amount"
        assert result.balance_column == "Balance"


# =============================================================================
# TRANSACTION PARSING
# =============================================================================

class TestTransactionParsing:
    """Tests for parse_bank_transactions and parse_ledger_transactions."""

    def test_bank_parsing(self):
        detection = BankColumnDetectionResult(
            date_column="Date",
            amount_column="Amount",
            description_column="Description",
            reference_column="Ref",
        )
        rows = [
            {"Date": "2025-01-15", "Amount": 1000.00, "Description": "Deposit", "Ref": "DEP001"},
            {"Date": "2025-01-16", "Amount": -250.50, "Description": "Check #101", "Ref": "CHK101"},
        ]
        txns = parse_bank_transactions(rows, detection)
        assert len(txns) == 2
        assert txns[0].date == "2025-01-15"
        assert txns[0].amount == 1000.00
        assert txns[0].description == "Deposit"
        assert txns[0].reference == "DEP001"
        assert txns[0].row_number == 1
        assert txns[1].amount == -250.50

    def test_ledger_parsing(self):
        detection = BankColumnDetectionResult(
            date_column="GL Date",
            amount_column="Net Amount",
            description_column="Memo",
        )
        rows = [
            {"GL Date": "2025-01-15", "Net Amount": "1,000.00", "Memo": "Cash receipt"},
        ]
        txns = parse_ledger_transactions(rows, detection)
        assert len(txns) == 1
        assert txns[0].date == "2025-01-15"
        assert txns[0].amount == 1000.00
        assert txns[0].description == "Cash receipt"
        assert txns[0].row_number == 1

    def test_empty_rows(self):
        detection = BankColumnDetectionResult(
            date_column="Date",
            amount_column="Amount",
        )
        txns = parse_bank_transactions([], detection)
        assert len(txns) == 0

    def test_to_dict(self):
        txn = BankTransaction(
            date="2025-01-15",
            description="Test",
            amount=100.0,
            reference="REF1",
            row_number=1,
        )
        d = txn.to_dict()
        assert d["date"] == "2025-01-15"
        assert d["amount"] == 100.0
        assert d["reference"] == "REF1"


# =============================================================================
# EXACT MATCHING
# =============================================================================

class TestExactMatching:
    """Tests for match_transactions."""

    def _make_bank(self, date_str, amount, desc="", ref=None, row=1):
        return BankTransaction(date=date_str, amount=amount, description=desc, reference=ref, row_number=row)

    def _make_ledger(self, date_str, amount, desc="", ref=None, row=1):
        return LedgerTransaction(date=date_str, amount=amount, description=desc, reference=ref, row_number=row)

    def test_all_matched(self):
        bank = [self._make_bank("2025-01-15", 1000.0, row=1)]
        ledger = [self._make_ledger("2025-01-15", 1000.0, row=1)]
        matches = match_transactions(bank, ledger)
        matched = [m for m in matches if m.match_type == MatchType.MATCHED]
        assert len(matched) == 1
        assert matched[0].match_confidence == 1.0

    def test_none_matched(self):
        bank = [self._make_bank("2025-01-15", 1000.0, row=1)]
        ledger = [self._make_ledger("2025-01-15", 2000.0, row=1)]
        matches = match_transactions(bank, ledger)
        bank_only = [m for m in matches if m.match_type == MatchType.BANK_ONLY]
        ledger_only = [m for m in matches if m.match_type == MatchType.LEDGER_ONLY]
        assert len(bank_only) == 1
        assert len(ledger_only) == 1

    def test_partial_match(self):
        bank = [
            self._make_bank("2025-01-15", 1000.0, row=1),
            self._make_bank("2025-01-16", 500.0, row=2),
        ]
        ledger = [self._make_ledger("2025-01-15", 1000.0, row=1)]
        matches = match_transactions(bank, ledger)
        matched = [m for m in matches if m.match_type == MatchType.MATCHED]
        bank_only = [m for m in matches if m.match_type == MatchType.BANK_ONLY]
        assert len(matched) == 1
        assert len(bank_only) == 1

    def test_tolerance_edge(self):
        """Amount within tolerance should match."""
        config = BankRecConfig(amount_tolerance=0.01)
        bank = [self._make_bank("2025-01-15", 1000.005, row=1)]
        ledger = [self._make_ledger("2025-01-15", 1000.00, row=1)]
        matches = match_transactions(bank, ledger, config)
        matched = [m for m in matches if m.match_type == MatchType.MATCHED]
        assert len(matched) == 1

    def test_tolerance_exceeded(self):
        """Amount outside tolerance should not match."""
        config = BankRecConfig(amount_tolerance=0.01)
        bank = [self._make_bank("2025-01-15", 1000.02, row=1)]
        ledger = [self._make_ledger("2025-01-15", 1000.00, row=1)]
        matches = match_transactions(bank, ledger, config)
        matched = [m for m in matches if m.match_type == MatchType.MATCHED]
        assert len(matched) == 0

    def test_duplicate_amounts_same_date(self):
        """Two bank txns with same amount and date should match to two different ledger txns."""
        bank = [
            self._make_bank("2025-01-15", 500.0, row=1),
            self._make_bank("2025-01-15", 500.0, row=2),
        ]
        ledger = [
            self._make_ledger("2025-01-15", 500.0, row=1),
            self._make_ledger("2025-01-15", 500.0, row=2),
        ]
        matches = match_transactions(bank, ledger)
        matched = [m for m in matches if m.match_type == MatchType.MATCHED]
        assert len(matched) == 2

    def test_one_to_one(self):
        """Each bank txn matches exactly one ledger txn."""
        bank = [
            self._make_bank("2025-01-15", 100.0, row=1),
            self._make_bank("2025-01-16", 200.0, row=2),
            self._make_bank("2025-01-17", 300.0, row=3),
        ]
        ledger = [
            self._make_ledger("2025-01-15", 100.0, row=1),
            self._make_ledger("2025-01-16", 200.0, row=2),
            self._make_ledger("2025-01-17", 300.0, row=3),
        ]
        matches = match_transactions(bank, ledger)
        matched = [m for m in matches if m.match_type == MatchType.MATCHED]
        assert len(matched) == 3

    def test_empty_inputs(self):
        matches = match_transactions([], [])
        assert len(matches) == 0

    def test_single_bank_no_ledger(self):
        bank = [self._make_bank("2025-01-15", 100.0, row=1)]
        matches = match_transactions(bank, [])
        assert len(matches) == 1
        assert matches[0].match_type == MatchType.BANK_ONLY

    def test_date_tolerance(self):
        """Date tolerance allows matching across days."""
        config = BankRecConfig(date_tolerance_days=2)
        bank = [self._make_bank("2025-01-15", 1000.0, row=1)]
        ledger = [self._make_ledger("2025-01-17", 1000.0, row=1)]
        matches = match_transactions(bank, ledger, config)
        matched = [m for m in matches if m.match_type == MatchType.MATCHED]
        assert len(matched) == 1

    def test_date_tolerance_exceeded(self):
        """Beyond date tolerance should not match."""
        config = BankRecConfig(date_tolerance_days=1)
        bank = [self._make_bank("2025-01-15", 1000.0, row=1)]
        ledger = [self._make_ledger("2025-01-18", 1000.0, row=1)]
        matches = match_transactions(bank, ledger, config)
        matched = [m for m in matches if m.match_type == MatchType.MATCHED]
        assert len(matched) == 0


# =============================================================================
# SUMMARY CALCULATION
# =============================================================================

class TestSummaryCalculation:
    """Tests for calculate_summary."""

    def test_balanced(self):
        matches = [
            ReconciliationMatch(
                bank_txn=BankTransaction(date="2025-01-15", amount=1000.0, row_number=1),
                ledger_txn=LedgerTransaction(date="2025-01-15", amount=1000.0, row_number=1),
                match_type=MatchType.MATCHED,
                match_confidence=1.0,
            ),
        ]
        summary = calculate_summary(matches)
        assert summary.matched_count == 1
        assert summary.matched_amount == 1000.0
        assert summary.bank_only_count == 0
        assert summary.ledger_only_count == 0
        assert summary.reconciling_difference == 0.0

    def test_bank_excess(self):
        matches = [
            ReconciliationMatch(
                bank_txn=BankTransaction(date="2025-01-15", amount=500.0, row_number=1),
                ledger_txn=None,
                match_type=MatchType.BANK_ONLY,
                match_confidence=0.0,
            ),
        ]
        summary = calculate_summary(matches)
        assert summary.bank_only_count == 1
        assert summary.bank_only_amount == 500.0
        assert summary.total_bank == 500.0
        assert summary.total_ledger == 0.0
        assert summary.reconciling_difference == 500.0

    def test_ledger_excess(self):
        matches = [
            ReconciliationMatch(
                bank_txn=None,
                ledger_txn=LedgerTransaction(date="2025-01-15", amount=300.0, row_number=1),
                match_type=MatchType.LEDGER_ONLY,
                match_confidence=0.0,
            ),
        ]
        summary = calculate_summary(matches)
        assert summary.ledger_only_count == 1
        assert summary.ledger_only_amount == 300.0
        assert summary.total_ledger == 300.0
        assert summary.reconciling_difference == -300.0

    def test_mixed(self):
        matches = [
            ReconciliationMatch(
                bank_txn=BankTransaction(date="2025-01-15", amount=1000.0, row_number=1),
                ledger_txn=LedgerTransaction(date="2025-01-15", amount=1000.0, row_number=1),
                match_type=MatchType.MATCHED,
                match_confidence=1.0,
            ),
            ReconciliationMatch(
                bank_txn=BankTransaction(date="2025-01-16", amount=200.0, row_number=2),
                ledger_txn=None,
                match_type=MatchType.BANK_ONLY,
                match_confidence=0.0,
            ),
            ReconciliationMatch(
                bank_txn=None,
                ledger_txn=LedgerTransaction(date="2025-01-17", amount=150.0, row_number=2),
                match_type=MatchType.LEDGER_ONLY,
                match_confidence=0.0,
            ),
        ]
        summary = calculate_summary(matches)
        assert summary.matched_count == 1
        assert summary.bank_only_count == 1
        assert summary.ledger_only_count == 1
        assert summary.total_bank == 1200.0
        assert summary.total_ledger == 1150.0
        assert summary.reconciling_difference == 50.0

    def test_to_dict(self):
        matches = [
            ReconciliationMatch(
                bank_txn=BankTransaction(amount=100.0, row_number=1),
                ledger_txn=LedgerTransaction(amount=100.0, row_number=1),
                match_type=MatchType.MATCHED,
                match_confidence=1.0,
            ),
        ]
        summary = calculate_summary(matches)
        d = summary.to_dict()
        assert "matched_count" in d
        assert "reconciling_difference" in d
        assert "matches" in d
        assert len(d["matches"]) == 1


# =============================================================================
# CSV EXPORT
# =============================================================================

class TestCsvExport:
    """Tests for export_reconciliation_csv."""

    def test_basic_export(self):
        matches = [
            ReconciliationMatch(
                bank_txn=BankTransaction(date="2025-01-15", description="Deposit", amount=1000.0, reference="DEP001", row_number=1),
                ledger_txn=LedgerTransaction(date="2025-01-15", description="Cash receipt", amount=1000.0, reference="JE001", row_number=1),
                match_type=MatchType.MATCHED,
                match_confidence=1.0,
            ),
            ReconciliationMatch(
                bank_txn=BankTransaction(date="2025-01-16", description="Wire", amount=500.0, row_number=2),
                ledger_txn=None,
                match_type=MatchType.BANK_ONLY,
                match_confidence=0.0,
            ),
        ]
        summary = calculate_summary(matches)
        csv_str = export_reconciliation_csv(summary)
        assert "MATCHED ITEMS" in csv_str
        assert "OUTSTANDING DEPOSITS (BANK ONLY)" in csv_str
        assert "OUTSTANDING CHECKS (LEDGER ONLY)" in csv_str
        assert "SUMMARY" in csv_str
        assert "Deposit" in csv_str
        assert "Wire" in csv_str
        assert "1000.00" in csv_str

    def test_empty_sections(self):
        """Export with no matches should still have section headers."""
        summary = ReconciliationSummary(matches=[])
        csv_str = export_reconciliation_csv(summary)
        assert "MATCHED ITEMS" in csv_str
        assert "OUTSTANDING DEPOSITS (BANK ONLY)" in csv_str
        assert "OUTSTANDING CHECKS (LEDGER ONLY)" in csv_str
        assert "SUMMARY" in csv_str

    def test_special_chars(self):
        """Descriptions with commas and quotes should be handled by CSV writer."""
        matches = [
            ReconciliationMatch(
                bank_txn=BankTransaction(date="2025-01-15", description='Payment, "Rush"', amount=100.0, row_number=1),
                ledger_txn=None,
                match_type=MatchType.BANK_ONLY,
                match_confidence=0.0,
            ),
        ]
        summary = calculate_summary(matches)
        csv_str = export_reconciliation_csv(summary)
        assert "Rush" in csv_str


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

class TestMainEntry:
    """Tests for reconcile_bank_statement."""

    def test_full_pipeline(self):
        bank_rows = [
            {"Date": "2025-01-15", "Amount": 1000.0, "Description": "Deposit", "Reference": "DEP001"},
            {"Date": "2025-01-16", "Amount": -250.0, "Description": "Check #101", "Reference": "CHK101"},
        ]
        ledger_rows = [
            {"Date": "2025-01-15", "Amount": 1000.0, "Description": "Cash receipt", "Reference": "DEP001"},
            {"Date": "2025-01-16", "Amount": -250.0, "Description": "Vendor payment", "Reference": "CHK101"},
        ]
        result = reconcile_bank_statement(
            bank_rows=bank_rows,
            ledger_rows=ledger_rows,
            bank_columns=["Date", "Amount", "Description", "Reference"],
            ledger_columns=["Date", "Amount", "Description", "Reference"],
        )
        assert isinstance(result, BankRecResult)
        assert result.summary.matched_count == 2
        assert result.summary.bank_only_count == 0
        assert result.summary.ledger_only_count == 0
        assert result.summary.reconciling_difference == 0.0

    def test_manual_mapping(self):
        bank_rows = [
            {"Col A": "2025-01-15", "Col B": 500.0, "Col C": "Test"},
        ]
        ledger_rows = [
            {"Col X": "2025-01-15", "Col Y": 500.0, "Col Z": "Test"},
        ]
        result = reconcile_bank_statement(
            bank_rows=bank_rows,
            ledger_rows=ledger_rows,
            bank_columns=["Col A", "Col B", "Col C"],
            ledger_columns=["Col X", "Col Y", "Col Z"],
            bank_mapping={"date_column": "Col A", "amount_column": "Col B", "description_column": "Col C"},
            ledger_mapping={"date_column": "Col X", "amount_column": "Col Y", "description_column": "Col Z"},
        )
        assert result.summary.matched_count == 1
        assert result.bank_column_detection.overall_confidence == 1.0
        assert result.ledger_column_detection.overall_confidence == 1.0

    def test_to_dict(self):
        result = reconcile_bank_statement(
            bank_rows=[{"Date": "2025-01-15", "Amount": 100.0}],
            ledger_rows=[{"Date": "2025-01-15", "Amount": 100.0}],
            bank_columns=["Date", "Amount"],
            ledger_columns=["Date", "Amount"],
        )
        d = result.to_dict()
        assert "summary" in d
        assert "bank_column_detection" in d
        assert "ledger_column_detection" in d
        assert d["summary"]["matched_count"] == 1

    def test_edge_empty_files(self):
        result = reconcile_bank_statement(
            bank_rows=[],
            ledger_rows=[],
            bank_columns=["Date", "Amount"],
            ledger_columns=["Date", "Amount"],
        )
        assert result.summary.matched_count == 0
        assert result.summary.reconciling_difference == 0.0


# =============================================================================
# API ROUTE REGISTRATION
# =============================================================================

class TestAPIRoute:
    """Tests for route registration."""

    def test_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/audit/bank-reconciliation" in paths

    def test_route_method_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/audit/bank-reconciliation":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /audit/bank-reconciliation not found")

    def test_export_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/export/csv/bank-rec" in paths

    def test_route_has_tag(self):
        from routes.bank_reconciliation import router
        assert "bank_reconciliation" in router.tags


# =============================================================================
# MATCH COLUMN HELPER
# =============================================================================

class TestMatchColumn:
    """Tests for _match_bank_column."""

    def test_exact_match_high_confidence(self):
        conf = _match_bank_column("Date", BANK_DATE_PATTERNS)
        assert conf >= 0.95

    def test_partial_match(self):
        conf = _match_bank_column("Transaction Date", BANK_DATE_PATTERNS)
        assert conf >= 0.90

    def test_no_match(self):
        conf = _match_bank_column("Vendor Name", BANK_DATE_PATTERNS)
        assert conf == 0.0
