# Security Policy

**Version:** 3.0 · **Effective:** 2026-10-24 · **Owner:** security@paciolus.com · **Classification:** Public

This replaces version 2.6, which described an organization Paciolus is not (a CISO, an on-call
rotation, annual penetration tests, monthly encryption verification, a database "architecturally
impossible" to breach). This version describes what is actually in place, so a customer can rely on
every sentence. The previous text is kept for the record in
[`archive/SECURITY_POLICY_pre-sprint-845_2026-10-24.md`](archive/SECURITY_POLICY_pre-sprint-845_2026-10-24.md).

## 1. Who runs Paciolus

Paciolus is built and operated by its founder. There is no security team and no 24/7 on-call.
Security issues are handled by the founder as soon as they are seen. Report one to
**security@paciolus.com** (see the [Vulnerability Disclosure Policy](VULNERABILITY_DISCLOSURE_POLICY.md)).

## 2. Certifications and testing

- **No SOC 2 audit has been performed and none is currently scheduled.**
- **No third-party penetration test has been performed.** There is no bug bounty.
- No ISO 27001, HIPAA or similar certification is held or claimed.

## 3. What data exists and where

| Data | Where | Notes |
|------|-------|-------|
| Uploaded files | Server memory, for the request | Not written to disk or the database. A previewed PDF or workbook is held in memory for up to 10 minutes so the tool can reuse it. |
| Accounts, client metadata, settings | Neon PostgreSQL (US East, us-east-1) | |
| Analysis summaries | Neon | Category totals, ratios, row counts, total debits/credits, materiality, flagged account names (no amounts). |
| Engagement entries | Neon | What the user types: materiality, follow-ups, intercompany mappings, analytical expectations, uncorrected misstatements (with amounts). |
| Shared report files | Cloudflare R2 (`paciolus-exports`) | Only reports a user chooses to share by link; 24 h (Professional) or 48 h (Enterprise), then deleted. |
| Rate-limit counters | Render Key Value | Request counts keyed by user or IP. |
| Application logs | Render log stream (and Grafana Cloud Loki if enabled) | No uploaded file contents; exception type names only; tracebacks stripped in production. |
| Error reports | Sentry | No request bodies, frame local variables, exception messages or breadcrumbs (stripped before sending). |
| Payments | Stripe | Card data never reaches Paciolus. |
| Email | SendGrid | Verification, password reset and billing notices. |

## 4. Controls in place

**Transport.** TLS 1.2 or higher (1.3 where supported), terminated at Vercel (frontend) and Render
(backend). HSTS, a nonce-based Content-Security-Policy with `strict-dynamic`, `frame-ancestors 'none'`
and `no-store` on downloads. Strict CORS allowlist.

**At rest.** Encryption at rest is provided and managed by Neon and Cloudflare R2. Paciolus does not
run its own encryption-at-rest layer and does not separately verify the providers' encryption.

**Authentication.** Passwords hashed with bcrypt (12 rounds). Access tokens expire after 15 minutes and are held in memory
in the browser; refresh tokens are HttpOnly, Secure, SameSite cookies rotated on use with reuse detection
(reuse revokes every session). A password change revokes all sessions. Five failed logins lock an
account for 15 minutes. Unknown-email and locked-account logins take the same time as real ones.
**There is no multi-factor authentication in the app**, including for the platform administrator.

**Request integrity.** CSRF tokens are HMAC-bound to the user, plus Origin and Fetch-Metadata checks.
Every route is rate-limited (60 requests/minute by default, tighter on authentication, upload,
export and write endpoints).

**Tenancy.** Every database query is scoped to the signed-in account in application code. There is
no database row-level security. This is designed to prevent one customer reading another's data;
no isolation guarantee beyond that is made.

**Uploads.** Size (100 MB), row (500,000), column and cell limits; file-signature checks; archive-bomb
limits (uncompressed size and ratio, per format); `defusedxml` for XML; a 500-page cap on PDFs.

**Exports.** Every CSV cell is escaped against spreadsheet formula injection by one shared writer.
Shared-report passcodes (optional) are hashed with Argon2id and throttled per token and per client IP.

**Administrator access.** One platform administrator role (superadmin). It can view customer accounts
and start a **read-only, 15-minute impersonation session**, which is recorded in the admin audit log and
cannot write. Revenue metrics are visible only to that role.

## 5. Monitoring and incidents

Errors go to Sentry. A GitHub Actions probe checks the live site every 15 minutes (GitHub may delay
scheduled runs). Security events — failed logins, lockouts, refresh-token reuse, impersonation,
account erasure — are written to the logs and, for the critical ones, to a `security_events` table
kept for 365 days. See the [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md).

## 6. Backups and recovery

The database relies on Neon's point-in-time recovery (window per the current Neon plan, to be
confirmed). **No independent, off-provider backup exists yet and no restore has been tested**; both
are in progress (Sprint 778b). See [Business Continuity](BUSINESS_CONTINUITY_DISASTER_RECOVERY.md).

## 7. Changes

Code changes go through pull requests with automated tests, linting and security scanning (see
[Secure SDL](SECURE_SDL_CHANGE_MANAGEMENT.md)). This policy is updated when the facts above change.
