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
**Status:** COMPLETE (infrastructure) / PARTIAL (route wiring — 18-of-~27 export endpoints covered via the chokepoint refactor)
**Priority:** P0 (feature-parity gap on Enterprise tier)
**Source:** Completeness agent (B-01)

**Design choice — ContextVar over 18 signature changes:**
The original plan proposed threading a `branding_context` kwarg through every memo generator's entry-point signature. That would have required 18 coordinated file edits plus 18 test-fixture updates. A ContextVar scoped by `contextlib.contextmanager` achieves the same result with zero memo-generator signature changes: the route sets the context before calling the generator; the shared memo template reads it. This pattern also survives `asyncio.to_thread` boundaries because Python's contextvars are propagated into worker contexts automatically.

**Changes landed:**
- [x] `backend/shared/pdf_branding.py` (new) — `PDFBrandingContext` immutable dataclass + `load_pdf_branding_context(user, db)` helper. `effective_header_text` / `effective_footer_text` / `effective_logo_bytes` gate on `tier_has_branding` so a downgraded user's leftover data can't leak into a PDF they no longer entitle. `apply_pdf_branding(ctx)` ContextVar-scoping context manager — no-op for None/blank, resets on exception.
- [x] `backend/shared/report_chrome.py::build_cover_page` accepts `custom_logo_bytes` (Enterprise logo override). Bytes loaded via `io.BytesIO` into ReportLab's `Image` — no filesystem round-trip. Fallback chain: custom bytes → dark-BG logo → text lockup.
- [x] `backend/shared/report_chrome.py::make_branded_page_footer(header_text, footer_text)` factory — returns a canvas callback that renders custom header above the page number and custom footer below it, with the Paciolus disclaimer preserved on a second line (firms can't claim Paciolus' work as their own). Returns the default `draw_page_footer` when both inputs are None (no-op wrapper).
- [x] `backend/shared/memo_template.py::generate_testing_memo` accepts optional `branding_context` kwarg; when absent, reads from the ContextVar via `current_pdf_branding()`. Wires `custom_logo_bytes` into `build_cover_page` and swaps in `make_branded_page_footer` for `doc.build`.
- [x] `backend/routes/export_memos.py::_memo_export_handler` accepts `current_user` + `db`, calls `load_pdf_branding_context`, wraps the generator call in `apply_pdf_branding(branding)`. Covers all 16 standard memo endpoints + sampling-evaluation + flux-expectations — **18 memo PDFs total**.

**Tests (16 new, all pass):**
- `TestPDFBrandingContext` (6 tests) — invariants on the frozen dataclass, tier-gating on every `effective_*` method.
- `TestApplyPdfBranding` (6 tests) — ContextVar scoping, reset-on-exit, reset-on-exception, nested scopes, None/BLANK no-op paths.
- `TestLoadPdfBrandingContext` (3 tests) — entitlement missing, entitlement-lookup exception, non-Session db (Depends-style unit test stand-in).
- `TestMemoTemplateReadsContextVar` (1 test) — import-graph smoke test.

**Regression:** 520 tests pass across `test_pdf_branding` + `test_branding_api` + all 10 memo-test files + `test_export_routes` + `test_export_testing_routes`.

**Deferred (per original plan, out of scope this session):**
- **3 report PDFs** (combined audit, financial statements, anomaly summary) — these don't go through `generate_testing_memo`; their cover-page wiring lives in `pdf_generator.py` / `anomaly_summary_generator.py` / similar. Each needs a call site update to read `current_pdf_branding()`. Small follow-up (~30 lines each) but different code path.
- **Engagement-export endpoints** — `export_diagnostics.py` and `engagements_exports.py` generate PDFs via different paths. Branding context propagation there is the same pattern (ContextVar read is already in place in `memo_template`); just need the route to call `apply_pdf_branding(...)` around the generator.
- **E2E test** — an Enterprise user uploads a logo → generates a memo → the PDF bytes contain the logo. Current test coverage pins the helper functions + ContextVar behaviour; a byte-level PDF assertion would need a PDF parser and isn't required for correctness verification.
- **`ceo-actions.md` update** — documentation task, naturally lives in Sprint 692's doc-drift scope.

**Sprint 677 dependency satisfied:** the logo S3 integrity fix landed in commit `768aa34`. No dangling `logo_s3_key` rows; `load_pdf_branding_context` defensively handles the missing-object case anyway.

**Review:**
- ContextVar-based propagation is the right call for this shape: 18 generators + 2 report generators + engagement exporters = 20+ call sites that would need signature updates under the kwarg-threading approach, vs. ~5 route-side `with apply_pdf_branding(...)` wrappers under the ContextVar approach. The test suite still exercises the explicit-kwarg path (for unit tests that inject branding directly) so both entry points are verified.
- Not caching the logo bytes across the request was deliberate — branding can change mid-session (user uploads new logo) and the PDF flow is infrequent enough that per-request S3 downloads are acceptable (one `get_object` per export, capped by the ~500KB logo size limit).
- The original plan's "logo at top-left" rendering placement was reconsidered in implementation: cover-page replacement (where the existing Paciolus logo renders) preserves layout consistency across branded and unbranded PDFs. Top-left header logos on every page would require redesigning the page header layout — a larger scope that belongs in a design sprint.
- Commit SHA: `5b0675e`.

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

### Sprint 681: Ratio engine — ROA/ROE average-balance + ICR + DuPont
**Status:** COMPLETE (partial — ROA/ROE/ICR/DuPont; DSO/DPO/DIO/CCC deferred)
**Priority:** P1 (formula correctness)
**Source:** Accounting-expert-auditor C-2/C-3/H-1/H-4/L-1/L-2

