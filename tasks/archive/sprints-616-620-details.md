# Sprints 616–620 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-15.

---

### Sprint 616: Workpaper Generator Ownership Check
**Status:** COMPLETE
**Source:** Guardian — cross-user leak if data integrity drifts
**File:** `backend/workpaper_index_generator.py:95-96`
**Problem:** Fetches Client by engagement.client_id without `Client.user_id == current_user.id` filter. Engagement access is checked upstream, but if an engagement drifts to reference a client from another user (data integrity failure scenario), client name leaks. Compare `routes/diagnostics.py:210` which correctly filters.
**Changes:**
- [x] Added `Client.user_id == user_id` filter + explicit `ValueError("Client not found or access denied")` if null
- [x] Regression test: `TestWorkpaperClientOwnershipGuard::test_foreign_client_raises_error` — 1 test, green

---

### Sprint 617: MappingToolbar Modal Confirmation
**Status:** COMPLETE
**Source:** Executor + Designer — hostile UX pattern
**File:** `frontend/src/components/mapping/MappingToolbar.tsx:69`
**Problem:** `window.confirm()` is a sync blocking call. Breaks PWA/iframe context, fails Oat & Obsidian design system, popup-blocker-suppressed in some browsers.
**Changes:**
- [x] Replaced `window.confirm()` with state-based `showClearConfirm` modal using the same pattern as `deleteConfirmClient` in `portfolio/page.tsx`
- [x] Modal uses Oat & Obsidian tokens: `clay-*` for warning, `font-serif` header, `font-mono` count, `obsidian-900/50` backdrop
- [x] Frontend build passes

---

### Sprint 618: Dashboard Error State + Toasts
**Status:** COMPLETE
**Source:** Executor — silent data failures
**File:** `frontend/src/app/dashboard/page.tsx:142, 147, 152`
**Problem:** Three `.catch(() => {})` swallow dashboard stats, activity feed, and user preferences errors. When APIs fail after a backend deploy, user sees a blank dashboard with zero feedback — no error state, no retry, no toast.
**Changes:**
- [x] All 3 `.catch(() => {})` replaced with `toastError()` calls + `statsError`/`activityError` state
- [x] Stats section: clay-colored error banner with "Retry" button (`retryStats`)
- [x] Activity section: centered error card with "Retry" button (`retryActivity`)
- [x] Frontend build passes

---

### Sprint 619: Orphan Billing Router Cleanup
**Status:** COMPLETE
**Source:** Executor — dead code confusion
**File:** `backend/routes/billing_checkout.py`, `backend/routes/billing_analytics.py`, `backend/routes/billing_webhooks.py`
**Problem:** None are imported in `routes/__init__.py`. Define duplicate `/billing/` prefix routers cloning live `billing.py` endpoints. Never served, but waste maintenance attention and invite merge confusion.
**Changes:**
- [x] Deleted all three files (2,837 + 10,138 + 4,985 bytes of dead code)
- [x] Grep confirmed zero import references in backend

---

### Sprint 620: Hero Headline Clarity + Trust Micro-Copy
**Status:** COMPLETE
**Source:** Scout — 5-second test failure
**File:** `frontend/src/components/marketing/hero/HeroProductFilm.tsx:83-147`
**Problem:** "The Workpapers Write Themselves" is clever but doesn't answer "what do I drop in and what do I get back?" in 5 seconds. "No credit card required" only appears in pricing page FAQ, not near any landing-page CTA.
**Changes:**
- [x] Replaced generic subheadline with action-oriented "Drop your trial balance. Get ISA/PCAOB-methodology diagnostics and workpapers in seconds."
- [x] Added secondary line: "Professional-grade analysis across 12 testing tools. Zero data retained."
- [x] Added "No credit card required" micro-copy directly under CTA buttons
- [x] Frontend build passes

---

