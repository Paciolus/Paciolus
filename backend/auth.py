"""
Paciolus Authentication Module
Day 13: Secure Commercial Infrastructure

JWT-based authentication with bcrypt password hashing.

Industry-standard libraries used:
- python-jose (JWT encoding/decoding) - MIT License
- passlib (password hashing) - BSD License
- bcrypt (hashing algorithm) - Apache 2.0 License

All libraries are open-source with permissive licenses.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES
from database import get_db
from models import User
from security_utils import log_secure_operation


# =============================================================================
# PASSWORD HASHING
# =============================================================================

# bcrypt context for secure password hashing
# bcrypt automatically handles salting and is resistant to rainbow table attacks
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    SECURITY: Password is NEVER logged or stored in plaintext.
    The bcrypt hash includes a random salt automatically.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Returns True if password matches, False otherwise.
    Uses constant-time comparison to prevent timing attacks.
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT TOKEN HANDLING
# =============================================================================

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: Optional[int] = None
    email: Optional[str] = None


def create_access_token(user_id: int, email: str) -> tuple[str, datetime]:
    """
    Create a JWT access token for a user.

    Args:
        user_id: Database ID of the user
        email: User's email address

    Returns:
        Tuple of (token_string, expiration_datetime)
    """
    expire = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRATION_MINUTES)

    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "email": email,
        "iat": datetime.now(UTC),  # Issued at
        "exp": expire,  # Expiration
    }

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

        return TokenData(user_id=int(user_id), email=email)

    except JWTError as e:
        log_secure_operation("token_decode_failed", str(e))
        return None


# =============================================================================
# AUTHENTICATION DEPENDENCIES
# =============================================================================

def get_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
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
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that REQUIRES authentication.

    Raises HTTPException 401 if user is not authenticated.
    Use this for protected routes.
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


def require_verified_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
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
                "message": "Email verification required. Please check your inbox for the verification email."
            }
        )

    return user


# =============================================================================
# PYDANTIC SCHEMAS FOR AUTH ENDPOINTS
# =============================================================================

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "cfo@example.com",
                "password": "SecurePassword123!"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Schema for user data in responses (excludes password)."""
    id: int
    email: str
    name: Optional[str] = None
    is_active: bool
    is_verified: bool
    tier: str = "free"  # Sprint 57: User subscription tier
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile (name and/or email)."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Smith",
                "email": "john.smith@example.com"
            }
        }


class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!"
            }
        }


class AuthResponse(BaseModel):
    """Schema for successful authentication response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


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

    db_user = User(
        email=user_data.email,
        hashed_password=hashed
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    log_secure_operation("user_created", f"New user registered: {user_data.email[:10]}...")

    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.

    Returns User if credentials are valid, None otherwise.
    Updates last_login timestamp on success.
    """
    user = get_user_by_email(db, email)

    if user is None:
        log_secure_operation("auth_failed", f"Unknown email: {email[:10]}...")
        return None

    if not verify_password(password, user.hashed_password):
        log_secure_operation("auth_failed", f"Invalid password for: {email[:10]}...")
        return None

    # Update last login timestamp
    user.last_login = datetime.now(UTC)
    db.commit()

    log_secure_operation("auth_success", f"User authenticated: {email[:10]}...")

    return user


def update_user_profile(db: Session, user: User, profile_data: UserProfileUpdate) -> User:
    """
    Update user profile (name and/or email).

    Returns updated user object.
    Raises ValueError if email already exists for another user.
    """
    if profile_data.email and profile_data.email != user.email:
        # Check if new email is already taken
        existing = db.query(User).filter(
            User.email == profile_data.email,
            User.id != user.id
        ).first()
        if existing:
            raise ValueError("Email already in use by another account")
        user.email = profile_data.email
        log_secure_operation("profile_update", f"Email changed for user {user.id}")

    if profile_data.name is not None:
        user.name = profile_data.name if profile_data.name.strip() else None
        log_secure_operation("profile_update", f"Name updated for user {user.id}")

    db.commit()
    db.refresh(user)
    return user


def change_user_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
    """
    Change user password after verifying current password.

    Returns True if successful, False if current password is incorrect.
    Raises ValueError if new password doesn't meet requirements.
    """
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        log_secure_operation("password_change_failed", f"Invalid current password for user {user.id}")
        return False

    # Validate new password strength
    is_valid, issues = validate_password_strength(new_password)
    if not is_valid:
        raise ValueError(f"New password does not meet requirements: {', '.join(issues)}")

    # Update password
    user.hashed_password = hash_password(new_password)
    db.commit()

    log_secure_operation("password_changed", f"Password changed for user {user.id}")
    return True


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength.

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    if len(password) < 8:
        issues.append("Password must be at least 8 characters")

    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")

    # Check for special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    if not any(c in special_chars for c in password):
        issues.append("Password must contain at least one special character")

    return len(issues) == 0, issues
