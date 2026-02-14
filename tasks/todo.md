# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Phase Lifecycle Protocol

**MANDATORY:** Follow this lifecycle for every phase. This eliminates manual archive requests.

### During a Phase
- Active phase details (audit findings, sprint checklists, reviews) live in this file under `## Active Phase`
- Each sprint gets a checklist section with tasks, status, and review

### On Phase Completion (Wrap Sprint)
1. **Regression:** `pytest` + `npm run build` must pass
2. **Archive:** Move all sprint checklists/reviews to `tasks/archive/phase-<name>-details.md`
3. **Summarize:** Add a one-line summary to `## Completed Phases` below (with test count if changed)
4. **Clean this file:** Delete the entire `## Active Phase` section content, leaving only the header ready for the next phase
5. **Update CLAUDE.md:** Add phase to completed list, update test count + current phase
6. **Update MEMORY.md:** Update project status
7. **Commit:** `Sprint X: Phase Y wrap — regression verified, documentation archived`

**The `## Active Phase` section should ONLY contain the current in-progress phase. Once complete, it becomes empty until the next phase begins.**

---

## Completed Phases

### Phases I–IX (Sprints 1–96) — COMPLETE
> Core platform through Three-Way Match. TB analysis, streaming, classification, 9 ratios, anomaly detection, benchmarks, lead sheets, prior period, adjusting entries, email verification, Multi-Period TB (Tool 2), JE Testing (Tool 3, 18 tests), Financial Statements (Tool 1), AP Testing (Tool 4, 13 tests), Bank Rec (Tool 5), Cash Flow, Payroll Testing (Tool 6, 11 tests), TWM (Tool 7), Classification Validator.

### Phase X (Sprints 96.5–102) — COMPLETE
> Engagement Layer: engagement model + materiality cascade, follow-up items, workpaper index, anomaly summary report, diagnostic package export, engagement workspace frontend.

### Phase XI (Sprints 103–110) — COMPLETE
> Tool-Engagement Integration, Revenue Testing (Tool 8, 12 tests), AR Aging (Tool 9, 11 tests).

### Phase XII (Sprints 111–120) — COMPLETE
> Nav overflow, Finding Comments + Assignments, Fixed Asset Testing (Tool 10, 9 tests), Inventory Testing (Tool 11, 9 tests). **v1.1.0**

### Phase XIII (Sprints 121–130) — COMPLETE
> Dual-theme "The Vault", security hardening, WCAG AAA, 11 PDF memos, 24 rate-limited exports. **v1.2.0. Tests: 2,593 + 128.**

### Phase XIV (Sprints 131–135) — COMPLETE
> 6 public marketing/legal pages, shared MarketingNav/Footer, contact backend.

### Phase XV (Sprints 136–141) — COMPLETE
> Code deduplication: shared parsing helpers, shared types, 4 shared testing components. ~4,750 lines removed.

### Phase XVI (Sprints 142–150) — COMPLETE
> API Hygiene: 15 fetch → apiClient, semantic tokens, Docker hardening.

### Phase XVII (Sprints 151–163) — COMPLETE
> Code Smell Refactoring: 7 backend shared modules, 8 frontend decompositions, 15 new shared files. **Tests: 2,716 + 128.**

### Phase XVIII (Sprints 164–170) — COMPLETE
> Async Architecture: `async def` → `def` for pure-DB, `asyncio.to_thread()` for CPU-bound, `BackgroundTasks`, `memory_cleanup()`.

### Phase XIX (Sprints 171–177) — COMPLETE
> API Contract Hardening: 25 endpoints gain response_model, 16 status codes corrected, trends.py fix, path fixes.

### Phase XX (Sprint 178) — COMPLETE
> Rate Limit Gap Closure: 4 endpoints secured, global 60/min default.

### Phase XXI (Sprints 180–183) — COMPLETE
> Migration Hygiene: Alembic baseline regeneration, datetime deprecation fix.

### Phase XXII (Sprints 184–190) — COMPLETE
> Pydantic Model Hardening: Field constraints, 13 Enum/Literal migrations, model decomposition, v2 syntax.

