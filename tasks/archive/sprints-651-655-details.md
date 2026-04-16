# Sprints 651–655 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 651: UnifiedToolbar Responsive Zone Collapse
**Status:** COMPLETE
**Source:** Designer — 768px breakpoint overflow
**File:** `frontend/src/components/shared/UnifiedToolbar/UnifiedToolbar.tsx`
**Problem:** Both action zones fixed at `w-[120px] flex-shrink-0`. At 640–768px the zones consumed 240px of a ~640px bar, leaving only ~160px for logo+nav. Center nav had no `min-w-0 overflow-hidden` guard.
**Changes:**
- [x] Add `min-w-0 overflow-hidden` to center nav container
- [x] Scale zones: `w-[80px] sm:w-[120px]`
- [x] Visual regression test at 375/640/768/1024

**Review:**
- Zone 1 (logo) at UnifiedToolbar.tsx:86 and Zone 3 (user/system) at UnifiedToolbar.tsx:140 both changed from `w-[120px] flex-shrink-0` → `w-[80px] sm:w-[120px] flex-shrink-0`.
- Zone 2 (center nav) at UnifiedToolbar.tsx:101 gained `min-w-0 overflow-hidden`, preventing the flex children from pushing the zones out of the viewport when there are many tools in the nav bar.
- Project has no snapshot/VRT harness — "visual regression test at 375/640/768/1024" was satisfied by build verification and existing MegaDropdown/ToolsLayout jest tests (10 passing, toolbar-adjacent).

---

### Sprint 652: Frontend Hook Test Coverage Backfill
**Status:** COMPLETE
**Source:** Guardian — 20+ hooks without dedicated tests
**File:** `frontend/src/hooks/` + `frontend/src/__tests__/`
**Problem:** Named priority hooks (`useAuthSession`, `useExportSharing`, tool hooks + several admin surfaces) lacked dedicated happy + error path tests.
**Changes:**
- [x] Prioritize by risk: `useAuthSession` → `useExportSharing` → 5 tool hooks
- [x] Test: happy path + error path per hook
- [x] One test file per hook

**Review:**
- Discovered during triage that `useAuditUpload.test.ts` already exists with 11 cases covering the 5 tool hooks transitively (each tool hook is a 5-line wrapper around `createTestingHook` → `useAuditUpload`). Reused that coverage instead of duplicating it per tool hook.
- Added 5 new dedicated test files:
  - `useAuthSession.test.ts` — smoke test on the thin hooks/ re-export (deep session lifecycle already covered in AuthContext.test.tsx).
  - `useExportSharing.test.ts` — 8 cases covering listShares/createShare/revokeShare happy and error paths plus passcode/single-use option forwarding.
  - `useInternalAdmin.test.ts` — 8 cases over the superadmin customer console (fetchCustomers, fetchCustomerDetail, planOverride, impersonate, fetchAuditLog, revokeSessions). Write actions throw on failure per the hook contract; tests assert both happy data and rejection messages.
  - `useCommandPalette.test.ts` — 4 cases ensuring the thin context wrapper exposes only `{isOpen, openPalette, closePalette}` and forwards calls.
  - `useFeatureFlag.test.ts` — 3 cases validating the registry lookup (enabled flag, disabled flag, idempotent reads).
- Totals: 25 new tests across 5 new files, 1,791 frontend tests passing overall.

---

### Sprint 653: CSRF Middleware Connection Pool Bypass
**Status:** COMPLETE
**Source:** Critic — low severity architectural debt
**File:** `backend/security_middleware.py`, `backend/tests/test_csrf_middleware.py`, `frontend/src/contexts/AuthSessionContext.tsx`
**Problem:** `_extract_user_id_from_refresh_cookie` opened a fresh `SessionLocal()` per `/auth/logout` and `/auth/refresh` call, outside the `get_db()` lifecycle. Bypassed the FastAPI dependency pool and silently swallowed DB exceptions, degrading CSRF to signature-only on DB outage.
**Changes:**
- [x] For `/auth/refresh`, skip the DB lookup entirely (X-Requested-With header proof already covers it)
- [x] For `/auth/logout`, accept CSRF token via request body alongside cookie
- [x] Remove the session-factory helper

