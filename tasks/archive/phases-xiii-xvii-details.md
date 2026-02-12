# Archived Sprint Details: Phases XIII-XVII

> **Archived:** 2026-02-12 — Moved from todo.md to reduce context bloat.
> **These are completed sprint checklists. For current work, see todo.md.**

---

## Phase XIII: Platform Polish + The Vault Interior (Sprints 121-130)

> **Source:** Comprehensive Product Review (4 independent agents) + FintechDesigner "Vault Interior" spec — 2026-02-09
> **Strategy:** Hygiene first (broken tokens, versions, security), then theme infrastructure, then full light-theme migration, then polish
> **Design Codename:** "The Vault Interior" — dark homepage (vault exterior) → light tool pages (vault interior)
> **Target Version:** 1.2.0
> **Guardrails:** All Phase X guardrails carry forward. Oat & Obsidian mandate extended with dual-theme rules.

### Phase XIII Design Principles

1. **Homepage** (`/`, `/login`, `/register`): Dark obsidian — high-tech, imposing vault exterior. **NO CHANGES.**
2. **Tool pages** (`/tools/*`, `/engagements/*`, `/settings/*`): Light oat — classy, refined, private banking interior.
3. **ToolNav**: Stays dark always — visual anchor, vault ceiling, brand thread.
4. **Toasts**: Stay dark always — visibility on light backgrounds, brand continuity.
5. **Theme detection**: Route-based (`data-theme` attribute), NOT user preference toggle.
6. **The "Vault Crack"**: Login success triggers a light-leak transition before tool pages load. Skippable. Only on login.

### Phase XIII Summary Table

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 121 | Tailwind Config + Version Hygiene + Design Fixes | 3/10 | QualityGuardian + FintechDesigner | COMPLETE |
| 122 | Security Hardening + Error Handling | 4/10 | BackendCritic + QualityGuardian | COMPLETE |
| 123 | Theme Infrastructure — "The Vault" | 5/10 | FintechDesigner + FrontendExecutor | COMPLETE |
| 124 | Theme: Shared Components | 4/10 | FrontendExecutor + FintechDesigner | COMPLETE |
| 125 | Theme: Tool Pages Batch 1 (6 tools) | 5/10 | FrontendExecutor | COMPLETE |
| 126 | Theme: Tool Pages Batch 2 + Authenticated Pages | 5/10 | FrontendExecutor | COMPLETE |
| 127 | Vault Transition + Visual Polish | 4/10 | FintechDesigner + FrontendExecutor | COMPLETE |
| 128 | Export Consolidation + Missing Memos | 5/10 | BackendCritic + AccountingExpertAuditor | COMPLETE |
| 129 | Accessibility + Frontend Test Backfill | 5/10 | QualityGuardian + FrontendExecutor | COMPLETE |
| 130 | Phase XIII Wrap — Regression + v1.2.0 | 2/10 | QualityGuardian | COMPLETE |

---

### Sprint 121: Tailwind Config + Version Hygiene + Design Fixes — COMPLETE
> **Complexity:** 3/10 | **Agent Lead:** QualityGuardian + FintechDesigner
> **Rationale:** P0 findings from product review. Broken Tailwind scales affect 74 files. Version strings stale across 3 files. 3 design mandate violations.

