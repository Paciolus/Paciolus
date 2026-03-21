"""
PDF serializers for Paciolus diagnostic exports.

Converts audit result payloads into PDF byte streams by delegating to the
underlying PDF generator modules (generate_audit_report, generate_financial_statements_pdf).
Each function accepts a typed payload and returns raw PDF bytes.
"""

from pdf_generator import generate_audit_report, generate_financial_statements_pdf
from shared.export_schemas import FinancialStatementsInput
from shared.schemas import AuditResultInput


def serialize_audit_pdf(audit_result: AuditResultInput) -> bytes:
    """Render an audit diagnostic result as a PDF report.

    Returns raw PDF bytes suitable for streaming to the client.
    """
    result_dict = audit_result.model_dump()
    return generate_audit_report(
        result_dict,
        audit_result.filename,
        prepared_by=audit_result.prepared_by,
        reviewed_by=audit_result.reviewed_by,
        workpaper_date=audit_result.workpaper_date,
        include_signoff=audit_result.include_signoff,
    )


def serialize_financial_statements_pdf(payload: FinancialStatementsInput, statements: object) -> bytes:
    """Render financial statements as a PDF report.

    Args:
        payload: The validated input with workpaper metadata.
        statements: Pre-built financial statement dict from FinancialStatementBuilder.

    Returns raw PDF bytes.
    """
    return generate_financial_statements_pdf(
        statements,
        prepared_by=payload.prepared_by,
        reviewed_by=payload.reviewed_by,
        workpaper_date=payload.workpaper_date,
        include_signoff=payload.include_signoff,
    )
