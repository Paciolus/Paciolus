# Phase XXXI — Frontend Test Coverage Expansion (Sprints 231–238)

> **Focus:** Raise frontend test coverage from 8.3% line / 4.5% file to ~15% line / ~20% file
> **Source:** 3-agent audit (frontend coverage, backend quality, deferred items) — 2026-02-14
> **Scope:** Frontend only — fix 22 pre-existing failures, add ~175 new tests across utilities, hooks, contexts
> **Design:** No UI/UX changes — pure test infrastructure hardening

## Results

| Metric | Before | After |
|--------|:------:|:-----:|
| Frontend test files | 13 | 33 |
| Tests (passing) | 106 / 128 | 389 / 389 |
| Pre-existing failures | 22 | 0 |
| Backend tests | 2,977 | 2,977 (unchanged) |

## Sprint Summary

| Sprint | Feature | Tests Added | Status |
|--------|---------|:-----------:|:---:|
| 231 | Fix 22 failing tests + ToolsLayout test | +7 new, -22 stale removed | COMPLETE |
| 232 | Pure utility tests (formatting, constants, themeUtils, animations, ThemeProvider) | +92 | COMPLETE |
| 233 | apiClient tests (cache, retry, CSRF, error handling) | +39 | COMPLETE |
| 234 | Auth + Form hooks (AuthContext, useFormValidation, commonValidators) | +56 | COMPLETE |
| 235 | Upload + Factory hooks (useFileUpload, useTestingExport, createTestingHook) | +19 | COMPLETE |
| 236 | CRUD hooks (useClients, useEngagement, useAdjustments, useBenchmarks) | +37 | COMPLETE |
| 237 | Context + Data hooks (EngagementContext, useFetchData, useSettings, usePriorPeriod) | +32 | COMPLETE |
| 238 | Phase XXXI Wrap — regression + documentation | 0 | COMPLETE |

## Sprint Details

### Sprint 231: Fix Pre-Existing Failures + ToolsLayout Test
- Root cause: Sprint 207 moved ToolNav/VerificationBanner to layout.tsx, 11 page tests still asserted on them
- Removed 22 stale test cases (2 per page × 11 pages) + orphaned jest.mock lines
- Created `ToolsLayout.test.tsx` with 7 tests covering layout-level concerns
- Special cases: BankRec/TWM kept FileDropZone in shared mock; TB kept inline "Verify Your Email" text assertion
- Result: 14 suites, 114 tests, 0 failures

### Sprint 232: Pure Utility Tests
- `formatting.test.ts` (25 tests): formatCurrency, formatCurrencyWhole, parseCurrency, formatNumber, formatPercent, formatPercentWhole, formatDate, formatTime, formatDateTime, formatDateTimeCompact, getRelativeTime
- `constants.test.ts` (13 tests): minutes(), hours(), API_URL, timeout/retry/cache constants
- `themeUtils.test.ts` (30 tests): getHealthClasses, getHealthLabel, getVarianceClasses, getInputClasses, getSelectClasses, getBadgeClasses, getRiskLevelClasses, cx utility, constant shapes
- `animations.test.ts` (12 tests): fadeInUp, fadeInUpSpring, fadeIn, dataFillTransition, scoreCircleTransition
- `ThemeProvider.test.tsx` (8 tests): DARK_ROUTES matching, theme resolution logic, children rendering
- Timezone fix: getRelativeTime test changed to midday/mid-month to avoid boundary issues

### Sprint 233: apiClient Tests
- `apiClient.test.ts` (39 tests): parseApiError, isAuthError, isNotFoundError, isValidationError, getStatusMessage, CSRF management, cache operations, apiFetch success/error paths, CSRF injection, convenience methods, downloadBlob
- Uses `global.fetch = jest.fn()` for fetch mocking
- Clears cache between tests with `invalidateCache()`

