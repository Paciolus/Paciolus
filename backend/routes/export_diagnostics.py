"""
Paciolus API — Diagnostic Export Routes (PDF, Excel, CSV TB, CSV Anomalies, Lead Sheets, Financial Statements).
Sprint 155: Extracted from routes/export.py.
"""
import csv
import logging
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from security_utils import log_secure_operation

logger = logging.getLogger(__name__)
from auth import require_verified_user
from excel_generator import generate_financial_statements_excel, generate_workpaper
from financial_statement_builder import FinancialStatementBuilder
from flux_engine import FluxItem, FluxResult
from leadsheet_generator import generate_leadsheets
from models import User
from pdf_generator import generate_audit_report, generate_financial_statements_pdf
from recon_engine import ReconResult, ReconScore
from shared.error_messages import sanitize_error
from shared.export_helpers import streaming_csv_response, streaming_excel_response, streaming_pdf_response
from shared.export_schemas import (
    FinancialStatementsInput,
    LeadSheetInput,
)
from shared.helpers import safe_download_filename, sanitize_csv_value, try_parse_risk, try_parse_risk_band
from shared.rate_limits import RATE_LIMIT_EXPORT, limiter
from shared.schemas import AuditResultInput

router = APIRouter(tags=["export"])


# --- PDF Export ---

@router.post("/export/pdf")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_pdf_report(request: Request, audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)):
    """Generate and stream a PDF audit report."""
    log_secure_operation(
        "pdf_export_start",
        f"Generating PDF report for: {audit_result.filename}"
    )

    try:
        result_dict = audit_result.model_dump()

        pdf_bytes = generate_audit_report(
            result_dict,
            audit_result.filename,
            prepared_by=audit_result.prepared_by,
            reviewed_by=audit_result.reviewed_by,
            workpaper_date=audit_result.workpaper_date
        )

        download_filename = safe_download_filename(audit_result.filename or "TrialBalance", "Diagnostic", "pdf")

        log_secure_operation(
            "pdf_export_complete",
            f"PDF generated: {len(pdf_bytes)} bytes, filename: {download_filename}"
        )

        return streaming_pdf_response(pdf_bytes, download_filename)

    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("PDF export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "pdf_export_error")
        )


# --- Excel Export ---

@router.post("/export/excel")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_excel_workpaper(request: Request, audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)):
    """Generate and stream an Excel workpaper."""
    log_secure_operation(
        "excel_export_start",
        f"Generating Excel workpaper for: {audit_result.filename}"
    )

    try:
        result_dict = audit_result.model_dump()

        excel_bytes = generate_workpaper(
            result_dict,
            audit_result.filename,
            prepared_by=audit_result.prepared_by,
            reviewed_by=audit_result.reviewed_by,
            workpaper_date=audit_result.workpaper_date
        )

        download_filename = safe_download_filename(audit_result.filename or "TrialBalance", "Workpaper", "xlsx")

        log_secure_operation(
            "excel_export_complete",
            f"Excel generated: {len(excel_bytes)} bytes, filename: {download_filename}"
        )

        return streaming_excel_response(excel_bytes, download_filename)

    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Excel export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "excel_export_error")
        )


# --- CSV Trial Balance ---

