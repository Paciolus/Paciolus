"""SQLAlchemy models for users, activity logs, clients, and diagnostic summaries."""

from datetime import datetime, date, UTC
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base


class PeriodType(str, PyEnum):
    """Period type for historical trend analysis."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class UserTier(str, PyEnum):
    """User subscription tier for feature access and usage limits."""
    FREE = "free"
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


class User(Base):
    """User model for authentication. Stores credentials and preferences only."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # User profile
    name = Column(String(100), nullable=True)  # Display name (optional)

    # User metadata
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email verification status

    # Sprint 57: User tier for feature access and usage limits
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)

    # Sprint 57: Email verification fields
    email_verification_token = Column(String(64), nullable=True, index=True)
    email_verification_sent_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    last_login = Column(DateTime, nullable=True)

    # User settings (JSON string) - for future preferences
    # IMPORTANT: This is for UI preferences only, NOT financial data
    settings = Column(String(2000), default="{}")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email[:10]}...)>"


class ActivityLog(Base):
    """Activity log for audit metadata history. Stores aggregate stats only."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)

    # User association (nullable for anonymous audits)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User", backref="activity_logs")

    # Audit identification (privacy-preserving)
    filename_hash = Column(String(64), nullable=False)  # SHA-256 hash of filename
    filename_display = Column(String(20), nullable=True)  # First 8 chars + "..." for UI

    # Timestamp
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    # Audit summary metadata (aggregate only - no specific account details)
    record_count = Column(Integer, nullable=False)  # Number of rows processed
    total_debits = Column(Float, nullable=False)  # Sum of all debits
    total_credits = Column(Float, nullable=False)  # Sum of all credits
    materiality_threshold = Column(Float, nullable=False)  # Threshold used

    # Results (aggregate only)
    was_balanced = Column(Boolean, nullable=False)  # Did debits equal credits?
    anomaly_count = Column(Integer, default=0)  # Total anomalies found (no details)
    material_count = Column(Integer, default=0)  # Material anomalies only
    immaterial_count = Column(Integer, default=0)  # Immaterial anomalies only

    # Multi-sheet info (optional)
    is_consolidated = Column(Boolean, default=False)
    sheet_count = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, balanced={self.was_balanced})>"

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename_hash": self.filename_hash,
            "filename_display": self.filename_display,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "record_count": self.record_count,
            "total_debits": self.total_debits,
            "total_credits": self.total_credits,
            "materiality_threshold": self.materiality_threshold,
            "was_balanced": self.was_balanced,
            "anomaly_count": self.anomaly_count,
            "material_count": self.material_count,
            "immaterial_count": self.immaterial_count,
            "is_consolidated": self.is_consolidated,
            "sheet_count": self.sheet_count,
        }


class Client(Base):
    """Client model with multi-tenant isolation. Stores metadata only."""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant: Client belongs to a specific user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", backref="clients")

    # Client identification
    name = Column(String(255), nullable=False)

    # Industry classification (standardized enum)
    industry = Column(Enum(Industry), default=Industry.OTHER, nullable=False)

    # Fiscal year end (e.g., "12-31" for calendar year, "06-30" for June)
    # Format: MM-DD string for flexibility
    fiscal_year_end = Column(String(5), default="12-31", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Optional: Client-specific settings (JSON string)
    # For future features like default materiality threshold per client
    settings = Column(String(2000), default="{}")

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name[:20]}..., user_id={self.user_id})>"

    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "industry": self.industry.value if self.industry else None,
            "fiscal_year_end": self.fiscal_year_end,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "settings": self.settings,
        }


class DiagnosticSummary(Base):
    """Diagnostic summary for aggregate category totals and variance tracking."""
    __tablename__ = "diagnostic_summaries"

    id = Column(Integer, primary_key=True, index=True)

    # Link to client for variance comparison
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    client = relationship("Client", backref="diagnostic_summaries")

    # Link to user (for multi-tenant security)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", backref="diagnostic_summaries")

    # Timestamp for ordering and trend analysis
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    # Sprint 33: Period identification for trend analysis
    period_date = Column(Date, nullable=True, index=True)  # End date of the period
    period_type = Column(Enum(PeriodType), nullable=True)  # monthly/quarterly/annual
    # Sprint 51: Human-readable period label (e.g., "FY2025", "Q3 2025")
    period_label = Column(String(50), nullable=True)

    # Filename hash for identification (same as ActivityLog)
    filename_hash = Column(String(64), nullable=True)
    filename_display = Column(String(20), nullable=True)

    # === AGGREGATE CATEGORY TOTALS (Zero-Storage compliant) ===
    # Balance Sheet totals
    total_assets = Column(Float, default=0.0)
    current_assets = Column(Float, default=0.0)
    inventory = Column(Float, default=0.0)
    total_liabilities = Column(Float, default=0.0)
    current_liabilities = Column(Float, default=0.0)
    total_equity = Column(Float, default=0.0)

    # Income Statement totals
    total_revenue = Column(Float, default=0.0)
    cost_of_goods_sold = Column(Float, default=0.0)
    total_expenses = Column(Float, default=0.0)
    operating_expenses = Column(Float, default=0.0)  # Sprint 33: For operating margin

    # === CALCULATED RATIOS (for trend tracking) ===
    current_ratio = Column(Float, nullable=True)
    quick_ratio = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    gross_margin = Column(Float, nullable=True)
    # Sprint 33: Extended ratios for trend analysis
    net_profit_margin = Column(Float, nullable=True)
    operating_margin = Column(Float, nullable=True)
    return_on_assets = Column(Float, nullable=True)
    return_on_equity = Column(Float, nullable=True)

    # === DIAGNOSTIC METADATA ===
    total_debits = Column(Float, default=0.0)
    total_credits = Column(Float, default=0.0)
    was_balanced = Column(Boolean, default=True)
    anomaly_count = Column(Integer, default=0)
    materiality_threshold = Column(Float, default=0.0)
    row_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<DiagnosticSummary(id={self.id}, client_id={self.client_id}, timestamp={self.timestamp})>"

    def to_dict(self):
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
            # Category totals
            "total_assets": self.total_assets,
            "current_assets": self.current_assets,
            "inventory": self.inventory,
            "total_liabilities": self.total_liabilities,
            "current_liabilities": self.current_liabilities,
            "total_equity": self.total_equity,
            "total_revenue": self.total_revenue,
            "cost_of_goods_sold": self.cost_of_goods_sold,
            "total_expenses": self.total_expenses,
            "operating_expenses": self.operating_expenses,
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
            # Diagnostic metadata
            "total_debits": self.total_debits,
            "total_credits": self.total_credits,
            "was_balanced": self.was_balanced,
            "anomaly_count": self.anomaly_count,
            "materiality_threshold": self.materiality_threshold,
            "row_count": self.row_count,
        }

    def get_category_totals_dict(self):
        """Get category totals as a dictionary for ratio calculations."""
        return {
            "total_assets": self.total_assets,
            "current_assets": self.current_assets,
            "inventory": self.inventory,
            "total_liabilities": self.total_liabilities,
            "current_liabilities": self.current_liabilities,
            "total_equity": self.total_equity,
            "total_revenue": self.total_revenue,
            "cost_of_goods_sold": self.cost_of_goods_sold,
            "total_expenses": self.total_expenses,
            "operating_expenses": self.operating_expenses,
        }

    def get_all_ratios_dict(self):
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
        }


class EmailVerificationToken(Base):
    """
    Email verification tokens for user email confirmation.
    Sprint 57: Verified-Account-Only Model

    Tokens are single-use and expire after 24 hours.
    """
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)

    # Link to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", backref="verification_tokens")

    # Token data
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Usage tracking
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    used_at = Column(DateTime, nullable=True)  # Set when token is verified

    def __repr__(self):
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
