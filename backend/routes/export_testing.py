"""
Paciolus API — Testing CSV Export Routes (JE, AP, Payroll, TWM, Revenue, AR, FA, Inventory).
Sprint 155: Extracted from routes/export.py.
Sprint 539: Schema-driven CSV serializer refactor — shared csv_export_handler.
"""

import csv
import logging
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from auth import require_verified_user
from models import User
from shared.entitlement_checks import check_export_access
from shared.error_messages import sanitize_error
from shared.helpers import safe_download_filename, sanitize_csv_value
from shared.rate_limits import RATE_LIMIT_EXPORT, limiter

logger = logging.getLogger(__name__)
from shared.export_helpers import streaming_csv_response, write_testing_csv_summary
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

# Type alias for a single column schema entry.
ColumnSpec = tuple[str, Any]  # (header_label, extractor_callable)

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
# Shared CSV export pipeline
# ---------------------------------------------------------------------------

SummaryWriter = Any  # Callable[[csv.writer, dict], None] | None


def _write_flagged_rows(writer: Any, test_results: list[dict], schema: list[ColumnSpec]) -> None:
    """Iterate test_results → flagged_entries and emit one CSV row per entry."""
    for tr in test_results:
        for fe in tr.get("flagged_entries", []):
            entry = fe.get("entry", {})
            writer.writerow([extractor(fe, entry) for _header, extractor in schema])


def csv_export_handler(
    *,
    test_results: list[dict],
    schema: list[ColumnSpec],
    composite_score: dict[str, Any],
    filename_raw: str,
    filename_suffix: str,
    entry_label: str,
    error_log_prefix: str,
    error_code: str,
    summary_writer: SummaryWriter = None,
) -> StreamingResponse:
    """Shared pipeline: header → flagged rows → summary → encode → response.

    Args:
        test_results: The test_results list from the export input model.
        schema: Column schema (list of (header, extractor) tuples).
        composite_score: The composite_score dict for the summary section.
        filename_raw: Raw filename from client input.
        filename_suffix: Fallback suffix for safe_download_filename.
        entry_label: Label for write_testing_csv_summary (e.g. "Entries").
        error_log_prefix: Prefix for the logger.exception message.
        error_code: Error code slug for sanitize_error.
        summary_writer: Optional custom summary writer. If None, uses the
            standard write_testing_csv_summary. Receives (writer, composite_score).
    """
    try:
        output = StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([header for header, _extractor in schema])

        # Data rows
        _write_flagged_rows(writer, test_results, schema)

        # Summary section
        if summary_writer is not None:
            summary_writer(writer, composite_score)
        else:
            write_testing_csv_summary(writer, composite_score, entry_label)

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode("utf-8-sig")

        download_filename = safe_download_filename(filename_raw, filename_suffix, "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("%s CSV export failed", error_log_prefix)
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", error_code))


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
    try:
        output = StringIO()
        writer = csv.writer(output)

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

        # Custom summary for TWM
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

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode("utf-8-sig")

        download_filename = safe_download_filename(twm_input.filename, "TWM_Results", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("TWM CSV export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "twm_csv_export_error"))


@router.post("/export/csv/sampling-selection", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_sampling_selection(
    request: Request,
    sampling_input: SamplingSelectionCSVInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Export selected sample items as CSV with blank 'Audited Amount' column."""
    try:
        output = StringIO()
        writer = csv.writer(output)

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

        # Summary
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Sampling Method", sampling_input.method.upper()])
        writer.writerow(["Population Size", f"{sampling_input.population_size:,}"])
        writer.writerow(["Population Value", f"${sampling_input.population_value:,.2f}"])
        writer.writerow(["Items Selected", len(sampling_input.selected_items)])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode("utf-8-sig")

        download_filename = safe_download_filename(sampling_input.filename, "SamplingSelection", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Sampling selection CSV export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "sampling_csv_export_error"))
