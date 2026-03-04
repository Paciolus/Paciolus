# Paciolus Daily Digital Excellence Council Report
Date: 2026-03-04
Commit/Branch: e3d6c88 / main
Files Changed Since Last Audit: 19 (1,266 insertions, 297 deletions across 7 commits)

## 1) Executive Summary
- Total Findings: 17
  - P0 (Stop-Ship): 0
  - P1 (High): 0
  - P2 (Medium): 6
  - P3 (Low): 11
- Top Risk Themes (max 6 bullets, group findings by pattern):
  - **Accessibility — ARIA Gaps on New UI**: F-003, F-004, F-005, F-006, F-016, F-017 (6 findings)
  - **Incomplete Sprint 479 Remediation**: F-007, F-008 (2 findings — partial fixes from last council)
  - **Process Protocol Drift**: F-001, F-014, F-015 (3 findings — Sprint 481 undocumented, orphaned commits)
  - **Deployment Documentation Staleness**: F-002 (1 finding — blocks Sprint 447)
  - **Theme Token Compliance**: F-012 (1 finding — non-palette color in animation)
  - **Reduced-Motion Completeness**: F-009 (1 finding — CSS animation bypasses MotionConfig)
- Critical System Status:
  - Zero-Storage Integrity: **PASS** — No new data persistence. ExportShare exception properly documented in SECURITY_POLICY.md §2.4 (Sprint 479 F-002). All audit endpoints retain `memory_cleanup()` context manager.
  - Auth/CSRF Integrity: **PASS** — `encodeURIComponent()` defense-in-depth fix confirmed on workspace redirect. No auth changes in this cycle. HttpOnly cookie, CSRF HMAC, account lockout all unchanged.
  - Observability Data Leakage: **PASS** — No new Sentry breadcrumbs, no new `console.log` in production components, no financial data in tracking events. `trackEvent('view_pricing_page')` payloads contain only plan name and interval.

## 2) Daily Checklist Status

1. **Zero-storage enforcement (backend/frontend/logs/telemetry/exports):** ✅ PASS — No new data persistence pathways introduced. Pricing page uses client-side state only (React `useState`). HeroProductFilm is purely presentational with hardcoded demo content. No `localStorage`/`sessionStorage` usage in changed files.

2. **Upload pipeline threat model (size limits, bombs, MIME, memory):** ✅ PASS — No upload pipeline changes in this cycle. 10-step validation pipeline unchanged.

3. **Auth + refresh + CSRF lifecycle coupling:** ✅ PASS — Single change: `encodeURIComponent(pathname)` in workspace redirect (Sprint 479 F-005). Correctly prevents parameter injection. No auth flow modifications.

4. **Observability data leakage (Sentry/logs/metrics):** ✅ PASS — No new telemetry endpoints. Two new `trackEvent()` calls in pricing page with non-sensitive payloads only (`plan_name`, `interval`).

5. **OpenAPI/TS type generation + contract drift:** ⚠️ AT RISK (unchanged) — Still no automated OpenAPI→TypeScript pipeline. Pricing tier definitions manually synchronized (verified: all 14 feature/limit values match between `pricing/page.tsx` and `backend/shared/entitlements.py`). Drift risk persists.

6. **CI security gates (Bandit/pip-audit/npm audit/policy):** ✅ PASS — No CI pipeline changes. 11-job pipeline intact.

7. **APScheduler safety under multi-worker:** ✅ PASS — Documentation added to `.env.example` in Sprint 479 (F-006). No scheduler code changes.

8. **Next.js CSP nonce + dynamic rendering:** ✅ PASS — No CSP or proxy changes. `proxy.ts` unchanged.

## 3) Findings Table (Core)

