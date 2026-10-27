"""
Diagnostic export pipeline — single entry point for all diagnostic export operations.

Each public function in this module orchestrates the full export flow:
validate input -> serialize to bytes -> build streaming response. Route handlers
call these directly and return the result, making each route a one-liner.
The pipeline owns all try/except handling via transport.handle_export_error.

Sprint 819 item 8: the eleven functions were near-identical copies of one
sequence; that sequence is ``_run_export``. Each public function now states only
what differs — the serializer, the download-name parts, the exceptions it maps
to a sanitized 500, and its audit-log events (event names and messages are
unchanged; the CSV exports other than TB/anomalies log nothing, as before).
"""

import logging
from collections.abc import Callable
from typing import Optional

from fastapi.responses import StreamingResponse

from export.serializers.csv import (
    serialize_accrual_completeness_csv,
    serialize_anomalies_csv,
    serialize_expense_category_csv,
    serialize_population_profile_csv,
    serialize_preflight_issues_csv,
    serialize_trial_balance_csv,
)
from export.serializers.excel import (
    serialize_audit_excel,
    serialize_financial_statements_excel,
    serialize_leadsheets_excel,
)
from export.serializers.pdf import serialize_audit_pdf, serialize_financial_statements_pdf
from export.transport import build_streaming_response, handle_export_error
from export.validators import validate_financial_statements_input
from financial_statement_builder import FinancialStatementBuilder
from security_utils import log_secure_operation
from shared.export_schemas import (
    AccrualCompletenessCSVInput,
    ExpenseCategoryCSVInput,
    FinancialStatementsInput,
    LeadSheetInput,
    PopulationProfileCSVInput,
    PreFlightCSVInput,
)
from shared.pdf_branding import PDFBrandingContext, apply_pdf_branding
from shared.schemas import AuditResultInput

logger = logging.getLogger(__name__)

# Exceptions each export maps to a sanitized 500. Binary (PDF/Excel) exports can
# hit file-system errors; CSV exports can hit encoding errors instead.
_BINARY_ERRORS: tuple[type[Exception], ...] = (ValueError, KeyError, TypeError, OSError)
_CSV_ERRORS: tuple[type[Exception], ...] = (ValueError, KeyError, TypeError, UnicodeEncodeError)


def _run_export(
    serialize: Callable[[], bytes],
    *,
    source_filename: str,
    filename_suffix: str,
    fmt: str,
    errors: tuple[type[Exception], ...],
    log_prefix: str,
    error_code: str,
    start_event: Optional[tuple[str, str]] = None,
    complete_event: Optional[tuple[str, Callable[[int], str]]] = None,
) -> StreamingResponse:
    """Serialize -> streaming response, with the shared logging and error mapping.

    ``start_event`` is logged before serializing; ``complete_event`` (name,
    message-from-byte-count) after the response is built. An exception in
    ``errors`` raised while serializing or building becomes a sanitized 500 via
    ``handle_export_error``; anything else propagates.
    """
    if start_event is not None:
        log_secure_operation(*start_event)
    try:
        file_bytes = serialize()
        response = build_streaming_response(
            file_bytes,
            source_filename=source_filename,
            filename_suffix=filename_suffix,
            fmt=fmt,
        )
        if complete_event is not None:
            event, message = complete_event
            log_secure_operation(event, message(len(file_bytes)))
        return response
    except errors as e:
        handle_export_error(e, log_prefix=log_prefix, error_code=error_code)


def _branded(serialize: Callable[[], bytes], branding: Optional[PDFBrandingContext]) -> Callable[[], bytes]:
    """Scope ``apply_pdf_branding`` around a PDF serializer call (Sprint 748b)."""

    def _run() -> bytes:
        with apply_pdf_branding(branding):
            return serialize()

    return _run


