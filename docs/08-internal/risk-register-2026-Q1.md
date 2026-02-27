# Risk Register — Q1 2026

**Document:** Formal Risk Register
**Period:** Q1 2026 (January – March 2026)
**SOC 2 Criteria:** CC4.1 / CC4.2 — Risk identification and assessment
**Owner:** Chief Information Security Officer
**Created:** 2026-02-27
**Last Reviewed:** 2026-02-27
**Next Review:** 2026-03-31 (Q1 close)
**Review Cadence:** Quarterly (Q1=March, Q2=June, Q3=September, Q4=December)

---

## Scoring Guide

| Dimension | 1 | 2 | 3 | 4 | 5 |
|-----------|---|---|---|---|---|
| **Likelihood** | Rare | Unlikely | Possible | Likely | Almost Certain |
| **Impact** | Negligible | Minor | Moderate | Major | Catastrophic |

**Inherent Score** = Likelihood × Impact (before controls)
**Residual Score** = Adjusted Likelihood × Adjusted Impact (after controls applied)

| Score Range | Risk Level |
|-------------|------------|
| 1–4 | Low |
| 5–9 | Medium |
| 10–14 | High |
| 15–25 | Critical |

---

## Risk Register

| Risk ID | Category | Description | Likelihood | Impact | Inherent Score | Mitigation Controls | Residual Score | Owner | Status | Last Reviewed |
|---------|----------|-------------|-----------|--------|----------------|---------------------|----------------|-------|--------|---------------|
| R-001 | Access Control | **Authentication / credential theft** — Adversary obtains valid user credentials via phishing, credential stuffing, or brute force; gains unauthorized access to client metadata or platform features | 3 | 4 | **12 (High)** | bcrypt 12-round hashing; 30-min JWT access tokens; 7-day refresh tokens with per-token reuse detection (revokes all tokens on replay); 5-attempt account lockout (15-min lockout period); HttpOnly/Secure/SameSite cookie delivery; HMAC-SHA256 user-bound CSRF tokens; email verification required for audit endpoints | 2×3 = **6 (Medium)** | CISO | Active | 2026-02-27 |
| R-002 | Application Security | **SQL injection / input validation failure** — Unsanitized user input reaches database query; attacker exfiltrates, modifies, or destroys persistent data | 2 | 5 | **10 (High)** | SQLAlchemy ORM (parameterized queries by default; no raw SQL); Pydantic `response_model` validation on all API inputs; `sanitize_error()` on all error responses; Bandit SAST in CI (blocks HIGH-severity findings); PR checklist attestation; ruff static analysis on every push | 1×5 = **5 (Medium)** | Engineering | Active | 2026-02-27 |
| R-003 | Data Handling | **Zero-Storage violation (accidental data persistence)** — Financial data (trial balance rows, account balances) accidentally written to database, violating the Zero-Storage architecture and creating a data breach surface | 2 | 4 | **8 (Medium)** | Zero-Storage architecture (no financial columns in any ORM model); accounting policy gate CI job (AST-based checker — fails build on any monetary float, hard-delete, or unapproved persistence pattern); PR checklist attestation; code review requirement; SoftDeleteMixin restricted to metadata-only models | 1×4 = **4 (Low)** | Engineering | Active | 2026-02-27 |
| R-004 | Supply Chain | **Third-party dependency compromise (supply chain)** — Malicious code introduced via compromised upstream package (npm or pip); executes in application context | 2 | 4 | **8 (Medium)** | Dependabot automated weekly PRs for dependency updates; pip-audit blocking CI gate (fails on HIGH/CRITICAL CVE); npm audit blocking CI gate (`--audit-level=high`, production deps only); version-pinned `requirements.txt` and `package-lock.json`; minimal dependency footprint | 1×4 = **4 (Low)** | Engineering | Active | 2026-02-27 |
| R-005 | Billing / Integrity | **Stripe webhook spoofing** — Attacker forges a Stripe webhook event to trigger unauthorized subscription upgrades, entitlement grants, or billing record manipulation | 2 | 4 | **8 (Medium)** | Stripe HMAC-SHA256 webhook signature verification on every event; server-side `success_url`/`cancel_url` derivation (client cannot inject redirect targets); `billing_redirect_injection_attempt_total` Prometheus counter; 7-test `TestCheckoutRedirectIntegrity` suite; billing analytics engine tracks anomalous event sequences | 1×4 = **4 (Low)** | Engineering | Active | 2026-02-27 |
| R-006 | Secrets Management | **Key / secret exposure** — API keys, JWT secret, database URL, or Stripe secret inadvertently committed to git, logged, or leaked in error responses | 2 | 5 | **10 (High)** | Environment variables only (never hardcoded); `.env` in `.gitignore`; Bandit SAST detects hardcoded secrets in CI; PR checklist attestation ("no secrets hardcoded in diff"); `sanitize_error()` strips sensitive fields from all client-facing error responses; structured logging scrubs credentials; production startup hard-fails if `SECRET_KEY` unset or < 32 chars | 1×5 = **5 (Medium)** | CISO | Active | 2026-02-27 |
| R-007 | Availability | **DDoS / rate-limit bypass** — Volumetric or application-layer attack overwhelms the API; service becomes unavailable to legitimate users | 3 | 3 | **9 (Medium)** | Tiered rate limiting: global 60 req/min default, per-tier per-endpoint limits (auth endpoints stricter); global body-size middleware (prevents large-payload exhaustion); Render + Vercel CDN absorbs volumetric traffic; Prometheus `rate_limit_exceeded_total` counter with alerting threshold; `429 Too Many Requests` returns `Retry-After` header | 2×2 = **4 (Low)** | Engineering | Active | 2026-02-27 |
| R-008 | Access Control | **Insider threat / privileged access abuse** — Authorized team member with production access intentionally or accidentally exfiltrates data, modifies records, or disrupts service | 1 | 4 | **4 (Low)** | Least-privilege access policy (no standing production DB write access); quarterly privileged access reviews; `ActivityLog` immutability via ORM `before_flush` guard (`AuditImmutabilityError` — cannot hard-delete audit records); GitHub branch protection on `main` (PR required); structured audit logging with request ID correlation | 1×3 = **3 (Low)** | CISO | Active | 2026-02-27 |
| R-009 | Infrastructure | **PostgreSQL TLS misconfiguration** — Database connection falls back to unencrypted transport; application data transmitted in plaintext between API server and database | 2 | 4 | **8 (Medium)** | PostgreSQL TLS startup guard: production hard-fails on startup if `sslmode` is not in `{require, verify-ca, verify-full}`; `init_db()` queries `pg_stat_ssl` and logs TLS negotiation status on every startup; 39 dedicated TLS guard + CIDR proxy trust tests in CI | 1×4 = **4 (Low)** | Engineering | Active | 2026-02-27 |
| R-010 | Application Security | **CSRF bypass** — Cross-site request forgery attack submits state-changing API requests on behalf of authenticated user via malicious third-party page | 2 | 3 | **6 (Medium)** | HMAC-SHA256 user-bound CSRF tokens (4-part format: `nonce:timestamp:user_id:HMAC`); 30-min token expiry; Origin/Referer header enforcement in `CSRFMiddleware`; CSRF token bound to authenticated user's `sub` claim (cannot be reused across accounts); `/auth/logout` not CSRF-exempt; HttpOnly refresh cookies eliminate cookie-based CSRF for auth refresh | 1×3 = **3 (Low)** | Engineering | Active | 2026-02-27 |
| R-011 | Privacy / Compliance | **Data subject rights failure (deletion non-compliance)** — User submits GDPR Art. 17 / CCPA deletion request; platform fails to fulfill within statutory deadline, creating regulatory liability | 2 | 3 | **6 (Medium)** | `/activity/clear` endpoint for user-initiated data clearing; soft-delete on all audit records (SoftDeleteMixin); Privacy Policy documents deletion rights; data-deletion-procedure.md documents 30-day SLA and step-by-step process (Sprint 456 — pending implementation); deletion request tracker planned | 2×2 = **4 (Low)** | CISO | Active — Sprint 456 reduces further | 2026-02-27 |
| R-012 | Availability | **Availability / service outage** — Cloud infrastructure failure (Render, Vercel), database unavailability, or deployment failure renders platform inaccessible | 3 | 3 | **9 (Medium)** | Render managed infrastructure (99.9% SLA); Vercel CDN global edge network; `/health` deep health endpoint (DB connectivity check); Sentry APM error rate alerting; BCP/DR plan (RTO 1–2h, RPO 0–1h); PostgreSQL automated daily backups (Render managed); semi-annual restore tests (Sprint 452 initiates first) | 2×2 = **4 (Low)** | Engineering | Active | 2026-02-27 |

