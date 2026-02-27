# Security Policy

**Version:** 2.5
**Document Classification:** Public
**Effective Date:** February 26, 2026
**Last Updated:** February 27, 2026
**Owner:** Chief Information Security Officer
**Review Cycle:** Quarterly
**Next Review:** May 26, 2026

---

## Executive Summary

This document defines Paciolus's security principles, practices, and incident response procedures. Our security posture is built on three foundational pillars:

1. **Zero-Storage Architecture** — Financial data is never persisted (see ZERO_STORAGE_ARCHITECTURE.md)
2. **Defense in Depth** — Multiple layers of security controls
3. **Privacy by Design** — Security integrated from the ground up, not bolted on

**Key Security Controls:**
- ✅ TLS 1.3 encryption for all data in transit
- ✅ AES-256 encryption at rest (Render managed PostgreSQL — verified monthly, evidence in `docs/08-internal/soc2-evidence/cc7/`)
- ✅ bcrypt password hashing (direct library, 12 rounds, salted)
- ✅ JWT authentication with short-lived access tokens (30-minute expiration) and rotating refresh tokens (7-day expiration)
- ✅ Stateless HMAC-SHA256 user-bound CSRF protection (4-part tokens, 30-min expiry, origin enforcement, user binding)
- ✅ DB-backed account lockout (5 failed attempts, 15-minute lockout)
- ✅ Multi-tenant data isolation (user-level database filtering)
- ✅ Tiered rate limiting (per-user, per-tier, per-endpoint category)
- ✅ Automated vulnerability scanning (Dependabot, Bandit, pip-audit, npm audit)
- ✅ Structured JSON logging with request ID correlation and PII masking
- ✅ Prometheus observability metrics
- ✅ Zero-Storage compliance (no financial data persistence)

**Target Audience:** Enterprise customers, auditors, security teams, compliance officers

---

## Table of Contents

