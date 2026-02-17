"""
Paciolus Backend API

Application entry point — creates the FastAPI app, registers middleware,
and includes all route modules.
"""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from logging_config import setup_logging, request_id_var
from security_utils import log_secure_operation
from security_middleware import (
    SecurityHeadersMiddleware, MaxBodySizeMiddleware, CSRFMiddleware,
    RequestIdMiddleware,
)
from database import init_db
from config import (
    API_HOST, API_PORT, CORS_ORIGINS, DEBUG, ENV_MODE,
    SENTRY_DSN, SENTRY_TRACES_SAMPLE_RATE, print_config_summary,
)
from shared.rate_limits import limiter
from routes import all_routers
from version import __version__

# Initialize logging before anything else
setup_logging()
logger = logging.getLogger(__name__)

# Sprint 275: Sentry APM — init before app creation, only if DSN configured
if SENTRY_DSN:
    import sentry_sdk

    def _before_send(event, hint):
        """Strip request bodies to comply with Zero-Storage policy."""
        if "request" in event and "data" in event["request"]:
            event["request"]["data"] = "[Stripped — Zero-Storage]"
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENV_MODE,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,
        before_send=_before_send,
    )
    logger.info("Sentry APM initialized (env=%s, traces=%.0f%%)", ENV_MODE, SENTRY_TRACES_SAMPLE_RATE * 100)

# Re-exports for test compatibility
# Tests import: from main import app, require_verified_user
from auth import require_verified_user  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — runs startup/shutdown logic."""
    # --- Startup ---
    init_db()
    logger.info("Database initialized")

    # Sprint 201/202: Clean up stale tokens on startup
    from auth import cleanup_expired_refresh_tokens, cleanup_expired_verification_tokens
    from tool_session_model import cleanup_expired_tool_sessions, sanitize_existing_sessions
    from retention_cleanup import run_retention_cleanup
    from database import SessionLocal
    db = SessionLocal()
    try:
        count = cleanup_expired_refresh_tokens(db)
        if count > 0:
            logger.info("Cleaned %d stale refresh tokens", count)
            log_secure_operation("startup_cleanup", f"Cleaned {count} stale refresh tokens")
        v_count = cleanup_expired_verification_tokens(db)
        if v_count > 0:
            logger.info("Cleaned %d stale verification tokens", v_count)
            log_secure_operation("startup_cleanup", f"Cleaned {v_count} stale verification tokens")
        # Sprint 262: Clean up expired tool sessions
        ts_count = cleanup_expired_tool_sessions(db)
        if ts_count > 0:
            logger.info("Cleaned %d expired tool sessions", ts_count)
            log_secure_operation("startup_cleanup", f"Cleaned {ts_count} expired tool sessions")
        # Packet 2: Sanitize legacy tool sessions with financial data
        san_count = sanitize_existing_sessions(db)
        if san_count > 0:
            logger.info("Sanitized %d legacy tool sessions", san_count)
            log_secure_operation("startup_cleanup", f"Sanitized {san_count} legacy tool sessions")
        # Packet 8: Retention cleanup for aggregate metadata
        retention = run_retention_cleanup(db)
        retention_total = sum(retention.values())
        if retention_total > 0:
            log_secure_operation(
                "startup_retention_cleanup",
                f"Retention cleanup: {retention}",
            )
    finally:
        db.close()

    logger.info("Paciolus API v%s started (debug=%s)", __version__, DEBUG)
    log_secure_operation("app_startup", "Paciolus API started")

    yield  # Application runs here

    # --- Shutdown (if needed in future) ---


app = FastAPI(
    title="Paciolus API",
    description="Trial Balance Diagnostic Intelligence for Financial Professionals",
    version=__version__,
    lifespan=lifespan,
)

# CORS configuration from environment — explicit methods/headers (Sprint 200)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "Accept"],
)

# GZip compression for responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware, production_mode=not DEBUG)

# CSRF protection for state-changing requests (Sprint 200)
app.add_middleware(CSRFMiddleware)

# Global request body size limit (110 MB — above per-file 100 MB to allow multipart overhead)
app.add_middleware(MaxBodySizeMiddleware)

# Request ID for log correlation (Sprint 211)
app.add_middleware(RequestIdMiddleware)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global catch-all for unhandled exceptions — prevents stack trace leakage
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    rid = request_id_var.get("-")
    logger.exception("Unhandled exception on %s %s [request_id=%s]", request.method, request.url.path, rid)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": rid},
    )


# Register all route modules
for router in all_routers:
    app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    print_config_summary()
    uvicorn.run(app, host=API_HOST, port=API_PORT)