### Phase XXIII (Sprints 191–194) — COMPLETE
> Pandas Performance: vectorized keyword matching, NEAR_ZERO guards, math.fsum. **Tests: 2,731 + 128.**

### Phase XXIV (Sprint 195) — COMPLETE
> Upload & Export Security: formula injection, column/cell limits, body size middleware. **Tests: 2,750 + 128.**

### Sprint 196 — PDF Generator Critical Fixes — COMPLETE
> Fix `_build_workpaper_signoff()` crash, dynamic tool count, BytesIO leak.

### Phase XXV (Sprints 197–201) — COMPLETE
> JWT Auth Hardening: refresh tokens, CSRF/CORS, bcrypt, jti claim, startup cleanup. **Tests: 2,883 + 128.**

### Phase XXVI (Sprints 202–203) — COMPLETE
> Email Verification Hardening: token cleanup, pending_email re-verification, disposable blocking. **Tests: 2,903 + 128.**

### Phase XXVII (Sprints 204–209) — COMPLETE
> Next.js App Router Hardening: 7 error boundaries, 4 route groups, skeleton components, loading.tsx files.

### Phase XXVIII (Sprints 210–216) — COMPLETE
> Production Hardening: GitHub Actions CI, structured logging + request ID, 46 exceptions narrowed, 45 return types, deprecated patterns migrated.

### Phase XXIX (Sprints 217–223) — COMPLETE
> API Integration Hardening: 102 Pydantic response schemas, apiClient 422 parsing, isAuthError in 3 hooks, downloadBlob→apiClient, CSRF on logout, UI state consistency, 74 contract tests, OpenAPI→TS generation. **Tests: 2,977 + 128.**

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix)

---

## Post-Sprint Checklist

**MANDATORY:** Complete after EVERY sprint.

- [ ] `npm run build` passes
- [ ] `pytest` passes (if tests modified)
- [ ] Zero-Storage compliance verified (if new data handling)
- [ ] Sprint status → COMPLETE, Review section added
- [ ] Lessons added to `lessons.md` (if corrections occurred)
- [ ] `git add <files> && git commit -m "Sprint X: Description"`

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Multi-Currency Conversion | Detection shipped; conversion logic needs RFC | Phase VII |
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, auditor judgment | Phase X |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Dual-key rate limiting | IP-only + lockout adequate for now | Phase XX |
| Wire Alembic into startup | Latency + multi-worker race risk; revisit for PostgreSQL | Phase XXI |
| `PaginatedResponse[T]` generic | Complicates OpenAPI schema generation | Phase XXII |
| Dedicated `backend/schemas/` dir | Model count doesn't justify yet | Phase XXII |
| Cookie-based auth (SSR) | Large blast radius; requires JWT → httpOnly cookie migration | Phase XXVII |
| Marketing pages SSG | Requires cookie auth first | Phase XXVII |
| Frontend test coverage (4.3% → 30%+) | 302 source files, 13 tested — needs dedicated multi-sprint effort | Phase XXVIII |
| Fix 22 pre-existing frontend test failures | Sprint 207 moved ToolNav/VerificationBanner to layout; 11 page tests still assert on them — see details below | Phase XXVII |

---

## Active Phase

### Phase XXX — Frontend Type Safety Hardening (Sprints 224–230)

> **Focus:** Eliminate `any`, unsafe assertions, missing return types, duplicated/drifting type definitions, and optional chaining band-aids across the frontend TypeScript codebase.
> **Source:** Comprehensive TypeScript type safety audit (2026-02-14) — 5-dimension scan (any, assertions, return types, duplication, optional chaining)
> **Strategy:** Foundation first (apiClient generic + tsconfig), then type consolidation, then discriminated unions, then assertion/any cleanup, then annotation pass, then optional chaining, then wrap
> **Scope:** Frontend only — 14 high-risk files, ~35 unsafe assertions, 33 missing return types, 5 `any` production sites, 60–80 unnecessary optional chains
> **Design:** No UI/UX changes — pure type-system hardening

#### Audit Findings Summary

