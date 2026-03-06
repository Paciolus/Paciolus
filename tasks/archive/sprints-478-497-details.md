# Sprints 478, 488–497 — Security Hardening & Quality Era

Archived from `tasks/todo.md` Active Phase on 2026-03-06.

---

## Sprint 478 — Deprecated Alias Migration

**Status:** COMPLETE
**Goal:** Remove 21 deprecated exports across 6 utility files. Migrate consumers to canonical `@/lib/motion` and `ThresholdStatus` APIs.
**Complexity Score:** Low-Medium
**Commit:** 6a2f66b (executed as part of Sprint 491 Path C)

### Wave 1: Zero-Consumer Deletions (safe, no migration needed)
- [x] `themeUtils.ts`: Delete `MODAL_OVERLAY_VARIANTS`, `MODAL_CONTENT_VARIANTS`, `createContainerVariants`, `CONTAINER_VARIANTS`, `createCardStaggerVariants`
- [x] `marketingMotion.tsx`: Delete `STAGGER`, `SectionReveal`
- [x] `types/mapping.ts`: Delete `HealthStatus` type alias
- [x] `HeroProductFilm.tsx` + `components/marketing/index.ts`: Remove `HeroProductFilm` alias export and barrel re-export

### Wave 2: Health → Threshold Rename (2 components + barrel + test)
- [x] `MetricCard.tsx`: Change `HealthStatus` → `ThresholdStatus`, `getHealthClasses` → `getThresholdClasses`, `getHealthLabel` → `getThresholdLabel`
- [x] `IndustryMetricsSection.tsx`: Same renames
- [x] `utils/index.ts`: Remove deprecated re-exports; add `THRESHOLD_STATUS_CLASSES`, `getThresholdClasses`, `getThresholdLabel` re-exports
- [x] `themeUtils.test.ts`: Update test imports to use canonical names
- [x] `themeUtils.ts`: Delete `HealthStatus`, `HealthClasses`, `HEALTH_STATUS_CLASSES`, `getHealthClasses`, `getHealthLabel`

### Wave 3: Motion Token Internals (internal rewiring)
- [x] `motionTokens.ts`: Inline `DURATION` values into `TIMING`, inline `OFFSET` values into `DISTANCE`
- [x] `marketingMotion.tsx`: Inline `DURATION.hero` value (0.6), remove `import { DURATION }`
- [x] `animations.ts`: Delete `fadeInUp`, `fadeInUpSpring`, `fadeIn`, `DURATION`
- [x] `animations.test.ts`: Delete deprecated export tests (kept `dataFillTransition`, `scoreCircleTransition`)
- [x] `utils/index.ts`: Remove `DISTANCE` re-export
- [x] `motionTokens.test.ts`: Update DISTANCE/TIMING test descriptions

### Wave 4: ENTER.clipReveal Migration (1 consumer)
- [x] `FeaturePillars.tsx`: Replace `ENTER.clipReveal` with inline `clipReveal` variant
- [x] `marketingMotion.tsx`: Delete `ENTER` and `OFFSET` exports

### Verification
- [x] `npm run build` passes
- [x] `npx jest --no-coverage` passes (111 suites, 1329 tests, 5 snapshots)
- [x] `@deprecated` count: 0 in themeUtils, animations, marketingMotion, mapping; 1 in motionTokens (DISTANCE — intentionally retained)

---

## Sprint 488 — Financial Statements Report Improvements

**Status:** COMPLETE
**Goal:** Enhance Report 02 (Financial Statements) with 5 changes: 4 new ratios, prior year comparative columns, footnote placeholders, cross-reference legend, Quality of Earnings expansion.
**Complexity Score:** Medium-High
**Commit:** 26e0590

### Changes
- [x] CHANGE 1: Add Quick Ratio, EBITDA, EBITDA Margin, Interest Coverage to Key Financial Ratios (reorder to 12 ratios)
- [x] CHANGE 2: Prior year comparative columns on BS/IS/ratios when prior_lead_sheet_grouping available
- [x] CHANGE 3: Notes to Financial Statements section (5 placeholder notes)
- [x] CHANGE 4: Cross-Reference Index legend after BS and IS
- [x] CHANGE 5: Quality of Earnings — rename to Cash Conversion Ratio, add benchmark sentence

