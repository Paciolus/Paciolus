# Lessons Learned

> **Protocol:** After ANY correction from the CEO or discovery of a better pattern, document it here. Review at session start.

---

## Security Sprint: Billing Redirect Integrity

### Server-Side URL Derivation > Allowlist Validation for Redirect Security
When a redirect URL is only ever one of two values (`/checkout/success` and `/pricing`), the correct control is to derive both server-side from `FRONTEND_URL` — not to validate user-supplied strings against an allowlist. Allowlist approaches require URL parsing and are vulnerable to Unicode normalization, subdomain squatting, and path traversal bypasses. Full derivation eliminates the attack surface entirely because no user input touches the field at all.

### Pydantic `model_validator(mode='before')` Fires Before `extra='ignore'` Strips Fields
A `model_validator(mode='before')` receives the raw input dict including extra fields that `extra='ignore'` will subsequently discard. This makes it the correct place to monitor for injection attempts: the validator increments a Prometheus counter for each URL field detected, then returns the dict unchanged. Pydantic's field-stripping happens afterward, so the final model object never has those fields. This pattern gives both detection and elimination.

### Old Required-Field Tests Must Be Replaced When Fields Are Removed
Two tests in `test_pricing_launch_validation.py` expected `ValidationError` when `success_url`/`cancel_url` were omitted — because they were formerly required fields. After removing those fields, those tests silently passed with no assertion. The fix: replace with positive assertions that verify the new behavior (fields not on model, silently ignored when supplied). Always check for inverted-expectation tests (`pytest.raises(ValidationError)`) when removing required fields.

---

## Zero-Storage Architecture v2.1 Consistency Pass

### "Zero-Storage" Is a Scope Claim, Not an Absolute Claim
The phrase "zero-storage" can be misread as "we store nothing at all." In reality it means "no persistence of line-level financial data." Compliance documents must explicitly disambiguate this — a "Terminology Clarity" callout and a "Scope Boundaries" preamble in the compliance implications section prevent overstated claims and reduce legal exposure. When adding marketing-friendly labels to architecture docs, always include a definition box that states what the term covers and what it does not.

### Cross-Doc Retention Alignment Is a Recurring Maintenance Task
Every time a retention value changes (e.g., "2 years" → "365 days"), all 4 compliance docs (Zero-Storage, Privacy, Security, ToS) must be updated in lockstep. A grep for the old value across `docs/04-compliance/` is the minimum verification step before closing a retention-related directive. The v2.0 pass already fixed "2 years" → "365 days" everywhere, so the v2.1 pass found nothing to fix — but the verification step confirmed consistency and should never be skipped.

### Control Verification Tables Add Auditor-Ready Evidence
Listing automated safeguards (retention cleanup, ORM deletion guard, memory_cleanup, Sentry stripping, CI policy guard) in a structured table with mechanism + frequency columns gives auditors and enterprise customers a concrete checklist to verify. This is more useful than narrative descriptions because each row maps to a specific code path they can inspect.

---

## Phase LXIV: HttpOnly Cookie Session Hardening

### CSRF_EXEMPT_PATHS Changes Require a Test Audit Pass
When adding or removing a path from `CSRF_EXEMPT_PATHS` in `security_middleware.py`, the CSRF test suite in `test_csrf_middleware.py` contains tests that directly assert membership in that set. These tests will fail silently if not updated — "silently" meaning they fail the suite but the intent (asserting the *old* policy) is wrong. When `/auth/logout` was removed from `CSRF_EXEMPT_PATHS`, four test cases needed updating: `test_auth_logout_exempt` (inverted to `not in`), `test_all_new_exempt_paths_pass` (path removed from tested list), `test_logout_exempt_documented` (checked for old comment text), and `test_exempt_set_is_frozen` (expected set updated). **Rule:** Any `CSRF_EXEMPT_PATHS` change must be followed by `grep -n "auth/logout\|CSRF_EXEMPT" backend/tests/test_csrf_middleware.py` (substituting the affected path) to find all assertions before running the suite.

### Mandatory Directive Protocol Applies to Security Sprints Too
Security hardening sprints (auth migration, CSRF changes, cookie policy) are often well-planned but executed with urgency, creating a tendency to skip the todo.md entry. The plan file (`.claude/plans/`) is not a substitute — the mandatory directive protocol requires writing the plan to `tasks/todo.md` as a checklist before implementation begins, regardless of sprint type. Skipping this step leaves no incremental tracking record, no review section with commit SHA, and no deferred item closure trail. The code quality is unaffected; the auditability is not.

---

## Sprint 448: pandas 3.0 Evaluation

### pandas 3.0 String Dtype: `dtype == object` Guard Breaks for CSV String Columns
**Correction:** pandas 3.0 uses `pd.StringDtype()` (displayed as `str`) for string columns read from CSV, replacing the old `object` dtype. Any guard of the form `if df[col].dtype == object:` silently skips string columns entirely, disabling the check.
**Root Cause:** The `dtype == object` pattern was valid for pandas 2.x but is not forward-compatible with pandas 3.0's new default string storage.
**Impact Found:** `shared/helpers.py:571` — cell-length protection for CSV uploads was bypassed. A cell with 100,001 characters would pass through without raising `HTTPException(400)`.
**Fix:** Replace `df[col].dtype == object` with `pd.api.types.is_string_dtype(df[col])`. This API returns True for both `object` dtype (pandas 2.x) and `pd.StringDtype()` / `str` dtype (pandas 3.0+).
**Prevention Rule:** Never use `dtype == object` to identify string columns. Always use `pd.api.types.is_string_dtype()`. Grep for `dtype == object` after any pandas major version bump.