### Sprint 234: Auth + Form Hooks
- `useFormValidation.test.ts` (47 tests): hook state, setValue, setValues, isDirty, isValid, validateField, validate, handleBlur, setError, clearErrors, setAllTouched, reset, handleSubmit, getFieldProps, getFieldState + commonValidators (required, email, minLength, maxLength, min, max, pattern, matches)
- `AuthContext.test.tsx` (9 tests): throws outside provider, initial state, auth methods, sessionStorage restoration, invalid data clearing, unauthenticated guards

### Sprint 235: Upload + Factory Hooks
- `useFileUpload.test.ts` (9 tests): drag/drop state, file handling, ref management
- `useTestingExport.test.ts` (6 tests): PDF/CSV export, fallback filenames, auth guard, error recovery
- `createTestingHook.test.ts` (4 tests): factory creates hook, idle state, custom buildFormData

### Sprint 236: CRUD Hooks
- `useClients.test.ts` (9 tests): CRUD operations, pagination, industries, auth guard
- `useEngagement.test.ts` (9 tests): CRUD, tool runs, materiality cascade, auth guard
- `useAdjustments.test.ts` (11 tests): entries, stats, create/update/delete, clearAll, getNextReference, applyAdjustments
- `useBenchmarks.test.ts` (8 tests): public endpoints (no token), auth comparison, clear, error states

### Sprint 237: Context + Data Hooks
- `EngagementContext.test.tsx` (7 tests): provider rendering, selectEngagement, clearEngagement, useOptionalEngagementContext (null outside/works inside), toast management
- `useFetchData.test.ts` (9 tests): fetch, transform, error, auth guard, clear, refetch, hasDataCheck, URL params
- `useSettings.test.ts` (8 tests): auto-fetch on mount, updatePracticeSettings, fetchClientSettings, updateClientSettings, previewMateriality, resolveMateriality, auth guard
- `usePriorPeriod.test.ts` (8 tests): fetchPeriods, savePeriod, comparePeriods, clearComparison, no-token guard, error handling

### Sprint 238: Phase XXXI Wrap
- `npm run build` passes
- `pytest` — 2,977 passed
- Frontend tests — 33 suites, 389 tests, 0 failures
- Archived phase details
- Updated todo.md, CLAUDE.md, MEMORY.md

## Files Created/Modified

### New Test Files (20)
- `__tests__/ToolsLayout.test.tsx`
- `__tests__/formatting.test.ts`
- `__tests__/constants.test.ts`
- `__tests__/themeUtils.test.ts`
- `__tests__/animations.test.ts`
- `__tests__/ThemeProvider.test.tsx`
- `__tests__/apiClient.test.ts`
- `__tests__/useFormValidation.test.ts`
- `__tests__/AuthContext.test.tsx`
- `__tests__/useFileUpload.test.ts`
- `__tests__/useTestingExport.test.ts`
- `__tests__/createTestingHook.test.ts`
- `__tests__/useClients.test.ts`
- `__tests__/useEngagement.test.ts`
- `__tests__/useAdjustments.test.ts`
- `__tests__/useBenchmarks.test.ts`
- `__tests__/EngagementContext.test.tsx`
- `__tests__/useFetchData.test.ts`
- `__tests__/useSettings.test.ts`
- `__tests__/usePriorPeriod.test.ts`

### Modified Test Files (11 — stale assertions removed)
- `__tests__/APTestingPage.test.tsx`
- `__tests__/ARAgingPage.test.tsx`
- `__tests__/BankRecPage.test.tsx`
- `__tests__/FixedAssetTestingPage.test.tsx`
- `__tests__/InventoryTestingPage.test.tsx`
- `__tests__/JournalEntryTestingPage.test.tsx`
- `__tests__/MultiPeriodPage.test.tsx`
- `__tests__/PayrollTestingPage.test.tsx`
- `__tests__/RevenueTestingPage.test.tsx`
- `__tests__/ThreeWayMatchPage.test.tsx`
- `__tests__/TrialBalancePage.test.tsx`
