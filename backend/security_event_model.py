"""Security event log (Sprint 840 — claims review S5).

Before this table, every security event went to ``log_secure_operation``,
which appended to a 1,000-entry in-memory list per worker that nothing ever
read. Failed logins, lockouts, refresh-token reuse and impersonation starts
vanished on every restart, while the Audit Logging Policy described them as
retained.

Rows hold no customer financial data: an event type, the user it concerns, a
SHA-256 of the client IP (never the raw address) and a short detail string
built from IDs and counts. Emails are masked before they get here.

Retention: ``retention_cleanup.purge_old_security_events`` deletes rows older
than ``SECURITY_EVENT_RETENTION_DAYS``. This is an operational security log,
not an audit-trail table, so it is not under the soft-delete guard.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

SECURITY_EVENT_RETENTION_DAYS = 365


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<SecurityEvent(type={self.event_type}, user={self.user_id}, at={self.created_at})>"
