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
| Cookie-based auth (enables SSR) | Requires migrating JWT from sessionStorage to httpOnly cookies; large blast radius | Phase XXVII audit |
| Marketing pages SSG | Requires cookie auth migration first; currently all pages are `'use client'` | Phase XXVII audit |

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

## Phase XXV — JWT Authentication Hardening (Sprints 197–201) — COMPLETE

> **Status:** COMPLETE
> **Tests:** 2,888 backend + 128 frontend
> **Source:** Comprehensive JWT security audit (2026-02-13) — 3-agent parallel analysis
> **Strategy:** Short-lived tokens + refresh rotation first (highest impact), then revocation, then cleanup
> **Impact:** Mitigates 24-hour token theft window, enables server-side session control, closes CSRF gap, explicit bcrypt rounds, jti claim for future revocation

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

### Sprint 200 — CSRF & CORS Hardening — COMPLETE

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Register `CSRFMiddleware` in `main.py` | MEDIUM | COMPLETE |
| 2 | Add CSRF token fetch to frontend `AuthContext` on login/register/refresh | MEDIUM | COMPLETE |
| 3 | Inject `X-CSRF-Token` header in `apiClient.ts` for mutation requests | MEDIUM | COMPLETE |
| 4 | Inject `X-CSRF-Token` in 7 direct `fetch()` callsites (useAuditUpload, etc.) | MEDIUM | COMPLETE |
| 5 | Restrict CORS `allow_methods` to actual methods used | LOW | COMPLETE |
| 6 | Restrict CORS `allow_headers` to actual headers used | LOW | COMPLETE |
| 7 | Evaluate `allow_credentials` — kept `True` (no downside, adds defense-in-depth) | LOW | COMPLETE |

#### Checklist

- [x] `main.py`: `app.add_middleware(CSRFMiddleware)` after `SecurityHeadersMiddleware`
- [x] `security_middleware.py`: Updated CSRF exempt paths (+5: refresh, logout, verify-email, contact/submit, waitlist)
- [x] `security_middleware.py`: Changed CSRFMiddleware to return Response (not raise HTTPException) for BaseHTTPMiddleware compatibility
- [x] `security_middleware.py`: Removed unused `HTTPException`/`status` imports
- [x] Frontend: `apiClient.ts` — `setCsrfToken()`, `getCsrfToken()`, `fetchCsrfToken()` module-level CSRF management
- [x] Frontend: `apiClient.ts` — CSRF token auto-injected on POST/PUT/DELETE/PATCH in `apiFetch()` and `apiDownload()`
- [x] Frontend: `apiClient.ts` — CSRF token refreshed after 401 token refresh
- [x] Frontend: `AuthContext.tsx` — `fetchCsrfToken()` after login, register, and token refresh; `setCsrfToken(null)` on logout
- [x] Frontend: Updated 7 direct `fetch()` callsites with CSRF injection:
  - `useAuditUpload.ts` (all 9+ tool uploads)
  - `useTrialBalanceAudit.ts` (TB audit)
  - `BatchUploadContext.tsx` (batch upload)
  - `DownloadReportButton.tsx` (PDF export)
  - `FinancialStatementsPreview.tsx` (financial statements export)
  - `multi-period/page.tsx` (multi-period upload)
  - `SamplingPanel.tsx` (JE sampling — 2 calls)
- [x] CORS `allow_methods`: `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`
- [x] CORS `allow_headers`: `["Authorization", "Content-Type", "X-CSRF-Token", "Accept"]`
- [x] `allow_credentials=True` retained (defense-in-depth, prevents wildcard origin loophole)
- [x] `npm run build` — passes
- [x] 42 new tests: token generation, validation, expiry, cleanup, exempt paths, middleware blocking, CORS config
- [x] `conftest.py`: autouse session fixture bypasses CSRF for API tests (CSRF tested explicitly in test_csrf_middleware.py)
- [x] `pytest` — 2,874 passed, 0 regressions

#### Review — Sprint 200

