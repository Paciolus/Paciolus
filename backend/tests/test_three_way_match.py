"""
Tests for Three-Way Match Validator Engine — Sprint 91-92

Sprint 91 (~50 tests): Column detection, parsing, data quality, config
Sprint 92 (~60 tests): Matching algorithm, variance analysis, summary, edge cases

Test IDs:
  TestPOColumnDetection: 8 tests
  TestInvoiceColumnDetection: 8 tests
  TestReceiptColumnDetection: 8 tests
  TestPOParsing: 6 tests
  TestInvoiceParsing: 6 tests
  TestReceiptParsing: 6 tests
  TestDataQuality: 5 tests
  TestConfig: 3 tests
  TestHelpers: 5 tests (safe_float, safe_str, parse_date)
"""

import pytest
from three_way_match_engine import (
    # Enums
    MatchDocumentType, MatchType, MatchRiskLevel,
    POColumnType, InvoiceColumnType, ReceiptColumnType,
    # Column detection
    detect_po_columns, detect_invoice_columns, detect_receipt_columns,
    # Data models
    PurchaseOrder, Invoice, Receipt,
    # Detection results
    POColumnDetectionResult, InvoiceColumnDetectionResult, ReceiptColumnDetectionResult,
    # Parsing
    parse_purchase_orders, parse_invoices, parse_receipts,
    # Data quality
    ThreeWayMatchDataQuality, assess_three_way_data_quality,
    # Config
    ThreeWayMatchConfig,
    # Matching
    ThreeWayMatch, MatchVariance, UnmatchedDocument,
    ThreeWayMatchSummary, ThreeWayMatchResult,
    run_three_way_match,
    # Helpers
    _match_column, _safe_float, _safe_str, _parse_date,
    _vendor_similarity, _compute_variances,
)


# =============================================================================
# HELPERS
# =============================================================================

class TestHelpers:
    """Tests for helper functions."""

    def test_safe_float_valid(self):
        assert _safe_float(42.5) == 42.5
        assert _safe_float("100.00") == 100.0
        assert _safe_float(0) == 0.0

    def test_safe_float_currency_strings(self):
        assert _safe_float("$1,234.56") == 1234.56
        assert _safe_float("($500.00)") == -500.0
        assert _safe_float("1,000") == 1000.0

    def test_safe_float_invalid(self):
        assert _safe_float(None) == 0.0
        assert _safe_float("abc") == 0.0
        assert _safe_float("") == 0.0
        assert _safe_float(float("nan")) == 0.0
        assert _safe_float(float("inf")) == 0.0

    def test_safe_str_valid(self):
        assert _safe_str("hello") == "hello"
        assert _safe_str(42) == "42"
        assert _safe_str(" spaced ") == "spaced"

    def test_safe_str_empty(self):
        assert _safe_str(None) is None
        assert _safe_str("") is None
        assert _safe_str("nan") is None
        assert _safe_str("None") is None

    def test_parse_date_formats(self):
        from datetime import date
        assert _parse_date("2025-01-15") == date(2025, 1, 15)
        assert _parse_date("01/15/2025") == date(2025, 1, 15)
        assert _parse_date("2025-01-15 10:30:00") == date(2025, 1, 15)

    def test_parse_date_invalid(self):
        assert _parse_date(None) is None
        assert _parse_date("") is None
        assert _parse_date("not-a-date") is None

    def test_vendor_similarity_exact(self):
        assert _vendor_similarity("Acme Corp", "Acme Corp") == 1.0
        assert _vendor_similarity("Acme Corp", "acme corp") == 1.0

    def test_vendor_similarity_empty(self):
        assert _vendor_similarity("", "Acme") == 0.0
        assert _vendor_similarity("Acme", "") == 0.0


# =============================================================================
# PO COLUMN DETECTION
# =============================================================================

class TestPOColumnDetection:
    """Tests for PO column detection."""

    def test_standard_columns(self):
        cols = ["PO Number", "Vendor Name", "Description", "Quantity", "Unit Price", "Total Amount", "Order Date"]
        result = detect_po_columns(cols)
        assert result.po_number_column == "PO Number"
        assert result.vendor_column == "Vendor Name"
        assert result.total_amount_column == "Total Amount"
        assert result.quantity_column == "Quantity"
        assert result.unit_price_column == "Unit Price"
        assert result.order_date_column == "Order Date"
        assert result.overall_confidence >= 0.85

    def test_alternate_headers(self):
        cols = ["PO#", "Supplier", "Item", "Qty Ordered", "Rate", "Amount", "Date"]
        result = detect_po_columns(cols)
        assert result.po_number_column == "PO#"
        assert result.vendor_column == "Supplier"
        assert result.total_amount_column == "Amount"
        assert result.overall_confidence > 0.0

    def test_minimal_columns(self):
        cols = ["PO", "Vendor", "Total"]
        result = detect_po_columns(cols)
        assert result.po_number_column is not None
        assert result.vendor_column is not None
        assert result.total_amount_column is not None

    def test_empty_columns(self):
        result = detect_po_columns([])
        assert result.overall_confidence == 0.0
        assert result.all_columns == []

    def test_low_confidence(self):
        cols = ["Col1", "Col2", "Col3"]
        result = detect_po_columns(cols)
        assert result.overall_confidence == 0.0
        assert result.requires_mapping is True

    def test_requires_mapping_false(self):
        cols = ["PO Number", "Vendor Name", "Total Amount"]
        result = detect_po_columns(cols)
        assert result.requires_mapping is False

    def test_to_dict(self):
        cols = ["PO Number", "Vendor", "Amount"]
        result = detect_po_columns(cols)
        d = result.to_dict()
        assert "po_number_column" in d
        assert "overall_confidence" in d
        assert "requires_mapping" in d
        assert isinstance(d["all_columns"], list)

    def test_detection_notes_missing_required(self):
        cols = ["Description", "Quantity", "Unit Price"]
        result = detect_po_columns(cols)
        assert len(result.detection_notes) > 0
        assert any("Required column" in note for note in result.detection_notes)