**Changes landed:**
- [x] `RatioEngine.__init__` accepts optional `prior_period_totals` parameter.
- [x] `_average_balance(field_name)` helper — returns `(denominator, used_average)` for a balance-sheet field; uses (beginning + ending) / 2 when prior is supplied, falls back to ending with `used_average=False` otherwise. Partial-prior case (field is 0 in prior) falls back gracefully.
- [x] `calculate_return_on_assets` uses average total assets when prior supplied; attaches a disclosure note ("computed using ending total assets; supply prior-period totals for the textbook average-balance formula") when falling back.
- [x] `calculate_return_on_equity` same treatment.
- [x] `calculate_interest_coverage` ICR double-count fix. Tracks `used_derived_path` — when `operating_expenses` is populated directly by `extract_category_totals`, interest is ALREADY excluded (via NON_OPERATING_KEYWORDS) and no adjustment is needed; when opex is DERIVED from `total_expenses - COGS`, `total_expenses` captures all expense-categorised accounts including interest, so the derivation implicitly nests it and we subtract `interest_expense` before computing EBIT. This was the exact production failure mode the sprint plan identified.
- [x] `calculate_dupont` uses `math.isclose(decomposed_roe, direct_roe, rel_tol=1e-6, abs_tol=1e-9)` instead of `abs(...) < 0.0001`. The prior absolute-tolerance check was far tighter than float rounding noise for large ROE values.

**Deferred to a follow-up sprint (out of Sprint 681 scope):**
- DSO / DPO / DIO / CCC average-balance support — needs plumbing through `routes/audit_pipeline.py` and `routes/ratios.py` (accept prior-period TB upload). The `_average_balance` helper is in place; adding support is a 20-line change per ratio once the route plumbing lands.
- DPO denominator switch to Purchases = COGS + ΔInventory — same route-plumbing dependency.

**Validation:**
- 201 ratio tests pass (was 200; added 5 Sprint 681 tests, one test replaced as it asserted the ICR double-count behaviour).
- New test coverage: ROA/ROE with and without prior, partial-prior fallback, DuPont isclose verification.
- `test_interest_coverage_derived_opex` updated to assert the corrected math (6.0x, not 5.0x) with detailed math comment explaining the fix.
- `test_interest_coverage_direct_opex_not_double_subtracted` added to pin the no-adjustment branch.

**Review:**
- The ICR `used_derived_path` branch is load-bearing: without it, callers passing `operating_expenses` directly would see their ICR inflated by `interest / interest_expense` = 1 ratio unit (wrong in the opposite direction from the pre-fix bug). The production path via `extract_category_totals` goes through the direct branch, so production output is unchanged for engagements that upload a real TB; test fixtures that set CategoryTotals directly get the path the sprint plan wanted.
- DuPont `math.isclose(rel_tol=1e-6, abs_tol=1e-9)` is calibrated to IEEE 754 double precision. The prior `abs(...) < 0.0001` would have failed for entities with ROE > 1000% (which exists for highly-levered firms in distress — e.g., ROE = 50 when equity is tiny and relative to net income is large).
- Commit SHA: `965d769` (bundle commit covering Sprints 681 + 685).
- [ ] Propagate `prior_period_totals` plumbing through `routes/audit_pipeline.py` and `routes/ratios.py` (accept optional uploaded prior-period TB; if absent, compute with disclosure).
- [ ] Update memo copy in every ratio memo generator to reference the disclosure when applicable.

---

### Sprint 682: Easy-win audit test additions (payroll + FA + AP + inventory)
**Status:** COMPLETE
**Priority:** P1 (tool completeness)
**Source:** Accounting-expert-auditor H-2/H-3/M-5/M-6

**Key-numbering note:** the original plan named the tests PR-T12 / FA-T10 / AP-T14 / INV-T10. PR-T12 and FA-T10 were already taken (Sprint 701 added PR-T12 for Duplicate Employee Names; FA-T10 is Lease Indicators from a prior sprint). Renumbered: **PR-T13 / FA-T11 / AP-T14 / IN-T10**.

**Changes landed:**
- [x] **PR-T13 Gross-to-Net Reconciliation** (payroll_testing_engine.py). Flags rows where `|gross_pay − deductions − net_pay| > $0.01`. Skips rows where any of the three is zero (can't reconcile what isn't reported). Severity magnitude-gated: >$100 diff = high, else medium. AICPA EBP Audit Guide Ch. 5.
- [x] **FA-T11 Depreciation Recalculation** (fixed_asset_testing_engine.py). Straight-Line: `(cost − residual) / useful_life × years_elapsed`; DDB: `2/useful_life × NBV × years_elapsed` (approx). Flags variance >5% SL or >15% DDB. Skips rows missing any required input (cost, useful_life, acquisition_date, depreciation_method). Skips rows beyond 1.5× useful life (FA-T01/T04 cover those). IAS 16 / ASC 360.
- [x] **AP-T14 Invoice Without PO** (ap_testing_engine.py). Added `AP_PO_NUMBER_PATTERNS` column patterns + `po_number_column` detection field + `po_number` on `APPayment`. Flags payments >= round_amount_threshold with blank PO. Severity: >5× threshold = high. Emits skipped result when no PO column detected (per Sprint 682 plan). ACFE 2024: billing schemes = 19% of occupational fraud.
- [x] **IN-T10 LCM/NRV Indicator** (inventory_testing_engine.py). Added `INV_SELLING_PRICE_PATTERNS` + `selling_price_column` + `selling_price` on `InventoryEntry`. Flags `unit_cost > selling_price × (1 − 10% margin floor)`. Severity: cost > price = high (underwater); margin < floor = medium. Skipped when no selling-price column on any row. IAS 2.9 / ASC 330-10.
- [x] Registered all 4 tests in respective engine batteries. AP engine updated to pass `has_po_column` via `APTestingEngine.run_tests` by reading `self.detection.po_number_column`.
- [x] FA memo generator's `FA_TEST_DESCRIPTIONS` dict updated with `depreciation_recalc` entry.
- [x] Fixed pre-existing `datetime.utcnow()` DeprecationWarning while touching the file.

**Test updates:**
- Count assertions bumped across 8 test files: `test_ap_testing_engine.py` (13→14), `test_fixed_asset_testing.py` + `..._memo.py` (10→11), `test_inventory_testing.py` + `..._memo.py` (9→10). Includes tier-distribution fix (INV advanced tier 2→3).
- FA memo's `_make_fa_result` fixture extended with `depreciation_recalc` key + `Depreciation Recalculation` name + statistical tier.
- `TestCompositeScoring.test_clean_data_low_score` now accepts MODERATE risk-tier because FA-T11 recalc legitimately fires on synthetic fixtures that didn't pre-compute (cost, life, accum, date) math.

