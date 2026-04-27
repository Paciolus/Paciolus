"""
Uncorrected Misstatement model — Sprint 729a (ISA 450).

Captures the auditor's Summary of Uncorrected Misstatements (SUM)
workpaper line items. Each row represents one identified misstatement
the auditor decided not to require correction for, classified per
ISA 450 §A2-A4 and dispositioned per ISA 450 §A12-A15.

ZERO-STORAGE EXCEPTION: This module persists only the auditor's
documented decisions. Adjusting entries (in-memory dataclass per
``backend/adjusting_entries.py``) and sample projections remain
ephemeral. The SUM is a snapshot workpaper of audit decisions, not a
database join over raw tool output.
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from shared.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from engagement_model import Engagement
    from models import User


class MisstatementSourceType(str, PyEnum):
    """Where the misstatement was identified (ISA 450 §A4 sources)."""

    ADJUSTING_ENTRY_PASSED = "adjusting_entry_passed"
    SAMPLE_PROJECTION = "sample_projection"
    KNOWN_ERROR = "known_error"


class MisstatementClassification(str, PyEnum):
    """ISA 450 §A6 classification."""

    FACTUAL = "factual"  # Quantitatively certain
    JUDGMENTAL = "judgmental"  # Differences in management judgment
    PROJECTED = "projected"  # Sampling extrapolation


class MisstatementDisposition(str, PyEnum):
    """ISA 450 §A12-A15 auditor disposition."""

    NOT_YET_REVIEWED = "not_yet_reviewed"
    AUDITOR_PROPOSES_CORRECTION = "auditor_proposes_correction"
    AUDITOR_ACCEPTS_AS_IMMATERIAL = "auditor_accepts_as_immaterial"


class MaterialityBucket(str, PyEnum):
    """Aggregate-vs-materiality bucket (computed, not stored)."""

    CLEARLY_TRIVIAL = "clearly_trivial"
    IMMATERIAL = "immaterial"
    APPROACHING_MATERIAL = "approaching_material"
    MATERIAL = "material"


class UncorrectedMisstatement(SoftDeleteMixin, Base):
    """
    ISA 450 SUM-schedule line item.

    Holds the auditor's structured record of a misstatement that was
    identified during the engagement and not corrected — including its
    source, classification, F/S impact, and the auditor's disposition.

    PROHIBITED fields (zero-storage guardrail):
    - account_number, transaction_id, vendor_name, employee_name
    The ``accounts_affected`` JSON column accepts a list of account-name
    strings + amounts at the *summary* level (the auditor's decision
    record), not raw transactional data.
    """

    __tablename__ = "uncorrected_misstatements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Engagement link (CASCADE: removed with engagement)
    engagement_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement: Mapped["Engagement"] = relationship("Engagement", back_populates="uncorrected_misstatements")

    # Source — narrative reference to the AJE / sample / known-error
    source_type: Mapped[MisstatementSourceType] = mapped_column(
        Enum(MisstatementSourceType), nullable=False, index=True
    )
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)

    # Description (1–2 sentences summarizing the misstatement)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Accounts affected — JSON list of {account: str, debit_credit: "DR"|"CR", amount: str}
    accounts_affected_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    # Classification (ISA 450 §A6)
    classification: Mapped[MisstatementClassification] = mapped_column(
        Enum(MisstatementClassification), nullable=False, index=True
    )

    # F/S impact — signed (positive = overstates target line; negative = understates)
    fs_impact_net_income: Mapped[Decimal] = mapped_column(Numeric(19, 2), nullable=False, default=Decimal("0.00"))
    fs_impact_net_assets: Mapped[Decimal] = mapped_column(Numeric(19, 2), nullable=False, default=Decimal("0.00"))

    # Auditor disposition
    cpa_disposition: Mapped[MisstatementDisposition] = mapped_column(
        Enum(MisstatementDisposition),
        nullable=False,
        default=MisstatementDisposition.NOT_YET_REVIEWED,
        index=True,
    )

    cpa_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    __table_args__ = (
        Index(
            "ix_uncorrected_misstatements_eng_disposition",
            "engagement_id",
            "cpa_disposition",
        ),
        Index(
            "ix_uncorrected_misstatements_eng_classification",
            "engagement_id",
            "classification",
        ),
    )

    def __repr__(self) -> str:
        cls_val = self.classification.value if self.classification else "?"
        disp_val = self.cpa_disposition.value if self.cpa_disposition else "?"
        return (
            f"<UncorrectedMisstatement(id={self.id}, "
            f"engagement_id={self.engagement_id}, "
            f"classification={cls_val}, disposition={disp_val})>"
        )

    def to_dict(self) -> dict[str, Any]:
        import json

        try:
            accounts = json.loads(self.accounts_affected_json) if self.accounts_affected_json else []
        except (ValueError, TypeError):
            accounts = []

        return {
            "id": self.id,
            "engagement_id": self.engagement_id,
            "source_type": self.source_type.value if self.source_type else None,
            "source_reference": self.source_reference,
            "description": self.description,
            "accounts_affected": accounts,
            "classification": self.classification.value if self.classification else None,
            "fs_impact_net_income": (str(self.fs_impact_net_income) if self.fs_impact_net_income is not None else None),
            "fs_impact_net_assets": (str(self.fs_impact_net_assets) if self.fs_impact_net_assets is not None else None),
            "cpa_disposition": (self.cpa_disposition.value if self.cpa_disposition else None),
            "cpa_notes": self.cpa_notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "archived_by": self.archived_by,
            "archive_reason": self.archive_reason,
        }