# =============================================================================
# INVOICE COLUMN DETECTION
# =============================================================================

class TestInvoiceColumnDetection:
    """Tests for invoice column detection."""

    def test_standard_columns(self):
        cols = ["Invoice Number", "PO Reference", "Vendor", "Description", "Quantity", "Unit Price", "Total Amount", "Invoice Date", "Due Date"]
        result = detect_invoice_columns(cols)
        assert result.invoice_number_column == "Invoice Number"
        assert result.po_reference_column == "PO Reference"
        assert result.vendor_column == "Vendor"
        assert result.total_amount_column == "Total Amount"
        assert result.overall_confidence >= 0.85

    def test_alternate_headers(self):
        cols = ["Inv#", "PO#", "Supplier Name", "Invoice Amount", "Bill Date"]
        result = detect_invoice_columns(cols)
        assert result.invoice_number_column == "Inv#"
        assert result.po_reference_column == "PO#"
        assert result.vendor_column == "Supplier Name"
        assert result.total_amount_column == "Invoice Amount"

    def test_without_po_reference(self):
        cols = ["Invoice Number", "Vendor", "Amount", "Invoice Date"]
        result = detect_invoice_columns(cols)
        assert result.invoice_number_column == "Invoice Number"
        assert result.vendor_column == "Vendor"
        assert result.po_reference_column is None

    def test_empty_columns(self):
        result = detect_invoice_columns([])
        assert result.overall_confidence == 0.0

    def test_low_confidence(self):
        cols = ["X", "Y", "Z"]
        result = detect_invoice_columns(cols)
        assert result.requires_mapping is True

    def test_bill_number_detection(self):
        cols = ["Bill Number", "Vendor", "Net Amount"]
        result = detect_invoice_columns(cols)
        assert result.invoice_number_column == "Bill Number"

    def test_to_dict(self):
        cols = ["Invoice#", "Vendor", "Amount"]
        result = detect_invoice_columns(cols)
        d = result.to_dict()
        assert "invoice_number_column" in d
        assert "po_reference_column" in d

    def test_detection_notes_missing_required(self):
        cols = ["Description", "Quantity"]
        result = detect_invoice_columns(cols)
        assert any("Required column" in note for note in result.detection_notes)


# =============================================================================
# RECEIPT COLUMN DETECTION
# =============================================================================

class TestReceiptColumnDetection:
    """Tests for receipt column detection."""

    def test_standard_columns(self):
        cols = ["Receipt Number", "PO Reference", "Invoice Ref", "Vendor", "Description", "Quantity Received", "Receipt Date", "Received By", "Condition"]
        result = detect_receipt_columns(cols)
        assert result.receipt_number_column == "Receipt Number"
        assert result.po_reference_column == "PO Reference"
        assert result.vendor_column == "Vendor"
        assert result.quantity_received_column == "Quantity Received"
        assert result.overall_confidence >= 0.85

    def test_grn_headers(self):
        cols = ["GRN Number", "PO#", "Supplier", "Qty Received", "GRN Date", "Inspector"]
        result = detect_receipt_columns(cols)
        assert result.receipt_number_column == "GRN Number"
        assert result.vendor_column == "Supplier"
        assert result.quantity_received_column == "Qty Received"

    def test_minimal_columns(self):
        cols = ["Vendor", "Qty", "Date"]
        result = detect_receipt_columns(cols)
        assert result.vendor_column is not None

    def test_empty_columns(self):
        result = detect_receipt_columns([])
        assert result.overall_confidence == 0.0

    def test_low_confidence(self):
        cols = ["A", "B", "C"]
        result = detect_receipt_columns(cols)
        assert result.requires_mapping is True

    def test_without_invoice_reference(self):
        cols = ["Receipt#", "PO#", "Vendor", "Quantity Received", "Receipt Date"]
        result = detect_receipt_columns(cols)
        assert result.receipt_number_column == "Receipt#"
        assert result.invoice_reference_column is None

    def test_to_dict(self):
        cols = ["Receipt#", "Vendor", "Qty Received"]
        result = detect_receipt_columns(cols)
        d = result.to_dict()
        assert "receipt_number_column" in d
        assert "po_reference_column" in d
        assert "requires_mapping" in d

    def test_condition_column(self):
        cols = ["Receipt#", "Vendor", "Qty", "Condition"]
        result = detect_receipt_columns(cols)
        assert result.condition_column == "Condition"


# =============================================================================
# PO PARSING
# =============================================================================

