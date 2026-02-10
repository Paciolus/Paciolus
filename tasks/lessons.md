# Lessons Learned

> **Protocol:** After ANY correction from the CEO or discovery of a better pattern, document it here. Review at session start.

---

## Template

When adding a lesson, use this format:

```
### [DATE] — [Short Title]
**Trigger:** What happened that led to this lesson?
**Pattern:** What's the rule or principle to follow?
**Example:** Concrete example of the right way to do it.
```

---

## Process & Strategy

### Commit Frequency Matters
**Trigger:** Audit scored 4/5 due to only 3 commits for 24 sprints.
**Pattern:** Each sprint = at least one atomic commit. Format: `Sprint X: Brief Description`. Stage specific files, never `git add -A`.

### Verification Before Declaring Complete
**Pattern:** Before marking ANY sprint complete: `npm run build` + `pytest` (if tests modified) + Zero-Storage compliance check. Added to CLAUDE.md Directive Protocol.

### Stability Before Features
**Pattern:** Prioritize: 1) Stability (error handling, security) → 2) Code Quality (extraction, types) → 3) User Features (new functionality). Quick wins first within each tier.

### Test Suites Before Feature Expansion
**Pattern:** Before expanding a module, create comprehensive tests for existing functionality. Cover edge cases (div-by-zero, negatives, boundaries). The 47 ratio engine tests made adding 4 new ratios safe.

### Test Fixture Data Must Match Requirements
**Trigger:** Sprint 27 — ROA tests failed because shared fixture had wrong values for the test scenario.
**Pattern:** Shared fixtures for common scenarios. Test-specific data for edge cases. Don't rely on shared fixtures for division-by-zero tests.

---

## Architecture & Patterns

### 2026-02-08 — Engagement Management ≠ Engagement Assurance
**Trigger:** Council initially proposed "Engagement Dashboard" with composite risk scoring and Management Letter Generator. AccountingExpertAuditor rejected both as ISA 265/315 violations. After deliberation, council converged on Path C: engagement workflow without audit assurance.
**Pattern:** When building engagement-level features, distinguish clearly between:
- **Workflow features** (tracking which tools were run, organizing follow-up items) — these are project management, NOT audit methodology
- **Assurance features** (risk scoring, deficiency classification, management letters) — these require auditor judgment and cross into regulated territory
The boundary: Paciolus detects data anomalies. Auditors assess control deficiencies. Never auto-classify findings using audit terminology (Material Weakness, Significant Deficiency). Use "Data Anomalies" and "Follow-Up Items" instead.
**Example:** An engagement workspace showing "JE Testing: Complete, AP Testing: Not Started" is workflow. A composite risk score saying "Engagement Risk: HIGH" is assurance. The former is safe; the latter requires ISA 315 inputs.

### 2026-02-08 — Disclaimers Are Not Sufficient for Feature Misalignment
**Trigger:** Council proposed adding disclaimers to Management Letter Generator to make it ISA 265-safe. AccountingExpertAuditor rejected: "The feature itself is the problem, not the wording. It's like providing a draft audit opinion with a disclaimer saying auditor must verify."
**Pattern:** Disclaimers cannot rescue a fundamentally misaligned feature. If a feature's implied workflow crosses professional standards boundaries, rename and redesign the feature — don't just add warning text. Regulators (PCAOB, FRC) assess the tool's purpose, not its disclaimers.

### Zero-Storage Boundary: Metadata vs Transaction Data
**Pattern:** When adding storage, document explicitly what IS stored vs NEVER stored. Auth DB = emails + hashes only. DiagnosticSummary = aggregate totals only. Client table = name + industry only. Financial data is always ephemeral.

### Two-Phase Flow for Complex Uploads
**Pattern:** When uploads need user decisions: 1) Inspection endpoint (fast metadata) → 2) Modal for user choice → 3) Full processing with selections. Used for: sheet selection (Sprint 11), column mapping (Sprint 9.2).

### Dynamic Materiality: Formula Storage vs Data Storage
**Pattern:** Store the formula config (type, value, thresholds). Never store the data it operates on. Evaluate at runtime with ephemeral data. Priority chain: session override → client → practice → system default.

### Factory Pattern for Industry-Specific Logic
**Pattern:** Abstract base class + factory map for per-industry implementations. Unmapped industries fall back to GenericCalculator. Adding a new industry = one file change.

### Multi-Tenant Data Isolation
**Pattern:** Always filter by `user_id` at the query level: `Client.user_id == user_id`. Never fetch-then-check. Foreign key constraints enforce referential integrity.

### Multi-Line Journal Entry Validation (Sprint 52)
**Pattern:** Each line has debit OR credit (not both). Entry-level validation: total debits == total credits. Status workflow: proposed → approved → posted. Session-only storage for Zero-Storage compliance. Multi-line is the standard, not the exception.

### Optional Dependencies for External Services
**Pattern:** External APIs (SendGrid, Stripe) should be optional imports with graceful fallback. Tests should run without API keys.
```python
try:
    from sendgrid import SendGridAPIClient
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
```

### Vectorized Pandas vs iterrows()
**Pattern:** Replace `.iterrows()` with `groupby().agg()`. For 10K+ rows, iterate unique accounts (~500) instead of all rows. 2-3x performance improvement.

---

## Frontend Patterns

### framer-motion Type Assertions (Recurring)
**Pattern:** TypeScript infers `'spring'` as `string`, but framer-motion expects literal types. Always use `as const` on transition properties:
```tsx
transition: { type: 'spring' as const, ease: 'easeOut' as const }
```
**Affected across:** SensitivityToolbar, CreateClientModal, ProcessTimeline, DemoZone variants. Apply to ALL framer-motion transitions extracted to module-level consts.

### useEffect Referential Loop Prevention
**Pattern:** Use `useRef` to track previous values. Compare prev vs current before triggering effects. For multiple params, use composite hash comparison (`computeAuditInputHash`).

### React.memo for Animation-Heavy Components
**Pattern:** Wrap components with expensive animations in `React.memo()`. Add `displayName`. Move constants outside component. Use `useCallback` for handlers passed to memoized children.

### Modal Result Handling
**Pattern:** Always check async operation result before closing modal. `if (await action()) closeModal()` — never fire-and-forget. Show errors IN the modal, not after it closes.

### Next.js Suspense Boundary for useSearchParams
**Pattern:** Pages using `useSearchParams()` must wrap content in `<Suspense>`. Extract inner component, wrap default export. Build-time requirement in Next.js 14+.

### TypeScript Type Guards with Array.filter()
**Pattern:** `.filter(x => x)` doesn't narrow types. Use type predicate:
```typescript
.filter((entry): entry is { key: string; ratio: RatioData } => entry.ratio !== undefined)
```

### Auth Context as Root-Level Provider
**Pattern:** Create `providers.tsx` client component wrapping all context providers. Import into server-side `layout.tsx`. Clean separation of server/client components.

### Ghost Click Prevention
**Pattern:** File inputs with `position: absolute; inset: 0` capture unintended clicks. Fix: `pointer-events-none` + `tabIndex={-1}` when not in idle state.

### Severity Type Mismatch (Sprint 60)
**Pattern:** Frontend `Severity` is `'high' | 'low'` only. `medium_severity` exists only as a count in RiskSummary. Always verify TypeScript types before assuming backend enum values map 1:1.

---

## Backend Patterns

### Timezone-Aware Datetime Comparisons
**Pattern:** SQLite stores naive datetimes. When comparing with `datetime.now(UTC)`, normalize first:
```python
if self.expires_at.tzinfo is None:
    expires = self.expires_at.replace(tzinfo=timezone.utc)
```

### Per-Sheet Column Detection
**Pattern:** Multi-sheet audits must run column detection independently per sheet. Track per-sheet mappings. Warn if column orders differ. Prevents silent data corruption.

### Weighted Heuristics for Classification
**Pattern:** Use weighted keyword scoring with confidence thresholds instead of binary matching. Multiple matches increase confidence. Single low-weight matches get flagged for review.

### Inverse Relationship for Weighted Materiality
**Pattern:** Higher weight = lower threshold (more scrutiny). Weight is a "scrutiny multiplier" not a "threshold multiplier". `threshold = base / weight`.

---

## Design & UI

### Premium Restraint for Alerts
**Pattern:** Left-border accent (not full background), subtle glow at low opacity, typography hierarchy over color. `border-l-4 border-l-clay-500 bg-obsidian-800/50` not `bg-red-500`.

### Terminology: API Stability vs UI Evolution
**Pattern:** Keep API endpoints unchanged (`/audit/trial-balance`). Update UI labels freely ("Export Diagnostic Summary"). Document the mapping for backwards compatibility.

