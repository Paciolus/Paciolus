# System Architecture

**Document Classification:** Internal (Technical Teams)  
**Version:** 1.0  
**Last Updated:** February 4, 2026  
**Owner:** Chief Technology Officer  
**Review Cycle:** Quarterly

---

## Executive Summary

Paciolus is a modern, cloud-native trial balance diagnostic platform built on a **Zero-Storage architecture**. This document provides a comprehensive technical overview of the system design, technology stack, and architectural patterns.

**Key Architectural Decisions:**
- ✅ **Zero-Storage Backend** — Financial data processed in-memory, never persisted
- ✅ **Serverless Frontend** — Next.js on Vercel CDN for global performance
- ✅ **Stateless API** — FastAPI with JWT authentication, horizontally scalable
- ✅ **Multi-Tenant Database** — PostgreSQL with row-level user isolation
- ✅ **Streaming Processing** — Handles large files (50K+ rows) via chunked processing

**Target Audience:** Engineering teams, technical leadership, DevOps, security auditors

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Data Architecture](#5-data-architecture)
6. [Security Architecture](#6-security-architecture)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Scalability and Performance](#8-scalability-and-performance)
9. [Development Workflow](#9-development-workflow)
10. [Future Architecture](#10-future-architecture)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ Next.js Frontend (React 18, TypeScript)                  │ │
│  │ - Static pages (marketing, login, register)              │ │
│  │ - Client-side state (React Context, hooks)               │ │
│  │ - Session storage (JWT token, ephemeral)                 │ │
│  └───────────────────────┬──────────────────────────────────┘ │
└────────────────────────────┼─────────────────────────────────┘
                             │ HTTPS (TLS 1.3)
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────────┐                    ┌──────────────────┐
│  Vercel CDN       │                    │  FastAPI Backend │
│  (Global Edge)    │                    │  (Python 3.11)   │
│                   │                    │                  │
│  - Static assets  │                    │  - REST API      │
│  - Next.js SSG    │                    │  - JWT auth      │
│  - DDoS protection│                    │  - Trial balance │
│                   │                    │    processing    │
└───────────────────┘                    └────────┬─────────┘
                                                  │
                                    ┌─────────────┴──────────────┐
                                    │                            │
                                    ▼                            ▼
                            ┌──────────────┐          ┌─────────────────┐
                            │ PostgreSQL   │          │ In-Memory       │
                            │ (Metadata)   │          │ Processing      │
                            │              │          │                 │
                            │ - Users      │          │ - BytesIO       │
                            │ - Clients    │          │ - pandas        │
                            │ - Activity   │          │ - NumPy         │
                            │   logs       │          │ - Audit engine  │
                            └──────────────┘          └─────────────────┘
```

**Key Characteristics:**
- **3-tier architecture**: Frontend (Next.js) → API (FastAPI) → Database (PostgreSQL)
- **Stateless backend**: No session storage on server (JWT-based auth)
- **Zero-Storage processing**: Financial data exists only in ephemeral memory

### 1.2 Design Principles

| Principle | Implementation | Benefit |
|-----------|---------------|---------|
| **Zero-Storage** | Financial data in BytesIO buffers, never disk | Security, privacy, compliance |
| **Stateless** | JWT authentication, no server sessions | Horizontal scalability |
| **API-First** | Backend as REST API, frontend as consumer | Flexibility, future mobile apps |
| **Multi-Tenant** | User-level data isolation (PostgreSQL RLS equivalent) | Security, SaaS-ready |
| **Immutable Infrastructure** | Docker containers, no manual server config | Reliability, reproducibility |

---

## 2. Technology Stack

### 2.1 Frontend Stack

| Technology | Version | Purpose | License |
|------------|---------|---------|---------|
| **Next.js** | 16.1.6 (Turbopack) | React framework, SSG/SSR | MIT |
| **React** | 18.x | UI library | MIT |
| **TypeScript** | 5.x | Type safety | Apache 2.0 |
| **Tailwind CSS** | 3.x | Utility-first CSS | MIT |
| **framer-motion** | 11.x | Animations | MIT |
| **Lucide React** | (icons) | Icon library | ISC |

**Build tools:**
- **Turbopack** (Next.js 16) for fast builds
- **ESLint** for linting
- **Prettier** for code formatting

### 2.2 Backend Stack

| Technology | Version | Purpose | License |
|------------|---------|---------|---------|
| **FastAPI** | 0.104+ | Web framework | MIT |
| **Python** | 3.11 | Language | PSF |
| **pandas** | 2.x | Data processing | BSD |
| **NumPy** | 1.x | Numerical computing | BSD |
| **SQLAlchemy** | 2.x | ORM | MIT |
| **python-jose** | 3.x | JWT handling | MIT |
| **passlib** | 1.7+ | Password hashing (bcrypt) | BSD |
| **Gunicorn** | 21.x | WSGI server | MIT |
| **Uvicorn** | 0.27+ | ASGI server | BSD |
| **ReportLab** | 4.x | PDF generation | BSD |
| **openpyxl** | 3.x | Excel generation | MIT |

**Development tools:**
- **pytest** for testing
- **Black** for code formatting
- **mypy** for type checking

### 2.3 Infrastructure Stack

| Component | Provider | Purpose |
|-----------|----------|---------|
| **Frontend Hosting** | Vercel | Next.js deployment, CDN |
| **Backend Hosting** | Render / DigitalOcean | FastAPI deployment |
| **Database** | PostgreSQL (managed) | Metadata storage |
| **DNS** | Vercel / Cloudflare | Domain management |
| **Monitoring** | Sentry | Error tracking |
| **Analytics** | (TBD) | Usage analytics |

---

## 3. Frontend Architecture

### 3.1 Next.js Application Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router (pages)
│   │   ├── page.tsx            # Home (guest/workspace conditional)
│   │   ├── login/page.tsx      # Login page
│   │   ├── register/page.tsx   # Registration
│   │   ├── portfolio/page.tsx  # Client portfolio
│   │   ├── history/page.tsx    # Activity history
│   │   ├── settings/page.tsx   # User settings
│   │   └── layout.tsx          # Root layout (global providers)
│   │
│   ├── components/             # React components
│   │   ├── auth/               # Authentication (ProfileDropdown, etc.)
│   │   ├── workspace/          # Workspace (WorkspaceHeader, etc.)
│   │   ├── marketing/          # Marketing (FeaturePillars, etc.)
│   │   ├── risk/               # Risk dashboard (AnomalyCard, etc.)
│   │   ├── mapping/            # Column mapping modal
│   │   ├── workbook/           # Workbook inspector
│   │   └── ...
│   │
│   ├── context/                # React Context providers
│   │   ├── AuthContext.tsx     # Authentication state
│   │   └── MappingContext.tsx  # Column mapping state
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useClients.ts       # Client management API
│   │   ├── useSettings.ts      # User settings API
│   │   └── ...
│   │
│   ├── types/                  # TypeScript type definitions
│   │   ├── auth.ts
│   │   ├── client.ts
│   │   ├── audit.ts
│   │   └── ...
│   │
│   └── lib/                    # Utility functions
│       └── api.ts              # API client utilities
│
├── public/                     # Static assets
│   ├── PaciolusLogo_DarkBG.png
│   └── ...
│
└── package.json
```

### 3.2 State Management

**React Context API** for global state:

```typescript
// AuthContext: User authentication state
const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: () => {},
  token: null,
});

// MappingContext: Column mapping preferences (session storage)
const MappingContext = createContext<MappingContextType>({
  savedMappings: {},
  saveMappingSet: () => {},
  clearMappingSet: () => {},
});
```

**Component-level state** (useState, useReducer) for local UI state.

**No global state management library** (Redux, Zustand) — unnecessary overhead for this application size.

### 3.3 Routing

**Next.js App Router** (file-based routing):

| Route | Component | Auth Required | Description |
|-------|-----------|---------------|-------------|
| `/` | `page.tsx` | No | Home (conditional guest/workspace) |
| `/login` | `login/page.tsx` | No | Login page |
| `/register` | `register/page.tsx` | No | Registration |
| `/portfolio` | `portfolio/page.tsx` | Yes | Client management |
| `/history` | `history/page.tsx` | Yes | Activity history |
| `/settings` | `settings/page.tsx` | Yes | User preferences |
| `/flux` | `flux/page.tsx` | Yes | Flux analysis (ratio engine) |
| `/recon` | `recon/page.tsx` | Yes | Reconciliation engine |

**Protected routes** use `AuthContext` to redirect unauthenticated users to `/login`.

### 3.4 API Integration

**Centralized API client:**

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = sessionStorage.getItem('token');
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  
  return response.json();
}
```

**Custom hooks** abstract API calls:

```typescript
// hooks/useClients.ts
export function useClients() {
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    apiRequest<Client[]>('/clients')
      .then(setClients)
      .finally(() => setIsLoading(false));
  }, []);
  
  return { clients, isLoading };
}
```

---

## 4. Backend Architecture

### 4.1 FastAPI Application Structure

```
backend/
├── main.py                   # FastAPI app, route definitions
├── config.py                 # Environment configuration
├── database.py               # SQLAlchemy engine, session
├── models.py                 # SQLAlchemy models (User, Client, etc.)
├── auth.py                   # JWT authentication, password hashing
├── audit_engine.py           # Trial balance processing (core logic)
├── classification_rules.py   # Account classification heuristics
├── ratio_engine.py           # Financial ratio calculations
├── flux_engine.py            # Flux analysis
├── recon_engine.py           # Reconciliation engine
├── pdf_generator.py          # PDF report generation (ReportLab)
├── excel_generator.py        # Excel workpaper generation (openpyxl)
├── leadsheet_generator.py    # Leadsheet generation
├── workbook_inspector.py     # Multi-sheet Excel inspection
├── client_manager.py         # Client CRUD operations
├── practice_settings.py      # Practice settings & materiality formulas
├── security_utils.py         # File processing utilities
├── secrets_manager.py        # Production credential management
│
├── tests/                    # pytest test suite
│   ├── test_audit_engine.py
│   ├── test_auth.py
│   └── ...
│
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container definition
└── .env.example              # Environment variable template
```

### 4.2 API Design

**RESTful API** with clear resource hierarchy:

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/auth/register` | POST | No | User registration |
| `/auth/login` | POST | No | User login (returns JWT) |
| `/auth/me` | GET | Yes | Get current user info |
| `/audit/trial-balance` | POST | Yes | Upload & analyze trial balance |
| `/audit/inspect-workbook` | POST | Yes | Inspect Excel workbook sheets |
| `/export/pdf` | POST | Yes | Generate PDF report |
| `/export/excel` | POST | Yes | Generate Excel workpaper |
| `/clients` | GET | Yes | List user's clients |
| `/clients` | POST | Yes | Create client |
| `/clients/{id}` | GET | Yes | Get client details |
| `/clients/{id}` | PUT | Yes | Update client |
| `/clients/{id}` | DELETE | Yes | Delete client |
| `/activity/log` | POST | Yes | Log activity (metadata) |
| `/activity/history` | GET | Yes | Get activity history |
| `/activity/clear` | DELETE | Yes | Delete all activity logs |
| `/dashboard/stats` | GET | Yes | Get dashboard statistics |
| `/settings` | GET | Yes | Get user settings |
| `/settings` | PUT | Yes | Update user settings |

**OpenAPI documentation** auto-generated at `/docs` (Swagger UI).

### 4.3 Zero-Storage Processing

**Core principle:** Financial data processed in-memory, never written to disk.

```python
# audit_engine.py
async def audit_trial_balance(file: UploadFile):
    """
    Process trial balance in-memory without disk persistence.
    """
    # 1. Read file into BytesIO buffer (memory, not disk)
    contents = await file.read()
    buffer = io.BytesIO(contents)
    
    # 2. Load into pandas DataFrame (memory)
    df = pd.read_csv(buffer)
    
    # 3. Process data
    results = classify_and_analyze(df)
    
    # 4. Explicit cleanup
    del df
    del buffer
    gc.collect()  # Force garbage collection
    
    # 5. Return summary only (no raw data)
    return {
        "balanced": results.is_balanced,
        "total_debits": results.total_debits,
        "total_credits": results.total_credits,
        "anomaly_count": len(results.anomalies),
        # NO: "anomalies": results.anomalies (would leak data)
    }
```

**Streaming for large files:**

```python
# For files >50K rows
for chunk in pd.read_csv(buffer, chunksize=10000):
    process_chunk(chunk)
    del chunk
    gc.collect()  # Clear each chunk after processing
```

### 4.4 Authentication Flow

**JWT-based authentication:**

```
1. User sends credentials to /auth/login
   POST /auth/login
   { "email": "user@example.com", "password": "..." }

2. Backend validates credentials
   - Query User table
   - Verify bcrypt hash: passlib.verify(password, user.password_hash)

3. Generate JWT token
   token = jose.jwt.encode({
     "sub": user.id,
     "email": user.email,
     "exp": datetime.utcnow() + timedelta(hours=8)
   }, secret_key, algorithm="HS256")

4. Return token to client
   { "access_token": "eyJ...", "token_type": "bearer", ... }

5. Client stores in sessionStorage (ephemeral)
   sessionStorage.setItem('token', access_token)

6. Client includes token in subsequent requests
   Authorization: Bearer eyJ...

7. Backend validates token on every request
   - Decode JWT
   - Verify signature
   - Check expiration
   - Extract user_id
```

---

## 5. Data Architecture

### 5.1 Database Schema

**PostgreSQL database** with 4 core tables:

```sql
-- Users table (authentication)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    settings JSONB DEFAULT '{}'
);

-- Clients table (metadata only, multi-tenant)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    fiscal_year_end VARCHAR(5),  -- MM-DD format
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'
);

-- Activity logs (aggregate summaries, GDPR-compliant)
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename_hash VARCHAR(64) NOT NULL,  -- SHA-256
    filename_display VARCHAR(20),  -- First 12 chars only
    timestamp TIMESTAMP DEFAULT NOW(),
    record_count INTEGER,
    total_debits NUMERIC(15, 2),  -- Summary only
    total_credits NUMERIC(15, 2),  -- Summary only
    materiality_threshold NUMERIC(15, 2),
    was_balanced BOOLEAN,
    anomaly_count INTEGER,  -- Count only, no details
    material_count INTEGER,
    immaterial_count INTEGER,
    is_consolidated BOOLEAN DEFAULT FALSE,
    sheet_count INTEGER
);

-- Diagnostic summaries (ratio engine, aggregate category totals)
CREATE TABLE diagnostic_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    -- Category totals (aggregate only, no account details)
    total_assets NUMERIC(15, 2),
    total_liabilities NUMERIC(15, 2),
    total_equity NUMERIC(15, 2),
    total_revenue NUMERIC(15, 2),
    total_expenses NUMERIC(15, 2),
    -- Financial ratios (calculated from category totals)
    current_ratio NUMERIC(10, 4),
    quick_ratio NUMERIC(10, 4),
    debt_to_equity NUMERIC(10, 4),
    gross_margin NUMERIC(10, 4),
    row_count INTEGER
);
```

**Indexes for performance:**

```sql
CREATE INDEX idx_clients_user_id ON clients(user_id);
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_timestamp ON activity_logs(timestamp DESC);
CREATE INDEX idx_diagnostic_summaries_user_id ON diagnostic_summaries(user_id);
```

### 5.2 Data Flow: Trial Balance Upload

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: User uploads CSV/Excel                              │
│ Frontend: <input type="file" accept=".csv,.xlsx" />         │
└──────────────────────┬──────────────────────────────────────┘
                       │ POST /audit/trial-balance
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: FastAPI receives file as UploadFile                 │
│ Type: multipart/form-data                                   │
│ Storage: BytesIO buffer (memory, NOT disk)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: pandas reads file into DataFrame                    │
│ df = pd.read_csv(buffer)                                    │
│ Memory footprint: ~10MB for 10K rows                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Audit engine processes data                         │
│ - Classify accounts (heuristics)                            │
│ - Detect anomalies (debit/credit violations)                │
│ - Calculate materiality (user threshold)                    │
│ - Generate summary statistics                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Database writes (METADATA ONLY)                     │
│ INSERT INTO activity_logs (aggregate statistics)            │
│ - NO account names, NO balances, NO transaction details     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 6: Return JSON summary to client                       │
│ { "balanced": true, "anomaly_count": 3, ... }               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 7: Memory cleanup (backend)                            │
│ del df; del buffer; gc.collect()                            │
│ Trial balance data is DESTROYED                             │
└─────────────────────────────────────────────────────────────┘
```

**Total time:** 3-5 seconds (typical)  
**Financial data persistence:** 0 seconds (Zero-Storage)

---

## 6. Security Architecture

**See SECURITY_POLICY.md for comprehensive details.**

### 6.1 Summary of Security Controls

| Layer | Control | Implementation |
|-------|---------|----------------|
| **Transport** | TLS 1.3 encryption | All HTTPS connections |
| **Authentication** | JWT tokens (HS256) | 8-hour expiration |
| **Authorization** | Multi-tenant isolation | User-level database filtering |
| **Password** | bcrypt hashing | Work factor 12, auto-salted |
| **Input Validation** | Server-side validation | All user inputs sanitized |
| **SQL Injection** | ORM parameterization | SQLAlchemy (no raw SQL) |
| **XSS** | React auto-escaping | No dangerouslySetInnerHTML |
| **CSRF** | CORS policy | Restricted origins |
| **Data** | Zero-Storage | Financial data never persisted |

### 6.2 Threat Model

**Primary threats:**
- **Data breach** (financial data exposure)  
  **Mitigation:** Zero-Storage architecture — data doesn't exist to breach
  
- **Credential theft** (user account compromise)  
  **Mitigation:** bcrypt hashing, JWT short expiration, HTTPS only
  
- **Man-in-the-middle** (interception)  
  **Mitigation:** TLS 1.3, HSTS headers

- **Denial of service** (service disruption)  
  **Mitigation:** Vercel DDoS protection, rate limiting (planned)

**Out of scope:**
- Client-side attacks (user's browser, outside our control)
- Physical access to user's devices
- Social engineering (phishing user credentials)

---

## 7. Deployment Architecture

**See DEPLOYMENT_ARCHITECTURE.md for full details.**

### 7.1 Production Environment

```
┌──────────────────────────────────────────────────────────────┐
│ Vercel CDN (Global Edge Network)                             │
│ - Next.js frontend (static + serverless functions)           │
│ - Automatic HTTPS (Let's Encrypt)                            │
│ - DDoS protection                                            │
│ - 99.99% uptime SLA                                          │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ Render / DigitalOcean App Platform                           │
│ - FastAPI backend (Docker container)                         │
│ - Gunicorn + Uvicorn (ASGI)                                  │
│ - Auto-scaling (1-10 instances)                              │
│ - Health checks: GET /health                                 │
└────────────────────────┬─────────────────────────────────────┘
                         │ Internal network
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ PostgreSQL (Managed Database)                                │
│ - Render/DigitalOcean managed instance                       │
│ - Automatic backups (daily)                                  │
│ - Encryption at rest                                         │
│ - Connection pooling                                         │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 Development Environment

**Local development:**

```bash
# Frontend (Next.js dev server)
cd frontend
npm run dev  # http://localhost:3000

# Backend (FastAPI with auto-reload)
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Environment variables:**

```bash
# Backend (.env)
ENV_MODE=development
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
JWT_SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///./paciolus.db  # SQLite for dev

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 8. Scalability and Performance

### 8.1 Frontend Performance

| Metric | Target | Current | Optimization |
|--------|--------|---------|--------------|
| **First Contentful Paint** | \u003c1.5s | ~1.2s | Vercel edge caching |
| **Largest Contentful Paint** | \u003c2.5s | ~2.0s | Image optimization |
| **Time to Interactive** | \u003c3.5s | ~2.8s | Code splitting |
| **Bundle Size** | \u003c500KB | ~420KB | Tree shaking |

**Optimizations:**
- Next.js static generation (SSG) for marketing pages
- Client-side rendering (CSR) for authenticated pages
- Image optimization (next/image)
- Font optimization (next/font)
- Lazy loading (React.lazy)

### 8.2 Backend Performance

| Endpoint | Latency (p50) | Latency (p95) | Target |
|----------|---------------|---------------|--------|
| `/auth/login` | 150ms | 300ms | \u003c500ms |
| `/audit/trial-balance` (1K rows) | 800ms | 1.5s | \u003c2s |
| `/audit/trial-balance` (10K rows) | 2.2s | 4s | \u003c5s |
| `/audit/trial-balance` (50K rows) | 8s | 12s | \u003c15s |
| `/export/pdf` | 1.2s | 2.5s | \u003c3s |

**Scalability:**
- Stateless backend → Horizontal scaling (add more instances)
- Database connection pooling (SQLAlchemy, max 10 connections/instance)
- Streaming processing prevents memory spikes

### 8.3 Database Performance

**Optimization strategies:**
- Indexes on foreign keys (`user_id`, `client_id`)
- Indexes on frequently queried fields (`timestamp DESC`)
- No joins on large tables (data is denormalized)
- Query result caching (future: Redis)

---

## 9. Development Workflow

### 9.1 Git Workflow

**Branching strategy:**
- `main` branch: Production
- `develop` branch: Staging (future)
- Feature branches: `feature/sprint-XX-description`

**Commit conventions:**
```
Sprint XX: [Brief Description]

- Change 1
- Change 2
- Change 3

Fixes: #issue-number (if applicable)
```

### 9.2 CI/CD Pipeline (Future)

**GitHub Actions workflow:**

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          cd backend
          pytest tests/
      - name: Run frontend build
        run: |
          cd frontend
          npm ci
          npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Vercel
        run: vercel --prod
      - name: Deploy to Render
        run: render deploy
```

---

## 10. Future Architecture

### 10.1 Planned Enhancements

| Feature | Priority | Timeline | Impact |
|---------|----------|----------|--------|
| **Redis caching** | High | Q2 2026 | Reduce DB load, faster responses |
| **WebSocket support** | Medium | Q3 2026 | Real-time updates |
| **Mobile app (React Native)** | Medium | Q4 2026 | Expand platform |
| **GraphQL API** | Low | 2027 | More flexible queries |
| **Multi-region deployment** | High | Q3 2026 | Lower latency globally |

### 10.2 Architectural Evolution

**Phase 1 (Current):** Monolithic backend, single-region  
**Phase 2 (Q3 2026):** Multi-region, Redis caching  
**Phase 3 (2027):** Microservices (audit engine, user service, client service)

---

## Appendices

### Appendix A: Technology Decision Log

| Decision | Reasoning | Alternatives Considered |
|----------|-----------|-------------------------|
| **Next.js over Create React App** | SSG/SSR capabilities, Vercel integration | CRA, Vite |
| **FastAPI over Flask** | Auto-generated docs, type safety, async | Flask, Django |
| **PostgreSQL over MongoDB** | Relational data model, ACID compliance | MongoDB, MySQL |
| **JWT over sessions** | Stateless, scalable | Server sessions, OAuth |
| **bcrypt over argon2** | Industry standard, mature | argon2, scrypt |

### Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Zero-Storage** | Architecture where financial data is never persisted |
| **SSG** | Static Site Generation (Next.js pre-renders pages at build time) |
| **SSR** | Server-Side Rendering (pages rendered on-demand) |
| **CSR** | Client-Side Rendering (browser renders pages) |
| **ORM** | Object-Relational Mapping (SQLAlchemy) |
| **JWT** | JSON Web Token (authentication standard) |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | CTO | Initial publication |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
