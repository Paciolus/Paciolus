"""
Paciolus API — Authentication Routes
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError
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
    _revoke_all_user_tokens,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    get_user_by_email,
    hash_token,
    require_current_user,
    revoke_refresh_token,
    rotate_refresh_token,
)
from config import (
    ACCESS_COOKIE_NAME,
    COOKIE_SECURE,
    ENV_MODE,
    JWT_EXPIRATION_MINUTES,
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRATION_DAYS,
)
from database import get_db
from disposable_email import is_disposable_email
from email_service import (
    RESEND_COOLDOWN_MINUTES,
    can_resend_verification,
    generate_password_reset_token,
    generate_verification_token,
    is_email_service_configured,
    send_password_reset_email,
    send_verification_email,
)
from models import EmailVerificationToken, PasswordResetToken, RefreshToken, User
from security_middleware import (
    check_ip_blocked,
    check_lockout_status,
    generate_csrf_token,
    get_client_ip,
    hash_ip_address,
    record_failed_login,
    record_ip_failure,
    reset_failed_attempts,
    reset_ip_failures,
)
from shared.background_email import safe_background_email
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUTH, limiter
from shared.response_schemas import SuccessResponse

router = APIRouter(tags=["auth"])


from typing import Optional


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

    if is_disposable_email(user_data.email):
        logger.warning("Registration blocked — disposable email: %s", masked)
        log_secure_operation("auth_register_blocked", f"Disposable email blocked: {masked}")
        raise HTTPException(
            status_code=400,
            detail="Temporary or disposable email addresses are not allowed. Please use a permanent email address.",
        )

    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        # Generic message prevents account enumeration (attacker cannot distinguish
        # "email taken" from other registration failures).
        raise HTTPException(
            status_code=400,
            detail="Unable to create account. Please check your information or try logging in.",
        )

    user = create_user(db, user_data)

    # Auto-verify when email service is not configured (no SendGrid API key)
    # AND we are in development mode. In production, a missing email service
    # must never silently bypass verification.
    if not is_email_service_configured():
        if ENV_MODE == "development":
            user.is_verified = True
            user.email_verified_at = datetime.now(UTC)
            log_secure_operation("auto_verified", f"Email service unavailable — auto-verified {masked}")
        else:
            log_secure_operation(
                "auto_verify_skipped", f"Email service unavailable in {ENV_MODE} — user left unverified: {masked}"
            )
    else:
        token_result = generate_verification_token()
        verification_token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(token_result.token),
            expires_at=token_result.expires_at,
        )
        db.add(verification_token)
        user.email_verification_sent_at = datetime.now(UTC)

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error during user registration commit")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_register"))

    if is_email_service_configured():
        background_tasks.add_task(
            safe_background_email,
            send_verification_email,
            label="register_verification",
            to_email=user.email,
            token=token_result.token,
            user_name=user.name,
        )

    jwt_token, expires = create_access_token(user.id, user.email, user.password_changed_at, tier=user.tier.value)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    raw_refresh_token, _ = create_refresh_token(
        db,
        user.id,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )
    # Registration is always session-only (no "Remember Me" option)
    _set_refresh_cookie(response, raw_refresh_token, remember_me=False)
    _set_access_cookie(response, jwt_token)

    csrf_token_value = generate_csrf_token(user_id=str(user.id))
    return AuthResponse(
        access_token=jwt_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token_value,
    )


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def login(request: Request, credentials: UserLogin, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    """Authenticate user and return JWT token."""
    masked = mask_email(credentials.email)
    logger.info("Login attempt: %s", masked)
    log_secure_operation("auth_login_attempt", f"Login attempt: {masked}")

    # AUDIT-07 F2: Per-IP brute-force gate
    client_ip = get_client_ip(request)
    if check_ip_blocked(client_ip):
        log_secure_operation("ip_blocked", f"IP {hash_ip_address(client_ip)} blocked: threshold exceeded")
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid email or password"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    existing_user = get_user_by_email(db, credentials.email)

    # AUDIT-07 F4: Locked accounts return same 401 as any other failure
    if existing_user:
        is_locked, _locked_until, _remaining = check_lockout_status(db, existing_user.id)
        if is_locked:
            record_ip_failure(client_ip)
            raise HTTPException(
                status_code=401,
                detail={"message": "Invalid email or password"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        # AUDIT-07 F4: Identical response for existing-wrong-password and non-existent
        if existing_user:
            record_failed_login(db, existing_user.id)
        record_ip_failure(client_ip)
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid email or password"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    reset_failed_attempts(db, user.id)
    reset_ip_failures(client_ip)

    token, expires = create_access_token(user.id, user.email, user.password_changed_at, tier=user.tier.value)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    raw_refresh_token, _ = create_refresh_token(
        db,
        user.id,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_refresh_cookie(response, raw_refresh_token, credentials.remember_me)
    _set_access_cookie(response, token)

    csrf_token_value = generate_csrf_token(user_id=str(user.id))
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token_value,
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
    token = request_data.token

    verification = (
        db.query(EmailVerificationToken).filter(EmailVerificationToken.token_hash == hash_token(token)).first()
    )

    if verification is None:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if verification.is_used:
        raise HTTPException(status_code=400, detail="This verification link has already been used")

    if verification.is_expired:
        raise HTTPException(status_code=400, detail="This verification link has expired. Please request a new one.")

    verification.used_at = datetime.now(UTC)

    user = verification.user

    # Sprint 203: If pending_email is set, swap it to be the new email
    if user.pending_email:
        user.email = user.pending_email
        user.pending_email = None
        log_secure_operation("email_changed", f"User {user.id} email swapped from pending")

    user.is_verified = True
    user.email_verified_at = datetime.now(UTC)

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error during email verification commit")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_verify_email"))

    log_secure_operation("email_verified", f"User {user.id} email verified")

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
    masked = mask_email(body.email)
    log_secure_operation("password_reset_request", f"Password reset requested for {masked}")

    # Generic success message — returned whether or not the email exists
    generic_response = ForgotPasswordResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )

    user = get_user_by_email(db, body.email)
    if not user:
        # Don't reveal whether the email is registered.
        # Temporary diagnostic (Sprint 594/595 incident): when the lookup
        # fails, log the total user row count so we can distinguish
        # "DB was wiped" (count=0) from "stored email does not match typed
        # email" (count>0). No PII is leaked — we never log other users'
        # addresses. Remove this instrumentation once the post-incident
        # root cause is fully understood.
        try:
            total_users = db.query(User).count()
        except Exception:  # pragma: no cover — diagnostic must never block the response
            total_users = -1
        logger.info(
            "Password reset requested for unknown email: %s (total_users=%d)",
            masked,
            total_users,
        )
        return generic_response

    if not user.is_active:
        logger.info("Password reset requested for inactive account: %s", masked)
        return generic_response

    # Generate token
    token_result = generate_password_reset_token()
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(token_result.token),
        expires_at=token_result.expires_at,
    )
    db.add(reset_token)

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error creating password reset token")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_password_reset"))

    # Send email in background (don't block the response)
    background_tasks.add_task(
        safe_background_email,
        send_password_reset_email,
        label="password_reset",
        to_email=user.email,
        token=token_result.token,
        user_name=user.name,
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
    token_hash = hash_token(body.token)

    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not reset_token:
        log_secure_operation("password_reset_invalid", "Invalid password reset token submitted")
        raise HTTPException(status_code=400, detail="Invalid or expired reset link. Please request a new one.")

    if reset_token.is_used:
        log_secure_operation("password_reset_reused", f"Attempt to reuse password reset token id={reset_token.id}")
        raise HTTPException(status_code=400, detail="This reset link has already been used. Please request a new one.")

    if reset_token.is_expired:
        log_secure_operation("password_reset_expired", f"Expired password reset token id={reset_token.id}")
        raise HTTPException(status_code=400, detail="This reset link has expired. Please request a new one.")

    user = reset_token.user
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link. Please request a new one.")

    # Update password
    from auth import hash_password

    user.hashed_password = hash_password(body.new_password)
    user.password_changed_at = datetime.now(UTC)

    # Mark token as used
    reset_token.used_at = datetime.now(UTC)

    # Revoke all existing refresh tokens (force re-login on all devices)
    _revoke_all_user_tokens(db, user.id)

    # Reset lockout state
    user.failed_login_attempts = 0
    user.locked_until = None

    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error during password reset")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_reset_password"))

    log_secure_operation("password_reset_success", f"Password reset completed for user {user.id}")

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
    # Sprint 203: Allow resend if verified user has a pending email change
    if current_user.is_verified and not current_user.pending_email:
        raise HTTPException(status_code=400, detail="Email is already verified")

    can_resend, seconds_remaining = can_resend_verification(current_user.email_verification_sent_at)

    if not can_resend:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Please wait before requesting another verification email",
                "seconds_remaining": seconds_remaining,
                "cooldown_minutes": RESEND_COOLDOWN_MINUTES,
            },
        )

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user.id, EmailVerificationToken.used_at == None
    ).update({"used_at": datetime.now(UTC)})

    token_result = generate_verification_token()
    verification_token = EmailVerificationToken(
        user_id=current_user.id,
        token_hash=hash_token(token_result.token),
        expires_at=token_result.expires_at,
    )
    db.add(verification_token)

    current_user.email_verification_sent_at = datetime.now(UTC)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error during resend verification commit")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_resend_verify"))

    # Sprint 203: Send to pending email if set, otherwise current email
    target_email = current_user.pending_email or current_user.email
    background_tasks.add_task(
        safe_background_email,
        send_verification_email,
        label="resend_verification",
        to_email=target_email,
        token=token_result.token,
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
    xrw = request.headers.get("X-Requested-With")
    if xrw != "XMLHttpRequest":
        raise HTTPException(status_code=403, detail="Missing or invalid X-Requested-With header")

    logger.debug("Token refresh requested")
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    access_token, new_refresh_token, user = rotate_refresh_token(db, raw_token)
    # Always issue a session cookie on rotation (security best-practice)
    _set_refresh_cookie(response, new_refresh_token, remember_me=False)
    _set_access_cookie(response, access_token)
    expires_in = JWT_EXPIRATION_MINUTES * 60

    csrf_token_value = generate_csrf_token(user_id=str(user.id))
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token_value,
    )


@router.post("/auth/logout", response_model=SuccessResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> SuccessResponse:
    """Revoke the HttpOnly refresh cookie (logout)."""
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        revoke_refresh_token(db, raw_token)
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
    tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .order_by(RefreshToken.created_at.desc())
        .all()
    )

    sessions = [
        SessionInfo(
            session_id=t.id,
            last_used_at=t.last_used_at.isoformat() if t.last_used_at else None,
            user_agent=t.user_agent,
            ip_address=t.ip_address,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in tokens
    ]

    return SessionListResponse(sessions=sessions)


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
    token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.id == session_id,
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .first()
    )

    if token is None:
        raise HTTPException(status_code=404, detail="Session not found")

    from datetime import UTC, datetime

    token.revoked_at = datetime.now(UTC)
    db.commit()

    log_secure_operation(
        "session_revoked",
        f"Session {session_id} revoked by user {current_user.id}",
    )

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
    count = _revoke_all_user_tokens(db, current_user.id)

    log_secure_operation(
        "all_sessions_revoked",
        f"User {current_user.id} revoked all {count} sessions",
    )

    return Response(status_code=204)
