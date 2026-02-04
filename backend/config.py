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
if _jwt_secret is None or _jwt_secret.strip() == "":
    if ENV_MODE == "production":
        _hard_fail("JWT_SECRET_KEY is required in production mode.")
    else:
        # Development fallback - generate a random key (not for production!)
        import secrets
        _jwt_secret = secrets.token_hex(32)
        print("[WARNING] JWT_SECRET_KEY not set. Using auto-generated key for development.")

JWT_SECRET_KEY = _jwt_secret
JWT_ALGORITHM = _load_optional("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(_load_optional("JWT_EXPIRATION_MINUTES", "1440"))  # 24 hours default

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
    print(f"  Database: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"  Database: {DATABASE_URL}")
    print('='*60 + "\n")
