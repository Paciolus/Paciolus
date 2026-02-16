"""
Paciolus API — Testing CSV Export Routes (JE, AP, Payroll, TWM, Revenue, AR, FA, Inventory).
Sprint 155: Extracted from routes/export.py.
"""
import csv
import logging
from io import StringIO

from fastapi import APIRouter, HTTPException, Depends, Request

from models import User
from auth import require_verified_user
from shared.helpers import safe_download_filename, sanitize_csv_value
from shared.rate_limits import limiter, RATE_LIMIT_EXPORT
from shared.error_messages import sanitize_error

logger = logging.getLogger(__name__)
from shared.export_helpers import streaming_csv_response, write_testing_csv_summary
from shared.export_schemas import (
    JETestingExportInput, APTestingExportInput, PayrollTestingExportInput,
    ThreeWayMatchExportInput, RevenueTestingExportInput,
    ARAgingExportInput, FixedAssetExportInput, InventoryExportInput,
    SamplingSelectionCSVInput,
)

router = APIRouter(tags=["export"])


# --- JE Testing CSV ---

@router.post("/export/csv/je-testing")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_je_testing(
    request: Request,
    je_input: JETestingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export flagged journal entries as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Test", "Test Key", "Tier", "Severity",
            "Entry ID", "Date", "Account", "Description",
            "Debit", "Credit", "Issue", "Confidence",
        ])

        for tr in je_input.test_results:
            for fe in tr.get("flagged_entries", []):
                entry = fe.get("entry", {})
                writer.writerow([
                    fe.get("test_name", ""),
                    fe.get("test_key", ""),
                    fe.get("test_tier", ""),
                    fe.get("severity", ""),
                    sanitize_csv_value(entry.get("entry_id", "")),
                    entry.get("posting_date", "") or entry.get("entry_date", ""),
                    sanitize_csv_value(entry.get("account", "")),
                    sanitize_csv_value((entry.get("description", "") or "")[:80]),
                    f"{entry.get('debit', 0):.2f}" if entry.get('debit') else "",
                    f"{entry.get('credit', 0):.2f}" if entry.get('credit') else "",
                    sanitize_csv_value(fe.get("issue", "")),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        write_testing_csv_summary(writer, je_input.composite_score, "Entries")

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(je_input.filename, "JETesting_Flagged", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("JE CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "je_csv_export_error")
        )


# --- AP Testing CSV ---

@router.post("/export/csv/ap-testing")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_ap_testing(
    request: Request,
    ap_input: APTestingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export flagged AP payments as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Test", "Test Key", "Tier", "Severity",
            "Vendor", "Invoice #", "Payment Date", "Amount",
            "Check #", "Description", "Issue", "Confidence",
        ])

        for tr in ap_input.test_results:
            for fe in tr.get("flagged_entries", []):
                entry = fe.get("entry", {})
                writer.writerow([
                    fe.get("test_name", ""),
                    fe.get("test_key", ""),
                    fe.get("test_tier", ""),
                    fe.get("severity", ""),
                    sanitize_csv_value(entry.get("vendor_name", "")),
                    sanitize_csv_value(entry.get("invoice_number", "")),
                    entry.get("payment_date", ""),
                    f"{entry.get('amount', 0):.2f}" if entry.get('amount') else "",
                    sanitize_csv_value(entry.get("check_number", "")),
                    sanitize_csv_value((entry.get("description", "") or "")[:80]),
                    sanitize_csv_value(fe.get("issue", "")),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        write_testing_csv_summary(writer, ap_input.composite_score, "Payments")

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(ap_input.filename, "APTesting_Flagged", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("AP CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "ap_csv_export_error")
        )


# --- Payroll Testing CSV ---

@router.post("/export/csv/payroll-testing")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_payroll_testing(
    request: Request,
    payroll_input: PayrollTestingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export flagged payroll entries as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Test", "Test Key", "Tier", "Severity",
            "Employee", "Employee ID", "Department", "Pay Date", "Gross Pay",
            "Issue", "Confidence",
        ])

        for tr in payroll_input.test_results:
            for fe in tr.get("flagged_entries", []):
                entry = fe.get("entry", {})
                writer.writerow([
                    fe.get("test_name", ""),
                    fe.get("test_key", ""),
                    fe.get("test_tier", ""),
                    fe.get("severity", ""),
                    sanitize_csv_value(entry.get("employee_name", "")),
                    sanitize_csv_value(entry.get("employee_id", "")),
                    sanitize_csv_value(entry.get("department", "")),
                    entry.get("pay_date", ""),
                    f"{entry.get('gross_pay', 0):.2f}" if entry.get('gross_pay') else "",
                    sanitize_csv_value(fe.get("issue", "")),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        write_testing_csv_summary(writer, payroll_input.composite_score, "Entries")

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(payroll_input.filename, "PayrollTesting_Flagged", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Payroll CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "payroll_csv_export_error")
        )


# --- Three-Way Match CSV (custom summary) ---

@router.post("/export/csv/three-way-match")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_three_way_match(
    request: Request,
    twm_input: ThreeWayMatchExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export three-way match results as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Match Type", "PO #", "Invoice #", "Receipt #", "Vendor",
            "PO Amount", "Invoice Amount", "Receipt Amount",
            "Variance", "Variance %", "Confidence",
        ])

        all_matches = twm_input.full_matches + twm_input.partial_matches
        for m in all_matches:
            po = m.get("po") or {}
            inv = m.get("invoice") or {}
            rec = m.get("receipt") or {}

            total_variance = sum(v.get("variance_amount", 0) for v in m.get("variances", []))
            max_pct = max((v.get("variance_pct", 0) for v in m.get("variances", [])), default=0)

            writer.writerow([
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
            ])

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
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(twm_input.filename, "TWM_Results", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("TWM CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "twm_csv_export_error")
        )


# --- Revenue Testing CSV ---

@router.post("/export/csv/revenue-testing")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_revenue_testing(
    request: Request,
    revenue_input: RevenueTestingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export flagged revenue entries as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Test", "Test Key", "Tier", "Severity",
            "Account Name", "Account Number", "Date", "Amount",
            "Description", "Entry Type", "Reference",
            "Issue", "Confidence",
        ])

        for tr in revenue_input.test_results:
            for fe in tr.get("flagged_entries", []):
                entry = fe.get("entry", {})
                writer.writerow([
                    fe.get("test_name", ""),
                    fe.get("test_key", ""),
                    fe.get("test_tier", ""),
                    fe.get("severity", ""),
                    sanitize_csv_value(entry.get("account_name", "")),
                    sanitize_csv_value(entry.get("account_number", "")),
                    entry.get("date", ""),
                    f"{entry.get('amount', 0):.2f}" if entry.get('amount') is not None else "",
                    sanitize_csv_value((entry.get("description", "") or "")[:80]),
                    sanitize_csv_value(entry.get("entry_type", "")),
                    sanitize_csv_value(entry.get("reference", "")),
                    sanitize_csv_value(fe.get("issue", "")),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        write_testing_csv_summary(writer, revenue_input.composite_score, "Revenue Entries")

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(revenue_input.filename, "RevenueTesting_Flagged", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Revenue CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "revenue_csv_export_error")
        )


# --- AR Aging CSV (custom summary) ---

@router.post("/export/csv/ar-aging")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_ar_aging(
    request: Request,
    ar_input: ARAgingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export flagged AR aging items as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Test", "Test Key", "Tier", "Severity",
            "Account Name", "Customer Name", "Invoice #", "Date",
            "Amount", "Aging Days", "Issue", "Confidence",
        ])

        for tr in ar_input.test_results:
            for fe in tr.get("flagged_entries", []):
                entry = fe.get("entry", {})
                writer.writerow([
                    fe.get("test_name", ""),
                    fe.get("test_key", ""),
                    fe.get("test_tier", ""),
                    fe.get("severity", ""),
                    sanitize_csv_value(entry.get("account_name", "")),
                    sanitize_csv_value(entry.get("customer_name", "")),
                    sanitize_csv_value(entry.get("invoice_number", "")),
                    entry.get("date", ""),
                    f"{entry.get('amount', 0):.2f}" if entry.get('amount') is not None else "",
                    str(entry.get("aging_days", "")) if entry.get("aging_days") is not None else "",
                    sanitize_csv_value(fe.get("issue", "")),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        # Custom summary for AR Aging
        cs = ar_input.composite_score
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Composite Score", f"{cs.get('score', 0):.1f}"])
        writer.writerow(["Risk Tier", cs.get("risk_tier", "")])
        writer.writerow(["Total Flagged", cs.get("total_flagged", 0)])
        writer.writerow(["Tests Run", cs.get("tests_run", 0)])
        writer.writerow(["Tests Skipped", cs.get("tests_skipped", 0)])
        writer.writerow(["Has Sub-Ledger", cs.get("has_subledger", False)])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(ar_input.filename, "ARAging_Flagged", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("AR Aging CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "ar_aging_csv_export_error")
        )


# --- Fixed Asset Testing CSV ---

@router.post("/export/csv/fixed-assets")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_fixed_assets(
    request: Request,
    fa_input: FixedAssetExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export flagged fixed assets as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Test", "Test Key", "Tier", "Severity",
            "Asset ID", "Description", "Category", "Cost",
            "Accum Depreciation", "Useful Life", "Acquisition Date",
            "Issue", "Confidence",
        ])

        for tr in fa_input.test_results:
            for fe in tr.get("flagged_entries", []):
                entry = fe.get("entry", {})
                writer.writerow([
                    fe.get("test_name", ""),
                    fe.get("test_key", ""),
                    fe.get("test_tier", ""),
                    fe.get("severity", ""),
                    sanitize_csv_value(entry.get("asset_id", "")),
                    sanitize_csv_value((entry.get("description", "") or "")[:80]),
                    sanitize_csv_value(entry.get("category", "")),
                    f"{entry.get('cost', 0):.2f}" if entry.get('cost') is not None else "",
                    f"{entry.get('accumulated_depreciation', 0):.2f}" if entry.get('accumulated_depreciation') is not None else "",
                    str(entry.get("useful_life", "")) if entry.get("useful_life") is not None else "",
                    entry.get("acquisition_date", ""),
                    sanitize_csv_value(fe.get("issue", "")),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        write_testing_csv_summary(writer, fa_input.composite_score, "Assets")

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(fa_input.filename, "FixedAsset_Flagged", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Fixed Asset CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "fa_csv_export_error")
        )


# --- Inventory Testing CSV ---

@router.post("/export/csv/inventory")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_inventory(
    request: Request,
    inv_input: InventoryExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export flagged inventory items as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Test", "Test Key", "Tier", "Severity",
            "Item ID", "Description", "Category", "Quantity",
            "Unit Cost", "Extended Value", "Location",
            "Last Movement Date", "Issue", "Confidence",
        ])

        for tr in inv_input.test_results:
            for fe in tr.get("flagged_entries", []):
                entry = fe.get("entry", {})
                writer.writerow([
                    fe.get("test_name", ""),
                    fe.get("test_key", ""),
                    fe.get("test_tier", ""),
                    fe.get("severity", ""),
                    sanitize_csv_value(entry.get("item_id", "")),
                    sanitize_csv_value((entry.get("description", "") or "")[:80]),
                    sanitize_csv_value(entry.get("category", "")),
                    f"{entry.get('quantity', 0):.2f}" if entry.get('quantity') is not None else "",
                    f"{entry.get('unit_cost', 0):.2f}" if entry.get('unit_cost') is not None else "",
                    f"{entry.get('extended_value', 0):.2f}" if entry.get('extended_value') is not None else "",
                    sanitize_csv_value(entry.get("location", "")),
                    entry.get("last_movement_date", ""),
                    sanitize_csv_value(fe.get("issue", "")),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        write_testing_csv_summary(writer, inv_input.composite_score, "Items")

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(inv_input.filename, "Inventory_Flagged", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Inventory CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "inv_csv_export_error")
        )


# --- Sampling Selection CSV ---

@router.post("/export/csv/sampling-selection")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_sampling_selection(
    request: Request,
    sampling_input: SamplingSelectionCSVInput,
    current_user: User = Depends(require_verified_user),
):
    """Export selected sample items as CSV with blank 'Audited Amount' column."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Row #", "Item ID", "Description", "Recorded Amount",
            "Audited Amount", "Stratum", "Selection Method",
        ])

        for item in sampling_input.selected_items:
            writer.writerow([
                item.get("row_index", ""),
                sanitize_csv_value(item.get("item_id", "")),
                sanitize_csv_value((item.get("description", "") or "")[:80]),
                f"{item.get('recorded_amount', 0):.2f}" if item.get('recorded_amount') is not None else "",
                "",  # Blank audited amount for auditor to fill in
                item.get("stratum", ""),
                item.get("selection_method", ""),
            ])

        # Summary
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Sampling Method", sampling_input.method.upper()])
        writer.writerow(["Population Size", f"{sampling_input.population_size:,}"])
        writer.writerow(["Population Value", f"${sampling_input.population_value:,.2f}"])
        writer.writerow(["Items Selected", len(sampling_input.selected_items)])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(sampling_input.filename, "SamplingSelection", "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Sampling selection CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "sampling_csv_export_error")
        )
