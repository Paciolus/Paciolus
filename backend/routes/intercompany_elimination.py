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

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from auth import User, require_verified_user
from intercompany_elimination_engine import (
    EntityAccount,
    EntityTrialBalance,
    IntercompanyConfig,
    IntercompanyInputError,
    run_intercompany_elimination,
)
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

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


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


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
) -> dict:
    try:
        result = run_intercompany_elimination(_build_config(payload))
    except IntercompanyInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, ValidationError) as e:
        logger.exception("Intercompany elimination failed")
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(e, "audit", "intercompany_error"),
        )
    return result.to_dict()


@router.post("/audit/intercompany-elimination/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_consolidation_csv(
    request: Request,
    payload: IntercompanyEliminationRequest,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    try:
        result = run_intercompany_elimination(_build_config(payload))
    except IntercompanyInputError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
