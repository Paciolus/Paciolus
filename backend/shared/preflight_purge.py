"""Purge a user's cached previews in every worker (Sprint 879d, review DH-07)."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from preview_purge_model import PreviewPurgeRequest

logger = logging.getLogger(__name__)

__all__ = ["PreviewPurgeRequest", "request_purge", "pending_purges"]


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def request_purge(db: Session, user_id: int) -> None:
    """Drop ``user_id``'s previews here now, and in every other worker on its next sweep.

    Called on logout and account deletion. Never raises: a failure to record
    the request leaves the other workers' copies to expire within 10 minutes.
    """
    from shared.preflight_cache import preflight_cache

    preflight_cache.purge_owner(user_id)
    try:
        db.add(PreviewPurgeRequest(user_id=user_id, requested_at=_utcnow()))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.warning("Preview purge request could not be recorded")


def pending_purges(ttl_seconds: int) -> Iterable[tuple[int, float]]:
    """Purge requests from the last cache lifetime, as (user_id, unix time).

    Uses its own session (the sweeper runs outside any request) and deletes
    requests old enough that no preview they could match can still exist.
    """
    from database import SessionLocal

    cutoff = _utcnow() - timedelta(seconds=ttl_seconds + 60)
    db = SessionLocal()
    try:
        db.query(PreviewPurgeRequest).filter(PreviewPurgeRequest.requested_at < cutoff).delete(
            synchronize_session=False
        )
        db.commit()
        rows = db.query(PreviewPurgeRequest.user_id, PreviewPurgeRequest.requested_at).all()
        return [(uid, at.replace(tzinfo=UTC).timestamp()) for uid, at in rows]
    finally:
        db.close()
