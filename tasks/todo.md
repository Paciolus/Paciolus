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

### Sprint 588: Chrome QA Remediation (2026-03-26) — COMPLETE
- [x] Remove `version` field from `/health` endpoint response — prevents server version disclosure (information leakage)
- [x] Update `test_health_api.py` assertions to verify version is absent
- [x] Add `Cross-Origin-Opener-Policy: same-origin` header to backend `SecurityHeadersMiddleware`
- [x] Add `Cross-Origin-Opener-Policy: same-origin` header to frontend `next.config.js`
- [x] Add `X-Robots-Tag: noindex, nofollow` header for non-production deployments in `next.config.js`
- [x] Add `extra="forbid"` to `UserCreate` and `UserProfileUpdate` Pydantic models — reject unknown fields
- [x] Add `sanitize_name` field validator on `UserProfileUpdate` — strip HTML tags to prevent stored XSS
- [x] Add `\n` (newline) to CSV formula injection trigger set in `shared/helpers.py` (CWE-1236)
- [x] Expand `robots.txt` — Allow public pages (login, register, pricing, trust, privacy, terms); Disallow authenticated routes (workspace, admin, billing, export, forgot-password, verify-email)
- [x] Add `name` and `autoComplete` attributes to login page inputs (email + password)
- [x] Add `name` and `autoComplete` attributes to register page inputs (email + password + confirmPassword)
- [x] Fix CommandPalette SSR hydration mismatch — defer `localStorage` read to `useEffect` (React #418)
- [x] Add Vercel `NEXT_PUBLIC_API_URL` env var action item to `ceo-actions.md`
- **Review:** 8 security fixes, 2 SEO/crawl improvements, 3 UX form fixes, 1 SSR hydration fix, 1 CEO action. Files: 4 backend, 1 test, 5 frontend, 1 task doc.

### Sprint 587: Dependency Sentinel Remediation (2026-03-26) — COMPLETE
- [x] Bump `cryptography` 46.0.5 → 46.0.6 (security patch, CVE-2026-26007 pin update)
- [x] Bump `stripe` 14.4.1 → 15.0.0 (major — StripeObject no longer dict subclass; no impact on our usage)
- [x] Bump `starlette` 0.52.1 → 1.0.0 (major — FastAPI 0.135.2 already compatible; removed deprecations don't affect us)
- [x] Bump `sentry-sdk` 2.55.0 → 2.56.0
- [x] Bump 6 transitive deps: anyio 4.13.0, chardet 7.3.0, redis 7.4.0, requests 2.33.0, tomli 2.4.1
- [x] Fix 3 npm audit vulnerabilities: flatted (prototype pollution), picomatch (ReDoS), yaml (stack overflow)
- [x] Deferred: pdfminer.six (locked by pdfplumber==0.11.9), pydantic_core (locked by pydantic==2.12.5), typescript 6.0 (blocked by @typescript-eslint <6.0.0 peer dep)
- **Review:** 8 packages upgraded (2 major, 1 security patch, 5 minor), 3 npm audit vulns fixed. Backend 7121 tests, frontend 1745 tests, build all pass. 3 deps deferred (parent/toolchain-locked).

### Sprint 586: Nightly Report Remediation (2026-03-25) — COMPLETE
- [x] Fix policy guard false positive — exclude `client_manager.py` from `no_hard_delete` rule (Sprint 580 import of `ToolRun` for read-only query triggered false positive on unrelated `db.delete(client)`)
- [x] Fix XSS regression test — update assertion to match `sanitize_name` HTML-stripping behavior (defense-in-depth pentest fix)
- [x] Fix BUG-001 — add prefix variation fallback to `get_tb_suggested_procedure()` in `tb_diagnostic_constants.py` (matched existing fix in `follow_up_procedures.py`)
- [x] Fix BUG-006 — track `missing_names`/`missing_balances` in `StreamingAuditor`, pass through both pipeline paths to `compute_population_profile()`, remove cosmetic domain micro-offset from `data_quality.py`
- [x] Update nightly report BUG_KEYWORDS for BUG-001 and BUG-006 to match actual anti-patterns
- **Review:** 2 test failures fixed, 2 confirmed bugs fixed. 152 module tests + 73 pipeline tests + frontend build all pass.