### F-001: Sprint 481 Has No todo.md Entry
- **Severity**: P2
- **Category**: Process
- **Evidence**:
  - `tasks/todo.md` — Sprint 481 (commit `e3d6c88`, "Sprint 481: Plan Estimator redesign — uploads match tier limits, tools→features axis") has zero documentation. No checklist, no goal, no status, no review, no build verification record. Three preparatory commits (`d44239f`, `2991cfc`, `893715f`) are also untracked.
    - Explanation: The Mandatory Directive Protocol (CLAUDE.md) requires every directive to begin with a Plan Update to `tasks/todo.md` and end with a Lesson Learned. This exact pattern was already documented in `tasks/lessons.md` under "Ad-Hoc Creative Work Still Requires Todo Entries" — the lesson states "A retroactive entry immediately after commit is acceptable; no entry at all is not."
- **Impact**: Breaks audit trail for a production pricing page change. No evidence that build verification ran. Repeated violation of a previously-captured lesson indicates the lesson has not been internalized.
- **Recommendation**: Add retroactive Sprint 481 entry with goal, checklist, review, and commit SHA. Fold the three preparatory commits under its scope.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add retroactive Sprint 481 documentation to tasks/todo.md
  Files in scope: tasks/todo.md
  Approach: Add Sprint 481 entry with status COMPLETE, goal (Plan Estimator redesign), checklist of changes, build verification confirmation, and review section with commit SHAs e3d6c88, 2991cfc, d44239f, 893715f.
  Acceptance criteria:
  - Sprint 481 fully documented in todo.md Active Phase
  - All 4 commits referenced
  - Build verification recorded
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Verification Marshal (I)
- **Supporting Agents**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 8/9 Approve P2 | Dissent: Performance & Cost Alchemist (B): "Pricing page styling is low-risk; P3 sufficient for documentation gap on a cosmetic change."
- **Chair Rationale**: P2 sustained. The Directive Protocol is mandatory, not optional for "small" changes. The commit message itself uses "Sprint 481:" — confirming this was treated as a sprint, yet no planning artifacts exist.

---

### F-002: Stale Stripe Environment Variable Names in .env.example
- **Severity**: P2
- **Category**: Deployment/Ops
- **Evidence**:
  - `backend/.env.example:226-227` — References `STRIPE_PRICE_TEAM_MONTHLY` / `STRIPE_PRICE_TEAM_ANNUAL` — the "Team" tier was renamed to "Professional" in Phase LXIX.
  - `backend/.env.example:232-233` — References `STRIPE_SEAT_PRICE_MONTHLY` / `STRIPE_SEAT_PRICE_ANNUAL` but code loads `STRIPE_SEAT_PRICE_PRO_MONTHLY`, `STRIPE_SEAT_PRICE_PRO_ANNUAL`, `STRIPE_SEAT_PRICE_ENT_MONTHLY`, `STRIPE_SEAT_PRICE_ENT_ANNUAL`.
  - `backend/billing/price_config.py:36` — Dynamically constructs env var names from `_PAID_TIERS = ("solo", "professional", "enterprise")`.
    - Explanation: Anyone following `.env.example` to configure production Stripe billing will set the wrong env var names. The startup validator (`validate_billing_config`) will `sys.exit(1)` with a missing-key error, but the error message won't explain that `.env.example` is wrong.