| Category | Count | Key Files |
|----------|:-----:|-----------|
| `any` in production code | 5 sites (3 files) | FlaggedEntriesTable, TestResultGrid, useFormValidation |
| Unsafe `as` assertions | 35 (14 files) | 16 double-casts in hooks, 4 non-null in ToolStatusGrid, 3 JSON.parse |
| Missing return types | 33 exported fns | 10 hooks, 6 providers, 17 utilities/components |
| Duplicated/drifting types | 5 issues | Severity (3 defs), Risk (4 defs), AuditResult (inline copy), AuditStatus (2 defs) |
| Optional chaining overuse | 60–80 chains | BankRecMatchTable (20+), TWM (15+), engagement triple-chain (3 files) |

---

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 224 | Foundation: apiClient Generic Signature + tsconfig Hardening | 4/10 | COMPLETE |
| 225 | Type Taxonomy Consolidation (Severity, Risk, AuditResult, AuditStatus) | 5/10 | COMPLETE |
| 226 | Discriminated Unions + Hook Return Narrowing | 6/10 | COMPLETE |
| 227 | `any` Elimination + Type Assertion Fixes | 4/10 | PENDING |
| 228 | Return Type Annotations (33 Exported Functions) | 3/10 | PENDING |
| 229 | Optional Chaining Cleanup | 4/10 | PENDING |
| 230 | Phase XXX Wrap — Regression + Documentation | 2/10 | PENDING |

---

#### Sprint 224: Foundation — apiClient Generic + tsconfig Hardening
> **Goal:** Fix the root cause behind 12 double-cast assertions and tighten the compiler

**apiClient Generic Signature:**
- [x] Widen `body` param from `Record<string, unknown>` to `object` in `ApiRequestOptions`, `apiPost`, `apiPut`, `apiPatch`
- [x] Remove all 12 `as unknown as Record<string, unknown>` double-casts across 6 hook files:
  - `useAdjustments.ts` (2)
  - `useEngagement.ts` (2)
  - `useClients.ts` (2)
  - `useFollowUpComments.ts` (2)
  - `useFollowUpItems.ts` (2)
  - `usePriorPeriod.ts` (2)
  - Note: `useFetchData.ts` had response-data casts (Sprint 227 scope), not body casts
- [x] Verify all POST/PUT/PATCH calls compile without casts

**tsconfig Hardening:**
- [x] Enable `noUncheckedIndexedAccess` — forces `T | undefined` on bracket access
- [x] Enable `noFallthroughCasesInSwitch` — prevents missing `break`
- [x] Enable `noImplicitReturns` — catches forgotten returns
- [x] Fix 14 new compiler errors introduced by new flags:
  - `AdjustmentEntryForm.tsx` — array index guard
  - `TrendSparkline.tsx` — `payload[0]!` after length check
  - `CommentThread.tsx` — `replies[parentId]!` after init
  - `BenfordChart.tsx` — `BENFORD_EXPECTED[digit] ?? 0`
  - `LeadSheetCard.tsx` / `ClientCard.tsx` — `Record<string, ...>` index fallbacks
  - `ToolNav.tsx` — early return for `noImplicitReturns`
  - `createTestingHook.ts` — `files[0]` guard
  - `useTrends.ts` — array last-element guard
  - `batch.ts` — `parts[length-1]` guard
  - `client.ts` — destructuring defaults for split
  - `apiClient.ts` — 3× `split('?')[0] ?? endpoint` fallback
- [x] `npm run build` passes
- [x] Frontend tests: 106 pass / 22 fail (pre-existing, identical before changes)

**Review:**
- Audit estimated 16 double-casts across 7 hooks; actual was 12 across 6 hooks (`useFetchData` only has response-data casts, not body casts)
- Body type widened from `Record<string, unknown>` to `object` rather than adding `TBody` generic — simpler, no caller changes, `JSON.stringify` accepts any `object`
- `noUncheckedIndexedAccess` was the most impactful flag — caught 10 of 14 errors, all real potential undefined accesses
- `noImplicitReturns` caught 1 issue (ToolNav useEffect missing return path)
- `noFallthroughCasesInSwitch` caught 0 issues — all switch cases were already safe

---

#### Sprint 225: Type Taxonomy Consolidation
> **Goal:** Unify competing type definitions into single sources of truth

