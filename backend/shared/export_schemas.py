"""
Pydantic models for Paciolus export endpoints.

Extracted from routes/export.py (Sprint 155) to support sub-module decomposition.
All 18 export input models live here; routes/export.py re-exports them for backward compat.
"""

from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from shared.schemas import ExportAmount, _ExportItem

# --- Workpaper Metadata Base ---


class WorkpaperMetadata(BaseModel):
    """Common workpaper signoff fields shared across all testing/memo export models."""

    filename: str = "export"
    source_document_title: Optional[str] = None
    source_context_note: Optional[str] = None
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    # Deprecated (Sprint 7): signoff fields are ignored unless include_signoff=True.
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    include_signoff: bool = False
    # Sprint 886 (OUT-18): the engagement (or client) the run belongs to. The
    # memo's reporting framework is resolved from it, after an access check.
    engagement_id: Optional[int] = Field(default=None, ge=1)
    client_id: Optional[int] = Field(default=None, ge=1)


# --- Diagnostics Models ---


class FluxItemInput(BaseModel):
    account: str
    type: str
    current: float
    prior: float
    delta_amount: float
    delta_percent: Optional[float] = None
    display_percent: Optional[str] = None
    is_new: bool
    is_removed: bool
    sign_flip: bool
    risk_level: str
    variance_indicators: list[str] = []


class FluxResultSummary(BaseModel):
    total_items: int
    high_risk_count: int
    medium_risk_count: int
    new_accounts: int
    removed_accounts: int
    threshold: float


class FluxResultInput(BaseModel):
    items: list[FluxItemInput]
    summary: FluxResultSummary


class ReconScoreInput(BaseModel):
    account: str
    score: int
    band: str
    factors: list[str]
    action: str


class ReconStats(BaseModel):
    high: int
    medium: int
    low: int


class ReconResultInput(BaseModel):
    scores: list[ReconScoreInput]
    stats: ReconStats


class LeadSheetInput(BaseModel):
    flux: FluxResultInput
    recon: ReconResultInput
    filename: str


# --- Flux Expectations Memo (Sprint 297) ---


class ExpectationEntry(BaseModel):
    """Single auditor-authored expectation for one flux item."""

    auditor_expectation: str = ""
    auditor_explanation: str = ""


class FluxExpectationsMemoInput(WorkpaperMetadata):
    """Input for ISA 520 flux expectations memo PDF export."""

    flux: FluxResultInput
    expectations: dict[str, ExpectationEntry] = {}  # keyed by account name


class LeadSheetAccountInput(_ExportItem):
    """One account inside a lead-sheet summary (Sprint 885, OUT-02)."""

    account: Optional[str] = None
    name: Optional[str] = None
    debit: ExportAmount = None
    credit: ExportAmount = None


class LeadSheetSummaryInput(_ExportItem):
    """One lead sheet (A–Z) of the grouping the financial statements are built from."""

    lead_sheet: str = ""
    name: Optional[str] = None
    net_balance: ExportAmount = None
    accounts: list[LeadSheetAccountInput] = []


class LeadSheetGroupingInput(_ExportItem):
    """The TB analysis ``lead_sheet_grouping``: its summaries are typed (Sprint 885, OUT-02)."""

    summaries: list[LeadSheetSummaryInput] = []


class FinancialStatementsInput(BaseModel):
    """Input model for financial statements export."""

    lead_sheet_grouping: LeadSheetGroupingInput
    prior_lead_sheet_grouping: Optional[LeadSheetGroupingInput] = None
    filename: str = "financial_statements"
    entity_name: Optional[str] = None
    period_end: Optional[str] = None
    # Deprecated (Sprint 7): signoff fields are ignored unless include_signoff=True.
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[date] = None  # Sprint 885 (OUT-02): a date, not free text
    include_signoff: bool = False


# --- Testing CSV Models ---


class SettingIgnoredInput(BaseModel):
    """A saved testing setting the run did not apply (Sprint 836)."""

    key: str = Field(max_length=100)
    reason: str = Field(max_length=300)


