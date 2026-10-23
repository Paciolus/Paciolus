"""
Multi-Entity Intercompany Elimination Routes (Sprint 637).

Form-input only — zero-storage. Accepts multiple entity TBs, returns
the matched intercompany pairs, mismatches, proposed elimination JEs,
and a consolidation worksheet.
"""

from __future__ import annotations

import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
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
from shared.entitlement_checks import check_upload_limit
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_route import enforce_tool_access
from shared.tool_run_recorder import maybe_record_tool_run

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


def _to_decimal(field_name: str, raw: str) -> Decimal:
    """Parse a decimal string, rejecting anything the engines cannot arithmetic on.

    PR #189 review: the finiteness check is the load-bearing half. ``Decimal``
    accepts ``"NaN"``, ``"sNaN"``, ``"Infinity"`` and ``"-Infinity"`` without
    raising, so a syntactically valid non-finite value used to pass straight
    through to the engine and blow up on the first comparison or quantisation —
    an uncaught ``InvalidOperation``, surfacing as a 500 where this function's
    whole purpose is to produce a 400.
    """
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")
    if not value.is_finite():
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")
    return value


def _build_config(payload: IntercompanyEliminationRequest) -> IntercompanyConfig:
    return IntercompanyConfig(
        entities=[
            EntityTrialBalance(
                entity_id=e.entity_id,
                entity_name=e.entity_name,
                accounts=[
                    EntityAccount(
                        account=a.account,
                        debit=_to_decimal("debit", a.debit),
                        credit=_to_decimal("credit", a.credit),
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
    # Sprint 689c: gate promoted tool at tier + upload-limit level.
    enforce_tool_access(current_user, "intercompany_elimination", db)
    check_upload_limit(current_user, db)

    try:
        result = run_intercompany_elimination(_build_config(payload))
    except IntercompanyInputError as e:
        maybe_record_tool_run(db, payload.engagement_id, current_user.id, "intercompany_elimination", False)
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, ValidationError, ArithmeticError) as e:
        logger.exception("Intercompany elimination failed")
        maybe_record_tool_run(db, payload.engagement_id, current_user.id, "intercompany_elimination", False)
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "audit", "intercompany_error"),
        )

    # Sprint 787b: record the run on the engagement workpaper trail. Both
    # composite_score and flagged_accounts are None by design, not omission:
    # this engine produces no composite score, and shared/account_extractors.py
    # has no extractor for it because its output is not GL-account-level.
    # PR #183 review: recorded synchronously, not via background_tasks.
    # Starlette sends the response body (responses.py:167) *before* awaiting the
    # background task (:170), so the client already has the result while the
    # insert is still pending. Sprint 791's hooks call refreshToolRuns() as soon
    # as the POST resolves, which would GET the workpaper list before the row
    # existed, replace the context state with the stale list, and never refresh
    # again — the new entry invisible until a manual reload. The write is one
    # INSERT plus a commit after an analysis that already ran in-process, so the
    # latency it buys back is not worth the race.
    maybe_record_tool_run(db, payload.engagement_id, current_user.id, "intercompany_elimination", True, None, None)
    return result.to_dict()


@router.post("/audit/intercompany-elimination/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_consolidation_csv(
    request: Request,
    payload: IntercompanyEliminationRequest,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
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
    writer = csv.writer(buffer)

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
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=intercompany_consolidation.csv"},
    )
