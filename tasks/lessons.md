# Lessons Learned

> **Protocol:** After ANY correction from the CEO or discovery of a better pattern, document it here. Review at session start.

---

## Process & Strategy

### Commit Frequency Matters
Each sprint = at least one atomic commit. Format: `Sprint X: Brief Description`. Stage specific files, never `git add -A`.

### Verification Before Declaring Complete
Before marking ANY sprint complete: `npm run build` + `pytest` (if tests modified) + Zero-Storage compliance check.

### Stability Before Features
Prioritize: 1) Stability (error handling, security) → 2) Code Quality (extraction, types) → 3) User Features (new functionality). Quick wins first within each tier.

### Test Suites Before Feature Expansion
Before expanding a module, create comprehensive tests for existing functionality. Cover edge cases (div-by-zero, negatives, boundaries).

### Test Fixture Data Must Match Requirements
Shared fixtures for common scenarios. Test-specific data for edge cases. Don't rely on shared fixtures for division-by-zero tests.

### Phase Wrap Sprints Are Pure Verification
**Observed across:** Sprints 110, 120, 130, 163. Write zero lines of application code. Run full backend test suite, frontend build, and guardrail checks. Documentation updates only. This pattern consistently catches inconsistencies.

### Extract Shared Components at the Right Time
Sprint 81 extracted ToolNav after 5 copies existed. Sprint 90 extracted shared enums before building Tool 7. Sprint 136-141 extracted testing components after 7+ copies stabilized. **Rule:** Extract after the second consumer appears for small utilities; extract after patterns stabilize across 7+ consumers for large component sets. During rapid feature delivery, cloning is correct — schedule a deduplication phase once feature velocity slows.

### Product Review Pays for Itself in Sprint 1
The 4-agent product review (Phase XIII) identified 51 findings. Sprint 121 alone fixed 7 P0 items. Without the review, issues like Tailwind shade gaps affecting 74 files would have accumulated silently.

---

## Architecture & Backend Patterns

### Engagement Management ≠ Engagement Assurance
Distinguish clearly between workflow features (tracking tools, organizing follow-ups — project management) and assurance features (risk scoring, deficiency classification — auditor judgment). Paciolus detects data anomalies; auditors assess control deficiencies. Never auto-classify using audit terminology (Material Weakness, Significant Deficiency). Use "Data Anomalies" and "Follow-Up Items" instead.

### Disclaimers Cannot Rescue Misaligned Features
If a feature's implied workflow crosses professional standards boundaries, rename and redesign the feature — don't just add warning text. Regulators (PCAOB, FRC) assess the tool's purpose, not its disclaimers.

### Zero-Storage Boundary: Metadata vs Transaction Data
Auth DB = emails + hashes only. DiagnosticSummary = aggregate totals only. Client table = name + industry only. Financial data is always ephemeral.

### Two-Phase Flow for Complex Uploads
When uploads need user decisions: 1) Inspection endpoint (fast metadata) → 2) Modal for user choice → 3) Full processing with selections.

### Dynamic Materiality: Formula Storage vs Data Storage
Store the formula config (type, value, thresholds). Never store the data it operates on. Evaluate at runtime with ephemeral data. Priority chain: session override → client → practice → system default.

### Factory Pattern for Industry-Specific Logic
Abstract base class + factory map for per-industry implementations. Unmapped industries fall back to GenericCalculator.

### Multi-Tenant Data Isolation
Always filter by `user_id` at the query level: `Client.user_id == user_id`. Never fetch-then-check.

### Optional Dependencies for External Services
External APIs (SendGrid, Stripe) should be optional imports with graceful fallback. Tests should run without API keys.

### Vectorized Pandas vs iterrows()
Replace `.iterrows()` with `groupby().agg()`. For 10K+ rows, iterate unique accounts (~500) instead of all rows. 2-3x improvement.

### Config-Driven Shared Modules for Cross-Engine Patterns
**Discovered:** Sprint 152. Use config objects (FieldQualityConfig, accessor callables) to parameterize shared functions rather than forcing all engines into one shape. Partial adoption (AR: CS only, TWM: neither) is better than force-fitting. This pattern powered column_detector (9 engines), memo_template (7 generators), testing_route (6 routes), data_quality (7 engines), and test_aggregator (7 engines).

### Callback-Based Factory Over Parameter-Heavy Abstraction
**Discovered:** Sprint 156. The `run_single_file_testing()` factory takes a `run_engine` callback rather than parameterizing all engine signature variations. Each route provides a lambda with its specific kwargs. Exclude multi-file routes (TWM, AR) where the factory adds more complexity than it removes.

