# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Completed Phases

### Phase I (Sprints 1-24) — COMPLETE
> Core platform: Zero-Storage TB analysis, streaming, classification, brand, risk dashboard, multi-sheet Excel, PDF/Excel export, JWT auth, activity logging, client management, practice settings, deployment prep.

### Phase II (Sprints 25-40) — COMPLETE
> Test suite, 9 ratios (Current/Quick/D2E/Gross/Net/Operating/ROA/ROE/DSO), IFRS/GAAP docs, trend analysis + viz, industry ratios (6 industries), rolling windows, batch upload, benchmark RFC.

### Phase III (Sprints 41-47) — COMPLETE
> Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI + integration.

### Phase IV (Sprints 48-55) — COMPLETE
> User profile, security hardening, lead sheets (A-Z), prior period comparison, adjusting entries, DSO ratio, CSV export, frontend test foundation.

### Phase V (Sprints 56-60) — COMPLETE
> UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode. **Tests: 625 backend + 26 frontend.**

### Phase VI (Sprints 61-70) — COMPLETE
> Multi-Period TB Comparison (Tool 2), Journal Entry Testing (Tool 3, 18-test battery + stratified sampling), platform rebrand to suite, diagnostic zone protection. Tests added: 268 JE + multi-period.

### Phase VII (Sprints 71-80) — COMPLETE
> Financial Statement Builder (Tool 1 enhancement), AP Payment Testing (Tool 4, 13-test battery), Bank Reconciliation (Tool 5). Tests added: 165 AP + 55 bank rec.

### Phase VIII (Sprints 81-89) — COMPLETE
> Cash Flow Statement (indirect method, ASC 230/IAS 7), Payroll & Employee Testing (Tool 6, 11-test battery), code quality sprints (81-82). Tests added: 139 payroll.

### Phase IX (Sprints 90-96) — COMPLETE
> Shared testing utilities extraction (enums/memo/round-amounts), Three-Way Match Validator (Tool 7), Classification Validator (TB Enhancement). Tests added: 114 three-way match + 52 classification.

### Phase X (Sprints 96.5-102) — COMPLETE
> The Engagement Layer: engagement model + materiality cascade, follow-up items tracker (narratives-only), workpaper index, anomaly summary report (PDF), diagnostic package export (ZIP with SHA-256), engagement workspace frontend. 8 AccountingExpertAuditor guardrails satisfied. Tests added: 158 engagement/follow-up/workpaper/export.

### Phase XI (Sprints 103-110) — COMPLETE
> Tool-Engagement Integration (frontend auto-link via EngagementProvider), Revenue Testing (Tool 8, 12-test battery, ISA 240), AR Aging Analysis (Tool 9, 11-test battery, dual-input TB + sub-ledger). Tests added: 110 revenue + 28 memo + 131 AR + 34 memo.

### Phase XII (Sprints 111-120) — COMPLETE
> Nav overflow infrastructure, FileDropZone extraction, Finding Comments + Assignments (collaboration), Fixed Asset Testing (Tool 10, 9-test battery, IAS 16), Inventory Testing (Tool 11, 9-test battery, IAS 2). Tests added: 41 comments + 15 assignments + 133 FA + 38 FA memo + 136 inventory + 38 inv memo.

**Test Coverage at Phase XII End:** 2,515 backend tests + 76 frontend tests | Version 1.1.0

> **Detailed checklists:** `tasks/archive/phases-vi-ix-details.md` | `tasks/archive/phases-x-xii-details.md`

---

## Post-Sprint Checklist

**MANDATORY:** Complete these steps after EVERY sprint before declaring it done.

### Verification
- [ ] Run `npm run build` in frontend directory (must pass)
- [ ] Run `pytest` in backend directory (if tests modified)
- [ ] Verify Zero-Storage compliance for new data handling

### Documentation
- [ ] Update sprint status to COMPLETE in todo.md
- [ ] Add Review section with Files Created/Modified
- [ ] Add lessons to lessons.md if corrections occurred

### Git Commit
- [ ] Stage relevant files: `git add <specific-files>`
- [ ] Commit with sprint reference: `git commit -m "Sprint X: Brief Description"`
- [ ] Verify commit: `git log -1`

---

## Not Currently Pursuing

> **Reviewed:** Agent Council + Future State Consultant (2026-02-09)
> **Criteria:** Deprioritized due to low leverage, niche markets, regulatory burden, or off-brand positioning.