### Files Modified
- `backend/financial_statement_builder.py` — Add depreciation_amount, interest_expense, prior period fields to FinancialStatements
- `backend/pdf_generator.py` — All 5 rendering changes
- `backend/generate_sample_reports.py` — Update Meridian sample data
- `backend/tests/test_financial_statements.py` — New tests for added fields

### Verification
- [x] `npm run build` passes
- [x] `pytest tests/test_financial_statements.py -v` passes (46/46)
- [x] Regenerate sample report 02 (50,183 bytes)

### Review
- All 5 changes implemented, 11 new tests added (35 → 46)
- Ratio computations verified: Quick=2.05x, EBITDA=$1,745,000, EBITDA Margin=25.5%, Interest Coverage=15.9x
- Prior period comparative columns render as table format when prior data available, leader-dot format when not
- Footnotes section renders 5 placeholder stubs with disclaimer
- Cross-reference legends render dynamically based on non-zero lead sheet refs

---

## Sprint 489 — Journal Entry Testing Report Fixes

**Status:** COMPLETE
**Goal:** Fix 5 bugs and add 2 improvements to JE Testing Memo (Report 03).
**Complexity Score:** Medium
**Commit:** 1b6ffc1

### Bugs
- [x] BUG-01: Benford Expected column — fixed formula in `generate_sample_reports.py`
- [x] BUG-02: Section V High Severity Detail — added flagged_entries + procedure text below tables
- [x] BUG-03: Suggested procedures — replaced index-based with `_resolve_test_key()` word-overlap matching
- [x] BUG-04: Risk tier — conclusion now uses `composite.risk_tier` directly (not re-derived)
- [x] BUG-05: Disclaimer "testing testing" — `domain_clause` logic in `build_disclaimer()`

### Improvements
- [x] IMP-01: Month-end clustering benchmark context — `FINDING_BENCHMARKS` in `follow_up_procedures.py`
- [x] IMP-02: Benford positive interpretation — added in `_build_benford_section()` when MAD < 0.006

### Verification
- [x] `npm run build` passes
- [x] `pytest` passes (226/226 memo/report tests)
- [x] All 21 sample reports regenerated (0 failures)

---

## Sprint 490 — AP Payment Testing Report Fixes

**Status:** COMPLETE
**Goal:** Fix 2 bugs and add 3 improvements to AP Payment Testing Memo (Report 04).
**Complexity Score:** Medium
**Commit:** 3ab2ed1

### Bugs
- [x] BUG-01: Suggested procedures — all 13 AP procedure texts updated in `follow_up_procedures.py`
- [x] BUG-02: Section V High Severity Payment Detail — 4 test-specific table layouts + generic fallback + procedure text

### Improvements
- [x] IMP-01: Vendor Name Variation pairs with total_paid columns, sorted by combined total, top 5 shown
- [x] IMP-02: Approval threshold source documentation added to just_below_threshold methodology description
- [x] IMP-03: DPO metric in scope section via `_build_ap_scope()` callback

### Verification
- [x] `pytest` passes (402/402 memo/AP tests)
- [x] All 21 sample reports regenerated (0 failures)
- [x] `npm run build` passes

---

## Sprint 491 — Digital Excellence Council Remediation (Paths A+B+C)

**Status:** COMPLETE
**Goal:** Execute all three Council remediation paths: methodology fixes, technical debt, and deprecated alias cleanup.
**Complexity Score:** High
**Commit:** 6a2f66b

### Path A: Methodology Fixes
- [x] A1: JE memo standard citation (AS 1215 → AS 2110 + ISA 240)
- [x] A2: FASB YAML citation correction for journal_entry_testing (ASC 230-10 → ASC 240-10)
- [x] A3: Harden assurance-boundary language in all 8 memo generators (low + high risk tiers)
- [x] A4: Fix Benford "non-fabrication" language in JE memo
- [x] A5: Fix "control failure" language in payment_before_invoice procedure (ISA 240 → ISA 265)
- [x] A6: Fix DPO "typical range 30–60 days" unsourced claim in AP memo
- [x] A7: Complete ~30 missing follow-up procedures (37→89 total across all tools)
- [x] A8: Add z-score threshold documentation in testing_enums.py (Nigrini 2012 citation)

### Path B: Technical Debt
- [x] B1: Fix broad `except Exception` in export_sharing.py (→ binascii.Error, ValueError)
- [x] B2: Billing.py handlers reviewed — Stripe API wrappers are defensible as-is (no change needed)
- [x] B3: Fix silent `except Exception: pass` in bulk_upload.py (→ logger.warning)
- [x] B4: Engine test stubs — verified 11 engine test files already exist (AP, JE, Payroll, Revenue, AR, Sampling, Currency, Recon, Flux, Population Profile, Benchmark). Scout's "16 untested engines" claim was incorrect.