**Severity Consolidation (3 definitions → 1):**
- [x] Decided 3-value (`'high' | 'medium' | 'low'`) — all backend Pydantic schemas enforce `Literal["high", "medium", "low"]`
- [x] Created `types/shared.ts` with canonical `Severity = 'high' | 'medium' | 'low'`
- [x] Fixed mapping.ts: was incorrectly 2-value (`'high' | 'low'`), now imports from shared
- [x] Fixed `RiskSummary` in mapping.ts: added missing `medium_severity: number` field
- [x] Removed `VarianceSeverity` from threeWayMatch.ts — imports `Severity` from shared
- [x] Updated `TestingSeverity` in testingShared.ts to alias canonical `Severity`
- [x] Updated `FollowUpItemsTable.tsx` SEVERITY_ORDER to use `Record<Severity, number>`
- [x] Fixed `demoData.ts` DEMO_RISK_SUMMARY: added `medium_severity: 0`

**Risk Taxonomy Consolidation (4 definitions → 2):**
- [x] Investigated: 4 risk types represent genuinely different scales:
  - `RiskLevel` (4-tier with 'none') — diagnostic flux analysis
  - `RiskBand` (3-tier) — diagnostic reconciliation scoring
  - `TWMRiskLevel` (3-tier) — three-way match, local to its types file
  - `TestingRiskTier` (5-tier) — testing tools
- [x] Decision: no forced consolidation — different scales serve different domains
- [x] `TWMRiskLevel` kept local since only used within `threeWayMatch.ts`

**AuditResult Relocation:**
- [x] Moved `AuditResult` interface from `hooks/useTrialBalanceAudit.ts` to `types/diagnostic.ts`
- [x] Deleted 20-line inline copy `AuditResultForExport` + `ClassificationSummary` in `DownloadReportButton.tsx`
- [x] Updated imports: `useTrialBalanceAudit.ts` (re-exports), `AuditResultsPanel.tsx`, `DownloadReportButton.tsx`

**AuditStatus → UploadStatus Dedup:**
- [x] Added `UploadStatus = 'idle' | 'loading' | 'success' | 'error'` to `types/shared.ts`
- [x] Replaced local `type AuditStatus` in `useAuditUpload.ts` and `PeriodFileDropZone.tsx`
- [x] Replaced inline union in `useTrialBalanceAudit.ts` and `GuestMarketingView.tsx`
- [x] Updated 9 testing hook return interfaces to use `UploadStatus`:
  useJETesting, useAPTesting, useARAging, useBankReconciliation, useFixedAssetTesting,
  useInventoryTesting, usePayrollTesting, useRevenueTesting, useThreeWayMatch

- [x] `npm run build` passes

**Review:**
- Severity was a genuine bug: frontend had 2-value but backend enforces 3-value — fixed by creating canonical type in `types/shared.ts`
- `RiskSummary` also had a drift: missing `medium_severity` field that backend returns — fixed
- Risk taxonomy audit found no consolidation needed — 4 scales serve genuinely different domains
- AuditResult relocation cleaned up 20-line inline copy + 8-line helper interface in DownloadReportButton
- UploadStatus dedup was broader than originally scoped: found 14 inline definitions, consolidated all 13 non-canonical sites to import from shared
- Total: 16 files modified, 0 new production `any` introduced, 0 behavioral changes

---

#### Sprint 226: Discriminated Unions + Hook Return Narrowing
> **Goal:** Replace optional-chaining band-aids with proper type narrowing via discriminated unions

**BankRec Match Discriminated Union:**
- [x] Update `ReconciliationMatchData` type (types/bankRec.ts) to use discriminated union by `match_type`:
  - `{ match_type: 'matched'; bank_txn: BankTxn; ledger_txn: LedgerTxn }`
  - `{ match_type: 'bank_only'; bank_txn: BankTxn; ledger_txn?: never }`
  - `{ match_type: 'ledger_only'; bank_txn?: never; ledger_txn: LedgerTxn }`
- [x] Update `BankRecMatchTable.tsx` — `getCategoryLabel()` uses narrowing (no `?.` on narrowed branches)
- [x] Verify no runtime behavior change

