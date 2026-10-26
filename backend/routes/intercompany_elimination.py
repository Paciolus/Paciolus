"""
Multi-Entity Intercompany Elimination Routes (Sprint 637).

Form-input only — zero-storage. Accepts multiple entity TBs, returns
the matched intercompany pairs, mismatches, proposed elimination JEs,
and a consolidation worksheet.
"""

from __future__ import annotations

import io
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import User, require_verified_user
from database import get_db
from intercompany_elimination_engine import (
    EntityAccount,
    EntityTrialBalance,
    IntercompanyConfig,
    IntercompanyInputError,
    run_intercompany_elimination,
)
from shared.export_helpers import MEDIA_CSV, attachment_response
from shared.filenames import safe_csv_writer
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.request_decimal import parse_request_amount
from shared.request_decimal import parse_request_decimal as _to_decimal
from shared.testing_route import enforce_tool_access, run_json_tool

logger = logging.getLogger(__name__)

router = APIRouter(tags=["intercompany-elimination"])


class EntityAccountRequest(BaseModel):
    account: str = Field(..., min_length=1, max_length=200)
    debit: str = Field(default="0", max_length=24)
    credit: str = Field(default="0", max_length=24)
    counterparty_entity: str | None = Field(default=None, max_length=200)


class EntityTBRequest(BaseModel):
    entity_id: str = Field(..., min_length=1, max_length=64)
    entity_name: str = Field(..., min_length=1, max_length=200)
    accounts: list[EntityAccountRequest] = Field(default_factory=list, max_length=5000)


class IntercompanyEliminationRequest(BaseModel):
    entities: list[EntityTBRequest] = Field(..., min_length=2, max_length=50)
    tolerance: str = Field(default="1.00", max_length=12)
    # Sprint 787b: optional engagement link so a run lands in the workpaper trail.
    engagement_id: Optional[int] = Field(None, description="Optional engagement to link this run to")


def _build_config(payload: IntercompanyEliminationRequest) -> IntercompanyConfig:
    return IntercompanyConfig(
        entities=[
            EntityTrialBalance(
                entity_id=e.entity_id,
                entity_name=e.entity_name,
                accounts=[
                    EntityAccount(
                        account=a.account,
                        debit=parse_request_amount("debit", a.debit),
                        credit=parse_request_amount("credit", a.credit),
                        counterparty_entity=a.counterparty_entity,
                    )
                    for a in e.accounts
                ],
            )
            for e in payload.entities
        ],
        tolerance=_to_decimal("tolerance", payload.tolerance),
    )


@router.post("/audit/intercompany-elimination")
@limiter.limit(RATE_LIMIT_AUDIT)
def run_consolidation(
    request: Request,
    payload: IntercompanyEliminationRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict:
    # Sprint 689c: gate promoted tool at tier + upload-limit level;
    # Sprint 787b: run recorded on the engagement workpaper trail (success
    # synchronously, before the response). Sprint 819: the sequence lives in
    # shared/testing_route.py::run_json_tool.
    result = run_json_tool(
        db=db,
        current_user=current_user,
        tool_name="intercompany_elimination",
        engagement_id=payload.engagement_id,
        compute=lambda: run_intercompany_elimination(_build_config(payload)),
        input_errors=(IntercompanyInputError,),
        error_key="intercompany_error",
        route_logger=logger,
        failure_log="Intercompany elimination failed",
    )
    return result.to_dict()


@router.post("/audit/intercompany-elimination/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_consolidation_csv(
    request: Request,
    payload: IntercompanyEliminationRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> Response:
    # Sprint 689c: gate promoted tool (export mirrors analyze-route gating).
    enforce_tool_access(current_user, "intercompany_elimination", db)

    try:
        result = run_intercompany_elimination(_build_config(payload))
    except IntercompanyInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ArithmeticError:
        # Sprint 827: a huge-but-finite amount ("1e400") passes parsing, then
        # quantize() raises InvalidOperation — an input problem, not a 500.
        raise HTTPException(status_code=400, detail="An amount is too large to process.")

    buffer = io.StringIO()
    writer = safe_csv_writer(buffer)

    writer.writerow(["Consolidation Worksheet"])
    writer.writerow(
        [
            "Entity ID",
            "Entity Name",
            "Debit Total",
            "Credit Total",
            "Intercompany Gross",
        ]
    )
    for column in result.worksheet.columns:
        writer.writerow(
            [
                column.entity_id,
                column.entity_name,
                str(column.debit_total),
                str(column.credit_total),
                str(column.intercompany_gross),
            ]
        )
    writer.writerow(
        [
            "Totals",
            "",
            str(result.worksheet.total_entity_debits),
            str(result.worksheet.total_entity_credits),
            "",
        ]
    )
    writer.writerow(
        [
            "Eliminations",
            "",
            str(result.worksheet.elimination_debits),
            str(result.worksheet.elimination_credits),
            "",
        ]
    )
    writer.writerow(
        [
            "Consolidated",
            "",
            str(result.worksheet.consolidated_debits),
            str(result.worksheet.consolidated_credits),
            "",
        ]
    )

    writer.writerow([])
    writer.writerow(["Elimination Journal Entries"])
    writer.writerow(["Description", "Debit Entity", "Debit Account", "Credit Entity", "Credit Account", "Amount"])
    for je in result.elimination_journal_entries:
        writer.writerow(
            [
                je.description,
                je.debit_entity,
                je.debit_account,
                je.credit_entity,
                je.credit_account,
                str(je.amount),
            ]
        )

    writer.writerow([])
    writer.writerow(["Mismatches"])
    writer.writerow(["Kind", "Entity", "Counterparty", "Account", "Direction", "Amount", "Message"])
    for m in result.mismatches:
        writer.writerow(
            [
                m.kind.value,
                m.entity,
                m.counterparty or "",
                m.account,
                m.direction,
                str(m.amount),
                m.message,
            ]
        )

    buffer.seek(0)
    return attachment_response(buffer.getvalue(), "intercompany_consolidation.csv", MEDIA_CSV, quote_filename=False)
