"""
Paciolus Database Models
Day 13: Secure Commercial Infrastructure
Day 14: Activity Logging & Metadata History
Sprint 16: Client Core Infrastructure
Sprint 19: Comparative Analytics & Ratio Engine

SQLAlchemy models for user authentication, activity logging, client management,
and diagnostic summary metadata.

ZERO-STORAGE EXCEPTION: Only user metadata, audit summary metadata, and client metadata is stored.
Trial balance data, file contents, and specific anomaly details are NEVER persisted.

PRIVACY COMPLIANCE (GDPR/CCPA):
- No PII is stored in activity logs
- Filenames are hashed (SHA-256) to prevent data leakage
- Only aggregate statistics are logged, never individual account details

CLIENT DATA BOUNDARY (Sprint 16):
- Stores ONLY client identification metadata (name, industry, fiscal year)
- NEVER stores client financial data or transaction details
- All client data is user-scoped (multi-tenant isolation)

DIAGNOSTIC SUMMARY (Sprint 19):
- Stores ONLY aggregate category totals for variance comparison
- NEVER stores individual account names, balances, or transaction details
- Enables "Variance Intelligence" between diagnostic runs
"""

from datetime import datetime, UTC
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base


# =============================================================================
# ENUMS
# =============================================================================

class Industry(str, PyEnum):
    """
    Standardized industry classification for clients.

    Based on common categories relevant to fractional CFO practice.
    These are high-level groupings, not detailed NAICS codes.
    """
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
    """
    User model for authentication.

    ZERO-STORAGE COMPLIANCE:
    - Stores ONLY authentication data (email, password hash)
    - Stores ONLY user preferences (settings JSON)
    - NEVER stores trial balance data, audit results, or financial information
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # User metadata
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # For future email verification

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
    """
    Activity Log model for audit metadata history.

    Day 14: Activity Logging & Metadata History

    ZERO-STORAGE COMPLIANCE:
    - Stores ONLY high-level summary metadata
    - NEVER stores actual file content
    - NEVER stores specific anomaly details or account names
    - Filename is hashed (SHA-256) for privacy

    GDPR/CCPA COMPLIANCE:
    - No PII (Personally Identifiable Information) in logs
    - Aggregate statistics only (counts, totals)
    - User can request deletion of their activity history
    """
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
    """
    Client model for managing CFO client relationships.

    Sprint 16: Client Core Infrastructure

    ZERO-STORAGE COMPLIANCE:
    - Stores ONLY client identification metadata
    - Stores ONLY high-level settings (fiscal year end, industry)
    - NEVER stores financial data, transactions, or audit results
    - Client-specific audit data remains ephemeral (in-memory only)

    MULTI-TENANT ISOLATION:
    - All clients are scoped to a specific user (user_id FK)
    - Users can only access their own clients
    - No cross-user client visibility

    DATA BOUNDARY:
    | What IS Stored          | What is NEVER Stored         |
    |-------------------------|------------------------------|
    | Client name             | Trial balance data           |
    | Industry classification | Transaction details          |
    | Fiscal year end         | Account balances             |
    | Created/updated times   | Audit results                |
    """
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
    """
    Diagnostic Summary model for storing aggregate category totals.

    Sprint 19: Comparative Analytics & Ratio Engine

    ZERO-STORAGE COMPLIANCE:
    - Stores ONLY aggregate category totals (assets, liabilities, etc.)
    - NEVER stores individual account names or balances
    - NEVER stores raw transaction data
    - Enables "Variance Intelligence" by comparing current vs previous totals

    DATA BOUNDARY:
    | What IS Stored          | What is NEVER Stored         |
    |-------------------------|------------------------------|
    | Total Assets (sum)      | Individual asset accounts    |
    | Total Liabilities (sum) | Individual liability accounts|
    | Total Revenue (sum)     | Individual revenue accounts  |
    | Calculated ratios       | Raw financial transactions   |
    | Diagnostic timestamp    | File contents                |
    """
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

    # === CALCULATED RATIOS (for trend tracking) ===
    current_ratio = Column(Float, nullable=True)
    quick_ratio = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    gross_margin = Column(Float, nullable=True)

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
            # Ratios
            "current_ratio": self.current_ratio,
            "quick_ratio": self.quick_ratio,
            "debt_to_equity": self.debt_to_equity,
            "gross_margin": self.gross_margin,
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
        }
