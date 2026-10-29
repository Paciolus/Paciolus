# Sprints 813 and 848 — archived 2026-10-28

Both merged in `1435b0e4` (2026-10-28). Archived by the 2026-10-28 action plan, Phase 5.

### Sprint 848: Authorization gaps (M8, M9, L1, L5)
**Status:** COMPLETE 2026-10-27 — merged + deployed 2026-10-28 in `1435b0e4` (PR #281, chain-merged via #286). **Priority:** P1. **Source:** security review M8 (verified), M9, L1 (verified), L5 (verified).

- [x] **M8: any org member could change firm branding.** `_get_branding(..., write=True)` also requires the
  owner or admin role (same rule and 403 as `organization_policy.require_admin`, checked on the membership row
  the helper already loads, so no second query). Used by `PUT /branding/`, `POST /branding/logo` and
  `DELETE /branding/logo`; `GET` stays open to every member.
- [x] **M9: an impersonation session could open the Stripe billing portal.** `require_current_user` sets
  `request.state.impersonation`; new `auth.reject_impersonation` dependency (403, `IMPERSONATION_READ_ONLY`)
  guards `GET /billing/portal-session`. Checkout is a POST, already blocked by the mutating-method guard.
  Grep of all 82 GET routes for Stripe URLs, share tokens, download tokens and passcodes: none other —
  `ExportShareResponse` and `OrganizationInviteResponse` carry no tokens, and `GET /auth/csrf` only enables
  writes, which impersonation cannot make.
- [x] **L1: `POST /activity/tool-log` stored an unvalidated `engagement_id`.** Resolved through
  `EngagementManager.get_engagement` as `tool_run_recorder` does; unresolved → stored as `None`, still 201.
- [x] **L5: admin billing actions could hit the wrong customer.** Fallback kept (solo customers). New
  `_require_target_user` in `routes/internal_admin.py` (404 unknown, 409 mismatch) runs before plan override,
  extend trial, credit, refund, force cancel **and revoke sessions** (same fallback, so it gets the same
  guard; it now takes a `RevokeSessionsRequest` body). Impersonation reuses the helper. Every request schema
  requires `target_user_id`; the admin hook and customer page send `d.user_id`.

Tests: `tests/test_authorization_gaps.py` (23; 16 fail on the pre-fix routes — including the FK 500 on an
unknown engagement — and pass after); `test_internal_admin.py` requests now name their target;
`useInternalAdmin.test.ts` +1.

**Verification:** ruff clean; frontend `tsc` + eslint clean, `useInternalAdmin` 10/10; full backend suite 9,990 passed (before stacking on 847–852); after stacking, the auth, admin, branding, impersonation, 847 and 849 test files pass (117). The branding test uploads a real 4×4 PNG, because Sprint 852's logo-dimension check opens the image with Pillow. OpenAPI snapshot regenerated (`target_user_id`, `RevokeSessionsRequest`).

**Commit SHA:** `5a9df962` (stacked on PR #280).

---

### Sprint 813: Memo PDFs — missing footers, ignored branding, and the hand-built skeleton behind both
**Status:** COMPLETE 2026-10-27 — merged + deployed 2026-10-28 in `1435b0e4` (PR #285, chain-merged via #286) — customer-facing defects (1, 2, 6, 8, 10)
and item 7 merged earlier; structural items 3, 4, 5, 9 done 2026-10-27 with byte-independent
rendering equivalence on every memo. Remaining work is listed under "Left open" below.
**Priority:** **P1** — items 1–2 ship defective PDFs today.
**Source:** Code health review 2026-10-23, memos/PDF pass.

Only 6 of 20 memo modules use `shared/memo_template.generate_testing_memo`; the other 14 build
page setup, cover, footer and `doc.build` by hand. Both defects below come from that.

**Scope:**
1. [x] **Footer missing after page 1** (S). `currency_memo_generator.py:514`,
   `expense_category_memo.py:863`, `flux_expectations_memo.py:515`,
   `population_profile_memo.py:765`, `sampling_memo_generator.py:1276` pass only `onFirstPage`.
   The cover always ends in a page break, so **every** content page lacks the page number and
   disclaimer. Confirmed on committed `sample-reports/` 13, 14, 15, 17, 18, 20. Add `onLaterPages`.
2. [x] **Enterprise branding ignored by 11 memos** although `routes/export_memos.py:162` sets
   the ContextVar for all: bank rec, currency, multi-period, preflight, both sampling,
   three-way match, accrual, expense, flux, population profile. Reproduced with
   `apply_pdf_branding(footer_text=...)`: JE memo carries it, preflight does not.
3. [x] *(Done 2026-10-27: all 14 + `generate_testing_memo` on `memo_base.render_memo`; guard test.)*
   Extract `render_memo(title, ref_prefix, body_builder, *, running_header=None, margins=...)`
   in `shared/memo_base.py`; route the 14 hand-built memos **and** `generate_testing_memo`
   through it. Keep each memo's current margins as parameters (they drift 0.75in/1.0in today)
   so output does not move. ~500–700 lines; closes 1 and 2 permanently.
4. [x] *(Done 2026-10-27: 20 true copies replaced; ~20 near-copies are genuine variants, left inline.)*
   `ledger_table_style()` is copied inline 47× — add `font_size`/`extra` params, replace copies.
5. [x] *(Done 2026-10-27: 10 memos + `build_scope_section`.)* `source_line(...)` helper for the 6-line Source block repeated in 10 memos; keep
   "Source File" vs "Source" as a parameter (no wording change).
6. [x] `tests/test_memo_boundary_phrasing.py:101` matches only `*_memo_generator.py`, so
   accrual/expense/flux/population-profile `*_memo.py` are never scanned. Widen the glob.
7. [x] *(Done 2026-10-23: memo/report producers scanned; the scanner now reads the `AU-C § 330`
   spelling, which surfaced AU-C 320 and 330 too; 10 codes registered, every citation checked
   accurate first. The anomaly summary's table keeps its literal titles — reading the registry's
   would change rendered wording — but every code in it is now guarded.)*
   `tests/test_citation_consistency.py` never scans backend PDF producers. Add them; register
   the unregistered codes cited in customer PDFs (AS 1305, AS 1105, AS 2810, AU-C 320/330/520/570,
   IFRS 9, ASC 275, ASC 450, 14 ASC codes in the FASB YAML). `anomaly_summary_generator.py:109-115`
   hard-codes its list — read the registry. No wording changes.
8. [x] Engagement ZIP (`engagements_exports.py` ~`:85-110`) ships the anomaly summary **unbranded**
   while the standalone route brands it; also passes neither engagement nor client, so access
   check + client lookup run twice.
9. [x] *(Done 2026-10-27; shim kept for 7 test files.)* Small: cache `create_memo_styles()`; module-constant fonts/fills in `excel_generator.py:327,401`;
   prefix arg on `generate_reference_number` (replaces 21 `.replace("PAC-", ...)`);
   point the ~30 `pdf_generator` shim importers at `pdf` directly.
10. [x] `generate_sample_reports.py:4076-~4325` `gen_anomaly_summary` re-implements the production
   PDF with a **drifted** disclaimer. Call `AnomalySummaryGenerator._build_story(...)` instead (~230 lines).

**Delivered 2026-10-23 (items 1, 2, 6, 8, 10):**
- `report_chrome.current_page_footer()` resolves the route-scoped `PDFBrandingContext` and returns
  the branded or default callback; all 11 hand-built memos now pass it as **both** `onFirstPage`
  and `onLaterPages`. `build_cover_page` reads the branded logo from the same context when the
  caller passes none, so those memos get the firm's cover logo too.
- **Measured before/after** by rendering all 21 sample reports under Enterprise branding and
  reading each page's text back: before, 6 PDFs had no page number on any content page and 12
  ignored the firm's header/footer; after, 0 and 0.
- `tests/test_memo_page_chrome.py` makes that measurement permanent. It checks **rendered output**,
  not source, so it holds whether or not item 3's `render_memo` extraction ever lands — which
  lowers item 3 from "closes 1 and 2 permanently" to a pure cleanup. 5 of its 6 tests fail on the
  pre-fix code.
- Item 10: `AnomalySummaryGenerator` split into `generate_pdf` (access check + client lookup) →
  `generate_pdf_for_engagement` (queries) → module-level `render_anomaly_summary_pdf` (no DB).
  The sample script now builds `SimpleNamespace` engagement/run/follow-up rows and renders through
  production — ~230 hand-copied lines deleted. The sample grew 5 → 9 pages: the copy had been
  omitting most of what customers actually receive.
- Item 8: the package route wraps `generate_zip` in `apply_pdf_branding`, and the exporter hands
  its already-verified engagement to `generate_pdf_for_engagement` (no second access check or
  client query). Route-level test proves the scope is active during the build.
- Item 6: glob widened to `*_memo.py`; 5 more files scanned, all clean.
- `sample-reports/` regenerated so the committed samples no longer show the defects.

**Two more defects found while verifying, both fixed:**
- **`MemoTitle` overprinted by its own subtitle** in accrual, expense, flux and population-profile
  (24pt font on ReportLab's default 12pt leading). Visible in the committed sample before this
  change. `leading=29`; a test now fails any memo style whose leading is below its font size.
- **Branded header struck through by the gold rule** on the accrual memo, which draws its own
  page header at the same 0.5in line. Branded header moved to 0.35in for all memos.

**Delivered 2026-10-27 (items 3, 4, 5, 9 — branch `sprint-813-memo-skeleton`, on top of Sprint 846):**
- [x] **Equivalence harness first.** `tests/test_memo_render_equivalence.py` renders all 24 memo/report
  PDFs (21 samples + engagement dashboard, analytical expectations, SUM schedule), unbranded and
  under Enterprise branding (header, footer, logo), clock frozen; pins page count, media box,
  per-page text, positioned text runs, text bbox and content-stream digest (byte-independent),
  plus the Excel workpaper's cell styles. Recorded on the pre-refactor code; green after every item;
  stable across hash seeds.
- [x] Item 5: `memo_base.source_line(title, filename, *, filename_label=, always=)`.
- [x] Item 4: `ledger_table_style(*, font_size=, extra=)`. A copy was converted only when moving its
  extra commands after the ledger block cannot change the drawing (no extra precedes a ledger
  command on the same attribute).
- [x] Item 9: `create_memo_styles()` cached (fresh dict per call); Excel per-row fill/border/fonts are
  module constants; `generate_reference_number(prefix)` replaces 17 `.replace("PAC-", ...)`;
  29 production modules import `pdf` directly.
- [x] Item 3: `render_memo(title, ref_prefix, body_builder, *, cover=, running_header=, margins=,
  branding=, page_footer=)`; per-memo margins kept (`MEMO_MARGINS` / `TESTING_MEMO_MARGINS`).
  Analytical expectations, SUM and anomaly summary build their own cover (banner precedes it) and
  take `render_memo`'s reference. `current_page_footer()` removed (no callers). Guard test fails any
  memo module that builds its own `SimpleDocTemplate`.
- [x] Found on the way: the anomaly summary's "Tools with Clean Results" list printed in set order
  (varied per process) — now catalog order.

**Left open (and why):**
- Engagement dashboard still uses the unbranded `draw_page_footer` (kept via `page_footer=` so output
  does not change; no route serves it today). Making it brand-aware is a one-line product call.
- ~20 TableStyle near-copies of the ledger style (4pt padding, no body font, no flush-left padding,
  MIDDLE valign) stay inline — they are variants, not copies.
- TB diagnostic / financial statements (`pdf/orchestrator.py`) and the loan-amortization PDF still
  own their page setup — reports, not memos, with different chrome.
- `pdf_generator.py` shim stays for the 7 test files that import it.

**Verification:** full backend suite 10,052 passed / 1 failed — `test_alembic_head_matches_base_metadata_foreign_keys`
hit its 180s subprocess timeout under full-suite load; the file passes alone (5/5). Equivalence harness
50/50, memo/report/export test set 1,705 passed; ruff check clean.

**Commit SHA:** 91753ba2 (PR #202, items 1/2/6/8/10); 064c5914 (PR #212, item 7); 4f38ecd5 (harness),
cb65fb58 (item 5), 5f42d192 (item 4), a2b5f373 (item 9), 2ebcaf84 (item 3) — branch `sprint-813-memo-skeleton`.