### Priority Ordering in Greedy Column Assignment
**Discovered:** Sprint 151. When multiple field configs match the same column name (e.g., "cost" matches both `cost` and `accum_depr`), lower `priority` numbers are assigned first. Always assign the most specific columns first.

### Guardrail Tests Must Inspect Module, Not Function
**Discovered:** Sprint 157. After refactoring memo generators to delegate to shared template, `inspect.getsource(function)` no longer contains ISA references — they're in module-level config. Use `inspect.getsource(inspect.getmodule(function))` instead. Source-code guardrail tests are brittle under refactoring.

### Centralized Error Sanitization
**Discovered:** Sprint 122. Use regex patterns to match common exception types (pandas, openpyxl, SQLAlchemy, reportlab) and map to user-friendly messages. `except ValueError` is safe (controlled messages); `except Exception` leaks tracebacks and needs sanitization.

### Rate Limiting Requires `Request` as First Parameter
Slowapi's `@limiter.limit()` decorator requires FastAPI `Request` as first positional parameter. When a Pydantic body model is already named `request`, rename it to `payload`.

### Upload Validation in Two Layers
Content-type and extension checks in `validate_file_size` (before bytes consumed). Encoding fallback and row count checks in `parse_uploaded_file` (during parsing). Short-circuit early.

---

## Frontend Patterns

### framer-motion Type Assertions
TypeScript infers `'spring'` as `string`, but framer-motion expects literal types. Always use `as const` on transition properties. Applies to ALL framer-motion transitions extracted to module-level consts.

### God Component Decomposition — Extract Hook First
**Discovered:** Sprint 159. When decomposing a god component: (1) extract the custom hook with ALL logic first, (2) extract self-contained presentational sub-components, (3) the page becomes a thin layout shell. Tests pass without modification because jest.mock applies at module level.

### useEffect Referential Loop Prevention
Use `useRef` to track previous values. Compare prev vs current before triggering effects. For multiple params, use composite hash comparison.

### Modal Result Handling
Always check async operation result before closing modal. `if (await action()) closeModal()` — never fire-and-forget. Show errors IN the modal, not after it closes.

### Next.js Suspense Boundary for useSearchParams
Pages using `useSearchParams()` must wrap content in `<Suspense>`. Build-time requirement in Next.js 14+.

### TypeScript Type Guards with Array.filter()
`.filter(x => x)` doesn't narrow types. Use type predicate: `.filter((entry): entry is { key: string } => entry !== undefined)`.

### Ghost Click Prevention
File inputs with `position: absolute; inset: 0` capture unintended clicks. Fix: `pointer-events-none` + `tabIndex={-1}` when not in idle state.

### Severity Type Mismatch
Frontend `Severity` is `'high' | 'low'` only. `medium_severity` exists only as a count in RiskSummary. Always verify TypeScript types before assuming backend enum values map 1:1.

### useOptionalEngagementContext for Backward Compatibility
**Discovered:** Sprint 103. Returns `null` instead of throwing when no provider is present. Lets `useAuditUpload` auto-inject `engagement_id` when wrapped, silently skip when standalone.

### Hook-Level Integration Minimizes Page Changes
**Discovered:** Sprint 103. By injecting engagement logic into `useAuditUpload`, 5 of 7 tools got engagement support with zero page changes. Only TB (custom fetch) and Multi-Period (JSON body) needed explicit changes.

### Data-Driven Config Sections Beat Code Duplication
**Discovered:** Sprint 160. Four 170-line testing config sections collapsed into one 218-line shared component + 4 config arrays (~55 lines). Key: `ThresholdField[]` with `displayScale`, `prefix`/`suffix`, and `children` slot for edge cases.

### Factory Functions for Identical Hook Wrappers
**Discovered:** Sprint 161. 9 testing hooks (35-45 lines each) collapsed to `createTestingHook<T>()` factory (36 lines). Multi-file hooks pass custom `buildFormData` — no special casing needed.

### Centralize Environment Variables as Constants
**Discovered:** Sprint 161. 14 files declared `const API_URL = process.env.NEXT_PUBLIC_API_URL` locally. A single `utils/constants.ts` with fallback handles all cases. `minutes()` / `hours()` helpers make TTL configs self-documenting.

### `useState` Initializer Is NOT `useEffect`
**Discovered:** Sprint 162. `useState(() => { fetchIndustries() })` abuses the lazy initializer — runs synchronously during render. Always use `useEffect` for mount-time data fetching.

