"""
Currency Conversion Routes — Sprint 258

Rate table upload, manual rate entry, and rate table management.
Currency conversion is triggered during TB upload when rates are present.
"""

import asyncio
import io
import logging
import time
from typing import Optional

import pandas as pd
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import User, require_verified_user
from database import get_db
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT
from shared.helpers import validate_file_size, memory_cleanup
from shared.error_messages import sanitize_error
from currency_engine import (
    parse_rate_table,
    parse_single_rate,
    CurrencyRateTable,
    RateValidationError,
    detect_currencies_in_tb,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["currency"])


# =============================================================================
# SESSION STORAGE (Zero-Storage — ephemeral rate tables)
# =============================================================================

_SESSION_TTL_SECONDS = 7200  # 2 hours
_MAX_SESSIONS = 500

_rate_sessions: dict[str, CurrencyRateTable] = {}
_rate_timestamps: dict[str, float] = {}


def _cleanup_expired_sessions() -> None:
    """Remove sessions that have exceeded TTL."""
    now = time.monotonic()
    expired = [
        key for key, ts in _rate_timestamps.items()
        if now - ts > _SESSION_TTL_SECONDS
    ]
    for key in expired:
        _rate_sessions.pop(key, None)
        _rate_timestamps.pop(key, None)


def get_user_rate_table(user_id: int) -> Optional[CurrencyRateTable]:
    """Get the rate table for a user's session, or None."""
    key = str(user_id)
    _cleanup_expired_sessions()

    table = _rate_sessions.get(key)
    if table is not None:
        _rate_timestamps[key] = time.monotonic()
    return table


def set_user_rate_table(user_id: int, table: CurrencyRateTable) -> None:
    """Store a rate table in the user's session."""
    key = str(user_id)
    _cleanup_expired_sessions()

    # Enforce max sessions — evict oldest
    if key not in _rate_sessions and len(_rate_sessions) >= _MAX_SESSIONS:
        oldest_key = min(_rate_timestamps, key=_rate_timestamps.get)
        _rate_sessions.pop(oldest_key, None)
        _rate_timestamps.pop(oldest_key, None)

    _rate_sessions[key] = table
    _rate_timestamps[key] = time.monotonic()


def clear_user_rate_table(user_id: int) -> bool:
    """Clear the rate table from a user's session. Returns True if existed."""
    key = str(user_id)
    existed = key in _rate_sessions
    _rate_sessions.pop(key, None)
    _rate_timestamps.pop(key, None)
    return existed


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class RateTableUploadResponse(BaseModel):
    """Response for rate table upload."""
    rate_count: int
    presentation_currency: str
    currency_pairs: list[str]
    uploaded_at: str


class SingleRateResponse(BaseModel):
    """Response for single rate entry."""
    from_currency: str
    to_currency: str
    rate: str
    presentation_currency: str
    total_rates: int


class RateTableStatusResponse(BaseModel):
    """Response for rate table status check."""
    has_rates: bool
    rate_count: int = 0
    presentation_currency: Optional[str] = None
    currency_pairs: list[str] = Field(default_factory=list)


class SingleRateRequest(BaseModel):
    """Request for manual single-rate entry."""
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    rate: str = Field(..., min_length=1)
    presentation_currency: Optional[str] = Field(default=None, min_length=3, max_length=3)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/audit/currency-rates",
    response_model=RateTableUploadResponse,
    status_code=201,
)
@limiter.limit(RATE_LIMIT_AUDIT)
async def upload_rate_table(
    request: Request,
    file: UploadFile = File(...),
    presentation_currency: str = Form(default="USD"),
    current_user: User = Depends(require_verified_user),
) -> RateTableUploadResponse:
    """Upload a CSV rate table for multi-currency conversion.

    Expected CSV columns: effective_date, from_currency, to_currency, rate
    """
    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = (file.filename or "").lower()

            # Parse CSV
            def _parse():
                if filename.endswith(".xlsx") or filename.endswith(".xls"):
                    df = pd.read_excel(io.BytesIO(file_bytes))
                else:
                    df = pd.read_csv(io.BytesIO(file_bytes))

                rows = df.to_dict(orient="records")
                return parse_rate_table(rows)

            rates = await asyncio.to_thread(_parse)

            # Validate presentation currency
            pres_curr = presentation_currency.strip().upper()
            if len(pres_curr) != 3:
                raise HTTPException(
                    status_code=400,
                    detail="Presentation currency must be a 3-letter ISO 4217 code",
                )

            table = CurrencyRateTable(
                rates=rates,
                uploaded_at=datetime.now(UTC),
                presentation_currency=pres_curr,
            )
            set_user_rate_table(current_user.id, table)

            table_dict = table.to_dict()

            logger.info(
                "Rate table uploaded: %d rates, presentation=%s, user=%d",
                len(rates), pres_curr, current_user.id,
            )

            return RateTableUploadResponse(
                rate_count=table_dict["rate_count"],
                presentation_currency=pres_curr,
                currency_pairs=table_dict["currency_pairs"],
                uploaded_at=table.uploaded_at.isoformat() if table.uploaded_at else "",
            )

        except RateValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Rate table upload failed")
            raise HTTPException(status_code=400, detail=sanitize_error(str(e)))


@router.post(
    "/audit/currency-rate",
    response_model=SingleRateResponse,
    status_code=201,
)
@limiter.limit(RATE_LIMIT_AUDIT)
def add_single_rate(
    request: Request,
    rate_data: SingleRateRequest,
    current_user: User = Depends(require_verified_user),
) -> SingleRateResponse:
    """Add a single exchange rate for simple conversions.

    If a rate table already exists, the rate is appended.
    Otherwise, a new single-rate table is created.
    """
    try:
        rate = parse_single_rate(
            rate_data.from_currency,
            rate_data.to_currency,
            rate_data.rate,
        )

        pres_curr = (rate_data.presentation_currency or rate_data.to_currency).strip().upper()

        existing = get_user_rate_table(current_user.id)
        if existing is not None:
            existing.rates.append(rate)
            existing.presentation_currency = pres_curr
            set_user_rate_table(current_user.id, existing)
            total = len(existing.rates)
        else:
            table = CurrencyRateTable(
                rates=[rate],
                uploaded_at=datetime.now(UTC),
                presentation_currency=pres_curr,
            )
            set_user_rate_table(current_user.id, table)
            total = 1

        return SingleRateResponse(
            from_currency=rate.from_currency,
            to_currency=rate.to_currency,
            rate=str(rate.rate),
            presentation_currency=pres_curr,
            total_rates=total,
        )

    except RateValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/audit/currency-rates",
    response_model=RateTableStatusResponse,
)
@limiter.limit("30/minute")
def get_rate_status(
    request: Request,
    current_user: User = Depends(require_verified_user),
) -> RateTableStatusResponse:
    """Check if the user has an active rate table in their session."""
    table = get_user_rate_table(current_user.id)
    if table is None:
        return RateTableStatusResponse(has_rates=False)

    table_dict = table.to_dict()
    return RateTableStatusResponse(
        has_rates=True,
        rate_count=table_dict["rate_count"],
        presentation_currency=table_dict["presentation_currency"],
        currency_pairs=table_dict["currency_pairs"],
    )


@router.delete(
    "/audit/currency-rates",
    status_code=204,
)
@limiter.limit(RATE_LIMIT_AUDIT)
def clear_rate_table(
    request: Request,
    current_user: User = Depends(require_verified_user),
) -> None:
    """Clear the user's rate table from the session."""
    clear_user_rate_table(current_user.id)
