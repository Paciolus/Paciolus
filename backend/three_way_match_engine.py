"""
Three-Way Match Validator Engine — Sprint 91-92

Matches purchase orders, invoices, and receipts/goods received notes
to validate AP completeness, detect variances, and identify procurement
anomalies.

Sprint 91: Data models, column detection, parsing, data quality, config
Sprint 92: Matching algorithm (exact PO# + fuzzy fallback), variance
  analysis, result aggregation, API endpoint

ZERO-STORAGE COMPLIANCE:
- All files processed in-memory only
- Match results are ephemeral (computed on demand)
- No raw procurement data is stored

Audit Standards References:
- ISA 505: External Confirmations
- ISA 500: Audit Evidence
- PCAOB AS 1105: Audit Evidence
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from typing import Optional

from shared.column_detector import ColumnFieldConfig, detect_columns
from shared.parsing_helpers import parse_date, safe_float, safe_str

# =============================================================================
# ENUMS
# =============================================================================

class MatchDocumentType(str, Enum):
    """Type of procurement document."""
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    RECEIPT = "receipt"


class MatchType(str, Enum):
    """How documents were matched."""
    EXACT_PO = "exact_po"      # Matched via PO number linkage
    FUZZY = "fuzzy"            # Matched via vendor+amount+date similarity
    PARTIAL = "partial"        # Only 2 of 3 documents matched


class MatchRiskLevel(str, Enum):
    """Overall risk assessment based on match rates and variances."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# =============================================================================
# PO COLUMN DETECTION
# =============================================================================

PO_NUMBER_PATTERNS = [
    (r"^po\s*#?$", 1.0, True),
    (r"^po\s*number$", 0.98, True),
    (r"^purchase\s*order\s*#?$", 0.98, True),
    (r"^purchase\s*order\s*number$", 0.95, True),
    (r"^po\s*no\.?$", 0.95, True),
    (r"^order\s*#?$", 0.85, True),
    (r"^order\s*number$", 0.85, True),
    (r"^po\s*id$", 0.90, True),
    (r"po.*num", 0.60, False),
    (r"purchase.*order", 0.55, False),
]

PO_VENDOR_PATTERNS = [
    (r"^vendor$", 0.95, True),
    (r"^vendor\s*name$", 0.98, True),
    (r"^supplier$", 0.95, True),
    (r"^supplier\s*name$", 0.98, True),
    (r"^company$", 0.70, True),
    (r"vendor", 0.55, False),
    (r"supplier", 0.55, False),
]

PO_DESCRIPTION_PATTERNS = [
    (r"^description$", 0.90, True),
    (r"^item\s*description$", 0.95, True),
    (r"^line\s*description$", 0.90, True),
    (r"^item$", 0.75, True),
    (r"^product$", 0.70, True),
    (r"^goods$", 0.70, True),
    (r"description", 0.55, False),
]

PO_QUANTITY_PATTERNS = [
    (r"^quantity$", 0.95, True),
    (r"^qty$", 0.95, True),
    (r"^qty\s*ordered$", 0.98, True),
    (r"^quantity\s*ordered$", 0.98, True),
    (r"^units$", 0.75, True),
    (r"^ordered$", 0.70, True),
    (r"quantity", 0.55, False),
    (r"qty", 0.55, False),
]

PO_UNIT_PRICE_PATTERNS = [
    (r"^unit\s*price$", 0.98, True),
    (r"^price$", 0.85, True),
    (r"^unit\s*cost$", 0.95, True),
    (r"^rate$", 0.70, True),
    (r"unit.*price", 0.60, False),
    (r"price", 0.50, False),
]

PO_TOTAL_AMOUNT_PATTERNS = [
    (r"^total$", 0.85, True),
    (r"^total\s*amount$", 0.98, True),
    (r"^amount$", 0.85, True),
    (r"^line\s*total$", 0.95, True),
    (r"^extended\s*amount$", 0.90, True),
    (r"^po\s*amount$", 0.95, True),
    (r"^order\s*amount$", 0.90, True),
    (r"total", 0.55, False),
    (r"amount", 0.50, False),
]

PO_ORDER_DATE_PATTERNS = [
    (r"^order\s*date$", 0.98, True),
    (r"^po\s*date$", 0.95, True),
    (r"^date\s*ordered$", 0.95, True),
    (r"^date$", 0.75, True),
    (r"^create\s*date$", 0.80, True),
    (r"order.*date", 0.60, False),
    (r"date", 0.40, False),
]

PO_EXPECTED_DELIVERY_PATTERNS = [
    (r"^expected\s*delivery$", 0.98, True),
    (r"^delivery\s*date$", 0.95, True),
    (r"^due\s*date$", 0.85, True),
    (r"^required\s*date$", 0.90, True),
    (r"^need\s*by$", 0.85, True),
    (r"delivery", 0.55, False),
]

PO_APPROVER_PATTERNS = [
    (r"^approver$", 0.95, True),
    (r"^approved\s*by$", 0.98, True),
    (r"^authorized\s*by$", 0.90, True),
    (r"^requestor$", 0.70, True),
    (r"approv", 0.55, False),
]

PO_DEPARTMENT_PATTERNS = [
    (r"^department$", 0.95, True),
    (r"^dept\.?$", 0.90, True),
    (r"^cost\s*center$", 0.85, True),
    (r"^division$", 0.80, True),
    (r"department", 0.55, False),
    (r"dept", 0.50, False),
]


# =============================================================================
# INVOICE COLUMN DETECTION
# =============================================================================

INV_NUMBER_PATTERNS = [
    (r"^invoice\s*#?$", 0.95, True),
    (r"^invoice\s*number$", 0.98, True),
    (r"^invoice\s*no\.?$", 0.95, True),
    (r"^inv\s*#?$", 0.90, True),
    (r"^inv\s*number$", 0.90, True),
    (r"^bill\s*number$", 0.85, True),
    (r"^bill\s*#?$", 0.85, True),
    (r"invoice.*num", 0.60, False),
    (r"inv.*num", 0.55, False),
]