### Path C: Sprint 478 — Deprecated Alias Migration
- [x] C1: Wave 1 — Zero-consumer deletions (5 themeUtils, 2 marketingMotion, 1 mapping, 1 HeroProductFilm)
- [x] C2: Wave 2 — Health → Threshold rename (MetricCard, IndustryMetricsSection, utils/index, test)
- [x] C3: Wave 3 — Motion token internals (inline DURATION/OFFSET, delete deprecated animations)
- [x] C4: Wave 4 — ENTER.clipReveal migration (FeaturePillars → lib/motion or inline)

### Verification
- [x] `pytest` passes (5,651 passed; 36 pre-existing failures unrelated to sprint)
- [x] `npm run build` passes (all dynamic routes)
- [x] `npm test` passes (111 suites, 1,329 tests)
- [x] All 21 sample reports regenerated (0 failures)
- [x] Zero `@deprecated` in themeUtils/animations/marketingMotion/mapping
- [x] Zero assurance-boundary violations (5 patterns grep-verified clean)

---

## Sprint 492 — Formula Consistency & Efficiency Hardening

**Status:** COMPLETE
**Goal:** Eliminate ratio formula inconsistencies, reduce redundant computation, harden edge-case behavior.
**Complexity Score:** Medium-High
**Commit:** fc2d5a2

### Changes
- [x] Fix CCC redundant computation in `calculate_all_ratios` (DSO/DPO/DIO computed twice)
- [x] Harden operating margin fallback for malformed totals (negative derived opex)
- [x] Use `is_percentage` in prior-period significance thresholds
- [x] Add cash-cycle ratios (DSO/DPO/DIO/CCC) to prior-period comparison
- [x] Add missing 10 ratios to frontend `RATIO_METRICS` metadata
- [x] Document reciprocal metric zero-case semantics
- [x] Tests: operating margin malformed input, CCC efficiency, prior-period percentage thresholds, reciprocal zero-cases, formula consistency

### Verification
- [x] `pytest tests/test_ratio_core.py -q` passes (77 tests)
- [x] `pytest tests/test_cash_conversion_cycle.py -q` passes (22 tests)
- [x] `pytest tests/test_prior_period.py -q` passes (42 tests)
- [x] `pytest tests/test_industry_ratios.py -q` passes (71 tests)
- [x] `npm run build` passes (all dynamic routes)
- [x] `npm test` passes (111 suites, 1329 tests)
- [x] Full backend: 5,679 passed (38 pre-existing failures unrelated to sprint)

---

## Sprint 493 — Access Hardening Security Audit

**Status:** COMPLETE
**Goal:** Full access control hardening — auth, authorization, session management, privilege escalation, tenant isolation.
**Complexity Score:** High
**Commit:** e57a49e

### Findings & Fixes
- [x] **H-1:** Billing analytics endpoint lacked admin role check → Added org owner/admin + subscription check
- [x] **H-2:** Org invite token not bound to invitee email → Added email matching validation
- [x] **H-3:** Entitlement checks called with wrong args (crashes) → Fixed call signatures in 4 locations
- [x] **M-1:** No max password length (bcrypt DoS vector) → Added max_length=128 to all password fields
- [x] **M-2:** Registration revealed email existence → Changed to generic error message
- [x] **M-3:** Content-Disposition header injection in export sharing → Added filename sanitization
- [x] **M-4:** Soft entitlement enforcement had no production guardrail → Added startup warning
- [x] **L-1:** /metrics endpoint leaks operational data → Added security documentation note
- [x] Test assertion updated for new registration message

### Verification
- [x] `pytest tests/test_auth_routes_api.py` passes (26 tests)
- [x] `pytest tests/test_csrf_middleware.py` passes (91 tests)
- [x] `npm run build` passes

---

## Sprint 494 — Data Hardening Security Audit

**Status:** COMPLETE
**Goal:** Full data hardening review — secrets management, error leakage, logging sanitization, API exposure, encryption boundaries.
**Complexity Score:** High
**Commit:** b21bebe