**Files Modified:**
- `backend/security_middleware.py` — Updated exempt paths, Response instead of HTTPException, removed unused imports
- `backend/main.py` — Registered CSRFMiddleware, restricted CORS methods/headers
- `backend/tests/conftest.py` — CSRF bypass autouse fixture for API tests
- `frontend/src/utils/apiClient.ts` — CSRF token management (set/get/fetch), auto-injection on mutations + downloads
- `frontend/src/utils/index.ts` — Export setCsrfToken, getCsrfToken, fetchCsrfToken
- `frontend/src/contexts/AuthContext.tsx` — fetchCsrfToken after login/register/refresh, setCsrfToken(null) on logout
- `frontend/src/hooks/useAuditUpload.ts` — CSRF header injection
- `frontend/src/hooks/useTrialBalanceAudit.ts` — CSRF header injection
- `frontend/src/contexts/BatchUploadContext.tsx` — CSRF header injection
- `frontend/src/components/export/DownloadReportButton.tsx` — CSRF header injection
- `frontend/src/components/financialStatements/FinancialStatementsPreview.tsx` — CSRF header injection
- `frontend/src/app/tools/multi-period/page.tsx` — CSRF header injection
- `frontend/src/components/jeTesting/SamplingPanel.tsx` — CSRF header injection (2 calls)

**Files Created:**
- `backend/tests/test_csrf_middleware.py` — 42 tests

### Sprint 201 — Cleanup & Explicit Configuration — COMPLETE

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Set explicit bcrypt rounds: `bcrypt__rounds=12` | LOW | COMPLETE |
| 2 | Clean up expired refresh tokens — startup job | LOW | COMPLETE |
| 3 | Add `jti` (JWT ID) claim for future token-level revocation | LOW | COMPLETE |
| 4 | Document production JWT configuration in `.env.example` | LOW | COMPLETE (already done in Sprint 198) |

#### Checklist

- [x] `auth.py`: `CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)`
- [x] `auth.py`: `cleanup_expired_refresh_tokens(db)` — delete revoked/expired tokens
- [x] `main.py`: call cleanup on startup via `SessionLocal`
- [x] `create_access_token()`: add `jti=secrets.token_hex(16)` claim
- [x] `.env.example`: verified — JWT docs already complete from Sprint 198
- [x] Tests: 14 new tests (4 bcrypt, 4 jti, 6 cleanup)
- [x] Full `pytest` regression — 2,888 passed, 0 regressions
- [x] `npm run build` — passes

#### Review — Sprint 201

**Files Modified:**
- `backend/auth.py` — `bcrypt__rounds=12`, `jti` claim in `create_access_token()`, `cleanup_expired_refresh_tokens()` function
- `backend/main.py` — Call `cleanup_expired_refresh_tokens()` on startup

**Files Created:**
- `backend/tests/test_sprint201_cleanup.py` — 14 tests (bcrypt rounds, jti claim, token cleanup)

---

## Phase XXVI — Email Verification Hardening (Sprints 202–203) — COMPLETE

> **Status:** COMPLETE
> **Tests:** 2,903 backend + 128 frontend
> **Source:** Security audit of SendGrid email verification flow (2026-02-13)
> **Strategy:** Token cleanup first (simple), then email-change re-verification (pending email approach)

### Sprint 202 — Verification Token Cleanup Job — COMPLETE

| # | Task | Status |
|---|------|--------|
| 1 | Add `cleanup_expired_verification_tokens()` to `auth.py` | COMPLETE |
| 2 | Register in `main.py` startup event | COMPLETE |
| 3 | Tests: 6 test cases in `test_sprint202_cleanup.py` | COMPLETE |

#### Checklist

- [x] `cleanup_expired_verification_tokens()` in `auth.py` — delete used/expired `EmailVerificationToken` rows
- [x] Register in `main.py` startup alongside refresh token cleanup
- [x] Tests: deletes used, deletes expired, preserves active, mixed, zero stale, multi-user
- [x] `pytest tests/test_sprint202_cleanup.py -v` — 6 passed

#### Review — Sprint 202

**Files Modified:**
- `backend/auth.py` — `cleanup_expired_verification_tokens()` function, `EmailVerificationToken` import
- `backend/main.py` — Call cleanup on startup alongside refresh token cleanup

**Files Created:**
- `backend/tests/test_sprint202_cleanup.py` — 6 tests

### Sprint 203 — Email-Change Re-Verification — COMPLETE

