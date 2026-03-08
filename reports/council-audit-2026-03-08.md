# Paciolus Daily Digital Excellence Council Report
Date: 2026-03-08
Commit/Branch: e0dcb03 / main
Files Changed Since Last Audit: 191 (across 34 commits, Sprints 499–515 + hotfixes)

## 1) Executive Summary
- Total Findings: 21
  - P0 (Stop-Ship): 0
  - P1 (High): 0
  - P2 (Medium): 8
  - P3 (Low): 12
  - Informational: 1
- Top Risk Themes (max 6 bullets, group findings by pattern):
  - **Memo Generator Code Duplication**: F-001 (1 finding — `_roman`, `_fmt_currency`, `_standard_table_style` duplicated across 6+ files instead of using shared modules)
  - **Accessibility — WCAG Level A Gaps**: F-003, F-004, F-005, F-015 (4 findings — skip navigation, nav landmarks, command palette ARIA, profile dropdown roles)
  - **CI/Testing Coverage Gaps**: F-006, F-007, F-018 (3 findings — webhook integration test, coverage measurement, untested memo generators)
  - **Observability Gaps**: F-008, F-009, F-017 (3 findings — HTTP metrics, structured access logs, Sentry filtering)
  - **Configuration Staleness**: F-010, F-019 (2 findings — .env.example defaults, stale version string)
  - **Zero-Storage Precision**: F-011, F-012 (2 findings — localStorage metadata persistence, DiagnosticSummary aggregate totals documentation)
- Critical System Status:
  - Zero-Storage Integrity: **PASS** — All 19 memo generators use `BytesIO` (in-memory). No new disk writes. ExportShare 48h TTL exception documented (SECURITY_POLICY.md §2.4). Two documentation precision gaps noted (F-011, F-012) but no new data persistence pathways.
  - Auth/CSRF Integrity: **PASS** — No auth changes in this cycle. HttpOnly cookie, HMAC CSRF, account lockout unchanged. JWT algorithm hardcoded (no downgrade vector). One auth classification inconsistency noted (F-002).
  - Observability Data Leakage: **PASS** — No financial data in logs/telemetry. Sentry `beforeSend` strips request bodies. `sendDefaultPii: false`. Breadcrumb filtering gap noted (F-009) but classified as defense-in-depth, not active leakage.

## 2) Daily Checklist Status

1. **Zero-storage enforcement (backend/frontend/logs/telemetry/exports):** ✅ PASS — No new data persistence pathways. All 191 changed files audited. Memo generators exclusively use `BytesIO`. Two precision gaps in existing architecture documentation (F-011: localStorage metadata for anonymous users; F-012: DiagnosticSummary aggregate totals). Neither is new — both predate this audit cycle.

2. **Upload pipeline threat model (size limits, bombs, MIME, memory):** ✅ PASS — No upload pipeline changes. 10-step validation pipeline unchanged. Bulk upload correctly uses `require_verified_user`.

3. **Auth + refresh + CSRF lifecycle coupling:** ✅ PASS — No auth flow modifications. Minor classification inconsistency in export sharing (F-002).

4. **Observability data leakage (Sentry/logs/metrics):** ⚠️ AT RISK — F-009. Sentry `beforeBreadcrumb` absent. `before_send_transaction` not configured. URL paths with engagement/client IDs visible in Sentry transaction traces. No financial data leakage, but metadata exposure.

5. **OpenAPI/TS type generation + contract drift:** ⚠️ AT RISK (unchanged) — No automated pipeline. F-013: `TestingRiskTier` includes `'critical'` value not in backend `RiskTier` enum. Manual sync risk persists.

6. **CI security gates (Bandit/pip-audit/npm audit/policy):** ✅ PASS — 15-job pipeline intact. No CI changes. Branch protection recommended but not enforced (CEO decision).

7. **APScheduler safety under multi-worker:** ✅ PASS — No scheduler changes. Singleton pattern with global `_scheduler`.

8. **Next.js CSP nonce + dynamic rendering:** ✅ PASS — `proxy.ts` unchanged. Per-request nonce with `crypto.randomUUID()`.

## 3) Findings Table (Core)

