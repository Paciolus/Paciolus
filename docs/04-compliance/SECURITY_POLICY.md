# Security Policy

**Document Classification:** Public  
**Version:** 1.0  
**Last Updated:** February 4, 2026  
**Owner:** Chief Information Security Officer  
**Review Cycle:** Quarterly

---

## Executive Summary

This document defines Paciolus's security principles, practices, and incident response procedures. Our security posture is built on three foundational pillars:

1. **Zero-Storage Architecture** — Financial data is never persisted (see ZERO_STORAGE_ARCHITECTURE.md)
2. **Defense in Depth** — Multiple layers of security controls
3. **Privacy by Design** — Security integrated from the ground up, not bolted on

**Key Security Controls:**
- ✅ TLS 1.3 encryption for all data in transit
- ✅ bcrypt password hashing (industry-standard, salted)
- ✅ JWT authentication with short-lived tokens (8 hour expiration)
- ✅ Multi-tenant data isolation (user-level database filtering)
- ✅ Automated vulnerability scanning (Dependabot, Snyk)
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
- **PostgreSQL** native encryption for database (AWS RDS/Render managed)
- **No encryption needed for financial data** (Zero-Storage — data is ephemeral)

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
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Expiration:** 8 hours (480 minutes)
- **Secret Key:** 64-character random hex string (stored in environment variables)
- **Rotation Policy:** Secret rotated every 90 days

**JWT payload** (claims):
```json
{
  "sub": "user_id",  // User ID (UUID)
  "email": "user@example.com",
  "iat": 1704672000,  // Issued at (Unix timestamp)
  "exp": 1704700800   // Expires at (8 hours later)
}
```

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
**Not currently implemented.** Planned for future release:
- Lock account after 5 failed login attempts
- 30-minute lockout period
- Email notification to user

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
| **Email** | RFC 5322 format, max 255 chars | `user@example.com` |
| **Password** | Complexity requirements (see above) | `Paciolus2026!` |
| **File upload** | MIME type check (CSV/Excel only), max 50MB | `trial_balance.xlsx` |
| **Client name** | Non-empty, max 100 chars, sanitized | `Acme Corp` |
| **Materiality** | Numeric, min 0, max 1,000,000 | `500` |

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
- **CSP (Content Security Policy)** headers enforced:
  ```
  Content-Security-Policy: default-src 'self'; script-src 'self'
  ```
- **No `dangerouslySetInnerHTML`** used in codebase

#### Cross-Site Request Forgery (CSRF) Prevention
- **SameSite cookies** (not used for JWT, but set for session cookies if added)
- **CORS policy** restricts origins:
  ```python
  CORS_ORIGINS = ["https://app.paciolus.com"]  # Production
  ```

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
- **Backend:** `python:3.11-slim` (official Python image, minimal attack surface)
- **Frontend:** `node:20-alpine` (official Node image, minimal size)

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
- **Dependabot** (GitHub): Automatic dependency updates
- **Snyk** (optional): Vulnerability scanning for npm and pip packages
- **npm audit**: Run on every build
- **pip-audit**: Run on every deployment

**Frequency:** Daily automated scans, alerts sent to engineering team.

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

**Policy:**
- We welcome responsible disclosure of security vulnerabilities
- We do not take legal action against security researchers acting in good faith
- We acknowledge all valid reports and provide updates on remediation

**Response SLA:**
- **Acknowledgment:** Within 2 business days
- **Initial assessment:** Within 5 business days
- **Fix deployed:** Within 30 days (depending on severity)

**Rewards:** Currently no bug bounty program (planned for future).

---

## 8. Security Monitoring

### 8.1 Logging

#### Application Logs
- **Level:** INFO (production), DEBUG (staging)
- **Location:** Centralized logging (e.g., Datadog, Logtail)
- **Retention:** 90 days
- **Sensitive data:** Passwords and JWT tokens never logged

**Example log entry:**
```json
{
  "timestamp": "2026-02-04T10:00:00Z",
  "level": "INFO",
  "message": "User login successful",
  "user_id": "uuid-1234",
  "ip_address": "192.168.1.1"
}
```

#### Audit Logs
- **Login events** (success/failure)
- **Account changes** (email update, password reset)
- **Data access** (client created, activity log viewed)
- **Administrative actions** (user account deletion)

**Retention:** 7 years (compliance requirement).

### 8.2 Alerting

#### Critical Alerts (PagerDuty/on-call)
- API error rate >5%
- Database connection pool exhausted
- Failed login attempts >100/minute (potential brute force)
- Zero-Storage violation (file persisted to disk)

#### Warning Alerts (Slack)
- API response time >2 seconds (p95)
- Memory usage >80%
- Dependency vulnerability detected (high severity)

---

## 9. Third-Party Security

### 9.1 Vendor Risk Assessment

All third-party services evaluated for security:

| Vendor | Service | Security Assessment | Compliance |
|--------|---------|---------------------|------------|
| **Vercel** | Frontend hosting | SOC 2 Type II, ISO 27001 | ✅ Passed |
| **Render** | Backend hosting | SOC 2 Type II | ✅ Passed |
| **PostgreSQL** | Database (managed) | GDPR-compliant | ✅ Passed |
| **Sentry** | Error tracking | SOC 2 Type II | ✅ Passed |

**Criteria:**
- ✅ SOC 2 Type II or equivalent certification
- ✅ GDPR/CCPA compliance
- ✅ Encryption at rest and in transit
- ✅ Regular security audits

### 9.2 Data Processing Agreements

**Signed DPAs with:**
- Vercel (frontend hosting)
- Render (backend hosting)
- Sentry (error tracking)

**Purpose:** GDPR Article 28 compliance (data processor agreement).

---

## 10. Security Training

### 10.1 Employee Training

**Onboarding (Day 1):**
- Security policy overview
- Password best practices
- Phishing awareness
- Zero-Storage architecture importance

**Annual Training:**
- OWASP Top 10 review
- Secure coding practices
- Incident response simulation
- GDPR/CCPA compliance updates

**Compliance:** 100% of employees complete annual training.

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
| 1.0 | 2026-02-04 | CISO | Initial publication |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