| Feature | Status | Reason |
|---------|--------|--------|
| Loan Amortization Generator | Not pursuing | Commodity calculator; off-brand |
| Depreciation Calculator | Not pursuing | MACRS table maintenance; better served by Excel |
| 1099 Preparation Helper | Not pursuing | US-only, seasonal, annual IRS rule changes |
| Book-to-Tax Adjustment Calculator | Not pursuing | Tax preparer persona; regulatory complexity |
| W-2/W-3 Reconciliation Tool | Not pursuing | Payroll niche; seasonal; different persona |
| Segregation of Duties Checker | Not pursuing | IT audit persona; different user base |
| Expense Allocation Testing | DROPPED | 2/5 market demand; niche applicability |
| Cross-Tool Composite Risk Scoring | REJECTED | ISA 315 violation — requires auditor risk inputs |
| Management Letter Generator | REJECTED | ISA 265 violation — deficiency classification is auditor judgment |
| Heat Map / Risk Visualization | REJECTED | Depends on composite scoring (rejected) |

### Deferred to Phase XIV+

| Feature | Reason | Earliest Phase |
|---------|--------|----------------|
| Budget Variance Deep-Dive | Multi-Period page tab refactor prerequisite | Phase XIV |
| Accrual Reasonableness Testing (Tool 12) | Dual-input fuzzy matching complexity | Phase XIV |
| Intercompany Transaction Testing (Tool 13) | Cycle-finding algorithm; narrow applicability | Phase XIV |
| Multi-Currency Conversion | Cross-cutting 11+ engine changes; needs dedicated RFC | Phase XIV |
| Engagement Templates | Premature until engagement workflow has real user feedback | Phase XIV |
| Lease Accounting (ASC 842) | 8/10 complexity; high value but needs research sprint | Phase XIV |
| Cash Flow Projector | Requires AR/AP aging + payment history | Phase XIV |
| Cash Flow — Direct Method | Requires AP/payroll detail integration | Phase XIV |
| Related Party Transaction Screening | Needs external data APIs; 8/10 complexity | Phase XIV+ |
| Finding Attachments | File storage contradicts Zero-Storage philosophy | Phase XIV+ |
| Real-Time Collaboration | WebSocket infrastructure; 9/10 complexity | Phase XIV+ |
| Custom Report Builder | Rich text editor + templating engine | Phase XIV+ |
| Historical Engagement Comparison | Requires persistent aggregated data | Phase XIV+ |

---

## Phase XIII: Platform Polish + The Vault Interior (Sprints 121–130)

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
| 125 | Theme: Tool Pages Batch 1 (6 tools) | 5/10 | FrontendExecutor | PENDING |
| 126 | Theme: Tool Pages Batch 2 + Authenticated Pages | 5/10 | FrontendExecutor | PENDING |
| 127 | Vault Transition + Visual Polish | 4/10 | FintechDesigner + FrontendExecutor | PENDING |
| 128 | Export Consolidation + Missing Memos | 5/10 | BackendCritic + AccountingExpertAuditor | PENDING |
| 129 | Accessibility + Frontend Test Backfill | 5/10 | QualityGuardian + FrontendExecutor | PENDING |
| 130 | Phase XIII Wrap — Regression + v1.2.0 | 2/10 | QualityGuardian | PENDING |

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

### Sprint 125: Theme: Tool Pages Batch 1 (6 tools)
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor
> **Rationale:** Migrate the 6 newer tool pages (consistent patterns, no legacy quirks) to semantic tokens. Includes their component sets.

#### Pages + Components
- [ ] Migrate Revenue Testing page + components (ScoreCard, TestResultGrid, DataQualityBadge, FlaggedTable)
- [ ] Migrate AR Aging page + components
- [ ] Migrate Fixed Asset Testing page + components
- [ ] Migrate Inventory Testing page + components
- [ ] Migrate AP Testing page + components
- [ ] Migrate Payroll Testing page + components

#### Pattern Changes (Light Theme)
- [ ] Replace `bg-gradient-obsidian` with `bg-surface-page` (or `bg-gradient-oat`)
- [ ] Replace `bg-obsidian-*` card backgrounds with `bg-surface-card`
- [ ] Replace `text-oatmeal-*` with `text-content-*` equivalents
- [ ] Replace `border-obsidian-*` with `border-theme`
- [ ] Replace tier gradient backgrounds with left-border accents (4px colored left border)
- [ ] Replace transparent sage/clay badge backgrounds with solid `sage-50`/`clay-50` fills
- [ ] Update buttons: primary = solid `sage-600`, secondary = white with `oatmeal-300` border

#### Verification
- [ ] `npm run build` passes
- [ ] All 6 tool pages render on light background
- [ ] WCAG AA contrast verified on key elements (headings, body text, financial numbers)
- [ ] Score cards, test grids, flagged tables all readable on light

