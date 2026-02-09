"""
Paciolus API — Export Routes (PDF, Excel, CSV, Lead Sheets, JE Testing, Financial Statements)
"""
import csv
import io
from io import StringIO
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from security_utils import log_secure_operation
from models import User
from auth import require_verified_user
from pdf_generator import generate_audit_report, generate_financial_statements_pdf
from excel_generator import generate_workpaper, generate_financial_statements_excel
from financial_statement_builder import FinancialStatementBuilder
from leadsheet_generator import generate_leadsheets
from flux_engine import FluxResult, FluxItem
from recon_engine import ReconResult, ReconScore
from je_testing_memo_generator import generate_je_testing_memo
from ap_testing_memo_generator import generate_ap_testing_memo
from payroll_testing_memo_generator import generate_payroll_testing_memo
from three_way_match_memo_generator import generate_three_way_match_memo
from revenue_testing_memo_generator import generate_revenue_testing_memo
from ar_aging_memo_generator import generate_ar_aging_memo
from fixed_asset_testing_memo_generator import generate_fixed_asset_testing_memo
from shared.schemas import AuditResultInput
from shared.helpers import try_parse_risk, try_parse_risk_band, safe_download_filename

router = APIRouter(tags=["export"])


# --- Lead Sheet Export Models ---

class FluxItemInput(BaseModel):
    account: str
    type: str
    current: float
    prior: float
    delta_amount: float
    delta_percent: Optional[float] = None
    display_percent: Optional[str] = None
    is_new: bool
    is_removed: bool
    sign_flip: bool
    risk_level: str
    risk_reasons: List[str]


class FluxResultSummary(BaseModel):
    total_items: int
    high_risk_count: int
    medium_risk_count: int
    new_accounts: int
    removed_accounts: int
    threshold: float


class FluxResultInput(BaseModel):
    items: List[FluxItemInput]
    summary: FluxResultSummary


class ReconScoreInput(BaseModel):
    account: str
    score: int
    band: str
    factors: List[str]
    action: str


class ReconStats(BaseModel):
    high: int
    medium: int
    low: int


class ReconResultInput(BaseModel):
    scores: List[ReconScoreInput]
    stats: ReconStats


class LeadSheetInput(BaseModel):
    flux: FluxResultInput
    recon: ReconResultInput
    filename: str


# --- JE Testing Export Models ---

class JETestingExportInput(BaseModel):
    """Input model for JE testing exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    multi_currency_warning: Optional[dict] = None
    benford_result: Optional[dict] = None
    filename: str = "je_testing"
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


# --- AP Testing Export Models ---

class APTestingExportInput(BaseModel):
    """Input model for AP testing exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    filename: str = "ap_testing"
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


