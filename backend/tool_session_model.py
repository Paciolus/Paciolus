"""
Tool Session model — Sprint 262, Packet 2

DB-backed session storage for tool state (adjustments, currency rates).
Replaces in-memory dicts that break across Gunicorn workers.

ZERO-STORAGE: Sessions expire via TTL (lazy + startup cleanup).
Financial line data (account names, debit/credit amounts) is stripped
before DB persistence; only workflow metadata is stored.
"""

import json
import logging
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Session

from database import Base

logger = logging.getLogger(__name__)

# TTL defaults (in seconds) per tool
TOOL_SESSION_TTLS: dict[str, int] = {
    "adjustments": 3600,      # 1 hour
    "currency_rates": 7200,   # 2 hours
}
DEFAULT_TTL_SECONDS = 3600

# =============================================================================
# FINANCIAL DATA SANITIZATION (Packet 2)
# =============================================================================

# Keys that indicate raw financial content — must never reach the DB.
# Defense-in-depth: recursively stripped from ALL tool session payloads.
FORBIDDEN_FINANCIAL_KEYS: frozenset[str] = frozenset({
    "account_name", "debit", "credit", "amount",
    "unadjusted_debit", "unadjusted_credit", "unadjusted_balance",
    "adjustment_debit", "adjustment_credit", "net_adjustment",
    "adjusted_debit", "adjusted_credit", "adjusted_balance",
})

# Per-entry keys stripped from adjustments sessions (contain line-level data)
_ADJUSTMENT_ENTRY_STRIP_KEYS: frozenset[str] = frozenset({
    "lines", "total_debits", "total_credits", "entry_total",
})

# Top-level keys stripped from adjustments sessions (aggregate financial totals)
_ADJUSTMENT_SET_STRIP_KEYS: frozenset[str] = frozenset({
    "total_adjustment_amount",
})

# Allowlist: ONLY these keys may appear in persisted adjustment session payloads.
# Any key NOT on these lists is stripped before DB write.
# Update these lists when adding new workflow metadata fields to AdjustingEntry/AdjustmentSet.
ALLOWED_ADJUSTMENT_ENTRY_KEYS: frozenset[str] = frozenset({
    "id", "reference", "description", "adjustment_type", "status",
    "account_count", "is_balanced",
    "prepared_by", "reviewed_by",
    "created_at", "updated_at",
    "notes", "is_reversing",
})

ALLOWED_ADJUSTMENT_SET_KEYS: frozenset[str] = frozenset({
    "entries",
    "total_adjustments", "proposed_count", "approved_count",
    "rejected_count", "posted_count",
    "period_label", "client_name", "created_at",
})


def _sanitize_adjustments_data(data: dict) -> dict:
    """Remove financial line data from adjustment session payload.

    Uses an ALLOWLIST approach: only explicitly permitted keys survive.
    This prevents new financial fields from leaking through if the
    AdjustingEntry/AdjustmentSet model evolves.

    Permitted entry keys: id, reference, description, adjustment_type, status,
    account_count, is_balanced, prepared_by, reviewed_by, created_at, updated_at,
    notes, is_reversing.

    Stripped: lines array, total_debits, total_credits, entry_total,
    total_adjustment_amount, and any future unlisted keys.

    See Sprint 262 (DB-backed sessions) and Sprint 279 (defense-in-depth).
    """
    sanitized = {k: v for k, v in data.items() if k in ALLOWED_ADJUSTMENT_SET_KEYS}
    if "entries" in sanitized:
        sanitized["entries"] = [
            {k: v for k, v in entry.items() if k in ALLOWED_ADJUSTMENT_ENTRY_KEYS}
            for entry in sanitized["entries"]
        ]
    return sanitized


def _strip_forbidden_keys_recursive(data: Any) -> Any:
    """Recursively strip forbidden financial keys from any data structure.

    Defense-in-depth: catches any financial content that per-tool
    sanitizers may have missed.
    """
    if isinstance(data, dict):
        return {
            k: _strip_forbidden_keys_recursive(v)
            for k, v in data.items()
            if k not in FORBIDDEN_FINANCIAL_KEYS
        }
    if isinstance(data, list):
        return [_strip_forbidden_keys_recursive(item) for item in data]
    return data


