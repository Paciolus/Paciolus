"""Cross-worker preview purge requests (Sprint 879d, review DH-07).

The preview cache (``shared/preflight_cache.py``) lives in each worker's memory.
Logout or account deletion handled by one worker purges that worker at once and
writes a row here; every other worker's sweeper drops the user's older previews
on its next tick. Rows older than the cache lifetime are deleted by the sweep.

ZERO-STORAGE: user id and time. No foreign key — a deleted account's request
must outlive the account row for up to 10 minutes.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class PreviewPurgeRequest(Base):
    """Drop this user's cached previews created before ``requested_at``."""

    __tablename__ = "preview_purge_requests"
    __table_args__ = (Index("ix_preview_purge_requests_requested_at", "requested_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<PreviewPurgeRequest(user_id={self.user_id}, at={self.requested_at})>"
