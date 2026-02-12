# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Completed Phases

### Phase I (Sprints 1-24) — COMPLETE
> Core platform: Zero-Storage TB analysis, streaming, classification, brand, risk dashboard, multi-sheet Excel, PDF/Excel export, JWT auth, activity logging, client management, practice settings, deployment prep.

### Phase II (Sprints 25-40) — COMPLETE
> Test suite, 9 ratios (Current/Quick/D2E/Gross/Net/Operating/ROA/ROE/DSO), IFRS/GAAP docs, trend analysis + viz, industry ratios (6 industries), rolling windows, batch upload, benchmark RFC.

### Phase III (Sprints 41-47) — COMPLETE
> Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI + integration.

### Phase IV (Sprints 48-55) — COMPLETE
> User profile, security hardening, lead sheets (A-Z), prior period comparison, adjusting entries, DSO ratio, CSV export, frontend test foundation.

### Phase V (Sprints 56-60) — COMPLETE
> UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode. **Tests: 625 backend + 26 frontend.**

### Phase VI (Sprints 61-70) — COMPLETE
> Multi-Period TB Comparison (Tool 2), Journal Entry Testing (Tool 3, 18-test battery + stratified sampling), platform rebrand to suite, diagnostic zone protection. Tests added: 268 JE + multi-period.

### Phase VII (Sprints 71-80) — COMPLETE
> Financial Statement Builder (Tool 1 enhancement), AP Payment Testing (Tool 4, 13-test battery), Bank Reconciliation (Tool 5). Tests added: 165 AP + 55 bank rec.

### Phase VIII (Sprints 81-89) — COMPLETE
> Cash Flow Statement (indirect method, ASC 230/IAS 7), Payroll & Employee Testing (Tool 6, 11-test battery), code quality sprints (81-82). Tests added: 139 payroll.

### Phase IX (Sprints 90-96) — COMPLETE
> Shared testing utilities extraction (enums/memo/round-amounts), Three-Way Match Validator (Tool 7), Classification Validator (TB Enhancement). Tests added: 114 three-way match + 52 classification.

### Phase X (Sprints 96.5-102) — COMPLETE
> The Engagement Layer: engagement model + materiality cascade, follow-up items tracker (narratives-only), workpaper index, anomaly summary report (PDF), diagnostic package export (ZIP with SHA-256), engagement workspace frontend. 8 AccountingExpertAuditor guardrails satisfied. Tests added: 158 engagement/follow-up/workpaper/export.

### Phase XI (Sprints 103-110) — COMPLETE
> Tool-Engagement Integration (frontend auto-link via EngagementProvider), Revenue Testing (Tool 8, 12-test battery, ISA 240), AR Aging Analysis (Tool 9, 11-test battery, dual-input TB + sub-ledger). Tests added: 110 revenue + 28 memo + 131 AR + 34 memo.

### Phase XII (Sprints 111-120) — COMPLETE
> Nav overflow infrastructure, FileDropZone extraction, Finding Comments + Assignments (collaboration), Fixed Asset Testing (Tool 10, 9-test battery, IAS 16), Inventory Testing (Tool 11, 9-test battery, IAS 2). Tests added: 41 comments + 15 assignments + 133 FA + 38 FA memo + 136 inventory + 38 inv memo.

### Phase XIII (Sprints 121-130) — COMPLETE
> Platform polish + dual-theme "The Vault Interior" architecture. Security hardening (26 rate-limited exports, upload validation, error sanitization). CSS custom property + Tailwind semantic token infrastructure. Light theme migration (all tool + authenticated pages). VaultTransition login animation. Export consolidation + Bank Rec/Multi-Period memos (11/11 tools with PDF memos). WCAG AAA accessibility + 60 frontend test backfill. **Version: 1.2.0. Tests: 2,593 backend + 128 frontend.**

### Phase XIV (Sprints 131-135) — COMPLETE
> Professional Threshold: 6 public marketing/legal pages (Privacy, Terms, Contact, About, Approach, Pricing, Trust). Shared MarketingNav/Footer. Contact backend with honeypot + rate limiting. All pages dark-themed (vault exterior).

### Phase XV (Sprints 136-141) — COMPLETE
> Code Deduplication: shared parsing helpers, shared types, 4 shared testing components (DataQualityBadge, ScoreCard, TestResultGrid, FlaggedTable), context consolidation. ~4,750 lines removed (81% deduplication), 100% backward compatible.