class TestPOParsing:
    """Tests for PO parsing."""

    def test_valid_parsing(self):
        detection = POColumnDetectionResult(
            po_number_column="PO#", vendor_column="Vendor",
            total_amount_column="Amount", quantity_column="Qty",
        )
        rows = [
            {"PO#": "PO-001", "Vendor": "Acme Corp", "Amount": "1000.00", "Qty": "10"},
            {"PO#": "PO-002", "Vendor": "Widgets Inc", "Amount": "2500.50", "Qty": "25"},
        ]
        orders = parse_purchase_orders(rows, detection)
        assert len(orders) == 2
        assert orders[0].po_number == "PO-001"
        assert orders[0].vendor == "Acme Corp"
        assert orders[0].total_amount == 1000.00
        assert orders[0].quantity == 10.0
        assert orders[0].row_number == 1

    def test_missing_fields(self):
        detection = POColumnDetectionResult(po_number_column="PO#")
        rows = [{"PO#": "PO-001"}]
        orders = parse_purchase_orders(rows, detection)
        assert len(orders) == 1
        assert orders[0].po_number == "PO-001"
        assert orders[0].vendor == ""
        assert orders[0].total_amount == 0.0

    def test_empty_rows(self):
        detection = POColumnDetectionResult(po_number_column="PO#")
        orders = parse_purchase_orders([], detection)
        assert len(orders) == 0

    def test_currency_amounts(self):
        detection = POColumnDetectionResult(
            po_number_column="PO#", total_amount_column="Total",
        )
        rows = [{"PO#": "PO-001", "Total": "$1,500.00"}]
        orders = parse_purchase_orders(rows, detection)
        assert orders[0].total_amount == 1500.00

    def test_to_dict(self):
        po = PurchaseOrder(
            po_number="PO-001", vendor="Test", total_amount=100.0, row_number=1,
        )
        d = po.to_dict()
        assert d["po_number"] == "PO-001"
        assert d["vendor"] == "Test"
        assert d["total_amount"] == 100.0
        assert d["row_number"] == 1

    def test_row_numbering(self):
        detection = POColumnDetectionResult(po_number_column="PO#")
        rows = [{"PO#": f"PO-{i}"} for i in range(5)]
        orders = parse_purchase_orders(rows, detection)
        assert [o.row_number for o in orders] == [1, 2, 3, 4, 5]


# =============================================================================
# INVOICE PARSING
# =============================================================================

class TestInvoiceParsing:
    """Tests for invoice parsing."""

    def test_valid_parsing(self):
        detection = InvoiceColumnDetectionResult(
            invoice_number_column="Inv#", po_reference_column="PO Ref",
            vendor_column="Vendor", total_amount_column="Amount",
        )
        rows = [
            {"Inv#": "INV-001", "PO Ref": "PO-001", "Vendor": "Acme Corp", "Amount": "1000.00"},
        ]
        invoices = parse_invoices(rows, detection)
        assert len(invoices) == 1
        assert invoices[0].invoice_number == "INV-001"
        assert invoices[0].po_reference == "PO-001"
        assert invoices[0].vendor == "Acme Corp"
        assert invoices[0].total_amount == 1000.00

    def test_missing_po_reference(self):
        detection = InvoiceColumnDetectionResult(
            invoice_number_column="Inv#", vendor_column="Vendor",
            total_amount_column="Amount",
        )
        rows = [{"Inv#": "INV-001", "Vendor": "Test", "Amount": "500"}]
        invoices = parse_invoices(rows, detection)
        assert invoices[0].po_reference is None

    def test_empty_rows(self):
        detection = InvoiceColumnDetectionResult()
        invoices = parse_invoices([], detection)
        assert len(invoices) == 0

    def test_date_fields(self):
        detection = InvoiceColumnDetectionResult(
            invoice_number_column="Inv#", invoice_date_column="Date",
            due_date_column="Due",
        )
        rows = [{"Inv#": "INV-001", "Date": "2025-01-15", "Due": "2025-02-15"}]
        invoices = parse_invoices(rows, detection)
        assert invoices[0].invoice_date == "2025-01-15"
        assert invoices[0].due_date == "2025-02-15"

    def test_to_dict(self):
        inv = Invoice(
            invoice_number="INV-001", po_reference="PO-001",
            vendor="Test", total_amount=500.0, row_number=1,
        )
        d = inv.to_dict()
        assert d["invoice_number"] == "INV-001"
        assert d["po_reference"] == "PO-001"

    def test_row_numbering(self):
        detection = InvoiceColumnDetectionResult(invoice_number_column="Inv#")
        rows = [{"Inv#": f"INV-{i}"} for i in range(3)]
        invoices = parse_invoices(rows, detection)
        assert [inv.row_number for inv in invoices] == [1, 2, 3]


# =============================================================================
# RECEIPT PARSING
# =============================================================================

class TestReceiptParsing:
    """Tests for receipt parsing."""

    def test_valid_parsing(self):
        detection = ReceiptColumnDetectionResult(
            receipt_number_column="Receipt#", po_reference_column="PO Ref",
            vendor_column="Vendor", quantity_received_column="Qty Received",
            receipt_date_column="Date",
        )
        rows = [
            {"Receipt#": "REC-001", "PO Ref": "PO-001", "Vendor": "Acme Corp",
             "Qty Received": "10", "Date": "2025-01-20"},
        ]
        receipts = parse_receipts(rows, detection)
        assert len(receipts) == 1
        assert receipts[0].receipt_number == "REC-001"
        assert receipts[0].po_reference == "PO-001"
        assert receipts[0].quantity_received == 10.0
        assert receipts[0].receipt_date == "2025-01-20"

    def test_with_invoice_reference(self):
        detection = ReceiptColumnDetectionResult(
            receipt_number_column="Receipt#", invoice_reference_column="Inv Ref",
            vendor_column="Vendor", quantity_received_column="Qty",
        )
        rows = [{"Receipt#": "REC-001", "Inv Ref": "INV-001", "Vendor": "Test", "Qty": "5"}]
        receipts = parse_receipts(rows, detection)
        assert receipts[0].invoice_reference == "INV-001"

    def test_empty_rows(self):
        detection = ReceiptColumnDetectionResult()
        receipts = parse_receipts([], detection)
        assert len(receipts) == 0

    def test_condition_field(self):
        detection = ReceiptColumnDetectionResult(
            receipt_number_column="Receipt#", condition_column="Condition",
            vendor_column="Vendor", quantity_received_column="Qty",
        )
        rows = [{"Receipt#": "REC-001", "Condition": "Good", "Vendor": "X", "Qty": "5"}]
        receipts = parse_receipts(rows, detection)
        assert receipts[0].condition == "Good"

    def test_to_dict(self):
        rec = Receipt(
            receipt_number="REC-001", po_reference="PO-001",
            vendor="Test", quantity_received=10.0, row_number=1,
        )
        d = rec.to_dict()
        assert d["receipt_number"] == "REC-001"
        assert d["po_reference"] == "PO-001"
        assert d["quantity_received"] == 10.0

    def test_row_numbering(self):
        detection = ReceiptColumnDetectionResult(receipt_number_column="Rec#")
        rows = [{"Rec#": f"REC-{i}"} for i in range(4)]
        receipts = parse_receipts(rows, detection)
        assert [r.row_number for r in receipts] == [1, 2, 3, 4]