def _sanitize_session_data(tool_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize session data before DB persistence — data minimization boundary.

    This is the Zero-Storage enforcement point for tool sessions.
    Financial line data (account names, debit/credit amounts, entry totals)
    must never reach the database. Only workflow metadata (IDs, references,
    statuses, timestamps, reviewer info) is persisted.

    Two-layer defense:
    1. Per-tool ALLOWLIST: Only explicitly permitted keys survive (adjustments).
       New fields added to to_dict() are blocked by default unless allowlisted.
    2. Recursive FORBIDDEN_FINANCIAL_KEYS check: Catches any remaining
       financial content in any tool's payload (defense-in-depth).

    History: Sprint 262 (DB-backed sessions), Sprint 279 (defense-in-depth),
    Sprint 301 (allowlist enforcement).
    """
    if tool_name == "adjustments":
        sanitized = _sanitize_adjustments_data(data)
    else:
        sanitized = data

    return _strip_forbidden_keys_recursive(sanitized)


class ToolSession(Base):
    """Ephemeral per-user per-tool session data, stored as JSON."""
    __tablename__ = "tool_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name = Column(String(50), nullable=False)
    session_data = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "tool_name", name="uq_tool_session_user_tool"),
    )

    def __repr__(self) -> str:
        return f"<ToolSession(id={self.id}, user_id={self.user_id}, tool={self.tool_name})>"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_ttl(tool_name: str) -> int:
    """Get TTL in seconds for a given tool name."""
    return TOOL_SESSION_TTLS.get(tool_name, DEFAULT_TTL_SECONDS)


def _is_expired(updated_at: Optional[datetime], tool_name: str) -> bool:
    """Check if a session is expired based on its updated_at timestamp."""
    if updated_at is None:
        return True
    # Handle tz-naive datetimes from SQLite
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    ttl = _get_ttl(tool_name)
    return (datetime.now(UTC) - updated_at).total_seconds() > ttl


def load_tool_session(
    db: Session,
    user_id: int,
    tool_name: str,
) -> Optional[dict[str, Any]]:
    """Load a tool session from the DB.

    Returns None if missing or expired.
    Lazy cleanup: expired sessions are deleted on read.
    """
    row = db.query(ToolSession).filter_by(
        user_id=user_id, tool_name=tool_name,
    ).first()

    if row is None:
        return None

    if _is_expired(row.updated_at, tool_name):
        db.delete(row)
        db.commit()
        return None

    return json.loads(row.session_data)


def _save_fallback(
    db: Session,
    user_id: int,
    tool_name: str,
    serialized: str,
    now: datetime,
) -> None:
    """Generic upsert fallback for dialects without native ON CONFLICT support."""
    existing = db.query(ToolSession).filter_by(
        user_id=user_id, tool_name=tool_name,
    ).first()
    if existing:
        existing.session_data = serialized
        existing.updated_at = now
    else:
        db.add(ToolSession(
            user_id=user_id,
            tool_name=tool_name,
            session_data=serialized,
            updated_at=now,
        ))
    db.commit()


def save_tool_session(
    db: Session,
    user_id: int,
    tool_name: str,
    data: dict[str, Any],
) -> None:
    """Save (upsert) a tool session. Dialect-aware: native upsert for SQLite/PostgreSQL, fallback for others.

    Financial data is sanitized before persistence (Packet 2).
    """
    now = datetime.now(UTC)
    data = _sanitize_session_data(tool_name, data)
    serialized = json.dumps(data)

    bind = db.bind
    if bind is None:
        logger.warning("Session has no bind — using generic upsert fallback")
        _save_fallback(db, user_id, tool_name, serialized, now)
        return

    dialect_name = bind.dialect.name

    if dialect_name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as dialect_insert
    elif dialect_name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
    else:
        _save_fallback(db, user_id, tool_name, serialized, now)
        return

    stmt = dialect_insert(ToolSession).values(
        user_id=user_id,
        tool_name=tool_name,
        session_data=serialized,
        updated_at=now,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["user_id", "tool_name"],
        set_={
            "session_data": stmt.excluded.session_data,
            "updated_at": stmt.excluded.updated_at,
        },
    )
    db.execute(stmt)
    db.commit()


def delete_tool_session(
    db: Session,
    user_id: int,
    tool_name: str,
) -> bool:
    """Delete a tool session. Returns True if it existed."""
    deleted = db.query(ToolSession).filter_by(
        user_id=user_id, tool_name=tool_name,
    ).delete()
    db.commit()
    return deleted > 0


def cleanup_expired_tool_sessions(db: Session) -> int:
    """Delete all expired tool sessions. Called at startup."""
    count = 0

    # Clean known tool types with their specific TTLs
    for tool_name, ttl_seconds in TOOL_SESSION_TTLS.items():
        cutoff = datetime.now(UTC) - timedelta(seconds=ttl_seconds)
        deleted = db.query(ToolSession).filter(
            ToolSession.tool_name == tool_name,
            ToolSession.updated_at < cutoff,
        ).delete()
        count += deleted

    # Clean unknown tool types with the default TTL
    known_tools = set(TOOL_SESSION_TTLS.keys())
    if known_tools:
        default_cutoff = datetime.now(UTC) - timedelta(seconds=DEFAULT_TTL_SECONDS)
        deleted = db.query(ToolSession).filter(
            ToolSession.tool_name.notin_(known_tools),
            ToolSession.updated_at < default_cutoff,
        ).delete(synchronize_session=False)
        count += deleted

    if count > 0:
        db.commit()
    return count


def sanitize_existing_sessions(db: Session) -> int:
    """One-time cleanup: sanitize legacy tool_session rows with financial data.

    Reads all rows, applies per-tool sanitization + defense-in-depth stripping,
    and updates any rows whose content changed.  Called at startup.
    Returns the number of rows sanitized.
    """
    count = 0
    rows = db.query(ToolSession).all()
    for row in rows:
        original = json.loads(row.session_data)
        sanitized = _sanitize_session_data(row.tool_name, original)
        new_json = json.dumps(sanitized)
        if new_json != row.session_data:
            row.session_data = new_json
            count += 1
    if count > 0:
        db.commit()
        logger.info("Sanitized %d legacy tool session(s) with financial data", count)
    return count