| # | Task | Status |
|---|------|--------|
| 1 | Add `pending_email` column to User model + Alembic migration | COMPLETE |
| 2 | Update `UserResponse` schema with `pending_email` | COMPLETE |
| 3 | Refactor `update_user_profile()` — pending email instead of direct swap | COMPLETE |
| 4 | Update `/users/me` endpoint — rate limit, BackgroundTasks, email sending | COMPLETE |
| 5 | Update `verify_email()` — swap pending_email on verification | COMPLETE |
| 6 | Update `resend_verification()` — allow resend for pending email change | COMPLETE |
| 7 | Add `send_email_change_notification()` to `email_service.py` | COMPLETE |
| 8 | Frontend: `pending_email` in User type + profile page banner | COMPLETE |
| 9 | Tests: 9 test cases in `test_email_change.py` | COMPLETE |

#### Checklist

- [x] `models.py`: `pending_email = Column(String(255), nullable=True)`
- [x] Alembic migration: `ea6c8f7cc976_add_pending_email_to_users.py`
- [x] `auth.py`: `pending_email: Optional[str] = None` in `UserResponse`
- [x] `auth.py`: Refactor `update_user_profile()` → return `tuple[User, Optional[str]]`
- [x] `routes/users.py`: Rate limit, BackgroundTasks, email sending for email changes
- [x] `routes/auth_routes.py`: `verify_email()` swaps `pending_email → email`
- [x] `routes/auth_routes.py`: `resend_verification()` allows verified users with pending email
- [x] `email_service.py`: `send_email_change_notification()` to old email
- [x] `frontend/src/types/auth.ts`: `pending_email?: string | null`
- [x] `frontend/src/app/settings/profile/page.tsx`: Pending email banner (clay-50/clay-200)
- [x] Tests: 9 test cases — all passing
- [x] `pytest tests/test_email_change.py -v` — 9 passed
- [x] `npm run build` — passes
- [x] Full regression: 2,903 passed, 0 regressions

#### Review — Sprint 203

**Files Modified:**
- `backend/models.py` — `pending_email` column on User
- `backend/auth.py` — `UserResponse.pending_email`, refactored `update_user_profile()` to pending email workflow
- `backend/routes/users.py` — Rate limit, BackgroundTasks, verification + notification emails
- `backend/routes/auth_routes.py` — `verify_email()` pending swap, `resend_verification()` pending guard
- `backend/email_service.py` — `send_email_change_notification()` function
- `frontend/src/types/auth.ts` — `pending_email` field
- `frontend/src/app/settings/profile/page.tsx` — Pending email banner

**Files Created:**
- `backend/migrations/alembic/versions/ea6c8f7cc976_add_pending_email_to_users.py`
- `backend/tests/test_email_change.py` — 9 tests

---

## Phase XXVII — Next.js App Router Hardening (Sprints 204–209)

> **Status:** IN PROGRESS
> **Source:** Comprehensive Next.js App Router audit (2026-02-13) — 4-agent parallel analysis
> **Strategy:** Error boundaries first (P0), then route groups to eliminate duplication, then provider/fetch cleanup
> **Scope:** 0 loading.tsx → systematic coverage, 0 error.tsx → systematic coverage, 0 route groups → 3 groups, 38 duplicated imports eliminated, DiagnosticProvider scoped, 8 direct fetch() migrated
> **Deferred:** Cookie-based auth migration (enables SSR/SSG for marketing pages) — too large for this phase

### Sprint 204 — Global Error Infrastructure — COMPLETE

> **Complexity:** 3/10
> **Goal:** Add `global-error.tsx`, root `not-found.tsx`, and root `error.tsx` — the three missing Next.js file-based boundaries that currently leave the app with blank screens on errors and default 404s.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create `app/global-error.tsx` — catches root layout errors, renders branded dark-theme fallback with "Reload Paciolus" button | CRITICAL | COMPLETE |
| 2 | Create `app/not-found.tsx` — branded 404 page (Oat & Obsidian dark theme), links to homepage/login | HIGH | COMPLETE |
| 3 | Create `app/error.tsx` — root-level error boundary with reset/retry, dev-mode error detail | HIGH | COMPLETE |

#### Checklist

