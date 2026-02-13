# Phase XXVII — Next.js App Router Hardening (Sprints 204–209) — COMPLETE

> **Source:** Comprehensive Next.js App Router audit (2026-02-13) — 4-agent parallel analysis
> **Strategy:** Error boundaries first (P0), then route groups to eliminate duplication, then provider/fetch cleanup, then shared skeletons
> **Scope:** 0 loading.tsx → 11 loading files, 0 error.tsx → 7 error boundaries, 0 route groups → 4 groups, 38 duplicated imports eliminated, DiagnosticProvider scoped, 8 direct fetch() migrated, 5 shared skeleton components
> **Deferred:** Cookie-based auth migration (enables SSR/SSG for marketing pages) — too large for this phase

## Sprint Summary

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 204 | Global Error Infrastructure (global-error, not-found, error) | 3/10 | COMPLETE |
| 205 | Marketing Route Group — 8 pages, shared layout | 4/10 | COMPLETE |
| 206 | Auth Route Group — 4 pages, shared layout | 4/10 | COMPLETE |
| 207 | Tool Layout Consolidation — ToolNav + VerificationBanner in layout | 5/10 | COMPLETE |
| 208 | Provider Scoping + Fetch Consolidation + Route Boundaries | 5/10 | COMPLETE |
| 209 | Shared Skeleton Components + Phase XXVII Wrap | 4/10 | COMPLETE |

## Impact Summary

- **Error Boundaries:** global-error.tsx (root layout fallback), not-found.tsx (branded 404), root error.tsx, tools/error.tsx, + 4 authenticated route error boundaries
- **Route Groups:** `(marketing)` (8 pages), `(auth)` (4 pages), `(diagnostic)` (2 pages), `tools/` (11 pages, enhanced layout)
- **Imports Eliminated:** ~60 duplicated imports across 23 pages (MarketingNav/Footer ×16, ToolNav/VerificationBanner ×22, DiagnosticProvider ×1)
- **Fetch Consolidation:** 8 direct `fetch()` calls → apiClient (apiPost/apiGet/apiDownload), manual getCsrfToken removed from 5 files
- **Provider Scoping:** DiagnosticProvider moved from global providers.tsx to `(diagnostic)` route group layout
- **Shared Skeletons:** 5 components (SkeletonPage, CardGridSkeleton, FormSkeleton, ListSkeleton, UploadZoneSkeleton) used by 8 loading.tsx files
- **Loading Coverage:** Every authenticated route now has a loading.tsx skeleton

## Key Design Decisions

1. **Route groups are URL-transparent** — ThemeProvider DARK_ROUTES never needed updating
2. **Auth layout provides static structure only** — animation variants stay in pages (containerVariants/itemVariants tightly coupled to per-page content stagger)
3. **ToolNav uses pathname-based mapping** — `SEGMENT_TO_TOOL` Record derives currentTool from `usePathname()`
4. **VerificationBanner is self-contained** — checks auth/verified internally, per-page conditionals were redundant
5. **DiagnosticProvider needs shared layout** — flux/recon share state via `setResult`/`result`, per-page wrapping would break cross-page state
6. **Stale `.next` cache after file moves** — `rm -rf .next` required before rebuild when using `git mv`

## Files Created (across all sprints)

### Error Boundaries
- `app/global-error.tsx` — standalone with own html/body, inline obsidian styles
- `app/not-found.tsx` — server component 404, explicit dark classes
- `app/error.tsx` — root error boundary, semantic tokens
- `app/tools/error.tsx` — tool-specific error boundary
- `app/engagements/error.tsx`, `app/portfolio/error.tsx`, `app/settings/error.tsx`, `app/history/error.tsx`

### Route Group Layouts
- `app/(marketing)/layout.tsx` — MarketingNav + MarketingFooter
- `app/(auth)/layout.tsx` — centering + "Back to Paciolus"
- `app/(diagnostic)/layout.tsx` — DiagnosticProvider

### Loading Skeletons
- `app/tools/loading.tsx`, `app/engagements/loading.tsx`, `app/portfolio/loading.tsx`
- `app/settings/loading.tsx`, `app/history/loading.tsx`, `app/status/loading.tsx`
- `app/(diagnostic)/flux/loading.tsx`, `app/(diagnostic)/recon/loading.tsx`

### Shared Skeleton Components
- `components/shared/skeletons/SkeletonPage.tsx` — universal page wrapper
- `components/shared/skeletons/CardGridSkeleton.tsx` — configurable card grid
- `components/shared/skeletons/FormSkeleton.tsx` — form field sections
- `components/shared/skeletons/ListSkeleton.tsx` — timeline/list rows
- `components/shared/skeletons/UploadZoneSkeleton.tsx` — file upload zone
- `components/shared/skeletons/index.ts` — barrel export