### Dependabot Merges of Deferred Risky Dependencies Still Require the Evaluation Sprint
A dependency listed in the Deferred Items table as "needs dedicated evaluation sprint" is not closed by a green test suite alone — it requires the explicit evaluation (CoW audit, dtype verification, perf baseline). The test suite passing is a necessary condition but not sufficient. Merging via dependabot does not substitute for the evaluation. **Rule:** When a deferred item's dependency is merged, immediately schedule the evaluation sprint and run it before the next unrelated sprint begins. Update the Deferred Items table with evaluation findings.

### pandas 3.0 CoW Patterns That Are Safe (Verified 2026-02-27)
- `df = df.copy()` before column mutation — SAFE
- `df.iloc[start:end].copy()` for chunked processing — SAFE
- `df.drop(columns=[...], inplace=True)` for `drop` specifically — SAFE (not deprecated in 3.0)
- Dict-based `accumulator[key]["field"] += value` — SAFE (not a DataFrame operation)
- `df[col] = df[col].apply(...)` column reassignment — SAFE (not chained indexing)

---

## Phase LXII: Export & Billing Test Coverage (Sprint 447)

### ORM Model Must Be Imported at Collection Time for `create_all()` to Create Its Table
When writing tests for a model that isn't imported by `conftest.py` (e.g., `Subscription` from `subscription_model.py`), the `db_engine` session-scoped fixture runs `Base.metadata.create_all()` before the model is ever imported — so the table is missing. **Fix:** Add a top-level import in the test file (`import subscription_model  # noqa: F401`) so the model registers with `Base.metadata` during pytest collection, before the session fixture runs. This is a one-line fix, but the failure mode (`OperationalError: no such table`) is opaque.

### Route Integration Tests Must Mock Generators, Not Routes
Export routes that delegate to PDF/Excel generators (`generate_audit_report`, `generate_workpaper`, etc.) cannot be tested end-to-end without the full library chain. The correct pattern is to patch the generator at the import location in the route module (e.g., `patch("routes.export_diagnostics.generate_audit_report", return_value=b"%PDF-1.4 fake")`) and verify the HTTP status + response headers. This achieves >90% route coverage without requiring PDF/Excel test fixtures.

### Entitlement Factory Dependencies Can Be Called Directly as Python
`check_tool_access("tool_name")` returns an inner function `_dependency(user)`. In tests, call it as `dep = check_tool_access("tool_name"); dep(user=user)` — no FastAPI DI needed. This produces clean unit tests that run in milliseconds without a TestClient or database.

---

## Sprints 445–446: Coverage Analysis + Usage Metrics Review

### React 19 userEvent + Blur Validation: Same Pattern Applies Beyond Submit
The React 19 `userEvent` timing issue documented in Phase LXI also affects blur-triggered validation. A test using `user.type(input, 'A')` + `user.tab()` fails to trigger the `onBlur` validation error because the state update from typing may not flush before the tab event fires. **Fix:** Use `fireEvent.change(input, { target: { value: 'A' } })` + `fireEvent.blur(input)` — same synchronous fireEvent pattern as the submit fix. All input validation tests should use `fireEvent` not `userEvent` when testing value-dependent blur behavior.

### Route Coverage vs Engine Coverage Are Decoupled
Backend route files (`routes/export_diagnostics.py` at 17%, `routes/billing.py` at 35%) can have very low coverage even when their underlying engines are 100% covered. This is because route tests (HTTP-level) require a running TestClient and database fixtures, while engine tests (unit-level) only need Python imports. Route coverage gaps are high-risk because they miss auth guard enforcement, request parsing errors, response model validation, and middleware interactions — things the engine tests don't exercise.

### `pytest-cov` Is Not in Default Dev Dependencies
The `pytest-cov` and `coverage` packages were not installed in the backend venv. They must be installed manually for coverage runs. Add to `requirements-dev.txt` if one exists, or document in CONTRIBUTING.md as a prerequisite for local coverage analysis.

---

## Phase LXI: Technical Upgrades (Sprints 441–444)

### React 19 + jsdom: Form Submission Testing Pattern
React 19 changes how `requestSubmit()` works in jsdom, breaking tests that use `userEvent.click()` on submit buttons. `userEvent.type()` + `userEvent.click()` causes stale values because React batches state updates and the submit fires before re-render completes. **Fix:** Use `fireEvent.change()` (sets values synchronously) + `act()`-wrapped `fireEvent.submit(form)`. This pattern bypasses keyboard simulation timing issues entirely.

### useEffect Must Return on All Paths with `noImplicitReturns`
When `tsconfig.json` has `noImplicitReturns: true`, a `useEffect` with a cleanup return inside an `if` branch but no return on the else branch fails the build. Use early-return guard (`if (!condition) return;`) instead of wrapping the body in `if (condition) { ... return cleanup; }`.

### Test Suites Can Mask Schema Drift
`test_timestamp_defaults.py` used raw SQL `INSERT INTO clients` that was missing 3 NOT NULL columns added in later migrations (`reporting_framework`, `entity_type`, `jurisdiction_country`). Tests passed before because the columns were added after the test was written. When upgrading SQLAlchemy, stricter constraint enforcement can surface these mismatches. Keep raw SQL inserts in sync with current schema.

