"""
Paciolus Backend
Trial Balance Diagnostic Intelligence for Financial Professionals
Sprint 24: Production Deployment Prep
"""

import csv
import hashlib
import json
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Query, Path as PathParam, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from security_utils import log_secure_operation, clear_memory
from audit_engine import (
    audit_trial_balance_streaming,
    audit_trial_balance_multi_sheet,
    DEFAULT_CHUNK_SIZE
)
from workbook_inspector import inspect_workbook, is_excel_file, WorkbookInfo
from pdf_generator import generate_audit_report
from excel_generator import generate_workpaper
from database import get_db, init_db
from models import User, ActivityLog, Client, Industry, DiagnosticSummary
from ratio_engine import CategoryTotals, calculate_analytics
from auth import (
    UserCreate, UserLogin, UserResponse, AuthResponse,
    create_user, authenticate_user, get_user_by_email,
    create_access_token, validate_password_strength,
    get_current_user, require_current_user
)
from client_manager import ClientManager, get_industry_options
from practice_settings import (
    PracticeSettings, ClientSettings, MaterialityFormula, MaterialityFormulaType,
    MaterialityConfig, MaterialityCalculator, resolve_materiality_config
)
from flux_engine import FluxEngine, FluxResult, FluxItem, FluxRisk
from recon_engine import ReconEngine, ReconResult, ReconScore, RiskBand
from leadsheet_generator import generate_leadsheets

# Import config (will hard fail if .env is missing)
from config import API_HOST, API_PORT, CORS_ORIGINS, DEBUG, print_config_summary

app = FastAPI(
    title="Paciolus API",
    description="Trial Balance Diagnostic Intelligence for Financial Professionals",
    version="0.16.0"  # Sprint 24: Production Deployment Prep
)

# CORS configuration from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Waitlist file path (only storage exception per security policy)
WAITLIST_FILE = Path(__file__).parent / "waitlist.csv"

# =============================================================================
# DATABASE INITIALIZATION (Day 13)
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    init_db()
    log_secure_operation("app_startup", "Paciolus API started with authentication enabled")


# =============================================================================
# REUSABLE DEPENDENCIES
# =============================================================================

async def require_client(
    client_id: int = PathParam(..., description="The ID of the client"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
) -> Client:
    """
    FastAPI dependency that validates client ownership.

    Raises HTTPException 404 if client not found or not owned by current user.
    Use this to simplify endpoints that need a validated client.
    """
    manager = ClientManager(db)
    client = manager.get_client(current_user.id, client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return client


class WaitlistEntry(BaseModel):
    email: EmailStr


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class WaitlistResponse(BaseModel):
    success: bool
    message: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns API status and version information.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version="0.13.0"  # Sprint 21: Practice Settings
    )


@app.post("/waitlist", response_model=WaitlistResponse)
async def join_waitlist(entry: WaitlistEntry):
    """
    Add an email to the waitlist.
    This is the ONLY storage exception per the Zero-Storage policy.
    Waitlist contains no accounting data.
    """
    try:
        # Check if file exists, create with header if not
        file_exists = WAITLIST_FILE.exists()

        with open(WAITLIST_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["email", "timestamp"])
            writer.writerow([entry.email, datetime.now(UTC).isoformat()])

        log_secure_operation("waitlist_signup", f"New signup: {entry.email[:3]}***")

        return WaitlistResponse(
            success=True,
            message="You're on the list! We'll be in touch soon."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to join waitlist. Please try again."
        )


# =============================================================================
# DAY 13: AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    ZERO-STORAGE COMPLIANCE:
    - User database stores ONLY authentication data (email, hashed password)
    - Trial balance data is NEVER stored
    - Passwords are hashed with bcrypt before storage

    Args:
        user_data: Email and password for registration

    Returns:
        JWT access token and user info on success

    Raises:
        400: Email already registered
        400: Password does not meet requirements
    """
    log_secure_operation("auth_register_attempt", f"Registration attempt: {user_data.email[:10]}...")

    # Check if email already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists"
        )

    # Validate password strength
    is_valid, issues = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Password does not meet requirements",
                "issues": issues
            }
        )

    # Create user (password is hashed in create_user)
    user = create_user(db, user_data)

    # Generate JWT token
    token, expires = create_access_token(user.id, user.email)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@app.post("/auth/login", response_model=AuthResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.

    Args:
        credentials: Email and password

    Returns:
        JWT access token and user info on success

    Raises:
        401: Invalid credentials
    """
    log_secure_operation("auth_login_attempt", f"Login attempt: {credentials.email[:10]}...")

    user = authenticate_user(db, credentials.email, credentials.password)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Generate JWT token
    token, expires = create_access_token(user.id, user.email)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(require_current_user)):
    """
    Get the current authenticated user's information.

    Requires valid JWT token in Authorization header.

    Returns:
        User information (excludes password)

    Raises:
        401: Not authenticated
    """
    return UserResponse.model_validate(current_user)


# =============================================================================
# DAY 14: ACTIVITY LOGGING ENDPOINTS
# =============================================================================

def hash_filename(filename: str) -> str:
    """
    Create a SHA-256 hash of a filename for privacy-preserving storage.

    GDPR/CCPA COMPLIANCE: We don't store the actual filename,
    only a hash that can be used for deduplication and display.
    """
    return hashlib.sha256(filename.encode('utf-8')).hexdigest()


def get_filename_display(filename: str, max_length: int = 12) -> str:
    """
    Create a safe display preview of a filename.

    Returns first few characters + "..." to give users context
    without storing the full filename.
    """
    if len(filename) <= max_length:
        return filename
    return filename[:max_length - 3] + "..."


class ActivityLogCreate(BaseModel):
    """Input model for creating an activity log entry."""
    filename: str
    record_count: int
    total_debits: float
    total_credits: float
    materiality_threshold: float
    was_balanced: bool
    anomaly_count: int = 0
    material_count: int = 0
    immaterial_count: int = 0
    is_consolidated: bool = False
    sheet_count: Optional[int] = None


class ActivityLogResponse(BaseModel):
    """Response model for activity log entries."""
    id: int
    filename_hash: str
    filename_display: Optional[str]
    timestamp: str
    record_count: int
    total_debits: float
    total_credits: float
    materiality_threshold: float
    was_balanced: bool
    anomaly_count: int
    material_count: int
    immaterial_count: int
    is_consolidated: bool
    sheet_count: Optional[int]


class ActivityHistoryResponse(BaseModel):
    """Response model for activity history list."""
    activities: List[ActivityLogResponse]
    total_count: int
    page: int
    page_size: int