### Phase XVI (Sprints 142-150) — COMPLETE
> API Hygiene: semantic token migration, API call consolidation (15 direct fetch → apiClient), N+1 query fix, Docker hardening (.dockerignore, multi-stage fix, SQLite path).

### Phase XVII (Sprints 151-163) — COMPLETE
> Code Smell Refactoring: 7 backend shared modules (column_detector, data_quality, test_aggregator, benford, export_schemas, testing_route, memo_template), 8 frontend decompositions (TB page 1,219→215, export 1,497→32, practice 1,203→665, multi-period 897→470, FinancialStatements 772→333), hook factory, centralized constants. 15 new shared files, 9,298 added / 8,849 removed. **Tests: 2,716 backend + 128 frontend.**

**Test Coverage at Phase XVIII End:** 2,716 backend tests + 128 frontend tests | Version 1.2.0

> **Detailed checklists:** `tasks/archive/phases-vi-ix-details.md` | `tasks/archive/phases-x-xii-details.md` | `tasks/archive/phases-xiii-xvii-details.md`

---

## Post-Sprint Checklist

**MANDATORY:** Complete these steps after EVERY sprint before declaring it done.

### Verification
- [ ] Run `npm run build` in frontend directory (must pass)
- [ ] Run `pytest` in backend directory (if tests modified)
- [ ] Verify Zero-Storage compliance for new data handling

### Documentation
- [ ] Update sprint status to COMPLETE in todo.md
- [ ] Add Review section with Files Created/Modified
- [ ] Add lessons to lessons.md if corrections occurred

### Git Commit
- [ ] Stage relevant files: `git add <specific-files>`
- [ ] Commit with sprint reference: `git commit -m "Sprint X: Brief Description"`
- [ ] Verify commit: `git log -1`

---

### Phase XVIII (Sprints 164-170) — COMPLETE
> Async Architecture Remediation: `async def` → `def` for 82+ pure-DB/export endpoints, `asyncio.to_thread()` for CPU-bound Pandas work, `BackgroundTasks` for email/tool-run recording, `memory_cleanup()` context manager, rate limit gap closure. Zero behavioral regressions. **Tests: 2,716 backend + 128 frontend.**

> **Detailed checklists:** `tasks/archive/phase-xviii-details.md`
> **Backlog & Decisions:** `tasks/archive/backlog.md`

---

### Phase XIX (Sprints 171-177) — COMPLETE
> **Focus:** API Contract Hardening — response_model coverage, correct HTTP status codes, consistent error handling
> **Source:** 3-agent audit of 21 route files (~115 endpoints)
> **Strategy:** Shared models first → status codes → per-file response_model → trends fix → path fixes → regression
> **Impact:** 25 endpoints gain response_model, 16 status codes corrected, 3 router issues fixed, trends.py error-in-body eliminated
> **Test Coverage at Phase XIX End:** 2,716 backend tests + 128 frontend tests | Version 1.2.0

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 171 | Shared Response Models (`shared/response_schemas.py`) + follow_up_items tag fix | 3/10 | COMPLETE |
| 172 | DELETE 204 No Content (7 endpoints) + POST 201 Created (9 endpoints) | 4/10 | COMPLETE |
| 173 | response_model: adjustments.py (9 endpoints) + auth_routes.py (4 endpoints) | 5/10 | COMPLETE |
| 174 | response_model: 10-file batch (settings, diagnostics, users, engagements, bank_rec, twm, je, multi_period, prior_period) | 4/10 | COMPLETE |
| 175 | trends.py architecture fix: error-in-body → HTTPException(422) + response_model | 6/10 | COMPLETE |
| 176 | Router path fixes: `/diagnostics/flux` → `/audit/flux`, lead-sheets tag fix | 5/10 | COMPLETE |
| 177 | audit.py response_model + Phase XIX regression + documentation | 4/10 | COMPLETE |

#### Sprint 171 — Shared Response Models + Tag Fix — COMPLETE
- [x] Create `backend/shared/response_schemas.py` with `SuccessResponse` and `ClearResponse`
- [x] Fix `follow_up_items.py` tag: `tags=["follow-up-items"]` → `tags=["follow_up_items"]`

**Files Created:** `backend/shared/response_schemas.py`
**Files Modified:** `backend/routes/follow_up_items.py`