@router.post("/export/csv/trial-balance")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_trial_balance(request: Request, audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)):
    """Export trial balance data as CSV."""
    log_secure_operation(
        "csv_tb_export_start",
        f"Generating CSV trial balance for: {audit_result.filename}"
    )

    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Reference", "Account", "Debit", "Credit", "Net Balance",
            "Category", "Classification Confidence"
        ])

        classification = audit_result.classification_summary or {}
        category_map = {}
        for category, accounts in classification.items():
            if isinstance(accounts, list):
                for acct in accounts:
                    if isinstance(acct, dict):
                        category_map[acct.get("account", "")] = {
                            "category": category,
                            "confidence": acct.get("confidence", 0)
                        }

        accounts_written = set()
        ref_idx = 1

        for anomaly in audit_result.abnormal_balances:
            if isinstance(anomaly, dict):
                account = anomaly.get("account", "Unknown")
                if account not in accounts_written:
                    debit = anomaly.get("debit", 0) or 0
                    credit = anomaly.get("credit", 0) or 0
                    amount = anomaly.get("amount", 0) or 0
                    category_info = category_map.get(account, {})

                    writer.writerow([
                        f"TB-{ref_idx:04d}",
                        sanitize_csv_value(account),
                        f"{debit:.2f}" if debit else "",
                        f"{credit:.2f}" if credit else "",
                        f"{amount:.2f}",
                        sanitize_csv_value(category_info.get("category", anomaly.get("type", "Unknown"))),
                        f"{category_info.get('confidence', 0):.0%}" if category_info.get('confidence') else ""
                    ])
                    accounts_written.add(account)
                    ref_idx += 1

        writer.writerow([])
        writer.writerow(["TOTALS", "", f"{audit_result.total_debits:.2f}", f"{audit_result.total_credits:.2f}", f"{audit_result.difference:.2f}", "", ""])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(audit_result.filename or "TrialBalance", "TB", "csv")

        log_secure_operation(
            "csv_tb_export_complete",
            f"CSV TB generated: {len(csv_bytes)} bytes"
        )

        return streaming_csv_response(csv_bytes, download_filename)

    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("CSV trial balance export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "csv_tb_export_error")
        )


# --- CSV Anomalies ---

@router.post("/export/csv/anomalies")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_anomalies(request: Request, audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)):
    """Export anomaly list as CSV."""
    log_secure_operation(
        "csv_anomaly_export_start",
        f"Generating CSV anomalies for: {audit_result.filename}"
    )

    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Reference", "Account", "Category", "Issue", "Amount",
            "Materiality", "Severity", "Anomaly Type", "Confidence"
        ])

        material_idx = 1
        immaterial_idx = 1

        for anomaly in audit_result.abnormal_balances:
            if isinstance(anomaly, dict):
                materiality = anomaly.get("materiality", "immaterial")

                if materiality == "material":
                    ref_num = f"TB-M{material_idx:03d}"
                    material_idx += 1
                else:
                    ref_num = f"TB-I{immaterial_idx:03d}"
                    immaterial_idx += 1

                writer.writerow([
                    ref_num,
                    sanitize_csv_value(anomaly.get("account", "Unknown")),
                    sanitize_csv_value(anomaly.get("type", "Unknown")),
                    sanitize_csv_value(anomaly.get("issue", "")),
                    f"{anomaly.get('amount', 0):.2f}",
                    materiality.title(),
                    anomaly.get("severity", "low").title(),
                    anomaly.get("anomaly_type", "abnormal_balance"),
                    f"{anomaly.get('confidence', 0):.0%}" if anomaly.get('confidence') else ""
                ])

        writer.writerow([])
        writer.writerow(["SUMMARY", "", "", "", "", "", "", "", ""])
        writer.writerow(["Material Count", audit_result.material_count, "", "", "", "", "", "", ""])
        writer.writerow(["Immaterial Count", audit_result.immaterial_count, "", "", "", "", "", "", ""])
        writer.writerow(["Total Anomalies", len(audit_result.abnormal_balances), "", "", "", "", "", "", ""])

        if audit_result.risk_summary:
            writer.writerow([])
            writer.writerow(["RISK BREAKDOWN", "", "", "", "", "", "", "", ""])
            for risk_type, count in audit_result.risk_summary.items():
                if isinstance(count, int) and count > 0:
                    writer.writerow([risk_type.replace("_", " ").title(), count, "", "", "", "", "", "", ""])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(audit_result.filename or "TrialBalance", "Anomalies", "csv")

        log_secure_operation(
            "csv_anomaly_export_complete",
            f"CSV anomalies generated: {len(csv_bytes)} bytes"
        )

        return streaming_csv_response(csv_bytes, download_filename)

    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("CSV anomaly export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "csv_anomaly_export_error")
        )


