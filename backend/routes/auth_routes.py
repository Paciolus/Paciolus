"""
Paciolus API — Authentication Routes
"""
from datetime import datetime, UTC

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from security_middleware import (
    generate_csrf_token,
    record_failed_login,
    check_lockout_status,
    reset_failed_attempts,
    get_lockout_info,
)
from database import get_db
from models import User, EmailVerificationToken
from auth import (
    UserCreate, UserLogin, UserResponse, AuthResponse,
    create_user, authenticate_user, get_user_by_email,
    create_access_token, validate_password_strength,
    require_current_user,
)
from disposable_email import is_disposable_email
from email_service import (
    generate_verification_token,
    send_verification_email,
    can_resend_verification,
    is_email_service_configured,
    RESEND_COOLDOWN_MINUTES,
)
from shared.helpers import safe_background_email
from shared.rate_limits import limiter, RATE_LIMIT_AUTH

router = APIRouter(tags=["auth"])


class VerifyEmailRequest(BaseModel):
    """Request body for email verification."""
    token: str


@router.post("/auth/register", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def register(
    request: Request,
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Register a new user account."""
    log_secure_operation("auth_register_attempt", f"Registration attempt: {user_data.email[:10]}...")

    if is_disposable_email(user_data.email):
        log_secure_operation("auth_register_blocked", f"Disposable email blocked: {user_data.email[:10]}...")
        raise HTTPException(
            status_code=400,
            detail="Temporary or disposable email addresses are not allowed. Please use a permanent email address."
        )

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

    token_result = generate_verification_token()
    verification_token = EmailVerificationToken(
        user_id=user.id,
        token=token_result.token,
        expires_at=token_result.expires_at,
    )
    db.add(verification_token)

    user.email_verification_token = token_result.token
    user.email_verification_sent_at = datetime.now(UTC)
    db.commit()

    background_tasks.add_task(
        safe_background_email,
        send_verification_email,
        label="register_verification",
        to_email=user.email,
        token=token_result.token,
        user_name=user.name,
    )

    jwt_token, expires = create_access_token(user.id, user.email)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    return AuthResponse(
        access_token=jwt_token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    log_secure_operation("auth_login_attempt", f"Login attempt: {credentials.email[:10]}...")

    existing_user = get_user_by_email(db, credentials.email)
    if existing_user:
        is_locked, locked_until, remaining = check_lockout_status(existing_user.id)
        if is_locked:
            lockout_info = get_lockout_info(existing_user.id)
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Account temporarily locked due to too many failed login attempts",
                    "lockout": lockout_info
                }
            )

    user = authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        if existing_user:
            failed_count, locked_until = record_failed_login(existing_user.id)
            lockout_info = get_lockout_info(existing_user.id)
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Invalid email or password",
                    "lockout": lockout_info
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

    reset_failed_attempts(user.id)

    token, expires = create_access_token(user.id, user.email)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserResponse.model_validate(user)
    )


@router.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(require_current_user)):
    return UserResponse.model_validate(current_user)


@router.get("/auth/csrf")
def get_csrf_token():
    """Generate and return a CSRF token."""
    token = generate_csrf_token()
    return {"csrf_token": token, "expires_in_minutes": 60}


@router.post("/auth/verify-email")
def verify_email(
    request_data: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """Verify email address with token."""
    token = request_data.token

    verification = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token == token
    ).first()

    if verification is None:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if verification.is_used:
        raise HTTPException(status_code=400, detail="This verification link has already been used")

    if verification.is_expired:
        raise HTTPException(
            status_code=400,
            detail="This verification link has expired. Please request a new one."
        )

    verification.used_at = datetime.now(UTC)

    user = verification.user
    user.is_verified = True
    user.email_verified_at = datetime.now(UTC)

    db.commit()

    log_secure_operation("email_verified", f"User {user.id} email verified")

    return {
        "message": "Email verified successfully",
        "user": UserResponse.model_validate(user)
    }


@router.post("/auth/resend-verification")
@limiter.limit("3/minute")
def resend_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Resend verification email."""
    if current_user.is_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")

    can_resend, seconds_remaining = can_resend_verification(
        current_user.email_verification_sent_at
    )

    if not can_resend:
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Please wait before requesting another verification email",
                "seconds_remaining": seconds_remaining,
                "cooldown_minutes": RESEND_COOLDOWN_MINUTES
            }
        )

    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user.id,
        EmailVerificationToken.used_at == None
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
    db.commit()

    background_tasks.add_task(
        safe_background_email,
        send_verification_email,
        label="resend_verification",
        to_email=current_user.email,
        token=token_result.token,
        user_name=current_user.name,
    )

    return {
        "message": "Verification email sent",
        "cooldown_minutes": RESEND_COOLDOWN_MINUTES
    }


@router.get("/auth/verification-status")
def get_verification_status(
    current_user: User = Depends(require_current_user)
):
    """Get current user's email verification status."""
    can_resend, seconds_remaining = can_resend_verification(
        current_user.email_verification_sent_at
    )

    return {
        "is_verified": current_user.is_verified,
        "email": current_user.email,
        "verified_at": current_user.email_verified_at.isoformat() if current_user.email_verified_at else None,
        "can_resend": can_resend,
        "resend_cooldown_seconds": seconds_remaining if not can_resend else 0,
        "email_service_configured": is_email_service_configured()
    }