@app.post("/activity/log", response_model=ActivityLogResponse)
async def log_activity(
    activity: ActivityLogCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Log an audit activity for the authenticated user.

    Day 14: Activity Logging & Metadata History

    ZERO-STORAGE COMPLIANCE:
    - Stores ONLY high-level summary metadata
    - Filename is hashed (SHA-256) for privacy
    - NO file content or specific anomaly details are stored

    GDPR/CCPA COMPLIANCE:
    - No PII in logs (filename is hashed)
    - Only aggregate statistics stored
    - User can request deletion via /activity/clear

    Args:
        activity: Audit summary metadata

    Returns:
        The created activity log entry

    Raises:
        401: Not authenticated
    """
    log_secure_operation(
        "activity_log_create",
        f"User {current_user.id} logging audit activity"
    )

    # Create activity log with hashed filename
    db_activity = ActivityLog(
        user_id=current_user.id,
        filename_hash=hash_filename(activity.filename),
        filename_display=get_filename_display(activity.filename),
        record_count=activity.record_count,
        total_debits=activity.total_debits,
        total_credits=activity.total_credits,
        materiality_threshold=activity.materiality_threshold,
        was_balanced=activity.was_balanced,
        anomaly_count=activity.anomaly_count,
        material_count=activity.material_count,
        immaterial_count=activity.immaterial_count,
        is_consolidated=activity.is_consolidated,
        sheet_count=activity.sheet_count,
    )

    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)

    log_secure_operation(
        "activity_log_created",
        f"Activity {db_activity.id} created for user {current_user.id}"
    )

    return ActivityLogResponse(
        id=db_activity.id,
        filename_hash=db_activity.filename_hash,
        filename_display=db_activity.filename_display,
        timestamp=db_activity.timestamp.isoformat(),
        record_count=db_activity.record_count,
        total_debits=db_activity.total_debits,
        total_credits=db_activity.total_credits,
        materiality_threshold=db_activity.materiality_threshold,
        was_balanced=db_activity.was_balanced,
        anomaly_count=db_activity.anomaly_count,
        material_count=db_activity.material_count,
        immaterial_count=db_activity.immaterial_count,
        is_consolidated=db_activity.is_consolidated,
        sheet_count=db_activity.sheet_count,
    )


@app.get("/activity/history", response_model=ActivityHistoryResponse)
async def get_activity_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the authenticated user's audit activity history.

    Day 14: Activity Logging & Metadata History

    Returns a paginated list of audit activities, newest first.

    ZERO-STORAGE PROMISE: This endpoint returns only metadata summaries.
    Your actual trial balance data was never stored.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)

    Returns:
        Paginated list of activity log entries

    Raises:
        401: Not authenticated
    """
    log_secure_operation(
        "activity_history_fetch",
        f"User {current_user.id} fetching activity history (page {page})"
    )

    # Optimized: Single query with window function for total count
    # Reduces database round-trips from 2 to 1
    offset = (page - 1) * page_size
    results = db.query(
        ActivityLog,
        func.count(ActivityLog.id).over().label('total_count')
    ).filter(
        ActivityLog.user_id == current_user.id
    ).order_by(
        ActivityLog.timestamp.desc()
    ).offset(offset).limit(page_size).all()

    # Extract activities and total count from results
    if not results:
        return ActivityHistoryResponse(
            activities=[],
            total_count=0,
            page=page,
            page_size=page_size,
        )

    total_count = results[0][1]  # Window function result
    activities = [row[0] for row in results]

    return ActivityHistoryResponse(
        activities=[
            ActivityLogResponse(
                id=a.id,
                filename_hash=a.filename_hash,
                filename_display=a.filename_display,
                timestamp=a.timestamp.isoformat(),
                record_count=a.record_count,
                total_debits=a.total_debits,
                total_credits=a.total_credits,
                materiality_threshold=a.materiality_threshold,
                was_balanced=a.was_balanced,
                anomaly_count=a.anomaly_count,
                material_count=a.material_count,
                immaterial_count=a.immaterial_count,
                is_consolidated=a.is_consolidated,
                sheet_count=a.sheet_count,
            )
            for a in activities
        ],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@app.delete("/activity/clear")
async def clear_activity_history(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear all activity history for the authenticated user.

    Day 14: GDPR/CCPA Compliance - Right to Deletion

    This permanently deletes all audit activity logs for the user.
    This action cannot be undone.

    Returns:
        Confirmation message with count of deleted entries

    Raises:
        401: Not authenticated
    """
    log_secure_operation(
        "activity_clear_request",
        f"User {current_user.id} requesting activity history deletion"
    )

    # Count and delete all user's activities
    deleted_count = db.query(ActivityLog).filter(
        ActivityLog.user_id == current_user.id
    ).delete()

    db.commit()

    log_secure_operation(
        "activity_clear_complete",
        f"Deleted {deleted_count} activity entries for user {current_user.id}"
    )

    return {
        "success": True,
        "message": f"Deleted {deleted_count} activity entries",
        "deleted_count": deleted_count
    }


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics."""
    total_clients: int
    assessments_today: int
    last_assessment_date: Optional[str]
    total_assessments: int


@app.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics for the authenticated user.

    Returns summary data for workspace header:
    - total_clients: Number of unique clients
    - assessments_today: Number of assessments uploaded today
    - last_assessment_date: Timestamp of most recent assessment
    - total_assessments: Total number of assessments ever uploaded

    Args:
        current_user: The authenticated user (from JWT token)

    Returns:
        Dashboard summary statistics

    Raises:
        401: Not authenticated
    """
    log_secure_operation(
        "dashboard_stats_fetch",
        f"User {current_user.id} fetching dashboard stats"
    )

    # Single aggregated query for all stats (optimized from 4 queries to 1)
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    # Get client count in separate query (different table)
    total_clients = db.query(func.count(Client.id)).filter(
        Client.user_id == current_user.id
    ).scalar() or 0

    # Get all activity stats in single query using aggregation
    activity_stats = db.query(
        func.count(ActivityLog.id).label('total_assessments'),
        func.sum(
            case(
                (ActivityLog.timestamp >= today_start, 1),
                else_=0
            )
        ).label('assessments_today'),
        func.max(ActivityLog.timestamp).label('last_assessment_date')
    ).filter(
        ActivityLog.user_id == current_user.id
    ).first()

    # Extract values with defaults
    total_assessments = activity_stats.total_assessments or 0 if activity_stats else 0
    assessments_today = activity_stats.assessments_today or 0 if activity_stats else 0
    last_assessment_date = None
    if activity_stats and activity_stats.last_assessment_date:
        last_assessment_date = activity_stats.last_assessment_date.isoformat()

    return DashboardStatsResponse(
        total_clients=total_clients,
        assessments_today=assessments_today,
        last_assessment_date=last_assessment_date,
        total_assessments=total_assessments
    )


# =============================================================================
# SPRINT 16: CLIENT MANAGEMENT ENDPOINTS
# =============================================================================

class ClientCreate(BaseModel):
    """Input model for creating a new client."""
    name: str
    industry: Optional[str] = "other"
    fiscal_year_end: Optional[str] = "12-31"
    settings: Optional[str] = "{}"


class ClientUpdate(BaseModel):
    """Input model for updating a client."""
    name: Optional[str] = None
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    settings: Optional[str] = None


class ClientResponse(BaseModel):
    """Response model for a single client."""
    id: int
    user_id: int
    name: str
    industry: str
    fiscal_year_end: str
    created_at: str
    updated_at: str
    settings: str


class ClientListResponse(BaseModel):
    """Response model for client list."""
    clients: List[ClientResponse]
    total_count: int
    page: int
    page_size: int


class IndustryOption(BaseModel):
    """Industry dropdown option."""
    value: str
    label: str


@app.get("/clients/industries", response_model=List[IndustryOption])
async def get_industries(response: Response):
    """
    Get list of available industry options for dropdowns.

    Returns:
        List of industry options with value and label

    Note:
        This endpoint returns static data that never changes,
        so it sets a long cache duration (1 hour public, 1 day private).
    """
    # Cache for 1 hour (public) or 1 day (private browser cache)
    # This data is completely static and safe to cache aggressively
    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=86400"
    return get_industry_options()


@app.get("/clients", response_model=ClientListResponse)
async def get_clients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all clients for the authenticated user.

    Sprint 16: Client Core Infrastructure

    MULTI-TENANT: Returns only clients belonging to the current user.
    No cross-user data access is possible.

    ZERO-STORAGE COMPLIANCE:
    - Returns only client metadata (name, industry, fiscal year)
    - No financial data is ever stored or returned

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        search: Optional search string to filter by client name

    Returns:
        Paginated list of clients

    Raises:
        401: Not authenticated
    """
    log_secure_operation(
        "clients_list",
        f"User {current_user.id} fetching client list (page {page})"
    )

    manager = ClientManager(db)

    if search:
        # Search mode
        clients = manager.search_clients(current_user.id, search, limit=page_size)
        total_count = len(clients)
    else:
        # Paginated list mode - optimized single query with count
        offset = (page - 1) * page_size
        clients, total_count = manager.get_clients_with_count(
            current_user.id, limit=page_size, offset=offset
        )

    return ClientListResponse(
        clients=[
            ClientResponse(
                id=c.id,
                user_id=c.user_id,
                name=c.name,
                industry=c.industry.value if c.industry else "other",
                fiscal_year_end=c.fiscal_year_end,
                created_at=c.created_at.isoformat() if c.created_at else "",
                updated_at=c.updated_at.isoformat() if c.updated_at else "",
                settings=c.settings or "{}"
            )
            for c in clients
        ],
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@app.post("/clients", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new client for the authenticated user.

    Sprint 16: Client Core Infrastructure

    ZERO-STORAGE COMPLIANCE:
    - Stores ONLY client identification metadata
    - NEVER stores financial data or transaction details
    - Client-specific audits remain ephemeral

    Args:
        client_data: Client name, industry, and fiscal year end

    Returns:
        The created client

    Raises:
        400: Validation error (empty name, invalid fiscal year format)
        401: Not authenticated
    """
    log_secure_operation(
        "client_create",
        f"User {current_user.id} creating client: {client_data.name[:20]}..."
    )

    manager = ClientManager(db)

    try:
        # Convert industry string to enum
        industry = Industry(client_data.industry) if client_data.industry else Industry.OTHER

        client = manager.create_client(
            user_id=current_user.id,
            name=client_data.name,
            industry=industry,
            fiscal_year_end=client_data.fiscal_year_end or "12-31",
            settings=client_data.settings or "{}"
        )

        return ClientResponse(
            id=client.id,
            user_id=client.user_id,
            name=client.name,
            industry=client.industry.value if client.industry else "other",
            fiscal_year_end=client.fiscal_year_end,
            created_at=client.created_at.isoformat() if client.created_at else "",
            updated_at=client.updated_at.isoformat() if client.updated_at else "",
            settings=client.settings or "{}"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client: Client = Depends(require_client)
):
    """
    Get a specific client by ID.

    Sprint 16: Client Core Infrastructure

    MULTI-TENANT: Only returns the client if it belongs to the current user.

    Args:
        client_id: The ID of the client to retrieve

    Returns:
        The client details

    Raises:
        401: Not authenticated
        404: Client not found or not owned by user
    """

    return ClientResponse(
        id=client.id,
        user_id=client.user_id,
        name=client.name,
        industry=client.industry.value if client.industry else "other",
        fiscal_year_end=client.fiscal_year_end,
        created_at=client.created_at.isoformat() if client.created_at else "",
        updated_at=client.updated_at.isoformat() if client.updated_at else "",
        settings=client.settings or "{}"
    )


@app.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a client's information.

    Sprint 16: Client Core Infrastructure

    MULTI-TENANT: Only updates the client if it belongs to the current user.

    Args:
        client_id: The ID of the client to update
        client_data: Fields to update (all optional)

    Returns:
        The updated client

    Raises:
        400: Validation error
        401: Not authenticated
        404: Client not found or not owned by user
    """
    log_secure_operation(
        "client_update",
        f"User {current_user.id} updating client {client_id}"
    )

    manager = ClientManager(db)

    try:
        # Convert industry string to enum if provided
        industry = None
        if client_data.industry is not None:
            industry = Industry(client_data.industry)

        client = manager.update_client(
            user_id=current_user.id,
            client_id=client_id,
            name=client_data.name,
            industry=industry,
            fiscal_year_end=client_data.fiscal_year_end,
            settings=client_data.settings
        )

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return ClientResponse(
            id=client.id,
            user_id=client.user_id,
            name=client.name,
            industry=client.industry.value if client.industry else "other",
            fiscal_year_end=client.fiscal_year_end,
            created_at=client.created_at.isoformat() if client.created_at else "",
            updated_at=client.updated_at.isoformat() if client.updated_at else "",
            settings=client.settings or "{}"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/clients/{client_id}")
async def delete_client(
    client_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a client.

    Sprint 16: Client Core Infrastructure

    MULTI-TENANT: Only deletes the client if it belongs to the current user.

    NOTE: This only deletes the client metadata. No financial data
    was ever stored, so there's nothing else to delete.

    Args:
        client_id: The ID of the client to delete

    Returns:
        Confirmation message

    Raises:
        401: Not authenticated
        404: Client not found or not owned by user
    """
    log_secure_operation(
        "client_delete",
        f"User {current_user.id} deleting client {client_id}"
    )

    manager = ClientManager(db)
    deleted = manager.delete_client(current_user.id, client_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "success": True,
        "message": "Client deleted successfully",
        "client_id": client_id
    }


# =============================================================================
# SPRINT 21: PRACTICE SETTINGS ENDPOINTS
# =============================================================================

class MaterialityFormulaInput(BaseModel):
    """Input model for materiality formula."""
    type: str = "fixed"  # fixed, percentage_of_revenue, percentage_of_assets, percentage_of_equity
    value: float = 500.0
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None


class PracticeSettingsInput(BaseModel):
    """Input model for updating practice settings."""
    default_materiality: Optional[MaterialityFormulaInput] = None
    show_immaterial_by_default: Optional[bool] = None
    default_fiscal_year_end: Optional[str] = None
    theme_preference: Optional[str] = None
    default_export_format: Optional[str] = None
    auto_save_summaries: Optional[bool] = None


class PracticeSettingsResponse(BaseModel):
    """Response model for practice settings."""
    default_materiality: dict
    show_immaterial_by_default: bool
    default_fiscal_year_end: str
    theme_preference: str
    default_export_format: str
    auto_save_summaries: bool


class ClientSettingsInput(BaseModel):
    """Input model for client-specific settings."""
    materiality_override: Optional[MaterialityFormulaInput] = None
    notes: Optional[str] = None
    industry_multiplier: Optional[float] = None
    diagnostic_frequency: Optional[str] = None


class ClientSettingsResponse(BaseModel):
    """Response model for client settings."""
    materiality_override: Optional[dict]
    notes: str
    industry_multiplier: float
    diagnostic_frequency: str


class MaterialityPreviewInput(BaseModel):
    """Input for materiality preview calculation."""
    formula: MaterialityFormulaInput
    total_revenue: float = 0.0
    total_assets: float = 0.0
    total_equity: float = 0.0


@app.get("/settings/practice", response_model=PracticeSettingsResponse)
async def get_practice_settings(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's practice settings.

    Sprint 21: Customization & Practice Settings

    ZERO-STORAGE COMPLIANCE:
    - Returns only configuration/formula settings
    - Never returns or stores financial data

    Returns:
        Practice settings including default materiality formula
    """
    log_secure_operation(
        "get_practice_settings",
        f"User {current_user.id} fetching practice settings"
    )

    # Parse settings from user's settings JSON field
    settings = PracticeSettings.from_json(current_user.settings or "{}")

    return PracticeSettingsResponse(
        default_materiality=settings.default_materiality.to_dict(),
        show_immaterial_by_default=settings.show_immaterial_by_default,
        default_fiscal_year_end=settings.default_fiscal_year_end,
        theme_preference=settings.theme_preference,
        default_export_format=settings.default_export_format,
        auto_save_summaries=settings.auto_save_summaries,
    )


@app.put("/settings/practice", response_model=PracticeSettingsResponse)
async def update_practice_settings(
    settings_input: PracticeSettingsInput,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's practice settings.

    Sprint 21: Customization & Practice Settings

    ZERO-STORAGE COMPLIANCE:
    - Stores only configuration/formula settings
    - Never stores financial data

    Args:
        settings_input: Partial settings to update

    Returns:
        Updated practice settings
    """
    log_secure_operation(
        "update_practice_settings",
        f"User {current_user.id} updating practice settings"
    )

    # Get current settings
    current_settings = PracticeSettings.from_json(current_user.settings or "{}")

    # Update fields if provided
    if settings_input.default_materiality:
        formula_input = settings_input.default_materiality
        current_settings.default_materiality = MaterialityFormula(
            type=MaterialityFormulaType(formula_input.type),
            value=formula_input.value,
            min_threshold=formula_input.min_threshold,
            max_threshold=formula_input.max_threshold,
        )

    if settings_input.show_immaterial_by_default is not None:
        current_settings.show_immaterial_by_default = settings_input.show_immaterial_by_default

    if settings_input.default_fiscal_year_end is not None:
        current_settings.default_fiscal_year_end = settings_input.default_fiscal_year_end

    if settings_input.theme_preference is not None:
        current_settings.theme_preference = settings_input.theme_preference

    if settings_input.default_export_format is not None:
        current_settings.default_export_format = settings_input.default_export_format

    if settings_input.auto_save_summaries is not None:
        current_settings.auto_save_summaries = settings_input.auto_save_summaries

    # Save to database
    current_user.settings = current_settings.to_json()
    db.commit()

    log_secure_operation(
        "practice_settings_updated",
        f"User {current_user.id} practice settings saved"
    )

    return PracticeSettingsResponse(
        default_materiality=current_settings.default_materiality.to_dict(),
        show_immaterial_by_default=current_settings.show_immaterial_by_default,
        default_fiscal_year_end=current_settings.default_fiscal_year_end,
        theme_preference=current_settings.theme_preference,
        default_export_format=current_settings.default_export_format,
        auto_save_summaries=current_settings.auto_save_summaries,
    )


@app.get("/clients/{client_id}/settings", response_model=ClientSettingsResponse)
async def get_client_settings(
    client: Client = Depends(require_client)
):
    """
    Get settings for a specific client.

    Sprint 21: Customization & Practice Settings

    MULTI-TENANT: Only returns settings for clients owned by the current user.

    Returns:
        Client-specific settings
    """
    settings = ClientSettings.from_json(client.settings or "{}")

    return ClientSettingsResponse(
        materiality_override=settings.materiality_override.to_dict() if settings.materiality_override else None,
        notes=settings.notes,
        industry_multiplier=settings.industry_multiplier,
        diagnostic_frequency=settings.diagnostic_frequency,
    )


@app.put("/clients/{client_id}/settings", response_model=ClientSettingsResponse)
async def update_client_settings(
    client_id: int,
    settings_input: ClientSettingsInput,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Update settings for a specific client.

    Sprint 21: Customization & Practice Settings

    MULTI-TENANT: Only updates settings for clients owned by the current user.

    Args:
        client_id: The client ID
        settings_input: Partial settings to update

    Returns:
        Updated client settings
    """
    log_secure_operation(
        "update_client_settings",
        f"User {current_user.id} updating settings for client {client_id}"
    )

    manager = ClientManager(db)
    client = manager.get_client(current_user.id, client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get current settings
    current_settings = ClientSettings.from_json(client.settings or "{}")

    # Update fields if provided
    if settings_input.materiality_override:
        formula_input = settings_input.materiality_override
        current_settings.materiality_override = MaterialityFormula(
            type=MaterialityFormulaType(formula_input.type),
            value=formula_input.value,
            min_threshold=formula_input.min_threshold,
            max_threshold=formula_input.max_threshold,
        )
    elif settings_input.materiality_override is None and 'materiality_override' in (settings_input.model_dump(exclude_unset=True) or {}):
        # Explicitly set to None to clear the override
        current_settings.materiality_override = None

    if settings_input.notes is not None:
        current_settings.notes = settings_input.notes

    if settings_input.industry_multiplier is not None:
        current_settings.industry_multiplier = settings_input.industry_multiplier

    if settings_input.diagnostic_frequency is not None:
        current_settings.diagnostic_frequency = settings_input.diagnostic_frequency

    # Save to database
    client.settings = current_settings.to_json()
    db.commit()

    log_secure_operation(
        "client_settings_updated",
        f"Client {client_id} settings saved for user {current_user.id}"
    )

    return ClientSettingsResponse(
        materiality_override=current_settings.materiality_override.to_dict() if current_settings.materiality_override else None,
        notes=current_settings.notes,
        industry_multiplier=current_settings.industry_multiplier,
        diagnostic_frequency=current_settings.diagnostic_frequency,
    )


@app.post("/settings/materiality/preview")
async def preview_materiality(
    preview_input: MaterialityPreviewInput,
    current_user: User = Depends(require_current_user)
):
    """
    Preview a materiality calculation.

    Sprint 21: Customization & Practice Settings

    This endpoint allows users to preview what their materiality threshold
    would be given sample financial data, without running a full diagnostic.

    ZERO-STORAGE COMPLIANCE:
    - Takes financial data as INPUT parameters (ephemeral)
    - Returns calculated threshold as OUTPUT
    - Never stores the financial data

    Args:
        preview_input: Formula and sample financial data

    Returns:
        Preview with calculated threshold and explanation
    """
    formula = MaterialityFormula(
        type=MaterialityFormulaType(preview_input.formula.type),
        value=preview_input.formula.value,
        min_threshold=preview_input.formula.min_threshold,
        max_threshold=preview_input.formula.max_threshold,
    )

    preview = MaterialityCalculator.preview(
        formula=formula,
        total_revenue=preview_input.total_revenue,
        total_assets=preview_input.total_assets,
        total_equity=preview_input.total_equity,
    )

    return preview


@app.get("/settings/materiality/resolve")
async def resolve_materiality(
    client_id: Optional[int] = Query(default=None),
    session_threshold: Optional[float] = Query(default=None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Resolve the effective materiality configuration.

    Sprint 21: Customization & Practice Settings

    This endpoint returns the resolved materiality configuration based on:
    1. Session threshold (if provided)
    2. Client-specific settings (if client_id provided)
    3. Practice-level defaults
    4. System default (Fixed $500)

    Useful for prepopulating the diagnostic view with the user's configured threshold.

    Args:
        client_id: Optional client ID to include client-specific settings
        session_threshold: Optional direct threshold override

    Returns:
        Resolved materiality configuration
    """
    # Get practice settings
    practice_settings = PracticeSettings.from_json(current_user.settings or "{}")

    # Get client settings if client_id provided
    client_settings = None
    if client_id:
        manager = ClientManager(db)
        client = manager.get_client(current_user.id, client_id)
        if client:
            client_settings = ClientSettings.from_json(client.settings or "{}")

    # Resolve configuration
    config = resolve_materiality_config(
        practice_settings=practice_settings,
        client_settings=client_settings,
        session_threshold=session_threshold
    )

    return {
        "formula": config.formula.to_dict(),
        "formula_display": config.formula.get_display_string(),
        "session_override": config.session_override,
        "source": "session" if config.session_override else (
            "client" if client_settings and client_settings.materiality_override else "practice"
        ),
    }


# =============================================================================
# SPRINT 19: DIAGNOSTIC SUMMARY ENDPOINTS (Variance Intelligence)
# =============================================================================

class DiagnosticSummaryCreate(BaseModel):
    """Input model for saving a diagnostic summary."""
    client_id: int
    filename: str
    # Category totals
    total_assets: float = 0.0
    current_assets: float = 0.0
    inventory: float = 0.0
    total_liabilities: float = 0.0
    current_liabilities: float = 0.0
    total_equity: float = 0.0
    total_revenue: float = 0.0
    cost_of_goods_sold: float = 0.0
    total_expenses: float = 0.0
    # Ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    gross_margin: Optional[float] = None
    # Diagnostic metadata
    total_debits: float = 0.0
    total_credits: float = 0.0
    was_balanced: bool = True
    anomaly_count: int = 0
    materiality_threshold: float = 0.0
    row_count: int = 0


class DiagnosticSummaryResponse(BaseModel):
    """Response model for a diagnostic summary."""
    id: int
    client_id: int
    user_id: int
    timestamp: str
    filename_hash: Optional[str]
    filename_display: Optional[str]
    # Category totals
    total_assets: float
    current_assets: float
    inventory: float
    total_liabilities: float
    current_liabilities: float
    total_equity: float
    total_revenue: float
    cost_of_goods_sold: float
    total_expenses: float
    # Ratios
    current_ratio: Optional[float]
    quick_ratio: Optional[float]
    debt_to_equity: Optional[float]
    gross_margin: Optional[float]
    # Diagnostic metadata
    total_debits: float
    total_credits: float
    was_balanced: bool
    anomaly_count: int
    materiality_threshold: float
    row_count: int


@app.post("/diagnostics/summary", response_model=DiagnosticSummaryResponse)
async def save_diagnostic_summary(
    summary_data: DiagnosticSummaryCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a diagnostic summary for variance tracking.

    Sprint 19: Comparative Analytics & Ratio Engine

    ZERO-STORAGE COMPLIANCE:
    - Stores ONLY aggregate category totals
    - NEVER stores individual account names or balances
    - Enables "Variance Intelligence" between diagnostic runs

    Args:
        summary_data: Aggregate totals and metadata from diagnostic run

    Returns:
        The created diagnostic summary

    Raises:
        401: Not authenticated
        404: Client not found
    """
    log_secure_operation(
        "diagnostic_summary_save",
        f"User {current_user.id} saving summary for client {summary_data.client_id}"
    )

    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == summary_data.client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Create diagnostic summary
    db_summary = DiagnosticSummary(
        client_id=summary_data.client_id,
        user_id=current_user.id,
        filename_hash=hash_filename(summary_data.filename),
        filename_display=get_filename_display(summary_data.filename),
        # Category totals
        total_assets=summary_data.total_assets,
        current_assets=summary_data.current_assets,
        inventory=summary_data.inventory,
        total_liabilities=summary_data.total_liabilities,
        current_liabilities=summary_data.current_liabilities,
        total_equity=summary_data.total_equity,
        total_revenue=summary_data.total_revenue,
        cost_of_goods_sold=summary_data.cost_of_goods_sold,
        total_expenses=summary_data.total_expenses,
        # Ratios
        current_ratio=summary_data.current_ratio,
        quick_ratio=summary_data.quick_ratio,
        debt_to_equity=summary_data.debt_to_equity,
        gross_margin=summary_data.gross_margin,
        # Metadata
        total_debits=summary_data.total_debits,
        total_credits=summary_data.total_credits,
        was_balanced=summary_data.was_balanced,
        anomaly_count=summary_data.anomaly_count,
        materiality_threshold=summary_data.materiality_threshold,
        row_count=summary_data.row_count,
    )

    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)

    return DiagnosticSummaryResponse(
        id=db_summary.id,
        client_id=db_summary.client_id,
        user_id=db_summary.user_id,
        timestamp=db_summary.timestamp.isoformat(),
        filename_hash=db_summary.filename_hash,
        filename_display=db_summary.filename_display,
        total_assets=db_summary.total_assets,
        current_assets=db_summary.current_assets,
        inventory=db_summary.inventory,
        total_liabilities=db_summary.total_liabilities,
        current_liabilities=db_summary.current_liabilities,
        total_equity=db_summary.total_equity,
        total_revenue=db_summary.total_revenue,
        cost_of_goods_sold=db_summary.cost_of_goods_sold,
        total_expenses=db_summary.total_expenses,
        current_ratio=db_summary.current_ratio,
        quick_ratio=db_summary.quick_ratio,
        debt_to_equity=db_summary.debt_to_equity,
        gross_margin=db_summary.gross_margin,
        total_debits=db_summary.total_debits,
        total_credits=db_summary.total_credits,
        was_balanced=db_summary.was_balanced,
        anomaly_count=db_summary.anomaly_count,
        materiality_threshold=db_summary.materiality_threshold,
        row_count=db_summary.row_count,
    )


@app.get("/diagnostics/summary/{client_id}/previous", response_model=Optional[DiagnosticSummaryResponse])
async def get_previous_diagnostic_summary(
    client_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the most recent diagnostic summary for a client.

    Sprint 19: Variance Intelligence

    Used to compare current diagnostic run against previous run.

    Args:
        client_id: The client ID to fetch summary for

    Returns:
        Most recent diagnostic summary, or null if none exists

    Raises:
        401: Not authenticated
        404: Client not found
    """
    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get most recent summary
    summary = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id
    ).order_by(DiagnosticSummary.timestamp.desc()).first()

    if not summary:
        return None

    return DiagnosticSummaryResponse(
        id=summary.id,
        client_id=summary.client_id,
        user_id=summary.user_id,
        timestamp=summary.timestamp.isoformat(),
        filename_hash=summary.filename_hash,
        filename_display=summary.filename_display,
        total_assets=summary.total_assets,
        current_assets=summary.current_assets,
        inventory=summary.inventory,
        total_liabilities=summary.total_liabilities,
        current_liabilities=summary.current_liabilities,
        total_equity=summary.total_equity,
        total_revenue=summary.total_revenue,
        cost_of_goods_sold=summary.cost_of_goods_sold,
        total_expenses=summary.total_expenses,
        current_ratio=summary.current_ratio,
        quick_ratio=summary.quick_ratio,
        debt_to_equity=summary.debt_to_equity,
        gross_margin=summary.gross_margin,
        total_debits=summary.total_debits,
        total_credits=summary.total_credits,
        was_balanced=summary.was_balanced,
        anomaly_count=summary.anomaly_count,
        materiality_threshold=summary.materiality_threshold,
        row_count=summary.row_count,
    )


@app.get("/diagnostics/summary/{client_id}/history")
async def get_diagnostic_history(
    client_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get diagnostic summary history for a client.

    Sprint 19: Trend Analysis

    Returns list of previous diagnostic summaries for trend analysis.

    Args:
        client_id: The client ID
        limit: Maximum number of summaries to return

    Returns:
        List of diagnostic summaries, newest first

    Raises:
        401: Not authenticated
        404: Client not found
    """
    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get summary history
    summaries = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id
    ).order_by(DiagnosticSummary.timestamp.desc()).limit(limit).all()

    return {
        "client_id": client_id,
        "client_name": client.name,
        "summaries": [s.to_dict() for s in summaries],
        "total_count": len(summaries),
    }


# =============================================================================
# DAY 11: WORKBOOK INSPECTION ENDPOINT
# =============================================================================

@app.post("/audit/inspect-workbook")
async def inspect_workbook_endpoint(
    file: UploadFile = File(...)
):
    """
    Inspect an Excel workbook to retrieve sheet metadata.

    Day 11: Two-phase flow for multi-sheet Excel support.
    - Phase 1: Call this endpoint to get sheet names/row counts
    - Phase 2: Call /audit/trial-balance with selected_sheets parameter

    ZERO-STORAGE: All processing is in-memory. No data written to disk.

    Args:
        file: The Excel file (.xlsx or .xls)

    Returns:
        WorkbookInfo with sheet names, row counts, and column headers.
        If file is not Excel or has only one sheet, returns appropriate metadata.
    """
    log_secure_operation(
        "inspect_workbook_upload",
        f"Inspecting workbook: {file.filename}"
    )

    try:
        # Read file bytes into memory - NO DISK STORAGE
        file_bytes = await file.read()

        # Check if it's an Excel file
        if not is_excel_file(file.filename or ""):
            # Return single-sheet info for CSV files
            clear_memory()
            return {
                "filename": file.filename,
                "sheet_count": 1,
                "sheets": [{
                    "name": "Sheet1",
                    "row_count": -1,  # Unknown until processed
                    "column_count": -1,
                    "columns": [],
                    "has_data": True
                }],
                "total_rows": -1,
                "is_multi_sheet": False,
                "format": "csv",
                "requires_sheet_selection": False
            }

        # Inspect the Excel workbook
        workbook_info = inspect_workbook(file_bytes, file.filename or "")

        # Clear file bytes after processing
        del file_bytes
        clear_memory()

        # Add flag for frontend to know if sheet selection is needed
        result = workbook_info.to_dict()
        result["requires_sheet_selection"] = workbook_info.is_multi_sheet

        return result

    except ValueError as e:
        log_secure_operation("inspect_workbook_error", str(e))
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        log_secure_operation("inspect_workbook_error", str(e))
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to inspect workbook: {str(e)}"
        )


@app.post("/audit/trial-balance")
async def audit_trial_balance(
    file: UploadFile = File(...),
    materiality_threshold: float = Form(default=0.0, ge=0.0),
    account_type_overrides: Optional[str] = Form(default=None),
    column_mapping: Optional[str] = Form(default=None),
    selected_sheets: Optional[str] = Form(default=None)
):
    """
    Analyze a trial balance file for balance validation using streaming processing.

    HIGH-PERFORMANCE: File is processed in chunks for memory efficiency.
    Handles files larger than available RAM.

    ZERO-STORAGE: All processing is in-memory. No data written to disk.

    Accepts CSV or Excel files with 'Debit' and 'Credit' columns.

    Day 9.2: Now includes intelligent column detection with confidence scoring.
    If column_detection.requires_mapping is True in the response, the frontend
    should prompt the user to select columns and re-submit with column_mapping.

    Day 11: Multi-sheet Excel support with Summation Consolidation.
    If selected_sheets is provided, processes multiple sheets and aggregates results.

    Args:
        file: The trial balance file (CSV or Excel)
        materiality_threshold: Dollar amount threshold for materiality classification.
            Balances below this threshold are marked as "immaterial" (Indistinct).
            Default: 0.0 (flag all abnormal balances as material)
        account_type_overrides: Optional JSON string of account_name -> category mappings.
            Example: '{"Cash": "asset", "Misc Income": "revenue"}'
            Valid categories: asset, liability, equity, revenue, expense
            Zero-Storage compliant: overrides are session-only, not persisted.
        column_mapping: Optional JSON string specifying which columns to use.
            Example: '{"account_column": "GL Account", "debit_column": "DR", "credit_column": "CR"}'
            If provided, bypasses auto-detection entirely (user override priority).
            Zero-Storage compliant: mappings are session-only, not persisted.
        selected_sheets: Optional JSON string list of sheet names for multi-sheet Excel.
            Example: '["Sheet1", "Q1 Data", "Q2 Data"]'
            If provided, performs Summation Consolidation across selected sheets.
            Zero-Storage compliant: selections are session-only, not persisted.
    """
    # Parse account type overrides (Zero-Storage: session-only)
    overrides_dict: Optional[dict[str, str]] = None
    if account_type_overrides:
        try:
            overrides_dict = json.loads(account_type_overrides)
            log_secure_operation(
                "audit_overrides",
                f"Received {len(overrides_dict)} account type overrides"
            )
        except json.JSONDecodeError:
            log_secure_operation("audit_overrides_error", "Invalid JSON in overrides, ignoring")

    # Parse column mapping (Day 9.2 - Zero-Storage: session-only)
    column_mapping_dict: Optional[dict[str, str]] = None
    if column_mapping:
        try:
            column_mapping_dict = json.loads(column_mapping)
            log_secure_operation(
                "audit_column_mapping",
                f"Received user column mapping: {column_mapping_dict}"
            )
        except json.JSONDecodeError:
            log_secure_operation("audit_column_mapping_error", "Invalid JSON in column_mapping, ignoring")

    # Day 11: Parse selected sheets for multi-sheet consolidation
    selected_sheets_list: Optional[list[str]] = None
    if selected_sheets:
        try:
            selected_sheets_list = json.loads(selected_sheets)
            if not isinstance(selected_sheets_list, list):
                selected_sheets_list = None
                log_secure_operation("audit_sheets_error", "selected_sheets must be a list, ignoring")
            else:
                log_secure_operation(
                    "audit_selected_sheets",
                    f"Received {len(selected_sheets_list)} selected sheets: {selected_sheets_list}"
                )
        except json.JSONDecodeError:
            log_secure_operation("audit_sheets_error", "Invalid JSON in selected_sheets, ignoring")

    log_secure_operation(
        "audit_upload_streaming",
        f"Processing file: {file.filename} (threshold: ${materiality_threshold:,.2f}, chunk_size: {DEFAULT_CHUNK_SIZE})"
    )

    try:
        # Read file bytes into memory - NO DISK STORAGE
        file_bytes = await file.read()

        # Day 11: Route to multi-sheet audit if sheets are selected
        if selected_sheets_list and len(selected_sheets_list) > 0:
            result = audit_trial_balance_multi_sheet(
                file_bytes=file_bytes,
                filename=file.filename or "",
                selected_sheets=selected_sheets_list,
                materiality_threshold=materiality_threshold,
                chunk_size=DEFAULT_CHUNK_SIZE,
                account_type_overrides=overrides_dict,
                column_mapping=column_mapping_dict
            )
        else:
            # Use standard streaming audit for single-sheet/CSV
            result = audit_trial_balance_streaming(
                file_bytes=file_bytes,
                filename=file.filename or "",
                materiality_threshold=materiality_threshold,
                chunk_size=DEFAULT_CHUNK_SIZE,
                account_type_overrides=overrides_dict,
                column_mapping=column_mapping_dict
            )

        # Clear file bytes after processing
        del file_bytes
        clear_memory()

        return result

    except Exception as e:
        log_secure_operation("audit_error", str(e))
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process file: {str(e)}"
        )


# =============================================================================
# DAY 12: PDF EXPORT ENDPOINT
# =============================================================================

class AuditResultInput(BaseModel):
    """Input model for PDF export - accepts audit result JSON."""
    status: str
    balanced: bool
    total_debits: float
    total_credits: float
    difference: float
    row_count: int
    message: str
    abnormal_balances: list
    has_risk_alerts: bool
    materiality_threshold: float
    material_count: int
    immaterial_count: int
    filename: str = "audit"
    # Optional fields
    classification_summary: Optional[dict] = None
    column_detection: Optional[dict] = None
    risk_summary: Optional[dict] = None
    is_consolidated: Optional[bool] = None
    sheet_count: Optional[int] = None
    selected_sheets: Optional[list] = None
    sheet_results: Optional[dict] = None


@app.post("/export/pdf")
async def export_pdf_report(audit_result: AuditResultInput):
    """
    Generate and stream a PDF audit report.

    Day 12: Surgical Export & Report Generation

    ZERO-STORAGE: The PDF is generated entirely in-memory using BytesIO.
    It is streamed directly to the user's browser and never written to disk.

    Args:
        audit_result: The audit result JSON from a previous audit

    Returns:
        StreamingResponse with PDF file attachment
    """
    log_secure_operation(
        "pdf_export_start",
        f"Generating PDF report for: {audit_result.filename}"
    )

    try:
        # Convert Pydantic model to dict
        result_dict = audit_result.model_dump()

        # Generate PDF in memory
        pdf_bytes = generate_audit_report(result_dict, audit_result.filename)

        # Create streaming response
        # The PDF is in memory as bytes - we yield it in chunks for streaming
        def iter_pdf():
            # Yield in 8KB chunks for efficient streaming
            chunk_size = 8192
            for i in range(0, len(pdf_bytes), chunk_size):
                yield pdf_bytes[i:i + chunk_size]

        # Sprint 18: Generate filename with Diagnostic convention
        # Format: [Client]_[Domain]_Diagnostic_[Date].pdf
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in audit_result.filename if c.isalnum() or c in "._-")
        if not safe_filename:
            safe_filename = "TrialBalance"
        download_filename = f"{safe_filename}_Diagnostic_{timestamp}.pdf"

        log_secure_operation(
            "pdf_export_complete",
            f"PDF generated: {len(pdf_bytes)} bytes, filename: {download_filename}"
        )

        return StreamingResponse(
            iter_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(pdf_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("pdf_export_error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF report: {str(e)}"
        )


# =============================================================================
# SPRINT 20: EXCEL WORKPAPER EXPORT ENDPOINT
# =============================================================================

@app.post("/export/excel")
async def export_excel_workpaper(audit_result: AuditResultInput):
    """
    Generate and stream an Excel workpaper.

    Sprint 20: Document Hardening & Loop Resolution

    ZERO-STORAGE: The Excel file is generated entirely in-memory using BytesIO.
    It is streamed directly to the user's browser and never written to disk.

    Workpaper Tabs:
    - Summary: Executive overview with key metrics
    - Standardized TB: Formatted trial balance with classifications
    - Flagged Anomalies: Material and immaterial anomaly details
    - Key Ratios: Financial ratio analysis and interpretations

    Args:
        audit_result: The audit result JSON from a previous audit

    Returns:
        StreamingResponse with Excel file attachment
    """
    log_secure_operation(
        "excel_export_start",
        f"Generating Excel workpaper for: {audit_result.filename}"
    )

    try:
        # Convert Pydantic model to dict
        result_dict = audit_result.model_dump()

        # Generate Excel in memory
        excel_bytes = generate_workpaper(result_dict, audit_result.filename)

        # Create streaming response
        def iter_excel():
            # Yield in 8KB chunks for efficient streaming
            chunk_size = 8192
            for i in range(0, len(excel_bytes), chunk_size):
                yield excel_bytes[i:i + chunk_size]

        # Generate filename with Diagnostic convention
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in audit_result.filename if c.isalnum() or c in "._-")
        if not safe_filename:
            safe_filename = "TrialBalance"
        download_filename = f"{safe_filename}_Workpaper_{timestamp}.xlsx"

        log_secure_operation(
            "excel_export_complete",
            f"Excel generated: {len(excel_bytes)} bytes, filename: {download_filename}"
        )

        return StreamingResponse(
            iter_excel(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(excel_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("excel_export_error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Excel workpaper: {str(e)}"
        )



# =============================================================================
# SPRINT 25: FLUX & VARIANCE INTELLIGENCE
# =============================================================================

@app.post("/diagnostics/flux")
async def flux_analysis(
    current_file: UploadFile = File(...),
    prior_file: UploadFile = File(...),
    materiality: float = Form(0.0),
    current_user: User = Depends(require_current_user)
):
    """
    Perform a Flux (Period-over-Period) Analysis.

    Zero-Storage Compliance:
    - Streams both files into memory (sequentially)
    - Compares them in-memory
    - Returns analysis result
    - Discards all data immediately

    Args:
        current_file: Current period trial balance
        prior_file: Prior period trial balance
        materiality: Threshold for variance flagging

    Returns:
        JSON with FluxResult and ReconResult
    """
    log_secure_operation("flux_start", f"Starting Flux Analysis for user {current_user.id}")

    current_balances = {}
    prior_balances = {}
    
    try:
        # 1. Process Current File
        # Use streaming auditor to handle large files memory-efficiently
        content_curr = await current_file.read()
        from audit_engine import StreamingAuditor, process_tb_chunked
        
        auditor_curr = StreamingAuditor(materiality_threshold=materiality)
        for chunk, rows in process_tb_chunked(content_curr, current_file.filename, DEFAULT_CHUNK_SIZE):
            auditor_curr.process_chunk(chunk, rows)
            del chunk
        
        # Extract balances and types
        classified_curr = auditor_curr.get_classified_accounts()
        for acct, bals in auditor_curr.account_balances.items():
            net = bals["debit"] - bals["credit"]
            acct_type = classified_curr.get(acct, "Unknown")
            current_balances[acct] = {"net": net, "type": acct_type, "debit": bals["debit"], "credit": bals["credit"]}
        
        # Explicit cleanup
        auditor_curr.clear()
        del auditor_curr
        del content_curr
        clear_memory()

        # 2. Process Prior File
        content_prior = await prior_file.read()
        
        auditor_prior = StreamingAuditor(materiality_threshold=materiality)
        for chunk, rows in process_tb_chunked(content_prior, prior_file.filename, DEFAULT_CHUNK_SIZE):
            auditor_prior.process_chunk(chunk, rows)
            del chunk
            
        # Extract balances and types
        classified_prior = auditor_prior.get_classified_accounts()
        for acct, bals in auditor_prior.account_balances.items():
            net = bals["debit"] - bals["credit"]
            acct_type = classified_prior.get(acct, "Unknown")
            prior_balances[acct] = {"net": net, "type": acct_type, "debit": bals["debit"], "credit": bals["credit"]}

        # Explicit cleanup
        auditor_prior.clear()
        del auditor_prior
        del content_prior
        clear_memory()

        # 3. Flux Engine Analysis
        flux_engine = FluxEngine(materiality_threshold=materiality)
        flux_result = flux_engine.compare(current_balances, prior_balances)

        # 4. Recon Engine Analysis
        recon_engine = ReconEngine(materiality_threshold=materiality)
        recon_result = recon_engine.calculate_scores(flux_result)

        log_secure_operation("flux_complete", f"Flux analysis complete: {len(flux_result.items)} items")

        return {
            "flux": flux_result.to_dict(),
            "recon": recon_result.to_dict()
        }

    except Exception as e:
        log_secure_operation("flux_error", f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Flux processing failed: {str(e)}")
    finally:
        clear_memory()


# =============================================================================
# LEAD SHEET EXPORT MODELS & ENDPOINT
# =============================================================================

class FluxItemInput(BaseModel):
    account: str
    type: str
    current: float
    prior: float
    delta_amount: float
    delta_percent: Optional[float] = None
    display_percent: Optional[str] = None
    is_new: bool
    is_removed: bool
    sign_flip: bool
    risk_level: str
    risk_reasons: List[str]

class FluxResultSummary(BaseModel):
    total_items: int
    high_risk_count: int
    medium_risk_count: int
    new_accounts: int
    removed_accounts: int
    threshold: float

class FluxResultInput(BaseModel):
    items: List[FluxItemInput]
    summary: FluxResultSummary

class ReconScoreInput(BaseModel):
    account: str
    score: int
    band: str
    factors: List[str]
    action: str

class ReconStats(BaseModel):
    high: int
    medium: int
    low: int

class ReconResultInput(BaseModel):
    scores: List[ReconScoreInput]
    stats: ReconStats

class LeadSheetInput(BaseModel):
    flux: FluxResultInput
    recon: ReconResultInput
    filename: str

@app.post("/export/leadsheets")
async def export_leadsheets(
    payload: LeadSheetInput, 
    current_user: User = Depends(require_current_user)
):
    """
    Generate Excel Lead Sheets from analysis result.
    
    Args:
        payload: The JSON result from /diagnostics/flux (FluxResult and ReconResult)
        
    Returns:
        Excel file stream
    """
    log_secure_operation("leadsheet_export", f"Exporting lead sheets for {len(payload.flux.items)} items")

    try:
        # Reconstruct internal FluxResult object
        flux_items = []
        for i in payload.flux.items:
            flux_items.append(FluxItem(
                account_name=i.account,
                account_type=i.type,
                current_balance=i.current,
                prior_balance=i.prior,
                delta_amount=i.delta_amount,
                delta_percent=i.delta_percent if i.delta_percent is not None else 0.0,
                is_new_account=i.is_new,
                is_removed_account=i.is_removed,
                has_sign_flip=i.sign_flip,
                risk_level=try_parse_risk(i.risk_level),
                risk_reasons=i.risk_reasons
            ))
            
        flux_result = FluxResult(
            items=flux_items,
            total_items=payload.flux.summary.total_items,
            high_risk_count=payload.flux.summary.high_risk_count,
            medium_risk_count=payload.flux.summary.medium_risk_count,
            new_accounts_count=payload.flux.summary.new_accounts,
            removed_accounts_count=payload.flux.summary.removed_accounts,
            materiality_threshold=payload.flux.summary.threshold
        )

        # Reconstruct internal ReconResult object
        recon_scores = []
        for s in payload.recon.scores:
            recon_scores.append(ReconScore(
                account_name=s.account,
                risk_score=s.score,
                risk_band=try_parse_risk_band(s.band),
                factors=s.factors,
                suggested_action=s.action
            ))
            
        recon_result = ReconResult(
            scores=recon_scores,
            high_risk_count=payload.recon.stats.high,
            medium_risk_count=payload.recon.stats.medium,
            low_risk_count=payload.recon.stats.low
        )

        # Generate Excel
        excel_bytes = generate_leadsheets(flux_result, recon_result, payload.filename)

        # Generate formatted filename
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in payload.filename if c.isalnum() or c in "._-")
        download_filename = f"LeadSheets_{safe_filename}_{timestamp}.xlsx"

        log_secure_operation("leadsheet_generated", f"Generated {len(excel_bytes)} bytes")

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Length": str(len(excel_bytes)),
            }
        )

    except Exception as e:
        log_secure_operation("leadsheet_error", f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def try_parse_risk(risk_str: str) -> FluxRisk:
    try:
        return FluxRisk(risk_str)
    except ValueError:
        return FluxRisk.LOW

def try_parse_risk_band(band_str: str) -> RiskBand:
    try:
        return RiskBand(band_str)
    except ValueError:
        return RiskBand.LOW


if __name__ == "__main__":
    import uvicorn
    print_config_summary()
    uvicorn.run(app, host=API_HOST, port=API_PORT)
