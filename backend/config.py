"""
CloseSignify Configuration Module
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
    print("CONFIGURATION ERROR - CloseSignify cannot start")
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

# API URL that the backend is served from (used for CORS)
API_HOST = _load_required("API_HOST")
API_PORT = int(_load_required("API_PORT"))

# Allowed frontend origins for CORS (comma-separated)
CORS_ORIGINS = [
    origin.strip()
    for origin in _load_required("CORS_ORIGINS").split(",")
]

# =============================================================================
# OPTIONAL CONFIGURATION
# =============================================================================

# Environment mode
ENV_MODE = _load_optional("ENV_MODE", "development")

# Debug mode (enables detailed error messages)
DEBUG = _load_optional("DEBUG", "false").lower() == "true"


# =============================================================================
# CONFIGURATION SUMMARY (logged at startup)
# =============================================================================

def print_config_summary() -> None:
    """Print configuration summary for verification."""
    print(f"\n{'='*60}")
    print("CloseSignify Configuration Loaded")
    print('='*60)
    print(f"  Environment: {ENV_MODE}")
    print(f"  API Host:    {API_HOST}")
    print(f"  API Port:    {API_PORT}")
    print(f"  CORS Origins: {CORS_ORIGINS}")
    print(f"  Debug Mode:  {DEBUG}")
    print('='*60 + "\n")
