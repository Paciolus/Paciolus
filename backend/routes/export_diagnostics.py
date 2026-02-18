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
    AccrualCompletenessCSVInput,
    ExpenseCategoryCSVInput,
    FinancialStatementsInput,
    LeadSheetInput,
    PopulationProfileCSVInput,
    PreFlightCSVInput,
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


# --- Pre-Flight Issues CSV (Sprint 283) ---

@router.post("/export/csv/preflight-issues")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_preflight_issues(
    request: Request,
    pf_input: PreFlightCSVInput,
    current_user: User = Depends(require_verified_user),
):
    """Export pre-flight quality issues as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(["Category", "Severity", "Message", "Affected Count", "Remediation"])

        for issue in pf_input.issues:
            if isinstance(issue, dict):
                writer.writerow([
                    sanitize_csv_value(issue.get("category", "").replace("_", " ").title()),
                    issue.get("severity", "").upper(),
                    sanitize_csv_value(issue.get("message", "")),
                    str(issue.get("affected_count", 0)),
                    sanitize_csv_value(issue.get("remediation", "")),
                ])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(pf_input.filename or "PreFlight", "Issues", "csv")
        return streaming_csv_response(csv_bytes, download_filename)

    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Pre-flight CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "preflight_csv_export_error")
        )


# --- Population Profile CSV (Sprint 287) ---

@router.post("/export/csv/population-profile")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_population_profile(
    request: Request,
    pp_input: PopulationProfileCSVInput,
    current_user: User = Depends(require_verified_user),
):
    """Export population profile data as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        # Summary section
        writer.writerow(["TB POPULATION PROFILE"])
        writer.writerow([])
        writer.writerow(["Statistic", "Value"])
        writer.writerow(["Account Count", pp_input.account_count])
        writer.writerow(["Total Absolute Balance", f"{pp_input.total_abs_balance:.2f}"])
        writer.writerow(["Mean (Absolute)", f"{pp_input.mean_abs_balance:.2f}"])
        writer.writerow(["Median (Absolute)", f"{pp_input.median_abs_balance:.2f}"])
        writer.writerow(["Standard Deviation", f"{pp_input.std_dev_abs_balance:.2f}"])
        writer.writerow(["Minimum", f"{pp_input.min_abs_balance:.2f}"])
        writer.writerow(["Maximum", f"{pp_input.max_abs_balance:.2f}"])
        writer.writerow(["P25", f"{pp_input.p25:.2f}"])
        writer.writerow(["P75", f"{pp_input.p75:.2f}"])
        writer.writerow(["Gini Coefficient", f"{pp_input.gini_coefficient:.4f}"])
        writer.writerow(["Gini Interpretation", pp_input.gini_interpretation])
        writer.writerow([])

        # Magnitude distribution
        writer.writerow(["MAGNITUDE DISTRIBUTION"])
        writer.writerow(["Bucket", "Count", "% of Accounts", "Sum of Balances"])
        for b in pp_input.buckets:
            if isinstance(b, dict):
                writer.writerow([
                    sanitize_csv_value(b.get("label", "")),
                    b.get("count", 0),
                    f"{b.get('percent_count', 0):.1f}%",
                    f"{b.get('sum_abs', 0):.2f}",
                ])
        writer.writerow([])

        # Top accounts
        writer.writerow(["TOP ACCOUNTS BY ABSOLUTE BALANCE"])
        writer.writerow(["Rank", "Account", "Category", "Net Balance", "Absolute Balance", "% of Total"])
        for t in pp_input.top_accounts:
            if isinstance(t, dict):
                writer.writerow([
                    t.get("rank", ""),
                    sanitize_csv_value(str(t.get("account", ""))),
                    sanitize_csv_value(t.get("category", "Unknown")),
                    f"{t.get('net_balance', 0):.2f}",
                    f"{t.get('abs_balance', 0):.2f}",
                    f"{t.get('percent_of_total', 0):.1f}%",
                ])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(pp_input.filename or "PopProfile", "Profile", "csv")
        return streaming_csv_response(csv_bytes, download_filename)

    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Population profile CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "population_profile_csv_export_error")
        )


# --- Expense Category CSV (Sprint 289) ---