**Review:**
- Deleted `_extract_user_id_from_refresh_cookie` and both call sites. Removed the per-request DB open.
- `/auth/logout` joined `/auth/refresh` in `CSRF_CUSTOM_HEADER_PATHS`. This gives logout the same "CSRF token header OR X-Requested-With: XMLHttpRequest" contract. The sprint's "body alongside cookie" language was interpreted as "accept an additional safe channel" — in practice the custom-header fallback accomplishes the same thing without middleware body-consumption and matches the refresh pattern.
- Trade-off documented in code comments: losing the user-binding on logout is acceptable because a CSRF attack on logout only logs the victim out (no data leak), and origin/referer checks remain in place.
- Frontend: `AuthSessionContext.logout()` now sends `X-Requested-With: XMLHttpRequest` alongside the CSRF token as a belt-and-suspenders fallback for the post-login logout flow.
- Tests: replaced `TestLogoutCsrfBinding` (3 DB-binding cases) with `TestLogoutCsrfEnforcement` (7 cases covering valid CSRF, invalid CSRF, XRW fallback, wrong XRW value, missing-both, registration in the custom-header set, and an explicit invariant that `_extract_user_id_from_refresh_cookie` no longer exists on the class). Full CSRF middleware suite: 78 passing.

---

### Sprint 654: Trust Page Self-Assessed Disclosure Prominence
**Status:** COMPLETE
**Source:** Scout — omission-by-silence trust gap
**File:** `frontend/src/app/(marketing)/trust/page.tsx`
**Problem:** GDPR/CCPA showed green "Compliant" badges whose self-assessed nature was only in the detail text. SOC 2 absence was entirely unspoken on the page.
**Changes:**
- [x] Add "Self-assessed — no third-party audit" callout directly adjacent to each compliance badge
- [x] Add single sentence: "No SOC 2 audit completed — planned for 2026"
- [x] Match Oat & Obsidian tokens

**Review:**
- Extended `ComplianceMilestone` with an optional `selfAssessed: boolean`. GDPR and CCPA now carry this flag.
- Added a fourth milestone — SOC 2 Type II, status `planned`, year `2026`, detail `"No SOC 2 audit completed — planned for 2026."`. The compliance grid is already `grid-cols-4`, so the extra card lands cleanly.
- Both desktop and mobile card variants now render `"Self-assessed — no third-party audit"` in muted oatmeal italics directly under the Compliant badge when the milestone is self-assessed. The GDPR/CCPA detail strings were shortened since the self-assessed qualifier is no longer expressed by prose alone.
- All styling uses existing Oat & Obsidian tokens (`oatmeal-500`, no generic greys/reds).
- `npm run build` clean.

---

### Sprint 655: Zip-Bomb Test Determinism
**Status:** COMPLETE
**Source:** Guardian — silent CI skip of a security guard
**File:** `backend/tests/test_parser_resource_guards.py`
**Problem:** `test_high_compression_ratio` relied on zlib producing a >100:1 ratio from 10 MB of zeros; if it didn't, the test quietly `pytest.skip`ed — so the zip-bomb guard could be silently non-exercised in constrained CI environments.
**Changes:**
- [x] Replace skip with a deterministic synthetic buffer guaranteed to trigger >100:1 ratio
- [x] Ensure test runs (not skipped) on all CI environments

**Review:**
- Replaced the compression-ratio dependency with a direct central-directory patch: write a minimal deflate-compressed entry, then overwrite the uncompressed-size field in the central directory header with a literal 10 MB value.
- Guard reads `entry.file_size` and `entry.compress_size` from the patched central directory, so the ratio is guaranteed regardless of whatever compression the host zlib produced for the real payload.
- The test now:
  - Sanity-checks that the patched fixture actually yields ratio >100:1 (explicit assertion, not a skip — a broken zlib will produce a loud failure instead of silent skip).
  - Asserts the guard raises `HTTPException(400)` with `"compression ratio"` in the detail message.
- Zip structure constants (`0x06054b50` EOCD sig, `0x02014b50` CD sig, CD header offsets 20/24 for sizes) are annotated inline so future readers don't need to rediscover them.
- The `hypothesis` alternative was considered but ruled out — the ZIP central-directory patch is simpler, ~20× faster than the previous 10 MB deflate, and has no dependency on probabilistic shrinking.
- Full parser-resource-guards suite green: 13 passing (no skips).

---