- **Impact**: **Directly blocks Sprint 447 (Stripe Production Cutover)**. The CEO will use this file to configure production env vars. Wrong names → failed deployment → confusion.
- **Recommendation**: Update `.env.example` lines 220-233 to reference actual env var names: `STRIPE_PRICE_SOLO_MONTHLY/ANNUAL`, `STRIPE_PRICE_PROFESSIONAL_MONTHLY/ANNUAL`, `STRIPE_PRICE_ENTERPRISE_MONTHLY/ANNUAL`, `STRIPE_SEAT_PRICE_PRO_MONTHLY/ANNUAL`, `STRIPE_SEAT_PRICE_ENT_MONTHLY/ANNUAL`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Update .env.example Stripe variable names to match actual code
  Files in scope: backend/.env.example
  Approach: Cross-reference backend/billing/price_config.py for actual env var names. Update all STRIPE_PRICE_* and STRIPE_SEAT_PRICE_* entries. Remove references to "Team" tier.
  Acceptance criteria:
  - All Stripe env var names in .env.example match price_config.py
  - No references to deprecated "Team" tier
  - validate_billing_config() would pass with values from .env.example
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-003: Pricing Comparison Table Missing `scope` Attributes on Header Cells
- **Severity**: P2
- **Category**: Accessibility
- **Evidence**:
  - `frontend/src/app/(marketing)/pricing/page.tsx:888-892` — Table `<th>` elements lack `scope="col"`:
    ```tsx
    <th className="font-serif text-sm text-oatmeal-400 py-4 px-5 w-[20%]">Feature</th>
    <th className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[20%]">Free</th>
    ```
  - First column data cells use `<td>` instead of `<th scope="row">`.
    - Explanation: The 15-row comparison table has 5 columns (Feature, Free, Solo, Professional, Enterprise). Without `scope` attributes, screen readers cannot associate data cells with their column/row headers. Users navigating cell-by-cell will not hear contextual information like "Feature: Team Seats, Professional: 7 (up to 20)".
- **Impact**: WCAG 1.3.1 (Info and Relationships) — data table accessibility. Affects screen reader users navigating the pricing comparison.
- **Recommendation**: Add `scope="col"` to all `<th>` in `<thead>`. Convert first `<td>` in each data row to `<th scope="row">`. Add `<caption className="sr-only">` describing the table purpose.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add WCAG-compliant scope attributes to pricing comparison table
  Files in scope: frontend/src/app/(marketing)/pricing/page.tsx
  Approach: Add scope="col" to <th> elements in thead. Convert first-column <td> in data rows to <th scope="row">. Add <caption className="sr-only">Feature comparison across Free, Solo, Professional, and Enterprise tiers</caption>.
  Acceptance criteria:
  - All table headers have scope attributes
  - Table has sr-only caption
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-004: FAQ Accordion Missing `aria-controls` and Content Panel IDs
- **Severity**: P2
- **Category**: Accessibility
- **Evidence**:
  - `frontend/src/app/(marketing)/pricing/page.tsx:946-949` — FAQ buttons have `aria-expanded` but lack `aria-controls`:
    ```tsx
    <button
      onClick={() => toggleFaq(idx)}
      className="w-full flex items-center justify-between py-4 px-6 text-left group"
      aria-expanded={isOpen}
    >
    ```
  - `frontend/src/app/(marketing)/pricing/page.tsx:967` — Answer `<div>` lacks `id` and `role="region"`.
    - Explanation: WCAG disclosure widget pattern requires `aria-controls` to reference the `id` of the panel being shown/hidden, allowing assistive technology to navigate directly to the controlled content.
- **Impact**: WCAG 4.1.2 (Name, Role, Value) — screen readers can detect expanded/collapsed state but cannot navigate to the controlled content.
- **Recommendation**: Add `id={`faq-answer-${idx}`}` to each answer div, `aria-controls={`faq-answer-${idx}`}` to each button, and `role="region"` with `aria-labelledby` to answer containers.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add aria-controls and content IDs to FAQ accordion
  Files in scope: frontend/src/app/(marketing)/pricing/page.tsx
  Approach: Add unique id to each FAQ answer div, aria-controls pointing to it on each button, role="region" on answer containers.
  Acceptance criteria:
  - Each FAQ button has aria-controls matching its answer panel id
  - Answer panels have role="region" and aria-labelledby
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-005: Slider `aria-valuenow` Uses Stale MotionValue Snapshot
- **Severity**: P2
- **Category**: Accessibility
- **Evidence**:
  - `frontend/src/components/marketing/HeroProductFilm.tsx:383` — `aria-valuenow={Math.round(progress.get() * 100)}`
    - Explanation: `progress` is a `MotionValue` that updates outside React's render cycle (for animation performance). `.get()` returns the value at render time, not the current animated position. During auto-play, `aria-valuenow` could remain at 0% while the visual scrubber shows 50%.
