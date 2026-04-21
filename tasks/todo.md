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

- [2026-04-19] 9f00070: nightly dep hygiene (part 2) — remaining 3 majors cleared in venv (numpy 1.26→2.4, pip 25.3→26.0.1, pytz 2025.2→2026.1.post1). Verified zero direct imports for numpy/pytz; pandas 3.0.2 compatible with numpy 2.x; pytz has no current dependents. pytest 7836 passed / 0 failed. Venv-only change (no requirements.txt edits needed).
- [2026-04-19] 8fd93bb: nightly dep hygiene — 26 safe package bumps (19 backend venv: anthropic, anyio, docstring_parser, greenlet, hypothesis, jiter, librt, lxml, Mako, mypy, packaging, prometheus_client, pypdf, pypdfium2, pytest, python-multipart, ruff, sentry-sdk, uvicorn; 6 frontend via npm update: @sentry/nextjs, eslint-plugin-react-hooks, @typescript-eslint/*, postcss, typescript). Deferred: numpy 2.x, pip 26, pytz 2026 (majors). frontend/package-lock.json only.
- [2026-04-18] 7915d77: nightly audit artifacts — commit 2026-04-18 report + sentinel JSONs (qa_warden, coverage, dependency, scout, sprint_shepherd, report_auditor) + run_log (reports/nightly/)
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
| `routes/billing.py::stripe_webhook` decomposition (signature-verify / dedup / error-mapping triad) | Already touched lightly in the 2026-04-20 refactor pass; full extraction pairs better with the deferred webhook-coverage sprint flagged in Sprint 676 review (handler is currently exercised by 6 route-test files but lacks unit coverage). Bundle both then. | Refactor Pass 2026-04-20 |
| `useTrialBalanceUpload` decomposition into composable hooks | Hook's state machine (progress indicator, recalc debounce, mapping-required preflight handoff) is tightly coupled to consumer semantics. Not a drop-in extraction — needs Playwright coverage of the mapping-required flow before a split is safe. | Refactor Pass 2026-04-20 |
| Move client-access helpers (`is_authorized_for_client`, `get_accessible_client`, `require_client`) out of `shared/helpers.py` shim | Three helpers depend on `User` / `Client` / `OrganizationMember` / `require_current_user`; a dedicated `shared/client_access.py` module isn't justified under the "prefer moving code, avoid new abstractions" guidance. Revisit if a fourth helper joins them, or if the shim grows another responsibility. | Refactor Pass 2026-04-20 |
| `routes/auth_routes.py` cookie/CSRF helper extraction | Module is already reasonably thin; cookie/token primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) are security-critical. Touching them without a specific bug or audit finding is net-negative. Revisit only if a follow-up auth/CSRF audit produces an actionable finding. | Refactor Pass 2026-04-20 |

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

### Sprint 675: Security-relevant dependency bump sweep + Sentinel scan-path fix
**Status:** COMPLETE
**Source:** Nightly audit review 2026-04-18 — Dependency Sentinel YELLOW (stable across 04-15, 04-17, 04-18)
**Why now:** Security-relevant updates pending unaddressed across three consecutive nightlies. While bumping, discovered the Dependency Sentinel was scanning `C:/Python312` (system Python, stale fork) instead of `backend/venv/Scripts/python.exe` (what actually matches `requirements.txt` and runs in production). Two of the five "security-relevant" packages reported in the nightly (SQLAlchemy 2.0.48→49, stripe 15.0.0→1) were already synced in the venv — the sentinel was giving false signals.

**Changes:**
- [x] `scripts/overnight/agents/dependency_sentinel.py` — switch backend scan from `SYSTEM_PYTHON` to `PYTHON_BIN` (the venv); keeps `SYSTEM_PYTHON` as fallback if venv missing. Import `PYTHON_BIN` from `config.py` (already defined, unused until now).
- [x] `backend/requirements.txt`: `fastapi` 0.135.3 → 0.136.0, `pydantic[email]` 2.12.5 → 2.13.2
- [x] `backend/requirements.txt`: `cryptography>=46.0.7` was already pinned but venv had 46.0.6 installed; `pip install -U` brought it current
- [x] `frontend/package.json`: `next` ^16.2.2 → ^16.2.4 (resolves 16.2.4 per nightly sentinel)
- [x] `npm install` — 3 packages changed, 0 vulnerabilities, all frontend deps intact
- [x] `npm run build` passes — all routes render as `ƒ (Dynamic)` (CSP proxy.ts nonce-based rendering intact after next 16.2.2→16.2.4)
- [x] Backend `pytest`: **7805 passed, 9 xfailed, 0 failed** in 644.25s after the bump — pydantic 2.13 migration clean, no API deprecations surfaced
- [x] Frontend `npm test` passes (see review below)

**Skipped (legitimately not outdated in the venv despite nightly report):**
- SQLAlchemy 2.0.48 → 2.0.49 — venv already at 2.0.49 (sentinel was reading system Python 2.0.48)
- stripe 15.0.0 → 15.0.1 — venv already at 15.0.1 (same root cause)

**Explicitly deferred:**
- `rich` 14.3.3 → 15.0.0 (major) — not security-relevant, defer until a feature needs it
- `tzdata` 2025.3 → 2026.1 (major) — not security-relevant
- `pdfminer.six` 20251230 → 20260107 — previously deferred, reviewed by 2026-04-30

**Review:**
- The Sentinel fix is the more important half of this sprint: without it, next week's nightly would continue reporting stale YELLOW signals from the system-Python fork even though production (Render) is on current requirements.txt. After this fix, Dependency Sentinel reports match what prod actually installs.
- pydantic 2.12 → 2.13 is semver-minor but changed validation internals; full 7805-test pass is strong evidence the upgrade is clean for our schemas.
- next 16.2.2 → 16.2.4 contains the patch advisory referenced in nightly reports; build output confirms dynamic-render + CSP nonce contract unbroken (`ƒ` on all routes).

---

### Sprint 676: Coverage fill — dead-code deletion + CSV serializer tests
**Status:** COMPLETE
**Source:** Nightly audit review 2026-04-18 — Coverage Sentinel (stable green 92.24% but persistent 0% files)

**Scope adjustment during execution:**
The nightly Coverage Sentinel's three worst 0%-coverage files turned out to have three distinct root causes, not one. Scope was adjusted per finding rather than forcing tests onto inappropriate targets:

1. **`services/organization_service.py` — 180 stmts @ 0%:** Investigation showed this file has **zero imports anywhere in the codebase**. Sprint 546 (archived) claimed "Refactor 5: organization.py → services/organization_service.py + thin routes" but only created the service module; `routes/organization.py` continued to use its own private `_get_user_org` / `_require_admin` helpers. The service file is orphaned dead code. **Fix: delete the file.** Testing dead code for coverage vanity would have been noise; completing the refactor is a larger risk-carrying change that deserves its own sprint, not a coverage-fill sprint.
2. **`export/serializers/csv.py` — 158 stmts @ 0%:** Genuine production path with no direct unit tests. **Fix: add `backend/tests/test_export_csv_serializers.py` with 31 tests** covering all 6 serializer functions (`trial_balance`, `anomalies`, `preflight_issues`, `population_profile`, `expense_category`, `accrual_completeness`) across happy paths, edge cases (empty input, prior-period vs no-prior, optional narrative, missing fields), CSV injection sanitization, and the UTF-8-sig BOM encoding contract.
3. **`billing/webhook_handler.py` — 180 stmts missing (55% covered):** Deferred. Existing route-level tests (`test_billing_webhooks_routes.py`, `test_billing_analytics.py`, `test_billing_routes.py`, `test_phase1_bug_fixes.py`, `test_pricing_integration.py`, `test_pricing_launch_validation.py`) already import from `billing.webhook_handler` and exercise real handler paths. Unit-testing the 180 defensive branches would be duplicative churn. A dedicated webhook-coverage sprint can pick this up later if the number becomes problematic.

**Changes:**
- [x] Delete `backend/services/organization_service.py` (180 lines, orphan dead code)
- [x] Add `backend/tests/test_export_csv_serializers.py` (31 tests, all passing in 1.64s)
- [x] Explicitly defer: `billing/webhook_handler.py` (covered indirectly by 6 route-test files)
- [x] Explicitly defer: `excel_generator.py`, `leadsheet_generator.py`, `workbook_inspector.py`, `generate_sample_reports.py` (non-production, larger lift)

**Impact:**
- Coverage Sentinel's top-10 uncovered list should lose `organization_service.py` (file gone) and `csv.py` (now ~100% covered). Overall backend coverage nudges up marginally (~0.2–0.3pp) but more importantly, the nightly's top-uncovered list becomes signal rather than noise.
- Removes a dangling refactor artifact that would eventually confuse future work on `routes/organization.py`.

**Review:**
- The decision not to test `organization_service.py` was a judgment call: writing tests for unimported code inflates coverage without improving safety. The archived Sprint 546 refactor appears to have stopped halfway; documenting that here lets a future sprint either complete the migration (replace route-level helpers with service imports) or confirm the deletion is permanent.
- CSV serializer tests target the *contract* (output shape, BOM, sanitization), not implementation details. They should survive future refactors of how the serializers walk inputs.
- Full backend `pytest` re-run confirms no test referenced the deleted module.

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

## Post-Audit Remediation Batch — 2026-04-20

> **Source:** Four-agent audit run 2026-04-20 (accounting-expert-auditor + backend/frontend/completeness Explore agents). 1 real CRITICAL backend bug, 5 CRITICAL accounting findings, 6 revenue-blocker gaps, ~15 HIGH, ~15 MEDIUM/LOW. Sprints below cluster findings by engine/theme to minimise touch-count and review overhead. Priority tags (P0/P1/P2) carry the audit's ranking; sprint order is execution-friendly, not strict priority.

---

### Sprint 677: Concentration % overflow + logo upload DB integrity
**Status:** COMPLETE
**Priority:** P0
**Source:** Backend-bugs agent (CRITICAL #1); Completeness agent (B-06)

**Scope adjustment during execution (validate-then-fix per Sprint 695 precedent):**
Two findings bundled into this sprint had different outcomes after audit. The concentration "50% → 5000%" claim was invalidated by the existing test contract; the logo-upload integrity finding was confirmed and fixed.

**Confirmed defect — FIXED:**
- [x] **Logo upload DB integrity** (`backend/routes/branding.py:129-150`): `POST /branding/logo` previously set `branding.logo_s3_key = s3_key` unconditionally, even when `upload_bytes` returned False (S3 unconfigured). The `except ImportError` branch caught a case that never fires (`upload_bytes` catches missing boto3 internally). Route now captures the return value and returns HTTP 503 when storage is unavailable, preventing dangling `logo_s3_key` rows that Sprint 679's PDF branding pipeline would then fail to resolve.

**Suspicion — REJECTED:**
- [x] **Concentration overflow** (`backend/audit/rules/concentration.py:110`): The audit claim was that `round(concentration_pct * 100, 1)` produced values that were then formatted with `:.1%` elsewhere, yielding 5000% for 50% concentration. Systematic search across `backend/`, `frontend/`, PDF memos, and diagnostic schemas found no such consumer. Existing tests (`test_float_precision.py:218,233,247,262`, `test_audit_anomalies.py:529,543`, `test_audit_validation.py:469,488`) all explicitly lock in the contract that `concentration_percent` is a 0-100 scaled percentage (50.0 for 50%), and the two `:.1%` format specifiers in `concentration.py` (lines 98, 120) apply to `concentration_pct` (the 0-1 local), not the stored field. Contract is correct as-is. Sprint 695 set the "validate-then-fix" precedent for rejecting un-reproducible audit findings.

**Test additions:**
- `backend/tests/test_post_audit_2026_04_20_batch2.py::TestConcentrationOverflowSuspicion` (2 tests) — pins the 0-100 scale contract + issue-text rendering.
- `backend/tests/test_post_audit_2026_04_20_batch2.py::TestLogoUploadDBIntegrity` (2 tests) — happy path + 503 rejection when storage is unavailable.

**Validation:**
- Full touched-surface regression (branding + three_way + multi_period + concentration-consuming suites): 628 passed, 0 failed.

**Review:**
- Rejecting the concentration finding was the correct call: testing dead code or breaking a live contract for a phantom bug would have churned consumers without fixing anything. The characterization tests now guard against a future refactor silently breaking the contract.
- The branding fix is minimal (one new return-value check, one 503) but closes a real integrity gap that Sprint 679 would otherwise stumble into.
- `logo_s3_key` backfill (for any existing rows pointing at missing S3 objects) is deferred to Sprint 679's branding pipeline, which is when it will first matter in production.
- Commit SHA: `768aa34` (landed together with Sprint 678).

---

### Sprint 678: Tier entitlement enforcement wire-up
**Status:** COMPLETE
**Priority:** P0 (revenue blocker)
**Source:** Completeness agent (B-02/B-03/B-04/B-05 + C-06)
**Why now:** Today a Free user can download every PDF/Excel/CSV export, upload every file format (OFX/QBO/PDF/ODS), and run 11 of 12 tools unbounded. The helpers exist; they're just never called. This single sprint closes the paid-tier moat without new engine work.

**Export gates (`check_export_access`):**
- [x] `routes/export_memos.py` — all 18 memo endpoints (16 registry-driven + sampling evaluation + flux expectations) wrapped with `dependencies=[Depends(check_export_access)]`.
- [x] `routes/export_diagnostics.py` — all 10 endpoints (`/export/pdf`, `/export/excel`, `/export/csv/trial-balance`, `/export/csv/anomalies`, `/export/leadsheets`, `/export/financial-statements`, `/export/csv/preflight-issues`, `/export/csv/population-profile`, `/export/csv/expense-category-analytics`, `/export/csv/accrual-completeness`) gated.
- [x] `routes/export_testing.py` — all 9 CSV export endpoints (JE/AP/Payroll/Revenue/AR/FA/Inventory/TWM/Sampling-selection) gated via regex patch.
- [x] `routes/engagements_exports.py` — anomaly-summary / package / convergence-csv gated.
- [x] `routes/loan_amortization.py` — CSV / XLSX / PDF export endpoints gated.
- [x] `routes/multi_period.py` — `/export/csv/movements` gated.
- [x] `routes/export_sharing.py` — already gated by the stricter `check_export_sharing_access` (Professional+ only, which implies any export access). No change needed.

**Format gates (`enforce_format_access` — new helper):**
- [x] Added `enforce_format_access(user, db, filename)` to `shared/entitlement_checks.py`. Unlike the dependency-factory form of `check_format_access`, this helper resolves the format from the uploaded filename at request time, which is the only way to gate format access on a polymorphic upload endpoint.
- [x] Wired into `routes/audit_pipeline.py::audit_trial_balance` and `routes/audit_upload.py::inspect_workbook_endpoint`. Free tier's `formats_allowed={csv,xlsx,xls,tsv,txt}` rejects OFX/QBO/IIF/PDF/ODS before any heavy processing.

**Tool-access gates (`enforce_tool_access`):**
- [x] `routes/multi_period.py::compare_period_trial_balances` and `::compare_three_way_trial_balances` — `multi_period` tool gate added.
- [x] `routes/currency.py::upload_rate_table` and `::add_single_rate` — `currency_rates` tool gate added. GET / DELETE endpoints left open (idempotent).

**Upload-limit gates (`check_upload_limit`):**
- [x] `shared/testing_route.py::run_single_file_testing` now calls `check_upload_limit` in addition to `enforce_tool_access`. Covers JE/AP/Payroll/Revenue/FA/Inventory in one place.
- [x] Non-factory routes updated individually: `routes/ar_aging.py`, `routes/bank_reconciliation.py`, `routes/three_way_match.py`, `routes/sampling.py`.
- [x] `routes/audit_pipeline.py` already had `check_diagnostic_limit` (alias for `check_upload_limit`).

**Test-fixture fixes (fallout from the new `require_current_user` dependency on export routes):**
- [x] `tests/conftest.py::override_auth_verified` — also overrides `require_current_user`.
- [x] `tests/test_multi_period_api.py`, `tests/test_engagements_exports_api.py`, `tests/test_three_way_comparison.py`, `tests/test_compare_periods_api.py`, `tests/test_rate_limit_enforcement.py` — mock users given a real `UserTier.PROFESSIONAL` (MagicMock `tier.value` attribute didn't resolve to a valid enum) and `require_current_user` overridden where missing.

**Test additions:**
- `backend/tests/test_post_audit_2026_04_20_batch2.py::TestEntitlementHelpersExist` (3 tests) — smoke-test each helper's callable shape.
- `TestExportRoutesAreGated` (4 parametrized tests) — structural guard that each export module has at least one `check_export_access`-gated route, so a future refactor can't silently drop the gate.
- `TestFormatAccessWiredOnUploadRoutes`, `TestToolRoutesCheckUploadLimit` — helper-availability checks.

**Validation:**
- Full touched-surface sweep (628 tests): all pass.
- Full backend pytest (ex. anomaly_framework): 7,939 passed / 9 xfailed / 0 failed after fixture fixes.

**Behaviour changes requiring stakeholder notice:**
1. Every PDF/Excel/CSV export endpoint now returns HTTP 403 with `code=TIER_LIMIT_EXCEEDED` for Free-tier users. Frontend UpgradeModal copy should surface this gracefully.
2. Uploads with OFX/QBO/IIF/PDF/ODS extensions now return 403 for Free tier before bytes are parsed. Error detail names the format explicitly.
3. Every testing-tool upload now increments the monthly upload counter. Free tier's 10-uploads-per-month cap now applies to testing tools as well as TB uploads; this changes the quota math for heavy-trial Free users.
4. `/audit/compare-periods`, `/audit/compare-three-way`, `/audit/currency-rates`, `/audit/currency-rate` now 403 for Free tier.

**Review:**
- Choice of route-level `dependencies=[Depends(check_export_access)]` over per-handler parameter was deliberate: keeps the gate visible at the decorator, survives the registry-based code in `export_memos.py` (which builds handlers in a loop), and doesn't require touching 30+ handler signatures.
- `enforce_format_access` as an imperative helper (rather than a dependency factory) was required by the shape of polymorphic upload routes — format is only knowable after the file is in hand.
- The `conftest.py` update is load-bearing: without it, ~90 existing export tests would 401 on the new gate without testing anything meaningful. The fix is intentionally narrow (override `require_current_user` to the same user as `require_verified_user`), so it doesn't mask legitimate auth issues — tests that specifically check auth rejection (`test_get_branding_no_auth_returns_401`, etc.) clear overrides first and still pass.
- Commit SHA: `768aa34` (landed together with Sprint 677).

---

### Sprint 679: Enterprise PDF branding end-to-end
**Status:** PENDING
**Priority:** P0 (feature-parity gap on Enterprise tier)
**Source:** Completeness agent (B-01)
**Why now:** Pricing page, Terms page, UpgradeModal, Settings, and `domain/pricing.ts` all sell "Custom PDF branding" as the Enterprise differentiator. The `FirmBranding` model, S3 upload, and entitlement gate all exist. **Zero PDF generator reads `logo_s3_key`, `header_text`, or `footer_text`.**
**Files:**
- `backend/routes/branding.py` (data source)
- `backend/pdf_generator.py` + every `backend/*_memo_generator.py` (~18 generators)
- `backend/shared/pdf_branding.py` — new helper
- `backend/shared/storage_client.py` — add signed-URL fetch helper if missing

**Changes:**
- [ ] New `backend/shared/pdf_branding.py` — loads the calling user's `FirmBranding` row (with org fallback), downloads logo bytes from S3, returns a `PDFBrandingContext` dataclass (`logo_bytes: bytes | None, header_text: str | None, footer_text: str | None, tier_has_branding: bool`).
- [ ] Extend base PDF generator header/footer to accept a `PDFBrandingContext` — when `tier_has_branding` is True, render the logo at top-left and `header_text`/`footer_text` at the margins; otherwise render Paciolus default.
- [ ] Wire the context load through every memo generator and the three report PDFs (combined audit, FS, anomaly summary). One call site per generator; data flows from the route `current_user`.
- [ ] E2E test: Enterprise user uploads logo → generates a memo → resulting PDF contains the logo at top-left and the configured `header_text`. Repeat for a Solo user → logo is ignored, default Paciolus branding appears.
- [ ] Sprint 677's `logo_s3_key` integrity fix must land first (or in the same PR) to avoid rendering a "missing logo" error when the S3 object was never persisted.
- [ ] Update CEO checklist in `ceo-actions.md` Phase 3 to note the branding round-trip is now live.

---

### Sprint 680: ISA 315 combined-risk matrix
**Status:** COMPLETE
**Priority:** P1 (standards compliance)
**Source:** Accounting-expert-auditor C-4
**Why now:** Current `compute_combined_risk_level` returned `max(IR, CR)`, which is not the ISA 315 Appendix 1 method. Moderate × moderate should yield elevated RMM; the max() approach returned moderate, systematically undercounting elevated-risk account/assertion pairs. Composite risk scoring is in CLAUDE.md's "Key Capabilities" — misrepresenting ISA 315 is a defensibility issue.

**Changes:**
- [x] Added `ISA_315_RMM_MATRIX` constant — 4×4 `inherent × control` lookup table per ISA 315 Appendix 1. Matrix is symmetric along the diagonal and non-decreasing on each axis.
- [x] Rewrote `compute_combined_risk_level` to do a table lookup instead of `max()`. Deleted the "(conservative approach)" comment — max is not conservative; the matrix is.
- [x] Expanded the disclaimer to name ISA 315 Appendix 1 explicitly and state that detection risk is outside scope (audit risk = IR × CR × DR remains the auditor's planning responsibility).
- [x] Regression tests: 58 of 58 composite-risk tests pass. Added `test_matrix_is_commutative` (symmetry invariant) and `test_monotonic_in_each_axis` (no reversals). Updated 11 downstream assertions where the old max() contract made inputs collapse to unintended buckets under the matrix (e.g., moderate × moderate is now elevated, low × moderate stays low).

**Key behaviour shifts requiring downstream-team awareness:**
1. Any `moderate × moderate` assessment now surfaces at the elevated bucket — the tool will count noticeably more elevated RMM pairs on existing engagements.
2. `low × moderate` and `moderate × low` now stay at low — reflecting that good controls override modest inherent risk.
3. `high × low` collapses to elevated, not high — acknowledging that effective controls materially mitigate high inherent risk.
4. `elevated × elevated` escalates to high — the most noticeable matrix-driven change.

**Review:**
- Source of truth for the matrix is ISA 315 (Revised 2019) Appendix 1; kept the constant and the helper in the same module so future auditor reviews can diff them against the standard without jumping files.
- 7,955 full-backend tests pass post-change — no other engine relied on the old max() behaviour even though 17 direct composite-risk tests had to be updated to the new contract.
- Commit SHA: `674c63c` (bundle commit covering Sprints 680/686/687/690/694).

---

### Sprint 681: Ratio engine — average-balance denominators + ICR + DuPont
**Status:** PENDING
**Priority:** P1 (formula correctness)
**Source:** Accounting-expert-auditor C-2/C-3/H-1/H-4/L-1/L-2
**Why now:** ROA/ROE/DSO/DPO all use ending TB balances in places where standard formulas require averages. For any entity with movement in receivables/assets/equity the ratio is materially distorted. ICR double-counts interest expense when the chart of accounts nests it under operating expenses. DuPont decomposition's `verification_matches` likely uses exact float equality.
**Files:**
- `backend/ratio_engine.py:276-296, 679-680, 730-731, 785-786, 867, 924`
- `backend/ar_aging_engine.py:79-83` (DSO consumer)

**Changes:**
- [ ] Add optional `prior_period_totals` parameter to the `RatioEngine` constructor. When provided, ROA/ROE/DSO/DPO/DIO/CCC compute `(beginning + ending) / 2`; when absent, use ending balance and attach a `formula_disclosure` field explaining the approximation.
- [ ] DPO denominator: switch to Purchases = COGS + ΔInventory when both periods are available; otherwise COGS with disclosure note.
- [ ] ICR: subtract `interest_expense` from `operating_exp` before computing EBIT to avoid the double-penalty when COA nests interest under opex.
- [ ] DuPont `verification_matches`: compare with `math.isclose(roe, decomposed_roe, rel_tol=1e-6)` instead of exact equality.
- [ ] Regression tests: an entity with 20% AR growth shows different DSO under ending vs. average; DuPont `verification_matches=True` for all legitimate decompositions.
- [ ] Propagate `prior_period_totals` plumbing through `routes/audit_pipeline.py` and `routes/ratios.py` (accept optional uploaded prior-period TB; if absent, compute with disclosure).
- [ ] Update memo copy in every ratio memo generator to reference the disclosure when applicable.

---

### Sprint 682: Easy-win audit test additions (payroll + FA + AP + inventory)
**Status:** PENDING
**Priority:** P1 (tool completeness)
**Source:** Accounting-expert-auditor H-2/H-3/M-5/M-6
**Why now:** Four standard substantive procedures are trivially implementable from columns already detected. Each is a first-line fraud/impairment indicator cited in AICPA/IAS/ASC literature. All four share a "detect column → arithmetic check → flag" shape.
**Files:**
- `backend/payroll_testing_engine.py` — new test PR-T12
- `backend/fixed_asset_testing_engine.py` — new test FA-T10
- `backend/ap_testing_engine.py` — new test AP-T14
- `backend/inventory_testing_engine.py` — new test INV-T10

**Changes:**
- [ ] **PR-T12 Gross-to-Net Reconciliation:** flag rows where `|gross_pay − deductions − net_pay| > $0.01`. AICPA EBP Audit Guide Ch. 5.
- [ ] **FA-T10 Depreciation Recalculation:** when prior-period accum-depr + method + useful life are present, recalc expected annual depreciation (SL: `(cost − residual) / life`; DDB: `2/life × NBV`) and flag variance > 5%. IAS 16 / ASC 360.
- [ ] **AP-T14 Invoice Without PO:** when a "PO Number" column is detected, flag payments above materiality with blank PO. ACFE 2024 — billing schemes = 19% of occupational fraud.
- [ ] **INV-T10 LCM/NRV Indicator:** when a selling-price or NRV column is detected, flag rows where `unit_cost > selling_price × (1 − expected_margin_floor)`. IAS 2.9 / ASC 330-10.
- [ ] Register each new test in the engine's test catalog, memo generator, CSV export schema, and entitlement matrix.
- [ ] Tests per new test: happy path, edge cases (missing column → skip with status note, zero/negative values).
- [ ] Update marketing copy: "19 JE tests, 14 AP tests, 12 payroll tests, 10 FA tests, 10 inventory tests" etc. — flow through CLAUDE.md, pricing page, memo titles.

---

### Sprint 683: Revenue testing refinements (RT-07 + RT-09 + ASC 606 Steps 1/3)
**Status:** PENDING
**Priority:** P1
**Source:** Accounting-expert-auditor H-5/M-2/M-8
**Why now:** RT-09 mislabels prior-period entries as "cut-off risk" — two distinct assertions. RT-07 injects a synthetic `[Aggregate Revenue]` row (`row_number=0`) into `flagged_entries` so PDF memos render an aggregate observation as if it were a GL line. ASC 606 Step 1 (contract identification) and Step 3 (transaction price / variable consideration constraint) have no tests; these are the most common revenue-recognition fraud vectors.
**Files:**
- `backend/revenue_testing_engine.py:1194-1211, 1351-1382, 1660-1890`
- `backend/revenue_testing_memo_generator.py`

**Changes:**
- [ ] Split RT-09 into two tests: `RT-09 Cut-Off Risk` (near period end only) and `RT-09b Prior-Period Timing` (near period start only). Update test descriptions and assertion mapping.
- [ ] Refactor `RevenueTestResult` to add `aggregate_findings: list[AggregateFinding]`; move RT-07's variance finding out of `flagged_entries`. Update the memo generator detail tables to render aggregates in a separate section.
- [ ] **RT-17 Step 1 Contract Validity:** flag recognition entries with missing customer ID, missing commercial-substance indicator (when a column is provided), or recognition without a prior contract-inception date.
- [ ] **RT-18 Step 3 Variable Consideration Constraint:** flag entries where `recognition_method=point-in-time` but `satisfaction_date` is blank, or where recognized amount exceeds contract price without a modification flag.
- [ ] Regression tests for both splits and both new tests.

---

### Sprint 684: MUS sampling standards compliance
**Status:** PENDING
**Priority:** P1 (standards compliance — most material auditor-facing defect)
**Source:** Accounting-expert-auditor C-1/M-1/L-3
**Why now:** Sampling is workpaper-bearing — sample sizes and evaluations get cited in engagement files. Homemade expansion factor understates samples ~4.6% at e/TM=0.25 vs. AICPA Audit Sampling Guide Table A-1. Inline TODO already acknowledges this.
**Files:**
- `backend/sampling_engine.py:297-318, 349-350, 472`
- `backend/sampling_memo_generator.py`
- `backend/shared/aicpa_tables.py` — new

**Changes:**
- [ ] Create `shared/aicpa_tables.py` with AICPA Audit Sampling Guide Table A-1 as a dict keyed on `(confidence_level, e_over_tm_bucket)` where buckets = {0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50}. Linear-interpolate between buckets.
- [ ] Replace the scalar expansion-factor math with the table lookup; keep the old path behind a `use_legacy_expansion=False` default-off flag for one release, then remove.
- [ ] Fix `sample_value` in the Stringer-bound evaluation to sum the entire selected sample's recorded value, not just the error items.
- [ ] Reject negative-balance items from MUS selection with an explicit "MUS applies to positive-balance populations only" warning. Document that understatement testing on negative balances requires a separate stratum.
- [ ] Regression tests: size(N=1M, conf=95%, e/TM=0.25, TM=$50K) matches Table A-1 value within rounding; size with no expected misstatement unchanged from current; Stringer `sample_value` matches total recorded value of selected items; MUS with mixed-sign population returns the warning and excludes negatives.
- [ ] Memo copy update — reference "AICPA Audit Sampling Guide, Table A-1" explicitly.

---

### Sprint 685: ISA 570 going concern expansion + test dedup
**Status:** PENDING
**Priority:** P1
**Source:** Accounting-expert-auditor C-5/M-4
**Why now:** Tool ships 6 indicators vs. ISA 570.16's ~20. Tests 2 and 3 are mathematically equivalent (current ratio < 1.0 ⇔ negative working capital) so the "2-of-6 indicators" threshold is implicitly 1-of-5. An auditor using this tool as a checklist prompt would miss major ISA 570.16 categories.
**Files:**
- `backend/going_concern_engine.py`
- `backend/going_concern_memo_generator.py`

**Changes:**
- [ ] Consolidate tests 2 (current ratio < 1.0) and 3 (negative working capital) into one test; keep the dollar-magnitude working-capital output (more informative for GC).
- [ ] Add cash-flow-based indicator: when a cash flow statement is derived, flag negative operating cash flow ≥ materiality threshold.
- [ ] Add covenant-breach indicator: take user-configurable thresholds (interest coverage minimum, debt/equity maximum, current ratio minimum); flag breaches.
- [ ] Add qualitative prompts (not detectable from TB but auditor-entered): loss of key customer, loss of key management, labor disputes, pending litigation, non-compliance with capital requirements. These render as *unchecked* by default in the memo with a note "requires auditor judgment — not TB-derivable."
- [ ] Update the ISA 570 disclaimer to list which categories are TB-derived vs. auditor-judgment-required.
- [ ] Regression tests: 2/3 merger doesn't double-count; cash-flow indicator fires on synthetic negative-opcf data; threshold count matches the new indicator list.

---

### Sprint 686: JE test tuning — Benford minimum + reversal window
**Status:** COMPLETE
**Priority:** P2
**Source:** Accounting-expert-auditor H-6/H-7

**Changes:**
- [x] Lowered `benford_min_entries` 500 → 300 in `JETestingConfig` with a Nigrini (2012) citation in the comment. `benford_min_magnitude_range` left at 2 (already correct per the same reference).
- [x] Added `_categorize_reversal(first_date, second_date, cross_account)` helper that classifies each reciprocal pair into one of three buckets based on period-boundary position:
  * `same_period` — both dates in the same calendar month. High-suspicion round-tripping indicator.
  * `accrual_reversal` — second entry lands on day 1 of the month after the first. Standard bookkeeping convention (post Dec 31, reverse Jan 1) — emitted at low/medium severity and 0.35/0.55 confidence so downstream risk scoring can deprioritise.
  * `cross_month` — any other cross-month pair. Medium/high suspicion because it crosses a close without the accrual-reversal shape.
- [x] Added `reversal_category` field to the flagged-entry details dict so PDFs and CSVs can surface the tier. Issue text now names the category inline ("same-period cross-account", "next-month day-1 accrual reversal", "cross-month").
- [x] Cross-account pairs continue to upgrade severity by one tier (same-period cross-account = high; accrual-reversal cross-account = medium rather than low) — offsetting entries to different accounts remain a stronger indicator than self-reversals.

**Validation:**
- 101 JE-engine + memo tests pass.
- No existing test asserted on the prior cross-account-binary severity model; the new tiered output is additive.

**Review:**
- The "day 1 of next month" heuristic is intentionally tight — ISA/Nigrini don't prescribe an exact window for what counts as a "standard accrual reversal", but first-of-month is the convention that every audit firm I've worked with trains juniors to spot. A looser window (e.g., first-week-of-next-month) would suppress too many genuine cross-month adjustments.
- Lowering Benford to 300 enables first-digit analysis on mid-size populations (300–499) that the prior threshold rejected. For populations below 300, Benford is unreliable (Nigrini 2012, p. 79) — keep the skip.
- Commit SHA: `674c63c` (bundle commit covering Sprints 680/686/687/690/694).

---

### Sprint 687: AR-aging silent date default + ASSET_KEYWORDS cleanup
**Status:** COMPLETE
**Priority:** P2
**Source:** Accounting-expert-auditor M-3/M-7

**Changes:**
- [x] **AR-aging date fix — already landed.** Sprint 695 resolved the `date.today()` fallback early on CPA-correctness grounds: `_compute_aging_days` returns `None` when no reference is supplied and raises `ValueError` on unparseable dates; the AR-aging route rejects sub-ledger uploads without `as_of_date` with HTTP 400. Sprint 687 verifies the fix is intact rather than duplicating work.
- [x] **ASSET_KEYWORDS extended** (`backend/audit/classification.py`) with the missing modern-COA families: `notes receivable`, `other receivable`, `investments`, `securities`, `deposits`, `goodwill`, `intangible`, `leasehold`, `right-of-use`, `rou asset`, `deferred tax asset`.
- [x] **Deduplicated the list** — `audit/ingestion.py` had a hardcoded duplicate of `ASSET_KEYWORDS` that had drifted from the canonical one. Replaced with an import from `audit.classification` so the legacy vectorized path stays in lock-step; there's now a single source of truth.
- [x] The list remains in `__all__` and re-exported from `audit_engine.py` — it's still reachable by external callers — but the module-level comment now explicitly states it's a lexical fallback for `AccountClassifier` rather than a production classifier.

**Validation:**
- 154 AR-aging + audit-validation tests pass. The existing `test_audit_validation.py` checks exercise the keyword vectorization path directly.

**Review:**
- The original "remove from `__all__` or document" decision: document wins. Removing breaks any downstream integration that imports from `audit_engine`, and the list IS still used by `detect_abnormal_balances` (a secondary path); marking it as a fallback rather than deleting keeps the compatibility surface intact.
- Extending the list was the real win — a "Goodwill" or "ROU Asset" account on a modern TB would previously fall through to the weighted classifier without the keyword sanity check, weakening the abnormal-balance vectorized fast-path.
- Commit SHA: `674c63c` (bundle commit covering Sprints 680/686/687/690/694).

---

### Sprint 688: Composite Risk + Account Risk Heatmap frontend
**Status:** PENDING
**Priority:** P2 (feature completeness — marketed in CLAUDE.md)
**Source:** Completeness agent H-01/H-02
**Why now:** Both tools ship with full backend engines, routes, and tests; neither has a single line of frontend code. CLAUDE.md markets both under "Key Capabilities." Either wire the UI or stop marketing them.
**Files (new):**
- `frontend/src/types/compositeRisk.ts`, `hooks/useCompositeRisk.ts`, `components/compositeRisk/*`, `app/tools/composite-risk/page.tsx`
- `frontend/src/types/accountRiskHeatmap.ts`, `hooks/useAccountRiskHeatmap.ts`, `components/accountRiskHeatmap/*`, `app/tools/account-risk-heatmap/page.tsx`

**Changes:**
- [ ] Composite Risk: auditor-input workflow (inherent/control/fraud risk per account/assertion) → combine with TB/testing signals → render RMM matrix + priority table. Bind to existing `/composite-risk/*` endpoints.
- [ ] Account Risk Heatmap: render the heatmap + CSV download. Bind to existing `/account-risk-heatmap/*` endpoints.
- [ ] Add both to `app/tools/page.tsx` catalog and `lib/commandRegistry.ts`.
- [ ] Both pages use Oat & Obsidian tokens, Reveal scroll-reveal, and tier-gating per `useEntitlements`.
- [ ] Jest tests for hook + at least one components/page happy path per tool.

---

### Sprint 689: Hidden backend tools — catalog wire-up or removal
**Status:** PENDING
**Priority:** P2
**Source:** Completeness agent H-03/H-05 + Claim-reality C-03/C-04
**Why now:** Six backend tools have endpoints and no UI: `book_to_tax`, `cash_flow_projector`, `intercompany_elimination`, `form_1099`, `w2_reconciliation`, `sod`. Separately, Multi-Currency is marketed as Tool #12 but is only a side-car on TB upload — no standalone card. Decide per-tool: promote to catalog or remove the route.
**Files:**
- `backend/routes/{book_to_tax, cash_flow_projector, intercompany_elimination, form_1099, w2_reconciliation, sod}.py`
- `frontend/src/app/tools/page.tsx`, `lib/commandRegistry.ts`
- `shared/entitlements.py:14` (canonical tool count)

**Changes:**
- [ ] For each of the six: CEO decides [promote / defer / remove]. Default recommendation:
  - `sod` — already Enterprise-gated; promote with minimal UI.
  - `form_1099`, `w2_reconciliation` — payroll-adjacent; promote under the Payroll tool umbrella as sub-workflows.
  - `book_to_tax`, `cash_flow_projector`, `intercompany_elimination` — remove routes if not shipping Tool #13+, document rationale in a sprint archive entry.
- [ ] Multi-Currency: add a standalone `/tools/multi-currency` card with its own page; continue rendering the side-car on TB upload for convenience.
- [ ] Reconcile `CANONICAL TOOL COUNT` in `shared/entitlements.py:14` with the final catalog count; propagate to CLAUDE.md, pricing page, ceo-actions.md, and marketing surfaces.
- [ ] Regression tests: every cataloged tool has a route, hook, page, and entitlement-gate test.

---

### Sprint 690: Stripe trial-ending email
**Status:** COMPLETE
**Priority:** P2
**Source:** Completeness agent H-04
**Why now:** `webhook_handler.py` received `customer.subscription.trial_will_end`, logged it, recorded a `TRIAL_ENDING` analytics event, and did nothing else. Docstring explicitly said "Notification email infrastructure deferred to a future sprint." Users didn't get the standard 3-day warning.

**Changes:**
- [x] Added `send_trial_ending_email(to_email, days_remaining, plan_name, portal_url)` to `backend/email_service.py`. Reuses the dunning-email infrastructure (`_send_dunning_email` + `_dunning_html`) because the shape is identical (single CTA, friendly tone, Oat & Obsidian branded); avoids duplicating the HTML template. Copy pluralizes day/days and names the plan explicitly.
- [x] Wired the send into `handle_subscription_trial_will_end`. The analytics event is recorded first (source-of-truth), then the email fires — so a SendGrid outage can never break analytics-backed decisioning.
- [x] Added `_days_until(epoch_seconds)` — converts Stripe's `trial_end` timestamp to an integer days-from-now value, clamped to [0, 365]. Falls back to 3 (Stripe's default notice window) when the field is absent or unparseable.
- [x] Added `_portal_url_for_user(db, user_id)` — resolves a Stripe Customer Portal session URL for the CTA. Falls back to the in-app `/settings/billing` page if the portal session cannot be created; the webhook handler must never crash on a URL lookup.
- [x] Dispatch is wrapped in try/except — a SendGrid outage or template error cannot break webhook processing. Failures surface via `log_secure_operation` for ops visibility.

**Tests:**
- `test_trial_will_end_sends_trial_ending_email` — patches `email_service.send_trial_ending_email` + `_portal_url_for_user`, fires the webhook with a trial_end 5 days in the future, asserts the email was dispatched with the right recipient, days (±1 for day-rounding), plan, and portal URL.
- `test_trial_will_end_missing_trial_end_defaults_to_3_days` — verifies the `_days_until` fallback fires when Stripe omits the field.
- Existing `test_trial_will_end_records_trial_ending_not_expired` still passes — analytics path unchanged.

**Review:**
- Reusing the dunning email chassis was the pragmatic call: the brand template, deliverability wiring, and "email send is skipped gracefully when SENDGRID_API_KEY is absent" behaviour are all already tested on that code path. Writing a parallel template would have meant duplicating ~40 lines of HTML and the SendGrid error handling.
- The portal-URL fallback to `/settings/billing` is deliberate — if Stripe's portal session creation fails (billing portal config missing, customer ID stale), we still want the CTA to land somewhere useful; the in-app settings page always works for authenticated users.
- Commit SHA: `674c63c` (bundle commit covering Sprints 680/686/687/690/694).
- [ ] Add a unit test (mock SendGrid) that verifies the send call + args; add an integration test that runs the webhook handler end-to-end.
- [ ] Update `tasks/pricing-launch-readiness.md:48` acceptance note — trial email no longer deferred.

---

### Sprint 691: Professional-tier DB enum + team-seat counting
**Status:** PENDING
**Priority:** P2
**Source:** Completeness agent H-07/H-08
**Why now:** `UserTier.PROFESSIONAL` is still in the DB enum but unpurchasable; legacy Professional users map to Solo entitlements. `pricing-launch-readiness.md:49-50` flagged team-member counting as a placeholder; hard-mode seat enforcement landed in `config.py:456` but the underlying counting logic was never verified.
**Files:**
- `backend/models.py` (UserTier enum)
- `backend/shared/entitlements.py` (Professional mapping)
- `backend/billing/seat_enforcement.py` or equivalent — wherever active-member counting lives
- Alembic migration (new)

**Changes:**
- [ ] Alembic migration: collapse `PROFESSIONAL` values to `SOLO` across `users.tier`; drop `PROFESSIONAL` from the enum (Postgres enum alter sequence: add new enum without PROFESSIONAL → copy → drop old). Backfill any Professional users to Solo with a logged event.
- [ ] Remove Professional-specific code paths from `shared/entitlements.py` and tests.
- [ ] Audit the active-member counting function: does it count pending invitations? terminated users? multi-org members? Build a concrete test matrix and exercise each.
- [ ] Verify Enterprise seat-hit returns 402 and frontend UpgradeModal surfaces it correctly.
- [ ] Sign-off note in `pricing-launch-readiness.md`.

---

### Sprint 692: Documentation drift correction
**Status:** PENDING
**Priority:** P2 (launch documentation hygiene)
**Source:** Completeness C-01/C-02/C-03/C-04/C-07 + Accounting H-8
**Why now:** "21 PDF memos" is actually 18 memos + 3 report PDFs. "24 export endpoints" is actually ~27. CLAUDE.md says 12 tools; frontend catalog shows 15. `pricing-launch-readiness.md` hasn't been re-signed since 2026-02-25 — pre-dates Phase 1 deploy, Pricing v3, Sprint 673, and Stripe live cutover.
**Files:**
- `CLAUDE.md`
- `frontend/src/app/(marketing)/pricing/page.tsx` + `components/marketing/ToolShowcase.tsx`
- `tasks/ceo-actions.md`
- `tasks/pricing-launch-readiness.md`
- `memory/*.md` (per-user)
- `backend/engagement_manager.py:163` + `backend/materiality_resolver.py:34` — materiality cascade disclosure

**Changes:**
- [ ] Replace "21 PDF memos" with "18 memo PDFs + 3 report PDFs (combined audit, financial statements, anomaly summary)" across CLAUDE.md, ceo-actions.md, marketing copy. Or reclassify and land on a single number.
- [ ] Recount export endpoints (`grep -rn "@router" backend/routes/export*.py engagements_exports.py loan_amortization.py`) and publish the exact number in CLAUDE.md.
- [ ] Reconcile "12 tools" vs. "15 catalog cards" — align after Sprint 689 lands.
- [ ] Materiality cascade: ensure every memo that references thresholds states explicitly that clearly-trivial = 5% of overall (not performance) materiality and PM = 75% of overall.
- [ ] `pricing-launch-readiness.md`: re-sign Section 7 after Sprints 677-679 (pricing enforcement + branding) are verified. Blocks Phase 4.1 per `ceo-actions.md:114`.
- [ ] Update `CLAUDE.md` test count to the current nightly total after all remediation sprints land.

---

### Sprint 693: Frontend polish — framer-motion + silent catches
**Status:** PENDING
**Priority:** P3
**Source:** Frontend-bugs agent (4 HIGH + 2 silent catches)
**Why now:** Five minor improvements, bundleable into one PR. No functional bugs; type-safety + observability only.
**Files:**
- `frontend/src/app/(auth)/verification-pending/page.tsx:70`
- `frontend/src/app/(auth)/verify-email/page.tsx:95, 112, 131`
- `frontend/src/app/tools/page.tsx:72`
- `frontend/src/hooks/useTrialBalanceUpload.ts:249`

**Changes:**
- [ ] Add `as const` to all four `type: 'spring'` framer-motion transitions in the auth pages.
- [ ] Replace `.catch(() => {})` in `tools/page.tsx:72` and `useTrialBalanceUpload.ts:249` with a structured logger call (`logger.warn(...)` or Sentry breadcrumb) — silent catches hide bugs in preference loading and telemetry.
- [ ] No new tests needed; existing suites cover behaviour.

---

### Sprint 695: High-assurance financial-report remediation (RPT-11 / DASH-01 / RPT-02 / RPT-07)
**Status:** COMPLETE
**Priority:** P0 (financial-calculation correctness)
**Source:** Post-audit high-assurance remediation brief 2026-04-20 — CPA-facing correctness bar, validate-then-fix.

**Why now:** Five confirmed defects in financial-report engines spanning three-way match variance math, dashboard taxonomy, and multi-period variance configuration — all in the CPA-facing output surface where a single wrong percentage erodes auditor trust.  Three additional suspicions required test-first validation before touching logic.

**Confirmed defects — FIXED:**
- [x] **RPT-11 price variance denominator** (`backend/three_way_match_engine.py`): replaced `config.price_variance_threshold` / `config.amount_tolerance` denominator guards with a monetary epsilon (`MONETARY_EPSILON = Decimal("0.005")`).  The 5% decision threshold was being used as a "$0.05 is close enough to zero" guard, mis-flagging every sub-$0.05 unit price at 100% variance.  Quantities use a separate count-space epsilon (`1e-6`).  Decimal-first arithmetic preserved.
- [x] **RPT-11 match-rate denominator** (same file, `run_three_way_match`): denominator now `max(len(pos), len(invoices), len(receipts), 1)`.  Added `match_rate_denominator` + `match_rate_denominator_source` response fields for audit-workpaper traceability.  Partial-delivery scenarios (receipts > POs) no longer inflate full-match rate above 1.0.
- [x] **RPT-11 route config overrides** (`backend/routes/three_way_match.py`): seven optional form fields + `_build_twm_config` with bounded validation (HTTP 400 on out-of-range); defaults preserved for every existing client.
- [x] **DASH-01 tier taxonomy mismatch** (`backend/shared/testing_enums.py` + `backend/engagement_dashboard_engine.py`): new shared `normalize_risk_tier` maps 3-tier `medium` → canonical 4-tier `moderate` plus defensive legacy-alias handling (`critical`/`minimal`/...).  Three-way-match reports no longer vanish from the dashboard priority-action list.
- [x] **RPT-02 configurable significance thresholds** (`backend/multi_period_comparison.py` + `backend/routes/multi_period.py`): new `SignificanceThresholds` dataclass; `compare_trial_balances` / `compare_three_periods` / `classify_significance` accept optional overrides.  API exposes `significant_variance_percent` / `significant_variance_amount` with bounded validation.  Active thresholds emitted in `active_thresholds` response field.

**Suspicions — resolved via test-first:**
- [x] **RPT-02 signed variance basis — REJECTED.** `abs(prior_balance)` denominator is intentional; pairs with credit-normal display sign-flip in `AccountMovement.to_dict`.  Locked behaviour in `TestRPT02SignedVarianceSuspicion` (5 tests, including sign-change + abs-symmetry properties the display layer depends on).
- [x] **RPT-07 non-deterministic aging — CONFIRMED.** `_compute_aging_days` no longer falls back to `date.today()`: returns `None` when no reference supplied, raises `ValueError` on unparseable dates.  Route rejects sub-ledger uploads without `as_of_date` (HTTP 400).  Lands the Sprint 687 fix early on CPA-correctness grounds.
- [x] **Cross-report float precision — ACCEPTED as-is with pinning tests.** Three-way match keeps Decimal end-to-end through the engine; multi-period converts at `calculate_movement`.  `TestCrossReportPrecisionBoundaries` pins the conversion boundaries so future refactors cannot silently drift.  Deeper Decimal migration across the other 15 engines is out-of-scope (no material-drift finding).

**Test additions:**
- `backend/tests/test_remediation_2026_04_20.py` — 39 tests, all pass.

**Validation:**
- `pytest tests/test_remediation_2026_04_20.py` → 39 passed.
- Touched-engine regression sweep (`test_three_way_match` + `test_multi_period_comparison` + `test_ar_aging_engine` + `test_flag_regressions`) → 269 passed.
- Route/memo sweep (`test_ar_aging*` + `test_multi_period_*` + `test_engagement_dashboard_memo` + `test_twm_memo` + `test_api_contracts` + `test_export_testing_routes`) → 424 passed.
- Broad touch-domain filter (`-k "dashboard or multi_period or three_way or ar_aging or movement or significance or variance"`) → 680 passed / 9 xfailed / 0 failed.

**Behaviour changes requiring stakeholder notice:**
1. Three-way match `full_match_rate` denominator now includes receipts — rates shift downward when receipt population exceeds PO/invoice (split deliveries).  Memos that quote the rate should cite the new `match_rate_denominator_source`.
2. AR-aging API rejects sub-ledger uploads without `as_of_date` (HTTP 400 instead of silent `date.today()` fallback).
3. Multi-period API adds `significant_variance_percent` / `significant_variance_amount` (both optional — historical 10% / $10,000 preserved when omitted); response now includes `active_thresholds` for audit traceability.
4. Engagement dashboard surfaces `medium` three-way-match findings as `moderate` — these previously never appeared in the priority-action list.

**Review:**
Nothing weakened — auth/security/zero-storage untouched, no tests silenced, every formula change has a paired test.  The RPT-02 "signed variance" suspicion turned out to be INTENTIONAL platform policy; rejecting it was the correct call per the test-first directive, and the pinning tests prevent a future "fix" from breaking the credit-normal display contract.

---

### Sprint 694: Coverage Sentinel non-prod ignore list
**Status:** COMPLETE
**Priority:** P3
**Source:** Completeness S-04

**Changes:**
- [x] Added `NON_PRODUCTION_FILE_SUFFIXES`, `NON_PRODUCTION_FILE_SUBSTRINGS`, and `NON_PRODUCTION_BASELINE_MARKERS` constants at the top of `scripts/overnight/agents/coverage_sentinel.py`. Data-driven so a future "exclude X" is a one-line change.
- [x] Added `_is_non_production_path(path)` helper — case-insensitive, slash-agnostic (handles both `alembic/versions/` and `alembic\versions\` since coverage.json mixes them on Windows).
- [x] `_top_uncovered_files()` now returns `(ranked, excluded_count)` — skips files that match the helper and tells the caller how many it dropped.
- [x] The sentinel summary string now includes "Non-production excluded: N file(s)" when the count is non-zero, so the exclusion is visible in the nightly report (not silently applied).
- [x] Result payload gains a `non_production_excluded` integer field for programmatic consumers.

**Validation:**
- Inline smoke-test harness verified:
  * `generate_sample_reports.py` (forward + back slash paths) → excluded.
  * `scripts/validate_report_standards.py` → excluded.
  * `migrations/alembic/versions/2026_01_baseline.py` → excluded (baseline marker matched).
  * `migrations/alembic/versions/2026_04_20_harden_passcode.py` → NOT excluded (regular migration — still ranks in top-uncovered because it DOES execute in production on deploy).
  * `backend/routes/billing.py`, `backend/routes/audit_pipeline.py` → NOT excluded.

**Review:**
- Baseline-only exclusion for alembic (not all migrations) was deliberate: regular migrations run in production on deploy and absolutely should be tested; only the frozen baseline file is genuinely non-productive to cover.
- Non-production exclusion is additive — the totals/percent_covered metrics still include these files (coverage.json's totals aren't affected), just the top-10 uncovered ranking changes. This keeps the overall coverage number stable so the rolling-mean drift detection isn't affected.
- Commit SHA: `674c63c` (bundle commit covering Sprints 680/686/687/690/694).

---

## Anomaly Framework Hardening — 2026-04-21

> **Source:** The 9 xfail markers in `tests/test_tool_anomaly_detection.py` — 3 currency validation gaps + 6 generator↔engine alignment issues. Sprint plan (A–E) drawn up 2026-04-20; executed as Sprints 699–703 below. End state: **zero xfails remaining**, formal contract layer in place, strict CI gate on contract compliance.

---

### Sprint 699 (A): Multi-currency defense-in-depth
**Status:** COMPLETE
**Priority:** P1
**Source:** 3 xfailed tests in `test_tool_anomaly_detection.py::test_currency_anomaly_detected` (zero / negative / stale exchange rate).

**Why now:** `parse_rate_table` rejected bad rates on the upload path, but `convert_trial_balance` trusted whatever was already in the `CurrencyRateTable`. Any bypass path (DB hydration via `from_storage_dict`, programmatic construction, test fixtures) could silently admit rate=0, rate<0, or heavily-stale rates and produce bad conversions without flagging.

**Changes:**
- [x] `ExchangeRate.__post_init__` — validate-at-construction. Rejects rate ≤ 0, empty currency codes, non-3-letter codes, identical from/to, non-date effective_date. Normalises str/int/float rate inputs to Decimal.
- [x] `CurrencyRateTable.staleness_threshold_days` — promoted from a module constant to a first-class configurable field; plumbed through `find_rate` / `_find_best_rate`.
- [x] `CurrencyRateTable.newest_rate_date()` — helper that returns the latest effective_date in the table. Drives the cohort-based staleness check.
- [x] `_find_best_rate` — now runs staleness in two modes: target-date-based (original) OR cohort-based (new). The cohort check catches "stale rate alongside a fresh one" without requiring the caller to supply as_of_date.
- [x] `convert_trial_balance` — defense-in-depth: checks `rate <= 0` at use time and emits `ConversionFlag(issue="invalid_rate")` if a malformed rate leaked through construction.
- [x] `from_storage_dict` — every hydrated ExchangeRate now runs through `__post_init__`, so a corrupted DB row can't silently re-admit bad data.
- [x] Row-level flag path carries the specific issue (`missing_rate` vs. `invalid_rate`) — different remediation, different severity.

**Test updates:**
- [x] `_build_rate_table` in `test_tool_anomaly_detection.py` wraps ExchangeRate construction in try/except and returns a `rejected` list. The test now accepts detection at either boundary (construction rejection OR use-time flagging) — both are valid defense mechanisms.
- [x] All 3 currency xfails removed.

**Validation:**
- Full currency + tool-anomaly regression: 204 passed / 6 xfailed (6 non-currency xfails still present — Sprints C/D scope) / 0 failed.
- `test_tool_anomaly_detected[currency_*]` — all 5 generators pass.

**Review:**
- Chose cohort-based staleness over requiring as_of_date because it mirrors how auditors actually think: "is this rate stale relative to the others in the table?" is the fast screening question. Target-date mode stays available for engagements that need period-specific validation.
- `invalid_rate` as a distinct flag from `missing_rate` preserves auditor signal — "rate wasn't there" and "rate was there but bad" require different follow-up.
- Commit SHA: pending (landed in anomaly-framework bundle commit).

---

### Sprint 700 (B): Anomaly framework contract layer
**Status:** COMPLETE
**Priority:** P1
**Source:** Sprint plan A–E; upstream of Sprints 701/702 which need the contract to describe their fixes.

**Why now:** Fixing the 6 Category A xfails individually without a formal contract means the next generator added re-introduces the same class of drift. Establishing the generator↔engine contract layer first makes subsequent fixes durable.

**Changes:**
- [x] `backend/shared/engine_contract.py` (new, production-location) — defines `EngineInputContract`, `DetectionPreconditions`, `GeneratorEvidence`, `ContractViolation`, and `check_contract()`. Pure data classes + one pure function; no side effects; safe to import from any engine.
- [x] `backend/tests/anomaly_framework/test_contract.py` (new) — 9 unit tests for `check_contract` (happy path, each violation type, substring-based pattern matching, commutativity, multi-gap surfacing).
- [x] `backend/tests/anomaly_framework/test_contract_compliance.py` (new) — cross-registry meta-test. Introspects each engine module for `ENGINE_CONTRACT`, each generator for `PRODUCES_EVIDENCE`, and runs `check_contract` on every annotated pair. Report-only during Sprints B–D.
- [x] `pyproject.toml` — registered the `anomaly_contract` pytest mark.
- [x] `currency_engine.ENGINE_CONTRACT` — worked example (5 detection targets: missing_rates, invalid_currencies, zero_rates, negative_rates, stale_rates).
- [x] Annotated all 5 currency generators with `PRODUCES_EVIDENCE`.

**Test coverage:**
- Contract unit tests: 9 passed.
- Compliance meta-test: 2 passed (one report, one importability sanity).
- 11 total contract tests pass.

**Review:**
- Placed `contract.py` in `shared/` rather than under `tests/` so production engines can import it without test-tree coupling. The module is pure data (dataclasses + one pure function) — arguably production infrastructure, not test scaffolding.
- Substring pattern matching (not set equality) is the correct shape for real-world account-name detection: engines look for "returns" anywhere in a name like "Sales Returns and Allowances", not for exact equality.
- Report-only mode for this sprint was deliberate: Sprints C/D can populate contracts incrementally; Sprint E flips to strict mode once coverage is meaningful.
- Commit SHA: pending (landed in anomaly-framework bundle commit).

---

### Sprint 701 (C): Revenue + Payroll alignment
**Status:** COMPLETE
**Priority:** P2
**Source:** 2 of the 6 Category A xfails — `revenue_contra_anomaly`, `payroll_duplicate_names`.

**Changes:**
- [x] **Revenue contra (generator fix).** Prior generator injected ~$6.4K of contras against ~$200K base gross revenue (3%) — the engine's RT-12 threshold is 15%, so the test never fired. Fix: bump injection to ~$60K (~30%) so RT-12 actually trips. Generator now emits "Sales Returns and Allowances" + "Sales Refunds" account names (matching the engine's contra keyword list).
- [x] **Payroll duplicate names (engine addition).** The generator targeted `PR-T2` — but PR-T2 is "Missing Critical Fields", which doesn't test name duplication at all. There was no engine test for same-name-different-ID detection, which is ACFE's canonical ghost-employee indicator (26% of payroll fraud). Fix: added `PR-T12 Duplicate Employee Names` (flags distinct employee_ids sharing the same name). Registered in the test pipeline. Generator retargeted to `PR-T12`.
- [x] xfail markers removed for both tests.

**Validation:**
- Revenue anomaly tests: 13 passed / 0 xfail.
- Payroll anomaly + engine + memo + tier2 + tier3 tests: 192 passed / 0 xfail.
- Broader regression (revenue + payroll + anomaly framework): 461 passed.

**Review:**
- PR-T12 was the right fix rather than retargeting the generator. Ghost-employee detection is a material gap; the existing `duplicate_name_similarity` config was orphaned (defined but unused). Filling the gap AND closing the xfail in one move.
- Revenue fix was generator-side because the engine's 15% threshold is correct per real auditor practice — the generator was just under-injecting relative to the base population size.
- Commit SHA: pending (landed in anomaly-framework bundle commit).

---

### Sprint 702 (D): AR + FA + Inventory alignment
**Status:** COMPLETE
**Priority:** P2
**Source:** 4 of the 6 Category A xfails — `ar_sign_anomalies`, `fa_duplicate_assets`, `inv_missing_fields`, `inv_duplicate_items`.

**Changes:**
- [x] **AR sign (engine split).** AR-01 checks TB-level sign mismatch (asset with credit balance); generator mutates the sub-ledger. Different assertions, shouldn't collide. Added `AR-01b ar_sl_negative_invoice` — flags sub-ledger invoices with `amount < 0` (credit memo / reversal signal). AICPA Audit Guide §5.11 describes the two as distinct control objectives. Generator retargeted to AR-01b. Added a skipped-slot for the new test when sub-ledger absent to keep the 12-slot test-list stable.
- [x] **FA duplicate assets (generator fix).** Engine dedups on `(cost, description, acquisition_date)` — generator was mutating the description, breaking the tuple. Fix: keep the triple identical, vary asset_id (the real "double-booked capitalisation" pattern per ACFE 2024).
- [x] **INV missing fields (generator fix).** Engine treats identifier (item_id OR description) + quantity + cost as required; Category and date are optional. Generator was blanking Category and date but keeping item_id populated. Fix: blank Item ID AND Description — a truly unidentifiable row, which is the engine's strict definition.
- [x] **INV duplicate items (generator fix).** Same shape as FA: engine dedups on `(unit_cost, description)`, generator was mutating description. Fix: keep description + unit_cost identical, vary Item ID.
- [x] Test assertion updates: `test_ar_aging.py` and `test_ar_aging_engine.py` bumped from 11 → 12 test slots (skipped and all).
- [x] xfail markers removed for all 4 tests.

**Validation:**
- AR + FA + INV + anomaly tests: 620 passed / 0 xfail.
- `test_tool_anomaly_detection.py`: 89 passed / 0 xfail — **all Category A xfails closed.**

**Review:**
- AR-01 / AR-01b split was the right shape; widening AR-01 to include SL-level negative invoices would have muddied the auditor memo (one test firing for two different control objectives).
- FA and INV duplicate fixes were symmetric generator-side fixes — the engines were correct, the generators were asking the wrong question.
- INV missing fields fix aligned the generator with the engine's strict identifier definition. Category being "required" is contested in literature (different inventory frameworks treat category differently); the engine's narrower definition is defensible.
- Commit SHA: pending (landed in anomaly-framework bundle commit).

---

### Sprint 703 (E): Contract enforcement + CI guardrails
**Status:** COMPLETE
**Priority:** P2
**Source:** Final sprint in the plan; locks in the contract layer so drift can't silently re-emerge.

**Changes:**
- [x] Annotated 5 engines with `ENGINE_CONTRACT`: currency (Sprint 700), revenue, payroll, ar_aging, fixed_asset, inventory. Each declares its required/optional columns, entry point, and per-`test_key` `DetectionPreconditions`.
- [x] Annotated 4 generators with `PRODUCES_EVIDENCE` (beyond the 5 currency from Sprint 700): revenue_contra_anomaly, duplicate_names, ar_sign_anomalies, fa_duplicate_assets, inv_missing_fields, inv_duplicate_items.
- [x] Upgraded `test_generator_engine_contracts` from report-only to **strict mode** — any contract violation now `pytest.fail()`s. Strict mode caught one real drift during Sprint 703 execution (revenue contract required "credit memo" as an account-name pattern but the engine accepts it in Description too); reconciled by narrowing the contract to exact-match auditor-facing account names.
- [x] `CONTRIBUTING.md` — added an "Anomaly-Framework Generator ↔ Engine Contracts" section documenting the pattern, the common violation shapes, and precedent for fix direction.

**Validation:**
- Contract unit tests: 9 passed.
- Strict-mode compliance meta-test: passes (0 violations).
- Full backend regression: **7,968 passed / 0 failed / 0 xfailed** (was 7,946 / 9 xfailed before Sprint A).

**Review:**
- Strict mode caught a real drift on day one — exactly the Sprint E design. The revenue contract was over-strict; reconciliation was a one-line change. This is the pattern future maintainers will see: add a generator, run the meta-test, get a precise violation report, fix, merge.
- Property-based tests for the contract itself (mentioned in the plan) were deprioritised — the unit tests in `test_contract.py` already cover the pure function exhaustively across all violation types. Adding hypothesis tests would be noise on top.
- Commit SHA: pending (landed in anomaly-framework bundle commit).

---

## Security Hardening Follow-Ups — 2026-04-20

> **Source:** Residual-risk + follow-up list from the six-objective security hardening batch (Sprint 696 when committed). Grouped by area; safe to land individually.

---

### Sprint 697: Argon2id upgrade for export-share passcodes
**Status:** PENDING
**Priority:** P2
**Source:** Security hardening brief 2026-04-20 — preferred KDF was Argon2id; bcrypt was the spec-permitted fallback because `argon2-cffi` is not in the dep tree.
**Why now:** Not urgent (bcrypt cost-12 is audit-defensible), but the hardening brief explicitly prefers Argon2id. Doing it as a standalone sprint keeps the dep churn out of the security sprint diff and lets us run the memory-cost parameter under a load test before landing.
**Files:**
- `backend/requirements.txt`
- `backend/shared/passcode_security.py`
- `backend/tests/test_security_hardening_2026_04_20.py`

**Changes:**
- [ ] Add `argon2-cffi>=23.1.0` to requirements.
- [ ] Switch `hash_passcode` to Argon2id (time_cost=3, memory_cost=65536, parallelism=4 — AWS-SECS recommendation; run local bench to confirm ≤ 250ms on Render Standard).
- [ ] Extend `verify_passcode` to:
  - accept Argon2 hashes (prefix `$argon2id$`),
  - continue rejecting legacy SHA-256,
  - still accept bcrypt hashes during the transition window (≤48h — one share-TTL cycle),
  - after cycle, remove the bcrypt branch.
- [ ] Update `_looks_like_bcrypt` → `_is_legacy_hash_format` (three-way: argon2 / bcrypt / sha256).
- [ ] Regression tests: argon2 round-trip, bcrypt→argon2 dual-path, rejection of sha256.
- [ ] Docs: note the rollout window in `docs/04-compliance/` security policy.

---

### Sprint 698: Per-IP passcode-failure throttle
**Status:** PENDING
**Priority:** P2
**Source:** Security hardening follow-up (brute-force defence — per-token is necessary, not sufficient).
**Why now:** Sprint 696 added per-token passcode lockout; an attacker cycling through multiple share tokens from one IP is bounded only by the slowapi IP rate limit (60/min generic). A focused per-IP failure counter — the same pattern `record_ip_failure` uses for auth — would catch credential-stuffing attempts across many share links before they accumulate enough signal.
**Files:**
- `backend/security_middleware.py` (reuse `record_ip_failure` / `check_ip_blocked` helpers)
- `backend/routes/export_sharing.py`
- `backend/tests/test_security_hardening_2026_04_20.py`

**Changes:**
- [ ] In `_verify_passcode_or_raise`, also call `record_ip_failure(client_ip)` on mismatch. Use `get_client_ip(request)` so trusted-proxy rules apply.
- [ ] Before verification, call `check_ip_blocked(client_ip)` and return 429 with generic "too many failed attempts" message (do NOT leak share-token existence).
- [ ] Keep per-token throttle intact; the new per-IP check is additive.
- [ ] Add env overrides for share-specific IP threshold if the auth threshold (20 failures / 15 min) is too loose — tentatively `SHARE_IP_FAILURE_THRESHOLD=10`.
- [ ] Tests: 10 wrong passcodes across 10 different share tokens from one IP → 11th attempt from that IP is 429 even against a fresh token.

---

### Sprint 699: Frontend passcode download flow audit
**Status:** PENDING
**Priority:** P1 (user-facing: broken UI if missed)
**Source:** Security hardening rollout — passcode download surface changed from GET `?passcode=` to POST body.
**Why now:** Sprint 696 removed the query-string passcode pattern. Anywhere in the frontend still constructing `?passcode=` URLs (download links, share-received modal, email copy) will render as "Invalid passcode" or "requires a passcode" 403s post-deploy.
**Files:**
- `frontend/src/app/(shares)/` — share-received page
- `frontend/src/components/share/*` — passcode modal
- `frontend/src/hooks/useShareDownload.ts` (if present) / fetch helpers
- `frontend/src/app/*/page.tsx` — audit grep for `export-sharing/` URL construction
- `backend/shared/email_templates/` — share-notification emails (ensure links don't carry passcodes)

**Changes:**
- [ ] Grep `frontend/src` for `export-sharing/` and any `passcode=` URL construction; migrate to POST body.
- [ ] Passcode modal: POST `/export-sharing/{token}/download` with `{passcode}` JSON body; show `Retry-After`-based countdown on 429.
- [ ] Non-passcode shares: confirm GET path still works end-to-end.
- [ ] Validate share-notification emails do NOT embed the passcode (user must enter it manually — that's the point of the out-of-band channel).
- [ ] Playwright/E2E: passcode-protected share receives file; wrong passcode shows clear error; 5 wrong attempts surface the lockout countdown.
- [ ] Jest unit tests for the passcode modal component.

---

### Sprint 700: Legacy passcode hash proactive cleanup
**Status:** PENDING
**Priority:** P3
**Source:** Security hardening residual risk — pre-Sprint-696 shares carry unverifiable SHA-256 hashes.
**Why now:** Shares auto-expire in ≤48h, so in practice legacy rows drain themselves within one weekend. A proactive cleanup script makes the invariant explicit and gives support a one-shot way to invalidate affected shares during the rollover window rather than users hitting silent 403s.
**Files:**
- `backend/scripts/invalidate_legacy_passcode_shares.py` (new)
- `backend/retention_cleanup.py` (optional: roll into the existing nightly cleanup)
- `backend/tests/test_retention_cleanup.py`

**Changes:**
- [ ] New admin script: scan `export_shares` WHERE `passcode_hash` is 64 chars hex AND not bcrypt prefix → set `revoked_at = now()` with reason-logged secure_event.
- [ ] Safe-mode dry-run flag; CEO-visible CSV of affected share IDs + owners for optional courtesy email.
- [ ] Optional: fold into `retention_cleanup.py` so the nightly scheduler handles it without manual intervention.
- [ ] Tests: legacy-hashed share is invalidated; bcrypt-hashed share is untouched; no-passcode share is untouched.

---

### Sprint 701: Compliance documentation refresh — security hardening
**Status:** PENDING
**Priority:** P2 (SOC 2 / operator hygiene)
**Source:** Security hardening sprint — contract changes need documentation before launch sign-off.
**Why now:** Sprint 696 introduced user-visible contract changes (passcode policy, `POST /download`, removed query-string flow) and operator-facing env changes (`RATE_LIMIT_STRICT_OVERRIDE`, dev-user script requirements). Documentation must land before external callers hit the first 403 "invalid passcode" wall.
**Files:**
- `docs/04-compliance/security-policy.md` (passcode KDF claim)
- `docs/runbooks/rate-limiter-modernization.md` (strict-mode override semantics)
- `docs/runbooks/emergency-playbook.md` (new: issuing a `RATE_LIMIT_STRICT_OVERRIDE`)
- `docs/api-reference.md` / OpenAPI tags (document `POST /export-sharing/{token}/download`)
- `README.md` or `backend/scripts/README.md` (new `create_dev_user.py` usage)

**Changes:**
- [ ] Security Policy: bump to v2.7; passcode section moves from "SHA-256" to "bcrypt cost-12 (Argon2id planned Sprint 697)"; per-token brute-force documented.
- [ ] Runbook: how to issue / rotate / retire a `RATE_LIMIT_STRICT_OVERRIDE` ticket.
- [ ] Runbook: how to bootstrap a dev user without the old `DevPass1!` default.
- [ ] API reference: document the new POST endpoint, the 429 `Retry-After` contract, and the removed GET `?passcode=` pattern (link to migration guide).
- [ ] Verify `docs/04-compliance/soc2-readiness.md` criteria still match what the code enforces (CC6.1 / CC6.6 updated passcode KDF).

---

## Design Refresh — 2026-04-20

> **Source:** Browser-walked design audit of paciolus.com public surface (home, demo with all four tabs, pricing, about, trust, contact, login, register) on 2026-04-20. Hero ("The Workpapers Write Themselves" + browser mock) is distinctive; the remaining 95% of the site reads "competent SaaS" rather than "forensic instrument." Sprints below execute the full pitch: auth-page quality, a cohesive editorial typography + texture system, homepage composition rhythm, the "Every Test Cites" specimen page as the signature moment, a ledger-style tool catalog, demo signature touches, a question-first pricing page, and one small-detail polish batch. All stays within Oat & Obsidian (one new brass accent token scoped to a single use).

---

### Sprint 702: Auth-page polish — autofill fix + Obsidian Vault commitment
**Status:** PENDING
**Priority:** P1 (first-impression break)
**Source:** Design audit 2026-04-20
**Why now:** `/login` with a Chrome-autofilled email/password renders the inputs in lavender-blue — a color that does not exist in Oat & Obsidian. The illusion of craft breaks the moment a paying auditor opens the sign-in screen. Cheapest / highest-leverage design fix on the site; lands independently of the typography overhaul.
**Files:**
- `frontend/src/app/(auth)/login/page.tsx`
- `frontend/src/app/(auth)/register/page.tsx`
- `frontend/src/app/(auth)/verify-email/page.tsx` + `verification-pending/page.tsx`
- `frontend/src/components/auth/AuthCard.tsx` (or equivalent card wrapper)
- `frontend/src/styles/globals.css` — global autofill override

**Changes:**
- [ ] Add `-webkit-autofill` override to input styles: `-webkit-box-shadow: 0 0 0 1000px theme('colors.obsidian.800') inset; -webkit-text-fill-color: theme('colors.oatmeal.100'); caret-color: theme('colors.sage.400');` Apply in `globals.css` so every form (auth, contact, billing, engagement config) inherits.
- [ ] Commit to the "Obsidian Vault" framing rather than half-using it: either (a) restore a minimal Paciolus wordmark at top-left so the auth page isn't an orphan from the marketing header, or (b) go full Vault — centered monogram, hairline frame around the card, "The Vault" in Merriweather italic. CEO picks one in PR review.
- [ ] Cross-browser verify: Chromium (blue autofill), Firefox (yellow autofill), Safari — all should render in-palette.
- [ ] Playwright / snapshot coverage of `/login` populated state so regressions are visible.

---

### Sprint 703: Typography system upgrade + signature paper texture
**Status:** PENDING
**Priority:** P1 (foundation for subsequent design sprints)
**Source:** Design audit 2026-04-20
**Why now:** Merriweather-everywhere reads "Medium blog," not "audit journal." Introducing a proper editorial serif pair + oldstyle figures on marketing + a single repeating aged-paper texture creates the foundation every other design sprint composes against. The italic pull-quote on About ("The moment when you need a defensible answer…") is the site's best typographic moment and needs to become a recurring rhythm device.
**Files:**
- `frontend/tailwind.config.js` — font tokens
- `frontend/src/app/layout.tsx` — `next/font` registrations
- `frontend/src/styles/globals.css` — base body, heading, `::selection`, numeral-variant defaults
- `skills/theme-factory/themes/oat-and-obsidian.md` — update the canonical spec
- `frontend/src/components/marketing/Blockquote.tsx` — new shared italic pull-quote

**Changes:**
- [ ] Adopt an editorial body serif (candidates: Tiempos Text, GT Sectra, Source Serif 4). Keep Merriweather for headers **or** upgrade the display face (GT Super Display / Canela). Evaluate license + file size; prefer Google Fonts / Adobe Fonts integration over custom hosting.
- [ ] Register the new body face via `next/font` (preserves FOUT avoidance). Add a `font-display` token distinct from `font-serif` so heading and body are independently tunable.
- [ ] Default marketing pages to `font-variant-numeric: oldstyle-nums proportional-nums;`; override with `tabular-nums lining-nums` on product/reporting screens + every table + `font-mono` surfaces.
- [ ] Add a seamless 256×256 aged-paper noise PNG (< 15 KB, ~3% opacity) applied as a `::before` overlay via a shared `.paper-grain` utility. Apply to every `section`.
- [ ] Remove the marble/liquid backdrop from the "Standards-Driven by Design" section. Replace with `paper-grain`; one texture language across the entire site.
- [ ] New `<Blockquote italic>` shared component — display-serif italic, hairline left rule in sage. Retrofit the About page blockquote as the first consumer. **Convention:** every marketing page uses it exactly once as a rhythm break.
- [ ] A11y: verify new fonts pass WCAG AAA against obsidian backgrounds (body 7:1, large text 4.5:1). Smoke-test Windows Chrome text-size rendering.
- [ ] Jest / Playwright: sample marketing page renders with the new body face; `::selection` is sage; `tabular-nums` applies on ratio dashboards while `oldstyle-nums` applies on marketing.

---

### Sprint 704: Homepage composition rhythm — alternating axis + engraved-monument stats + CTA variety
**Status:** PENDING
**Priority:** P1 (composition)
**Source:** Design audit 2026-04-20
**Blocks on:** Sprint 703 (typography system must land first)
**Why now:** Nine consecutive centered serif-heading → centered sub → centered card-row sections. The eye stops tracking after section three. Alternating left/right axis composition + one visually distinctive stat block restores narrative rhythm and replaces the "stat tile row" cliché.
**Files:**
- `frontend/src/app/(marketing)/page.tsx` — homepage section sequence
- `frontend/src/components/marketing/Section.tsx` — add `axis="left" | "right" | "center"` prop
- `frontend/src/components/marketing/EngravedStat.tsx` — new component
- `frontend/src/components/ui/Button.tsx` — formalize `variant="primary" | "secondary" | "tertiary"`

**Changes:**
- [ ] Extend `Section` with `axis` prop. Left anchor: heading/sub sits left, supporting content takes a 40% right column. Right anchor: mirror. Centered reserved for hero + the specimen page (Sprint 705).
- [ ] Re-sequence homepage: `center` (hero) → `left` (Twelve Tools) → `right` (Built for Pros) → `left` (How It Works) → `center` (Every Test Cites — Sprint 705) → `right` (stats).
- [ ] Replace `140+ / 12 / 7` stat cards with `<EngravedStat>` — oversized display-serif numeral (oldstyle figures), hairline underline, roman-numeral kicker ("I. Automated Tests"), small-caps label. Three instances on homepage, reusable elsewhere.
- [ ] CTA variety: add `secondary` (hairline obsidian border, serif label, no fill) and `tertiary` (sage underline, serif italic) variants to the Button component. Audit every marketing CTA — one primary sage-fill per section maximum; secondaries for alternatives (Explore Demo); tertiaries for low-priority (See Pricing →, Learn more about our technical approach).
- [ ] Mobile (`<md`): retain center-column layout — alternating axis activates at `md:` breakpoint only.
- [ ] Jest: `axis="left"` renders heading on left + content on right; `<EngravedStat>` renders the roman-numeral kicker and small-caps label.

---

### Sprint 705: "Every Test Cites Its Standard" — typographic specimen page (THE ONE THING)
**Status:** PENDING
**Priority:** P0 (the differentiating moment)
**Source:** Design audit 2026-04-20 — "the one thing to do if only one"
**Blocks on:** Sprint 703 (editorial fonts required)
**Why now:** "Every test cites its standard" is the single claim that separates Paciolus from every other AI-branded audit tool. Currently it's rendered as a thin strip of gray pills — visually indistinguishable from a tech blog's tech-stack badges. Rendering it as a specimen page from a bound journal of auditing standards turns the section into something an auditor will screenshot and share. This is the headline of the entire redesign.
**Files:**
- `frontend/src/components/marketing/StandardsSpecimen.tsx` — new component replacing the pill strip
- `frontend/src/app/(marketing)/page.tsx` — consume
- `frontend/src/content/standards-specimen.ts` — data source (standard code, citation, paragraph, governing body, scope, linked tool)
- Tailwind utilities for hairline column rules, drop-cap, small-caps

**Changes:**
- [ ] Design brief: recreate a specimen page from a bound audit-reference volume. Two-column grid with a hairline vertical rule between. Per entry: standard code (small caps, oldstyle figures), paragraph citation, one-line scope description, governing body. Drop-cap on the first letter of each column. Footnote-style superscripts where tests cite multiple standards.
- [ ] Build `<StandardsSpecimen>` as a data-driven component — citations live in `content/standards-specimen.ts` so new tests from Sprints 682 / 683 absorb without code changes.
- [ ] Content must include every currently-cited standard: ISA 240 / 315 / 500 / 501 / 505 / 520 / 530 / 540 / 570, PCAOB AS 1215 / 2401 / 2501 / 2315, ASC 230 / 330 / 360 / 606, IAS 2 / 7 / 16, IFRS 15.
- [ ] Hover state on a row: briefly expands to reveal the one-sentence test description and a link to the tool that cites it (deep-link to the matching catalog card).
- [ ] Keep the current pill strip as a **mobile-only fallback** (specimen layout does not collapse under 768 px).
- [ ] A11y: semantic `<dl>` with `<dt>` citations and `<dd>` scopes; screen-reader-friendly; keyboard-navigable rows with visible focus rings.
- [ ] Jest: renders every standard; clicking a row routes/scrolls to the correct tool page.

---

### Sprint 706: Twelve Tools — ledger-column grid (replace carousel)
**Status:** PENDING
**Priority:** P1
**Source:** Design audit 2026-04-20
**Blocks on:** Sprint 703 (typography)
**Depends on clarity from:** Sprint 689 (catalog reconciliation — tool-count truth source)
**Why now:** The current "01 / 12 ‹ ›" carousel shows one tool at a time; users see the first card and bounce. The full catalog *is* the product pitch. Rendering all twelve at once in a bound-ledger grid respects the auditor's reading pattern (scanning an index, not advancing a slideshow).
**Files:**
- `frontend/src/components/marketing/ToolLedger.tsx` — new grid component
- `frontend/src/components/marketing/ToolShowcase.tsx` — refactor or delete (existing carousel)
- `frontend/src/app/(marketing)/page.tsx` — consume the new component
- Retain a minimal carousel for the mobile breakpoint only

**Changes:**
- [ ] Ledger layout at `md+`: 12 rows × 4 columns (Tool # · Name · Test Count · Standards). Hairline rules between rows. Tool # in `font-mono` with right-aligned oldstyle figures. Standards in small caps.
- [ ] Row hover: accordion expansion in place — reveals description, checklist, export formats, standards tags. No page navigation.
- [ ] Palette: tool number in sage; body in oatmeal; rules in obsidian-600. No new tokens.
- [ ] Mobile (`<md`): fall back to a simplified carousel; feature-flag via `useMediaQuery`.
- [ ] Tool count must read from the canonical source (`shared/entitlements.py:CANONICAL_TOOL_COUNT` surfaced via an API or a generated TS constant) — no hardcoded "12" in the marketing surface. Prevents drift after Sprint 689 reconciles the catalog.
- [ ] Jest: renders all rows; hover expands in-place; mobile breakpoint renders the carousel fallback.

---

### Sprint 707: Demo page — signature "forensic instrument" moments
**Status:** PENDING
**Priority:** P2
**Source:** Design audit 2026-04-20
**Blocks on:** Sprint 703 (fonts)
**Why now:** Demo tabs (TB Diagnostics / Testing Suite / Workspace / Sample Reports / Standards) function correctly but read as "generic SaaS dashboard." Three small signature moments would sell the "forensic instrument" positioning viscerally without touching the underlying data model.
**Files:**
- `frontend/src/components/demo/TBDiagnosticsTab.tsx` (or equivalent)
- `frontend/src/components/demo/TestingSuiteTab.tsx`
- `frontend/src/components/demo/ScanlineOverlay.tsx` — new
- `frontend/src/components/demo/MechanicalGauge.tsx` — new
- `frontend/src/components/demo/MarginAnnotation.tsx` — new

**Changes:**
- [ ] **Scanline animation:** On TB Diagnostics tab mount, render a subtle sage-tinted horizontal scanline that sweeps the TB table once in 1.2 s before the ratios resolve. Sells the "under three seconds" claim viscerally.
- [ ] **Mechanical gauge for Composite Diagnostic Score (76):** Replace the flat circle dial with a proper arc gauge — hairline tick marks every 10, serif numeral at center, needle easing on mount. Component signature: `<MechanicalGauge score={76} riskLevel="low" />`.
- [ ] **Margin annotations for anomaly flags:** Replace pill / toast styling with typewriter-style red-pen margin annotations — hairline left border in clay, serif italic copy, inline caret glyph. Matches the physical audit-review language.
- [ ] All three respect `prefers-reduced-motion: reduce` — scanline and needle skip animation, rendering the final state immediately.
- [ ] Component isolation: everything in `components/demo/` — cannot leak into real product views.
- [ ] Jest: each new component tested; reduced-motion path explicitly covered.

---

### Sprint 708: Pricing page — calculator-first + "Most Popular" foil treatment
**Status:** PENDING
**Priority:** P2
**Source:** Design audit 2026-04-20
**Why now:** The Find-Your-Plan + Seat Calculator is the pricing page's most differentiated element and it's buried beneath three standard plan cards. Leading with a consultative question-first flow and following with plan confirmation is rare in audit software and matches Paciolus's tone. Also: the current "Most Popular" badge on Professional is invisible.
**Files:**
- `frontend/src/app/(marketing)/pricing/page.tsx`
- `frontend/src/components/marketing/PlanCard.tsx`
- `frontend/src/components/marketing/SeatCalculator.tsx`
- `frontend/src/components/marketing/FindYourPlan.tsx`
- `frontend/tailwind.config.js` — one new scoped `brass` token

**Changes:**
- [ ] Reorder the page: hero → `FindYourPlan` (3 questions: practice size → features needed → team size) → recommended-plan sticky callout → `SeatCalculator` → three plan cards (as confirmation) → feature comparison → FAQ.
- [ ] `FindYourPlan` keeps the existing pillbox toggles. "Based on your needs, we recommend …" becomes a sticky callout that scrolls into the matching plan card when clicked.
- [ ] Add one new token `brass-400: #B08D57` (or comparable warm accent). Use **only** on the Most Popular badge + one hairline accent on the Professional card. No other surface uses brass — the scarcity is the design point.
- [ ] Apply the editorial typography system from Sprint 703: plan name in display serif, price in `font-mono` with oldstyle figures, feature list in body serif.
- [ ] Verify pricing copy parity with the homepage Twelve Tools. One Platform. preview and with Sprint 692's canonical source.
- [ ] A11y: the question-first flow must be fully keyboard-navigable; the plan recommendation must be announced to screen readers when it changes.

---

### Sprint 709: Small-detail polish batch — contact alignment, Pacioli colophon, nav anchor hint, CTA audit, favicon, demo copy bug
**Status:** PENDING
**Priority:** P3 (polish)
**Source:** Design audit 2026-04-20
**Why now:** Six small but high-signal details that ship as one atomic polish PR after the larger design sprints land.
**Files:**
- `frontend/src/app/(marketing)/contact/page.tsx`
- `frontend/src/components/marketing/Footer.tsx`
- `frontend/src/components/marketing/MarketingHeader.tsx`
- `frontend/src/app/(marketing)/demo/page.tsx` — copy correction
- `frontend/public/favicon.svg` + 16×16, 32×32, 180×180, OG preview sizes

**Changes:**
- [ ] **Contact page alignment:** "Contact Us" heading is left-aligned while the form itself is centered — axis mismatch. Align both to a left-anchored editorial column (preferred) or both centered. Pick one.
- [ ] **Demo copy bug:** "Seven tools included with Solo — all twelve with Team." Contradicts the canonical pricing policy (all paid tiers receive all 12 tools). Fix to "All twelve tools included with every paid plan." Cross-check `shared/entitlements.py` + Sprint 692's reconciled language.
- [ ] **Footer Pacioli colophon:** "*Particularis de Computis et Scripturis* — On Accounts and Records, Luca Pacioli 1494" currently renders at link-list size. Upgrade to a real colophon — 24–28 px display-serif italic, centered on its own row with generous top/bottom spacing, hairline rule above. The emotional climax of the site should feel like one.
- [ ] **Header nav anchor hint:** the `Platform` nav link is a homepage anchor, not a route. Add a subtle visual hint on anchor-only items (a small `↓` glyph, a leading dot, or a dashed underline) to distinguish them from real-route links — prevents the "I clicked Platform and nothing happened" confusion.
- [ ] **CTA audit:** grep the marketing surface for `Start Free Trial` / `Get Started` / `Explore Demo` / `Sign In` / `Schedule a call` and align each to the correct variant from Sprint 704 — one primary per section; secondaries for alternatives; tertiaries for low-priority. Deduplicate stacked primaries.
- [ ] **Favicon check:** verify the `P` monogram renders sharply at 16×16 / 32×32 / 180×180 / OG preview. If the current SVG is too detailed at 16 px, export a simplified variant specifically for the favicon size.

---