class PayrollTestingExportInput(BaseModel):
    """Input model for payroll testing exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    filename: str = "payroll_testing"
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


# --- PDF Export ---

@router.post("/export/pdf")
async def export_pdf_report(audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)):
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

        def iter_pdf():
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(audit_result.filename or "TrialBalance", "Diagnostic", "pdf")

        log_secure_operation(
            "pdf_export_complete",
            f"PDF generated: {len(pdf_bytes)} bytes, filename: {download_filename}"
        )

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("pdf_export_error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF report: {str(e)}"
        )


# --- Excel Export ---

@router.post("/export/excel")
async def export_excel_workpaper(audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)):
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

        def iter_excel():
            chunk_size = 8192
            for i in range(0, len(excel_bytes), chunk_size):
                yield excel_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(audit_result.filename or "TrialBalance", "Workpaper", "xlsx")

        log_secure_operation(
            "excel_export_complete",
            f"Excel generated: {len(excel_bytes)} bytes, filename: {download_filename}"
        )

        return StreamingResponse(
            iter_excel(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(excel_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("excel_export_error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Excel workpaper: {str(e)}"
        )


# --- CSV Trial Balance ---

@router.post("/export/csv/trial-balance")
async def export_csv_trial_balance(audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)):
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
                        account,
                        f"{debit:.2f}" if debit else "",
                        f"{credit:.2f}" if credit else "",
                        f"{amount:.2f}",
                        category_info.get("category", anomaly.get("type", "Unknown")),
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

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("csv_tb_export_error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate CSV: {str(e)}"
        )


# --- CSV Anomalies ---

@router.post("/export/csv/anomalies")
async def export_csv_anomalies(audit_result: AuditResultInput, current_user: User = Depends(require_verified_user)):
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
                    anomaly.get("account", "Unknown"),
                    anomaly.get("type", "Unknown"),
                    anomaly.get("issue", ""),
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

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("csv_anomaly_export_error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate CSV: {str(e)}"
        )


# --- Lead Sheet Export ---

@router.post("/export/leadsheets")
async def export_leadsheets(
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

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(excel_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("leadsheet_error", f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# --- JE Testing Memo PDF ---

@router.post("/export/je-testing-memo")
async def export_je_testing_memo(
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

        def iter_pdf():
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(je_input.filename, "JETesting_Memo", "pdf")

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("je_memo_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate memo: {str(e)}")


# --- JE Testing CSV ---

@router.post("/export/csv/je-testing")
async def export_csv_je_testing(
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
                    entry.get("entry_id", ""),
                    entry.get("posting_date", "") or entry.get("entry_date", ""),
                    entry.get("account", ""),
                    (entry.get("description", "") or "")[:80],
                    f"{entry.get('debit', 0):.2f}" if entry.get('debit') else "",
                    f"{entry.get('credit', 0):.2f}" if entry.get('credit') else "",
                    fe.get("issue", ""),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        cs = je_input.composite_score
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Composite Score", f"{cs.get('score', 0):.1f}"])
        writer.writerow(["Risk Tier", cs.get("risk_tier", "")])
        writer.writerow(["Total Entries", cs.get("total_entries", 0)])
        writer.writerow(["Total Flagged", cs.get("total_flagged", 0)])
        writer.writerow(["Flag Rate", f"{cs.get('flag_rate', 0):.1%}"])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(je_input.filename, "JETesting_Flagged", "csv")

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("je_csv_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")


# --- Financial Statements Export ---

class FinancialStatementsInput(BaseModel):
    """Input model for financial statements export."""
    lead_sheet_grouping: dict
    prior_lead_sheet_grouping: Optional[dict] = None
    filename: str = "financial_statements"
    entity_name: Optional[str] = None
    period_end: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


@router.post("/export/financial-statements")
async def export_financial_statements(
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
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
        else:
            file_bytes = generate_financial_statements_pdf(
                statements,
                prepared_by=payload.prepared_by,
                reviewed_by=payload.reviewed_by,
                workpaper_date=payload.workpaper_date,
            )
            media_type = "application/pdf"
            ext = "pdf"

        def iter_bytes():
            chunk_size = 8192
            for i in range(0, len(file_bytes), chunk_size):
                yield file_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(payload.filename or "FinancialStatements", "FinStmts", ext)

        log_secure_operation(
            "financial_statements_export_complete",
            f"Financial statements {format} generated: {len(file_bytes)} bytes"
        )

        return StreamingResponse(
            iter_bytes(),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(file_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("financial_statements_export_error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate financial statements: {str(e)}"
        )


# --- AP Testing Memo PDF ---

@router.post("/export/ap-testing-memo")
async def export_ap_testing_memo(
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

        def iter_pdf():
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(ap_input.filename, "APTesting_Memo", "pdf")

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("ap_memo_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate memo: {str(e)}")


# --- AP Testing CSV ---

@router.post("/export/csv/ap-testing")
async def export_csv_ap_testing(
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
                    entry.get("vendor_name", ""),
                    entry.get("invoice_number", ""),
                    entry.get("payment_date", ""),
                    f"{entry.get('amount', 0):.2f}" if entry.get('amount') else "",
                    entry.get("check_number", ""),
                    (entry.get("description", "") or "")[:80],
                    fe.get("issue", ""),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        cs = ap_input.composite_score
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Composite Score", f"{cs.get('score', 0):.1f}"])
        writer.writerow(["Risk Tier", cs.get("risk_tier", "")])
        writer.writerow(["Total Payments", cs.get("total_entries", 0)])
        writer.writerow(["Total Flagged", cs.get("total_flagged", 0)])
        writer.writerow(["Flag Rate", f"{cs.get('flag_rate', 0):.1%}"])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(ap_input.filename, "APTesting_Flagged", "csv")

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("ap_csv_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")


# --- Payroll Testing Memo ---

@router.post("/export/payroll-testing-memo")
async def export_payroll_testing_memo(
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

        def iter_pdf():
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(payroll_input.filename, "PayrollTesting_Memo", "pdf")

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("payroll_memo_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate memo: {str(e)}")


# --- Payroll Testing CSV ---

@router.post("/export/csv/payroll-testing")
async def export_csv_payroll_testing(
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
                    entry.get("employee_name", ""),
                    entry.get("employee_id", ""),
                    entry.get("department", ""),
                    entry.get("pay_date", ""),
                    f"{entry.get('gross_pay', 0):.2f}" if entry.get('gross_pay') else "",
                    fe.get("issue", ""),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        cs = payroll_input.composite_score
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Composite Score", f"{cs.get('score', 0):.1f}"])
        writer.writerow(["Risk Tier", cs.get("risk_tier", "")])
        writer.writerow(["Total Entries", cs.get("total_entries", 0)])
        writer.writerow(["Total Flagged", cs.get("total_flagged", 0)])
        writer.writerow(["Flag Rate", f"{cs.get('flag_rate', 0):.1%}"])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(payroll_input.filename, "PayrollTesting_Flagged", "csv")

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("payroll_csv_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")


# --- Three-Way Match Export Models ---

class ThreeWayMatchExportInput(BaseModel):
    """Input model for three-way match exports."""
    summary: dict
    full_matches: list
    partial_matches: list
    unmatched_pos: list = []
    unmatched_invoices: list = []
    unmatched_receipts: list = []
    variances: list = []
    data_quality: dict = {}
    config: dict = {}
    filename: str = "three_way_match"
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


# --- Three-Way Match Memo PDF ---

@router.post("/export/three-way-match-memo")
async def export_three_way_match_memo(
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

        def iter_pdf():
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(twm_input.filename, "TWM_Memo", "pdf")

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("twm_memo_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate memo: {str(e)}")


# --- Three-Way Match CSV ---

@router.post("/export/csv/three-way-match")
async def export_csv_three_way_match(
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
                po.get("po_number", ""),
                inv.get("invoice_number", ""),
                rec.get("receipt_number", ""),
                po.get("vendor", "") or inv.get("vendor", ""),
                f"{po.get('total_amount', 0):.2f}" if po else "",
                f"{inv.get('total_amount', 0):.2f}" if inv else "",
                f"{rec.get('total_amount', 0):.2f}" if rec else "",
                f"{total_variance:.2f}" if total_variance else "",
                f"{max_pct:.1%}" if max_pct else "",
                f"{m.get('match_confidence', 0):.2f}",
            ])

        # Summary section
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
        writer.writerow(["Risk Assessment", s.get("risk_assessment", "")])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(twm_input.filename, "TWM_Results", "csv")

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("twm_csv_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")


# --- Revenue Testing Export Models ---

class RevenueTestingExportInput(BaseModel):
    """Input model for revenue testing exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    column_detection: Optional[dict] = None
    filename: str = "revenue_testing"
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