### Generic TypeScript Interfaces via Type Parameters and Slots
**Discovered:** Sprint 137. `BaseCompositeScore<TFinding = string>` handles Payroll's structured findings. `DataQualityBadge`'s `extra_stats?: ReactNode` slot handles AR's unique display. `FlaggedEntriesTable`'s `ColumnDef<T>` handles 7 table schemas. Use `object` constraint with explicit cast for generic form components (Sprint 160).

### CSS Custom Properties Don't Support Tailwind Opacity Modifiers
**Discovered:** Sprint 124. `bg-surface-card/50` doesn't work. Design semantic tokens with opacity built into the variable, or use separate tokens for different opacity needs.

### Modal Overlays Are NOT Dark-Theme Remnants
`bg-obsidian-900/50` is correct on both themes — semi-transparent dark backdrops dim whatever's behind the modal.

### Dark-Pinned Components Use `data-theme="dark"` Attribute
**Discovered:** Sprint 124. ToolNav and ToolLinkToast stay dark on light pages via `data-theme="dark"` on their wrapper element.

### JSX String Apostrophe Escaping
**Discovered:** Sprint 131. Background agents create TSX with unescaped apostrophes (`what's`, `it's`, `Children's`). Always scan agent output and fix with `\u0027` or `&apos;`.

---

## Testing Patterns

### Z-Score Fixtures Need Large Populations
With only 20 entries, a single outlier shifts the mean and stdev significantly. Use 100+ base entries to produce expected z-scores for HIGH severity thresholds.

### Benford Test Data Must Span Orders of Magnitude
Amounts must span 2+ orders of magnitude to pass prechecks. Use amounts like 50+, 500+, 5000+.

### Scoring Calibration: Comparative Over Absolute
Use `assert clean_score.score < moderate_score.score < high_score.score` rather than asserting absolute tiers, which change as tests are added.

### SignificanceTier Enum vs String in Tests
When constructing test dataclasses that use enums, always use the enum member, not its string value.

### Pytest Collection of Engine Functions
Functions named `test_*` in engine files are collected by pytest. Either don't use `test_` prefix, or import with aliases: `from engine import test_foo as run_foo_test`.

### `jest.clearAllMocks()` Does NOT Reset `mockReturnValue`
Must explicitly re-set default mock values in `beforeEach` after `clearAllMocks()`.

### Mock Result Shapes Must Match Inline Property Access
Even when child components are mocked, the page evaluates prop expressions like `result.summary.matches` before passing to the mock. Always check page source for inline property chains.

### framer-motion Test Mock Must Strip Motion Props
Spreading all props from `motion.div` onto a real `<div>` passes invalid HTML attributes. Destructure out `initial`, `animate`, `exit`, `transition`, `variants`, `whileHover`, etc. before spreading rest props.

### Mock Barrel Exports Must Include ALL Named Exports
When mocking a barrel file (`@/components/shared`), include ALL named exports the page uses, not just one.

### Hook Method Names Must Match Page Destructuring
Always verify the page's `const { ... } = useHook()` line before writing mock return values.

### SQLite FK Constraints Need PRAGMA
FK constraints NOT enforced by default. Need `PRAGMA foreign_keys=ON` via engine event listener in conftest.py.

### SQLite Strips Timezone from Datetime Columns
Compare with `.replace(tzinfo=None)` when mixing DB-loaded and fresh timezone-aware datetime values.

### SQLAlchemy Backref Passive Deletes
When deleting a parent with related children, use `backref=backref("items", passive_deletes=True)` to let DB handle CASCADE instead of SQLAlchemy's default SET NULL behavior.

### Test Import Redirection Preserves Compatibility
When extracting helpers into shared modules, test files can use `from shared.module import func as _old_name` — same alias, zero test body changes.

### Ghost Employee Tests Affect "Clean" Fixture Design
Tests that flag single-entry employees mean clean fixtures must ensure each employee has 2+ entries across different months.

---

## Design & Deployment

### Premium Restraint for Alerts
Left-border accent (not full background), subtle glow at low opacity, typography hierarchy over color.

### CSS Custom Properties Bridge Tailwind and Runtime Theming
Define semantic CSS variables in `:root` (dark defaults) with `[data-theme="light"]` overrides in `globals.css`, reference via Tailwind token aliases. Route-based theming via `usePathname`, not user toggle.

### ScoreCard Tier Gradients → Left-Border Accents on Light Theme
Dark theme used gradient backgrounds for risk tier encoding. On light backgrounds, use `border-l-4 border-l-{tier-color}` instead.

