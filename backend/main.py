"""
Paciolus Backend API
"""

import csv
import hashlib
import io
import json
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Query, Path as PathParam, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
from models import User, ActivityLog, Client, Industry, DiagnosticSummary, PeriodType
from ratio_engine import (
    CategoryTotals, calculate_analytics,
    TrendAnalyzer, PeriodSnapshot, create_period_snapshot
)
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
    version="0.16.0"
)

# CORS configuration from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for responses > 500 bytes
# Sprint 41: Reduces response size by 60-70% for large JSON payloads
app.add_middleware(GZipMiddleware, minimum_size=500)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

RATE_LIMIT_AUDIT = "10/minute"
RATE_LIMIT_AUTH = "5/minute"
RATE_LIMIT_EXPORT = "20/minute"
RATE_LIMIT_DEFAULT = "60/minute"

WAITLIST_FILE = Path(__file__).parent / "waitlist.csv"
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
MAX_FILE_SIZE_MB = 100


async def validate_file_size(file: UploadFile) -> bytes:
    """Read uploaded file with size validation. Raises 413 if too large."""
    contents = bytearray()
    chunk_size = 1024 * 1024

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        contents.extend(chunk)

        if len(contents) > MAX_FILE_SIZE_BYTES:
            log_secure_operation(
                "file_size_exceeded",
                f"File {file.filename} exceeds {MAX_FILE_SIZE_MB}MB limit"
            )
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB. "
                       f"Please reduce file size or split into smaller files."
            )

    return bytes(contents)


@app.on_event("startup")
async def startup_event():
    init_db()
    log_secure_operation("app_startup", "Paciolus API started")


async def require_client(
    client_id: int = PathParam(..., description="The ID of the client"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
) -> Client:
    """Validate client ownership. Raises 404 if not found or not owned by user."""
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
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        version="0.13.0"
    )


@app.post("/waitlist", response_model=WaitlistResponse)
async def join_waitlist(entry: WaitlistEntry):
    """Add email to waitlist (only non-ephemeral storage in the system)."""
    try:
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


