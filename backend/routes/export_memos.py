"""
Paciolus API — Memo PDF Export Routes (all 10 testing/tool memo endpoints).
Sprint 155: Extracted from routes/export.py.
"""
from fastapi import APIRouter, HTTPException, Depends, Request

from models import User
from auth import require_verified_user
from je_testing_memo_generator import generate_je_testing_memo
from ap_testing_memo_generator import generate_ap_testing_memo
from payroll_testing_memo_generator import generate_payroll_testing_memo
from three_way_match_memo_generator import generate_three_way_match_memo
from revenue_testing_memo_generator import generate_revenue_testing_memo
from ar_aging_memo_generator import generate_ar_aging_memo
from fixed_asset_testing_memo_generator import generate_fixed_asset_testing_memo
from inventory_testing_memo_generator import generate_inventory_testing_memo
from bank_reconciliation_memo_generator import generate_bank_rec_memo
from multi_period_memo_generator import generate_multi_period_memo
from shared.helpers import safe_download_filename
from shared.rate_limits import limiter, RATE_LIMIT_EXPORT
from shared.error_messages import sanitize_error
from shared.export_helpers import streaming_pdf_response
from shared.export_schemas import (
    JETestingExportInput, APTestingExportInput, PayrollTestingExportInput,
    ThreeWayMatchExportInput, RevenueTestingExportInput,
    ARAgingExportInput, FixedAssetExportInput, InventoryExportInput,
    BankRecMemoInput, MultiPeriodMemoInput,
)

router = APIRouter(tags=["export"])


# --- JE Testing Memo PDF ---

