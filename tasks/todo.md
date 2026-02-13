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

### Phase XVIII (Sprints 164-170) — COMPLETE
> Async Architecture Remediation: `async def` → `def` for 82+ pure-DB/export endpoints, `asyncio.to_thread()` for CPU-bound Pandas work, `BackgroundTasks` for email/tool-run recording, `memory_cleanup()` context manager, rate limit gap closure. Zero behavioral regressions.

### Phase XIX (Sprints 171-177) — COMPLETE
> API Contract Hardening: 25 endpoints gain response_model, 16 status codes corrected (DELETE→204, POST→201), trends.py error-in-body→HTTPException(422), `/diagnostics/flux`→`/audit/flux` path fix, shared response schemas.

### Phase XX (Sprint 178) — COMPLETE
> Rate Limit Gap Closure: missing limits on verify-email, password-change, waitlist, inspect-workbook; global 60/min default.

### Phase XXI (Sprints 180-183) — COMPLETE
> Migration Hygiene: Alembic env.py model imports, baseline regeneration (e2f21cb79a61), manual script archival, datetime deprecation fix.

### Phase XXII (Sprints 184-190) — COMPLETE
> Pydantic Model Hardening: Field constraints (min_length/max_length/ge/le), 13 str→Enum/Literal migrations, ~100 lines manual validation removed, WorkpaperMetadata base class (10 models), DiagnosticSummaryCreate decomposition, v2 ConfigDict syntax, password field_validators, adjustments bugfix.

### Phase XXIII (Sprints 191-194) — COMPLETE
> Pandas Performance & Precision Hardening: vectorized keyword matching (.apply→.str.contains), filtered-index iteration, Decimal concentration totals, NEAR_ZERO float guards (4 engines), math.fsum compensated summation (8 locations), identifier dtype preservation, dtype passthrough in security_utils. **Tests: 2,731 backend + 128 frontend.**

> **Detailed checklists:** `tasks/archive/phases-vi-ix-details.md` | `tasks/archive/phases-x-xii-details.md` | `tasks/archive/phases-xiii-xvii-details.md` | `tasks/archive/phase-xviii-details.md` | `tasks/archive/phases-xix-xxiii-details.md`

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

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Multi-Currency Conversion | Detection shipped (Sprint 64); conversion logic needs RFC | Phase VII |
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, deficiency classification is auditor judgment | Phase X |
| Dual-key rate limiting (IP + user_id) | Needs custom JWT key_func; IP-only + lockout is adequate for now | Phase XX |
| Wire Alembic into startup | Adds latency, multi-worker race risk; revisit for PostgreSQL | Phase XXI |
| `PaginatedResponse[T]` generic | Complicates OpenAPI schema generation | Phase XXII |
| Dedicated `backend/schemas/` directory | Model count doesn't justify yet | Phase XXII |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |

---

## Phase XXIV — Upload & Export Security Hardening (Sprint 195) — COMPLETE

> **Status:** COMPLETE
> **Version:** 1.2.0 | **Tests:** 2,750 backend + 128 frontend
> **Source:** Comprehensive upload/export pipeline security audit (2026-02-13)

### Sprint 195 — Upload & Export Security Hardening

| # | Fix | Severity | Status |
|---|-----|----------|--------|
| 1 | CSV/Excel formula injection sanitization in all export endpoints | CRITICAL | COMPLETE |
| 2 | Column count limit in `parse_uploaded_file()` | MEDIUM | COMPLETE |
| 3 | Cell content length limit in `parse_uploaded_file()` | MEDIUM | COMPLETE |
| 4 | Global request body size limit middleware | LOW | COMPLETE |

#### Checklist

**Fix 1: Formula Injection (CWE-1236)**
- [x] Add `sanitize_csv_value()` to `shared/helpers.py`
- [x] Apply to `routes/export_testing.py` — 8 CSV endpoints (JE, AP, Payroll, TWM, Revenue, AR, FA, Inventory)
- [x] Apply to `routes/export_diagnostics.py` — TB CSV + Anomaly CSV
- [x] Apply to `excel_generator.py` — Standardized TB + Anomalies tabs (user-data cells)
- [x] Apply to `leadsheet_generator.py` — account_name + account_type cells

**Fix 2: Column Count Limit**
- [x] Add `MAX_COL_COUNT = 1_000` constant to `shared/helpers.py`
- [x] Add column count check after DataFrame parse in `parse_uploaded_file()`

