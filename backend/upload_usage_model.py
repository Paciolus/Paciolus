"""Server-side upload usage ledger (Sprint 878, review AZ-05).

One row per successful metered analysis run by a user who has no active
metered subscription (Free, or a lapsed plan). The monthly allowance for those
users is the number of rows in the current calendar month.

It replaced counting ``ActivityLog`` rows, which the browser writes itself in a
separate request and which "Clear history" archives - so skipping the log call
or clearing history reset the allowance. This table is written only by
``shared.entitlement_checks.increment_upload_count`` and is never archived,
updated or deleted by any user-facing route. Account erasure removes it with
the account.

ZERO-STORAGE: user id, tool name and time. Nothing from the uploaded file.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class UploadUsageEvent(Base):
    """One unit of upload allowance consumed."""

    __tablename__ = "upload_usage_events"
    __table_args__ = (Index("ix_upload_usage_events_user_consumed", "user_id", "consumed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC).replace(tzinfo=None), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<UploadUsageEvent(user_id={self.user_id}, tool={self.tool_name}, at={self.consumed_at})>"
