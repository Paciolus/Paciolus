"""
Paciolus API — Authentication Routes
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from shared.log_sanitizer import mask_email

logger = logging.getLogger(__name__)
from auth import (
    AuthResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    _check_password_complexity,
    require_current_user,
)
from config import (
    ACCESS_COOKIE_NAME,
    COOKIE_SECURE,
    JWT_EXPIRATION_MINUTES,
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRATION_DAYS,
)
from database import get_db
from email_service import (
    RESEND_COOLDOWN_MINUTES,
    can_resend_verification,
    is_email_service_configured,
    send_password_reset_email,
    send_verification_email,
)
from models import User
from security_middleware import (
    generate_csrf_token,
    get_client_ip,
)
from services.auth.identity import (
    authenticate_login,
    refresh_session,
    revoke_session_token,
)
from services.auth.recovery import (
    PasswordResetError,
    complete_password_reset,
    initiate_password_reset,
)
from services.auth.registration import (
    EmailAlreadyVerifiedError,
    EmailVerificationError,
    RegistrationError,
    VerificationCooldownError,
    complete_email_verification,
    register_user,
    resend_verification_email,
)
from services.auth.sessions import (
    SessionNotFoundError,
    list_user_sessions,
    revoke_all_user_sessions,
    revoke_session_by_id,
)
from shared.background_email import safe_background_email
from shared.rate_limits import RATE_LIMIT_AUTH, limiter
from shared.response_schemas import SuccessResponse

router = APIRouter(tags=["auth"])


from typing import Optional

# Opt-in header for non-browser API clients to receive the access token in
# the JSON body. Browser clients omit this header and rely solely on the
# HttpOnly paciolus_access cookie. Default OFF — bodies omit access_token
# unless the client explicitly opts in.
_BEARER_RESPONSE_HEADER = "X-Token-Response"
_BEARER_RESPONSE_VALUE = "bearer"


def _wants_bearer_in_body(request: Request) -> bool:
    """Return True iff the caller explicitly opted in to a bearer token in the body."""
    raw = request.headers.get(_BEARER_RESPONSE_HEADER)
    return bool(raw) and raw.strip().lower() == _BEARER_RESPONSE_VALUE


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    """Set the HttpOnly refresh token cookie.

    SameSite policy:
      - Production (cross-origin): "none" + Secure — required for cross-origin AJAX
        POST requests (e.g., /auth/refresh from Vercel frontend → Render backend).
        SameSite=Lax silently drops cookies on cross-origin POST, breaking refresh.
      - Development (same-origin): "lax" — SameSite=None requires Secure (HTTPS),
        which isn't available on localhost HTTP.
    """
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="none" if COOKIE_SECURE else "lax",
        path="/auth",
        max_age=REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 3600 if remember_me else None,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the HttpOnly refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/auth",
        secure=COOKIE_SECURE,
        samesite="none" if COOKIE_SECURE else "lax",
    )


def _set_access_cookie(response: Response, token: str) -> None:
    """Set the HttpOnly access token cookie.

    Unlike the refresh cookie (path=/auth), the access cookie is sent on
    ALL API paths so the browser never needs a JS-readable bearer token.
    Max-age matches the JWT expiration so the cookie auto-expires with the token.
    """
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="none" if COOKIE_SECURE else "lax",
        path="/",
        max_age=JWT_EXPIRATION_MINUTES * 60,
    )


def _clear_access_cookie(response: Response) -> None:
    """Clear the HttpOnly access token cookie."""
    response.delete_cookie(
        key=ACCESS_COOKIE_NAME,
        path="/",
        secure=COOKIE_SECURE,
        samesite="none" if COOKIE_SECURE else "lax",
    )


class VerifyEmailRequest(BaseModel):
    """Request body for email verification."""

    token: str = Field(..., min_length=1)


class CsrfTokenResponse(BaseModel):
    csrf_token: str
    expires_in_minutes: int


class EmailVerifyResponse(BaseModel):
    message: str
    user: UserResponse


class ResendVerificationResponse(BaseModel):
    message: str
    cooldown_minutes: int


class VerificationStatusResponse(BaseModel):
    is_verified: bool
    email: str
    verified_at: Optional[str] = None
    can_resend: bool
    resend_cooldown_seconds: int
    email_service_configured: bool


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
@limiter.limit(RATE_LIMIT_AUTH)
def register(
    request: Request,
    user_data: UserCreate,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Register a new user account."""
    masked = mask_email(user_data.email)
    logger.info("Registration attempt: %s", masked)
    log_secure_operation("auth_register_attempt", f"Registration attempt: {masked}")

    try:
        result = register_user(
            db,
            user_data=user_data,
            user_agent=request.headers.get("User-Agent"),
            request_host=request.client.host if request.client else None,
        )
    except RegistrationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if result.verification_token is not None:
        background_tasks.add_task(
            safe_background_email,
            send_verification_email,
            label="register_verification",
            to_email=result.user.email,
            token=result.verification_token,
            user_name=result.user.name,
        )

    # Registration is always session-only (no "Remember Me" option)
    _set_refresh_cookie(response, result.issuance.raw_refresh_token, remember_me=False)
    _set_access_cookie(response, result.issuance.access_token)

    return AuthResponse(
        access_token=result.issuance.access_token if _wants_bearer_in_body(request) else None,
        token_type="bearer",
        expires_in=result.issuance.expires_in,
        user=UserResponse.model_validate(result.user),
        csrf_token=result.issuance.csrf_token,
    )


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def login(request: Request, credentials: UserLogin, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    """Authenticate user and return JWT token."""
    log_secure_operation("auth_login_attempt", f"Login attempt: {mask_email(credentials.email)}")

    issuance = authenticate_login(
        db,
        email=credentials.email,
        password=credentials.password,
        client_ip=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        request_host=request.client.host if request.client else None,
    )

    _set_refresh_cookie(response, issuance.raw_refresh_token, credentials.remember_me)
    _set_access_cookie(response, issuance.access_token)

    return AuthResponse(
        access_token=issuance.access_token if _wants_bearer_in_body(request) else None,
        token_type="bearer",
        expires_in=issuance.expires_in,
        user=UserResponse.model_validate(issuance.user),
        csrf_token=issuance.csrf_token,
    )


@router.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(require_current_user)) -> UserResponse:
    """Return the authenticated user's profile information."""
    return UserResponse.model_validate(current_user)