- **Impact**: Screen reader users receive stale progress information during auto-play animation. The semantic slider pattern is correctly implemented (role, label, min/max) but the dynamic value is unreliable.
- **Recommendation**: Track progress via `progress.on('change', ...)` into a React state variable, or derive from `activeStep` (e.g., `Math.round((activeStep / 2) * 100)`).
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Fix stale aria-valuenow on timeline slider
  Files in scope: frontend/src/components/marketing/HeroProductFilm.tsx
  Approach: Replace progress.get() with a derived value from activeStep state: aria-valuenow={Math.round((activeStep / (STEP_LABELS.length - 1)) * 100)}. This updates on each step transition (render-triggered) and gives meaningful values (0, 50, 100).
  Acceptance criteria:
  - aria-valuenow updates on step changes
  - Screen reader announces correct progress
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: Systems Architect (A)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-006: Slider Missing `aria-valuetext` for Semantic Step Names
- **Severity**: P2
- **Category**: Accessibility
- **Evidence**:
  - `frontend/src/components/marketing/HeroProductFilm.tsx:379-384` — Slider has `aria-valuemin`, `aria-valuemax`, `aria-valuenow` but no `aria-valuetext`:
    ```tsx
    role="slider"
    aria-label="Timeline scrubber"
    aria-valuemin={0}
    aria-valuemax={100}
    aria-valuenow={Math.round(progress.get() * 100)}
    ```
    - Explanation: Without `aria-valuetext`, screen readers announce "Timeline scrubber, 50 percent" — which is meaningless. The slider maps to three named steps: Upload, Analyze, Export.
- **Impact**: Screen readers cannot convey the semantic meaning of slider positions. Users hear percentages instead of step names.
- **Recommendation**: Add `aria-valuetext={STEP_LABELS[activeStep]}` so screen readers announce "Timeline scrubber, Drop your file" / "Analyzing your data" / "Export your results".
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add aria-valuetext to timeline slider
  Files in scope: frontend/src/components/marketing/HeroProductFilm.tsx
  Approach: Add aria-valuetext={STEP_LABELS[activeStep]} to the slider div.
  Acceptance criteria:
  - Screen readers announce step name instead of percentage
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: None
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-007: Incomplete Sprint 479 F-004 Remediation — 3 f-string SQL Remain
- **Severity**: P3
- **Category**: Code Hygiene / Defense-in-Depth
- **Evidence**:
  - `backend/tests/test_timestamp_defaults.py:98` — `f"VALUES ({user_id}, 'abc123', 100, 1000.0, ...)"` in `test_activity_log_timestamp`
  - `backend/tests/test_timestamp_defaults.py:117-118` — `f"VALUES ({user_id}, 'Test Corp', ...)"` in `test_client_timestamps`
  - `backend/tests/test_timestamp_defaults.py:139-140, 147-149` — f-string interpolation in `test_engagement_timestamps`
    - Explanation: Sprint 479 fixed F-004 (SQL interpolation in tests) but only migrated `test_tool_run_timestamp` to `bindparams()`. Three other test methods still use f-string SQL. Values are integer scalars from prior queries — not exploitable.
- **Impact**: Inconsistent remediation. Zero exploitation risk (test-only code, integer literals from ORM).
- **Recommendation**: Convert remaining 3 f-string SQL statements to `.bindparams()` for consistency.
- **Primary Agent**: Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-008: Residual `status_code=200` on Accrual-Completeness Endpoint
- **Severity**: P3
- **Category**: API Consistency
- **Evidence**:
  - `backend/routes/audit.py:363` — `@router.post("/audit/accrual-completeness", response_model=AccrualCompletenessReportResponse, status_code=200)`
    - Explanation: Sprint 479 F-007 removed redundant `status_code=200` from 3 POST endpoints but missed this 4th instance. FastAPI defaults POST to 200, so this is cosmetic.
