"""
Paciolus API — Core Audit Routes (Inspect, Trial Balance, Flux)
"""
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request

from security_utils import log_secure_operation, clear_memory
from models import User
from auth import require_verified_user
from audit_engine import (
    audit_trial_balance_streaming,
    audit_trial_balance_multi_sheet,
    DEFAULT_CHUNK_SIZE,
)
from workbook_inspector import inspect_workbook, is_excel_file
from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict
from flux_engine import FluxEngine, FluxResult, FluxItem
from recon_engine import ReconEngine, ReconResult
from shared.helpers import validate_file_size, parse_json_mapping
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT

router = APIRouter(tags=["audit"])


@router.post("/audit/inspect-workbook")
async def inspect_workbook_endpoint(
    file: UploadFile = File(...),
    current_user: User = Depends(require_verified_user),
):
    """Inspect an Excel workbook to retrieve sheet metadata."""
    log_secure_operation(
        "inspect_workbook_upload",
        f"Inspecting workbook: {file.filename}"
    )

    try:
        file_bytes = await validate_file_size(file)

        if not is_excel_file(file.filename or ""):
            clear_memory()
            return {
                "filename": file.filename,
                "sheet_count": 1,
                "sheets": [{
                    "name": "Sheet1",
                    "row_count": -1,
                    "column_count": -1,
                    "columns": [],
                    "has_data": True
                }],
                "total_rows": -1,
                "is_multi_sheet": False,
                "format": "csv",
                "requires_sheet_selection": False
            }

        workbook_info = inspect_workbook(file_bytes, file.filename or "")

        del file_bytes
        clear_memory()

        result = workbook_info.to_dict()
        result["requires_sheet_selection"] = workbook_info.is_multi_sheet

        return result

    except ValueError as e:
        log_secure_operation("inspect_workbook_error", str(e))
        clear_memory()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_secure_operation("inspect_workbook_error", str(e))
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to inspect workbook: {str(e)}"
        )


@router.post("/audit/trial-balance")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_trial_balance(
    request: Request,
    file: UploadFile = File(...),
    materiality_threshold: float = Form(default=0.0, ge=0.0),
    account_type_overrides: Optional[str] = Form(default=None),
    column_mapping: Optional[str] = Form(default=None),
    selected_sheets: Optional[str] = Form(default=None),
    current_user: User = Depends(require_verified_user),
):
    """Analyze a trial balance file for balance validation using streaming processing."""
    overrides_dict: Optional[dict[str, str]] = None
    if account_type_overrides:
        try:
            overrides_dict = json.loads(account_type_overrides)
            log_secure_operation(
                "audit_overrides",
                f"Received {len(overrides_dict)} account type overrides"
            )
        except json.JSONDecodeError:
            log_secure_operation("audit_overrides_error", "Invalid JSON in overrides, ignoring")

    column_mapping_dict = parse_json_mapping(column_mapping, "audit_column")

    selected_sheets_list: Optional[list[str]] = None
    if selected_sheets:
        try:
            selected_sheets_list = json.loads(selected_sheets)
            if not isinstance(selected_sheets_list, list):
                selected_sheets_list = None
                log_secure_operation("audit_sheets_error", "selected_sheets must be a list, ignoring")
            else:
                log_secure_operation(
                    "audit_selected_sheets",
                    f"Received {len(selected_sheets_list)} selected sheets: {selected_sheets_list}"
                )
        except json.JSONDecodeError:
            log_secure_operation("audit_sheets_error", "Invalid JSON in selected_sheets, ignoring")

    log_secure_operation(
        "audit_upload_streaming",
        f"Processing file: {file.filename} (threshold: ${materiality_threshold:,.2f}, chunk_size: {DEFAULT_CHUNK_SIZE})"
    )

    try:
        file_bytes = await validate_file_size(file)

        if selected_sheets_list and len(selected_sheets_list) > 0:
            result = audit_trial_balance_multi_sheet(
                file_bytes=file_bytes,
                filename=file.filename or "",
                selected_sheets=selected_sheets_list,
                materiality_threshold=materiality_threshold,
                chunk_size=DEFAULT_CHUNK_SIZE,
                account_type_overrides=overrides_dict,
                column_mapping=column_mapping_dict
            )
        else:
            result = audit_trial_balance_streaming(
                file_bytes=file_bytes,
                filename=file.filename or "",
                materiality_threshold=materiality_threshold,
                chunk_size=DEFAULT_CHUNK_SIZE,
                account_type_overrides=overrides_dict,
                column_mapping=column_mapping_dict
            )

        del file_bytes
        clear_memory()

        if 'abnormal_balances' in result:
            accounts_for_grouping = []
            for ab in result.get('abnormal_balances', []):
                accounts_for_grouping.append({
                    'account': ab.get('account', ''),
                    'debit': ab.get('amount', 0) if ab.get('amount', 0) > 0 else 0,
                    'credit': abs(ab.get('amount', 0)) if ab.get('amount', 0) < 0 else 0,
                    'type': ab.get('type', 'unknown'),
                    'issue': ab.get('issue', ''),
                    'materiality': ab.get('materiality', ''),
                    'severity': ab.get('severity', 'low'),
                    'anomaly_type': ab.get('anomaly_type', 'unknown'),
                })

            lead_sheet_grouping = group_by_lead_sheet(accounts_for_grouping)
            result['lead_sheet_grouping'] = lead_sheet_grouping_to_dict(lead_sheet_grouping)

        return result

    except Exception as e:
        log_secure_operation("audit_error", str(e))
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process file: {str(e)}"
        )


