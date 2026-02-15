"""
Paciolus API — Core Audit Routes (Inspect, Trial Balance, Flux)
"""
import asyncio
import json
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User
from auth import require_verified_user
from shared.error_messages import sanitize_error
from audit_engine import (
    audit_trial_balance_streaming,
    audit_trial_balance_multi_sheet,
    DEFAULT_CHUNK_SIZE,
)
from workbook_inspector import inspect_workbook, is_excel_file
from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict
from flux_engine import FluxEngine, FluxResult, FluxItem
from recon_engine import ReconEngine, ReconResult
from shared.helpers import validate_file_size, parse_json_list, parse_json_mapping, maybe_record_tool_run, memory_cleanup
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT
from shared.diagnostic_response_schemas import (
    FluxAnalysisResponse,
    TrialBalanceResponse,
)

router = APIRouter(tags=["audit"])


class SheetInfo(BaseModel):
    name: str
    row_count: int
    column_count: int
    columns: list
    has_data: bool


class WorkbookInspectResponse(BaseModel):
    filename: str
    sheet_count: int
    sheets: List[SheetInfo]
    total_rows: int
    is_multi_sheet: bool
    format: str
    requires_sheet_selection: bool



# FluxAnalysisResponse moved to shared.diagnostic_response_schemas


@router.post("/audit/inspect-workbook", response_model=WorkbookInspectResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def inspect_workbook_endpoint(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_verified_user),
):
    """Inspect an Excel workbook to retrieve sheet metadata."""
    log_secure_operation(
        "inspect_workbook_upload",
        f"Inspecting workbook: {file.filename}"
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            if not is_excel_file(filename):
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

            def _inspect():
                workbook_info = inspect_workbook(file_bytes, filename)
                result = workbook_info.to_dict()
                result["requires_sheet_selection"] = workbook_info.is_multi_sheet
                return result

            result = await asyncio.to_thread(_inspect)

            return result

        except ValueError as e:
            raise HTTPException(status_code=400, detail=sanitize_error(
                e, "upload", "inspect_workbook_error",
            ))
        except (KeyError, TypeError, OSError) as e:
            logger.exception("Workbook inspection failed")
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "upload", "inspect_workbook_error")
            )


@router.post("/audit/trial-balance", response_model=TrialBalanceResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_trial_balance(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    materiality_threshold: float = Form(default=0.0, ge=0.0),
    account_type_overrides: Optional[str] = Form(default=None),
    column_mapping: Optional[str] = Form(default=None),
    selected_sheets: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
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
    selected_sheets_list = parse_json_list(selected_sheets, "audit_selected_sheets")

    log_secure_operation(
        "audit_upload_streaming",
        f"Processing file: {file.filename} (threshold: ${materiality_threshold:,.2f}, chunk_size: {DEFAULT_CHUNK_SIZE})"
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _analyze():
                if selected_sheets_list and len(selected_sheets_list) > 0:
                    result = audit_trial_balance_multi_sheet(
                        file_bytes=file_bytes,
                        filename=filename,
                        selected_sheets=selected_sheets_list,
                        materiality_threshold=materiality_threshold,
                        chunk_size=DEFAULT_CHUNK_SIZE,
                        account_type_overrides=overrides_dict,
                        column_mapping=column_mapping_dict
                    )
                else:
                    result = audit_trial_balance_streaming(
                        file_bytes=file_bytes,
                        filename=filename,
                        materiality_threshold=materiality_threshold,
                        chunk_size=DEFAULT_CHUNK_SIZE,
                        account_type_overrides=overrides_dict,
                        column_mapping=column_mapping_dict
                    )

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

            result = await asyncio.to_thread(_analyze)

            background_tasks.add_task(maybe_record_tool_run, db, engagement_id, current_user.id, "trial_balance", True)

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Trial balance analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "trial_balance", False)
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "upload", "audit_error")
            )


@router.post("/audit/flux", response_model=FluxAnalysisResponse)
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

    with memory_cleanup():
        try:
            content_curr = await validate_file_size(current_file)
            content_prior = await validate_file_size(prior_file)
            curr_filename = current_file.filename
            prior_filename = prior_file.filename

            def _analyze():
                from audit_engine import StreamingAuditor, process_tb_chunked

                current_balances = {}
                auditor_curr = StreamingAuditor(materiality_threshold=materiality)
                for chunk, rows in process_tb_chunked(content_curr, curr_filename, DEFAULT_CHUNK_SIZE):
                    auditor_curr.process_chunk(chunk, rows)
                    del chunk

                classified_curr = auditor_curr.get_classified_accounts()
                for acct, bals in auditor_curr.account_balances.items():
                    net = bals["debit"] - bals["credit"]
                    acct_type = classified_curr.get(acct, "Unknown")
                    current_balances[acct] = {"net": net, "type": acct_type, "debit": bals["debit"], "credit": bals["credit"]}

                auditor_curr.clear()
                del auditor_curr

                prior_balances = {}
                auditor_prior = StreamingAuditor(materiality_threshold=materiality)
                for chunk, rows in process_tb_chunked(content_prior, prior_filename, DEFAULT_CHUNK_SIZE):
                    auditor_prior.process_chunk(chunk, rows)
                    del chunk

                classified_prior = auditor_prior.get_classified_accounts()
                for acct, bals in auditor_prior.account_balances.items():
                    net = bals["debit"] - bals["credit"]
                    acct_type = classified_prior.get(acct, "Unknown")
                    prior_balances[acct] = {"net": net, "type": acct_type, "debit": bals["debit"], "credit": bals["credit"]}

                auditor_prior.clear()
                del auditor_prior

                flux_engine = FluxEngine(materiality_threshold=materiality)
                flux_result = flux_engine.compare(current_balances, prior_balances)

                recon_engine = ReconEngine(materiality_threshold=materiality)
                recon_result = recon_engine.calculate_scores(flux_result)

                return flux_result, recon_result

            flux_result, recon_result = await asyncio.to_thread(_analyze)

            log_secure_operation("flux_complete", f"Flux analysis complete: {len(flux_result.items)} items")

            return {
                "flux": flux_result.to_dict(),
                "recon": recon_result.to_dict()
            }

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Flux analysis failed")
            raise HTTPException(status_code=500, detail=sanitize_error(e, "analysis", "flux_error"))
