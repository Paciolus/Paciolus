"""
TeamActivityLog model — Phase LXIX: Pricing v3 (Phase 7).

Lightweight activity log for team-level visibility.
90-day auto-purge via cleanup scheduler.

ZERO-STORAGE NOTE: Stores action metadata only — no financial data.
File identifiers are SHA-256 hashed.
"""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Index, Integer, String, func
from sqlalchemy.schema import ForeignKey

from database import Base


class TeamActionType(str, PyEnum):
    """Types of team activity events."""

    UPLOAD = "upload"
    EXPORT = "export"
    SHARE = "share"
    LOGIN = "login"


class TeamActivityLog(Base):
    """Team-level activity record for admin dashboard."""

    __tablename__ = "team_activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    action_type = Column(Enum(TeamActionType), nullable=False)
    tool_name = Column(String(100), nullable=True)
    file_identifier_hash = Column(String(64), nullable=True)  # SHA-256 of filename

    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    # Composite index for admin dashboard date-range queries
    __table_args__ = (Index("ix_team_activity_org_created", "organization_id", "created_at"),)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "action_type": self.action_type.value if self.action_type else None,
            "tool_name": self.tool_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