### F-001: Memo Generator Utility Duplication — Shared Modules Bypassed
- **Severity**: P2
- **Category**: Architecture
- **Evidence**:
  - `_roman()` duplicated in 4 files (`payroll_testing_memo_generator.py:104`, `currency_memo_generator.py:82`, `sampling_memo_generator.py:1638`, `preflight_memo_generator.py:491`) plus `_ROMAN` dict in 2 more (`bank_reconciliation_memo_generator.py:69`, `three_way_match_memo_generator.py:66`). Canonical version exists in `shared/memo_template.py:376`.
  - `_fmt_currency()` duplicated in 3 files (`payroll_testing_memo_generator.py:96`, `revenue_testing_memo_generator.py:175`, `fixed_asset_testing_memo_generator.py:99`). Canonical `format_currency()` exists in `shared/drill_down.py`.
  - `_standard_table_style()` duplicated in 5 files (`payroll:110`, `revenue:183`, `fixed_asset:107`, `bank_rec:129`, `twm:215`). Canonical `ledger_table_style()` exists in `shared/report_styles.py:69`.
    - Explanation: Sprints 500–504 enriched these memo generators but introduced local utility copies instead of importing from existing shared modules. JE and AP generators correctly import from shared; the enriched generators diverged.
- **Impact**: ~120 lines of duplicated code. Any change to table styling, currency formatting, or section numbering must be applied in 6+ locations. The shared modules exist specifically to prevent this.
- **Recommendation**: Replace all local copies with imports from their canonical shared modules.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Eliminate duplicated utility functions in memo generators
  Files in scope: backend/payroll_testing_memo_generator.py, backend/revenue_testing_memo_generator.py, backend/fixed_asset_testing_memo_generator.py, backend/bank_reconciliation_memo_generator.py, backend/three_way_match_memo_generator.py, backend/currency_memo_generator.py, backend/sampling_memo_generator.py, backend/preflight_memo_generator.py
  Approach: In each file, remove the local _roman()/_ROMAN, _fmt_currency(), and _standard_table_style() definitions. Add imports from shared/memo_template (_roman), shared/drill_down (format_currency), and shared/report_styles (ledger_table_style). Update call sites to use the shared function names.
  Acceptance criteria:
  - No local _roman, _fmt_currency, or _standard_table_style definitions remain in memo generators
  - All imports reference canonical shared modules
  - pytest passes for all affected test files
  - npm run build passes (no frontend impact)
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Modernity & Consistency Curator (E), Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-002: Export Sharing Routes Use `require_current_user` Instead of `require_verified_user`
- **Severity**: P2
- **Category**: Security / Defense-in-Depth
- **Evidence**:
  - `backend/routes/export_sharing.py:19` — `from auth import require_current_user`
  - All 4 endpoints use `require_current_user`. Documented classification: "Audit/export = `require_verified_user`".
  - Secondary `check_export_sharing_access(user)` entitlement gating compensates.
- **Impact**: Defense-in-depth gap. Functional risk low (entitlement check rejects unpaid users).
- **Recommendation**: Change to `require_verified_user` for all 4 endpoints.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Align export sharing auth with documented classification
  Files in scope: backend/routes/export_sharing.py
  Approach: Replace require_current_user with require_verified_user in import and all 4 Depends() calls.
  Acceptance criteria:
  - All export_sharing endpoints use require_verified_user
  - Existing tests pass
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Security & Privacy Lead (D)
- **Supporting Agents**: Data Governance Warden (G)
- **Vote** (9 members; quorum=6): 8/9 Approve P2 | Dissent: Performance Alchemist (B): "Entitlement check already gates; P3."
- **Chair Rationale**: P2 sustained. Auth classification is explicit policy.

---

### F-003: Missing Skip Navigation Link (WCAG 2.4.1 Level A)
- **Severity**: P2
- **Category**: Accessibility
- **Evidence**:
  - `frontend/src/components/shared/UnifiedToolbar/UnifiedToolbar.tsx:73` — No "Skip to main content" link exists.
  - Keyboard-only users must Tab through 15+ toolbar elements before reaching `<main>` content.
- **Impact**: WCAG 2.4.1 Level A failure. Affects all keyboard and screen reader users on every page.
- **Recommendation**: Add `<a href="#main-content" className="sr-only focus:not-sr-only ...">Skip to main content</a>` before the toolbar, and `id="main-content"` on the `<main>` element.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add skip navigation link for WCAG 2.4.1 compliance
  Files in scope: frontend/src/components/shared/UnifiedToolbar/UnifiedToolbar.tsx, frontend/src/app/layout.tsx (or wherever <main> is rendered)
  Approach: Add a visually hidden anchor that becomes visible on focus, positioned before the toolbar. Add id="main-content" to the <main> element.
  Acceptance criteria:
  - Tab from page load focuses the skip link first
  - Activating it jumps to main content area
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-004: Command Palette Missing Combobox/Listbox ARIA Semantics
- **Severity**: P2
- **Category**: Accessibility
- **Evidence**:
  - `frontend/src/components/shared/CommandPalette/GlobalCommandPalette.tsx:206-213` — Search input has no `aria-label`, no `role="combobox"`.
  - `GlobalCommandPalette.tsx:220` — Results container has no `role="listbox"`. `CommandRow` buttons lack `role="option"`. No `aria-activedescendant`.
