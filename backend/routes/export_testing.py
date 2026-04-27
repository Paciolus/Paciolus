"""
Paciolus API — Testing CSV Export Routes (JE, AP, Payroll, TWM, Revenue, AR, FA, Inventory).
Sprint 155: Extracted from routes/export.py.
Sprint 539: Schema-driven CSV serializer refactor — shared csv_export_handler.
Sprint 725: csv_export_handler promoted to backend/shared/csv_export.py for cross-module reuse.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from auth import require_verified_user
from models import User
from shared.csv_export import ColumnSpec, csv_export_handler, diagnostic_csv_export
from shared.entitlement_checks import check_export_access
from shared.filenames import sanitize_csv_value
from shared.rate_limits import RATE_LIMIT_EXPORT, limiter

logger = logging.getLogger(__name__)
from shared.export_schemas import (
    APTestingExportInput,
    ARAgingExportInput,
    FixedAssetExportInput,
    InventoryExportInput,
    JETestingExportInput,
    PayrollTestingExportInput,
    RevenueTestingExportInput,
    SamplingSelectionCSVInput,
    ThreeWayMatchExportInput,
)

router = APIRouter(tags=["export"])


# ---------------------------------------------------------------------------
# Schema-driven CSV field extraction
# ---------------------------------------------------------------------------
#
# Each column in a tool's CSV is described by a (header, extractor) pair.
# The extractor receives (flagged_entry_dict, entry_dict) and returns the
# cell value as a string.  Four common field prefixes exist:
#   - flag_*   : pulled from the flagged_entry envelope
#   - entry_*  : pulled from the nested entry dict
#   - money_*  : numeric with :.2f formatting (blank when falsy/None)
#   - sanitized_*: run through sanitize_csv_value for formula-injection defense
#
# Rather than building yet another mini-DSL, we use plain lambdas — they are
# transparent, auditable, and preserve the exact original formatting logic.
# ---------------------------------------------------------------------------

# ColumnSpec is imported from shared.csv_export.

# -- Shared prefix columns (every flagged-entry tool starts with these) ------
_FLAG_PREFIX: list[ColumnSpec] = [
    ("Test", lambda fe, _e: fe.get("test_name", "")),
    ("Test Key", lambda fe, _e: fe.get("test_key", "")),
    ("Tier", lambda fe, _e: fe.get("test_tier", "")),
    ("Severity", lambda fe, _e: fe.get("severity", "")),
]

# -- Shared suffix columns (every flagged-entry tool ends with these) --------
_FLAG_SUFFIX: list[ColumnSpec] = [
    ("Issue", lambda fe, _e: sanitize_csv_value(fe.get("issue", ""))),
    ("Confidence", lambda fe, _e: f"{fe.get('confidence', 0):.2f}"),
]


def _build_schema(*groups: list[ColumnSpec]) -> list[ColumnSpec]:
    """Concatenate column-spec groups into a single flat schema."""
    result: list[ColumnSpec] = []
    for g in groups:
        result.extend(g)
    return result


# ---------------------------------------------------------------------------
# Per-tool column schemas
# ---------------------------------------------------------------------------

JE_COLUMNS: list[ColumnSpec] = _build_schema(
    _FLAG_PREFIX,
    [
        ("Entry ID", lambda _fe, e: sanitize_csv_value(e.get("entry_id", ""))),
        ("Date", lambda _fe, e: e.get("posting_date", "") or e.get("entry_date", "")),
        ("Account", lambda _fe, e: sanitize_csv_value(e.get("account", ""))),
        ("Description", lambda _fe, e: sanitize_csv_value((e.get("description", "") or "")[:80])),
        ("Debit", lambda _fe, e: f"{e.get('debit', 0):.2f}" if e.get("debit") else ""),
        ("Credit", lambda _fe, e: f"{e.get('credit', 0):.2f}" if e.get("credit") else ""),
    ],
    _FLAG_SUFFIX,
)

AP_COLUMNS: list[ColumnSpec] = _build_schema(
    _FLAG_PREFIX,
    [
        ("Vendor", lambda _fe, e: sanitize_csv_value(e.get("vendor_name", ""))),
        ("Invoice #", lambda _fe, e: sanitize_csv_value(e.get("invoice_number", ""))),
        ("Payment Date", lambda _fe, e: e.get("payment_date", "")),
        ("Amount", lambda _fe, e: f"{e.get('amount', 0):.2f}" if e.get("amount") else ""),
        ("Check #", lambda _fe, e: sanitize_csv_value(e.get("check_number", ""))),
        ("Description", lambda _fe, e: sanitize_csv_value((e.get("description", "") or "")[:80])),
    ],
    _FLAG_SUFFIX,
)

PAYROLL_COLUMNS: list[ColumnSpec] = _build_schema(
    _FLAG_PREFIX,
    [
        ("Employee", lambda _fe, e: sanitize_csv_value(e.get("employee_name", ""))),
        ("Employee ID", lambda _fe, e: sanitize_csv_value(e.get("employee_id", ""))),
        ("Department", lambda _fe, e: sanitize_csv_value(e.get("department", ""))),
        ("Pay Date", lambda _fe, e: e.get("pay_date", "")),
        ("Gross Pay", lambda _fe, e: f"{e.get('gross_pay', 0):.2f}" if e.get("gross_pay") else ""),
    ],
    _FLAG_SUFFIX,
)

REVENUE_COLUMNS: list[ColumnSpec] = _build_schema(
    _FLAG_PREFIX,
    [
        ("Account Name", lambda _fe, e: sanitize_csv_value(e.get("account_name", ""))),
        ("Account Number", lambda _fe, e: sanitize_csv_value(e.get("account_number", ""))),
        ("Date", lambda _fe, e: e.get("date", "")),
        ("Amount", lambda _fe, e: f"{e.get('amount', 0):.2f}" if e.get("amount") is not None else ""),
        ("Description", lambda _fe, e: sanitize_csv_value((e.get("description", "") or "")[:80])),
        ("Entry Type", lambda _fe, e: sanitize_csv_value(e.get("entry_type", ""))),
        ("Reference", lambda _fe, e: sanitize_csv_value(e.get("reference", ""))),
    ],
    _FLAG_SUFFIX,
)

AR_COLUMNS: list[ColumnSpec] = _build_schema(
    _FLAG_PREFIX,
    [
        ("Account Name", lambda _fe, e: sanitize_csv_value(e.get("account_name", ""))),
        ("Customer Name", lambda _fe, e: sanitize_csv_value(e.get("customer_name", ""))),
        ("Invoice #", lambda _fe, e: sanitize_csv_value(e.get("invoice_number", ""))),
        ("Date", lambda _fe, e: e.get("date", "")),
        ("Amount", lambda _fe, e: f"{e.get('amount', 0):.2f}" if e.get("amount") is not None else ""),
        ("Aging Days", lambda _fe, e: str(e.get("aging_days", "")) if e.get("aging_days") is not None else ""),
    ],
    _FLAG_SUFFIX,
)

FA_COLUMNS: list[ColumnSpec] = _build_schema(
    _FLAG_PREFIX,
    [
        ("Asset ID", lambda _fe, e: sanitize_csv_value(e.get("asset_id", ""))),
        ("Description", lambda _fe, e: sanitize_csv_value((e.get("description", "") or "")[:80])),
        ("Category", lambda _fe, e: sanitize_csv_value(e.get("category", ""))),
        ("Cost", lambda _fe, e: f"{e.get('cost', 0):.2f}" if e.get("cost") is not None else ""),
        (
            "Accum Depreciation",
            lambda _fe, e: (
                f"{e.get('accumulated_depreciation', 0):.2f}" if e.get("accumulated_depreciation") is not None else ""
            ),
        ),
        ("Useful Life", lambda _fe, e: str(e.get("useful_life", "")) if e.get("useful_life") is not None else ""),
        ("Acquisition Date", lambda _fe, e: e.get("acquisition_date", "")),
    ],
    _FLAG_SUFFIX,
)

INVENTORY_COLUMNS: list[ColumnSpec] = _build_schema(
    _FLAG_PREFIX,
    [
        ("Item ID", lambda _fe, e: sanitize_csv_value(e.get("item_id", ""))),
        ("Description", lambda _fe, e: sanitize_csv_value((e.get("description", "") or "")[:80])),
        ("Category", lambda _fe, e: sanitize_csv_value(e.get("category", ""))),
        ("Quantity", lambda _fe, e: f"{e.get('quantity', 0):.2f}" if e.get("quantity") is not None else ""),
        ("Unit Cost", lambda _fe, e: f"{e.get('unit_cost', 0):.2f}" if e.get("unit_cost") is not None else ""),
        (
            "Extended Value",
            lambda _fe, e: f"{e.get('extended_value', 0):.2f}" if e.get("extended_value") is not None else "",
        ),
        ("Location", lambda _fe, e: sanitize_csv_value(e.get("location", ""))),
        ("Last Movement Date", lambda _fe, e: e.get("last_movement_date", "")),
    ],
    _FLAG_SUFFIX,
)


# ---------------------------------------------------------------------------
# Custom summary writers for tools that diverge from the standard pattern
# ---------------------------------------------------------------------------


def _ar_aging_summary_writer(writer: Any, composite_score: dict[str, Any]) -> None:
    """AR Aging has a custom summary layout including has_subledger."""
    writer.writerow([])
    writer.writerow(["SUMMARY"])
    writer.writerow(["Composite Score", f"{composite_score.get('score', 0):.1f}"])
    writer.writerow(["Diagnostic Tier", composite_score.get("risk_tier", "")])
    writer.writerow(["Total Flagged", composite_score.get("total_flagged", 0)])
    writer.writerow(["Tests Run", composite_score.get("tests_run", 0)])
    writer.writerow(["Tests Skipped", composite_score.get("tests_skipped", 0)])
    writer.writerow(["Has Sub-Ledger", composite_score.get("has_subledger", False)])


# ---------------------------------------------------------------------------
# Route endpoints — standard flagged-entry tools (schema-driven)
# ---------------------------------------------------------------------------


@router.post("/export/csv/je-testing", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_je_testing(
    request: Request,
    je_input: JETestingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export flagged journal entries as CSV."""
    return csv_export_handler(
        test_results=je_input.test_results,
        schema=JE_COLUMNS,
        composite_score=je_input.composite_score,
        filename_raw=je_input.filename,
        filename_suffix="JETesting_Flagged",
        entry_label="Entries",
        error_log_prefix="JE",
        error_code="je_csv_export_error",
    )