INV_PO_REFERENCE_PATTERNS = [
    (r"^po\s*#?$", 0.90, True),
    (r"^po\s*number$", 0.95, True),
    (r"^po\s*reference$", 0.98, True),
    (r"^po\s*ref\.?$", 0.95, True),
    (r"^purchase\s*order$", 0.90, True),
    (r"^purchase\s*order\s*#?$", 0.90, True),
    (r"^order\s*ref\.?$", 0.85, True),
    (r"po.*ref", 0.60, False),
    (r"purchase.*order", 0.55, False),
]

INV_VENDOR_PATTERNS = PO_VENDOR_PATTERNS  # Reuse
INV_DESCRIPTION_PATTERNS = PO_DESCRIPTION_PATTERNS
INV_QUANTITY_PATTERNS = PO_QUANTITY_PATTERNS
INV_UNIT_PRICE_PATTERNS = PO_UNIT_PRICE_PATTERNS

INV_TOTAL_AMOUNT_PATTERNS = [
    (r"^total$", 0.85, True),
    (r"^total\s*amount$", 0.98, True),
    (r"^amount$", 0.85, True),
    (r"^invoice\s*amount$", 0.95, True),
    (r"^invoice\s*total$", 0.95, True),
    (r"^net\s*amount$", 0.85, True),
    (r"total", 0.55, False),
    (r"amount", 0.50, False),
]

INV_DATE_PATTERNS = [
    (r"^invoice\s*date$", 0.98, True),
    (r"^inv\s*date$", 0.95, True),
    (r"^bill\s*date$", 0.90, True),
    (r"^date$", 0.75, True),
    (r"invoice.*date", 0.60, False),
    (r"date", 0.40, False),
]

INV_DUE_DATE_PATTERNS = [
    (r"^due\s*date$", 0.98, True),
    (r"^payment\s*due$", 0.90, True),
    (r"^pay\s*by$", 0.85, True),
    (r"^due$", 0.80, True),
    (r"due.*date", 0.60, False),
]


# =============================================================================
# RECEIPT COLUMN DETECTION
# =============================================================================

REC_NUMBER_PATTERNS = [
    (r"^receipt\s*#?$", 0.95, True),
    (r"^receipt\s*number$", 0.98, True),
    (r"^grn\s*#?$", 0.90, True),
    (r"^grn\s*number$", 0.95, True),
    (r"^goods\s*received\s*#?$", 0.95, True),
    (r"^receiving\s*#?$", 0.85, True),
    (r"receipt.*num", 0.60, False),
    (r"grn", 0.55, False),
]

REC_PO_REFERENCE_PATTERNS = INV_PO_REFERENCE_PATTERNS  # Reuse

REC_INVOICE_REFERENCE_PATTERNS = [
    (r"^invoice\s*#?$", 0.85, True),
    (r"^invoice\s*number$", 0.90, True),
    (r"^invoice\s*ref\.?$", 0.95, True),
    (r"^inv\s*#?$", 0.85, True),
    (r"^inv\s*ref\.?$", 0.90, True),
    (r"invoice.*ref", 0.60, False),
]

REC_VENDOR_PATTERNS = PO_VENDOR_PATTERNS  # Reuse
REC_DESCRIPTION_PATTERNS = PO_DESCRIPTION_PATTERNS

REC_QUANTITY_RECEIVED_PATTERNS = [
    (r"^quantity\s*received$", 0.98, True),
    (r"^qty\s*received$", 0.98, True),
    (r"^received\s*qty$", 0.95, True),
    (r"^quantity$", 0.80, True),
    (r"^qty$", 0.80, True),
    (r"^received$", 0.70, True),
    (r"quantity.*rec", 0.60, False),
    (r"qty.*rec", 0.55, False),
]

REC_DATE_PATTERNS = [
    (r"^receipt\s*date$", 0.98, True),
    (r"^received\s*date$", 0.95, True),
    (r"^date\s*received$", 0.95, True),
    (r"^grn\s*date$", 0.90, True),
    (r"^date$", 0.75, True),
    (r"receipt.*date", 0.60, False),
    (r"receiv.*date", 0.55, False),
    (r"date", 0.40, False),
]

REC_RECEIVED_BY_PATTERNS = [
    (r"^received\s*by$", 0.98, True),
    (r"^receiver$", 0.90, True),
    (r"^inspector$", 0.85, True),
    (r"^checked\s*by$", 0.85, True),
    (r"received.*by", 0.60, False),
]

REC_CONDITION_PATTERNS = [
    (r"^condition$", 0.95, True),
    (r"^status$", 0.75, True),
    (r"^quality$", 0.80, True),
    (r"^inspection\s*result$", 0.90, True),
    (r"condition", 0.55, False),
]


# =============================================================================
# SHARED COLUMN DETECTOR CONFIGS (Sprint 151)
# =============================================================================

PO_COLUMN_CONFIGS: list[ColumnFieldConfig] = [
    ColumnFieldConfig("po_number_column", PO_NUMBER_PATTERNS, required=True,
                      missing_note="Required column not detected: po_number", priority=10),
    ColumnFieldConfig("vendor_column", PO_VENDOR_PATTERNS, required=True,
                      missing_note="Required column not detected: vendor", priority=15),
    ColumnFieldConfig("total_amount_column", PO_TOTAL_AMOUNT_PATTERNS, required=True,
                      missing_note="Required column not detected: total_amount", priority=20),
    ColumnFieldConfig("quantity_column", PO_QUANTITY_PATTERNS, priority=25),
    ColumnFieldConfig("unit_price_column", PO_UNIT_PRICE_PATTERNS, priority=30),
    ColumnFieldConfig("order_date_column", PO_ORDER_DATE_PATTERNS, priority=35),
    ColumnFieldConfig("expected_delivery_column", PO_EXPECTED_DELIVERY_PATTERNS, priority=40),
    ColumnFieldConfig("approver_column", PO_APPROVER_PATTERNS, priority=45),
    ColumnFieldConfig("department_column", PO_DEPARTMENT_PATTERNS, priority=50),
    ColumnFieldConfig("description_column", PO_DESCRIPTION_PATTERNS, priority=55),
]