@router.post("/diagnostics/flux")
@limiter.limit(RATE_LIMIT_AUDIT)
async def flux_analysis(
    request: Request,
    current_file: UploadFile = File(...),
    prior_file: UploadFile = File(...),
    materiality: float = Form(0.0),
    current_user: User = Depends(require_verified_user)
):
    """Perform a Flux (Period-over-Period) Analysis."""
    log_secure_operation("flux_start", f"Starting Flux Analysis for user {current_user.id}")

    current_balances = {}
    prior_balances = {}

    try:
        from audit_engine import StreamingAuditor, process_tb_chunked

        content_curr = await validate_file_size(current_file)
        auditor_curr = StreamingAuditor(materiality_threshold=materiality)
        for chunk, rows in process_tb_chunked(content_curr, current_file.filename, DEFAULT_CHUNK_SIZE):
            auditor_curr.process_chunk(chunk, rows)
            del chunk

        classified_curr = auditor_curr.get_classified_accounts()
        for acct, bals in auditor_curr.account_balances.items():
            net = bals["debit"] - bals["credit"]
            acct_type = classified_curr.get(acct, "Unknown")
            current_balances[acct] = {"net": net, "type": acct_type, "debit": bals["debit"], "credit": bals["credit"]}

        auditor_curr.clear()
        del auditor_curr
        del content_curr
        clear_memory()

        content_prior = await validate_file_size(prior_file)
        auditor_prior = StreamingAuditor(materiality_threshold=materiality)
        for chunk, rows in process_tb_chunked(content_prior, prior_file.filename, DEFAULT_CHUNK_SIZE):
            auditor_prior.process_chunk(chunk, rows)
            del chunk

        classified_prior = auditor_prior.get_classified_accounts()
        for acct, bals in auditor_prior.account_balances.items():
            net = bals["debit"] - bals["credit"]
            acct_type = classified_prior.get(acct, "Unknown")
            prior_balances[acct] = {"net": net, "type": acct_type, "debit": bals["debit"], "credit": bals["credit"]}

        auditor_prior.clear()
        del auditor_prior
        del content_prior
        clear_memory()

        flux_engine = FluxEngine(materiality_threshold=materiality)
        flux_result = flux_engine.compare(current_balances, prior_balances)

        recon_engine = ReconEngine(materiality_threshold=materiality)
        recon_result = recon_engine.calculate_scores(flux_result)

        log_secure_operation("flux_complete", f"Flux analysis complete: {len(flux_result.items)} items")

        return {
            "flux": flux_result.to_dict(),
            "recon": recon_result.to_dict()
        }

    except Exception as e:
        log_secure_operation("flux_error", f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Flux processing failed: {str(e)}")
    finally:
        clear_memory()