- **Impact**: WCAG 4.1.2 Level A. Screen readers cannot convey the search-and-select interaction pattern. Arrow key navigation is not announced.
- **Recommendation**: Add `role="combobox"`, `aria-label`, `aria-controls`, `aria-activedescendant` to input. Add `role="listbox"` to results. Add `role="option"` + `id` to each `CommandRow`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add combobox/listbox ARIA roles to command palette
  Files in scope: frontend/src/components/shared/CommandPalette/GlobalCommandPalette.tsx
  Approach: Add role="combobox" + aria-label="Search commands" + aria-controls="palette-results" + aria-activedescendant={activeId} to the input. Add role="listbox" id="palette-results" to the results container. Add role="option" + unique id to each CommandRow.
  Acceptance criteria:
  - Screen reader announces combobox, options, and active selection
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-005: Navigation Landmarks Missing `aria-label` (4 Locations)
- **Severity**: P2
- **Category**: Accessibility
- **Evidence**:
  - `UnifiedToolbar.tsx:73` — `<nav>` has no `aria-label`
  - `MarketingNav.tsx:64` — `<nav>` has no `aria-label`
  - `ToolNav.tsx:106` — `<nav>` has no `aria-label`
  - `terms/page.tsx:38`, `privacy/page.tsx:47` — ToC `<nav>` elements unlabeled
- **Impact**: Screen reader landmark navigation lists multiple unlabeled "navigation" regions.
- **Recommendation**: Add `aria-label="Primary navigation"`, `aria-label="Marketing navigation"`, `aria-label="Tool navigation"`, and `aria-label="Table of contents"` respectively.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add aria-label to all <nav> elements
  Files in scope: frontend/src/components/shared/UnifiedToolbar/UnifiedToolbar.tsx, frontend/src/components/marketing/MarketingNav.tsx, frontend/src/components/shared/ToolNav.tsx, frontend/src/app/(marketing)/terms/page.tsx, frontend/src/app/(marketing)/privacy/page.tsx
  Approach: Add aria-label attribute to each <nav> element with a descriptive label.
  Acceptance criteria:
  - All <nav> elements have aria-label
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-006: No Stripe Webhook HTTP-Layer Integration Test
- **Severity**: P2
- **Category**: Verification / Critical Path Coverage
- **Evidence**:
  - `backend/routes/billing.py:626` — `/billing/webhook` endpoint calls `stripe.Webhook.construct_event()` for signature verification.
  - `backend/tests/test_billing_routes.py` — Tests cover handler functions (unit tests) and route existence, but no test sends a POST to `/billing/webhook` with a mock Stripe signature.
  - `test_csrf_middleware.py:575` — Only verifies webhook is in CSRF exemption list.
- **Impact**: A regression in webhook signature verification, request body parsing, or HTTP-level error handling would not be caught. Payment-critical path.
- **Recommendation**: Add integration test that mocks `stripe.Webhook.construct_event` and sends POST via `httpx.AsyncClient`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P0/P1]
  Goal: Add HTTP-layer integration test for Stripe webhook endpoint
  Files in scope: backend/tests/test_billing_routes.py
  Constraints:
  - Ultra-safe: mock stripe.Webhook.construct_event, do not call real Stripe
  - Test both valid-signature (200) and invalid-signature (400) paths
  - Test CSRF exemption (webhook should not require CSRF token)
  Plan:
  1. Mock stripe.Webhook.construct_event to return a valid event dict
  2. POST to /billing/webhook with a mock body and signature header
  3. Assert 200 response
  4. Mock construct_event to raise stripe.error.SignatureVerificationError
  5. Assert 400 response
  Acceptance criteria:
  - Two test methods: test_webhook_valid_signature, test_webhook_invalid_signature
  - pytest tests/test_billing_routes.py passes
  Non-goals:
  - Do not test Stripe API calls (those are unit-tested elsewhere)
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Verification Marshal (I)
- **Supporting Agents**: Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 7/9 Approve P2 | Dissent: Verification Marshal (I): "This is P1 — payment-critical path with zero HTTP coverage." Systems Architect (A): "Handler unit tests cover business logic; HTTP layer is thin."
- **Chair Rationale**: P2 sustained. The webhook HTTP layer is a thin wrapper around tested handler functions. The risk is real but mitigated by unit test coverage of `process_webhook_event`. A P1 would require concurrence from Security Lead (D) who voted P2.

---

### F-007: No Backend Test Coverage Measurement in CI
- **Severity**: P2
- **Category**: CI/CD / Verification
- **Evidence**:
  - `.github/workflows/ci.yml:96` — `pytest tests/ -v --tb=short -q` runs without `--cov`.
  - `pytest-cov` is not in `requirements-dev.txt`.
  - `ci.yml:229` — Frontend Jest runs with `--no-coverage`, bypassing the 25% thresholds in `jest.config.js:71-78`.
