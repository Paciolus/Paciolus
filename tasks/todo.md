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

---

## Active Phase
> Sprints 478–531 archived to `tasks/archive/sprints-478-531-details.md` (consolidated).
> Sprints 532–561 archived to `tasks/archive/sprints-532-561-details.md` (consolidated).
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.
> FIX-3–8B, AUDIT-09–10 archived to `tasks/archive/fix-3-8b-audit-09-10-details.md`.
> Sprints 563–569, CI-FIX archived to `tasks/archive/sprints-563-569-details.md`.
> Sprints 570–571 archived to `tasks/archive/sprints-570-571-details.md`.

### Sprint 572: Password Reset Flow
> Source: Launch Readiness Review item B-15 / Deferred NEW-015

#### Backend
- [x] `PasswordResetToken` model (SHA-256 hashed, 1-hour expiry, single-use)
- [x] `POST /auth/forgot-password` — rate-limited, always returns 200 (prevents enumeration)
- [x] `POST /auth/reset-password` — validates token, sets new password, revokes all sessions, clears lockout
- [x] Password reset email template (HTML + plaintext, Oat & Obsidian branding)
- [x] `generate_password_reset_token()` + `send_password_reset_email()` in email_service.py
- [x] CSRF exemption for both endpoints (pre-auth, no CSRF token available)

#### Frontend
- [x] `/forgot-password` page — email form, success screen (always shown to prevent enumeration)
- [x] `/reset-password` page — new password form with complexity validation, token capture + URL stripping
- [x] Login page "Forgot password?" link → `/forgot-password`

#### Tests
- [x] 12 backend tests: forgot-password (4), reset-password (5), CSRF exemption (2), lockout reset (1)
- [x] 10 frontend tests: ForgotPasswordPage (5), ResetPasswordPage (5)
- [x] Updated CSRF exemption snapshot test with 2 new paths

- **Tests:** 7,108 backend (12 new), 1,735 frontend (10 new) — 0 failures
- **Verification:** npm run build PASS, npm test PASS (1,735/1,735), backend tests PASS (106/106 auth+csrf+reset)
- **Status:** COMPLETE