def export_diagnostic_pdf(
    audit_result: AuditResultInput,
    *,
    branding: Optional[PDFBrandingContext] = None,
) -> StreamingResponse:
    """Full pipeline: audit result -> PDF bytes -> streaming response.

    Sprint 748b: optional ``branding`` parameter scopes
    ``apply_pdf_branding`` around the serializer call so Enterprise
    custom logos / headers / footers flow through the ContextVar to
    the underlying ``generate_audit_report`` template. Routes resolve
    ``branding`` via ``load_pdf_branding_context(user, db)`` and pass
    it through.
    """
    return _run_export(
        _branded(lambda: serialize_audit_pdf(audit_result), branding),
        source_filename=audit_result.filename or "TrialBalance",
        filename_suffix="Diagnostic",
        fmt="pdf",
        errors=_BINARY_ERRORS,
        log_prefix="PDF export",
        error_code="pdf_export_error",
        start_event=("pdf_export_start", f"Generating PDF report for: {audit_result.filename}"),
        complete_event=("pdf_export_complete", lambda n: f"PDF generated: {n} bytes"),
    )


def export_diagnostic_excel(audit_result: AuditResultInput) -> StreamingResponse:
    """Full pipeline: audit result -> Excel bytes -> streaming response.

    Excel exports don't apply PDF branding (logo / header / footer live
    in PDF chrome only) — no ``branding`` parameter is needed.
    """
    return _run_export(
        lambda: serialize_audit_excel(audit_result),
        source_filename=audit_result.filename or "TrialBalance",
        filename_suffix="Workpaper",
        fmt="xlsx",
        errors=_BINARY_ERRORS,
        log_prefix="Excel export",
        error_code="excel_export_error",
        start_event=("excel_export_start", f"Generating Excel workpaper for: {audit_result.filename}"),
        complete_event=("excel_export_complete", lambda n: f"Excel generated: {n} bytes"),
    )


def export_csv_trial_balance(audit_result: AuditResultInput) -> StreamingResponse:
    """Full pipeline: audit result -> trial balance CSV bytes -> streaming response."""
    return _run_export(
        lambda: serialize_trial_balance_csv(audit_result),
        source_filename=audit_result.filename or "TrialBalance",
        filename_suffix="TB",
        fmt="csv",
        errors=_CSV_ERRORS,
        log_prefix="CSV trial balance export",
        error_code="csv_tb_export_error",
        start_event=("csv_tb_export_start", f"Generating CSV trial balance for: {audit_result.filename}"),
        complete_event=("csv_tb_export_complete", lambda n: f"CSV TB generated: {n} bytes"),
    )


def export_csv_anomalies(audit_result: AuditResultInput) -> StreamingResponse:
    """Full pipeline: audit result -> anomalies CSV bytes -> streaming response."""
    return _run_export(
        lambda: serialize_anomalies_csv(audit_result),
        source_filename=audit_result.filename or "TrialBalance",
        filename_suffix="Anomalies",
        fmt="csv",
        errors=_CSV_ERRORS,
        log_prefix="CSV anomaly export",
        error_code="csv_anomaly_export_error",
        start_event=("csv_anomaly_export_start", f"Generating CSV anomalies for: {audit_result.filename}"),
        complete_event=("csv_anomaly_export_complete", lambda n: f"CSV anomalies generated: {n} bytes"),
    )


def export_leadsheets(payload: LeadSheetInput) -> StreamingResponse:
    """Full pipeline: lead sheet input -> Excel bytes -> streaming response."""
    return _run_export(
        lambda: serialize_leadsheets_excel(payload),
        source_filename=payload.filename,
        filename_suffix="LeadSheets",
        fmt="xlsx",
        errors=_BINARY_ERRORS,
        log_prefix="Lead sheet export",
        error_code="leadsheet_error",
        start_event=("leadsheet_export", f"Exporting lead sheets for {len(payload.flux.items)} items"),
        complete_event=("leadsheet_generated", lambda n: f"Generated {n} bytes"),
    )