INV_COLUMN_CONFIGS: list[ColumnFieldConfig] = [
    ColumnFieldConfig("invoice_number_column", INV_NUMBER_PATTERNS, required=True,
                      missing_note="Required column not detected: invoice_number", priority=10),
    ColumnFieldConfig("po_reference_column", INV_PO_REFERENCE_PATTERNS, priority=15),
    ColumnFieldConfig("vendor_column", INV_VENDOR_PATTERNS, required=True,
                      missing_note="Required column not detected: vendor", priority=20),
    ColumnFieldConfig("total_amount_column", INV_TOTAL_AMOUNT_PATTERNS, required=True,
                      missing_note="Required column not detected: total_amount", priority=25),
    ColumnFieldConfig("quantity_column", INV_QUANTITY_PATTERNS, priority=30),
    ColumnFieldConfig("unit_price_column", INV_UNIT_PRICE_PATTERNS, priority=35),
    ColumnFieldConfig("invoice_date_column", INV_DATE_PATTERNS, priority=40),
    ColumnFieldConfig("due_date_column", INV_DUE_DATE_PATTERNS, priority=45),
    ColumnFieldConfig("description_column", INV_DESCRIPTION_PATTERNS, priority=50),
]

REC_COLUMN_CONFIGS: list[ColumnFieldConfig] = [
    ColumnFieldConfig("receipt_number_column", REC_NUMBER_PATTERNS, priority=10),
    ColumnFieldConfig("po_reference_column", REC_PO_REFERENCE_PATTERNS, priority=15),
    ColumnFieldConfig("invoice_reference_column", REC_INVOICE_REFERENCE_PATTERNS, priority=20),
    ColumnFieldConfig("vendor_column", REC_VENDOR_PATTERNS, required=True,
                      missing_note="Required column not detected: vendor", priority=25),
    ColumnFieldConfig("quantity_received_column", REC_QUANTITY_RECEIVED_PATTERNS, required=True,
                      missing_note="Required column not detected: quantity_received", priority=30),
    ColumnFieldConfig("receipt_date_column", REC_DATE_PATTERNS, priority=35),
    ColumnFieldConfig("received_by_column", REC_RECEIVED_BY_PATTERNS, priority=40),
    ColumnFieldConfig("condition_column", REC_CONDITION_PATTERNS, priority=45),
    ColumnFieldConfig("description_column", REC_DESCRIPTION_PATTERNS, priority=50),
]


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ThreeWayMatchConfig:
    """Configurable thresholds for three-way matching."""
    amount_tolerance: float = 0.01          # Dollar tolerance for amount matching
    quantity_tolerance: float = 0.0          # Quantity tolerance (0 = exact match)
    date_window_days: int = 30              # Receipt within N days of PO delivery date
    fuzzy_vendor_threshold: float = 0.85    # SequenceMatcher ratio for vendor names
    enable_fuzzy_matching: bool = True       # Enable vendor+amount+date fallback
    price_variance_threshold: float = 0.05   # 5% price variance tolerance
    fuzzy_composite_threshold: float = 0.70  # Min composite score for fuzzy match

    def to_dict(self) -> dict:
        return {
            "amount_tolerance": self.amount_tolerance,
            "quantity_tolerance": self.quantity_tolerance,
            "date_window_days": self.date_window_days,
            "fuzzy_vendor_threshold": self.fuzzy_vendor_threshold,
            "enable_fuzzy_matching": self.enable_fuzzy_matching,
            "price_variance_threshold": self.price_variance_threshold,
            "fuzzy_composite_threshold": self.fuzzy_composite_threshold,
        }


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class PurchaseOrder:
    """A single purchase order line."""
    po_number: Optional[str] = None
    vendor: str = ""
    description: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    total_amount: float = 0.0
    order_date: Optional[str] = None
    expected_delivery: Optional[str] = None
    approver: Optional[str] = None
    department: Optional[str] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "po_number": self.po_number,
            "vendor": self.vendor,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "order_date": self.order_date,
            "expected_delivery": self.expected_delivery,
            "approver": self.approver,
            "department": self.department,
            "row_number": self.row_number,
        }


@dataclass
class Invoice:
    """A single invoice line."""
    invoice_number: Optional[str] = None
    po_reference: Optional[str] = None
    vendor: str = ""
    description: str = ""
    quantity: float = 0.0
    unit_price: float = 0.0
    total_amount: float = 0.0
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "invoice_number": self.invoice_number,
            "po_reference": self.po_reference,
            "vendor": self.vendor,
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_amount": self.total_amount,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "row_number": self.row_number,
        }


@dataclass
class Receipt:
    """A single receipt/goods received note line."""
    receipt_number: Optional[str] = None
    po_reference: Optional[str] = None
    invoice_reference: Optional[str] = None
    vendor: str = ""
    description: str = ""
    quantity_received: float = 0.0
    receipt_date: Optional[str] = None
    received_by: Optional[str] = None
    condition: Optional[str] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "receipt_number": self.receipt_number,
            "po_reference": self.po_reference,
            "invoice_reference": self.invoice_reference,
            "vendor": self.vendor,
            "description": self.description,
            "quantity_received": self.quantity_received,
            "receipt_date": self.receipt_date,
            "received_by": self.received_by,
            "condition": self.condition,
            "row_number": self.row_number,
        }


# =============================================================================
# COLUMN DETECTION RESULTS
# =============================================================================

@dataclass
class POColumnDetectionResult:
    """Column detection result for purchase order files."""
    po_number_column: Optional[str] = None
    vendor_column: Optional[str] = None
    description_column: Optional[str] = None
    quantity_column: Optional[str] = None
    unit_price_column: Optional[str] = None
    total_amount_column: Optional[str] = None
    order_date_column: Optional[str] = None
    expected_delivery_column: Optional[str] = None
    approver_column: Optional[str] = None
    department_column: Optional[str] = None
    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "po_number_column": self.po_number_column,
            "vendor_column": self.vendor_column,
            "description_column": self.description_column,
            "quantity_column": self.quantity_column,
            "unit_price_column": self.unit_price_column,
            "total_amount_column": self.total_amount_column,
            "order_date_column": self.order_date_column,
            "expected_delivery_column": self.expected_delivery_column,
            "approver_column": self.approver_column,
            "department_column": self.department_column,
            "overall_confidence": round(self.overall_confidence, 4),
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
            "requires_mapping": self.requires_mapping,
        }


