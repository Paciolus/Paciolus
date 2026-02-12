"""
Paciolus API — Bank Reconciliation Routes
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from security_utils import log_secure_operation, clear_memory
from database import get_db
from models import User
from auth import require_verified_user
from shared.error_messages import sanitize_error
from bank_reconciliation import reconcile_bank_statement, export_reconciliation_csv, ReconciliationSummary, ReconciliationMatch, MatchType, BankTransaction, LedgerTransaction
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_mapping, safe_download_filename, maybe_record_tool_run
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT, RATE_LIMIT_EXPORT

router = APIRouter(tags=["bank_reconciliation"])


@router.post("/audit/bank-reconciliation")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_bank_reconciliation(
    request: Request,
    bank_file: UploadFile = File(...),
    ledger_file: UploadFile = File(...),
    bank_column_mapping: Optional[str] = Form(default=None),
    ledger_column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Reconcile bank statement against general ledger."""
    bank_mapping_dict = parse_json_mapping(bank_column_mapping, "bank_rec_bank")
    ledger_mapping_dict = parse_json_mapping(ledger_column_mapping, "bank_rec_ledger")

    log_secure_operation(
        "bank_rec_upload",
        f"Processing bank rec: bank={bank_file.filename}, ledger={ledger_file.filename}"
    )

    try:
        # Read file bytes (async I/O)
        bank_bytes = await validate_file_size(bank_file)
        ledger_bytes = await validate_file_size(ledger_file)
        bank_filename = bank_file.filename or ""
        ledger_filename = ledger_file.filename or ""

        def _analyze():
            bank_columns, bank_rows = parse_uploaded_file(bank_bytes, bank_filename)
            ledger_columns, ledger_rows = parse_uploaded_file(ledger_bytes, ledger_filename)
            return reconcile_bank_statement(
                bank_rows=bank_rows,
                ledger_rows=ledger_rows,
                bank_columns=bank_columns,
                ledger_columns=ledger_columns,
                config=None,
                bank_mapping=bank_mapping_dict,
                ledger_mapping=ledger_mapping_dict,
            )

        result = await asyncio.to_thread(_analyze)
        clear_memory()

        maybe_record_tool_run(db, engagement_id, current_user.id, "bank_reconciliation", True)

        return result.to_dict()

    except Exception as e:
        maybe_record_tool_run(db, engagement_id, current_user.id, "bank_reconciliation", False)
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "analysis", "bank_rec_error")
        )


class BankRecExportInput(BaseModel):
    """Input model for bank reconciliation CSV export."""
    summary: dict
    matches: list
    filename: str = "bank_reconciliation"


@router.post("/export/csv/bank-rec")
@limiter.limit(RATE_LIMIT_EXPORT)
async def export_csv_bank_rec(
    request: Request,
    export_input: BankRecExportInput,
    current_user: User = Depends(require_verified_user),
):
    """Export bank reconciliation results as CSV."""
    try:
        # Rebuild ReconciliationSummary from dict input
        match_objects: list[ReconciliationMatch] = []
        for m in export_input.matches:
            bank_txn = None
            ledger_txn = None
            if m.get("bank_txn"):
                bt = m["bank_txn"]
                bank_txn = BankTransaction(
                    date=bt.get("date"),
                    description=bt.get("description", ""),
                    amount=bt.get("amount", 0.0),
                    reference=bt.get("reference"),
                    row_number=bt.get("row_number", 0),
                )
            if m.get("ledger_txn"):
                lt = m["ledger_txn"]
                ledger_txn = LedgerTransaction(
                    date=lt.get("date"),
                    description=lt.get("description", ""),
                    amount=lt.get("amount", 0.0),
                    reference=lt.get("reference"),
                    row_number=lt.get("row_number", 0),
                )
            match_objects.append(ReconciliationMatch(
                bank_txn=bank_txn,
                ledger_txn=ledger_txn,
                match_type=MatchType(m.get("match_type", "matched")),
                match_confidence=m.get("match_confidence", 0.0),
            ))

        summary_data = export_input.summary
        summary = ReconciliationSummary(
            matched_count=summary_data.get("matched_count", 0),
            matched_amount=summary_data.get("matched_amount", 0.0),
            bank_only_count=summary_data.get("bank_only_count", 0),
            bank_only_amount=summary_data.get("bank_only_amount", 0.0),
            ledger_only_count=summary_data.get("ledger_only_count", 0),
            ledger_only_amount=summary_data.get("ledger_only_amount", 0.0),
            reconciling_difference=summary_data.get("reconciling_difference", 0.0),
            total_bank=summary_data.get("total_bank", 0.0),
            total_ledger=summary_data.get("total_ledger", 0.0),
            matches=match_objects,
        )

        csv_content = export_reconciliation_csv(summary)
        csv_bytes = csv_content.encode('utf-8-sig')

        download_filename = safe_download_filename(export_input.filename, "BankRec", "csv")

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "bank_rec_csv_export_error"))