def export_financial_statements(
    payload: FinancialStatementsInput,
    fmt: str = "pdf",
    *,
    branding: Optional[PDFBrandingContext] = None,
) -> StreamingResponse:
    """Full pipeline: financial statements input -> PDF or Excel bytes -> streaming response.

    Args:
        payload: Validated FinancialStatementsInput with lead_sheet_grouping.
        fmt: Output format — "pdf" (default) or "excel".
        branding: Optional Enterprise branding context, applied via
            ``apply_pdf_branding`` for the PDF path. Excel ignores it.
            Sprint 748b extension.
    """
    log_secure_operation(
        "financial_statements_export_start", f"Generating {fmt} financial statements for: {payload.filename}"
    )
    # Outside the mapped-exception scope: validation raises its own 4xx.
    validate_financial_statements_input(payload)

    def _serialize() -> bytes:
        builder = FinancialStatementBuilder(
            payload.lead_sheet_grouping,
            entity_name=payload.entity_name or "",
            period_end=payload.period_end or "",
            prior_lead_sheet_grouping=payload.prior_lead_sheet_grouping,
        )
        statements = builder.build()
        if fmt == "excel":
            return serialize_financial_statements_excel(payload, statements)
        with apply_pdf_branding(branding):
            return serialize_financial_statements_pdf(payload, statements)

    return _run_export(
        _serialize,
        source_filename=payload.filename or "FinancialStatements",
        filename_suffix="FinStmts",
        fmt="xlsx" if fmt == "excel" else "pdf",
        errors=_BINARY_ERRORS,
        log_prefix="Financial statements export",
        error_code="financial_statements_export_error",
        complete_event=(
            "financial_statements_export_complete",
            lambda n: f"Financial statements {fmt} generated: {n} bytes",
        ),
    )


def export_csv_preflight_issues(pf_input: PreFlightCSVInput) -> StreamingResponse:
    """Full pipeline: pre-flight issues input -> CSV bytes -> streaming response."""
    return _run_export(
        lambda: serialize_preflight_issues_csv(pf_input),
        source_filename=pf_input.filename or "PreFlight",
        filename_suffix="Issues",
        fmt="csv",
        errors=_CSV_ERRORS,
        log_prefix="Pre-flight CSV export",
        error_code="preflight_csv_export_error",
    )


def export_csv_population_profile(pp_input: PopulationProfileCSVInput) -> StreamingResponse:
    """Full pipeline: population profile input -> CSV bytes -> streaming response."""
    return _run_export(
        lambda: serialize_population_profile_csv(pp_input),
        source_filename=pp_input.filename or "PopProfile",
        filename_suffix="Profile",
        fmt="csv",
        errors=_CSV_ERRORS,
        log_prefix="Population profile CSV export",
        error_code="population_profile_csv_export_error",
    )


def export_csv_expense_category(ec_input: ExpenseCategoryCSVInput) -> StreamingResponse:
    """Full pipeline: expense category input -> CSV bytes -> streaming response."""
    return _run_export(
        lambda: serialize_expense_category_csv(ec_input),
        source_filename=ec_input.filename or "ExpenseCategory",
        filename_suffix="Analytics",
        fmt="csv",
        errors=_CSV_ERRORS,
        log_prefix="Expense category CSV export",
        error_code="expense_category_csv_export_error",
    )


def export_csv_accrual_completeness(ac_input: AccrualCompletenessCSVInput) -> StreamingResponse:
    """Full pipeline: accrual completeness input -> CSV bytes -> streaming response."""
    return _run_export(
        lambda: serialize_accrual_completeness_csv(ac_input),
        source_filename=ac_input.filename or "AccrualCompleteness",
        filename_suffix="Estimator",
        fmt="csv",
        errors=_CSV_ERRORS,
        log_prefix="Accrual completeness CSV export",
        error_code="accrual_completeness_csv_export_error",
    )