@dataclass
class InvoiceColumnDetectionResult:
    """Column detection result for invoice files."""
    invoice_number_column: Optional[str] = None
    po_reference_column: Optional[str] = None
    vendor_column: Optional[str] = None
    description_column: Optional[str] = None
    quantity_column: Optional[str] = None
    unit_price_column: Optional[str] = None
    total_amount_column: Optional[str] = None
    invoice_date_column: Optional[str] = None
    due_date_column: Optional[str] = None
    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "invoice_number_column": self.invoice_number_column,
            "po_reference_column": self.po_reference_column,
            "vendor_column": self.vendor_column,
            "description_column": self.description_column,
            "quantity_column": self.quantity_column,
            "unit_price_column": self.unit_price_column,
            "total_amount_column": self.total_amount_column,
            "invoice_date_column": self.invoice_date_column,
            "due_date_column": self.due_date_column,
            "overall_confidence": round(self.overall_confidence, 4),
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
            "requires_mapping": self.requires_mapping,
        }


@dataclass
class ReceiptColumnDetectionResult:
    """Column detection result for receipt/GRN files."""
    receipt_number_column: Optional[str] = None
    po_reference_column: Optional[str] = None
    invoice_reference_column: Optional[str] = None
    vendor_column: Optional[str] = None
    description_column: Optional[str] = None
    quantity_received_column: Optional[str] = None
    receipt_date_column: Optional[str] = None
    received_by_column: Optional[str] = None
    condition_column: Optional[str] = None
    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "receipt_number_column": self.receipt_number_column,
            "po_reference_column": self.po_reference_column,
            "invoice_reference_column": self.invoice_reference_column,
            "vendor_column": self.vendor_column,
            "description_column": self.description_column,
            "quantity_received_column": self.quantity_received_column,
            "receipt_date_column": self.receipt_date_column,
            "received_by_column": self.received_by_column,
            "condition_column": self.condition_column,
            "overall_confidence": round(self.overall_confidence, 4),
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
            "requires_mapping": self.requires_mapping,
        }


# =============================================================================
# COLUMN DETECTION FUNCTIONS
# =============================================================================

def detect_po_columns(column_names: list[str]) -> POColumnDetectionResult:
    """Detect PO column types using shared column detector."""
    result = POColumnDetectionResult(all_columns=list(column_names))
    if not column_names:
        return result

    det = detect_columns(column_names, PO_COLUMN_CONFIGS)
    result.all_columns = det.all_columns

    for cfg in PO_COLUMN_CONFIGS:
        col = det.get_column(cfg.field_name)
        if col:
            setattr(result, cfg.field_name, col)

    # Confidence: min of required columns (po_number, vendor, total_amount)
    required_fields = ["po_number_column", "vendor_column", "total_amount_column"]
    confidences = [
        det.get_confidence(f) if det.get_column(f) else 0.0
        for f in required_fields
    ]
    result.overall_confidence = min(confidences) if confidences else 0.0
    result.detection_notes = list(det.detection_notes)
    return result


def detect_invoice_columns(column_names: list[str]) -> InvoiceColumnDetectionResult:
    """Detect invoice column types using shared column detector."""
    result = InvoiceColumnDetectionResult(all_columns=list(column_names))
    if not column_names:
        return result

    det = detect_columns(column_names, INV_COLUMN_CONFIGS)
    result.all_columns = det.all_columns

    for cfg in INV_COLUMN_CONFIGS:
        col = det.get_column(cfg.field_name)
        if col:
            setattr(result, cfg.field_name, col)

    # Confidence: min of required columns (invoice_number, vendor, total_amount)
    required_fields = ["invoice_number_column", "vendor_column", "total_amount_column"]
    confidences = [
        det.get_confidence(f) if det.get_column(f) else 0.0
        for f in required_fields
    ]
    result.overall_confidence = min(confidences) if confidences else 0.0
    result.detection_notes = list(det.detection_notes)
    return result


def detect_receipt_columns(column_names: list[str]) -> ReceiptColumnDetectionResult:
    """Detect receipt/GRN column types using shared column detector."""
    result = ReceiptColumnDetectionResult(all_columns=list(column_names))
    if not column_names:
        return result

    det = detect_columns(column_names, REC_COLUMN_CONFIGS)
    result.all_columns = det.all_columns

    for cfg in REC_COLUMN_CONFIGS:
        col = det.get_column(cfg.field_name)
        if col:
            setattr(result, cfg.field_name, col)

    # Confidence: min of required columns (vendor, quantity_received)
    required_fields = ["vendor_column", "quantity_received_column"]
    confidences = [
        det.get_confidence(f) if det.get_column(f) else 0.0
        for f in required_fields
    ]
    result.overall_confidence = min(confidences) if confidences else 0.0
    result.detection_notes = list(det.detection_notes)
    return result


# =============================================================================
# PARSING
# =============================================================================

def parse_purchase_orders(
    rows: list[dict],
    detection: POColumnDetectionResult,
) -> list[PurchaseOrder]:
    """Parse raw rows into PurchaseOrder objects."""
    orders: list[PurchaseOrder] = []
    for idx, row in enumerate(rows):
        po = PurchaseOrder(row_number=idx + 1)
        if detection.po_number_column:
            po.po_number = safe_str(row.get(detection.po_number_column))
        if detection.vendor_column:
            po.vendor = safe_str(row.get(detection.vendor_column)) or ""
        if detection.description_column:
            po.description = safe_str(row.get(detection.description_column)) or ""
        if detection.quantity_column:
            po.quantity = safe_float(row.get(detection.quantity_column))
        if detection.unit_price_column:
            po.unit_price = safe_float(row.get(detection.unit_price_column))
        if detection.total_amount_column:
            po.total_amount = safe_float(row.get(detection.total_amount_column))
        if detection.order_date_column:
            po.order_date = safe_str(row.get(detection.order_date_column))
        if detection.expected_delivery_column:
            po.expected_delivery = safe_str(row.get(detection.expected_delivery_column))
        if detection.approver_column:
            po.approver = safe_str(row.get(detection.approver_column))
        if detection.department_column:
            po.department = safe_str(row.get(detection.department_column))
        orders.append(po)
    return orders


