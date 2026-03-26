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

### Sprint 591: Dunning & Failed Payment Workflow (2026-03-26) — COMPLETE
- [x] Create `dunning_model.py` — DunningEpisode table with 6 states, composite indexes
- [x] Create Alembic migration `591a_add_dunning_episodes.py`
- [x] Add 5 dunning email functions to `email_service.py` (first failure, second, final notice, suspended, recovered) with Oat & Obsidian HTML templates
- [x] Create `billing/dunning_engine.py` — state machine engine (handle_payment_failed, handle_payment_recovered, process_grace_period_expirations, resolve_manually)
- [x] Integrate dunning into `webhook_handler.py` — invoice.payment_failed triggers state advance, invoice.paid resolves episodes
- [x] Add `_job_dunning_grace_period()` hourly task to `cleanup_scheduler.py` for grace period expiration
- [x] Add dunning metrics to `compute_churn_metrics()` (active episodes, at-risk MRR, recovered, lost, recovery rate)
- [x] Add `DunningMetrics` schema to `internal_metrics_schemas.py`
- [x] Add dunning info to admin customer detail (`_get_dunning_info()` in `admin_customers.py`)
- [x] Add `POST /internal/admin/dunning/{episode_id}/resolve` endpoint for manual resolution
- [x] Register DunningEpisode in `conftest.py` and `alembic/env.py`
- [x] Create `tests/test_dunning.py` — 21 tests (full lifecycle, early recovery, idempotency, grace period, manual resolve, metrics, email triggers, new episode after resolution)
- [x] Verification: 99 tests pass (21 dunning + 32 admin + 41 metrics + 5 analytics), no regressions
- **Review:** Automated dunning state machine (FIRST→SECOND→THIRD→GRACE→CANCELED) with idempotent webhook-driven transitions, 5 branded email templates, hourly grace period expiration job, dunning metrics in churn API, manual admin resolve. Stripe Smart Retries handle actual payment retries — we only track state + communicate. Files: 3 new (model, engine, tests), 7 modified (webhook, email, scheduler, metrics, schemas, admin, conftest).

### Sprint 590: Internal Admin Console — Superadmin CRM (2026-03-26) — COMPLETE
- [x] Add `is_superadmin` boolean to User model (default false, CLI-only grant)
- [x] Create `admin_audit_model.py` — AdminAuditLog model with 8 action types
- [x] Create Alembic migration `590a_add_superadmin_and_admin_audit_log.py`
- [x] Add `require_superadmin` auth dependency to `auth.py`
- [x] Add `create_impersonation_token()` — time-boxed JWT with `imp`/`imp_by` claims
- [x] Create `billing/admin_customers.py` — service layer (customer list/detail, 6 admin actions, audit log query)
- [x] Create `schemas/admin_customer_schemas.py` — 14 Pydantic models (requests + responses)
- [x] Create `routes/internal_admin.py` — 10 endpoints under `/internal/admin/` (customers CRUD, 6 actions, impersonation, audit log)
- [x] Add `ImpersonationMiddleware` to `security_middleware.py` — blocks mutations on `imp` JWT tokens (403)
- [x] Register middleware in `main.py`
- [x] Create `scripts/set_superadmin.py` — CLI for granting/revoking superadmin
- [x] Create `tests/test_internal_admin.py` — 32 tests (auth, CRUD, actions, impersonation, audit log, service layer)
- [x] Create frontend: types, hook, 3 pages (customer list, customer detail, audit log), impersonation banner
- [x] Register `ImpersonationBanner` in providers.tsx
- [x] Verification: 73 backend tests pass (32 admin + 41 metrics), frontend build passes
- **Review:** Full superadmin CRM — customer list with search/filter/pagination, customer detail with billing/usage/activity/members, 6 admin actions (plan override, trial extension, credit, refund, cancel, impersonation) all with audit trail, impersonation read-only enforcement via middleware, admin audit log with filtering. Backend: 7 new files, 5 modified. Frontend: 7 new files, 1 modified.

### Sprint 589: Internal Metrics API — Founder Ops Dashboard (2026-03-26) — COMPLETE
- [x] Create `billing/internal_metrics.py` — MRR/ARR computation engine with 4 metric functions
- [x] Create `schemas/internal_metrics_schemas.py` — Pydantic response models (Revenue, Churn, TrialFunnel, History)
- [x] Create `routes/internal_metrics.py` — 4 GET endpoints under `/internal/metrics/` with owner-only auth
- [x] Register router in `routes/__init__.py`
- [x] Create `tests/test_internal_metrics.py` — 41 tests (auth, MRR calc, churn rates, trial funnel, revenue history, edge cases)
- [x] Verification: 46 billing tests pass (41 new + 5 existing), no regressions
- **Review:** 4 new endpoints (revenue, churn, trial-funnel, revenue/history), read-only, owner-gated. Service layer computes MRR from Subscription table + 30-day movements from BillingEvent log. Files: 3 new (service, schemas, route), 1 modified (routes/__init__.py), 1 test file (41 tests).

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