#### Sprint 172 — HTTP Status Codes — COMPLETE
**DELETE → 204 No Content (7 endpoints):**
- [x] `clients.py` — `delete_client`
- [x] `adjustments.py` — `delete_adjusting_entry`
- [x] `adjustments.py` — `clear_all_adjustments`
- [x] `follow_up_items.py` — `delete_follow_up_item`
- [x] `follow_up_items.py` — `delete_comment`
- [x] `activity.py` — `clear_activity_history`
- [x] `engagements.py` — `archive_engagement`

**POST → 201 Created (9 endpoints):**
- [x] `auth_routes.py` — `register`
- [x] `clients.py` — `create_client`
- [x] `adjustments.py` — `create_adjusting_entry`
- [x] `activity.py` — `log_activity`
- [x] `diagnostics.py` — `save_diagnostic_summary`
- [x] `engagements.py` — `create_engagement`
- [x] `follow_up_items.py` — `create_follow_up_item`
- [x] `follow_up_items.py` — `create_comment`
- [x] `health.py` — `join_waitlist`

**Frontend:** No changes needed — `apiClient.ts` already handles 204 (returns undefined data) and 201 (via `response.ok` for all 2xx).

**Files Modified:** `clients.py`, `adjustments.py`, `follow_up_items.py`, `activity.py`, `engagements.py`, `auth_routes.py`, `diagnostics.py`, `health.py`

#### Sprint 173 — response_model: adjustments + auth — COMPLETE
- [x] Apply `AdjustmentSetResponse` to `list_adjusting_entries`
- [x] Create inline models: `AdjustmentCreateResponse`, `NextReferenceResponse`, `EnumOption`, `AdjustmentTypesResponse`, `AdjustmentStatusesResponse`, `AdjustmentStatusUpdateResponse`
- [x] `get_adjusting_entry` + `apply_adjustments_to_tb` → `response_model=dict`
- [x] Create inline models for auth: `CsrfTokenResponse`, `EmailVerifyResponse`, `ResendVerificationResponse`, `VerificationStatusResponse`

**Files Modified:** `backend/routes/adjustments.py`, `backend/routes/auth_routes.py`

#### Sprint 174 — response_model: 10-file batch — COMPLETE
- [x] `settings.py`: `MaterialityResolveResponse` + `response_model=dict` for preview
- [x] `diagnostics.py`: `DiagnosticHistoryResponse`
- [x] `users.py`: Use `SuccessResponse` from shared for `change_password`
- [x] `engagements.py`: `response_model=dict` for workpaper-index
- [x] `bank_reconciliation.py`: `response_model=dict`
- [x] `three_way_match.py`: `response_model=dict`
- [x] `je_testing.py`: `SamplingPreviewResponse` + `response_model=dict` for JE + sample
- [x] `multi_period.py`: `response_model=dict` for compare-periods + compare-three-way
- [x] `prior_period.py`: `PeriodSaveResponse` (status_code=201) + `response_model=dict` for compare
- [x] `clients.py`: `response_model=list` for lead-sheets/options

**Files Modified:** `settings.py`, `diagnostics.py`, `users.py`, `engagements.py`, `bank_reconciliation.py`, `three_way_match.py`, `je_testing.py`, `multi_period.py`, `prior_period.py`, `clients.py`

#### Sprint 175 — trends.py Architecture Fix — COMPLETE
- [x] Convert "insufficient data" error-in-body to `HTTPException(status_code=422)` (3 endpoints)
- [x] Create inline: `ClientTrendsResponse`, `IndustryRatiosResponse`, `RollingAnalysisResponse`
- [x] Apply `response_model=` to all 3 endpoints
- [x] Convert `async def` → `def` (pure-DB endpoints, missed in Phase XVIII)
- [x] Frontend: remove `error?`/`message?` from `ClientTrendsResponse`, `RollingWindowResponse`, `IndustryRatiosData`
- [x] Frontend: remove error-in-body check in `useTrends.ts` (lines 249-257)
- [x] Frontend: update `RollingWindowSection.tsx` and `IndustryMetricsSection.tsx` error checks

**Files Modified:** `backend/routes/trends.py`, `frontend/src/hooks/useTrends.ts`, `frontend/src/hooks/useRollingWindow.ts`, `frontend/src/components/analytics/IndustryMetricsSection.tsx`, `frontend/src/components/analytics/RollingWindowSection.tsx`

#### Sprint 176 — Router Path Fixes — COMPLETE
- [x] Move `/diagnostics/flux` → `/audit/flux` in `audit.py`
- [x] Update frontend reference in `flux/page.tsx`
- [x] Fix `lead-sheets/options` tag in `clients.py`: added `tags=["reference"]` override

