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
| `PeriodFileDropZone.tsx` deferred type migration | TODO open for 3+ consecutive audit cycles. Benign incomplete type migration, not a hack. Revisit when touching the upload surface for another reason. | Project-Auditor Audit 35 (2026-04-14) |

---

## Active Phase

> **Launch-readiness Council Review — 2026-04-16.** 8-agent consensus: code is launch-ready; gating path is CEO calendar (Phase 3 validation → Phase 4.1 Stripe cutover → legal sign-off). **Recommended path: ship on ~3-week ETA** with two engineering amendments — Sprint 673 below removes the 2026-05-09 TLS-override fuse before it collides with launch week, and Guardian's 5-item production-behavior checklist runs in parallel with Phase 3/4.1 (tracked in [`ceo-actions.md`](ceo-actions.md) "This Week's Action Map"). Full verdict tradeoff map in conversation transcript.

> **Prior sprint detail:** All pre-Sprint-673 work archived under `tasks/archive/`. See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for the era index and archive file pointers.

> **CEO remediation brief 2026-04-15** — Sprints 665–671 cleared the blocking TB-intake issues from the six-file test sweep. Sprints 668–671 remaining pending items archived alongside — no longer blocking launch.

---

### Sprint 674: QA Warden pytest timeout raised 600s → 1200s
**Status:** COMPLETE
**Source:** Nightly audit review 2026-04-18 — Sprint Shepherd / QA Warden trend
**Why now:** 2026-04-17 overnight RED because `qa_warden.py` backend pytest subprocess hit its 600s hard timeout at 601.8s. On 2026-04-18 the suite ran in 581.2s — **19s of margin**. Test count grew 7,405 (04-15) → 7,804 (04-18); next sprint or two reliably re-triggers the timeout.
**File:** `scripts/overnight/agents/qa_warden.py:39, 69`
**Changes:**
- [x] Raise `subprocess.run` timeout from 600 → 1200 in `_run_backend_tests` (both the json-report path and the fallback path)
- [x] No changes to `_run_frontend_tests` — ran 46.3s of 300s budget, ample headroom
- [x] No migration to pytest-xdist — rejected to avoid DB-fixture parallelism risk (single-worker guarantees in current fixtures); revisit if 1200s ceiling approached again

**Review:**
- Rationale for 1200s (vs. 900s or 1800s): 1200s gives ~2× current runtime — enough to absorb ~3,000 new tests at current pace without requiring another bump; not so generous that a genuine regression (e.g. a hanging test) burns the whole nightly window before surfacing. Next agent (`report_auditor`) sleeps until 02:15, so even a full 1200s wait still completes ahead of schedule.
- Did NOT touch pytest config — keeps the fix isolated to the nightly driver so regular `pytest` and CI behavior are unchanged.

---

### Sprint 675: Security-relevant dependency bump sweep
**Status:** PENDING
**Source:** Nightly audit review 2026-04-18 — Dependency Sentinel YELLOW (stable across 04-15, 04-17, 04-18)
**Why now:** Five security-relevant updates have been pending unaddressed across three consecutive nightlies. Bundling into one PR is lower overhead than repeated single-package hotfixes and keeps Dependency Sentinel out of chronic YELLOW before launch.
**Changes:**
- [ ] Backend: `cryptography` 46.0.6 → 46.0.7 (patch), `fastapi` 0.135.2 → 0.136.0 (minor), `SQLAlchemy` 2.0.48 → 2.0.49 (patch), `stripe` 15.0.0 → 15.0.1 (patch), `pydantic` 2.12.5 → 2.13.2 (minor)
- [ ] Frontend: `next` 16.2.3 → 16.2.4 (patch)
- [ ] Run full backend + frontend test suite; pydantic 2.12→2.13 is the only non-trivial one (schema-validation semantics) — watch for any Pydantic API deprecation warnings
- [ ] Verify `npm run build` passes post-next bump (CSP proxy.ts, dynamic rendering intact)
- [ ] Defer majors (`rich` 14→15, `tzdata` 2025→2026) to a separate sprint if needed — not security-blocking

---