**Fix 3: Cell Content Length Limit**
- [x] Add `MAX_CELL_LENGTH = 100_000` constant to `shared/helpers.py`
- [x] Add max cell string length check after parse in `parse_uploaded_file()`

**Fix 4: Global Body Size Limit**
- [x] Add `MaxBodySizeMiddleware` to `security_middleware.py` (110 MB threshold)
- [x] Wire middleware in `main.py`

**Tests**
- [x] Test `sanitize_csv_value()` with all trigger chars (`=`, `+`, `-`, `@`, `\t`, `\r`) — 13 tests
- [x] Test column count limit enforcement — 3 tests
- [x] Test cell content length limit enforcement — 3 tests
- [x] Run full `pytest` regression — 2,750 passed, 0 regressions

**Verification**
- [x] `pytest` — 2,750 passed (1 pre-existing TestClient failure)
- [x] Zero regressions from Sprint 195 changes

#### Review — Sprint 195

**Files Modified:**
- `backend/shared/helpers.py` — `sanitize_csv_value()`, `MAX_COL_COUNT`, `MAX_CELL_LENGTH`, column/cell checks
- `backend/security_middleware.py` — `MaxBodySizeMiddleware` class
- `backend/main.py` — Wire `MaxBodySizeMiddleware`
- `backend/routes/export_testing.py` — Sanitize 8 CSV export endpoints
- `backend/routes/export_diagnostics.py` — Sanitize TB + Anomaly CSV exports
- `backend/excel_generator.py` — Sanitize user-data cells in 3 locations
- `backend/leadsheet_generator.py` — Sanitize account name/type cells
- `backend/tests/test_upload_validation.py` — 19 new tests (13 sanitization + 3 column + 3 cell length)

---

## Sprint 196 — PDF Generator Critical Fixes — COMPLETE

> **Source:** Comprehensive ReportLab PDF generation review (2026-02-13)

| # | Fix | Severity | Status |
|---|-----|----------|--------|
| 1 | Fix `PaciolusReportGenerator._build_workpaper_signoff()` crash — nonexistent style/color/font refs | CRITICAL | COMPLETE |
| 2 | Fix hardcoded "7 available tools" in `anomaly_summary_generator.py` (now 11) | CRITICAL | COMPLETE |
| 3 | Close BytesIO buffer in `anomaly_summary_generator.py` `generate_pdf()` | MEDIUM | COMPLETE |

#### Checklist

**Fix 1: TB Diagnostic PDF Workpaper Signoff Crash**
- [x] Replace `self.styles['SectionTitle']` → `self.styles['SectionHeader']` + spaced header
- [x] Replace `ClassicalColors.OBSIDIAN_DARK` → `ClassicalColors.OBSIDIAN_DEEP` / `OBSIDIAN_600`
- [x] Replace font `'Merriweather'` → `'Times-Bold'`
- [x] Replace font `'Lato'` → `'Times-Roman'`
- [x] Align table style with Financial Statements signoff pattern (ledger rules, no background header)

**Fix 2: Wrong Tool Count**
- [x] Replace hardcoded `"7 of 7"` → dynamic `f"{len(ToolName)}"` in anomaly_summary_generator.py

**Fix 3: BytesIO Leak**
- [x] Add `buffer.close()` before return in `AnomalySummaryGenerator.generate_pdf()`

**Verification**
- [x] Smoke test: TB Diagnostic PDF with workpaper signoff generates successfully (101 KB)
- [x] `pytest tests/test_anomaly_summary.py` — 28 passed
- [x] `pytest tests/test_financial_statements.py tests/test_audit_engine.py` — 108 passed
- [x] Full `pytest` — 2,716 passed (1 pre-existing TestClient failure excluded)

#### Review — Sprint 196

**Files Modified:**
- `backend/pdf_generator.py` — Rewrote `_build_workpaper_signoff()` to use correct styles/colors/fonts
- `backend/anomaly_summary_generator.py` — Dynamic tool count via `len(ToolName)`, buffer.close()
- `tasks/todo.md` — Sprint 196 tracking

---

## Phase XXV — JWT Authentication Hardening (Sprints 197–201)

> **Status:** IN PROGRESS
> **Source:** Comprehensive JWT security audit (2026-02-13) — 3-agent parallel analysis
> **Strategy:** Short-lived tokens + refresh rotation first (highest impact), then revocation, then cleanup
> **Impact:** Mitigates 24-hour token theft window, enables server-side session control, closes CSRF gap

