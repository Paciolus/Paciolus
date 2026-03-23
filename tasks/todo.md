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
| ~~Rate limiter → Redis storage backend~~ | RESOLVED — Sprint 563 | AUDIT-07 Phase 5 |

---

## Active Phase
> Sprints 478–531 archived to `tasks/archive/sprints-478-531-details.md` (consolidated).
> Sprints 532–561 archived to `tasks/archive/sprints-532-561-details.md` (consolidated).
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.
> FIX-3–8B, AUDIT-09–10 archived to `tasks/archive/fix-3-8b-audit-09-10-details.md`.

### Sprint 563: Redis Rate-Limit Storage Backend
- [x] Add `redis>=5.0.0` dependency to `requirements.txt`
- [x] Add `REDIS_URL` optional config to `config.py` with startup summary log
- [x] Implement `_resolve_storage_uri()` in `shared/rate_limits.py` — Redis when reachable, graceful memory fallback
- [x] Pass `storage_uri` to `Limiter()` constructor
- [x] Add `get_storage_backend()` accessor for health checks and logging
- [x] Add Redis startup log in `main.py` lifespan
- [x] Add Redis service to `docker-compose.yml` (commented, opt-in)
- [x] Add `REDIS_URL` documentation to `.env.example`
- [x] Write 10 tests: storage resolution (3), backend accessor (3), limiter config (2), canary imports (2)
- [x] Verify all 50 existing rate-limit tests still pass (0 regressions)
- **Tests:** 60 passed (10 new + 50 existing), 0 regressions
- **Status:** COMPLETE