**Files Modified:** `backend/routes/audit.py`, `backend/routes/clients.py`, `frontend/src/app/flux/page.tsx`

#### Sprint 177 — Phase XIX Wrap — COMPLETE
- [x] `audit.py`: `WorkbookInspectResponse` + `SheetInfo`, `response_model=dict` for TB, `FluxAnalysisResponse`
- [x] Full regression: `pytest` (2,715 passed, 1 pre-existing failure) + `npm run build` (pass)
- [x] Update `CLAUDE.md` Phase XIX section
- [x] Update `tasks/todo.md` phase status

**Files Modified:** `backend/routes/audit.py`, `CLAUDE.md`, `tasks/todo.md`

**Pre-existing test failure:** `test_security.py::TestAccountLockoutIntegration::test_failed_login_returns_lockout_info` — bcrypt/passlib compatibility issue, unrelated to Phase XIX.

---

### Phase XX (Sprint 178) — Rate Limit Gap Closure
> **Focus:** Close rate limiting gaps found in Slowapi audit — missing limits on sensitive endpoints, no global default, IP-only keying
> **Source:** Manual rate limit audit of 21 route files (2026-02-12)
> **Strategy:** Single sprint — add missing decorators, add global default, document keying decision

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 178 | Rate limit gap closure + global default | 3/10 | COMPLETE |

#### Sprint 178 — Rate Limit Gap Closure — COMPLETE

**P0 — Critical (security-sensitive endpoints missing limits):**
- [x] `auth_routes.py`: Add `@limiter.limit(RATE_LIMIT_AUTH)` to `POST /auth/verify-email` — token brute-force vector
- [x] `users.py`: Add `@limiter.limit(RATE_LIMIT_AUTH)` to `PUT /users/me/password` — current-password brute-force with stolen session

**P1 — Medium (public/CPU-bound endpoints missing limits):**
- [x] `health.py`: Add `@limiter.limit("3/minute")` to `POST /waitlist` — public, writes to disk, DoS vector
- [x] `audit.py`: Add `@limiter.limit(RATE_LIMIT_AUDIT)` to `POST /audit/inspect-workbook` — CPU-bound file processing, sibling endpoints already limited

**P2 — Safety net (global default):**
- [x] `shared/rate_limits.py`: Add `default_limits=["60/minute"]` to `Limiter()` constructor — ensures new endpoints without explicit decorators still have a baseline limit

**Deferred — Dual-key rate limiting (IP + user_id):**
> Authenticated endpoints currently rate-limit by IP only. Behind shared NAT, all users share one bucket. Ideal fix: custom `key_func` that returns `f"{ip}:{user_id}"` for authenticated routes. Deferred because it requires a custom key function that reads the JWT from the request, adding complexity. Current IP-only + account lockout layering is adequate for initial deployment.

**Verification:**
- [x] `pytest` — 2,715 passed, 1 pre-existing failure (bcrypt/passlib), zero regressions
- [x] `npm run build` — clean pass
- [ ] Manual: confirm 429 on verify-email, password-change, waitlist, inspect-workbook when limit exceeded

**Files Modified:** `shared/rate_limits.py`, `routes/auth_routes.py`, `routes/users.py`, `routes/health.py`, `routes/audit.py`

---

### Phase XXI (Sprints 180-183) — Migration Hygiene — COMPLETE
> **Focus:** Fix broken Alembic migration chain — missing model imports, non-functional baseline, hardcoded DB URL, orphaned manual scripts
> **Source:** Alembic migration audit (2026-02-12)
> **Context:** Dual migration system (`Base.metadata.create_all()` at startup + Alembic + 2 manual scripts) with no coordination. Alembic is non-functional for fresh deployments. These sprints establish a working migration chain before any future schema changes require it.
> **Strategy:** Fix data-loss trap first → regenerate baseline → sync config → archive legacy scripts
> **Test Coverage at Phase XXI End:** 2,716 backend tests + 128 frontend tests | Version 1.2.0

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 180 | Fix env.py missing models + sync alembic.ini DB URL | 2/10 | COMPLETE |
| 181 | Regenerate Alembic baseline from current schema | 4/10 | COMPLETE |
| 182 | Archive manual migration scripts + update README | 2/10 | COMPLETE |
| 183 | Fix deprecated `datetime.utcnow()` + Phase XXI wrap | 1/10 | COMPLETE |