@router.get("/auth/csrf", response_model=CsrfTokenResponse)
def get_csrf_token(current_user: User = Depends(require_current_user)) -> dict[str, object]:
    """Generate and return a user-bound CSRF token (requires authentication)."""
    token = generate_csrf_token(user_id=str(current_user.id))
    return {"csrf_token": token, "expires_in_minutes": 30}


@router.post("/auth/verify-email", response_model=EmailVerifyResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def verify_email(
    request: Request, request_data: VerifyEmailRequest, db: Session = Depends(get_db)
) -> dict[str, object]:
    """Verify email address with token."""
    try:
        user = complete_email_verification(db, request_data.token)
    except EmailVerificationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {"message": "Email verified successfully", "user": UserResponse.model_validate(user)}


# =============================================================================
# PASSWORD RESET (Sprint 572)
# =============================================================================


class ForgotPasswordRequest(BaseModel):
    """Request body for forgot-password (initiate reset)."""

    email: str = Field(..., min_length=1)


class ForgotPasswordResponse(BaseModel):
    """Response for forgot-password — always returns success to prevent enumeration."""

    message: str


class ResetPasswordRequest(BaseModel):
    """Request body for reset-password (consume token + set new password)."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _check_password_complexity(v)


class ResetPasswordResponse(BaseModel):
    """Response for successful password reset."""

    message: str


@router.post("/auth/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    """Initiate password reset. Always returns 200 to prevent account enumeration."""
    log_secure_operation("password_reset_request", f"Password reset requested for {mask_email(body.email)}")

    generic_response = ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )

    initiation = initiate_password_reset(db, body.email)
    if initiation.user is not None and initiation.token_result is not None:
        background_tasks.add_task(
            safe_background_email,
            send_password_reset_email,
            label="password_reset",
            to_email=initiation.user.email,
            token=initiation.token_result.token,
            user_name=initiation.user.name,
        )

    return generic_response


@router.post("/auth/reset-password", response_model=ResetPasswordResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> ResetPasswordResponse:
    """Consume a password reset token and set a new password."""
    try:
        complete_password_reset(db, body.token, body.new_password)
    except PasswordResetError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return ResetPasswordResponse(message="Your password has been reset successfully. You can now log in.")


@router.post("/auth/resend-verification", response_model=ResendVerificationResponse)
@limiter.limit("3/minute")
def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Resend verification email."""
    try:
        result = resend_verification_email(db, current_user)
    except EmailAlreadyVerifiedError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except VerificationCooldownError as e:
        raise HTTPException(
            status_code=429,
            detail={
                "message": str(e),
                "seconds_remaining": e.seconds_remaining,
                "cooldown_minutes": RESEND_COOLDOWN_MINUTES,
            },
        ) from e

    background_tasks.add_task(
        safe_background_email,
        send_verification_email,
        label="resend_verification",
        to_email=result.target_email,
        token=result.token,
        user_name=current_user.name,
    )

    return {"message": "Verification email sent", "cooldown_minutes": RESEND_COOLDOWN_MINUTES}


@router.get("/auth/verification-status", response_model=VerificationStatusResponse)
def get_verification_status(current_user: User = Depends(require_current_user)) -> dict[str, object]:
    """Get current user's email verification status."""
    can_resend, seconds_remaining = can_resend_verification(current_user.email_verification_sent_at)

    return {
        "is_verified": current_user.is_verified,
        "email": current_user.email,
        "verified_at": current_user.email_verified_at.isoformat() if current_user.email_verified_at else None,
        "can_resend": can_resend,
        "resend_cooldown_seconds": seconds_remaining if not can_resend else 0,
        "email_service_configured": is_email_service_configured(),
    }


@router.post("/auth/refresh", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    """Exchange the HttpOnly refresh cookie for a new access + refresh token pair."""
    # Defense-in-depth: require X-Requested-With header to mitigate cross-origin
    # form POSTs. Browsers never auto-attach custom headers on simple requests.
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        raise HTTPException(status_code=403, detail="Missing or invalid X-Requested-With header")

    logger.debug("Token refresh requested")
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    issuance = refresh_session(db, raw_refresh_token=raw_token)

    # Always issue a session cookie on rotation (security best-practice)
    _set_refresh_cookie(response, issuance.raw_refresh_token, remember_me=False)
    _set_access_cookie(response, issuance.access_token)

    return AuthResponse(
        access_token=issuance.access_token if _wants_bearer_in_body(request) else None,
        token_type="bearer",
        expires_in=issuance.expires_in,
        user=UserResponse.model_validate(issuance.user),
        csrf_token=issuance.csrf_token,
    )


@router.post("/auth/logout", response_model=SuccessResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> SuccessResponse:
    """Revoke the HttpOnly refresh cookie (logout)."""
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        revoke_session_token(db, raw_token)
    _clear_refresh_cookie(response)
    _clear_access_cookie(response)
    return SuccessResponse(success=True, message="Logged out successfully")


# =============================================================================
# AUDIT-02 FIX 2: Session Inventory & Revocation
# =============================================================================


class SessionInfo(BaseModel):
    """Response model for a single session entry."""

    session_id: int
    last_used_at: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[str] = None


class SessionListResponse(BaseModel):
    """Response model for GET /auth/sessions."""

    sessions: list[SessionInfo]


@router.get("/auth/sessions", response_model=SessionListResponse)
def list_sessions(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> SessionListResponse:
    """List all active (non-revoked) sessions for the calling user.

    AUDIT-02 FIX 2: Provides session inventory visibility.
    Never returns the token hash.
    """
    entries = list_user_sessions(db, current_user)
    return SessionListResponse(
        sessions=[
            SessionInfo(
                session_id=e.session_id,
                last_used_at=e.last_used_at,
                user_agent=e.user_agent,
                ip_address=e.ip_address,
                created_at=e.created_at,
            )
            for e in entries
        ]
    )


@router.delete("/auth/sessions/{session_id}", status_code=204)
@limiter.limit(RATE_LIMIT_AUTH)
def revoke_session(
    request: Request,
    session_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Revoke a single session by ID. Only the owning user can revoke.

    AUDIT-02 FIX 2: Per-session revocation endpoint.
    Returns 204 on success, 404 if not found or not owned by caller.
    """
    try:
        revoke_session_by_id(db, current_user, session_id)
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail="Session not found") from e
    return Response(status_code=204)


@router.delete("/auth/sessions", status_code=204)
@limiter.limit(RATE_LIMIT_AUTH)
def revoke_all_sessions(
    request: Request,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Revoke all active sessions for the calling user.

    AUDIT-02 FIX 2: Bulk session revocation endpoint.
    Returns 204 on success.
    """
    revoke_all_user_sessions(db, current_user)
    return Response(status_code=204)
