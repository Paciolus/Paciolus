# Sprints 646–650 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 646: PeriodFileDropZone Deferred Item Tracking
**Status:** COMPLETE
**Source:** Project Auditor — 3 consecutive audit mention
**File:** `frontend/src/components/multiPeriod/PeriodFileDropZone.tsx:10`, `tasks/todo.md` Deferred Items table
**Problem:** `// TODO: type as AuditResult after full migration` had appeared in three consecutive audits without being added to the Deferred Items table. Untracked deferrals are a tracking liability.
**Changes:**
- [x] Add row to Deferred Items table: `| PeriodFileDropZone type migration | Full AuditResult typing deferred until multi-period migration completes | Sprint 596+ |`

**Review:**
- Row added to the Deferred Items table in the same commit that opens the 646–650 sweep.
- Resolved within the same sweep by Sprint 647 — the row is removed in that sprint's commit so the Deferred Items table doesn't carry a stale tracker for work already delivered.

---

### Sprint 647: PeriodFileDropZone AuditResult Type Migration
**Status:** COMPLETE
**Source:** Executor — type-safety escape hatch
**File:** `frontend/src/components/multiPeriod/PeriodFileDropZone.tsx:10`, `frontend/src/app/tools/multi-period/page.tsx`
**Problem:** `result: Record<string, unknown> | null` forced `as unknown as AuditResult` casts in 6 places. Type-unsafe.
**Changes:**
- [x] Change property type to `AuditResult | null`
- [x] Remove all 6 cast sites
- [x] Update consumers to use typed access

**Review:**
- `PeriodState.result` is now `AuditResult | null`.
- All 6 `as unknown as AuditResult` casts removed from `app/tools/multi-period/page.tsx` (lines 116, 117, 122, 135, 136, 141) plus the adjacent `response.data as Record<string, unknown>` cast at line 85 (replaced with a single `as AuditResult`).
- `useMultiPeriodComparison` already expected `AuditResult` (`AuditResultForComparison = AuditResult` per Sprint 573), so the signature is now honest.
- Test fixture at `__tests__/PeriodFileDropZone.test.tsx:13` changed `result: {}` to `result: null` — the component never reads `result`, and `{}` no longer satisfies `AuditResult`.
- Deferred Items table row added in Sprint 646 removed in this sprint's commit now that the underlying item is resolved.

---

### Sprint 648: useTrialBalanceUpload Error Response Typing
**Status:** COMPLETE
**Source:** Executor — error shape untyped
**File:** `frontend/src/hooks/useTrialBalanceUpload.ts`, `frontend/src/types/diagnostic.ts`
**Problem:** `data as unknown as Record<string, string>` on the error path — typed as `AuditResultResponse` elsewhere, double-cast indicated an untyped error response.
**Changes:**
- [x] Add discriminated union for success vs error response
- [x] Replace the cast with a type guard
- [x] Apply pattern to other hooks with similar escape hatches

**Review:**
- `AuditErrorResponse` added to `types/diagnostic.ts`: `{ status: 'error' | string; message?; detail? }`.
- `AuditRunResponse = AuditResultResponse | AuditErrorResponse` discriminated by `status`.
- `isAuditErrorResponse(data)` type-guard added alongside the types for reuse.
- `useTrialBalanceUpload` now narrows `result.data as AuditRunResponse` via the guard rather than double-casting. Success branch binds a `const success: AuditResultResponse` so downstream property access (`success.abnormal_balances`, `success.row_count`, etc.) is statically typed.
- Repo-wide grep for the same double-cast pattern (`as unknown as Record<string, string>`) found only this one site, so the pattern is applied fully.

---

### Sprint 649: Export Filename Context
**Status:** COMPLETE
**Source:** Scout — 10 identical `Paciolus_Report.pdf` downloads
**File:** `frontend/src/components/export/DownloadReportButton.tsx`, `frontend/src/components/preflight/PreFlightSummary.tsx`, `frontend/src/components/trialBalance/AccrualCompletenessSection.tsx`, new `frontend/src/utils/exportFilenames.ts`
**Problem:** Default filename was `Paciolus_Report.pdf`. A CPA running 10 engagements in a day would end up with 10 identical filenames in their Downloads folder. Also: no adjacent micro-copy explaining what each export contains.
**Changes:**
- [x] Dynamic filename: `Paciolus_<Tool>_<Client>_<YYYYMMDD>.pdf`
- [x] Micro-copy under each export button: "PDF — full diagnostic memo" / "CSV — raw findings"

**Review:**
- New `utils/exportFilenames.ts::buildExportFilename({ tool, client?, extension?, date? })` emits `Paciolus_<Tool>[_<Client>]_<YYYYMMDD>.<ext>`. Slugifies unsafe characters, drops blank clients cleanly, caps client slugs at 40 chars, defaults the extension to `pdf`, and exposes a `date` override for deterministic tests.
- `DownloadReportButton` accepts new optional `toolName` (default `'TB_Diagnostic'`) and `clientName` props. The server-supplied filename from `/export/pdf` still wins; the dynamic builder only kicks in as the fallback.
- Micro-copy added beneath the export button: `PDF — full diagnostic memo`, with the Zero-Storage reassurance retained below it.
- `PreFlightSummary`: wrapped the two export buttons in a column with `PDF — pre-flight summary memo • CSV — raw issue list` hint.
- `AccrualCompletenessSection`: wrapped its two export buttons the same way with `PDF — accrual completeness memo • CSV — flagged account list`.
- `clientName` is left optional — plumbing it through engagement context is out of scope for this sprint; the builder handles the absent case cleanly. When a future sprint passes it in, filenames upgrade automatically.
- Tests: 8 cases in `__tests__/exportFilenames.test.ts` covering the happy path, client slugification, extension override, empty-client and empty-tool fallbacks, and the 40-char cap.

---

### Sprint 650: PricingComparison Duplicate Render Cleanup
**Status:** COMPLETE
**Source:** Designer — duplicated table markup
**File:** `frontend/src/app/(marketing)/pricing/page.tsx`, `frontend/src/components/pricing/PricingComparison.tsx`
**Problem:** Pricing page rendered an inline comparison table identical to the `PricingComparison` component, resulting in two separate `min-w-[700px]` tables on the same page and four stale local definitions (`CellValue`, `ComparisonRow`, `comparisonRows`, `CellContent`).
**Changes:**
- [x] Delete inline duplicate, render `<PricingComparison />` in its place
- [x] Add CSS fade-edge scroll hint on the overflow container

**Review:**
- `pricing/page.tsx` now imports `PricingComparison` and renders it inside the Feature Comparison section. Saves ~50 lines in the page body.
- Local duplicates (`CellValue`, `ComparisonRow`, `comparisonRows`, `CellContent`) removed. The canonical data source is `@/domain/pricing.comparisonRows`, which `PricingComparison` already uses.
- Fade-edge scroll hint added to the shared component: `[mask-image:linear-gradient(to_right,transparent,black_16px,black_calc(100%-16px),transparent)]` on the overflow container with `md:[mask-image:none]` so desktop viewports render without the fade. An `sr-only` scroll hint sits alongside for screen readers.
- `npm run build` + full `jest` suite (1,766 tests) green. The project-wide lint warning on `dashboard/page.tsx:177` is pre-existing (Sprint 622), not introduced here; the lint-staged gate only lints touched files.

---
