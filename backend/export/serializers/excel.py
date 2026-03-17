"""
Excel serializers for Paciolus diagnostic exports.

Converts audit result payloads into Excel (.xlsx) byte streams by delegating
to the underlying Excel generator modules (generate_workpaper,
generate_financial_statements_excel, generate_leadsheets).
"""

from excel_generator import generate_financial_statements_excel, generate_workpaper
from flux_engine import FluxItem, FluxResult
from leadsheet_generator import generate_leadsheets
from recon_engine import ReconResult, ReconScore
from shared.export_schemas import FinancialStatementsInput, LeadSheetInput
from shared.helpers import try_parse_risk, try_parse_risk_band
from shared.schemas import AuditResultInput


def serialize_audit_excel(audit_result: AuditResultInput) -> bytes:
    """Render an audit diagnostic result as an Excel workpaper.

    Returns raw .xlsx bytes.
    """
    result_dict = audit_result.model_dump()
    return generate_workpaper(
        result_dict,
        audit_result.filename,
        prepared_by=audit_result.prepared_by,
        reviewed_by=audit_result.reviewed_by,
        workpaper_date=audit_result.workpaper_date,
        include_signoff=audit_result.include_signoff,
    )


def serialize_financial_statements_excel(payload: FinancialStatementsInput, statements: dict) -> bytes:
    """Render financial statements as an Excel workbook.

    Args:
        payload: The validated input with workpaper metadata.
        statements: Pre-built financial statement dict from FinancialStatementBuilder.

    Returns raw .xlsx bytes.
    """
    return generate_financial_statements_excel(
        statements,
        prepared_by=payload.prepared_by,
        reviewed_by=payload.reviewed_by,
        workpaper_date=payload.workpaper_date,
        include_signoff=payload.include_signoff,
    )


def serialize_leadsheets_excel(payload: LeadSheetInput) -> bytes:
    """Build flux/recon domain objects from the input payload and generate lead sheets.

    Returns raw .xlsx bytes.
    """
    flux_items = []
    for i in payload.flux.items:
        flux_items.append(
            FluxItem(
                account_name=i.account,
                account_type=i.type,
                current_balance=i.current,
                prior_balance=i.prior,
                delta_amount=i.delta_amount,
                delta_percent=i.delta_percent if i.delta_percent is not None else 0.0,
                is_new_account=i.is_new,
                is_removed_account=i.is_removed,
                has_sign_flip=i.sign_flip,
                risk_level=try_parse_risk(i.risk_level),
                variance_indicators=i.variance_indicators,
            )
        )

    flux_result = FluxResult(
        items=flux_items,
        total_items=payload.flux.summary.total_items,
        high_risk_count=payload.flux.summary.high_risk_count,
        medium_risk_count=payload.flux.summary.medium_risk_count,
        new_accounts_count=payload.flux.summary.new_accounts,
        removed_accounts_count=payload.flux.summary.removed_accounts,
        materiality_threshold=payload.flux.summary.threshold,
    )

    recon_scores = []
    for s in payload.recon.scores:
        recon_scores.append(
            ReconScore(
                account_name=s.account,
                risk_score=s.score,
                risk_band=try_parse_risk_band(s.band),
                factors=s.factors,
                suggested_action=s.action,
            )
        )

    recon_result = ReconResult(
        scores=recon_scores,
        high_risk_count=payload.recon.stats.high,
        medium_risk_count=payload.recon.stats.medium,
        low_risk_count=payload.recon.stats.low,
    )

    return generate_leadsheets(flux_result, recon_result, payload.filename)