### CSS Custom Properties for Theme System
**Pattern:** Store base colors as RGB triplets for `rgba()` composability. Pre-define variations (border, glow, subtle). Standardize transition durations to 3 values (fast/base/slow).

---

## Deployment

### Multi-Stage Docker Builds
**Pattern:** Separate deps → builder → runner stages. Only runtime in final image. Non-root users. Health checks. Next.js `output: 'standalone'` for ~100MB images instead of ~1GB.

### ReportLab: Style Collision + Page Callbacks + Paragraph Wrapping
**Pattern:** Use get-or-create for styles (avoid "already defined" error). Use `onFirstPage`/`onLaterPages` callbacks for repeating elements (disclaimers). Wrap table cell text in `Paragraph` objects for wrapping. Prefer built-in fonts (Times, Helvetica) over custom font embedding.

---

## Sprint Retrospectives & Dated Entries

### 2026-02-06 — Composition Over Modification for Multi-Way Comparison (Sprint 63)
**Trigger:** Needed three-way comparison but two-way engine was already tested with 63 tests.
**Pattern:** Wrap existing function rather than modifying it. `compare_three_periods()` calls `compare_trial_balances()` then enriches results with budget data. This preserves all existing tests and keeps the two-way path unchanged.
**Example:** Build budget lookup dict from normalized account names, iterate two-way movements and attach BudgetVariance objects. New endpoint `/audit/compare-three-way` is separate from `/audit/compare-periods`.

### 2026-02-06 — SignificanceTier Enum vs String in Tests (Sprint 63)
**Trigger:** Test `test_budget_variance_to_dict` failed because it passed string `"minor"` instead of `SignificanceTier.MINOR` enum. The `to_dict()` method called `.value` on a string.
**Pattern:** When constructing test dataclasses that use enums, always import and use the enum member, not its string value. Verify serialization output separately.
**Example:** `BudgetVariance(variance_significance=SignificanceTier.MINOR)` not `BudgetVariance(variance_significance="minor")`

### 2026-02-06 — Pytest Collection of Engine Functions (Sprint 64)
**Trigger:** Functions named `test_unbalanced_entries()`, `test_missing_fields()`, etc. in `je_testing_engine.py` were collected by pytest as test cases when imported, causing 5 errors.
**Pattern:** Never name production functions with `test_` prefix, OR import them with aliases in test files: `from engine import test_foo as run_foo_test`.
**Example:** `from je_testing_engine import test_unbalanced_entries as run_unbalanced_test`

### 2026-02-06 — Outlier Detection and Statistical Skew (Sprint 64)
**Trigger:** Tests expected outlier detection with only 9 normal entries + 1 outlier, but including the outlier in mean/stdev calculation inflated stdev so much the outlier fell within 3 standard deviations.
**Pattern:** When testing z-score outlier detection, use enough baseline entries (~25+) so the outlier doesn't dominate the stdev calculation. With N=10, a 1000x outlier won't flag; with N=30, it will.
**Example:** Use 29 entries at $100 + 1 at $100,000 instead of 9+1.

### 2026-02-06 — Benford Test Data Must Span Orders of Magnitude (Sprint 65)
**Trigger:** `test_nonconforming_data_detected` failed because all amounts were 5000-5099 (single order of magnitude), causing the Benford precheck to reject data before analysis.
**Pattern:** When generating non-Benford test data, amounts must span 2+ orders of magnitude to pass prechecks. Use amounts like 50+, 500+, 5000+ (all starting with same first digit but different magnitudes).
**Example:** `amt = 5 * (10 ** (i % 3 + 1)) + (i % 50)` produces 50s, 500s, and 5000s.

### 2026-02-06 — Scoring Calibration: Comparative Over Absolute (Sprint 65)
**Trigger:** `test_moderate_risk_gl` expected ELEVATED tier but got LOW (score 6.05) because weekend postings on clean GL entries diluted the risk signal across 8 tests.
**Pattern:** For composite scoring calibration, use comparative assertions (clean < moderate < high) rather than absolute tier assertions. Absolute tiers depend on the scoring formula's normalization which changes as tests are added.
**Example:** `assert clean_score.score < moderate_score.score < high_score.score` is more robust than `assert moderate_score.risk_tier == RiskTier.ELEVATED`.

### 2026-02-06 — CSPRNG for Audit Sampling (Sprint 69)
**Trigger:** QualityGuardian flagged `random.sample()` as non-compliant with PCAOB AS 2315 for audit sampling.
**Pattern:** Always use `secrets.SystemRandom()` for audit-related random sampling. The `secrets` module provides CSPRNG guarantees required by PCAOB and ISA 530. Record the seed (via `secrets.token_bytes`) for reproducibility.
**Example:** `rng = secrets.SystemRandom(); sampled = rng.sample(population, sample_size)`

### 2026-02-06 — FormData File Re-upload for Multi-Step Flows (Sprint 69)
**Trigger:** SamplingPanel needs the same GL file for both preview and execute steps, but FormData is single-use.
**Pattern:** Keep the `File` object reference and create a new `FormData` for each API call. The File object can be reused — it's the FormData that must be fresh. This works because the File reference is a blob handle, not consumed on first read.

### 2026-02-06 — Phase VI Retrospective (Sprints 61-70)
**Trigger:** Phase VI complete — 10 sprints delivering Multi-Period Comparison (Tool 2), Journal Entry Testing (Tool 3), platform rebrand, and diagnostic zone protection.
**Key outcomes:**
- 2 new tools added to the platform (multi-period 2-way/3-way comparison, JE testing with 18-test battery)
- ~400 new backend tests (625 → 1022), frontend 20 routes clean
- Stratified sampling engine with CSPRNG (PCAOB AS 2315)
- JE Testing Memo PDF export (PCAOB AS 1215 / ISA 530)
- Platform homepage rebrand with 3-tool showcase
**Pattern: Frontend auth gating must be 3-state, not 2-state.** Guest vs authenticated is insufficient — must also distinguish verified vs unverified. Two of three tools shipped without this check; caught in Sprint 70 wrap-up. Backend endpoint protection (`require_verified_user`) is necessary but not sufficient — frontend UX must also gate access to prevent misleading 403 errors.
**Pattern: Wrap-up sprints catch inconsistencies.** Low-complexity "protection + wrap" sprints are valuable for standardizing patterns across features built over multiple sprints by different agent leads.

### 2026-02-06 — FastAPI Field Import Source (Pre-Sprint 71 Refactor)
**Trigger:** After extracting routes into APIRouter modules, `pytest` failed with `ImportError: cannot import name 'Field' from 'fastapi'` in `routes/prior_period.py` and `routes/multi_period.py`.
**Pattern:** `Field` comes from `pydantic`, not `fastapi`. When splitting files that had a single combined import block, verify each symbol's origin. `APIRouter`, `HTTPException`, `Depends`, `Query` are from `fastapi`; `BaseModel`, `Field` are from `pydantic`.
**Example:** `from fastapi import APIRouter, Depends` + `from pydantic import BaseModel, Field` — never `from fastapi import Field`.

### 2026-02-06 — Phase VII Retrospective (Sprints 71-80)
**Trigger:** Phase VII complete — 10 sprints delivering Financial Statements (Tool 1 enhancement), AP Payment Testing (Tool 4), Bank Reconciliation (Tool 5), and 5-tool navigation standardization.
**Key outcomes:**
- 3 features shipped: Financial Statements (BS + IS from lead sheets), AP Testing (13-test battery), Bank Reconciliation (exact matching + bridge)
- ~248 new backend tests (1,022 → 1,270), frontend 22 routes clean
- AP Testing Memo PDF export (ISA 240 / ISA 500 / PCAOB AS 2401)
- Bank Rec CSV export with 4-section layout (matched, bank-only, ledger-only, summary)
- All 5 tool pages now have standardized cross-tool navigation
**Pattern: Navigation consistency requires a dedicated wrap-up sprint.** Each tool page was built by different agent leads across different sprints, resulting in 5 different nav styles (no links, rounded pills, border-bottom, etc.). Sprint 80's sole purpose was standardization — retroactively normalizing nav across all pages. Lesson: establish a shared nav component or pattern early; retrofitting is cheaper than inconsistency but more expensive than doing it right the first time.
**Pattern: Leverage-first feature selection works.** Phase VII prioritized features by reuse of existing engines (Financial Statements: 85% built, AP Testing: 70% clone, Bank Rec: 50% reuse). All three shipped on time with predictable complexity. The highest-reuse feature (Financial Statements) took only 2 sprints; the lowest (Bank Rec) took 3.