---

## Risk Summary

| Risk Level | Count | Risk IDs |
|------------|-------|----------|
| **Critical** (15–25) | 0 | — |
| **High** (10–14) | 0 | — |
| **Medium** (5–9) | 3 | R-001, R-002, R-006 |
| **Low** (1–4) | 9 | R-003, R-004, R-005, R-007, R-008, R-009, R-010, R-011, R-012 |

**No High or Critical residual risks.** Three Medium residuals (R-001, R-002, R-006) are inherent to any web application accepting authentication credentials; controls are layered and consistent with industry practice.

---

## Open Remediation Items

| Risk ID | Gap | Remediating Sprint | Target Date |
|---------|----|-------------------|-------------|
| R-011 | Data deletion procedure and tracker not yet formalized | Sprint 456 | Q2 2026 |
| R-012 | First backup restore test not yet completed | Sprint 452 | Q1 2026 |

---

## Quarterly Review Procedure

> **CEO / CISO ACTION REQUIRED each quarter:** Add a recurring calendar event — "Paciolus Risk Register Quarterly Review" — for Q1=March 31, Q2=June 30, Q3=September 30, Q4=December 31.

Each quarterly review must:
1. Re-assess likelihood and impact scores for each existing risk
2. Verify that stated mitigation controls are still in place (spot-check CI gates, access review reports)
3. Add any new risks identified since last review
4. Close risks that no longer apply
5. Update "Open Remediation Items" table
6. Update "Last Reviewed" date on each risk row
7. Update the "Last Reviewed" date at the top of this document
8. File updated register as `docs/08-internal/risk-register-YYYY-QN.md`
9. Link new version from SECURITY_POLICY.md §7.4

The risk register update is a standing agenda item in the quarterly access review (see ACCESS_CONTROL_POLICY.md §8.1).

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-27 | CISO | Initial register — 12 risks identified, scored, and mitigated |