**global-error.tsx**
- [x] Must include its own `<html>` and `<body>` tags (Next.js requirement — replaces root layout)
- [x] Dark theme (vault exterior aesthetic) — inline styles with obsidian gradient (Tailwind unavailable here)
- [x] "Reload Paciolus" button → `window.location.reload()`
- [x] Dev-mode error message display (`process.env.NODE_ENV === 'development'`) + digest display
- [x] `'use client'` directive (required by Next.js)
- [x] Google Fonts link for Merriweather + Lato (stylesheet unavailable in global-error)
- [x] "Try Again" button → `reset()` + "Reload Paciolus" button

**not-found.tsx**
- [x] Oat & Obsidian branded 404 — serif heading, sans body, mono 404 badge
- [x] "Back to Home" and "Go to Login" links
- [x] Dark theme via explicit obsidian/oatmeal classes (ThemeProvider defaults unknown routes to light)
- [x] Server Component (no `'use client'`)

**error.tsx**
- [x] `'use client'` directive (required by Next.js)
- [x] Accepts `{ error, reset }` props
- [x] "Try Again" button → calls `reset()` with refresh icon
- [x] "Back to Home" link fallback
- [x] Theme-aware via semantic tokens (`text-content-primary`, `bg-surface-card`, etc.)
- [x] Dev-mode error detail panel with digest

**Verification**
- [x] `npm run build` — passes (36 static pages, 0 errors)

#### Review — Sprint 204

**Files Created:**
- `frontend/src/app/global-error.tsx` — Standalone error boundary with own html/body, inline obsidian styles, font import
- `frontend/src/app/not-found.tsx` — Server Component 404 page, explicit dark classes, home/login links
- `frontend/src/app/error.tsx` — Client error boundary, semantic token theme-awareness, reset/retry/home actions

---

### Sprint 205 — Marketing Route Group — COMPLETE

> **Complexity:** 4/10
> **Goal:** Create `(marketing)` route group with shared layout containing `MarketingNav` + `MarketingFooter`, eliminating 16 duplicated imports across 8 pages.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create `app/(marketing)/layout.tsx` with `MarketingNav` + `MarketingFooter` | HIGH | COMPLETE |
| 2 | Move 8 marketing pages into `(marketing)/` group | HIGH | COMPLETE |
| 3 | Remove `MarketingNav` / `MarketingFooter` imports from all 8 moved pages | HIGH | COMPLETE |
| 4 | Update `ThemeProvider` DARK_ROUTES if paths change (route groups are URL-transparent) | MEDIUM | N/A — no changes needed |

#### Checklist

**Layout**
- [x] `app/(marketing)/layout.tsx` — Server Component, renders `<MarketingNav />`, `{children}`, `<MarketingFooter />`
- [x] Dark theme — these are vault exterior pages (MarketingNav is client component, MarketingFooter is server component)
- [x] No `'use client'` needed — layout is a Server Component that renders client/server child components

**Page Moves (8 pages, URL-transparent)**
- [x] `app/page.tsx` → `app/(marketing)/page.tsx` (homepage)
- [x] `app/about/page.tsx` → `app/(marketing)/about/page.tsx`
- [x] `app/approach/page.tsx` → `app/(marketing)/approach/page.tsx`
- [x] `app/contact/page.tsx` → `app/(marketing)/contact/page.tsx`
- [x] `app/pricing/page.tsx` → `app/(marketing)/pricing/page.tsx`
- [x] `app/privacy/page.tsx` → `app/(marketing)/privacy/page.tsx`
- [x] `app/terms/page.tsx` → `app/(marketing)/terms/page.tsx`
- [x] `app/trust/page.tsx` → `app/(marketing)/trust/page.tsx`

**Cleanup per page**
- [x] Remove `import { MarketingNav }` from each page (or from combined import)
- [x] Remove `import { MarketingFooter }` from each page (or from combined import)
- [x] Remove `<MarketingNav />` and `<MarketingFooter />` JSX from each page
- [x] Verified: only layout.tsx references MarketingNav/MarketingFooter in `(marketing)/`

**Theme / Routing**
- [x] `ThemeProvider` DARK_ROUTES unchanged — route groups are URL-transparent
- [x] All routes confirmed in build output: `/`, `/about`, `/approach`, `/contact`, `/pricing`, `/privacy`, `/terms`, `/trust`
- [x] `MarketingNav` active-link highlighting uses `usePathname()` — still works (paths unchanged)

**Verification**
- [x] `npm run build` — passes (36 static pages, 0 errors)
- [x] Stale `.next/dev/types/validator.ts` required cache clean (expected after file moves)