1. [Security Principles](#1-security-principles)
2. [Data Security](#2-data-security)
3. [Application Security](#3-application-security)
4. [Infrastructure Security](#4-infrastructure-security)
5. [Access Control](#5-access-control)
6. [Incident Response](#6-incident-response)
7. [Vulnerability Management](#7-vulnerability-management)
8. [Security Monitoring](#8-security-monitoring)
9. [Third-Party Security](#9-third-party-security)
10. [Security Training](#10-security-training)
11. [Compliance and Audits](#11-compliance-and-audits)
12. [Contact](#12-contact)

---

## 1. Security Principles

### 1.1 Core Tenets

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Least Privilege** | Users/systems have minimum necessary permissions | JWT scopes, database row-level security, API endpoint authorization |
| **Defense in Depth** | Multiple layers of security controls | TLS + JWT + database isolation + application-level validation |
| **Zero Trust** | Never trust, always verify | Every API request authenticated, no implicit trust between services |
| **Privacy by Design** | Security integrated from architecture phase | Zero-Storage model designed before first line of code |
| **Fail Secure** | Failures default to deny access | API returns 401/403 on auth failures, not fallback to public access |

### 1.2 Security-First Development

**Security is integrated into every phase:**

| Phase | Security Activity | Example |
|-------|-------------------|---------|
| **Design** | Threat modeling, architecture review | Zero-Storage decision to eliminate data breach risk |
| **Development** | Secure coding standards, code review | Input validation, parameterized SQL queries |
| **Testing** | Security testing, penetration testing | OWASP Top 10 testing, dependency scanning |
| **Deployment** | Security configuration, hardening | TLS 1.3 enforcement, secure HTTP headers |
| **Operations** | Monitoring, incident response | Real-time alerting on failed login attempts |

---

## 2. Data Security

### 2.1 DataClassification

| Classification | Examples | Protection Level |
|----------------|----------|------------------|
| **Public** | Marketing website content | None required |
| **Internal** | Employee email, project documentation | Access control |
| **Confidential** | User credentials, client metadata | Encryption + access control |
| **Highly Confidential** | Trial balance data | **Zero-Storage (not retained)** |

**Key Point:** The most sensitive data category (financial transactions) is **never stored**, eliminating the highest-risk scenario.

### 2.2 Encryption Standards

#### Data in Transit
- **TLS 1.3** for all HTTPS connections (frontend ↔ backend)
- **TLS 1.2** minimum accepted (for backward compatibility)
- **No plaintext HTTP** — All requests redirected to HTTPS

**Configuration:**
```nginx
# Nginx TLS configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers on;
```

#### Data at Rest
- **bcrypt** for password hashing (work factor: 12 rounds, auto-salted)
- **AES-256 encryption** for all application data at rest — provided and enforced by Render's managed PostgreSQL service (industry-standard provider-level encryption; not reliant on application configuration)
- **No encryption needed for financial data** (Zero-Storage — data is ephemeral; trial balance data is never written to disk)
- **Vercel** (frontend hosting) has no persistent storage configured — no KV, Blob, Postgres, or Edge Config instances are provisioned; all application data resides exclusively on Render

**Encryption at Rest — Control Verification:**

Provider-level encryption is verified monthly by the CISO or delegate. Evidence is recorded in `docs/08-internal/encryption-at-rest-verification-YYYYMM.md` and archived in `docs/08-internal/soc2-evidence/cc7/`. The monthly verification procedure:
1. Log into Render dashboard → confirm PostgreSQL encryption-at-rest setting is enabled; screenshot as evidence
2. Log into Vercel dashboard → confirm no persistent storage instances are attached; screenshot as evidence
3. File completed verification document with screenshots before end of month

Verification artifacts are retained for a minimum of 3 years (see AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md).

**Why bcrypt:**
- Adaptive algorithm (can increase work factor as computers get faster)
- Automatically salted (prevents rainbow table attacks)
- Industry standard (OWASP recommended)

### 2.3 Data Retention

See **ZERO_STORAGE_ARCHITECTURE.md** for detailed retention policies.

**Summary:**
| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| Trial balance data | 0 seconds | Zero-Storage security model |
| User credentials | Until deletion request | Account management |
| Activity logs (aggregates) | 365 days (1 year) | Workflow tracking, compliance |
| Client metadata | Until deletion request | Business functionality |

---

## 3. Application Security

### 3.1 Authentication

#### JWT (JSON Web Tokens)
- **Algorithm:** HS256 (HMAC with SHA-256, hardcoded to prevent downgrade attacks)
- **Access token expiration:** 30 minutes (configurable via `JWT_EXPIRATION_MINUTES`)
- **Refresh token expiration:** 7 days (configurable via `REFRESH_TOKEN_EXPIRATION_DAYS`)
- **Secret Key:** 64-character random hex string (stored in environment variables; minimum 32 chars enforced, production startup hard-fails if unset)
- **Rotation Policy:** Secret rotated every 90 days

**Access token payload** (claims):
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "tier": "team",
  "jti": "unique_token_id",
  "iat": 1704672000,
  "exp": 1704673800,
  "pwd_at": "2026-01-15T00:00:00Z"
}
```

**Key claims:**
- `jti` — Unique token identifier (enables per-token revocation)
- `tier` — User subscription tier (used for rate-limit resolution)
- `pwd_at` — Password change timestamp (invalidates pre-change tokens)

**Refresh token rotation:**
- Refresh tokens are DB-backed (SHA-256 hash stored, not raw token)
- Each refresh produces a new token and revokes the old one
- **Token reuse detection:** Presenting a revoked refresh token triggers revocation of ALL user tokens (breach containment)
- Password changes revoke all outstanding refresh tokens

**Note:** JWT does not contain sensitive data (no passwords, no financial data).

#### Password Requirements
Enforced at registration and password reset:
- ✅ Minimum 8 characters
- ✅ At least one uppercase letter (A-Z)
- ✅ At least one lowercase letter (a-z)
- ✅ At least one number (0-9)
- ✅ At least one special character (!@#$%^&*)

**Example valid password:** `Paciolus2026!`

**Rejected passwords:**
- ❌ `password` (too weak)
- ❌ `12345678` (no letters)
- ❌ `HelloWorld` (no number or special char)

#### Account Lockout
- **Implementation:** DB-backed (columns `failed_login_attempts` and `locked_until` on User model)
- **Threshold:** Account locked after **5 consecutive failed login attempts**
- **Lockout duration:** **15 minutes** (auto-resets when lockout period expires)
- **Counter reset:** On successful login
- **Account enumeration protection:** Lockout responses for unknown emails return an identical response shape to prevent user enumeration

### 3.2 Authorization

#### Multi-Tenant Isolation
Every database query filters by `user_id`:

```python
# Example: ClientManager.get_clients_for_user()
clients = db.query(Client).filter(
    Client.user_id == current_user.id  # Prevents cross-user access
).all()
```

**Enforcement:** Applied at the ORM level (SQLAlchemy), not application logic—prevents bypass.

#### API Endpoint Protection

| Endpoint | Authentication Required | Authorization |
|----------|------------------------|---------------|
| `POST /auth/register` | ❌ No | Public |
| `POST /auth/login` | ❌ No | Public |
| `GET /auth/me` | ✅ Yes | User's own data |
| `GET /clients` | ✅ Yes | User's clients only |
| `POST /audit/trial-balance` | ✅ Yes | User's session |
| `GET /dashboard/stats` | ✅ Yes | User's stats only |

**Default policy:** All endpoints require authentication unless explicitly marked public.

### 3.3 Input Validation

#### Server-Side Validation
All user inputs validated on backend (never trust client-side validation):

| Input Type | Validation | Example |
|------------|------------|---------|
| **Email** | RFC 5322 format, max 255 chars, disposable domain blocking | `user@example.com` |
| **Password** | Complexity requirements (see above) | `Paciolus2026!` |
| **File upload** | Format-specific parsers (CSV, Excel, TSV, OFX/QBO, IIF, ODS, PDF, TXT), global 110MB body limit | `trial_balance.xlsx` |
| **Client name** | Non-empty, max 100 chars, sanitized | `Acme Corp` |
| **Materiality** | Numeric, min 0, max 1,000,000 | `500` |

**Upload security hardening:**
- CSV/Excel formula injection sanitization (cells starting with `=`, `+`, `-`, `@` are prefixed)
- Column and cell count limits enforced per format
- Global body size middleware rejects requests exceeding 110MB before body is read (HTTP 413)

#### SQL Injection Prevention
- **SQLAlchemy ORM** used for all database queries (parameterized automatically)
- **No raw SQL** except for specific optimized queries (reviewed and parameterized)

**Example safe query:**
```python
# SQLAlchemy automatically parameterizes
user = db.query(User).filter(User.email == user_email).first()
```

**Never do this:**
```python
# UNSAFE: SQL injection vulnerability
query = f"SELECT * FROM users WHERE email = '{user_email}'"  # BAD!
```

#### Cross-Site Scripting (XSS) Prevention
- **React** auto-escapes all rendered content
- **CSP (Content Security Policy)** headers enforced per-request via Next.js middleware (`src/middleware.ts`). A cryptographic nonce (UUID → base64) is generated on every request, forwarded as `x-nonce` to the Next.js rendering pipeline, and embedded in the `Content-Security-Policy` response header.

  **Production CSP (enforced):**
  ```
  default-src 'self';
  script-src 'self' 'nonce-{per-request-nonce}';
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  img-src 'self' data: https:;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' {API_URL} https://*.sentry.io;
  frame-src 'none';
  frame-ancestors 'none';
  object-src 'none';
  base-uri 'self';
  form-action 'self'
  ```

  **Key controls:**
  - `unsafe-eval` removed from `script-src` — no `eval()`, `new Function()`, or webpack eval source maps in production.
  - `unsafe-inline` absent from `script-src` — Next.js RSC streaming scripts and all framework-injected inline scripts carry the per-request nonce; CSP3 browsers block non-nonce-tagged inline script execution.
  - `style-src 'unsafe-inline'` intentionally retained — React's `style` prop compiles to HTML `style=""` attributes, which CSP cannot nonce (only `<style>` elements accept nonces). Removing `unsafe-inline` from `style-src` would block all dynamic inline styles across the platform. CSS injection via `style-src` is a lower-severity vector than script injection and is mitigated by React's escaping of injected values.
  - `frame-src 'none'` and `object-src 'none'` added for defence-in-depth against plugin and cross-origin frame attacks.

- **No `dangerouslySetInnerHTML`** used in codebase

#### Security Headers
All responses include the following headers (via `SecurityHeadersMiddleware`):

| Header | Value |
|--------|-------|
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` (production only) |
| `Content-Security-Policy` | See above (production only) |

---

### 3.4 Request Integrity Controls

#### Cross-Site Request Forgery (CSRF)
- **Mechanism:** Stateless HMAC-SHA256 signed, user-bound tokens (no server-side state required)
- **Secret isolation:** `CSRF_SECRET_KEY` is a dedicated secret, separate from `JWT_SECRET_KEY`; production startup hard-fails if they are identical
- **Token format:** `{nonce}:{unix_timestamp}:{user_id}:{hmac_hex}` — four colon-separated segments; the nonce provides per-request uniqueness, the timestamp enables expiry enforcement, and the `user_id` binds the token to the authenticated session
- **Token expiry:** 30 minutes
- **User binding:** The `user_id` embedded in the token is verified against the `sub` claim of the request's Authorization Bearer token. A CSRF token issued for user A is cryptographically rejected for requests authenticated as user B. Requests without a Bearer token bypass user binding (the HMAC and expiry checks still apply).
- **Origin/Referer enforcement:** On every state-changing request, the `Origin` header is checked first; if absent, `Referer` is checked. When either header is present, its value must prefix-match an entry in `CORS_ORIGINS`. Requests from unlisted origins are rejected with HTTP 403 before CSRF token validation. Non-browser clients that omit both headers (e.g., server-to-server calls) are permitted.
- **Issuance:** A user-bound CSRF token is returned inline with every `login`, `register`, and `refresh` response — eliminating the extra `/auth/csrf` round-trip on auth events. The `/auth/csrf` endpoint remains available for edge-case re-fetches (e.g., CSRF expiry within an active session) and requires authentication.
- **Header:** `X-CSRF-Token` required on all state-changing methods (`POST`, `PUT`, `DELETE`, `PATCH`)
- **Validation:** Constant-time comparison via `hmac.compare_digest()` (prevents timing side-channels)
- **Exempt paths:** Login, registration, refresh, webhook, and other unauthenticated endpoints

**Failure modes:**

| Condition | Response | HTTP Status |
|-----------|----------|-------------|
| Missing `X-CSRF-Token` header | Request rejected | 403 Forbidden |
| Expired token (>30 minutes) | Request rejected | 403 Forbidden |
| Invalid HMAC signature | Request rejected | 403 Forbidden |
| Malformed token (wrong segment count) | Request rejected | 403 Forbidden |
| User ID mismatch (token issued for a different user) | Request rejected | 403 Forbidden |
| Origin or Referer not in `CORS_ORIGINS` allow-list | Request rejected | 403 Forbidden |

#### Cross-Origin Resource Sharing (CORS)
- **Origins:** Configured via `CORS_ORIGINS` environment variable (comma-separated allowlist)
- **Credentials:** `allow_credentials=True` with explicit origins (no wildcards)
- **Production guard:** Wildcard `*` in `CORS_ORIGINS` causes hard-fail at startup
- **Allowed headers:** `Authorization`, `Content-Type`, `X-CSRF-Token`, `Accept`

---

### 3.5 Rate Limit Tiers

All API endpoints are rate-limited via a tiered policy matrix. Limits are per-user (authenticated) or per-IP (anonymous), enforced per minute.

#### Endpoint Categories

| Category | Scope | Examples |
|----------|-------|---------|
| **Auth** | Authentication operations | Login, registration, password reset, email verification |
| **Audit** | Diagnostic and testing tool runs | Trial balance upload, journal entry testing, revenue testing |
| **Export** | File generation and download | PDF memos, Excel exports, CSV downloads, diagnostic packages |
| **Write** | Data mutation operations | Client create/update, engagement updates, adjustment entries |
| **Default** | All other endpoints | Dashboard stats, settings reads, reference data lookups |

#### Tier Matrix (requests per minute)

| Tier | Auth | Audit | Export | Write | Default |
|------|------|-------|--------|-------|---------|
| **Anonymous** | 5 | 10 | 20 | 30 | 60 |
| **Free** | 5 | 15 | 30 | 45 | 90 |
| **Solo** | 8 | 20 | 45 | 60 | 120 |
| **Team** | 15 | 45 | 90 | 135 | 240 |
| **Organization** | 20 | 60 | 120 | 180 | 300 |

#### Enforcement Behavior
- **Key resolution:** Authenticated requests keyed by `user_id`; anonymous requests keyed by client IP
- **Proxy trust:** `X-Forwarded-For` only accepted from IPs listed in `TRUSTED_PROXY_IPS` (prevents rate-limit bypass via header spoofing)
- **Overrides:** All limits are overridable via environment variables for operational flexibility
- **Exhaustion response:** HTTP 429 Too Many Requests with `Retry-After` header

---

## 4. Infrastructure Security

### 4.1 Cloud Provider Security

| Component | Provider | Security Features |
|-----------|----------|-------------------|
| **Frontend** | Vercel | DDoS protection, automatic HTTPS, edge caching |
| **Backend** | Render / DigitalOcean | Managed PostgreSQL, automatic OS patching, firewall |
| **Database** | PostgreSQL (managed) | Encrypted at rest, automated backups, network isolation |

**Shared Responsibility Model:**
- **Provider:** Physical security, hypervisor, network infrastructure
- **Paciolus:** Application code, access control, data encryption, vulnerability management

### 4.2 Network Security

#### HTTPS Enforcement
- All HTTP requests automatically redirected to HTTPS
- **HSTS (HTTP Strict Transport Security)** header enforced:
  ```
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  ```
- **Certificate:** Let's Encrypt (auto-renewed)

#### Firewall Rules
- Database port (5432) accessible only from backend API servers
- API server port (8000) accessible from internet (HTTPS only)
- No SSH access to frontend (serverless)
- SSH access to backend limited to authorized IPs (if self-hosted)

### 4.3 Docker Security

#### Base Images
- **Backend:** `python:3.12-slim-bookworm` (official Python image, minimal attack surface)
- **Frontend:** `node:22-alpine` (official Node image, minimal size)

#### Multi-Stage Builds
- Build dependencies not included in production image
- **Example:** Development tools (`pytest`, `black`) removed from production

#### Non-Root User
Containers run as non-root user (`appuser`):
```dockerfile
# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser
```

**Why:** Limits damage if container is compromised.

---

## 5. Access Control

**For the complete access control policy, including provisioning/deprovisioning SLAs, privileged access management, MFA requirements, and periodic review cadence, see [ACCESS_CONTROL_POLICY.md](./ACCESS_CONTROL_POLICY.md).**

### 5.1 Employee Access

| Role | Access Level | Systems |
|------|-------------|----------|
| **Developers** | Read/write code, read logs | GitHub, backend logs, staging environment |
| **DevOps/SRE** | Full infrastructure access | Production servers, database, monitoring |
| **Support** | Read-only user data | Activity logs (metadata only), user accounts |
| **Management** | Administrative access | Billing, analytics, user accounts |

**Principle:** No employee has access to financial data (Zero-Storage ensures this).

### 5.2 Production Access

#### SSH Access (if applicable)
- **Bastion host** required (no direct SSH to production)
- **SSH keys only** (no password authentication)
- **Audit logging** of all SSH sessions

#### Database Access
- **No direct database access** for developers (use read replicas for debugging)
- **DBA access** restricted to senior engineers (emergency only)
- **All queries logged** for audit trail

### 5.3 Secrets Management

#### Environment Variables
- **Never commit** secrets to Git (`.env` files in `.gitignore`)
- **Production secrets** stored in platform-specific secret managers:
  - Vercel: Environment Variables (encrypted at rest)
  - Render: Environment Variables (encrypted at rest)
  - Self-hosted: AWS Secrets Manager / Google Secret Manager

**Example secret:** `JWT_SECRET_KEY`

#### Rotation Policy
| Secret Type | Rotation Frequency | Automated |
|-------------|-------------------|-----------|
| JWT secret key | 90 days | No (manual) |
| Database password | 180 days | Yes (managed service) |
| API keys (third-party) | 365 days | No (manual) |

---

## 6. Incident Response

### 6.1 Incident Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| **P0 - Critical** | Complete service outage or data breach | Immediate (15 min) | Database offline, Zero-Storage violation |
| **P1 - High** | Major functionality degraded | 1 hour | API 50% error rate, auth system down |
| **P2 - Medium** | Minor functionality degraded | 4 hours | PDF export failing, slow response times |
| **P3 - Low** | Cosmetic issues, low-impact bugs | Next business day | UI alignment issue, typo |

**For the complete incident response playbook, including communication templates, post-mortem procedures, and incident-specific runbooks, see [INCIDENT_RESPONSE_PLAN.md](./INCIDENT_RESPONSE_PLAN.md).**

### 6.2 Incident Response Process

#### Phase 1: Detection (0-15 minutes)
- **Automated monitoring** (Sentry, Datadog) alerts on-call engineer
- **Manual report** via support email or Slack escalation channel
- **Incident declared** by on-call engineer

#### Phase 2: Assessment (15-30 minutes)
- **Severity assigned** (P0-P3)
- **Incident commander appointed** (senior engineer)
- **Status page updated** (status.paciolus.com)

#### Phase 3: Mitigation (30 minutes - 4 hours)
- **Immediate fixes** applied (rollback, service restart, rate limiting)
- **Root cause identified** (logs, metrics, database queries)
- **Escalation** to CTO if P0/P1 persists >2 hours

#### Phase 4: Resolution
- **Fix deployed** to production
- **Monitoring** for recurrence (24-48 hours)
- **Status page** updated to "resolved"

#### Phase 5: Post-Mortem (within 5 business days)
- **Blameless post-mortem** document created
- **Timeline** of events documented
- **Root cause** analysis (5 Whys)
- **Action items** to prevent recurrence
- **Post-mortem shared** with team

**Template:** `docs/08-internal/incident-YYYYMMDD-short-description.md`

### 6.3 Security Incident Specific

#### Data Breach
**Definition:** Unauthorized access to user credentials or client metadata.

**Special procedures:**
1. **Immediate containment:** Rotate JWT secret, force logout all users
2. **Assess scope:** Which users affected? What data accessed?
3. **Legal notification:** Consult legal team on GDPR/CCPA notification requirements
4. **User notification:** Email affected users within 72 hours (GDPR requirement)
5. **Regulatory notification:** Report to authorities if required (e.g., ICO for UK users)

**Note:** Financial data breach is architecturally impossible (Zero-Storage).

#### Zero-Storage Violation
**Definition:** Trial balance data persisted to disk/database (policy violation).

**Special procedures:**
1. **Critical incident (P0):** Zero-Storage is Paciolus's core security promise
2. **Immediate data deletion:** Delete persisted data within 1 hour
3. **Root cause:** Identify code change that caused persistence
4. **Rollback:** Immediate rollback to previous version
5. **Audit:** External security audit to verify complete data deletion
6. **Disclosure:** Transparent public disclosure on blog/status page

---

## 7. Vulnerability Management

### 7.1 Dependency Scanning

#### Automated Tools

| Tool | Type | CI Blocking | Scope |
|------|------|-------------|-------|
| **Bandit** | Python static analysis (SAST) | Yes — fails on HIGH severity + HIGH/MEDIUM confidence | Backend Python code |
| **pip-audit** | Python CVE scanner (SCA) | Yes — hard-fails on any finding | `requirements.txt` |
| **npm audit** | Node CVE scanner (SCA) | Yes — `--audit-level=high`, production deps only | Frontend packages |
| **Dependabot** | Automated dependency update PRs | N/A — weekly PRs | pip, npm, GitHub Actions |
| **Accounting Policy Guard** | Custom AST-based invariant checker | Yes — 5 accounting control invariants | Backend Python |

**Frequency:** Every CI run (on push and pull request). Dependabot PRs generated weekly.

#### Remediation SLA

| Severity | Response Time | Fix Deployment |
|----------|--------------|----------------|
| **Critical** | 24 hours | 48 hours |
| **High** | 72 hours | 1 week |
| **Medium** | 1 week | 2 weeks |
| **Low** | 2 weeks | Next release |

### 7.2 Penetration Testing

**Frequency:** Annually (minimum)  
**Provider:** Third-party security firm (e.g., Bishop Fox, Trail of Bits)  
**Scope:** Web application, API endpoints, infrastructure

**Deliverable:** Report with findings and remediation recommendations.

**Recent test:** [Planned for Q2 2026]

### 7.3 Vulnerability Disclosure Program

**Public email:** security@paciolus.com

**For the complete vulnerability disclosure policy, including safe-harbor provisions, testing boundaries, coordinated disclosure timeline, and researcher protections, see [VULNERABILITY_DISCLOSURE_POLICY.md](./VULNERABILITY_DISCLOSURE_POLICY.md).**

**Policy:**
- We welcome responsible disclosure of security vulnerabilities
- We do not take legal action against security researchers acting in good faith
- We acknowledge all valid reports and provide updates on remediation

**Response SLA:**
- **Acknowledgment:** Within 2 business days
- **Initial assessment:** Within 5 business days
- **Fix deployed:** Within 30 days (depending on severity)

**Rewards:** Currently no bug bounty program (planned for future).

### 7.4 Risk Management

Paciolus maintains a formal risk register documenting all identified security and operational risks, their likelihood and impact scores, mitigation controls, residual risk levels, and owners.

**Risk Register:** [`docs/08-internal/risk-register-2026-Q1.md`](../08-internal/risk-register-2026-Q1.md)

**Key metrics (Q1 2026):**
- 12 risks identified across 7 categories
- 0 Critical residual risks; 0 High residual risks
- 3 Medium residual risks (credential theft, SQL injection, secret exposure — inherent to any authenticated web application; layered controls applied)
- 9 Low residual risks

**Review cadence:** Quarterly (Q1=March, Q2=June, Q3=September, Q4=December). The risk register update is a standing agenda item in the quarterly access review (ACCESS_CONTROL_POLICY.md §8.1).

**SOC 2 criteria:** CC4.1 (risk identification), CC4.2 (risk assessment and response).

---

## 8. Security Monitoring

**For the complete audit logging policy, including event classification, tamper-resistance controls, retention schedules, and legal hold procedures, see [AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md](./AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md).**

### 8.1 Logging

#### Application Logs
- **Level:** INFO (production), DEBUG (staging/development)
- **Format:** Structured JSON in production (`JSONFormatter`), human-readable in development
- **Request ID correlation:** Every request receives a unique ID (from `X-Request-ID` header or auto-generated 12-char UUID), propagated via `ContextVar` and returned in `X-Request-ID` response header
- **Location:** Centralized logging (e.g., Datadog, Logtail)
- **Retention:** 90 days
- **PII handling:** See Section 8.2 (Log Redaction and Sensitive Data Handling)

**Example log entry (production JSON format):**
```json
{
  "timestamp": "2026-02-26T10:00:00Z",
  "level": "INFO",
  "logger": "routes.auth",
  "message": "User login successful",
  "request_id": "a1b2c3d4e5f6"
}
```

#### Audit Logs
- **Login events** (success/failure)
- **Account changes** (email update, password reset)
- **Data access** (client created, activity log viewed)
- **Administrative actions** (user account deletion)

**Retention:** 7 years (compliance requirement).

### 8.2 Log Redaction and Sensitive Data Handling

All application logs are processed through a dedicated sanitization layer (`log_sanitizer`) before emission. No raw credentials, tokens, or personally identifiable information (PII) appear in log output.

#### Email Masking
- Emails are redacted to the format `first3***@domain.com` (e.g., `abc***@example.com`)
- Applied to all log messages, structured fields, and error contexts

#### Token Fingerprinting
- JWT access tokens and refresh tokens are never logged in full
- Token references use a fingerprint format: first 8 characters + `[` + 8-character SHA-256 prefix + `]`
- Enables correlation of token-related events without exposing the token value

#### Exception Sanitization
- Caught exceptions are logged as class name only (e.g., `ValueError`), never via raw `str(e)`
- Prevents accidental leakage of file paths, SQL fragments, or user data embedded in exception messages
- All route-level exception handlers use `sanitize_error()` to produce safe client-facing messages

#### Absolute Exclusions
The following data categories are never written to any log destination:
- Passwords (plaintext or hashed)
- JWT token bodies
- CSRF tokens
- Trial balance line items or financial figures (Zero-Storage compliance)
- Database connection strings

### 8.3 Alerting

#### Critical Alerts (PagerDuty/on-call)
- API error rate >5%
- Database connection pool exhausted
- Failed login attempts >100/minute (potential brute force)
- Zero-Storage violation (file persisted to disk)

#### Warning Alerts (Slack)
- API response time >2 seconds (p95)
- Memory usage >80%
- Dependency vulnerability detected (high severity)

### 8.4 Observability

#### Prometheus Metrics
- **Endpoint:** `GET /metrics` (unauthenticated, standard Prometheus scrape pattern, hidden from OpenAPI schema)
- **Registry:** Dedicated registry (does not expose default process/GC collectors)
- **Metrics exposed:** Parse counters/histograms by format, billing event counters, active trial/subscription gauges

#### Sentry APM
- **Integration:** Conditional (enabled only if `SENTRY_DSN` environment variable is set)
- **Trace sample rate:** 10% (configurable via `SENTRY_TRACES_SAMPLE_RATE`)
- **PII policy:** `send_default_pii=False`
- **Zero-Storage compliance:** `before_send` hook strips `event["request"]["data"]` from all error reports

---

## 9. Third-Party Security

### 9.1 Vendor Risk Assessment

All third-party services evaluated for security:

| Vendor | Service | Security Assessment | Compliance |
|--------|---------|---------------------|------------|
| **Vercel** | Frontend hosting | SOC 2 Type II, ISO 27001 | ✅ Passed |
| **Render** | Backend hosting | SOC 2 Type II | ✅ Passed |
| **PostgreSQL** | Database (managed) | GDPR-compliant | ✅ Passed |
| **Stripe** | Payment processing | PCI DSS Level 1, SOC 2 Type II | ✅ Passed |
| **Sentry** | Error tracking (Zero-Storage compliant — request body stripped) | SOC 2 Type II | ✅ Passed |

**Criteria:**
- ✅ SOC 2 Type II or equivalent certification
- ✅ GDPR/CCPA compliance
- ✅ Encryption at rest and in transit
- ✅ Regular security audits

### 9.2 Data Processing Agreements

**Signed DPAs with:**
- Vercel (frontend hosting)
- Render (backend hosting)
- Stripe (payment processing)
- Sentry (error tracking)

**Purpose:** GDPR Article 28 compliance (data processor agreement).

---

## 10. Security Training

### 10.1 Employee Training

All Paciolus team members complete mandatory security awareness training on hire and annually.

**Curriculum:** `docs/08-internal/security-training-curriculum-2026.md`

| Module | Topic | Duration | Audience |
|--------|-------|----------|---------|
| M1 | OWASP Top 10 for Web Applications | ~1 hour | All |
| M2 | Secure Coding — Python + TypeScript | ~1 hour | Engineers |
| M3 | Incident Response Roles + Escalation | ~30 min | All |
| M4 | Access Control + Least Privilege | ~30 min | All |
| M5 | Social Engineering + Phishing Awareness | ~30 min | All |

**Onboarding (Day 1):** Modules M3, M4, M5 completed before system access is granted.
**Onboarding (Week 1):** Modules M1 + M2 (engineers) completed within the first 7 days.
**Annual refresh:** All modules re-completed by January 31 each calendar year.

**Compliance:** 100% of team members complete all applicable modules annually. Completion is tracked in `docs/08-internal/security-training-log-2026.md` and filed as SOC 2 evidence in `docs/08-internal/soc2-evidence/cc2/`.

**Onboarding procedure:** `docs/08-internal/onboarding-runbook.md`

### 10.2 Developer Security Standards

**Mandatory code review checklist:**
- [ ] Input validation on all user inputs
- [ ] SQL queries parameterized (no string concatenation)
- [ ] Secrets not hardcoded
- [ ] Zero-Storage compliance verified (no file persistence)
- [ ] Error messages do not leak sensitive data

---

## 11. Compliance and Audits

### 11.1 Security Certifications (Planned)

| Certification | Target Date | Status |
|---------------|-------------|--------|
| **SOC 2 Type II** | Q4 2026 | In progress |
| **ISO 27001** | Q2 2027 | Planned |
| **GDPR Article 42** | Q3 2027 | Planned |

### 11.2 Security Audits

**Internal audits:** Quarterly (by CTO)  
**External audits:** Annually (by third-party firm)

**Audit scope:**
- Code review (random sampling)
- Infrastructure configuration
- Access control policies
- Incident response procedures
- Zero-Storage compliance verification

---

## 12. Contact

### Security Inquiries

| Type | Contact | Response Time |
|------|---------|---------------|
| **Vulnerability reports** | security@paciolus.com | 2 business days |
| **General security questions** | security@paciolus.com | 5 business days |
| **Enterprise sales security** | sales@paciolus.com | 1 business day |
| **Compliance documentation** | compliance@paciolus.com | 3 business days |

### Emergency Security Hotline

**For critical security incidents only:**  
Phone: [To be established]  
Available: 24/7

---

## Appendices

### Appendix A: Security Glossary

| Term | Definition |
|------|------------|
| **bcrypt** | Password hashing algorithm with adaptive work factor |
| **JWT** | JSON Web Token for stateless authentication |
| **TLS 1.3** | Latest version of Transport Layer Security protocol |
| **Zero-Storage** | Architecture where financial data is never persisted |
| **Multi-tenant** | Single application serving multiple isolated customers |

### Appendix B: Security Standards Referenced

- OWASP Top 10 (2021): https://owasp.org/Top10/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks
- GDPR Security Requirements: https://gdpr-info.eu/art-32-gdpr/

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.5 | 2026-02-27 | CISO | Section 10.1 (Security Training): replaced bullet list with structured 5-module curriculum table, added per-module duration + audience, onboarding schedule (Day 1 / Week 1), compliance tracking references (`security-training-curriculum-2026.md`, `security-training-log-2026.md`, `soc2-evidence/cc2/`), onboarding runbook reference |
| 2.4 | 2026-02-27 | Engineering | Section 7.4 (Risk Management): risk register link added; reference to `risk-register-2026-Q1.md` |
| 2.3 | 2026-02-27 | Engineering | Section 2.2 (Encryption at Rest): AES-256 assertion, Vercel no-storage statement, monthly verification procedure with evidence path |
| 2.2 | 2026-02-27 | CISO | Section 3.4 (CSRF): 4-part user-bound token format (`nonce:timestamp:user_id:HMAC`), expiry 60 min → 30 min, Origin/Referer enforcement, user binding check, `/auth/csrf` auth-guarded, `csrf_token` embedded in login/register/refresh responses; failure mode table updated with user mismatch and origin enforcement rows |
| 2.1 | 2026-02-26 | CISO | Restructure: dedicated subsections for Request Integrity Controls (3.4), Rate Limit Tiers (3.5), Log Redaction and Sensitive Data Handling (8.2); CSRF failure mode table; endpoint category definitions; enforcement behavior details; token fingerprinting and exception sanitization expanded |
| 2.0 | 2026-02-26 | CISO | Align with implementation: JWT refresh rotation, DB-backed lockout, HMAC CSRF, rate limiting, security headers, Docker 3.12/22, scanning tools (Bandit/pip-audit/npm audit), structured logging, Prometheus metrics, Sentry APM, Stripe vendor, retention 365 days |
| 1.0 | 2026-02-04 | CISO | Initial publication |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
