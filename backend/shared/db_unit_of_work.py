"""
Database unit-of-work helper (Sprint 745 — Phase 1.2).

Wraps the commit / rollback / HTTPException-mapping triad that's been
copy-pasted across ~12 route modules with the shape:

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error during ...")
        raise HTTPException(500, detail=sanitize_error(e, log_label="..."))

Replaced by:

    with db_transaction(db, log_label="db_activity_create"):
        db.add(db_activity)
    db.refresh(db_activity)  # outside the with block; commit already ran

`db.refresh(...)` after a successful commit is virtually never going to
raise `SQLAlchemyError` (the transaction is already durable). If it does,
the 500 propagates uncaught — same observable behavior as the legacy code,
which would have called `db.rollback()` on an already-committed transaction
(a no-op) before raising.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from shared.error_messages import sanitize_error

logger = logging.getLogger(__name__)


@contextmanager
def db_transaction(
    db: Session,
    *,
    log_label: str,
    log_message: str | None = None,
) -> Iterator[None]:
    """
    Commit on clean exit; rollback + sanitized `HTTPException(500)` on `SQLAlchemyError`.

    Args:
        db: SQLAlchemy session bound to the current request.
        log_label: Stable label for `sanitize_error` and `log_secure_operation`
            (e.g. "db_register", "db_activity_create"). Used for log routing
            and incident triage.
        log_message: Optional override for `logger.exception(...)`. Defaults to
            ``f"Database error during {log_label}"``.

    Raises:
        HTTPException(500): On any `SQLAlchemyError`. Detail is sanitized
            via `sanitize_error` (no PII, no SQL fragments leaked).
    """
    try:
        yield
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(log_message or f"Database error during {log_label}")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, log_label=log_label),
        ) from e
