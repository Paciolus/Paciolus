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
from pydantic import BaseModel, EmailStr
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

async def get_current_user(
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


async def require_current_user(
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


# =============================================================================
# PYDANTIC SCHEMAS FOR AUTH ENDPOINTS
# =============================================================================

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str

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
    password: str


class UserResponse(BaseModel):
    """Schema for user data in responses (excludes password)."""
    id: int
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


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
