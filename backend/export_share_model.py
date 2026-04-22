"""
ExportShare model — Phase LXIX: Pricing v3 (Phase 6).

Temporary shared export links for Professional+ tiers.
Export data (PDF/Excel/CSV bytes) stored temporarily with tier-configurable TTL.
Auto-purged by cleanup scheduler.

ZERO-STORAGE NOTE: This stores rendered export ARTIFACTS (cached outputs),
NOT source financial data. All records auto-expire within 24–48 hours.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import Boolean, DateTime, Integer, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import ForeignKey

from database import Base

DEFAULT_SHARE_EXPIRY_HOURS = 24


class ExportShare(Base):
    """Temporary export share link with cached export data."""

    __tablename__ = "export_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )

    # Token stored as SHA-256 hash
    share_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # Export metadata
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    export_format: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, xlsx, csv

    # Cached export bytes (auto-purged after TTL)
    export_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    # Security: optional passcode protection.
    # Historically a 64-char SHA-256 hex hash; as of 2026-04-20 this column
    # stores bcrypt hashes (~60 chars, salt built in).  Column widened to 255
    # to accommodate the new format.  Mixed-format rows are rejected at
    # verification time — SHA-256 rows from pre-migration shares are
    # invalidated and must be re-created (shares are ephemeral, ≤48h TTL).
    passcode_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Brute-force protection for passcode-protected shares (2026-04-20).
    # Tracks consecutive failed passcode attempts and an absolute lockout
    # timestamp.  Lockout is token-scoped, not global — one attacker
    # brute-forcing one share cannot lock out another share's legitimate
    # owner.
    passcode_failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passcode_locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Single-use: auto-revoke after first download
    single_use: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Metadata
    shared_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps & lifecycle
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC) + timedelta(hours=DEFAULT_SHARE_EXPIRY_HOURS),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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
            "single_use": self.single_use,
            "has_passcode": self.passcode_hash is not None,
        }