@app.post("/auth/register", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    log_secure_operation("auth_register_attempt", f"Registration attempt: {user_data.email[:10]}...")

    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists"
        )

    is_valid, issues = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={"message": "Password does not meet requirements", "issues": issues}
        )

    user = create_user(db, user_data)
    token, expires = create_access_token(user.id, user.email)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@app.post("/auth/login", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    log_secure_operation("auth_login_attempt", f"Login attempt: {credentials.email[:10]}...")

    user = authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

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
    return UserResponse.model_validate(current_user)


def hash_filename(filename: str) -> str:
    """SHA-256 hash of filename for privacy-preserving storage."""
    return hashlib.sha256(filename.encode('utf-8')).hexdigest()


def get_filename_display(filename: str, max_length: int = 12) -> str:
    """Truncated filename preview for display."""
    if len(filename) <= max_length:
        return filename
    return filename[:max_length - 3] + "..."


class ActivityLogCreate(BaseModel):
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
    """Log audit activity. Stores only aggregate metadata, filename is hashed."""
    log_secure_operation(
        "activity_log_create",
        f"User {current_user.id} logging audit activity"
    )

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
    """Clear all activity history for the user. Cannot be undone."""
    log_secure_operation(
        "activity_clear_request",
        f"User {current_user.id} requesting activity history deletion"
    )

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
    total_clients: int
    assessments_today: int
    last_assessment_date: Optional[str]
    total_assessments: int


@app.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for workspace header."""
    log_secure_operation("dashboard_stats_fetch", f"User {current_user.id} fetching dashboard stats")

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    total_clients = db.query(func.count(Client.id)).filter(
        Client.user_id == current_user.id
    ).scalar() or 0

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


class ClientCreate(BaseModel):
    name: str
    industry: Optional[str] = "other"
    fiscal_year_end: Optional[str] = "12-31"
    settings: Optional[str] = "{}"


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    settings: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    user_id: int
    name: str
    industry: str
    fiscal_year_end: str
    created_at: str
    updated_at: str
    settings: str


class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    total_count: int
    page: int
    page_size: int


class IndustryOption(BaseModel):
    value: str
    label: str


@app.get("/clients/industries", response_model=List[IndustryOption])
async def get_industries(response: Response):
    """Get available industry options. Static data, cached aggressively."""
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
    """Get paginated list of clients for the user."""
    log_secure_operation("clients_list", f"User {current_user.id} fetching client list (page {page})")

    manager = ClientManager(db)

    if search:
        clients = manager.search_clients(current_user.id, search, limit=page_size)
        total_count = len(clients)
    else:
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
class MaterialityFormulaInput(BaseModel):
    type: str = "fixed"
    value: float = 500.0
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None


class PracticeSettingsInput(BaseModel):
    default_materiality: Optional[MaterialityFormulaInput] = None
    show_immaterial_by_default: Optional[bool] = None
    default_fiscal_year_end: Optional[str] = None
    theme_preference: Optional[str] = None
    default_export_format: Optional[str] = None
    auto_save_summaries: Optional[bool] = None


class PracticeSettingsResponse(BaseModel):
    default_materiality: dict
    show_immaterial_by_default: bool
    default_fiscal_year_end: str
    theme_preference: str
    default_export_format: str
    auto_save_summaries: bool


class ClientSettingsInput(BaseModel):
    materiality_override: Optional[MaterialityFormulaInput] = None
    notes: Optional[str] = None
    industry_multiplier: Optional[float] = None
    diagnostic_frequency: Optional[str] = None


class ClientSettingsResponse(BaseModel):
    materiality_override: Optional[dict]
    notes: str
    industry_multiplier: float
    diagnostic_frequency: str


class MaterialityPreviewInput(BaseModel):
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


class DiagnosticSummaryCreate(BaseModel):
    client_id: int
    filename: str
    # Sprint 33: Period identification for trend analysis
    period_date: Optional[str] = None  # ISO format date string (YYYY-MM-DD)
    period_type: Optional[str] = None  # monthly, quarterly, annual
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
    operating_expenses: float = 0.0  # Sprint 33: For operating margin
    # Core 4 Ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    gross_margin: Optional[float] = None
    # Sprint 33: Advanced 4 Ratios
    net_profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
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
    # Sprint 33: Period identification
    period_date: Optional[str] = None
    period_type: Optional[str] = None
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
    operating_expenses: float = 0.0  # Sprint 33
    # Core 4 Ratios
    current_ratio: Optional[float]
    quick_ratio: Optional[float]
    debt_to_equity: Optional[float]
    gross_margin: Optional[float]
    # Sprint 33: Advanced 4 Ratios
    net_profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
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

    # Sprint 33: Parse period_date if provided
    from datetime import date as date_type
    period_date = None
    if summary_data.period_date:
        try:
            period_date = date_type.fromisoformat(summary_data.period_date)
        except ValueError:
            log_secure_operation("period_date_parse_error", f"Invalid date format: {summary_data.period_date}")

    # Sprint 33: Parse period_type if provided
    period_type = None
    if summary_data.period_type:
        try:
            period_type = PeriodType(summary_data.period_type)
        except ValueError:
            log_secure_operation("period_type_parse_error", f"Invalid period type: {summary_data.period_type}")

    # Create diagnostic summary
    db_summary = DiagnosticSummary(
        client_id=summary_data.client_id,
        user_id=current_user.id,
        # Sprint 33: Period identification
        period_date=period_date,
        period_type=period_type,
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
        operating_expenses=summary_data.operating_expenses,  # Sprint 33
        # Core 4 Ratios
        current_ratio=summary_data.current_ratio,
        quick_ratio=summary_data.quick_ratio,
        debt_to_equity=summary_data.debt_to_equity,
        gross_margin=summary_data.gross_margin,
        # Sprint 33: Advanced 4 Ratios
        net_profit_margin=summary_data.net_profit_margin,
        operating_margin=summary_data.operating_margin,
        return_on_assets=summary_data.return_on_assets,
        return_on_equity=summary_data.return_on_equity,
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
        # Sprint 33: Period identification
        period_date=db_summary.period_date.isoformat() if db_summary.period_date else None,
        period_type=db_summary.period_type.value if db_summary.period_type else None,
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
        operating_expenses=db_summary.operating_expenses or 0.0,  # Sprint 33
        # Core 4 Ratios
        current_ratio=db_summary.current_ratio,
        quick_ratio=db_summary.quick_ratio,
        debt_to_equity=db_summary.debt_to_equity,
        gross_margin=db_summary.gross_margin,
        # Sprint 33: Advanced 4 Ratios
        net_profit_margin=db_summary.net_profit_margin,
        operating_margin=db_summary.operating_margin,
        return_on_assets=db_summary.return_on_assets,
        return_on_equity=db_summary.return_on_equity,
        # Diagnostic metadata
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
        # Sprint 33: Period identification
        period_date=summary.period_date.isoformat() if summary.period_date else None,
        period_type=summary.period_type.value if summary.period_type else None,
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
        operating_expenses=summary.operating_expenses or 0.0,  # Sprint 33
        # Core 4 Ratios
        current_ratio=summary.current_ratio,
        quick_ratio=summary.quick_ratio,
        debt_to_equity=summary.debt_to_equity,
        gross_margin=summary.gross_margin,
        # Sprint 33: Advanced 4 Ratios
        net_profit_margin=summary.net_profit_margin,
        operating_margin=summary.operating_margin,
        return_on_assets=summary.return_on_assets,
        return_on_equity=summary.return_on_equity,
        # Diagnostic metadata
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
# SPRINT 33: TREND ANALYSIS ENDPOINTS
# =============================================================================

@app.get("/clients/{client_id}/trends")
async def get_client_trends(
    client_id: int,
    period_type: Optional[str] = Query(default=None, description="Filter by period type: monthly, quarterly, annual"),
    limit: int = Query(default=12, ge=2, le=36, description="Number of periods to analyze"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get trend analysis for a client's historical diagnostic data.

    Sprint 33: Trend Analysis Foundation

    ZERO-STORAGE COMPLIANCE:
    - Analyzes ONLY aggregate totals and ratios
    - NEVER processes raw transaction data
    - Returns calculated trends, not stored data

    Args:
        client_id: The client ID to analyze trends for
        period_type: Optional filter for period type (monthly, quarterly, annual)
        limit: Maximum number of periods to include (default 12, max 36)

    Returns:
        Trend analysis including:
        - Category total trends (assets, liabilities, revenue, etc.)
        - Ratio trends (current ratio, quick ratio, margins, returns)
        - Overall direction for each metric
        - Period-over-period changes

    Raises:
        401: Not authenticated
        404: Client not found
        400: Insufficient data for trend analysis (need at least 2 periods)
    """
    log_secure_operation(
        "trend_analysis_request",
        f"User {current_user.id} requesting trends for client {client_id}"
    )

    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Build query for historical summaries
    query = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id
    )

    # Filter by period type if specified
    if period_type:
        try:
            pt = PeriodType(period_type)
            query = query.filter(DiagnosticSummary.period_type == pt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period_type. Must be one of: monthly, quarterly, annual"
            )

    # Get summaries ordered by period_date (or timestamp if no period_date)
    summaries = query.order_by(
        DiagnosticSummary.period_date.asc().nullslast(),
        DiagnosticSummary.timestamp.asc()
    ).limit(limit).all()

    if len(summaries) < 2:
        return {
            "client_id": client_id,
            "client_name": client.name,
            "error": "Insufficient data for trend analysis",
            "message": f"Need at least 2 diagnostic summaries, found {len(summaries)}",
            "summaries_found": len(summaries),
            "trends": None
        }

    # Convert summaries to PeriodSnapshots for TrendAnalyzer
    from datetime import date as date_type
    snapshots = []

    for summary in summaries:
        # Use period_date if available, otherwise extract date from timestamp
        if summary.period_date:
            snapshot_date = summary.period_date
        else:
            snapshot_date = summary.timestamp.date() if summary.timestamp else date_type.today()

        # Determine period type
        snapshot_period_type = summary.period_type.value if summary.period_type else "monthly"

        # Build category totals
        totals = CategoryTotals(
            total_assets=summary.total_assets or 0.0,
            current_assets=summary.current_assets or 0.0,
            inventory=summary.inventory or 0.0,
            total_liabilities=summary.total_liabilities or 0.0,
            current_liabilities=summary.current_liabilities or 0.0,
            total_equity=summary.total_equity or 0.0,
            total_revenue=summary.total_revenue or 0.0,
            cost_of_goods_sold=summary.cost_of_goods_sold or 0.0,
            total_expenses=summary.total_expenses or 0.0,
            operating_expenses=summary.operating_expenses or 0.0,
        )

        # Build ratios dictionary
        ratios = {
            "current_ratio": summary.current_ratio,
            "quick_ratio": summary.quick_ratio,
            "debt_to_equity": summary.debt_to_equity,
            "gross_margin": summary.gross_margin,
            "net_profit_margin": summary.net_profit_margin,
            "operating_margin": summary.operating_margin,
            "return_on_assets": summary.return_on_assets,
            "return_on_equity": summary.return_on_equity,
        }
        # Filter out None values
        ratios = {k: v for k, v in ratios.items() if v is not None}

        snapshot = PeriodSnapshot(
            period_date=snapshot_date,
            period_type=snapshot_period_type,
            category_totals=totals,
            ratios=ratios
        )
        snapshots.append(snapshot)

    # Run trend analysis
    analyzer = TrendAnalyzer(snapshots)
    analysis = analyzer.get_full_analysis()

    log_secure_operation(
        "trend_analysis_complete",
        f"Analyzed {len(snapshots)} periods for client {client_id}"
    )

    return {
        "client_id": client_id,
        "client_name": client.name,
        "analysis": analysis,
        "periods_analyzed": len(snapshots),
        "period_type_filter": period_type,
    }