- **Impact**: No functional impact. Minor inconsistency.
- **Recommendation**: Remove `status_code=200` from line 363.
- **Primary Agent**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-009: CSS `animate-pulse` Bypasses MotionConfig Reduced-Motion
- **Severity**: P3
- **Category**: Accessibility / Reduced Motion
- **Evidence**:
  - `frontend/src/components/marketing/HeroProductFilm.tsx:418` — `<div className="... animate-pulse ..." />`
    - Explanation: The `HeroScrollSection` wraps everything in `<MotionConfig reducedMotion="user">` (line 1219), which correctly handles framer-motion animations. However, `animate-pulse` is a CSS keyframe animation that runs infinitely and completely ignores framer-motion's config. Users who prefer reduced motion will still see the pulsing glow ring.
- **Impact**: WCAG 2.3.3 (Animation from Interactions) — minor violation. The pulse is a subtle glow ring, not a content-bearing animation.
- **Recommendation**: Replace `animate-pulse` with a framer-motion animation, or add `motion-safe:animate-pulse` Tailwind variant so it respects `prefers-reduced-motion`.
- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 8/9 Approve P3 | Dissent: Performance & Cost Alchemist (B): "Continuous CSS animation on a marketing page wastes battery on mobile — should be P2."
- **Chair Rationale**: P3 sustained. The pulse is a single CSS animation on one element. Performance impact is negligible on modern compositors. The accessibility concern is valid but the animation is decorative, not informational.

---

### F-010: Missing `as const` on `ease: 'linear'` in HeroProductFilm
- **Severity**: P3
- **Category**: Types/Conventions
- **Evidence**:
  - `frontend/src/components/marketing/HeroProductFilm.tsx:740` — `ease: 'linear'` without `as const`
    - Explanation: Project convention (CLAUDE.md, MEMORY.md) requires `as const` on all framer-motion transition type/ease properties. Sprint 479 fixed 11 instances across 6 files, but this new instance was introduced in the Sprint 480 rewrite.
- **Impact**: Zero runtime impact. TypeScript type widening from literal to string.
- **Recommendation**: Add `as const`: `ease: 'linear' as const`.
- **Primary Agent**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-011: `StaticFallback` Component Is Dead Code (136 Lines)
- **Severity**: P3
- **Category**: Code Quality
- **Evidence**:
  - `frontend/src/components/marketing/HeroProductFilm.tsx:1075-1211` — `StaticFallback` is defined but never called or exported.
    - Explanation: Sprint 480 replaced the `if (prefersReducedMotion) return <StaticFallback />` pattern with `<MotionConfig reducedMotion="user">`. The fallback component was intentionally kept (comment: "Kept for potential SSR/noscript use") but is currently unreachable.
- **Impact**: 136 lines of dead code in the bundle (~2KB gzipped). Not functionally harmful.
- **Recommendation**: Either export for noscript/SSR use case, or remove. If keeping, add `// eslint-disable-next-line @typescript-eslint/no-unused-vars` to suppress future warnings.
- **Primary Agent**: Modernity & Consistency Curator (E)
- **Vote** (9 members; quorum=6): 7/9 Approve P3 | Dissent: Systems Architect (A): "Keeping the fallback is defensive for future SSR needs." DX & Accessibility Lead (C): "Dead code should be removed; it can be restored from git."

---

