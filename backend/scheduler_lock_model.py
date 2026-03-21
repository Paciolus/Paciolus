"""
Scheduler lock model for preventing multi-worker job duplication.

AUDIT-06 FIX 3: DB-backed execution lock for APScheduler jobs.

When running under Gunicorn with WEB_CONCURRENCY > 1, every worker starts
its own APScheduler instance. Without coordination, all jobs run N times.
This table provides a distributed lock so only one worker executes each job.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SchedulerLock(Base):
    """DB-backed lock for scheduler job deduplication across workers."""

    __tablename__ = "scheduler_locks"

    job_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    locked_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    locked_by: Mapped[str] = mapped_column(String(100), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<SchedulerLock(job={self.job_name}, by={self.locked_by}, expires={self.expires_at})>"
