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
> Sprints 592–595 archived to `tasks/archive/sprints-592-595-details.md`.

### Sprint 596: UnverifiedCTA — Explicit Verification Prompt on All Tool Pages
**Status:** COMPLETE
**Goal:** Replace silent content gating with an explicit "Verify Your Email" card so unverified users understand why tool pages appear blank

**Problem:** 11 of 12 tool pages hid their entire UI behind `isAuthenticated && isVerified` with no explanation. Authenticated users who hadn't verified their email saw only the page title and a blank area below — no upload zone, no controls, no message. The `VerificationBanner` in the top shell existed but was a small dismissible bar, easily overlooked. Users assumed the app was broken.

**Changes:**
- [x] New `UnverifiedCTA` component (`frontend/src/components/shared/UnverifiedCTA.tsx`) — email icon, "Verify Your Email" heading, explanation text, pointer to the resend banner. Oat & Obsidian tokens, motion entrance animation. Parallel to `GuestCTA`.
- [x] Exported from `frontend/src/components/shared/index.ts`
- [x] Added `{isAuthenticated && !isVerified && (<UnverifiedCTA />)}` block to all 11 tool pages: trial-balance, ap-testing, ar-aging, bank-rec, fixed-assets, inventory-testing, journal-entry-testing, payroll-testing, revenue-testing, statistical-sampling, three-way-match
- [x] Multi-period page left untouched — already has its own inline "Verify Your Email" card (Pattern B)
- [x] `npm run build` passes — all 12 tool pages compile cleanly

**Review:**
- Consistent three-state UX across all tools: unauthenticated → GuestCTA, unverified → UnverifiedCTA, verified → full tool UI
- The `VerificationBanner` in `AuthenticatedShell` still renders above the CTA for redundancy (resend button lives there)
- No backend changes; purely frontend UX improvement

