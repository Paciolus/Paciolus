"""
Admin audit log model — Sprint 590: Internal admin console.

Append-only audit trail for all superadmin actions on customer accounts.
Every admin action (plan override, trial extension, credit, refund,
cancellation, impersonation) creates a record here.

ZERO-STORAGE COMPLIANT: No financial data. Only action metadata.
"""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class AdminActionType(str, PyEnum):
    """Taxonomy of admin actions for audit trail."""

    PLAN_OVERRIDE = "plan_override"
    TRIAL_EXTENSION = "trial_extension"
    CREDIT_ISSUED = "credit_issued"
    REFUND_ISSUED = "refund_issued"
    FORCE_CANCEL = "force_cancel"
    IMPERSONATION_START = "impersonation_start"
    IMPERSONATION_END = "impersonation_end"
    SESSION_REVOKE = "session_revoke"


class AdminAuditLog(Base):
    """Append-only admin action audit trail.

    Every superadmin action on a customer account is recorded here.
    """

    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Who performed the action
    admin_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    admin_user: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[admin_user_id]
    )

    # What action was taken
    action_type: Mapped[AdminActionType] = mapped_column(Enum(AdminActionType), nullable=False, index=True)

    # Target of the action (nullable — some actions may be system-wide)
    target_org_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    target_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Action details (JSON string — reason, old/new values, etc.)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Request context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AdminAuditLog(id={self.id}, action={self.action_type}, "
            f"admin={self.admin_user_id}, target_org={self.target_org_id})>"
        )