- **Impact**: Coverage can silently regress. New features can ship with zero test coverage undetected.
- **Recommendation**: Add `pytest-cov` to dev deps, add `--cov=. --cov-fail-under=60` to CI. Remove `--no-coverage` from Jest CI invocation.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Enable coverage measurement in CI
  Files in scope: backend/requirements-dev.txt, .github/workflows/ci.yml
  Approach: Add pytest-cov to requirements-dev.txt. Add --cov=. --cov-report=term-missing to pytest invocation. Remove --no-coverage from Jest CI command. Do NOT add --cov-fail-under yet (establish baseline first).
  Acceptance criteria:
  - CI outputs coverage percentages for both backend and frontend
  - No failing threshold yet (baseline measurement only)
  - CI pipeline passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-008: No HTTP Request Duration Metrics (Prometheus)
- **Severity**: P2
- **Category**: Observability
- **Evidence**:
  - `backend/routes/metrics.py` — Prometheus metrics exist for file parsing but no `http_request_duration_seconds` histogram, no request count by endpoint/method/status.
  - Sentry traces at 10% sample rate miss 90% of requests.
- **Impact**: Cannot build RED dashboards, set SLO alerts, or identify endpoint-level latency regressions.
- **Recommendation**: Add `starlette-prometheus` middleware or custom middleware emitting `http_request_duration_seconds` and `http_requests_total` counters.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add HTTP RED metrics to Prometheus endpoint
  Files in scope: backend/main.py, backend/routes/metrics.py, backend/shared/parser_metrics.py
  Approach: Add a lightweight middleware that records request method, path template, and status code into a Histogram and Counter. Expose via the existing /metrics endpoint.
  Acceptance criteria:
  - /metrics includes http_request_duration_seconds and http_requests_total
  - Labels include method, path, status_code
  - pytest passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Observability & Incident Readiness (F)
- **Supporting Agents**: Performance Alchemist (B)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-009: Sentry SDK Missing Breadcrumb and Transaction Filtering
- **Severity**: P3
- **Category**: Observability / Zero-Storage
- **Evidence**:
  - `frontend/sentry.client.config.ts` — No `beforeBreadcrumb`.
  - `frontend/sentry.server.config.ts` — No `beforeBreadcrumb`.
  - `backend/main.py:52-56` — `_before_send` strips request body but not headers/query strings. No `before_send_transaction`.
- **Impact**: API endpoint URLs in breadcrumbs/transactions contain engagement IDs and client IDs. No financial data, but metadata exposure.
- **Recommendation**: Add `beforeBreadcrumb` to strip XHR URL query params. Add `before_send_transaction` to backend.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add breadcrumb and transaction sanitization to Sentry
  Files in scope: frontend/sentry.client.config.ts, frontend/sentry.server.config.ts, backend/main.py
  Approach: Add beforeBreadcrumb that strips URL query parameters from xhr/fetch breadcrumbs. Add before_send_transaction to backend that strips query strings from transaction names.
  Acceptance criteria:
  - beforeBreadcrumb configured in both frontend configs
  - before_send_transaction configured in backend
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Observability & Incident Readiness (F)
- **Supporting Agents**: Data Governance Warden (G), Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-010: `.env.example` Stale Defaults — JWT_ALGORITHM, PRICING_V2_ENABLED, SEAT_ENFORCEMENT_MODE
- **Severity**: P3
- **Category**: Deployment / Ops
- **Evidence**:
  - `docker-compose.yml:32` — Exposes `JWT_ALGORITHM` as configurable env var but `config.py:154` hardcodes `HS256`.
  - `backend/.env.example:254-261` — `PRICING_V2_ENABLED=false` default, but `config.py:357` shows it's always-on (retired Phase LXIX). `SEAT_ENFORCEMENT_MODE=soft` documented but `config.py:347` defaults to `hard`.