---

## Sprint 440: Billing Smoke Test

### Stripe API Errors Must Be Caught at the Route Level
All 6 billing endpoints that call Stripe (checkout, cancel, reactivate, add-seats, remove-seats, portal) were missing try/except around the Stripe SDK calls. When Stripe returns an error (e.g., business name not set, invalid subscription ID), the exception propagated to the global handler and produced a generic 500. Wrap all external API calls in try/except at the route level and return 502 ("Payment provider error") so users and frontend get actionable status codes. This is especially important because Stripe has many configuration prerequisites (business name, product creation, webhook setup) that may not be met in all environments.

### SQLAlchemy `Enum(PythonEnum)` Stores Member NAMES, Not Values
When using `Column(Enum(SubscriptionStatus))` with a Python `str` enum like `class SubscriptionStatus(str, Enum): ACTIVE = "active"`, SQLAlchemy stores the enum **member name** (`ACTIVE`) in the DB, not the value (`active`). Raw SQL inserts must use `'ACTIVE'` not `'active'`, or the ORM will fail with a `KeyError` when loading the row. This applies to all `Enum()` column types that reference Python enums.

---

## Sprint 439: BillingEvent Migration + Runbook Fix

### Model-Without-Migration Is a Silent Production Bomb
Phase LX defined `BillingEvent` in `subscription_model.py` and wired it into `analytics.py` + `webhook_handler.py`, but never created the Alembic migration. SQLite tests passed because the test harness uses `Base.metadata.create_all()`, which creates all tables from models directly — masking the missing migration. In PostgreSQL production, the table wouldn't exist. Lesson: after adding any new SQLAlchemy model, immediately verify it has a corresponding Alembic migration AND is imported in `env.py`. The test suite's `create_all()` is not a substitute for a real migration.

### Runbook Staleness After Enum Renames
The `starter → solo` rename (d9e0f1a2b3c4) updated `.env.example`, code, and tests, but missed `docs/runbooks/billing-launch.md` and `pricing-rollback.md` which still referenced `STRIPE_PRICE_STARTER_*`. Lesson: when renaming an enum value, grep ALL documentation (not just code + tests) for the old name. Runbooks and deployment guides are especially dangerous because they're used manually in production by people who won't get a compiler error.

---

## Pricing Launch Validation Matrix

### Frontend Tests: Prefer `getAllByText` Over `getByText` for Prices
When testing pages where the same text appears in multiple locations (e.g., `$50/mo` in both a plan summary header and a price breakdown line), `getByText` throws "Found multiple elements." Use `getAllByText` with a `.length` assertion instead: `expect(screen.getAllByText('$50/mo').length).toBeGreaterThanOrEqual(1)`.

### Frontend Tests: DOM Navigation for Seat Counters
Numeric seat counters (e.g., "1", "5") collide with other DOM text. Instead of `getByText('5')`, navigate the DOM relative to a unique aria-labeled button: `screen.getByLabelText('Add seat').previousElementSibling`. This avoids multi-match errors while staying structurally coupled to the component layout.

---

## Phase LIX Sprint F: Integration Testing + Feature Flag Rollout

### Prometheus Counter Names Strip `_total` in `collect()`
`prometheus_client` internally appends `_total` to Counter metric names per OpenMetrics convention. When iterating `REGISTRY.collect()`, the returned `Metric.name` is the base name (e.g., `paciolus_pricing_v2_checkouts`), not the full `_total` suffixed name. Tests that verify counter presence on a registry must match the base name, not the `_total` variant.

---

## Phase LIX Sprint B: Seat Model + Stripe Product Architecture

### SQLAlchemy Column `default=` Does NOT Apply on Bare Instantiation
`Column(Integer, default=1)` only fires on `INSERT` (via `db.add()` + `db.flush()`). A bare `Subscription()` object will have `seat_count = None`, not `1`. Tests that verify defaults must either: (a) test in DB context with `db_session.flush()`, or (b) test the property/method that handles `None` gracefully (e.g., `total_seats` uses `self.seat_count or 1`). This is distinct from `server_default` which only applies at the SQL level.

---

## Phase LIX Sprint A: Pricing Model Overhaul

### Test Fixture Defaults Cascade Through Entire Suite
When changing `UserTier.PROFESSIONAL` entitlements from all-tools to starter-level, the `conftest.py` default `make_user(tier=UserTier.PROFESSIONAL)` would have broken ~30 test files. The fix was to update the default to `UserTier.TEAM` and mechanically update all explicit `tier=UserTier.PROFESSIONAL` call sites. Lesson: test fixture defaults are a high-leverage coupling point — changing the semantics of a tier value requires auditing every fixture that uses it as a default.

### Display-Name Layer Prevents DB Enum Lock-In
PostgreSQL enum values can be added but not easily removed or renamed. Using a thin display-name mapping (`tier_display.py`) instead of renaming the enum lets us change public branding without touching the DB schema, Stripe metadata, or Alembic migrations. This pattern should be used for any future renaming of enums that are persisted in PostgreSQL.

---

## Sprint 6: Source Document Transparency

### Cross-Cutting Sprints Require Import Verification on Every File
When adding function calls (e.g., `create_leader_dots()`) to existing files during a cross-cutting sprint, always verify the function is already imported. `currency_memo_generator.py` used `create_leader_dots` in its inline source line but lacked the import — caught by regression tests (`TestCurrencyMemoLongInputs`) not by the new Sprint 6 tests. Lesson: regression suites across existing test files catch missing imports that targeted new tests may miss.

