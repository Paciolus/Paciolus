# Archived Sprint Details: Phases XIX-XXIII

> **Archived:** 2026-02-13 — Moved from todo.md to reduce context bloat.
> **These are completed sprint checklists. For current work, see todo.md.**

---

## Phase XIX (Sprints 171-177) — API Contract Hardening — COMPLETE
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

## Phase XX (Sprint 178) — Rate Limit Gap Closure — COMPLETE
> **Focus:** Close rate limiting gaps — missing limits on sensitive endpoints, no global default
> **Source:** Manual rate limit audit of 21 route files (2026-02-12)

#### Sprint 178 — Rate Limit Gap Closure — COMPLETE

**P0 — Critical (security-sensitive endpoints missing limits):**
- [x] `auth_routes.py`: Add `@limiter.limit(RATE_LIMIT_AUTH)` to `POST /auth/verify-email` — token brute-force vector
- [x] `users.py`: Add `@limiter.limit(RATE_LIMIT_AUTH)` to `PUT /users/me/password` — current-password brute-force with stolen session

**P1 — Medium (public/CPU-bound endpoints missing limits):**
- [x] `health.py`: Add `@limiter.limit("3/minute")` to `POST /waitlist` — public, writes to disk, DoS vector
- [x] `audit.py`: Add `@limiter.limit(RATE_LIMIT_AUDIT)` to `POST /audit/inspect-workbook` — CPU-bound file processing

**P2 — Safety net (global default):**
- [x] `shared/rate_limits.py`: Add `default_limits=["60/minute"]` to `Limiter()` constructor

**Deferred — Dual-key rate limiting (IP + user_id):**
> Authenticated endpoints currently rate-limit by IP only. Behind shared NAT, all users share one bucket. Deferred because it requires a custom key function that reads the JWT from the request.

**Files Modified:** `shared/rate_limits.py`, `routes/auth_routes.py`, `routes/users.py`, `routes/health.py`, `routes/audit.py`

---

## Phase XXI (Sprints 180-183) — Migration Hygiene — COMPLETE
> **Focus:** Fix broken Alembic migration chain — missing model imports, non-functional baseline, orphaned manual scripts
> **Source:** Alembic migration audit (2026-02-12)
> **Test Coverage at Phase XXI End:** 2,716 backend tests + 128 frontend tests | Version 1.2.0

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 180 | Fix env.py missing models + sync alembic.ini DB URL | 2/10 | COMPLETE |
| 181 | Regenerate Alembic baseline from current schema | 4/10 | COMPLETE |
| 182 | Archive manual migration scripts + update README | 2/10 | COMPLETE |
| 183 | Fix deprecated `datetime.utcnow()` + Phase XXI wrap | 1/10 | COMPLETE |

#### Sprint 180 — Fix env.py Missing Models + Sync DB URL — COMPLETE
- [x] Add `from follow_up_items_model import FollowUpItem, FollowUpItemComment` to `migrations/alembic/env.py`
- [x] Override ini URL programmatically: `config.set_main_option("sqlalchemy.url", DATABASE_URL)`
- [x] Verify: `alembic current` resolves correctly → `ae18bcf1ba02 (head)`
- [x] Verify: `Base.metadata.tables` contains all 9 tables

**Files Modified:** `backend/migrations/alembic/env.py`, `backend/alembic.ini`

#### Sprint 181 — Regenerate Alembic Baseline — COMPLETE
- [x] Delete old baseline `ae18bcf1ba02`, generate new: `e2f21cb79a61`
- [x] Stamp existing database
- [x] Verify: `alembic upgrade head` succeeds on empty database — all 9 tables created
- [x] Verify: `alembic revision --autogenerate` produces empty migration (zero drift)

**Files Created:** `migrations/alembic/versions/e2f21cb79a61_baseline_full_schema_as_of_v1_2_0.py`
**Files Deleted:** `migrations/alembic/versions/ae18bcf1ba02_initial_schema_users_clients_activity_.py`