class SavedSettingsDisclosure(BaseModel):
    """Sprint 836: saved-settings transparency echoed back from the tool result.

    ``settings_applied`` lists thresholds that differed from the Paciolus
    defaults for this run; the memo's methodology section states them.
    """

    settings_applied: Optional[dict[str, bool | int | float | list[float]]] = Field(default=None, max_length=100)
    settings_ignored: Optional[list[SettingIgnoredInput]] = Field(default=None, max_length=100)


# --- Supplemental schedules (Sprint 886, OUT-12) ---
# Typed copies of what the engines emit and the memos print. Absent stays absent:
# the memo then omits the section rather than printing zeros.


class DuplicatePaymentVendorRateInput(BaseModel):
    vendor: str
    duplicate_payments: int = Field(ge=0)
    total_payments: int = Field(ge=0)
    duplicate_rate: float = Field(ge=0, le=1)


class DuplicatePaymentMonthInput(BaseModel):
    month: str
    duplicate_payments: int = Field(ge=0)


class DuplicatePaymentSummaryInput(BaseModel):
    """AP ``duplicate_payment_summary``."""

    exact_duplicate_count: int = Field(ge=0)
    fuzzy_duplicate_count: int = Field(ge=0)
    recovery_value_total: Decimal
    vendor_rates: list[DuplicatePaymentVendorRateInput] = []
    monthly_trend: list[DuplicatePaymentMonthInput] = []
    distinct_flagged_payments: int = Field(default=0, ge=0)


class PayrollDepartmentSummaryInput(BaseModel):
    department: str
    employee_count: int = Field(ge=0)
    total_gross_pay: Decimal
    pct_of_total: float


class HeadcountRollforwardInput(BaseModel):
    period_start: str
    period_end: str
    beginning_headcount: int = Field(ge=0)
    new_hires: int = Field(ge=0)
    terminations: int = Field(ge=0)
    computed_ending: int
    final_period_headcount: int = Field(ge=0)
    variance: int


class ARAgingBucketInput(BaseModel):
    bucket: str
    count: int = Field(ge=0)
    amount: Decimal
    percentage: float


class _CompletenessInRange(BaseModel):
    """Sprint 886 (OUT-14): ``data_quality.completeness_score`` is a percentage, 0–100, for every tool.

    Payroll sent 0–1 (complete data printed as 1%); a value outside 0–100 is refused.
    """

    @field_validator("data_quality", check_fields=False)
    @classmethod
    def _completeness_is_a_percentage(cls, value: object) -> object:
        if isinstance(value, dict) and value.get("completeness_score") is not None:
            score = value["completeness_score"]
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
                raise ValueError("data_quality.completeness_score must be a percentage from 0 to 100")
        return value


class JETestingExportInput(_CompletenessInRange, SavedSettingsDisclosure, WorkpaperMetadata):
    """Input model for JE testing exports."""

    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    multi_currency_warning: Optional[dict] = None
    benford_result: Optional[dict] = None
    filename: str = "je_testing"


class APTestingExportInput(_CompletenessInRange, SavedSettingsDisclosure, WorkpaperMetadata):
    """Input model for AP testing exports."""

    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    duplicate_payment_summary: Optional[DuplicatePaymentSummaryInput] = None
    filename: str = "ap_testing"


class PayrollTestingExportInput(_CompletenessInRange, SavedSettingsDisclosure, WorkpaperMetadata):
    """Input model for payroll testing exports."""

    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    payroll_register_total: Optional[Decimal] = None
    department_summary: Optional[list[PayrollDepartmentSummaryInput]] = None
    headcount_rollforward: Optional[HeadcountRollforwardInput] = None
    filename: str = "payroll_testing"


class ThreeWayMatchExportInput(SavedSettingsDisclosure, WorkpaperMetadata):
    """Input model for three-way match exports."""

    summary: dict
    full_matches: list
    partial_matches: list
    unmatched_pos: list = []
    unmatched_invoices: list = []
    unmatched_receipts: list = []
    variances: list = []
    data_quality: dict = {}
    config: dict = {}
    # Sprint 839: tolerances supplied for this run only; the memo states them.
    settings_run_overrides: Optional[dict[str, bool | int | float]] = Field(default=None, max_length=20)
    filename: str = "three_way_match"


class RevenueTestingExportInput(_CompletenessInRange, WorkpaperMetadata):
    """Input model for revenue testing exports."""

    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    filename: str = "revenue_testing"


