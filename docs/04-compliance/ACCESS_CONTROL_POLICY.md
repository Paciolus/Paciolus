# Access Control Policy

**Version:** 1.2
**Document Classification:** Internal
**Effective Date:** February 26, 2026
**Last Updated:** February 27, 2026
**Owner:** Chief Information Security Officer
**Review Cycle:** Quarterly
**Next Review:** May 26, 2026

---

## Executive Summary

This document defines Paciolus's access control requirements for employees, contractors, and automated systems. It covers identity lifecycle management, privileged access governance, and periodic access reviews.

**Key Controls:**
- ✅ Role-based access with least-privilege assignment
- ✅ Provisioning/deprovisioning SLAs (1 business day / 4 hours)
- ✅ Quarterly privileged access reviews
- ✅ MFA required for all production and administrative access
- ✅ Zero-Storage architecture means no employee has access to customer financial data

**Target Audience:** Engineering team, HR, management, auditors

---

## Table of Contents

1. [Principles](#1-principles)
2. [Identity Lifecycle Management](#2-identity-lifecycle-management)
3. [Role Definitions](#3-role-definitions)
4. [Authentication Requirements](#4-authentication-requirements)
5. [Privileged Access Management](#5-privileged-access-management)
6. [Application-Level Access Control](#6-application-level-access-control)
7. [Third-Party and Contractor Access](#7-third-party-and-contractor-access)
8. [Access Reviews](#8-access-reviews)
9. [Violations and Enforcement](#9-violations-and-enforcement)
10. [Contact](#10-contact)

---

## 1. Principles

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Least Privilege** | Grant minimum permissions necessary for job function | Role-based assignments, no standing admin access |
| **Need to Know** | Access limited to data required for specific tasks | Database access restricted by role; no developer access to production DB |
| **Separation of Duties** | Critical operations require multiple approvals | Production deployments require PR approval; secret rotation requires two engineers |
| **Zero-Storage Guarantee** | No employee can access customer financial data | Financial data is never persisted — access is architecturally impossible |
| **Accountability** | All access actions are logged and attributable | Structured logging with request ID correlation, SSH session logging |

---

## 2. Identity Lifecycle Management

### 2.1 Provisioning

| Stage | SLA | Owner | Process |
|-------|-----|-------|---------|
| **Account creation** | Within 1 business day of start date | HR + Engineering Manager | Create accounts in GitHub, Render, Vercel, Sentry, Slack |
| **Role assignment** | Within 1 business day of start date | Engineering Manager | Assign role per Section 3 based on job function |
| **Access verification** | Within 2 business days of start date | New employee + manager | Employee confirms access to required systems; manager verifies no excess permissions |

### 2.2 Deprovisioning

| Stage | SLA | Owner | Process |
|-------|-----|-------|---------|
| **Voluntary departure** | Within 4 hours of last working day | HR + Engineering Manager | Revoke all system access, rotate shared secrets if applicable |
| **Involuntary departure** | Within 1 hour of notification | HR + CISO | Immediately revoke all access; audit recent activity |
| **Role change** | Within 1 business day | Engineering Manager | Remove old role permissions, assign new role permissions |
| **Contractor engagement end** | Within 4 hours of contract end | Engineering Manager | Revoke all access, remove from all systems |

### 2.3 Deprovisioning Checklist

When an employee or contractor departs, revoke access to:

- [ ] GitHub organization (remove from teams, revoke PATs)
- [ ] Render dashboard
- [ ] Vercel dashboard
- [ ] PostgreSQL database credentials (if applicable)
- [ ] Stripe dashboard
- [ ] Sentry organization
- [ ] SendGrid
- [ ] Slack workspace
- [ ] PagerDuty
- [ ] VPN / SSH keys (if applicable)
- [ ] Shared password manager entries (rotate if accessed)
- [ ] Any environment variables or secrets the individual had access to

### 2.4 Orphaned Account Detection

| Control | Frequency | Owner |
|---------|-----------|-------|
| Reconcile active system accounts against HR roster | Monthly | Engineering Manager |
| Flag accounts with no login in 90 days | Monthly (automated) | DevOps |
| Disable flagged accounts after manager review | Within 5 business days of flag | Engineering Manager |

---

## 3. Role Definitions

### 3.1 Internal Roles

| Role | Description | Systems Access | Database Access | Production SSH |
|------|-------------|---------------|-----------------|----------------|
| **Developer** | Builds and maintains application code | GitHub (read/write), Sentry (read), staging environment | None (read replica for debugging only) | ❌ No |
| **Senior Developer** | Developer + code review authority + on-call | Same as Developer + Render (deploy), PagerDuty | Read replica only | ❌ No |
| **DevOps/SRE** | Infrastructure management and incident response | GitHub, Render (full), Vercel (full), monitoring systems | Production (emergency only, logged) | ✅ Via bastion |
| **Team Lead** | Developer + team management + access approvals | Same as Senior Developer | Read replica only | ❌ No |
| **CTO** | Technical leadership + production access authority | All systems | Production (emergency, logged) | ✅ Via bastion |
| **CISO** | Security governance + incident command authority | Security tools, audit logs, all monitoring | Audit log read only | ❌ No |
| **Support** | Customer-facing support | Support tools, read-only user metadata | ❌ No direct access | ❌ No |
| **Management** | Business operations | Billing (Stripe), analytics | ❌ No | ❌ No |

### 3.2 Automated Service Accounts

| Account | Purpose | Permissions | Credential Type | Rotation |
|---------|---------|-------------|-----------------|----------|
| **CI/CD (GitHub Actions)** | Automated testing and deployment | GitHub read, Render deploy | GitHub Secrets (encrypted) | On change |
| **Application backend** | Database access, Stripe API, SendGrid API | PostgreSQL read/write, Stripe API, SendGrid API | Environment variables (encrypted at rest) | Per rotation policy |
| **Dependabot** | Automated dependency updates | GitHub PR creation | GitHub App token | Automatic |
| **Prometheus scraper** | Metrics collection | `/metrics` endpoint (read-only, unauthenticated) | N/A (network-level restriction) | N/A |

---

## 4. Authentication Requirements

### 4.1 Employee Authentication

| System | Authentication Method | MFA Required | Password Policy |
|--------|----------------------|-------------|-----------------|
| **GitHub** | SSO or password + MFA | ✅ Yes (enforced at org level) | GitHub-managed |
| **Render** | Password + MFA | ✅ Yes | Provider-managed |
| **Vercel** | SSO or password + MFA | ✅ Yes | Provider-managed |
| **Stripe** | Password + MFA | ✅ Yes (enforced at account level) | Provider-managed |
| **Sentry** | SSO or password + MFA | ✅ Yes | Provider-managed |
| **PostgreSQL** | Certificate or password | N/A (network-restricted) | 32+ character random, rotated per schedule |
| **SSH (bastion)** | SSH key + MFA | ✅ Yes | Key-based only |

### 4.2 MFA Policy

| Requirement | Value |
|-------------|-------|
| MFA enforcement | Mandatory for all employees on all production-adjacent systems |
| Acceptable MFA methods | Hardware security key (preferred), TOTP authenticator app |
| SMS-based MFA | ❌ Not permitted (SIM swap risk) |
| Recovery codes | Must be stored in approved password manager, not printed or emailed |
| Lost MFA device | Identity verification by manager + CISO approval for reset |

### 4.3 Password Requirements (Internal Systems)

Where provider-managed SSO is not available:

| Parameter | Requirement |
|-----------|-------------|
| Minimum length | 16 characters |
| Complexity | Uppercase + lowercase + number + special character |
| Reuse prevention | Last 12 passwords may not be reused |
| Maximum age | 90 days |
| Storage | Approved password manager only (no plaintext, no browser-only storage) |

### 4.4 Customer Authentication

Customer-facing authentication is governed by [SECURITY_POLICY.md](./SECURITY_POLICY.md) Section 3.1:
- JWT with 30-minute access tokens and 7-day rotating refresh tokens
- Password requirements (8+ chars, complexity rules)
- DB-backed account lockout (5 failed attempts, 15-minute lockout)
- Stateless HMAC-SHA256 CSRF protection

---

## 5. Privileged Access Management

### 5.1 Privileged Access Definition

Privileged access includes:
- Production database write access
- Production SSH access
- Deployment authority (production releases)
- Secret management (create, read, rotate secrets)
- User account administration (in Paciolus or provider systems)
- Billing administration (Stripe)

### 5.2 Privileged Access Controls

| Control | Implementation |
|---------|---------------|
| **Just-in-time access** | Production database access granted on-demand for specific incidents, revoked after resolution |
| **Access logging** | All privileged actions logged with timestamp, user, action, and target |
| **Dual authorization** | Secret rotation requires two engineers (one to initiate, one to verify) |
| **Break-glass procedure** | Emergency production access via documented break-glass procedure; audited within 24 hours |
| **No standing admin** | No engineer has persistent production database write access; granted per-incident |

### 5.3 Break-Glass Procedure

For emergency production access when normal approval channels are unavailable:

| Step | Action | Owner |
|------|--------|-------|
| 1 | Declare incident per [Incident Response Plan](./INCIDENT_RESPONSE_PLAN.md) | IC |
| 2 | Request emergency access with justification in incident channel | Requesting engineer |
| 3 | Grant temporary access (4-hour TTL) | CTO or designated backup |
| 4 | Log access grant with timestamp and justification | Scribe |
| 5 | Revoke access when incident resolved or TTL expires | CTO |
| 6 | Post-incident review of all break-glass actions | CISO (within 24 hours) |

---

## 6. Application-Level Access Control

### 6.1 Customer Data Isolation

Paciolus enforces multi-tenant isolation at the ORM level:

```python
# Every database query filters by authenticated user
clients = db.query(Client).filter(Client.user_id == current_user.id).all()
```

| Control | Implementation |
|---------|---------------|
| **Row-level security** | All queries filter by `user_id` at ORM level |
| **No cross-tenant access** | No API endpoint exposes data across users |
| **No admin override** | No "god mode" or admin endpoint to view other users' data |
| **Zero-Storage** | Financial data not queryable (never persisted) |

See [SECURITY_POLICY.md](./SECURITY_POLICY.md) Section 3.2 for detailed authorization model.

### 6.2 Tier-Based Entitlements

Customer feature access is gated by subscription tier:

| Tier | Diagnostic Limit | Client Limit | Tool Access | File Formats |
|------|-------------------|--------------|-------------|-------------|
| **Free** | 10/month | 3 | All 12 tools | 5 basic formats |
| **Solo** | 20/month | 10 | All 12 tools | 9 formats |
| **Team** | Unlimited | Unlimited | All 12 tools | All 10 formats |
| **Organization** | Unlimited | Unlimited | All 12 tools | All 10 formats |

Enforcement is implemented in `backend/shared/entitlements.py` and checked at the route level.

### 6.3 API Endpoint Protection

| Endpoint Category | Auth Required | Authorization Model |
|-------------------|---------------|---------------------|
| Public (marketing, health) | ❌ No | Open |
| Authentication (login, register) | ❌ No | Rate-limited |
| User data (clients, settings) | ✅ Yes (`require_current_user`) | User's own data only |
| Diagnostic tools (upload, analysis) | ✅ Yes (`require_verified_user`) | User's own data + tier entitlements |
| Billing (subscription, checkout) | ✅ Yes (`require_current_user`) | User's own subscription |
| Export (PDF, CSV, Excel) | ✅ Yes (`require_verified_user`) | User's own data + rate-limited |

---

## 7. Third-Party and Contractor Access

### 7.1 Contractor Access Policy

| Parameter | Requirement |
|-----------|-------------|
| Access scope | Limited to specific project/task requirements |
| Duration | Time-bound (maximum 90 days, renewable with review) |
| Approval | Engineering Manager + CISO sign-off |
| MFA | Required (same policy as employees) |
| NDA | Signed before any access granted |
| Production access | ❌ Not permitted (staging only) |
| Deprovisioning | Within 4 hours of engagement end |

### 7.2 Third-Party Service Access

Third-party services (subprocessors) access Paciolus data only as documented in:
- [SUBPROCESSOR_LIST.md](./SUBPROCESSOR_LIST.md) — Complete provider inventory
- [DATA_PROCESSING_ADDENDUM.md](./DATA_PROCESSING_ADDENDUM.md) — Processing terms and restrictions

No third-party service has access to customer financial data (Zero-Storage architecture).

---

## 8. Access Reviews

### 8.1 Review Schedule

| Review Type | Frequency | Scope | Owner | Deliverable |
|-------------|-----------|-------|-------|-------------|
| **Privileged access review** | Quarterly | All users with production DB, SSH, or deployment access | CISO | Signed review report |
| **General access review** | Semi-annual | All employee system access | Engineering Manager | Reconciliation report |
| **Service account review** | Quarterly | CI/CD credentials, API keys, database passwords | DevOps | Credential inventory update |
| **Orphaned account scan** | Monthly | Accounts with no activity in 90 days | DevOps (automated) | Flagged account list |
| **Risk register update** | Quarterly | All risks in `docs/08-internal/risk-register-YYYY-QN.md` | CISO | Updated register filed; residual scores re-validated; new/closed risks documented |

### 8.2 Privileged Access Review Process

| Step | Action | Owner | SLA |
|------|--------|-------|-----|
| 1 | Generate list of all users with privileged access | DevOps | 1 business day |
| 2 | For each user: verify current role still requires privileged access | Engineering Manager | 3 business days |
| 3 | Remove access for users who no longer require it | Engineering Manager | 1 business day |
| 4 | Document review results and exceptions | CISO | 2 business days |
| 5 | Sign-off | CISO | 1 business day |

### 8.3 Review Outputs

Each access review must produce:
- Date and reviewer name
- List of all accounts reviewed (per system: GitHub, Render, Vercel, PostgreSQL, Sentry, SendGrid, Stripe)
- Access level for each account (current vs. required)
- Actions taken (access removed, access modified, no change with justification)
- Exceptions (access retained despite role change, with documented business justification)
- Sign-off by CISO (privileged) or Engineering Manager (general)

**Template:** `docs/08-internal/access-review-template.md`

**Naming convention:** `docs/08-internal/access-review-YYYY-QN.md` (e.g., `access-review-2026-Q1.md`)

**Evidence filing:** Copy completed review to `docs/08-internal/soc2-evidence/cc6/` after sign-off.

#### Access Review Artifact History

| Review | Report | Due Date | Status |
|--------|--------|---------|--------|
| 2026 Q1 (first review) | [`access-review-2026-Q1.md`](../08-internal/access-review-2026-Q1.md) | 2026-03-31 | Pending CEO execution |

---

## 9. Violations and Enforcement

### 9.1 Policy Violations

| Violation | Severity | Response |
|-----------|----------|----------|
| Sharing credentials with unauthorized person | High | Immediate credential rotation; disciplinary review |
| Accessing production database without authorization | High | Access revoked; incident review |
| Disabling MFA without approval | Medium | MFA re-enabled; warning |
| Failed deprovisioning (access not revoked on time) | Medium | Immediate revocation; process review |
| Using personal email for system access | Low | Corrective guidance; account migrated |
| Weak password detected | Low | Forced password reset |

### 9.2 Reporting

Access control violations are reported as security incidents per [INCIDENT_RESPONSE_PLAN.md](./INCIDENT_RESPONSE_PLAN.md) and tracked to resolution.

---

## 10. Contact

| Role | Contact | Purpose |
|------|---------|---------|
| CISO | security@paciolus.com | Access policy questions, privileged access reviews |
| Engineering Manager | engineering@paciolus.com | Role assignments, provisioning requests |
| HR | hr@paciolus.com | Onboarding/offboarding notifications |
| DevOps | devops@paciolus.com | Service account management, infrastructure access |

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [Security Policy](./SECURITY_POLICY.md) | Section 5 (access control overview), Section 3.1 (customer authentication) |
| [Privacy Policy](./PRIVACY_POLICY.md) | Data handling obligations for access holders |
| [Incident Response Plan](./INCIDENT_RESPONSE_PLAN.md) | Reporting access control violations |
| [Secure SDLC / Change Management](./SECURE_SDL_CHANGE_MANAGEMENT.md) | Deployment access and approval requirements |
| [Subprocessor List](./SUBPROCESSOR_LIST.md) | Third-party access inventory |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-26 | CISO | Initial publication: role definitions, provisioning/deprovisioning SLAs, MFA policy, privileged access management, quarterly review cadence, tier-based entitlements |
| 1.2 | 2026-02-27 | CISO | Header version corrected (1.0→1.2); §8.3: template reference added (`access-review-template.md`), naming convention updated (`YYYY-QN.md`), evidence folder path (`soc2-evidence/cc6/`), Q1 2026 first review entry added to artifact history table |
| 1.1 | 2026-02-27 | CISO | §8.1: added "Risk register update" as a standing quarterly review item (CC4.1/CC4.2) |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
