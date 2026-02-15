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
from typing import Any, Dict, List, Literal, Optional

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
    risk_reasons: List[str]


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
    items: List[FluxItemResponse]
    summary: FluxSummaryResponse


class ReconScoreResponse(BaseModel):
    """Per-account reconciliation risk score."""
    account: str
    score: int
    band: Literal["high", "medium", "low"]
    factors: List[str]
    action: str


class ReconStatsResponse(BaseModel):
    """Reconciliation risk statistics by band."""
    high: int
    medium: int
    low: int


class ReconDataResponse(BaseModel):
    """Reconciliation readiness data: scores + stats."""
    scores: List[ReconScoreResponse]
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
    balance_sheet_variances: List[CategoryVarianceResponse]
    income_statement_variances: List[CategoryVarianceResponse]
    ratio_variances: List[RatioVarianceResponse]
    diagnostic_variances: List[DiagnosticVarianceResponse]
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
    movements: List[AccountMovementResponse]


class MovementSummaryResponse(BaseModel):
    """2-way period comparison response."""
    prior_label: str
    current_label: str
    total_accounts: int
    movements_by_type: Dict[str, int]
    movements_by_significance: Dict[str, int]
    all_movements: List[AccountMovementResponse]
    lead_sheet_summaries: List[LeadSheetMovementSummaryResponse]
    significant_movements: List[AccountMovementResponse]
    new_accounts: List[str]
    closed_accounts: List[str]
    dormant_accounts: List[str]
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
    movements_by_type: Dict[str, int]
    movements_by_significance: Dict[str, int]
    all_movements: List[Dict[str, Any]]
    lead_sheet_summaries: List[ThreeWayLeadSheetSummaryResponse]
    significant_movements: List[Dict[str, Any]]
    new_accounts: List[str]
    closed_accounts: List[str]
    dormant_accounts: List[str]
    prior_total_debits: float
    prior_total_credits: float
    current_total_debits: float
    current_total_credits: float
    budget_total_debits: float
    budget_total_credits: float
    budget_variances_by_significance: Dict[str, int]
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
    lines: List[AdjustmentLineResponse]
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
    accounts: List[AdjustedAccountBalanceResponse]
    adjustments_applied: List[str]
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
    matched_keywords: List[str]


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
    matched_keywords: List[str]
    requires_review: bool
    anomaly_type: str
    expected_balance: Optional[str] = None
    actual_balance: Optional[str] = None
    severity: Literal["high", "medium", "low"]
    suggestions: List[AbnormalBalanceSuggestionResponse]

    # Optional: anomaly-type-specific flags added by _merge_anomalies()
    recommendation: Optional[str] = None
    is_suspense_account: Optional[bool] = None
    suspense_confidence: Optional[float] = None
    suspense_keywords: Optional[List[str]] = None
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
    issues: List[ClassificationIssueResponse]
    quality_score: float
    issue_counts: Dict[str, int]
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
    all_columns: List[str]
    detection_notes: List[str]


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
    abnormal_balances: List[AbnormalBalanceResponse]
    materiality_threshold: float
    material_count: int
    immaterial_count: int
    has_risk_alerts: bool

    # Analysis
    risk_summary: RiskSummaryResponse
    classification_summary: Dict[str, int]
    classification_quality: ClassificationQualityResponse
    column_detection: Optional[ColumnDetectionResponse] = None
    analytics: Dict[str, Any]
    category_totals: Dict[str, float]
    balance_sheet_validation: BalanceSheetValidationResponse

    # Optional: single-sheet only (added post-engine by route handler)
    lead_sheet_grouping: Optional[Dict[str, Any]] = None

    # Optional: multi-sheet only
    is_consolidated: Optional[bool] = None
    sheet_count: Optional[int] = None
    selected_sheets: Optional[List[str]] = None
    sheet_results: Optional[Dict[str, SheetResultResponse]] = None
    sheet_column_detections: Optional[Dict[str, ColumnDetectionResponse]] = None
    column_order_warnings: Optional[List[str]] = None
    has_column_order_mismatch: Optional[bool] = None