@router.post("/export/csv/ap-testing", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_ap_testing(
    request: Request,
    ap_input: APTestingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export flagged AP payments as CSV."""
    return csv_export_handler(
        test_results=ap_input.test_results,
        schema=AP_COLUMNS,
        composite_score=ap_input.composite_score,
        filename_raw=ap_input.filename,
        filename_suffix="APTesting_Flagged",
        entry_label="Payments",
        error_log_prefix="AP",
        error_code="ap_csv_export_error",
    )


@router.post("/export/csv/payroll-testing", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_payroll_testing(
    request: Request,
    payroll_input: PayrollTestingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export flagged payroll entries as CSV."""
    return csv_export_handler(
        test_results=payroll_input.test_results,
        schema=PAYROLL_COLUMNS,
        composite_score=payroll_input.composite_score,
        filename_raw=payroll_input.filename,
        filename_suffix="PayrollTesting_Flagged",
        entry_label="Entries",
        error_log_prefix="Payroll",
        error_code="payroll_csv_export_error",
    )


@router.post("/export/csv/revenue-testing", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_revenue_testing(
    request: Request,
    revenue_input: RevenueTestingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export flagged revenue entries as CSV."""
    return csv_export_handler(
        test_results=revenue_input.test_results,
        schema=REVENUE_COLUMNS,
        composite_score=revenue_input.composite_score,
        filename_raw=revenue_input.filename,
        filename_suffix="RevenueTesting_Flagged",
        entry_label="Revenue Entries",
        error_log_prefix="Revenue",
        error_code="revenue_csv_export_error",
    )


@router.post("/export/csv/ar-aging", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_ar_aging(
    request: Request,
    ar_input: ARAgingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export flagged AR aging items as CSV."""
    return csv_export_handler(
        test_results=ar_input.test_results,
        schema=AR_COLUMNS,
        composite_score=ar_input.composite_score,
        filename_raw=ar_input.filename,
        filename_suffix="ARAging_Flagged",
        entry_label="Items",
        error_log_prefix="AR Aging",
        error_code="ar_aging_csv_export_error",
        summary_writer=_ar_aging_summary_writer,
    )


@router.post("/export/csv/fixed-assets", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_fixed_assets(
    request: Request,
    fa_input: FixedAssetExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export flagged fixed assets as CSV."""
    return csv_export_handler(
        test_results=fa_input.test_results,
        schema=FA_COLUMNS,
        composite_score=fa_input.composite_score,
        filename_raw=fa_input.filename,
        filename_suffix="FixedAsset_Flagged",
        entry_label="Assets",
        error_log_prefix="Fixed Asset",
        error_code="fa_csv_export_error",
    )


@router.post("/export/csv/inventory", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_inventory(
    request: Request,
    inv_input: InventoryExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export flagged inventory items as CSV."""
    return csv_export_handler(
        test_results=inv_input.test_results,
        schema=INVENTORY_COLUMNS,
        composite_score=inv_input.composite_score,
        filename_raw=inv_input.filename,
        filename_suffix="Inventory_Flagged",
        entry_label="Items",
        error_log_prefix="Inventory",
        error_code="inv_csv_export_error",
    )


# ---------------------------------------------------------------------------
# Non-standard exports (TWM, Sampling) — custom iteration logic
# ---------------------------------------------------------------------------


@router.post("/export/csv/three-way-match", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_three_way_match(
    request: Request,
    twm_input: ThreeWayMatchExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export three-way match results as CSV."""

    def _body(writer: Any) -> None:
        writer.writerow(
            [
                "Match Type",
                "PO #",
                "Invoice #",
                "Receipt #",
                "Vendor",
                "PO Amount",
                "Invoice Amount",
                "Receipt Amount",
                "Variance",
                "Variance %",
                "Confidence",
            ]
        )

        all_matches = twm_input.full_matches + twm_input.partial_matches
        for m in all_matches:
            po = m.get("po") or {}
            inv = m.get("invoice") or {}
            rec = m.get("receipt") or {}

            total_variance = sum(v.get("variance_amount", 0) for v in m.get("variances", []))
            max_pct = max((v.get("variance_pct", 0) for v in m.get("variances", [])), default=0)

            writer.writerow(
                [
                    m.get("match_type", ""),
                    sanitize_csv_value(po.get("po_number", "")),
                    sanitize_csv_value(inv.get("invoice_number", "")),
                    sanitize_csv_value(rec.get("receipt_number", "")),
                    sanitize_csv_value(po.get("vendor", "") or inv.get("vendor", "")),
                    f"{po.get('total_amount', 0):.2f}" if po else "",
                    f"{inv.get('total_amount', 0):.2f}" if inv else "",
                    f"{rec.get('total_amount', 0):.2f}" if rec else "",
                    f"{total_variance:.2f}" if total_variance else "",
                    f"{max_pct:.1%}" if max_pct else "",
                    f"{m.get('match_confidence', 0):.2f}",
                ]
            )

        s = twm_input.summary
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Total POs", s.get("total_pos", 0)])
        writer.writerow(["Total Invoices", s.get("total_invoices", 0)])
        writer.writerow(["Total Receipts", s.get("total_receipts", 0)])
        writer.writerow(["Full Matches", s.get("full_match_count", 0)])
        writer.writerow(["Partial Matches", s.get("partial_match_count", 0)])
        writer.writerow(["Full Match Rate", f"{s.get('full_match_rate', 0):.1%}"])
        writer.writerow(["Net Variance", f"${s.get('net_variance', 0):,.2f}"])
        writer.writerow(["Risk Assessment", sanitize_csv_value(s.get("risk_assessment", ""))])

    return diagnostic_csv_export(
        body_writer=_body,
        filename_raw=twm_input.filename,
        filename_suffix="TWM_Results",
        error_log_prefix="TWM",
        error_code="twm_csv_export_error",
    )


@router.post("/export/csv/sampling-selection", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_sampling_selection(
    request: Request,
    sampling_input: SamplingSelectionCSVInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export selected sample items as CSV with blank 'Audited Amount' column."""

    def _body(writer: Any) -> None:
        writer.writerow(
            [
                "Row #",
                "Item ID",
                "Description",
                "Recorded Amount",
                "Audited Amount",
                "Stratum",
                "Selection Method",
            ]
        )

        for item in sampling_input.selected_items:
            writer.writerow(
                [
                    item.get("row_index", ""),
                    sanitize_csv_value(item.get("item_id", "")),
                    sanitize_csv_value((item.get("description", "") or "")[:80]),
                    f"{item.get('recorded_amount', 0):.2f}" if item.get("recorded_amount") is not None else "",
                    "",  # Blank audited amount for auditor to fill in
                    item.get("stratum", ""),
                    item.get("selection_method", ""),
                ]
            )

        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Sampling Method", sampling_input.method.upper()])
        writer.writerow(["Population Size", f"{sampling_input.population_size:,}"])
        writer.writerow(["Population Value", f"${sampling_input.population_value:,.2f}"])
        writer.writerow(["Items Selected", len(sampling_input.selected_items)])

    return diagnostic_csv_export(
        body_writer=_body,
        filename_raw=sampling_input.filename,
        filename_suffix="SamplingSelection",
        error_log_prefix="Sampling selection",
        error_code="sampling_csv_export_error",
    )