@router.post("/export/je-testing-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_je_testing_memo(
    request: Request,
    je_input: JETestingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download a JE Testing Memo PDF."""
    try:
        result_dict = je_input.model_dump()
        pdf_bytes = generate_je_testing_memo(
            je_result=result_dict,
            filename=je_input.filename,
            client_name=je_input.client_name,
            period_tested=je_input.period_tested,
            prepared_by=je_input.prepared_by,
            reviewed_by=je_input.reviewed_by,
            workpaper_date=je_input.workpaper_date,
        )

        download_filename = safe_download_filename(je_input.filename, "JETesting_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "je_memo_export_error")
        )


# --- AP Testing Memo PDF ---

@router.post("/export/ap-testing-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_ap_testing_memo(
    request: Request,
    ap_input: APTestingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download an AP Testing Memo PDF."""
    try:
        result_dict = ap_input.model_dump()
        pdf_bytes = generate_ap_testing_memo(
            ap_result=result_dict,
            filename=ap_input.filename,
            client_name=ap_input.client_name,
            period_tested=ap_input.period_tested,
            prepared_by=ap_input.prepared_by,
            reviewed_by=ap_input.reviewed_by,
            workpaper_date=ap_input.workpaper_date,
        )

        download_filename = safe_download_filename(ap_input.filename, "APTesting_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "ap_memo_export_error")
        )


# --- Payroll Testing Memo ---

@router.post("/export/payroll-testing-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_payroll_testing_memo(
    request: Request,
    payroll_input: PayrollTestingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download a Payroll Testing Memo PDF."""
    try:
        result_dict = payroll_input.model_dump()
        pdf_bytes = generate_payroll_testing_memo(
            payroll_result=result_dict,
            filename=payroll_input.filename,
            client_name=payroll_input.client_name,
            period_tested=payroll_input.period_tested,
            prepared_by=payroll_input.prepared_by,
            reviewed_by=payroll_input.reviewed_by,
            workpaper_date=payroll_input.workpaper_date,
        )

        download_filename = safe_download_filename(payroll_input.filename, "PayrollTesting_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "payroll_memo_export_error")
        )


# --- Three-Way Match Memo PDF ---

@router.post("/export/three-way-match-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_three_way_match_memo(
    request: Request,
    twm_input: ThreeWayMatchExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download a Three-Way Match Memo PDF."""
    try:
        result_dict = twm_input.model_dump()
        pdf_bytes = generate_three_way_match_memo(
            twm_result=result_dict,
            filename=twm_input.filename,
            client_name=twm_input.client_name,
            period_tested=twm_input.period_tested,
            prepared_by=twm_input.prepared_by,
            reviewed_by=twm_input.reviewed_by,
            workpaper_date=twm_input.workpaper_date,
        )

        download_filename = safe_download_filename(twm_input.filename, "TWM_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "twm_memo_export_error")
        )


# --- Revenue Testing Memo PDF ---

@router.post("/export/revenue-testing-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_revenue_testing_memo(
    request: Request,
    revenue_input: RevenueTestingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download a Revenue Testing Memo PDF."""
    try:
        result_dict = revenue_input.model_dump()
        pdf_bytes = generate_revenue_testing_memo(
            revenue_result=result_dict,
            filename=revenue_input.filename,
            client_name=revenue_input.client_name,
            period_tested=revenue_input.period_tested,
            prepared_by=revenue_input.prepared_by,
            reviewed_by=revenue_input.reviewed_by,
            workpaper_date=revenue_input.workpaper_date,
        )

        download_filename = safe_download_filename(revenue_input.filename, "RevenueTesting_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "revenue_memo_export_error")
        )


# --- AR Aging Memo PDF ---

@router.post("/export/ar-aging-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_ar_aging_memo(
    request: Request,
    ar_input: ARAgingExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download an AR Aging Analysis Memo PDF."""
    try:
        result_dict = ar_input.model_dump()
        pdf_bytes = generate_ar_aging_memo(
            ar_result=result_dict,
            filename=ar_input.filename,
            client_name=ar_input.client_name,
            period_tested=ar_input.period_tested,
            prepared_by=ar_input.prepared_by,
            reviewed_by=ar_input.reviewed_by,
            workpaper_date=ar_input.workpaper_date,
        )

        download_filename = safe_download_filename(ar_input.filename, "ARAging_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "ar_aging_memo_export_error")
        )


# --- Fixed Asset Testing Memo PDF ---

@router.post("/export/fixed-asset-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_fixed_asset_memo(
    request: Request,
    fa_input: FixedAssetExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download a Fixed Asset Testing Memo PDF."""
    try:
        result_dict = fa_input.model_dump()
        pdf_bytes = generate_fixed_asset_testing_memo(
            fa_result=result_dict,
            filename=fa_input.filename,
            client_name=fa_input.client_name,
            period_tested=fa_input.period_tested,
            prepared_by=fa_input.prepared_by,
            reviewed_by=fa_input.reviewed_by,
            workpaper_date=fa_input.workpaper_date,
        )

        download_filename = safe_download_filename(fa_input.filename, "FixedAsset_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "fa_memo_export_error")
        )


# --- Inventory Testing Memo PDF ---

@router.post("/export/inventory-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_inventory_memo(
    request: Request,
    inv_input: InventoryExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download an Inventory Testing Memo PDF."""
    try:
        result_dict = inv_input.model_dump()
        pdf_bytes = generate_inventory_testing_memo(
            inv_result=result_dict,
            filename=inv_input.filename,
            client_name=inv_input.client_name,
            period_tested=inv_input.period_tested,
            prepared_by=inv_input.prepared_by,
            reviewed_by=inv_input.reviewed_by,
            workpaper_date=inv_input.workpaper_date,
        )

        download_filename = safe_download_filename(inv_input.filename, "Inventory_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "inv_memo_export_error")
        )


# --- Bank Reconciliation Memo PDF ---

@router.post("/export/bank-rec-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_bank_rec_memo(
    request: Request,
    rec_input: BankRecMemoInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download a Bank Reconciliation Memo PDF."""
    try:
        result_dict = rec_input.model_dump()
        pdf_bytes = generate_bank_rec_memo(
            rec_result=result_dict,
            filename=rec_input.filename,
            client_name=rec_input.client_name,
            period_tested=rec_input.period_tested,
            prepared_by=rec_input.prepared_by,
            reviewed_by=rec_input.reviewed_by,
            workpaper_date=rec_input.workpaper_date,
        )

        download_filename = safe_download_filename(rec_input.filename, "BankRec_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "bank_rec_memo_export_error")
        )


# --- Multi-Period Comparison Memo PDF ---

@router.post("/export/multi-period-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_multi_period_memo(
    request: Request,
    mp_input: MultiPeriodMemoInput,
    current_user: User = Depends(require_verified_user),
):
    """Generate and download a Multi-Period Comparison Memo PDF."""
    try:
        result_dict = mp_input.model_dump()
        pdf_bytes = generate_multi_period_memo(
            comparison_result=result_dict,
            filename=mp_input.filename,
            client_name=mp_input.client_name,
            period_tested=mp_input.period_tested,
            prepared_by=mp_input.prepared_by,
            reviewed_by=mp_input.reviewed_by,
            workpaper_date=mp_input.workpaper_date,
        )

        download_filename = safe_download_filename(mp_input.filename, "MultiPeriod_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "multi_period_memo_export_error")
        )