### Three Generator Categories Need Different Integration Patterns
The 20+ PDF generators fall into 3 categories: (A) cover-page via `build_cover_page()` + `ReportMetadata`, (B) header via `build_memo_header()`, (C) custom inline headers. Each category requires a different source-transparency integration pattern — (A) gets fields on the dataclass, (B) gets leader-dot lines after the header, (C) needs conditional replacement of hardcoded "Source File" lines. Identifying the categories upfront and applying the right pattern to each saved significant rework.

### PDF Binary Search Assertions Are Unreliable
ReportLab compresses text in PDF content streams, so `b"expected text" in pdf_bytes` will fail even when the text is correctly rendered. End-to-end PDF tests should assert `pdf_bytes[:5] == b"%PDF-"` (valid PDF header) and `isinstance(pdf_bytes, bytes)` rather than searching for raw text in the binary. Use unit tests on story flowables (pre-build) for text content assertions.

---

## Sprint 5: Heading Readability & Typographic Consistency

### Letter-Spaced Headings Were Confined to One File
Initial assumption was that spaced-caps headings ("E X E C U T I V E   S U M M A R Y") might be spread across many files. In reality, all 13 instances were in `pdf_generator.py` only. Memo generators used ALL-CAPS but not letter-spacing. A thorough audit upfront saved wasted effort searching wrong files.

### ALL-CAPS Headings Were Universal Across All 17 Memo Generators
While memo generators didn't use letter-spacing, every single one used ALL-CAPS section headers ("I. SCOPE", "II. METHODOLOGY"). The shared `memo_base.py` builders set the pattern, but many individual generators also had their own hardcoded headings. Converting to title case required touching 17 files — but because the pattern was consistent, the changes were mechanical and low-risk.

### Parametrized Test Discovery Catches Regressions Automatically
Writing tests that discover generator files via glob and parametrize assertions means new generators added in future sprints will automatically be checked for heading consistency — no manual test updates needed.

---

## Sprint 4: Text Layout Hardening

### Paragraph Wrapping Replaces String Slicing for PDF Tables
8 different memo generators independently used `[:N]` string slicing (with or without "..." ellipsis) to force text into fixed-width table columns. This pattern hides user data and creates inconsistent behavior (some add "...", some silently truncate). ReportLab's `Paragraph` flowable already auto-wraps text within its column width and dynamically expands row height — the slicing was unnecessary. Fix: wrap all text-heavy cells in `Paragraph(text, style)` and let ReportLab handle layout.

### repeatRows=1 Prevents Header Loss on Page Breaks
None of the 20+ PDF tables used `repeatRows=1`. When a large table spans multiple pages, the header row only appears on the first page, making subsequent pages unreadable. Adding `repeatRows=1` to all multi-row data tables ensures the header repeats on every page. Minimal effort, significant readability improvement.

### VALIGN TOP Is Critical for Mixed-Height Rows
Two tables (currency memo, sampling memo) were missing `VALIGN: TOP`. When some cells wrap to 2-3 lines while others are single-line, the default middle alignment causes misaligned text across columns. Always include `("VALIGN", (0, 0), (-1, -1), "TOP")` in any table that may have wrapped cells.

---

## Sprint 0: Report Standards Alignment

### Two Parallel Style Systems Are More Divergent Than Expected
Audit of all 20 PDF generators revealed two completely independent style systems (`create_classical_styles` with 16 styles vs `create_memo_styles` with 11 styles) that share zero code. They differ in title size (28pt vs 24pt), body text color (OBSIDIAN_600 vs OBSIDIAN_DEEP), section header size (12pt vs 11pt), and signoff column widths. The currency and flux expectations memos additionally use Helvetica (a third font family) and dark-background GRID tables — a pattern found nowhere else. Lesson: when shared primitives exist (memo_base.py), generators still drift if there is no enforced spec. The standards doc now locks every font, size, color, and margin to prevent future drift.

### Diagnostic Extension Memos Use Hardcoded Workpaper Codes
Five diagnostic memos (preflight, population profile, expense category, accrual completeness, flux expectations) use static `WP-PF-001`-style codes instead of dynamic `generate_reference_number()`. This creates duplicate reference numbers across different clients and periods. Migration plan assigns unique prefixes (PFL-, PPR-, ECA-, ACE-, FEX-) and requires dynamic generation.

---

## Sprint 420: Verification & Cleanup Release

### Redundant sr-only Inputs With Custom ARIA Checkboxes
Sprint 412c added `role="checkbox" aria-checked tabIndex={0} onKeyDown` to custom checkbox divs in login/register, but left the original `<input type="checkbox" class="sr-only">` in place. This created duplicate checkbox roles — `getByRole('checkbox')` found two elements, breaking tests. When upgrading a custom control to proper ARIA attributes, remove the hidden native input it was originally wrapping. The ARIA div IS the accessible control now.

---

## Sprint 415: Accessibility Semantic Fixes

### Modal Backdrops Should Use role="presentation", Not role="button"
Sprint 412c added `role="button" tabIndex={-1}` to a modal backdrop for ESLint compliance, but this is semantically incorrect — a backdrop is not an interactive control. The `tabIndex={-1}` contradicts the button role (removes from tab order), and the `onKeyDown` handler is unreachable. Correct pattern: `role="presentation"` with just `onClick` for click-outside-to-close. The backdrop's close behavior is a convenience, not an accessibility control — the real close mechanism is the modal's Cancel button or Escape key (via useFocusTrap).