#### Review — Sprint 205

**Files Created:**
- `frontend/src/app/(marketing)/layout.tsx` — Server Component layout with MarketingNav + MarketingFooter

**Files Moved (git mv):**
- `app/page.tsx` → `app/(marketing)/page.tsx`
- `app/about/page.tsx` → `app/(marketing)/about/page.tsx`
- `app/approach/page.tsx` → `app/(marketing)/approach/page.tsx`
- `app/contact/page.tsx` → `app/(marketing)/contact/page.tsx`
- `app/pricing/page.tsx` → `app/(marketing)/pricing/page.tsx`
- `app/privacy/page.tsx` → `app/(marketing)/privacy/page.tsx`
- `app/terms/page.tsx` → `app/(marketing)/terms/page.tsx`
- `app/trust/page.tsx` → `app/(marketing)/trust/page.tsx`

**Lines Removed:** ~32 lines (16 imports + 16 JSX tags across 8 pages)

---

### Sprint 206 — Auth Route Group — COMPLETE

> **Complexity:** 4/10
> **Goal:** Create `(auth)` route group with shared layout for centering + "Back to Paciolus" footer, reducing duplicated structure across 4 auth pages.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create `app/(auth)/layout.tsx` — shared centering wrapper + back link | HIGH | COMPLETE |
| 2 | Move 4 auth pages into `(auth)/` group | HIGH | COMPLETE |
| 3 | Strip shared structure from each page | MEDIUM | COMPLETE |

#### Checklist

**Shared Auth Layout**
- [x] `app/(auth)/layout.tsx` — Server Component (no 'use client' needed)
- [x] Shared structure: `<main>` centering container + `bg-gradient-obsidian` + `max-w-md` width constraint
- [x] "Back to Paciolus" footer link with back arrow icon (shared across all 4 pages)
- [x] Animation variants kept in pages (containerVariants/itemVariants tightly coupled to per-page content)

**Page Moves (4 pages, URL-transparent)**
- [x] `app/login/page.tsx` → `app/(auth)/login/page.tsx`
- [x] `app/register/page.tsx` → `app/(auth)/register/page.tsx`
- [x] `app/verify-email/page.tsx` → `app/(auth)/verify-email/page.tsx`
- [x] `app/verification-pending/page.tsx` → `app/(auth)/verification-pending/page.tsx`

**Per-page cleanup**
- [x] Removed `<main>` wrapper + `bg-gradient-obsidian` centering (layout provides this)
- [x] Removed `className="w-full max-w-md"` from outer motion.div (layout provides this)
- [x] Removed "Back to Paciolus" `<motion.div>` block (~15 lines each × 4 pages)
- [x] Updated Suspense fallbacks in verify-email + verification-pending (removed `<main>` wrapper)
- [x] Pages retain animation variants + vault card structure (form content unchanged)

**Theme / Routing**
- [x] `ThemeProvider` DARK_ROUTES unchanged — route groups are URL-transparent
- [x] All 4 routes confirmed in build output: `/login`, `/register`, `/verify-email`, `/verification-pending`
- [x] `useSearchParams()` pages still have `<Suspense>` wrappers (verify-email, verification-pending)

**Verification**
- [x] `npm run build` — passes (36 static pages, 0 errors)

#### Review — Sprint 206

**Files Created:**
- `frontend/src/app/(auth)/layout.tsx` — Server Component: centering container + max-w-md + "Back to Paciolus" link

**Files Moved (git mv):**
- `app/login/page.tsx` → `app/(auth)/login/page.tsx`
- `app/register/page.tsx` → `app/(auth)/register/page.tsx`
- `app/verify-email/page.tsx` → `app/(auth)/verify-email/page.tsx`
- `app/verification-pending/page.tsx` → `app/(auth)/verification-pending/page.tsx`

**Lines Removed:** ~80 lines (4 × `<main>` wrapper + 4 × `max-w-md` class + 4 × "Back to Paciolus" block + 2 × Suspense fallback `<main>`)

---

### Sprint 207 — Tool Layout Consolidation + Boundaries — PLANNED

