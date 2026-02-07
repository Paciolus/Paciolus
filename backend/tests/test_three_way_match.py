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