---

## Phase XLIX: Diagnostic Feature Expansion (Sprints 356–361)

### Multiple FKs to Same Table Require foreign_keys Disambiguation
When adding `completed_by = ForeignKey("users.id")` to the Engagement model which already had `created_by = ForeignKey("users.id")`, the User model's `engagements` relationship needed `foreign_keys="[Engagement.created_by]"` and the Engagement model's `creator` relationship needed `foreign_keys=[created_by]`. Same pattern from Phase XLVI's SoftDeleteMixin, but this time for a non-mixin column. Always add `foreign_keys=` disambiguation when a model has 2+ FKs to the same target table.

### Allowlist Constants Must Be Updated When Adding Model Fields
Sprint 354 added `approved_by`/`approved_at` to AdjustingEntry but didn't update `ALLOWED_ADJUSTMENT_ENTRY_KEYS` in `tool_session_model.py`. This caused a pre-existing test failure that persisted across 6 sprints until caught in the Phase XLIX wrap. When adding fields to a model with an allowlist/blocklist sanitizer, always search for the allowlist constant and update it.

### Revenue Decline `else` Branch Missing Severity Assignment
In `going_concern_engine.py`, the `_test_revenue_decline()` function had `severity` assigned in the `if triggered:` branch but not in the `else:` branch, causing `UnboundLocalError`. When writing branching logic that builds a return value, ensure ALL branches initialize ALL variables used in the return statement.

---

## Phase XLVI: Audit History Immutability (Sprint 345–349)

### SoftDeleteMixin Creates Ambiguous ForeignKeys
When a mixin adds `archived_by = Column(Integer, ForeignKey("users.id"))`, any model that already has a FK to `users.id` (e.g., `user_id`) will cause SQLAlchemy `AmbiguousForeignKeysError` on relationships. The fix is to explicitly declare `foreign_keys=[user_id]` on every relationship pointing to User from an affected model, and `foreign_keys="[Model.user_id]"` on the reverse relationship in User. This affected 3 models (ActivityLog, DiagnosticSummary, FollowUpItemComment) and 2 User reverse relationships.

### ToolRun Ordering Needs Secondary Sort
`get_tool_run_trends()` ordered by `run_at.desc()` only. When two ToolRuns are recorded in the same test nearly simultaneously, they can get the same `run_at` timestamp, making the ordering non-deterministic. Adding `ToolRun.id.desc()` as a secondary sort key guarantees deterministic ordering. This was a pre-existing flaky test exposed by the full suite run.

## Phase XLV: Monetary Precision Hardening (Sprint 340–344)

### BALANCE_TOLERANCE as Decimal, Not Float
The float literal `BALANCE_TOLERANCE = 0.01` was used in 10 locations for balance comparisons. Comparing `abs(float_diff) < 0.01` has subtle issues: the float 0.01 itself is inexact (`Decimal(0.01)` = `0.01000000000000000020816681711721685228163...`). Replacing with `Decimal("0.01")` and comparing `abs(Decimal(str(diff))) < BALANCE_TOLERANCE` eliminates this.

### Alembic Multiple Heads
When the migration chain has multiple heads (two independent branches), you must merge them first (`alembic merge heads -m "message"`) before creating a new migration. Otherwise Alembic refuses to generate a new revision.

### SQLite + Alembic ALTER COLUMN
SQLite doesn't support ALTER COLUMN natively. Alembic's `batch_alter_table` creates a temp table, copies data, drops original, and renames. This works but is slow on large tables. For the dev SQLite DB, the models define the schema via `init_db()` not Alembic, so `alembic stamp head` is needed to mark the DB as current.

### Python round() Uses Banker's Rounding
`round(2.225, 2)` = `2.22` (ROUND_HALF_EVEN), not `2.23`. For financial applications, always use `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`. The `quantize_monetary()` shared utility encapsulates this.

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

### Inline Imports in Methods Defeat Return Type Annotations
**Discovered:** Sprint 414. `def _make_evidence(self, ...) -> "ContractEvidenceLevel":` with `from engine import ContractEvidenceLevel` inside the method body triggers ruff F821 (undefined name) because the string annotation references a name not in module scope. Either move the import to module level or remove the return type annotation. Prefer module-level imports in test files — there's no circular import risk.

### Account Classifier Lives in `account_classifier.py`
The `AccountClassifier` class and `create_classifier()` factory are in `account_classifier.py`, NOT `classification_rules.py`. The latter only has `ClassificationRule`, `ClassificationResult`, and `AccountCategory`. Sprint 289 learned this the hard way.

### Priority Ordering in Greedy Column Assignment
**Discovered:** Sprint 151. When multiple field configs match the same column name (e.g., "cost" matches both `cost` and `accum_depr`), lower `priority` numbers are assigned first. Always assign the most specific columns first.

### Guardrail Tests Must Inspect Module, Not Function
**Discovered:** Sprint 157. After refactoring memo generators to delegate to shared template, `inspect.getsource(function)` no longer contains ISA references — they're in module-level config. Use `inspect.getsource(inspect.getmodule(function))` instead. Source-code guardrail tests are brittle under refactoring.