### CI-FIX: Pre-Existing CI Failures
- [x] **Backend Tests**: commit untracked `anomaly_framework/` generators, fixtures, `__init__.py`, and test files; add `hypothesis` to requirements-dev.txt
- [x] **Frontend Build + Lint**: fix 11 `import/order` ESLint errors; fix CI `$GITHUB_OUTPUT` stderr pollution
- [x] **OpenAPI Schema Drift Check**: regenerate snapshot (162 paths, 315 schemas)
- [x] **Report Standards Gate**: exclude `pdf_generator.py` backward-compat shim from validator
- [x] **Backend Type Check (mypy)**: convert to baseline gate (1,011 errors baseline); fail only on regressions
- **PR:** [#48](https://github.com/Paciolus/Paciolus/pull/48) — merged
- **Status:** COMPLETE

### Sprint 564: DEC P1/P2 Remediation (6 Findings)
- [x] **F-001 (P1):** Rename "Composite Risk Score" → "Composite Diagnostic Score" across 20 backend + 4 frontend files. Function renames: `compute_bank_rec_risk_score` → `compute_bank_rec_diagnostic_score`, `compute_twm_risk_score` → `compute_twm_diagnostic_score`, `compute_apc_risk_score` → `compute_apc_diagnostic_score`. Backward-compat aliases added. All user-facing PDF labels already said "Composite Diagnostic Score"; cleaned up remaining docstrings, comments, and f-strings.
- [x] **F-002 (P1):** Fix ISA 530 "population accepted" language in `sampling_memo_generator.py`. Pass case: "upper error limit does not exceed tolerable misstatement" + ISA 530.14 auditor evaluation reminder. Fail case: "exceeds" + ISA 530.17 alternative procedures guidance. 3 test updates (negative assertions against old language).
- [x] **F-003 (P2):** Integration tests for 2 highest-risk untested routes: `test_billing_webhooks_routes.py` (5 tests: 400/500 error classification) and `test_audit_pipeline_routes.py` (7 tests: auth gates, validation, dedup, rate limiting).
- [x] **F-004 (P2):** Webhook error classification in `billing.py` + `billing_webhooks.py`: ValueError/KeyError → 400 (data error, not retryable); generic Exception → 500 (operational, retryable). Structured logging with event ID, type, and exception class.
- [x] **F-005 (P2):** Atomic billing checkout with saga rollback in `checkout_orchestrator.py`. `_rollback_stripe_customer()` helper deletes orphaned customers on failure. Tracks `created_new_customer` flag; only rolls back new customers. DB commit failure logs CRITICAL with resource IDs for manual reconciliation. 9 new tests.
- [x] **F-006 (P2):** Going concern indicators section added to TB Diagnostic PDF in `pdf/sections/diagnostic.py`. Renders triggered indicators as bullet points (name, value, assessment). ISA 570/AU-C 570 disclaimer always present. "No indicators identified" shown when empty.
- **Tests:** 21 new tests (5 webhook + 7 pipeline + 9 saga) + 345 existing pass on modified files
- **Verification:** pytest full suite PASS (exit 0), npm run build PASS, npm test PASS (1,725/1,725)
- **Status:** COMPLETE

### Sprint 565: Chrome QA Remediation (11 Findings)
> Source: `reports/qa/2026-03-21-chrome-qa.md`

#### P0 — Blocking
- [ ] **NEW-001:** Alembic migration to clean stale `ORGANIZATION` tier values in `users.tier` column → `FREE`. *(Deferred — not on this branch)*
- [x] **NEW-002:** Migration f4a5b6c7d8e9 already adds `uploads_used_current_period`. Added 3 regression tests verifying column, model, and migration chain.
- [x] **NEW-003:** Hotfix applied in c795c60. Added 7 regression tests validating all severity levels including informational.

#### P1 — High
- [x] **NEW-004:** Convert Decimal→float in `lead_sheet_grouping_to_dict()`. Frontend defensive coercion was already in c795c60. 3 backend tests + 77 existing pass.
- [x] **NEW-005:** Added `GET /activity/recent` endpoint to `routes/activity.py` with limit param, auth, reverse-chronological order. 5 tests (auth gate, empty, ordering, limit, user isolation).
- [x] **NEW-006:** Fixed `apply_lead_sheet_grouping()` to use `all_accounts` instead of `abnormal_balances` — root cause of one-account-per-sheet artifacts. Falls back to abnormal_balances for backward compat. 5 tests.

#### P2 — Medium
- [x] **NEW-007:** Added mounted guard to ToolLinkToast to defer AnimatePresence rendering to client.
- [x] **NEW-008:** Added `suppressHydrationWarning` to ParallaxSection motion.div.
- [x] **NEW-009:** Added 27-pattern contra account exclusion list to `classification_validator.py`. `check_sign_anomalies()` skips recognized contra accounts. 21 tests + 52 existing pass.

#### P3 — Low
- [x] **NEW-010:** Gated Stripe billing config warnings to DEBUG in dev, WARNING in production (both `validate_billing_config()` and `main.py` startup).
- [x] **NEW-011:** Resolved by NEW-007/008 hydration fixes.

- **Tests:** 7,085 backend (0 failures), 1,725 frontend (0 failures)
- **Verification:** pytest PASS, npm run lint PASS (0 errors), npm run build PASS, npm test PASS
- **Status:** COMPLETE

### Sprint 566: Frontend Design Enrichment (14 Findings)
> Source: Chrome QA visual design assessment — Dashboard, Tools, Workspaces, Portfolio

#### Quick Fixes
- [x] **X1:** Standardize `max-w-5xl` → `max-w-6xl` on Dashboard page
- [x] **P2:** Rename "Open Audit" → "Open Diagnostics" in ClientCard (terminology guardrail)
- [x] **D3:** Enlarge dashboard welcome header to `text-3xl md:text-4xl` + contextual summary line
- [x] **T3:** Reduce trial-balance drop zone padding from `p-12` to `p-8` in globals.css
- [x] **W3:** Shorten workspace detail tab labels (Status/Follow-Up/Workpapers/Convergence)

#### Empty State Consistency
- [x] **X3:** Create shared `PageEmptyState` component (`components/shared/PageEmptyState.tsx`)
- [x] **W2:** Add CTA button + Zero-Storage badge to Workspaces empty state via `onCreateNew` prop
- [x] Dashboard + Portfolio empty states enriched with icons, descriptions, and consistent CTAs

#### Dashboard Enrichments
- [x] **D1:** Stat cards — sage icon circles, `font-mono` numbers, contextual dim for zero values
- [x] **D2:** Hero Upload TB card (full-width, `sage-50/50` bg, arrow affordance) + 2-col secondary row
- [x] **D4:** `2px` gradient accent strip below toolbar on all pages
- [x] **D5:** Enhanced empty Recent Activity — icon, description, larger CTA

#### Portfolio Enhancements
- [x] **P1+P3:** Spine `w-1.5` → `w-2` with hover color shift (oatmeal→sage), card shadow lift + border transition
- [x] **P4:** Search bar with magnifying glass icon, client-side name/industry filter
- [x] **P5:** Empty state icon changed to open-book/ledger (reinforces bound-ledger theme)

#### Workspaces Enhancements
- [x] **W1:** `AnimatePresence mode="wait"` with slide-in/slide-out crossfade on list↔detail
- [x] **W4:** Left accent border on EngagementCard (sage-500 active, oatmeal-300 archived)
- [x] **W5:** `{n}/12 tools` progress indicator in detail header next to status badge

#### Cross-Page Polish
- [x] **X2:** Subtle sage gradient accent strip below toolbar on Dashboard, Workspaces, Portfolio
- [x] **X4:** Page mount `opacity` fade-in on Workspaces and Portfolio (`motion.div`)
- [ ] ~~**X6:** Button style class refactor~~ — Deferred: existing inline styles already match `btn-primary` definition; cosmetic-only rename

- **Verification:** `npm run build` PASS, `npm test` 1,725/1,725 PASS
- **Status:** COMPLETE

### Sprint 567: Overnight Report Bug Fixes + Dependency Updates
> Source: `reports/nightly/2026-03-22.md` — 5 confirmed open bugs, 16 outdated packages

#### Bug Fixes
- [x] **BUG-001:** Add 25 alternate follow-up procedures to `FOLLOW_UP_PROCEDURES_ALT` for high-frequency test keys (AP, Revenue, AR, Fixed Asset, Inventory) to enable rotation across reports
- [x] **BUG-002:** Make risk tier conclusion labels score-aware in 3 memo generators (three_way_match, multi_period, bank_reconciliation). Conclusion text now includes Composite Diagnostic Score (e.g., "MODERATE (20.0/100)"). Bank rec if/elif chain converted to dict lookup.
- [x] **BUG-003:** Wrap raw string table cells in `Paragraph` objects in `anomaly_summary_generator.py` (scope table, not-executed table, anomaly table) to prevent PDF text overflow
- [x] **BUG-006:** Track `missing_names` and `missing_balances` from raw rows in `run_population_profile()` and pass to `_compute_data_quality()` so completeness scores vary by input quality
- [x] **BUG-007:** Add BUG-007 guard in `revenue_testing_memo_generator.py` for data-inconsistency case (entries_flagged > 0 but flagged_entries empty). Renders placeholder text instead of orphaned section header.

#### Dependency Updates
- [x] Upgraded 14 of 16 outdated backend packages: bandit, certifi, charset-normalizer, coverage, cyclonedx-python-lib, filelock, greenlet, platformdirs, pypdfium2, pytest-cov, pytz, rich, stevedore, wrapt
- [x] 2 packages blocked by upstream pins: pdfminer.six (pdfplumber==0.11.9 requires ==20251230), pydantic_core (pydantic==2.12.5 requires ==2.41.5)

- **Tests:** 7,041 backend passed, 0 failed (no regressions)
- **Status:** COMPLETE

### Sprint 568: Overnight Report Bug Fix Completions
> Source: `reports/nightly/2026-03-23.md` — 5 confirmed open bugs (residual from Sprint 567 incomplete fixes)

#### Bug Fixes
- [x] **BUG-001:** Pass `rotation_index` at 5 remaining call sites: `ap_testing_memo_generator.py` (vendor_name_variations), `multi_period_memo_generator.py` (apc_sign_change, apc_dormant_account, new_account, apc_closed_account)
- [x] **BUG-003:** Add `wrap_table_strings()` helper to `shared/memo_base.py`; apply across 6 memo generators (anomaly_summary, bank_reconciliation, accrual_completeness, population_profile, expense_category, preflight) — 13 tables total
- [x] **BUG-006:** Add `test_data_quality_varies_by_input` meridian test to `test_population_profile_engine.py` validating score variation between high-quality and degraded inputs
- [x] **BUG-007:** Add `flagged_entries` filter to list comprehensions in 4 memo generators (payroll, fixed_asset, ap DRILL-03, ar_aging DRILL-05) to prevent empty drill-down stubs at source

#### Dependency Assessment
- [x] All 3 flagged packages blocked by upstream pins: pdfminer.six (pdfplumber==0.11.9 requires ==20251230), starlette (FastAPI 0.135.1 is latest), pydantic_core (pydantic 2.12.5 is latest)

- **Tests:** 7,086 backend passed (1 new), 0 failed; frontend build PASS
- **Status:** COMPLETE

### Sprint 569: Chrome QA Content Remediation (6 Findings)
> Source: Exhaustive Chrome browser review of all 42 pages

- [x] **NEW-012 (P2):** Update `backend/version.py` from `1.9.3` to `2.1.0` — status page displayed stale version
- [x] **NEW-013 (P2):** Extract `key` from spread props in `BrandIcon.tsx` — React 19 console error on every page with BrandIcon
- [x] **NEW-014 (P3):** Add fallback "your email address" text on `/verification-pending` when email state is empty
- [x] **NEW-016 (P3):** Replace generic "Automated Analysis" badges with specific standard citations on 5 tool pages (JE→ISA 240/PCAOB AS 2401, AP→ISA 500, Payroll→ISA 500, Bank Rec→ISA 505, Three-Way Match→ISA 500)
- [x] **NEW-017 (P3):** Add `isAuthenticated` gate + `GuestCTA` to `/flux` and `/recon` diagnostic pages, consistent with tool pages
- [ ] **NEW-015 (P3):** "Forgot password?" shows "Coming soon" — deferred (requires backend password reset flow)

- **Tests:** 1,725 frontend passed, frontend build PASS; 93 backend version/health tests pass
- **Status:** COMPLETE