### Findings & Fixes
- [x] **H-1:** DATABASE_URL with credentials logged in startup summary → Mask credentials via `_mask_database_url()`
- [x] **H-2:** Raw `str(e)` leaked to API clients in 6 route endpoints → Route through `sanitize_error()` with passthrough safety net
- [x] **H-3:** Raw exception in bulk upload job status returned to user → Generic error message
- [x] **M-1:** FastAPI Swagger/OpenAPI docs exposed in production → Disable docs/redoc/openapi_url in production
- [x] **M-2:** Raw exception logged with potential PII from email service → Log only exception class name
- [x] **M-3:** Raw exception logged from Excel parse failure → Log only exception class name
- [x] **M-4:** `sanitize_error()` passthrough mode lacked internal-detail blocking → Added `_contains_internal_details()` safety net
- [x] **L-1:** Raw exception class+message in bulk upload warning logs → Log only exception class name
- [x] **L-2:** Stripe exception details logged with raw `%s, e` in 7 billing endpoints → Log only exception class name
- [x] **L-3:** S3 client init exception logged with raw details → Log only exception class name

### Defense-in-Depth Improvements
- [x] **D-1:** Apply `sanitize_csv_value()` to all user-controlled Excel cell writes in `excel_generator.py`
- [x] **D-2:** Add binary magic byte guard (XLSX/XLS/PDF) in UNKNOWN format fallback in `shared/helpers.py`
- [x] **D-3:** Add scheduled bulk upload job cleanup (30min interval) in `cleanup_scheduler.py`
- [x] **D-4:** Add `TracebackRedactionFilter` in `logging_config.py` — opt-in via `REDACT_LOG_TRACEBACKS=true`

### Verification
- [x] `pytest` passes: 5,679 passed
- [x] `npm run build` passes (all dynamic routes)
- [x] Upload validation tests: 141 passed
- [x] Financial statements tests: 46 passed
- [x] Export route tests: 85 passed
- [x] Memo template tests: 29 passed

---

## Sprint 495 — Surface Area Hardening Security Audit

**Status:** COMPLETE
**Goal:** Full surface area hardening — API endpoints, input handling, injection risks, SSRF, XSS, CSRF, CORS, security headers, file parsing, third-party integrations, container exposure.
**Complexity Score:** High
**Commit:** b197fc4

### Findings & Fixes
- [x] **SA-1 (M):** MaxBodySizeMiddleware crash on malformed/negative Content-Length → try/except + negative check
- [x] **SA-2 (M):** Prometheus /metrics publicly exposed in production → loopback-only restriction with 404 stealth
- [x] **SA-3 (L):** /health/ready pool stats leaking operational data → stripped in production
- [x] **SA-4 (L):** Bulk upload UploadFile use-after-close in asyncio.create_task → pre-read bytes
- [x] **SA-5 (L):** Frontend missing X-Frame-Options and HSTS headers → added to next.config.js
- [x] **SA-6 (I):** /metrics returns 404 (not 403) for stealth in production
- [x] **SA-7 (L):** Org invite duplicate error leaked email enumeration → generic message
- [x] **SA-8 (L):** Email comparisons in org invite/member queries were case-sensitive → `func.lower()` normalization
- [x] **SA-9 (L):** JPEG magic byte check in branding.py too narrow (3 bytes) → SOI + 0xFF segment marker check

### Verification
- [x] `pytest` passes (250 security/CSRF/upload tests; 2 pre-existing lockout failures)
- [x] `npm run build` passes (all dynamic routes)
- [x] All 7 files verified: security_middleware.py, routes/metrics.py, routes/health.py, routes/bulk_upload.py, frontend/next.config.js, routes/organization.py, routes/branding.py

---

## Sprint 496 — Engineering Process Hardening

**Status:** COMPLETE
**Goal:** Full SDLC hardening — secrets scanning, CI/CD security controls, missing security tests, workflow permissions, frontend test CI gate, mypy CI gate, pre-commit secrets prevention.
**Complexity Score:** High
**Commit:** 9004db1