### Centralized Error Sanitization
**Discovered:** Sprint 122. Use regex patterns to match common exception types (pandas, openpyxl, SQLAlchemy, reportlab) and map to user-friendly messages. `except ValueError` is safe (controlled messages); `except Exception` leaks tracebacks and needs sanitization. **Refinement (Sprint 252):** `allow_passthrough=True` mode for CRUD validation routes — dangerous patterns still caught, but safe business-logic messages pass through unchanged. Without this, all ValueErrors become generic "An unexpected error occurred."

### Rate Limiting Requires `Request` as First Parameter
Slowapi's `@limiter.limit()` decorator requires FastAPI `Request` as first positional parameter. When a Pydantic body model is already named `request`, rename it to `payload`.

### Upload Validation in Two Layers
Content-type and extension checks in `validate_file_size` (before bytes consumed). Encoding fallback and row count checks in `parse_uploaded_file` (during parsing). Short-circuit early.

### Memo Generator API Signatures Must Match
**Discovered:** Sprint 259. The shared memo base functions have specific signatures: `build_memo_header(story, styles, doc_width, title, reference, client_name)`, `build_workpaper_signoff(story, styles, doc_width, ...)`, and `generate_reference_number()` (no args). Always read the actual signature before using — the style key is `MemoSection` (not `MemoSectionHeader`), and color tokens are `OBSIDIAN_700` / `OATMEAL_400` (not `_LIGHT` / `_DARK`).

---

## Frontend Patterns

### framer-motion Type Assertions
TypeScript infers `'spring'` as `string`, but framer-motion expects literal types. Always use `as const` on transition properties. Applies to ALL framer-motion transitions extracted to module-level consts.

### framer-motion Performance Rules (Sprint 240)
- **Never animate `width`/`height` for visual-only effects** — use `scaleX`/`scaleY` + `transformOrigin` instead. Progress bars: `scaleX: progress/100` with `w-full` and `transformOrigin: 'left'`. Light-leak effects: set width statically, animate `scaleX`.
- **Infinite `boxShadow` animations in JS are expensive** — `boxShadow` forces repaint every frame. Move to CSS `@keyframes` where the browser can optimize off main thread. Limit decorative pulses to 3 cycles.
- **`AnimatePresence` children must be `motion.*` elements** — plain `<div>` inside `AnimatePresence mode="popLayout"` won't fire exit animations. The immediate child must be a motion component.
- **`AnimatePresence` is pointless on always-rendered content** — if early returns prevent the component from mounting, the exit animation never fires.
- **`<MotionConfig reducedMotion="user">` in root providers** — single line that makes all framer-motion animations respect `prefers-reduced-motion`. Highest-ROI accessibility fix.
- **`key={index}` in `AnimatePresence` causes wrong exit animations** — use stable IDs (counter ref or UUID) for list items that can be deleted from the middle.
- **Add `layout` prop to filterable/deletable list items** — prevents remaining items from jumping position when siblings are removed.

### God Component Decomposition — Extract Hook First
**Discovered:** Sprint 159. When decomposing a god component: (1) extract the custom hook with ALL logic first, (2) extract self-contained presentational sub-components, (3) the page becomes a thin layout shell. Tests pass without modification because jest.mock applies at module level.

### useEffect Referential Loop Prevention
Use `useRef` to track previous values. Compare prev vs current before triggering effects. For multiple params, use composite hash comparison.

### Memoize `initialValues` When Passed to Hooks That Derive Callbacks
**Discovered:** Sprint 414b. `useFormValidation({ initialValues: getInitialValues() })` creates a new object every render. If the hook's `reset` callback depends on `initialValues` (via `useCallback([initialValues])`), then `reset` is also recreated every render. Adding `reset` to a `useEffect` dep array causes an infinite re-render loop — the effect calls `reset()`, which updates state, which re-renders, which creates new `initialValues`, which creates new `reset`, which re-triggers the effect. A `useRef` guard only prevents the body from executing, not the effect from re-scheduling. **Fix:** `useMemo` the `initialValues` object on the actual primitive fields (`client?.name`, `client?.industry`, etc.) so the hook's derived callbacks are referentially stable.

### Modal Result Handling
Always check async operation result before closing modal. `if (await action()) closeModal()` — never fire-and-forget. Show errors IN the modal, not after it closes.

### Next.js Suspense Boundary for useSearchParams
Pages using `useSearchParams()` must wrap content in `<Suspense>`. Build-time requirement in Next.js 14+.

### TypeScript Type Guards with Array.filter()
`.filter(x => x)` doesn't narrow types. Use type predicate: `.filter((entry): entry is { key: string } => entry !== undefined)`.

### Ghost Click Prevention
File inputs with `position: absolute; inset: 0` capture unintended clicks. Fix: `pointer-events-none` + `tabIndex={-1}` when not in idle state.

### TypeScript `interface` vs `type` for Index Signature Compatibility
**Discovered:** Sprint 227. `interface Foo { a: string }` does NOT satisfy `Record<string, unknown>` because TypeScript interfaces lack implicit index signatures. `type Foo = { a: string }` DOES satisfy it. When a generic constraint requires `Record<string, unknown>` (e.g., `TEntry extends Record<string, unknown>`), all concrete types passed as `TEntry` must be `type` aliases, not `interface` declarations. This affected 11 types across the codebase (7 entry data types + 4 form value types).

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

### Warm-Toned Shadows for Premium Light Themes
**Discovered:** Sprint 325. Neutral gray shadows (`rgba(33,33,33,...)`) feel clinical. Using warm-toned shadows (`rgba(139,119,91,...)`) with the same alpha values creates a parchment-adjacent feel that matches Oat & Obsidian's warm palette. Apply to light theme only — dark theme shadows should stay neutral.