**Three-Way Match Discriminated Union — SKIPPED (by design):**
- [x] Investigated: `TWMMatchType` (`exact_po | fuzzy | partial`) describes _match strategy_, NOT document presence
  - All `full_matches` have PO + Invoice + Receipt regardless of match_type
  - `partial_matches` may miss documents regardless of match_type
  - Discriminated union by match_type would NOT reduce `?.` chains
- [x] Decision: keep `po: POData | null` etc. — the `?.` chains are genuinely necessary

**Hook Return Type Narrowing (7 testing tools):**
- [x] Define discriminated union on `UseAuditUploadReturn<T>`:
  `{ status: 'success'; result: T } | { status: 'idle'; result: null } | { status: 'loading'; result: null } | { status: 'error'; result: null }`
- [x] Type assertion in `useAuditUpload.ts` return (safe: React 18 batches `setStatus` + `setResult`)
- [x] Remove 33 `result?.` chains across 7 tool pages using `result ? { ... } : null` guard:
  - `ap-testing/page.tsx` (4 chains)
  - `fixed-assets/page.tsx` (4 chains)
  - `inventory-testing/page.tsx` (4 chains)
  - `payroll-testing/page.tsx` (4 chains)
  - `revenue-testing/page.tsx` (4 chains)
  - `journal-entry-testing/page.tsx` (6 chains)
  - `ar-aging/page.tsx` (7 chains including `skippedTests`)

**Engagement Context Flattening:**
- [x] Added `engagementId: number | null` to `OptionalEngagementContext` type
- [x] `useOptionalEngagementContext()` now returns flattened `engagementId` directly
- [x] Removed triple-chain `engagement?.activeEngagement?.id` in 3 files:
  - `useAuditUpload.ts` — `engagement?.engagementId`
  - `useTrialBalanceAudit.ts` (2 sites) — `engagement?.engagementId`
  - `multi-period/page.tsx` (2 sites) — `engagement?.engagementId`

- [x] `npm run build` passes

