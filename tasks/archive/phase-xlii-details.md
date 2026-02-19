# Phase XLII — Design Foundation Fixes (Sprints 313–318)

> **Focus:** Fix broken design tokens and visual hierarchy — shadow/border repair, opacity/contrast audit, typography/spacing, light theme semantic token migration
> **Source:** Comprehensive visual design audit — 10 foundation fixes identified
> **Strategy:** Tokens first → dark theme opacity → typography → light theme migration (3 batches)
> **Impact:** All surfaces gain proper visual hierarchy; light theme fully semantic; dark theme elements visible

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 313 | Shadow & Border Token Repair | 3/10 | COMPLETE |
| 314 | Opacity & Contrast Audit | 4/10 | COMPLETE |
| 315 | Visual Hierarchy — Typography & Spacing | 4/10 | COMPLETE |
| 316 | Light Theme Component Migration — Batch 1 | 5/10 | COMPLETE |
| 317 | Light Theme Component Migration — Batch 2 | 5/10 | COMPLETE |
| 318 | Light Theme Migration — Batch 3 + Regression | 3/10 | COMPLETE |

## Sprint 313: Shadow & Border Token Repair
- `globals.css`: Light theme border strengthened from `#DDD9D1` to `#C8C3BA`
- Layered card shadows: `0 2px 8px rgba(33,33,33,0.08), 0 1px 3px rgba(33,33,33,0.06)`
- Added `--shadow-theme-card-lg` token for featured/hero cards
- Added `--surface-elevated` token (dark: `rgba(55,55,55,0.9)`, light: `#F7F6F4`)
- Added `.card-premium` utility class with hover lift
- `tailwind.config.ts`: registered `shadow-theme-card-lg` and `surface-elevated`

## Sprint 314: Opacity & Contrast Audit
- FeaturePillars.tsx: gradient `/20`→`/40`, icon bg `/10`→`/20`, border `/50`→`/40`
- ProcessTimeline.tsx: connecting lines `/20`→`/50`, accent bg `/10`→`/20`
- DemoZone.tsx: background `/30`→`/50`, internal cards raised
- Homepage page.tsx: tool cards `/50`→`/70`, borders `/30`→`/40`
- Pricing page: "Most Popular" tier `sage-500/15 border-sage-500/40 shadow-lg`

## Sprint 315: Visual Hierarchy — Typography & Spacing
- Hero headline: `text-5xl md:text-7xl` with `leading-[1.1]`
- Gradient text on "Intelligence Suite": sage→oatmeal CSS gradient clip
- Primary CTA: solid sage with glow shadow (`shadow-sage-600/25`)
- Section spacing `py-16`→`py-24` across all homepage sections
- Gradient section dividers between major sections
- Tool showcase heading `text-2xl`→`text-3xl`

## Sprint 316: Light Theme Component Migration — Batch 1
- RiskDashboard.tsx: `bg-obsidian-700/50` → `bg-surface-card` + semantic text
- AnomalyCard.tsx: `bg-obsidian-800/50` → `bg-surface-card` + semantic tokens
- LeadSheetSection.tsx + LeadSheetCard.tsx: full semantic migration
- BenchmarkSection.tsx + BenchmarkCard.tsx: full semantic migration
- PercentileBar.tsx: track `bg-obsidian-700` → `bg-oatmeal-200`
- Key insight: WorkspaceHeader/QuickActionsBar/RecentHistoryMini are dark-route — NOT migrated

## Sprint 317: Light Theme Component Migration — Batch 2
- IndustryMetricsSection.tsx: text tokens to semantic
- RollingWindowSection.tsx: card backgrounds and text tokens
- TrendSummaryCard.tsx: skeleton colors to oatmeal-200
- TestingScoreCard.tsx: circle stroke color adjusted
- Tooltips intentionally left dark (same pattern as toasts)

## Sprint 318: Light Theme Migration — Batch 3 + Regression
- 14 component files migrated to semantic tokens:
  - FinancialStatementsPreview, ColumnMappingModal, MappingToolbar, AccountTypeDropdown
  - SensitivityToolbar, WeightedMaterialityEditor, WorkbookInspector
  - HeritageTimeline, ActivityEntry, ClientCard, EditClientModal, CreateClientModal
  - MaterialityControl, SectionHeader
- ToolLinkToast.tsx skipped (toasts stay dark by design)
- ColumnMappingModal test updated for semantic token change
- Regression: 995 frontend tests pass, `npm run build` clean

## Files Modified
- `frontend/src/app/globals.css` — theme tokens
- `frontend/tailwind.config.ts` — semantic token registration
- `frontend/src/app/(marketing)/page.tsx` — homepage layout
- `frontend/src/components/marketing/FeaturePillars.tsx`
- `frontend/src/components/marketing/ProcessTimeline.tsx`
- `frontend/src/components/marketing/DemoZone.tsx`
- `frontend/src/app/(marketing)/pricing/page.tsx`
- `frontend/src/components/risk/RiskDashboard.tsx`
- `frontend/src/components/risk/AnomalyCard.tsx`
- `frontend/src/components/leadSheet/LeadSheetSection.tsx`
- `frontend/src/components/leadSheet/LeadSheetCard.tsx`
- `frontend/src/components/benchmark/BenchmarkSection.tsx`
- `frontend/src/components/benchmark/BenchmarkCard.tsx`
- `frontend/src/components/benchmark/PercentileBar.tsx`
- `frontend/src/components/analytics/IndustryMetricsSection.tsx`
- `frontend/src/components/analytics/RollingWindowSection.tsx`
- `frontend/src/components/analytics/TrendSummaryCard.tsx`
- `frontend/src/components/shared/testing/TestingScoreCard.tsx`
- `frontend/src/components/mapping/ColumnMappingModal.tsx`
- `frontend/src/components/mapping/MappingToolbar.tsx`
- `frontend/src/components/mapping/AccountTypeDropdown.tsx`
- `frontend/src/components/sensitivity/SensitivityToolbar.tsx`
- `frontend/src/components/sensitivity/WeightedMaterialityEditor.tsx`
- `frontend/src/components/upload/WorkbookInspector.tsx`
- `frontend/src/components/HeritageTimeline.tsx`
- `frontend/src/components/ActivityEntry.tsx`
- `frontend/src/components/clients/ClientCard.tsx`
- `frontend/src/components/clients/EditClientModal.tsx`
- `frontend/src/components/clients/CreateClientModal.tsx`
- `frontend/src/components/MaterialityControl.tsx`
- `frontend/src/components/SectionHeader.tsx`
- `frontend/src/components/statements/FinancialStatementsPreview.tsx`
- `frontend/src/__tests__/ColumnMappingModal.test.tsx`