# --- Revenue Testing Memo PDF ---

@router.post("/export/revenue-testing-memo")
async def export_revenue_testing_memo(
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

        def iter_pdf():
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(revenue_input.filename, "RevenueTesting_Memo", "pdf")

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("revenue_memo_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate memo: {str(e)}")


# --- Revenue Testing CSV ---

@router.post("/export/csv/revenue-testing")
async def export_csv_revenue_testing(
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
                    entry.get("account_name", ""),
                    entry.get("account_number", ""),
                    entry.get("date", ""),
                    f"{entry.get('amount', 0):.2f}" if entry.get('amount') is not None else "",
                    (entry.get("description", "") or "")[:80],
                    entry.get("entry_type", ""),
                    entry.get("reference", ""),
                    fe.get("issue", ""),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        cs = revenue_input.composite_score
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Composite Score", f"{cs.get('score', 0):.1f}"])
        writer.writerow(["Risk Tier", cs.get("risk_tier", "")])
        writer.writerow(["Total Revenue Entries", cs.get("total_entries", 0)])
        writer.writerow(["Total Flagged", cs.get("total_flagged", 0)])
        writer.writerow(["Flag Rate", f"{cs.get('flag_rate', 0):.1%}"])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(revenue_input.filename, "RevenueTesting_Flagged", "csv")

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("revenue_csv_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")


# --- AR Aging Export Models ---

class ARAgingExportInput(BaseModel):
    """Input model for AR aging exports."""
    composite_score: dict
    test_results: list
    data_quality: dict
    tb_column_detection: Optional[dict] = None
    sl_column_detection: Optional[dict] = None
    ar_summary: Optional[dict] = None
    filename: str = "ar_aging"
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


# --- AR Aging Memo PDF ---

@router.post("/export/ar-aging-memo")
async def export_ar_aging_memo(
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

        def iter_pdf():
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(ar_input.filename, "ARAging_Memo", "pdf")

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("ar_aging_memo_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate memo: {str(e)}")


# --- AR Aging CSV ---

@router.post("/export/csv/ar-aging")
async def export_csv_ar_aging(
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
                    entry.get("account_name", ""),
                    entry.get("customer_name", ""),
                    entry.get("invoice_number", ""),
                    entry.get("date", ""),
                    f"{entry.get('amount', 0):.2f}" if entry.get('amount') is not None else "",
                    str(entry.get("aging_days", "")) if entry.get("aging_days") is not None else "",
                    fe.get("issue", ""),
                    f"{fe.get('confidence', 0):.2f}",
                ])

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

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("ar_aging_csv_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")


# --- Fixed Asset Testing Export Models ---

class FixedAssetExportInput(BaseModel):
    """Input model for fixed asset testing exports."""
    composite_score: dict
    test_results: list
    data_quality: Optional[dict] = None
    column_detection: Optional[dict] = None
    filename: str = "fixed_asset_testing"
    client_name: Optional[str] = None
    period_tested: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    workpaper_date: Optional[str] = None


# --- Fixed Asset Testing Memo PDF ---

@router.post("/export/fixed-asset-memo")
async def export_fixed_asset_memo(
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

        def iter_pdf():
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        download_filename = safe_download_filename(fa_input.filename, "FixedAsset_Memo", "pdf")

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("fa_memo_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate memo: {str(e)}")


# --- Fixed Asset Testing CSV ---

@router.post("/export/csv/fixed-assets")
async def export_csv_fixed_assets(
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
                    entry.get("asset_id", ""),
                    (entry.get("description", "") or "")[:80],
                    entry.get("category", ""),
                    f"{entry.get('cost', 0):.2f}" if entry.get('cost') is not None else "",
                    f"{entry.get('accumulated_depreciation', 0):.2f}" if entry.get('accumulated_depreciation') is not None else "",
                    str(entry.get("useful_life", "")) if entry.get("useful_life") is not None else "",
                    entry.get("acquisition_date", ""),
                    fe.get("issue", ""),
                    f"{fe.get('confidence', 0):.2f}",
                ])

        cs = fa_input.composite_score
        writer.writerow([])
        writer.writerow(["SUMMARY"])
        writer.writerow(["Composite Score", f"{cs.get('score', 0):.1f}"])
        writer.writerow(["Risk Tier", cs.get("risk_tier", "")])
        writer.writerow(["Total Assets", cs.get("total_entries", 0)])
        writer.writerow(["Total Flagged", cs.get("total_flagged", 0)])
        writer.writerow(["Flag Rate", f"{cs.get('flag_rate', 0):.1%}"])

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(fa_input.filename, "FixedAsset_Flagged", "csv")

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("fa_csv_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")