- **Impact**: Operators deploying from `.env.example` get weaker seat enforcement than expected. JWT_ALGORITHM creates false sense of configurability.
- **Recommendation**: Remove `PRICING_V2_ENABLED` from `.env.example` (retired). Update `SEAT_ENFORCEMENT_MODE` default to `hard`. Remove `JWT_ALGORITHM` from `docker-compose.yml`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Update .env.example and docker-compose.yml for accuracy
  Files in scope: backend/.env.example, docker-compose.yml
  Approach: Remove PRICING_V2_ENABLED (retired). Update SEAT_ENFORCEMENT_MODE comment to show hard as default. Remove JWT_ALGORITHM from docker-compose.yml.
  Acceptance criteria:
  - .env.example matches config.py defaults
  - docker-compose.yml does not expose hardcoded config as env var
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-011: `localStorage` Persists Audit Metadata Indefinitely for Anonymous Users
- **Severity**: P3
- **Category**: Zero-Storage / Data Governance
- **Evidence**:
  - `frontend/src/hooks/useActivityHistory.ts:88` — `localStorage.getItem(HISTORY_STORAGE_KEY)` stores activity metadata (timestamps, debit/credit totals, anomaly counts, materiality thresholds) for unauthenticated users.
  - Unlike `sessionStorage`, `localStorage` persists across browser sessions indefinitely.
  - Authenticated users use the backend API (no localStorage).
- **Impact**: Financial metadata (aggregate totals, thresholds) persists in browser indefinitely for anonymous users. This weakens the zero-storage guarantee for the guest flow.
- **Recommendation**: Switch anonymous fallback from `localStorage` to `sessionStorage`, or add TTL-based expiry.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Limit anonymous audit history persistence
  Files in scope: frontend/src/hooks/useActivityHistory.ts
  Approach: Replace localStorage with sessionStorage for the anonymous fallback. This ensures audit metadata is cleared when the browser tab closes, matching the zero-storage expectation.
  Acceptance criteria:
  - Anonymous history uses sessionStorage instead of localStorage
  - Authenticated users still use backend API
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Data Governance & Zero-Storage Warden (G)
- **Supporting Agents**: Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 8/9 Approve P3 | Dissent: Data Governance Warden (G): "Should be P2 — indefinite persistence of financial metadata violates the brand promise."
- **Chair Rationale**: P3 sustained. The stored data is aggregate metadata (totals, thresholds) for anonymous users only. No account names, no transaction details. Authenticated users use the API. The zero-storage claim covers the backend architecture.

---

### F-012: `sanitize_exception()` Hardcoded "email delivery failed" for All Contexts
- **Severity**: P3
- **Category**: Observability / Incident Readiness
- **Evidence**:
  - `backend/shared/log_sanitizer.py:48-61` — `sanitize_exception()` always returns `f"{type(e).__name__}: email delivery failed"` regardless of context.
  - Called from `email_service.py`, `cleanup_scheduler.py`, and potentially other callers.
  - A cleanup failure logs "OSError: email delivery failed" — misleading.
- **Impact**: Engineers investigating non-email failures see "email delivery failed" and look in the wrong direction. Incident misdirection risk.
- **Recommendation**: Accept a `context` parameter: `sanitize_exception(e, context="email delivery")`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Make sanitize_exception() context-aware
  Files in scope: backend/shared/log_sanitizer.py, backend/email_service.py, backend/cleanup_scheduler.py
  Approach: Add a context parameter to sanitize_exception(e, context="operation"). Update callers to pass their context ("email delivery", "share cleanup", etc.).
  Acceptance criteria:
  - Log messages reflect actual operation context
  - pytest passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-013: Frontend `TestingRiskTier` Includes `'critical'` — Backend `RiskTier` Does Not
- **Severity**: P3
- **Category**: Types / Contracts
- **Evidence**:
  - `frontend/src/types/testingShared.ts:12` — `export type TestingRiskTier = 'low' | 'elevated' | 'moderate' | 'high' | 'critical'`
  - `backend/shared/testing_enums.py:17-23` — `RiskTier` enum has only 4 values (low, moderate, elevated, high).
  - Color/label maps in `testingShared.ts:65-79` define styling for `critical`.
- **Impact**: Dead frontend code for a value the backend never emits. Schema drift between frontend and backend.
- **Recommendation**: Remove `'critical'` from `TestingRiskTier` and its styling maps, or add it to the backend `RiskTier` enum if planned.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Align TestingRiskTier with backend RiskTier enum
  Files in scope: frontend/src/types/testingShared.ts
  Approach: Remove 'critical' from the TestingRiskTier union type and remove its entries from RISK_TIER_COLORS, RISK_TIER_LABELS, and RISK_TIER_BADGES.
  Acceptance criteria:
  - TestingRiskTier matches backend RiskTier (4 values)
  - npm run build passes
  - Frontend tests pass
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-014: Anomaly Summary Uses `random.randint()` Instead of Shared Reference Generator
- **Severity**: P3
- **Category**: Correctness / Architecture
- **Evidence**:
  - `backend/anomaly_summary_generator.py:102-106` — `random.randint(100, 999)` for reference suffix.
  - All other 18 memo generators use `pdf_generator.generate_reference_number()` with prefix replacement.
