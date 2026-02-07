"""
Paciolus API — Bank Reconciliation Routes
"""
import io
import json
from datetime import datetime, UTC
from io import StringIO
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from security_utils import log_secure_operation, clear_memory
from models import User
from auth import require_verified_user
from bank_reconciliation import reconcile_bank_statement, export_reconciliation_csv, ReconciliationSummary, ReconciliationMatch, MatchType, BankTransaction, LedgerTransaction
from shared.helpers import validate_file_size
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT

router = APIRouter(tags=["bank_reconciliation"])


@router.post("/audit/bank-reconciliation")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_bank_reconciliation(
    request: Request,
    bank_file: UploadFile = File(...),
    ledger_file: UploadFile = File(...),
    bank_column_mapping: Optional[str] = Form(default=None),
    ledger_column_mapping: Optional[str] = Form(default=None),
    current_user: User = Depends(require_verified_user),
):
    """Reconcile bank statement against general ledger."""
    bank_mapping_dict: Optional[dict[str, str]] = None
    ledger_mapping_dict: Optional[dict[str, str]] = None

    if bank_column_mapping:
        try:
            bank_mapping_dict = json.loads(bank_column_mapping)
            log_secure_operation(
                "bank_rec_bank_mapping",
                f"Received bank column mapping: {list(bank_mapping_dict.keys())}"
            )
        except json.JSONDecodeError:
            log_secure_operation("bank_rec_bank_mapping_error", "Invalid JSON in bank_column_mapping")

    if ledger_column_mapping:
        try:
            ledger_mapping_dict = json.loads(ledger_column_mapping)
            log_secure_operation(
                "bank_rec_ledger_mapping",
                f"Received ledger column mapping: {list(ledger_mapping_dict.keys())}"
            )
        except json.JSONDecodeError:
            log_secure_operation("bank_rec_ledger_mapping_error", "Invalid JSON in ledger_column_mapping")

    log_secure_operation(
        "bank_rec_upload",
        f"Processing bank rec: bank={bank_file.filename}, ledger={ledger_file.filename}"
    )

    try:
        # Read both files
        bank_bytes = await validate_file_size(bank_file)
        ledger_bytes = await validate_file_size(ledger_file)

        # Parse bank file
        bank_filename = (bank_file.filename or "").lower()
        if bank_filename.endswith(('.xlsx', '.xls')):
            bank_df = pd.read_excel(io.BytesIO(bank_bytes))
        else:
            bank_df = pd.read_csv(io.BytesIO(bank_bytes))

        bank_columns = list(bank_df.columns.astype(str))
        bank_rows = bank_df.to_dict('records')

        del bank_bytes
        del bank_df

        # Parse ledger file
        ledger_filename = (ledger_file.filename or "").lower()
        if ledger_filename.endswith(('.xlsx', '.xls')):
            ledger_df = pd.read_excel(io.BytesIO(ledger_bytes))
        else:
            ledger_df = pd.read_csv(io.BytesIO(ledger_bytes))

        ledger_columns = list(ledger_df.columns.astype(str))
        ledger_rows = ledger_df.to_dict('records')

        del ledger_bytes
        del ledger_df

        # Run reconciliation
        result = reconcile_bank_statement(
            bank_rows=bank_rows,
            ledger_rows=ledger_rows,
            bank_columns=bank_columns,
            ledger_columns=ledger_columns,
            config=None,
            bank_mapping=bank_mapping_dict,
            ledger_mapping=ledger_mapping_dict,
        )

        del bank_rows
        del ledger_rows
        clear_memory()

        return result.to_dict()

    except Exception as e:
        log_secure_operation("bank_rec_error", str(e))
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process bank reconciliation: {str(e)}"
        )


class BankRecExportInput(BaseModel):
    """Input model for bank reconciliation CSV export."""
    summary: dict
    matches: list
    filename: str = "bank_reconciliation"


@router.post("/export/csv/bank-rec")
async def export_csv_bank_rec(
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

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in export_input.filename if c.isalnum() or c in "._-")
        download_filename = f"{safe_name}_BankRec_{timestamp}.csv"

        return StreamingResponse(
            iter([csv_bytes]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(csv_bytes)),
            }
        )
    except Exception as e:
        log_secure_operation("bank_rec_csv_export_error", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {str(e)}")