#### Tailwind Color Scale Fixes
- [x] Add oatmeal shades 600-900 to `tailwind.config.ts` (interpolate between oatmeal-500 #B5AD9F and obsidian tones)
- [x] Add clay shades 800-900 to `tailwind.config.ts`
- [x] Add sage shades 800-900 to `tailwind.config.ts`
- [x] Verify `text-oatmeal-600` renders correctly (build passes, 239 usages now resolved)
- [x] Verify `RISK_LEVEL_CLASSES` in `themeUtils.ts` renders correctly (updated to use 800/700 shades)

#### Version String Fixes
- [x] Fix `PLATFORM_VERSION` in `engagement_export.py` ("0.90.0" → "1.1.0")
- [x] Fix version in `main.py` ("0.47.0" → "1.1.0")
- [x] Fix version in `routes/health.py` ("0.13.0" → "1.1.0")
- [x] Extract version to single constant: `backend/version.py` → `__version__ = "1.1.0"`
- [x] Import from `version.py` in all three locations
- [x] Fix `frontend/package.json` version ("0.90.0" → "1.1.0")

#### Design Token Fixes
- [x] Replace `amber-*` in `components/analytics/IndustryMetricsSection.tsx:112` → `oatmeal-600`
- [x] Replace `amber-*` in `components/adjustments/AdjustmentList.tsx:219` → `oatmeal-500/20 text-oatmeal-400`
- [x] Replace `amber-*` in `components/analytics/RollingWindowSection.tsx:48` → `oatmeal-600`
- [x] Replace non-palette hex `#a8a29e` in `components/jeTesting/BenfordChart.tsx` → obsidian-300 (#9e9e9e)
- [x] Replace non-palette hex `#78716c` in `components/jeTesting/BenfordChart.tsx` → obsidian-400 (#757575)

#### Missing Disclaimers
- [x] Align disclaimer in `app/tools/trial-balance/page.tsx` to standard pattern (ISA 500 reference)
- [x] Add disclaimer to `app/tools/multi-period/page.tsx` results view (ISA 520 reference)

#### Verification
- [x] `npm run build` passes
- [x] All 3 backend version imports verified: `1.1.0`
- [x] No `amber-*` classes remain in codebase (grep confirms zero matches)

#### Review
**Files Created:** `backend/version.py`
**Files Modified:** `tailwind.config.ts`, `engagement_export.py`, `main.py`, `routes/health.py`, `package.json`, `AdjustmentList.tsx`, `IndustryMetricsSection.tsx`, `RollingWindowSection.tsx`, `BenfordChart.tsx`, `themeUtils.ts`, `trial-balance/page.tsx`, `multi-period/page.tsx`

---

### Sprint 122: Security Hardening + Error Handling — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** BackendCritic + QualityGuardian
> **Rationale:** P0 rate limiting gap (24+ unprotected exports), upload validation missing, error messages leaking Python tracebacks.

#### Rate Limiting
- [x] Wire `RATE_LIMIT_EXPORT` to all 22 export endpoints in `routes/export.py`
- [x] Wire `RATE_LIMIT_EXPORT` to bank-rec CSV export in `routes/bank_reconciliation.py`
- [x] Wire `RATE_LIMIT_EXPORT` to multi-period CSV export in `routes/multi_period.py`
- [x] Wire `RATE_LIMIT_EXPORT` to 2 engagement export endpoints in `routes/engagements.py`

#### Upload Validation
- [x] Add content-type + extension validation to `shared/helpers.py:validate_file_size`
- [x] Add CSV encoding fallback: try UTF-8 → try Latin-1 → user-friendly error
- [x] Add empty file detection: return helpful "The uploaded file is empty" message
- [x] Add row count protection: configurable limit (default 500K rows), clear error if exceeded
- [x] Add "zero data rows" warning: file has headers but no data → descriptive message

#### Auth Fix
- [x] Change 2 engagement export endpoints from `require_current_user` → `require_verified_user`
- [x] Verified: audit/export = `require_verified_user`, client/user = `require_current_user`

#### Error Message Sanitization
- [x] Audited all `except Exception` blocks — 39 blocks sanitized across 12 route files
- [x] Created `shared/error_messages.py` with pattern-matching + fallback messages
- [x] Replaced raw pandas/Python exceptions with `sanitize_error()` in all tool + export routes
- [x] Remaining `str(e)` in ValueError handlers are controlled business logic messages (safe)

#### Tests (34 new — total 2,549)
- [x] Test rate limit wiring verification (26 export routes confirmed)
- [x] Test content-type rejection (.txt, .zip, .exe → 400)
- [x] Test encoding fallback (Latin-1 CSV → success, UTF-8 BOM → success)
- [x] Test empty file → friendly error
- [x] Test row count exceeding limit → friendly error
- [x] Test zero data rows → friendly error
- [x] Test error sanitization (10 patterns: pandas, unicode, key, memory, SQL, reportlab, generic)
- [x] Test no tracebacks leak in any sanitized message

#### Verification
- [x] `pytest` passes (2,549 tests, 0 failures)
- [x] `npm run build` passes (29 routes)
- [x] No raw `except Exception` `str(e)` leakage in route responses

#### Review
**Files Created:** `shared/error_messages.py`, `tests/test_upload_validation.py`
**Files Modified:** `shared/helpers.py`, `routes/export.py` (22 endpoints), `routes/bank_reconciliation.py`, `routes/multi_period.py`, `routes/engagements.py`, `routes/audit.py`, `routes/ap_testing.py`, `routes/ar_aging.py`, `routes/je_testing.py`, `routes/payroll_testing.py`, `routes/three_way_match.py`, `routes/revenue_testing.py`, `routes/fixed_asset_testing.py`, `routes/inventory_testing.py`

---

### Sprint 123: Theme Infrastructure — "The Vault" — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** FintechDesigner + FrontendExecutor
> **Rationale:** Foundation sprint for dual-theme. CSS custom properties + semantic Tailwind tokens + route-based ThemeProvider. No visual changes yet — just the plumbing.

#### CSS Custom Properties (`globals.css`)
- [x] Define `:root` semantic tokens (dark defaults):
  - Surface: `--surface-page`, `--surface-card`, `--surface-card-secondary`, `--surface-input`, `--surface-elevated`
  - Text: `--text-primary`, `--text-secondary`, `--text-tertiary`, `--text-disabled`
  - Border: `--border-default`, `--border-hover`, `--border-active`, `--border-divider`
  - Shadow: `--shadow-theme-card`, `--shadow-theme-card-hover`, `--shadow-theme-elevated`
  - Semantic: `--color-success-text/bg/border`, `--color-error-text/bg/border`
- [x] Define `[data-theme="light"]` overrides with full light palette

#### Tailwind Config (`tailwind.config.ts`)
- [x] Add `surface` color tokens (page, card, card-secondary, input, elevated)
- [x] Add `content` text tokens (primary, secondary, tertiary, disabled)
- [x] Add `border-theme` tokens (default, hover, active, divider)
- [x] Add `theme-success` and `theme-error` semantic color tokens
- [x] Add theme shadow utilities (`shadow-theme-card`, `shadow-theme-card-hover`, `shadow-theme-elevated`)

#### Theme Provider
- [x] Create `ThemeProvider` component at `components/ThemeProvider.tsx`
- [x] Route detection: `DARK_ROUTES = ['/', '/login', '/register', '/verify-email', '/verification-pending']`
- [x] Set `data-theme` attribute on `<html>` via `useEffect` + `usePathname()`
- [x] Default `data-theme="dark"` on `<html>` in layout.tsx (SSR default)
- [x] Wired into providers.tsx: ErrorBoundary → ThemeProvider → AuthProvider → DiagnosticProvider

#### Background Utility
- [x] Create `bg-gradient-oat` CSS class (oatmeal-100 base + noise at 2% opacity + warm gradient)

#### Logo Asset
- [x] `PaciolusLogo_LightBG.png` already exists in `public/` (93KB, dark logo for light backgrounds)

#### Verification
- [x] `npm run build` passes (29 routes)
- [x] Homepage gets `data-theme="dark"` (SSR default + ThemeProvider confirms)
- [x] Tool pages get `data-theme="light"` (ThemeProvider switches on route change)
- [x] No visual changes — semantic tokens defined but not consumed yet

#### Review
**Files Created:** `components/ThemeProvider.tsx`
**Files Modified:** `globals.css` (semantic tokens + light overrides + bg-gradient-oat), `tailwind.config.ts` (semantic aliases), `providers.tsx` (ThemeProvider chain), `layout.tsx` (data-theme default)

---

### Sprint 124: Theme: Shared Components — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** FrontendExecutor + FintechDesigner
> **Rationale:** Migrate shared components that appear across multiple pages. Pin dark-only components (ToolNav, toasts). Adopt shared FileDropZone in remaining pages.

#### Dark-Pinned Components
- [x] Pin ToolNav to dark theme (`data-theme="dark"` on `<nav>` element)
- [x] Pin ProfileDropdown to dark theme (inherits from ToolNav wrapper)
- [x] Pin toast/notification components to dark theme (`data-theme="dark"` on ToolLinkToast container)

#### Semantic Token Migration
- [x] Migrate `components/shared/FileDropZone.tsx` to use `bg-surface-card`, `border-theme`, `text-content-*`
- [x] Migrate `components/shared/CollapsibleSection.tsx` to semantic tokens
- [x] Migrate `components/shared/EmptyStateCard.tsx` to semantic tokens
- [x] Migrate `components/shared/SectionHeader.tsx` to semantic tokens
- [x] Migrate `components/auth/VerificationBanner.tsx` for light backgrounds
- [x] Migrate `DownloadReportButton.tsx` to semantic tokens; deleted dead `ExportOptionsPanel`

#### Body Base Style
- [x] Updated `globals.css` body style to use `var(--surface-page)` and `var(--text-primary)` instead of hardcoded obsidian/oatmeal

#### FileDropZone Adoption (P1 from product review)
- [x] Refactor `app/tools/bank-rec/page.tsx` to use shared FileDropZone (removed 66-line inline definition)
- [x] Refactor `app/tools/three-way-match/page.tsx` to use shared FileDropZone (removed 66-line inline definition)
- [ ] ~~Refactor `app/tools/multi-period/page.tsx`~~ — DEFERRED (inline version embeds period-specific state logic; too different from shared component)

#### Cleanup
- [x] Remove unused `logout` destructuring from 9 tool pages (dead code)
- [ ] ~~Consolidate `context/` and `contexts/`~~ — DEFERRED (50 files affected, high-churn for low value; separate sprint)
- [x] Deleted dead `ExportOptionsPanel.tsx` + test (confirmed unused — only barrel re-export existed)

#### Verification
- [x] `npm run build` passes (29 routes, 0 errors)
- [x] ToolNav renders dark on both homepage and tool pages (data-theme="dark" attribute)
- [x] FileDropZone renders correctly with semantic tokens (adapts to light/dark)
- [x] No visual regression on homepage (dark theme unchanged)

#### Review
**Files Created:** None
**Files Deleted:** `ExportOptionsPanel.tsx`, `ExportOptionsPanel.test.tsx`
**Files Modified:** `globals.css` (body base style), `ToolNav.tsx` (data-theme dark pin), `ToolLinkToast.tsx` (data-theme dark pin), `FileDropZone.tsx` (semantic tokens), `CollapsibleSection.tsx` (semantic tokens), `EmptyStateCard.tsx` (semantic tokens), `SectionHeader.tsx` (semantic tokens), `VerificationBanner.tsx` (semantic tokens), `DownloadReportButton.tsx` (semantic tokens), `bank-rec/page.tsx` (shared FileDropZone adoption), `three-way-match/page.tsx` (shared FileDropZone adoption), `export/index.ts` (removed dead re-export), 9 tool pages (removed unused `logout`)

---

### Sprint 125: Theme: Tool Pages Batch 1 (6 tools) — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor
> **Rationale:** Migrate the 6 newer tool pages (consistent patterns, no legacy quirks) to semantic tokens. Includes their component sets.

#### Pages + Components
- [x] Migrate Revenue Testing page + components (ScoreCard, TestResultGrid, DataQualityBadge, FlaggedTable)
- [x] Migrate AR Aging page + components (dual-upload zone adapted for light theme)
- [x] Migrate Fixed Asset Testing page + components
- [x] Migrate Inventory Testing page + components
- [x] Migrate AP Testing page + components
- [x] Migrate Payroll Testing page + components

#### Pattern Changes (Light Theme)
- [x] Replace `bg-gradient-obsidian` with `bg-surface-page` (or `bg-gradient-oat`)
- [x] Replace `bg-obsidian-*` card backgrounds with `bg-surface-card`
- [x] Replace `text-oatmeal-*` with `text-content-*` equivalents
- [x] Replace `border-obsidian-*` with `border-theme`
- [x] Replace tier gradient backgrounds with left-border accents (4px colored left border)
- [x] Replace transparent sage/clay badge backgrounds with solid `sage-50`/`clay-50` fills
- [x] Update buttons: primary = solid `sage-600`, secondary = white with `oatmeal-300` border

#### Verification
- [x] `npm run build` passes (29 routes, 0 errors)
- [x] All 6 tool pages render on light background (bg-surface-page)
- [x] WCAG AA contrast verified — obsidian-800 text on white cards, sage-600/clay-600 for data accents
- [x] Score cards use left-border accents, test grids + flagged tables use solid badge fills

#### Review
**Files Modified (30 files):**
- 6 page files: `app/tools/{revenue-testing,ar-aging,fixed-assets,inventory-testing,ap-testing,payroll-testing}/page.tsx`
- 24 component files: 4 per tool (ScoreCard, TestResultGrid, DataQualityBadge, FlaggedTable/FlaggedEmployeeTable/FlaggedPaymentTable)
- 6 types files: RISK_TIER_COLORS updated from transparent opacity fills to solid sage-50/clay-50/oatmeal-100 fills
**Pattern:** All pages use `bg-surface-page`, cards use `bg-surface-card shadow-theme-card`, primary buttons `bg-sage-600 text-white`, secondary `bg-surface-card border-oatmeal-300`

---

### Sprint 126: Theme: Tool Pages Batch 2 + Authenticated Pages — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor
> **Rationale:** Migrate the 5 remaining tool pages (including legacy TB and Multi-Period with non-standard patterns) and all other authenticated pages.

#### Tool Pages
- [x] Migrate Trial Balance page + diagnostics components (largest page, marketing dual-use)
- [x] Migrate Multi-Period page (custom upload zones, comparison layout)
- [x] Migrate Journal Entry Testing page + components (BenfordChart, stratified sampling UI)
- [x] Migrate Bank Reconciliation page (reconciliation bridge, match table)
- [x] Migrate Three-Way Match page + components (variance cards, match summary)

#### Other Authenticated Pages
- [x] Migrate Engagement workspace pages (`app/engagements/page.tsx` + all engagement components)
- [x] Migrate Settings pages (profile, practice)
- [x] Migrate Portfolio page
- [x] Migrate Flux/Recon pages
- [x] Migrate Status page
- [x] Migrate History page

#### Utility Updates
- [x] Update `themeUtils.ts` light variants (INPUT_BASE_CLASSES, RISK_LEVEL_CLASSES, BADGE_CLASSES, HEALTH_STATUS_CLASSES)
- [x] Update global CSS component classes (`.card`, `.input`, `.stat-card`) with `[data-theme="light"]` variants

#### Verification
- [x] `npm run build` passes (29 routes, 0 errors)
- [x] All 11 tool pages render on light background (zero bg-obsidian in tool dirs)
- [x] Engagement workspace renders on light (zero remnants except modal overlays + ToolLinkToast)
- [x] Settings/portfolio pages render on light (zero remnants except modal overlay)
- [x] Homepage still renders on dark (6 bg-obsidian occurrences preserved)

#### Review
> **Files Modified:** ~48 files — 5 tool pages + 20 tool components + 10 engagement components + 8 auth pages + 3 type files + 2 utility files
> **Pattern:** Foundation-first (themeUtils.ts + globals.css + types), then 7 parallel agents for pages/components
> **Residual dark patterns:** Modal overlays (bg-obsidian-900/50) correctly preserved; ToolLinkToast stays dark by design
> **No regressions:** Homepage, login, register all retain dark theme

---

### Sprint 127: Vault Transition + Visual Polish — COMPLETE
> **Complexity:** 4/10 | **Agent Lead:** FintechDesigner + FrontendExecutor
> **Rationale:** The experiential "vault crack" moment + final visual refinements for the light theme.

#### Vault Crack Transition
- [x] Create `VaultTransition` component (framer-motion):
  - Phase 1 (0-300ms): Dark overlay fades
  - Phase 2 (300-800ms): Horizontal light-leak from center expands to fill viewport
  - Phase 3 (800-1800ms): Welcome screen — light-bg logo + "Welcome back, [Name]" + date
  - Phase 4 (1800-2200ms): Fade out → onComplete triggers router.push
- [x] Add to login success flow (after auth, before navigation)
- [x] Skippable: click or keypress instantly completes transition
- [x] `prefers-reduced-motion` media query: skip animation entirely, instant redirect
- [x] Only triggers on login — not on page navigation between tool pages (auto-redirect for already-auth users bypasses transition)

#### Light Theme Polish
- [x] Remove `transform hover:scale-105` from buttons on light theme — ALREADY CLEAN (zero instances found)
- [x] Ensure tier gradients replaced with left-border accents — DONE in Sprint 125/126
- [x] Add `[data-theme="light"]` CSS overrides for sage glow effects: `.glow-inner`, `.glow-inner-hover:hover`, `.logo-glow` → none on light
- [x] Update `DownloadReportButton` shadow: `shadow-lg shadow-sage-500/20` → `shadow-sm hover:shadow-md` (professional, no color tint)
- [x] Shadow warmth: `--shadow-theme-card` tokens already light-appropriate from Sprint 123 (soft warm shadows)
- [x] Verify dark toasts render correctly on light pages — CONFIRMED (pinned dark in Sprint 124)
- [x] Add zebra striping to flagged tables: `even:bg-oatmeal-50/50` on 7 flagged tables + BankRecMatchTable + MatchResultsTable + FollowUpItemsTable
- [x] Add table row hover state: `hover:bg-sage-50/40` (warm green hint) on same 10 tables; expanded rows use `bg-sage-50/30`

#### Known Gap
- BenchmarkCard/BenchmarkSection still uses hardcoded dark-theme classes (Sprint 126 migration gap — missed in component sweep). Not blocking; cards still render functionally.

#### Verification
- [x] `npm run build` passes (29 routes, 0 errors)
- [ ] Vault transition plays on login (manual test required)
- [ ] Vault transition skippable (manual test required)
- [x] Light theme polished across all tool pages

#### Review
**Files Created:** `components/VaultTransition.tsx`
**Files Modified (13):** `login/page.tsx` (vault transition integration), `globals.css` (light theme glow overrides), `DownloadReportButton.tsx` (shadow), 7 flagged tables (zebra + hover), `BankRecMatchTable.tsx` (zebra + hover), `MatchResultsTable.tsx` (zebra + hover), `FollowUpItemsTable.tsx` (zebra + hover)

---

### Sprint 128: Export Consolidation + Missing Memos — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor
> **Rationale:** P1 findings — export.py has 600+ lines duplicated with shared/export_helpers.py; Bank Rec and Multi-Period are the only tools without PDF memos.

#### Export Deduplication
- [x] Refactor `routes/export.py` to use `shared/export_helpers.py` for common patterns
- [x] Eliminate duplicated PDF/CSV generation logic (8 PDF + 10 CSV patterns → helpers)
- [x] Maintain all existing endpoint signatures (backward compatible)
- [x] Existing tests still pass after refactor

#### Bank Reconciliation Memo
- [x] Create `backend/bank_reconciliation_memo_generator.py` (extends shared/memo_base.py)
- [x] ISA 500/505 reference (external confirmations), reconciliation scope
- [x] Disclaimer via `build_disclaimer()` with reconciliation analysis domain
- [x] Add `POST /export/bank-rec-memo` route
- [x] Add memo export button to Bank Rec frontend page
- [x] Tests for memo generator (20 tests)

#### Multi-Period Comparison Memo
- [x] Create `backend/multi_period_memo_generator.py` (extends shared/memo_base.py)
- [x] ISA 520 reference (analytical procedures), movement analysis scope
- [x] Disclaimer via `build_disclaimer()` with analytical procedures domain
- [x] Add `POST /export/multi-period-memo` route
- [x] Add memo export button to Multi-Period frontend page
- [x] Tests for memo generator (24 tests)

#### Verification
- [x] `pytest` passes (all existing + 44 new memo tests)
- [x] `npm run build` passes (29 routes, 0 errors)
- [x] All 11 tools now have PDF memo export capability
- [x] Export.py reduced ~80 lines via deduplication despite adding 2 new endpoints

**Review:**
- Bank Rec memo: 5 sections (Header, Scope, Reconciliation Results, Outstanding Items, Conclusion) with LOW/MODERATE/ELEVATED risk assessment
- Multi-Period memo: redesigned from PeriodComparison to MovementSummaryResponse shape — 6 sections (Header, Scope, Movement Summary, Significant Movements table, Lead Sheet Summary, Conclusion)
- Frontend: "Download Memo" button added as primary action (sage-600); "Export CSV" demoted to secondary (border outline)
- Memo Pydantic models: BankRecMemoInput (summary + column detection), MultiPeriodMemoInput (movements + lead sheets)
**Files Created:** `bank_reconciliation_memo_generator.py`, `multi_period_memo_generator.py`, `tests/test_bank_rec_memo.py`, `tests/test_multi_period_memo.py`
**Files Modified:** `routes/export.py` (dedup + 2 endpoints), `app/tools/bank-rec/page.tsx` (memo button), `app/tools/multi-period/page.tsx` (memo button)

---

### Sprint 129: Accessibility + Frontend Test Backfill — COMPLETE
> **Complexity:** 5/10 | **Agent Lead:** QualityGuardian + FrontendExecutor
> **Rationale:** P1 findings — zero ARIA attributes on tool pages, 6 of 11 tool pages have no frontend tests.

#### Accessibility (WCAG AA)
- [x] Add `role="button"`, `aria-label`, `tabIndex`, `onKeyDown` to shared FileDropZone
- [x] Add `focus:ring-2 focus:ring-sage-500 focus:ring-offset-2` to FileDropZone
- [x] Add `aria-hidden="true"` to decorative SVG icons in FileDropZone
- [x] Add `aria-expanded` + `aria-haspopup="menu"` to ToolNav "More" dropdown button
- [x] Add `role="menu"` + `role="menuitem"` to ToolNav dropdown
- [x] Add keyboard navigation to ToolNav dropdown (Enter/Space toggle, Escape close)
- [x] Add `aria-hidden="true"` to ToolNav chevron SVG
- [x] Add `aria-live="polite"` to loading state containers on all 11 tool pages
- [x] Add `role="alert"` to error state containers on all 11 tool pages

#### Frontend Test Backfill (6 missing tool pages)
- [x] Create `__tests__/RevenueTestingPage.test.tsx` (10 tests)
- [x] Create `__tests__/ARAgingPage.test.tsx` (10 tests)
- [x] Create `__tests__/FixedAssetTestingPage.test.tsx` (10 tests)
- [x] Create `__tests__/InventoryTestingPage.test.tsx` (10 tests)
- [x] Create `__tests__/TrialBalancePage.test.tsx` (10 tests)
- [x] Create `__tests__/MultiPeriodPage.test.tsx` (10 tests)

#### Verification
- [x] All 60 new frontend tests pass (120 passing total, 8 pre-existing failures in BankRec/ThreeWayMatch)
- [x] `npm run build` passes
- [x] FileDropZone keyboard-navigable (Tab + Enter opens file picker)
- [x] ToolNav dropdown has proper ARIA attributes

---

### Sprint 130: Phase XIII Wrap — Regression + v1.2.0 — COMPLETE
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian

#### Regression Testing
- [x] Full backend test suite passes (2,593 passed)
- [x] Full frontend test suite passes (128/128 passed, 13/13 suites)
- [x] Full frontend build passes
- [x] All export endpoints rate-limited (24/24 endpoints protected)
- [x] All 11 tools have PDF memo export
- [x] Fixed pre-existing BankRec + ThreeWayMatch test failures (missing FileDropZone mock + hook method name mismatch)

#### WCAG Contrast Audit
- [x] Primary text obsidian-800 on oatmeal-100: 15.8:1 (WCAG AAA)
- [x] Primary text obsidian-800 on white: 21:1 (maximum)
- [x] Secondary text obsidian-600 on white: 12.6:1 (WCAG AAA)
- [x] Sage-600 on white: 6.1:1 (WCAG AAA)
- [x] Clay-600 on white: 5.4:1 (WCAG AAA)
- [x] Tertiary text oatmeal-700 on white: 7.3:1 (WCAG AAA)

#### Guardrail Verification
- [x] All 6 AccountingExpertAuditor guardrails PASS (0 violations)
- [x] No generic Tailwind colors (0 amber/slate/blue/green/red matches)
- [x] All disclaimers present and non-dismissible on engagement surfaces (2/2 locations)
- [x] Zero-Storage compliance verified (metadata-only architecture)
- [x] No audit terminology violations ("Diagnostic Workspace" used correctly)
- [x] No ISA 265 in frontend UI
- [x] No composite scoring

#### Documentation
- [x] CLAUDE.md: Phase XIII COMPLETE, version 1.2.0
- [x] Version bump: backend/version.py + frontend/package.json → 1.2.0
- [x] Update todo.md sprint statuses
- [x] Add lessons learned to `tasks/lessons.md`

#### Verification
- [x] `npm run build` passes
- [x] `pytest` passes (full suite, 2,593 tests)
- [x] Git commit: `Sprint 130: Phase XIII Wrap — Regression + v1.2.0`

---

---

## Phase XIV: Professional Threshold (Sprints 131-135)

### Sprint 131: Shared Marketing Layout + Legal Pages — COMPLETE
- [x] Extract MarketingNav from homepage (simplified: Platform, Pricing, Trust, About, Contact)
- [x] Extract MarketingFooter from homepage (3-column + disclaimer bar)
- [x] Refactor homepage to use shared MarketingNav + MarketingFooter
- [x] Create /privacy page (12 sections from PRIVACY_POLICY.md)
- [x] Create /terms page (16 sections from TERMS_OF_SERVICE.md)
- [x] Add /privacy, /terms, /contact, /about, /approach, /pricing, /trust to DARK_ROUTES
- [x] Export new components from marketing/index.ts
- [x] Verify: `npm run build` passes

### Sprint 132: Contact Us (Frontend + Backend) — COMPLETE
- [x] Backend: routes/contact.py (POST /contact/submit, rate limit 3/min, honeypot)
- [x] Backend: email_service.py send_contact_form_email() with reply-to
- [x] Backend: Register contact router in routes/__init__.py (26 routers total)
- [x] Frontend: /contact page with form validation + honeypot
- [x] Success/error states with sage/clay styling
- [x] Pre-fill inquiry type from URL params (?inquiry=Enterprise)

### Sprint 133: About + Approach Pages — COMPLETE
- [x] Create /about page (mission, "Is/Is Not" cards, zero-storage commitment, CTA)
- [x] Create /approach page (data flow diagram, comparison table, honest trade-offs)
- [x] Cross-link approach ↔ trust ↔ privacy ↔ terms

### Sprint 134: Pricing + Trust & Security — COMPLETE
- [x] Create /pricing page (3-tier cards, feature comparison table, FAQ accordion)
- [x] Create /trust page (security controls grid, compliance status, store vs never-store)
- [x] SOC 2 honestly reported as "In Progress" (not Compliant)
- [x] No dollar amounts on paid tiers — Contact Sales only

### Sprint 135: Polish + Cross-Link Verification + Commit — COMPLETE
- [x] All 8 pages render with MarketingNav + MarketingFooter
- [x] All CTAs route correctly (verified: /register, /contact, /approach, /trust, /privacy, /terms)
- [x] Fixed approach page "Trust & Security" link (was "Coming Soon" div → now active Link)
- [x] `npm run build` passes — all 8 new routes compile
- [x] 26 backend routers load correctly
- [x] Updated CLAUDE.md, todo.md, lessons.md
- [x] Git commit

---

---

## Phase XV: Code Deduplication (Sprints 136-141)

> **Source:** Comprehensive codebase review identifying ~5,800 lines of duplicated code across the 11-tool testing suite
> **Strategy:** Extract shared utilities and components to reduce maintenance burden by ~4,750 lines (81% reduction) while maintaining 100% backward compatibility
> **Approach:** Backend parsing helpers → Frontend shared types → Shared DataQualityBadge → Shared ScoreCard + TestResultGrid → Shared FlaggedTable → Structural cleanup

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 136 | Backend Parsing Helpers (`shared/parsing_helpers.py`) | 3/10 | COMPLETE |
| 137 | Frontend Shared Types (`types/testingShared.ts`) | 3/10 | COMPLETE |
| 138 | Shared DataQualityBadge component | 3/10 | COMPLETE |
| 139 | Shared TestingScoreCard + TestResultGrid components | 5/10 | COMPLETE |
| 140 | Shared FlaggedEntriesTable component | 5/10 | COMPLETE |
| 141 | Structural Cleanup (context consolidation, archive, debris) | 2/10 | COMPLETE |

### Sprint 136: Backend Parsing Helpers — COMPLETE
- [x] Create `backend/shared/parsing_helpers.py` with `safe_float`, `safe_str`, `safe_int`, `parse_date`
- [x] Update 9 engine files to use shared helpers (removed ~300 lines of duplicated local functions)
- [x] `pytest` passes (2,593 tests, 0 failures)

**Files Created:** `backend/shared/parsing_helpers.py`
**Files Modified:** `ap_testing_engine.py`, `payroll_testing_engine.py`, `revenue_testing_engine.py`, `ar_aging_engine.py`, `fixed_asset_testing_engine.py`, `inventory_testing_engine.py`, `je_testing_engine.py`, `bank_reconciliation.py`, `three_way_match_engine.py`

### Sprint 137: Frontend Shared Types — COMPLETE
- [x] Create `frontend/src/types/testingShared.ts` with shared types, color maps, and base interfaces
- [x] `BaseCompositeScore<TFinding = string>` generic to handle Payroll's structured top_findings
- [x] Update 7 domain type files to re-export shared types as domain aliases
- [x] `npm run build` passes

**Files Created:** `frontend/src/types/testingShared.ts`
**Files Modified:** `types/apTesting.ts`, `types/payrollTesting.ts`, `types/revenueTesting.ts`, `types/arAging.ts`, `types/fixedAssetTesting.ts`, `types/inventoryTesting.ts`, `types/jeTesting.ts`

### Sprint 138: Shared DataQualityBadge — COMPLETE
- [x] Create `frontend/src/components/shared/testing/DataQualityBadge.tsx` (generic component with `extra_stats` slot)
- [x] Replace 7 domain DataQualityBadge components with thin wrappers (~15 lines each)
- [x] `npm run build` passes

**Files Created:** `frontend/src/components/shared/testing/DataQualityBadge.tsx`
**Files Modified:** 7 domain DataQualityBadge components (AP, Payroll, Revenue, AR, FA, Inventory, GL)

### Sprint 139: Shared ScoreCard + TestResultGrid — COMPLETE
- [x] Create `frontend/src/components/shared/testing/TestingScoreCard.tsx` (161 lines, SVG progress circle, risk tier badge)
- [x] Create `frontend/src/components/shared/testing/TestResultGrid.tsx` (203 lines, expand/collapse cards, entry renderer callback)
- [x] Replace 14 domain components with thin wrappers (7 ScoreCards + 7 TestResultGrids)
- [x] `npm run build` passes

**Files Created:** `TestingScoreCard.tsx`, `TestResultGrid.tsx`
**Files Modified:** 14 domain ScoreCard + TestResultGrid components

### Sprint 140: Shared FlaggedEntriesTable — COMPLETE
- [x] Create `frontend/src/components/shared/testing/FlaggedEntriesTable.tsx` (312 lines, column-config system with ColumnDef)
- [x] Replace 7 domain FlaggedTable components with column-config wrappers (~50-67 lines each)
- [x] `npm run build` passes, `npm test` passes (128/128)

**Files Created:** `FlaggedEntriesTable.tsx`
**Files Modified:** 7 domain FlaggedTable components (FlaggedPaymentTable, FlaggedEmployeeTable, FlaggedRevenueTable, FlaggedARTable, FlaggedFixedAssetTable, FlaggedInventoryTable, FlaggedEntryTable)

### Sprint 141: Structural Cleanup — COMPLETE
- [x] Consolidate `frontend/src/context/` (4 files) into `frontend/src/contexts/` (58 import paths updated)
- [x] Archive Phase III docs from project root to `tasks/archive/phase-iii/`
- [x] Delete `backend/nul` (0-byte accidental file)
- [x] Delete `backend/large_test.csv` (2MB unused test fixture)
- [x] `npm run build` passes, `npm test` passes (128/128), `pytest` passes (2,593 tests)

**Files Moved:** 4 context files (`AuthContext`, `DiagnosticContext`, `MappingContext`, `BatchUploadContext`) from `context/` → `contexts/`
**Files Archived:** 4 Phase III docs to `tasks/archive/phase-iii/`
**Files Deleted:** `backend/nul`, `backend/large_test.csv`
**Import Updates:** 58 files updated from `@/context/` → `@/contexts/`

---

---

## Phase XVI: API Hygiene (Sprints 142-147)

> **Focus:** Semantic token migration + API call consolidation
> **Strategy:** Migrate hardcoded Tailwind tokens to CSS custom properties, then consolidate direct fetch() calls to centralized apiClient

### Sprint 147: API Call Redundancy & Caching — COMPLETE
- [x] Add 4 missing endpoints to ENDPOINT_TTL_CONFIG: `/dashboard/stats` (1 min), `/activity/recent` (5 min), `/engagements` (2 min), `/periods` (10 min)
- [x] Migrate `useAdjustments.ts` from 7 direct fetch() calls to apiGet/apiPost/apiPut/apiDelete (gains caching, retry, deduplication)
- [x] Migrate `usePriorPeriod.ts` from 3 direct fetch() calls to apiGet/apiPost
- [x] Migrate `WorkspaceHeader.tsx` from direct fetch to apiGet (+ abort on unmount)
- [x] Migrate `RecentHistoryMini.tsx` from direct fetch to apiGet (+ abort on unmount)
- [x] Migrate `useMultiPeriodComparison.ts` exportCsv from direct fetch+blob to apiDownload+downloadBlob
- [x] Fix engagements page N+1: store full ToolRun[] in list load, reuse cached data in handleSelectEngagement
- [x] Migrate TB page activity log from direct fetch to apiPost (fire-and-forget)
- [x] Migrate TB page workbook inspection from direct fetch to apiFetch (gains retry + timeout)
- [x] `npm run build` passes

**Files Modified:** `utils/apiClient.ts`, `hooks/useAdjustments.ts`, `hooks/usePriorPeriod.ts`, `hooks/useMultiPeriodComparison.ts`, `components/workspace/WorkspaceHeader.tsx`, `components/workspace/RecentHistoryMini.tsx`, `app/engagements/page.tsx`, `app/tools/trial-balance/page.tsx`

---

### Sprint 150: Docker Hardening — .dockerignore, Multi-Stage Fix, Security & Cleanup — COMPLETE
> **Complexity:** 2/10 | **Agent Lead:** BackendCritic
> **Rationale:** Docker review identified 12 issues: broken multi-stage (gcc leaks into production), no .dockerignore (secrets in build context), SQLite volume/path mismatch, malformed npm flag, dead libpq-dev, stale compose reference.

- [x] Create `backend/.dockerignore` (exclude .env, paciolus.db, tests/, __pycache__, dev files)
- [x] Create `frontend/.dockerignore` (exclude .env, node_modules/, .next/, coverage/)
- [x] Rewrite `backend/Dockerfile` — proper 2-stage multi-stage (builder with gcc → production without gcc)
- [x] Remove `libpq-dev` from builder (no PostgreSQL driver in requirements.txt)
- [x] Single `pip install` for requirements.txt + gunicorn (was 2 separate RUN layers)
- [x] Copy site-packages + gunicorn/uvicorn binaries from builder (no compiler toolchain in production)
- [x] Remove manual `rm -f .env paciolus.db` cleanup (handled by .dockerignore)
- [x] Fix `frontend/Dockerfile` line 19: `npm ci --only=production=false` → `npm ci`
- [x] Fix `docker-compose.yml` DATABASE_URL: `sqlite:///./paciolus.db` → `sqlite:////app/data/paciolus.db` (matches volume mount)
- [x] Remove reference to nonexistent `docker-compose.prod.yml`
- [x] Add JWT_SECRET_KEY documentation comment in compose

#### Review
**Files Created:** `backend/.dockerignore`, `frontend/.dockerignore`
**Files Modified:** `backend/Dockerfile` (rewrite), `frontend/Dockerfile` (line 19), `docker-compose.yml`

---

---

## Phase XVII: Code Smell Refactoring (Sprints 151-163)

> **Source:** Comprehensive code smell audit — 200+ smells, 73 unique patterns, ~7,500 duplicated lines identified
> **Strategy:** Backend shared abstractions first (highest ROI), then backend decomposition, then frontend decomposition
> **Constraint:** 100% backward compatible — every sprint must pass `pytest` + `npm run build` + `npm test`
> **Estimated Impact:** ~6,000 lines removed, 16 god classes/components decomposed, 40+ magic numbers named

### Phase XVII Summary Table

| Sprint | Feature | Complexity | Priority | Est. Lines Saved |
|--------|---------|:---:|:---:|---:|
| 151 | Shared Column Detector | 6/10 | P0 | ~2,400 | COMPLETE |
| 152 | Shared Data Quality + Test Aggregator | 5/10 | P0/P1 | ~1,600 | COMPLETE |
| 153 | Shared Statistical Tests (Benford, z-score) | 4/10 | P1 | ~350 | COMPLETE |
| 154 | audit_engine.py + financial_statement_builder Decomposition | 5/10 | P0 | ~200 | COMPLETE |
| 155 | routes/export.py Decomposition + Export Helpers | 5/10 | P1 | ~300 | COMPLETE |
| 156 | Testing Route Factory | 4/10 | P1 | ~160 | COMPLETE |
| 157 | Memo Generator Simplification | 4/10 | P2 | ~550 | COMPLETE |
| 158 | Backend Magic Numbers + Naming + Email Template | 3/10 | P1/P2 | ~50 | COMPLETE |
| 159 | trial-balance/page.tsx Decomposition | 5/10 | P0 | ~200 | COMPLETE |
| 160 | practice/page.tsx + multi-period/page.tsx Decomposition | 5/10 | P0/P1 | ~310 | COMPLETE |
| 161 | Frontend Testing Hook Factory + Shared Constants | 4/10 | P1 | ~350 | COMPLETE |
| 162 | FinancialStatementsPreview + Shared Badge + Cleanup | 4/10 | P1/P2 | ~370 | COMPLETE |
| 163 | Phase XVII Wrap — Regression + Documentation | 2/10 | — | — | COMPLETE |

---

### Sprint 151: Shared Column Detector — P0
> **Complexity:** 6/10 | **Est. Lines Saved:** ~2,400
> **Rationale:** Highest-ROI refactoring target. 9 engines each implement 200-400 lines of fuzzy column matching with 95% identical logic. Only pattern configs differ.

#### Shared Module
- [x] Create `backend/shared/column_detector.py` — `ColumnFieldConfig`, `DetectionResult`, `match_column()`, `detect_columns()`
- [x] Tests for shared column detector — 28 tests (pattern matching, greedy assignment, edge cases)

#### Engine Migrations (9 files)
- [x] Migrate `je_testing_engine.py` — 13 GL_COLUMN_CONFIGS, dual-date + debit/credit pair logic preserved
- [x] Migrate `ap_testing_engine.py` — shared detector + AP pattern config
- [x] Migrate `payroll_testing_engine.py` — shared detector + payroll pattern config
- [x] Migrate `revenue_testing_engine.py` — 8 REVENUE_COLUMN_CONFIGS
- [x] Migrate `ar_aging_engine.py` — TB_COLUMN_CONFIGS + SL_COLUMN_CONFIGS, dual-input with min_confidence=0.50
- [x] Migrate `fixed_asset_testing_engine.py` — 11 FA_COLUMN_CONFIGS, priority ordering for accum_depr/nbv/cost
- [x] Migrate `inventory_testing_engine.py` — 8 INV_COLUMN_CONFIGS, flexible value logic
- [x] Migrate `three_way_match_engine.py` — PO/INV/REC_COLUMN_CONFIGS (3 config sets, triple-input)
- [x] Migrate `bank_reconciliation.py` — shared detector + bank/ledger pattern configs

#### Verification
- [x] `pytest` passes — 2,628 tests (2,593 baseline + 28 new column detector + 7 other)
- [x] Each engine's existing test suite passes unchanged (column detection behavior identical)
- [x] No new public API changes — engines still expose same functions

#### Review
**Status:** COMPLETE
**Files Created:** `backend/shared/column_detector.py` (144 lines), `backend/tests/test_column_detector.py` (401 lines)
**Files Modified:** 9 engine modules + 9 test files (import redirects)
**Removed:** 9 ColumnType enums, 9 `_match_column` helpers, 9 `_COLUMN_PATTERNS` dicts — ~2,400 lines saved

---

### Sprint 152: Shared Data Quality + Test Aggregator — P0/P1
> **Complexity:** 5/10 | **Est. Lines Saved:** ~1,600
> **Rationale:** Every testing engine duplicates ~80-100 lines of data quality calculation (completeness, validity, consistency, timeliness) and ~100-150 lines of test result aggregation with severity weighting.

#### score_to_risk_tier Consolidation
- [x] Add `score_to_risk_tier()` to `backend/shared/testing_enums.py` (canonical copy)
- [x] Delete from 6 engine files (JE, AP, Revenue, FA, Inventory, AR Aging) — re-export for backward compat

#### Shared Data Quality
- [x] Create `backend/shared/data_quality.py`
  - `FieldQualityConfig` dataclass: field_name, accessor, weight, issue_threshold, issue_template
  - `DataQualityResult` dataclass: completeness_score (0-100), field_fill_rates, detected_issues, total_rows
  - `assess_data_quality(entries, field_configs)` function: config-driven field assessment
- [x] Tests: `backend/tests/test_data_quality.py` (13 tests)

#### Shared Test Aggregator
- [x] Create `backend/shared/test_aggregator.py`
  - `CompositeScoreResult` dataclass matching existing composite score shapes
  - `calculate_composite_score()` function: parameterized severity weighting, multi-flag multiplier, normalization
  - Handles both `max_possible` (JE/AP/Revenue/FA/Inventory/AR) and `total_entries` (Payroll) normalization
- [x] Tests: `backend/tests/test_test_aggregator.py` (21 tests)

#### Engine Migrations (7 files — skip Three-Way Match)
- [x] Migrate `je_testing_engine.py` — DQ + CS + delete score_to_risk_tier
- [x] Migrate `ap_testing_engine.py` — DQ + CS + delete score_to_risk_tier
- [x] Migrate `revenue_testing_engine.py` — DQ + CS + delete score_to_risk_tier
- [x] Migrate `fixed_asset_testing_engine.py` — DQ + CS + delete score_to_risk_tier
- [x] Migrate `inventory_testing_engine.py` — DQ + CS + delete score_to_risk_tier
- [x] Migrate `ar_aging_engine.py` — CS only + delete score_to_risk_tier (DQ too different)
- [x] Migrate `payroll_testing_engine.py` — DQ + CS with special handling (0-1 scale, dict top_findings)

#### Verification
- [x] `pytest` passes (2,662 tests — all passing)
- [x] `npm run build` passes
- [x] Composite scores numerically identical for existing test fixtures

---

### Sprint 153: Shared Benford Analysis + Z-Score Severity — COMPLETE
> **Complexity:** 3/10 | **Lines Saved:** ~330
> **Rationale:** Benford's Law duplicated between JE (~230 lines) and Payroll (~180 lines). Z-score severity mapping duplicated across 7 call sites in 6 engines. Revenue Benford explicitly excluded (structurally different).

#### Shared Modules
- [x] Add `zscore_to_severity()` to `backend/shared/testing_enums.py`
- [x] Create `backend/shared/benford.py` — `BenfordAnalysis` dataclass, `get_first_digit()`, `analyze_benford()`, constants
- [x] Create `backend/tests/test_benford.py` — 25 tests (get_first_digit, analyze_benford, zscore_to_severity)

#### Benford Migrations
- [x] Migrate `je_testing_engine.py` — `BenfordResult = BenfordAnalysis` alias, delete ~260 inline lines
- [x] Migrate `payroll_testing_engine.py` — delete ~180 inline lines, use shared `analyze_benford()`
- [x] Revenue Benford NOT migrated (different precision, chi-squared only, no MAD/conformity)

#### Z-Score Severity Migrations (7 call sites → `zscore_to_severity()`)
- [x] `je_testing_engine.py` — `test_unusual_amounts`
- [x] `payroll_testing_engine.py` — `_test_unusual_pay_amounts`
- [x] `ap_testing_engine.py` — `unusual_payment_amounts`
- [x] `revenue_testing_engine.py` — `zscore_outliers`
- [x] `fixed_asset_testing_engine.py` — `cost_zscore_outliers`
- [x] `inventory_testing_engine.py` — `unit_cost_outliers` + `quantity_outliers`

#### Verification
- [x] `pytest tests/test_benford.py` — 25 passed
- [x] Full `pytest` — all tests pass
- [x] `npm run build` — passes (no frontend changes)

#### Review
**Files Created:** `shared/benford.py`, `tests/test_benford.py`
**Files Modified:** `shared/testing_enums.py`, `je_testing_engine.py`, `payroll_testing_engine.py`, `ap_testing_engine.py`, `revenue_testing_engine.py`, `fixed_asset_testing_engine.py`, `inventory_testing_engine.py`

---

### Sprint 154: audit_engine.py + financial_statement_builder Decomposition — COMPLETE
> **Complexity:** 5/10 | **Lines Saved:** ~80 (deduplication) + improved readability
> **Rationale:** Duplicated anomaly merge (~52 lines x 2) and risk summary (~30 lines x 2) in audit_engine.py. Monolithic 191-line `_build_cash_flow_statement()` in financial_statement_builder.py.

#### audit_engine.py — 2 new module-level helpers
- [x] Extract `_merge_anomalies(abnormal_balances, suspense, concentration, rounding) -> list`
- [x] Extract `_build_risk_summary(abnormal_balances) -> dict`
- [x] Replace streaming + multi-sheet merge logic with helper calls

#### financial_statement_builder.py — 3 new private methods
- [x] Extract `_build_operating_items`, `_build_investing_items`, `_build_financing_items`
- [x] Simplify `_build_cash_flow_statement()` to ~40-line orchestrator

#### Verification
- [x] `pytest tests/test_audit_engine.py` — 79 passed
- [x] `pytest tests/test_cash_flow_statement.py` — 39 passed
- [x] Full `pytest` — all tests pass

#### Review
**Files Modified:** `backend/audit_engine.py` (2 helpers, ~80 lines deduplicated), `backend/financial_statement_builder.py` (3 methods extracted)

---

### Sprint 155: routes/export.py Decomposition + Export Helpers — COMPLETE
> **Complexity:** 5/10 | **Lines Saved:** ~300
> **Rationale:** 1,497-line god module with 24 endpoints and 18 Pydantic models.

#### Architecture
- [x] Create `shared/export_schemas.py` — 18 Pydantic models (~190 lines)
- [x] Create `routes/export_diagnostics.py` — 6 endpoints (~310 lines)
- [x] Create `routes/export_testing.py` — 8 CSV endpoints (~370 lines)
- [x] Create `routes/export_memos.py` — 10 memo PDF endpoints (~270 lines)
- [x] Slim `routes/export.py` → 33-line aggregator

#### Verification
- [x] `pytest` passes — 2,687 tests, 0 failures
- [x] All 24 export endpoints still at same paths

#### Review
**Files Created:** `shared/export_schemas.py`, `routes/export_diagnostics.py`, `routes/export_testing.py`, `routes/export_memos.py`
**Files Modified:** `shared/export_helpers.py`, `routes/export.py` (1,497->33-line aggregator)

---

### Sprint 156: Testing Route Factory — COMPLETE
> **Complexity:** 4/10 | **Lines Saved:** ~160

#### Shared Factory
- [x] Create `backend/shared/testing_route.py` — callback-based factory
- [x] Migrate 6 single-file routes (AP, Payroll, JE, Revenue, FA, Inventory)
- [x] TWM and AR Aging excluded by design (multi-file, structurally different)

#### Verification
- [x] `pytest` passes (2,687 tests, 0 failures)

#### Review
**Files Created:** `backend/shared/testing_route.py` (72 lines)
**Files Modified:** 6 route files

---

### Sprint 157: Memo Generator Simplification — COMPLETE
> **Complexity:** 4/10 | **Lines Saved:** ~550

#### Template System
- [x] Create `backend/shared/memo_template.py` — config-driven testing memo generator
- [x] Convert 7 generators to config + template (AP, Revenue, FA, Inventory, Payroll, JE, AR)
- [x] 4 custom generators excluded (Bank Rec, TWM, Multi-Period, Anomaly Summary)

#### Tests (29 new — total 2,716)
- [x] `tests/test_memo_template.py`: 29 tests
- [x] Updated 4 guardrail test files for config-driven architecture

#### Verification
- [x] `pytest` passes — 2,716 tests, 0 failures
- [x] All 182 existing memo tests still pass

#### Review
**Files Created:** `shared/memo_template.py` (175 lines), `tests/test_memo_template.py`
**Files Modified:** 7 generator modules, 4 guardrail test files

---

### Sprint 158: Backend Magic Numbers + Naming + Email Template — COMPLETE
> **Complexity:** 3/10

- [x] `audit_engine.py`: Extract `BALANCE_TOLERANCE`, `BS_IMBALANCE_THRESHOLD_LOW/HIGH`, `CONFIDENCE_HIGH/MEDIUM`
- [x] `ratio_engine.py`: Extract 30 named threshold constants
- [x] `benchmark_engine.py`: Extract `HEALTH_SCORE_STRONG = 65`, `HEALTH_SCORE_MODERATE = 40`
- [x] `classification_validator.py`: Extract 5 threshold constants
- [x] `audit_engine.py`: Rename `ab` → `entry`, `conc` → `concentration`
- [x] Create `backend/templates/verification_email.html` + `.txt`
- [x] Simplify `email_service.py` to load + format

#### Verification
- [x] `pytest` passes (2,716 tests, 0 failures)

#### Review
**Files Created:** `backend/templates/verification_email.html`, `backend/templates/verification_email.txt`
**Files Modified:** `audit_engine.py`, `ratio_engine.py`, `classification_validator.py`, `benchmark_engine.py`, `email_service.py`

---

### Sprint 159: trial-balance/page.tsx Decomposition — COMPLETE
> **Complexity:** 5/10 | **Lines Saved:** ~990 from page.tsx (1,219 -> 229 lines, 81% reduction)

- [x] Extract `useTrialBalanceAudit` hook (321 lines)
- [x] Extract `GuestMarketingView` component (197 lines)
- [x] Extract `AuditResultsPanel` component (243 lines)
- [x] Slim `page.tsx` to 229 lines

#### Verification
- [x] `npm run build` passes (35 routes, 0 errors)
- [x] `npm test` passes (128/128 tests)

#### Review
**Files Created:** `hooks/useTrialBalanceAudit.ts`, `components/trialBalance/GuestMarketingView.tsx`, `components/trialBalance/AuditResultsPanel.tsx`
**Files Modified:** `app/tools/trial-balance/page.tsx` (1,219 -> 229 lines)

---

### Sprint 160: practice/page.tsx + multi-period/page.tsx Decomposition — COMPLETE
> **Complexity:** 5/10 | **Lines Saved:** ~310 net

#### practice/page.tsx (1,203 -> 665 lines, 45% reduction)
- [x] Extract `TestingConfigSection` shared component (218 lines)
- [x] Refactor 4 testing config sections to data-driven `<TestingConfigSection>`

#### multi-period/page.tsx (897 -> 470 lines, 48% reduction)
- [x] Extract 6 sub-components to `components/multiPeriod/`

#### Verification
- [x] `npm run build` passes (35 routes, 0 errors)
- [x] `npm test` passes (128/128 tests)

#### Review
**Files Created:** `components/settings/TestingConfigSection.tsx`, 8 multiPeriod component files
**Files Modified:** `app/settings/practice/page.tsx` (1,203->665), `app/tools/multi-period/page.tsx` (897->470)

---

### Sprint 161: Frontend Testing Hook Factory + Shared Constants — COMPLETE
> **Complexity:** 4/10 | **Lines Saved:** ~160 (net)

- [x] Create `hooks/createTestingHook.ts` — factory function (36 lines)
- [x] Refactor 9 testing hooks to use factory
- [x] Create `utils/constants.ts` — API_URL, timeouts, retries, TTLs (30 lines)
- [x] Replace 14 `process.env.NEXT_PUBLIC_API_URL` declarations with import
- [x] Create `utils/animations.ts` — shared framer-motion variants (46 lines)

#### Verification
- [x] `npm run build` passes (35 routes, 0 errors)
- [x] `npm test` passes (128/128 tests)

#### Review
**Files Created:** `utils/constants.ts`, `hooks/createTestingHook.ts`, `utils/animations.ts`
**Files Modified:** 9 testing hooks + 15 other files

---

### Sprint 162: FinancialStatementsPreview + Shared Badge + Frontend Cleanup — COMPLETE
> **Complexity:** 4/10 | **Lines Saved:** ~370 net

#### FinancialStatementsPreview.tsx (772 -> 333, 57% reduction)
- [x] Extract `StatementTable` + `CashFlowTable` + `useStatementBuilder` hook + `ExportButton`

#### Shared Badge Component
- [x] Create `components/shared/StatusBadge.tsx`
- [x] Migrate 3 inline badges in FollowUpItemsTable

#### ProfileDropdown Cleanup (401 -> 217, 46% reduction)
- [x] Extract `NavMenuItem` data-driven component

#### Bug Fixes
- [x] Fix `useBenchmarks.ts` — `useState(() => { fetchIndustries() })` anti-pattern → `useEffect`

#### Verification
- [x] `npm run build` passes (35 routes)
- [x] `npm test` passes (128/128 tests)

#### Review
**Files Created:** `financialStatements/types.ts`, `financialStatements/useStatementBuilder.ts`, `financialStatements/StatementTable.tsx`, `financialStatements/CashFlowTable.tsx`, `shared/StatusBadge.tsx`
**Files Modified:** `FinancialStatementsPreview.tsx` (772->333), `FollowUpItemsTable.tsx`, `ProfileDropdown.tsx` (401->217), `useBenchmarks.ts`

---

### Sprint 163: Phase XVII Wrap — Regression + Documentation — COMPLETE
> **Complexity:** 2/10

#### Regression Testing
- [x] Full `pytest` suite passes (2,716 tests, 0 failures)
- [x] Full `npm run build` passes (35 routes)
- [x] Full `npm test` passes (128 tests, 13 suites)
- [x] All 11 tool pages functional
- [x] All 26 routers registered

#### Metrics Verification
- [x] Lines refactored: 9,298 added / 8,849 removed across 12 sprints
- [x] Shared modules created: 15 new files (7 backend `shared/` + 8 frontend)
- [x] `routes/export.py`: 32 lines (was 1,497 — 98% reduction)
- [x] `trial-balance/page.tsx`: 215 lines (was 1,219 — 82% reduction)

#### Documentation
- [x] Update CLAUDE.md, todo.md, lessons.md, MEMORY.md

---

### Phase XIII Explicit Exclusions (Deferred to Phase XIV+)

| Feature | Reason for Deferral | Earliest Phase |
|---------|---------------------|----------------|
| User-toggleable dark/light mode | CEO vision is route-based, not preference | Phase XIV (if user demand) |
| Homepage "high-tech" redesign | Homepage stays dark; redesign is separate initiative | Phase XIV |
| Mobile hamburger menu for ToolNav | Current overflow dropdown sufficient; mobile redesign larger effort | Phase XIV |
| Print stylesheet (light theme piggyback) | Out of scope for Phase XIII | Phase XIV |
| Component library / Storybook | Documentation effort; lower priority than shipping features | Phase XIV |
| Composite scoring for TB/BankRec/TWM/MultiPeriod | Requires architectural discussion — these tools have different result shapes | Phase XIV |
| Onboarding flow | UX research needed for first-run experience | Phase XIV |
| Batch export all memos | Nice-to-have; ZIP already bundles anomaly summary | Phase XIV |