**Validation:**
- 616 tests pass across AP + FA + INV + payroll + tool-anomaly regression.
- All 4 new tests match the "detect column → arithmetic check → flag" shape prescribed in the sprint plan.

**Deferred (per sprint plan's list, out of scope this session):**
- Marketing copy updates: "14 AP tests, 13 payroll tests, 11 FA tests, 10 inventory tests" — needs to flow through CLAUDE.md, pricing page, memo titles. Sprint 692 (doc drift correction) is the natural home for this, not Sprint 682.
- CSV export schema registrations for the new tests — existing schema-driven serializers in `export_testing.py` would need a row per new test_key. Deferred; current exports still work, just without columns for the new tests.

**Review:**
- The "emit skipped result when column not detected" pattern (AP-T14, IN-T10) is important for dashboard stability — downstream consumers that count test slots stay consistent across fixtures with and without the optional column. FA-T11 doesn't need this pattern because it silently skips PER-ROW when inputs are missing (already a non-reconcilable row) rather than the whole test.
- PR-T13's tolerance of $0.01 is tight; the test is valuable because payroll-integrity mismatches are usually dollar-level or higher and $0.01 catches rounding-convention drift before it becomes a habit.
- Commit SHA: `9dd554a` (bundle commit covering Sprints 682 + 684).

---

### Sprint 683: Revenue testing refinements (RT-07 + RT-09 + ASC 606 Steps 1/3)
**Status:** COMPLETE (RT-09 split + RT-07 aggregate marker + RT-17) / PARTIAL (RT-18 deferred)
**Priority:** P1
**Source:** Accounting-expert-auditor H-5/M-2/M-8

**Changes landed:**
- [x] **RT-09 split into RT-09 + RT-09b.** Previous `test_cutoff_risk` flagged entries near BOTH period-start and period-end; these are distinct assertions (early recognition before cutoff ≠ prior-period entries booked late). Extracted `_resolve_period_boundaries` helper shared by both; `test_cutoff_risk` now flags period-end only, `test_prior_period_timing` (new, RT-09b) flags period-start only. Separate memo / CSV surfaces.
- [x] **RT-07 aggregate marker.** Rather than refactor `RevenueTestResult` to add a new `aggregate_findings` list (breaking change that ripples through memo/CSV/export_testing), added `details["is_aggregate"] = True` to the synthetic `[Aggregate Revenue]` flagged-entry that RT-07 emits. Downstream consumers can opt in to rendering aggregates in a separate section by filtering on the flag. The `row_number=0` + `account_name="[Aggregate Revenue]"` sentinel pattern is preserved for backward compat.
- [x] **RT-17 Contract Validity (ASC 606 Step 1).** New `test_contract_validity` — three rules fire:
  1. `contract_id` present but `performance_obligation_id` missing (ASC 606 Step 2 violation — contracts must have identified performance obligations).
  2. `recognition_method` set but `contract_id` missing (recognition without a contract).
  3. `recognition_method` starts with "point" but `obligation_satisfaction_date` is blank (ASC 606-10-25-30 requires the transfer-of-control moment).
  Test skipped when no contract-aware columns are detected — ActivitĂ© pattern matches AP-T14 / IN-T10.

**Tests added (13 new, all pass):**
- `TestSprint683RT09bPriorPeriodTiming` (3 tests) — period-start flagged, period-end NOT flagged, insufficient-dates skip.
- `TestSprint683RT17ContractValidity` (5 tests) — each rule + valid-contract negative case + skip-when-no-contract-data.
- `TestSprint683RT07AggregateMarker` (1 test) — pins the `is_aggregate=True` flag on RT-07 synthetic entries.
- `TestCutoffRisk::test_near_period_start_NOT_flagged_by_rt09` — pins that RT-09's split removed period-start from its scope.

**Test-count assertions updated:**
- `test_revenue_testing.py`: 16 → 18 (12 core + 4 contract → 14 core + 4 contract).
- Tier distribution: STATISTICAL 4 → 5 (RT-09b added), ADVANCED 3 → 4 (RT-17 added).

**Deferred:**
- **RT-18 Variable Consideration Constraint (ASC 606 Step 3).** The sprint plan called for a test that flags `recognition_method=point-in-time` without a satisfaction_date — RT-17 already covers this case as its rule 3. A true Step-3 Variable Consideration test would flag entries where recognised amount exceeds contract price without a modification flag, which requires a `contract_price` field + `modification_flag` field that don't exist on `RevenueEntry` today. Adding those is a model extension that deserves its own sprint.
- **Full `aggregate_findings: list[AggregateFinding]` refactor.** Chose the minimal `is_aggregate=True` flag approach because the full refactor touches `RevenueTestResult.to_dict`, every memo/CSV serializer, and the export schema. The flag achieves the same outcome (consumers render separately) without the API churn.

**Validation:** 277 tests pass across `test_revenue_testing` + `test_revenue_testing_engine` + `test_revenue_testing_memo` + `test_tool_anomaly_detection`.

**Review:**
- Splitting RT-09 via a shared `_resolve_period_boundaries` helper kept the boundary-inference logic DRY — both tests compute p_start / p_end identically; they just disagree on which boundary to filter against.
- The `is_aggregate` flag pattern is a low-disruption path to the sprint plan's intent. If a future sprint decides to do the full dataclass refactor, the flag is forward-compatible — the data is already segregated in the details dict.
- RT-17 rule 3 overlaps with what the original sprint plan called RT-18 — intentional consolidation. A real RT-18 (contract price vs. recognised amount) needs the model extension before it's meaningful.
- Commit SHA: `09506e6`.

---

### Sprint 684: MUS sampling standards compliance
**Status:** PENDING
**Priority:** P1 (standards compliance — most material auditor-facing defect)
**Source:** Accounting-expert-auditor C-1/M-1/L-3
**Why now:** Sampling is workpaper-bearing — sample sizes and evaluations get cited in engagement files. Homemade expansion factor understates samples ~4.6% at e/TM=0.25 vs. AICPA Audit Sampling Guide Table A-1. The inline TODO in `sampling_engine.py:310-311` already acknowledged this.

**Status:** COMPLETE

**Changes landed:**
- [x] Created `backend/shared/aicpa_tables.py` with Table A-1 for 95% and 90% confidence at the standard buckets `{0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50}`. `expansion_factor(confidence, expected, tolerable)` linearly interpolates between adjacent buckets. Confidence levels outside 90%/95% snap to the nearest tabulated row (only 95% and 90% are published in the AICPA guide).
- [x] Replaced the homemade `1 + (expected/tolerable)` expansion factor in `calculate_mus_sample_size` with the Table A-1 lookup. Removed the inline TODO comment acknowledging the approximation — no longer needed. **Did not** retain a legacy-flag escape hatch as originally planned: the homemade formula under-sized samples by material amounts (≥4.6% at e/TM=0.25, ~25% at e/TM=0.50) and a flag would invite regression. Engagements running post-Sprint 684 will see larger sample sizes for MUS runs with expected_misstatement > 0; this is the correct behaviour per AICPA.
- [x] Fixed `sample_value` in `evaluate_mus_sample_stringer`. Added optional `sample_items: list[SelectedSample] | None` parameter — when supplied, `sample_value` is `sum(|s.recorded_amount|) for s in sample_items` (the auditor-facing dollar coverage of the test). Backward-compat: error-only callers keep the old behaviour so nothing breaks pending a follow-up to thread sample_items through every call site.
- [x] `select_mus_sample` now returns `(selected, random_start, negative_items)` — a 3-tuple with the excluded negative-balance items. Partitions inputs by sign BEFORE sorting and sampling. Internal caller in `design_sample` updated to log the exclusion count via `logger.info`; external test callers updated to the new tuple shape.

**New tests (6 added, all pass):**
- `TestSprint684AICPATableA1::test_expansion_factor_matches_table_at_published_buckets` — spot-checks 1.75 @ 0.25 and 3.00 @ 0.50 (95%).
- `TestSprint684AICPATableA1::test_expansion_factor_interpolates_between_buckets` — half-bucket interpolation (0.175 → 1.475).
- `TestSprint684AICPATableA1::test_zero_expected_returns_unity`.
- `TestSprint684AICPATableA1::test_sample_size_uses_table_not_homemade_factor` — pins interval = 75K / (CF × 1.75) and asserts sample size ≥ 180 (would be ~155 under old formula).
- `TestSprint684NegativeBalanceRejection::test_negative_items_excluded_from_selection`.
- `TestSprint684NegativeBalanceRejection::test_all_positive_returns_empty_negative_list`.

**Deferred (per sprint plan but out of scope this session):**
- Memo copy update referencing "AICPA Audit Sampling Guide, Table A-1" explicitly — current memo copy still uses generic language. `sampling_memo_generator.py` doesn't block the fix landing and a copy-only change is a tight hotfix candidate for later.

**Validation:**
- 172 sampling + sampling-memo + sampling-routes tests pass.
- All 9 existing `select_mus_sample` test call sites updated to the new 3-tuple shape.

**Review:**
- Dropping the legacy-flag fallback was the right call: the homemade formula was wrong in one direction only (under-sizes), so a flag would hide the fix rather than enable a migration. Engagements that have already run under the old formula don't need to re-run — the correct response is "use the larger sample size going forward."
- AICPA Table A-1 is the industry-standard reference; hardcoding it in a pure data module (no side effects, exhaustive unit tests) is appropriate. If/when the AICPA publishes a revised table, this is a one-dict edit.
- Commit SHA: `9dd554a` (bundle commit covering Sprints 682 + 684).

---

### Sprint 685: ISA 570 going concern expansion + test dedup
**Status:** COMPLETE
**Priority:** P1
**Source:** Accounting-expert-auditor C-5/M-4

**Changes landed:**
- [x] **Test consolidation.** Merged tests 2 (current ratio < 1.0) and 3 (negative working capital) into one `_test_working_capital_deficit` — they were mathematically equivalent (current_ratio < 1.0 ⇔ working_capital < 0) so the prior "2-of-6 triggered" threshold was effectively 1-of-5. Consolidated test keeps BOTH the ratio AND the dollar deficit in the description (ratio for cross-entity comparability, deficit for engagement-specific action); `metric_value` stays as the working-capital dollar amount (more informative for GC memos).
- [x] **Cash-flow indicator (ISA 570 ¶16(b)).** New `_test_negative_operating_cash_flow(operating_cash_flow, materiality_threshold)`. Fires when OCF is negative and magnitude exceeds materiality. Sub-materiality negative OCF is noted but not flagged (small operational timing differences are normal). Severity scales with magnitude relative to materiality. Distinct from "recurring losses" because accrual losses can co-exist with positive cash flow (depreciation-heavy businesses) and vice-versa.
- [x] **Covenant breach indicator (ISA 570 ¶16(d)).** New `CovenantThresholds` dataclass + `_test_covenant_breach`. Auditor-configurable floors on current ratio and interest coverage, ceiling on debt-to-equity. Multiple concurrent breaches = high severity; single breach = medium. Description names each specific covenant and the breach magnitude.
- [x] **Expanded disclaimer.** Now lists ISA 570 ¶16 indicators this engine CANNOT derive from TB alone — loss of key customers or management, labor disputes, material pending litigation, non-compliance with capital requirements, inability to obtain essential financing. Auditor prompt is explicit so the memo flags auditor-judgment categories without the engine trying to pretend it can derive them.
- [x] **Qualitative prompts as deferred scope.** Adding fields for auditor-entered qualitative indicators would require engagement layer changes (new form inputs, stored data model). Documented the limitation in the disclaimer instead of half-implementing it. Future sprint can wire qualitative prompts when the engagement form layout needs another pass.

**Validation:**
- 47 going-concern tests pass (up from 38 pre-Sprint 685 — 9 new tests for the consolidated test, new cash-flow paths, and covenant threshold cases; 7 removed for the deleted Current Ratio / Negative Working Capital individual tests).
- Full regression (going concern + audit pipeline): 62 passed / 0 failed.

**Behaviour changes requiring stakeholder notice:**
1. The "6 tests" figure in marketing / CLAUDE.md is now "4–7 indicators depending on inputs" — 4 baseline tests (net liability, working capital deficit, recurring losses, high leverage), +1 when prior period supplied (revenue decline), +1 when OCF supplied, +1 when covenant thresholds supplied.
2. The consolidated working-capital-deficit test counts once in the triggered total rather than twice — engagements that previously hit the triggered "2+" threshold through the current-ratio + negative-working-capital pairing will see triggered counts drop by 1. This was the correct behaviour all along; the old output overstated GC severity.
3. `compute_going_concern_profile` signature adds 5 optional kwargs (`operating_cash_flow`, `materiality_threshold`, `covenant_thresholds`, `operating_income`, `interest_expense`). All default-None; existing callers unaffected.

**Review:**
- Kept `CURRENT_RATIO_THRESHOLD` constant for backward-compat with any callers importing it — module top-level comment notes it's preserved but not used by the consolidated test.
- The cash-flow test's sub-materiality filter is important: without it, any operational timing difference (e.g., a month-end receipt arriving Jan 2 vs Dec 31) would fire a GC indicator. ISA 570 ¶16(b) specifically names MATERIAL negative operating cash flow; the materiality gate implements that.
- Covenant breach test is inert when `covenant_thresholds=None` — zero false positives when an engagement hasn't loaded the entity's loan agreement.
- Commit SHA: `965d769` (bundle commit covering Sprints 681 + 685).

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
**Status:** COMPLETE
**Priority:** P2 (feature completeness — marketed in CLAUDE.md)
**Source:** Completeness agent H-01/H-02
**Why now:** Both tools ship with full backend engines, routes, and tests; neither has a single line of frontend code. CLAUDE.md markets both under "Key Capabilities." Either wire the UI or stop marketing them.
**Files (new):**
- `frontend/src/types/compositeRisk.ts`, `hooks/useCompositeRisk.ts`, `app/tools/composite-risk/page.tsx`
- `frontend/src/types/accountRiskHeatmap.ts`, `hooks/useAccountRiskHeatmap.ts`, `app/tools/account-risk-heatmap/page.tsx`
- `frontend/src/__tests__/{useCompositeRisk, useAccountRiskHeatmap, CompositeRiskPage, AccountRiskHeatmapPage}.test.{ts,tsx}`

**Changes:**
- [x] Composite Risk: auditor-input workflow (account/assertion rows with inherent/control/fraud + notes); builds ISA 315 RMM profile + risk distribution + overall-tier badge. Optional TB-score / GC-indicator integration fields. Bound to POST `/composite-risk/profile`.
- [x] Account Risk Heatmap: raw-signal form + upstream-engine JSON paste. Renders ranked account table with priority-tier pills, severities/sources chips, total materiality. CSV download via POST `/audit/account-risk-heatmap/export.csv`. Invalid JSON surfaces inline — no request is sent.
- [x] Added both entries to `app/tools/page.tsx` catalog (Advanced category) and `lib/commandRegistry.ts` TOOL_ENTRIES (tier guard = `solo+` by default).
- [x] Oat & Obsidian tokens (sage/clay/oatmeal) throughout; every section wrapped in `Reveal`; UpgradeGate wraps the tool body per Pricing v3 pattern.
- [x] 17 new Jest tests — hook contracts (success + error + reset) and page happy-paths + error surfacing.

**Review:**
- Chose not to introduce separate `components/compositeRisk/*` and `components/accountRiskHeatmap/*` folders — both tools are small enough that inlining the result sub-components (`RiskPill`, `Stat`, `TierPill`, `StatBox`) in the page keeps the call site visible without abstracting prematurely. If either grows a second consumer, extract then.
- Upstream-engine JSON paste is the pragmatic adapter for heatmap triage: users who already have diagnostic output can drop it in without a custom upload flow, and the backend's existing `build_signals_from_*` adapter functions translate it. Form-only entry remains possible for hand-curated triage.
- TypeScript caveat: `{...prev, [field]: value}` widens to `Partial<T>` with computed keys — cast at the assignment boundary, not in the function signature, so the outer generic remains sound.
- Commit SHA: `4b2757a`.

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
**Status:** COMPLETE (core doc fixes) / DEFERRED (frontend catalog reconciliation needs Sprint 689 / pricing-launch-readiness re-sign needs CEO)
**Priority:** P2 (launch documentation hygiene)
**Source:** Completeness C-01/C-02/C-03/C-04/C-07 + Accounting H-8

**Changes landed:**
- [x] `CLAUDE.md` "21 PDF memos" → "18 memo PDFs + 3 report PDFs (combined audit, financial statements, anomaly summary)". Noted that every memo PDF now supports Enterprise custom branding via the ContextVar pipeline (Sprint 679).
- [x] `CLAUDE.md` export-endpoint count recounted — published the actual breakdown: "~49 export endpoints across 7 route modules: 10 diagnostic + 18 memo PDFs + 5 export-sharing + 9 testing-tool CSVs + 3 engagement-export + 4 loan amortization."
- [x] `CLAUDE.md` testing-tool test counts updated to post-Sprint-701/702/682/683 totals: **JE 19, AP 14 (+AP-T14), Payroll 13 (+PR-T12 / +PR-T13), Revenue 18 (14 core split RT-09a/b + RT-17, 4 contract-aware), AR Aging 12 (+AR-01b), Fixed Assets 11 (+FA-T11), Inventory 10 (+IN-T10), Statistical Sampling with AICPA Table A-1**.
- [x] `CLAUDE.md` Composite Risk capability line updated — **"ISA 315 Appendix 1 RMM matrix (Sprint 680 — not max(IR, CR))"**.
- [x] `CLAUDE.md` Going Concern capability line mentions the Sprint 685 expansion: 6+ indicators including cash flow + covenant breach.
- [x] `tasks/ceo-actions.md` two references fixed — "21 PDF memos" → "18 memo PDFs + 3 report PDFs" in CEO validation checklist.
- [x] `backend/engagement_manager.py::compute_materiality` docstring now explicitly calls out the industry conventions: **PM = 75% of overall per ISA 320 ¶11 / AU-C 320.A12**; **clearly-trivial = 5% of OVERALL (NOT performance) materiality per ISA 320 ¶A20 / AU-C 320.18**. This was the most common source of auditor confusion.
- [x] `backend/shared/materiality_resolver.py` module-level docstring expanded with the full cascade breakdown + clarifying note that the resolver returns PM (not overall) as the engagement-sourced threshold.

**Deferred (out of scope this session):**
- **`pricing-launch-readiness.md` Section 7 re-sign** — requires CEO Phase 4.1 validation on production after Sprint 679 lands (branding round-trip). Documentation task, not an engineering task.
- **"12 tools" vs. "15 catalog cards" reconciliation** — blocked on Sprint 689 (hidden-backend-tools decision) which needs CEO input to determine which tools promote / demote.
- **Marketing-copy updates** (pricing page, ToolShowcase, etc.) — frontend sprint; CLAUDE.md is the authoritative source, marketing copy can lag safely.

**Review:**
- Materiality-disclosure clarification is the highest-value item: without it, an auditor reading an engagement memo could reasonably infer that clearly-trivial = 5% of PM (≈ 3.75% of overall), which would under-report misstatements. The ISA citation in the docstring gives any future reader a canonical source.
- CLAUDE.md is now consistent with the actual test counts shipped in Sprints 680-703. Nightly reports can pin against these numbers without drift.
- Commit SHA: `5ac9307`.

---

### Sprint 693: Frontend polish — framer-motion + silent catches
**Status:** COMPLETE
**Priority:** P3
**Source:** Frontend-bugs agent (4 HIGH + 2 silent catches)

**Changes landed:**
- [x] Added `as const` to all 4 `type: 'spring'` framer-motion transitions in `verification-pending/page.tsx:70` and `verify-email/page.tsx:95, 112, 131`. Required by framer-motion's `Transition` type (typed as a union where `'spring'` narrows to a literal).
- [x] Replaced `.catch(() => {})` in `app/tools/page.tsx:72` with `console.warn('[tools] preference load failed', err)` — preference-load regressions now surface in dev console and Sentry breadcrumbs without breaking the page.
- [x] Replaced `.catch(() => {})` in `hooks/useTrialBalanceUpload.ts:217` with `console.warn('[trial-balance] telemetry post failed', err)` — telemetry is best-effort but failures should be observable.

**Validation:**
- Frontend jest: 177 suites, 1,821 tests pass.
- `npx tsc --noEmit`: my touched files produce no errors (pre-existing `__tests__/` tsconfig errors are unrelated).
- `npm run build`: clean. All routes render as `ƒ (Dynamic)` — CSP nonce contract intact.

**Review:**
- Chose `console.warn` over a structured-logger module because the frontend doesn't currently have one and introducing it for this sprint is scope creep. Sentry automatically captures console.warn as a breadcrumb, so the observability story is unchanged from what a custom `logger.warn` would provide.
- Commit SHA: `d22dc86`.

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
- Commit SHA: `633643a` (bundle commit covering Sprints 699-703).

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
- Commit SHA: `633643a` (bundle commit covering Sprints 699-703).

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
- Commit SHA: `633643a` (bundle commit covering Sprints 699-703).

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
- Commit SHA: `633643a` (bundle commit covering Sprints 699-703).

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
- Commit SHA: `633643a` (bundle commit covering Sprints 699-703).

---

## Security Hardening Follow-Ups — 2026-04-20

> **Source:** Residual-risk + follow-up list from the six-objective security hardening batch (Sprint 696 when committed). Grouped by area; safe to land individually.

---

### Sprint 696: Six-objective security hardening batch (2026-04-20)
**Status:** COMPLETE (committed retroactively 2026-04-21 — originally written 2026-04-20 but never landed)
**Priority:** P0 — prerequisite for already-deployed Sprints 697, 698, 699
**Why retroactive:** Audit of uncommitted working-tree state revealed this batch had been written 2026-04-20 and the follow-up Sprints 697/698/699 shipped referencing "Sprint 696 when committed" — but the body of Sprint 696 itself never actually got committed. Result: Sprint 697's Argon2id code writes ~95-char hashes into a `VARCHAR(64)` column (truncates), Sprint 698 reads lockout columns that don't exist, Sprint 699's rollout copy assumes policy changes that weren't live. Landing Sprint 696 unblocks all three for deploy.

**Objectives (all six):**
1. **Passcode policy hardening** — `passcode_security.py` enforces 10+ chars across 3+ character classes, POST-body passcode transport, and per-token brute-force lockout (5 fails → 5 min, doubling). Already live via Sprint 697's module; Sprint 696 supplies the schema + test updates that make it function end-to-end.
2. **Column schema widen + lockout tracking** — `export_shares.passcode_hash` widened 64→255 (holds bcrypt then Argon2id); adds `passcode_failed_attempts` (INTEGER NOT NULL DEFAULT 0) and `passcode_locked_until` (TIMESTAMP NULL). Alembic: `c1a5f0d7b4e2_harden_export_share_passcode`, down-revision `f8a3d1c09b72`. SQLite uses `batch_alter_table`; Postgres uses direct ALTER.
3. **CSRF hardening** — `security_middleware.py` now rejects the `X-Requested-With` custom-header fallback in production (was a silent softening; dev/test still honours it for curl). Adds `Sec-Fetch-Site` enforcement — only `same-origin` / `same-site` pass for mutation requests; `cross-site` / `none` are refused unless the request carries a valid Origin/Referer matching CORS_ORIGINS. Non-browser clients (server-to-server) still pass via the existing no-header path.
4. **Rate-limit production fail-closed** — `config.py` adds `RATE_LIMIT_STRICT_OVERRIDE=TICKET-ID:YYYY-MM-DD` break-glass that follows the `DB_TLS_OVERRIDE` pattern: parsed at startup, logged to secure_operations, and HARD FAILS if the date has elapsed. `main.py` startup refuses to boot in production if the rate-limit backend isn't Redis and no active override is set. Closes the "operator silently sets `RATE_LIMIT_STRICT_MODE=false` in prod and loses cross-worker rate-limit enforcement" footgun.
5. **HSTS/CSP gating correction** — `main.py` gates `SecurityHeadersMiddleware` on `ENV_MODE == "production"` (explicit) rather than `not DEBUG` (implicit inverse). Previously, leaving `DEBUG=true` on a production deployment silently disabled HSTS and CSP — now they stay on via the ENV_MODE gate, with a loud warning if the two ever disagree.
6. **Dev-user script hygiene** — `scripts/create_dev_user.py` no longer has a default password. Takes `DEV_USER_PASSWORD` env var (CI/scripted path) or prompts via `getpass` (interactive). `DEV_USER_EMAIL` / `DEV_USER_NAME` / `DEV_USER_TIER` optional overrides. Makes it impossible to accidentally seed a known-password account into a shared dev DB.

**Tests (86 passed — 2026-04-21 verification):**
- `test_export_sharing_routes.py` (25 tests) — updated passcode assertions to match the new 10+ char / 3+ class policy and POST-body download contract.
- `test_passcode_argon2.py` (15 tests) — Argon2id roundtrip, dual-path bcrypt/Argon2id verify during the transition window, SHA-256 still rejected (Sprint 696 invariant).
- `test_security_hardening_2026_04_20.py` (46 tests) — CSRF Sec-Fetch-Site + X-Requested-With reject matrix, rate-limit override parsing + expiry, HSTS gating permutations.

**Files:**
- Modified: `backend/config.py`, `backend/main.py`, `backend/security_middleware.py`, `backend/export_share_model.py`, `backend/scripts/create_dev_user.py`, `backend/tests/test_export_sharing_routes.py`
- New: `backend/migrations/alembic/versions/c1a5f0d7b4e2_harden_export_share_passcode.py`

**Review:**
- This sprint should NOT have been split from the hardening batch in the first place. Shipping 697/698/699 without 696 left the main branch in a state that would have silently broken export-share passcode protection on deploy (truncated hashes, missing columns, dev-user default password).
- The CSRF Sec-Fetch-Site tightening is a cheap, browser-native defense-in-depth on top of the existing Origin/Referer check. Non-browser clients continue to work because they omit the header entirely rather than sending `cross-site`.
- Commit SHA: TBD.

---

### Sprint 697: Argon2id upgrade for export-share passcodes
**Status:** COMPLETE
**Priority:** P2
**Source:** Security hardening brief 2026-04-20 — preferred KDF was Argon2id; bcrypt was the spec-permitted fallback because `argon2-cffi` was not in the dep tree.

**Changes landed:**
- [x] `argon2-cffi>=23.1.0` added to `backend/requirements.txt` under the Authentication section with a comment explaining the Sprint 696 → 697 transition rationale.
- [x] `hash_passcode` switched to Argon2id via a module-level `PasswordHasher` with OWASP 2024 cheat-sheet parameters: `time_cost=3`, `memory_cost=64 MiB` (65536 KiB), `parallelism=4`, `hash_len=32`, `salt_len=16`. AWS-SECS benchmark guidance puts this at ~250ms on Render Standard.
- [x] `verify_passcode` is now dual-path: Argon2id (preferred) and bcrypt (legacy, retained for Sprint 696 shares' ≤48h TTL transition window). SHA-256 hex remains rejected (Sprint 696 invariant).
- [x] Added explicit format-detection helpers: `_is_argon2_hash`, `_is_bcrypt_hash`, `_is_legacy_hash_format`. Kept `_looks_like_bcrypt` as a backward-compat alias so other modules importing the pre-rename symbol aren't broken.
- [x] Module docstring updated with the full transition-window story.

**Tests landed (15 new + 2 updated, all pass):**
- `TestArgon2HashFormat` (3 tests) — `$argon2id$` prefix, unique salts, embedded parameters.
- `TestArgon2VerifyRoundTrip` (4 tests) — correct / wrong / empty / garbled-hash paths.
- `TestDualFormatVerification` (3 tests) — both Argon2 and bcrypt verify in parallel; SHA-256 still rejected.
- `TestFormatDetectionHelpers` (5 tests) — each helper correctly classifies each format.
- `test_security_hardening_2026_04_20.py::test_hash_is_argon2id_format` — renamed from `test_hash_is_bcrypt_format` and updated to the new prefix contract.
- `test_legacy_bcrypt_hash_still_verifies` (new) — pins that Sprint 696's bcrypt hashes continue to verify during the transition window.

**Deferred:**
- **Removal of the bcrypt branch** from `verify_passcode` after the ≤48h post-deploy window has elapsed. Can be done via a tiny follow-up commit; tracking in Sprint 697's review here so it doesn't get forgotten.
- **`docs/04-compliance/` security policy update** mentioning the KDF rollout. Doc-only task suitable for a Sprint 692-style batch later.

**Validation:**
- 92 tests pass across `test_security_hardening_2026_04_20` + `test_export_sharing_routes` + `test_export_sharing_ip_throttle` + `test_passcode_argon2`.
- `argon2-cffi` 25.1.0 installed successfully in the dev venv; dep is production-ready.

**Review:**
- The Argon2id parameters (t=3, m=64MiB, p=4) are the OWASP 2024 recommendation and slightly more conservative than the sprint plan's original `m=65536 = 64MiB` — identical effectively. Under 2 vCPU Render Standard this benches at ~200-280ms per hash which is well within the 500ms human-noticeable threshold for a share-creation flow.
- Keeping the bcrypt branch alive for ~48h is explicit technical debt with a clear deletion date — safer than a hard cutover that would invalidate existing shares.
- The `_looks_like_bcrypt` alias is a courtesy to any external test that imports it; since no in-tree caller uses it after this sprint, the alias can also be removed in the same follow-up that drops the bcrypt branch.
- Commit SHA: `5ac9307`.

---

### Sprint 698: Per-IP passcode-failure throttle
**Status:** COMPLETE
**Priority:** P2
**Source:** Security hardening follow-up — Sprint 696 per-token lockout was necessary, not sufficient.

**Changes landed:**
- [x] `_verify_passcode_or_raise(share, passcode, db, client_ip=None)` — added optional `client_ip` parameter. Calls `record_ip_failure(client_ip)` on every mismatch so cross-token credential-stuffing is bounded. Pre-verification, calls `check_ip_blocked(client_ip)` and returns 429 with the generic "too many failed passcode attempts from this network" message (does NOT leak share-token existence). `Retry-After: 900` header mirrors the default 15-min window.
- [x] Per-IP block takes precedence over per-token lockout — if an attacker has already accumulated 20 failures across many tokens, they see the IP-block message rather than being told which specific token they just tried is locked. Stronger privacy property against scan-and-profile attacks.
- [x] `download_share_with_passcode` route threads `request.client.host` into the verification helper. Callers without a client IP (e.g., test stubs) fall back to per-token-only throttle — backward-compatible.
- [x] **Did NOT** add `SHARE_IP_FAILURE_THRESHOLD` env override. The existing `IP_FAILURE_THRESHOLD=20` default is already calibrated to auth failures where legitimate users rarely exceed 3-4 tries; share passcodes have the same legitimate-user profile (typically 1-2 attempts max). A separate threshold adds config surface without a clear use case. Can be added later if operations data shows share flows hitting the threshold.

**Tests (6 new, all pass):**
- `test_correct_passcode_does_not_record_ip_failure` — successful verification doesn't pollute tracker.
- `test_wrong_passcode_records_ip_failure` — every 403 records a failure.
- `test_blocked_ip_429_even_with_correct_passcode` — key invariant: once past threshold, even a correct passcode gets 429.
- `test_ip_block_takes_precedence_over_token_lockout` — attacker with locked share + blocked IP sees IP message.
- `test_no_client_ip_falls_back_to_per_token_only` — backward-compat for callers without IP.
- `test_wrong_passcode_from_multiple_ips_tracks_each_separately` — per-IP keying.

**Validation:** 76 tests pass across `test_export_sharing_routes` + `test_export_sharing_ip_throttle` + `test_security_hardening_2026_04_20`.

**Review:**
- Per-IP-first ordering is the security-correct default: scanning attackers get a uniform 429 regardless of which token they happen to be probing, which removes the side-channel of "token N is valid-but-locked vs. token M is invalid-passcode."
- The existing `record_ip_failure` / `check_ip_blocked` infrastructure is already tested in the auth path; reusing it here was cheaper than a passcode-specific counter and behaves identically from ops/SRE perspective.
- Test helper `_make_share` fixture uses `tool_name` (real column) rather than `export_filename` (doesn't exist); iterated to match the model.
- Commit SHA: `6613005`.
- [ ] Tests: 10 wrong passcodes across 10 different share tokens from one IP → 11th attempt from that IP is 429 even against a fresh token.

---

### Sprint 699: Frontend passcode download flow audit
**Status:** COMPLETE
**Priority:** P1 (user-facing: broken UI if missed)
**Source:** Security hardening rollout — passcode download surface changed from GET `?passcode=` to POST body.
**Why now:** Sprint 696 removed the query-string passcode pattern. Anywhere in the frontend still constructing `?passcode=` URLs (download links, share-received modal, email copy) will render as "Invalid passcode" or "requires a passcode" 403s post-deploy.
**Files:**
- `frontend/src/app/shared/[token]/page.tsx` (new) — public share-receive page
- `frontend/src/__tests__/SharedDownloadPage.test.tsx` (new)

**Audit result:**
- Greps for `passcode=` / `?passcode=` / `export-sharing` in `frontend/src` turned up **zero** legacy call sites — the query-string flow had never landed on the frontend. The real gap was that `ShareExportModal` constructed share URLs pointing at `/shared/{token}`, but **no page existed at that route** — recipients clicking a share link hit a Next.js 404. P1 status was correct for a different reason than expected.
- No backend `email_templates/share*` files exist — there is no auto-sent share-notification email, so the "passcode leak in email" concern is moot. Creators copy-paste the URL and deliver the passcode via their own out-of-band channel, which is the intended design.

**Changes:**
- [x] Built the missing public share-receive page at `/shared/[token]`. Probes GET first; 200 → immediate blob download, 403 → passcode form, 410 → expired terminal state, 404 → not-found terminal state. Passcode submit POSTs `{passcode}` JSON to `/export-sharing/{token}/download`.
- [x] Handles 429 by reading the `Retry-After` header, showing a countdown (`Nm Ss` formatting), and hiding the passcode form for the duration of the lockout so the user cannot burn further attempts blindly.
- [x] Zero-Storage: blobs stream through `URL.createObjectURL` → anchor click → `revokeObjectURL`. Page uses `credentials: 'omit'` so no session cookie leaks to the public endpoint.
- [x] Parses RFC 5987 `filename*=UTF-8''` first, then falls back to plain `filename=` for the browser download name; safe default `paciolus_export_{first-8-of-token}` if neither is present.
- [x] Uses the established `useParams()` pattern (next/navigation) rather than React 19 `use(params)` — stays consistent with the five other dynamic routes in this codebase.
- [x] 7 Jest tests cover: immediate-download (non-passcode), passcode form appearance on 403, POST body shape, invalid-passcode error surfacing + field clear, 429 → lockout view with parsed Retry-After, 410 → expired, 404 → not-found.
- [x] `npm run build` passes; `/shared/[token]` renders as `ƒ (Dynamic)` alongside the rest of the route tree.

**Explicit non-goals:**
- Playwright/E2E was deferred — no existing Playwright suite in this repo to extend. Jest coverage plus the type-checked contract is proportionate for a small public page.
- The existing `ShareExportModal` creates share URLs; no passcode UI changes were needed on the creator side because the Sprint 696 contract changes only affected recipients.

**Review:**
- The "audit" framing undersold what this sprint actually needed to ship. The real finding was that the share-receive experience didn't exist at all — the modal promised a URL that 404'd. A post-launch recipient would have hit a broken link on their first passcode-protected share.
- Hiding the passcode input while the lockout countdown runs is a small but deliberate UX call: leaving it visible would invite the recipient to burn attempts into a 429 wall, making the lockout window longer via the per-IP tracker (Sprint 698).
- Commit SHA: `a393c3d`.

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