### Card Hierarchy via CSS Custom Properties
**Discovered:** Sprint 325. Three tiers — `surface-card` (default white), `surface-card-elevated` (same white, bigger shadow), `surface-card-inset` (slightly tinted, inset shadow) — provide clear visual nesting without adding extra borders or backgrounds. The `.card-inset` utility class bundles bg + border + shadow for one-liner application.

### Left-Border Accent Pattern for Visual Rhythm
**Discovered:** Sprint 326. `border-l-4` with color-coded accents (sage for positive, clay for negative, oatmeal for neutral) creates consistent visual rhythm across stat cards, summary cards, and metric displays without adding bulk. Map colors to the component's health/status data via `themeUtils.ts` for consistency.

### CSS-Only Textures Over Image Assets
**Discovered:** Sprint 328. SVG `feTurbulence` encoded as a data URI provides paper-like texture at 0.015 opacity — no image downloads, no CDN dependency, fully CSS-contained. Always pair decorative textures with `prefers-reduced-motion: reduce` media query to disable them.

---

## Testing Patterns

### Layout Refactors Must Update Test Assertions
When moving components from pages to layouts (e.g., Sprint 207 moved ToolNav/VerificationBanner to `app/tools/layout.tsx`), the corresponding page-level test assertions become stale. Tests that mock `@/components/shared` at the page level will silently pass the mock setup but fail the assertion because the page no longer imports those modules. **Rule:** Any component relocation must include a grep for test mocks targeting the old import path.

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

### Mock the Import Path the Component Actually Uses
**Discovered:** Sprint 249. If a page imports from `@/components/engagement` (barrel), mocking `@/components/engagement/EngagementList` (individual file) does nothing — Jest resolves mocks by the exact import path string. Always mock the barrel path when that's what the source file imports.

### `getByText` Fails on Duplicated Page Text (Nav + Heading)
**Discovered:** Sprint 249. Pages with breadcrumb navigation often render the same text in both `<span>` (nav) and `<h1>` (heading). Use `getByRole('heading', { name: '...' })` to target the heading specifically, or `getAllByText` when both are valid.

### Named vs Default Export Mocks Are Not Interchangeable
**Discovered:** Sprint 249. `import { CommentThread } from './CommentThread'` requires mock `{ CommentThread: ... }`. Using `{ __esModule: true, default: ... }` silently resolves to `undefined` and causes "Element type is invalid" at render time — the error appears on click (expand), not on initial render, making it hard to diagnose.

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

### BaseHTTPMiddleware Cannot Raise HTTPException
Starlette's `BaseHTTPMiddleware` wraps exceptions in `ExceptionGroup`, so raising `HTTPException` inside `dispatch()` produces opaque errors. Return a `Response(content=..., status_code=..., media_type="application/json")` instead — matches the pattern in `MaxBodySizeMiddleware`.

### CSRF Middleware Breaks API Integration Tests
Registering CSRF middleware blocks all test POST/PUT/DELETE requests that don't include a CSRF token. Solution: add an autouse session fixture in conftest.py that patches `validate_csrf_token = lambda token: True`, then restore the original in `test_csrf_middleware.py` setup/teardown for explicit CSRF testing.

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
Separate deps → builder → runner stages. Only runtime in final image. Non-root users. Health checks. `sqlite:////app/data/paciolus.db` (4 slashes = absolute path). Use `pip install --prefix=/install` in builder to avoid copying pip/setuptools/wheel (~20MB) into production stage. Prefer `curl -f` for healthchecks over spawning a full Python interpreter every 30 seconds.

### .dockerignore Prevents Secrets in Build Context
Without `.dockerignore`, `docker build` sends everything (`.env`, `paciolus.db`) to the daemon, even if not COPY'd.

### Docker Compose Defaults Drift from Backend Config
**Discovered:** Sprint 250. `docker-compose.yml` had `JWT_EXPIRATION_MINUTES:-1440` (24h) but `config.py` was hardened to 30 minutes in Phase XXV Sprint 198. Compose env defaults silently override backend config module defaults. **Rule:** After any security hardening phase that changes config defaults, grep `docker-compose.yml` for the same env var and update the compose default to match.

### Gunicorn Worker Recycling for Pandas Memory
**Discovered:** Sprint 250. Long-running Gunicorn workers processing large DataFrames via Pandas accumulate memory over time. `--max-requests 1000 --max-requests-jitter 50` restarts workers after ~1000 requests, preventing slow memory leaks. Jitter prevents all workers from restarting simultaneously (thundering herd).

### Dockerfile HEALTHCHECK vs Compose healthcheck Duplication
**Discovered:** Sprint 250. Defining healthchecks in both `Dockerfile` and `docker-compose.yml` causes the compose definition to silently override the Dockerfile's `HEALTHCHECK`. Pick one location: Dockerfile for self-contained images, compose for orchestration-specific tuning. Don't duplicate.

### ReportLab Best Practices
Use get-or-create for styles (avoid "already defined" error). Use `onFirstPage`/`onLaterPages` callbacks for repeating elements. Wrap table cell text in `Paragraph` objects. Prefer built-in fonts. **Sprint 196:** Only reference styles that exist in the style dict being used (`create_classical_styles()` vs `create_memo_styles()` have different names). Only use fonts registered with `pdfmetrics` — `Times-*` and `Courier` are built-in; custom fonts like `Merriweather`/`Lato` require explicit registration. Always close BytesIO buffers after `getvalue()`.

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