# =============================================================================
# DATA QUALITY
# =============================================================================

class TestDataQuality:
    """Tests for data quality assessment."""

    def test_full_quality(self):
        pos = [PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=100)]
        invoices = [Invoice(invoice_number="INV-001", vendor="Acme", total_amount=100, po_reference="PO-001")]
        receipts = [Receipt(vendor="Acme", quantity_received=10, po_reference="PO-001")]
        dq = assess_three_way_data_quality(pos, invoices, receipts)
        assert dq.po_count == 1
        assert dq.invoice_count == 1
        assert dq.receipt_count == 1
        assert dq.po_vendor_fill_rate == 1.0
        assert dq.po_number_fill_rate == 1.0
        assert dq.overall_quality_score > 0.8

    def test_empty_data(self):
        dq = assess_three_way_data_quality([], [], [])
        assert dq.po_count == 0
        assert dq.invoice_count == 0
        assert dq.receipt_count == 0
        assert dq.overall_quality_score == 0.0

    def test_low_po_ref_issues(self):
        invoices = [
            Invoice(invoice_number=f"INV-{i}", vendor="V", total_amount=100) for i in range(10)
        ]
        pos = [PurchaseOrder(po_number=f"PO-{i}", vendor="V", total_amount=100) for i in range(10)]
        receipts = [Receipt(vendor="V", quantity_received=10) for _ in range(10)]
        dq = assess_three_way_data_quality(pos, invoices, receipts)
        assert "PO reference on invoices" in " ".join(dq.detected_issues)
        assert "PO reference on receipts" in " ".join(dq.detected_issues)

    def test_to_dict(self):
        dq = ThreeWayMatchDataQuality(po_count=5, invoice_count=3, receipt_count=4)
        d = dq.to_dict()
        assert d["po_count"] == 5
        assert d["invoice_count"] == 3
        assert d["receipt_count"] == 4
        assert "overall_quality_score" in d

    def test_partial_fill_rates(self):
        pos = [
            PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=100),
            PurchaseOrder(po_number=None, vendor="", total_amount=0),
        ]
        dq = assess_three_way_data_quality(pos, [], [])
        assert dq.po_number_fill_rate == 0.5
        assert dq.po_vendor_fill_rate == 0.5


# =============================================================================
# CONFIG
# =============================================================================

class TestConfig:
    """Tests for ThreeWayMatchConfig."""

    def test_defaults(self):
        config = ThreeWayMatchConfig()
        assert config.amount_tolerance == 0.01
        assert config.quantity_tolerance == 0.0
        assert config.date_window_days == 30
        assert config.fuzzy_vendor_threshold == 0.85
        assert config.enable_fuzzy_matching is True
        assert config.price_variance_threshold == 0.05

    def test_custom_values(self):
        config = ThreeWayMatchConfig(
            amount_tolerance=0.10,
            quantity_tolerance=1.0,
            date_window_days=60,
            fuzzy_vendor_threshold=0.90,
        )
        assert config.amount_tolerance == 0.10
        assert config.quantity_tolerance == 1.0
        assert config.date_window_days == 60

    def test_to_dict(self):
        config = ThreeWayMatchConfig()
        d = config.to_dict()
        assert "amount_tolerance" in d
        assert "quantity_tolerance" in d
        assert "enable_fuzzy_matching" in d
        assert d["fuzzy_composite_threshold"] == 0.70


# =============================================================================
# ENUMS
# =============================================================================

class TestEnums:
    """Tests for enum values."""

    def test_match_document_type(self):
        assert MatchDocumentType.PURCHASE_ORDER.value == "purchase_order"
        assert MatchDocumentType.INVOICE.value == "invoice"
        assert MatchDocumentType.RECEIPT.value == "receipt"

    def test_match_type(self):
        assert MatchType.EXACT_PO.value == "exact_po"
        assert MatchType.FUZZY.value == "fuzzy"
        assert MatchType.PARTIAL.value == "partial"

    def test_match_risk_level(self):
        assert MatchRiskLevel.LOW.value == "low"
        assert MatchRiskLevel.MEDIUM.value == "medium"
        assert MatchRiskLevel.HIGH.value == "high"


# =============================================================================
# SPRINT 92: MATCHING ALGORITHM TESTS
# =============================================================================