@router.post("/export/csv/expense-category-analytics")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_expense_category(
    request: Request,
    ec_input: ExpenseCategoryCSVInput,
    current_user: User = Depends(require_verified_user),
):
    """Export expense category analytics data as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        # Summary section
        writer.writerow(["EXPENSE CATEGORY ANALYTICAL PROCEDURES"])
        writer.writerow([])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Expenses", f"{ec_input.total_expenses:.2f}"])
        writer.writerow(["Total Revenue", f"{ec_input.total_revenue:.2f}"])
        writer.writerow(["Revenue Available", "Yes" if ec_input.revenue_available else "No"])
        writer.writerow(["Prior Period Data", "Yes" if ec_input.prior_available else "No"])
        writer.writerow(["Materiality Threshold", f"{ec_input.materiality_threshold:.2f}"])
        writer.writerow(["Active Categories", ec_input.category_count])
        writer.writerow([])

        # Category breakdown
        has_prior = ec_input.prior_available and any(
            isinstance(c, dict) and c.get("prior_amount") is not None
            for c in ec_input.categories
        )

        if has_prior:
            writer.writerow(["CATEGORY BREAKDOWN"])
            writer.writerow(["Category", "Amount", "% of Revenue", "Prior Amount", "Dollar Change", "Exceeds Materiality"])
        else:
            writer.writerow(["CATEGORY BREAKDOWN"])
            writer.writerow(["Category", "Amount", "% of Revenue"])

        for c in ec_input.categories:
            if isinstance(c, dict):
                amount = c.get("amount", 0)
                pct = c.get("pct_of_revenue")
                pct_str = f"{pct:.2f}%" if pct is not None else "N/A"

                if has_prior:
                    prior_amt = c.get("prior_amount")
                    dollar_change = c.get("dollar_change")
                    exceeds = c.get("exceeds_materiality", False)
                    writer.writerow([
                        sanitize_csv_value(c.get("label", "")),
                        f"{amount:.2f}",
                        pct_str,
                        f"{prior_amt:.2f}" if prior_amt is not None else "N/A",
                        f"{dollar_change:.2f}" if dollar_change is not None else "N/A",
                        "Yes" if exceeds else "No",
                    ])
                else:
                    writer.writerow([
                        sanitize_csv_value(c.get("label", "")),
                        f"{amount:.2f}",
                        pct_str,
                    ])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(ec_input.filename or "ExpenseCategory", "Analytics", "csv")
        return streaming_csv_response(csv_bytes, download_filename)

    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Expense category CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "expense_category_csv_export_error")
        )


# --- Accrual Completeness CSV (Sprint 290) ---

@router.post("/export/csv/accrual-completeness")
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_accrual_completeness(
    request: Request,
    ac_input: AccrualCompletenessCSVInput,
    current_user: User = Depends(require_verified_user),
):
    """Export accrual completeness data as CSV."""
    try:
        output = StringIO()
        writer = csv.writer(output)

        # Summary section
        writer.writerow(["ACCRUAL COMPLETENESS ESTIMATOR"])
        writer.writerow([])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Accrual Accounts Identified", ac_input.accrual_account_count])
        writer.writerow(["Total Accrued Balance", f"{ac_input.total_accrued_balance:.2f}"])
        writer.writerow(["Prior Period Data", "Yes" if ac_input.prior_available else "No"])
        if ac_input.prior_operating_expenses is not None:
            writer.writerow(["Prior Operating Expenses", f"{ac_input.prior_operating_expenses:.2f}"])
        if ac_input.monthly_run_rate is not None:
            writer.writerow(["Monthly Run-Rate", f"{ac_input.monthly_run_rate:.2f}"])
        if ac_input.accrual_to_run_rate_pct is not None:
            writer.writerow(["Accrual-to-Run-Rate %", f"{ac_input.accrual_to_run_rate_pct:.1f}%"])
        writer.writerow(["Threshold", f"{ac_input.threshold_pct:.0f}%"])
        writer.writerow(["Below Threshold", "Yes" if ac_input.below_threshold else "No"])
        writer.writerow([])

        # Accrual accounts
        writer.writerow(["ACCRUAL ACCOUNTS"])
        writer.writerow(["Account", "Balance", "Matched Keyword"])
        for a in ac_input.accrual_accounts:
            if isinstance(a, dict):
                writer.writerow([
                    sanitize_csv_value(str(a.get("account_name", ""))),
                    f"{a.get('balance', 0):.2f}",
                    sanitize_csv_value(a.get("matched_keyword", "")),
                ])
        writer.writerow([])

        # Narrative
        if ac_input.narrative:
            writer.writerow(["NARRATIVE"])
            writer.writerow([sanitize_csv_value(ac_input.narrative)])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(ac_input.filename or "AccrualCompleteness", "Estimator", "csv")
        return streaming_csv_response(csv_bytes, download_filename)

    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Accrual completeness CSV export failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "export", "accrual_completeness_csv_export_error")
        )
