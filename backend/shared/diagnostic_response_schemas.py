"""
Paciolus API — Diagnostic Tool Response Models
Sprint 217: Phase XXIX — API Integration Hardening

Typed Pydantic models replacing response_model=dict for:
- Trial Balance audit
- Flux Analysis
- Prior Period comparison
- Multi-Period comparison (2-way and 3-way)
- Adjusting Entries
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict

# ═══════════════════════════════════════════════════════════════
# Flux Analysis
# ═══════════════════════════════════════════════════════════════

class FluxItemResponse(BaseModel):
    """Individual account period-over-period comparison."""
    account: str
    type: str
    current: float
    prior: float
    delta_amount: float
    delta_percent: Optional[float] = None
    display_percent: str
    is_new: bool
    is_removed: bool
    sign_flip: bool
    risk_level: Literal["high", "medium", "low", "none"]
    risk_reasons: list[str]


class FluxSummaryResponse(BaseModel):
    """Aggregate flux analysis statistics."""
    total_items: int
    high_risk_count: int
    medium_risk_count: int
    new_accounts: int
    removed_accounts: int
    threshold: float


class FluxDataResponse(BaseModel):
    """Flux analysis data: items + summary."""
    items: list[FluxItemResponse]
    summary: FluxSummaryResponse


class ReconScoreResponse(BaseModel):
    """Per-account reconciliation risk score."""
    account: str
    score: int
    band: Literal["high", "medium", "low"]
    factors: list[str]
    action: str


class ReconStatsResponse(BaseModel):
    """Reconciliation risk statistics by band."""
    high: int
    medium: int
    low: int


class ReconDataResponse(BaseModel):
    """Reconciliation readiness data: scores + stats."""
    scores: list[ReconScoreResponse]
    stats: ReconStatsResponse


class FluxAnalysisResponse(BaseModel):
    """Complete flux analysis response: flux + recon."""
    flux: FluxDataResponse
    recon: ReconDataResponse


# ═══════════════════════════════════════════════════════════════
# Prior Period Comparison
# ═══════════════════════════════════════════════════════════════

class CategoryVarianceResponse(BaseModel):
    """Balance sheet or income statement category variance."""
    category_key: str
    category_name: str
    current_value: float
    prior_value: float
    dollar_variance: float
    percent_variance: Optional[float] = None
    is_significant: bool
    direction: Literal["increase", "decrease", "unchanged"]


class RatioVarianceResponse(BaseModel):
    """Financial ratio variance between periods."""
    ratio_key: str
    ratio_name: str
    current_value: Optional[float] = None
    prior_value: Optional[float] = None
    point_change: Optional[float] = None
    is_significant: bool
    direction: Literal["increase", "decrease", "unchanged"]
    is_percentage: bool


class DiagnosticVarianceResponse(BaseModel):
    """Diagnostic metadata variance (debits, credits, anomaly count, rows)."""
    metric_key: str
    metric_name: str
    current_value: float
    prior_value: float
    variance: float
    direction: Literal["increase", "decrease", "unchanged"]


class PeriodComparisonResponse(BaseModel):
    """Complete prior period comparison response."""
    current_period_label: str
    prior_period_label: str
    prior_period_id: int
    comparison_timestamp: str
    balance_sheet_variances: list[CategoryVarianceResponse]
    income_statement_variances: list[CategoryVarianceResponse]
    ratio_variances: list[RatioVarianceResponse]
    diagnostic_variances: list[DiagnosticVarianceResponse]
    significant_variance_count: int
    total_categories_compared: int


# ═══════════════════════════════════════════════════════════════
# Multi-Period Comparison
# ═══════════════════════════════════════════════════════════════

class AccountMovementResponse(BaseModel):
    """Account movement between two periods."""
    account_name: str
    account_type: str
    prior_balance: float
    current_balance: float
    change_amount: float
    change_percent: Optional[float] = None
    movement_type: Literal[
        "new_account", "closed_account", "sign_change",
        "increase", "decrease", "unchanged",
    ]
    significance: Literal["material", "significant", "minor"]
    lead_sheet: str
    lead_sheet_name: str
    lead_sheet_category: str
    is_dormant: bool


class LeadSheetMovementSummaryResponse(BaseModel):
    """Lead sheet level movement summary with account details."""
    lead_sheet: str
    lead_sheet_name: str
    lead_sheet_category: str
    prior_total: float
    current_total: float
    net_change: float
    change_percent: Optional[float] = None
    account_count: int
    movements: list[AccountMovementResponse]


class MovementSummaryResponse(BaseModel):
    """2-way period comparison response."""
    prior_label: str
    current_label: str
    total_accounts: int
    movements_by_type: dict[str, int]
    movements_by_significance: dict[str, int]
    all_movements: list[AccountMovementResponse]
    lead_sheet_summaries: list[LeadSheetMovementSummaryResponse]
    significant_movements: list[AccountMovementResponse]
    new_accounts: list[str]
    closed_accounts: list[str]
    dormant_accounts: list[str]
    prior_total_debits: float
    prior_total_credits: float
    current_total_debits: float
    current_total_credits: float


class BudgetVarianceResponse(BaseModel):
    """Budget variance data for a single account."""
    budget_balance: float
    variance_amount: float
    variance_percent: Optional[float] = None
    variance_significance: Literal["material", "significant", "minor"]


class ThreeWayLeadSheetSummaryResponse(BaseModel):
    """Lead sheet summary with optional budget variance data."""
    lead_sheet: str
    lead_sheet_name: str
    lead_sheet_category: str
    prior_total: float
    current_total: float
    net_change: float
    change_percent: Optional[float] = None
    budget_total: Optional[float] = None
    budget_variance: Optional[float] = None
    budget_variance_percent: Optional[float] = None
    account_count: int


class ThreeWayMovementSummaryResponse(BaseModel):
    """3-way period comparison (Prior vs Current vs Budget) response."""
    prior_label: str
    current_label: str
    budget_label: str
    total_accounts: int
    movements_by_type: dict[str, int]
    movements_by_significance: dict[str, int]
    all_movements: list[dict[str, Any]]
    lead_sheet_summaries: list[ThreeWayLeadSheetSummaryResponse]
    significant_movements: list[dict[str, Any]]
    new_accounts: list[str]
    closed_accounts: list[str]
    dormant_accounts: list[str]
    prior_total_debits: float
    prior_total_credits: float
    current_total_debits: float
    current_total_credits: float
    budget_total_debits: float
    budget_total_credits: float
    budget_variances_by_significance: dict[str, int]
    accounts_over_budget: int
    accounts_under_budget: int
    accounts_on_budget: int


# ═══════════════════════════════════════════════════════════════
# Adjusting Entries
# ═══════════════════════════════════════════════════════════════

class AdjustmentLineResponse(BaseModel):
    """Individual line item in an adjusting entry."""
    account_name: str
    debit: float
    credit: float
    description: Optional[str] = None


class AdjustingEntryResponse(BaseModel):
    """Complete adjusting journal entry."""
    id: str
    reference: str
    description: str
    adjustment_type: Literal[
        "accrual", "deferral", "estimate",
        "error_correction", "reclassification", "other",
    ]
    status: Literal["proposed", "approved", "rejected", "posted"]
    lines: list[AdjustmentLineResponse]
    total_debits: float
    total_credits: float
    is_balanced: bool
    entry_total: float
    account_count: int
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    notes: Optional[str] = None
    is_reversing: bool


class AdjustedAccountBalanceResponse(BaseModel):
    """Account with unadjusted and adjusted balances."""
    account_name: str
    unadjusted_debit: float
    unadjusted_credit: float
    unadjusted_balance: float
    adjustment_debit: float
    adjustment_credit: float
    net_adjustment: float
    adjusted_debit: float
    adjusted_credit: float
    adjusted_balance: float
    has_adjustment: bool


class AdjustedTBTotalsResponse(BaseModel):
    """Aggregate totals for adjusted trial balance."""
    unadjusted_debits: float
    unadjusted_credits: float
    adjustment_debits: float
    adjustment_credits: float
    adjusted_debits: float
    adjusted_credits: float


class AdjustedTrialBalanceResponse(BaseModel):
    """Adjusted trial balance with all entries applied."""
    accounts: list[AdjustedAccountBalanceResponse]
    adjustments_applied: list[str]
    totals: AdjustedTBTotalsResponse
    is_balanced: bool
    adjustment_count: int
    accounts_with_adjustments_count: int
    generated_at: str


# ═══════════════════════════════════════════════════════════════
# Trial Balance Audit
# ═══════════════════════════════════════════════════════════════

class AbnormalBalanceSuggestionResponse(BaseModel):
    """Suggested classification for low-confidence accounts."""
    category: str
    confidence: float
    reason: str
    matched_keywords: list[str]


class AbnormalBalanceResponse(BaseModel):
    """Individual anomaly detected in trial balance.

    Uses extra='allow' because anomaly entries carry variable flags
    depending on anomaly type (suspense, concentration, rounding).
    """
    model_config = ConfigDict(extra="allow")

    # Core fields (always present)
    account: str
    type: str
    issue: str
    amount: float
    debit: float
    credit: float
    materiality: Literal["material", "immaterial"]
    category: str
    confidence: float
    matched_keywords: list[str]
    requires_review: bool
    anomaly_type: str
    expected_balance: Optional[str] = None
    actual_balance: Optional[str] = None
    severity: Literal["high", "medium", "low"]
    suggestions: list[AbnormalBalanceSuggestionResponse]

    # Optional: anomaly-type-specific flags added by _merge_anomalies()
    recommendation: Optional[str] = None
    is_suspense_account: Optional[bool] = None
    suspense_confidence: Optional[float] = None
    suspense_keywords: Optional[list[str]] = None
    has_concentration_risk: Optional[bool] = None
    concentration_percent: Optional[float] = None
    category_total: Optional[float] = None
    has_rounding_anomaly: Optional[bool] = None
    rounding_pattern: Optional[str] = None
    rounding_divisor: Optional[int] = None

    # Optional: multi-sheet only
    sheet_name: Optional[str] = None


class RiskSummaryAnomalyTypesResponse(BaseModel):
    """Anomaly type counts in risk summary."""
    natural_balance_violation: int = 0
    suspense_account: int = 0
    concentration_risk: int = 0
    rounding_anomaly: int = 0
    balance_sheet_imbalance: int = 0


class RiskSummaryResponse(BaseModel):
    """Aggregated risk metrics for trial balance."""
    total_anomalies: int
    high_severity: int
    medium_severity: int
    low_severity: int
    anomaly_types: RiskSummaryAnomalyTypesResponse


class ClassificationIssueResponse(BaseModel):
    """Individual structural COA validation issue."""
    account_number: str
    account_name: str
    issue_type: str
    description: str
    severity: Literal["high", "medium", "low"]
    confidence: float
    category: str
    suggested_action: str


class ClassificationQualityResponse(BaseModel):
    """Structural COA validation result."""
    issues: list[ClassificationIssueResponse]
    quality_score: float
    issue_counts: dict[str, int]
    total_issues: int


class ColumnDetectionResponse(BaseModel):
    """Column auto-detection result."""
    account_column: Optional[str] = None
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    account_confidence: float
    debit_confidence: float
    credit_confidence: float
    overall_confidence: float
    requires_mapping: bool
    all_columns: list[str]
    detection_notes: list[str]


class BalanceSheetValidationResponse(BaseModel):
    """Balance sheet equation (Assets = L + E) validation."""
    is_balanced: bool
    status: Literal[
        "balanced", "minor_imbalance",
        "moderate_imbalance", "significant_imbalance",
    ]
    total_assets: float
    total_liabilities: float
    total_equity: float
    liabilities_plus_equity: float
    difference: float
    abs_difference: float
    severity: Optional[Literal["high", "medium", "low"]] = None
    recommendation: str
    equation: str


class SheetResultResponse(BaseModel):
    """Per-sheet audit result for multi-sheet audits."""
    balanced: bool
    total_debits: float
    total_credits: float
    difference: float
    row_count: int
    abnormal_count: int
    column_detection: Optional[ColumnDetectionResponse] = None


class TrialBalanceResponse(BaseModel):
    """Complete trial balance audit response.

    Uses extra='allow' as a safety net during migration — any fields
    not yet modeled still pass through to the frontend.
    """
    model_config = ConfigDict(extra="allow")

    # Core balance data
    status: str
    balanced: bool
    total_debits: float
    total_credits: float
    difference: float
    row_count: int
    timestamp: str
    message: str

    # Anomaly data
    abnormal_balances: list[AbnormalBalanceResponse]
    materiality_threshold: float
    material_count: int
    immaterial_count: int
    has_risk_alerts: bool

    # Analysis
    risk_summary: RiskSummaryResponse
    classification_summary: dict[str, int]
    classification_quality: ClassificationQualityResponse
    column_detection: Optional[ColumnDetectionResponse] = None
    analytics: dict[str, Any]
    category_totals: dict[str, float]
    balance_sheet_validation: BalanceSheetValidationResponse

    # Optional: single-sheet only (added post-engine by route handler)
    lead_sheet_grouping: Optional[dict[str, Any]] = None

    # Optional: multi-sheet only
    is_consolidated: Optional[bool] = None
    sheet_count: Optional[int] = None
    selected_sheets: Optional[list[str]] = None
    sheet_results: Optional[dict[str, SheetResultResponse]] = None
    sheet_column_detections: Optional[dict[str, ColumnDetectionResponse]] = None
    column_order_warnings: Optional[list[str]] = None
    has_column_order_mismatch: Optional[bool] = None


# ═══════════════════════════════════════════════════════════════
# Pre-Flight Report (Sprint 283)
# ═══════════════════════════════════════════════════════════════

class PreFlightColumnQualityResponse(BaseModel):
    """Detection confidence for a single column role."""
    role: str
    detected_name: Optional[str] = None
    confidence: float
    status: Literal["found", "low_confidence", "missing"]


class PreFlightIssueResponse(BaseModel):
    """A single pre-flight quality issue."""
    category: str
    severity: Literal["high", "medium", "low"]
    message: str
    affected_count: int
    remediation: str


class PreFlightDuplicateResponse(BaseModel):
    """A group of duplicate account codes."""
    account_code: str
    count: int


class PreFlightEncodingAnomalyResponse(BaseModel):
    """An account name with non-ASCII characters."""
    row_index: int
    value: str
    column: str


class PreFlightMixedSignResponse(BaseModel):
    """An account with mixed positive/negative debit values."""
    account: str
    positive_count: int
    negative_count: int


class PreFlightReportResponse(BaseModel):
    """Complete pre-flight quality assessment response."""
    filename: str
    row_count: int
    column_count: int
    readiness_score: float
    readiness_label: Literal["Ready", "Review Recommended", "Issues Found"]
    columns: list[PreFlightColumnQualityResponse]
    issues: list[PreFlightIssueResponse]
    duplicates: list[PreFlightDuplicateResponse]
    encoding_anomalies: list[PreFlightEncodingAnomalyResponse]
    mixed_sign_accounts: list[PreFlightMixedSignResponse]
    zero_balance_count: int
    null_counts: dict[str, int]