class TestExactPOMatching:
    """Tests for Phase 1: Exact PO number linkage."""

    def test_full_three_way_match(self):
        """PO, Invoice, and Receipt all link via PO number."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="Acme Corp", total_amount=1000.0, quantity=10, row_number=1)]
        invoices = [Invoice(invoice_number="INV-001", po_reference="PO-001", vendor="Acme Corp", total_amount=1000.0, quantity=10, row_number=1)]
        receipts = [Receipt(receipt_number="REC-001", po_reference="PO-001", vendor="Acme Corp", quantity_received=10, row_number=1)]
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.full_matches) == 1
        assert len(result.partial_matches) == 0
        assert len(result.unmatched_pos) == 0
        assert result.full_matches[0].match_type == "exact_po"
        assert result.full_matches[0].match_confidence == 0.95

    def test_po_invoice_only(self):
        """PO and Invoice match, no Receipt."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=500, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="Acme", total_amount=500, row_number=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.full_matches) == 0
        assert len(result.partial_matches) == 1
        assert result.partial_matches[0].po is not None
        assert result.partial_matches[0].invoice is not None
        assert result.partial_matches[0].receipt is None

    def test_po_receipt_only(self):
        """PO and Receipt match via PO number, no Invoice."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=500, quantity=10, row_number=1)]
        invoices = []
        receipts = [Receipt(po_reference="PO-001", vendor="Acme", quantity_received=10, row_number=1)]
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.partial_matches) == 1
        assert result.partial_matches[0].receipt is not None
        assert result.partial_matches[0].invoice is None

    def test_no_match(self):
        """PO number doesn't match any invoice or receipt."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=500, row_number=1)]
        invoices = [Invoice(po_reference="PO-999", vendor="Widget", total_amount=500, row_number=1)]
        receipts = [Receipt(po_reference="PO-888", vendor="Other", quantity_received=10, row_number=1)]
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, invoices, receipts, config)
        assert len(result.full_matches) == 0
        assert len(result.unmatched_pos) == 1
        assert len(result.unmatched_invoices) == 1
        assert len(result.unmatched_receipts) == 1

    def test_multiple_pos(self):
        """Multiple POs each match their own invoice."""
        pos = [
            PurchaseOrder(po_number="PO-001", vendor="A", total_amount=100, row_number=1),
            PurchaseOrder(po_number="PO-002", vendor="B", total_amount=200, row_number=2),
        ]
        invoices = [
            Invoice(po_reference="PO-001", vendor="A", total_amount=100, row_number=1),
            Invoice(po_reference="PO-002", vendor="B", total_amount=200, row_number=2),
        ]
        receipts = [
            Receipt(po_reference="PO-001", vendor="A", quantity_received=5, row_number=1),
            Receipt(po_reference="PO-002", vendor="B", quantity_received=10, row_number=2),
        ]
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.full_matches) == 2
        assert len(result.unmatched_pos) == 0

    def test_case_insensitive_po_number(self):
        """PO number matching is case-insensitive."""
        pos = [PurchaseOrder(po_number="po-001", vendor="Acme", total_amount=100, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="Acme", total_amount=100, row_number=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.partial_matches) == 1

    def test_receipt_linked_via_invoice_reference(self):
        """Receipt links via invoice reference when no PO ref on receipt."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=1000, quantity=10, row_number=1)]
        invoices = [Invoice(invoice_number="INV-100", po_reference="PO-001", vendor="Acme", total_amount=1000, quantity=10, row_number=1)]
        receipts = [Receipt(invoice_reference="INV-100", vendor="Acme", quantity_received=10, row_number=1)]
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.full_matches) == 1

    def test_one_to_one_matching(self):
        """Each PO matches at most one invoice (no double-matching)."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=100, row_number=1)]
        invoices = [
            Invoice(po_reference="PO-001", vendor="Acme", total_amount=100, row_number=1),
            Invoice(po_reference="PO-001", vendor="Acme", total_amount=100, row_number=2),
        ]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        # Only one invoice should match — the other remains unmatched
        assert len(result.partial_matches) == 1
        assert len(result.unmatched_invoices) == 1

    def test_duplicate_po_numbers(self):
        """Two POs with same number each match separate invoices."""
        pos = [
            PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=100, row_number=1),
            PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=200, row_number=2),
        ]
        invoices = [
            Invoice(po_reference="PO-001", vendor="Acme", total_amount=100, row_number=1),
            Invoice(po_reference="PO-001", vendor="Acme", total_amount=200, row_number=2),
        ]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        total_matched = len(result.full_matches) + len(result.partial_matches)
        assert total_matched == 2

    def test_po_without_number(self):
        """POs without PO number skip Phase 1 matching."""
        pos = [PurchaseOrder(vendor="Acme", total_amount=100, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="Acme", total_amount=100, row_number=1)]
        receipts = []
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, invoices, receipts, config)
        assert len(result.unmatched_pos) == 1


