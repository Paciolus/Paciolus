"""
Paciolus Authentication Module
Day 13: Secure Commercial Infrastructure

JWT-based authentication with bcrypt password hashing.

Industry-standard libraries used:
- PyJWT (JWT encoding/decoding) - MIT License
- bcrypt (password hashing) - Apache 2.0 License

All libraries are open-source with permissive licenses.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Optional

import bcrypt as _bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from config import JWT_ALGORITHM, JWT_EXPIRATION_MINUTES, JWT_SECRET_KEY, REFRESH_TOKEN_EXPIRATION_DAYS
from database import get_db
from models import EmailVerificationToken, RefreshToken, User
from security_utils import log_secure_operation
from shared.log_sanitizer import mask_email

# Bcrypt cost factor — 12 rounds (2^12 iterations)
BCRYPT_ROUNDS = 12


# =============================================================================
# PASSWORD HASHING
# =============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    SECURITY: Password is NEVER logged or stored in plaintext.
    The bcrypt hash includes a random salt automatically.
    """
    salt = _bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Returns True if password matches, False otherwise.
    Uses constant-time comparison to prevent timing attacks.
    """
    return _bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# =============================================================================
# JWT TOKEN HANDLING
# =============================================================================

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class TokenResponse(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class TokenData(BaseModel):
    """Data extracted from JWT token."""

    user_id: Optional[int] = None
    email: Optional[str] = None
    password_changed_at: Optional[datetime] = None  # Sprint 199: pwd_at claim


def create_access_token(
    user_id: int,
    email: str,
    password_changed_at: Optional[datetime] = None,
    tier: str = "free",
) -> tuple[str, datetime]:
    """
    Create a JWT access token for a user.

    Args:
        user_id: Database ID of the user
        email: User's email address
        password_changed_at: Timestamp of last password change (embedded as pwd_at claim)
        tier: User subscription tier (embedded for rate-limit resolution, Sprint 306)

    Returns:
        Tuple of (token_string, expiration_datetime)
    """
    expire = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRATION_MINUTES)

    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "email": email,
        "tier": tier,  # Sprint 306: user tier for rate-limit middleware
        "jti": secrets.token_hex(16),  # JWT ID for future token-level revocation
        "iat": datetime.now(UTC),  # Issued at
        "exp": expire,  # Expiration
    }

    # Sprint 199: Embed password change timestamp for token invalidation
    if password_changed_at is not None:
        # Handle timezone-naive datetimes from SQLite (treat as UTC)
        if password_changed_at.tzinfo is None:
            from datetime import timezone

            password_changed_at = password_changed_at.replace(tzinfo=timezone.utc)
        payload["pwd_at"] = int(password_changed_at.timestamp())

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    log_secure_operation("token_created", f"JWT issued for user_id={user_id}")

    return token, expire


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT access token.

    Returns TokenData if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")

        if user_id is None:
            return None

        # Sprint 199: Extract password_changed_at from pwd_at claim
        pwd_at_epoch = payload.get("pwd_at")
        pwd_at = datetime.fromtimestamp(pwd_at_epoch, tz=UTC) if pwd_at_epoch is not None else None

        return TokenData(user_id=int(user_id), email=email, password_changed_at=pwd_at)

    except PyJWTError as e:
        log_secure_operation("token_decode_failed", f"{type(e).__name__}: token validation failed")
        return None


# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================


def get_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency to get the current authenticated user.

    Returns User if authenticated, None if not authenticated.
    Use this for routes that support both authenticated and anonymous access.
    """
    if token is None:
        return None

    token_data = decode_access_token(token)
    if token_data is None or token_data.user_id is None:
        return None

    user = db.query(User).filter(User.id == token_data.user_id).first()

    if user is None or not user.is_active:
        return None

    return user


