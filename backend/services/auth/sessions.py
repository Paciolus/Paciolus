"""
Sessions service (Sprint 746d).

Extracts the session inventory + revocation lifecycle from
`routes/auth_routes.py`. AUDIT-02 FIX 2 (per-session revocation
visibility) is enforced here — the route layer becomes a thin controller
that maps `SessionNotFoundError` to 404.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from auth import _revoke_all_user_tokens
from models import RefreshToken, User
from security_utils import log_secure_operation


class SessionNotFoundError(LookupError):
    """Raised by `revoke_session_by_id` when the session id is unknown,
    already revoked, or owned by a different user. The route maps this
    uniformly to 404 to avoid leaking session-existence to non-owners."""


@dataclass(frozen=True)
class SessionEntry:
    """A single non-revoked refresh token, surfaced by `list_user_sessions`.

    Mirrors the `SessionInfo` Pydantic shape but stays free of HTTP types
    so service callers (and unit tests) can use it without importing
    FastAPI."""

    session_id: int
    last_used_at: str | None
    user_agent: str | None
    ip_address: str | None
    created_at: str | None


def list_user_sessions(db: Session, user: User) -> list[SessionEntry]:
    """
    Return all active (non-revoked) sessions for the calling user.

    Ordered by creation time, descending. Token hashes are never returned.
    """
    tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .order_by(RefreshToken.created_at.desc())
        .all()
    )

    return [
        SessionEntry(
            session_id=t.id,
            last_used_at=t.last_used_at.isoformat() if t.last_used_at else None,
            user_agent=t.user_agent,
            ip_address=t.ip_address,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in tokens
    ]


def revoke_session_by_id(db: Session, user: User, session_id: int) -> None:
    """
    Revoke a single session owned by the calling user.

    Raises `SessionNotFoundError` if the session is unknown, already
    revoked, or owned by a different user — the route maps all three to
    a uniform 404 to defeat session-id enumeration across users.

    Commits the revocation directly (single-row update); no `db_transaction`
    wrapper used here because the SQLAlchemy `relationship`-driven cascade
    is intentionally minimal.
    """
    token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.id == session_id,
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .first()
    )
    if token is None:
        raise SessionNotFoundError(f"session_id={session_id}")

    token.revoked_at = datetime.now(UTC)
    db.commit()

    log_secure_operation(
        "session_revoked",
        f"Session {session_id} revoked by user {user.id}",
    )


def revoke_all_user_sessions(db: Session, user: User) -> int:
    """
    Bulk-revoke every active session for the calling user.

    Returns the count revoked. Wraps the existing
    `auth._revoke_all_user_tokens` helper so the count semantics stay
    identical to the legacy behavior.
    """
    count = _revoke_all_user_tokens(db, user.id)
    log_secure_operation(
        "all_sessions_revoked",
        f"User {user.id} revoked all {count} sessions",
    )
    return count