### Phase XXVIII Sprint 210 — CI Pipeline
Ruff linting caught a real bug: `fixed_asset_testing_engine.py` used `re.sub()` without importing `re`. The function was reachable only on a `(ValueError, TypeError)` fallback path — never caught by tests because test data doesn't hit the regex branch. **Lesson:** Static analysis tools catch bugs that 2,903 tests miss, especially on error-handling paths. Start with conservative rules (Pyflakes only) and expand incrementally.

### Phase XXIII (Sprints 191-194)
4 sprints of Pandas performance and precision hardening, zero behavioral regressions. **Key lessons:** (1) `detect_abnormal_balances()` (standalone function) uses keyword matching but the streaming pipeline uses the classifier-based `StreamingAuditor.get_abnormal_balances()` — tests for vectorized keyword matching must call the standalone function directly, not the full pipeline. (2) `float('inf')` in JSON is not valid JSON — replacing with `None` for zero-prior percentages is both more correct and JSON-safe. (3) `max(abs(x), 0.01)` as a division guard is problematic because `0.01` is an arbitrary magic number that inflates percentages near zero — using config tolerances as the threshold with a 100% cap is semantically cleaner. (4) `math.fsum` is a true drop-in for `sum` on generators of floats — no signature changes, no test changes needed. (5) Identifier column dtype preservation must be post-read (not `dtype=str` globally) because `dtype=str` on all columns would break `pd.to_numeric` calls downstream.

### Phase XL (Sprints 292-299)
8 sprints closing 6 analytical gaps + 4 language risks from AccountingExpertAuditor review. **Key lessons:** (1) `build_disclaimer(story, styles, domain=..., isa_reference=...)` parameter is `domain=`, not `tool_name=` — always verify shared function signatures before use. (2) Backward compat aliases (`risk_reasons`) should be introduced in one sprint and removed in a follow-up cleanup sprint — never leave them permanently. (3) Frontend `getByText` fails when text appears in multiple DOM locations (e.g., "Revenue" as both account name and category) — use `getAllByText` and check length. (4) Section density sparse detection requires both balance and count checks: `count < 3 AND balance > materiality AND count > 0` — empty sections should never be sparse.

### Phase XLII (Sprints 313-318)
6 sprints of design foundation fixes and light theme semantic token migration. **Key lessons:** (1) WorkspaceHeader/QuickActionsBar/RecentHistoryMini render on the `/` route which is DARK themed — don't migrate these to light semantic tokens. Always verify which route a component renders on before migrating. (2) Components like RiskDashboard that render on BOTH themes (DemoZone on homepage = dark, tool pages = light) work automatically with semantic tokens since CSS custom properties adapt to `data-theme`. (3) When migrating medium-confidence color from `text-oatmeal-500` to `text-content-primary`, tests checking for `toContain('text-oatmeal')` will break — always update tests alongside component migrations. (4) Tooltips and toasts stay dark by design for visibility on both themes — skip these during light-theme migration.

### Phase XLIII (Sprints 319-324)
6 sprints transforming homepage from flat dark page to cinematic scroll-driven experience. **Key lessons:** (1) When using `Record<string, string>` with typed keys, TypeScript's `noUncheckedIndexedAccess` requires explicit type aliases for the key union (e.g., `type ElementSize = 'sm' | 'md' | 'lg'`) and `Record<ElementSize, string>` — otherwise `as const` arrays produce `string` inference for element fields. (2) Extracting large inline arrays (toolCards) from page.tsx into dedicated components (ToolShowcase) dramatically improves maintainability — page.tsx dropped from 323 to ~155 lines. (3) ProductPreview with stylized static mockups is lighter and more maintainable than DemoZone which imported real components (RiskDashboard, KeyMetricsSection) requiring demo data setup. (4) Fixed-position gradient mesh backgrounds need `pointer-events-none` and content sections need `relative z-10` to remain interactive above the atmospheric layer.

### Sprint 2: Unified Cover Page + Brand System
Report chrome extraction. **Key lessons:** (1) Circular imports between `pdf_generator.py` and `shared/report_chrome.py` — resolved via lazy imports inside methods rather than at module level. When module A defines primitives (ClassicalColors, DoubleRule) that module B needs, and B provides shared utilities that A wants, the consumer (A) must import lazily. (2) ReportLab's `StyleSheet1.get(key)` raises `KeyError` instead of returning `None` like a dict — a `_safe_style(styles, *names)` helper tries multiple key names with try/except to gracefully handle both `create_classical_styles()` (ClassicalTitle) and `create_memo_styles()` (MemoTitle) style systems. (3) PDF text content is compressed — raw byte search (`b"TITLE" in pdf`) fails. Verify cover page presence structurally (page count, `/Type /Page` occurrences, valid header/trailer).

### Sprint 337
Marketing motion consolidation. **Key lessons:** (1) Files with JSX components (CountUp, SectionReveal) must use `.tsx` extension, not `.ts` — even when the file is primarily constants/presets. (2) Always grep for ALL usages before deleting "dead" code — DemoZone appeared dead from homepage but was still imported by GuestMarketingView via barrel export. (3) `satisfies Record<string, Variants>` provides type-checking on variant objects without widening the type — useful for ensuring preset shapes are valid framer-motion Variants.
