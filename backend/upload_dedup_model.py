"""
Upload deduplication model for preventing duplicate trial-balance submissions.

AUDIT-06 FIX 4: SHA-256-based dedup key prevents rapid double-submissions
from executing full analysis runs and duplicating tool-run side effects.

Keys expire after 5 minutes. A periodic cleanup job purges expired rows.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, func

from database import Base


class UploadDedup(Base):
    """Deduplication record for upload endpoints."""

    __tablename__ = "upload_dedup"

    dedup_key = Column(String(255), primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<UploadDedup(key={self.dedup_key[:30]}..., expires={self.expires_at})>"