def parse_invoices(
    rows: list[dict],
    detection: InvoiceColumnDetectionResult,
) -> list[Invoice]:
    """Parse raw rows into Invoice objects."""
    invoices: list[Invoice] = []
    for idx, row in enumerate(rows):
        inv = Invoice(row_number=idx + 1)
        if detection.invoice_number_column:
            inv.invoice_number = safe_str(row.get(detection.invoice_number_column))
        if detection.po_reference_column:
            inv.po_reference = safe_str(row.get(detection.po_reference_column))
        if detection.vendor_column:
            inv.vendor = safe_str(row.get(detection.vendor_column)) or ""
        if detection.description_column:
            inv.description = safe_str(row.get(detection.description_column)) or ""
        if detection.quantity_column:
            inv.quantity = safe_float(row.get(detection.quantity_column))
        if detection.unit_price_column:
            inv.unit_price = safe_float(row.get(detection.unit_price_column))
        if detection.total_amount_column:
            inv.total_amount = safe_float(row.get(detection.total_amount_column))
        if detection.invoice_date_column:
            inv.invoice_date = safe_str(row.get(detection.invoice_date_column))
        if detection.due_date_column:
            inv.due_date = safe_str(row.get(detection.due_date_column))
        invoices.append(inv)
    return invoices


def parse_receipts(
    rows: list[dict],
    detection: ReceiptColumnDetectionResult,
) -> list[Receipt]:
    """Parse raw rows into Receipt objects."""
    receipts: list[Receipt] = []
    for idx, row in enumerate(rows):
        rec = Receipt(row_number=idx + 1)
        if detection.receipt_number_column:
            rec.receipt_number = safe_str(row.get(detection.receipt_number_column))
        if detection.po_reference_column:
            rec.po_reference = safe_str(row.get(detection.po_reference_column))
        if detection.invoice_reference_column:
            rec.invoice_reference = safe_str(row.get(detection.invoice_reference_column))
        if detection.vendor_column:
            rec.vendor = safe_str(row.get(detection.vendor_column)) or ""
        if detection.description_column:
            rec.description = safe_str(row.get(detection.description_column)) or ""
        if detection.quantity_received_column:
            rec.quantity_received = safe_float(row.get(detection.quantity_received_column))
        if detection.receipt_date_column:
            rec.receipt_date = safe_str(row.get(detection.receipt_date_column))
        if detection.received_by_column:
            rec.received_by = safe_str(row.get(detection.received_by_column))
        if detection.condition_column:
            rec.condition = safe_str(row.get(detection.condition_column))
        receipts.append(rec)
    return receipts


# =============================================================================
# DATA QUALITY
# =============================================================================

@dataclass
class ThreeWayMatchDataQuality:
    """Per-file and aggregate data quality assessment."""
    po_count: int = 0
    invoice_count: int = 0
    receipt_count: int = 0
    po_vendor_fill_rate: float = 0.0
    po_amount_fill_rate: float = 0.0
    po_number_fill_rate: float = 0.0
    invoice_vendor_fill_rate: float = 0.0
    invoice_amount_fill_rate: float = 0.0
    invoice_number_fill_rate: float = 0.0
    invoice_po_ref_fill_rate: float = 0.0
    receipt_vendor_fill_rate: float = 0.0
    receipt_qty_fill_rate: float = 0.0
    receipt_po_ref_fill_rate: float = 0.0
    overall_quality_score: float = 0.0
    detected_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "po_count": self.po_count,
            "invoice_count": self.invoice_count,
            "receipt_count": self.receipt_count,
            "po_vendor_fill_rate": round(self.po_vendor_fill_rate, 4),
            "po_amount_fill_rate": round(self.po_amount_fill_rate, 4),
            "po_number_fill_rate": round(self.po_number_fill_rate, 4),
            "invoice_vendor_fill_rate": round(self.invoice_vendor_fill_rate, 4),
            "invoice_amount_fill_rate": round(self.invoice_amount_fill_rate, 4),
            "invoice_number_fill_rate": round(self.invoice_number_fill_rate, 4),
            "invoice_po_ref_fill_rate": round(self.invoice_po_ref_fill_rate, 4),
            "receipt_vendor_fill_rate": round(self.receipt_vendor_fill_rate, 4),
            "receipt_qty_fill_rate": round(self.receipt_qty_fill_rate, 4),
            "receipt_po_ref_fill_rate": round(self.receipt_po_ref_fill_rate, 4),
            "overall_quality_score": round(self.overall_quality_score, 4),
            "detected_issues": self.detected_issues,
        }


def _fill_rate(items: list, accessor) -> float:
    """Calculate fill rate for a field across items."""
    if not items:
        return 0.0
    filled = sum(1 for item in items if accessor(item))
    return filled / len(items)