#### Sprint 180 — Fix env.py Missing Models + Sync DB URL — COMPLETE

- [x] Add `from follow_up_items_model import FollowUpItem, FollowUpItemComment` to `migrations/alembic/env.py`
- [x] Without this, `alembic revision --autogenerate` generates a migration that **drops** `follow_up_items` and `follow_up_item_comments` tables
- [x] In `migrations/alembic/env.py`, override the ini URL programmatically: `config.set_main_option("sqlalchemy.url", DATABASE_URL)` using `from config import DATABASE_URL`
- [x] Leave hardcoded `sqlalchemy.url` in `alembic.ini` as commented fallback
- [x] Verify: `alembic current` resolves correctly → `ae18bcf1ba02 (head)`
- [x] Verify: `Base.metadata.tables` contains all 9 tables (was missing `follow_up_items`, `follow_up_item_comments`)

**Verification:**
- [x] `pytest` — 2,457 passed, 1 pre-existing failure (bcrypt/passlib), zero regressions
- [x] `npm run build` — clean pass

**Files Modified:** `backend/migrations/alembic/env.py`, `backend/alembic.ini`

#### Sprint 181 — Regenerate Alembic Baseline — COMPLETE

- [x] Delete `migrations/alembic/versions/ae18bcf1ba02_*.py` (current baseline assumes pre-existing tables, fails on empty DB)
- [x] Generate new baseline against empty database: `alembic revision --autogenerate -m "baseline: full schema as of v1.2.0"` → revision `e2f21cb79a61`
- [x] Stamp existing database: updated `alembic_version` from `ae18bcf1ba02` → `e2f21cb79a61`
- [x] Verify: `alembic upgrade head` succeeds on a completely empty database — all 9 tables created
- [x] Verify: `alembic upgrade head` is a no-op on the stamped existing database
- [x] Verify: `alembic revision --autogenerate` produces an empty migration (zero schema drift)

**Verification:**
- [x] `pytest` — 2,457 passed, 1 pre-existing failure (bcrypt/passlib), zero regressions
- [x] `npm run build` — clean pass

**Files Created:** `migrations/alembic/versions/e2f21cb79a61_baseline_full_schema_as_of_v1_2_0.py`
**Files Deleted:** `migrations/alembic/versions/ae18bcf1ba02_initial_schema_users_clients_activity_.py`

#### Sprint 182 — Archive Manual Migration Scripts — COMPLETE

- [x] Verify Sprint 181 baseline captures all schema changes from `add_user_name_field.py` and `add_email_verification_fields.py`
  - `users.name` (baseline line 27), `users.tier` (line 30), `users.email_verification_token` (line 31), `users.email_verification_sent_at` (line 32), `users.email_verified_at` (line 33), `email_verification_tokens` table (lines 85-98) — all present
- [x] Create `migrations/archive/` directory
- [x] Move `migrations/add_user_name_field.py` → `migrations/archive/`
- [x] Move `migrations/add_email_verification_fields.py` → `migrations/archive/`
- [x] Update `migrations/README.md` — updated baseline section (all 9 tables), added Archived Scripts section

**Verification:**
- [x] `pytest` — 2,457 passed, 1 pre-existing failure (bcrypt/passlib), zero regressions
- [x] `npm run build` — clean pass

**Files Moved:** `add_user_name_field.py`, `add_email_verification_fields.py` → `migrations/archive/`
**Files Modified:** `migrations/README.md`

#### Sprint 183 — Deprecation Fix + Phase XXI Wrap — COMPLETE

- [x] Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` in `migrations/archive/add_email_verification_fields.py:85`
- [x] Verified: zero `datetime.utcnow()` usages remaining in project code (remaining warnings are from openpyxl third-party)
- [x] `pytest` — 2,457 passed, 1 pre-existing failure (bcrypt/passlib), zero regressions
- [x] `npm run build` — clean pass
- [x] Update `CLAUDE.md` — Phase XXI overview, completed phases list, current phase header
- [x] Update `tasks/todo.md` — mark all sprints COMPLETE

**Files Modified:** `migrations/archive/add_email_verification_fields.py`, `CLAUDE.md`, `tasks/todo.md`

**Deferred — Wire Alembic Into Startup:**
> Running `alembic upgrade head` at app startup (before `init_db()`) would auto-apply schema changes on deploy. Deferred because: (1) adds startup latency, (2) needs testing with multi-worker deployments (concurrent migration race), (3) revisit when deploying to PostgreSQL or when schema changes become frequent.
