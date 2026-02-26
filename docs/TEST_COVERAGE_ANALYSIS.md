# Test Coverage Analysis — Paciolus

**Date:** 2026-02-26
**Baseline:** ~4,650 backend tests + ~1,190 frontend tests
**Frontend coverage threshold:** 25% (branches/functions/lines/statements)
**Backend coverage threshold:** None enforced

---

## Executive Summary

The codebase has strong test volume but significant structural gaps. **~65 backend source files have no dedicated test file**, including 13 core engines totaling **20,700+ lines** of untested business logic. The frontend has **19 untested hooks**, **6 untested contexts**, **40+ untested tool-specific components**, and **zero E2E tests**. Backend CI runs no coverage measurement at all.

---

## Priority 1: Backend Engine Unit Tests (HIGH IMPACT)

These core engines contain the platform's financial analysis logic. They are currently exercised *only* through route integration tests, meaning edge cases in the computation logic itself are likely untested.

| Engine | Lines | Current Coverage | Risk |
|--------|-------|-----------------|------|
| `je_testing_engine.py` | 2,709 | Route-only (6 refs) | 19-test battery, Benford's Law — logic errors impact audit conclusions |
| `revenue_testing_engine.py` | 2,104 | Route-only (3 refs) | ASC 606/IFRS 15 contract tests — regulatory exposure |
| `ratio_engine.py` | 1,884 | Route-only (6 refs) | 12 core ratios + CCC — numeric precision critical |
| `ar_aging_engine.py` | 1,838 | Route-only (1 ref) | ISA 500/540 receivables — valuation assertions |
| `ap_testing_engine.py` | 1,715 | Route-only (3 refs) | 13-test battery, duplicate detection — fraud indicators |
| `payroll_testing_engine.py` | 1,699 | Route-only (3 refs) | Ghost employee detection — fraud indicators |
| `audit_engine.py` | 1,494 | Route-only (5 refs) | Core TB analysis — foundation of platform |
| `fixed_asset_testing_engine.py` | 1,337 | Route-only (1 ref) | IAS 16/ASC 360 PP&E — depreciation calculations |
| `three_way_match_engine.py` | 1,314 | Route-only (1 ref) | PO→Invoice→Receipt matching — procurement integrity |
| `inventory_testing_engine.py` | 1,278 | Route-only (1 ref) | IAS 2/ASC 330 — slow-moving/obsolescence |
| `financial_statement_builder.py` | 835 | None | Balance Sheet + Income Statement + Cash Flow |
| `preflight_engine.py` | 562 | Route-only (1 ref) | Data quality gateway — blocks downstream analysis |
| `lease_diagnostic_engine.py` | 492 | Route-only (1 ref) | IFRS 16/ASC 842 compliance |
| `going_concern_engine.py` | 468 | Route-only (1 ref) | ISA 570 — mandatory disclaimer logic |
| `expense_category_engine.py` | 337 | Route-only (1 ref) | ISA 520 analytical procedures |
| `cutoff_risk_engine.py` | 338 | Route-only (1 ref) | ISA 501 cutoff assertions |
| `accrual_completeness_engine.py` | 315 | Route-only (1 ref) | Run-rate ratio thresholds |

**Recommendation:** Write dedicated unit tests for each engine, focusing on:
- Boundary conditions (zero rows, single row, max rows)
- Numeric precision (Decimal vs float edge cases, rounding)
- Classification logic branches (pass/fail/skip thresholds)
- Malformed input handling (missing columns, NaN values, mixed types)

---

## Priority 2: Security-Sensitive Code (HIGH IMPACT)

These files handle authentication, authorization, and data protection — yet lack dedicated test files.

| File | Lines | Gap |
|------|-------|-----|
| `security_middleware.py` | 504 | CSRF, CORS, body size limits, security headers — no direct tests |
| `security_utils.py` | 259 | Upload sanitization, dtype preservation — no direct tests |
| `secrets_manager.py` | 200 | Secret rotation, env var fallback — no direct tests |
| `disposable_email.py` | 294 | Blocklist enforcement, email-change gating — no direct tests |
| `auth.py` | 766 | Has route tests (302 lines) but ratio is 2.5:1 source:test — thin |

**Recommendation:** These are security-critical. Each should have focused unit tests covering:
- Middleware bypass attempts (malformed headers, edge-case content types)
- CSRF token validation (missing, expired, replayed)
- Secrets manager fallback behavior (env missing, rotation during request)
- Disposable email edge cases (subdomain variants, new TLDs)

