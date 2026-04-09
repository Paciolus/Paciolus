# Paciolus Development Roadmap

> **Protocol:** See [`tasks/PROTOCOL.md`](PROTOCOL.md) for lifecycle rules, post-sprint checklist, and archival thresholds.
>
> **Completed eras:** See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for all historical phase summaries.
>
> **Executive blockers:** See [`tasks/EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) for CEO/legal/security pending decisions.
>
> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md).

---

## Hotfixes

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

- [2026-04-07] PENDING: dependency patch — uvicorn 0.43.0→0.44.0, python-multipart 0.0.22→0.0.24 (nightly report remediation)
- [2026-04-06] PENDING: secret domain separation — AUDIT_CHAIN_SECRET_KEY independent from JWT, backward-compat verification fallback, TLS evidence signing updated
- [2026-04-04] PENDING: dependency upgrades — 14 packages updated, 3 security-relevant (fastapi 0.135.3, SQLAlchemy 2.0.49, stripe 15.0.1), tzdata 2026.1, uvicorn 0.43.0, pillow 12.2.0, next watchlist patch
- [2026-03-26] e04e63e: full sweep remediation — sessionStorage financial data removal, CSRF on /auth/refresh, billing interval base-plan fix, Decimal float-cast elimination (13 files, 16 tests added)
- [2026-03-21] 8b3f76d: resolve 25 test failures (4 root causes: StyleSheet1 iteration, Decimal returns, IIF int IDs, ActivityLog defaults), 5 report bugs (procedure rotation, risk tier labels, PDF overflow, population profile, empty drill-downs), dependency updates (Next.js 16.2.1, Sentry, Tailwind, psycopg2, ruff)
- [2026-03-21] 8372073: resolve all 1,013 mypy type errors — Mapped annotations, Decimal/float casts, return types, stale ignores (#49)
- [2026-03-20] AUDIT-07-F5: rate-limit 5 unprotected endpoints — webhook (10/min), health (60/min), metrics (30/min); remove webhook exemption from coverage test
- [2026-03-19] CI fix: 8 test failures — CircularDependencyError (use_alter), scheduler_locks mock, async event loop, rate limit decorators, seat enforcement assertion, perf budget, PG boolean literals
- [2026-03-18] 7fa8a21: AUDIT-07-F1 bind Docker ports to loopback only (docker-compose.yml)
- [2026-03-18] 52ddfe0: AUDIT-07-F2 replace curl healthcheck with python-native probe (backend/Dockerfile)
- [2026-03-18] 5fc0453: AUDIT-07-F3 create /app/data with correct ownership before USER switch (backend/Dockerfile)
- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| ~~Password reset flow (NEW-015)~~ | RESOLVED — Sprint 572 | Sprint 569 |
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |

---

## Active Phase
> Sprints 478–531 archived to `tasks/archive/sprints-478-531-details.md` (consolidated).
> Sprints 532–561 archived to `tasks/archive/sprints-532-561-details.md` (consolidated).
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.
> FIX-3–8B, AUDIT-09–10 archived to `tasks/archive/fix-3-8b-audit-09-10-details.md`.
> Sprints 563–569, CI-FIX archived to `tasks/archive/sprints-563-569-details.md`.
> Sprints 570–571 archived to `tasks/archive/sprints-570-571-details.md`.
> Sprints 572–578 archived to `tasks/archive/sprints-572-578-details.md`.
> Sprints 579–585 archived to `tasks/archive/sprints-579-585-details.md`.
> Sprints 586–591 archived to `tasks/archive/sprints-586-591-details.md`.

### Sprint 592: Token Exposure Reduction — Cookie-Only Auth
**Status:** COMPLETE
**Goal:** Eliminate JS-readable bearer tokens from browser auth flow

**Changes:**
- [x] Backend: `paciolus_access` HttpOnly cookie set on login/register/refresh, cleared on logout
- [x] Backend: `resolve_access_token` dependency — Bearer header (API clients) → cookie fallback (browser)
- [x] Backend: JWT lifetime reduced 30m → 15m (config default + .env.example)
- [x] Frontend: `injectAuthHeaders` no longer injects `Authorization: Bearer` header
- [x] Frontend: `fetchCsrfToken`, `uploadTransport` — use cookie auth, not Bearer
- [x] Frontend: `downloadAdapter` — add missing `credentials: 'include'`
- [x] ESLint: XSS sink governance — `no-eval`, `no-implied-eval`, ban `dangerouslySetInnerHTML`, `innerHTML`, `document.write`
- [x] Tests: 3 test suites updated (removed Bearer assertions), 1745 frontend + 26 backend auth tests pass

**Review:**
- Access token cookie: HttpOnly, Secure (prod), SameSite=None (prod) / Lax (dev), path=/, max-age=JWT_EXPIRATION_MINUTES*60
- Bearer header still accepted for non-browser API clients (backward compatible)
- No `dangerouslySetInnerHTML` usage found in codebase (clean baseline)
- `style-src 'unsafe-inline'` retained (React inline styles — documented limitation)

### Sprint 595: verify-email 422 Fix + forgot-password Diagnostic
**Status:** COMPLETE
**Goal:** Unblock the production email-verification click-through and gather data on why post-Sprint-594 password reset still returns "unknown email".

**Symptoms observed post-Sprint-594 deploy:**
1. CEO clicks an email (from spam) → `/verify-email` page shows "Verification Failed". Render logs: `POST /auth/verify-email?token=... 422`.
2. CEO retries `/auth/forgot-password` → still logs `"Password reset requested for unknown email: com***@gmail.com"`. The Sprint 594 migration ran cleanly (`Running upgrade a848ac91d39a -> f7b3c91a04e2`) but the lookup still fails.

**Root cause (Problem A — verify-email 422):**
`VerificationContext.verifyEmail` was calling `apiPost('/auth/verify-email?token=...', null, {})` — token in the URL query string, empty body. The backend's `VerifyEmailRequest` is a Pydantic body model requiring `{token: string}` in the JSON body, so every click-through 422'd on the missing field. Latent since Sprint 58 (original email verification work) because Phase 1 only tested email *delivery*, not the click-through path. The email the CEO kept clicking was the old verification email from the 17:39:51 registration sitting in spam.

**Root cause (Problem B — unknown email):** still undetermined. Options are (a) the Neon DB has zero user rows (user wiped somehow between 17:39 creation and now), or (b) the stored email is genuinely different from `comcgee89@gmail.com` despite what the CEO is typing. Sprint 595 instruments this so the NEXT failure answers the question.

**Changes:**
- [x] Frontend: `VerificationContext.verifyEmail` now POSTs `'/auth/verify-email'` with `{token}` in the JSON body. Retains the `encodeURIComponent`-free path since tokens are already URL-safe hex.
- [x] Frontend test: `src/__tests__/VerificationContext.test.tsx` — new file with 3 tests asserting (i) endpoint has no query string, (ii) body contains `{token}`, (iii) success/failure paths propagate correctly. Regression guard for this specific bug.
- [x] Backend: `/auth/forgot-password` now logs `total_users=N` when the lookup fails. Zero PII leaked (we do not log other addresses). Temporary instrumentation — to be removed once the root cause is understood. Docstring notes the Sprint tie-in so it's clear this is not permanent.
- [x] Backend: `scripts/set_superadmin.py` switches from raw `User.email == args.email` to `get_user_by_email(db, args.email)` so the CLI respects the Sprint 594 case-insensitive lookup. Also prints `total_users=N` on failure so a Render Shell session can diagnose from the other direction.

**Review:**
- All 40 backend auth/password-reset tests green (`test_auth_routes_api.py` + `test_password_reset.py`)
- New `VerificationContext.test.tsx` — 3/3 pass
- Deploy sequence: push → Vercel auto-deploys frontend → Render auto-deploys backend → CEO retries forgot-password → Render logs expose `total_users` → we know whether the DB is empty or the email is mismatched → either re-register or dig into the stored email

### Sprint 594: Email Case-Insensitivity Fix (Production Lockout Hotfix)
**Status:** COMPLETE
**Goal:** Resolve 2026-04-09 production login lockout caused by case-sensitive email lookup

**Incident:** CEO registered on prod Neon DB at 17:39 UTC, then could not log in or request a password reset at 21:24/22:07. Render logs showed `POST /auth/login 401` and `"Password reset requested for unknown email"`. Root cause: `create_user` stored the email exactly as typed (`auth.py:494`), but `forgot_password` did `get_user_by_email(db, body.email.strip().lower())` (`auth_routes.py:433`). A mixed-case registration created a user row that lowercased lookups could not find. Login's `get_user_by_email` was also case-sensitive, so the same row was unreachable from `/auth/login` when the email was typed in a different case. The Phase 1 smoke test masked the bug because it only verified `/auth/me` (which rides the cookie set by `/auth/register`) plus a deliberately-wrong-password `/auth/login → 401` — it never asserted that a correct-password `/auth/login` returns 200.

**Changes:**
- [x] Backend: new `normalize_email()` helper in `auth.py` — canonical form is `email.strip().lower()`
- [x] Backend: `get_user_by_email` normalizes input before the ORM filter (case-insensitive lookup at the application layer)
- [x] Backend: `create_user` stores the normalized email so existing-row checks are deterministic
- [x] Backend: `update_user_profile` normalizes both the duplicate-email check and the `pending_email` assignment
- [x] Backend: `/auth/forgot-password` drops its redundant inline `.strip().lower()` — normalization is centralized in `get_user_by_email`
- [x] Migration: `f7b3c91a04e2_normalize_user_emails_lowercase.py` backfills `users.email` and `users.pending_email` with `LOWER(TRIM(...))`; aborts with a clear error if case-collision duplicates exist rather than silently dropping rows
- [x] Smoke test: `scripts/smoke_test_render.sh` adds three new assertions — correct-password login → 200, wrong-password login → 401 (renamed 5b), mixed-case email login → 200 (regression guard)
- [x] Tests: `test_register_then_login_case_insensitive` covers mixed-case register → lowercase/alt-case/padded login → 200; `test_register_duplicate_differs_only_in_case` asserts case-only duplicates are rejected at registration

**Review:**
- No existing tests or fixtures needed to change: `make_user` (bypasses `create_user`) and the existing test emails are already lowercase
- Migration is idempotent: the `WHERE email <> LOWER(TRIM(email))` filter means re-running on an already-normalized table is a no-op
- Downgrade is a deliberate no-op: lowercasing is lossy and restoring original casing would require information we no longer have
- Backfill pre-check refuses to merge case-collision groups — operator must resolve manually. Production currently has one user (the CEO) so the collision branch is inert, but the guard protects future re-runs on a populated DB
- Deploy sequence: push → Render auto-deploys → Alembic runs in Dockerfile entrypoint (per Sprint 545) → CEO retries password reset → SendGrid email arrives → CEO sets new password → login succeeds

### Sprint 593: Share-Link Security Hardening + Documentation Integrity CI
**Status:** COMPLETE
**Goal:** Strengthen public share-link security and prevent documentation drift

**Changes:**
- [x] DB migration: `passcode_hash` (String(64)) + `single_use` (Boolean) columns on `export_shares`
- [x] Optional passcode protection: SHA-256 hashed passcode, 403 on wrong/missing passcode
- [x] Single-use mode: auto-revoke (`revoked_at = now`) after first successful download
- [x] Tier-configurable TTL: Professional 24h, Enterprise 48h (was 48h flat), `share_ttl_hours` entitlement
- [x] Security headers: `Cache-Control: no-store` on download responses (middleware provides `X-Content-Type-Options`, `Referrer-Policy`)
- [x] Download anomaly logging: per-download structured log (share_id, masked IP, UA hash), warning at >10 access_count
- [x] Frontend: passcode input + single-use checkbox in ShareExportModal, protection column in shares page
- [x] Doc consistency guard: `guards/doc_consistency_guard.py` — checks tier names, pricing, JWT expiry across docs vs code
- [x] CI job: `doc-consistency` gate in ci.yml (blocking)
- [x] Doc fixes: SECURITY_POLICY.md (JWT 30m→15m, Team/Org→Professional/Enterprise, TTL 48h→24-48h, 10 compensating controls)
- [x] Doc fixes: TERMS_OF_SERVICE.md (Solo limits 20→100/10→unlimited, Team/Org→Professional/Enterprise, seat pricing $80/$70→$65/$45 flat)
- [x] Tests: 25 backend (12 new: passcode, single-use, headers, TTL, anomaly), 20 frontend (6 new)

**Review:**
- Backward compatible: existing shares (passcode_hash=NULL, single_use=False) work unchanged
- Passcode brute-force mitigated by existing 20/min rate limit on download endpoint
- Single-use race condition: concurrent downloads both succeed, link revoked after first commit (acceptable for ephemeral links)
- Guard catches tier name drift, pricing drift, JWT expiry drift — stdlib only, no external deps

