"""
Analytical Expectation model — Sprint 728a (ISA 520).

Captures the auditor's *workpaper* for an analytical procedure:
expected value, precision threshold, corroboration basis, and (once
evaluated) the actual result + variance + within/exceeds status.

ZERO-STORAGE EXCEPTION: This module stores ONLY auditor-supplied
expectations and the platform-recorded comparison result. Underlying
trial-balance / flux / ratio data remains ephemeral.

ISA 520 §A4–A8 treats analytical procedures as evidence the auditor
must document — expectation, precision, basis, conclusion. The entity
is a structured workpaper, not a database join over tool output.
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from shared.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from engagement_model import Engagement
    from models import User


class ExpectationTargetType(str, PyEnum):
    """What the analytical procedure targets."""

    ACCOUNT = "account"
    BALANCE = "balance"
    RATIO = "ratio"
    FLUX_LINE = "flux_line"


class ExpectationCorroborationTag(str, PyEnum):
    """Categories of corroboration basis (ISA 520 §A12-A13)."""

    INDUSTRY_DATA = "industry_data"
    PRIOR_PERIOD = "prior_period"
    BUDGET = "budget"
    REGRESSION_MODEL = "regression_model"
    OTHER = "other"


class ExpectationResultStatus(str, PyEnum):
    """Evaluation outcome — set when the actual value is captured."""

    NOT_EVALUATED = "not_evaluated"
    WITHIN_THRESHOLD = "within_threshold"
    EXCEEDS_THRESHOLD = "exceeds_threshold"


VALID_CORROBORATION_TAGS = {tag.value for tag in ExpectationCorroborationTag}


class AnalyticalExpectation(SoftDeleteMixin, Base):
    """
    ISA 520 analytical-procedure expectation workpaper.

    PROHIBITED fields (zero-storage guardrail):
    - account_number, account_name, transaction_id, vendor_name, employee_name
    - amount as raw transactional data (we store only the auditor's expected
      and recorded actual — both are summaries, not transaction-level data).
    """

    __tablename__ = "analytical_expectations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Engagement link (CASCADE: removed with engagement)
    engagement_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement: Mapped["Engagement"] = relationship("Engagement", back_populates="analytical_expectations")

    # What the expectation targets
    procedure_target_type: Mapped[ExpectationTargetType] = mapped_column(
        Enum(ExpectationTargetType), nullable=False, index=True
    )
    procedure_target_label: Mapped[str] = mapped_column(String(200), nullable=False)

    # Expected values — the auditor provides EITHER an expected_value OR a
    # range (low+high). XOR enforced at the manager layer.
    expected_value: Mapped[Decimal | None] = mapped_column(Numeric(19, 2), nullable=True)
    expected_range_low: Mapped[Decimal | None] = mapped_column(Numeric(19, 2), nullable=True)
    expected_range_high: Mapped[Decimal | None] = mapped_column(Numeric(19, 2), nullable=True)

    # Precision threshold — XOR (amount OR percent, not both). Enforced at
    # the manager layer.
    precision_threshold_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 2), nullable=True)
    precision_threshold_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Corroboration basis (ISA 520 §A12-A13)
    corroboration_basis_text: Mapped[str] = mapped_column(Text, nullable=False)
    corroboration_tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Auditor notes
    cpa_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Result — populated when the actual is captured (manually or via 728c
    # tool-wiring auto-persist).
    result_actual_value: Mapped[Decimal | None] = mapped_column(Numeric(19, 2), nullable=True)
    result_variance_amount: Mapped[Decimal | None] = mapped_column(Numeric(19, 2), nullable=True)
    result_status: Mapped[ExpectationResultStatus] = mapped_column(
        Enum(ExpectationResultStatus),
        nullable=False,
        default=ExpectationResultStatus.NOT_EVALUATED,
        index=True,
    )

    # Audit trail
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])

    __table_args__ = (Index("ix_analytical_expectations_eng_status", "engagement_id", "result_status"),)

    def __repr__(self) -> str:
        target_val = self.procedure_target_type.value if self.procedure_target_type else "?"
        status_val = self.result_status.value if self.result_status else "?"
        return (
            f"<AnalyticalExpectation(id={self.id}, "
            f"engagement_id={self.engagement_id}, "
            f"target={target_val}/{self.procedure_target_label}, "
            f"status={status_val})>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        import json

        try:
            tags = json.loads(self.corroboration_tags_json) if self.corroboration_tags_json else []
        except (ValueError, TypeError):
            tags = []

        return {
            "id": self.id,
            "engagement_id": self.engagement_id,
            "procedure_target_type": (self.procedure_target_type.value if self.procedure_target_type else None),
            "procedure_target_label": self.procedure_target_label,
            "expected_value": (str(self.expected_value) if self.expected_value is not None else None),
            "expected_range_low": (str(self.expected_range_low) if self.expected_range_low is not None else None),
            "expected_range_high": (str(self.expected_range_high) if self.expected_range_high is not None else None),
            "precision_threshold_amount": (
                str(self.precision_threshold_amount) if self.precision_threshold_amount is not None else None
            ),
            "precision_threshold_percent": self.precision_threshold_percent,
            "corroboration_basis_text": self.corroboration_basis_text,
            "corroboration_tags": tags,
            "cpa_notes": self.cpa_notes,
            "result_actual_value": (str(self.result_actual_value) if self.result_actual_value is not None else None),
            "result_variance_amount": (
                str(self.result_variance_amount) if self.result_variance_amount is not None else None
            ),
            "result_status": self.result_status.value if self.result_status else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "archived_by": self.archived_by,
            "archive_reason": self.archive_reason,
        }
