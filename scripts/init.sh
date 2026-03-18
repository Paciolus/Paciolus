#!/usr/bin/env bash
# =============================================================================
# Paciolus Development Environment Bootstrap
# =============================================================================
# Prerequisites:
#   - Python 3.12+ installed
#   - Node.js 22+ installed
#   - Backend .env file populated from backend/.env.example
#   - Frontend .env.local file populated from frontend/.env.example
#
# Usage:
#   ./scripts/init.sh              # Full startup (install deps + start services)
#   ./scripts/init.sh --check-only # Validate environment without starting services
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CHECK_ONLY=false

if [[ "$1" == "--check-only" ]]; then
    CHECK_ONLY=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
info() { echo -e "       $1"; }

ERRORS=0

echo "============================================="
echo " Paciolus Development Environment Bootstrap"
echo "============================================="
echo ""

# -----------------------------------------------
# Step 1: Check prerequisites
# -----------------------------------------------
echo "--- Checking prerequisites ---"

if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    pass "Python $PY_VERSION"
elif command -v python &>/dev/null; then
    PY_VERSION=$(python --version 2>&1 | awk '{print $2}')
    pass "Python $PY_VERSION"
else
    fail "Python not found — install Python 3.12+"
    ERRORS=$((ERRORS + 1))
fi

if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    pass "Node.js $NODE_VERSION"
else
    fail "Node.js not found — install Node.js 22+"
    ERRORS=$((ERRORS + 1))
fi

if command -v npm &>/dev/null; then
    NPM_VERSION=$(npm --version)
    pass "npm $NPM_VERSION"
else
    fail "npm not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# -----------------------------------------------
# Step 2: Check environment files
# -----------------------------------------------
echo "--- Checking environment files ---"

if [[ -f "$ROOT_DIR/backend/.env" ]]; then
    pass "backend/.env exists"
else
    fail "backend/.env missing — copy from backend/.env.example and configure"
    ERRORS=$((ERRORS + 1))
fi

if [[ -f "$ROOT_DIR/frontend/.env.local" ]]; then
    pass "frontend/.env.local exists"
else
    fail "frontend/.env.local missing — copy from frontend/.env.example and configure"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# -----------------------------------------------
# Step 3: Check/install dependencies
# -----------------------------------------------
echo "--- Checking dependencies ---"

if [[ -f "$ROOT_DIR/backend/requirements.txt" ]]; then
    pass "backend/requirements.txt found"
else
    fail "backend/requirements.txt missing"
    ERRORS=$((ERRORS + 1))
fi

if [[ -f "$ROOT_DIR/frontend/package.json" ]]; then
    pass "frontend/package.json found"
else
    fail "frontend/package.json missing"
    ERRORS=$((ERRORS + 1))
fi

if [[ -d "$ROOT_DIR/frontend/node_modules" ]]; then
    pass "frontend/node_modules exists"
else
    warn "frontend/node_modules missing — will install"
fi

echo ""

if [[ "$CHECK_ONLY" == true ]]; then
    # -----------------------------------------------
    # Check-only: verify services are running
    # -----------------------------------------------
    echo "--- Checking running services (--check-only) ---"

    # Check backend health
    if curl -s -f http://localhost:8000/health/live >/dev/null 2>&1; then
        pass "Backend is running (http://localhost:8000)"
    else
        warn "Backend is not running on port 8000"
    fi

    # Check frontend
    if curl -s -f http://localhost:3000 >/dev/null 2>&1; then
        pass "Frontend is running (http://localhost:3000)"
    else
        warn "Frontend is not running on port 3000"
    fi

    echo ""
    if [[ $ERRORS -gt 0 ]]; then
        fail "Environment check failed with $ERRORS error(s)"
        exit 1
    else
        pass "Environment check passed"
        exit 0
    fi
fi

# -----------------------------------------------
# Step 4: Install dependencies
# -----------------------------------------------
if [[ $ERRORS -gt 0 ]]; then
    fail "Cannot continue — fix the $ERRORS error(s) above first"
    exit 1
fi

echo "--- Installing dependencies ---"

# Backend
echo "Installing backend dependencies..."
cd "$ROOT_DIR/backend"
if command -v python3 &>/dev/null; then
    python3 -m pip install -r requirements.txt --quiet 2>&1 | tail -1
else
    python -m pip install -r requirements.txt --quiet 2>&1 | tail -1
fi
pass "Backend dependencies installed"

# Frontend
echo "Installing frontend dependencies..."
cd "$ROOT_DIR/frontend"
npm install --silent 2>&1 | tail -1
pass "Frontend dependencies installed"

echo ""

# -----------------------------------------------
# Step 5: Start services
# -----------------------------------------------
echo "--- Starting services ---"

# Check if Docker is preferred
if command -v docker-compose &>/dev/null && [[ -f "$ROOT_DIR/docker-compose.yml" ]]; then
    info "Docker detected. To use Docker instead: docker-compose up --build"
fi

# Start backend
cd "$ROOT_DIR/backend"
echo "Starting backend (FastAPI on port 8000)..."
if command -v python3 &>/dev/null; then
    python3 -m uvicorn main:app --reload --port 8000 --host 0.0.0.0 &
else
    python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0 &
fi
BACKEND_PID=$!
info "Backend PID: $BACKEND_PID"

# Start frontend
cd "$ROOT_DIR/frontend"
echo "Starting frontend (Next.js on port 3000)..."
npm run dev &
FRONTEND_PID=$!
info "Frontend PID: $FRONTEND_PID"

# Wait for backend to be ready
echo ""
echo "--- Waiting for services to start ---"
for i in $(seq 1 30); do
    if curl -s -f http://localhost:8000/health/live >/dev/null 2>&1; then
        pass "Backend is ready"
        break
    fi
    if [[ $i -eq 30 ]]; then
        fail "Backend did not start within 30 seconds"
        ERRORS=$((ERRORS + 1))
    fi
    sleep 1
done

echo ""

# -----------------------------------------------
# Step 6: Smoke check
# -----------------------------------------------
echo "--- Running smoke check ---"

if curl -s -f http://localhost:8000/health/live >/dev/null 2>&1; then
    pass "Backend health check passed"
else
    fail "Backend health check failed"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "============================================="
if [[ $ERRORS -gt 0 ]]; then
    fail "Environment failed at step above — $ERRORS error(s)"
    exit 1
else
    pass "Environment ready"
    info "Backend:  http://localhost:8000"
    info "Frontend: http://localhost:3000"
    info "API Docs: http://localhost:8000/docs"
fi
echo "============================================="
