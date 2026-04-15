# Sprints 600–603 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-14.

---

### Sprint 600: Password Reset Complexity Validator
**Status:** COMPLETE
**Source:** Critic — critical auth invariant hole
**File:** `backend/routes/auth_routes.py:403-407`
**Problem:** `ResetPasswordRequest.new_password` had only `min_length=8` — no complexity validator. A user could reset to `password` (8 chars, no upper/digit/special), bypassing the policy enforced at registration (`auth.py:456-461`) and at password-change. Invariant violation.

**Changes:**
- [x] `backend/routes/auth_routes.py` — imported `_check_password_complexity` from `auth`, added `@field_validator("new_password")` on `ResetPasswordRequest` mirroring `PasswordChange`, added `max_length=128` to match other password schemas
- [x] `backend/tests/test_password_reset.py` — new `test_reset_password_weak_password_rejected` asserts weak password returns 422 and leaves the reset token unused (so a follow-up with a compliant password still succeeds)

**Review:**
- Backend: `pytest tests/test_password_reset.py` — 13 passed (up from 12); existing `test_reset_password_short_password` still passes
- Registration, password-change and reset paths now share one complexity policy — `_check_password_complexity` is the single source of truth

---

### Sprint 601: Statistical Sampling Tier Gate Name Alignment
**Status:** COMPLETE
**Source:** Scout — frontend/backend key drift
**File:** `frontend/src/app/tools/statistical-sampling/page.tsx:178`, `frontend/src/components/shared/UpgradeGate.tsx`
**Problem:** Frontend wrapped the statistical sampling tool with `toolName="sampling"`, while the backend entitlement map and command registry use `"statistical_sampling"`. Telemetry and future TIER_TOOLS additions would diverge from backend under the stale key.

**Changes:**
- [x] `frontend/src/app/tools/statistical-sampling/page.tsx` — `UpgradeGate toolName="sampling"` → `"statistical_sampling"`
- [x] `frontend/src/__tests__/UpgradeGate.test.tsx` — new regression test asserts free tier on `statistical_sampling` sees the upgrade CTA instead of the tool UI

**Review:**
- `npm run build` clean; `npx jest UpgradeGate` — 9 passed (up from 8)
- No change to the `UpgradeGate` free-tier logic (`trial_balance` + `flux_analysis` only); the rename aligns telemetry keys with backend entitlements and `commandRegistry.ts`

---

### Sprint 602: Tool Catalog Tier Badge Vocabulary Correction
**Status:** COMPLETE
**Source:** Scout — false-upgrade-pressure UX
**File:** `frontend/src/app/tools/page.tsx`, `frontend/src/components/shared/UnifiedToolbar/toolbarConfig.ts`, `MegaDropdown.tsx`, `UnifiedToolbar.tsx`
**Problem:** Tool catalog + mega-dropdown showed `Solo / Team / Org` badges, but real pricing is `Free / Solo / Professional / Enterprise` and per `backend/shared/entitlements.py` all paid tiers (Solo included) get every tool. Seven of twelve tools carried phantom `Team`/`Org` badges, driving false upgrade pressure on users who already had full access.

**Changes:**
- [x] `toolbarConfig.ts` — removed `TierBadge` type, `tier` field from `ToolItem`, and `TIER_BADGE_STYLES` map
- [x] `MegaDropdown.tsx` — removed tier badge rendering and `TIER_BADGE_STYLES` import
- [x] `UnifiedToolbar.tsx` — removed mobile drawer tier badge rendering and the `TIER_BADGE_STYLES` import
- [x] `app/tools/page.tsx` — removed `TierBadge` type, `tier` field from `ToolDef`, `TIER_STYLES` map, and the badge `<span>` in the card layout

**Review:**
- `npm run build` clean; no test references to `TierBadge` or `TIER_BADGE_STYLES`
- Grep confirms zero `'Team'` / `'Org'` phantom tier references remain under `frontend/src/app/tools/` or `dashboard/`
- Tier gating is still enforced where it actually matters — at `UpgradeGate` (Free tier restricted set) — no functional regression

---

### Sprint 603: Pricing CTA → Register → Checkout Plan Param Wiring
**Status:** COMPLETE
**Source:** Scout — Stripe conversion leak on CTA-driven signups
**File:** `frontend/src/lib/authFlowState.ts`, `frontend/src/app/(auth)/register/page.tsx`, `frontend/src/app/(auth)/verify-email/page.tsx`
**Problem:** Pricing CTAs send `/register?plan=solo&interval=monthly`, but the register page never read `useSearchParams` — the param was silently dropped. Users finished signup on Free tier and had to manually hunt for Settings → Billing. CTA-driven paid signups converted at zero.

**Changes:**
- [x] `lib/authFlowState.ts` — new `setPendingPlanSelection` / `consumePendingPlanSelection` / `peekPendingPlanSelection` backed by `sessionStorage` (survives the email-link verification reload in the same tab). Validates allowed plan/interval enum values before persisting or reading.
- [x] `app/(auth)/register/page.tsx` — wraps the page in `<Suspense>`, parses `plan` / `interval` from `useSearchParams()`, calls `setPendingPlanSelection` on successful registration, and — when an already-authenticated user hits the CTA — short-circuits the `/` redirect straight into `/checkout?plan=…&interval=…`.
- [x] `app/(auth)/verify-email/page.tsx` — on successful verification, calls `consumePendingPlanSelection`; if a selection was queued, auto-redirects to `/checkout?plan=…&interval=…` instead of `/`.

**Review:**
- `npm run build` clean — `/register`, `/verify-email`, `/checkout` all compile as dynamic routes
- Same-tab flow (Pricing CTA → Register → email link in the same tab) resumes at `/checkout` with correct plan/interval
- New tab verification edge case falls back to the existing `/` redirect, matching the current sessionless behaviour — documented inline in `authFlowState.ts`
- Uses the existing `authFlowState` module to keep auth-flow handoffs in one place

---

---