### 2026-02-06 — Extract Shared Components Early, Not Late (Sprint 81)
**Trigger:** Codebase audit found 5 tool pages with nearly identical 50-66 line navigation blocks and 3 pages with duplicated drag/drop handlers (~26 lines each). Also found a production-risk memory leak in session storage (no TTL, no eviction).
**Pattern: Shared UI components should be extracted when the second consumer appears, not after the fifth.** Sprint 80 standardized nav styles across 5 pages — but each page still had its own copy of the nav code. Sprint 81 extracted a single `ToolNav` component, reducing ~300 lines of duplicated JSX to 5 one-liner usages. The same applied to `useFileUpload` — 3 pages had identical drag/drop handlers that should have been a hook from Sprint 75 when AP Testing cloned JE Testing's pattern.
**Pattern: In-memory session stores need TTL + capacity limits from day one.** The adjustments session dict (`_session_adjustments`) had no expiration or size limit. In production with concurrent users, this is a memory leak. Adding `time.monotonic()`-based TTL (1 hour) + LRU eviction (500 max) is trivial — but only if you remember to do it when creating the store, not after an audit finds it.

### 2026-02-06 — Three Layers of DRY: Parsing, Download, Auth (Sprint 82)
**Trigger:** Sprints 73-79 cloned file parsing (CSV/Excel → DataFrame → rows), blob download (fetch → blob → anchor → click), and auth error handling (401/403/EMAIL_NOT_VERIFIED) across 4 backend routes and 5 frontend pages — totaling ~500 lines of near-identical code.
**Pattern: Utility extraction should follow the "Rule of Three" — extract after the third copy, not the fifth.** Sprint 82 extracted `parse_uploaded_file()`, `parse_json_mapping()`, and `safe_download_filename()` on the backend, and `downloadBlob()` + `useAuditUpload<T>()` on the frontend. Each utility is 15-30 lines but replaces 5-10 copies. The backend helpers eliminated `import io`, `import json`, `import pandas`, and `from datetime import datetime, UTC` from 4 route files. The frontend `useAuditUpload` generic hook reduced each domain hook from ~92 lines to ~35 lines.
**Pattern: Generic hooks should accept a config object, not individual params.** `useAuditUpload<T>` takes `{ endpoint, toolName, buildFormData, parseResult }` — this keeps each domain hook as a thin wrapper that only specifies what's different. The `buildFormData` callback handles the single-file vs dual-file divergence without conditional logic in the generic hook.

### 2026-02-07 — Phase VIII Retrospective: Clone Pattern Maturity (Sprints 83-89)

**Trigger:** Phase VIII shipped Cash Flow Statement + Payroll Testing (11-test battery) across 7 sprints — the fastest feature phase yet.

**Pattern: The clone pattern compounds — each new tool ships faster than the last.** AP Testing (Phase VII) took 4 sprints to ship from scratch. Payroll Testing (Phase VIII) cloned the same architecture and shipped in 4 sprints with 11 tests, but required far less debugging because the patterns were already proven. Key clone paths: `ap_testing_engine.py` → `payroll_testing_engine.py` (68% reuse), `ap_testing_memo_generator.py` → `payroll_testing_memo_generator.py` (~90% structural reuse), `apTesting/` components → `payrollTesting/` components (~80% structural reuse).

**Pattern: Cross-sprint dependency ordering matters for ToolNav.** Sprint 89 was planned to add `payroll-testing` to ToolNav, but the Sprint 87 frontend page needed it to compile. Moving the ToolNav update to the consuming sprint (87) instead of the wrap sprint (89) prevented a build failure.

**Pattern: Z-score test fixtures need large populations.** With only 20 entries, a single $1M outlier shifts the mean and stdev significantly, yielding z ≈ 4.36 instead of z > 5. Using 100+ base entries keeps the population statistics stable and produces expected z-scores for HIGH severity thresholds.

**Pattern: Ghost employee tests affect "clean" fixture design.** PR-T9 flags employees with single entries — so any clean fixture must ensure each employee has 2+ entries across different months. This is a cross-test interaction that doesn't exist in isolation.

### 2026-02-07 — Phase IX Retrospective: Extraction + Tool 7 + TB Enhancement (Sprints 90-96)

**Trigger:** Phase IX delivered code quality extraction (Sprint 90), Three-Way Match Validator Tool 7 (Sprints 91-94), and Classification Validator TB Enhancement (Sprint 95) across 7 sprints.

**Pattern: Extract shared utilities BEFORE building the next tool, not after.** Sprint 90 extracted shared enums, round-amount detection, and memo base functions from 3 engines. This paid off immediately — the Three-Way Match memo generator (Sprint 94) imported directly from `shared/memo_base.py` and `shared/testing_enums.py` instead of cloning yet another copy. Net result: ~400 lines removed, 0 tests broken.

**Pattern: ToolNav must be updated when the consuming page ships, not in the wrap sprint.** Sprint 93 (Three-Way Match frontend) needed `'three-way-match'` in ToolNav's `ToolKey` type to compile. Moving the ToolNav update from Sprint 96 (wrap) to Sprint 93 prevented a build failure — same lesson as Phase VIII with payroll-testing.

