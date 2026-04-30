# ADR-017: Tool Page Architecture Template

**Status:** Accepted (Sprint 750 — multi-period pilot)
**Date:** 2026-04-29
**Decision-makers:** Engineering team

## Context

Tool pages under `frontend/src/app/tools/<tool>/page.tsx` historically
mixed several concerns inline:

- Upload state machines (file → loading → success/error transitions).
- Form metadata + label state (period labels, materiality, client info).
- Filter/search UI state.
- Export workflows (CSV / PDF memo download orchestration).
- Compare / analyze invocations against domain hooks.
- Composition + render JSX.

The multi-period page topped 500 lines with ~190 of them being mixed
state machinery + handlers. Tests had to mount the whole page to
exercise any one workflow, which made them slow and made regressions in
the upload state machine indistinguishable from regressions in the
render layer.

Phase 4 of the architectural remediation initiative (`tasks/todo.md`)
calls for a tool-page template that separates these concerns.

## Decision

Tool pages follow this composition pattern:

```
function ToolPage() {
  // 1. Context + auth
  const { user, token, ... } = useAuthSession()
  const engagement = useOptionalEngagementContext()

  // 2. Domain workflow hooks (one per concern, narrow API)
  const uploads = useToolUploads({ token, ... })
  const analysis = useToolAnalysis({ engagementId })
  const memoExport = useToolMemoExport(token)

  // 3. Local UI state (filters, tabs, view toggles)
  const [filterType, setFilterType] = useState('all')

  // 4. Local form state (labels, materiality, metadata)
  // — small / cohesive enough that a hook would be aesthetic-only.

  // 5. Page-level orchestration callbacks (thin glue)
  const handleCompare = useCallback(async () => {
    if (!uploads.canCompare) return
    await analysis.run(uploads.prior, uploads.current, ...)
  }, [...])

  // 6. Render — JSX only, no inline state machines
  return <Layout>...</Layout>
}
```

### Hook responsibilities

- **`use<Tool>Uploads`** — file-upload state machines, derived flags
  like `canCompare` / `anyLoading`, reset semantics. Shared shape:
  inputs (`token`, `materialityThreshold`, `engagementId`,
  `onBeforeUpload?`); outputs (slot states + handler functions +
  derived boolean flags + `reset`).
- **`use<Tool>Comparison` / `use<Tool>Analysis`** — domain workflow:
  POST to `/audit/<tool>` and friends, track `isAnalyzing`,
  `comparison`, `error`. (Already established pattern — multi-period
  uses `useMultiPeriodComparison`.)
- **`use<Tool>MemoExport`** — memo PDF download workflow: assemble
  the export payload, call `apiDownload`, trigger blob download. Track
  `exporting` flag for button disabling.

### Local-state vs hook decision

A workflow gets its own hook when **any** of these apply:

- More than ~15 lines of state-machine logic.
- Reused across two or more pages.
- Has an async operation that consumers must await.
- Should be unit-testable without rendering the page.

Otherwise, keep state inline. Filters and form metadata are typically
inline because their state is simple and their lifetime is the page's
mount.

### Presentational components

Components under `frontend/src/components/<tool>/` are presentational
only. They accept shaped props and render JSX. They do not own the
workflow state — the page (or hook) does.

## Pilot — multi-period (Sprint 750)

The multi-period page was decomposed into:

- `usePeriodUploads(options)` — three `PeriodState` slots (prior /
  current / budget), `auditFile` machine, `showBudget` toggle, derived
  `canCompare` / `anyLoading`, `reset`. 142 lines.
- `useMultiPeriodMemoExport(token)` — assembles the memo payload from
  a `MovementSummaryResponse` + metadata, calls `apiDownload`,
  triggers `downloadBlob`. 81 lines.
- Page composition root: 423 lines (down from 501; the remainder is
  predominantly JSX + form-field state).

Both new hooks have direct unit tests:
`__tests__/usePeriodUploads.test.ts` (8 tests) and
`__tests__/useMultiPeriodMemoExport.test.ts` (8 tests). Tests mock
`uploadTrialBalance` / `apiDownload` rather than rendering the page —
the speed and isolation gain is the template's headline benefit.

## Migration approach

- Apply incrementally: start with the largest page or the highest-risk
  surface (multi-period was both).
- Each migration is one PR per page. Hook extractions land before the
  page's JSX is touched.
- The template is **not** a pre-imposed framework — it documents what
  good tool-page composition looks like once you've extracted the
  hooks. Pages with simpler workflows can deviate (single hook,
  inline state) when the size/complexity doesn't warrant the split.

## Consequences

- Tool pages become composition roots — easier to read, easier to
  PR-review.
- Hooks become unit-testable in isolation. Page tests focus on
  interaction + render contract.
- New tool pages start from the template instead of growing organically
  to 500+ lines.
- Hooks that are reused across tools (e.g., a future
  `useFilterControls`) become natural candidates for
  `frontend/src/hooks/`.

## Alternatives considered

- **Single mega-hook per tool** (`useMultiPeriodTool()`). Rejected —
  loses isolation: the upload state machine and the export workflow
  have different lifetimes and different test surfaces.
- **Class-based composition / context providers per tool.** Rejected —
  React idiom is hooks; context providers make sense when state must
  be shared across distant components, not for a single page's local
  state.
- **Codemod-driven mass migration.** Rejected — each tool page has
  bespoke domain workflows that need careful extraction. Manual,
  one-page-at-a-time is safer.

## See also

- `frontend/src/hooks/usePeriodUploads.ts` — pilot upload hook.
- `frontend/src/hooks/useMultiPeriodMemoExport.ts` — pilot memo-export hook.
- `frontend/src/__tests__/usePeriodUploads.test.ts` — hook test pattern.
- ADR-014 (frontend network) — `apiClient` is the canonical entry the
  memo-export hook uses.
- Sprint 751 will apply the template to the dashboard page next.