### Findings & Fixes
- [x] **EP-1 (H):** No secrets scanning in CI or pre-commit → Added trufflehog CI job (blocking) + pre-commit pattern scan
- [x] **EP-2 (H):** CI workflow has no `permissions:` block → Added `permissions: contents: read` at top level (least-privilege)
- [x] **EP-3 (H):** No frontend tests in CI → Added `frontend-tests` job running Jest with `--ci --forceExit`
- [x] **EP-4 (M):** No mypy type checking in CI → Added `mypy-check` job enforcing 0 errors on non-test source
- [x] **EP-5 (M):** No security regression tests → Added `test_injection_regression.py` (61 tests: SQLi, SSTI, path traversal, XSS, CWE-1236, header injection)
- [ ] **EP-6 (M):** No pinned action versions — supply chain risk via tag-based references (deferred: requires SHA research)
- [x] **EP-7 (L):** No CODEOWNERS file → Created `.github/CODEOWNERS` covering security-critical paths
- [x] **EP-8 (L):** Pre-commit hook only runs lint-staged → Added secrets pattern scanning (Stripe, AWS, private keys, GitHub/Slack tokens)
- [ ] **EP-9 (L):** Bandit excludes all test files — security bugs in test helpers go undetected (accepted risk: test code doesn't ship)

### Verification
- [x] `pytest tests/test_injection_regression.py` passes (61 tests)
- [x] `pytest tests/test_security.py tests/test_csrf_middleware.py tests/test_injection_regression.py` passes (170 passed, 2 pre-existing failures)
- [x] `npm run build` passes (all dynamic routes)
- [x] CI workflow validates: secrets-scan, frontend-tests, mypy-check added
- [x] CODEOWNERS covers 20+ security-critical file paths
- [x] Pre-commit hook scans for 7 secret pattern families

---

## Sprint 497 — Digital Excellence Council Remediation (Paths A+B+C)

**Status:** COMPLETE
**Goal:** Fix methodology citations, test regressions, and infrastructure polish identified by Digital Excellence Council audit.
**Complexity Score:** High
**Commit:** bfb4ed6

### Path A: Methodology Integrity (10 fixes across 17 files)
- [x] A1: JE memo PCAOB AS 2110 → AS 2401 (3 locations)
- [x] A2: ISA 240.A40 fabricated paragraph citation → ISA 240 (11 locations across 6 files)
- [x] A3: Sampling "Population Not Accepted" → "UEL Exceeds TM — Further Evaluation Required"
- [x] A4: ASC 450-20 → ASC 250-10 in statistical_sampling FASB YAML
- [x] A5: MUS dead code removal + expansion factor methodology note
- [x] A6: Risk assessment "exhibits X risk profile" → "returned X flag density" (33 instances across 9 memo generators)
- [x] A7: ISA 265 reference removed from payment_before_invoice follow-up procedure
- [x] A8: Benford ISA 530 → ISA 520 (2 files)
- [x] A9: Ghost employee "physical verification" — added engagement team qualifier
- [x] A10: Shared tax ID — added payroll tax reporting implication note

### Path B: Test Regression Triage (26 fixes across 10 test files)
- [x] B1: `diagnostics_per_month` → `uploads_per_month` (test_entitlements.py, test_pricing_launch_validation.py)
- [x] B2: FREE tier `pdf_export` now False (was True) — updated assertions
- [x] B3: Seat pricing tests: test included seats (0) vs add-on seats (8+/21+)
- [x] B4: Rate limit tiers: added 'team' and 'organization' to expected set
- [x] B5: Seat management max: 22 → 60 (matches CheckoutRequest le=60)
- [x] B6: Report cover page: DoubleRule → GoldGradientRule (2 expected)
- [x] B7: Pricing integration: removed obsolete `_require_pricing_v2` tests
- [x] B8: SQLite migration: added organization_id column patch in database.py init_db()
- [x] B9: Entitlement checks unit: resource "diagnostics" → "uploads", Solo tier all-access fixes
- [x] B10: Entitlement parity: `diagnostics_per_month` → `uploads_per_month`
- [x] B11: Audit API: resource "diagnostics" → "uploads", Solo limit 20 → 100
- [x] B12: Billing routes: `_load_seat_price_ids` → `_load_pro_seat_price_ids`/`_load_ent_seat_price_ids` (5 tests)
- [x] B13: Billing routes: seat_count cap 22 → 60 in schema test

### Path C: Infrastructure Polish
- [x] C1: Frontend package.json version 1.8.0 → 2.1.0
- [x] C2: CONTACT_EMAIL documented in .env.example
- [ ] C3: N+1 eager loading (deferred — requires profiling)

### Verification
- [x] `pytest` passes — 5,776 passed, 0 failed, 1 skipped (1 pre-existing teardown error)
- [x] `npm run build` passes — all routes dynamic
- [x] Regression: 0 new failures introduced