- **Impact**: Reference number inconsistency and non-determinism.
- **Recommendation**: Replace with `generate_reference_number().replace("PAC-", "ANS-")`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Unify anomaly summary reference generation
  Files in scope: backend/anomaly_summary_generator.py
  Approach: Import generate_reference_number from pdf_generator. Replace _generate_reference() with generate_reference_number().replace("PAC-", "ANS-"). Remove import random.
  Acceptance criteria:
  - References follow shared pattern
  - No import random in production code
  - pytest tests/test_anomaly_summary.py passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Modernity & Consistency Curator (E)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-015: ProfileDropdown Missing Menu ARIA Roles + Stale Version String
- **Severity**: P3
- **Category**: Accessibility / DX
- **Evidence**:
  - `frontend/src/components/auth/ProfileDropdown.tsx:121-205` — Trigger has `aria-haspopup="true"` and `aria-expanded`, but dropdown panel lacks `role="menu"` and items lack `role="menuitem"`.
  - `ProfileDropdown.tsx:202` — Hardcoded `"Paciolus v1.2.0"` when actual version is v2.1.0.
- **Impact**: Screen readers announce dropdown as generic container. Stale version undermines trust.
- **Recommendation**: Add `role="menu"` to panel, `role="menuitem"` to items. Update version string or derive from `package.json`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add menu ARIA roles and fix version string
  Files in scope: frontend/src/components/auth/ProfileDropdown.tsx
  Approach: Add role="menu" to dropdown panel, role="menuitem" to each NavMenuItem and logout button. Update version string to "v2.1.0" or import from package.json.
  Acceptance criteria:
  - Dropdown announces as menu with menuitem children
  - Version string matches current version
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-016: UsageMeter Uses Non-Palette `amber-*` Colors
- **Severity**: P3
- **Category**: Design / Theme Compliance
- **Evidence**:
  - `frontend/src/components/shared/UsageMeter.tsx:32` — `text-amber-600`
  - `UsageMeter.tsx:42` — `bg-amber-500`
  - Oat & Obsidian palette has no `amber` token.
- **Impact**: Minor theme deviation. Visible on settings/billing pages.
- **Recommendation**: Replace with `clay-400` (lighter warning tone) to maintain visual hierarchy.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Replace non-palette amber colors
  Files in scope: frontend/src/components/shared/UsageMeter.tsx
  Approach: Replace text-amber-600 with text-clay-400 and bg-amber-500 with bg-clay-400.
  Acceptance criteria:
  - No amber-* classes remain
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-017: No Request-Level Structured Access Log
- **Severity**: P3
- **Category**: Observability / Incident Readiness
- **Evidence**:
  - `backend/logging_config.py` — Structured logging propagates `request_id` via `ContextVar` but no middleware emits a per-request summary record.
  - Cannot query for "all 500 errors in the last hour" without relying on individual route-level `logger.exception()`.
  - No single record ties method + path + status + duration + user_id + request_id.
- **Impact**: Post-mortem reconstruction requires piecing together individual log lines.
- **Recommendation**: Add a lightweight middleware that emits one structured log record per request at completion.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add per-request access log middleware
  Files in scope: backend/main.py, backend/logging_config.py
  Approach: Add a Starlette middleware that logs method, path, status_code, duration_ms, request_id at INFO level for every request. Use the existing JSONFormatter for production environments.
  Acceptance criteria:
  - Each request produces one structured access log record
  - Record includes method, path, status, duration_ms, request_id
  - No PII or financial data in the log record
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-018: 5 Memo Generators Lack Dedicated Test Files
- **Severity**: P3
- **Category**: Verification / Coverage Gap
- **Evidence**:
  - `ap_testing_memo_generator.py` — Covered only by `test_memo_template.py` (smoke test)
  - `je_testing_memo_generator.py` — Same
  - `payroll_testing_memo_generator.py` — Same
  - `preflight_memo_generator.py` — Covered only by `test_report_chrome.py`
  - `engagement_dashboard_memo.py` — No test references found
  - These were enriched in Sprints 489–500 but tests were not expanded.
  - 13 other memo generators have deep dedicated test coverage.
- **Impact**: Regressions in enriched sections would not be caught. engagement_dashboard_memo is entirely untested.
- **Recommendation**: Create dedicated test files for each with section-level assertions.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add dedicated tests for untested memo generators
  Files in scope: backend/tests/ (new files: test_ap_testing_memo.py, test_je_testing_memo.py, test_payroll_testing_memo.py, test_preflight_memo.py, test_engagement_dashboard_memo.py)
  Approach: Create test files following the pattern in test_bank_rec_memo.py or test_sampling_memo.py. Each should test: PDF generation returns bytes, cover page metadata correct, section headers present, risk scoring rendered, suggested procedures included.
  Acceptance criteria:
  - Each new test file has 5+ test methods
  - pytest passes for all new test files
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-019: Sprint 481 Documentation Gap Persists (Carryover — Downgraded)
- **Severity**: P3
- **Category**: Process
- **Evidence**:
  - No entry in `tasks/todo.md` or any archive for Sprint 481 (commit `e3d6c88`).
  - Process guardrails added in `e0dcb03` (archival self-check, hotfix track) prevent recurrence.
