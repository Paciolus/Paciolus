"""
Paciolus API — Authentication Routes
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
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
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    get_user_by_email,
    require_current_user,
    revoke_refresh_token,
    rotate_refresh_token,
)
from config import COOKIE_SECURE, JWT_EXPIRATION_MINUTES, REFRESH_COOKIE_NAME, REFRESH_TOKEN_EXPIRATION_DAYS
from database import get_db
from disposable_email import is_disposable_email
from email_service import (
    RESEND_COOLDOWN_MINUTES,
    can_resend_verification,
    generate_verification_token,
    is_email_service_configured,
    send_verification_email,
)
from models import EmailVerificationToken, User
from security_middleware import (
    check_lockout_status,
    generate_csrf_token,
    get_fake_lockout_info,
    get_lockout_info,
    record_failed_login,
    reset_failed_attempts,
)
from shared.error_messages import sanitize_error
from shared.helpers import safe_background_email
from shared.rate_limits import RATE_LIMIT_AUTH, limiter
from shared.response_schemas import SuccessResponse

router = APIRouter(tags=["auth"])


from typing import Optional


def _set_refresh_cookie(response: Response, token: str, remember_me: bool) -> None:
    """Set the HttpOnly refresh token cookie."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/auth",
        max_age=REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 3600 if remember_me else None,
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the HttpOnly refresh token cookie."""
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/auth")


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
):
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
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = create_user(db, user_data)

    token_result = generate_verification_token()
    verification_token = EmailVerificationToken(
        user_id=user.id,
        token=token_result.token,
        expires_at=token_result.expires_at,
    )
    db.add(verification_token)

    user.email_verification_token = token_result.token
    user.email_verification_sent_at = datetime.now(UTC)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Database error during user registration commit")
        raise HTTPException(status_code=500, detail=sanitize_error(e, log_label="db_register"))

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

    raw_refresh_token, _ = create_refresh_token(db, user.id)
    # Registration is always session-only (no "Remember Me" option)
    _set_refresh_cookie(response, raw_refresh_token, remember_me=False)

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
def login(request: Request, credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    masked = mask_email(credentials.email)
    logger.info("Login attempt: %s", masked)
    log_secure_operation("auth_login_attempt", f"Login attempt: {masked}")

    existing_user = get_user_by_email(db, credentials.email)
    if existing_user:
        is_locked, locked_until, remaining = check_lockout_status(db, existing_user.id)
        if is_locked:
            lockout_info = get_lockout_info(db, existing_user.id)
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Account temporarily locked due to too many failed login attempts",
                    "lockout": lockout_info,
                },
            )

    user = authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        # Sprint 261: Uniform response shape prevents account enumeration.
        # Both existing and non-existing users get the same response structure.
        if existing_user:
            record_failed_login(db, existing_user.id)
            lockout_info = get_lockout_info(db, existing_user.id)
        else:
            lockout_info = get_fake_lockout_info()
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid email or password", "lockout": lockout_info},
            headers={"WWW-Authenticate": "Bearer"},
        )

    reset_failed_attempts(db, user.id)

    token, expires = create_access_token(user.id, user.email, user.password_changed_at, tier=user.tier.value)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    raw_refresh_token, _ = create_refresh_token(db, user.id)
    _set_refresh_cookie(response, raw_refresh_token, credentials.remember_me)

    csrf_token_value = generate_csrf_token(user_id=str(user.id))
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token_value,
    )


@router.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(require_current_user)):
    return UserResponse.model_validate(current_user)


@router.get("/auth/csrf", response_model=CsrfTokenResponse)
def get_csrf_token(current_user: User = Depends(require_current_user)):
    """Generate and return a user-bound CSRF token (requires authentication)."""
    token = generate_csrf_token(user_id=str(current_user.id))
    return {"csrf_token": token, "expires_in_minutes": 30}


@router.post("/auth/verify-email", response_model=EmailVerifyResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def verify_email(request: Request, request_data: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify email address with token."""
    token = request_data.token

    verification = db.query(EmailVerificationToken).filter(EmailVerificationToken.token == token).first()

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


@router.post("/auth/resend-verification", response_model=ResendVerificationResponse)
@limiter.limit("3/minute")
def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
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
        token=token_result.token,
        expires_at=token_result.expires_at,
    )
    db.add(verification_token)

    current_user.email_verification_token = token_result.token
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
def get_verification_status(current_user: User = Depends(require_current_user)):
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
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    """Exchange the HttpOnly refresh cookie for a new access + refresh token pair."""
    logger.debug("Token refresh requested")
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    access_token, new_refresh_token, user = rotate_refresh_token(db, raw_token)
    # Always issue a session cookie on rotation (security best-practice)
    _set_refresh_cookie(response, new_refresh_token, remember_me=False)
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
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Revoke the HttpOnly refresh cookie (logout)."""
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        revoke_refresh_token(db, raw_token)
    _clear_refresh_cookie(response)
    return SuccessResponse(success=True, message="Logged out successfully")