---

## Priority 3: Backend Route Integration Gaps

These route files have **zero** test file references:

| Route File | Responsibility |
|------------|---------------|
| `routes/export_diagnostics.py` | Diagnostic PDF/CSV export |
| `routes/export_memos.py` | Memo PDF generation endpoints |
| `routes/export_testing.py` | Testing tool export endpoints |
| `routes/auth_routes.py` | Login/register/token refresh (has `test_auth_routes_api.py` but it doesn't reference the route file name) |

**Other low-coverage routes** (only general reference, not route-specific tests):
- `routes/adjustments.py` — Adjusting entry CRUD (approval-gated workflow)
- `routes/ap_testing.py` — AP testing trigger endpoint
- `routes/benchmarks.py` — Industry benchmark queries
- `routes/je_testing.py` — JE testing trigger
- `routes/payroll_testing.py` — Payroll testing trigger

**Recommendation:** Add route-level integration tests that verify:
- HTTP status codes for valid/invalid requests
- Authentication/authorization enforcement
- Response schema conformance
- Error responses for missing/invalid parameters
- Rate limit headers present

---

## Priority 4: Frontend Hook Coverage (MEDIUM IMPACT)

19 hooks lack test files. Many of these are tool-specific data-fetching hooks:

| Hook | Responsibility |
|------|---------------|
| `useAPTesting.ts` | AP Testing data fetch + state |
| `useARAging.ts` | AR Aging data fetch + state |
| `useBankReconciliation.ts` | Bank Rec data fetch + state |
| `useFixedAssetTesting.ts` | Fixed Asset data fetch + state |
| `useInventoryTesting.ts` | Inventory data fetch + state |
| `useJETesting.ts` | JE Testing data fetch + state |
| `usePayrollTesting.ts` | Payroll data fetch + state |
| `useRevenueTesting.ts` | Revenue Testing data fetch + state |
| `useThreeWayMatch.ts` | Three-Way Match data fetch + state |
| `useBilling.ts` | Subscription/checkout state |
| `useCommandPalette.ts` | Command palette open/close + search |
| `useKeyboardShortcuts.ts` | 7 global keyboard shortcuts |
| `useFeatureFlag.ts` | Feature flag evaluation |
| `useCanvasAccentSync.ts` | Canvas accent color sync |
| `usePreflight.ts` | Pre-flight check orchestration |
| `useReducedMotion.ts` | Accessibility motion preference |
| `useRegisterCommands.ts` | Command palette registration |
| `useSonification.ts` | Data sonification toggle |
| `useWorkspaceInsights.ts` | Workspace insight data |

**Recommendation:** The 9 tool-specific hooks likely share a pattern via `createTestingHook.ts` (which IS tested). Prioritize:
- `useBilling.ts` — payment flow correctness
- `useKeyboardShortcuts.ts` — accessibility compliance
- `useCommandPalette.ts` — user interaction correctness
- `useFeatureFlag.ts` — tier gating correctness

---

## Priority 5: Frontend Context Providers (MEDIUM IMPACT)

6 of 8 context providers lack tests:

| Context | Tested? |
|---------|---------|
| `AuthContext.tsx` | Yes |
| `EngagementContext.tsx` | Yes |
| `BatchUploadContext.tsx` | No |
| `CanvasAccentContext.tsx` | No |
| `CommandPaletteContext.tsx` | No |
| `DiagnosticContext.tsx` | No |
| `MappingContext.tsx` | No |
| `WorkspaceContext.tsx` | No |

**Recommendation:** `DiagnosticContext` and `MappingContext` are functionally critical (they manage TB upload state and column mapping). `WorkspaceContext` manages the shared workspace shell state. These three should be tested first.

---

## Priority 6: Frontend Component Coverage Gaps

### Shared Components (25 untested)
Includes: `UpgradeGate`, `ToolNav`, `StatusBadge`, `UsageMeter`, `GlobalCommandPalette`, `IntelligenceCanvas` (4 files), `ProofTraceBar`, all 5 skeleton components, and all 4 shared testing components (`DataQualityBadge`, `FlaggedEntriesTable`, `TestResultGrid`, `TestingScoreCard`).

### Workspace Components (9 untested)
`CommandBar`, `ContextPane`, `InsightRail`, `QuickActionsBar`, `QuickSwitcher`, `RecentHistoryMini`, `WorkspaceFooter`, `WorkspaceHeader`, `WorkspaceShell`

### Marketing Components (10 untested)
All marketing components: `BottomProof`, `DemoZone`, `FeaturePillars`, `HeroProductFilm`, `MarketingFooter`, `MarketingNav`, `ProcessTimeline`, `ProductPreview`, `ProofStrip`, `ToolShowcase`

### Tool-Specific Components (40 untested)
Every tool sub-directory has untested components: AP (4), AR (4), Bank Rec (3), Fixed Assets (4), Inventory (4), JE (5), Payroll (4), Revenue (4), Three-Way Match (4), Statistical Sampling (4).

**Recommendation:** Prioritize:
1. **Shared testing components** (4) — used across 9+ tool pages
2. **UpgradeGate** — tier enforcement UI
3. **Workspace shell** — core layout, affects all authenticated pages
4. Marketing components are lowest priority (static content)

---

## Priority 7: Infrastructure & Tooling Gaps

### No Backend Coverage Measurement
- Backend CI runs `pytest tests/ -v --tb=short -q` with **no coverage flag**
- No `pytest-cov` in dependencies
- No coverage threshold enforcement
- **Recommendation:** Add `pytest-cov`, set initial threshold at 40%, enforce in CI

### No E2E Tests
- No Playwright, Cypress, or similar framework
- Critical user flows (login → upload TB → run diagnostics → export) are untested end-to-end
- **Recommendation:** Add Playwright for 3-5 critical flows

### No Mutation Testing
- Tests may pass but miss real bugs (low assertion density in some files)
- **Recommendation:** Evaluate `mutmut` (Python) or Stryker (JS) for critical engines

### Shallow Test Files
Files with fewest assertions relative to size:
- `test_sentry_integration.py` — 6 assertions in 66 lines
- `test_recon_engine.py` — 6 assertions in 68 lines
- `test_audit_api.py` — 10 assertions in 163 lines
- `test_rate_limit_enforcement.py` — 9 assertions in 279 lines

---

## Memo Generator Coverage

All 17 memo generators lack dedicated unit tests:

| Generator | Lines |
|-----------|-------|
| `je_testing_memo_generator.py` | — |
| `ap_testing_memo_generator.py` | — |
| `ar_aging_memo_generator.py` | — |
| `revenue_testing_memo_generator.py` | — |
| `payroll_testing_memo_generator.py` | — |
| `fixed_asset_testing_memo_generator.py` | — |
| `inventory_testing_memo_generator.py` | — |
| `three_way_match_memo_generator.py` | — |
| `bank_reconciliation_memo_generator.py` | — |
| `multi_period_memo_generator.py` | — |
| `sampling_memo_generator.py` | — |
| `currency_memo_generator.py` | — |
| `accrual_completeness_memo.py` | — |
| `expense_category_memo.py` | — |
| `flux_expectations_memo.py` | — |
| `population_profile_memo.py` | — |
| `preflight_memo_generator.py` | — |

**Recommendation:** These generate PCAOB/ISA-compliant PDF workpapers. A broken memo means a broken audit deliverable. At minimum, test that each generator:
- Produces non-empty output for valid input
- Handles edge cases (empty results, all-pass, all-fail)
- Includes required standard references (ISA/PCAOB citations)

---

## Summary: Recommended Test Improvement Phases

### Phase A: Backend Engine Unit Tests (highest ROI)
- Target: 13 engines without direct tests (~17,000 lines)
- Estimated: 200-300 new tests
- Impact: Validates core financial analysis logic in isolation

### Phase B: Security Module Tests
- Target: 4 security files (~1,257 lines)
- Estimated: 40-60 new tests
- Impact: Validates authentication/authorization/sanitization boundaries

### Phase C: Backend Coverage Infrastructure
- Add `pytest-cov` to CI
- Set and enforce coverage threshold
- Generate coverage reports as CI artifacts

### Phase D: Frontend Hook + Context Tests
- Target: 19 hooks + 6 contexts
- Estimated: 100-150 new tests
- Impact: Validates data flow and state management

### Phase E: Frontend Component Tests
- Target: 40 tool-specific + 25 shared + 9 workspace
- Estimated: 200+ new tests
- Impact: Validates UI rendering and interaction

### Phase F: E2E Test Foundation
- Add Playwright
- Target: 5 critical user flows
- Impact: Validates full-stack integration