### Sprint 197 — Refresh Token Infrastructure (Backend) — COMPLETE

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create `RefreshToken` database model (token_hash, user_id, expires_at, revoked_at, replaced_by_hash) | HIGH | COMPLETE |
| 2 | Add Alembic migration for `refresh_tokens` table | HIGH | COMPLETE |
| 3 | Implement `create_refresh_token()` in `auth.py` — `secrets.token_urlsafe(48)`, 7-day expiry, SHA-256 hash stored in DB | HIGH | COMPLETE |
| 4 | Implement `POST /auth/refresh` endpoint — validate refresh token, rotate (issue new pair, revoke old) | HIGH | COMPLETE |
| 5 | Reduce access token expiration default from 1440 → 30 minutes | HIGH | DEFERRED to Sprint 198 (needs frontend refresh logic first) |
| 6 | Update `POST /auth/login` and `POST /auth/register` to return both access + refresh tokens | HIGH | COMPLETE |
| 7 | Add `POST /auth/logout` endpoint — revoke refresh token server-side | HIGH | COMPLETE |

#### Checklist

- [x] `RefreshToken` model: token_hash (String 64, unique, indexed), user_id (FK), expires_at, revoked_at, created_at, replaced_by_hash
- [x] Alembic migration generated and tested
- [x] `create_refresh_token(user_id)` → returns raw token string, stores SHA-256 hash in DB
- [x] `POST /auth/refresh` — validates refresh token, issues new access + refresh pair, revokes old refresh token (rotation)
- [x] `POST /auth/logout` — revokes refresh token by setting `revoked_at`
- [x] `JWT_EXPIRATION_MINUTES` default changed to `30` in `config.py` — completed in Sprint 198
- [x] `REFRESH_TOKEN_EXPIRATION_DAYS` config variable added (default: 7)
- [x] Rate limit on `/auth/refresh`: `RATE_LIMIT_AUTH`
- [x] Rate limit on `/auth/logout`: `RATE_LIMIT_AUTH`
- [x] Tests: refresh token creation, rotation, expiry, revocation, reuse detection (53 tests)
- [x] Fix pre-existing `test_security.py` status code assertion (200→201)
- [x] Full regression: 2,804 passed, 0 failed

#### Review — Sprint 197

**Files Modified:** config.py, models.py, auth.py, routes/auth_routes.py, database.py, migrations/alembic/env.py, .env.example, tests/conftest.py, tests/test_security.py
**Files Created:** migrations/alembic/versions/17fe65a813fb_add_refresh_tokens_table.py, tests/test_refresh_tokens.py

### Sprint 198 — Refresh Token Frontend Integration — COMPLETE

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Update `AuthContext` to store refresh token in sessionStorage/localStorage | HIGH | COMPLETE |
| 2 | Add silent token refresh in `apiClient.ts` — intercept 401, call `/auth/refresh`, retry original request | HIGH | COMPLETE |
| 3 | Update `login()` and `register()` to persist both tokens | HIGH | COMPLETE |
| 4 | Update `logout()` to call `POST /auth/logout` then clear all storage | HIGH | COMPLETE |
| 5 | Implement "Remember Me" — localStorage for refresh token persistence across sessions | LOW | COMPLETE |

#### Checklist

- [x] `AuthResponse` type: add `refresh_token` field
- [x] `AuthContextType`: update `login` signature for `rememberMe`, `logout` returns `void | Promise<void>`
- [x] `AuthContext.tsx`: store `paciolus_refresh_token` in sessionStorage (default) or localStorage (Remember Me)
- [x] `AuthContext.tsx`: `refreshAccessToken()` with deduplication via `useRef`
- [x] `AuthContext.tsx`: init from localStorage refresh token on page load (Remember Me recovery)
- [x] `AuthContext.tsx`: register `setTokenRefreshCallback` for apiClient 401 interception
- [x] `apiClient.ts`: `setTokenRefreshCallback` + 401 interceptor — retry failed request with new token
- [x] Prevent refresh loop: skip `/auth/refresh`, `/auth/login`, `/auth/register` endpoints
- [x] `logout()`: `POST /auth/logout` with refresh token, then clear sessionStorage + localStorage
- [x] "Remember Me": wired checkbox → `localStorage` for refresh token, `sessionStorage` for access token
- [x] `login/page.tsx`: pass `rememberMe: formValues.rememberMe` to `login()` call
- [x] `config.py`: `JWT_EXPIRATION_MINUTES` default changed from 1440 → 30
- [x] `.env.example`: updated JWT documentation for 30-minute default
- [x] `npm run build` — passes
- [x] `pytest` — 2,804 passed, 0 regressions