### RISK_TIER_COLORS Must Use Solid Fills for Light Theme
Replace opacity colors (`bg-sage-500/10`) with solid palette fills (`bg-sage-50`, `text-sage-700`, `border-sage-200`).

### `prefers-reduced-motion` Should Skip, Not Slow Down
Don't show a faster animation — skip it completely and call `onComplete` immediately.

### Memo "Download Memo" as Primary, "Export CSV" as Secondary
PDF memos are the higher-value audit artifact. Make memo button visually primary (sage-600 filled) to guide users toward the more useful export.

### Memo Data Shape Must Match Tool Output
Always check the frontend data shape (hook response) before designing a memo generator. Design the Pydantic input model from the hook's TypeScript types first.

### Multi-Stage Docker Builds
Separate deps → builder → runner stages. Only runtime in final image. Non-root users. Health checks. `sqlite:////app/data/paciolus.db` (4 slashes = absolute path).

### .dockerignore Prevents Secrets in Build Context
Without `.dockerignore`, `docker build` sends everything (`.env`, `paciolus.db`) to the daemon, even if not COPY'd.

### ReportLab Best Practices
Use get-or-create for styles (avoid "already defined" error). Use `onFirstPage`/`onLaterPages` callbacks for repeating elements. Wrap table cell text in `Paragraph` objects. Prefer built-in fonts.

### Tailwind Silently Drops Undefined Color Shades
Classes referencing undefined shades simply produce no CSS — no warnings. Always define the full shade range (50-900) when a scale is used extensively.

### Single Version Source of Truth
Extract version to `backend/version.py` with `__version__`. Import everywhere. Future bumps require exactly one edit.

---

## Adding New Tools — Cascade Checklist

### ToolName Enum Cascade (4-file, N-assertion update)
**Observed across:** Sprints 104, 107, 114. When adding a new `ToolName`: (1) add to enum, (2) add to `TOOL_LABELS`, (3) add to `TOOL_LEAD_SHEET_REFS`, (4) grep tests for hardcoded tool counts (e.g., `== 9`). Update `test_anomaly_summary.py`, `test_engagement.py`, `test_workpaper_index.py`.

### Frontend Tool 4-Location Cascade
**Observed across:** Sprints 106, 109, 116, 119. New tool frontend requires: (1) `ToolNav.tsx` (ToolKey type + TOOLS array), (2) `app/page.tsx` (toolCards + nav + tool count copy), (3) `types/engagement.ts` (ToolName + TOOL_NAME_LABELS + TOOL_SLUGS), (4) tool's own files (types, hook, 4 components, page).

### Frontend Tool Pages Are a 4-File Formula
**Observed across:** Sprints 106, 116, 119. Types file → Hook (thin `useAuditUpload` wrapper via `createTestingHook`) → 4 components (ScoreCard, TestResultGrid, DataQualityBadge, FlaggedTable) → Page.

### Memo Generators Are Config-Driven (5 minutes)
**Observed across:** Sprints 105, 115, 118. With `shared/memo_template.py`: define test descriptions dict, methodology intro, risk-tier conclusions, ISA references. ~90 lines per generator.

---

## Phase Retrospectives

### Phase VI (Sprints 61-70)
Delivered Multi-Period Comparison + JE Testing (18-test battery). ~400 new tests. **Key lesson:** Frontend auth gating must be 3-state (guest/authenticated/verified), not 2-state. Wrap-up sprints catch inconsistencies that individual feature sprints miss.

### Phase VII (Sprints 71-80)
Delivered Financial Statements + AP Testing + Bank Reconciliation. ~248 new tests. **Key lesson:** Navigation consistency requires a dedicated wrap-up sprint — establish shared patterns early. Leverage-first feature selection (highest reuse) ships fastest.

### Phase VIII (Sprints 83-89)
Delivered Cash Flow Statement + Payroll Testing. Fastest feature phase. **Key lesson:** The clone pattern compounds — each new tool ships faster. Cross-sprint dependency ordering matters for ToolNav (update when consuming page ships, not in wrap sprint).

### Phase IX (Sprints 90-96)
Delivered shared testing utilities + Three-Way Match + Classification Validator. **Key lesson:** Extract shared utilities BEFORE building the next tool. Classification validators should be structural-only (information/detection, not advisory) to avoid liability.

### Phase X (Sprints 96.5-102)
Delivered full engagement workflow layer without violating 8 guardrails. **Key lessons:** Narratives-only data model kept financial data out of storage. Post-completion aggregation kept tool routes independent. Per-tool-run scores avoided ISA 315 composite scoring trap.

