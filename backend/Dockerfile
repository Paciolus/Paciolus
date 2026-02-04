# =============================================================================
# Paciolus Backend Dockerfile
# Sprint 24: Production Deployment Prep
# =============================================================================
# Zero-Storage Architecture: Container processes data in-memory only.
# Database stores only user metadata, settings, and activity logs - never financial data.
# =============================================================================

FROM python:3.11-slim-bookworm AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Dependencies Stage
# =============================================================================
FROM base AS dependencies

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn for production WSGI server
RUN pip install --no-cache-dir gunicorn==21.2.0

# =============================================================================
# Production Stage
# =============================================================================
FROM dependencies AS production

# Create non-root user for security
RUN groupadd --gid 1000 paciolus \
    && useradd --uid 1000 --gid paciolus --shell /bin/bash --create-home paciolus

# Copy application code
COPY --chown=paciolus:paciolus . .

# Remove any development files
RUN rm -f .env paciolus.db *.pyc __pycache__ 2>/dev/null || true

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