#### Sprint 182 — Archive Manual Migration Scripts — COMPLETE
- [x] Verify baseline captures all schema from manual scripts
- [x] Move `add_user_name_field.py` and `add_email_verification_fields.py` → `migrations/archive/`
- [x] Update `migrations/README.md`

#### Sprint 183 — Deprecation Fix + Phase XXI Wrap — COMPLETE
- [x] Replace `datetime.utcnow()` → `datetime.now(timezone.utc)` in archived script
- [x] Zero `datetime.utcnow()` usages remaining in project code

**Deferred — Wire Alembic Into Startup:**
> Running `alembic upgrade head` at startup would auto-apply schema changes. Deferred: adds latency, needs multi-worker race testing.

---

## Phase XXII (Sprints 184-190) — Pydantic Model Hardening — COMPLETE
> **Focus:** Field constraints, Enum/Literal migration, manual validation removal, model decomposition, v2 syntax
> **Source:** Comprehensive Pydantic audit of 96 models across 28 files (2026-02-12)
> **Impact:** ~100 lines manual validation removed, 13 str→Enum/Literal migrations, 25+ Field constraints, WorkpaperMetadata base class (10 models), password validation centralized

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 184 | P0 security constraints: auth passwords, tokens, client names | 3/10 | COMPLETE |
| 185 | Enum-like strings → `Literal`/Enum types + manual validation removal | 5/10 | COMPLETE |
| 186 | `min_length` / `max_length` / `ge` / `le` constraints across all route models | 4/10 | COMPLETE |
| 187 | Decompose `DiagnosticSummary*` (30 fields) + extract `WorkpaperMetadata` base | 5/10 | COMPLETE |
| 188 | Migrate v1 `class Config:` → v2 `model_config = ConfigDict(...)` + naming fixes | 3/10 | COMPLETE |
| 189 | Password `@field_validator` + `sample_rate` range + date migration | 4/10 | COMPLETE |
| 190 | Phase XXII Wrap — regression + adjustments bugfix + documentation | 2/10 | COMPLETE |

#### Sprint 184 — P0 Security Constraints — COMPLETE
- [x] Auth models: `password` min_length=8, login/change min_length=1, token min_length=1
- [x] Client: `name` min_length=1, max_length=200
- [x] Follow-up items: description/tool_source/comment_text with bounds

**Files Modified:** `backend/auth.py`, `routes/auth_routes.py`, `routes/clients.py`, `routes/follow_up_items.py`

#### Sprint 185 — Enum/Literal Migration — COMPLETE
- [x] 13 str→Enum/Literal migrations across 6 files
- [x] Removed ~30 lines manual try/except enum validation

**Files Modified:** `routes/adjustments.py`, `routes/follow_up_items.py`, `routes/engagements.py`, `routes/settings.py`, `routes/contact.py`, `routes/prior_period.py`

#### Sprint 186 — Field Constraints — COMPLETE
- [x] 11 string fields gain min_length/max_length
- [x] 13 numeric fields gain ge/le bounds
- [x] 2 list fields gain min_length=1

**Files Modified:** `routes/adjustments.py`, `routes/activity.py`, `routes/diagnostics.py`, `routes/multi_period.py`, `routes/prior_period.py`, `routes/engagements.py`, `routes/settings.py`

#### Sprint 187 — Model Decomposition — COMPLETE
- [x] `DiagnosticSummaryCreate` decomposed: 30→13 fields + 3 sub-models (BalanceSheetTotals, IncomeStatementTotals, FinancialRatios)
- [x] `WorkpaperMetadata` base model: 10 export input models now inherit (50 lines removed)

**Files Modified:** `routes/diagnostics.py`, `shared/export_schemas.py`

#### Sprint 188 — V2 Syntax Migration — COMPLETE
- [x] 4 `class Config:` → `model_config = ConfigDict(...)` conversions in `auth.py`
- [x] 3 model renames: `Token`→`TokenResponse`, `EnumOption`→`EnumOptionResponse`, `PeriodListItem`→`PeriodListItemResponse`