> **Complexity:** 5/10
> **Goal:** Move `ToolNav` + `VerificationBanner` from 11 individual tool pages into `tools/layout.tsx`, add shared `tools/loading.tsx` + `tools/error.tsx`. Eliminates 22 duplicated imports.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Add `ToolNav` + `VerificationBanner` to `tools/layout.tsx` | HIGH | PENDING |
| 2 | Remove `ToolNav` + `VerificationBanner` imports/JSX from all 11 tool pages | HIGH | PENDING |
| 3 | Add shared auth redirect guard in `tools/layout.tsx` | MEDIUM | PENDING |
| 4 | Create `tools/loading.tsx` — shared tool loading skeleton | MEDIUM | PENDING |
| 5 | Create `tools/error.tsx` — shared tool error boundary with retry | MEDIUM | PENDING |

#### Checklist

**Layout Expansion**
- [ ] `tools/layout.tsx`: import and render `<ToolNav />` (pass `currentTool` via `usePathname()`)
- [ ] `tools/layout.tsx`: import and render `<VerificationBanner />`
- [ ] `tools/layout.tsx`: add auth guard — redirect to `/login` if not authenticated
- [ ] Ensure `ToolNav` `currentTool` prop derived from URL segment (`/tools/journal-entry-testing` → `"journal-entry-testing"`)
- [ ] Maintain existing `EngagementProvider` + `EngagementBanner` + `ToolLinkToast` structure

**Per-page cleanup (11 tool pages)**
- [ ] `tools/trial-balance/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/journal-entry-testing/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/ap-testing/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/bank-rec/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/multi-period/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/payroll-testing/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/three-way-match/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/revenue-testing/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/ar-aging/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/fixed-assets/page.tsx` — remove ToolNav, VerificationBanner, auth redirect
- [ ] `tools/inventory-testing/page.tsx` — remove ToolNav, VerificationBanner, auth redirect

**Loading + Error Boundaries**
- [ ] `tools/loading.tsx` — skeleton UI: ToolNav placeholder, upload zone skeleton, results panel skeleton
- [ ] `tools/error.tsx` — `'use client'`, accepts `{ error, reset }`, "Try Again" button, light-theme aware
- [ ] Both files use Oat & Obsidian semantic tokens (`bg-surface-page`, `border-theme`, etc.)

**Verification**
- [ ] `npm run build` — passes
- [ ] All 11 tool pages render with ToolNav + VerificationBanner from layout
- [ ] No duplicate ToolNav on any page
- [ ] Tool switching preserves engagement banner
- [ ] Auth redirect works when unauthenticated

---

### Sprint 208 — Provider Scoping + Fetch Consolidation + Route Boundaries — PLANNED

> **Complexity:** 5/10
> **Goal:** Scope `DiagnosticProvider` to the 2 pages that use it, migrate 8 direct `fetch()` calls to `apiClient`, add `loading.tsx` + `error.tsx` to high-traffic authenticated routes.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Remove `DiagnosticProvider` from global `providers.tsx` | MEDIUM | PENDING |
| 2 | Wrap `DiagnosticProvider` locally in `flux/page.tsx` and `recon/page.tsx` | MEDIUM | PENDING |
| 3 | Migrate 8 direct `fetch()` calls to `apiClient` | MEDIUM | PENDING |
| 4 | Add `loading.tsx` + `error.tsx` to `engagements/` | HIGH | PENDING |
| 5 | Add `loading.tsx` + `error.tsx` to `portfolio/` | MEDIUM | PENDING |
| 6 | Add `loading.tsx` + `error.tsx` to `settings/` (covers profile + practice) | MEDIUM | PENDING |

#### Checklist

**Provider Scoping**
- [ ] `app/providers.tsx`: remove `DiagnosticProvider` from provider chain
- [ ] `app/flux/page.tsx`: wrap content in `<DiagnosticProvider>` locally
- [ ] `app/recon/page.tsx`: wrap content in `<DiagnosticProvider>` locally
- [ ] Verify `DiagnosticContext` imports still resolve in both pages
- [ ] Verify no other pages consume `useDiagnostic()` — confirmed: only flux + recon