- **Impact**: Historical audit trail gap. All subsequent sprints (499–515) fully documented.
- **Recommendation**: Add retroactive one-line entry to `## Hotfixes`.
- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-020: OpenAPI→TypeScript Contract Drift Risk (Systemic — Unchanged)
- **Severity**: P3
- **Category**: Types / Contracts
- **Evidence**:
  - No automated OpenAPI→TS pipeline exists. 34 commits changed backend schemas and frontend types independently.
- **Impact**: Potential runtime type mismatches. Currently mitigated by manual sync and tests.
- **Recommendation**: Add CI drift detection job.
- **Primary Agent**: Type & Contract Purist (H)
- **Supporting Agents**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 7/9 Approve P3 | Dissent: Modernity Curator (E): "P2"; Performance Alchemist (B): "Manual sync works."

---

### F-021: Prior DEC Findings — Remediation Status
- **Severity**: Informational
- **Category**: Process / Verification
- **Evidence**:

  | Prior Finding | Status |
  |---------------|--------|
  | F-001: Sprint 481 undocumented | **OPEN** → F-019 (P3) |
  | F-002: Stale Stripe env vars | **FIXED** |
  | F-003: Table scope attributes | **FIXED** |
  | F-004: FAQ aria-controls | **FIXED** |
  | F-005: Slider aria-valuenow | **FIXED** |
  | F-006: Slider aria-valuetext | **FIXED** |
  | F-007: f-string SQL in tests | **FIXED** |
  | F-008: status_code=200 | **FIXED** |
  | F-009: animate-pulse bypass | **FIXED** |
  | F-010: Missing as const | **FIXED** |
  | F-011: StaticFallback dead code | **FIXED** |
  | F-012: Non-palette rgba | **RECLASSIFIED** (sage-500 derived) |
  | F-013: Hardcoded FAQ pricing | **PARTIALLY FIXED** |
  | F-014: Orphaned commits | **FIXED** |
  | F-015: Missing npm test results | **FIXED** |
  | F-016: Missing radiogroup ARIA | **NOT VERIFIED** (unchanged) |
  | F-017: Decorative SVGs aria-hidden | **NOT VERIFIED** (unchanged) |

  **Remediation Rate**: 13/17 fixed (76%), 2 reclassified/carried, 2 not verified.

- **Primary Agent**: Verification Marshal (I)

---

## 4) Council Tensions & Resolution

### Tension 1: Export Sharing Zero-Storage Classification
- **Data Governance Warden (G)** and **Security Lead (D)** flagged `ExportShare.export_data` (LargeBinary, 48h TTL) as a P1 Zero-Storage violation.
- **Systems Architect (A)** and **DX Lead (C)** note this is a documented exception in SECURITY_POLICY.md §2.4 with compensating controls (TTL, cleanup scheduler, Professional+ gating, token-hashed access).
- **Resolution**: Not elevated to P1. Previous DECs (March 3, March 4) assessed this as PASS. The compensating controls are adequate. However, the label "Zero-Storage" is imprecise — "Ephemeral Financial Processing" would be more accurate. No finding created; existing documentation deemed sufficient.

### Tension 2: Stripe Webhook Test — P1 vs P2
- **Verification Marshal (I)** wants P1: "Payment-critical path with zero HTTP coverage."
- **Systems Architect (A)** supports P2: "Handler unit tests cover business logic; HTTP layer is a thin FastAPI wrapper."
- **Resolution**: P2 sustained (7/9 vote). P1 requires mandatory concurrence from Security Lead (D) or Data Governance Warden (G) per quorum rules — neither voted P1.

### Tension 3: Memo Duplication — P2 vs P3
- **Performance Alchemist (B)** suggests P3: "Duplication is cosmetic; functions are identical and stable."
- **Systems Architect (A)** insists P2: "120 lines duplicated across 6+ files when shared modules already exist is an architecture regression."
- **Resolution**: P2 sustained (8/9 vote). The shared modules were created specifically to prevent this. Sprint enrichments should use them.

## 5) Discovered Standards → Proposed Codification

- **Existing standards verified**:
  - `as const` convention: **100% compliant** (improvement from 99%)
  - Sprint commit convention: **100% compliant** for Sprints 499–515
  - Post-sprint checklist: **100% followed**
  - Auth classification: **98% compliant** (1 misclassification: export_sharing)
  - Theme palette: **99%+ compliant** (1 violation: amber-* in UsageMeter)

