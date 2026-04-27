"""
Paciolus API — Memo PDF Export Routes (all 18 testing/tool memo endpoints).
Sprint 155: Extracted from routes/export.py.
Sprint 539: Registry-based refactor — declarative dispatch eliminates per-route boilerplate.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from shared.entitlement_checks import check_export_access
from shared.memory_budget import track_memo_memory
from shared.pdf_branding import apply_pdf_branding, load_pdf_branding_context

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
from shared.filenames import safe_download_filename
from shared.rate_limits import RATE_LIMIT_EXPORT, limiter
from three_way_match_memo_generator import generate_three_way_match_memo

router = APIRouter(tags=["export"])


# ---------------------------------------------------------------------------
# Registry infrastructure
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MemoRegistryEntry:
    """Declarative descriptor for a standard memo export endpoint."""

    route_path: str
    generator: Callable[..., bytes]
    result_kwarg: str
    filename_template: str
    log_label: str
    error_code: str
    docstring: str


# Custom pre-processing hooks for non-standard memo types.  Each receives the
# Pydantic input model and returns (result_dict, extra_kwargs) where
# extra_kwargs are merged into the generator call alongside the common
# workpaper fields.
CustomPreprocessor = Callable[[BaseModel], tuple[dict[str, Any], dict[str, Any]]]


def _standard_preprocessor(payload: BaseModel) -> tuple[dict[str, Any], dict[str, Any]]:
    """Default: model_dump() the entire payload; no extra kwargs."""
    return payload.model_dump(), {}


def _sampling_evaluation_preprocessor(payload: BaseModel) -> tuple[dict[str, Any], dict[str, Any]]:
    """Sampling evaluation pops design_result from the dump for a separate kwarg."""
    result_dict = payload.model_dump()
    design_ctx = result_dict.pop("design_result", None)
    return result_dict, {"design_result": design_ctx}


def _flux_expectations_preprocessor(payload: BaseModel) -> tuple[dict[str, Any], dict[str, Any]]:
    """Flux expectations has nested sub-model serialization."""
    # payload.flux and payload.expectations are typed sub-models
    flux_dict = payload.flux.model_dump()  # type: ignore[attr-defined]
    expectations_dict = {
        k: v.model_dump()
        for k, v in payload.expectations.items()  # type: ignore[attr-defined]
    }
    return flux_dict, {"expectations": expectations_dict}


# ---------------------------------------------------------------------------
# Shared handler
# ---------------------------------------------------------------------------


def _memo_export_handler(
    entry: MemoRegistryEntry,
    payload: BaseModel,
    preprocessor: CustomPreprocessor = _standard_preprocessor,
    current_user: User | None = None,
    db: Session | None = None,
) -> StreamingResponse:
    """Deserialize -> generate -> stream -> exception handling for any memo type.

    Sprint 679: ``current_user`` + ``db`` propagate the Enterprise PDF
    branding context via ContextVar. When present, the memo template
    picks up the user's firm logo / header / footer automatically — no
    signature changes needed on the 18 downstream memo generators.
    """
    try:
        result_dict, extra_kwargs = preprocessor(payload)

        # Common workpaper fields present on every input model
        common_kwargs = {
            "filename": payload.filename,  # type: ignore[attr-defined]
            "client_name": payload.client_name,  # type: ignore[attr-defined]
            "period_tested": payload.period_tested,  # type: ignore[attr-defined]
            "prepared_by": payload.prepared_by,  # type: ignore[attr-defined]
            "reviewed_by": payload.reviewed_by,  # type: ignore[attr-defined]
            "workpaper_date": payload.workpaper_date,  # type: ignore[attr-defined]
            "source_document_title": payload.source_document_title,  # type: ignore[attr-defined]
            "source_context_note": payload.source_context_note,  # type: ignore[attr-defined]
            "fiscal_year_end": payload.fiscal_year_end,  # type: ignore[attr-defined]
            "include_signoff": payload.include_signoff,  # type: ignore[attr-defined]
        }

        # Sprint 679: resolve branding for the caller and scope it to the
        # PDF-generation call via ContextVar. Falls back to blank
        # (Paciolus default) when user/db aren't supplied or the tier
        # doesn't include custom branding.
        branding = None
        if current_user is not None and db is not None:
            branding = load_pdf_branding_context(current_user, db)

        with apply_pdf_branding(branding), track_memo_memory(entry.log_label):
            pdf_bytes: bytes = entry.generator(
                **{entry.result_kwarg: result_dict},
                **common_kwargs,
                **extra_kwargs,
            )

        download_filename = safe_download_filename(
            payload.filename,  # type: ignore[attr-defined]
            entry.filename_template,
            "pdf",
        )
        return streaming_pdf_response(pdf_bytes, download_filename)
    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("%s export failed", entry.log_label)
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", entry.error_code),
        )


# ---------------------------------------------------------------------------
# Standard memo registry — 15 endpoints with identical structure
# ---------------------------------------------------------------------------

_STANDARD_REGISTRY: list[tuple[MemoRegistryEntry, type[BaseModel]]] = [
    (
        MemoRegistryEntry(
            route_path="/export/je-testing-memo",
            generator=generate_je_testing_memo,
            result_kwarg="je_result",
            filename_template="JETesting_Memo",
            log_label="JE Testing memo",
            error_code="je_memo_export_error",
            docstring="Generate and download a JE Testing Memo PDF.",
        ),
        JETestingExportInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/ap-testing-memo",
            generator=generate_ap_testing_memo,
            result_kwarg="ap_result",
            filename_template="APTesting_Memo",
            log_label="AP Testing memo",
            error_code="ap_memo_export_error",
            docstring="Generate and download an AP Testing Memo PDF.",
        ),
        APTestingExportInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/payroll-testing-memo",
            generator=generate_payroll_testing_memo,
            result_kwarg="payroll_result",
            filename_template="PayrollTesting_Memo",
            log_label="Payroll Testing memo",
            error_code="payroll_memo_export_error",
            docstring="Generate and download a Payroll Testing Memo PDF.",
        ),
        PayrollTestingExportInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/three-way-match-memo",
            generator=generate_three_way_match_memo,
            result_kwarg="twm_result",
            filename_template="TWM_Memo",
            log_label="TWM memo",
            error_code="twm_memo_export_error",
            docstring="Generate and download a Three-Way Match Memo PDF.",
        ),
        ThreeWayMatchExportInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/revenue-testing-memo",
            generator=generate_revenue_testing_memo,
            result_kwarg="revenue_result",
            filename_template="RevenueTesting_Memo",
            log_label="Revenue Testing memo",
            error_code="revenue_memo_export_error",
            docstring="Generate and download a Revenue Testing Memo PDF.",
        ),
        RevenueTestingExportInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/ar-aging-memo",
            generator=generate_ar_aging_memo,
            result_kwarg="ar_result",
            filename_template="ARAging_Memo",
            log_label="AR Aging memo",
            error_code="ar_aging_memo_export_error",
            docstring="Generate and download an AR Aging Analysis Memo PDF.",
        ),
        ARAgingExportInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/fixed-asset-memo",
            generator=generate_fixed_asset_testing_memo,
            result_kwarg="fa_result",
            filename_template="FixedAsset_Memo",
            log_label="Fixed Asset memo",
            error_code="fa_memo_export_error",
            docstring="Generate and download a Fixed Asset Testing Memo PDF.",
        ),
        FixedAssetExportInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/inventory-memo",
            generator=generate_inventory_testing_memo,
            result_kwarg="inv_result",
            filename_template="Inventory_Memo",
            log_label="Inventory memo",
            error_code="inv_memo_export_error",
            docstring="Generate and download an Inventory Testing Memo PDF.",
        ),
        InventoryExportInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/bank-rec-memo",
            generator=generate_bank_rec_memo,
            result_kwarg="rec_result",
            filename_template="BankRec_Memo",
            log_label="Bank Rec memo",
            error_code="bank_rec_memo_export_error",
            docstring="Generate and download a Bank Reconciliation Memo PDF.",
        ),
        BankRecMemoInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/multi-period-memo",
            generator=generate_multi_period_memo,
            result_kwarg="comparison_result",
            filename_template="MultiPeriod_Memo",
            log_label="Multi-Period memo",
            error_code="multi_period_memo_export_error",
            docstring="Generate and download a Multi-Period Comparison Memo PDF.",
        ),
        MultiPeriodMemoInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/currency-conversion-memo",
            generator=generate_currency_conversion_memo,
            result_kwarg="conversion_result",
            filename_template="Currency_Conversion_Memo",
            log_label="Currency conversion memo",
            error_code="currency_memo_export_error",
            docstring="Generate and download a Currency Conversion Memo PDF.",
        ),
        CurrencyConversionMemoInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/sampling-design-memo",
            generator=generate_sampling_design_memo,
            result_kwarg="design_result",
            filename_template="Sampling_Design_Memo",
            log_label="Sampling design memo",
            error_code="sampling_design_memo_error",
            docstring="Generate and download a Sampling Design Memo PDF.",
        ),
        SamplingDesignMemoInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/preflight-memo",
            generator=generate_preflight_memo,
            result_kwarg="preflight_result",
            filename_template="PreFlight_Memo",
            log_label="Pre-flight memo",
            error_code="preflight_memo_export_error",
            docstring="Generate and download a Pre-Flight Report Memo PDF.",
        ),
        PreFlightMemoInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/population-profile-memo",
            generator=generate_population_profile_memo,
            result_kwarg="profile_result",
            filename_template="PopProfile_Memo",
            log_label="Population profile memo",
            error_code="population_profile_memo_error",
            docstring="Generate and download a Population Profile Memo PDF.",
        ),
        PopulationProfileMemoInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/expense-category-memo",
            generator=generate_expense_category_memo,
            result_kwarg="report_result",
            filename_template="ExpenseCategory_Memo",
            log_label="Expense category memo",
            error_code="expense_category_memo_error",
            docstring="Generate and download an Expense Category Analytical Procedures Memo PDF.",
        ),
        ExpenseCategoryMemoInput,
    ),
    (
        MemoRegistryEntry(
            route_path="/export/accrual-completeness-memo",
            generator=generate_accrual_completeness_memo,
            result_kwarg="report_result",
            filename_template="AccrualCompleteness_Memo",
            log_label="Accrual completeness memo",
            error_code="accrual_completeness_memo_error",
            docstring="Generate and download an Accrual Completeness Estimator Memo PDF.",
        ),
        AccrualCompletenessMemoInput,
    ),
]


def _register_standard_routes() -> None:
    """Programmatically register all standard memo export routes.

    Each route gets its own closure so that FastAPI can inspect the correct
    Pydantic model for request-body validation via the type annotation on
    the ``payload`` parameter.
    """
    for entry, schema_cls in _STANDARD_REGISTRY:

        def _make_handler(
            _entry: MemoRegistryEntry = entry,
            _schema: type[BaseModel] = schema_cls,
        ) -> Callable[..., StreamingResponse]:
            """Factory that captures registry entry per-closure."""

            # We need the concrete schema type in the signature for FastAPI's
            # dependency-injection / OpenAPI generation.  Build a thin wrapper
            # whose annotation FastAPI will introspect.
            def _handler(
                request: Request,
                payload: _schema,  # type: ignore[valid-type]
                current_user: User = Depends(require_verified_user),
                db: Session = Depends(get_db),
            ) -> StreamingResponse:
                # Sprint 679: thread user + db for PDF branding.
                return _memo_export_handler(_entry, payload, current_user=current_user, db=db)

            _handler.__doc__ = _entry.docstring
            _handler.__name__ = f"export_{_entry.route_path.split('/')[-1].replace('-', '_')}"
            return _handler

        handler = _make_handler()
        decorated = limiter.limit(RATE_LIMIT_EXPORT)(handler)
        # Sprint 678: tier-gate every memo export behind check_export_access.
        # Free tier has no pdf/excel/csv export; helper raises 403 in hard mode.
        router.post(entry.route_path, dependencies=[Depends(check_export_access)])(decorated)


_register_standard_routes()


# ---------------------------------------------------------------------------
# Non-standard memo routes (custom preprocessing)
# ---------------------------------------------------------------------------

# --- Sampling Evaluation Memo PDF ---
# Requires popping design_result from the dump before passing to the generator.

_SAMPLING_EVAL_ENTRY = MemoRegistryEntry(
    route_path="/export/sampling-evaluation-memo",
    generator=generate_sampling_evaluation_memo,
    result_kwarg="evaluation_result",
    filename_template="Sampling_Evaluation_Memo",
    log_label="Sampling evaluation memo",
    error_code="sampling_eval_memo_error",
    docstring="Generate and download a Sampling Evaluation Memo PDF.",
)


@router.post(_SAMPLING_EVAL_ENTRY.route_path, dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_sampling_evaluation_memo(
    request: Request,
    eval_input: SamplingEvaluationMemoInput,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate and download a Sampling Evaluation Memo PDF."""
    return _memo_export_handler(
        _SAMPLING_EVAL_ENTRY,
        eval_input,
        preprocessor=_sampling_evaluation_preprocessor,
        current_user=current_user,
        db=db,
    )


# --- Flux Expectations Memo PDF (Sprint 297) ---
# Requires nested sub-model serialization (flux + expectations dict).

_FLUX_ENTRY = MemoRegistryEntry(
    route_path="/export/flux-expectations-memo",
    generator=generate_flux_expectations_memo,
    result_kwarg="flux_result",
    filename_template="FluxExpectations_Memo",
    log_label="Flux expectations memo",
    error_code="flux_expectations_memo_error",
    docstring="Generate and download ISA 520 Flux Expectations Memo PDF.",
)


@router.post(_FLUX_ENTRY.route_path, dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_flux_expectations_memo(
    request: Request,
    payload: FluxExpectationsMemoInput,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate and download ISA 520 Flux Expectations Memo PDF."""
    return _memo_export_handler(
        _FLUX_ENTRY,
        payload,
        preprocessor=_flux_expectations_preprocessor,
        current_user=current_user,
        db=db,
    )