### Phase XV (Sprints 136-141)
Deduplicated ~4,750 lines across 11-tool testing suite. **Key lesson:** Generic TypeScript interfaces handle domain variation via type parameters (`BaseCompositeScore<TFinding>`) and ReactNode slots (`extra_stats`). Backward-compatible type aliases prevent cascading import changes. Context directory consolidation is safe mechanical mass-rename, not risky refactor.

### Phase XVII (Sprints 151-163)
12 sprints of structural refactoring, zero behavioral regressions. **What worked:** Config-driven shared modules (one module replaces 6-9 copies), factory pattern scales cleanly for new tools. **What to watch:** `audit_engine.py` at 1,393 lines remains largest file; Revenue Benford was excluded from shared module (structurally different). **Metrics:** 15 new shared files, 9,298 added / 8,849 removed, +123 new backend tests.

### Phase XVIII (Sprints 164-170)
7 sprints of async architecture remediation, zero behavioral regressions. **Key lessons:** (1) `def` is the correct FastAPI default unless the handler explicitly `await`s — FastAPI auto-threadpools `def` handlers, making sync SQLAlchemy safe. (2) `asyncio.to_thread()` is the right pattern for CPU-bound Pandas work in `async def` handlers that must `await` file validation. (3) `BackgroundTasks` for non-critical success-path work (email, metadata recording); keep error-path synchronous for reliability. (4) Context managers (`memory_cleanup()`) guarantee resource cleanup regardless of early returns or exceptions — always prefer over manual try/finally. **What to watch:** Full AsyncSession migration (aiosqlite) deferred to Phase XIX if threadpool proves insufficient under production load.

### Phase XIX (Sprints 171-177)
7 sprints of API contract hardening, zero behavioral regressions. **Key lessons:** (1) Error-in-body anti-pattern (returning `{"error": "...", "analysis": null}` as 200) leaks into frontend types as `error?`/`message?` optional fields — converting to HTTPException(422) eliminates the dual-shape response and simplifies both backend and frontend contracts. (2) When removing optional fields from TypeScript types, search ALL components consuming the type (not just hooks) — `RollingWindowSection.tsx` referenced `data.error` but wasn't in the initial plan. (3) `response_model=dict` is a valid placeholder for complex engine `.to_dict()` results; full typing can follow when engines are refactored. (4) Frontend `apiClient.ts` already handled 204 and 201 via `response.ok` — DELETE→204/POST→201 changes required zero frontend modifications. (5) trends.py endpoints were still `async def` (missed in Phase XVIII) — caught during Sprint 175 as a bonus fix.

### Phase XXII (Sprints 184-190)
7 sprints of Pydantic model hardening, zero behavioral regressions. **Key lessons:** (1) Always verify plan's Literal/Enum values against actual source code — Sprint 185 plan specified `Literal["active", "completed", "archived"]` for EngagementStatus but the actual enum only has active/archived. Using actual Enum types over Literal avoids this. (2) `min_length=1` on list fields can break edge cases — multi-period comparison legitimately accepts empty lists for all-new/all-closed account detection; Sprint 186 required a revert. (3) `@model_validator(mode='before')` enables backward-compatible model decomposition — DiagnosticSummaryCreate was split into 3 sub-models while still accepting the flat JSON format from the frontend. (4) Pydantic v2 `field_validator` centralizes validation in the schema layer, eliminating standalone validation functions and manual calls scattered across routes — single source of truth for password complexity rules.

### Phase XXIII (Sprints 191-194)
4 sprints of Pandas performance and precision hardening, zero behavioral regressions. **Key lessons:** (1) `detect_abnormal_balances()` (standalone function) uses keyword matching but the streaming pipeline uses the classifier-based `StreamingAuditor.get_abnormal_balances()` — tests for vectorized keyword matching must call the standalone function directly, not the full pipeline. (2) `float('inf')` in JSON is not valid JSON — replacing with `None` for zero-prior percentages is both more correct and JSON-safe. (3) `max(abs(x), 0.01)` as a division guard is problematic because `0.01` is an arbitrary magic number that inflates percentages near zero — using config tolerances as the threshold with a 100% cap is semantically cleaner. (4) `math.fsum` is a true drop-in for `sum` on generators of floats — no signature changes, no test changes needed. (5) Identifier column dtype preservation must be post-read (not `dtype=str` globally) because `dtype=str` on all columns would break `pd.to_numeric` calls downstream.
