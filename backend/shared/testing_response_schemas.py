"""
Paciolus API — Testing Tool Response Models
Sprints 218-219: Phase XXIX — API Integration Hardening

Typed Pydantic models replacing response_model=dict for:
- Journal Entry Testing (JE)
- AP Payment Testing (AP)
- Bank Reconciliation
- Three-Way Match (TWM)
- AR Aging Analysis
- Payroll Testing
- Revenue Testing
- Fixed Asset Testing
- Inventory Testing
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict


# ═══════════════════════════════════════════════════════════════
# Shared Models (reused across tools)
# ═══════════════════════════════════════════════════════════════

class CompositeScoreResponse(BaseModel):
    """Testing composite score — shared by JE and AP."""
    score: float
    risk_tier: Literal["low", "elevated", "moderate", "high", "critical"]
    tests_run: int
    total_entries: int
    total_flagged: int
    flag_rate: float
    flags_by_severity: Dict[str, int]
    top_findings: List[str]


class DataQualityResponse(BaseModel):
    """Data quality assessment — shared by JE and AP."""
    completeness_score: float
    field_fill_rates: Dict[str, float]
    detected_issues: List[str]
    total_rows: int


class BenfordAnalysisResponse(BaseModel):
    """Benford's Law first-digit analysis — shared by JE (and Payroll/Revenue in Sprint 219)."""
    passed_prechecks: bool
    precheck_message: Optional[str] = None
    eligible_count: int
    total_count: int
    expected_distribution: Dict[str, float]
    actual_distribution: Dict[str, float]
    actual_counts: Dict[str, int]
    deviation_by_digit: Dict[str, float]
    mad: float
    chi_squared: float
    conformity_level: str
    most_deviated_digits: List[int]


# ═══════════════════════════════════════════════════════════════
# Journal Entry Testing
# ═══════════════════════════════════════════════════════════════

class JournalEntryResponse(BaseModel):
    """Individual parsed journal entry."""
    entry_id: Optional[str] = None
    entry_date: Optional[str] = None
    posting_date: Optional[str] = None
    account: str
    description: Optional[str] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    posted_by: Optional[str] = None
    source: Optional[str] = None
    reference: Optional[str] = None
    currency: Optional[str] = None
    row_number: int


class JEFlaggedEntryResponse(BaseModel):
    """Flagged journal entry with test metadata."""
    entry: JournalEntryResponse
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    severity: Literal["high", "medium", "low"]
    issue: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


class JETestResultResponse(BaseModel):
    """Single JE test result with flagged entries."""
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Literal["high", "medium", "low"]
    description: str
    flagged_entries: List[JEFlaggedEntryResponse]


class GLColumnDetectionResponse(BaseModel):
    """GL column auto-detection result."""
    date_column: Optional[str] = None
    account_column: Optional[str] = None
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    amount_column: Optional[str] = None
    entry_date_column: Optional[str] = None
    posting_date_column: Optional[str] = None
    description_column: Optional[str] = None
    reference_column: Optional[str] = None
    posted_by_column: Optional[str] = None
    source_column: Optional[str] = None
    currency_column: Optional[str] = None
    entry_id_column: Optional[str] = None
    has_dual_dates: bool
    has_separate_debit_credit: bool
    overall_confidence: float
    requires_mapping: bool
    all_columns: List[str]
    detection_notes: List[str]


class MultiCurrencyWarningResponse(BaseModel):
    """Multi-currency detection warning."""
    currencies_found: List[str]
    primary_currency: Optional[str] = None
    entry_counts_by_currency: Dict[str, int]
    warning_message: str


class SamplingStratumResponse(BaseModel):
    """Stratified sampling stratum."""
    name: str
    criteria: str
    population_size: int
    sample_size: int
    sampled_rows: List[int]


class SamplingResultResponse(BaseModel):
    """Stratified sampling result — standalone endpoint response."""
    total_population: int
    total_sampled: int
    strata: List[SamplingStratumResponse]
    sampled_entries: List[JournalEntryResponse]
    sampling_seed: str
    parameters: Dict[str, Any]