**Pattern: Multi-file upload tools follow the bank-rec dual-file pattern with minimal extension.** Three-Way Match uses 3 dropzones instead of 2, but the architecture (separate column detection per file type, `buildFormData` callback in hook, `parse_uploaded_file()` helper) scaled cleanly. The matching algorithm (Phase 1 exact PO# → Phase 2 fuzzy fallback) is the same greedy-sort approach as bank rec.

**Pattern: Classification validators should be structural-only to avoid liability risk.** The AccountingExpertAuditor's scope boundary was critical: 6 structural checks (duplicates, orphans, unclassified, gaps, naming, sign anomalies) with no "this account should be classified as X" recommendations. This keeps the tool in the information/detection category rather than the advisory category.

---

### Sprint 96.5 — Test Infrastructure

**Trigger:** Building test infrastructure (DB fixtures, frontend test backfill) ahead of Phase X persistent data layer.

**Gotcha: `jest.clearAllMocks()` does NOT reset `mockReturnValue`.** Tests that call `mockHook.mockReturnValue({status: 'success', ...})` leave stale state for subsequent tests. `clearAllMocks` only clears call records, not return values. Fix: explicitly re-set default mock values in `beforeEach` after `clearAllMocks()`. This caused 7 test failures across all 5 tool page test suites.

**Gotcha: Mock result shapes must match INLINE page property access, not just component props.** Even when child components are mocked (e.g., `BankRecMatchTable`), the page evaluates prop expressions like `result.summary.matches` before passing to the mock. Wrong field names (`match_summary` vs `summary`) crash with TypeError. Always check the page source for inline property access chains.

**Pattern: framer-motion test mock must strip motion-specific props.** Spreading all props from `motion.div` onto a real `<div>` passes invalid HTML attributes (`initial`, `animate`, `exit`, `transition`, `variants`, `whileHover`, etc.). Fix: destructure these out explicitly before spreading rest props.

---

### Sprint 97 — Engagement Model + Materiality Cascade

**Trigger:** First persistent metadata layer in Phase X — SQLAlchemy models for Engagement + ToolRun.

**Gotcha: SQLite doesn't enforce FK constraints by default.** Tests for ON DELETE RESTRICT/CASCADE silently passed even with invalid FK references. Fix: add `PRAGMA foreign_keys=ON` via SQLAlchemy `event.listens_for(engine, "connect")` in conftest.py. This is SQLite-specific — PostgreSQL enforces FKs by default.

**Gotcha: SQLite strips timezone from datetime columns.** When updating an engagement field with a timezone-aware datetime, the existing DB-loaded value is timezone-naive (SQLite doesn't store timezone info). Comparing them directly raises `TypeError: can't compare offset-naive and offset-aware datetimes`. Fix: strip tzinfo with `.replace(tzinfo=None)` before comparison in validation logic.

**Pattern: Shared tool run recording helper avoids 7x copy-paste.** Instead of duplicating engagement recording logic in each tool route, a single `maybe_record_tool_run()` function in `shared/helpers.py` handles the pattern: check if engagement_id is provided, validate ownership, record success or failure. Each route adds just 2 lines (success + error paths).

---

### Sprint 98 — Engagement Workspace (Frontend)

**Trigger:** First Phase X frontend deliverable — types, CRUD hook, context, page, and 4 components.

**Pattern: AuthContext lives at `context/` (singular), not `contexts/` (plural).** The existing project structure uses `frontend/src/context/AuthContext.tsx`. New contexts (like EngagementContext) go in `frontend/src/contexts/` — note the different directory. Always check existing imports before assuming directory names.

**Pattern: Page-scoped context providers avoid premature coupling.** EngagementProvider wraps only the `/engagements` page, not the global `providers.tsx`. Tool page integration (`?engagement=X` auto-linking) is deferred to Sprint 100+. This prevents all tool pages from requiring engagement state they don't yet use.

**Pattern: Separate CRUD hook from Context.** `useEngagement` (CRUD operations, follows `useClients` pattern) is distinct from `EngagementContext` (active-engagement state management). The hook can be used anywhere; the context is scoped to the engagements page. This separation keeps the hook reusable.

---

### Sprint 99 — Follow-Up Items Tracker (Backend)

**Trigger:** Follow-up items model, CRUD API, auto-population from tool runs, 59 tests.

**Gotcha: SQLAlchemy backref default behavior conflicts with DB-level CASCADE.** When deleting an Engagement with related FollowUpItems, SQLAlchemy's default backref tries to SET NULL on the FK column before the database CASCADE can fire, causing `IntegrityError: NOT NULL constraint failed`. Fix: use `backref=backref("follow_up_items", passive_deletes=True)` which tells SQLAlchemy to let the DB handle deletion. This requires importing `backref` from `sqlalchemy.orm`.

**Pattern: Manager class isolates ownership checks from route logic.** `FollowUpItemsManager` handles all ownership verification (joining through Engagement → Client → user_id), keeping route handlers thin. The same pattern was used in `EngagementManager` (Sprint 97). Each manager method takes `user_id` as its first parameter and validates access before any mutation.

**Pattern: Auto-population uses narrative descriptions only.** The `auto_populate_from_tool_run()` method accepts a list of `{description, severity}` dicts — never amounts, account numbers, or PII. This enforces Guardrail 2 at the API boundary. Tool routes that call auto-population are responsible for converting findings to narrative text before passing them in.

---

### Sprint 100 — Follow-Up Items UI + Workpaper Index

**Trigger:** First full-stack Phase X sprint — frontend follow-up items table + backend workpaper index generator + page integration.

**Pattern: Tabbed workspace detail replaces stacked sections.** Three tabs (Diagnostic Status, Follow-Up Items, Workpaper Index) replaced a growing vertical stack. Each tab loads its data when the engagement is selected (parallel with `Promise.all`), not on tab switch. This avoids redundant API calls while keeping the UI responsive.

**Pattern: Expandable table rows replace separate card components.** Instead of creating a `FollowUpItemCard.tsx` component (as originally planned), the table row expands inline with auditor notes textarea, disposition dropdown, and delete button. This reduces component count and keeps the interaction surface in context — the user never loses their place in the list.

**Gotcha: Factory fixtures that create cascaded objects need unique email addresses.** The `make_engagement` fixture creates a user → client → engagement chain. When a test needs two separate engagements owned by different users, it must explicitly create a second user with a distinct email to avoid `UNIQUE constraint failed: users.email`. Use `make_user(email="other@example.com")` before `make_client(user=user2)`.

---

### Sprint 101 — Engagement ZIP Export + Anomaly Summary Report

**Trigger:** Anomaly summary PDF, engagement ZIP export, strengthened disclaimers. Backend-only sprint.

**Pattern: Composition over inheritance for PDF generators.** `AnomalySummaryGenerator` reuses `create_memo_styles()` from `shared/memo_base.py` and `ClassicalColors`/`DoubleRule`/`LedgerRule` from `pdf_generator.py` but does NOT extend the `PaciolusReportGenerator` class. The anomaly summary has a fundamentally different structure (disclaimer-first, blank auditor section) that doesn't fit the base class's executive-summary pattern. Composition keeps it clean.

**Pattern: ZIP export delegates to existing generators.** `EngagementExporter.generate_zip()` calls `AnomalySummaryGenerator.generate_pdf()` and `WorkpaperIndexGenerator.generate()` rather than duplicating logic. Each generator handles its own access control, so the exporter just orchestrates.

**Pattern: Backward-compatible parameter additions.** The `build_disclaimer()` signature gained an `isa_reference` parameter with a default value (`"applicable professional standards"`). Existing callers (JE/AP/Payroll/TWM memo generators) continue to work without changes. New callers can pass domain-specific ISA references.

---

### Sprint 102 — Phase X Wrap

**Trigger:** Wrap sprint covering regression testing, guardrail verification, navigation updates, TOS draft, documentation.

**Pattern: Document guardrail grep commands as CI/CD reference.** Instead of just running guardrail checks ad hoc, writing them to `docs/guardrail-checks.md` with exact `rg` commands and expected behavior makes them reproducible. Each check includes: the rule, the command, what "pass" looks like, and last verification date. This is ready to drop into a CI pipeline when the project adds one.

**Pattern: Per-tool-run `composite_score` is NOT an engagement composite.** Guardrail 6 prohibits aggregating tool scores into an engagement-level risk score. The `composite_score` field on `ToolRunResponse` stores individual tool native scores (e.g., AP testing's composite from its 13-test battery). This distinction must be documented because a naive grep will flag the field name. The guardrail targets `engagement_risk_score` or cross-tool aggregation, not per-run metadata.

**Phase X Retrospective:** 7 sprints delivered a full engagement workflow layer without violating any of the 8 AccountingExpertAuditor guardrails. Key success factors: (1) narratives-only data model kept financial data out of persistent storage, (2) post-completion aggregation kept tool routes independent, (3) non-dismissible disclaimers enforced at page + PDF + export levels, (4) per-tool-run scores avoided the ISA 315 composite scoring trap.

---

### Sprint 103 — Tool-Engagement Integration (Frontend)

**Trigger:** Phase XI kickoff — connecting 7 tool pages to the engagement workspace.

**Pattern: useOptionalEngagementContext for backward compatibility.** The standard `useEngagementContext()` throws when no provider is present. Tools need to work standalone (no engagement) and linked (with engagement). Solution: export a `useOptionalEngagementContext()` that returns `null` instead of throwing. This lets `useAuditUpload` auto-inject `engagement_id` when wrapped in a provider, and silently skip when standalone.

**Pattern: Hook-level integration minimizes page-level changes.** By injecting engagement logic into the shared `useAuditUpload` hook, 5 of 7 tools (JE, AP, BankRec, Payroll, 3WM) got full engagement support with zero changes to their individual hooks or page files. Only the TB page (custom fetch) and Multi-Period hook (JSON body) needed explicit changes. This validates the Sprint 82 extraction of `useAuditUpload` as a centralization point.

**Pattern: Next.js layout.tsx for cross-cutting concerns.** Creating `app/tools/layout.tsx` with `<Suspense>` + `<EngagementProvider>` automatically wraps all `/tools/*` pages without touching any individual tool page. The layout reads `?engagement=X` on mount, shows the banner/toast, and provides context to all descendant components.

---

### Sprint 104 — Revenue Testing Engine + Routes

**Trigger:** Phase XI Sprint 104 — adding revenue testing as Tool 8.

**Pattern: Adding a new ToolName enum value cascades to workpaper index + existing tests.** When adding `REVENUE_TESTING` to `ToolName`, the workpaper index generator iterates `for tool_name in ToolName` so the new value appears automatically in `document_register`. However, existing tests that assert counts (e.g., "7 tools", "5 not_started") must be updated to 8/6. Also, `TOOL_LABELS` and `TOOL_LEAD_SHEET_REFS` dicts must be updated or the new tool gets empty labels/refs. Checklist for new ToolName values: (1) add to enum, (2) add to TOOL_LABELS, (3) add to TOOL_LEAD_SHEET_REFS, (4) grep tests for hardcoded tool counts.

**Pattern: Revenue testing follows AP testing engine pattern exactly.** Column detection (weighted regex patterns + greedy assignment), dataclass models (Entry → FlaggedEntry → TestResult → CompositeScore → FullResult), 3-tier test battery (structural/statistical/advanced), composite scoring with severity weights + multi-flag multiplier. The same pattern works for any transaction-level testing engine — reuse the architecture for AR aging (Sprint 107).

---

### Sprint 105 — Revenue Testing Memo + Export

**Trigger:** Phase XI Sprint 105 — adding PDF memo and CSV export for revenue testing.

**Pattern: Memo generators are now a 5-minute copy-and-customize.** With `shared/memo_base.py` providing all section builders (header, scope, methodology, results, workpaper, disclaimer), a new memo generator only needs: (1) test descriptions dict, (2) domain-specific methodology intro text, (3) risk-tier conclusion paragraphs, (4) ISA references for the disclaimer. Revenue testing memo was 165 lines vs the original JE testing memo's 400+ lines before extraction.

**Pattern: PDF binary content is compressed — don't test via decode("latin-1").** ReportLab compresses content streams by default. Tests that `decode("latin-1")` the PDF bytes and search for text strings will fail. Instead, verify guardrail compliance at the source code level using `inspect.getsource()`. This is more reliable and tests the actual behavior (what strings are passed to the PDF builder) rather than an artifact of the PDF encoding.

**Pattern: Export input models follow a consistent shape.** All testing export input models (JE, AP, Payroll, Revenue) share: `composite_score: dict`, `test_results: list`, `data_quality: dict`, `column_detection: Optional[dict]`, plus the 5 workpaper fields (filename, client_name, period_tested, prepared_by/reviewed_by, workpaper_date). Three-Way Match is the exception (different data shape). When adding a new testing tool export, copy the `APTestingExportInput` and rename.

---

### Sprint 106 — Revenue Testing Frontend + 8-Tool Nav

**Trigger:** Phase XI Sprint 106 — adding the revenue testing frontend page and expanding ToolNav to 8 tools.

**Pattern: Frontend tool pages are now a 4-file formula.** Types file → Hook (thin `useAuditUpload` wrapper) → 4 components (ScoreCard, TestResultGrid, DataQualityBadge, FlaggedTable) → Page. Revenue testing frontend followed the AP/Payroll/TWM pattern exactly. The `useTestingExport` hook and `useFileUpload` hook handle export and drag-and-drop — no custom logic needed per tool.

**Pattern: ToolNav label brevity matters at 8 tools.** At 7 tools, the nav was already tight. Adding tool 8 required shortening "Payroll Testing" to "Payroll" and using "Revenue" instead of "Revenue Testing". The homepage inline nav mirrors ToolNav labels. When adding tool 9 (AR Aging), further abbreviation may be needed or consider a dropdown/overflow pattern.

**Pattern: Adding a tool cascades to 4 frontend locations.** New tool frontend requires updates in: (1) `components/shared/ToolNav.tsx` (ToolKey type + TOOLS array), (2) `app/page.tsx` (toolCards + nav links + tool count copy), (3) `types/engagement.ts` (ToolName + TOOL_NAME_LABELS + TOOL_SLUGS), (4) the tool's own page/hook/components/types. Checklist: ToolNav → Homepage → Engagement types → Tool files.

---

### Sprint 107 — AR Aging Engine + Routes

**Trigger:** Phase XI Sprint 107 — adding AR aging analysis as Tool 9.

**Pattern: Dual-input architecture for multi-source analysis.** AR Aging is the first tool with truly optional secondary input — TB is required, sub-ledger is optional. When only TB is provided, 4 structural tests run (sign anomalies, missing allowance, negative aging from TB dates, unreconciled detail skipped). When sub-ledger is provided, all 11 tests can run including aging bucket analysis, customer concentration, and DSO trend. The route follows the bank reconciliation dual-file pattern but makes the second file optional via `File(default=None)`.

**Bug: Column detection priority ordering prevents greedy misassignment.** In `detect_sl_columns()`, `aging_days_column` was being assigned before `aging_bucket_column`. Because the non-exact pattern `"aging"` in `SL_AGING_DAYS_PATTERNS` scored 0.60 for "Aging Bucket" columns (above the 0.50 threshold), the greedy `_assign_best()` grabbed it for aging_days, leaving aging_bucket unable to find its column. Fix: assign higher-specificity fields (aging_bucket, exact match 1.0) before lower-specificity fields (aging_days, partial match 0.60). **Lesson: When using greedy column assignment, always order assignments from most specific to least specific.**

**Pattern: ToolName enum cascade is now a 4-assertion update.** Adding AR_AGING as the 9th tool required updating exactly 4 hardcoded count assertions across 3 test files: `test_anomaly_summary.py` (document_register == 9), `test_engagement.py` (ToolName set), `test_workpaper_index.py` (document_register == 9, not_started == 7). This is the same cascade pattern documented in Sprint 104 — use `grep -r "== 8\|== 7\|== 6" tests/` to find count assertions before adding a new ToolName value.

**Pattern: Test skipping with `skip_reason` for optional inputs.** Tests that require sub-ledger data (AR05-AR11 except AR02) return `skipped=True, skip_reason="Requires AR sub-ledger"` when only TB is provided. This is cleaner than raising errors — the client can display which tests were skipped and why, guiding users to upload the optional file for fuller coverage.

---

### Sprint 108 — AR Aging Memo + Export

**Trigger:** Phase XI Sprint 108 — adding PDF memo and CSV export for AR aging analysis.

**Pattern: AR-specific scope section for dual-input memos.** The standard `build_scope_section()` from memo_base works for single-input tools (total_entries + tests_run + data_quality). For AR aging's dual-input architecture, a custom `_build_ar_scope_section()` adds: TB Accounts Analyzed, Sub-Ledger Entries (if present), Analysis Mode (Full vs TB-Only), Tests Skipped count. This is the first memo with a custom scope section — future dual-input tools should follow this pattern.

**Pattern: ISA 540 for estimation-based tools.** AR aging references ISA 540 (Auditing Accounting Estimates) because allowance for doubtful accounts is an estimate, not a fact. Revenue testing uses ISA 240 (fraud risk); AP/Payroll use ISA 240/500. The ISA reference should match the nature of what's being tested: ISA 240 for fraud risk, ISA 500 for evidence, ISA 540 for estimates, ISA 505 for confirmations.

---

### Sprint 109 — AR Aging Frontend + 9-Tool Nav

**Trigger:** Phase XI Sprint 109 — adding AR aging frontend and expanding to 9-tool navigation.

**Pattern: Dual-dropzone pages need a separate "Run" button.** Unlike single-file tools that auto-run on drop, the AR aging page has two dropzones (TB required + sub-ledger optional). Users need to: (1) drop TB, (2) optionally drop sub-ledger, (3) explicitly click "Run". The button shows mode indicator — "(Full Mode)" when both files present, "(TB-Only)" when only TB. This pattern applies to any future tool with optional secondary input.

**Pattern: Skipped tests need graceful UI handling in 3 locations.** When TB-only mode skips 7 of 11 tests: (1) ARTestResultGrid shows "Skipped" badge with dimmed opacity + skip_reason text, non-clickable; (2) FlaggedARTable excludes skipped test entries from allFlagged collection; (3) Page shows a notice banner with skip count directing users to upload sub-ledger. Future tools with optional inputs should handle skipped results in all three display layers.

**Pattern: 9-tool nav is at the display limit.** At 9 tools, the ToolNav bar uses abbreviated labels (e.g., "Revenue" not "Revenue Testing", "Payroll" not "Payroll Testing"). Homepage nav mirrors these. If adding a 10th tool, consider an overflow/dropdown pattern rather than continuing to add inline links.

---

### Sprint 110 — Phase XI Wrap — Regression + v1.0.0

**Trigger:** Phase XI Sprint 110 — final regression testing, guardrail verification, and v1.0.0 release.

**Milestone: v1.0.0 reached with 9-tool suite + engagement layer.** Phase XI delivered: tool-engagement integration (frontend), Revenue Testing (engine + memo + frontend), AR Aging (engine + memo + frontend), and 9-tool navigation. Final state: 2,114 backend tests (0 failures), frontend build clean (27 routes), all 6 AccountingExpertAuditor guardrails verified. The platform is a complete professional audit intelligence suite with Zero-Storage architecture.

**Pattern: Phase wrap sprints are pure verification — no new code.** Sprint 110 wrote zero lines of application code. It ran the full backend test suite, frontend build, and guardrail checks. Documentation updates (CLAUDE.md version bump, todo.md checklist, lessons.md) are the only file changes. This confirms the "regression + documentation" sprint pattern works for phase boundaries.

**Observation: Test count trajectory across Phase XI.** Phase X ended at ~1,100 tests. Phase XI added: +110 revenue testing, +28 revenue memo, +131 AR aging, +34 AR aging memo = 303 new tests across 8 sprints. The 9-tool suite now has comprehensive test coverage with each tool averaging ~150 tests.

---

### Sprint 111 — Prerequisites — Nav Overflow + ToolStatusGrid + FileDropZone Extraction

**Trigger:** Phase XII Sprint 111 — prerequisite infrastructure before adding tools 10+11.

**Pattern: ToolStatusGrid should derive from canonical maps, not hardcoded arrays.** The `ALL_TOOLS` array was hardcoded to 7 tools and fell behind when tools 8 and 9 were added. Replaced with `Object.keys(TOOL_NAME_LABELS) as ToolName[]` so it auto-updates. Always derive from the single source of truth (`TOOL_NAME_LABELS` in `types/engagement.ts`) rather than maintaining parallel arrays.

**Pattern: ToolNav overflow at INLINE_COUNT=6.** With 9 tools, showing all inline was at the limit. The overflow dropdown shows first 6 inline and remaining in a "More" dropdown. When the current tool is in the overflow, the button highlights sage-400 and shows the tool name. Click-outside-to-close via `useRef` + `useEffect`. This pattern scales indefinitely for tools 10+.

**Pattern: FileDropZone shared component covers 80% of use cases.** The unified component supports: label, hint, icon (optional), file, onFileSelect, disabled, accept. This covers bank-rec, three-way-match, and ar-aging patterns. Multi-period's status-aware pattern (loading/success/error states) is different enough that it keeps its inline implementation — don't over-abstract to force 100% coverage.

---

### Sprint 112 — Finding Comments — Backend Model + API + Tests

**Trigger:** Phase XII Sprint 112 — adding threaded comment support for follow-up items.

**Pattern: Comment model follows the same ownership chain as its parent entity.** `FollowUpItemComment` access is verified through the chain: Comment → FollowUpItem → Engagement → Client → User. The `_verify_comment_access` method joins across 4 tables. Author-only edit/delete adds a second check (`comment.user_id != user_id`) after the ownership check passes.

**Pattern: Self-referential FK for comment threading.** `parent_comment_id` is a nullable FK to the same table with `ondelete="CASCADE"`, so deleting a parent comment cascades to all replies. The `replies` relationship uses `remote_side` to handle the self-join. Export renders one nesting level (top-level → replies), keeping markdown readable.

**Pattern: Conditional ZIP file inclusion.** The comments markdown is only added to the ZIP when comments exist. The manifest is built from the `files` dict, so conditional inclusion is automatic — no separate manifest logic needed. This is cleaner than including an empty file.

---

### Sprint 113 — Finding Assignments + Collaboration Frontend

**Trigger:** Phase XII Sprint 113 — adding assignment workflow and comment UI to follow-up items.

**Pattern: Sentinel value -1 for "no change" on nullable FK updates.** The `assigned_to` field can be: a user ID (assign), None (unassign), or -1 (leave unchanged). Using -1 as the default in `update_item()` means callers updating only disposition/notes don't accidentally unassign. This avoids the ambiguity of Optional[Optional[int]] and keeps the API clean.

**Pattern: No `apiPatch` existed — added it.** The existing apiClient had GET/POST/PUT/DELETE but no PATCH. Comment updates use PATCH semantically (partial update). Added `apiPatch` following the same pattern as `apiPut` (cache invalidation on success). Export from utils barrel for hooks to use.

**Pattern: Assignment filter presets are client-side.** "My Items" and "Unassigned" filtering is done client-side on the already-fetched items list, not via separate API calls. The backend has `get_my_items` and `get_unassigned_items` endpoints for potential future use, but the current UI filters the full list in-memory. This is simpler and avoids extra round-trips since all items are already loaded.

---

### Sprint 114 — Fixed Asset Testing — Engine + Routes

**Trigger:** Phase XII Sprint 114 — adding fixed asset register testing as Tool 10.

**Pattern: Fixed asset column detection has more columns than revenue/AP.** FA registers have 11 detectable columns (asset_id, description, cost, accumulated_depreciation, acquisition_date, useful_life, depreciation_method, residual_value, location, category, net_book_value) vs revenue's 8. The greedy assignment order matters more: accumulated_depreciation and net_book_value must be assigned before cost, because "cost" appears as a substring in many column names. Always assign the most specific columns first.

**Pattern: ToolName enum cascade is now a 4-file, 5-assertion update.** Adding `FIXED_ASSET_TESTING` as the 10th tool required updating hardcoded count assertions in: `test_ar_aging.py` (enum count 9→10), `test_workpaper_index.py` (document_register 9→10, not_started 7→8), `test_engagement.py` (ToolName set), `test_anomaly_summary.py` (document_register 9→10). Grep for `== 9` across test files when adding tool 11.

**Pattern: `_safe_float_optional` for nullable numeric fields.** Fixed assets have `useful_life` and `net_book_value` which are genuinely optional — not "default to 0". Using `_safe_float_optional` (returns None for missing/invalid) instead of `_safe_float` (returns 0.0) lets tests distinguish "no data" from "zero value". Revenue testing didn't need this because all its numeric fields default to 0.

---

### Sprint 120 — Phase XII Wrap — Regression + v1.1.0

**Trigger:** Phase XII Sprint 120 — final regression, guardrail verification, and v1.1.0 release.

**Milestone: v1.1.0 reached with 11-tool suite + collaboration layer.** Phase XII delivered: nav overflow infrastructure, finding comments + assignments (collaboration layer), Fixed Asset Testing (engine + memo + frontend), Inventory Testing (engine + memo + frontend), and 11-tool navigation. Final state: 2,515 backend tests (0 failures), frontend build clean (29 routes), all 6 AccountingExpertAuditor guardrails verified, both FA and Inventory memos COMPLIANT.

**Observation: Test count trajectory across Phase XII.** Phase XI ended at ~2,114 tests. Phase XII added: +41 finding comments, +133 fixed asset testing, +38 FA memo, +136 inventory testing, +38 inventory memo = 401 new tests across 10 sprints (Sprints 111-120). The 11-tool suite has comprehensive coverage with each testing tool averaging ~140 tests.

**Pattern: Phase wrap sprints are pure verification — no new code.** Sprint 120 wrote zero lines of application code. Full backend regression (2,515 tests), frontend build (29 routes), 6 guardrail checks, and AccountingExpertAuditor memo review for both new tools. Documentation updates only.

---

### Sprint 119 — Inventory Testing — Frontend + 11-Tool Nav

**Trigger:** Phase XII Sprint 119 — adding frontend page, components, and 11-tool nav for inventory testing.

**Pattern: Frontend tool pages are fully templatable from fixed asset testing.** The inventory testing frontend (types, hook, 4 components, page) follows the fixed asset testing pattern exactly. Domain-specific changes: field names (item_id/quantity/unit_cost/extended_value vs asset_id/cost/accumulated_depreciation), table columns (added Qty + Value columns, removed Cost), test tier labels (IN-01 to IN-09 vs FA-01 to FA-09), export endpoints (/export/inventory-memo + /export/csv/inventory), and IAS 2/ISA 501 disclaimer references.

**Pattern: 11-tool nav scales cleanly with overflow.** With INLINE_COUNT=6, the 11th tool automatically appears in the "More" dropdown alongside tools 7-10. The homepage inline nav mirrors ToolNav by adding an "Inventory" link. Copy updates: "Ten" → "Eleven" across hero text, section headings, and workspace CTA.

---

### Sprint 121 — Tailwind Config + Version Hygiene + Design Fixes

**Trigger:** Phase XIII Sprint 121 — P0 findings from product review. First hygiene sprint before theme migration.

**Pattern: Tailwind silently drops undefined color shades.** The `oatmeal` scale only went to 500, but 239 usages across 74 files referenced `oatmeal-600`. Tailwind generates no warnings — the class simply produces no CSS. This means `text-oatmeal-600` rendered as the browser default (black on white), silently breaking the design. Similarly, `clay-800/900` and `sage-800/900` were referenced in `RISK_LEVEL_CLASSES` but undefined, making all risk badges invisible. Always define the full shade range (50-900) when a scale is used extensively.

**Pattern: Extract version to single source of truth.** Three backend files had different hardcoded version strings ("0.90.0", "0.47.0", "0.13.0") that drifted independently. Created `backend/version.py` with `__version__ = "1.1.0"` imported by `main.py`, `routes/health.py`, and `engagement_export.py`. Future version bumps require exactly one edit. Also caught `frontend/package.json` at "0.90.0".

**Pattern: Product review pays for itself in Sprint 1.** The 4-agent product review identified 51 findings. Sprint 121 alone fixed 7 P0 items (broken color scale, 3 amber violations, 2 non-palette hexes, stale versions) plus 2 P1 items (missing disclaimers). Without the review, these would have accumulated silently — especially the Tailwind shade issue affecting 74 files.

---

### Sprint 122 — Security Hardening + Error Handling

**Trigger:** Phase XIII Sprint 122 — P0 rate limiting gap (26 unprotected export endpoints), upload validation missing, error messages leaking Python tracebacks.

**Pattern: Rate limiting requires `Request` as first function parameter.** Slowapi's `@limiter.limit()` decorator requires the FastAPI `Request` object to be the first positional parameter of the endpoint function. When a Pydantic body model is already named `request` (as in multi_period.py's `MovementExportRequest`), rename it to `payload` to avoid the naming conflict. Always check for this clash when adding rate limits to existing endpoints.

**Pattern: Centralized error sanitization with pattern matching.** Instead of sanitizing each error handler individually, `shared/error_messages.py` uses regex patterns to match common exception types (pandas, openpyxl, SQLAlchemy, reportlab) and map them to user-friendly messages. This handles the long tail of Python exceptions with ~10 patterns plus operation-specific fallbacks. The `sanitize_error()` function also handles secure logging internally, eliminating the need for separate `log_secure_operation` calls in exception handlers.

**Pattern: `except ValueError` is safe; `except Exception` is not.** All `except ValueError as e: raise HTTPException(400, detail=str(e))` blocks in our codebase are safe because we raise ValueError with controlled messages for business logic (e.g., "Engagement not found", "Invalid adjustment"). Only `except Exception as e` blocks leak raw tracebacks. Sprint 122 sanitized all 39 `except Exception` blocks across 12 route files while leaving ~22 `except ValueError` blocks intact.

**Pattern: Upload validation belongs in `validate_file_size`, not `parse_uploaded_file`.** Content-type and extension checks happen during file reading (before bytes are consumed), while encoding fallback and row count checks happen during parsing. This two-layer approach means validation errors short-circuit early without wasting time reading the full file.

**Pattern: 4-location frontend cascade is stable.** Adding tool 11 required updates to the same 4 locations as tools 8-10: (1) ToolNav.tsx (ToolKey type + TOOLS array), (2) page.tsx homepage (toolCards array + nav links + "Eleven" copy), (3) engagement.ts (ToolName union + TOOL_NAME_LABELS + TOOL_SLUGS), (4) tool's own 8 files (types, hook, 4 components + barrel, page).

---

### Sprint 118 — Inventory Testing — Memo + Export

**Trigger:** Phase XII Sprint 118 — adding PDF memo and CSV export for inventory testing.

**Pattern: Inventory memo generator follows the established 5-minute copy-and-customize.** With `shared/memo_base.py`, the inventory memo was a straightforward customization: (1) 9 test descriptions referencing IAS 2/ISA 501/540, (2) methodology intro citing inventory estimation standards, (3) 4 risk-tier conclusion paragraphs using "inventory anomaly indicators" language, (4) disclaimer with ISA 500/540 references. Total: ~170 lines.

**Guardrail: "Inventory register analysis" not "NRV testing" or "obsolescence determination".** The memo title is "Inventory Register Analysis Memo" rather than "Inventory Valuation Testing Memo". Descriptions say "anomaly indicator" and explicitly state "not an NRV determination". This mirrors the fixed asset + AR aging pattern — the tool describes data anomalies, not accounting conclusions.

---

### Sprint 117 — Inventory Testing — Engine + Routes

**Trigger:** Phase XII Sprint 117 — building inventory testing engine (Tool 11) with 9-test battery.

**Pattern: Inventory engine is a clean derivative of fixed asset testing.** The column detection → parsing → test battery → scoring → orchestrator structure copies perfectly. Key domain differences: (1) inventory has `extended_value = qty × unit_cost` cross-check (IN-03) which is unique, (2) slow-moving inventory uses `last_movement_date` + `_days_since()` helper — dates require robust multi-format parsing, (3) category concentration is statistical not advanced (inventory categories are a key audit concern per IAS 2).

**Pattern: Test file structure is highly replicable.** The 18-class structure (detection, match, helpers, parsing, quality, risk tier, 9 individual tests, battery, score, pipeline, serialization, API) maps 1:1 from fixed assets. The inventory test file (136 tests) was written in one pass with only a single issue: Python syntax error from `07` (leading zero in date literal) — fixed to `7`.

**Guardrail: "Anomaly indicators" not "NRV determination" or "obsolescence sufficiency".** Engine docstring explicitly says "does NOT constitute an NRV adequacy opinion" and slow-moving test description says "obsolescence anomaly indicator" not "obsolescence provision". This follows the AR aging + fixed asset patterns.

---

### Sprint 116 — Fixed Asset Testing — Frontend + 10-Tool Nav

**Trigger:** Phase XII Sprint 116 — adding frontend page, components, and 10-tool nav for fixed asset testing.

**Pattern: Frontend tool pages are fully templatable from revenue testing.** The fixed asset testing frontend (types, hook, 4 components, page) follows the revenue testing pattern exactly. Only domain-specific changes: field names (asset_id/cost/category vs account_name/amount/date), table sort columns, search placeholders, test tier labels (FA-01 to FA-09 vs RT-01 to RT-12), and IAS 16/ISA 540 standard references in the disclaimer.

**Pattern: Tool slug should match backend route.** Backend route is `/audit/fixed-assets`, so the frontend page path is `/tools/fixed-assets/` and the ToolNav key is `fixed-assets`. The todo.md originally said `fixed-asset-testing` but keeping slugs short and consistent with the API is better.

**Pattern: ToolNav overflow is automatic.** With INLINE_COUNT=6, the 10th tool (Fixed Assets) automatically appears in the "More" dropdown. No UI changes needed beyond adding the entry to the TOOLS array.

---

### Sprint 124 — Theme: Shared Components

**Trigger:** Phase XIII Sprint 124 — migrating shared components to semantic tokens, dark-pinning nav/toast, adopting shared FileDropZone, dead code cleanup.

**Pattern: Dark-pinned components use `data-theme="dark"` attribute, not semantic tokens.** ToolNav and ToolLinkToast must stay dark on light-themed pages. Adding `data-theme="dark"` to their wrapper element ensures any CSS custom properties resolve to dark values. The existing hardcoded obsidian/oatmeal palette classes already work (they don't respond to theme), but `data-theme` future-proofs against accidental semantic token usage inside these components.

**Pattern: CSS custom properties don't support Tailwind opacity modifiers.** `bg-surface-card/50` doesn't work because Tailwind can't split opacity from a `var()` value. Design semantic tokens with the right opacity built into the variable (e.g., `--surface-card: rgba(48, 48, 48, 0.8)`), or use separate tokens for different opacity needs. This constraint shaped the FileDropZone migration — idle backgrounds use `bg-surface-card-secondary` instead of `bg-surface-card/30`.

**Pattern: Deferred items are OK when risk exceeds value.** Context directory consolidation (`context/` → `contexts/`) would touch 50 files for cosmetic benefit. Multi-period FileDropZone has period-specific state logic that doesn't match the shared component. Both were deferred without reducing sprint quality.

---

### Sprint 123 — Theme Infrastructure — "The Vault"

**Trigger:** Phase XIII Sprint 123 — building dual-theme infrastructure with CSS custom properties, Tailwind semantic tokens, and route-based ThemeProvider.

**Pattern: CSS custom properties bridge Tailwind and runtime theming.** Tailwind generates classes at build time, but theme switching needs runtime adaptation. The solution: define semantic CSS variables in `:root` (dark defaults) with `[data-theme="light"]` overrides in `globals.css`, then reference them via Tailwind token aliases (`bg-surface-card` → `var(--surface-card)`). This gives Tailwind's class-based workflow with runtime theme switching — no JavaScript style injection needed.

**Pattern: Route-based theming via usePathname, not user toggle.** The ThemeProvider reads `usePathname()` and sets `data-theme` on `<html>` via `useEffect`. DARK_ROUTES array lists homepage + auth pages; everything else gets light. This is intentionally NOT a user preference — the "vault exterior → vault interior" metaphor is a brand decision. Adding `suppressHydrationWarning` on `<html>` prevents React warnings since the server renders `data-theme="dark"` but the client may immediately switch to light.

**Pattern: Infrastructure-only sprints change zero visual behavior.** Sprint 123 added ~80 lines of CSS custom properties, ~30 lines of Tailwind config, and a 37-line ThemeProvider. No existing component was modified to USE these tokens. This means zero visual regression risk — existing `bg-obsidian-800` classes still work identically. Sprint 124+ will incrementally migrate components to semantic tokens. Infrastructure first, migration second.

---

### Sprint 115 — Fixed Asset Testing — Memo + Export

**Trigger:** Phase XII Sprint 115 — adding PDF memo and CSV export for fixed asset testing.

**Pattern: FA memo generator follows the established 5-minute copy-and-customize.** With `shared/memo_base.py`, the fixed asset memo was a straightforward customization: (1) 9 test descriptions referencing IAS 16/ISA 540, (2) methodology intro citing depreciation estimation standards, (3) 4 risk-tier conclusion paragraphs using "PP&E anomaly indicators" language, (4) disclaimer with ISA 500/540 references. Total: ~170 lines.

**Guardrail: "Fixed asset register analysis" not "valuation testing".** The memo title is "Fixed Asset Register Analysis Memo" rather than "Fixed Asset Valuation Testing Memo". Descriptions say "anomaly indicator" not "impairment determination" or "depreciation sufficiency". This mirrors AR aging's "accounts receivable aging analysis" pattern — the tool describes data anomalies, not accounting conclusions.

**Pattern: CSV export for fixed assets uses FixedAssetEntry fields.** The CSV columns match the FixedAssetEntry dataclass: asset_id, description, category, cost, accumulated_depreciation, useful_life, acquisition_date. This is more fields than AP testing (vendor, invoice, amount) but follows the same test→flagged_entries→entry pattern.

### 2026-02-10 — Parallel Agent Migration for Uniform Component Sets (Sprint 125)

**Trigger:** Sprint 125 required migrating 30 files (6 pages + 24 components) across 6 tool suites from dark-only styling to semantic theme tokens.

**Pattern: Establish reference migration on one tool, then parallelize the rest.** Revenue Testing was migrated manually first to establish the exact token mapping (bg-gradient-obsidian→bg-surface-page, tier gradients→left-border accents, opacity fills→solid fills, etc.). Then 5 parallel agents applied the same pattern to the remaining tools. This reduced a ~30-file migration from serial to ~5 minutes wall-clock.

**Pattern: ScoreCard tier gradients → left-border accents on light theme.** The dark theme used `bg-gradient-to-br from-sage-500/20 to-sage-500/5` for risk tier visual encoding. On light backgrounds these gradients are nearly invisible. The light pattern uses a white card with `border-l-4 border-l-{tier-color}` — a 4px colored left border that encodes tier while keeping the card visually clean.

**Pattern: RISK_TIER_COLORS must use solid fills for light theme.** Dark-theme-tuned opacity colors (`bg-sage-500/10`, `text-sage-400`) lack contrast on white backgrounds. Replace with solid palette fills: `bg-sage-50`, `text-sage-700`, `border-sage-200`. Each tool has its own types file with these constants — update per-tool, not globally.

### 2026-02-10 — Foundation-First Utility Migration + CSS Component Overrides (Sprint 126)

**Trigger:** Sprint 126 required migrating ~48 files (5 tool pages + 20+ components + 10 engagement components + 8 auth pages + 3 type files + 2 utility files).

**Pattern: Update shared utilities and type constants BEFORE component files.** `themeUtils.ts` exports (HEALTH_STATUS_CLASSES, INPUT_BASE_CLASSES, BADGE_CLASSES, RISK_LEVEL_CLASSES) and types files (RISK_TIER_COLORS, MATCH_TYPE_COLORS, etc.) were updated first to use semantic tokens/solid fills. This meant agents migrating components could rely on already-correct utility values rather than needing to know about them.

**Pattern: CSS component class light overrides via `[data-theme="light"]` selectors.** Rather than converting `.card`, `.input`, `.badge-*` etc. to semantic tokens (which would break the dark homepage), add `[data-theme="light"] .card { ... }` overrides in globals.css. This preserves dark-page styling while enabling light-page usage of the same CSS classes.

**Pattern: Modal overlays (`bg-obsidian-900/50`) are NOT dark-theme remnants.** Semi-transparent dark backdrops are correct on both themes — they dim whatever's behind the modal. Do not convert these to semantic tokens.

### 2026-02-10 — Vault Transition + Light Theme Table Polish (Sprint 127)

**Trigger:** Sprint 127 — login transition animation + light theme visual refinements.

**Pattern: Full-screen overlay transitions should store pending redirect, not block navigation.** The VaultTransition intercepts the login flow by storing `pendingRedirect` in state instead of calling `router.push()` immediately. The component's `onComplete` callback triggers the actual navigation. This keeps the transition decoupled from auth logic — the login page controls when to show it, and auto-redirects for already-authenticated users bypass it entirely.

**Pattern: `prefers-reduced-motion` should skip, not slow down.** For users who opt out of animations, don't show a faster version — skip the animation completely. The VaultTransition returns `null` and calls `onComplete` immediately when reduced-motion is detected. This respects the user's intent rather than just reducing animation intensity.

**Pattern: Zebra striping + warm hover on light theme tables use `even:bg-oatmeal-50/50` + `hover:bg-sage-50/40`.** Tailwind's `even:` variant targets `:nth-child(even)` which naturally alternates rows in `<tbody>`. The sage hover (vs grey) gives a warm, on-brand feel. Expanded rows override to `bg-sage-50/30` to differentiate from hover state.

**Gap: BenchmarkCard/BenchmarkSection still uses hardcoded dark-theme classes.** Sprint 126 migrated "diagnostics components" but the benchmark components under `components/benchmark/` were missed. These render on the TB page (light theme) but still use `bg-obsidian-800/80`, `border-obsidian-600`, etc. Needs dedicated migration.

### 2026-02-10 — Memo Data Shape Must Match Tool Output, Not Backend Model (Sprint 128)

**Trigger:** Multi-Period memo generator was initially designed around `PeriodComparison.to_dict()` (balance_sheet_variances, income_statement_variances, ratio_variances) but the Multi-Period frontend tool produces `MovementSummaryResponse` (per-account movements, lead sheet summaries, movements_by_type/significance). These are from two different backend modules (`prior_period_comparison.py` vs `movement_tracker.py`).

**Pattern: Always check the frontend data shape before designing a memo generator.** The memo generator must accept data that the frontend can actually provide. Reading the hook (`useMultiPeriodComparison`) and the page component reveals the exact response structure. Designing the Pydantic input model first (from the hook's TypeScript types) and THEN building the memo generator around it prevents wasted work.

**Pattern: Strip nested arrays from lead_sheet_summaries before sending to memo endpoint.** Each `LeadSheetMovementSummary` contains a full `movements[]` array (one entry per account). The memo only needs the summary-level fields (lead_sheet, name, count, prior_total, current_total, net_change). The frontend strips `movements` before POSTing to keep the payload small and avoid serializing potentially thousands of account entries.

**Pattern: Memo "Download Memo" as primary (sage-600 filled), "Export CSV" as secondary (border outline).** PDF memos are the higher-value audit artifact (workpaper-ready with ISA references and sign-off blocks). CSV is a data export supplement. Making the memo button visually primary guides users toward the more useful export.

### 2026-02-10 — useBenchmarks Mock Must Include All Destructured Fields (Sprint 129)

**Trigger:** TrialBalancePage test failed with `clearBenchmarks is not a function`. The page destructures `{ clear: clearBenchmarks, fetchIndustries, compareToBenchmarks }` from `useBenchmarks()`, but the test mock only provided `{ fetchComparison, industriesFetchedRef }`.

**Pattern: When mocking hooks for complex pages, read the page's destructuring pattern first.** The TB page destructures ~6 fields from `useBenchmarks()`. Missing any function causes a "not a function" error on first useEffect that calls it. Always inspect the page's `const { ... } = useHook()` line before writing the mock.

### 2026-02-10 — Inline Components Need Mock Data for All Referenced Fields (Sprint 129)

**Trigger:** MultiPeriodPage test failed with `result is not iterable`. The `AccountMovementTable` component spreads `comparison.all_movements`, but the test mock for `comparison` only included `significant_movements`.

**Pattern: When a page renders inline sub-components (not imported), the test mock must include ALL fields the sub-components access.** Unlike imported components that can be stubbed, inline components run real code. Check what fields they read from shared state (like `comparison.all_movements`) and include those in the mock.

### 2026-02-10 — Mock Barrel Exports Must Include ALL Named Exports Used by Page (Sprint 130)

**Trigger:** BankRecPage and ThreeWayMatchPage tests had been failing since Sprint 111 when `FileDropZone` was extracted to `@/components/shared`. The tests mocked `@/components/shared` with only `{ ToolNav }`, but both pages also import `FileDropZone` from the same barrel. React received `undefined` for `FileDropZone`, causing "Element type is invalid" errors.

**Pattern: When mocking a barrel file (`@/components/shared`), include ALL named exports the page uses, not just one.** The quick fix is: `jest.mock('@/components/shared', () => ({ ToolNav: () => ..., FileDropZone: ({ label }: any) => <div>{label}</div> }))`.

**Pattern: Hook method names must match the page's destructuring, not just semantics.** BankRec hook returns `reconcile` but the test mock provided `runReconciliation`. Always verify the page's `const { ... } = useHook()` line.