class ARAgingExportInput(_CompletenessInRange, WorkpaperMetadata):
    """Input model for AR aging exports."""

    composite_score: dict
    test_results: list
    data_quality: dict
    tb_column_detection: Optional[dict] = None
    sl_column_detection: Optional[dict] = None
    ar_summary: Optional[dict] = None
    aging_schedule: Optional[list[ARAgingBucketInput]] = None
    filename: str = "ar_aging"


class FixedAssetExportInput(_CompletenessInRange, WorkpaperMetadata):
    """Input model for fixed asset testing exports."""

    composite_score: dict
    test_results: list
    data_quality: Optional[dict] = None
    column_detection: Optional[dict] = None
    filename: str = "fixed_asset_testing"


class InventoryExportInput(_CompletenessInRange, WorkpaperMetadata):
    """Input model for inventory testing exports."""

    composite_score: dict
    test_results: list
    data_quality: Optional[dict] = None
    column_detection: Optional[dict] = None
    filename: str = "inventory_testing"


# --- Memo-Only Models ---


class RecFlaggedItemInput(_ExportItem):
    """One item a reconciliation test flagged (kept as sent; the exports read the counts)."""


class RecTestInput(_ExportItem):
    """One reconciliation test of the bank rec run (``BankRecResult.rec_tests``)."""

    test_name: str
    # Sprint 887 (OUT-17): absent → the memo lists the test with no suggested procedure.
    test_key: Optional[str] = None
    flagged_count: int = Field(ge=0)
    severity: str = "low"
    flagged_items: list[RecFlaggedItemInput] = []


class OutstandingAgingInput(_ExportItem):
    """Aging of one category of unmatched items (``BankRecResult.outstanding_aging``)."""

    category: Literal["bank_only", "ledger_only"]
    total_count: int = Field(ge=0)
    over_10_days: int = Field(ge=0)
    over_30_days: int = Field(ge=0)
    oldest_item_days: Optional[int] = None
    oldest_item_date: Optional[str] = None
    oldest_item_amount: ExportAmount = None


class BankRecCompositeInput(_ExportItem):
    """The bank rec composite diagnostic score (``compute_bank_rec_diagnostic_score``)."""

    score: float = Field(ge=0, le=100)
    risk_tier: Literal["low", "moderate", "elevated", "high"]
    total_flagged: int = Field(ge=0)
    flag_rate: float = 0.0
    flags_by_severity: dict[str, int] = {}
    tests_run: int = Field(ge=0)
    total_entries: int = 0
    top_findings: list[str] = []


class BankRecThresholdSourcesInput(_ExportItem):
    """Per threshold: supplied for this run ("caller") or the Paciolus default."""

    materiality: Literal["caller", "default"]
    performance_materiality: Literal["caller", "default"]


class BankRecThresholdsInput(_ExportItem):
    """The thresholds the bank rec engine applied (``BankRecResult.active_thresholds``)."""

    materiality: Decimal
    performance_materiality: Decimal
    amount_tolerance: Optional[Decimal] = None
    date_tolerance_days: Optional[int] = None
    split_match_max_candidates: Optional[int] = None
    materiality_source: Literal["caller", "default"]
    threshold_sources: Optional[BankRecThresholdSourcesInput] = None


class BankRecExportResult(BaseModel):
    """Sprint 886 (OUT-10): one model for everything a bank rec run produced.

    The memo and the CSV both take it, so neither can silently drop a result
    the screen shows. Every result block is optional: one the request did not
    carry prints as "Not available", never as a LOW tier, a zero score or an
    empty aging.
    """

    summary: dict
    bank_column_detection: Optional[dict] = None
    ledger_column_detection: Optional[dict] = None
    # Sprint 833: split-match search bounds, disclosed in the memo methodology.
    split_search: Optional[dict] = None
    rec_tests: Optional[list[RecTestInput]] = None
    outstanding_aging: Optional[list[OutstandingAgingInput]] = None
    composite_score: Optional[BankRecCompositeInput] = None
    active_thresholds: Optional[BankRecThresholdsInput] = None


class BankRecMemoInput(BankRecExportResult, WorkpaperMetadata):
    """Input model for bank reconciliation memo export."""

    filename: str = "bank_reconciliation"


