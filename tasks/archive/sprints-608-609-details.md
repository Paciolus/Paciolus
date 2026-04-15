# Sprints 608–609 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-15.

---

### Sprint 608: Telemetry Beacon Endpoint
**Status:** COMPLETE
**Source:** Executor — silent prod 404
**File:** `frontend/src/app/api/telemetry/route.ts` (new)
**Problem:** `utils/telemetry.ts:59` fires `navigator.sendBeacon('/api/telemetry', …)` when `NEXT_PUBLIC_ANALYTICS_WRITE_KEY` is set, but no Next.js route handler existed under `frontend/src/app/api/`. Every pricing page view and CTA click 404'd silently in production.

**Decision:** Keep the beacon call and create a stub route handler. The beacon is already in production and telemetry is valuable; removing the call would make future analytics wiring harder. A validating stub is the least-risk option.

**Changes:**
- [x] `frontend/src/app/api/telemetry/route.ts` (new) — POST handler runs in the Node.js runtime, `force-dynamic`. Validates payload: `event` must be a non-empty string ≤64 chars, `timestamp` must be a string, `properties` must be a ≤20-key object of primitive values. Returns 413 on oversize (>2 KB), 400 on malformed, 405 on GET, 200 on accepted payloads. Does not forward anywhere yet — hook real analytics in when ready.

**Review:**
- `npm run build` — route shows up as `ƒ /api/telemetry` dynamic handler alongside the other server-rendered routes; no TypeScript errors
- Zero-Storage: no financial data is ever accepted through this endpoint — only the fixed event-name vocabulary from `utils/telemetry.ts` (billing, hero, command-palette) and small primitive property maps

---

### Sprint 609: global-error.tsx A11y + Token Remediation
**Status:** COMPLETE
**Source:** Designer — crash-screen a11y + brand hex hygiene
**File:** `frontend/src/app/global-error.tsx`
**Problem:** The top-level Next.js error boundary hardcoded raw hex values (`#9e9e9e`, `#757575`, `#E99A9B`, `#4A7C59`, `#BC4749`, `#EBE9E4`) inline. Some were incidentally in the Oat & Obsidian palette, but `#9e9e9e` was a wandering off-brand grey, and the buttons had no `aria-label` and no visible focus outline. Critically, the error boundary replaces the root layout, so CSS custom properties defined in `globals.css` do not resolve here — `var(--text-tertiary)` fixes do not work, which is why the original author reached for inline hex in the first place.

**Changes:**
- [x] Added a local `BRAND_TOKENS` constant at the top of the file — named entries for every obsidian / oatmeal / clay / sage value the component uses. Acts as a ledger so future readers cannot accidentally introduce a random grey again. Docstring explains why CSS variables are not an option in `global-error.tsx` specifically.
- [x] Replaced every inline hex literal with a `BRAND_TOKENS.*` reference, including the "muted body text" value which was previously `#9e9e9e` (obsidian-300) and is now `oatmealMuted` (`#B5AD9F`, oatmeal-500 — the canonical "secondary body text on dark surface").
- [x] Both buttons gained `type="button"`, `aria-label` (Try Again → "Retry the last action that failed"; Reload Paciolus → "Reload the Paciolus application"), and an explicit `onFocus`/`onBlur` pair that draws a 2px `oatmealBase` outline with 2px offset on keyboard focus.
- [x] Added `aria-hidden="true"` to the decorative warning SVG so screen readers skip straight to the heading.

**Review:**
- `npm run build` clean — the error boundary still compiles standalone (no CSS-var dependencies since this page runs when the root layout itself is broken)
- Keyboard-only: tabbing now produces a visible focus ring on both actions, matching the rest of the Obsidian Vault aesthetic
- A11y audit items that the sprint flagged (aria-label, focus outline, brand palette) are closed; the "use `var(--text-tertiary)` etc." suggestion was intentionally rejected — explained in a code comment inside the file

---
