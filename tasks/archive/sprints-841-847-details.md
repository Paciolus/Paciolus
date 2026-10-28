# Sprints 841–847 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-27.

---

### Sprint 841: One honest storage statement everywhere
**Status:** COMPLETE 2026-10-24. **Priority:** P1. **Source:** report Part 2 (A1–A26 + Medium list).

- [x] Option B wording in one place — `frontend/src/content/storage-statement.ts` (`UPLOAD_HANDLING`,
      `WHAT_WE_KEEP`, link to `/trust#transparency`) — and applied at every A1–A26 location and the Medium list:
      SEO metadata (root, about, approach, privacy, terms, trust), homepage pillars/evidence band/demo zone/hero,
      About, login/register, all four email templates, TB tool page, WelcomeModal, workspace + marketing footers,
      portfolio, multi-currency and the five JSON-tool sidebars, the four error pages (they claimed "nothing was
      persisted"; now: saved work is unaffected, an in-progress upload was not kept), history, batch panel,
      Privacy §1.3 (now a kept / not-kept / how-long table), §3 (adds the 10-minute preview cache and R2 share
      links), retention table (adds analysis summaries + engagement entries; flagged account names marked kept),
      Terms §5 (rewritten from the facts; counsel reviews wording later), USER_GUIDE, Subprocessor List, DPA §2.3 +
      data table, ZERO_STORAGE_ARCHITECTURE (R2 share-link exception; flagged names), Security / Access Control /
      BCP absolutes.
- [x] USER_GUIDE: "Clear All Activity History" now says it archives, and erasure goes to privacy@paciolus.com.
- [x] Sentry/log claims: Trust page now describes what Sprint 840 S2 strips.
- [x] Guards in `backend/tests/test_storage_claims.py`: (1) 22 retired phrases fail anywhere on the site, app,
      emails, user guide or compliance docs (archive/ excluded); (2) "Zero-Storage" as a claim fails on the site,
      app, emails and user guide (code comments skipped; compliance docs keep the name until Sprint 845).
- [ ] Optional later (CEO): Option C — stop storing `tool_runs.flagged_accounts` etc. so "we keep nothing from your
      uploads" becomes literally true.
- **Also done here because the same lines carried them:** L5 "Audit Intelligence" in the about/approach metadata,
      M6 "ISA and PCAOB alignment" in the approach metadata, "enterprise-grade encryption" in the trust metadata,
      A3's "Eliminate sign errors" → "flags likely sign errors". Sprint 843/844 should skip those.
- **Left for 844:** the account-deletion promises ("immediate and irreversible", "deleted within 30 days") and the
      "anonymized usage statistics" line — they need the deletion feature / the analytics decision, not a rewording.

**Commit SHA:** TBD.

---

### Sprint 842: Billing, pricing and business claims
**Status:** COMPLETE 2026-10-24. **Priority:** P1 (trial/auto-renewal disclosure is the legal-risk item). **Source:** report Part 3.

- [x] Trial: "no credit card required" removed (pricing page, FAQ, homepage hero); checkout shows a "Trial and
      renewal" box before the card is collected — card required, the amount and the date of the first charge
      (today + `TRIAL_DAYS`), then the renewal amount per month/year until cancelled. The non-existent day-8
      read-only flow is replaced by what happens: the card is charged; on failure, emails + retries + 7-day grace,
      then cancellation to Free.
- [x] "Most Popular" removed.
- [x] Refund clause: tier names fixed (Solo, Professional, Enterprise) and "issued manually"; the markdown Terms now
      match the website wording. **The policy itself is still the open CEO decision** (`ceo-actions.md` item 2).
- [x] Row limit "100 MB and 500,000 rows"; billing "monthly from your start date"; invoicing "contact us";
      downgrade FAQ (exports aren't stored by Paciolus).
- [x] One support promise (CEO default): "Email support (reply within 1–2 business days)" on every tier, contact page
      and meta, User Guide. Dedicated account manager, custom SLA, priority support, 8 hr / next-business-day gone.
- [x] Test counts derived: `TOTAL_AUTOMATED_TESTS` in `tool-ledger.ts` (97) feeds EvidenceBand and BottomProof.
      Speed: the 3 s figure is a p95 alert threshold, so the copy now says "seconds"/"usually a few seconds";
      "days now takes seconds" gone; demo "overview of all 18 tools"; "of 12" → "of 18".
- [x] USER_GUIDE seats ($65 up to 20 / $45 up to 100), 100 MB, Professional 500 uploads, ODS "Solo and above";
      Subprocessor List "optionally passcode-protected" (done in 841); "Branded" only on Enterprise; "(.xlsx/.xls)".
- [x] `backend/tests/test_pricing_copy_consistency.py` pins trial days, ledger test total vs registry, upload limits
      vs entitlements, seat configs vs price_config, file limits vs upload_pipeline, User Guide seat prices, and the
      retired billing phrases. Checkout disclosure has its own frontend tests.

**Commit SHA:** TBD.

---

### Sprint 846: Memo PDFs — escape user text before ReportLab parses it (M1)
**Status:** COMPLETE 2026-10-27 (pending CI + merge). **Priority:** P1. **Source:** security review M1 (verified by integrator).

**Defect:** ReportLab `Paragraph(text, style)` parses `text` as markup; account names, descriptions and client
names from uploaded files reached it unescaped, so `<a href=...>` became a live, Paciolus-branded link in an
exported memo, `<font size=0>` hid text and `<img src=...>` failed the export.

**Plan change (why):** the inventory found **1,036 `Paragraph(` calls in 36 modules, ~700 with non-literal text**
(285 f-strings mixing template markup with values). Per-call-site escaping plus an AST guard on arguments, as
originally planned, was not feasible or reviewable. Shipped instead — a single door:
- [x] `shared/safe_paragraph.py`: a `Paragraph` subclass that sanitizes before ReportLab parses. It keeps the
      template vocabulary found by inventory (`b i u strong em strike super sup sub`, `<br/>`, `<font>` with only
      `size` 6–72 and `color` `#rrggbb`/`0xrrggbb`, allowed named + numeric entities) and escapes every other tag
      and stray `< > &`. Unparseable text (e.g. an unbalanced user `<b>`) falls back to fully escaped text, so the
      export completes. `split()`'s `text=None` re-instantiation passes through.
- [x] All 36 modules import `Paragraph` from `shared.safe_paragraph` (mechanical AST-driven swap; import-only diff).
- [x] Full escape (`escape_markup` / `xml_escape`) where values are known user data: `wrap_table_strings` cells
      (inventory: no caller puts markup in table data), `build_memo_header` client name, and the custom headers in
      the accrual, expense-category, flux, population-profile memos and `pdf/orchestrator.py` (entity name).
- [x] `tests/test_safe_paragraph.py` (35 tests): sanitizer unit tests, a guard that fails if any module imports
      ReportLab's `Paragraph` directly, and end-to-end runs of the accrual memo and the TB diagnostic report with
      link/img/font payloads asserting **no `/URI` annotation** in the PDF. Guard + both end-to-end tests fail on the
      pre-fix code and pass after.
- [x] Regression audit: a temporary pytest plugin rendered every paragraph raw and sanitized across the 1,606
      PDF/memo/export tests — **0 differences in visible text** for legitimate templates.
- **Residual (accepted, documented in the module):** user data that is interpolated into templates can still use
  the allowed formatting tags (bold/italic, or `<font color>` to colour text). Links, images, hidden (size<6)
  text and every other tag are neutralised. Wrap a value in `escape_markup()` at the call site when touching it.
- **Note for Sprint 813** (memo skeleton rebuild): keep `shared.safe_paragraph` as the only door; the guard test
  enforces it.

**Verification:** ruff clean; mypy 209 errors (baseline 1,011), none in touched files; full backend suite 9,979 passed (2 Stripe pin tests first failed on a stale local venv — stripe 15.1 vs pinned 16.0.1 — and pass after `pip install stripe==16.0.1`).

**Commit SHA:** `d61bab47` (PR #275).

---

### Sprint 847: Session and account takeover hardening (M3, M4, L3, L4, L14)
**Status:** COMPLETE 2026-10-27 (pending CI + merge). **Priority:** P1. **Source:** security review M3, M4 (both verified), L3, L4, L14.

- [x] **M3: refresh-token reuse detection lasted only about 1 hour.** `cleanup_expired_refresh_tokens` now
  deletes only `expires_at < now`; revoked rows live until expiry (≤ 7 days) so reuse detection still fires.
  Docstring updated. Test: issue → rotate → cleanup → replay old token → "All sessions terminated" and 0 active
  tokens (`test_sprint201_cleanup.py`; three existing cleanup tests updated to the new semantics).
- [x] **M4: email change required no password.** `UserProfileUpdate.current_password` (max 128); required when
  the email actually changes (400 "Enter your current password…"), checked with `verify_password`, logs
  `email_change_failed` on mismatch. The verification swap now, in the same transaction, sets
  `sessions_revoked_at`, revokes all refresh tokens and retires all outstanding reset links.
  - **Deviation from plan:** the swap sets the new `sessions_revoked_at` (L3) rather than `password_changed_at` —
    same effect on live access tokens, without recording a password change that never happened.
  - Frontend: settings/profile shows a "Current Password" field only once the email differs, Save is disabled
    until it is filled, `current_password` is sent, and the API's 400 shows in the existing inline error.
    `ProfileSettingsPage.test.tsx` (3 tests).
- [x] **L4: older password-reset links stayed valid.** `_retire_outstanding_reset_tokens` runs on a new request
  and on a completed reset; the email swap retires them too.
- [x] **L3: access JWT survived "revoke all sessions".** `User.sessions_revoked_at` (migration `b5d2c8e71f30`,
  inspector-guarded, nullable, no backfill); `revoke_all_user_sessions` sets it; `require_current_user` rejects
  tokens whose `iat` (whole seconds, like `pwd_at`) is earlier.
  - **Plain logout deliberately not wired (decision):** the timestamp is user-wide, so setting it on a one-device
    logout would 401 every other device's access token. `apiClient` refreshes silently, but `uploadTransport.ts`
    does not retry on 401, so a phone logout would fail an upload in progress on a laptop. Plain logout already
    clears that device's access cookie and revokes its refresh token. Reopen only with a per-`jti` denylist.
- [x] **L14: impersonation failed after a password change.** `create_impersonation_token(password_changed_at=…)`
  embeds `pwd_at`; `internal_admin.impersonate_customer` passes the target's value.
- **L11 (email enumeration via `PUT /users/me` "Email already in use"): no action.** Accepted risk, because
  registration reveals the same thing. Don't reopen it.

Tests: `tests/test_session_hardening.py` (11) + updates to `test_email_change.py`, `test_sprint201_cleanup.py`.

**Verification:** ruff clean; alembic single head `b5d2c8e71f30`; frontend build passes, 209 suites / 2,075 tests,
`tsc` + eslint clean; full backend suite 9,992 passed.

**Commit SHA:** `6ca55f1b` (stacked on PR #275).

---
