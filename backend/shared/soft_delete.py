"""
Soft-delete infrastructure for audit-history immutability — Phase XLVI, Sprint 345.

Protected tables (audit trail):
  - activity_logs
  - diagnostic_summaries
  - tool_runs
  - follow_up_items
  - follow_up_item_comments

These tables are append-only at the application level.  Physical deletion
via ``db.delete()`` is blocked by an ORM-level ``before_flush`` guard that
raises ``AuditImmutabilityError``.  All "delete" operations are converted
to soft-delete (setting ``archived_at``).

Non-protected tables (security tokens, sessions, users, clients) are
unaffected — physical cleanup is correct for those.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, event
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------


class SoftDeleteMixin:
    """Mixin adding soft-delete columns to audit-trail models.

    Columns:
      archived_at   — NULL means active; non-NULL means archived
      archived_by   — FK to users.id (NULL for system/retention jobs)
      archive_reason — machine-readable tag (e.g. "user_deletion", "retention_policy")
    """

    archived_at = Column(DateTime, nullable=True, index=True)
    archived_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    archive_reason = Column(String(255), nullable=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def soft_delete(
    db: Session,
    record: SoftDeleteMixin,
    user_id: int | None,
    reason: str,
) -> None:
    """Archive a single record (set archived_at/by/reason) and commit."""
    record.archived_at = datetime.now(UTC)  # type: ignore[assignment]
    record.archived_by = user_id  # type: ignore[assignment]
    record.archive_reason = reason  # type: ignore[assignment]
    db.commit()


def soft_delete_bulk(
    db: Session,
    query: Any,
    user_id: int | None,
    reason: str,
) -> int:
    """Bulk-archive rows matching *query*.  Returns count of rows updated.

    Uses SQLAlchemy ``.update()`` for efficiency.
    Caller should pass a query already filtered to active rows.
    """
    now = datetime.now(UTC)
    count: int = query.update(
        {
            "archived_at": now,
            "archived_by": user_id,
            "archive_reason": reason,
        },
        synchronize_session=False,
    )
    if count > 0:
        db.commit()
    return count


def active_only(query: Any, model: Any) -> Any:
    """Append ``WHERE model.archived_at IS NULL`` to a query."""
    return query.filter(model.archived_at.is_(None))


# ---------------------------------------------------------------------------
# ORM deletion guard
# ---------------------------------------------------------------------------


class AuditImmutabilityError(RuntimeError):
    """Raised when application code attempts ``db.delete()`` on a protected model."""


# Set of model classes that must never be physically deleted
_PROTECTED_MODELS: set[type] = set()


def register_deletion_guard(protected_models: list[type]) -> None:
    """Register a ``before_flush`` listener that blocks ``db.delete()`` on
    any of the *protected_models*.

    Call once at application startup (main.py lifespan) and once in the
    test conftest to ensure coverage.
    """
    _PROTECTED_MODELS.update(protected_models)
    # The listener is idempotent — SQLAlchemy deduplicates identical
    # (target, identifier, fn) triples, but we guard anyway.
    if not event.contains(Session, "before_flush", _guard_before_flush):
        event.listen(Session, "before_flush", _guard_before_flush)


def _guard_before_flush(session: Session, flush_context: Any, instances: Any) -> None:
    """Intercept pending deletions and raise for protected models."""
    for obj in list(session.deleted):
        if type(obj) in _PROTECTED_MODELS:
            raise AuditImmutabilityError(
                f"Physical deletion of {type(obj).__name__} is forbidden. Use soft_delete() instead."
            )
