"""SQLAlchemy models for users, activity logs, clients, and diagnostic summaries."""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from shared.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from engagement_model import Engagement


class PeriodType(str, PyEnum):
    """Period type for historical trend analysis."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class UserTier(str, PyEnum):
    """User subscription tier for feature access and usage limits.

    Pricing v3 restructure (Phase LXIX):
    - FREE: View-only, 2 tools, no exports
    - SOLO: Individual practitioner ($100/mo)
    - PROFESSIONAL: Small firm ($500/mo, 7 seats)
    - ENTERPRISE: Large firm ($1,000/mo, 20 seats)
    """

    FREE = "free"
    SOLO = "solo"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Industry(str, PyEnum):
    """Standardized industry classification for clients."""

    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    PROFESSIONAL_SERVICES = "professional_services"
    REAL_ESTATE = "real_estate"
    CONSTRUCTION = "construction"
    HOSPITALITY = "hospitality"
    NONPROFIT = "nonprofit"
    EDUCATION = "education"
    OTHER = "other"


class ReportingFramework(str, PyEnum):
    """Authoritative reporting framework for financial statements."""

    AUTO = "auto"  # Resolve from entity_type / jurisdiction
    FASB = "fasb"  # US GAAP (ASC codification)
    GASB = "gasb"  # Governmental accounting standards


class EntityType(str, PyEnum):
    """Legal/organizational classification of the reporting entity."""

    FOR_PROFIT = "for_profit"
    NONPROFIT = "nonprofit"
    GOVERNMENTAL = "governmental"
    OTHER = "other"


class User(Base):
    """User model for authentication. Stores credentials and preferences only."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # User profile
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Display name (optional)

    # User metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # Email verification status

    # Sprint 57: User tier for feature access and usage limits
    tier: Mapped[UserTier] = mapped_column(Enum(UserTier), default=UserTier.FREE, nullable=False)

    # Phase LXIX: Organization membership (user belongs to at most one org)
    # use_alter=True breaks the users↔organizations FK cycle for create_all()/drop_all()
    organization_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("organizations.id", use_alter=True, name="fk_users_organization_id"),
        nullable=True,
        index=True,
    )

    # Sprint 57: Email verification fields
    email_verification_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Sprint 203: Pending email for re-verification on email change
    pending_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), server_default=func.now()
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Sprint 199: Password change tracking for token invalidation
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Sprint 261: DB-backed account lockout (replaces in-memory _lockout_tracker)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # User settings (JSON string) - for future preferences
    # IMPORTANT: This is for UI preferences only, NOT financial data
    settings: Mapped[str] = mapped_column(String(2000), default="{}")

    # Reverse relationships (Sprint 280: backref → back_populates)
    # Sprint 345: foreign_keys needed to disambiguate from SoftDeleteMixin.archived_by FK
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user", foreign_keys="[ActivityLog.user_id]"
    )
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="user")
    diagnostic_summaries: Mapped[list["DiagnosticSummary"]] = relationship(
        "DiagnosticSummary", back_populates="user", foreign_keys="[DiagnosticSummary.user_id]"
    )
    verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship(
        "EmailVerificationToken", back_populates="user"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken", back_populates="user"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="user")
    engagements: Mapped[list["Engagement"]] = relationship(
        "Engagement", back_populates="creator", foreign_keys="[Engagement.created_by]"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email[:10]}...)>"


