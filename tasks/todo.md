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

- [2026-04-16] 22e16dc: backlog hygiene — Sprint 611 R2/S3 bucket added to ceo-actions Backlog Blockers; Sprint 672 placeholder for Loan Amortization XLSX/PDF export (Sprint 625 deferred work)
- [2026-04-14] a32f566: hallucination audit hotfix — /auth/refresh handler 401→403 for X-Requested-With mismatch (aligns with CSRF middleware); added .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md
- [2026-04-07] 73aaa51: dependency patch — uvicorn 0.44.0, python-multipart 0.0.24 (nightly report remediation)
- [2026-04-06] 39791ec: secret domain separation — AUDIT_CHAIN_SECRET_KEY independent from JWT, backward-compat verification fallback, TLS evidence signing updated
- [2026-04-04] 29f768e: dependency upgrades — 14 packages updated, 3 security-relevant (fastapi 0.135.3, SQLAlchemy 2.0.49, stripe 15.0.1), tzdata 2026.1, uvicorn 0.43.0, pillow 12.2.0, next watchlist patch
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
> Sprints 596–599 archived to `tasks/archive/sprints-596-599-details.md`.
> Sprints 600–603 archived to `tasks/archive/sprints-600-603-details.md`.
> Sprints 604–607 archived to `tasks/archive/sprints-604-607-details.md`.
> Sprints 608–609 archived to `tasks/archive/sprints-608-609-details.md`.
> Sprints 665–667 archived to `tasks/archive/sprints-665-667-details.md` (CEO remediation brief v6 — harness, intake hardening, risk scoring/conclusion).
> Sprints 668–671 archived to `tasks/archive/sprints-668-671-details.md` (materiality coverage, multi-column TB, account-type-aware diagnostics, DOCX/PDF ingestion).
> Sprints 610, 612–615 archived to `tasks/archive/sprints-610-615-details.md`.
> Sprints 616–620 archived to `tasks/archive/sprints-616-620-details.md`.
> Sprints 621–625 archived to `tasks/archive/sprints-621-625-details.md`.
> Sprints 626–630 archived to `tasks/archive/sprints-626-630-details.md`.
> Sprints 631–635 archived to `tasks/archive/sprints-631-635-details.md`.
> Sprints 636–640 archived to `tasks/archive/sprints-636-640-details.md`.
> Sprints 641–645 archived to `tasks/archive/sprints-641-645-details.md`.
> Sprints 646–650 archived to `tasks/archive/sprints-646-650-details.md`.
> Sprints 651–655 archived to `tasks/archive/sprints-651-655-details.md`.
> Sprints 656–660 archived to `tasks/archive/sprints-656-660-details.md`.
> Sprints 661–664 archived to `tasks/archive/sprints-661-664-details.md`.
> Sprint 672 archived to `tasks/archive/sprint-672-details.md`.

> **Multi-agent review 2026-04-14 — Sprints 600–664 seeded from 8 parallel agent reviews (Critic, Designer, Executor, Guardian, Scout, Accounting Auditor, Project Auditor, Future-State Consultant). Each sprint cites its originating agent. Ordered by severity, not discovery order.**

> **CEO remediation brief 2026-04-15 — Sprints 665–671 inserted ahead of the seeded 610–664 backlog. Source: six-file TB test sweep (`tests/evaluatingfiles/`) surfacing 16 issues across intake, scoring, column detection, and multi-format handling. Issues 5 (BLOCKING), 9, 2, 7, 3, 4, 12 cleared by Sprints 665–667; Sprints 668–671 remain pending.**

---



### Sprint 611: ExportShare Object Store Migration
**Status:** PENDING
**Source:** Critic — DB bloat risk
**File:** `backend/export_share_model.py:43`
**Problem:** `export_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)` stores up to 50 MB per shared export in primary Neon Postgres. 20 concurrent shares = 1 GB of binary row storage; Neon Launch tier cap is 10 GB. Also bloats every DB backup — unclear whether zero-storage policy permits this.
**Changes:**
- [ ] Provision object store bucket (R2 or S3) with pre-signed URL pattern
- [ ] Store `export_data` in bucket keyed by `share_token_hash`; DB row keeps metadata + object key only
- [ ] Extend cleanup scheduler to delete object when share revoked/expired
- [ ] Backfill migration for existing shares

---



<!-- Sprints 641–645 archived to tasks/archive/sprints-641-645-details.md -->

---

<!-- Sprints 646–650 archived to tasks/archive/sprints-646-650-details.md -->

---

<!-- Sprints 651–655 archived to tasks/archive/sprints-651-655-details.md -->

---

<!-- Sprints 656–660 archived to tasks/archive/sprints-656-660-details.md -->

---

<!-- Sprints 661–664 archived to tasks/archive/sprints-661-664-details.md -->

<!-- Sprint 672 archived to tasks/archive/sprint-672-details.md -->

---
