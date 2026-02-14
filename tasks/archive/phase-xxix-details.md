# Phase XXIX — API Integration Hardening (Sprints 217–223) — Detailed Checklists

> **Status:** COMPLETE
> **Source:** Comprehensive 4-agent API integration audit (2026-02-14) — API client consistency, TS/Pydantic type drift, error handling patterns, loading/error/empty state consistency
> **Strategy:** Backend type safety first (highest ROI — silent runtime failures), then frontend error handling, then UI state consistency, then infrastructure guardrails
> **Scope:** 15 `response_model=dict` → typed Pydantic models, Literal/Enum tightening, apiClient 422 parsing, CSRF gaps, UI state standardization, contract test infrastructure

## Audit Findings Summary

| Category | Finding | Count | Severity |
|----------|---------|:-----:|----------|
| **Type Safety** | Testing tool endpoints return `response_model=dict` (no validation) | 15 | CRITICAL |
| **Type Safety** | Engagement/follow-up use `str` where frontend expects `Literal` unions | 5 fields | MEDIUM |
| **Type Safety** | `FluxAnalysisResponse` nested `flux: dict, recon: dict` untyped | 2 fields | HIGH |
| **Error Handling** | No Pydantic 422 validation error parsing in apiClient | 1 | HIGH |
| **Error Handling** | `useSettings` mutations fail silently (no try/catch) | 3+ calls | HIGH |
| **Error Handling** | Missing `isAuthError()` checks in hooks | 3 hooks | MEDIUM |
| **Error Handling** | `downloadBlob.ts` bypasses apiClient — missing CSRF | 1 file | HIGH |
| **Error Handling** | Logout endpoint missing CSRF token | 1 call | MEDIUM |
| **UI States** | Portfolio/Engagements error states lack retry buttons | 2 pages | LOW |
| **UI States** | Trial-balance error styling uses hardcoded colors not theme tokens | 1 page | LOW |
| **UI States** | Settings profile loading spinner has no loading text | 1 page | LOW |
| **Infrastructure** | No API contract tests validating response shapes | — | MEDIUM |
| **Infrastructure** | No OpenAPI → TypeScript generation (types manually maintained) | — | MEDIUM |

---

## Sprint 217 — Backend Response Models: Diagnostic Tools — COMPLETE

> **Complexity:** 5/10

### Checklist

- [x] Audit `audit_engine.py` `to_dict()` output shape → create `TrialBalanceResponse(BaseModel)` with 12 nested models
- [x] Audit `FluxAnalysisResponse` nested dict shapes → create `FluxDataResponse`, `ReconDataResponse` with `FluxItemResponse`, `ReconScoreResponse`
- [x] Audit `prior_period_comparison.py` → create `PeriodComparisonResponse` with `CategoryVarianceResponse`, `RatioVarianceResponse`, `DiagnosticVarianceResponse`
- [x] Audit `multi_period_comparison.py` → create `MovementSummaryResponse` (2-way), `ThreeWayMovementSummaryResponse` (3-way) with nested movement/lead-sheet models
- [x] Audit `adjusting_entries.py` → create `AdjustingEntryResponse`, `AdjustedTrialBalanceResponse` with line/account/totals sub-models
- [x] New file: `backend/shared/diagnostic_response_schemas.py` (~370 lines, 32 Pydantic models)
- [x] Update 7 route decorators: `response_model=dict` → typed models across 4 files
- [x] `TrialBalanceResponse` and `AbnormalBalanceResponse` use `extra="allow"` for safe migration
- [x] `pytest` — 2,903 passed
- [x] `npm run build` — passes

### Files

**Created:** `backend/shared/diagnostic_response_schemas.py` (32 models)
**Modified:** `routes/audit.py`, `routes/prior_period.py`, `routes/multi_period.py`, `routes/adjustments.py`

**Endpoints migrated (7):**
- `POST /audit/trial-balance` → `TrialBalanceResponse`
- `POST /audit/flux` → `FluxAnalysisResponse`
- `POST /audit/compare` → `PeriodComparisonResponse`
- `POST /audit/compare-periods` → `MovementSummaryResponse`
- `POST /audit/compare-three-way` → `ThreeWayMovementSummaryResponse`
- `GET /audit/adjustments/{entry_id}` → `AdjustingEntryResponse`
- `POST /audit/adjustments/apply` → `AdjustedTrialBalanceResponse`

---

## Sprint 218 — Backend Response Models: Testing Tools Batch 1 — COMPLETE

> **Complexity:** 5/10

### Checklist

- [x] Audit 5 testing engines → create response models (JE, AP, Bank Rec, TWM, AR Aging)
- [x] Extract shared: `CompositeScoreResponse`, `DataQualityResponse`, `BenfordAnalysisResponse`
- [x] New file: `backend/shared/testing_response_schemas.py` (~500 lines, 42 models)
- [x] Update 6 route decorators
- [x] `pytest` — 2,903 passed
- [x] `npm run build` — passes

### Files

**Created:** `backend/shared/testing_response_schemas.py` (42 models)
**Modified:** `routes/je_testing.py`, `routes/ap_testing.py`, `routes/bank_reconciliation.py`, `routes/three_way_match.py`, `routes/ar_aging.py`

**Endpoints migrated (6):**
- `POST /audit/journal-entries` → `JETestingResponse`
- `POST /audit/journal-entries/sample` → `SamplingResultResponse`
- `POST /audit/ap-payments` → `APTestingResponse`
- `POST /audit/bank-reconciliation` → `BankRecResponse`
- `POST /audit/three-way-match` → `ThreeWayMatchResponse`
- `POST /audit/ar-aging` → `ARAgingResponse`