def require_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that REQUIRES authentication.

    Raises HTTPException 401 if user is not authenticated.
    Use this for protected routes.

    Sprint 199: Also validates pwd_at claim against DB password_changed_at.
    Tokens issued before a password change are rejected.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    token_data = decode_access_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == token_data.user_id).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated")

    # Sprint 199: Reject tokens issued before the last password change
    if user.password_changed_at is not None:
        if token_data.password_changed_at is None:
            # Token was issued before password_changed_at was tracked — stale
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalidated by password change",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Compare epoch seconds (truncate to int to avoid sub-second drift)
        db_pwd_at = user.password_changed_at
        if db_pwd_at.tzinfo is None:
            from datetime import timezone

            db_pwd_at = db_pwd_at.replace(tzinfo=timezone.utc)
        if int(token_data.password_changed_at.timestamp()) < int(db_pwd_at.timestamp()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalidated by password change",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


def require_verified_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that REQUIRES authentication AND email verification.

    Sprint 57: Verified-Account-Only Model

    Raises:
        HTTPException 401 if user is not authenticated
        HTTPException 403 with code EMAIL_NOT_VERIFIED if email not verified

    Use this for protected routes that require verified accounts.
    """
    # First, require basic authentication
    user = require_current_user(token, db)

    # Then check email verification
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Email verification required. Please check your inbox for the verification email.",
            },
        )

    return user


# =============================================================================
# PYDANTIC SCHEMAS FOR AUTH ENDPOINTS
# =============================================================================

_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;':\",./<>?"


def _check_password_complexity(password: str) -> str:
    """Validate password has uppercase, lowercase, digit, and special character."""
    issues = []
    if not any(c.isupper() for c in password):
        issues.append("Must contain at least one uppercase letter")
    if not any(c.islower() for c in password):
        issues.append("Must contain at least one lowercase letter")
    if not any(c.isdigit() for c in password):
        issues.append("Must contain at least one number")
    if not any(c in _SPECIAL_CHARS for c in password):
        issues.append("Must contain at least one special character")
    if issues:
        raise ValueError(f"Password requirements: {'; '.join(issues)}")
    return password


class UserCreate(BaseModel):
    """Schema for user registration."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "cfo@example.com", "password": "SecurePassword123!"}}
    )

    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _check_password_complexity(v)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class UserResponse(BaseModel):
    """Schema for user data in responses (excludes password)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: Optional[str] = None
    pending_email: Optional[str] = None  # Sprint 203
    is_active: bool
    is_verified: bool
    tier: str = "free"  # Sprint 57: User subscription tier
    created_at: datetime


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile (name and/or email)."""

    model_config = ConfigDict(json_schema_extra={"example": {"name": "John Smith", "email": "john.smith@example.com"}})

    name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = Field(None, max_length=254)