class JETestingResponse(BaseModel):
    """Complete journal entry testing response.

    Uses extra='allow' as a safety net during migration — any fields
    not yet modeled still pass through to the frontend.
    """
    model_config = ConfigDict(extra="allow")

    composite_score: CompositeScoreResponse
    test_results: List[JETestResultResponse]
    data_quality: Optional[DataQualityResponse] = None
    multi_currency_warning: Optional[MultiCurrencyWarningResponse] = None
    column_detection: Optional[GLColumnDetectionResponse] = None
    benford_result: Optional[BenfordAnalysisResponse] = None
    sampling_result: Optional[Dict[str, Any]] = None


# ═══════════════════════════════════════════════════════════════
# AP Payment Testing
# ═══════════════════════════════════════════════════════════════

class APPaymentResponse(BaseModel):
    """Individual parsed AP payment entry."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    payment_date: Optional[str] = None
    vendor_name: str
    vendor_id: Optional[str] = None
    amount: float
    check_number: Optional[str] = None
    description: Optional[str] = None
    gl_account: Optional[str] = None
    payment_method: Optional[str] = None
    row_number: int


class APFlaggedEntryResponse(BaseModel):
    """Flagged AP payment entry with test metadata."""
    entry: APPaymentResponse
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    severity: Literal["high", "medium", "low"]
    issue: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


class APTestResultResponse(BaseModel):
    """Single AP test result with flagged entries."""
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Literal["high", "medium", "low"]
    description: str
    flagged_entries: List[APFlaggedEntryResponse]


class APColumnDetectionResponse(BaseModel):
    """AP column auto-detection result."""
    vendor_name_column: Optional[str] = None
    amount_column: Optional[str] = None
    payment_date_column: Optional[str] = None
    invoice_number_column: Optional[str] = None
    invoice_date_column: Optional[str] = None
    vendor_id_column: Optional[str] = None
    check_number_column: Optional[str] = None
    description_column: Optional[str] = None
    gl_account_column: Optional[str] = None
    payment_method_column: Optional[str] = None
    has_dual_dates: bool
    has_check_numbers: bool
    overall_confidence: float
    requires_mapping: bool
    all_columns: List[str]
    detection_notes: List[str]


class APTestingResponse(BaseModel):
    """Complete AP payment testing response.

    Uses extra='allow' as a safety net during migration.
    """
    model_config = ConfigDict(extra="allow")

    composite_score: CompositeScoreResponse
    test_results: List[APTestResultResponse]
    data_quality: Optional[DataQualityResponse] = None
    column_detection: Optional[APColumnDetectionResponse] = None


# ═══════════════════════════════════════════════════════════════
# Bank Reconciliation
# ═══════════════════════════════════════════════════════════════

class TransactionResponse(BaseModel):
    """Bank or ledger transaction."""
    date: Optional[str] = None
    description: str
    amount: float
    reference: Optional[str] = None
    row_number: int


class ReconciliationMatchResponse(BaseModel):
    """Single reconciliation match pair."""
    bank_txn: Optional[TransactionResponse] = None
    ledger_txn: Optional[TransactionResponse] = None
    match_type: Literal["matched", "bank_only", "ledger_only"]
    match_confidence: float


class ReconciliationSummaryResponse(BaseModel):
    """Reconciliation summary with match statistics."""
    matched_count: int
    matched_amount: float
    bank_only_count: int
    bank_only_amount: float
    ledger_only_count: int
    ledger_only_amount: float
    reconciling_difference: float
    total_bank: float
    total_ledger: float
    matches: List[ReconciliationMatchResponse]


class BankColumnDetectionResponse(BaseModel):
    """Bank/ledger column auto-detection result."""
    date_column: Optional[str] = None
    amount_column: Optional[str] = None
    description_column: Optional[str] = None
    reference_column: Optional[str] = None
    balance_column: Optional[str] = None
    overall_confidence: float
    requires_mapping: bool
    all_columns: List[str]
    detection_notes: List[str]


class BankRecResponse(BaseModel):
    """Complete bank reconciliation response."""
    summary: ReconciliationSummaryResponse
    bank_column_detection: BankColumnDetectionResponse
    ledger_column_detection: BankColumnDetectionResponse


# ═══════════════════════════════════════════════════════════════
# Three-Way Match
# ═══════════════════════════════════════════════════════════════

class PurchaseOrderResponse(BaseModel):
    """Individual purchase order."""
    po_number: Optional[str] = None
    vendor: str
    description: str
    quantity: float
    unit_price: float
    total_amount: float
    order_date: Optional[str] = None
    expected_delivery: Optional[str] = None
    approver: Optional[str] = None
    department: Optional[str] = None
    row_number: int


class InvoiceResponse(BaseModel):
    """Individual invoice."""
    invoice_number: Optional[str] = None
    po_reference: Optional[str] = None
    vendor: str
    description: str
    quantity: float
    unit_price: float
    total_amount: float
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    row_number: int


class ReceiptResponse(BaseModel):
    """Individual receipt."""
    receipt_number: Optional[str] = None
    po_reference: Optional[str] = None
    invoice_reference: Optional[str] = None
    vendor: str
    description: str
    quantity_received: float
    receipt_date: Optional[str] = None
    received_by: Optional[str] = None
    condition: Optional[str] = None
    row_number: int


class MatchVarianceResponse(BaseModel):
    """Variance between matched documents."""
    field: str
    po_value: Optional[float] = None
    invoice_value: Optional[float] = None
    receipt_value: Optional[float] = None
    variance_amount: float
    variance_pct: float
    severity: Literal["high", "medium", "low"]


class ThreeWayMatchItemResponse(BaseModel):
    """Single three-way match result (full or partial)."""
    po: Optional[PurchaseOrderResponse] = None
    invoice: Optional[InvoiceResponse] = None
    receipt: Optional[ReceiptResponse] = None
    match_type: Literal["exact_po", "fuzzy", "partial"]
    match_confidence: float
    variances: List[MatchVarianceResponse]


class UnmatchedDocumentResponse(BaseModel):
    """Unmatched PO, invoice, or receipt."""
    document: Dict[str, Any]
    document_type: Literal["purchase_order", "invoice", "receipt"]
    reason: str


class ThreeWayMatchSummaryResponse(BaseModel):
    """Summary statistics for three-way match."""
    total_pos: int
    total_invoices: int
    total_receipts: int
    full_match_count: int
    partial_match_count: int
    full_match_rate: float
    partial_match_rate: float
    total_po_amount: float
    total_invoice_amount: float
    total_receipt_amount: float
    net_variance: float
    material_variances_count: int
    risk_assessment: Literal["low", "medium", "high"]


class ThreeWayMatchDataQualityResponse(BaseModel):
    """Data quality assessment for three-way match."""
    po_count: int
    invoice_count: int
    receipt_count: int
    po_vendor_fill_rate: float
    po_amount_fill_rate: float
    po_number_fill_rate: float
    invoice_vendor_fill_rate: float
    invoice_amount_fill_rate: float
    invoice_number_fill_rate: float
    invoice_po_ref_fill_rate: float
    receipt_vendor_fill_rate: float
    receipt_qty_fill_rate: float
    receipt_po_ref_fill_rate: float
    overall_quality_score: float
    detected_issues: List[str]


class ThreeWayMatchConfigResponse(BaseModel):
    """Three-way match configuration parameters."""
    amount_tolerance: float
    quantity_tolerance: float
    date_window_days: int
    fuzzy_vendor_threshold: float
    enable_fuzzy_matching: bool
    price_variance_threshold: float
    fuzzy_composite_threshold: float


class POColumnDetectionResponse(BaseModel):
    """PO column auto-detection result."""
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
    overall_confidence: float
    all_columns: List[str]
    detection_notes: List[str]
    requires_mapping: bool


class InvoiceColumnDetectionResponse(BaseModel):
    """Invoice column auto-detection result."""
    invoice_number_column: Optional[str] = None
    po_reference_column: Optional[str] = None
    vendor_column: Optional[str] = None
    description_column: Optional[str] = None
    quantity_column: Optional[str] = None
    unit_price_column: Optional[str] = None
    total_amount_column: Optional[str] = None
    invoice_date_column: Optional[str] = None
    due_date_column: Optional[str] = None
    overall_confidence: float
    all_columns: List[str]
    detection_notes: List[str]
    requires_mapping: bool


class ReceiptColumnDetectionResponse(BaseModel):
    """Receipt column auto-detection result."""
    receipt_number_column: Optional[str] = None
    po_reference_column: Optional[str] = None
    invoice_reference_column: Optional[str] = None
    vendor_column: Optional[str] = None
    description_column: Optional[str] = None
    quantity_received_column: Optional[str] = None
    receipt_date_column: Optional[str] = None
    received_by_column: Optional[str] = None
    condition_column: Optional[str] = None
    overall_confidence: float
    all_columns: List[str]
    detection_notes: List[str]
    requires_mapping: bool


class TWMColumnDetectionResponse(BaseModel):
    """Typed column detection for all three document types."""
    po: POColumnDetectionResponse
    invoice: InvoiceColumnDetectionResponse
    receipt: ReceiptColumnDetectionResponse


class ThreeWayMatchResponse(BaseModel):
    """Complete three-way match response.

    Uses extra='allow' as a safety net during migration.
    """
    model_config = ConfigDict(extra="allow")

    full_matches: List[ThreeWayMatchItemResponse]
    partial_matches: List[ThreeWayMatchItemResponse]
    unmatched_pos: List[UnmatchedDocumentResponse]
    unmatched_invoices: List[UnmatchedDocumentResponse]
    unmatched_receipts: List[UnmatchedDocumentResponse]
    summary: ThreeWayMatchSummaryResponse
    variances: List[MatchVarianceResponse]
    data_quality: ThreeWayMatchDataQualityResponse
    column_detection: TWMColumnDetectionResponse
    config: ThreeWayMatchConfigResponse


# ═══════════════════════════════════════════════════════════════
# AR Aging Analysis
# ═══════════════════════════════════════════════════════════════

class AREntryResponse(BaseModel):
    """Individual AR entry (from TB or sub-ledger)."""
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    customer_name: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    amount: float
    aging_days: Optional[int] = None
    row_number: int
    entry_source: Literal["tb", "subledger", "reconciliation", "analysis"]


class ARFlaggedEntryResponse(BaseModel):
    """Flagged AR entry with test metadata."""
    entry: AREntryResponse
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    severity: Literal["high", "medium", "low"]
    issue: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


class ARTestResultResponse(BaseModel):
    """Single AR test result with flagged entries."""
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Literal["high", "medium", "low"]
    description: str
    flagged_entries: List[ARFlaggedEntryResponse]
    skipped: bool
    skip_reason: Optional[str] = None


class ARCompositeScoreResponse(BaseModel):
    """AR composite score — differs from shared (tests_skipped, has_subledger)."""
    score: float
    risk_tier: Literal["low", "elevated", "moderate", "high", "critical"]
    tests_run: int
    tests_skipped: int
    total_flagged: int
    flags_by_severity: Dict[str, int]
    top_findings: List[str]
    has_subledger: bool


class ARDataQualityResponse(BaseModel):
    """AR data quality — differs from shared (tb/subledger counts)."""
    completeness_score: float
    field_fill_rates: Dict[str, float]
    detected_issues: List[str]
    total_tb_accounts: int
    total_subledger_entries: int
    has_subledger: bool


class ARTBColumnDetectionResponse(BaseModel):
    """AR trial balance column auto-detection result."""
    account_name_column: Optional[str] = None
    account_number_column: Optional[str] = None
    balance_column: Optional[str] = None
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    has_debit_credit: bool
    overall_confidence: float
    all_columns: List[str]
    detection_notes: List[str]


class ARSLColumnDetectionResponse(BaseModel):
    """AR sub-ledger column auto-detection result."""
    customer_name_column: Optional[str] = None
    customer_id_column: Optional[str] = None
    invoice_number_column: Optional[str] = None
    invoice_date_column: Optional[str] = None
    due_date_column: Optional[str] = None
    amount_column: Optional[str] = None
    aging_days_column: Optional[str] = None
    aging_bucket_column: Optional[str] = None
    credit_limit_column: Optional[str] = None
    overall_confidence: float
    all_columns: List[str]
    detection_notes: List[str]


class ARSummaryResponse(BaseModel):
    """AR aging summary — 6 required + 6 conditional fields."""
    total_ar_balance: float
    ar_account_count: int
    total_allowance: float
    allowance_account_count: int
    total_revenue: float
    has_subledger: bool
    # Conditional fields (present only when data allows calculation)
    dso: Optional[float] = None
    allowance_ratio: Optional[float] = None
    subledger_entry_count: Optional[int] = None
    subledger_total: Optional[float] = None
    aging_distribution: Optional[Dict[str, float]] = None
    unique_customers: Optional[int] = None


class ARAgingResponse(BaseModel):
    """Complete AR aging analysis response.

    Uses extra='allow' as a safety net during migration.
    """
    model_config = ConfigDict(extra="allow")

    composite_score: ARCompositeScoreResponse
    test_results: List[ARTestResultResponse]
    data_quality: Optional[ARDataQualityResponse] = None
    tb_column_detection: Optional[ARTBColumnDetectionResponse] = None
    sl_column_detection: Optional[ARSLColumnDetectionResponse] = None
    ar_summary: Optional[ARSummaryResponse] = None


# ═══════════════════════════════════════════════════════════════
# Payroll Testing
# ═══════════════════════════════════════════════════════════════

class PayrollEntryResponse(BaseModel):
    """Individual parsed payroll entry."""
    employee_id: Optional[str] = None
    employee_name: str
    department: Optional[str] = None
    pay_date: Optional[str] = None
    gross_pay: float
    net_pay: float
    deductions: float
    check_number: Optional[str] = None
    pay_type: Optional[str] = None
    hours: float
    rate: float
    term_date: Optional[str] = None
    bank_account: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    row_index: int


class PayrollFlaggedEntryResponse(BaseModel):
    """Flagged payroll entry with test metadata."""
    entry: PayrollEntryResponse
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    severity: Literal["high", "medium", "low"]
    issue: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


class PayrollTestResultResponse(BaseModel):
    """Single payroll test result with flagged entries."""
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Literal["high", "medium", "low"]
    description: str
    flagged_entries: List[PayrollFlaggedEntryResponse]


class PayrollColumnDetectionResponse(BaseModel):
    """Payroll column auto-detection result."""
    employee_name_column: Optional[str] = None
    gross_pay_column: Optional[str] = None
    pay_date_column: Optional[str] = None
    employee_id_column: Optional[str] = None
    department_column: Optional[str] = None
    net_pay_column: Optional[str] = None
    deductions_column: Optional[str] = None
    check_number_column: Optional[str] = None
    pay_type_column: Optional[str] = None
    hours_column: Optional[str] = None
    rate_column: Optional[str] = None
    term_date_column: Optional[str] = None
    bank_account_column: Optional[str] = None
    address_column: Optional[str] = None
    tax_id_column: Optional[str] = None
    has_check_numbers: bool
    has_term_dates: bool
    has_bank_accounts: bool
    has_addresses: bool
    has_tax_ids: bool
    overall_confidence: float
    requires_mapping: bool
    all_columns: List[str]
    detection_notes: List[str]


class PayrollCompositeScoreResponse(BaseModel):
    """Payroll composite score — top_findings are dicts, not strings."""
    score: float
    risk_tier: str
    tests_run: int
    total_entries: int
    total_flagged: int
    flag_rate: float
    flags_by_severity: Dict[str, int]
    top_findings: List[Dict[str, Any]]


class PayrollTestingResponse(BaseModel):
    """Complete payroll testing response.

    Uses extra='allow' as a safety net during migration.
    """
    model_config = ConfigDict(extra="allow")

    composite_score: PayrollCompositeScoreResponse
    test_results: List[PayrollTestResultResponse]
    data_quality: Optional[DataQualityResponse] = None
    column_detection: Optional[PayrollColumnDetectionResponse] = None
    filename: str


# ═══════════════════════════════════════════════════════════════
# Revenue Testing
# ═══════════════════════════════════════════════════════════════

class RevenueEntryResponse(BaseModel):
    """Individual parsed revenue GL entry."""
    date: Optional[str] = None
    amount: float
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    description: Optional[str] = None
    entry_type: Optional[str] = None
    reference: Optional[str] = None
    posted_by: Optional[str] = None
    row_number: int


class RevenueFlaggedEntryResponse(BaseModel):
    """Flagged revenue entry with test metadata."""
    entry: RevenueEntryResponse
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    severity: Literal["high", "medium", "low"]
    issue: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


class RevenueTestResultResponse(BaseModel):
    """Single revenue test result with flagged entries."""
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Literal["high", "medium", "low"]
    description: str
    flagged_entries: List[RevenueFlaggedEntryResponse]


class RevenueColumnDetectionResponse(BaseModel):
    """Revenue GL column auto-detection result."""
    date_column: Optional[str] = None
    amount_column: Optional[str] = None
    account_name_column: Optional[str] = None
    account_number_column: Optional[str] = None
    description_column: Optional[str] = None
    entry_type_column: Optional[str] = None
    reference_column: Optional[str] = None
    posted_by_column: Optional[str] = None
    overall_confidence: float
    requires_mapping: bool
    all_columns: List[str]
    detection_notes: List[str]


class RevenueTestingResponse(BaseModel):
    """Complete revenue testing response.

    Uses extra='allow' as a safety net during migration.
    """
    model_config = ConfigDict(extra="allow")

    composite_score: CompositeScoreResponse
    test_results: List[RevenueTestResultResponse]
    data_quality: Optional[DataQualityResponse] = None
    column_detection: Optional[RevenueColumnDetectionResponse] = None


# ═══════════════════════════════════════════════════════════════
# Fixed Asset Testing
# ═══════════════════════════════════════════════════════════════

class FixedAssetEntryResponse(BaseModel):
    """Individual parsed fixed asset entry."""
    asset_id: Optional[str] = None
    description: Optional[str] = None
    cost: float
    accumulated_depreciation: float
    acquisition_date: Optional[str] = None
    useful_life: Optional[float] = None
    depreciation_method: Optional[str] = None
    residual_value: float
    location: Optional[str] = None
    category: Optional[str] = None
    net_book_value: Optional[float] = None
    row_number: int


class FAFlaggedEntryResponse(BaseModel):
    """Flagged fixed asset entry with test metadata."""
    entry: FixedAssetEntryResponse
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    severity: Literal["high", "medium", "low"]
    issue: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


class FATestResultResponse(BaseModel):
    """Single fixed asset test result with flagged entries."""
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Literal["high", "medium", "low"]
    description: str
    flagged_entries: List[FAFlaggedEntryResponse]


class FAColumnDetectionResponse(BaseModel):
    """Fixed asset column auto-detection result."""
    asset_id_column: Optional[str] = None
    description_column: Optional[str] = None
    cost_column: Optional[str] = None
    accumulated_depreciation_column: Optional[str] = None
    acquisition_date_column: Optional[str] = None
    useful_life_column: Optional[str] = None
    depreciation_method_column: Optional[str] = None
    residual_value_column: Optional[str] = None
    location_column: Optional[str] = None
    category_column: Optional[str] = None
    net_book_value_column: Optional[str] = None
    overall_confidence: float
    requires_mapping: bool
    all_columns: List[str]
    detection_notes: List[str]


class FATestingResponse(BaseModel):
    """Complete fixed asset testing response.

    Uses extra='allow' as a safety net during migration.
    """
    model_config = ConfigDict(extra="allow")

    composite_score: CompositeScoreResponse
    test_results: List[FATestResultResponse]
    data_quality: Optional[DataQualityResponse] = None
    column_detection: Optional[FAColumnDetectionResponse] = None


# ═══════════════════════════════════════════════════════════════
# Inventory Testing
# ═══════════════════════════════════════════════════════════════

class InventoryEntryResponse(BaseModel):
    """Individual parsed inventory entry."""
    item_id: Optional[str] = None
    description: Optional[str] = None
    quantity: float
    unit_cost: float
    extended_value: float
    location: Optional[str] = None
    last_movement_date: Optional[str] = None
    category: Optional[str] = None
    row_number: int


class InvFlaggedEntryResponse(BaseModel):
    """Flagged inventory entry with test metadata."""
    entry: InventoryEntryResponse
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    severity: Literal["high", "medium", "low"]
    issue: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


class InvTestResultResponse(BaseModel):
    """Single inventory test result with flagged entries."""
    test_name: str
    test_key: str
    test_tier: Literal["structural", "statistical", "advanced"]
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Literal["high", "medium", "low"]
    description: str
    flagged_entries: List[InvFlaggedEntryResponse]


class InvColumnDetectionResponse(BaseModel):
    """Inventory column auto-detection result."""
    item_id_column: Optional[str] = None
    description_column: Optional[str] = None
    quantity_column: Optional[str] = None
    unit_cost_column: Optional[str] = None
    extended_value_column: Optional[str] = None
    location_column: Optional[str] = None
    last_movement_date_column: Optional[str] = None
    category_column: Optional[str] = None
    overall_confidence: float
    requires_mapping: bool
    all_columns: List[str]
    detection_notes: List[str]


class InvTestingResponse(BaseModel):
    """Complete inventory testing response.

    Uses extra='allow' as a safety net during migration.
    """
    model_config = ConfigDict(extra="allow")

    composite_score: CompositeScoreResponse
    test_results: List[InvTestResultResponse]
    data_quality: Optional[DataQualityResponse] = None
    column_detection: Optional[InvColumnDetectionResponse] = None