---

### Sprint 126: Theme: Tool Pages Batch 2 + Authenticated Pages
> **Complexity:** 5/10 | **Agent Lead:** FrontendExecutor
> **Rationale:** Migrate the 5 remaining tool pages (including legacy TB and Multi-Period with non-standard patterns) and all other authenticated pages.

#### Tool Pages
- [ ] Migrate Trial Balance page + diagnostics components (largest page, marketing dual-use)
- [ ] Migrate Multi-Period page (custom upload zones, comparison layout)
- [ ] Migrate Journal Entry Testing page + components (BenfordChart, stratified sampling UI)
- [ ] Migrate Bank Reconciliation page (reconciliation bridge, match table)
- [ ] Migrate Three-Way Match page + components (variance cards, match summary)

#### Other Authenticated Pages
- [ ] Migrate Engagement workspace pages (`app/engagements/page.tsx` + all engagement components)
- [ ] Migrate Settings pages (profile, practice)
- [ ] Migrate Portfolio page
- [ ] Migrate Flux/Recon pages
- [ ] Migrate Status page
- [ ] Migrate History page

#### Utility Updates
- [ ] Update `themeUtils.ts` light variants (INPUT_BASE_CLASSES, RISK_LEVEL_CLASSES, BADGE_CLASSES, HEALTH_STATUS_CLASSES)
- [ ] Update global CSS component classes (`.card`, `.input`, `.stat-card`) with `[data-theme="light"]` variants

#### Verification
- [ ] `npm run build` passes
- [ ] All 11 tool pages render on light background
- [ ] Engagement workspace renders on light
- [ ] Settings/portfolio pages render on light
- [ ] Homepage still renders on dark (no regression)

---

### Sprint 127: Vault Transition + Visual Polish
> **Complexity:** 4/10 | **Agent Lead:** FintechDesigner + FrontendExecutor
> **Rationale:** The experiential "vault crack" moment + final visual refinements for the light theme.

#### Vault Crack Transition
- [ ] Create `VaultTransition` component (framer-motion):
  - Phase 1 (0-300ms): Login form fades, auth succeeds
  - Phase 2 (300-800ms): Horizontal light-leak from center expands to fill viewport
  - Phase 3 (800-1400ms): Welcome screen — light-bg logo + "Welcome back, [Name]" + date
  - Phase 4 (1400-2000ms): Cross-fade into target tool page
- [ ] Add to login success flow (after auth, before navigation)
- [ ] Skippable: click or keypress instantly completes transition
- [ ] `prefers-reduced-motion` media query: skip animation entirely, instant transition
- [ ] Only triggers on login — not on page navigation between tool pages

#### Light Theme Polish
- [ ] Remove `transform hover:scale-105` from buttons on light theme (professional, not playful)
- [ ] Ensure tier gradients replaced with left-border accents across all score cards
- [ ] Remove sage glow effects on light backgrounds (replace with subtle sage border)
- [ ] Tune shadow warmth across all card components
- [ ] Verify dark toasts render correctly on light pages
- [ ] Add zebra striping to flagged tables (`bg-white` / `bg-oatmeal-50/50` alternating)
- [ ] Add table row hover state: `bg-sage-50/40` (warm green hint, not grey)

#### Cross-Browser Verification
- [ ] Chrome: full visual check
- [ ] Firefox: full visual check
- [ ] Edge: spot check
- [ ] Mobile viewport: spot check (responsive grid behavior)

#### Verification
- [ ] `npm run build` passes
- [ ] Vault transition plays on login (manual test)
- [ ] Vault transition skippable (manual test)
- [ ] No visual artifacts in transition
- [ ] Light theme polished across all pages

---

### Sprint 128: Export Consolidation + Missing Memos
> **Complexity:** 5/10 | **Agent Lead:** BackendCritic + AccountingExpertAuditor
> **Rationale:** P1 findings — export.py has 600+ lines duplicated with shared/export_helpers.py; Bank Rec and Multi-Period are the only tools without PDF memos.

#### Export Deduplication
- [ ] Refactor `routes/export.py` to use `shared/export_helpers.py` for common patterns
- [ ] Eliminate duplicated PDF/CSV generation logic
- [ ] Maintain all existing endpoint signatures (backward compatible)
- [ ] Existing tests still pass after refactor

#### Bank Reconciliation Memo
- [ ] Create `backend/bank_reconciliation_memo_generator.py` (extends shared/memo_base.py)
- [ ] ISA 500 reference (external confirmations), reconciliation scope
- [ ] Disclaimer: "Reconciliation analysis, not bank balance confirmation"
- [ ] Add `POST /export/bank-rec-memo` route
- [ ] Add memo export button to Bank Rec frontend page
- [ ] Tests for memo generator