### Sprint 676: Coverage fill for 0% production-path files
**Status:** PENDING
**Source:** Nightly audit review 2026-04-18 — Coverage Sentinel (stable green 92.24% but persistent 0% files)
**Why now:** Three production-path files show 0% or near-0% coverage and have been stable in the nightly "top uncovered" list across all three audits. Not regressing, but a real test gap — especially `billing/webhook_handler.py` (Stripe webhook is business-critical) and `services/organization_service.py` (org entity lifecycle).
**Scope (targeted, not a sweep):**
- [ ] `services/organization_service.py` — **0%** / 180 statements — add service-level tests covering create / update / delete / member add-remove paths
- [ ] `export/serializers/csv.py` — **0%** / 158 statements — round-trip tests for CSV export of each tool's result envelope
- [ ] `billing/webhook_handler.py` — **55.1%** / 180 missing — target the 180 uncovered lines (failure paths for signature mismatch, unknown event types, idempotency replay)
- [ ] Explicitly defer: `excel_generator.py`, `leadsheet_generator.py`, `workbook_inspector.py` — older utilities, bigger lift, lower priority than billing/org
- [ ] Explicitly defer: `generate_sample_reports.py` — one-off dev script, not production path
- [ ] Target: lift overall backend coverage 92.24% → ≥92.6% (adds ~300 statements covered)

---

### Sprint 611: ExportShare Object Store Migration
**Status:** PENDING — CEO-gated (bucket provision)
**Source:** Critic — DB bloat risk
**File:** `backend/export_share_model.py:43`
**Problem:** `export_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)` stores up to 50 MB per shared export in primary Neon Postgres. 20 concurrent shares = 1 GB of binary row storage; Neon Launch tier cap is 10 GB. Also bloats every DB backup — unclear whether zero-storage policy permits this.
**Changes:**
- [ ] Provision object store bucket (R2 or S3) with pre-signed URL pattern — CEO owns this, tracked in [`ceo-actions.md`](ceo-actions.md) "Backlog Blockers"
- [ ] Store `export_data` in bucket keyed by `share_token_hash`; DB row keeps metadata + object key only
- [ ] Extend cleanup scheduler to delete object when share revoked/expired
- [ ] Backfill migration for existing shares

---

### Sprint 673: Remove DB_TLS_OVERRIDE via pooler-aware pg_stat_ssl skip
**Status:** CODE-COMPLETE — pending deploy + CEO env-var removal
**Source:** Council Review 2026-04-16 — Critic (time-fused architectural debt) + Executor (front-run launch week)
**Why now:** `DB_TLS_OVERRIDE=NEON-POOLER-PGSSL-BLINDSPOT:2026-05-09` expires in 23 days. Without the proper fix landed first, the override must either be renewed (kicks the can) or allowed to expire (hard-fails production startup during Phase 4 launch window). Fixing before Phase 4 removes one ticking clock from launch week.
**File:** `backend/database.py`
**Problem:** Production startup runs a `pg_stat_ssl` check to confirm the DB connection is encrypted. Neon's pooled endpoint (`-pooler` hostname) is a transparent connection pooler — the underlying connection IS TLS-encrypted, but `pg_stat_ssl` reports the pooler-to-backend hop, not the client-to-pooler hop. The check therefore returns `ssl=false` on a correctly encrypted connection, forcing the current override.
**Changes:**
- [x] Detect `-pooler` in `DATABASE_URL` hostname via new `_is_pooled_hostname()` helper (`backend/database.py`)
- [x] On pooled hostnames: skip the `pg_stat_ssl` assertion, log `tls=pooler-skip`, emit `db_tls_pooler_skip` secure event (sslmode still enforced in config.py)
- [x] On direct hostnames: retain the assertion (Neon direct endpoint, RDS, local postgres all continue to verify)
- [x] Unit tests cover all branches: pooler host with ssl_active=False doesn't crash, direct host with ssl_active=True still logs `db_tls_verified`, helper recognises pooler suffix (18/18 tests pass)
- [ ] **CEO deploy step:** Deploy; verify Render startup logs show `tls=pooler-skip` and no override warning
- [ ] **CEO env-var step:** Remove `DB_TLS_OVERRIDE` from Render env vars once startup is confirmed green
- [x] `DB_TLS_OVERRIDE` config path kept intact — it's a general break-glass used by both the `pg_stat_ssl` check AND the `sslmode` connection-string check in `config.py`; not pooler-specific, so deletion would lose a legitimate escape hatch.

**Review:**
- New helper `_is_pooled_hostname()` lives alongside imports in `backend/database.py`; it's a parse-and-substring test with no DB coupling (trivially unit-testable).
- The pooled branch short-circuits BEFORE the four-way `ssl_active / DB_TLS_OVERRIDE_VALID / DB_TLS_REQUIRED / else` logic, so `DB_TLS_REQUIRED=true` + pooler host no longer crashes startup.
- Secure event `db_tls_pooler_skip` added — distinct from `db_tls_verified` and `db_tls_override` so log audits can tell "TLS is actually on, just invisible" apart from "TLS is off, break-glass approved".
- Existing 15 TLS tests still pass unchanged; 3 new tests added (pooler skip, direct still runs, helper unit).

---
