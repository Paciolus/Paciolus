"""Sprint 890 (CEO brief 15C, review ST-10): response models for the five promoted JSON tools; amounts stay exact decimal strings by design.

Each model tree mirrors one engine's ``to_dict()`` output field for field:

* ``POST /audit/form-1099``               -> ``Form1099Response``          (``form_1099_engine``)
* ``POST /audit/book-to-tax``             -> ``BookToTaxResponse``         (``book_to_tax_engine``)
* ``POST /audit/cash-flow-projector``     -> ``CashFlowForecastResponse``  (``cash_flow_projector_engine``)
* ``POST /audit/intercompany-elimination`` -> ``IntercompanyEliminationResponse`` (``intercompany_elimination_engine``)
* ``POST /audit/w2-reconciliation``       -> ``W2ReconciliationResponse``  (``w2_reconciliation_engine``)

Monetary amounts, rates and probabilities are ``str``: the engines emit
``str(Decimal)`` so a figure reaches the client exactly as computed, with no
binary-float rounding. Every model forbids extra keys and validates strictly
(no str <-> number coercion), so an engine change that adds, drops or retypes
a field fails ``tests/test_sprint_890_promoted_tool_response_models.py``
instead of reaching the client unannounced.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


# =============================================================================
# Form 1099 (form_1099_engine.py)
# =============================================================================

Form1099FormType = Literal["1099-NEC", "1099-MISC", "1099-INT"]
Form1099PaymentCategory = Literal[
    "nonemployee_comp", "rents", "royalties", "medical", "legal", "attorney_fees", "interest", "other"
]


class Form1099ThresholdItemResponse(_Strict):
    """``ThresholdItem.to_dict``."""

    form_type: Form1099FormType
    box: int
    description: str
    amount: str
    basis: str
    needs_confirmation: bool


class Form1099ThresholdScheduleResponse(_Strict):
    """``ThresholdSchedule.to_dict``."""

    tax_year: int
    figures_from_tax_year: int
    items: list[Form1099ThresholdItemResponse]
    confirm_against: str


class Form1099BoxAmountResponse(_Strict):
    """``VendorBoxAmount.to_dict``."""

    category: Form1099PaymentCategory
    form_type: Form1099FormType
    box: int
    amount: str


class Form1099DataQualityResponse(_Strict):
    """``VendorDataQuality.to_dict``."""

    vendor_id: str
    vendor_name: str
    missing_tin: bool
    invalid_tin_format: bool
    missing_address: bool
    unknown_entity_type: bool
    has_issue: bool
    notes: list[str]


class Form1099CandidateResponse(_Strict):
    """``Form1099Candidate.to_dict``."""

    vendor_id: str
    vendor_name: str
    form_type: Form1099FormType
    total_reportable: str
    box_amounts: list[Form1099BoxAmountResponse]
    payment_count: int
    excluded_amount: str
    flagged_for_review: bool
    review_reasons: list[str]


class Form1099W9CollectionRowResponse(_Strict):
    """``W9CollectionRow.to_dict``."""

    vendor_id: str
    vendor_name: str
    reason: str


class Form1099BelowThresholdPayeeResponse(_Strict):
    """``BelowThresholdPayee.to_dict``."""

    vendor_id: str
    vendor_name: str
    form_type: Form1099FormType
    total: str
    box_amounts: list[Form1099BoxAmountResponse]
    reason: str


class Form1099SummaryResponse(_Strict):
    """The ``summary`` dict built in ``prepare_1099s``."""

    total_candidates: int
    totals_by_form: dict[str, str]
    counts_by_form: dict[str, int]
    w9_collection_count: int
    data_quality_issue_count: int
    payments_without_vendor: int
    payments_outside_tax_year: int
    below_threshold_count: int


class Form1099Response(_Strict):
    """``Form1099Result.to_dict`` — ``POST /audit/form-1099``."""

    tax_year: int
    candidates: list[Form1099CandidateResponse]
    data_quality: list[Form1099DataQualityResponse]
    w9_collection_list: list[Form1099W9CollectionRowResponse]
    summary: Form1099SummaryResponse
    thresholds: Optional[Form1099ThresholdScheduleResponse]
    notices: list[str]
    below_threshold_payees: list[Form1099BelowThresholdPayeeResponse]


# =============================================================================
# Book-to-tax (book_to_tax_engine.py)
# =============================================================================


class BookToTaxAdjustmentLineResponse(_Strict):
    """``AdjustmentLine.to_dict``."""

    label: str
    code: Optional[str]
    difference_type: Literal["permanent", "temporary"]
    direction: Literal["add", "subtract"]
    amount: str
    signed_amount: str


class BookToTaxScheduleM1Response(_Strict):
    """``ScheduleM1.to_dict``."""

    net_income_per_books: str
    federal_income_tax_per_books: str
    permanent_additions: list[BookToTaxAdjustmentLineResponse]
    temporary_additions: list[BookToTaxAdjustmentLineResponse]
    permanent_subtractions: list[BookToTaxAdjustmentLineResponse]
    temporary_subtractions: list[BookToTaxAdjustmentLineResponse]
    taxable_income: str


class BookToTaxScheduleM3SectionResponse(_Strict):
    """``ScheduleM3Section.to_dict``."""

    label: str
    code: Optional[str]
    permanent: str
    temporary: str
    total: str


class BookToTaxScheduleM3Response(_Strict):
    """``ScheduleM3.to_dict``."""

    income_per_books: str
    income_items: list[BookToTaxScheduleM3SectionResponse]
    expense_items: list[BookToTaxScheduleM3SectionResponse]
    taxable_income: str


class BookToTaxDeferredTaxResponse(_Strict):
    """``DeferredTaxRollforward.to_dict``."""

    beginning_dta: str
    beginning_dtl: str
    current_year_temporary_adjustments: str
    tax_rate: str
    current_year_movement: str
    ending_dta: str
    ending_dtl: str


class BookToTaxProvisionResponse(_Strict):
    """``TaxProvision.to_dict`` (Sprint 889: ``is_complete`` + ``limitations``)."""

    taxable_income: str
    current_federal_tax: str
    current_state_tax: str
    deferred_tax_expense: str
    total_tax_expense: str
    effective_rate: str
    is_complete: bool
    limitations: list[str]


class BookToTaxResponse(_Strict):
    """``BookToTaxResult.to_dict`` — ``POST /audit/book-to-tax``."""

    tax_year: int
    entity_size: Literal["small", "large"]
    schedule_m1: BookToTaxScheduleM1Response
    schedule_m3: BookToTaxScheduleM3Response
    deferred_tax: BookToTaxDeferredTaxResponse
    tax_provision: BookToTaxProvisionResponse


# =============================================================================
# Cash-flow projector (cash_flow_projector_engine.py)
# =============================================================================

CashFlowAgingBucket = Literal["current", "1-30", "31-60", "61-90", "over-90"]


class CashFlowDailyPointResponse(_Strict):
    """``DailyPoint.to_dict``."""

    day_index: int
    day_date: str
    ar_inflow: str
    ap_outflow: str
    recurring_net: str
    net_change: str
    ending_balance: str


class CashFlowHorizonSummaryResponse(_Strict):
    """``HorizonSummary.to_dict``."""

    day: int
    cumulative_inflow: str
    cumulative_outflow: str
    ending_balance: str
    lowest_balance: str
    lowest_balance_day: int


class CashFlowCollectionPriorityResponse(_Strict):
    """``CollectionPriority.to_dict``."""

    bucket: CashFlowAgingBucket
    amount_outstanding: str
    expected_collection: str
    collection_probability: str


class CashFlowApDeferralCandidateResponse(_Strict):
    """One dict from ``_ap_deferral_candidates``."""

    bucket: CashFlowAgingBucket
    outstanding: str
    defer_amount: str
    defer_rate: str
    paid_between_days: list[int]


class CashFlowScenarioResponse(_Strict):
    """``ScenarioResult.to_dict``. ``horizon`` is keyed by the day as a string ("30", "60", "90")."""

    scenario: Literal["base", "stress", "best"]
    daily: list[CashFlowDailyPointResponse]
    horizon: dict[str, CashFlowHorizonSummaryResponse]
    goes_negative: bool
    first_negative_day: Optional[int]
    breach_min_safe_cash: bool
    collection_priorities: list[CashFlowCollectionPriorityResponse]
    ap_deferral_candidates: list[CashFlowApDeferralCandidateResponse]
    ap_deferral_rule: Optional[str]


class CashFlowScenariosResponse(_Strict):
    """The ``scenarios`` dict: always exactly base, stress and best."""

    base: CashFlowScenarioResponse
    stress: CashFlowScenarioResponse
    best: CashFlowScenarioResponse


class CashFlowInputsResponse(_Strict):
    """The ``inputs`` dict built in ``project_cash_flow``."""

    opening_balance: str
    start_date: str
    ar_total: str
    ap_total: str
    recurring_flow_count: int
    min_safe_cash: Optional[str]


class CashFlowForecastResponse(_Strict):
    """``CashFlowForecast.to_dict`` — ``POST /audit/cash-flow-projector``."""

    inputs: CashFlowInputsResponse
    scenarios: CashFlowScenariosResponse
    horizon_days: list[int]


# =============================================================================
# Intercompany elimination (intercompany_elimination_engine.py)
# =============================================================================

IntercompanyDirectionValue = Literal["receivable", "payable", "revenue", "expense", "investment", "unknown"]


class IntercompanyLineResponse(_Strict):
    """``IntercompanyLine.to_dict``."""

    entity_id: str
    account: str
    direction: IntercompanyDirectionValue
    counterparty_entity: Optional[str]
    net_balance: str
    debit: str
    credit: str


class IntercompanyEliminationPairResponse(_Strict):
    """``EliminationPair.to_dict`` (``a_has_debit_balance`` is not serialised)."""

    entity_a: str
    entity_b: str
    account_a: str
    account_b: str
    direction_a: IntercompanyDirectionValue
    direction_b: IntercompanyDirectionValue
    amount_a: str
    amount_b: str
    net_residual: str
    reconciles: bool


class IntercompanyMismatchResponse(_Strict):
    """``Mismatch.to_dict``."""

    kind: Literal["no_reciprocal", "amount_mismatch", "direction_mismatch"]
    entity: str
    counterparty: Optional[str]
    account: str
    direction: IntercompanyDirectionValue
    amount: str
    message: str


class IntercompanyEliminationJEResponse(_Strict):
    """``EliminationJE.to_dict``."""

    description: str
    debit_entity: str
    debit_account: str
    credit_entity: str
    credit_account: str
    amount: str


class IntercompanyConsolidationColumnResponse(_Strict):
    """``ConsolidationColumn.to_dict``."""

    entity_id: str
    entity_name: str
    debit_total: str
    credit_total: str
    intercompany_gross: str


class IntercompanyWorksheetResponse(_Strict):
    """``ConsolidationWorksheet.to_dict``."""

    columns: list[IntercompanyConsolidationColumnResponse]
    total_entity_debits: str
    total_entity_credits: str
    elimination_debits: str
    elimination_credits: str
    consolidated_debits: str
    consolidated_credits: str


class IntercompanySummaryResponse(_Strict):
    """The ``summary`` dict built in ``run_intercompany_elimination``."""

    entity_count: int
    intercompany_line_count: int
    matched_pair_count: int
    reconciling_pair_count: int
    mismatch_count: int
    elimination_je_count: int
    consolidation_complete: bool


class IntercompanyEliminationResponse(_Strict):
    """``IntercompanyEliminationResult.to_dict`` — ``POST /audit/intercompany-elimination``."""

    intercompany_lines: list[IntercompanyLineResponse]
    pairs: list[IntercompanyEliminationPairResponse]
    mismatches: list[IntercompanyMismatchResponse]
    elimination_journal_entries: list[IntercompanyEliminationJEResponse]
    worksheet: IntercompanyWorksheetResponse
    summary: IntercompanySummaryResponse


# =============================================================================
# W-2 / W-3 reconciliation (w2_reconciliation_engine.py)
# =============================================================================

W2DiscrepancyKind = Literal[
    "ss_wages",
    "ss_wage_base_exceeded",
    "ss_tax_withholding",
    "medicare_wages",
    "medicare_withholding",
    "additional_medicare",
    "federal_wages",
    "federal_withholding",
    "hsa_over_limit",
    "retirement_over_limit",
    "form_941_mismatch",
    "ss_tax_withheld_vs_payroll",
    "medicare_tax_withheld_vs_payroll",
    "box_12_vs_payroll",
]
W2Severity = Literal["high", "medium", "low"]


class W2DiscrepancyResponse(_Strict):
    """``Discrepancy.to_dict``."""

    employee_id: str
    employee_name: str
    kind: W2DiscrepancyKind
    severity: W2Severity
    expected: str
    actual: str
    difference: str
    message: str


class W2Form941MismatchResponse(_Strict):
    """``Form941Mismatch.to_dict``. ``quarter`` is None for the four-quarter sum."""

    quarter: Optional[int]
    compared_with: Literal["payroll_ytd", "w3"]
    kind: W2DiscrepancyKind
    severity: W2Severity
    expected: str
    actual: str
    difference: str
    message: str


class W2W3TotalsResponse(_Strict):
    """``W3Totals.to_dict``."""

    total_federal_wages: str
    total_federal_withholding: str
    total_ss_wages: str
    total_ss_tax_withheld: str
    total_medicare_wages: str
    total_medicare_tax_withheld: str
    employee_count: int


class W2CheckNotRunResponse(_Strict):
    """One ``checks_not_run`` notice (``_checks_not_run`` / ``_check_form_941``)."""

    check: str
    reason: Literal[
        "limit_not_supplied",
        "age_not_supplied",
        "form_941_quarters_incomplete",
        "form_941_field_not_supplied",
    ]
    employee_ids: list[str]
    message: str


class W2SummaryResponse(_Strict):
    """The ``summary`` dict built in ``reconcile_w2``."""

    employee_count: int
    employees_missing_w2_draft: list[str]
    duplicate_w2_drafts: list[str]
    orphan_w2_drafts: list[str]
    total_employee_discrepancies: int
    informational_notices: int
    total_form_941_mismatches: int
    form_941_quarters_missing: list[int]
    form_941_quarters_duplicated: list[int]
    w3_status: Optional[str]
    discrepancies_by_kind: dict[str, int]


class W2ReconciliationResponse(_Strict):
    """``W2ReconciliationResult.to_dict`` — ``POST /audit/w2-reconciliation``."""

    tax_year: int
    employee_discrepancies: list[W2DiscrepancyResponse]
    form_941_mismatches: list[W2Form941MismatchResponse]
    w3_totals: Optional[W2W3TotalsResponse]
    summary: W2SummaryResponse
    statutory_basis: Optional[int]
    statutory_basis_source: Optional[str]
    checks_not_run: list[W2CheckNotRunResponse]
    statutory_basis_note: str
