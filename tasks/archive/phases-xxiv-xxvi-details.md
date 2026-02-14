# Phases XXIV–XXVI — Detailed Checklists (Sprints 195–203) — COMPLETE

> Archived from `tasks/todo.md` during Phase XXVIII planning.

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
