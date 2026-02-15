"""
Pydantic models for Paciolus export endpoints.

Extracted from routes/export.py (Sprint 155) to support sub-module decomposition.
All 18 export input models live here; routes/export.py re-exports them for backward compat.
"""
from typing import Optional, List

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
    risk_reasons: List[str]


class FluxResultSummary(BaseModel):
    total_items: int
    high_risk_count: int
    medium_risk_count: int
    new_accounts: int
    removed_accounts: int
    threshold: float


class FluxResultInput(BaseModel):
    items: List[FluxItemInput]
    summary: FluxResultSummary


class ReconScoreInput(BaseModel):
    account: str
    score: int
    band: str
    factors: List[str]
    action: str


class ReconStats(BaseModel):
    high: int
    medium: int
    low: int


class ReconResultInput(BaseModel):
    scores: List[ReconScoreInput]
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