**Review:**
- TWM discriminated union was correctly skipped — the audit overestimated by conflating match_type with document presence. TWM match_type is about HOW the match was made (exact PO#, fuzzy, partial), not WHICH documents are present. The `?.` chains on `po`, `invoice`, `receipt` are genuinely necessary.
- BankRec discriminated union is a clean win: `getCategoryLabel()` now uses proper narrowing. Most table-render `?.` chains remain necessary because the component operates on all match types without narrowing (search, sort, render cells). Net removal: 3 `?.` chains in `getCategoryLabel`, not the 20+ estimated.
- Hook return discriminated union requires a type assertion at the implementation boundary (React `useState` can't enforce it). This is safe because React 18 batches state updates in event handlers.
- Tool page `exportBody` pattern changed from `result?.field` to `result ? { ... } : null` + `exportBody && handleExport(exportBody)`. Removes 33 `?.` chains. The guard pattern is also cleaner because it makes the null case explicit.
- Engagement flattening replaced 5 triple-chains (`?.activeEngagement?.id`) with single chains (`?.engagementId`) across 3 files. The `engagementId` derivation lives in `useOptionalEngagementContext()` (single source).
- Total: 15 files modified, 0 behavioral changes, 0 new `any` types

---

#### Sprint 227: `any` Elimination + Type Assertion Fixes
> **Goal:** Remove all production `any` types and fix unsafe assertions

**`any` Elimination (5 sites → 0):**
- [x] `FlaggedEntriesTable.tsx` — full generic refactor: `results: any[]` → `results: FlaggedResultInput<TEntry>[]`, `Record<string, any>` → parameterized `TEntry extends Record<string, unknown>`
- [x] `TestResultGrid.tsx:32` — `entry: any` → `entry: Record<string, unknown>` in FlaggedEntryBase
- [x] `useFormValidation.ts:74` — `{ [key: string]: any }` → `Record<string, unknown>`, all consumers compile
- [x] Remove all `// eslint-disable-next-line @typescript-eslint/no-explicit-any` comments from fixed lines
- [x] 7 consumer Flagged*Table files — added entry data type generics (`ColumnDef<APPaymentData>[]`, etc.)
- [x] 7 entry data types — `interface` → `type` for `Record<string, unknown>` index signature compat
- [x] 4 form value types — `interface` → `type` (LoginFormValues, RegisterFormValues, 2× ClientFormValues)

**Non-Null Assertion Fixes:**
- [x] `ToolStatusGrid.tsx:155-163` — replaced `data!.` with direct `data` ternary narrowing (4 assertions removed)
- [x] `flux/page.tsx:62-63` — added `!response.data` to guard, removing `response.data!.` assertions

**JSON.parse Validation:**
- [x] `AuthContext.tsx:195` — runtime shape check (`'id' in parsed && 'email' in parsed`)
- [x] `MappingContext.tsx:63` — runtime shape check (object, not array)
- [x] `types/client.ts:142` — runtime shape check in `parseClientPreferences()`

**useFetchData Response Safety:**
- [x] `useFetchData.ts:150, 157-158` — replaced `as TResponse & {...}` with runtime `typeof` + `'error' in` narrowing

- [x] `npm run build` passes

**Review:**
- FlaggedEntriesTable required full generic refactor rather than simple `any` → `unknown` because 7 consumer files access `fe.entry.propertyName` through `ColumnDef` callbacks. Made `FlaggedEntriesTable<TEntry>`, `ColumnDef<TEntry>`, `FlatFlaggedEntry<TEntry>`, `FlaggedResultInput<TEntry>` all generic with `TEntry extends Record<string, unknown>` + defaults.
- Discovered TypeScript `interface` vs `type` distinction: interfaces do NOT have implicit index signatures, so `interface Foo { a: string }` doesn't satisfy `Record<string, unknown>`. Required converting 11 types from `interface` to `type` (7 entry data types + 4 form value types). New lesson recorded.
- JSON.parse validation uses `const parsed: unknown = JSON.parse(str)` + shape checks — avoids `as` cast until shape is confirmed.
- useFetchData fix uses runtime `typeof response.data === 'object' && 'error' in response.data` to narrow before accessing error fields. No `as` cast needed for the error path.
- Total: 23 files modified, 5 `any` types eliminated, 6 non-null assertions removed, 3 JSON.parse sites validated, 2 type assertions replaced with runtime narrowing

---

#### Sprint 228: Return Type Annotations (33 Exported Functions)
> **Goal:** Add explicit return types to all exported hooks, providers, and utilities

**Hooks (High Priority — 10 functions):**
- [ ] `useTrialBalanceAudit()` — define and apply return type interface
- [ ] `useSettings()` — define and apply return type interface
- [ ] `useFileUpload()` — define and apply return type interface
- [ ] `useActivityHistory()` — apply existing `UseActivityHistoryReturn` interface
- [ ] `useAuth()` — define and apply return type interface
- [ ] `useMappings()` — apply existing `MappingContextValue` interface
- [ ] `useDiagnostic()` — apply existing `DiagnosticContextType`
- [ ] `useEngagementContext()` — apply existing `EngagementContextType`
- [ ] `useBatchUploadContext()` — apply existing `BatchUploadContextType`
- [ ] `useStatementBuilder()` — define and apply return type interface

**Providers (Medium Priority — 6 functions):**
- [ ] `AuthProvider` → `: JSX.Element`
- [ ] `MappingProvider` → `: JSX.Element`
- [ ] `EngagementProvider` → `: JSX.Element`
- [ ] `DiagnosticProvider` → `: JSX.Element`
- [ ] `BatchUploadProvider` → `: JSX.Element`
- [ ] `ThemeProvider` → `: JSX.Element`
- [ ] `Providers` (app/providers.tsx) → `: JSX.Element`

**Utilities (Lower Priority — 17 functions):**
- [ ] `constants.ts` — `minutes()`, `hours()` → `: number`
- [ ] `multiPeriod/constants.ts` — `formatCurrency()` → `: string`
- [ ] `EmptyStateCard.tsx` — `ChartIcon`, `TrendIcon`, `IndustryIcon`, `RollingIcon` → `: JSX.Element`
- [ ] Remaining exported component functions without return types

- [ ] `npm run build` passes

**Review:**
- _Sprint 228 review notes go here_

---

#### Sprint 229: Optional Chaining Cleanup
> **Goal:** Remove 40+ unnecessary optional chains that mask type modeling issues

**`File.name` False Optionality (8 tool pages):**
- [ ] Remove `?.` from `selectedFile?.name?.replace(...)` in:
  - `bank-rec/page.tsx` (2 sites)
  - `ar-aging/page.tsx`
  - `ap-testing/page.tsx`
  - `inventory-testing/page.tsx`
  - `payroll-testing/page.tsx`
  - `revenue-testing/page.tsx`
  - `fixed-assets/page.tsx`
- [ ] Guard at `selectedFile` level only (it can be null), not at `.name` (always string on File)

**MappingContext Narrowing:**
- [ ] `MappingContext.tsx` — replace 5 `existing?.` chains with early return `if (!existing) return`

**Login Page User Narrowing:**
- [ ] `login/page.tsx:144` — narrow `user` once with guard, remove redundant `user?.name || user?.email?.split(...)`

**Remaining Tool Page Result Chains:**
- [ ] Verify Sprint 226 hook return narrowing eliminated `result?.` chains in 7 tool pages
- [ ] Clean up any remaining `?.` that Sprint 226 discriminated unions should have resolved

**ESLint Rule (Optional):**
- [ ] Consider adding `@typescript-eslint/no-unnecessary-condition` to catch future unnecessary optional chains

- [ ] `npm run build` passes

**Review:**
- _Sprint 229 review notes go here_

---

#### Sprint 230: Phase XXX Wrap — Regression + Documentation
> **Goal:** Full regression, verify zero `any` in production, update documentation

**Regression:**
- [ ] `npm run build` passes
- [ ] `pytest` passes (no backend changes expected, but verify)
- [ ] Run frontend tests: `npm test`
- [ ] Grep for remaining `any` in production code (should be 0, excluding test mocks)
- [ ] Grep for `as unknown as` double-casts (should be 0)
- [ ] Grep for `data!.` non-null assertions (should be 0 or justified)
- [ ] Count remaining optional chains — document reduction

**Documentation:**
- [ ] Archive sprint details to `tasks/archive/phase-xxx-details.md`
- [ ] Add one-line summary to `## Completed Phases`
- [ ] Update CLAUDE.md: add Phase XXX to completed list
- [ ] Update MEMORY.md: project status

**Review:**
- _Sprint 230 review notes go here_

---

#### Known Issue: 22 Pre-Existing Frontend Test Failures

> **Introduced in:** Sprint 207 (Phase XXVII — Next.js App Router Hardening)
> **Root cause:** Architectural mismatch between tests and layout refactor
> **Impact:** 22 of 128 frontend tests fail (11 suites × 2 tests each)
> **Severity:** Low — all 106 passing tests cover actual page behavior; failing tests assert on layout concerns

**What happened:**
Sprint 207 moved `ToolNav` and `VerificationBanner` from individual tool pages into the shared layout (`app/tools/layout.tsx`). The 11 tool page test files were not updated:

- Tests mock `@/components/shared` (ToolNav) and `@/components/auth` (VerificationBanner)
- Pages no longer import from these modules — the mocks never execute
- Tests assert on `data-testid="tool-nav"` and `data-testid="verification-banner"` which don't render

**Failing test suites (all in `__tests__/`):**
APTestingPage, ARAgingPage, BankRecPage, FixedAssetTestingPage, InventoryTestingPage,
JournalEntryTestingPage, MultiPeriodPage, PayrollTestingPage, RevenueTestingPage,
ThreeWayMatchPage, TrialBalancePage

**Each suite fails exactly 2 tests:**
1. `renders tool navigation` — expects `[data-testid="tool-nav"]`
2. `shows verification banner for unverified user` — expects `[data-testid="verification-banner"]`

**Fix options (choose one):**
- **Option A (Recommended):** Remove the 22 stale assertions from page tests + create a dedicated `ToolsLayout.test.tsx` that tests layout-level concerns (ToolNav, VerificationBanner, EngagementProvider). Net result: fewer tests, but accurate coverage.
- **Option B:** Wrap page renders in `<ToolsLayout>` in each test — but this requires mocking `usePathname`, `EngagementProvider`, and all layout deps (fragile).
- **Option C:** Just delete the 22 assertions. The layout is implicitly tested via integration/E2E.
