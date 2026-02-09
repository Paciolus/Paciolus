"""
Engagement and ToolRun models for Phase X Engagement Layer.

ZERO-STORAGE EXCEPTION: This module stores ONLY:
- Engagement metadata (client_id, period, status, materiality parameters)
- Tool run metadata (tool_name, run_number, composite_score, timestamp)

Financial data (account numbers, amounts, transactions) is NEVER persisted.
"""

from datetime import datetime, UTC
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship

from database import Base


class EngagementStatus(str, PyEnum):
    """Engagement lifecycle status."""
    ACTIVE = "active"
    ARCHIVED = "archived"


class MaterialityBasis(str, PyEnum):
    """Basis for materiality calculation."""
    REVENUE = "revenue"
    ASSETS = "assets"
    MANUAL = "manual"


class ToolName(str, PyEnum):
    """Tool identifiers matching the tool suite."""
    TRIAL_BALANCE = "trial_balance"
    MULTI_PERIOD = "multi_period"
    JOURNAL_ENTRY_TESTING = "journal_entry_testing"
    AP_TESTING = "ap_testing"
    BANK_RECONCILIATION = "bank_reconciliation"
    PAYROLL_TESTING = "payroll_testing"
    THREE_WAY_MATCH = "three_way_match"
    REVENUE_TESTING = "revenue_testing"
    AR_AGING = "ar_aging"
    FIXED_ASSET_TESTING = "fixed_asset_testing"


class ToolRunStatus(str, PyEnum):
    """Outcome of a tool run."""
    COMPLETED = "completed"
    FAILED = "failed"


class Engagement(Base):
    """
    Engagement model — metadata-only wrapper tying tool runs to a client+period.

    PROHIBITED fields (AccountingExpertAuditor guardrail):
    - risk_level, audit_opinion, control_effectiveness
    - Any field storing financial data (amounts, account numbers, PII)
    """
    __tablename__ = "engagements"

    id = Column(Integer, primary_key=True, index=True)

    # Client link (RESTRICT: cannot delete client with active engagements)
    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    client = relationship("Client", backref="engagements")

    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Status
    status = Column(
        Enum(EngagementStatus),
        default=EngagementStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Materiality parameters
    materiality_basis = Column(Enum(MaterialityBasis), nullable=True)
    materiality_percentage = Column(Float, nullable=True)
    materiality_amount = Column(Float, nullable=True)
    performance_materiality_factor = Column(Float, default=0.75, nullable=False)
    trivial_threshold_factor = Column(Float, default=0.05, nullable=False)

    # Audit trail
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", backref="engagements")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Tool runs (CASCADE: deleting engagement removes its tool runs)
    tool_runs = relationship("ToolRun", back_populates="engagement", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Engagement(id={self.id}, client_id={self.client_id}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "status": self.status.value if self.status else None,
            "materiality_basis": self.materiality_basis.value if self.materiality_basis else None,
            "materiality_percentage": self.materiality_percentage,
            "materiality_amount": self.materiality_amount,
            "performance_materiality_factor": self.performance_materiality_factor,
            "trivial_threshold_factor": self.trivial_threshold_factor,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ToolRun(Base):
    """
    Record of a single tool execution within an engagement.
    Stores only metadata — never financial results.
    """
    __tablename__ = "tool_runs"

    id = Column(Integer, primary_key=True, index=True)

    # Engagement link (CASCADE: removed with engagement)
    engagement_id = Column(
        Integer,
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement = relationship("Engagement", back_populates="tool_runs")

    # Tool identification
    tool_name = Column(Enum(ToolName), nullable=False, index=True)
    run_number = Column(Integer, nullable=False)  # Auto-incremented per engagement+tool

    # Outcome
    status = Column(Enum(ToolRunStatus), nullable=False)
    composite_score = Column(Float, nullable=True)  # 0-100 for testing tools, None for others

    # Timestamp
    run_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)

    # Composite index for efficient run_number queries
    __table_args__ = (
        Index("ix_tool_runs_engagement_tool", "engagement_id", "tool_name"),
    )

    def __repr__(self):
        return f"<ToolRun(id={self.id}, engagement_id={self.engagement_id}, tool={self.tool_name}, run={self.run_number})>"

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "engagement_id": self.engagement_id,
            "tool_name": self.tool_name.value if self.tool_name else None,
            "run_number": self.run_number,
            "status": self.status.value if self.status else None,
            "composite_score": self.composite_score,
            "run_at": self.run_at.isoformat() if self.run_at else None,
        }