class PasswordChange(BaseModel):
    """Schema for changing password."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"current_password": "OldPassword123!", "new_password": "NewSecurePassword456!"}}
    )

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _check_password_complexity(v)


class AuthResponse(BaseModel):
    """Schema for successful authentication response."""

    access_token: str
    # refresh_token removed — now an HttpOnly cookie set server-side
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    csrf_token: Optional[str] = None  # Security Sprint: user-bound CSRF token


# =============================================================================
# USER CRUD OPERATIONS
# =============================================================================


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email address."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user with hashed password.

    SECURITY: Password is hashed before storage.
    Plaintext password is NEVER stored or logged.
    """
    hashed = hash_password(user_data.password)

    db_user = User(email=user_data.email, hashed_password=hashed)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    log_secure_operation("user_created", f"New user registered: {mask_email(user_data.email)}")

    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Returns User if credentials are valid, None otherwise.
    Updates last_login timestamp on success.
    """
    user = get_user_by_email(db, email)

    if user is None:
        log_secure_operation("auth_failed", f"Unknown email: {mask_email(email)}")
        return None

    if not verify_password(password, user.hashed_password):
        log_secure_operation("auth_failed", f"Invalid password for: {mask_email(email)}")
        return None

    # Update last login timestamp
    user.last_login = datetime.now(UTC)
    db.commit()

    log_secure_operation("auth_success", f"User authenticated: {mask_email(email)}")

    return user


def update_user_profile(db: Session, user: User, profile_data: UserProfileUpdate) -> tuple[User, Optional[str]]:
    """
    Update user profile (name and/or email).

    Sprint 203: Email changes go through pending_email + re-verification.

    Returns:
        Tuple of (updated_user, verification_token_or_None).
        verification_token is set only when an email change is requested.

    Raises ValueError if email already exists or is disposable.
    """
    from disposable_email import is_disposable_email
    from email_service import generate_verification_token

    verification_token = None

    if profile_data.email and profile_data.email != user.email:
        new_email = profile_data.email

        # Check if new email is already taken
        existing = db.query(User).filter(User.email == new_email, User.id != user.id).first()
        if existing:
            raise ValueError("Email already in use by another account")

        # Block disposable emails
        if is_disposable_email(new_email):
            raise ValueError(
                "Temporary or disposable email addresses are not allowed. Please use a permanent email address."
            )

        # Invalidate any previous unused verification tokens
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at == None,  # noqa: E711
        ).update({"used_at": datetime.now(UTC)})

        # Set pending email (NOT user.email — current email stays active)
        user.pending_email = new_email

        # Generate verification token
        token_result = generate_verification_token()
        vt = EmailVerificationToken(
            user_id=user.id,
            token=token_result.token,
            expires_at=token_result.expires_at,
        )
        db.add(vt)

        user.email_verification_token = token_result.token
        user.email_verification_sent_at = datetime.now(UTC)
        verification_token = token_result.token

        log_secure_operation(
            "profile_update",
            f"Email change requested for user {user.id} → pending verification",
        )

    if profile_data.name is not None:
        user.name = profile_data.name if profile_data.name.strip() else None
        log_secure_operation("profile_update", f"Name updated for user {user.id}")

    db.commit()
    db.refresh(user)
    return user, verification_token


def change_user_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
    """
    Change user password after verifying current password.

    Sprint 199: Also sets password_changed_at and revokes all refresh tokens,
    forcing all existing sessions to re-authenticate.

    Returns True if successful, False if current password is incorrect.
    """
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        log_secure_operation("password_change_failed", f"Invalid current password for user {user.id}")
        return False

    # Update password and timestamp
    user.hashed_password = hash_password(new_password)
    user.password_changed_at = datetime.now(UTC)

    # Revoke all refresh tokens — forces re-login on all devices
    _revoke_all_user_tokens(db, user.id)

    db.commit()

    log_secure_operation("password_changed", f"Password changed for user {user.id}, all tokens revoked")
    return True


# =============================================================================
# REFRESH TOKEN OPERATIONS (Sprint 197)
# =============================================================================


def _hash_token(raw_token: str) -> str:
    """Compute SHA-256 hex digest of a raw refresh token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_refresh_token(db: Session, user_id: int) -> tuple[str, RefreshToken]:
    """
    Generate a new refresh token and store its hash in the database.

    Returns:
        Tuple of (raw_token_string, RefreshToken_db_record)
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)

    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)

    log_secure_operation("refresh_token_created", f"Refresh token issued for user_id={user_id}")

    return raw_token, db_token


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[str, str, User]:
    """
    Validate a refresh token, revoke it, and issue a new pair.

    Implements reuse detection: if a revoked token is presented,
    ALL of that user's tokens are revoked (indicates theft).

    Returns:
        Tuple of (new_access_token, new_raw_refresh_token, user)

    Raises:
        HTTPException 401 if token is invalid, expired, or user is inactive
    """
    token_hash = _hash_token(raw_token)
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Reuse detection: revoked token was presented → compromise detected
    if db_token.is_revoked:
        count = _revoke_all_user_tokens(db, db_token.user_id)
        log_secure_operation(
            "refresh_token_reuse_detected",
            f"Revoked token reused for user_id={db_token.user_id}. All {count} active tokens revoked.",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked. All sessions terminated for security.",
        )

    if db_token.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Load user and verify active status
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Rotate: revoke old token, create new one atomically
    new_raw_token = secrets.token_urlsafe(48)
    new_hash = _hash_token(new_raw_token)
    new_expires = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRATION_DAYS)

    db_token.revoked_at = datetime.now(UTC)
    db_token.replaced_by_hash = new_hash

    new_db_token = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=new_expires,
    )
    db.add(new_db_token)

    # Create new access token (with pwd_at claim if password was changed)
    access_token, _ = create_access_token(user.id, user.email, user.password_changed_at, tier=user.tier.value)

    db.commit()

    log_secure_operation("refresh_token_rotated", f"Token rotated for user_id={user.id}")

    return access_token, new_raw_token, user


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    """
    Revoke a single refresh token (logout).

    Returns:
        True if token was found and revoked, False if not found.
    """
    token_hash = _hash_token(raw_token)
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

    if db_token is None:
        return False

    if db_token.is_revoked:
        return False

    db_token.revoked_at = datetime.now(UTC)
    db.commit()

    log_secure_operation("refresh_token_revoked", f"Token revoked for user_id={db_token.user_id}")

    return True


def _revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """
    Revoke ALL active refresh tokens for a user (reuse detection response).

    Returns:
        Count of tokens revoked.
    """
    now = datetime.now(UTC)
    active_tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at == None,  # noqa: E711
        )
        .all()
    )

    count = 0
    for token in active_tokens:
        token.revoked_at = now
        count += 1

    if count > 0:
        db.commit()
        log_secure_operation(
            "all_tokens_revoked",
            f"Revoked {count} active tokens for user_id={user_id}",
        )

    return count


def cleanup_expired_refresh_tokens(db: Session) -> int:
    """
    Delete refresh tokens that are revoked or expired.

    Sprint 201: Called on startup to prevent table bloat.

    Returns:
        Count of tokens deleted.
    """
    now = datetime.now(UTC)
    stale_tokens = (
        db.query(RefreshToken)
        .filter(
            (RefreshToken.revoked_at != None) | (RefreshToken.expires_at < now)  # noqa: E711
        )
        .all()
    )

    count = len(stale_tokens)
    for token in stale_tokens:
        db.delete(token)

    if count > 0:
        db.commit()
        log_secure_operation(
            "refresh_tokens_cleaned",
            f"Deleted {count} expired/revoked refresh tokens",
        )

    return count


def cleanup_expired_verification_tokens(db: Session) -> int:
    """
    Delete verification tokens that are used or expired.

    Sprint 202: Called on startup to prevent table bloat.

    Returns:
        Count of tokens deleted.
    """
    now = datetime.now(UTC)
    stale_tokens = (
        db.query(EmailVerificationToken)
        .filter(
            (EmailVerificationToken.used_at != None) | (EmailVerificationToken.expires_at < now)  # noqa: E711
        )
        .all()
    )

    count = len(stale_tokens)
    for token in stale_tokens:
        db.delete(token)

    if count > 0:
        db.commit()
        log_secure_operation(
            "verification_tokens_cleaned",
            f"Deleted {count} used/expired verification tokens",
        )

    return count
