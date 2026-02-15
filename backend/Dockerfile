# =============================================================================
# Paciolus Backend Dockerfile
# Sprint 150: Multi-stage hardening
# =============================================================================
# Zero-Storage Architecture: Container processes data in-memory only.
# Database stores only user metadata, settings, and activity logs - never financial data.
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder — install compiled dependencies (gcc required)
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install to isolated prefix — avoids copying pip/setuptools/wheel to production (~20MB savings)
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt gunicorn==21.2.0

# -----------------------------------------------------------------------------
# Stage 2: Production — clean image, no compiler toolchain
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Copy only application dependencies from builder (no gcc, pip, setuptools)
COPY --from=builder /install/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /install/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=builder /install/bin/uvicorn /usr/local/bin/uvicorn

# Install curl for lightweight health checks (avoids spawning full Python interpreter)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 paciolus \
    && useradd --uid 1000 --gid paciolus --shell /bin/bash --create-home paciolus

# Copy application code
COPY --chown=paciolus:paciolus . .

# Switch to non-root user
USER paciolus

# Expose port
EXPOSE 8000

# Health check — curl is ~100x lighter than spawning a Python interpreter every 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command using Gunicorn + Uvicorn workers
# Tuning parameters (all configurable via environment variables):
#   WEB_CONCURRENCY:          Worker count. Default 4. Formula: (2 * CPU cores) + 1
#   GUNICORN_TIMEOUT:         Worker timeout for large file processing. Default 120s
#   GUNICORN_GRACEFUL_TIMEOUT: Time to finish in-flight requests on shutdown. Default 30s
#   GUNICORN_KEEP_ALIVE:      Keep-alive for reverse proxy compatibility. Default 5s
#   GUNICORN_MAX_REQUESTS:    Worker recycling to prevent memory leaks (Pandas). Default 1000
CMD ["sh", "-c", \
    "gunicorn main:app \
     --bind 0.0.0.0:8000 \
     --workers ${WEB_CONCURRENCY:-4} \
     --worker-class uvicorn.workers.UvicornWorker \
     --timeout ${GUNICORN_TIMEOUT:-120} \
     --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-30} \
     --keep-alive ${GUNICORN_KEEP_ALIVE:-5} \
     --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
     --max-requests-jitter 50 \
     --access-logfile - \
     --error-logfile - \
     --capture-output"]
