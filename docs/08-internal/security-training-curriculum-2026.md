# Security Awareness Training Curriculum — 2026

**Document Classification:** Internal
**Version:** 1.0
**Effective Date:** February 27, 2026
**Last Updated:** February 27, 2026
**Owner:** CISO
**Review Cycle:** Annual (next review: February 2027)
**Control Reference:** CC2.2 / CC3.2 — Security awareness training

---

## Overview

This curriculum defines the mandatory security awareness training program for all Paciolus team members. Training is required:
- **On hire:** All 5 modules completed within the first 30 days of employment
- **Annually:** All 5 modules re-completed by January 31 each calendar year

Completion is tracked in `docs/08-internal/security-training-log-2026.md`.

**Total estimated duration:** ~4.5 hours across 5 modules

---

## Module 1: OWASP Top 10 for Web Applications

**Duration:** ~1 hour
**Delivery method:** Self-study (written content below + external references)
**Audience:** All team members

### Learning Objectives

After completing this module, the learner will be able to:
1. Name and describe each of the OWASP Top 10 vulnerability categories
2. Identify which categories are most relevant to Paciolus's stack (Next.js + FastAPI + PostgreSQL)
3. Describe the control Paciolus has in place for each relevant category

### Content

#### A01 — Broken Access Control (Critical for Paciolus)

Access control failures occur when users can act outside their intended permissions.

**Paciolus exposure:** Every API route must enforce the correct auth dependency (`require_verified_user` vs `require_current_user` vs public). Tool pages with team-tier features must use `UpgradeGate` on the frontend.

**Controls in place:**
- All protected routes use FastAPI dependency injection (`Depends(require_verified_user)`)
- Tier-based entitlement checks via `check_diagnostic_limit` dependency
- Frontend `UpgradeGate` for team-only tool pages
- Role-based access reviewed quarterly (see `ACCESS_CONTROL_POLICY.md`)

**Warning signs:** A route that returns data without checking `current_user.id`; a frontend page that renders without checking tier.

#### A02 — Cryptographic Failures

Sensitive data exposed due to weak or missing encryption.

**Paciolus exposure:** User credentials (passwords, email verification tokens), JWT secrets, database connection strings, Stripe API keys.

**Controls in place:**
- Passwords: bcrypt with explicit cost factor (12 rounds)
- Email verification tokens: SHA-256 hash-at-rest only (plaintext never stored — Alembic `ecda5f408617`)
- JWT secrets: stored in environment variables (never in code)
- Database: TLS enforced at startup (hard-fail if `sslmode` not `require/verify-ca/verify-full`)
- Backups: AES-256 at rest (provider-managed, Render)

**Warning signs:** `hashlib.md5()` for anything security-sensitive; secrets in `.env` committed to git; database URL without `sslmode=require`.

#### A03 — Injection (Critical for Paciolus)

Untrusted data sent to an interpreter (SQL, shell, etc.) as part of a command.

**Paciolus exposure:** All database operations; CSV/Excel formula injection via uploaded files; any user-controlled string used in dynamic queries.

**Controls in place:**
- All database queries use SQLAlchemy ORM (parameterized by default)
- Raw SQL is prohibited; if unavoidable, use `text()` with `:param` binding
- CSV/Excel upload: formula injection sanitization in `shared/security_utils.py` (strips `=`, `+`, `-`, `@` prefix on cell values)
- `sanitize_error()` prevents error messages from leaking injection context

**Warning signs:** `f"SELECT * FROM users WHERE id = {user_id}"`; raw string concatenation in any database query.

#### A04 — Insecure Design

Security gaps baked into architecture rather than implementation bugs.

**Paciolus exposure:** Zero-Storage architecture — financial data must never persist. Any design that stores trial balance data would be an insecure design failure.

**Controls in place:**
- Zero-Storage enforced at architecture level: no TB columns in any ORM model
- `ACCOUNTING_INVARIANT_CHECKER` CI job (`scripts/accounting_invariants.py`) — AST check blocks any PR that adds `Float` monetary columns or hard deletes audit records
- Soft-delete-only pattern on all audit tables (`SoftDeleteMixin`)

