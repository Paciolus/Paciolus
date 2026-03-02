"""
FirmBranding model — Phase LXIX: Pricing v3 (Phase 8).

Custom PDF branding for Enterprise tier.
Logo stored as S3 key reference (not in database).

ZERO-STORAGE NOTE: Only stores branding CONFIG metadata
(S3 key, header/footer text). No financial data.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.schema import ForeignKey

from database import Base


class FirmBranding(Base):
    """Firm branding configuration for custom PDF generation."""

    __tablename__ = "firm_branding"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Logo stored in S3
    logo_s3_key = Column(String(500), nullable=True)
    logo_content_type = Column(String(50), nullable=True)
    logo_size_bytes = Column(Integer, nullable=True)

    # Text branding
    header_text = Column(String(200), nullable=True)
    footer_text = Column(String(300), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "has_logo": self.logo_s3_key is not None,
            "logo_content_type": self.logo_content_type,
            "logo_size_bytes": self.logo_size_bytes,
            "header_text": self.header_text,
            "footer_text": self.footer_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
