"""
Pydantic models for Paciolus export endpoints.

Extracted from routes/export.py (Sprint 155) to support sub-module decomposition.
All 18 export input models live here; routes/export.py re-exports them for backward compat.
"""
from typing import Optional

from pydantic import BaseModel

# --- Workpaper Metadata Base ---

class WorkpaperMetadata(BaseModel):
    """Common workpaper signoff fields shared across all testing/memo export models."""
    filename: str = "export"
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


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
    risk_reasons: list[str]


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


class FinancialStatementsInput(BaseModel):
    """Input model for financial statements export."""
    lead_sheet_grouping: dict
    prior_lead_sheet_grouping: Optional[dict] = None
    filename: str = "financial_statements"
    entity_name: Optional[str] = None
    period_end: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


# --- Testing CSV Models ---

class JETestingExportInput(WorkpaperMetadata):
    """Input model for JE testing exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    multi_currency_warning: Optional[dict] = None
    benford_result: Optional[dict] = None
    filename: str = "je_testing"


class APTestingExportInput(WorkpaperMetadata):
    """Input model for AP testing exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    filename: str = "ap_testing"


class PayrollTestingExportInput(WorkpaperMetadata):
    """Input model for payroll testing exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    filename: str = "payroll_testing"


class ThreeWayMatchExportInput(WorkpaperMetadata):
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
    filename: str = "three_way_match"


class RevenueTestingExportInput(WorkpaperMetadata):
    """Input model for revenue testing exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    filename: str = "revenue_testing"


class ARAgingExportInput(WorkpaperMetadata):
    """Input model for AR aging exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    tb_column_detection: Optional[dict] = None
    sl_column_detection: Optional[dict] = None
    ar_summary: Optional[dict] = None
    filename: str = "ar_aging"


class FixedAssetExportInput(WorkpaperMetadata):
    """Input model for fixed asset testing exports."""
    composite_score: dict
    test_results: list
    data_quality: Optional[dict] = None
    column_detection: Optional[dict] = None
    filename: str = "fixed_asset_testing"


class InventoryExportInput(WorkpaperMetadata):
    """Input model for inventory testing exports."""
    composite_score: dict
    test_results: list
    data_quality: Optional[dict] = None
    column_detection: Optional[dict] = None
    filename: str = "inventory_testing"


# --- Memo-Only Models ---

class BankRecMemoInput(WorkpaperMetadata):
    """Input model for bank reconciliation memo export."""
    summary: dict
    bank_column_detection: Optional[dict] = None
    ledger_column_detection: Optional[dict] = None
    filename: str = "bank_reconciliation"


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