def assess_three_way_data_quality(
    pos: list[PurchaseOrder],
    invoices: list[Invoice],
    receipts: list[Receipt],
) -> ThreeWayMatchDataQuality:
    """Assess data quality across all three document sets."""
    dq = ThreeWayMatchDataQuality(
        po_count=len(pos),
        invoice_count=len(invoices),
        receipt_count=len(receipts),
    )

    # PO fill rates
    dq.po_vendor_fill_rate = _fill_rate(pos, lambda p: p.vendor)
    dq.po_amount_fill_rate = _fill_rate(pos, lambda p: p.total_amount != 0)
    dq.po_number_fill_rate = _fill_rate(pos, lambda p: p.po_number)

    # Invoice fill rates
    dq.invoice_vendor_fill_rate = _fill_rate(invoices, lambda i: i.vendor)
    dq.invoice_amount_fill_rate = _fill_rate(invoices, lambda i: i.total_amount != 0)
    dq.invoice_number_fill_rate = _fill_rate(invoices, lambda i: i.invoice_number)
    dq.invoice_po_ref_fill_rate = _fill_rate(invoices, lambda i: i.po_reference)

    # Receipt fill rates
    dq.receipt_vendor_fill_rate = _fill_rate(receipts, lambda r: r.vendor)
    dq.receipt_qty_fill_rate = _fill_rate(receipts, lambda r: r.quantity_received != 0)
    dq.receipt_po_ref_fill_rate = _fill_rate(receipts, lambda r: r.po_reference)

    # Quality issues
    if dq.po_number_fill_rate < 0.80:
        dq.detected_issues.append("Low PO number fill rate — matching will rely on fuzzy methods")
    if dq.invoice_po_ref_fill_rate < 0.50:
        dq.detected_issues.append("Low PO reference on invoices — linking to POs may be incomplete")
    if dq.receipt_po_ref_fill_rate < 0.50:
        dq.detected_issues.append("Low PO reference on receipts — linking to POs may be incomplete")

    # Overall score: weighted average of key fill rates
    weights = [
        (dq.po_number_fill_rate, 0.20),
        (dq.po_vendor_fill_rate, 0.10),
        (dq.po_amount_fill_rate, 0.10),
        (dq.invoice_number_fill_rate, 0.15),
        (dq.invoice_vendor_fill_rate, 0.10),
        (dq.invoice_amount_fill_rate, 0.10),
        (dq.invoice_po_ref_fill_rate, 0.10),
        (dq.receipt_vendor_fill_rate, 0.05),
        (dq.receipt_qty_fill_rate, 0.05),
        (dq.receipt_po_ref_fill_rate, 0.05),
    ]
    dq.overall_quality_score = sum(rate * w for rate, w in weights)

    return dq


# =============================================================================
# MATCHING ALGORITHM (Sprint 92)
# =============================================================================

@dataclass
class MatchVariance:
    """A variance detected between matched documents."""
    field: str              # quantity, amount, price, date
    po_value: Optional[float] = None
    invoice_value: Optional[float] = None
    receipt_value: Optional[float] = None
    variance_amount: float = 0.0
    variance_pct: float = 0.0
    severity: str = "low"   # high, medium, low

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "po_value": self.po_value,
            "invoice_value": self.invoice_value,
            "receipt_value": self.receipt_value,
            "variance_amount": round(self.variance_amount, 2),
            "variance_pct": round(self.variance_pct, 4),
            "severity": self.severity,
        }


@dataclass
class ThreeWayMatch:
    """A matched set of documents (any can be None for partial matches)."""
    po: Optional[PurchaseOrder] = None
    invoice: Optional[Invoice] = None
    receipt: Optional[Receipt] = None
    match_type: str = "exact_po"    # exact_po, fuzzy, partial
    match_confidence: float = 0.0
    variances: list[MatchVariance] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "po": self.po.to_dict() if self.po else None,
            "invoice": self.invoice.to_dict() if self.invoice else None,
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "match_type": self.match_type,
            "match_confidence": round(self.match_confidence, 4),
            "variances": [v.to_dict() for v in self.variances],
        }


@dataclass
class UnmatchedDocument:
    """A document that could not be matched."""
    document: dict = field(default_factory=dict)
    document_type: str = ""     # purchase_order, invoice, receipt
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "document": self.document,
            "document_type": self.document_type,
            "reason": self.reason,
        }


@dataclass
class ThreeWayMatchSummary:
    """Summary statistics for the matching results."""
    total_pos: int = 0
    total_invoices: int = 0
    total_receipts: int = 0
    full_match_count: int = 0
    partial_match_count: int = 0
    full_match_rate: float = 0.0
    partial_match_rate: float = 0.0
    total_po_amount: float = 0.0
    total_invoice_amount: float = 0.0
    total_receipt_amount: float = 0.0
    net_variance: float = 0.0
    material_variances_count: int = 0
    risk_assessment: str = "low"    # low, medium, high

    def to_dict(self) -> dict:
        return {
            "total_pos": self.total_pos,
            "total_invoices": self.total_invoices,
            "total_receipts": self.total_receipts,
            "full_match_count": self.full_match_count,
            "partial_match_count": self.partial_match_count,
            "full_match_rate": round(self.full_match_rate, 4),
            "partial_match_rate": round(self.partial_match_rate, 4),
            "total_po_amount": round(self.total_po_amount, 2),
            "total_invoice_amount": round(self.total_invoice_amount, 2),
            "total_receipt_amount": round(self.total_receipt_amount, 2),
            "net_variance": round(self.net_variance, 2),
            "material_variances_count": self.material_variances_count,
            "risk_assessment": self.risk_assessment,
        }


@dataclass
class ThreeWayMatchResult:
    """Complete three-way match results."""
    full_matches: list[ThreeWayMatch] = field(default_factory=list)
    partial_matches: list[ThreeWayMatch] = field(default_factory=list)
    unmatched_pos: list[UnmatchedDocument] = field(default_factory=list)
    unmatched_invoices: list[UnmatchedDocument] = field(default_factory=list)
    unmatched_receipts: list[UnmatchedDocument] = field(default_factory=list)
    summary: ThreeWayMatchSummary = field(default_factory=ThreeWayMatchSummary)
    variances: list[MatchVariance] = field(default_factory=list)
    data_quality: ThreeWayMatchDataQuality = field(default_factory=ThreeWayMatchDataQuality)
    column_detection: dict = field(default_factory=dict)
    config: ThreeWayMatchConfig = field(default_factory=ThreeWayMatchConfig)

    def to_dict(self) -> dict:
        return {
            "full_matches": [m.to_dict() for m in self.full_matches],
            "partial_matches": [m.to_dict() for m in self.partial_matches],
            "unmatched_pos": [u.to_dict() for u in self.unmatched_pos],
            "unmatched_invoices": [u.to_dict() for u in self.unmatched_invoices],
            "unmatched_receipts": [u.to_dict() for u in self.unmatched_receipts],
            "summary": self.summary.to_dict(),
            "variances": [v.to_dict() for v in self.variances],
            "data_quality": self.data_quality.to_dict(),
            "column_detection": self.column_detection,
            "config": self.config.to_dict(),
        }


# =============================================================================
# VARIANCE ANALYSIS
# =============================================================================

