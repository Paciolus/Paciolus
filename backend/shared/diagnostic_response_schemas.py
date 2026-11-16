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

from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict

from shared.exact_json import ExactMoney

# Monetary Decimal: stores as Decimal in Python, serializes as a JSON number.
# Sprint 884 (TQ-12): the number carries the exact digits (it was float(v), so
# 90,071,992,547,409.93 went out as ...409.94) — see shared/exact_json.py.
MonetaryDecimal = ExactMoney

# ═══════════════════════════════════════════════════════════════
# Flux Analysis
# ═══════════════════════════════════════════════════════════════


class FluxItemResponse(BaseModel):
    """Individual account period-over-period comparison."""

    account: str
    type: str
    current: MonetaryDecimal
    prior: MonetaryDecimal
    delta_amount: MonetaryDecimal
    delta_percent: Optional[float] = None
    display_percent: str
    is_new: bool
    is_removed: bool
    sign_flip: bool
    risk_level: Literal["high", "medium", "low", "none"]
    variance_indicators: list[str]
    has_reclassification: bool = False
    prior_type: str = ""


class FluxSummaryResponse(BaseModel):
    """Aggregate flux analysis statistics."""

    total_items: int
    high_risk_count: int
    medium_risk_count: int
    new_accounts: int
    removed_accounts: int
    reclassification_count: int = 0
    threshold: float


class FluxDataResponse(BaseModel):
    """Flux analysis data: items + summary."""

    items: list[FluxItemResponse]
    summary: FluxSummaryResponse


class ReconScoreResponse(BaseModel):
    """Per-account reconciliation diagnostic score."""

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


class ProposedActualResponse(BaseModel):
    """Sprint 879b (DH-04): an actual proposed for an open ISA 520 expectation.

    Matched by target_type + target_label against the tool's output. Nothing
    is saved; the auditor captures it with ``capture_token``
    (``POST /engagements/{id}/analytical-expectations/capture-actuals``).
    """

    expectation_id: int
    target_type: str
    target_label: str
    actual: float
    variance: float
    status: str
    capture_token: str


class FluxAnalysisResponse(BaseModel):
    """Complete flux analysis response: flux + recon."""

    flux: FluxDataResponse
    recon: ReconDataResponse
    proposed_actuals: list[ProposedActualResponse] = []


# ═══════════════════════════════════════════════════════════════
# Prior Period Comparison
# ═══════════════════════════════════════════════════════════════


class CategoryVarianceResponse(BaseModel):
    """Balance sheet or income statement category variance."""

    category_key: str
    category_name: str
    current_value: MonetaryDecimal
    prior_value: MonetaryDecimal
    dollar_variance: MonetaryDecimal
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
    framework_note: Optional[str] = None
    # Sprint 765: declarative variance basis on the response.
    variance_basis: Optional[str] = None
    variance_formula: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# Multi-Period Comparison
# ═══════════════════════════════════════════════════════════════


