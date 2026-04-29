"""
Diagnostic export pipeline — single entry point for all diagnostic export operations.

Each public function in this module orchestrates the full export flow:
validate input -> serialize to bytes -> build streaming response. Route handlers
call these directly and return the result, making each route a one-liner.
The pipeline owns all try/except handling via transport.handle_export_error.
"""

import logging
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
    log_secure_operation("pdf_export_start", f"Generating PDF report for: {audit_result.filename}")
    try:
        with apply_pdf_branding(branding):
            pdf_bytes = serialize_audit_pdf(audit_result)
        response = build_streaming_response(
            pdf_bytes,
            source_filename=audit_result.filename or "TrialBalance",
            filename_suffix="Diagnostic",
            fmt="pdf",
        )
        log_secure_operation("pdf_export_complete", f"PDF generated: {len(pdf_bytes)} bytes")
        return response
    except (ValueError, KeyError, TypeError, OSError) as e:
        handle_export_error(e, log_prefix="PDF export", error_code="pdf_export_error")


def export_diagnostic_excel(audit_result: AuditResultInput) -> StreamingResponse:
    """Full pipeline: audit result -> Excel bytes -> streaming response.

    Excel exports don't apply PDF branding (logo / header / footer live
    in PDF chrome only) — no ``branding`` parameter is needed.
    """
    log_secure_operation("excel_export_start", f"Generating Excel workpaper for: {audit_result.filename}")
    try:
        excel_bytes = serialize_audit_excel(audit_result)
        response = build_streaming_response(
            excel_bytes,
            source_filename=audit_result.filename or "TrialBalance",
            filename_suffix="Workpaper",
            fmt="xlsx",
        )
        log_secure_operation("excel_export_complete", f"Excel generated: {len(excel_bytes)} bytes")
        return response
    except (ValueError, KeyError, TypeError, OSError) as e:
        handle_export_error(e, log_prefix="Excel export", error_code="excel_export_error")


def export_csv_trial_balance(audit_result: AuditResultInput) -> StreamingResponse:
    """Full pipeline: audit result -> trial balance CSV bytes -> streaming response."""
    log_secure_operation("csv_tb_export_start", f"Generating CSV trial balance for: {audit_result.filename}")
    try:
        csv_bytes = serialize_trial_balance_csv(audit_result)
        response = build_streaming_response(
            csv_bytes,
            source_filename=audit_result.filename or "TrialBalance",
            filename_suffix="TB",
            fmt="csv",
        )
        log_secure_operation("csv_tb_export_complete", f"CSV TB generated: {len(csv_bytes)} bytes")
        return response
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        handle_export_error(e, log_prefix="CSV trial balance export", error_code="csv_tb_export_error")


def export_csv_anomalies(audit_result: AuditResultInput) -> StreamingResponse:
    """Full pipeline: audit result -> anomalies CSV bytes -> streaming response."""
    log_secure_operation("csv_anomaly_export_start", f"Generating CSV anomalies for: {audit_result.filename}")
    try:
        csv_bytes = serialize_anomalies_csv(audit_result)
        response = build_streaming_response(
            csv_bytes,
            source_filename=audit_result.filename or "TrialBalance",
            filename_suffix="Anomalies",
            fmt="csv",
        )
        log_secure_operation("csv_anomaly_export_complete", f"CSV anomalies generated: {len(csv_bytes)} bytes")
        return response
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        handle_export_error(e, log_prefix="CSV anomaly export", error_code="csv_anomaly_export_error")


def export_leadsheets(payload: LeadSheetInput) -> StreamingResponse:
    """Full pipeline: lead sheet input -> Excel bytes -> streaming response."""
    log_secure_operation("leadsheet_export", f"Exporting lead sheets for {len(payload.flux.items)} items")
    try:
        excel_bytes = serialize_leadsheets_excel(payload)
        response = build_streaming_response(
            excel_bytes,
            source_filename=payload.filename,
            filename_suffix="LeadSheets",
            fmt="xlsx",
        )
        log_secure_operation("leadsheet_generated", f"Generated {len(excel_bytes)} bytes")
        return response
    except (ValueError, KeyError, TypeError, OSError) as e:
        handle_export_error(e, log_prefix="Lead sheet export", error_code="leadsheet_error")


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
    validate_financial_statements_input(payload)

    try:
        builder = FinancialStatementBuilder(
            payload.lead_sheet_grouping,
            entity_name=payload.entity_name or "",
            period_end=payload.period_end or "",
            prior_lead_sheet_grouping=payload.prior_lead_sheet_grouping,
        )
        statements = builder.build()

        if fmt == "excel":
            file_bytes = serialize_financial_statements_excel(payload, statements)
            response = build_streaming_response(
                file_bytes,
                source_filename=payload.filename or "FinancialStatements",
                filename_suffix="FinStmts",
                fmt="xlsx",
            )
        else:
            with apply_pdf_branding(branding):
                file_bytes = serialize_financial_statements_pdf(payload, statements)
            response = build_streaming_response(
                file_bytes,
                source_filename=payload.filename or "FinancialStatements",
                filename_suffix="FinStmts",
                fmt="pdf",
            )

        log_secure_operation(
            "financial_statements_export_complete",
            f"Financial statements {fmt} generated: {len(file_bytes)} bytes",
        )
        return response
    except (ValueError, KeyError, TypeError, OSError) as e:
        handle_export_error(e, log_prefix="Financial statements export", error_code="financial_statements_export_error")


def export_csv_preflight_issues(pf_input: PreFlightCSVInput) -> StreamingResponse:
    """Full pipeline: pre-flight issues input -> CSV bytes -> streaming response."""
    try:
        csv_bytes = serialize_preflight_issues_csv(pf_input)
        return build_streaming_response(
            csv_bytes,
            source_filename=pf_input.filename or "PreFlight",
            filename_suffix="Issues",
            fmt="csv",
        )
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        handle_export_error(e, log_prefix="Pre-flight CSV export", error_code="preflight_csv_export_error")


def export_csv_population_profile(pp_input: PopulationProfileCSVInput) -> StreamingResponse:
    """Full pipeline: population profile input -> CSV bytes -> streaming response."""
    try:
        csv_bytes = serialize_population_profile_csv(pp_input)
        return build_streaming_response(
            csv_bytes,
            source_filename=pp_input.filename or "PopProfile",
            filename_suffix="Profile",
            fmt="csv",
        )
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        handle_export_error(
            e, log_prefix="Population profile CSV export", error_code="population_profile_csv_export_error"
        )


def export_csv_expense_category(ec_input: ExpenseCategoryCSVInput) -> StreamingResponse:
    """Full pipeline: expense category input -> CSV bytes -> streaming response."""
    try:
        csv_bytes = serialize_expense_category_csv(ec_input)
        return build_streaming_response(
            csv_bytes,
            source_filename=ec_input.filename or "ExpenseCategory",
            filename_suffix="Analytics",
            fmt="csv",
        )
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        handle_export_error(e, log_prefix="Expense category CSV export", error_code="expense_category_csv_export_error")


def export_csv_accrual_completeness(ac_input: AccrualCompletenessCSVInput) -> StreamingResponse:
    """Full pipeline: accrual completeness input -> CSV bytes -> streaming response."""
    try:
        csv_bytes = serialize_accrual_completeness_csv(ac_input)
        return build_streaming_response(
            csv_bytes,
            source_filename=ac_input.filename or "AccrualCompleteness",
            filename_suffix="Estimator",
            fmt="csv",
        )
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        handle_export_error(
            e, log_prefix="Accrual completeness CSV export", error_code="accrual_completeness_csv_export_error"
        )