**Warning signs:** Any PR that adds a new table with columns like `amount`, `balance`, `debit`, `credit` as Float types; any `db.delete()` call on a protected model.

#### A05 — Security Misconfiguration

Insecure default configurations, incomplete setups, verbose error messages.

**Paciolus exposure:** Debug mode in production, overly permissive CORS, verbose stack traces in API responses.

**Controls in place:**
- `DEBUG=False` enforced in production environment
- CORS: explicit origin allowlist (never `*` in production)
- `sanitize_error()` removes stack traces from API error responses
- Content Security Policy: per-request nonce, `strict-dynamic`, no `unsafe-eval` in production
- `HttpOnly + Secure + SameSite=Lax` cookies for refresh tokens

**Warning signs:** `allow_origins=["*"]` in CORS config; `raise HTTPException(detail=str(e))` without sanitization; `DEBUG=True` in any production environment variable.

#### A06 — Vulnerable and Outdated Components

Using components with known vulnerabilities.

**Paciolus exposure:** Python dependencies (FastAPI, SQLAlchemy, PyJWT, etc.), Node dependencies (Next.js, React, etc.).

**Controls in place:**
- GitHub Dependabot: automated PRs for dependency updates
- `pip-audit` CI job: fails on known CVEs in Python dependencies
- Bandit CI job: static analysis for Python security issues
- Quarterly manual review of major dependency versions

**Warning signs:** Ignoring Dependabot PRs for >30 days; overriding `pip-audit` failures without documented justification.

#### A07 — Identification and Authentication Failures

Weak authentication, credential stuffing, session management issues.

**Paciolus exposure:** Login endpoint, password reset, JWT token lifecycle.

**Controls in place:**
- Account lockout after 5 failed attempts (DB-backed, not in-memory)
- JWT: 30-min access tokens (in-memory `useRef`), 7-day refresh tokens (HttpOnly cookie, `path="/auth"`)
- Refresh token rotation: new token issued on each refresh; reuse detection raises security alert
- Password-change revokes all existing refresh tokens (jti cleanup)
- CSRF: user-bound 4-part token with 30-min expiry + Origin/Referer enforcement

**Warning signs:** Storing access tokens in `localStorage`; refresh tokens with >7-day expiry; login endpoint without rate limiting.

#### A08 — Software and Data Integrity Failures

Insecure deserialization, unverified CI/CD pipeline integrity.

**Paciolus exposure:** Webhook payloads (Stripe), CI/CD pipeline (GitHub Actions).

**Controls in place:**
- Stripe webhook: signature verification via `stripe.Webhook.construct_event()` (HMAC-SHA256)
- GitHub Actions: pinned action versions; `GITHUB_TOKEN` scoped to minimum permissions
- Alembic migrations: version-controlled, reviewed in PR process

**Warning signs:** Accepting webhook payload without signature check; using `@latest` in GitHub Actions steps.

#### A09 — Security Logging and Monitoring Failures

Not logging enough to detect and respond to breaches.

**Paciolus exposure:** Failed logins, CSRF failures, token reuse events, rate limit spikes.

**Controls in place:**
- Structured JSON logging with `request_id` correlation (Python `structlog`)
- Prometheus counters: rate limit hits, CSRF failures, billing redirect injection attempts, token reuse events
- Sentry: exception capture with Zero-Storage compliant scrubbing (no financial data in error context)
- Weekly security event review process (`docs/08-internal/security-review-template.md`)

**Warning signs:** Silently swallowing exceptions (`except Exception: pass`); no log output on auth failures.

#### A10 — Server-Side Request Forgery (SSRF)

Server makes requests to attacker-controlled URLs.

**Paciolus exposure:** Any feature that fetches external URLs based on user input (currency rate lookup is the main candidate).

**Controls in place:**
- Currency rate lookup: fixed allowlist of external endpoints; user cannot supply arbitrary URLs
- No general-purpose HTTP proxy or webhook delivery features
- Checkout `success_url`/`cancel_url`: derived server-side from `FRONTEND_URL` env var (user cannot inject redirect URLs — see billing security sprint)