class TestFuzzyFallback:
    """Tests for Phase 2: Fuzzy vendor+amount+date matching."""

    def test_fuzzy_vendor_match(self):
        """Fuzzy matches when vendor names are similar and amounts match."""
        pos = [PurchaseOrder(vendor="Acme Corporation LLC", total_amount=1000.0, row_number=1)]
        invoices = [Invoice(vendor="Acme Corporation", total_amount=1000.0, row_number=1)]
        receipts = []
        config = ThreeWayMatchConfig(fuzzy_vendor_threshold=0.70)
        result = run_three_way_match(pos, invoices, receipts, config)
        assert len(result.partial_matches) >= 1

    def test_fuzzy_disabled(self):
        """No fuzzy matching when disabled."""
        pos = [PurchaseOrder(vendor="Acme Corp", total_amount=1000.0, row_number=1)]
        invoices = [Invoice(vendor="Acme Corp", total_amount=1000.0, row_number=1)]
        receipts = []
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, invoices, receipts, config)
        # No PO number → no Phase 1 match. Fuzzy disabled → no Phase 2 match.
        assert len(result.unmatched_pos) == 1
        assert len(result.unmatched_invoices) == 1

    def test_fuzzy_vendor_below_threshold(self):
        """No fuzzy match when vendor similarity below threshold."""
        pos = [PurchaseOrder(vendor="Acme Corp", total_amount=1000.0, row_number=1)]
        invoices = [Invoice(vendor="Totally Different Inc", total_amount=1000.0, row_number=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.unmatched_pos) == 1

    def test_fuzzy_amount_proximity(self):
        """Fuzzy matching considers amount proximity."""
        pos = [PurchaseOrder(vendor="Acme Corp", total_amount=1000.0, row_number=1)]
        invoices = [Invoice(vendor="Acme Corp", total_amount=1000.01, row_number=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        # Amount within tolerance → should match
        assert len(result.partial_matches) >= 1 or len(result.full_matches) >= 1

    def test_fuzzy_date_proximity(self):
        """Fuzzy matching uses date proximity in scoring."""
        pos = [PurchaseOrder(vendor="Acme Corp", total_amount=1000.0, order_date="2025-01-01", row_number=1)]
        invoices = [Invoice(vendor="Acme Corp", total_amount=1000.0, invoice_date="2025-01-05", row_number=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.partial_matches) >= 1

    def test_fuzzy_composite_below_threshold(self):
        """No match when composite score below threshold."""
        pos = [PurchaseOrder(vendor="Acme Corp", total_amount=1000.0, row_number=1)]
        invoices = [Invoice(vendor="Acme Corp", total_amount=5000.0, row_number=1)]
        receipts = []
        config = ThreeWayMatchConfig(fuzzy_composite_threshold=0.95)
        result = run_three_way_match(pos, invoices, receipts, config)
        # Large amount difference → low amount score → below 0.95 threshold
        assert len(result.unmatched_pos) == 1

    def test_fuzzy_with_receipt(self):
        """Fuzzy matches PO to both invoice and receipt."""
        pos = [PurchaseOrder(vendor="Acme Corp", total_amount=1000.0, quantity=10, row_number=1)]
        invoices = [Invoice(vendor="Acme Corp", total_amount=1000.0, row_number=1)]
        receipts = [Receipt(vendor="Acme Corp", quantity_received=10, row_number=1)]
        result = run_three_way_match(pos, invoices, receipts)
        total = len(result.full_matches) + len(result.partial_matches)
        assert total >= 1

    def test_fuzzy_only_used_for_unmatched(self):
        """Fuzzy matching only applies to documents not matched in Phase 1."""
        pos = [
            PurchaseOrder(po_number="PO-001", vendor="Acme", total_amount=1000, row_number=1),
            PurchaseOrder(vendor="Acme", total_amount=500, row_number=2),
        ]
        invoices = [
            Invoice(po_reference="PO-001", vendor="Acme", total_amount=1000, row_number=1),
            Invoice(vendor="Acme", total_amount=500, row_number=2),
        ]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        # PO-001 matched via Phase 1, second PO via Phase 2
        total = len(result.full_matches) + len(result.partial_matches)
        assert total == 2


class TestVarianceAnalysis:
    """Tests for variance computation between matched documents."""

    def test_amount_variance(self):
        """Amount variance detected between PO and Invoice."""
        po = PurchaseOrder(total_amount=1000.0)
        inv = Invoice(total_amount=1100.0)
        config = ThreeWayMatchConfig()
        variances = _compute_variances(po, inv, None, config)
        amount_vars = [v for v in variances if v.field == "amount"]
        assert len(amount_vars) == 1
        assert amount_vars[0].variance_amount == 100.0
        assert amount_vars[0].po_value == 1000.0
        assert amount_vars[0].invoice_value == 1100.0

    def test_quantity_variance(self):
        """Quantity variance detected between PO and Receipt."""
        po = PurchaseOrder(quantity=100)
        rec = Receipt(quantity_received=90)
        config = ThreeWayMatchConfig()
        variances = _compute_variances(po, None, rec, config)
        qty_vars = [v for v in variances if v.field == "quantity"]
        assert len(qty_vars) == 1
        assert qty_vars[0].variance_amount == 10.0

    def test_price_variance(self):
        """Price variance detected between PO and Invoice unit prices."""
        po = PurchaseOrder(unit_price=10.0)
        inv = Invoice(unit_price=12.0)
        config = ThreeWayMatchConfig(price_variance_threshold=0.05)
        variances = _compute_variances(po, inv, None, config)
        price_vars = [v for v in variances if v.field == "price"]
        assert len(price_vars) == 1
        assert price_vars[0].severity in ("high", "medium", "low")

    def test_date_variance(self):
        """Date variance detected when receipt is beyond window."""
        po = PurchaseOrder(expected_delivery="2025-01-15")
        rec = Receipt(receipt_date="2025-03-20")
        config = ThreeWayMatchConfig(date_window_days=30)
        variances = _compute_variances(po, None, rec, config)
        date_vars = [v for v in variances if v.field == "date"]
        assert len(date_vars) == 1
        assert date_vars[0].severity in ("high", "medium")

    def test_no_variance_within_tolerance(self):
        """No variance when amounts within tolerance."""
        po = PurchaseOrder(total_amount=1000.0)
        inv = Invoice(total_amount=1000.005)
        config = ThreeWayMatchConfig(amount_tolerance=0.01)
        variances = _compute_variances(po, inv, None, config)
        assert len([v for v in variances if v.field == "amount"]) == 0

    def test_variance_severity_high(self):
        """High severity for >10% variance."""
        po = PurchaseOrder(total_amount=1000.0)
        inv = Invoice(total_amount=1200.0)
        config = ThreeWayMatchConfig()
        variances = _compute_variances(po, inv, None, config)
        amount_vars = [v for v in variances if v.field == "amount"]
        assert amount_vars[0].severity == "high"

    def test_variance_severity_medium(self):
        """Medium severity for 5-10% variance."""
        po = PurchaseOrder(total_amount=1000.0)
        inv = Invoice(total_amount=1070.0)
        config = ThreeWayMatchConfig()
        variances = _compute_variances(po, inv, None, config)
        amount_vars = [v for v in variances if v.field == "amount"]
        assert amount_vars[0].severity == "medium"

    def test_variance_severity_low(self):
        """Low severity for 1-5% variance."""
        po = PurchaseOrder(total_amount=1000.0)
        inv = Invoice(total_amount=1020.0)
        config = ThreeWayMatchConfig()
        variances = _compute_variances(po, inv, None, config)
        amount_vars = [v for v in variances if v.field == "amount"]
        assert amount_vars[0].severity == "low"

    def test_no_variances_when_null(self):
        """No variances when documents are None."""
        config = ThreeWayMatchConfig()
        variances = _compute_variances(None, None, None, config)
        assert len(variances) == 0

    def test_variance_to_dict(self):
        """MatchVariance.to_dict() serializes correctly."""
        v = MatchVariance(
            field="amount", po_value=1000, invoice_value=1100,
            variance_amount=100, variance_pct=0.10, severity="medium",
        )
        d = v.to_dict()
        assert d["field"] == "amount"
        assert d["variance_amount"] == 100.0
        assert d["severity"] == "medium"


class TestUnmatched:
    """Tests for unmatched document collection."""

    def test_orphan_pos(self):
        """POs without matching invoices/receipts are unmatched."""
        pos = [PurchaseOrder(po_number="PO-ORPHAN", vendor="Lost Inc", total_amount=999, row_number=1)]
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, [], [], config)
        assert len(result.unmatched_pos) == 1
        assert result.unmatched_pos[0].document_type == "purchase_order"
        assert "No matching" in result.unmatched_pos[0].reason

    def test_orphan_invoices(self):
        """Invoices without matching POs are unmatched."""
        invoices = [Invoice(invoice_number="INV-ORPHAN", vendor="Lost Inc", total_amount=999, row_number=1)]
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match([], invoices, [], config)
        assert len(result.unmatched_invoices) == 1
        assert result.unmatched_invoices[0].document_type == "invoice"

    def test_orphan_receipts(self):
        """Receipts without matching POs/invoices are unmatched."""
        receipts = [Receipt(receipt_number="REC-ORPHAN", vendor="Lost Inc", quantity_received=5, row_number=1)]
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match([], [], receipts, config)
        assert len(result.unmatched_receipts) == 1
        assert result.unmatched_receipts[0].document_type == "receipt"

    def test_unmatched_to_dict(self):
        """UnmatchedDocument serializes correctly."""
        u = UnmatchedDocument(
            document={"po_number": "PO-001"},
            document_type="purchase_order",
            reason="Test reason",
        )
        d = u.to_dict()
        assert d["document_type"] == "purchase_order"
        assert d["reason"] == "Test reason"

    def test_mixed_matched_and_unmatched(self):
        """Some documents match, some don't."""
        pos = [
            PurchaseOrder(po_number="PO-001", vendor="A", total_amount=100, row_number=1),
            PurchaseOrder(po_number="PO-002", vendor="B", total_amount=200, row_number=2),
        ]
        invoices = [Invoice(po_reference="PO-001", vendor="A", total_amount=100, row_number=1)]
        receipts = []
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, invoices, receipts, config)
        assert len(result.partial_matches) == 1
        assert len(result.unmatched_pos) == 1

    def test_unmatched_preserves_document_data(self):
        """Unmatched document preserves full to_dict() data."""
        pos = [PurchaseOrder(po_number="PO-X", vendor="Test Co", total_amount=5000, row_number=1)]
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, [], [], config)
        doc = result.unmatched_pos[0].document
        assert doc["po_number"] == "PO-X"
        assert doc["vendor"] == "Test Co"
        assert doc["total_amount"] == 5000


class TestSummary:
    """Tests for match summary and risk assessment."""

    def test_summary_counts(self):
        """Summary counts match actual results."""
        pos = [PurchaseOrder(po_number=f"PO-{i}", vendor="A", total_amount=100, quantity=5, row_number=i) for i in range(1, 6)]
        invoices = [Invoice(po_reference=f"PO-{i}", vendor="A", total_amount=100, quantity=5, row_number=i) for i in range(1, 4)]
        receipts = [Receipt(po_reference=f"PO-{i}", vendor="A", quantity_received=5, row_number=i) for i in range(1, 4)]
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, invoices, receipts, config)
        assert result.summary.total_pos == 5
        assert result.summary.total_invoices == 3
        assert result.summary.total_receipts == 3
        assert result.summary.full_match_count == 3
        assert len(result.unmatched_pos) == 2

    def test_summary_amounts(self):
        """Summary amounts are correctly summed."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="A", total_amount=1000, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="A", total_amount=1200, row_number=1)]
        receipts = [Receipt(po_reference="PO-001", vendor="A", quantity_received=10, row_number=1)]
        result = run_three_way_match(pos, invoices, receipts)
        assert result.summary.total_po_amount == 1000
        assert result.summary.total_invoice_amount == 1200
        assert result.summary.net_variance == 200.0

    def test_risk_assessment_low(self):
        """Low risk when all match with no material variances."""
        pos = [PurchaseOrder(po_number=f"PO-{i}", vendor="A", total_amount=100, quantity=5, row_number=i) for i in range(1, 11)]
        invoices = [Invoice(po_reference=f"PO-{i}", vendor="A", total_amount=100, quantity=5, row_number=i) for i in range(1, 11)]
        receipts = [Receipt(po_reference=f"PO-{i}", vendor="A", quantity_received=5, row_number=i) for i in range(1, 11)]
        result = run_three_way_match(pos, invoices, receipts)
        assert result.summary.risk_assessment == "low"

    def test_risk_assessment_high(self):
        """High risk when match rate is low."""
        pos = [PurchaseOrder(po_number=f"PO-{i}", vendor="A", total_amount=100, row_number=i) for i in range(1, 11)]
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, [], [], config)
        assert result.summary.risk_assessment == "high"

    def test_summary_to_dict(self):
        """Summary serializes correctly."""
        s = ThreeWayMatchSummary(
            total_pos=10, total_invoices=8, total_receipts=9,
            full_match_count=7, partial_match_count=1,
        )
        d = s.to_dict()
        assert d["total_pos"] == 10
        assert d["full_match_count"] == 7
        assert "risk_assessment" in d


class TestEdgeCases:
    """Edge cases for the matching algorithm."""

    def test_empty_all_files(self):
        """No crash when all files are empty."""
        result = run_three_way_match([], [], [])
        assert len(result.full_matches) == 0
        assert len(result.partial_matches) == 0
        assert result.summary.total_pos == 0

    def test_single_row_each(self):
        """Single row per file matches correctly."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="X", total_amount=100, quantity=5, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="X", total_amount=100, quantity=5, row_number=1)]
        receipts = [Receipt(po_reference="PO-001", vendor="X", quantity_received=5, row_number=1)]
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.full_matches) == 1

    def test_all_unmatched(self):
        """All documents unmatched when no PO refs and fuzzy disabled."""
        pos = [PurchaseOrder(vendor="A", total_amount=100, row_number=1)]
        invoices = [Invoice(vendor="B", total_amount=200, row_number=1)]
        receipts = [Receipt(vendor="C", quantity_received=5, row_number=1)]
        config = ThreeWayMatchConfig(enable_fuzzy_matching=False)
        result = run_three_way_match(pos, invoices, receipts, config)
        assert len(result.unmatched_pos) == 1
        assert len(result.unmatched_invoices) == 1
        assert len(result.unmatched_receipts) == 1

    def test_large_dataset(self):
        """Performance sanity check with 100 rows each."""
        pos = [PurchaseOrder(po_number=f"PO-{i:03d}", vendor=f"Vendor-{i}", total_amount=i * 100, quantity=i, row_number=i) for i in range(1, 101)]
        invoices = [Invoice(po_reference=f"PO-{i:03d}", vendor=f"Vendor-{i}", total_amount=i * 100, quantity=i, row_number=i) for i in range(1, 101)]
        receipts = [Receipt(po_reference=f"PO-{i:03d}", vendor=f"Vendor-{i}", quantity_received=i, row_number=i) for i in range(1, 101)]
        result = run_three_way_match(pos, invoices, receipts)
        assert result.summary.full_match_count == 100
        assert len(result.unmatched_pos) == 0

    def test_whitespace_po_numbers(self):
        """PO numbers with whitespace are trimmed before matching."""
        pos = [PurchaseOrder(po_number=" PO-001 ", vendor="A", total_amount=100, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="A", total_amount=100, row_number=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        assert len(result.partial_matches) == 1


class TestSerialization:
    """Tests for result serialization."""

    def test_three_way_match_to_dict(self):
        """ThreeWayMatch serializes to dict."""
        m = ThreeWayMatch(
            po=PurchaseOrder(po_number="PO-001", row_number=1),
            invoice=Invoice(invoice_number="INV-001", row_number=1),
            receipt=None,
            match_type="exact_po",
            match_confidence=0.95,
        )
        d = m.to_dict()
        assert d["po"]["po_number"] == "PO-001"
        assert d["invoice"]["invoice_number"] == "INV-001"
        assert d["receipt"] is None
        assert d["match_type"] == "exact_po"

    def test_full_result_to_dict(self):
        """ThreeWayMatchResult serializes completely."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="A", total_amount=100, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="A", total_amount=100, row_number=1)]
        receipts = [Receipt(po_reference="PO-001", vendor="A", quantity_received=5, row_number=1)]
        result = run_three_way_match(pos, invoices, receipts)
        d = result.to_dict()
        assert "full_matches" in d
        assert "partial_matches" in d
        assert "unmatched_pos" in d
        assert "summary" in d
        assert "variances" in d
        assert "config" in d

    def test_result_json_safe(self):
        """Result can be serialized to JSON."""
        import json
        pos = [PurchaseOrder(po_number="PO-001", vendor="Test", total_amount=100, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="Test", total_amount=105, row_number=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        json_str = json.dumps(result.to_dict())
        assert len(json_str) > 0

    def test_variance_in_result(self):
        """Variances are included in result."""
        pos = [PurchaseOrder(po_number="PO-001", vendor="A", total_amount=1000, row_number=1)]
        invoices = [Invoice(po_reference="PO-001", vendor="A", total_amount=1200, row_number=1)]
        receipts = []
        result = run_three_way_match(pos, invoices, receipts)
        d = result.to_dict()
        assert len(d["variances"]) > 0
        assert d["variances"][0]["field"] == "amount"


class TestAPIRouteRegistration:
    """Tests for API route registration."""

    def test_route_registered(self):
        from main import app
        routes = [r.path for r in app.routes]
        assert "/audit/three-way-match" in routes

    def test_post_method(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/audit/three-way-match":
                assert "POST" in route.methods

    def test_router_tag(self):
        from routes.three_way_match import router
        assert "three_way_match" in router.tags

    def test_router_in_all_routers(self):
        from routes import all_routers
        from routes.three_way_match import router
        assert router in all_routers
