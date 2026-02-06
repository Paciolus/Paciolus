"""
Paciolus Backend API

Application entry point — creates the FastAPI app, registers middleware,
and includes all route modules.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from security_utils import log_secure_operation
from security_middleware import SecurityHeadersMiddleware
from database import init_db
from config import API_HOST, API_PORT, CORS_ORIGINS, DEBUG, print_config_summary
from shared.rate_limits import limiter
from routes import all_routers

# Re-exports for test compatibility
# Tests import: from main import app, require_verified_user
from auth import require_verified_user  # noqa: F401

app = FastAPI(
    title="Paciolus API",
    description="Trial Balance Diagnostic Intelligence for Financial Professionals",
    version="0.47.0"
)

# CORS configuration from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware, production_mode=not DEBUG)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register all route modules
for router in all_routers:
    app.include_router(router)


@app.on_event("startup")
async def startup_event():
    init_db()
    log_secure_operation("app_startup", "Paciolus API started")


if __name__ == "__main__":
    import uvicorn
    print_config_summary()
    uvicorn.run(app, host=API_HOST, port=API_PORT)