**Warning signs:** `httpx.get(user_supplied_url)` with no validation; Stripe checkout where frontend supplies redirect URLs.

### External References

- [OWASP Top 10 (2021)](https://owasp.org/Top10/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [OWASP ASVS (Application Security Verification Standard)](https://owasp.org/www-project-application-security-verification-standard/)

### Attestation Questions

After reading this module, answer the following questions (answers provided for self-study):

1. **Which OWASP category covers storing passwords in plaintext?**
   *A02 — Cryptographic Failures*

2. **A developer writes `cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")`— which OWASP category is violated?**
   *A03 — Injection*

3. **Stripe sends a webhook to our `/billing/webhook` endpoint. What must we verify before processing the payload?**
   *The Stripe-Signature header using `stripe.Webhook.construct_event()` — A08 — Software and Data Integrity Failures*

---

## Module 2: Secure Coding Practices — Python + TypeScript

**Duration:** ~1 hour
**Delivery method:** Self-study (written content below)
**Audience:** Engineers

### Learning Objectives

1. Apply Paciolus-specific secure coding patterns in Python (FastAPI/SQLAlchemy) and TypeScript (Next.js)
2. Recognize and avoid the most common security mistakes in our codebase
3. Use the tools and shared utilities that enforce security controls

### Content

#### 2.1 Zero-Storage Compliance

The single most important Paciolus-specific rule: **financial data (trial balance rows, amounts, account balances) must never be written to the database.**

**What this means in practice:**
- Trial balance analysis runs in-memory within a single request lifecycle
- Only metadata is persisted: diagnostic summaries (flags, counts), engagement records (client name, period), tool run records (tool name, duration, result count)
- The `ACCOUNTING_INVARIANT_CHECKER` CI job will block any PR that adds `Float` monetary columns to an ORM model

**How to verify your work:**
```python
# WRONG — monetary float column in ORM model
class DiagnosticSummary(Base):
    net_income: Mapped[float]  # ❌ blocks CI

# RIGHT — metadata only
class DiagnosticSummary(Base):
    record_count: Mapped[int]  # ✅ count only, not amounts
    has_anomaly: Mapped[bool]  # ✅ flag only
```

#### 2.2 Input Validation — Backend (Pydantic)

All API inputs are validated via Pydantic models. Never bypass Pydantic with raw `request.body()`.

```python
# WRONG
@router.post("/clients")
async def create_client(request: Request):
    body = await request.json()
    name = body["name"]  # ❌ no validation

# RIGHT
class CreateClientRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    industry: ClientIndustry  # ❌ Enum — rejects arbitrary strings

@router.post("/clients", response_model=ClientResponse, status_code=201)
async def create_client(data: CreateClientRequest, ...):  # ✅
```

**Field constraint requirements:**
- Strings: always set `min_length` and `max_length`
- Numbers: always set `ge` (≥) and/or `le` (≤) bounds where applicable
- Enums: use `Literal` or `Enum` types for constrained string sets
- Monetary amounts: use `Decimal` (never `float`) for any persisted monetary value

#### 2.3 Error Sanitization

Never expose internal error details to API consumers. Use `sanitize_error()` from `shared/log_sanitizer.py`.

```python
from backend.shared.log_sanitizer import sanitize_error

# WRONG
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # ❌ leaks stack trace

# RIGHT
except ValueError as e:
    logger.warning("validation_error", detail=str(e))
    raise HTTPException(status_code=422, detail=sanitize_error(e))  # ✅
```

**Rule:** Never use `except Exception` as a catch-all. Always catch the narrowest exception type that makes sense.

#### 2.4 Database Safety — SQLAlchemy ORM

**Parameterization is automatic** when using the ORM. The only risk is mixing raw SQL.

```python
# WRONG — raw SQL with f-string
result = db.execute(f"SELECT * FROM users WHERE email = '{email}'")  # ❌

# RIGHT — ORM query (parameterized automatically)
user = db.query(User).filter(User.email == email).first()  # ✅

# IF raw SQL is unavoidable — use text() with bound parameters
from sqlalchemy import text
result = db.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email})  # ✅
```

**Soft-delete rule:** Never call `db.delete(obj)` on audit-protected models (ActivityLog, DiagnosticSummary, ToolRun, FollowUpItem, FollowUpItemComment). Use `soft_delete(obj, user_id, reason)` from `shared/soft_delete.py`. The ORM `before_flush` guard will raise `AuditImmutabilityError` if you attempt a hard delete.

#### 2.5 Authentication Guards — Which to Use

| Endpoint type | Guard |
|--------------|-------|
| Financial analysis / exports | `require_verified_user` |
| Client / engagement management | `require_current_user` |
| Account settings / password change | `require_current_user` |
| Reference data (benchmarks, industries) | No guard (public) |
| Billing operations | `require_current_user` |

**Never** use no guard on a route that accesses user-specific data.

#### 2.6 CSRF Token Handling

All state-changing requests (POST, PUT, PATCH, DELETE) require a CSRF token in the `X-CSRF-Token` header. The token is included in every auth response (`AuthResponse.csrf_token`). The `apiClient` in `frontend/src/lib/apiClient.ts` handles this automatically.

**When writing new frontend API calls:** Always use `apiClient.post()` / `.put()` / `.delete()`, never raw `fetch()` for state-changing requests.

#### 2.7 TypeScript Type Safety

```typescript
// WRONG — using any
const result: any = await apiClient.post('/audit/trial-balance', data);
result.unknownField;  // ❌ no type checking

// RIGHT — typed response
const result: TrialBalanceResponse = await apiClient.post<TrialBalanceResponse>(
  '/audit/trial-balance',
  data
);
```

**Rules:**
- `any` is prohibited (`noImplicitAny` is enforced in tsconfig)
- Use discriminated unions for result types that can be success or error
- The `Severity` type is `'high' | 'medium' | 'low'` — canonical definition in `types/shared.ts`
- framer-motion transition properties require `as const`: `type: 'spring' as const`

#### 2.8 Content Security Policy Compliance

- Never use `dangerouslySetInnerHTML` — this bypasses CSP and introduces XSS risk
- Never use `eval()`, `new Function()`, or dynamic `<script>` injection
- Style changes must use CSS classes or CSS custom properties — not inline `style` attributes where avoidable
- The CSP nonce is injected automatically by the root layout; do not attempt to manage it manually

### External References

- [OWASP Secure Coding Practices Quick Reference](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security Practices](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
- [TypeScript Strict Mode](https://www.typescriptlang.org/tsconfig#strict)

### Attestation Questions

1. **A new route needs to let authenticated users view their own invoices. Which auth guard is correct?**
   *`require_current_user` — billing operations, not financial analysis*

2. **A frontend component needs to display dynamic HTML from an API response. What should you do?**
   *Never use `dangerouslySetInnerHTML`. Render individual fields as text nodes. If HTML is unavoidable, sanitize with DOMPurify first.*

3. **You need to find all clients matching a search string. What's wrong with `db.execute(f"SELECT * FROM clients WHERE name LIKE '%{q}%'")`?**
   *SQL injection risk. Use `db.query(Client).filter(Client.name.ilike(f"%{q}%"))` instead.*

---

## Module 3: Incident Response Roles + Escalation Procedures

**Duration:** ~30 minutes
**Delivery method:** Self-study (summary below + full doc reference)
**Audience:** All team members

### Learning Objectives

1. Know your role and responsibilities during a security incident
2. Know the escalation path for each severity level
3. Know the initial triage actions required in the first 15 minutes of an incident

### Content

#### 3.1 Severity Levels

| Severity | Definition | Example | Response Time |
|----------|-----------|---------|---------------|
| **P0 — Critical** | Active breach, data exposure, complete outage | Production DB compromised; authentication bypass discovered | Immediate (24/7) |
| **P1 — High** | Significant security issue or major degradation | Credential stuffing attack; billing system down | 1 hour (business hours), 4 hours (off-hours) |
| **P2 — Medium** | Limited impact, no confirmed breach | Single account compromised; elevated error rate | 4 hours (business hours) |
| **P3 — Low** | Informational, no immediate impact | Vulnerability in non-critical dependency; failed login spike | 24 hours |

#### 3.2 Your Role

| Role | Responsibilities |
|------|----------------|
| **Incident Commander (IC)** | Declares incidents; coordinates response; owns communication; makes containment decisions |
| **Technical Lead** | Executes containment and remediation; provides technical analysis |
| **Product Lead** | Manages customer communication; drafts status page updates |
| **CISO** | Approves breach notifications; coordinates legal/regulatory response |

**If you discover a potential incident:** You are the first responder. Your job is **not** to fix it — it is to escalate immediately so the IC can be engaged.

#### 3.3 First 15 Minutes — First Responder Checklist

If you suspect an incident:

1. **Do not attempt to remediate on your own** — you may destroy evidence
2. **Document what you observed:** timestamp, what you saw, what system, what data may be affected
3. **Escalate immediately:**
   - Slack: `#security-incidents` channel (or direct message to CTO/CISO if channel unavailable)
   - For P0: call/text CTO + CISO directly — do not wait for Slack
4. **Do not communicate externally** about the incident (no customer emails, no social media) until IC approves messaging
5. **Preserve evidence:** do not delete logs, restart services, or rotate secrets until IC authorizes

#### 3.4 Containment Decisions (IC Only)

Containment actions that may be taken by the IC:
- Revoke all user JWT tokens (via token cleanup job)
- Rotate secrets (JWT_SECRET, DATABASE_URL, Stripe keys)
- Take service offline (coordinated with Product Lead for customer notification)
- Block IPs or CIDRs at the infrastructure level

**You need IC authorization before any of these actions.**

#### 3.5 Post-Incident

All P0/P1 incidents require a post-mortem within 5 business days. The post-mortem template is in `docs/04-compliance/INCIDENT_RESPONSE_PLAN.md` §9. Post-mortems are blameless — focus on systemic improvements, not individual fault.

### External References

- [Full Incident Response Plan](../../04-compliance/INCIDENT_RESPONSE_PLAN.md)
- [NIST SP 800-61r2 — Computer Security Incident Handling Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf)
- [SANS Incident Handler's Handbook](https://www.sans.org/white-papers/33901/)

### Attestation Questions

1. **You notice the production database is returning queries much slower than normal and you see unusual `SELECT *` queries in the slow query log. What is your first action?**
   *Document the observation with timestamps, then escalate immediately to the IC via #security-incidents / CTO/CISO. Do not attempt remediation or restart the database.*

2. **The IC has declared a P0 incident. You have Render dashboard access and could restart the compromised service. Should you?**
   *No — not without IC authorization. Restarting may destroy forensic evidence. Wait for IC direction.*

3. **A customer emails you directly saying their account looks "weird." What do you do?**
   *Do not make promises or share incident details. Escalate to the IC immediately. Respond to the customer only with IC-approved messaging.*

---

## Module 4: Access Control + Least Privilege

**Duration:** ~30 minutes
**Delivery method:** Self-study (written content below)
**Audience:** All team members

### Learning Objectives

1. Understand the principle of least privilege and apply it to your system access
2. Follow Paciolus's credential hygiene requirements (password, MFA, secrets)
3. Know how to request, grant, and revoke access properly

### Content

#### 4.1 Principle of Least Privilege

Every team member and every service account should have the **minimum access required** to perform their function — nothing more.

**In practice:**
- Request only the permissions you need; do not request admin access "just in case"
- When your role changes, your access should be reviewed and adjusted
- Service accounts (GitHub Actions, Render deploy keys) should have scoped permissions, not full admin

#### 4.2 Password Requirements

| Requirement | Standard |
|-------------|---------|
| Minimum length | 16 characters |
| Complexity | Mix of uppercase, lowercase, digits, symbols |
| Uniqueness | Never reuse passwords across services |
| Storage | Use a password manager (1Password, Bitwarden, or equivalent) |
| Sharing | Never share passwords — if a credential must be shared, use a shared vault entry |

**Never store passwords in:**
- Slack messages
- Email
- Code comments
- Plaintext files
- Git commits

#### 4.3 Multi-Factor Authentication (MFA)

MFA is **mandatory** for all systems that support it:

| System | MFA Requirement |
|--------|----------------|
| GitHub | Required — TOTP or hardware key |
| Render | Required |
| Vercel | Required |
| Stripe Dashboard | Required |
| Sentry | Required |
| SendGrid | Required |
| Google Workspace (if applicable) | Required |

Use a TOTP app (Authy, Google Authenticator) or hardware security key (YubiKey). SMS-based MFA is permitted only where TOTP is unavailable.

#### 4.4 Secret Handling

Secrets include: API keys, database credentials, JWT secrets, Stripe keys, SMTP credentials, Sentry DSN.

**Rules:**
1. Secrets live in environment variables (Render / Vercel secret stores) — never in code
2. Secrets are never committed to git — even in private repos
3. Secrets are never sent via Slack, email, or any unencrypted channel
4. When a secret may have been exposed (accidental commit, Slack message), rotate it immediately — do not wait to confirm exposure
5. Use the principle of least privilege for API keys: grant only the scopes the application actually uses

**If you accidentally commit a secret:**
1. Rotate the secret immediately (before any other action)
2. Remove the commit from history (force-push with history rewrite, or create a new commit removing the secret)
3. Report to the CISO — even if you believe exposure was minimal

#### 4.5 Access Request and Revocation

**Requesting access:**
- Submit request to CTO/CISO via Slack with: system name, access level needed, business justification
- Access is provisioned within 1 business day

**When you no longer need access:**
- Proactively notify CTO/CISO when you complete a project or change roles
- Do not wait for the quarterly access review to remove stale access

**Quarterly access reviews:**
- All system access is reviewed quarterly (see `docs/04-compliance/ACCESS_CONTROL_POLICY.md`)
- You will be asked to confirm continued need for your access — respond promptly
- Unused access will be revoked without further notice after the review deadline

### External References

- [Paciolus Access Control Policy](../../04-compliance/ACCESS_CONTROL_POLICY.md)
- [NIST SP 800-63B — Digital Identity Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

### Attestation Questions

1. **A contractor needs read-only access to Sentry to debug an error for 2 weeks. What should you grant?**
   *Member-level access to the specific Sentry project only. Set a reminder to revoke it after 2 weeks — do not grant org-admin or permanent access.*

2. **You commit a file and realize 10 seconds later it contained a Stripe test API key. What do you do first?**
   *Rotate the key immediately via the Stripe dashboard — before history rewrite, before anything else. Then report to CISO and clean the git history.*

3. **You need the production DATABASE_URL to debug a query. Where should you look?**
   *Render dashboard environment variables. Never in Slack, email, or any team member's message history.*

---

## Module 5: Social Engineering + Phishing Awareness

**Duration:** ~30 minutes
**Delivery method:** Self-study (written content below)
**Audience:** All team members

### Learning Objectives

1. Recognize the common patterns used in phishing and social engineering attacks
2. Apply the "verify out-of-band" rule before acting on unusual requests
3. Know what to do when you receive a suspicious message

### Content

#### 5.1 Why This Matters for Paciolus

Social engineering attacks target people, not systems. A technically hardened platform can be compromised if an attacker can convince a team member to:
- Approve a malicious OAuth application
- Share credentials or MFA codes
- Click a link that installs malware on a development machine
- Accept a fraudulent wire transfer request

Financial software companies are high-value targets for spear-phishing because attackers know team members work with sensitive financial information.

#### 5.2 Phishing Attack Patterns

**Email phishing — what to look for:**

| Red flag | Example |
|----------|---------|
| Urgency or fear | "Your account will be suspended in 24 hours" |
| Unexpected sender | Email claiming to be from Stripe but sent from `stripe-billing@gmail.com` |
| Mismatched links | Displayed URL says `stripe.com` but hover shows `str1pe.com` |
| Requests for credentials | Any email asking you to enter a password or MFA code on a linked page |
| Unexpected attachments | PDF or ZIP attachments from senders you don't recognize |
| CEO/executive impersonation | "Hi, this is [CEO name], I need you to urgently buy gift cards / wire funds" |

**Spear phishing (targeted):**
Attackers research their targets. A spear-phishing email to Paciolus staff might:
- Reference real customer names (obtained from LinkedIn or data breaches)
- Impersonate a known tool provider (Stripe, Render, GitHub)
- Appear to come from a colleague's compromised email account

**SMS/voice phishing (vishing/smishing):**
- Calls claiming to be from "Stripe fraud department" asking to verify account details
- SMS with a link to "verify your Render login" after a "suspicious access attempt"

#### 5.3 The Verify Out-of-Band Rule

**If a message asks you to take an action involving credentials, payments, or access:**

1. **Stop.** Do not click the link or call the number in the message.
2. **Verify independently.** Contact the alleged sender via a known, trusted channel:
   - Log into the service directly (type the URL yourself)
   - Call a known phone number from the company's official website
   - Ask a colleague in person or via a separate communication channel
3. **Only then act** if the request is verified as legitimate.

This rule applies even if the message appears to come from a colleague or executive — email accounts get compromised.

#### 5.4 Protecting Your Devices

- Lock your screen when stepping away (auto-lock after 5 minutes recommended)
- Use full-disk encryption (FileVault on macOS, BitLocker on Windows)
- Keep OS and browser up to date — attackers exploit known vulnerabilities in older software
- Do not install software from untrusted sources, especially browser extensions
- Use a VPN when on public Wi-Fi, particularly when accessing Render or database consoles

#### 5.5 What to Do If You Suspect You Were Phished

1. **Do not try to "undo" anything yourself** — you may make things worse
2. **Disconnect from the network** if you believe malware may have been installed
3. **Immediately notify the CISO / CTO** via phone or Slack `#security-incidents`
4. **Preserve evidence:** do not delete the suspicious email; do not close the browser tab
5. **Change your passwords** for any accounts you believe were accessed — after notifying the CISO
6. **Do not be embarrassed** — phishing attacks are sophisticated. Reporting quickly is the most important thing.

### External References

- [SANS Phishing Awareness Resources](https://www.sans.org/security-awareness-training/resources/phishing/)
- [CISA Phishing Guidance](https://www.cisa.gov/phishing)
- [Google Safe Browsing — Check URLs](https://transparencyreport.google.com/safe-browsing/search)

### Attestation Questions

1. **You receive an email from "GitHub Security" saying your organization has a vulnerability that requires immediate action — click here. What do you do?**
   *Do not click the link. Log into GitHub directly at github.com and check Security Advisories. If nothing appears there, forward the email to CISO for investigation.*

2. **Your CEO sends you a Slack message saying to wire $5,000 for an urgent vendor payment — they're in a meeting and can't call. What do you do?**
   *Apply verify out-of-band: walk to the CEO's location, call them on a known personal number, or ask another executive. Wire transfers are never initiated on the basis of a single electronic message.*

3. **You click a link in an email and your browser asks you to install a browser extension. What do you do?**
   *Close the tab immediately. Notify the CISO. Do not install the extension. Check your browser for any recently installed extensions and remove any you don't recognize.*

---

## Curriculum Summary

| Module | Topic | Duration | Audience |
|--------|-------|----------|---------|
| 1 | OWASP Top 10 | ~1 hour | All |
| 2 | Secure Coding — Python + TypeScript | ~1 hour | Engineers |
| 3 | Incident Response Roles + Escalation | ~30 min | All |
| 4 | Access Control + Least Privilege | ~30 min | All |
| 5 | Social Engineering + Phishing | ~30 min | All |
| **Total** | | **~3.5 hours (engineers) / ~2.5 hours (non-engineers)** | |

---

## Completion and Attestation

After completing each module, team members must:
1. Read the full module content
2. Answer the attestation questions correctly (self-graded for self-study; manager reviews during onboarding)
3. Log completion in `docs/08-internal/security-training-log-2026.md`

Completion requires reading the module and answering the attestation questions. No formal exam is required for the annual cycle; new hires have their attestation reviewed by their manager during onboarding.

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-27 | CISO | Initial publication: 5 modules, attestation questions, Paciolus-specific controls |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
*Internal document — SOC 2 Type II control evidence — CC2.2 / CC3.2*
