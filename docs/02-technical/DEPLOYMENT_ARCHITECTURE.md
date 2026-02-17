# Deployment & Operations Architecture

**Document Classification:** Internal (DevOps, SRE)  
**Version:** 1.0  
**Last Updated:** February 4, 2026  
**Owner:** Chief Technology Officer / DevOps Lead  
**Review Cycle:** Monthly

---

## Executive Summary

This document provides comprehensive deployment and operational procedures for Paciolus. The platform follows a **stateless, cloud-native architecture** designed for reliability, scalability, and zero-downtime deployments.

**Recommended Production Stack:**
- ✅ **Frontend:** Vercel (Next.js, global CDN)
- ✅ **Backend:** Render / DigitalOcean App Platform (FastAPI, Docker)
- ✅ **Database:** PostgreSQL (managed service)
- ✅ **Monitoring:** Sentry (error tracking)

**Key Capabilities:**
- Zero-downtime deployments via blue-green strategy
- Automatic HTTPS with Let's Encrypt
- Horizontal scaling (backend instances)
- Daily automated database backups
- 99.9% uptime SLA target

**Target Audience:** DevOps engineers, SRE teams, technical leadership

---

## Table of Contents

1. [Production Architecture](#1-production-architecture)
2. [Prerequisites](#2-prerequisites)
3. [Environment Configuration](#3-environment-configuration)
4. [Frontend Deployment (Vercel)](#4-frontend-deployment-vercel)
5. [Backend Deployment (Render)](#5-backend-deployment-render)
6. [Backend Deployment (DigitalOcean)](#6-backend-deployment-digitalocean)
7. [Docker Deployment](#7-docker-deployment)
8. [Database Configuration](#8-database-configuration)
9. [Monitoring and Observability](#9-monitoring-and-observability)
10. [Backup and Recovery](#10-backup-and-recovery)
11. [Scaling Strategies](#11-scaling-strategies)
12. [Security Hardening](#12-security-hardening)
13. [Runbook: Common Operations](#13-runbook-common-operations)
14. [Disaster Recovery](#14-disaster-recovery)
15. [Cost Optimization](#15-cost-optimization)
16. [Post-Deployment Checklist](#16-post-deployment-checklist)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. Production Architecture

### 1.1 Deployment Topology

```
┌───────────────────────────────────────────────────────────────┐
│ DNS (Cloudflare / Vercel DNS)                                 │
│ paciolus.com → Vercel Edge Network                            │
│ api.paciolus.com → Render/DigitalOcean Load Balancer          │
└────────────────────────┬──────────────────────────────────────┘
                         │
         ┌───────────────┴────────────────┐
         │                                │
         ▼                                ▼
┌─────────────────────┐          ┌──────────────────────┐
│ VERCEL CDN          │          │ BACKEND CLUSTER      │
│ (Global Edge)       │          │ (Render/DO)          │
│                     │          │                      │
│ ┌─────────────────┐ │          │ ┌────────────────┐  │
│ │ Next.js         │ │          │ │ Instance 1     │  │
│ │ Static Assets   │ │          │ │ FastAPI+Uvicorn│  │
│ │ Serverless Fns  │ │          │ └────────────────┘  │
│ └─────────────────┘ │          │ ┌────────────────┐  │
│                     │          │ │ Instance 2     │  │
│ Features:           │          │ │ FastAPI+Uvicorn│  │
│ - Auto-HTTPS        │          │ └────────────────┘  │
│ - DDoS Protection   │          │                      │
│ - Cache Control     │          │ Load Balancer:       │
│ - Analytics         │          │ - Round-robin        │
└─────────────────────┘          │ - Health checks      │
         │                       │                      │
         │                       └──────────┬───────────┘
         │                                  │
         │ HTTPS API Calls                  │ PostgreSQL
         │                                  │ Connection Pool
         │                                  ▼
         │                       ┌──────────────────────┐
         │                       │ POSTGRESQL (Managed) │
         │                       │                      │
         │                       │ - Primary instance   │
         │                       │ - Daily backups      │
         │                       │ - Encryption at rest │
         │                       │ - Connection pooling │
         └──────────────────────→└──────────────────────┘
```

### 1.2 Infrastructure Providers

| Component | Provider (Primary) | Provider (Alternative) | Rationale |
|-----------|-------------------|------------------------|-----------|
| **Frontend** | Vercel | Netlify | Best Next.js integration, global CDN |
| **Backend** | Render | DigitalOcean App Platform | Ease of use, Docker support |
| **Database** | Render PostgreSQL | DigitalOcean Managed DB | Integrated with backend provider |
| **DNS** | Vercel DNS | Cloudflare | Automatic HTTPS, simple setup |
| **Monitoring** | Sentry | Datadog | Error tracking, APM |

---

## 2. Prerequisites

### 2.1 Accounts Required

- [ ] GitHub account (code repository)
- [ ] Vercel account (frontend hosting)
- [ ] Render or DigitalOcean account (backend hosting)
- [ ] Domain registrar (optional but recommended)
- [ ] Sentry account (error monitoring, optional)

### 2.2 Local Development Tools

**Required:**
- Node.js 20+ (`node --version`)
- Python 3.11+ (`python --version`)
- Git (`git --version`)

**Optional:**
- Docker Desktop (`docker --version`)
- PostgreSQL client (`psql --version`)
- Postman / Insomnia (API testing)

---

## 3. Environment Configuration

### 3.1 Backend Environment Variables

**Production `.env`:**

```bash
# === ENVIRONMENT ===
ENV_MODE=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000  # Or ${PORT} for Render auto-detection

# === SECURITY ===
CORS_ORIGINS=https://paciolus.com,https://www.paciolus.com
JWT_SECRET_KEY=<64-character-hex-string>  # ROTATE EVERY 90 DAYS
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=480  # 8 hours

# === DATABASE ===
DATABASE_URL=postgresql://user:password@host:5432/paciolus
# Example: postgresql://paciolus_user:abc123@dpg-xxx.render.com:5432/paciolus_db

# === OPTIONAL ===
SENTRY_DSN=https://xxx@sentry.io/xxx  # Error tracking
LOG_LEVEL=INFO  # INFO, WARNING, ERROR
```

**Generate JWT secret:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Output: e4a2b1c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1
```

### 3.2 Frontend Environment Variables

**Production (Vercel environment variables):**

```bash
# === API Configuration ===
NEXT_PUBLIC_API_URL=https://api.paciolus.com
# Or: https://paciolus-api.onrender.com

# === Analytics (optional) ===
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX  # Google Analytics
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

**Note:** All variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

### 3.3 Secrets Management

| Environment | Storage Method | Access Control |
|-------------|----------------|----------------|
| **Local Dev** | `.env` files (gitignored) | Developer machine only |
| **Staging** | Render/Vercel env vars | Team access |
| **Production** | Render/Vercel env vars (encrypted) | Admin access only |

**Security best practices:**
- ✅ Never commit `.env` files to Git
- ✅ Rotate `JWT_SECRET_KEY` every 90 days
- ✅ Use different secrets per environment
- ✅ Limit access to production secrets

---

## 4. Frontend Deployment (Vercel)

### 4.1 Initial Setup

**Step 1: Connect Repository**

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click "Add New → Project"
3. Import your Paciolus repository
4. Configure:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)
   - **Install Command:** `npm ci` (default)

**Step 2: Environment Variables**

In Vercel dashboard → Project Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL = https://api.paciolus.com
```

**Step 3: Deploy**

Click "Deploy" → Vercel builds and deploys automatically.

**Deployment URL:** `https://paciolus.vercel.app` (auto-generated)

### 4.2 Custom Domain

**Add custom domain:**

1. Go to Project Settings → Domains
2. Add `paciolus.com` and `www.paciolus.com`
3. Configure DNS records as instructed by Vercel:
   - **A record:** `@` → `76.76.21.21`
   - **CNAME:** `www` → `cname.vercel-dns.com`
4. Wait for DNS propagation (5-60 minutes)
5. Vercel automatically provisions SSL certificate (Let's Encrypt)

**Update backend CORS:**

```bash
# backend/.env (production)
CORS_ORIGINS=https://paciolus.com,https://www.paciolus.com
```

### 4.3 Vercel Deployment Configuration

**`vercel.json` (optional, for advanced config):**

```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "framework": "nextjs",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.paciolus.com/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

### 4.4 Continuous Deployment

**Automatic deploys:**
- Every push to `main` branch → Production deployment
- Every push to feature branches → Preview deployment

**Disable auto-deploy:**
Project Settings → Git → Uncheck "Production Branch: main"

---

## 5. Backend Deployment (Render)

### 5.1 Initial Setup

**Step 1: Create Web Service**

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - **Name:** `paciolus-api`
   - **Region:** Oregon (US West) or closest to users
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:**
     ```bash
     gunicorn main:app --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120 --access-logfile - --error-logfile -
     ```

**Step 2: Create Database**

1. Click "New +" → "PostgreSQL"
2. Configure:
   - **Name:** `paciolus-db`
   - **Database:** `paciolus`
   - **User:** `paciolus_user`
   - **Region:** Oregon (same as web service)
   - **Plan:** Free (starter) or Starter ($7/month production)
3. Copy "Internal Database URL" for next step

**Step 3: Set Environment Variables**

In Render dashboard → Web Service → Environment:

```
API_HOST=0.0.0.0
API_PORT=10000
ENV_MODE=production
DEBUG=false
CORS_ORIGINS=https://paciolus.com,https://www.paciolus.com
JWT_SECRET_KEY=<your-generated-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=480
DATABASE_URL=<internal-database-url-from-step-2>
```

**Step 4: Deploy**

Click "Create Web Service" → Render builds and deploys automatically.

**API URL:** `https://paciolus-api.onrender.com`

### 5.2 Health Checks

Configure in Render dashboard → Settings → Health & Alerts:

```
Health Check Path: /health
```

Render will ping `GET /health` every 30 seconds. If it fails 3 times, the instance is restarted.

### 5.3 Auto-Scaling (Paid Plans)

Render Starter plan and above support auto-scaling:

- **Min instances:** 1
- **Max instances:** 5
- **Scale up on:** CPU >80% for 2 minutes
- **Scale down on:** CPU <30% for 5 minutes

---

## 6. Backend Deployment (DigitalOcean)

### 6.1 DigitalOcean App Platform Setup

**Step 1: Create App**

1. Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)
2. Click "Apps" → "Create App"
3. Connect GitHub repository
4. Configure Components:

**API Component:**

```yaml
name: paciolus-api
type: service  # Web service
source:
  repo: your-github-org/paciolus
  branch: main
  deploy_on_push: true
build:
  context: backend
  dockerfile_path: backend/Dockerfile
run:
  command: |
    gunicorn main:app --bind 0.0.0.0:8080 --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120
http_port: 8080
instance_count: 1
instance_size: basic-xs  # $5/month (512MB RAM, 1 vCPU)
health_check:
  http_path: /health
```

**Database Component:**

```yaml
name: paciolus-db
type: database
engine: postgresql
version: 15
size: db-s-dev-database  # $7/month (Development tier)
```

**Step 2: Environment Variables**

```
API_HOST=0.0.0.0
API_PORT=8080
ENV_MODE=production
CORS_ORIGINS=https://paciolus.com
JWT_SECRET_KEY=<your-secret>
DATABASE_URL=${db.DATABASE_URL}  # Auto-injected by DO
```

**Step 3: Custom Domain**

Add custom domain: `api.paciolus.com`

**DNS Configuration:**
- **CNAME:** `api` → `paciolus-api.ondigitalocean.app`

### 6.2 DigitalOcean Auto-Scaling

Configure in App → Settings → Resources:

- **Instance size:** Basic ($5-12/month per instance)
- **Autoscaling:** Enable
- **Min instances:** 1
- **Max instances:** 3

---

## 7. Docker Deployment

### 7.1 Backend Dockerfile

**`backend/Dockerfile` (multi-stage build):**

```dockerfile
# === Stage 1: Builder ===
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# === Stage 2: Runtime ===
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Add .local/bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "120"]
```

**Build and run:**

```bash
# Build
docker build -t paciolus-backend:latest backend/

# Run locally
docker run -p 8000:8000 --env-file backend/.env paciolus-backend:latest

# Test
curl http://localhost:8000/health
```

### 7.2 Docker Compose (Local Development)

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - ENV_MODE=development
      - CORS_ORIGINS=http://localhost:3000
      - JWT_SECRET_KEY=dev-secret-change-me
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/paciolus
    depends_on:
      - db
    volumes:
      - ./backend:/app  # Hot reload in dev

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=paciolus
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app  # Hot reload in dev
      - /app/node_modules  # Persist node_modules
      - /app/.next  # Persist Next.js build cache

volumes:
  postgres_data:
```

**Usage:**

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up --build
```

---

## 8. Database Configuration

### 8.1 Initial Schema Setup

**Automatic schema creation:**

SQLAlchemy creates tables automatically on first run:

```python
# backend/database.py
def init_db():
    Base.metadata.create_all(bind=engine)
```

**Manual schema creation (if needed):**

```bash
# Connect to database
psql $DATABASE_URL

# Verify tables were created
\dt

# Expected tables:
# - users
# - clients
# - activity_logs
# - diagnostic_summaries
```

### 8.2 Database Migrations (Alembic)

Alembic is installed and configured since Phase XXI (Sprint 181). The baseline migration
covers the full current schema.

```bash
# Create a new migration after model changes
cd backend
alembic revision --autogenerate -m "Add new field to users table"

# Apply all pending migrations
alembic upgrade head

# Check current migration state
alembic current

# Roll back one migration
alembic downgrade -1
```

**Note:** `init_db()` still calls `Base.metadata.create_all()` at startup for fresh
installs. For existing databases, use Alembic migrations to apply schema changes.

### 8.3 Connection Pooling

Implemented in Sprint 274. PostgreSQL connections use SQLAlchemy's QueuePool with
tunable parameters via environment variables. SQLite bypasses pooling automatically.

```python
# backend/database.py (actual implementation)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,               # Verify connections before use
    pool_size=DB_POOL_SIZE,            # env: DB_POOL_SIZE, default 10
    max_overflow=DB_MAX_OVERFLOW,      # env: DB_MAX_OVERFLOW, default 20
    pool_recycle=DB_POOL_RECYCLE,      # env: DB_POOL_RECYCLE, default 3600
)
```

**Environment variables** (set in `.env` or container env):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_POOL_SIZE` | 10 | Max persistent connections per worker |
| `DB_MAX_OVERFLOW` | 20 | Burst connections above pool_size |
| `DB_POOL_RECYCLE` | 3600 | Recycle after N seconds (avoids stale TCP) |

---

## 9. Monitoring and Observability

### 9.1 Error Tracking (Sentry)

**Backend integration:**

```python
# backend/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENV_MODE"),
    traces_sample_rate=0.1,  # 10% of transactions
)
```

**Frontend integration:**

```typescript
// frontend/src/app/layout.tsx
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
});
```

### 9.2 Application Metrics

**Custom metrics to track:**

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| **API response time (p95)** | 95th percentile latency | >3 seconds |
| **Error rate** | 5XX errors / total requests | >5% |
| **Database connection pool usage** | Active connections / pool size | >80% |
| **Memory usage** | RAM consumption | >85% |
| **Failed login attempts** | Potential brute force | >100/minute |

### 9.3 Logging Strategy

**Log levels:**

| Level | Use Case | Example |
|-------|----------|---------|
| **DEBUG** | Development only | SQL queries, detailed traces |
| **INFO** | Normal operations | User login, file uploaded |
| **WARNING** | Recoverable errors | Slow query, deprecated API |
| **ERROR** | Application errors | Uncaught exceptions, API failures |
| **CRITICAL** | System failures | Database offline, Zero-Storage violation |

**Centralized logging (future):**
- Datadog Logs
- Logtail
- CloudWatch Logs

---

## 10. Backup and Recovery

### 10.1 Database Backup Strategy

**Automated backups (Render/DigitalOcean managed):**
- **Frequency:** Daily at 2:00 AM UTC
- **Retention:** 7 days (free tier), 30 days (paid tier)
- **Type:** Full database dump

**Manual backup:**

```bash
# Export database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup_20260204.sql
```

### 10.2 Zero-Storage Advantage

**What needs backup:**
- ✅ User accounts (credentials)
- ✅ Client metadata
- ✅ Activity logs (aggregate summaries)
- ❌ **Trial balance data (never stored, no backup needed)**

**Recovery time:** \u003c15 minutes (small database size)

---

## 11. Scaling Strategies

### 11.1 Horizontal Scaling (Backend)

**Stateless backend** enables easy horizontal scaling:

```
Before:                    After (scaled 1 → 3):
┌──────────────┐          ┌──────────────┐
│ Instance 1   │          │ Load Balancer│
│ 100 req/s    │          └───────┬──────┘
└──────────────┘                  │
                          ┌───────┴────────────┐
                          │                    │
                    ┌─────▼──────┐      ┌─────▼──────┐      ┌────────────┐
                    │Instance 1  │      │Instance 2  │      │Instance 3  │
                    │ 33 req/s   │      │ 33 req/s   │      │ 33 req/s   │
                    └────────────┘      └────────────┘      └────────────┘
```

**When to scale:**
- CPU >70% for >5 minutes
- API response time (p95) >2 seconds
- Queue depth >100 requests

### 11.2 Database Scaling

**Vertical scaling (current):**
- Increase instance size (RAM, CPU)
- Render: Free → Starter ($7) → Standard ($50)

**Horizontal scaling (future):**
- Read replicas for analytical queries
- Connection pooling (PgBouncer)

### 11.3 Frontend Scaling

**Vercel automatic scaling:**
- Global CDN (automatic)
- Serverless functions auto-scale
- No manual configuration needed

---

## 12. Security Hardening

### 12.1 Production Security Checklist

**Backend:**
- [ ] `ENV_MODE=production` (disables debug endpoints)
- [ ] `DEBUG=false` (no stack traces in responses)
- [ ] CORS origins set to production domains only
- [ ] JWT secret rotated (not using dev key)
- [ ] Database password is strong (32+ characters)
- [ ] TLS 1.3 enforced (default on Render/Vercel)
- [ ] `user` in Docker container is non-root

**Frontend:**
- [ ] Environment variables use `NEXT_PUBLIC_` prefix
- [ ] No API keys or secrets in client-side code
- [ ] CSP headers configured (Content Security Policy)
- [ ] HSTS header enabled (Strict-Transport-Security)

---

## 13. Runbook: Common Operations

### 13.1 Deploy New Version

**Automatic (recommended):**

```bash
# 1. Merge PR to main branch
git checkout main
git merge feature/sprint-XX

# 2. Push to GitHub
git push origin main

# 3. Vercel and Render auto-deploy (2-5 minutes)
```

**Manual (emergency):**

```bash
# Vercel
vercel --prod

# Render (via dashboard)
# Dashboard → Manual Deploy → Deploy latest commit
```

### 13.2 Rollback Deployment

**Vercel:**
1. Dashboard → Deployments
2. Find previous working deployment
3. Click "..." → "Promote to Production"

**Render:**
1. Dashboard → Events
2. Find previous deployment
3. Click "Rollback"

### 13.3 Restart Backend

**Render:**
1. Dashboard → Manual Deploy → "Clear build cache & deploy"
2. Or: Settings → "Suspend" then "Resume"

**DigitalOcean:**
1. App → Components → API → "Force Rebuild and Deploy"

### 13.4 View Logs

**Backend logs (Render):**

```bash
# Via CLI
render logs --service paciolus-api --tail

# Via dashboard
Dashboard → Logs (real-time stream)
```

**Frontend logs (Vercel):**

```bash
# Via CLI
vercel logs paciolus.vercel.app

# Via dashboard
Dashboard → Runtime Logs
```

### 13.5 Database Maintenance

**Vacuum (optimize storage):**

```bash
psql $DATABASE_URL -c "VACUUM ANALYZE;"
```

**Check database size:**

```bash
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('paciolus'));"
```

---

## 14. Disaster Recovery

### 14.1 Failure Scenarios

| Scenario | Impact | Recovery Time | Recovery Procedure |
|----------|--------|---------------|-------------------|
| **Vercel outage** | Frontend down | 0s (auto-failover to edge) | Wait for Vercel recovery |
| **Backend instance crash** | API unavailable | 30s | Auto-restart via health check |
| **Database crash** | All services degraded | 2-5 min | Managed service auto-recovery |
| **Complete data loss** | User accounts lost | 15 min | Restore from latest backup |
| **Zero-Storage violation** | **CRITICAL** | 1 hour | Delete data, external audit |

### 14.2 Recovery Procedures

**Database restore:**

```bash
# 1. Download latest backup from Render/DO dashboard
# 2. Restore to database
psql $DATABASE_URL < backup_latest.sql

# 3. Verify restoration
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
```

**Complete infrastructure rebuild:**

```bash
# 1. Re-deploy backend (Render/DO dashboard)
# 2. Re-deploy frontend (Vercel dashboard)
# 3. Restore database from backup
# 4. Update DNS if needed (5-60 min propagation)
# 5. Verify all services: https://paciolus.com/health
```

---

## 15. Cost Optimization

### 15.1 Current Monthly Costs (Estimated)

| Service | Tier | Cost |
|---------|------|------|
| **Vercel** | Pro | $20/month (team) |
| **Render** | Starter (backend) | $7/month |
| **Render** | Starter (database) | $7/month |
| **Domain** | .com TLD | $12/year (~$1/month) |
| **Sentry** | Developer | Free (up to 5K errors/month) |
| **Total** | | **~$35/month** |

### 15.2 Cost Scaling

**At 1,000 users:**
- Backend: Render Standard ($50/month) for more CPU
- Database: Render Standard ($50/month) for larger storage
- **Total:** ~$120/month

**At 10,000 users:**
- Backend: 2-3 instances (Render Pro, ~$200/month)
- Database: PostgreSQL Pro ($200/month)
- Monitoring: Sentry Team ($29/month)
- **Total:** ~$430/month

---

## 16. Post-Deployment Checklist

### 16.1 Functional Verification

- [ ] Frontend loads: `https://paciolus.com`
- [ ] User can register: `https://paciolus.com/register`
- [ ] User can log in: `https://paciolus.com/login`
- [ ] Trial balance upload works
- [ ] PDF export generates
- [ ] Excel export generates
- [ ] Activity history displays
- [ ] Client management works (create, edit, delete)

### 16.2 Security Verification

- [ ] HTTPS enforced (no HTTP access)
- [ ] JWT token required for protected endpoints
- [ ] CORS policy restricts origins
- [ ] Password requirements enforced
- [ ] No sensitive data in logs
- [ ] Zero-Storage compliance verified (no files on disk)

### 16.3 Performance Verification

- [ ] Home page loads in \u003c2 seconds
- [ ] API health check responds in \u003c200ms: `GET /health`
- [ ] Trial balance analysis completes in \u003c5 seconds (10K rows)
- [ ] No memory leaks (monitor for 24 hours)

---

## 17. Troubleshooting

### 17.1 Common Issues

**Issue: CORS errors in browser**

```
Access to fetch at 'https://api.paciolus.com/audit/trial-balance' from origin
'https://paciolus.com' has been blocked by CORS policy
```

**Solution:**
1. Check `CORS_ORIGINS` in backend `.env`
2. Ensure it includes `https://paciolus.com` (no trailing slash)
3. Restart backend service

---

**Issue: JWT token invalid**

```
401 Unauthorized: Could not validate credentials
```

**Solution:**
1. Check JWT_SECRET_KEY is the same across all backend instances
2. Verify token hasn't expired (8-hour lifetime)
3. Clear browser sessionStorage and re-login

---

**Issue: Database connection failed**

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
1. Verify `DATABASE_URL` is correct
2. Check database is running (Render/DO dashboard)
3. Verify network allows connection (firewall rules)
4. Check connection pool isn't exhausted

---

**Appendix A: Environment Variable Reference**

See Section 3 for complete list.

---

**Appendix B: Docker Commands**

```bash
# Build
docker build -t paciolus-backend backend/
docker build -t paciolus-frontend frontend/

# Run
docker run -p 8000:8000 --env-file backend/.env paciolus-backend
docker run -p 3000:3000 --env-file frontend/.env.local paciolus-frontend

# Debug
docker exec -it <container-id> /bin/bash
docker logs <container-id>

# Clean up
docker system prune -a  # Remove unused images
```

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | CTO | Initial publication, migrated from DEPLOYMENT.md |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