**Files Modified:** `backend/auth.py`, `routes/adjustments.py`, `routes/prior_period.py`

#### Sprint 189 — Password Validator + Remaining Constraints — COMPLETE
- [x] `@field_validator('password')` on `UserCreate`, `@field_validator('new_password')` on `PasswordChange`
- [x] Removed `validate_password_strength()` standalone function
- [x] `sample_rate` Form field: `ge=0.01, le=1.0`
- [x] `period_date: Optional[str]` → `Optional[date]`

**Files Modified:** `auth.py`, `routes/auth_routes.py`, `routes/je_testing.py`, `routes/prior_period.py`

#### Sprint 190 — Phase XXII Wrap — COMPLETE
- [x] Fixed pre-existing bug: `adjustments.py:309` `new_status.value` → `status_update.status.value`
- [x] Full regression: 2,457 passed

**Deferred — Further Model Hygiene:**
> - `PaginatedResponse[T]` generic — complicates OpenAPI schema generation
> - Dedicated `backend/schemas/` directory — deferred until model count grows
> - Split dual-purpose settings models — pragmatic for JSON file storage

---

## Phase XXIII (Sprints 191-194) — Pandas Performance & Precision Hardening — COMPLETE
> **Focus:** Vectorize audit_engine.py, float zero-guard hardening, precision summation, dtype safety
> **Source:** Comprehensive Pandas audit — 2 performance anti-patterns, 7 float precision issues, 8 imprecise sums
> **Impact:** Vectorized keyword matching, NEAR_ZERO guards in 4 engines, math.fsum in 8 locations, identifier dtype preservation

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 191 | Vectorize audit_engine.py (.apply → .str.contains, filtered-index, Decimal accumulation) | 4/10 | COMPLETE |
| 192 | Float Zero-Guard Hardening (NEAR_ZERO guards in 4 variance engines) | 4/10 | COMPLETE |
| 193 | Precision Summation (8× math.fsum) + Identifier dtype preservation + dtype passthrough | 3/10 | COMPLETE |
| 194 | Phase XXIII Wrap — regression + documentation | 2/10 | COMPLETE |

#### Sprint 191 — Vectorize audit_engine.py — COMPLETE
- [x] Replace `.apply(lambda)` with `str.contains(regex)` for keyword matching
- [x] Replace `range(len(df))` loop with filtered-index iteration
- [x] Replace float accumulation with `Decimal` in `detect_concentration_risk()`

**Files Modified:** `audit_engine.py`, `tests/test_audit_engine.py`

#### Sprint 192 — Float Zero-Guard Hardening — COMPLETE
- [x] `prior_period_comparison.py`: `abs(prior) > NEAR_ZERO` guard, `inf` → `None`
- [x] `multi_period_comparison.py`: 3 locations
- [x] `flux_engine.py`: 3 locations
- [x] `three_way_match_engine.py`: 3 locations with 100% cap

**Files Modified:** `prior_period_comparison.py`, `multi_period_comparison.py`, `flux_engine.py`, `three_way_match_engine.py` + 4 test files

#### Sprint 193 — Precision Summation & dtype Safety — COMPLETE
- [x] 8× `sum()` → `math.fsum()` replacements
- [x] Identifier column dtype preservation in `shared/helpers.py`
- [x] `dtype` parameter added to all 5 `security_utils.py` reading functions

**Files Modified:** `revenue_testing_engine.py`, `ap_testing_engine.py`, `fixed_asset_testing_engine.py`, `inventory_testing_engine.py`, `shared/benford.py`, `shared/helpers.py`, `security_utils.py` + 2 test files

#### Sprint 194 — Phase XXIII Wrap — COMPLETE
- [x] Full regression: 2,731 passed
- [x] `npm run build` — clean pass

**Test Coverage at Phase XXIII End:** 2,731 backend tests + 128 frontend tests