#### Multi-Period Comparison Memo
- [ ] Create `backend/multi_period_memo_generator.py` (extends shared/memo_base.py)
- [ ] ISA 520 reference (analytical procedures), variance analysis scope
- [ ] Disclaimer: "Trend analysis, not predictive assurance"
- [ ] Add `POST /export/multi-period-memo` route
- [ ] Add memo export button to Multi-Period frontend page
- [ ] Tests for memo generator

#### Verification
- [ ] `pytest` passes (all existing + new memo tests)
- [ ] `npm run build` passes
- [ ] All 11 tools now have PDF memo export capability
- [ ] Export.py line count significantly reduced

---

### Sprint 129: Accessibility + Frontend Test Backfill
> **Complexity:** 5/10 | **Agent Lead:** QualityGuardian + FrontendExecutor
> **Rationale:** P1 findings — zero ARIA attributes on tool pages, 6 of 11 tool pages have no frontend tests.

#### Accessibility (WCAG AA)
- [ ] Add `role="button"` and `aria-label` to file upload drop zones on all 11 tool pages
- [ ] Add `aria-live="polite"` to loading state containers
- [ ] Add `role="alert"` to error state containers
- [ ] Add `aria-expanded` + `aria-haspopup` to ToolNav "More" dropdown
- [ ] Add keyboard navigation to ToolNav dropdown (Tab, Enter, Escape handlers)
- [ ] Add keyboard navigation to ProfileDropdown
- [ ] Add `focus:ring-2 focus:ring-sage-500 focus:ring-offset-2` to file dropzones
- [ ] Add `aria-hidden="true"` to decorative SVG icons across tool pages

#### Frontend Test Backfill (6 missing tool pages)
- [ ] Create `__tests__/RevenueTestingPage.test.tsx` (~10 tests)
- [ ] Create `__tests__/ARAgingPage.test.tsx` (~10 tests)
- [ ] Create `__tests__/FixedAssetTestingPage.test.tsx` (~10 tests)
- [ ] Create `__tests__/InventoryTestingPage.test.tsx` (~10 tests)
- [ ] Create `__tests__/TrialBalancePage.test.tsx` (~10 tests)
- [ ] Create `__tests__/MultiPeriodPage.test.tsx` (~10 tests)

#### Verification
- [ ] All frontend tests pass (existing 76 + ~60 new)
- [ ] `npm run build` passes
- [ ] Keyboard-only navigation through ToolNav dropdown works
- [ ] Screen reader can identify upload zones

---

### Sprint 130: Phase XIII Wrap — Regression + v1.2.0
> **Complexity:** 2/10 | **Agent Lead:** QualityGuardian

#### Regression Testing
- [ ] Full backend test suite passes
- [ ] Full frontend test suite passes (including new tests)
- [ ] Full frontend build passes
- [ ] All 11 tool pages render correctly on light theme
- [ ] Homepage renders correctly on dark theme
- [ ] Login/register pages render on dark theme
- [ ] Vault transition plays on login
- [ ] All export endpoints rate-limited
- [ ] All upload endpoints validate content type
- [ ] All 11 tools have PDF memo export

#### WCAG Contrast Audit
- [ ] Primary text on oatmeal-100: contrast ratio >= 4.5:1
- [ ] Secondary text on oatmeal-100: contrast ratio >= 4.5:1
- [ ] Sage-600 on white: contrast ratio >= 4.5:1
- [ ] Clay-600 on white: contrast ratio >= 4.5:1
- [ ] Financial data (font-mono) legible on all surfaces

#### Guardrail Verification
- [ ] All 6 AccountingExpertAuditor guardrails PASS
- [ ] No generic Tailwind colors (`grep -r "amber\|slate-\|blue-\|green-\|red-" --include="*.tsx"`)
- [ ] All disclaimers present and non-dismissible on engagement surfaces
- [ ] Zero-Storage compliance verified

#### Documentation
- [ ] CLAUDE.md: Phase XIII COMPLETE, version 1.2.0, dual-theme architecture
- [ ] Update todo.md sprint statuses
- [ ] Add lessons learned to `tasks/lessons.md`
- [ ] Update MEMORY.md with theme architecture patterns

#### Verification
- [ ] `npm run build` passes
- [ ] `pytest` passes (full suite)
- [ ] Git commit: `Sprint 130: Phase XIII Wrap — Regression + v1.2.0`

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
