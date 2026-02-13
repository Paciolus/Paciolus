"""
Paciolus Configuration Module
Hard fails if .env file is missing or required variables are not set.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Determine the .env file path
ENV_FILE = Path(__file__).parent / ".env"


def _hard_fail(message: str) -> None:
    """Print error message and exit with failure code."""
    print(f"\n{'='*60}")
    print("CONFIGURATION ERROR - Paciolus cannot start")
    print('='*60)
    print(f"\n{message}\n")
    print("Please create a .env file based on .env.example")
    print(f"Expected location: {ENV_FILE}")
    print('='*60 + "\n")
    sys.exit(1)


def _load_required(var_name: str) -> str:
    """Load a required environment variable or hard fail."""
    value = os.getenv(var_name)
    if value is None or value.strip() == "":
        _hard_fail(f"Required environment variable '{var_name}' is not set.")
    return value.strip()


def _load_optional(var_name: str, default: str) -> str:
    """Load an optional environment variable with a default."""
    value = os.getenv(var_name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


# Check if .env file exists
if not ENV_FILE.exists():
    _hard_fail(f".env file not found at: {ENV_FILE}")

# Load environment variables from .env file
load_dotenv(ENV_FILE)

# =============================================================================
# REQUIRED CONFIGURATION
# =============================================================================

# Environment mode (development/production)
ENV_MODE = _load_optional("ENV_MODE", "development")

# API URL that the backend is served from (used for CORS)
API_HOST = _load_required("API_HOST")
API_PORT = int(_load_required("API_PORT"))

# Allowed frontend origins for CORS (comma-separated)
_cors_raw = _load_required("CORS_ORIGINS")
CORS_ORIGINS = [
    origin.strip()
    for origin in _cors_raw.split(",")
    if origin.strip()  # Filter empty strings
]

# Production CORS validation (Sprint 24)
if ENV_MODE == "production":
    # Validate no wildcards in production
    if "*" in _cors_raw:
        _hard_fail(
            "Wildcard (*) CORS origins are not allowed in production mode.\n"
            "Please specify explicit origins in CORS_ORIGINS."
        )
    # Validate HTTPS in production
    for origin in CORS_ORIGINS:
        if not origin.startswith("https://"):
            print(f"[WARNING] Non-HTTPS origin in production: {origin}")
            print("           Consider using HTTPS for all production origins.")

# =============================================================================
# OPTIONAL CONFIGURATION
# =============================================================================

# Environment mode
ENV_MODE = _load_optional("ENV_MODE", "development")

# Debug mode (enables detailed error messages)
DEBUG = _load_optional("DEBUG", "false").lower() == "true"

# =============================================================================
# AUTHENTICATION CONFIGURATION (Day 13)
# =============================================================================

# JWT Secret Key - REQUIRED for production, auto-generated for development
_jwt_secret = os.getenv("JWT_SECRET_KEY")
_using_generated_jwt = False

if _jwt_secret is None or _jwt_secret.strip() == "":
    if ENV_MODE == "production":
        _hard_fail("JWT_SECRET_KEY is required in production mode.")
    else:
        # Development fallback - generate a random key (not for production!)
        import secrets
        _jwt_secret = secrets.token_hex(32)
        _using_generated_jwt = True
        print("[WARNING] JWT_SECRET_KEY not set. Using auto-generated key for development.")

# Sprint 25: Additional security validation
# Warn if using auto-generated key while bound to public interfaces
if _using_generated_jwt and API_HOST in ("0.0.0.0", "::"):
    print("\n" + "!" * 60)
    print("SECURITY WARNING: Auto-generated JWT key with public binding!")
    print("!" * 60)
    print("You are using an auto-generated JWT_SECRET_KEY while binding")
    print(f"to '{API_HOST}', which makes the server publicly accessible.")
    print("")
    print("This is INSECURE because:")
    print("  - JWT tokens can be forged if the key is predictable")
    print("  - Session tokens will be invalidated on every restart")
    print("")
    print("To fix: Set JWT_SECRET_KEY in your .env file:")
    print(f"  JWT_SECRET_KEY={secrets.token_hex(32)}")
    print("!" * 60 + "\n")

JWT_SECRET_KEY = _jwt_secret

# Validate JWT secret strength (minimum 32 characters for HS256)
if not _using_generated_jwt and len(JWT_SECRET_KEY) < 32:
    if ENV_MODE == "production":
        _hard_fail(
            f"JWT_SECRET_KEY is too short ({len(JWT_SECRET_KEY)} chars).\n"
            "For HS256, use at least 32 characters (64 hex chars recommended).\n"
            f"Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    else:
        print(f"[WARNING] JWT_SECRET_KEY is short ({len(JWT_SECRET_KEY)} chars). "
              "Use at least 32 characters for production.")

JWT_ALGORITHM = _load_optional("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(_load_optional("JWT_EXPIRATION_MINUTES", "1440"))  # 24 hours default
REFRESH_TOKEN_EXPIRATION_DAYS = int(_load_optional("REFRESH_TOKEN_EXPIRATION_DAYS", "7"))

# Database URL - SQLite by default for local development
DATABASE_URL = _load_optional(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).parent / 'paciolus.db'}"
)


# =============================================================================
# CONFIGURATION SUMMARY (logged at startup)
# =============================================================================

def print_config_summary() -> None:
    """Print configuration summary for verification."""
    print(f"\n{'='*60}")
    print("Paciolus Configuration Loaded")
    print('='*60)
    print(f"  Environment: {ENV_MODE}")
    print(f"  API Host:    {API_HOST}")
    print(f"  API Port:    {API_PORT}")
    print(f"  CORS Origins: {CORS_ORIGINS}")
    print(f"  Debug Mode:  {DEBUG}")
    print(f"  JWT Algorithm: {JWT_ALGORITHM}")
    print(f"  JWT Expiration: {JWT_EXPIRATION_MINUTES} minutes")
    print(f"  Refresh Token Expiration: {REFRESH_TOKEN_EXPIRATION_DAYS} days")
    print(f"  Database: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"  Database: {DATABASE_URL}")
    print('='*60 + "\n")
