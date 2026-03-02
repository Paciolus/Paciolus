"""
ExportShare model — Phase LXIX: Pricing v3 (Phase 6).

Temporary shared export links for Professional+ tiers.
Export data (PDF/Excel/CSV bytes) stored temporarily with a 48h TTL.
Auto-purged by cleanup scheduler.

ZERO-STORAGE NOTE: This stores rendered export ARTIFACTS (cached outputs),
NOT source financial data. All records auto-expire within 48 hours.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, func
from sqlalchemy.schema import ForeignKey

from database import Base

SHARE_EXPIRY_HOURS = 48


class ExportShare(Base):
    """Temporary export share link with cached export data."""

    __tablename__ = "export_shares"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Token stored as SHA-256 hash
    share_token_hash = Column(String(64), unique=True, index=True, nullable=False)

    # Export metadata
    tool_name = Column(String(100), nullable=False)
    export_format = Column(String(20), nullable=False)  # pdf, xlsx, csv

    # Cached export bytes (auto-purged after 48h)
    export_data = Column(LargeBinary, nullable=False)

    # Metadata
    shared_by_name = Column(String(255), nullable=True)

    # Timestamps & lifecycle
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    expires_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC) + timedelta(hours=SHARE_EXPIRY_HOURS),
        nullable=False,
    )
    revoked_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response (excludes export_data bytes)."""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "export_format": self.export_format,
            "shared_by_name": self.shared_by_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "access_count": self.access_count,
        }