**Fetch Migration (8 files → apiClient)**
- [ ] `multi-period/page.tsx` — direct `fetch()` → `apiPost()` with FormData
- [ ] `contact/page.tsx` — direct `fetch()` → `apiPost()` (public, no auth)
- [ ] `FinancialStatementsPreview.tsx` — direct `fetch()` → `apiPost()`
- [ ] `DownloadReportButton.tsx` — direct `fetch()` → `apiDownload()`
- [ ] `SamplingPanel.tsx` — 2 direct `fetch()` calls → `apiPost()`/`apiGet()`
- [ ] `GuestMarketingView.tsx` — direct `fetch()` → `apiGet()`
- [ ] `status/page.tsx` — direct `fetch()` → `apiGet()` (public health check)
- [ ] Verify CSRF tokens still injected correctly after migration
- [ ] NOT migrating: `AuthContext.tsx` (intentionally bypasses apiClient), `useAuditUpload.ts` (FormData + engagement_id injection), `useTrialBalanceAudit.ts` (FormData), `BatchUploadContext.tsx` (batch FormData)

**Route Boundaries**
- [ ] `engagements/loading.tsx` — skeleton: engagement cards grid, workspace header, disclaimer banner
- [ ] `engagements/error.tsx` — "Workspace Error" message, retry button, light-theme
- [ ] `portfolio/loading.tsx` — skeleton: client cards grid, search bar
- [ ] `portfolio/error.tsx` — "Failed to load clients" message, retry button
- [ ] `settings/loading.tsx` — skeleton: form fields, save button (covers both profile + practice)
- [ ] `settings/error.tsx` — "Settings Error" message, retry button
- [ ] All boundaries use Oat & Obsidian semantic tokens

**Verification**
- [ ] `npm run build` — passes
- [ ] flux + recon pages still access DiagnosticContext correctly
- [ ] All migrated fetch calls still work (CSRF, auth, retry)
- [ ] Engagements/portfolio/settings show skeleton on slow load
- [ ] Error boundaries render on forced errors

---

### Sprint 209 — Skeleton UI Components + Phase XXVII Wrap — PLANNED

> **Complexity:** 4/10
> **Goal:** Create shared skeleton components for consistent loading states. Replace inline spinner patterns with proper skeletons. Run full regression.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create shared skeleton components (`CardSkeleton`, `TableSkeleton`, `FormSkeleton`) | LOW | PENDING |
| 2 | Update existing `loading.tsx` files to use shared skeletons | LOW | PENDING |
| 3 | Add `loading.tsx` to remaining authenticated routes (flux, history, recon, status) | LOW | PENDING |
| 4 | Full regression — `npm run build` + `pytest` + manual smoke tests | HIGH | PENDING |
| 5 | Archive Phase XXVII details | LOW | PENDING |

#### Checklist

**Shared Skeleton Components**
- [ ] `components/shared/skeletons/CardSkeleton.tsx` — configurable card grid placeholder (count prop)
- [ ] `components/shared/skeletons/TableSkeleton.tsx` — table rows placeholder (rows/columns props)
- [ ] `components/shared/skeletons/FormSkeleton.tsx` — form fields placeholder (fields prop)
- [ ] All use `animate-pulse` + Oat & Obsidian tokens (`bg-oatmeal-200`, `bg-surface-card`)
- [ ] Export from `components/shared/skeletons/index.ts`

**Update Existing loading.tsx Files**
- [ ] `tools/loading.tsx` — use shared skeletons
- [ ] `engagements/loading.tsx` — use `CardSkeleton`
- [ ] `portfolio/loading.tsx` — use `CardSkeleton`
- [ ] `settings/loading.tsx` — use `FormSkeleton`

**Additional Route Boundaries**
- [ ] `flux/loading.tsx` — dual file upload skeleton
- [ ] `history/loading.tsx` — table skeleton
- [ ] `recon/loading.tsx` — upload + results skeleton
- [ ] `status/loading.tsx` — status cards skeleton

**Regression**
- [ ] `npm run build` — passes with 0 errors
- [ ] `pytest` — all tests pass, 0 regressions
- [ ] Manual smoke: navigate all routes, verify loading states appear on slow network
- [ ] Manual smoke: verify no duplicate nav/footer/toolnav on any page
- [ ] Manual smoke: verify auth redirects work from tools and authenticated routes
- [ ] Verify all internal links resolve correctly after route group restructure

**Documentation**
- [ ] Archive Phase XXVII details to `tasks/archive/phase-xxvii-details.md`
- [ ] Update CLAUDE.md Phase XXVII summary
- [ ] Update version if warranted

#### Review — Sprint 209
*(To be filled on completion)*