class MultiPeriodThresholdsInput(BaseModel):
    """Sprint 887: the thresholds the comparison applied, as the engine reports them."""

    significant_variance_percent: float = Field(ge=0)
    significant_variance_amount: float = Field(ge=0)
    # 0 (or absent) means no materiality threshold was supplied for the run.
    materiality_threshold: Optional[float] = Field(default=None, ge=0)


class MultiPeriodMemoInput(WorkpaperMetadata):
    """Input model for multi-period comparison memo export (MovementSummaryResponse shape)."""

    prior_label: str = "Prior"
    current_label: str = "Current"
    budget_label: Optional[str] = None
    total_accounts: int = 0
    movements_by_type: dict = {}
    movements_by_significance: dict = {}
    significant_movements: list = []
    lead_sheet_summaries: list = []
    dormant_account_count: int = 0
    dormant_accounts: list[str] = []
    # Sprint 887: the summary states the thresholds applied ("Not available" when absent).
    active_thresholds: Optional[MultiPeriodThresholdsInput] = None
    filename: str = "multi_period_comparison"


class CurrencyConversionMemoInput(WorkpaperMetadata):
    """Input model for currency conversion memo export."""

    conversion_performed: bool = True
    presentation_currency: str = "USD"
    total_accounts: int = 0
    converted_count: int = 0
    unconverted_count: int = 0
    unconverted_items: list = []
    currencies_found: list = []
    rates_applied: dict = {}
    balance_check_passed: bool = True
    balance_imbalance: float = 0.0
    conversion_summary: str = ""
    currency_exposure: list = []
    filename: str = "currency_conversion"


# --- Sampling Models ---


class SamplingDesignMemoInput(WorkpaperMetadata):
    """Input model for sampling design memo export."""

    method: str = "mus"
    confidence_level: float = 0.95
    confidence_factor: float = 3.0
    tolerable_misstatement: float = 0.0
    expected_misstatement: float = 0.0
    population_size: int = 0
    population_value: float = 0.0
    sampling_interval: Optional[float] = None
    calculated_sample_size: int = 0
    actual_sample_size: int = 0
    high_value_count: int = 0
    high_value_total: float = 0.0
    remainder_count: int = 0
    remainder_sample_size: int = 0
    strata_summary: list = []
    selected_items: list = []
    population_type: str = ""
    filename: str = "sampling_design"


class SamplingEvaluationMemoInput(WorkpaperMetadata):
    """Input model for sampling evaluation memo export."""

    method: str = "mus"
    confidence_level: float = 0.95
    tolerable_misstatement: float = 0.0
    expected_misstatement: float = 0.0
    population_value: float = 0.0
    sample_size: int = 0
    sample_value: float = 0.0
    errors_found: int = 0
    total_misstatement: float = 0.0
    projected_misstatement: float = 0.0
    basic_precision: float = 0.0
    incremental_allowance: float = 0.0
    upper_error_limit: float = 0.0
    conclusion: str = ""
    conclusion_detail: str = ""
    errors: list = []
    taintings_ranked: list = []
    # Sprint 825 (S6): the understatement bound, evaluated separately from the
    # overstatement bound above. None = an older client that did not send it;
    # the memo then omits the understatement lines rather than printing $0.
    understatement_projected_misstatement: Optional[float] = None
    understatement_basic_precision: Optional[float] = None
    understatement_incremental_allowance: Optional[float] = None
    understatement_upper_error_limit: Optional[float] = None
    understatement_errors_found: Optional[int] = None
    total_overstatement: Optional[float] = None
    total_understatement: Optional[float] = None
    # Optional design context for combined memo
    design_result: Optional[dict] = None
    filename: str = "sampling_evaluation"


class SamplingSelectionCSVInput(BaseModel):
    """Input model for sampling selection CSV export."""

    selected_items: list
    method: str = "mus"
    population_size: int = 0
    population_value: float = 0.0
    filename: str = "sampling_selection"


# --- Pre-Flight Models (Sprint 283) ---


class PreFlightMemoInput(WorkpaperMetadata):
    """Input model for pre-flight report memo export."""

    readiness_score: float = 0.0
    readiness_label: str = "Issues Found"
    row_count: int = 0
    column_count: int = 0
    columns: list = []
    issues: list = []
    filename: str = "preflight_report"


