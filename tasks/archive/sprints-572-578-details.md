# Sprints 572–578: Password Reset, Decimal Pipeline, Response Schemas, Error Handling, Anomaly Expansion

> Archived from `tasks/todo.md` Active Phase on 2026-03-23.

### Sprint 572: Password Reset Flow
> Source: Launch Readiness Review item B-15 / Deferred NEW-015

#### Backend
- [x] `PasswordResetToken` model (SHA-256 hashed, 1-hour expiry, single-use)
- [x] `POST /auth/forgot-password` — rate-limited, always returns 200 (prevents enumeration)
- [x] `POST /auth/reset-password` — validates token, sets new password, revokes all sessions, clears lockout
- [x] Password reset email template (HTML + plaintext, Oat & Obsidian branding)
- [x] `generate_password_reset_token()` + `send_password_reset_email()` in email_service.py
- [x] CSRF exemption for both endpoints (pre-auth, no CSRF token available)

#### Frontend
- [x] `/forgot-password` page — email form, success screen (always shown to prevent enumeration)
- [x] `/reset-password` page — new password form with complexity validation, token capture + URL stripping
- [x] Login page "Forgot password?" link → `/forgot-password`

#### Tests
- [x] 12 backend tests: forgot-password (4), reset-password (5), CSRF exemption (2), lockout reset (1)
- [x] 10 frontend tests: ForgotPasswordPage (5), ResetPasswordPage (5)
- [x] Updated CSRF exemption snapshot test with 2 new paths

- **Tests:** 7,108 backend (12 new), 1,735 frontend (10 new) — 0 failures
- **Status:** COMPLETE

### Sprint 573: Decimal Pipeline Refactor (AUDIT-06-F001, AUDIT-06-F003)
> Source: AUDIT-06 Findings F001 (float arithmetic in ingestion) and F003 (cross-engine float down-casts)

- [x] streaming_auditor.py: Decimal accumulators (chunks, balances, finalize)
- [x] pipeline.py: Decimal arithmetic for totals and coverage
- [x] ratio_engine.py: CategoryTotals → Decimal, coerce at boundary
- [x] flux_engine.py: Decimal NEAR_ZERO, balance extraction
- [x] population_profile_engine.py: Decimal accumulation
- [x] going_concern_engine.py: Decimal-safe division
- [x] parsing_helpers.py: safe_float() deprecation docstring

- **Tests:** 7,107 backend — 0 failures
- **Status:** COMPLETE

### Sprint 574: Response Schema Reconciliation + Decimal Serialization (AUDIT-06-F002, AUDIT-11-F001, AUDIT-11-F005)

- [x] `MonetaryDecimal` annotated type: Decimal field → float JSON serialization
- [x] Response models: RiskSummaryResponse, TrialBalanceResponse expanded
- [x] Frontend type alignment: RiskSummary, AuditResult canonical imports

- **Tests:** 7,064 backend, 1,735 frontend — 0 failures
- **Status:** COMPLETE

### Sprint 575: Account Identifier Preservation (AUDIT-06-F004)

- [x] `dtype=str` for CSV/Excel readers (preserves leading-zero account codes)
- [x] 9 new tests covering CSV, Excel, StreamingAuditor paths

- **Tests:** 7,073 backend (9 new) — 0 failures
- **Status:** COMPLETE

### Sprint 576: Organization & Untyped Endpoint Response Models (AUDIT-11-F002, AUDIT-11-F003)

- [x] shared/organization_schemas.py: 8 response models
- [x] Route decorators: organization (10), admin_dashboard (3), branding (4), bulk_upload (2), export_sharing (3)

- **Status:** COMPLETE

### Sprint 577: Unified Error Schema & Frontend Error Handling (AUDIT-11-F004)

- [x] ErrorResponse Pydantic model + 3 exception handlers
- [x] Frontend parseErrorResponse() shared parser

- **Tests:** 7,073 backend, 1,735 frontend — 0 failures
- **Status:** COMPLETE

### Sprint 578: Synthetic Anomaly Framework Expansion (AUDIT-06-F005)

- [x] 4 new generators: related_party_activity, revenue_concentration, expense_concentration, balance_sheet_imbalance
- [x] Registry + COVERAGE_MAP updated

- **Tests:** 7,077 backend (4 new) — 0 failures
- **Status:** COMPLETE