def _compute_variances(
    po: Optional[PurchaseOrder],
    invoice: Optional[Invoice],
    receipt: Optional[Receipt],
    config: ThreeWayMatchConfig,
) -> list[MatchVariance]:
    """Compute variances between matched documents."""
    variances: list[MatchVariance] = []

    # Amount variance: PO total vs Invoice total
    if po and invoice:
        po_amt = po.total_amount
        inv_amt = invoice.total_amount
        if po_amt != 0 or inv_amt != 0:
            diff = abs(po_amt - inv_amt)
            if abs(po_amt) > config.amount_tolerance:
                pct = diff / abs(po_amt)
            else:
                pct = 1.0  # 100% — near-zero base, cap variance percentage
            if diff > config.amount_tolerance:
                sev = "high" if pct > 0.10 else ("medium" if pct > 0.05 else "low")
                variances.append(MatchVariance(
                    field="amount",
                    po_value=po_amt,
                    invoice_value=inv_amt,
                    variance_amount=diff,
                    variance_pct=pct,
                    severity=sev,
                ))

    # Quantity variance: PO qty vs Receipt qty
    if po and receipt:
        po_qty = po.quantity
        rec_qty = receipt.quantity_received
        if po_qty != 0 or rec_qty != 0:
            diff = abs(po_qty - rec_qty)
            if abs(po_qty) > config.quantity_tolerance:
                pct = diff / abs(po_qty)
            else:
                pct = 1.0  # 100% — near-zero base, cap variance percentage
            if diff > config.quantity_tolerance:
                sev = "high" if pct > 0.10 else ("medium" if pct > 0.05 else "low")
                variances.append(MatchVariance(
                    field="quantity",
                    po_value=po_qty,
                    receipt_value=rec_qty,
                    variance_amount=diff,
                    variance_pct=pct,
                    severity=sev,
                ))

    # Price variance: PO unit_price vs Invoice unit_price
    if po and invoice and po.unit_price > 0 and invoice.unit_price > 0:
        diff = abs(po.unit_price - invoice.unit_price)
        if abs(po.unit_price) > config.price_variance_threshold:
            pct = diff / abs(po.unit_price)
        else:
            pct = 1.0  # 100% — near-zero base, cap variance percentage
        if pct > config.price_variance_threshold:
            sev = "high" if pct > 0.10 else ("medium" if pct > 0.05 else "low")
            variances.append(MatchVariance(
                field="price",
                po_value=po.unit_price,
                invoice_value=invoice.unit_price,
                variance_amount=diff,
                variance_pct=pct,
                severity=sev,
            ))

    # Date variance: receipt_date vs PO expected_delivery
    if po and receipt and po.expected_delivery and receipt.receipt_date:
        po_date = parse_date(po.expected_delivery)
        rec_date = parse_date(receipt.receipt_date)
        if po_date and rec_date:
            days_diff = abs((rec_date - po_date).days)
            if days_diff > config.date_window_days:
                sev = "high" if days_diff > 60 else ("medium" if days_diff > 30 else "low")
                variances.append(MatchVariance(
                    field="date",
                    po_value=float(days_diff),
                    variance_amount=float(days_diff),
                    variance_pct=0.0,
                    severity=sev,
                ))

    return variances


# =============================================================================
# MATCHING CORE
# =============================================================================

