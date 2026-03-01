"""
Paciolus API — Memo PDF Export Routes (all 10 testing/tool memo endpoints).
Sprint 155: Extracted from routes/export.py.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from auth import require_verified_user
from models import User

logger = logging.getLogger(__name__)
from accrual_completeness_memo import generate_accrual_completeness_memo
from ap_testing_memo_generator import generate_ap_testing_memo
from ar_aging_memo_generator import generate_ar_aging_memo
from bank_reconciliation_memo_generator import generate_bank_rec_memo
from currency_memo_generator import generate_currency_conversion_memo
from expense_category_memo import generate_expense_category_memo
from fixed_asset_testing_memo_generator import generate_fixed_asset_testing_memo
from flux_expectations_memo import generate_flux_expectations_memo
from inventory_testing_memo_generator import generate_inventory_testing_memo
from je_testing_memo_generator import generate_je_testing_memo
from multi_period_memo_generator import generate_multi_period_memo
from payroll_testing_memo_generator import generate_payroll_testing_memo
from population_profile_memo import generate_population_profile_memo
from preflight_memo_generator import generate_preflight_memo
from revenue_testing_memo_generator import generate_revenue_testing_memo
from sampling_memo_generator import generate_sampling_design_memo, generate_sampling_evaluation_memo
from shared.error_messages import sanitize_error
from shared.export_helpers import streaming_pdf_response
from shared.export_schemas import (
    AccrualCompletenessMemoInput,
    APTestingExportInput,
    ARAgingExportInput,
    BankRecMemoInput,
    CurrencyConversionMemoInput,
    ExpenseCategoryMemoInput,
    FixedAssetExportInput,
    FluxExpectationsMemoInput,
    InventoryExportInput,
    JETestingExportInput,
    MultiPeriodMemoInput,
    PayrollTestingExportInput,
    PopulationProfileMemoInput,
    PreFlightMemoInput,
    RevenueTestingExportInput,
    SamplingDesignMemoInput,
    SamplingEvaluationMemoInput,
    ThreeWayMatchExportInput,
)
from shared.helpers import safe_download_filename
from shared.rate_limits import RATE_LIMIT_EXPORT, limiter
from three_way_match_memo_generator import generate_three_way_match_memo

router = APIRouter(tags=["export"])


# --- JE Testing Memo PDF ---


@router.post("/export/je-testing-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_je_testing_memo(
    request: Request,
    je_input: JETestingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=je_input.source_document_title,
            source_context_note=je_input.source_context_note,
            include_signoff=je_input.include_signoff,
        )

        download_filename = safe_download_filename(je_input.filename, "JETesting_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("JE Testing memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "je_memo_export_error"))


# --- AP Testing Memo PDF ---


@router.post("/export/ap-testing-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_ap_testing_memo(
    request: Request,
    ap_input: APTestingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=ap_input.source_document_title,
            source_context_note=ap_input.source_context_note,
            include_signoff=ap_input.include_signoff,
        )

        download_filename = safe_download_filename(ap_input.filename, "APTesting_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("AP Testing memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "ap_memo_export_error"))


# --- Payroll Testing Memo ---


@router.post("/export/payroll-testing-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_payroll_testing_memo(
    request: Request,
    payroll_input: PayrollTestingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=payroll_input.source_document_title,
            source_context_note=payroll_input.source_context_note,
            include_signoff=payroll_input.include_signoff,
        )

        download_filename = safe_download_filename(payroll_input.filename, "PayrollTesting_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Payroll Testing memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "payroll_memo_export_error"))


# --- Three-Way Match Memo PDF ---


@router.post("/export/three-way-match-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_three_way_match_memo(
    request: Request,
    twm_input: ThreeWayMatchExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=twm_input.source_document_title,
            source_context_note=twm_input.source_context_note,
            include_signoff=twm_input.include_signoff,
        )

        download_filename = safe_download_filename(twm_input.filename, "TWM_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("TWM memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "twm_memo_export_error"))


# --- Revenue Testing Memo PDF ---


@router.post("/export/revenue-testing-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_revenue_testing_memo(
    request: Request,
    revenue_input: RevenueTestingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=revenue_input.source_document_title,
            source_context_note=revenue_input.source_context_note,
            include_signoff=revenue_input.include_signoff,
        )

        download_filename = safe_download_filename(revenue_input.filename, "RevenueTesting_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Revenue Testing memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "revenue_memo_export_error"))


# --- AR Aging Memo PDF ---


@router.post("/export/ar-aging-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_ar_aging_memo(
    request: Request,
    ar_input: ARAgingExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=ar_input.source_document_title,
            source_context_note=ar_input.source_context_note,
            include_signoff=ar_input.include_signoff,
        )

        download_filename = safe_download_filename(ar_input.filename, "ARAging_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("AR Aging memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "ar_aging_memo_export_error"))


# --- Fixed Asset Testing Memo PDF ---


@router.post("/export/fixed-asset-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_fixed_asset_memo(
    request: Request,
    fa_input: FixedAssetExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=fa_input.source_document_title,
            source_context_note=fa_input.source_context_note,
            include_signoff=fa_input.include_signoff,
        )

        download_filename = safe_download_filename(fa_input.filename, "FixedAsset_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Fixed Asset memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "fa_memo_export_error"))


# --- Inventory Testing Memo PDF ---


@router.post("/export/inventory-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_inventory_memo(
    request: Request,
    inv_input: InventoryExportInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=inv_input.source_document_title,
            source_context_note=inv_input.source_context_note,
            include_signoff=inv_input.include_signoff,
        )

        download_filename = safe_download_filename(inv_input.filename, "Inventory_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Inventory memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "inv_memo_export_error"))


# --- Bank Reconciliation Memo PDF ---


@router.post("/export/bank-rec-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_bank_rec_memo(
    request: Request,
    rec_input: BankRecMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=rec_input.source_document_title,
            source_context_note=rec_input.source_context_note,
            include_signoff=rec_input.include_signoff,
        )

        download_filename = safe_download_filename(rec_input.filename, "BankRec_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Bank Rec memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "bank_rec_memo_export_error"))


# --- Multi-Period Comparison Memo PDF ---


@router.post("/export/multi-period-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_multi_period_memo(
    request: Request,
    mp_input: MultiPeriodMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
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
            source_document_title=mp_input.source_document_title,
            source_context_note=mp_input.source_context_note,
            include_signoff=mp_input.include_signoff,
        )

        download_filename = safe_download_filename(mp_input.filename, "MultiPeriod_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Multi-Period memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "multi_period_memo_export_error"))


# --- Currency Conversion Memo PDF ---


@router.post("/export/currency-conversion-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_currency_conversion_memo(
    request: Request,
    cc_input: CurrencyConversionMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Generate and download a Currency Conversion Memo PDF."""
    try:
        result_dict = cc_input.model_dump()
        pdf_bytes = generate_currency_conversion_memo(
            conversion_result=result_dict,
            filename=cc_input.filename,
            client_name=cc_input.client_name,
            period_tested=cc_input.period_tested,
            prepared_by=cc_input.prepared_by,
            reviewed_by=cc_input.reviewed_by,
            workpaper_date=cc_input.workpaper_date,
            source_document_title=cc_input.source_document_title,
            source_context_note=cc_input.source_context_note,
            include_signoff=cc_input.include_signoff,
        )

        download_filename = safe_download_filename(cc_input.filename, "Currency_Conversion_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Currency conversion memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "currency_memo_export_error"))


# --- Sampling Design Memo PDF ---


@router.post("/export/sampling-design-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_sampling_design_memo(
    request: Request,
    design_input: SamplingDesignMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Generate and download a Sampling Design Memo PDF."""
    try:
        result_dict = design_input.model_dump()
        pdf_bytes = generate_sampling_design_memo(
            design_result=result_dict,
            filename=design_input.filename,
            client_name=design_input.client_name,
            period_tested=design_input.period_tested,
            prepared_by=design_input.prepared_by,
            reviewed_by=design_input.reviewed_by,
            workpaper_date=design_input.workpaper_date,
            source_document_title=design_input.source_document_title,
            source_context_note=design_input.source_context_note,
            include_signoff=design_input.include_signoff,
        )

        download_filename = safe_download_filename(design_input.filename, "Sampling_Design_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Sampling design memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "sampling_design_memo_error"))


# --- Sampling Evaluation Memo PDF ---


@router.post("/export/sampling-evaluation-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_sampling_evaluation_memo(
    request: Request,
    eval_input: SamplingEvaluationMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Generate and download a Sampling Evaluation Memo PDF."""
    try:
        result_dict = eval_input.model_dump()
        design_ctx = result_dict.pop("design_result", None)
        pdf_bytes = generate_sampling_evaluation_memo(
            evaluation_result=result_dict,
            design_result=design_ctx,
            filename=eval_input.filename,
            client_name=eval_input.client_name,
            period_tested=eval_input.period_tested,
            prepared_by=eval_input.prepared_by,
            reviewed_by=eval_input.reviewed_by,
            workpaper_date=eval_input.workpaper_date,
            source_document_title=eval_input.source_document_title,
            source_context_note=eval_input.source_context_note,
            include_signoff=eval_input.include_signoff,
        )

        download_filename = safe_download_filename(eval_input.filename, "Sampling_Evaluation_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Sampling evaluation memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "sampling_eval_memo_error"))


# --- Pre-Flight Report Memo PDF (Sprint 283) ---


@router.post("/export/preflight-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_preflight_memo(
    request: Request,
    pf_input: PreFlightMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Generate and download a Pre-Flight Report Memo PDF."""
    try:
        result_dict = pf_input.model_dump()
        pdf_bytes = generate_preflight_memo(
            preflight_result=result_dict,
            filename=pf_input.filename,
            client_name=pf_input.client_name,
            period_tested=pf_input.period_tested,
            prepared_by=pf_input.prepared_by,
            reviewed_by=pf_input.reviewed_by,
            workpaper_date=pf_input.workpaper_date,
            source_document_title=pf_input.source_document_title,
            source_context_note=pf_input.source_context_note,
            include_signoff=pf_input.include_signoff,
        )

        download_filename = safe_download_filename(pf_input.filename, "PreFlight_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Pre-flight memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "preflight_memo_export_error"))


# --- Population Profile Memo PDF (Sprint 287) ---


@router.post("/export/population-profile-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_population_profile_memo(
    request: Request,
    pp_input: PopulationProfileMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Generate and download a Population Profile Memo PDF."""
    try:
        result_dict = pp_input.model_dump()
        pdf_bytes = generate_population_profile_memo(
            profile_result=result_dict,
            filename=pp_input.filename,
            client_name=pp_input.client_name,
            period_tested=pp_input.period_tested,
            prepared_by=pp_input.prepared_by,
            reviewed_by=pp_input.reviewed_by,
            workpaper_date=pp_input.workpaper_date,
            source_document_title=pp_input.source_document_title,
            source_context_note=pp_input.source_context_note,
            include_signoff=pp_input.include_signoff,
        )

        download_filename = safe_download_filename(pp_input.filename, "PopProfile_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Population profile memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "population_profile_memo_error"))


# --- Expense Category Memo PDF (Sprint 289) ---


@router.post("/export/expense-category-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_expense_category_memo(
    request: Request,
    ec_input: ExpenseCategoryMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Generate and download an Expense Category Analytical Procedures Memo PDF."""
    try:
        result_dict = ec_input.model_dump()
        pdf_bytes = generate_expense_category_memo(
            report_result=result_dict,
            filename=ec_input.filename,
            client_name=ec_input.client_name,
            period_tested=ec_input.period_tested,
            prepared_by=ec_input.prepared_by,
            reviewed_by=ec_input.reviewed_by,
            workpaper_date=ec_input.workpaper_date,
            source_document_title=ec_input.source_document_title,
            source_context_note=ec_input.source_context_note,
            include_signoff=ec_input.include_signoff,
        )

        download_filename = safe_download_filename(ec_input.filename, "ExpenseCategory_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Expense category memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "expense_category_memo_error"))


# --- Accrual Completeness Memo PDF (Sprint 290) ---


@router.post("/export/accrual-completeness-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_accrual_completeness_memo(
    request: Request,
    ac_input: AccrualCompletenessMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Generate and download an Accrual Completeness Estimator Memo PDF."""
    try:
        result_dict = ac_input.model_dump()
        pdf_bytes = generate_accrual_completeness_memo(
            report_result=result_dict,
            filename=ac_input.filename,
            client_name=ac_input.client_name,
            period_tested=ac_input.period_tested,
            prepared_by=ac_input.prepared_by,
            reviewed_by=ac_input.reviewed_by,
            workpaper_date=ac_input.workpaper_date,
            source_document_title=ac_input.source_document_title,
            source_context_note=ac_input.source_context_note,
            include_signoff=ac_input.include_signoff,
        )

        download_filename = safe_download_filename(ac_input.filename, "AccrualCompleteness_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Accrual completeness memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "accrual_completeness_memo_error"))


# --- Flux Expectations Memo PDF (Sprint 297) ---


@router.post("/export/flux-expectations-memo")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_flux_expectations_memo(
    request: Request,
    payload: FluxExpectationsMemoInput,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """Generate and download ISA 520 Flux Expectations Memo PDF."""
    try:
        flux_dict = payload.flux.model_dump()
        expectations_dict = {k: v.model_dump() for k, v in payload.expectations.items()}
        pdf_bytes = generate_flux_expectations_memo(
            flux_result=flux_dict,
            expectations=expectations_dict,
            filename=payload.filename,
            client_name=payload.client_name,
            period_tested=payload.period_tested,
            prepared_by=payload.prepared_by,
            reviewed_by=payload.reviewed_by,
            workpaper_date=payload.workpaper_date,
            source_document_title=payload.source_document_title,
            source_context_note=payload.source_context_note,
            include_signoff=payload.include_signoff,
        )

        download_filename = safe_download_filename(payload.filename, "FluxExpectations_Memo", "pdf")
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Flux expectations memo export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "flux_expectations_memo_error"))
