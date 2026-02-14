"""
Follow-Up Items model for Phase X Engagement Layer.

ZERO-STORAGE EXCEPTION: This module stores ONLY:
- Narrative descriptions (text summaries, never account numbers or amounts)
- Severity classification (high/medium/low)
- Disposition tracking (auditor workflow state)
- Auditor notes (free-text commentary)

PROHIBITED (AccountingExpertAuditor Guardrail 2):
- account_number, account_name, amount, debit, credit
- transaction_id, entry_id, vendor_name, employee_name
- Any personally identifiable information (PII)
"""

from datetime import datetime, UTC
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship, backref

from database import Base


class FollowUpSeverity(str, PyEnum):
    """Severity level for follow-up items."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FollowUpDisposition(str, PyEnum):
    """Auditor disposition workflow states."""
    NOT_REVIEWED = "not_reviewed"
    INVESTIGATED_NO_ISSUE = "investigated_no_issue"
    INVESTIGATED_ADJUSTMENT_POSTED = "investigated_adjustment_posted"
    INVESTIGATED_FURTHER_REVIEW = "investigated_further_review"
    IMMATERIAL = "immaterial"


class FollowUpItem(Base):
    """
    Follow-up item — narrative-only anomaly tracker tied to an engagement.

    PROHIBITED fields (AccountingExpertAuditor guardrail):
    - account_number, account_name, amount, debit, credit
    - transaction_id, entry_id, vendor_name, employee_name
    - Any field storing financial data or PII
    """
    __tablename__ = "follow_up_items"

    id = Column(Integer, primary_key=True, index=True)

    # Engagement link (CASCADE: removed with engagement)
    engagement_id = Column(
        Integer,
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement = relationship("Engagement", backref=backref("follow_up_items", passive_deletes=True))

    # Optional link to the specific tool run that generated this item
    tool_run_id = Column(
        Integer,
        ForeignKey("tool_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tool_run = relationship("ToolRun", backref="follow_up_items")

    # Narrative description — NEVER embed account numbers or dollar amounts
    description = Column(Text, nullable=False)

    # Source tool that generated this item
    tool_source = Column(String(50), nullable=False, index=True)

    # Severity classification
    severity = Column(
        Enum(FollowUpSeverity),
        nullable=False,
        default=FollowUpSeverity.MEDIUM,
        index=True,
    )

    # Auditor disposition
    disposition = Column(
        Enum(FollowUpDisposition),
        nullable=False,
        default=FollowUpDisposition.NOT_REVIEWED,
        index=True,
    )

    # Auditor free-text notes
    auditor_notes = Column(Text, nullable=True)

    # Assignment — nullable FK to user (Sprint 113)
    assigned_to = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Composite index for efficient filtering
    __table_args__ = (
        Index("ix_follow_up_engagement_severity", "engagement_id", "severity"),
        Index("ix_follow_up_engagement_disposition", "engagement_id", "disposition"),
    )

    def __repr__(self) -> str:
        return f"<FollowUpItem(id={self.id}, engagement_id={self.engagement_id}, severity={self.severity})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "engagement_id": self.engagement_id,
            "tool_run_id": self.tool_run_id,
            "description": self.description,
            "tool_source": self.tool_source,
            "severity": self.severity.value if self.severity else None,
            "disposition": self.disposition.value if self.disposition else None,
            "auditor_notes": self.auditor_notes,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FollowUpItemComment(Base):
    """
    Threaded comment on a follow-up item.

    Supports flat and nested (parent_comment_id) comment threads.
    Stores ONLY narrative text — no financial data, account numbers, or PII.

    Sprint 112: Finding Comments — Backend Model.
    """
    __tablename__ = "follow_up_item_comments"

    id = Column(Integer, primary_key=True, index=True)

    # Follow-up item link (CASCADE: removed with item)
    follow_up_item_id = Column(
        Integer,
        ForeignKey("follow_up_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    follow_up_item = relationship(
        "FollowUpItem",
        backref=backref("comments", passive_deletes=True, cascade="all, delete-orphan"),
    )

    # Author
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author = relationship("User")

    # Comment text — NEVER embed account numbers, amounts, or PII
    comment_text = Column(Text, nullable=False)

    # Threading — nullable self-FK for nested replies
    parent_comment_id = Column(
        Integer,
        ForeignKey("follow_up_item_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    replies = relationship(
        "FollowUpItemComment",
        backref=backref("parent", remote_side="FollowUpItemComment.id"),
        cascade="all, delete-orphan",
    )

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Composite index for efficient thread queries
    __table_args__ = (
        Index("ix_comment_item_parent", "follow_up_item_id", "parent_comment_id"),
    )

    def __repr__(self) -> str:
        return f"<FollowUpItemComment(id={self.id}, item_id={self.follow_up_item_id}, user_id={self.user_id})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "follow_up_item_id": self.follow_up_item_id,
            "user_id": self.user_id,
            "author_name": self.author.name if self.author else None,
            "comment_text": self.comment_text,
            "parent_comment_id": self.parent_comment_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