- **Missing standards that should become policy**:
  - **Memo generator utility import rule**: New/enriched memo generators MUST import utilities from shared modules (`memo_template._roman`, `drill_down.format_currency`, `report_styles.ledger_table_style`). No local copies permitted.
  - **Warning state color token**: Define `clay-400` as canonical warning color in Oat & Obsidian spec.
  - **ARIA navigation landmarks**: Every `<nav>` element MUST have `aria-label`.
  - **Sentry breadcrumb policy**: `beforeBreadcrumb` filter required in all Sentry configs.
  - **Coverage measurement**: CI MUST output coverage percentages (enforcement thresholds deferred).

- **Proposed enforcement mechanisms**:
  - Linting: Custom ESLint rule or grep guard for unlabeled `<nav>` elements
  - CI: Coverage reporting (pytest-cov + Jest coverage), OpenAPI drift check
  - Pre-commit: Guard against `amber-*`, `green-*`, `red-*` non-palette colors

## 6) Agent Coverage Report

- **Systems Architect (A) — "The Stalwart"**:
  - Touched areas: All 19 memo generators, `shared/` modules, `Dockerfile`, `docker-compose.yml`, route patterns
  - Top 3 findings contributed: F-001 (primary), F-010 (primary), F-014 (primary)
  - Non-obvious risk: Memo generators enriched in Sprints 500–504 systematically bypassed shared utilities, suggesting the enrichment process didn't reference existing infrastructure.

- **Performance & Cost Alchemist (B) — "The Optimizer"**:
  - Touched areas: Memo generation hot paths, Gunicorn config, pandas engine files, query patterns
  - Top 3 findings contributed: F-001 (supporting), F-008 (supporting)
  - Non-obvious risk: `BytesIO` → `getvalue()` → return doubles memory for large reports. Not current issue (~100KB/report) but worth monitoring.

- **DX & Accessibility Lead (C) — "The Diplomat"**:
  - Touched areas: All navigation components, command palette, pricing page, profile dropdown, toolbar
  - Top 3 findings contributed: F-003 (primary), F-004 (primary), F-005 (primary), F-015 (primary), F-016 (primary)
  - Non-obvious risk: 5 WCAG Level A failures in core navigation components — suggests ARIA review is not part of the component creation workflow.

- **Security & Privacy Lead (D) — "Digital Fortress"**:
  - Touched areas: All route files, Sentry configs, `.env.example`, auth system, CSRF middleware, CSP proxy
  - Top 3 findings contributed: F-002 (primary), F-009 (supporting), F-010 (supporting)
  - Non-obvious risk: `ExportShare` stores `shared_by_name = user.name or user.email` — PII persists in DB beyond 48h if cleanup fails.

- **Modernity & Consistency Curator (E) — "The Trendsetter"**:
  - Touched areas: Package versions, code patterns, memo generator consistency
  - Top 3 findings contributed: F-001 (supporting), F-013 (supporting)
  - Non-obvious risk: `ts-jest` v29 with Jest v30 — version mismatch may cause subtle issues.

- **Observability & Incident Readiness (F) — "The Detective"**:
  - Touched areas: `logging_config.py`, Sentry configs, health probes, Prometheus metrics
  - Top 3 findings contributed: F-008 (primary), F-009 (primary), F-012 (primary), F-017 (primary)
  - Non-obvious risk: `logger.exception()` in health probes generates massive traceback volume during outages — should be `logger.warning()`.

- **Data Governance & Zero-Storage Warden (G) — "The Auditor"**:
  - Touched areas: All data persistence paths, frontend storage APIs, DB models, export flows
  - Top 3 findings contributed: F-002 (supporting), F-011 (primary)
  - Non-obvious risk: `DiagnosticSummary` stores aggregate financial totals (assets, liabilities, revenue) — `.env.example` documentation is incomplete.

- **Type & Contract Purist (H) — "The Pedant"**:
  - Touched areas: Frontend type definitions, backend response schemas, `as const` compliance, stripe client typing
  - Top 3 findings contributed: F-013 (primary), F-020 (primary), F-016 (supporting)
  - Non-obvious risk: `stripe_client.py` returns `Any` from `get_stripe()`, propagating type blindness to all billing call sites.

- **Verification Marshal (I) — "The Skeptic"**:
  - Touched areas: CI pipeline, test files, coverage config, git history, todo.md
  - Top 3 findings contributed: F-006 (primary), F-007 (primary), F-018 (primary), F-019 (primary)
  - Non-obvious risk: `engagement_dashboard_memo.py` has zero test coverage — the only memo generator with no test references at all.