#### Review — Sprint 198

**Files Modified:** `frontend/src/types/auth.ts`, `frontend/src/contexts/AuthContext.tsx`, `frontend/src/utils/apiClient.ts`, `frontend/src/utils/index.ts`, `frontend/src/app/login/page.tsx`, `backend/config.py`, `backend/.env.example`

### Sprint 199 — Token Revocation on Password Change

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Revoke all refresh tokens on password change (`change_user_password()`) | HIGH | COMPLETE |
| 2 | Add `password_changed_at` column to `User` model | MEDIUM | COMPLETE |
| 3 | Validate `password_changed_at` in `decode_access_token()` — reject tokens issued before last password change | MEDIUM | COMPLETE |
| 4 | Revoke all refresh tokens on account deactivation | MEDIUM | COMPLETE |

#### Checklist

- [x] `User.password_changed_at` column (DateTime, nullable)
- [x] Alembic migration for `password_changed_at`
- [x] `change_user_password()` sets `password_changed_at = datetime.now(UTC)` and revokes all user's refresh tokens
- [x] `create_access_token()` embeds `pwd_at` claim (epoch of `password_changed_at`)
- [x] `decode_access_token()` returns `password_changed_at` in `TokenData`
- [x] `require_current_user()` compares token's `pwd_at` claim against DB `password_changed_at` — reject if stale
- [x] Account deactivation (`is_active=False`) revokes all refresh tokens (via `_revoke_all_user_tokens()`)
- [x] Tests: 28 tests — password change invalidates old tokens, deactivation revokes tokens, SQLite timezone handling
- [x] `pytest` — 2,832 passed, 0 regressions

#### Review — Sprint 199

**Files Modified:** `backend/models.py`, `backend/auth.py`, `backend/routes/auth_routes.py`, `backend/migrations/alembic/versions/c324b5d13ed5_add_password_changed_at_to_users.py`, `backend/tests/test_password_revocation.py`

### Sprint 200 — CSRF & CORS Hardening

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Register `CSRFMiddleware` in `main.py` | MEDIUM | NOT STARTED |
| 2 | Add CSRF token fetch to frontend `AuthContext` on login | MEDIUM | NOT STARTED |
| 3 | Inject `X-CSRF-Token` header in `apiClient.ts` for mutation requests | MEDIUM | NOT STARTED |
| 4 | Restrict CORS `allow_methods` to actual methods used | LOW | NOT STARTED |
| 5 | Restrict CORS `allow_headers` to actual headers used | LOW | NOT STARTED |
| 6 | Remove `allow_credentials=True` if cookie-based auth not adopted | LOW | NOT STARTED |

#### Checklist

- [ ] `main.py`: `app.add_middleware(CSRFMiddleware)` after `SecurityHeadersMiddleware`
- [ ] Frontend: fetch `/auth/csrf` after login, store token in memory (not sessionStorage)
- [ ] `apiClient.ts`: attach `X-CSRF-Token` header on POST/PUT/DELETE/PATCH requests
- [ ] CORS `allow_methods`: `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`
- [ ] CORS `allow_headers`: `["Authorization", "Content-Type", "X-CSRF-Token", "Accept"]`
- [ ] Evaluate `allow_credentials` — remove if not needed (no cookies in use)
- [ ] `npm run build` — must pass
- [ ] Tests: CSRF-protected endpoints reject requests without valid token

### Sprint 201 — Cleanup & Explicit Configuration

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Set explicit bcrypt rounds: `bcrypt__rounds=12` | LOW | NOT STARTED |
| 2 | Clean up expired refresh tokens — background task or startup job | LOW | NOT STARTED |
| 3 | Add `jti` (JWT ID) claim for future token-level revocation | LOW | NOT STARTED |
| 4 | Document production JWT configuration in `.env.example` | LOW | NOT STARTED |

#### Checklist

- [ ] `auth.py`: `CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)`
- [ ] Startup task or periodic background job: delete refresh tokens where `revoked_at IS NOT NULL` or `expires_at < now`
- [ ] `create_access_token()`: add `jti=secrets.token_hex(16)` claim
- [ ] `.env.example`: document `JWT_EXPIRATION_MINUTES=30`, `JWT_REFRESH_EXPIRATION_DAYS=7`
- [ ] Update `CLAUDE.md` Phase XXV entry after completion
- [ ] Full `pytest` regression — 0 regressions
- [ ] `npm run build` — must pass
