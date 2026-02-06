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

*Add new lessons below this line. Newest at bottom.*

---

### 2026-02-06 — Composition Over Modification for Multi-Way Comparison (Sprint 63)
**Trigger:** Needed three-way comparison but two-way engine was already tested with 63 tests.
**Pattern:** Wrap existing function rather than modifying it. `compare_three_periods()` calls `compare_trial_balances()` then enriches results with budget data. This preserves all existing tests and keeps the two-way path unchanged.
**Example:** Build budget lookup dict from normalized account names, iterate two-way movements and attach BudgetVariance objects. New endpoint `/audit/compare-three-way` is separate from `/audit/compare-periods`.

### 2026-02-06 — SignificanceTier Enum vs String in Tests (Sprint 63)
**Trigger:** Test `test_budget_variance_to_dict` failed because it passed string `"minor"` instead of `SignificanceTier.MINOR` enum. The `to_dict()` method called `.value` on a string.
**Pattern:** When constructing test dataclasses that use enums, always import and use the enum member, not its string value. Verify serialization output separately.
**Example:** `BudgetVariance(variance_significance=SignificanceTier.MINOR)` not `BudgetVariance(variance_significance="minor")`