class ActivityLog(SoftDeleteMixin, Base):
    """Activity log for audit metadata history. Stores aggregate stats only."""

    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # User association (nullable for anonymous audits)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user: Mapped["User"] = relationship("User", back_populates="activity_logs", foreign_keys=[user_id])

    # Audit identification (privacy-preserving)
    filename_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 hash of filename
    filename_display: Mapped[str | None] = mapped_column(String(20), nullable=True)  # First 8 chars + "..." for UI

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), index=True
    )

    # Audit summary metadata (aggregate only - no specific account details)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)  # Number of rows processed
    total_debits: Mapped[Decimal] = mapped_column(Numeric(19, 2), nullable=False)  # Sum of all debits
    total_credits: Mapped[Decimal] = mapped_column(Numeric(19, 2), nullable=False)  # Sum of all credits
    materiality_threshold: Mapped[Decimal] = mapped_column(Numeric(19, 2), nullable=False)  # Threshold used

    # Results (aggregate only)
    was_balanced: Mapped[bool] = mapped_column(Boolean, nullable=False)  # Did debits equal credits?
    anomaly_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )  # Total anomalies found (no details)
    material_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # Material anomalies only
    immaterial_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # Immaterial anomalies only

    # Multi-sheet info (optional)
    is_consolidated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    sheet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Sprint 461: Cryptographic audit chain (SOC 2 CC7.4)
    chain_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, balanced={self.was_balanced})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename_hash": self.filename_hash,
            "filename_display": self.filename_display,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "record_count": self.record_count,
            "total_debits": str(self.total_debits or 0),
            "total_credits": str(self.total_credits or 0),
            "materiality_threshold": str(self.materiality_threshold or 0),
            "was_balanced": self.was_balanced,
            "anomaly_count": self.anomaly_count,
            "material_count": self.material_count,
            "immaterial_count": self.immaterial_count,
            "is_consolidated": self.is_consolidated,
            "sheet_count": self.sheet_count,
            "chain_hash": self.chain_hash,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "archived_by": self.archived_by,
            "archive_reason": self.archive_reason,
        }