# =============================================================================
# SPRINT 36: INDUSTRY RATIOS ENDPOINT
# =============================================================================

@app.get("/clients/{client_id}/industry-ratios")
async def get_client_industry_ratios(
    client_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get industry-specific ratios for a client based on their industry classification.

    Sprint 36: Industry Ratio Expansion

    ZERO-STORAGE COMPLIANCE:
    - Uses ONLY aggregate totals from most recent diagnostic summary
    - NEVER processes raw transaction data
    - Returns calculated ratios with industry benchmarks

    Args:
        client_id: The client ID to calculate industry ratios for

    Returns:
        Industry-specific ratios including:
        - Manufacturing: Inventory Turnover, DIO, Asset Turnover
        - Retail: Inventory Turnover, GMROI
        - Professional Services: Revenue/Employee, Utilization Rate, Revenue/Hour
        - Other: Generic Asset Turnover

    Raises:
        401: Not authenticated
        404: Client not found
        400: No diagnostic data available
    """
    from industry_ratios import calculate_industry_ratios, get_available_industries

    log_secure_operation(
        "industry_ratios_request",
        f"User {current_user.id} requesting industry ratios for client {client_id}"
    )

    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Get most recent diagnostic summary for this client
    latest_summary = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id
    ).order_by(
        DiagnosticSummary.timestamp.desc()
    ).first()

    if not latest_summary:
        return {
            "client_id": client_id,
            "client_name": client.name,
            "industry": client.industry.value if client.industry else "other",
            "error": "No diagnostic data available",
            "message": "Run a diagnostic assessment first to calculate industry ratios",
            "ratios": None,
            "available_industries": get_available_industries(),
        }

    # Build totals dict from latest summary
    totals_dict = {
        "total_assets": latest_summary.total_assets or 0.0,
        "current_assets": latest_summary.current_assets or 0.0,
        "inventory": latest_summary.inventory or 0.0,
        "total_liabilities": latest_summary.total_liabilities or 0.0,
        "current_liabilities": latest_summary.current_liabilities or 0.0,
        "total_equity": latest_summary.total_equity or 0.0,
        "total_revenue": latest_summary.total_revenue or 0.0,
        "cost_of_goods_sold": latest_summary.cost_of_goods_sold or 0.0,
        "total_expenses": latest_summary.total_expenses or 0.0,
        "operating_expenses": latest_summary.operating_expenses or 0.0,
    }

    # Get client industry
    industry = client.industry.value if client.industry else "other"

    # Calculate industry-specific ratios
    industry_result = calculate_industry_ratios(industry, totals_dict)

    log_secure_operation(
        "industry_ratios_complete",
        f"Calculated {industry_result['industry']} ratios for client {client_id}"
    )

    return {
        "client_id": client_id,
        "client_name": client.name,
        "industry": industry,
        "industry_display": industry_result["industry"],
        "industry_type": industry_result["industry_type"],
        "ratios": industry_result["ratios"],
        "summary_date": latest_summary.timestamp.isoformat() if latest_summary.timestamp else None,
        "available_industries": get_available_industries(),
    }


# =============================================================================
# SPRINT 37: ROLLING WINDOW ANALYSIS ENDPOINT
# =============================================================================

@app.get("/clients/{client_id}/rolling-analysis")
async def get_client_rolling_analysis(
    client_id: int,
    window: Optional[int] = Query(default=None, description="Specific window size (3, 6, or 12 months)"),
    period_type: Optional[str] = Query(default=None, description="Filter by period type: monthly, quarterly, annual"),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Get rolling window analysis for a client's historical data.

    Sprint 37: Rolling Window Analysis

    ZERO-STORAGE COMPLIANCE:
    - Analyzes ONLY aggregate totals and ratios
    - NEVER processes raw transaction data
    - Returns calculated rolling averages and momentum indicators

    Args:
        client_id: The client ID to analyze
        window: Optional specific window (3, 6, or 12 months)
        period_type: Optional filter for period type

    Returns:
        Rolling window analysis including:
        - 3/6/12 month rolling averages for each metric
        - Momentum indicators (accelerating/decelerating/steady/reversing)
        - Trend direction and current values

    Raises:
        401: Not authenticated
        404: Client not found
        400: Invalid window size or insufficient data
    """
    from ratio_engine import RollingWindowAnalyzer, PeriodSnapshot, CategoryTotals

    log_secure_operation(
        "rolling_analysis_request",
        f"User {current_user.id} requesting rolling analysis for client {client_id}"
    )

    # Validate window parameter if provided
    if window is not None and window not in [3, 6, 12]:
        raise HTTPException(
            status_code=400,
            detail="Invalid window size. Must be 3, 6, or 12 months."
        )

    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Build query for historical summaries
    query = db.query(DiagnosticSummary).filter(
        DiagnosticSummary.client_id == client_id,
        DiagnosticSummary.user_id == current_user.id
    )

    # Filter by period type if specified
    if period_type:
        try:
            pt = PeriodType(period_type)
            query = query.filter(DiagnosticSummary.period_type == pt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid period_type. Must be one of: monthly, quarterly, annual"
            )

    # Get summaries ordered by period_date
    summaries = query.order_by(
        DiagnosticSummary.period_date.asc().nullslast(),
        DiagnosticSummary.timestamp.asc()
    ).limit(36).all()  # Max 36 periods for rolling analysis

    if len(summaries) < 2:
        return {
            "client_id": client_id,
            "client_name": client.name,
            "error": "Insufficient data for rolling analysis",
            "message": f"Need at least 2 diagnostic summaries, found {len(summaries)}",
            "periods_found": len(summaries),
            "analysis": None,
        }

    # Convert summaries to PeriodSnapshots
    from datetime import date as date_type
    snapshots = []

    for summary in summaries:
        # Use period_date if available, otherwise extract from timestamp
        if summary.period_date:
            snapshot_date = summary.period_date
        else:
            snapshot_date = summary.timestamp.date() if summary.timestamp else date_type.today()

        snapshot_period_type = summary.period_type.value if summary.period_type else "monthly"

        # Build CategoryTotals
        totals = CategoryTotals(
            total_assets=summary.total_assets or 0.0,
            current_assets=summary.current_assets or 0.0,
            inventory=summary.inventory or 0.0,
            total_liabilities=summary.total_liabilities or 0.0,
            current_liabilities=summary.current_liabilities or 0.0,
            total_equity=summary.total_equity or 0.0,
            total_revenue=summary.total_revenue or 0.0,
            cost_of_goods_sold=summary.cost_of_goods_sold or 0.0,
            total_expenses=summary.total_expenses or 0.0,
            operating_expenses=summary.operating_expenses or 0.0,
        )

        # Build ratios dict
        ratios = {}
        if summary.current_ratio is not None:
            ratios["current_ratio"] = summary.current_ratio
        if summary.quick_ratio is not None:
            ratios["quick_ratio"] = summary.quick_ratio
        if summary.debt_to_equity is not None:
            ratios["debt_to_equity"] = summary.debt_to_equity
        if summary.gross_margin is not None:
            ratios["gross_margin"] = summary.gross_margin
        if summary.net_profit_margin is not None:
            ratios["net_profit_margin"] = summary.net_profit_margin
        if summary.operating_margin is not None:
            ratios["operating_margin"] = summary.operating_margin
        if summary.return_on_assets is not None:
            ratios["return_on_assets"] = summary.return_on_assets
        if summary.return_on_equity is not None:
            ratios["return_on_equity"] = summary.return_on_equity

        snapshot = PeriodSnapshot(
            period_date=snapshot_date,
            period_type=snapshot_period_type,
            category_totals=totals,
            ratios=ratios,
        )
        snapshots.append(snapshot)

    # Run rolling window analysis
    analyzer = RollingWindowAnalyzer(snapshots)
    analysis = analyzer.get_full_analysis()

    # If specific window requested, filter the results
    if window is not None:
        # Filter rolling averages to only include the requested window
        for key in analysis.get("category_rolling", {}):
            metric = analysis["category_rolling"][key]
            if "rolling_averages" in metric:
                filtered = {k: v for k, v in metric["rolling_averages"].items() if k == str(window)}
                metric["rolling_averages"] = filtered

        for key in analysis.get("ratio_rolling", {}):
            metric = analysis["ratio_rolling"][key]
            if "rolling_averages" in metric:
                filtered = {k: v for k, v in metric["rolling_averages"].items() if k == str(window)}
                metric["rolling_averages"] = filtered

    log_secure_operation(
        "rolling_analysis_complete",
        f"Analyzed {len(snapshots)} periods for client {client_id}"
    )

    return {
        "client_id": client_id,
        "client_name": client.name,
        "analysis": analysis,
        "periods_analyzed": len(snapshots),
        "window_filter": window,
        "period_type_filter": period_type,
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
        # Read file bytes into memory with size validation - NO DISK STORAGE
        file_bytes = await validate_file_size(file)

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
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_trial_balance(
    request: Request,
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
        # Read file bytes into memory with size validation - NO DISK STORAGE
        file_bytes = await validate_file_size(file)

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
@limiter.limit(RATE_LIMIT_AUDIT)
async def flux_analysis(
    request: Request,
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
        # 1. Process Current File with size validation
        # Use streaming auditor to handle large files memory-efficiently
        content_curr = await validate_file_size(current_file)
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

        # 2. Process Prior File with size validation
        content_prior = await validate_file_size(prior_file)
        
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