# --- Lead Sheet Export ---

@router.post("/export/leadsheets")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_leadsheets(
    request: Request,
    payload: LeadSheetInput,
    current_user: User = Depends(require_verified_user)
):
    """Generate Excel Lead Sheets from analysis result."""
    log_secure_operation("leadsheet_export", f"Exporting lead sheets for {len(payload.flux.items)} items")

    try:
        flux_items = []
        for i in payload.flux.items:
            flux_items.append(FluxItem(
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
                risk_reasons=i.risk_reasons
            ))

        flux_result = FluxResult(
            items=flux_items,
            total_items=payload.flux.summary.total_items,
            high_risk_count=payload.flux.summary.high_risk_count,
            medium_risk_count=payload.flux.summary.medium_risk_count,
            new_accounts_count=payload.flux.summary.new_accounts,
            removed_accounts_count=payload.flux.summary.removed_accounts,
            materiality_threshold=payload.flux.summary.threshold
        )

        recon_scores = []
        for s in payload.recon.scores:
            recon_scores.append(ReconScore(
                account_name=s.account,
                risk_score=s.score,
                risk_band=try_parse_risk_band(s.band),
                factors=s.factors,
                suggested_action=s.action
            ))

        recon_result = ReconResult(
            scores=recon_scores,
            high_risk_count=payload.recon.stats.high,
            medium_risk_count=payload.recon.stats.medium,
            low_risk_count=payload.recon.stats.low
        )

        excel_bytes = generate_leadsheets(flux_result, recon_result, payload.filename)

        download_filename = safe_download_filename(payload.filename, "LeadSheets", "xlsx")

        log_secure_operation("leadsheet_generated", f"Generated {len(excel_bytes)} bytes")

        return streaming_excel_response(excel_bytes, download_filename)

    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Lead sheet export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "leadsheet_error")
        )


# --- Financial Statements Export ---

@router.post("/export/financial-statements")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_financial_statements(
    request: Request,
    payload: FinancialStatementsInput,
    format: str = Query(default="pdf", pattern="^(pdf|excel)$"),
    current_user: User = Depends(require_verified_user),
):
    """Generate and download financial statements as PDF or Excel."""
    log_secure_operation(
        "financial_statements_export_start",
        f"Generating {format} financial statements for: {payload.filename}"
    )

    # Validate input
    summaries = payload.lead_sheet_grouping.get("summaries", [])
    if not summaries:
        raise HTTPException(
            status_code=400,
            detail="lead_sheet_grouping must contain non-empty 'summaries' list"
        )

    try:
        builder = FinancialStatementBuilder(
            payload.lead_sheet_grouping,
            entity_name=payload.entity_name or "",
            period_end=payload.period_end or "",
            prior_lead_sheet_grouping=payload.prior_lead_sheet_grouping,
        )
        statements = builder.build()

        if format == "excel":
            file_bytes = generate_financial_statements_excel(
                statements,
                prepared_by=payload.prepared_by,
                reviewed_by=payload.reviewed_by,
                workpaper_date=payload.workpaper_date,
            )
            download_filename = safe_download_filename(payload.filename or "FinancialStatements", "FinStmts", "xlsx")
            return streaming_excel_response(file_bytes, download_filename)
        else:
            file_bytes = generate_financial_statements_pdf(
                statements,
                prepared_by=payload.prepared_by,
                reviewed_by=payload.reviewed_by,
                workpaper_date=payload.workpaper_date,
            )
            download_filename = safe_download_filename(payload.filename or "FinancialStatements", "FinStmts", "pdf")

        log_secure_operation(
            "financial_statements_export_complete",
            f"Financial statements {format} generated: {len(file_bytes)} bytes"
        )

        return streaming_pdf_response(file_bytes, download_filename)

    except (ValueError, KeyError, TypeError, OSError) as e:
        logger.exception("Financial statements export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "financial_statements_export_error")
        )