class PreFlightCSVInput(BaseModel):
    """Input model for pre-flight issues CSV export."""

    issues: list = []
    filename: str = "preflight_issues"


# --- Population Profile Models (Sprint 287) ---


class PopulationProfileMemoInput(WorkpaperMetadata):
    """Input model for population profile memo export."""

    account_count: int = 0
    total_abs_balance: float = 0.0
    mean_abs_balance: float = 0.0
    median_abs_balance: float = 0.0
    std_dev_abs_balance: float = 0.0
    min_abs_balance: float = 0.0
    max_abs_balance: float = 0.0
    p25: float = 0.0
    p75: float = 0.0
    gini_coefficient: float = 0.0
    gini_interpretation: str = "Low"
    buckets: list = []
    top_accounts: list = []
    account_type_stratification: list = []
    benford_analysis: Optional[dict] = None
    exception_flags: Optional[dict] = None
    suggested_procedures: list = []
    data_quality: Optional[dict] = None
    filename: str = "population_profile"


class PopulationProfileCSVInput(BaseModel):
    """Input model for population profile CSV export."""

    account_count: int = 0
    total_abs_balance: float = 0.0
    mean_abs_balance: float = 0.0
    median_abs_balance: float = 0.0
    std_dev_abs_balance: float = 0.0
    min_abs_balance: float = 0.0
    max_abs_balance: float = 0.0
    p25: float = 0.0
    p75: float = 0.0
    gini_coefficient: float = 0.0
    gini_interpretation: str = "Low"
    buckets: list = []
    top_accounts: list = []
    filename: str = "population_profile"


# --- Expense Category Models (Sprint 289) ---


class ExpenseCategoryMemoInput(WorkpaperMetadata):
    """Input model for expense category analytical procedures memo export."""

    categories: list = []
    total_expenses: float = 0.0
    total_revenue: float = 0.0
    revenue_available: bool = False
    prior_available: bool = False
    materiality_threshold: float = 0.0
    category_count: int = 0
    filename: str = "expense_category"


class ExpenseCategoryCSVInput(BaseModel):
    """Input model for expense category CSV export."""

    categories: list = []
    total_expenses: float = 0.0
    total_revenue: float = 0.0
    revenue_available: bool = False
    prior_available: bool = False
    materiality_threshold: float = 0.0
    category_count: int = 0
    filename: str = "expense_category"


# --- Accrual Completeness Models (Sprint 290) ---


class AccrualCompletenessMemoInput(WorkpaperMetadata):
    """Input model for accrual completeness estimator memo export."""

    accrual_accounts: list = []
    total_accrued_balance: float = 0.0
    accrual_account_count: int = 0
    deferred_revenue_accounts: list = []
    total_deferred_revenue: float = 0.0
    monthly_run_rate: Optional[float] = None
    accrual_to_run_rate_pct: Optional[float] = None
    threshold_pct: float = 50.0
    # Sprint 887 (OUT-08): absent → the memo prints "Threshold source: Not available".
    threshold_source: Optional[Literal["default", "entered"]] = None
    meets_threshold: bool = False
    below_threshold: bool = False
    prior_operating_expenses: Optional[float] = None
    prior_available: bool = False
    narrative: str = ""
    reasonableness_results: list = []
    expected_accrual_checklist: list = []
    deferred_revenue_analysis: Optional[dict] = None
    findings: list = []
    suggested_procedures: list = []
    filename: str = "accrual_completeness"


class AccrualCompletenessCSVInput(BaseModel):
    """Input model for accrual completeness CSV export."""

    accrual_accounts: list = []
    total_accrued_balance: float = 0.0
    accrual_account_count: int = 0
    deferred_revenue_accounts: list = []
    total_deferred_revenue: float = 0.0
    monthly_run_rate: Optional[float] = None
    accrual_to_run_rate_pct: Optional[float] = None
    threshold_pct: float = 50.0
    meets_threshold: bool = False
    below_threshold: bool = False
    prior_operating_expenses: Optional[float] = None
    prior_available: bool = False
    narrative: str = ""
    reasonableness_results: list = []
    findings: list = []
    filename: str = "accrual_completeness"
