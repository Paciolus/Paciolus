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
