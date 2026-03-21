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
- [ ] **NEW-001:** Alembic migration to clean stale `ORGANIZATION` tier values in `users.tier` column → `FREE`. Add a data migration that updates any row where `tier NOT IN ('free','solo','professional','enterprise')` to `'free'`. Prevents 500 on login for any unmigrated DB.
- [ ] **NEW-002:** Alembic migration to add `uploads_used_current_period INTEGER NOT NULL DEFAULT 0` to `subscriptions` table. Column is defined in `subscription_model.py` but no migration exists. Causes 500 on TB upload.
- [ ] **NEW-003:** Add `"informational"` to `severity` Literal in `shared/diagnostic_response_schemas.py` (lines 572 and 622). Backend engine (`classification_rules.py:672`, `classification_validator.py:229`) returns `"informational"` severity but the Pydantic response schema rejects it with `ResponseValidationError`. **Hotfix applied during QA — needs commit.**

#### P1 — High
- [ ] **NEW-004:** Backend returns `net_balance`, `total_debit`, `total_credit` as strings in lead sheet grouping response (Decimal→str JSON serialization). Frontend `LeadSheetCard.formatCurrency()` calls `.toFixed()` on raw value → `TypeError` crash. Fix: either serialize as float in backend, or coerce in all frontend consumers. **Hotfix applied to `LeadSheetCard.tsx` during QA — needs commit + backend root cause fix.**
- [ ] **NEW-005:** Add `GET /activity/recent` endpoint to backend routes. Dashboard calls `/activity/recent?limit=5` on load but endpoint returns 404. Activity log writes (`POST /activity/log` → 201) work, but reads are missing. Need route in `routes/` that queries `activity_logs` table.
- [ ] **NEW-006:** Lead sheet grouping shows "1 Account" per sheet for a 102-account TB. Expected A–Z grouping with multiple accounts aggregated per lead sheet letter. Investigate serialization/aggregation logic in `audit_engine.py` → `lead_sheet_grouping` response builder.

#### P2 — Medium
- [ ] **NEW-007:** Hydration mismatch on sonification button in `ToolLinkToast` component. SSR renders button but client differs. Wrap in `useEffect`-guarded render or add `suppressHydrationWarning`.
- [ ] **NEW-008:** Hydration mismatch on `ParallaxSection` `translateY` in `HeroScrollSection`. Scroll-dependent motion values differ server/client. Add `suppressHydrationWarning` on motion container divs.
- [ ] **NEW-009:** Classification quality flags normal contra accounts (Allowance for Doubtful Accounts, Accumulated Depreciation, Inventory Reserve, Treasury Stock, Sales Returns/Discounts) as "sign_anomaly". These are standard contra accounts — add exclusion list to `classification_rules.py` sign-anomaly checker.

#### P3 — Low
- [ ] **NEW-010:** Backend startup warns about missing `STRIPE_PRICE_PROFESSIONAL_MONTHLY` and `STRIPE_PRICE_PROFESSIONAL_ANNUAL` env vars. Professional/Enterprise monthly/annual checkout will fail. Document required env vars or suppress warning when not in production.
- [ ] **NEW-011:** Next.js dev overlay shows "2 Issues" badge (hydration warnings). Not visible in production build. No action needed unless suppression is desired in dev.

- **Status:** PENDING

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