class Client(Base):
    """Client model with multi-tenant isolation. Stores metadata only."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Multi-tenant: Client belongs to a specific user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user: Mapped["User"] = relationship("User", back_populates="clients")

    # Reverse relationships (Sprint 280: backref → back_populates)
    diagnostic_summaries: Mapped[list["DiagnosticSummary"]] = relationship("DiagnosticSummary", back_populates="client")
    engagements: Mapped[list["Engagement"]] = relationship("Engagement", back_populates="client")

    # Client identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Industry classification (standardized enum)
    industry: Mapped[Industry] = mapped_column(Enum(Industry), default=Industry.OTHER, nullable=False)

    # Fiscal year end (e.g., "12-31" for calendar year, "06-30" for June)
    # Format: MM-DD string for flexibility
    fiscal_year_end: Mapped[str] = mapped_column(String(5), default="12-31", nullable=False)

    # Sprint 1: Reporting framework metadata
    reporting_framework: Mapped[ReportingFramework] = mapped_column(
        Enum(ReportingFramework), default=ReportingFramework.AUTO, nullable=False
    )
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType), default=EntityType.OTHER, nullable=False)
    jurisdiction_country: Mapped[str] = mapped_column(String(2), default="US", nullable=False)  # ISO 3166-1 alpha-2
    jurisdiction_state: Mapped[str | None] = mapped_column(String(50), nullable=True)  # US state or sub-national region

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), server_default=func.now()
    )

    # Optional: Client-specific settings (JSON string)
    # For future features like default materiality threshold per client
    settings: Mapped[str] = mapped_column(String(2000), default="{}")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name={self.name[:20]}..., user_id={self.user_id})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "industry": self.industry.value if self.industry else None,
            "fiscal_year_end": self.fiscal_year_end,
            "reporting_framework": self.reporting_framework.value if self.reporting_framework else "auto",
            "entity_type": self.entity_type.value if self.entity_type else "other",
            "jurisdiction_country": self.jurisdiction_country or "US",
            "jurisdiction_state": self.jurisdiction_state,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "settings": self.settings,
        }


class DiagnosticSummary(SoftDeleteMixin, Base):
    """Diagnostic summary for aggregate category totals and variance tracking."""

    __tablename__ = "diagnostic_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to client for variance comparison
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    client: Mapped["Client"] = relationship("Client", back_populates="diagnostic_summaries")

    # Link to user (for multi-tenant security)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user: Mapped["User"] = relationship("User", back_populates="diagnostic_summaries", foreign_keys=[user_id])

    # Timestamp for ordering and trend analysis
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), index=True
    )

    # Sprint 33: Period identification for trend analysis
    period_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)  # End date of the period
    period_type: Mapped[PeriodType | None] = mapped_column(Enum(PeriodType), nullable=True)  # monthly/quarterly/annual
    # Sprint 51: Human-readable period label (e.g., "FY2025", "Q3 2025")
    period_label: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Filename hash for identification (same as ActivityLog)
    filename_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filename_display: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # === AGGREGATE CATEGORY TOTALS (Zero-Storage compliant) ===
    # Balance Sheet totals (Sprint 341: Float → Numeric for monetary precision)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    current_assets: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    inventory: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    current_liabilities: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    total_equity: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)

    # Income Statement totals (Sprint 341: Float → Numeric for monetary precision)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    cost_of_goods_sold: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    operating_expenses: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)  # Sprint 33: For operating margin

    # === CALCULATED RATIOS (for trend tracking) ===
    current_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    quick_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    debt_to_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Sprint 33: Extended ratios for trend analysis
    net_profit_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_on_assets: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_on_equity: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Sprint 449: Cash cycle ratios for trend tracking
    dso: Mapped[float | None] = mapped_column(Float, nullable=True)  # Days Sales Outstanding
    dpo: Mapped[float | None] = mapped_column(Float, nullable=True)  # Days Payable Outstanding
    dio: Mapped[float | None] = mapped_column(Float, nullable=True)  # Days Inventory Outstanding
    ccc: Mapped[float | None] = mapped_column(Float, nullable=True)  # Cash Conversion Cycle

    # === DIAGNOSTIC METADATA === (Sprint 341: monetary Float → Numeric)
    total_debits: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    total_credits: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    was_balanced: Mapped[bool] = mapped_column(Boolean, default=True)
    anomaly_count: Mapped[int] = mapped_column(Integer, default=0)
    materiality_threshold: Mapped[Decimal] = mapped_column(Numeric(19, 2), default=0.0)
    row_count: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<DiagnosticSummary(id={self.id}, client_id={self.client_id}, timestamp={self.timestamp})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            # Sprint 33: Period identification
            "period_date": self.period_date.isoformat() if self.period_date else None,
            "period_type": self.period_type.value if self.period_type else None,
            # Sprint 51: Human-readable label
            "period_label": self.period_label,
            "filename_hash": self.filename_hash,
            "filename_display": self.filename_display,
            # Category totals (str() for JSON — Numeric returns Decimal, preserve precision)
            "total_assets": str(self.total_assets or 0),
            "current_assets": str(self.current_assets or 0),
            "inventory": str(self.inventory or 0),
            "total_liabilities": str(self.total_liabilities or 0),
            "current_liabilities": str(self.current_liabilities or 0),
            "total_equity": str(self.total_equity or 0),
            "total_revenue": str(self.total_revenue or 0),
            "cost_of_goods_sold": str(self.cost_of_goods_sold or 0),
            "total_expenses": str(self.total_expenses or 0),
            "operating_expenses": str(self.operating_expenses or 0),
            # Ratios (Core 4)
            "current_ratio": self.current_ratio,
            "quick_ratio": self.quick_ratio,
            "debt_to_equity": self.debt_to_equity,
            "gross_margin": self.gross_margin,
            # Ratios (Advanced 4 - Sprint 33)
            "net_profit_margin": self.net_profit_margin,
            "operating_margin": self.operating_margin,
            "return_on_assets": self.return_on_assets,
            "return_on_equity": self.return_on_equity,
            # Cash cycle ratios (Sprint 449)
            "dso": self.dso,
            "dpo": self.dpo,
            "dio": self.dio,
            "ccc": self.ccc,
            # Diagnostic metadata (str() for JSON — Numeric returns Decimal, preserve precision)
            "total_debits": str(self.total_debits or 0),
            "total_credits": str(self.total_credits or 0),
            "was_balanced": self.was_balanced,
            "anomaly_count": self.anomaly_count,
            "materiality_threshold": str(self.materiality_threshold or 0),
            "row_count": self.row_count,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "archived_by": self.archived_by,
            "archive_reason": self.archive_reason,
        }

    def get_category_totals_dict(self) -> dict[str, Any]:
        """Get category totals as a dictionary for ratio calculations."""
        return {
            "total_assets": float(self.total_assets or 0),
            "current_assets": float(self.current_assets or 0),
            "inventory": float(self.inventory or 0),
            "total_liabilities": float(self.total_liabilities or 0),
            "current_liabilities": float(self.current_liabilities or 0),
            "total_equity": float(self.total_equity or 0),
            "total_revenue": float(self.total_revenue or 0),
            "cost_of_goods_sold": float(self.cost_of_goods_sold or 0),
            "total_expenses": float(self.total_expenses or 0),
            "operating_expenses": float(self.operating_expenses or 0),
        }

    def get_all_ratios_dict(self) -> dict[str, Any]:
        """Get all stored ratios as a dictionary for trend analysis."""
        return {
            "current_ratio": self.current_ratio,
            "quick_ratio": self.quick_ratio,
            "debt_to_equity": self.debt_to_equity,
            "gross_margin": self.gross_margin,
            "net_profit_margin": self.net_profit_margin,
            "operating_margin": self.operating_margin,
            "return_on_assets": self.return_on_assets,
            "return_on_equity": self.return_on_equity,
            "dso": self.dso,
            "dpo": self.dpo,
            "dio": self.dio,
            "ccc": self.ccc,
        }


class EmailVerificationToken(Base):
    """
    Email verification tokens for user email confirmation.
    Sprint 57: Verified-Account-Only Model

    Tokens are single-use and expire after 24 hours.
    """

    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user: Mapped["User"] = relationship("User", back_populates="verification_tokens")

    # Token data (hashed — SHA-256 hex digest of raw token; never stored plaintext)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Usage tracking
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Set when token is verified

    def __repr__(self) -> str:
        return f"<EmailVerificationToken(id={self.id}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        now = datetime.now(UTC)
        # Handle timezone-naive datetimes from SQLite
        if self.expires_at.tzinfo is None:
            from datetime import timezone

            expires = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires = self.expires_at
        return now > expires

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None


class PasswordResetToken(Base):
    """
    Password reset tokens for account recovery.
    Sprint 572: Password Reset Flow

    Tokens are single-use and expire after 1 hour.
    SHA-256 hash stored — raw token sent via email, never persisted.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user: Mapped["User"] = relationship("User", back_populates="password_reset_tokens")

    # Token data (hashed — SHA-256 hex digest of raw token; never stored plaintext)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Usage tracking
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        now = datetime.now(UTC)
        if self.expires_at.tzinfo is None:
            from datetime import timezone

            expires = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires = self.expires_at
        return now > expires

    @property
    def is_used(self) -> bool:
        """Check if token has been used."""
        return self.used_at is not None


class RefreshToken(Base):
    """
    Refresh tokens for JWT token rotation.
    Sprint 197: Refresh Token Infrastructure

    Stores SHA-256 hash of the raw token (not plaintext).
    Supports token rotation with reuse detection.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Link to user
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    # Token data — stores SHA-256 hash, NOT plaintext
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Lifecycle tracking
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Rotation chain — hash of the replacement token (for reuse detection)
    replaced_by_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # AUDIT-02 FIX 2: Session metadata for inventory & revocation
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        now = datetime.now(UTC)
        # Handle timezone-naive datetimes from SQLite
        if self.expires_at.tzinfo is None:
            from datetime import timezone

            expires = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires = self.expires_at
        return now > expires

    @property
    def is_revoked(self) -> bool:
        """Check if token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_active(self) -> bool:
        """Check if token is still usable (not expired, not revoked)."""
        return not self.is_expired and not self.is_revoked


class WaitlistSignup(Base):
    """Waitlist signups — replaces CSV file storage with database-backed dedup."""

    __tablename__ = "waitlist_signups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