---

## Sprint 219 — Backend Response Models: Testing Batch 2 + Enum Tightening — COMPLETE

> **Complexity:** 5/10

### Checklist

- [x] Create response models for Payroll (7), Revenue (5), FA (5), Inventory (5)
- [x] Update 4 route decorators
- [x] Tighten `EngagementResponse.status` to `Literal['active', 'archived']`
- [x] Tighten `EngagementResponse.materiality_basis` to `Optional[Literal['revenue', 'assets', 'manual']]`
- [x] Tighten `FollowUpItemResponse.severity`/`.disposition` to Literal types
- [x] Add `MaterialityPreviewResponse` to settings.py
- [x] Add `WorkpaperIndexResponse` (4 nested models) to engagements.py
- [x] `pytest` — 2,903 passed
- [x] `npm run build` — passes

### Files

**Modified:** `shared/testing_response_schemas.py` (+22 models), `routes/payroll_testing.py`, `routes/revenue_testing.py`, `routes/fixed_asset_testing.py`, `routes/inventory_testing.py`, `routes/engagements.py`, `routes/follow_up_items.py`, `routes/settings.py`

**Endpoints migrated (6):** Payroll, Revenue, FA, Inventory, workpaper-index, materiality/preview
**Enum tightening (4 fields):** EngagementResponse.status, EngagementResponse.materiality_basis, FollowUpItemResponse.severity, FollowUpItemResponse.disposition

---

## Sprint 220 — Frontend Error Handling Hardening — COMPLETE

> **Complexity:** 4/10

### Checklist

- [x] `apiClient.ts`: detect `Array.isArray(detail)` → extract Pydantic 422 `msg` field
- [x] `useTrends.ts`: add `isAuthError(status)` check
- [x] `useSettings.ts`: add `isAuthError(status)` + error surfacing to 6 methods
- [x] `useBenchmarks.ts`: add `isAuthError(status)` on `compareToBenchmarks`
- [x] Delete `lib/downloadBlob.ts`; migrate 3 consumers to `apiDownload()` + `downloadBlob()`
- [x] Update 2 test mocks (BankRecPage.test, MultiPeriodPage.test)
- [x] `AuthContext.tsx`: inject `getCsrfToken()` into logout POST headers
- [x] `npm run build` — passes

### Files

**Deleted:** `frontend/src/lib/downloadBlob.ts`
**Modified:** `apiClient.ts`, `useTrends.ts`, `useSettings.ts`, `useBenchmarks.ts`, `useTestingExport.ts`, `multi-period/page.tsx`, `bank-rec/page.tsx`, `AuthContext.tsx`, 2 test files

---

## Sprint 221 — UI State Consistency — COMPLETE

> **Complexity:** 3/10

### Checklist

- [x] `portfolio/page.tsx`: retry button + theme tokens + `role="alert"`
- [x] `engagements/page.tsx`: retry button + theme tokens + `role="alert"`
- [x] `trial-balance/page.tsx`: `bg-clay-50` → `bg-theme-error-bg`
- [x] `settings/profile/page.tsx`: loading text + dismiss button + theme tokens
- [x] `settings/practice/page.tsx`: loading text + theme tokens
- [x] `history/page.tsx`: framer-motion spinner → CSS `animate-spin`
- [x] `npm run build` — passes

### Files

**Modified:** `portfolio/page.tsx`, `engagements/page.tsx`, `trial-balance/page.tsx`, `settings/profile/page.tsx`, `settings/practice/page.tsx`, `history/page.tsx`

---

## Sprint 222 — API Contract Tests + Type Generation Infrastructure — COMPLETE

> **Complexity:** 4/10

### Checklist

- [x] `test_api_contracts.py`: 74 tests across 12 test classes
- [x] Testing tools: composite_score/test_results/data_quality validation + unique fields
- [x] Literal value validation: risk_tier, test_tier, severity, status, disposition, etc.
- [x] Schema generation smoke tests for 19 top-level models
- [x] `generate-types.sh`: OpenAPI → TypeScript with server auto-detection
- [x] `package.json`: `"generate:types"` script
- [x] `pytest` — 2,977 passed (+74 contract tests)
- [x] `npm run build` — passes

### Files

**Created:** `backend/tests/test_api_contracts.py` (74 tests), `frontend/scripts/generate-types.sh`
**Modified:** `frontend/package.json`

---

## Sprint 223 — Phase XXIX Wrap — Regression + Documentation — COMPLETE

> **Complexity:** 2/10

### Checklist

- [x] `pytest` — 2,977 passed, 0 regressions
- [x] `npm run build` — passes
- [x] CLAUDE.md: Phase XXIX summary added, status COMPLETE, test count updated
- [x] Archive detailed checklists to `tasks/archive/phase-xxix-details.md`
- [x] MEMORY.md: project status updated
- [x] todo.md: Phase XXIX replaced with summary

---

## Phase Summary

| Metric | Value |
|--------|-------|
| **Sprints** | 7 (217–223) |
| **Backend Models Created** | 102 Pydantic response schemas |
| **Endpoints Migrated** | 19 (response_model=dict → typed) |
| **Enum Fields Tightened** | 4 (str → Literal) |
| **Frontend Files Modified** | 12 |
| **Frontend Files Deleted** | 1 (downloadBlob.ts) |
| **Contract Tests Added** | 74 |
| **Total Test Count** | 2,977 backend + 128 frontend |