### F-012: Non-Palette Color `rgba(189,189,189,0.3)` in Animation
- **Severity**: P3
- **Category**: Design / Theme Compliance
- **Evidence**:
  - `frontend/src/components/marketing/HeroProductFilm.tsx:762` — `rgba(189,189,189,0.3)` (#BDBDBD at 30% opacity)
    - Explanation: This value is used in a framer-motion `animate` prop where Tailwind classes cannot be applied. The color is a generic gray not present in the Oat & Obsidian palette. Closest theme equivalents: `obsidian-300` (#B0B0B0), `oatmeal-500` (#C8C3BA).
- **Impact**: Minor theme deviation in an animation value. Not visible to users as a static color — it's a transitional animation state.
- **Recommendation**: Replace with an obsidian-palette-derived value (e.g., `rgba(176,176,176,0.3)` for obsidian-300 equivalent).
- **Primary Agent**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-013: Hardcoded Pricing in FAQ Answers (Drift Risk)
- **Severity**: P3
- **Category**: Architecture / Consistency
- **Evidence**:
  - `frontend/src/app/(marketing)/pricing/page.tsx:470-523` — FAQ answers contain hardcoded pricing figures: `"Enterprise ($1,000/mo)"`, `"$65/month"`, `"$650/year"`, `"$45/month"`, `"$450/year"`.
    - Explanation: The `tiers` array (lines 364-427) and `SEAT_CONFIGS` (lines 99-118) define pricing as structured data. FAQ answers duplicate these values as prose strings. Any future price change requires updating both locations.
- **Impact**: Drift risk. Currently consistent with backend `price_config.py`, but a price change could create inconsistencies if FAQ is overlooked.
- **Recommendation**: Interpolate pricing values from the `tiers`/`SEAT_CONFIGS` constants into FAQ answer strings.
- **Primary Agent**: Systems Architect (A)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-014: Three Orphaned Commits Without Sprint Numbers
- **Severity**: P3
- **Category**: Process
- **Evidence**:
  - `d44239f` — "Pricing page polish: remove Most Popular badge, unify card styling, add sage accents"
  - `2991cfc` — "Pricing page: introduce oatmeal accents across full color spectrum"
  - `893715f` — "Fix Platform nav link to go to homepage hero instead of #tools anchor"
    - Explanation: 50% of commits since last audit violate the `Sprint X: Description` convention. These modify production code (97 lines total) but are untracked in any sprint.
- **Impact**: Breaks grep-by-sprint audit trail. Makes it harder to correlate code changes with planning artifacts.
- **Recommendation**: Fold under Sprint 481 scope retroactively. Future fix commits should use `Sprint X (fix): Description`.
- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-015: Sprint 480 Review Missing `npm test` Results
- **Severity**: P3
- **Category**: Process
- **Evidence**:
  - `tasks/todo.md:121` — `[x] Build verification: npm run build passes`
    - Explanation: Post-Sprint Checklist requires BOTH `npm run build` AND `npm test`. Sprint 480 records build but not test suite results. The `lessons.md` has a dedicated section "Verification Gate Discipline" stating: "run `npx jest --no-coverage` and record 'npm test: X suites, Y tests passing'." Sprint 480 was a complete rewrite of a major component — test verification is especially important.
- **Impact**: Possible undetected regression from the HeroProductFilm rewrite.
- **Recommendation**: Record `npm test` results retroactively in Sprint 480 review.
- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-016: Pricing Selectors/Toggles Missing Radiogroup ARIA Semantics
- **Severity**: P3
- **Category**: Accessibility
- **Evidence**:
  - `frontend/src/app/(marketing)/pricing/page.tsx:161-193` — `SegmentedSelector` renders as plain `<button>` elements without `role="radiogroup"` / `role="radio"` / `aria-checked`.
  - `frontend/src/app/(marketing)/pricing/page.tsx:206-243` — Monthly/Annual billing toggle uses two `<button>` elements with no `aria-pressed` or radio semantics.
    - Explanation: Both controls exhibit radio-like behavior (single selection) but are announced as independent buttons by screen readers.
- **Impact**: WCAG 4.1.2 — selected state not communicated programmatically. Users relying on assistive technology cannot determine which option is active.
- **Recommendation**: Add `role="radiogroup"` to containers, `role="radio"` + `aria-checked` to buttons, `aria-labelledby` to associate with labels.
- **Primary Agent**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-017: Decorative SVGs Missing `aria-hidden="true"`
- **Severity**: P3
- **Category**: Accessibility
- **Evidence**:
  - `frontend/src/components/marketing/HeroProductFilm.tsx:118` — `CursorIcon` SVG
  - `frontend/src/components/marketing/HeroProductFilm.tsx:1023,1028` — Play/pause button SVGs
  - `frontend/src/app/(marketing)/pricing/page.tsx:739` — Feature checkmark SVG (compare line 562 which correctly has `aria-label="Included"`)
    - Explanation: Decorative SVGs without `aria-hidden="true"` cause screen readers to attempt to announce empty SVG content, producing confusing "group" or "image" announcements.
- **Impact**: Minor screen reader noise. Not a functional barrier.
- **Recommendation**: Add `aria-hidden="true"` to all decorative SVGs.
- **Primary Agent**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

## 4) Council Tensions & Resolution

### Tension 1: Sprint 481 Documentation — P2 vs P3
- **Verification Marshal (I)** and **Data Governance Warden (G)** want P2: "The Directive Protocol is mandatory. Repeated violations indicate systemic non-compliance."
- **Performance & Cost Alchemist (B)** dissents for P3: "It's a pricing page styling change — low risk. Strict process for cosmetic commits adds overhead without proportional safety."
- **Resolution**: P2 sustained (8/9 vote). The commit uses "Sprint 481:" naming, confirming it was treated as a sprint. If it merits a sprint number, it merits documentation.

### Tension 2: `animate-pulse` — P2 vs P3
- **Performance & Cost Alchemist (B)** wants P2: "Infinite CSS animation wastes mobile battery and contradicts the reduced-motion fix Sprint 480 was built to solve."
- **Systems Architect (A)** supports P3: "Single CSS animation, negligible compositor cost. The reduced-motion concern is valid but the pulse is decorative."
- **Resolution**: P3 sustained (8/9 vote). Tailwind's `motion-safe:` variant provides a one-word fix without a full framer-motion rewrite.

### Tension 3: StaticFallback Dead Code — Keep vs Remove
- **Systems Architect (A)**: "Keep — it's a safety net for future SSR/noscript needs."
- **DX & Accessibility Lead (C)**: "Remove — dead code should live in git history, not in the bundle."
- **Resolution**: P3 finding stands. Removal recommended with git blame as the recovery mechanism. If SSR fallback becomes needed, it should be rebuilt to match the current UI (the existing fallback is already stale relative to the Sprint 480 rewrite).

## 5) Discovered Standards → Proposed Codification

- **Existing standards verified** (from codebase):
  - `as const` convention: 99% compliant (1 new miss out of ~40 instances in changed files)
  - Oat & Obsidian palette: 98% compliant (1 rgba value, 11 intentional `bg-white` in simulated panels)
  - Sprint commit message convention: 50% compliant this cycle (regression from ~100% prior)
  - Post-Sprint Checklist: partially followed (build yes, test no)

- **Missing standards that should become policy**:
  - **Simulated UI panel exception**: `bg-white` / `text-gray-*` used intentionally inside mock application screenshots should be documented as an Oat & Obsidian exception (similar to ExportShare zero-storage exception)
  - **FAQ aria-controls pattern**: No boilerplate/component exists for accessible accordion. This is the 2nd FAQ component in the codebase — a shared `<Accordion>` component with built-in ARIA would prevent recurrence
  - **`motion-safe:` prefix**: Should be required whenever raw CSS animations (`animate-*`) are used alongside `MotionConfig reducedMotion`

## 6) Agent Coverage Report

- **Systems Architect (A) — "The Stalwart"**:
  - Touched areas: `backend/.env.example`, `backend/billing/price_config.py`, `backend/routes/audit.py`, `frontend/src/components/marketing/HeroProductFilm.tsx` (hook lifecycle analysis)
  - Top 3 findings contributed: F-002 (primary), F-009 (primary), F-013 (primary)
  - One non-obvious risk flagged: `.env.example` stale Stripe variable names directly block Sprint 447 production cutover — the CEO will configure wrong env vars.

- **Performance & Cost Alchemist (B) — "The Optimizer"**:
  - Touched areas: HeroProductFilm.tsx (animation chain analysis, rAF cleanup), pricing/page.tsx (bundle impact)
  - Top 3 findings contributed: F-009 (dissent-P2), F-011 (voter), F-002 (voter)
  - One non-obvious risk flagged: HeroProductFilm's `useCountAnimation` rAF loop was verified correct — the closure-over-`raf` pattern properly chains cancellation.

- **DX & Accessibility Lead (C) — "The Diplomat"**:
  - Touched areas: pricing/page.tsx (full ARIA audit), HeroProductFilm.tsx (slider semantics), todo.md (process compliance)
  - Top 3 findings contributed: F-003 (primary), F-004 (primary), F-005 (primary), F-006 (primary), F-016 (primary), F-017 (primary)
  - One non-obvious risk flagged: The pricing page has 6 accessibility gaps in a single page — suggests ARIA review was skipped during Sprint 481.

- **Security & Privacy Lead (D) — "Digital Fortress"**:
  - Touched areas: All backend changes, frontend layout.tsx, SECURITY_POLICY.md
  - Top 3 findings contributed: F-007 (primary), F-002 (supporting)
  - One non-obvious risk flagged: Sprint 479 remediation for F-004 was incomplete — only 1 of 4 test methods was migrated to `bindparams()`.

- **Modernity & Consistency Curator (E) — "The Trendsetter"**:
  - Touched areas: HeroProductFilm.tsx (dead code analysis), batch components (convention verification)
  - Top 3 findings contributed: F-011 (primary), F-010 (supporting), F-012 (supporting)
  - One non-obvious risk flagged: The `StaticFallback` component (136 lines) was already stale relative to the Sprint 480 UI changes — if ever resurrected, it would need a full rewrite.

- **Observability & Incident Readiness (F) — "The Detective"**:
  - Touched areas: `.env.example` scheduler documentation, pricing page analytics events
  - Top 3 findings contributed: F-002 (supporting), F-015 (supporting)
  - One non-obvious risk flagged: `trackEvent()` calls in pricing page are fire-and-forget with no error handling — analytics failures are silent (acceptable for non-critical telemetry).

- **Data Governance & Zero-Storage Warden (G) — "The Auditor"**:
  - Touched areas: All data handling paths in changed files
  - Top 3 findings contributed: F-001 (supporting)
  - One non-obvious risk flagged: Zero-Storage compliance fully maintained across this cycle. No new data persistence pathways. ExportShare exception documentation (Sprint 479 F-002) is comprehensive.

- **Type & Contract Purist (H) — "The Pedant"**:
  - Touched areas: All frontend changed files (type safety, convention compliance)
  - Top 3 findings contributed: F-010 (primary), F-012 (primary), F-003 (supporting)
  - One non-obvious risk flagged: Frontend pricing tier definitions are manually synchronized with backend `entitlements.py` — all 14 values match today, but no automated validation exists.

- **Verification Marshal (I) — "The Skeptic"**:
  - Touched areas: `tasks/todo.md` (process compliance), `tasks/lessons.md` (lesson capture), git log (commit convention)
  - Top 3 findings contributed: F-001 (primary), F-014 (primary), F-015 (primary)
  - One non-obvious risk flagged: Sprint 480 lessons are excellent quality (3 entries with root cause + prevention), but Sprint 481 has zero lessons despite being a nontrivial redesign — asymmetric documentation rigor across consecutive sprints.