def _vendor_similarity(a: str, b: str) -> float:
    """Compute vendor name similarity using SequenceMatcher."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def run_three_way_match(
    pos: list[PurchaseOrder],
    invoices: list[Invoice],
    receipts: list[Receipt],
    config: Optional[ThreeWayMatchConfig] = None,
) -> ThreeWayMatchResult:
    """Run the three-way matching algorithm.

    Phase 1: Exact PO number linkage
    Phase 2: Fuzzy fallback (vendor + amount + date)

    Returns complete match results with variances and summary.
    """
    if config is None:
        config = ThreeWayMatchConfig()

    result = ThreeWayMatchResult(config=config)

    # Track which documents have been matched
    matched_po_ids: set[int] = set()     # row_number indices
    matched_inv_ids: set[int] = set()
    matched_rec_ids: set[int] = set()

    # Build lookup tables
    po_by_number: dict[str, list[PurchaseOrder]] = {}
    for po in pos:
        if po.po_number:
            po_by_number.setdefault(po.po_number.strip().upper(), []).append(po)

    inv_by_po_ref: dict[str, list[Invoice]] = {}
    for inv in invoices:
        if inv.po_reference:
            inv_by_po_ref.setdefault(inv.po_reference.strip().upper(), []).append(inv)

    rec_by_po_ref: dict[str, list[Receipt]] = {}
    for rec in receipts:
        if rec.po_reference:
            rec_by_po_ref.setdefault(rec.po_reference.strip().upper(), []).append(rec)

    rec_by_inv_ref: dict[str, list[Receipt]] = {}
    for rec in receipts:
        if rec.invoice_reference:
            rec_by_inv_ref.setdefault(rec.invoice_reference.strip().upper(), []).append(rec)

    # ---- PHASE 1: Exact PO Number Linkage ----
    for po_num, po_list in po_by_number.items():
        for po in po_list:
            if po.row_number in matched_po_ids:
                continue

            # Find invoice(s) with this PO reference
            linked_invoices = inv_by_po_ref.get(po_num, [])
            linked_invoice = None
            for inv in linked_invoices:
                if inv.row_number not in matched_inv_ids:
                    linked_invoice = inv
                    break

            # Find receipt(s) with this PO reference
            linked_receipts = rec_by_po_ref.get(po_num, [])
            linked_receipt = None
            for rec in linked_receipts:
                if rec.row_number not in matched_rec_ids:
                    linked_receipt = rec
                    break

            # Also try linking receipt via invoice reference
            if not linked_receipt and linked_invoice and linked_invoice.invoice_number:
                inv_key = linked_invoice.invoice_number.strip().upper()
                for rec in rec_by_inv_ref.get(inv_key, []):
                    if rec.row_number not in matched_rec_ids:
                        linked_receipt = rec
                        break

            if linked_invoice or linked_receipt:
                variances = _compute_variances(po, linked_invoice, linked_receipt, config)
                is_full = linked_invoice is not None and linked_receipt is not None
                match = ThreeWayMatch(
                    po=po,
                    invoice=linked_invoice,
                    receipt=linked_receipt,
                    match_type=MatchType.EXACT_PO.value,
                    match_confidence=0.95,
                    variances=variances,
                )

                matched_po_ids.add(po.row_number)
                if linked_invoice:
                    matched_inv_ids.add(linked_invoice.row_number)
                if linked_receipt:
                    matched_rec_ids.add(linked_receipt.row_number)

                if is_full:
                    result.full_matches.append(match)
                else:
                    result.partial_matches.append(match)
                result.variances.extend(variances)

    # ---- PHASE 2: Fuzzy Fallback ----
    if config.enable_fuzzy_matching:
        unmatched_pos_list = [po for po in pos if po.row_number not in matched_po_ids]
        unmatched_inv_list = [inv for inv in invoices if inv.row_number not in matched_inv_ids]
        unmatched_rec_list = [rec for rec in receipts if rec.row_number not in matched_rec_ids]

        for po in unmatched_pos_list:
            if po.row_number in matched_po_ids:
                continue

            best_inv, best_inv_score = None, 0.0
            for inv in unmatched_inv_list:
                if inv.row_number in matched_inv_ids:
                    continue
                # Compute composite score: vendor 40% + amount 30% + date 30%
                vendor_score = _vendor_similarity(po.vendor, inv.vendor)
                amount_score = 1.0 if abs(po.total_amount - inv.total_amount) <= config.amount_tolerance else (
                    max(0.0, 1.0 - abs(po.total_amount - inv.total_amount) / max(abs(po.total_amount), 0.01))
                )
                # Date score: order_date vs invoice_date proximity
                date_score = 0.5  # default if no dates
                if po.order_date and inv.invoice_date:
                    po_date = parse_date(po.order_date)
                    inv_date = parse_date(inv.invoice_date)
                    if po_date and inv_date:
                        days = abs((inv_date - po_date).days)
                        date_score = max(0.0, 1.0 - days / max(config.date_window_days, 1))

                composite = vendor_score * 0.40 + amount_score * 0.30 + date_score * 0.30
                if composite > best_inv_score and vendor_score >= config.fuzzy_vendor_threshold:
                    best_inv = inv
                    best_inv_score = composite

            best_rec, best_rec_score = None, 0.0
            for rec in unmatched_rec_list:
                if rec.row_number in matched_rec_ids:
                    continue
                vendor_score = _vendor_similarity(po.vendor, rec.vendor)
                if vendor_score < config.fuzzy_vendor_threshold:
                    continue
                qty_score = 1.0 if abs(po.quantity - rec.quantity_received) <= config.quantity_tolerance else (
                    max(0.0, 1.0 - abs(po.quantity - rec.quantity_received) / max(abs(po.quantity), 0.01))
                )
                composite = vendor_score * 0.50 + qty_score * 0.50
                if composite > best_rec_score:
                    best_rec = rec
                    best_rec_score = composite

            # Apply composite threshold
            if best_inv and best_inv_score >= config.fuzzy_composite_threshold:
                variances = _compute_variances(po, best_inv, best_rec if best_rec and best_rec_score >= config.fuzzy_composite_threshold else None, config)
                is_full = best_inv is not None and best_rec is not None and best_rec_score >= config.fuzzy_composite_threshold
                match = ThreeWayMatch(
                    po=po,
                    invoice=best_inv,
                    receipt=best_rec if is_full else None,
                    match_type=MatchType.FUZZY.value if is_full else MatchType.PARTIAL.value,
                    match_confidence=best_inv_score,
                    variances=variances,
                )

                matched_po_ids.add(po.row_number)
                matched_inv_ids.add(best_inv.row_number)
                if is_full and best_rec:
                    matched_rec_ids.add(best_rec.row_number)

                if is_full:
                    result.full_matches.append(match)
                else:
                    result.partial_matches.append(match)
                result.variances.extend(variances)

    # ---- Collect unmatched documents ----
    for po in pos:
        if po.row_number not in matched_po_ids:
            result.unmatched_pos.append(UnmatchedDocument(
                document=po.to_dict(),
                document_type=MatchDocumentType.PURCHASE_ORDER.value,
                reason="No matching invoice or receipt found",
            ))

    for inv in invoices:
        if inv.row_number not in matched_inv_ids:
            result.unmatched_invoices.append(UnmatchedDocument(
                document=inv.to_dict(),
                document_type=MatchDocumentType.INVOICE.value,
                reason="No matching purchase order found",
            ))

    for rec in receipts:
        if rec.row_number not in matched_rec_ids:
            result.unmatched_receipts.append(UnmatchedDocument(
                document=rec.to_dict(),
                document_type=MatchDocumentType.RECEIPT.value,
                reason="No matching purchase order or invoice found",
            ))

    # ---- Summary ----
    total_docs = max(len(pos), len(invoices), 1)
    summary = ThreeWayMatchSummary(
        total_pos=len(pos),
        total_invoices=len(invoices),
        total_receipts=len(receipts),
        full_match_count=len(result.full_matches),
        partial_match_count=len(result.partial_matches),
        full_match_rate=len(result.full_matches) / total_docs,
        partial_match_rate=len(result.partial_matches) / total_docs,
        total_po_amount=sum(po.total_amount for po in pos),
        total_invoice_amount=sum(inv.total_amount for inv in invoices),
        total_receipt_amount=0.0,  # Receipts don't always have amounts
        net_variance=abs(sum(po.total_amount for po in pos) - sum(inv.total_amount for inv in invoices)),
        material_variances_count=sum(1 for v in result.variances if v.severity in ("high", "medium")),
    )

    # Risk assessment
    match_rate = summary.full_match_rate + summary.partial_match_rate * 0.5
    if match_rate >= 0.90 and summary.material_variances_count == 0:
        summary.risk_assessment = MatchRiskLevel.LOW.value
    elif match_rate >= 0.70 and summary.material_variances_count <= 5:
        summary.risk_assessment = MatchRiskLevel.MEDIUM.value
    else:
        summary.risk_assessment = MatchRiskLevel.HIGH.value

    result.summary = summary
    return result
