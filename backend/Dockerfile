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

RUN pip install --no-cache-dir -r requirements.txt gunicorn==21.2.0

# -----------------------------------------------------------------------------
# Stage 2: Production — clean image, no compiler toolchain
# -----------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Copy installed packages from builder (no gcc in this stage)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Create non-root user for security
RUN groupadd --gid 1000 paciolus \
    && useradd --uid 1000 --gid paciolus --shell /bin/bash --create-home paciolus

# Copy application code
COPY --chown=paciolus:paciolus . .

# Switch to non-root user
USER paciolus

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Production command using Gunicorn
# Workers: (2 * CPU cores) + 1 is recommended
# Timeout: 120s for large file processing
CMD ["gunicorn", "main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output"]
