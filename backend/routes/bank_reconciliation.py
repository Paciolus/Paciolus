"""
Paciolus API — Bank Reconciliation Routes
"""

import asyncio
import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from auth import require_verified_user
from bank_reconciliation import (
    BankRecConfig,
    BankTransaction,
    LedgerTransaction,
    MatchType,
    ReconciliationMatch,
    ReconciliationSummary,
    export_reconciliation_csv,
    export_reconciliation_results_csv,
    reconcile_bank_statement,
)
from database import get_db
from models import User
from security_utils import log_secure_operation
from shared.entitlement_checks import check_export_access
from shared.error_messages import sanitize_error
from shared.export_helpers import csv_response
from shared.export_schemas import BankRecExportResult
from shared.filenames import safe_download_filename
from shared.helpers import parse_json_mapping
from shared.rate_limits import RATE_LIMIT_AUDIT, RATE_LIMIT_EXPORT, limiter
from shared.testing_response_schemas import BankRecResponse
from shared.tool_run_recorder import maybe_record_tool_run
from shared.upload_pipeline import (
    memory_cleanup,
    parse_uploaded_file,
    validate_file_size,
)

router = APIRouter(tags=["bank_reconciliation"])


@router.post("/audit/bank-reconciliation", response_model=BankRecResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_bank_reconciliation(
    request: Request,
    bank_file: UploadFile = File(...),
    ledger_file: UploadFile = File(...),
    bank_column_mapping: Optional[str] = Form(default=None),
    ledger_column_mapping: Optional[str] = Form(default=None),
    materiality: Optional[float] = Form(default=None),
    performance_materiality: Optional[float] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reconcile bank statement against general ledger."""
    from shared.entitlement_checks import check_upload_limit
    from shared.testing_route import enforce_tool_access

    enforce_tool_access(current_user, "bank_reconciliation", db)
    # Sprint 678: count bank rec uploads toward the monthly quota.
    check_upload_limit(current_user, db)

    # Sprint 839: the app now sends these. Refuse unusable values with a clear
    # message instead of letting BankRecConfig's ValueError reach the generic
    # sanitised 400 inside the analysis block.
    for label, value in (("Materiality", materiality), ("Performance materiality", performance_materiality)):
        if value is not None and (not math.isfinite(value) or value < 0):
            raise HTTPException(status_code=400, detail=f"{label} must be a dollar amount of zero or more.")
    if materiality is not None and performance_materiality is not None and performance_materiality > materiality:
        raise HTTPException(
            status_code=400,
            detail="Performance materiality cannot exceed materiality.",
        )

    bank_mapping_dict = parse_json_mapping(bank_column_mapping, "bank_rec_bank", field="bank_column_mapping")
    ledger_mapping_dict = parse_json_mapping(ledger_column_mapping, "bank_rec_ledger", field="ledger_column_mapping")

    log_secure_operation(
        "bank_rec_upload", f"Processing bank rec: bank={bank_file.filename}, ledger={ledger_file.filename}"
    )

    with memory_cleanup():
        try:
            # Read file bytes (async I/O)
            bank_bytes = await validate_file_size(bank_file)
            ledger_bytes = await validate_file_size(ledger_file)
            bank_filename = bank_file.filename or ""
            ledger_filename = ledger_file.filename or ""

            config_kwargs: dict[str, Any] = {}
            if materiality is not None:
                config_kwargs["materiality"] = materiality
            if performance_materiality is not None:
                config_kwargs["performance_materiality"] = performance_materiality
            rec_config = BankRecConfig(**config_kwargs) if config_kwargs else None
            # Sprint 763 (RPT-10 finish): tag the materiality source so
            # ``BankRecResult.active_thresholds`` discloses whether the
            # request supplied thresholds or fell back to documented
            # defaults.  Memos / PDFs render this in the workpaper.
            materiality_source = "caller" if config_kwargs else "default"

            def _analyze() -> Any:
                bank_columns, bank_rows = parse_uploaded_file(bank_bytes, bank_filename)
                ledger_columns, ledger_rows = parse_uploaded_file(ledger_bytes, ledger_filename)
                return reconcile_bank_statement(
                    bank_rows=bank_rows,
                    ledger_rows=ledger_rows,
                    bank_columns=bank_columns,
                    ledger_columns=ledger_columns,
                    config=rec_config,
                    bank_mapping=bank_mapping_dict,
                    ledger_mapping=ledger_mapping_dict,
                    materiality_source=materiality_source,
                )

            result = await asyncio.to_thread(_analyze)
            # Sprint 839: ``materiality_source`` is "caller" when either value
            # was supplied; say per threshold which one this run supplied, so a
            # run that set only one does not present the other as entered.
            if result.active_thresholds is not None:
                result.active_thresholds["threshold_sources"] = {
                    "materiality": "caller" if materiality is not None else "default",
                    "performance_materiality": "caller" if performance_materiality is not None else "default",
                }

            # Sprint 887 (OUT-20): the run's flagged-item count, for the anomaly summary.
            bank_flags = (result.composite_score or {}).get("total_flagged")
            maybe_record_tool_run(
                db,
                engagement_id,
                current_user.id,
                "bank_reconciliation",
                True,
                consumes_upload=True,
                flag_count=bank_flags if isinstance(bank_flags, int) else None,
            )

            return result.to_dict()  # type: ignore[no-any-return]

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Bank reconciliation failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "bank_reconciliation", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "analysis", "bank_rec_error"))


class BankRecExportInput(BankRecExportResult):
    """Input model for bank reconciliation CSV export.

    Sprint 886 (OUT-10): the same result model as the memo, plus the match list.
    """

    matches: list
    filename: str = "bank_reconciliation"


@router.post("/export/csv/bank-rec", dependencies=[Depends(check_export_access)])
@limiter.limit(RATE_LIMIT_EXPORT)
def export_csv_bank_rec(
    request: Request,
    export_input: BankRecExportInput,
    current_user: User = Depends(require_verified_user),
) -> Response:
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
            # Sprint 838: split matches carry their ledger pieces in
            # ``ledger_txns`` and open bank items carry ``split_search_limited``;
            # both were dropped here, so the CSV could not show either.
            ledger_txns = [
                LedgerTransaction(
                    date=lt.get("date"),
                    description=lt.get("description", ""),
                    amount=lt.get("amount", 0.0),
                    reference=lt.get("reference"),
                    row_number=lt.get("row_number", 0),
                )
                for lt in (m.get("ledger_txns") or [])
                if isinstance(lt, dict)
            ]
            match_objects.append(
                ReconciliationMatch(
                    bank_txn=bank_txn,
                    ledger_txn=ledger_txn,
                    match_type=MatchType(m.get("match_type", "matched")),
                    match_confidence=m.get("match_confidence", 0.0),
                    ledger_txns=ledger_txns,
                    split_search_limited=bool(m.get("split_search_limited")),
                )
            )

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
        # Sprint 886 (OUT-10): the tests, aging, score and thresholds of the run.
        csv_content += export_reconciliation_results_csv(
            rec_tests=[t.model_dump() for t in export_input.rec_tests] if export_input.rec_tests is not None else None,
            outstanding_aging=(
                [a.model_dump() for a in export_input.outstanding_aging]
                if export_input.outstanding_aging is not None
                else None
            ),
            composite_score=export_input.composite_score.model_dump() if export_input.composite_score else None,
            active_thresholds=export_input.active_thresholds.model_dump() if export_input.active_thresholds else None,
        )
        csv_bytes = csv_content.encode("utf-8-sig")

        download_filename = safe_download_filename(export_input.filename, "BankRec", "csv")

        return csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("Bank rec CSV export failed")
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", "bank_rec_csv_export_error"))