class AccountMovementResponse(BaseModel):
    """Account movement between two periods."""

    account_name: str
    account_type: str
    prior_balance: MonetaryDecimal
    current_balance: MonetaryDecimal
    change_amount: MonetaryDecimal
    change_percent: Optional[float] = None
    movement_type: Literal[
        "new_account",
        "closed_account",
        "sign_change",
        "increase",
        "decrease",
        "unchanged",
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
    prior_total: MonetaryDecimal
    current_total: MonetaryDecimal
    net_change: MonetaryDecimal
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
    prior_total_debits: MonetaryDecimal
    prior_total_credits: MonetaryDecimal
    current_total_debits: MonetaryDecimal
    current_total_credits: MonetaryDecimal
    framework_note: Optional[str] = None
    proposed_actuals: list[ProposedActualResponse] = []
    # Sprint 763: bank-rec materiality emission pattern; for multi-period,
    # ``active_thresholds`` carries the significance thresholds applied.
    active_thresholds: Optional[dict[str, Any]] = None
    duplicate_account_warnings: list[dict[str, Any]] = []
    # Sprint 765: declarative variance basis on the response.
    variance_basis: Optional[str] = None
    variance_formula: Optional[str] = None


class BudgetVarianceResponse(BaseModel):
    """Budget variance data for a single account.

    Sprint 640: ``variance_direction`` classifies the variance as
    favorable / unfavorable / on_budget / neutral based on the account's
    income-statement role. Balance-sheet accounts return ``neutral``.
    ``commentary_prompt`` is populated for MATERIAL variances.
    """

    budget_balance: MonetaryDecimal
    variance_amount: MonetaryDecimal
    variance_percent: Optional[float] = None
    variance_significance: Literal["material", "significant", "minor"]
    variance_direction: Literal["favorable", "unfavorable", "on_budget", "neutral"] = "neutral"
    commentary_prompt: Optional[str] = None


class ThreeWayLeadSheetSummaryResponse(BaseModel):
    """Lead sheet summary with optional budget variance data."""

    lead_sheet: str
    lead_sheet_name: str
    lead_sheet_category: str
    prior_total: MonetaryDecimal
    current_total: MonetaryDecimal
    net_change: MonetaryDecimal
    change_percent: Optional[float] = None
    budget_total: Optional[MonetaryDecimal] = None
    budget_variance: Optional[MonetaryDecimal] = None
    budget_variance_percent: Optional[float] = None
    account_count: int
    movements: list[dict[str, Any]] = []


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
    prior_total_debits: MonetaryDecimal
    prior_total_credits: MonetaryDecimal
    current_total_debits: MonetaryDecimal
    current_total_credits: MonetaryDecimal
    budget_total_debits: MonetaryDecimal
    budget_total_credits: MonetaryDecimal
    budget_variances_by_significance: dict[str, int]
    accounts_over_budget: int
    accounts_under_budget: int
    accounts_on_budget: int
    framework_note: Optional[str] = None
    duplicate_account_warnings: list[dict[str, Any]] = []
    proposed_actuals: list[ProposedActualResponse] = []
    # Sprint 763: active thresholds emission.
    active_thresholds: Optional[dict[str, Any]] = None
    # Sprint 765: declarative variance basis on the response.
    variance_basis: Optional[str] = None
    variance_formula: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# Adjusting Entries
# ═══════════════════════════════════════════════════════════════


class AdjustmentLineResponse(BaseModel):
    """Individual line item in an adjusting entry."""

    account_name: str
    debit: MonetaryDecimal
    credit: MonetaryDecimal
    description: Optional[str] = None


class AdjustingEntryResponse(BaseModel):
    """Complete adjusting journal entry."""

    id: str
    reference: str
    description: str
    adjustment_type: Literal[
        "accrual",
        "deferral",
        "estimate",
        "error_correction",
        "reclassification",
        "other",
    ]
    status: Literal["proposed", "approved", "rejected", "posted"]
    lines: list[AdjustmentLineResponse]
    total_debits: MonetaryDecimal
    total_credits: MonetaryDecimal
    is_balanced: bool
    entry_total: MonetaryDecimal
    account_count: int
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    notes: Optional[str] = None
    is_reversing: bool


class AdjustedAccountBalanceResponse(BaseModel):
    """Account with unadjusted and adjusted balances."""

    account_name: str
    unadjusted_debit: MonetaryDecimal
    unadjusted_credit: MonetaryDecimal
    unadjusted_balance: MonetaryDecimal
    adjustment_debit: MonetaryDecimal
    adjustment_credit: MonetaryDecimal
    net_adjustment: MonetaryDecimal
    adjusted_debit: MonetaryDecimal
    adjusted_credit: MonetaryDecimal
    adjusted_balance: MonetaryDecimal
    has_adjustment: bool


class AdjustedTBTotalsResponse(BaseModel):
    """Aggregate totals for adjusted trial balance."""

    unadjusted_debits: MonetaryDecimal
    unadjusted_credits: MonetaryDecimal
    adjustment_debits: MonetaryDecimal
    adjustment_credits: MonetaryDecimal
    adjusted_debits: MonetaryDecimal
    adjusted_credits: MonetaryDecimal


class AdjustedTrialBalanceResponse(BaseModel):
    """Adjusted trial balance with all entries applied."""

    accounts: list[AdjustedAccountBalanceResponse]
    adjustments_applied: list[str]
    totals: AdjustedTBTotalsResponse
    is_balanced: bool
    is_simulation: bool = False
    adjustment_count: int
    accounts_with_adjustments_count: int
    generated_at: str


# ═══════════════════════════════════════════════════════════════
# Population Profile (Sprint 287) — must be before TrialBalanceResponse
# ═══════════════════════════════════════════════════════════════


class BucketBreakdownResponse(BaseModel):
    """One row in the magnitude histogram."""

    label: str
    lower: float
    upper: Optional[float] = None
    count: int
    sum_abs: MonetaryDecimal
    percent_count: float


class TopAccountResponse(BaseModel):
    """One row in the top-N accounts table."""

    rank: int
    account: str
    category: str
    net_balance: MonetaryDecimal
    abs_balance: MonetaryDecimal
    percent_of_total: float
    account_number: Optional[str] = None


class SectionDensityResponse(BaseModel):
    """Density metrics for one lead sheet section."""

    section_label: str
    section_letters: list[str]
    account_count: int
    section_balance: MonetaryDecimal
    balance_per_account: float
    is_sparse: bool


class PopulationProfileResponse(BaseModel):
    """Complete TB population profile statistics."""

    account_count: int
    total_abs_balance: MonetaryDecimal
    mean_abs_balance: float
    median_abs_balance: float
    std_dev_abs_balance: float
    min_abs_balance: MonetaryDecimal
    max_abs_balance: MonetaryDecimal
    p25: float
    p75: float
    gini_coefficient: float
    gini_interpretation: Literal["Low", "Moderate", "High"]
    # Sprint 887 (OUT-22): adjusted Fisher-Pearson skewness and Tukey upper fence.
    skewness: Optional[float] = None
    upper_fence: Optional[float] = None
    accounts_above_upper_fence: Optional[int] = None
    buckets: list[BucketBreakdownResponse]
    top_accounts: list[TopAccountResponse]
    section_density: Optional[list[SectionDensityResponse]] = None
    account_type_stratification: Optional[list[dict]] = None
    benford_analysis: Optional[dict] = None
    exception_flags: Optional[dict] = None
    suggested_procedures: Optional[list[dict]] = None
    data_quality: Optional[dict] = None


# ═══════════════════════════════════════════════════════════════
# Expense Category Analytics (Sprint 289) — must be before TrialBalanceResponse
# ═══════════════════════════════════════════════════════════════


class ExpenseCategoryItemResponse(BaseModel):
    """One row in the expense category breakdown."""

    label: str
    key: str
    amount: MonetaryDecimal
    pct_of_revenue: Optional[float] = None
    prior_amount: Optional[MonetaryDecimal] = None
    prior_pct_of_revenue: Optional[float] = None
    dollar_change: Optional[MonetaryDecimal] = None
    exceeds_threshold: bool = False
    benchmark_pct: Optional[float] = None
    # Sprint 887: % change and its band (Change ≥ 20% and over materiality / ≥ 10% or over / below both).
    pct_change: Optional[float] = None
    change_band: Optional[Literal["both", "either", "neither"]] = None


class ExpenseChangeThresholdsResponse(BaseModel):
    """The thresholds behind change_band (Paciolus defaults + the run's materiality)."""

    pct_both: float
    pct_either: float
    materiality: MonetaryDecimal


class ExpenseCategoryReportResponse(BaseModel):
    """Complete expense category analytical procedures response."""

    categories: list[ExpenseCategoryItemResponse]
    total_expenses: MonetaryDecimal
    total_revenue: MonetaryDecimal
    revenue_available: bool
    prior_available: bool
    materiality_threshold: MonetaryDecimal
    category_count: int
    change_thresholds: Optional[ExpenseChangeThresholdsResponse] = None


# ═══════════════════════════════════════════════════════════════
# Accrual Completeness (Sprint 290) — must be before TrialBalanceResponse
# ═══════════════════════════════════════════════════════════════


class AccrualAccountResponse(BaseModel):
    """One identified accrual account."""

    account_name: str
    balance: MonetaryDecimal
    matched_keyword: str
    classification: str = "Accrued Liability"


class ReasonablenessResultResponse(BaseModel):
    """Per-account reasonableness test result."""

    account_name: str
    recorded_balance: MonetaryDecimal
    annual_driver: Optional[float] = None
    driver_source: str = ""
    months_to_accrue: int = 1
    expected_balance: Optional[MonetaryDecimal] = None
    variance: Optional[MonetaryDecimal] = None
    variance_pct: Optional[float] = None
    status: str = ""


class DeferredRevenueAnalysisResponse(BaseModel):
    """Deferred Revenue analysis metrics."""

    deferred_balance: MonetaryDecimal = Decimal("0")
    total_revenue: Optional[MonetaryDecimal] = None
    deferred_pct_of_revenue: Optional[float] = None


class AccrualFindingResponse(BaseModel):
    """One finding from the analysis."""

    area: str
    finding: str
    risk: str
    action_required: str


class AccrualProcedureResponse(BaseModel):
    """One suggested audit procedure."""

    priority: str
    area: str
    procedure: str


class ExpectedAccrualCheckResponse(BaseModel):
    """One row in the expected accrual checklist."""

    expected_name: str
    detected: bool
    balance: Optional[MonetaryDecimal] = None
    risk_if_absent: str = ""
    basis: str = ""
    recommended_action: str = ""


class AccrualCompletenessReportResponse(BaseModel):
    """Complete accrual completeness estimator response."""

    accrual_accounts: list[AccrualAccountResponse]
    total_accrued_balance: MonetaryDecimal
    accrual_account_count: int
    deferred_revenue_accounts: list[AccrualAccountResponse] = []
    total_deferred_revenue: MonetaryDecimal = Decimal("0")
    monthly_run_rate: Optional[MonetaryDecimal] = None
    accrual_to_run_rate_pct: Optional[float] = None
    threshold_pct: float
    # Sprint 887 (OUT-08): "default" or "entered" — where the threshold came from.
    threshold_source: Optional[Literal["default", "entered"]] = None
    meets_threshold: bool = False
    below_threshold: bool = False
    prior_operating_expenses: Optional[MonetaryDecimal] = None
    prior_available: bool
    narrative: str
    reasonableness_results: list[ReasonablenessResultResponse] = []
    expected_accrual_checklist: list[ExpectedAccrualCheckResponse] = []
    deferred_revenue_analysis: Optional[DeferredRevenueAnalysisResponse] = None
    findings: list[AccrualFindingResponse] = []
    suggested_procedures: list[AccrualProcedureResponse] = []


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

    Uses extra='ignore' — unknown fields silently dropped (Sprint 561 hardening).
    Anomaly entries carry variable flags depending on anomaly type
    (suspense, concentration, rounding).
    """

    model_config = ConfigDict(extra="ignore")

    # Core fields (always present)
    account: str
    type: str
    issue: str
    amount: MonetaryDecimal
    debit: MonetaryDecimal
    credit: MonetaryDecimal
    materiality: Literal["material", "immaterial"]
    category: str
    confidence: float
    matched_keywords: list[str]
    requires_review: bool
    anomaly_type: str
    expected_balance: Optional[str] = None
    actual_balance: Optional[str] = None
    severity: Literal["high", "medium", "low", "informational"]
    suggestions: list[AbnormalBalanceSuggestionResponse]

    # Optional: anomaly-type-specific flags added by _merge_anomalies()
    recommendation: Optional[str] = None
    is_suspense_account: Optional[bool] = None
    suspense_confidence: Optional[float] = None
    suspense_keywords: Optional[list[str]] = None
    has_concentration_risk: Optional[bool] = None
    concentration_percent: Optional[float] = None
    category_total: Optional[MonetaryDecimal] = None
    has_rounding_anomaly: Optional[bool] = None
    rounding_pattern: Optional[str] = None
    rounding_divisor: Optional[int] = None
    # Sprint 873: concentration rows are materiality-coverage context, not
    # anomalies (Sprint 668). Undeclared, `extra="ignore"` stripped the flag, so
    # the app listed them under "Material Risks" and the PDF built from the app's
    # payload never split them into its coverage section.
    coverage_analysis: Optional[bool] = None
    # Sprint 873: emitted by the equity / intercompany rules and rendered by the
    # TB PDF (pdf/sections/diagnostic.py), but stripped here like coverage_analysis.
    cross_reference_note: Optional[str] = None

    # Optional: multi-sheet only
    sheet_name: Optional[str] = None


class RiskSummaryAnomalyTypesResponse(BaseModel):
    """Anomaly type counts in risk summary."""

    natural_balance_violation: int = 0
    suspense_account: int = 0
    concentration_risk: int = 0
    revenue_concentration: int = 0
    asset_concentration: int = 0
    liability_concentration: int = 0
    expense_concentration: int = 0
    rounding_anomaly: int = 0
    balance_sheet_imbalance: int = 0


class RiskFactorResponse(BaseModel):
    """Individual risk factor contributing to the diagnostic score."""

    name: str
    points: float


class RiskSummaryResponse(BaseModel):
    """Aggregated risk metrics for trial balance."""

    total_anomalies: int
    high_severity: int
    medium_severity: int
    low_severity: int
    anomaly_types: RiskSummaryAnomalyTypesResponse

    # Sprint 573: Previously undeclared fields computed by pipeline
    risk_score: Optional[float] = None
    risk_tier: Optional[str] = None
    risk_factors: Optional[list[list[Any]]] = None
    coverage_pct: Optional[float] = None


class ClassificationIssueResponse(BaseModel):
    """Individual structural COA validation issue."""

    account_number: str
    account_name: str
    issue_type: str
    description: str
    severity: Literal["high", "medium", "low", "informational"]
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
        "balanced",
        "minor_imbalance",
        "moderate_imbalance",
        "significant_imbalance",
    ]
    total_assets: MonetaryDecimal
    total_liabilities: MonetaryDecimal
    total_equity: MonetaryDecimal
    liabilities_plus_equity: MonetaryDecimal
    difference: MonetaryDecimal
    abs_difference: MonetaryDecimal
    severity: Optional[Literal["high", "medium", "low"]] = None
    recommendation: str
    equation: str


class SheetResultResponse(BaseModel):
    """Per-sheet audit result for multi-sheet audits."""

    balanced: bool
    total_debits: MonetaryDecimal
    total_credits: MonetaryDecimal
    difference: MonetaryDecimal
    row_count: int
    abnormal_count: int
    column_detection: Optional[ColumnDetectionResponse] = None


class MaterialityBasisResponse(BaseModel):
    """The threshold the analysis used: its amount, purpose and origin (Sprint 886, OUT-16)."""

    amount: MonetaryDecimal
    purpose: Literal["overall_materiality", "performance_materiality", "test_threshold"]
    origin: Literal["software_default", "firm_setting", "engagement", "entered", "none"]


class TrialBalanceAccountResponse(BaseModel):
    """One entry of ``all_accounts`` (Sprint 890, 15C): amounts are exact JSON numbers, like the totals."""

    model_config = ConfigDict(extra="ignore")

    account: str
    debit: MonetaryDecimal
    credit: MonetaryDecimal
    type: str
    type_supplied: bool = False


class AccountBalanceResponse(BaseModel):
    """One value of ``account_balances`` (Sprint 890, 15C)."""

    model_config = ConfigDict(extra="ignore")

    debit: MonetaryDecimal
    credit: MonetaryDecimal


class ConvertedAccountResponse(BaseModel):
    """One account in the convenience conversion (Sprint 890, 15D)."""

    account: str
    currency: Optional[str] = None
    original_amount: MonetaryDecimal
    converted_amount: Optional[MonetaryDecimal] = None
    rate: Optional[str] = None
    rate_date: Optional[str] = None
    rate_source: Optional[str] = None
    issue: Optional[str] = None


class TBCurrencyConversionResponse(BaseModel):
    """Convenience conversion at one closing rate per currency — not ASC 830 / IAS 21 translation."""

    method: str
    label: str
    presentation_currency: str
    converted_count: int
    unconverted_count: int
    rows: list[ConvertedAccountResponse]


class TrialBalanceResponse(BaseModel):
    """Complete trial balance audit response.

    Uses extra='ignore' — unknown fields silently dropped (Sprint 561 hardening).
    """

    model_config = ConfigDict(extra="ignore")

    # Core balance data
    status: str
    balanced: bool
    total_debits: MonetaryDecimal
    total_credits: MonetaryDecimal
    difference: MonetaryDecimal
    row_count: int
    timestamp: str
    message: str

    # Anomaly data
    abnormal_balances: list[AbnormalBalanceResponse]
    materiality_threshold: MonetaryDecimal
    material_count: int
    immaterial_count: int
    informational_count: int = 0
    has_risk_alerts: bool

    # Analysis
    risk_summary: RiskSummaryResponse
    classification_summary: dict[str, int]
    classification_quality: ClassificationQualityResponse
    column_detection: Optional[ColumnDetectionResponse] = None
    analytics: dict[str, Any]
    category_totals: dict[str, str]
    balance_sheet_validation: BalanceSheetValidationResponse

    # Sprint 573: Previously undeclared fields returned by pipeline
    data_quality: Optional[dict[str, Any]] = None
    all_accounts: Optional[list[TrialBalanceAccountResponse]] = None
    account_balances: Optional[dict[str, AccountBalanceResponse]] = None
    # Sprint 890 (15D): currency codes per account (when the file has a currency column), and the
    # convenience conversion when the user has a rate table.
    account_currencies: Optional[dict[str, list[str]]] = None
    currency_conversion: Optional[TBCurrencyConversionResponse] = None
    classified_accounts: Optional[dict[str, str]] = None
    account_subtypes: Optional[dict[str, str]] = None

    # Optional: population profile (Sprint 287)
    population_profile: Optional[PopulationProfileResponse] = None

    # Optional: expense category analytics (Sprint 289)
    expense_category_analytics: Optional[ExpenseCategoryReportResponse] = None

    # Optional: accrual completeness (Sprint 290)
    accrual_completeness: Optional[AccrualCompletenessReportResponse] = None

    # Optional: diagnostics (Sprint 291+)
    lease_diagnostic: Optional[dict[str, Any]] = None
    cutoff_risk: Optional[dict[str, Any]] = None
    going_concern: Optional[dict[str, Any]] = None

    # Sprint 310 / 886: where the threshold came from — "software_default",
    # "firm_setting", "engagement", "entered" or "none" (was "manual" for any amount).
    materiality_source: Optional[str] = None
    # Sprint 886 (OUT-16): amount, purpose and origin, printed by every export.
    materiality_basis: Optional[MaterialityBasisResponse] = None

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
    downstream_impact: str = ""
    affected_items: list[str] = []
    affected_items_truncated: bool = False
    affected_items_total: int = 0
    tests_affected: int = 0


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


class PreFlightBalanceCheckResponse(BaseModel):
    """TB debit/credit balance verification result."""

    total_debits: MonetaryDecimal
    total_credits: MonetaryDecimal
    difference: MonetaryDecimal
    balanced: bool
    tolerance: MonetaryDecimal = Decimal("0.01")


class PreFlightScoreComponentResponse(BaseModel):
    """A single component of the readiness score breakdown."""

    component: str
    weight: float
    score: float
    contribution: float


class PreFlightCategoryCompletenessResponse(BaseModel):
    """Sprint 631: GAAP category completeness snapshot."""

    asset_count: int
    liability_count: int
    equity_count: int
    revenue_count: int
    expense_count: int
    unknown_count: int
    missing_categories: list[str] = []
    revenue_total: MonetaryDecimal = Decimal("0")
    cogs_total: MonetaryDecimal = Decimal("0")
    cogs_gap: bool = False


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
    balance_check: Optional[PreFlightBalanceCheckResponse] = None
    score_breakdown: list[PreFlightScoreComponentResponse] = []
    category_completeness: Optional[PreFlightCategoryCompletenessResponse] = None
