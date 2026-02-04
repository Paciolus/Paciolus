# Paciolus Deployment Guide

> Sprint 24: Production Deployment Prep
> Version: 0.16.0

This guide covers deploying Paciolus to production environments. The recommended architecture separates the frontend (Vercel) from the backend (Render/DigitalOcean).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Variables](#environment-variables)
4. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
5. [Backend Deployment (Render)](#backend-deployment-render)
6. [Backend Deployment (DigitalOcean)](#backend-deployment-digitalocean)
7. [Docker Deployment](#docker-deployment)
8. [Database Setup](#database-setup)
9. [Post-Deployment Checklist](#post-deployment-checklist)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────┐     HTTPS      ┌─────────────────┐
│                 │ ◄────────────► │                 │
│  Vercel CDN     │                │  Backend API    │
│  (Frontend)     │                │  (Render/DO)    │
│                 │                │                 │
│  Next.js SSG    │                │  FastAPI +      │
│  Static Assets  │                │  Gunicorn       │
│                 │                │                 │
└─────────────────┘                └────────┬────────┘
                                            │
                                            │ SQLAlchemy
                                            ▼
                                   ┌─────────────────┐
                                   │                 │
                                   │  PostgreSQL     │
                                   │  (Metadata DB)  │
                                   │                 │
                                   │  Zero-Storage:  │
                                   │  User accounts, │
                                   │  client info,   │
                                   │  activity logs  │
                                   │                 │
                                   └─────────────────┘
```

### Zero-Storage Architecture

**Critical**: Paciolus operates under a Zero-Storage security model:

- ✅ **Stored**: User accounts, client metadata, activity logs, practice settings
- ❌ **Never Stored**: Trial balance data, financial figures, uploaded files

All financial data is processed in-memory and immediately discarded after analysis.

---

## Prerequisites

- Git repository with Paciolus codebase
- Vercel account (free tier works)
- Render or DigitalOcean account
- Domain name (optional but recommended)

### Required Tools (Local Development)

```bash
# Node.js 20+
node --version

# Python 3.11+
python --version

# Docker (optional)
docker --version
```

---

## Environment Variables

### Backend Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `API_HOST` | Yes | Host binding | `0.0.0.0` |
| `API_PORT` | Yes | Port number | `8000` |
| `CORS_ORIGINS` | Yes | Allowed origins (comma-separated) | `https://paciolus.vercel.app` |
| `ENV_MODE` | Yes | Environment mode | `production` |
| `JWT_SECRET_KEY` | Yes (prod) | 32+ char secret | `<generated>` |
| `DATABASE_URL` | Yes | Database connection string | `postgresql://...` |
| `DEBUG` | No | Enable debug mode | `false` |

### Frontend Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API URL | `https://api.paciolus.com` |

### Generate JWT Secret

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Frontend Deployment (Vercel)

Vercel provides the best experience for Next.js deployments.

### Step 1: Connect Repository

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New..." → "Project"
3. Import your Git repository
4. Select the `frontend` directory as the root

### Step 2: Configure Build Settings

```
Framework Preset: Next.js
Root Directory: frontend
Build Command: npm run build
Output Directory: .next
Install Command: npm ci
```

### Step 3: Set Environment Variables

In Vercel dashboard → Project Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL = https://your-backend-url.onrender.com
```

### Step 4: Deploy

Click "Deploy" and wait for the build to complete.

### Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your domain (e.g., `app.paciolus.com`)
3. Configure DNS records as instructed
4. Update backend `CORS_ORIGINS` to include the new domain

---

## Backend Deployment (Render)

Render provides simple Python hosting with managed PostgreSQL.

### Step 1: Create Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click "New" → "Web Service"
3. Connect your repository
4. Configure:

```
Name: paciolus-api
Region: Oregon (US West)
Branch: main
Root Directory: backend
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn main:app --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120
```

### Step 2: Create PostgreSQL Database

1. Click "New" → "PostgreSQL"
2. Configure:

```
Name: paciolus-db
Region: Oregon (same as web service)
Plan: Free (or Starter for production)
```

3. Copy the "Internal Database URL" for the next step

### Step 3: Set Environment Variables

In Render dashboard → Web Service → Environment:

```
API_HOST=0.0.0.0
API_PORT=10000
ENV_MODE=production
CORS_ORIGINS=https://your-frontend.vercel.app
JWT_SECRET_KEY=<your-generated-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=480
DATABASE_URL=<internal-database-url-from-step-2>
```

### Step 4: Deploy

Render will automatically deploy on push to main branch.

### Health Check

Configure health check in Render dashboard:

```
Health Check Path: /health
```

---

## Backend Deployment (DigitalOcean)

DigitalOcean App Platform provides more control and scalability.

### Step 1: Create App

1. Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)
2. Click "Apps" → "Create App"
3. Connect your repository

### Step 2: Configure Components

**API Component:**
```
Type: Web Service
Source Directory: /backend
Build Command: pip install -r requirements.txt
Run Command: gunicorn main:app --bind 0.0.0.0:8080 --workers 4 --worker-class uvicorn.workers.UvicornWorker
HTTP Port: 8080
Instance Size: Basic ($5/mo) or larger
```

**Database Component:**
```
Type: Database
Engine: PostgreSQL
Version: 15
Size: Development ($7/mo) or larger
```

### Step 3: Set Environment Variables

```
API_HOST=0.0.0.0
API_PORT=8080
ENV_MODE=production
CORS_ORIGINS=https://your-frontend.vercel.app
JWT_SECRET_KEY=<your-generated-secret>
DATABASE_URL=${db.DATABASE_URL}
```

### Step 4: Deploy

Click "Create Resources" to deploy.

---

## Docker Deployment

For self-hosted or custom cloud deployments.

### Local Testing

```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit .env files with your configuration
# Then build and run:
docker-compose up --build
```

### Production with Docker Compose

1. Create `.env` in project root:

```bash
# Production environment
ENV_MODE=production
DEBUG=false

# Backend
API_PORT=8000
CORS_ORIGINS=https://your-domain.com
JWT_SECRET_KEY=<your-generated-secret>
DATABASE_URL=postgresql://user:pass@db:5432/paciolus

# Frontend
NEXT_PUBLIC_API_URL=https://api.your-domain.com
FRONTEND_PORT=3000
```

2. Build and run:

```bash
docker-compose -f docker-compose.yml up -d --build
```

### Using Docker Images Directly

**Backend:**
```bash
docker build -t paciolus-backend ./backend
docker run -d \
  -p 8000:8000 \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -e ENV_MODE=production \
  -e CORS_ORIGINS=https://your-frontend.com \
  -e JWT_SECRET_KEY=<secret> \
  -e DATABASE_URL=postgresql://... \
  paciolus-backend
```

**Frontend:**
```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.your-domain.com \
  -t paciolus-frontend ./frontend

docker run -d -p 3000:3000 paciolus-frontend
```

---

## Database Setup

### Initial Schema Creation

The backend automatically creates tables on first run using SQLAlchemy.

### PostgreSQL Configuration

Recommended settings for production:

```sql
-- Connection pooling (if not using managed database)
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';

-- Performance
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
```

### Backup Strategy

Since Paciolus uses Zero-Storage, database backups only need to cover:
- User accounts
- Client metadata
- Activity logs
- Practice settings

**No financial data is ever stored**, so backup requirements are minimal.

```bash
# Daily backup example (PostgreSQL)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

---

## Post-Deployment Checklist

### Security Verification

- [ ] `ENV_MODE` is set to `production`
- [ ] `DEBUG` is set to `false`
- [ ] `JWT_SECRET_KEY` is 32+ characters and unique
- [ ] `CORS_ORIGINS` contains only your domains (no wildcards)
- [ ] HTTPS is enforced on both frontend and backend
- [ ] Database credentials are not exposed in logs

### Functional Verification

- [ ] Frontend loads without errors
- [ ] User registration works
- [ ] User login works
- [ ] File upload and analysis works
- [ ] PDF export works
- [ ] Excel export works
- [ ] Activity history displays

### Performance Verification

- [ ] Backend health check responds: `GET /health`
- [ ] API response times are acceptable (<2s for analysis)
- [ ] No memory leaks during file processing

### Zero-Storage Verification

- [ ] Verify no uploaded files persist on server
- [ ] Verify database contains only metadata
- [ ] Verify logs don't contain financial data

---

## Troubleshooting

### CORS Errors

**Symptom:** Browser console shows CORS policy errors

**Solution:**
1. Check `CORS_ORIGINS` includes your frontend URL
2. Include both `https://` and `www.` variants if needed
3. No trailing slashes in origins
4. Restart backend after changing CORS settings

### Database Connection Failed

**Symptom:** Application fails to start with database errors

**Solution:**
1. Verify `DATABASE_URL` format is correct
2. Check database is running and accessible
3. Verify network/firewall allows connection
4. For Render/DO, use internal URLs for same-region resources

### JWT Token Invalid

**Symptom:** Users logged out unexpectedly, 401 errors

**Solution:**
1. Verify `JWT_SECRET_KEY` is the same across all backend instances
2. Check `JWT_EXPIRATION_MINUTES` is reasonable
3. Ensure server clocks are synchronized

### Build Failures

**Frontend (Vercel):**
```bash
# Clear cache and rebuild
vercel --prod --force
```

**Backend (Render):**
```bash
# Check build logs for missing dependencies
# Ensure requirements.txt is complete
```

### Memory Issues

**Symptom:** Backend crashes during large file processing

**Solution:**
1. Increase worker timeout: `--timeout 120`
2. Reduce concurrent workers if memory-constrained
3. Large files (50K+ rows) use streaming - verify chunked processing is active

---

## Support

For issues specific to Paciolus, check:
- GitHub Issues: [repository issues page]
- Documentation: This file and `CLAUDE.md`

For platform-specific issues:
- Vercel: [vercel.com/docs](https://vercel.com/docs)
- Render: [render.com/docs](https://render.com/docs)
- DigitalOcean: [docs.digitalocean.com](https://docs.digitalocean.com)

---

*Paciolus v0.16.0 — Zero-Storage Trial Balance Diagnostic Intelligence*
