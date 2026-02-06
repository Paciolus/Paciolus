"""
Paciolus API — Export Routes (PDF, Excel, CSV, Lead Sheets, JE Testing)
"""
import csv
import io
from datetime import datetime, UTC
from io import StringIO
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from security_utils import log_secure_operation
from models import User
from auth import require_verified_user
from pdf_generator import generate_audit_report
from excel_generator import generate_workpaper
from leadsheet_generator import generate_leadsheets
from flux_engine import FluxResult, FluxItem
from recon_engine import ReconResult, ReconScore
from je_testing_memo_generator import generate_je_testing_memo
from shared.schemas import AuditResultInput
from shared.helpers import try_parse_risk, try_parse_risk_band

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

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in audit_result.filename if c.isalnum() or c in "._-")
        if not safe_filename:
            safe_filename = "TrialBalance"
        download_filename = f"{safe_filename}_Diagnostic_{timestamp}.pdf"

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

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in audit_result.filename if c.isalnum() or c in "._-")
        if not safe_filename:
            safe_filename = "TrialBalance"
        download_filename = f"{safe_filename}_Workpaper_{timestamp}.xlsx"

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

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in audit_result.filename if c.isalnum() or c in "._-")
        if not safe_filename:
            safe_filename = "TrialBalance"
        download_filename = f"{safe_filename}_TB_{timestamp}.csv"

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

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in audit_result.filename if c.isalnum() or c in "._-")
        if not safe_filename:
            safe_filename = "TrialBalance"
        download_filename = f"{safe_filename}_Anomalies_{timestamp}.csv"

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

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in payload.filename if c.isalnum() or c in "._-")
        download_filename = f"LeadSheets_{safe_filename}_{timestamp}.xlsx"

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

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in je_input.filename if c.isalnum() or c in "._-")
        download_filename = f"{safe_name}_JETesting_Memo_{timestamp}.pdf"

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

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in je_input.filename if c.isalnum() or c in "._-")
        download_filename = f"{safe_name}_JETesting_Flagged_{timestamp}.csv"

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
