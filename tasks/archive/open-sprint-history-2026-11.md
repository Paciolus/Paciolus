# Full history of sprints still open on 2026-11-15

Moved verbatim out of `tasks/todo.md` on 2026-11-15; each sprint keeps a stub there (status + every unchecked item). Update the stub, not this file.

### Sprint 856: First run, public-page accessibility, and one look in a browser
**Status:** PENDING. **Priority:** P1 (Phase 1 — before the first Sprint 781 CPA session). **Source:** 2026-10-28 council (Designer, Accounting Expert, Executor).

- [x] **WelcomeModal step 1** (`components/shared/WelcomeModal.tsx:32`) still says "Upload a Trial Balance", and #235
      does not change it — 14 of 18 tools take no TB. Point it at the tool picker. (Steps 2–3 copy is in #235; verify after merge.)
      *Done: "Choose a Tool" → `/tools`. Three-way merge with `origin/sprint-843-positioning` is conflict-free (file + test).
      Still open: step 3's "Get Started" CTA also routes to `/tools/trial-balance` — left for #235, which owns step 3.*
- [x] WelcomeModal: Escape closes it, focus trap, initial focus — match the five other modals. Fix the header comment
      "Shows once per user" (completion is in localStorage — once per device). *Done via shared `useFocusTrap`.*
- [x] Skip-to-content link in `MarketingNav` (public pages declare `#main-content` but nothing links to it; only
      `UnifiedToolbar.tsx:82` has one). *Done. 6 of 10 marketing pages (about, approach, contact, privacy, terms, trust)
      and the `(marketing)/error.tsx` boundary had no `#main-content` — added; a Jest invariant now walks the route group.
      Not covered: `/login`, `/register` (no MarketingNav, no skip link).*
- [x] **Browser pass:** home, pricing, workspace and two tool result tables at 375px and 1440px. Record findings; fix
      anything a CPA would hit (no source-only review has ever looked at these rendered — `tasks/todo.md:267`).
      *Done 2026-10-28 (Playwright, `next dev --webpack` + local backend/SQLite, Professional test user): home, pricing,
      about, trust, terms, contact, tools, login, dashboard, portfolio, TB Diagnostics and AP Testing results. No page has
      horizontal overflow at either width. **Fixed:** (a) home hero H1 was unreachable above the fold at 375px
      (`max-h-[900px]` + `justify-center` pushed it above y=0) → `lg:max-h-[900px]`; (b) TB results printed
      `$1,412,330.8` and the ratio footer printed `Assets: $1420425.07` (`toLocaleString` on numbers / on the API's
      Decimal *strings*) → `formatCurrency` in `AnomalyCard` + `KeyMetricsSection`; (c) TB anomaly account names
      truncated to ~12 chars at 375px → wrap; (d) pre-flight Column Detection cards overlapped label and % at 375px →
      single column below `sm`; (e) pricing seat calculator label touched the amount. **Open (larger / copy):**
      [ ] re-uploading the same TB within 5 min shows the raw API text "re-submit with force_resubmit=true" and offers no
      button (`routes/audit_pipeline.py:128`); [ ] TB "Material Risks (9)" lists 5 "coverage observation, not an anomaly"
      rows with clay warning icons and a "Material" label; [ ] "TOP FINDINGS" on AP results, "fraud indicators" in the AP
      subtitle, "SEE THE FINDINGS" in the home hero scrubber — guardrail wording; [ ] `/tools` header says "24 tools across
      3 categories" vs 18 everywhere else; [ ] `/engagements` redirected to `/portfolio` for a fresh Professional user —
      confirm intended; [ ] hydration-mismatch console warning on authed pages (dev).*
- [x] **793b tax banner.** Non-dismissible disclaimer banner (existing pattern, clay/oatmeal tokens): "Statutory figures
      current through tax year 2025 — verify before relying". Same line in each tool's PDF and Excel exports — the export
      is what a CPA files. **First verify per tool** which tools are year-keyed to 2025: W-2 already refuses unknown years
      (`w2_reconciliation_engine.py:21,75-80`); check 1099, Book-to-Tax and Depreciation before printing the claim.
      **Hard date:** if no practitioner has confirmed the 2026 figures by **2026-12-15**, the banner becomes a disable.
      **Done:** verified only W-2 (2025 table, other years refused) and 1099 (2025 + secondary-source 2026 tables) apply year-keyed figures — Book-to-Tax, Depreciation and Loan apply none — so each of those two gets its own accurate banner (`backend/tax_figures_status.py` ↔ `frontend/src/content/tax-figures.ts`) on the page and as the first line of its CSV export (their only export; no PDF/Excel exists), and `tests/test_tax_figures_status.py` fails after 2026-12-15 unless a practitioner confirmation is recorded per tool.

**Verification (items 1–4):** `npx tsc --noEmit` clean; `npm run lint` clean; full Jest 209 suites / 2,083 tests green
(+4 WelcomeModal: step-1 copy, Escape, initial focus, Tab trap; +2 MarketingNav: skip link first, `#main-content`
invariant; +1 KeyMetricsSection: Decimal-string totals). `npm run build` NOT run in the worktree (Turbopack cannot build
through the node_modules junction) — run from the main checkout before merge. Screenshots in session scratch only.

**Landing (2026-11-14):** re-applied onto `main` after #254 in the batch branch `batch-854-856-857-858-778b` (#288–#292
in one CI run). Item 5 conflicted only in `tests/test_w2_reconciliation_routes.py` — Sprint 855's
`TestSprint846Form941AndW3` and this sprint's `TestSprint856TaxFiguresBanner` both append to the file; kept both
(28/28 in that file pass).

**Commit SHA:** TBD.

### Sprint 853: Firm-owned client data and role gates (M7, L12)
**Status:** BLOCKED on CEO decision. **Priority:** P2 (largest change; data-model migration). **Source:** security review M7, L12.

**Defect M7:**
- `Client` has only `user_id`, with no org column. Org access is "all user IDs currently in my org"
  (`client_manager.py:102-118`, `engagement_manager.py:104-119`, `follow_up_items_manager.py:34-47`).
- `remove_member` (`routes/organization.py:406-441`, `shared/organization_policy.py:162`) only drops the membership.
- Consequences:
  - A removed staffer keeps full read and export access, including the `/engagements/{id}/export/package` ZIP, to
    every client and engagement they created.
  - The firm loses access to those records at the same moment.
  - A user who joins a firm exposes all their earlier clients to it.

**Defect L12:** members have the same rights as owners and admins to hard-delete clients and archive engagements.
- Client delete is `db.delete` at `client_manager.py:285`.
- An admin can remove another admin (`organization.py:413`).
- `OrgRole` is checked only in `organization.py` and `admin_dashboard.py`.

**CEO decisions** (defaults; use them if the CEO says "go with recommendations"):
1. Clients belong to **the firm**, not the individual (default: yes).
2. On joining a firm, the user **chooses** whether to bring their existing clients (default: ask, opt-in).
3. Destructive operations (client delete, engagement archive, misstatement/expectation archive) are **owner or
   admin only** (default: yes).
4. Only the **owner** can remove an admin (default: yes).

- [ ] Alembic migration: add a nullable `Client.organization_id` (FK `organizations.id`, `ondelete=RESTRICT`).
      Backfill it from the creating user's current `organization_id`. Run the migration-drift checks from Sprint 738.
- [ ] Switch the access computation in the three managers to: `Client.user_id == me` (personal, no org) OR
      `Client.organization_id == my current org`. Do it in **one** shared helper; the IDOR reviewer noted that
      these checks are copy-pasted.
- [ ] Unify `workpaper_index_generator.py:83-118` and `shared/expectation_evaluation.py:61-67`. They filter
      `Client.user_id == user_id` only, so org teammates get a 400 on `/export/package` and `/workpaper-index`.
      Move them onto the same helper deliberately.
- [ ] Join flow: opt-in "bring my N clients into <Firm>" when an invite is accepted (backend flag plus frontend
      prompt).
- [ ] Interim, if the migration slips: in `remove_member`, reassign the departing member's clients to the org owner
      (`Client.user_id = org.owner_user_id`) and log it.
- [ ] Role gates: `require_admin` on client delete/update-destructive paths, engagement archive, misstatement and
      expectation archive. Owner-only for removing an admin (`organization.py:413`).
- [ ] Tests:
  - removed member → 404 on their former clients, and the firm still sees them;
  - joiner without opt-in → their personal clients are not visible to the firm;
  - member → 403 on delete/archive, admin → 200;
  - admin removing an admin → 403.

**Commit SHA:** TBD.

---

### Sprint 823: Seven of the eighteen tools have never been exercised against realistic input
**Status:** PARTIAL — discovery done 2026-10-23 (58 findings, 21 P1; register in `reports/sprint-823-discovery-2026-10-23.md`, merged in PR #205 `40044bc7`); remediation in Sprints 824–827. Generator registration (item 3) done 2026-10-27; item 5 is 10/11 (multi-period remains); the CEO usefulness judgement remains.
**Priority:** **P1 for discovery** — not a known defect, but the highest-yield unexamined
surface in the product. The full-spectrum review found three P1s in its first hour of doing
exactly this, on fewer than 70 synthetic accounts.
**Source:** `tasks/ceo-actions.md:65` + the coverage gap measured 2026-10-23.

**The CEO action cannot be executed as written, which is probably why it sat.** It reads
"run all 18 audit tools against a realistic sample trial balance" — but **14 of the 18 do
not take a trial balance.** They take journal registers, invoice registers, payroll
registers, W-2 drafts, 1099 data, fixed-asset schedules. The task needs one realistic
dataset *per tool family*, not one TB.

**Measured 2026-10-23.** `backend/tests/anomaly_framework/generators/` holds 27 modules and
107 generator functions. Eleven of the eighteen tools already have deterministic generators:

| Covered | Generator |
|---|---|
| trial_balance | 13 registered TB anomaly types |
| journal_entry_testing | `je_generators.py` (13) |
| ap_testing | `ap_generators.py` (14) |
| revenue_testing | `revenue_generators.py` (17) |
| ar_aging | `ar_generators.py` (12) |
| payroll_testing | `payroll_generators.py` (12) |
| inventory_testing | `inv_generators.py` (10) |
| multi_period | `multi_period_generators.py` (7) |
| bank_reconciliation | `bank_rec_generators.py` (5) |
| three_way_match | `twm_generators.py` (5) |
| statistical_sampling | `sampling_generators.py` (6) |

**Seven have none** — and the pattern is the point:


**Six of those seven are exactly the tools Sprint 689 added** when the catalog went 12 → 18.
The synthetic framework predates that expansion and was never extended to it. So the tools
the framework has never looked at are the *newest* ones — the least-exercised code in the
product, reached through a UI that presents them identically to the mature eleven.

- [x] Build a realistic fixture per uncovered tool, from each engine's own input dataclass
      (the pattern used for `W2ReconciliationConfig` in Sprint 811)
- [x] Drive each of the seven engines end-to-end and record the output, not just the absence
      of an exception — A-5 returned `0.0` happily for the life of the product
- [x] Register each generator in `tests/anomaly_framework/registry.py` and add its row to
      `COVERAGE_MAP.md`, which `test_coverage_map.py` already enforces
      **Done 2026-10-27.** The registry was TB-only (`ANOMALY_REGISTRY` injects into a TB
      DataFrame), so non-TB generators could not join it. Added `TOOL_GENERATOR_REGISTRY`
      (all 18 slugs → their generator lists) and `CONFIG_TOOL_HARNESSES`; a new
      "Per-Tool Generator Coverage" table in `COVERAGE_MAP.md` with a row per tool;
      `test_coverage_map.py` now requires registry == map == `tools_registry` catalog, counts equal,
      names unique. **28 new generators** for the six config-shaped tools (SoD 5, intercompany 4,
      W-2 5, 1099 5, book-to-tax 5, cash flow 4) in `generators/*_generators.py`, baselines in
      `fixtures/base_config_tools.py`, run by `test_config_tool_anomaly_detected` — each asserts
      **clean on baseline, detected after injection**. Reverting Sprint 827 D1 (role rows overwrite)
      fails 2 of them. **Correction:** FA was never generator-less — `fa_generators.py` (9) predates
      823; it is now registered, so the uncovered count was six, not seven. **Found:** 16
      `requires_large_population` generators (AP 2, revenue 3, AR 4, payroll 3, FA 2, inventory 2)
      are registered but never parametrized — only JE runs its large-population set; recorded as
      PARTIAL in the map, not fixed. Book-to-tax is a calculator, so its five are known-answer
      checks rather than detections.
- [x] File each abnormal output as a finding with its measurement, in the A-1…A-6 style
- [ ] Then the remaining eleven, which have generators but whose *application* was never
      exercised end-to-end either
      **10 of 11 done:** Sprint 829 (discovery round 2, PR #218 `106c5782`) drove JE, AP, payroll,
      revenue, AR, inventory, TB, bank rec and three-way match; statistical sampling was driven by
      823 itself (S1–S9). **Multi-period comparison was driven by neither** — it is the one left.
- [ ] **CEO, after the engineering half:** judge whether the output is professionally useful
      to a practitioner. That part is not mechanisable and is the half the action item was
      really asking for.

**What the discovery found, in one paragraph.** The review's premise held: the least-exercised
code had the most defects. Statistical sampling — which *had* generators — could flip an audit
conclusion from fail to pass (S1). Fixed-asset depreciation recalculation flags every correct
declining-balance asset (A1). The intercompany elimination entry for revenue/expense is
reversed (I1). Three 1099 rules are wrong in ways that change whether a form is due (F1–F3). A
shared-parser bug read `$(2,000.00)` as +2,000 in every engine (P-1). The full register, with
reproductions, actual vs expected values and code locations, is in the report.



### Sprint 826: Tax tools — 1099 rules, W-2 coverage, book-to-tax loss years
**Status:** PARTIAL — F0–F8, W3–W7, W10, B3–B5 merged 2026-10-23; W1/W2 done 2026-10-24; B1 and the remaining items below are open.
**Priority:** **P1** — F1–F3 change whether a 1099 is due; W2 flags a correct HSA contribution
HIGH with an excise-tax message.

Engineering-only items first (F0, F2, F3, F6, F7, W3–W10, B2–B5). Statutory figures (F1's $10
royalty threshold, W1's SIMPLE catch-up, W2's HSA catch-up, F5's possible 2026 threshold change)
go through Sprint 793b's practitioner confirmation like the rest of the tables. B1 (NOL and
valuation allowance) needs a scope call.

- [x] **F0** — done in Sprint 827 (huge-but-finite amounts → 400 on all promoted tools).
- [x] **F2** — dated payments outside the tax year are excluded and counted
      (`summary.payments_outside_tax_year`); undated payments still count, as before.
- [x] **F3** — payments aggregate per payee TIN; the candidate names every vendor record it
      combined. Two existing tests changed for a stated reason: one fixture gave two "different"
      vendors the same TIN (they are one payee), and one asserted a $500 rents + $400 legal MISC
      filing — the F6 defect itself.
- [x] **F6 + F1** — 1099-MISC thresholds are per box (rents/other/medical/attorney $600,
      royalties $10); a MISC is due when any box qualifies. The $10 royalty figure is
      long-standing and not indexed, but goes on the 793b confirmation list with the rest.
- [x] **F7** — `other` → 1099-MISC box 3.
- [x] **W1/W2 — done 2026-10-24 (CEO decision 6, option C).** Three optional fields
      (`hsa_catchup_55`, `limit_simple_catchup_50`, `limit_simple_catchup_60_63`) that never count as
      missing, so an 11-field 2026 override still works. When a figure is absent and an employee
      could qualify, the check does not run and the response says so in a new `checks_not_run` list
      (also in the results view and CSV). Amounts over the base limit stay HIGH, but when age or the
      catch-up figure is unknown the finding says the catch-up could not be checked instead of
      asserting an excess contribution. SIMPLE plans now use SIMPLE catch-up figures (the old code
      allowed the 401(k) $7,500, missing real over-contributions). 2025 figures with sources:
      HSA $1,000 (IRC §223(b)(3)(B)); SIMPLE 50+ $3,500 and 60–63 $5,250 (IRC §414(v); IRS Notice
      2024-80). All on the 793b confirmation list in the engine. Not modelled: SECURE 2.0 §117 higher
      SIMPLE limits for small employers.
- [x] **W3** — Boxes 4 and 6 are compared with what payroll actually withheld (when supplied),
      and Box 12 codes D/W/S with payroll deferrals and HSA contributions.
- [x] **W4 (part)** — duplicate and orphan W-2 drafts are reported in the summary, IDs match
      whitespace-normalised, and the first of a duplicate pair is kept. The W-3 ↔ 941 comparison
      the module docstring promises is still missing.
- [x] **W5** — with no plan type, the plan is inferred from which deferral field is populated.
- [x] **F8** — governments and tax-exempt organisations are exempt payees (no medical/legal
      carve-back, unlike corporations).
- [x] **B3** — state rate validated to 0–1 like the federal rate. **B4** — a positive temporary
      movement reverses any DTL before building a DTA (gross balances were wrong; net was right).
- [x] **F4** — new `attorney_fees` category → 1099-NEC box 1, reportable for corporate law firms;
      `legal` remains gross proceeds paid to an attorney (MISC box 10). Backend, route literal,
      frontend type, CSV parser and help text.
- [x] **W6** — `ss_wage_base_exceeded` fires on a supplied draft only when Box 3 itself exceeds the
      base (a correctly capped draft no longer draws HIGH); with no draft it stays as the reminder.
      One test changed: it asserted the false alarm. **W7** — the Additional Medicare notice is
      counted as `informational_notices`, not as a discrepancy. **W10** — negative tolerance refused.
- [ ] F5, F9, B1, B2, B5, B6. (W4 W-3 vs 941, W8, W9 done in Sprint 855.)

**Commit SHA:** 8f7046ac (PR #206); 38df065f (PR #213); 643f7d42 (PR #214); 9d774226 (PR #215).

---

### Sprint 827: Fixed assets, intercompany, SoD, cash flow projector
**Status:** PARTIAL — A1–A3, A6, I1–I5, D1, D2 (part), C1, C4 merged 2026-10-23; open items listed below.
**Priority:** **P1** — A1 and I1 produce wrong output on correct input for every DDB register and
every IC revenue/expense pair.

- [x] **I1** — eliminations now credit the debit-natural side (receivable, expense, investment)
      and debit the credit-natural side (payable, revenue). Revenue/expense was reversed in both
      entity orders; none of the 51 existing intercompany tests pinned that direction.
- [x] **I2** — matching is one-to-one per entity pair: amount-reconciling matches first, then
      compatible-direction mismatches, no line used twice. 2 × $500 each side now eliminates
      $1,000 (was $2,000 across 4 pairs, "complete"); 600/400 vs 400/600 pairs by amount.
      **Known limitation:** one side split across accounts (600 + 400 against 1,000) still
      reports mismatches — it fails safe (incomplete, flagged) rather than over-eliminating.
- [x] **I3** — an explicit counterparty marks a line intercompany regardless of account name.
- [x] **I5 (500 + double count)** and **F0** — `ArithmeticError` (huge-but-finite amounts
      overflowing `quantize`) is a 400 on the analyze and export routes of W-2, 1099,
      book-to-tax, intercompany and cash-flow. The double-reported direction mismatch is gone
      with the one-to-one matcher.
- [x] **A1** — declining balance computed as compounding, `cost × (1 − (1 − r)^t)` with
      r = 2/life (or 1.5/life for 150% DB), floored at salvage. Correct DDB and 150% DB registers
      now produce 0 flags (every asset was flagged HIGH).
- [x] **A2** — expected accumulation capped at the depreciable base.
- [x] **A3** — FA-T11 uses the shared `parse_date`, so Excel date cells and `YYYY/MM/DD` are
      tested rather than silently skipped. ~~(`01-Jan-2019` is still outside the shared parser.)~~
      **Remainder closed 2026-10-27 — no code change needed:** Sprint 829 (D-2, PR #218 `106c5782`)
      had already added `%d-%b-%Y`, `%d %b %Y` and `%b %d, %Y` to the shared `parse_date` *for every
      caller*, so FA-T11 reads `01-Jan-2019` today. So the "widen it only for FA" constraint is moot:
      it was widened globally, and FA needs no per-call format. Pinned by
      `test_day_month_name_dates_are_tested_not_skipped` (4 forms; all 4 fail with those three
      formats removed). **Sprint 819 item 4 interaction:** its optional `formats=` parameter on
      `parse_date` must keep these three in the *default* list, or this test fails — FA passes none.
- [x] **A6** — FA-T11 compares magnitudes, so contra-negative accumulated depreciation no longer
      flags every row. FA-03 still flags negative accumulated depreciation; whether a contra
      presentation is "negative" there is a product call.
- [x] **D1** — SoD role rows are unioned per role and user rows merged per user ID, so a
      long-format matrix no longer hides conflicts split across rows.
- [x] **C1** — monthly/quarterly recurring flows step by calendar month from the first date,
      clamped to month-end without drift.
- [x] **I4** — IC phrases match whole words; generic phrases ("due to", "receivable from") count
      only when they name an entity in the consolidation; counterparty parsing no longer reads
      "Dublin Ltd" as "Ltd", and resolves dash forms ("IC AR - Beta").
- [x] **D2 (part)** — SoD results now list matrix permissions that no rule recognises (engine,
      API field `unmatched_permissions`, and a notice in the results view). **Policy call open:**
      a user with a single HIGH conflict scores 3 and tiers "moderate"; whether one HIGH conflict
      should make a user high-risk is a scoring decision, not a bug fix. *(Decided 2026-10-24 and done
      in Sprint 833: one HIGH conflict tiers the user high.)*
- [ ] Open (A4, A5, A8, C2, C3, C5, C6 and I5 done in Sprint 855): D2 (tiering; degenerate custom rules),
      I4's investment/payable pairing,
      P-3 (non-USD / EU number formats — needs a locale decision).

**Commit SHA:** 8f7046ac (PR #206); 38df065f (PR #213).

---

### Sprint 814: Upload routes — one scaffold, gating in one place
**Status:** PARTIAL — items 1–4 fixed (each reproduced or measured first; item 1 had a third
case the review missed, item 2 a root cause in the shared parser). Item 5 (one scaffold) remains,
and belongs with Sprint 790.
**Priority:** **P1** — item 1 is a paywall gap; items 2–3 are live inconsistencies.
**Source:** Code health review 2026-10-23, routes + frontend passes.

Two upload scaffolds exist and have drifted — `services/audit/file_tool_scaffold.py:26`
(TB + diagnostics only) and `shared/testing_route.py:66` (the six single-file testing tools) —
and nine routes use neither (`ar_aging`, `bank_reconciliation`, `three_way_match`, `sampling` ×2,
`audit_flux`, `audit_pipeline`, `audit_preview`, `audit_upload`, `currency`).

**Scope:**
1. [x] **`UpgradeGate` missing** on `app/tools/ap-testing/page.tsx` and
   `journal-entry-testing/page.tsx` (verified). Free users get the full upload UI and a 403
   after uploading. Confirm whether depreciation/loan-amortization omit it intentionally.
2. [x] `testing_route.py:139` never received the Sprint 713 `ArithmeticError` handling → a
   malformed decimal can still 500 and log at ERROR. `sampling.py:249` doesn't catch `ValueError`.
3. [x] Tool-run recording still uses `background_tasks.add_task` in `testing_route.py:124`,
   `file_tool_scaffold.py:56` and ~7 hand-written routes — the race PR #183 fixed elsewhere
   (`useAuditUpload.ts:137` refreshes the run list immediately). Record synchronously.
   *Code-read, not reproduced.*
4. [x] Verify then fix: `audit_flux.py:39` has no quota, tool-access or format check — a Free
   user can likely send PDF/OFX/QBO through flux. Only `audit_pipeline`/`audit_upload` call
   `enforce_format_access`.
5. [ ] One scaffold taking `(files, gates, analyze_fn, record_policy)`; migrate all upload routes.
   **Coordinate with Sprint 790**, whose increment-on-success belongs in the same recorder path.

**Delivered 2026-10-23 (items 1–4):**
- **Item 1 — three pages, not two.** Checked every tool page against the backend gates:
  depreciation and loan-amortization have no backend tool check (free calculators outside the
  18), so their omission is correct; **multi-period** enforces `multi_period` server-side but
  had no `UpgradeGate` either. All three wrapped. `src/__tests__/ToolPageGating.test.ts` derives
  the page list from `TOOL_LEDGER` and the Free set from `UpgradeGate.tsx`, and asserts every
  paid tool page renders `<UpgradeGate toolName="<ledger id>">` — 3 of 18 fail on the old pages.
  AP/JE page tests now opt into the shared helper's existing `hasTierGating` scenario (they never
  had); MultiPeriod gets a Free-tier test and paid-tier default mocks.
- **Item 2 — reproduced by fuzzing, root cause in the shared parser.** Injected 13 malformed
  numerics into every cell of the AP/JE/Payroll/Revenue/FA/Inventory base fixtures (663 cases):
  **5 of 6 tools 500'd** on `Infinity`/`-inf`/`1e999999` in an identifier column.
  `upload_pipeline.py:677` strips a trailing `.0` from ID columns with `int(float(x))`, which
  raises `OverflowError` on a non-finite float — in `parse_uploaded_file`, so every upload
  route was exposed, not just these six. Guarded with `math.isfinite`; 663/663 clean after.
  `testing_route` now also catches `ArithmeticError` at WARNING (it had the Sprint 713 gap
  exactly as described). The sampling `ValueError` claim was **wrong** — both handlers already
  map it to 422; their real gap was `ArithmeticError`, which I could not reproduce from input
  (the engine parses through `safe_decimal`), so that handler is recorded as defensive only.
- **Item 3 — 11 call sites, not ~9.** Every `background_tasks.add_task(maybe_record_tool_run, …)`
  is now a direct call (the PR #183 fix, extended): `testing_route`, `file_tool_scaffold`, flux,
  pipeline, AR, bank rec, TWM, multi-period ×2, sampling ×2. Unused `BackgroundTasks` params
  dropped from seven handlers. An AST guard fails any reintroduction.
- **Item 4 — verified, then fixed.** Flux ran no gates at all. It now enforces tool access,
  the monthly quota and the format allow-list on both files, before reading any bytes. Tests:
  Free + `.pdf` → 403, Free at quota → 403 (engine never called), Free within limits → 200.
  The other non-TB upload routes are paid-only, and paid tiers allow every format, so flux was
  the only route where the missing format check was reachable.

**Found while fuzzing — filed, not fixed (needs its own measurement):** the identifier heuristic
at `upload_pipeline.py:670` matches by **substring**, so `"id"` catches *Res**id**ual Value*,
*Pa**id** Amount*, *Div**id**end*, and `"no"` catches *Notes*, *Nominal*. Those monetary columns
are converted to strings before the engines see them. The engines re-parse through
`safe_decimal`, so no wrong number has been demonstrated — but NaN becomes `""` on the way,
which changes "missing" semantics for any check that tests `isinstance(x, float)`. Word-boundary
matching is the likely fix; it needs a sweep of real column names first.

**Also observed:** both sampling routes accept `nan`/`inf` form floats (Pydantic's default) and
return a result rather than a 422 — e.g. `sampling_interval=nan`. Same family as above; filed here.
- [x] **Done — fixed in Sprint 824 (S9, PR #205 `40044bc7`, `routes/sampling.py::_require_finite`), and now
  swept.** 2026-10-27: re-verified both routes return 422; the four Sprint 824 cases only pinned the
  fields the review tried, so `test_every_float_form_field_on_both_sampling_routes_rejects_non_finite`
  derives every float form field from the two handler signatures (4 + 5) × `nan`/`inf`/`-inf`.
  Removing `stratification_threshold` from the guard fails 3 of the new cases and none of the old four.

**Commit SHA:** 91753ba2 (PR #202).

---

### Sprint 815: Engine performance — parse once, prune pairs
**Status:** PARTIAL — items 1, 3, 4, 5 done with identical outputs; item 2 still blocked on CEO decision 2.
**Priority:** **P1** — a 100k-row GL takes up to 113s today.
**Source:** Code health review 2026-10-23, engines pass. Measured on synthetic data.

**Scope:**
1. [x] **Dates re-parsed 11× per JE entry.** `shared/parsing_helpers.py:141` `parse_date` tries
   up to 9 formats; `je_testing/analysis.py:1513` `_extract_hour` up to 6. Profile: 1.19M
   `parse_date` / 8.4M `strptime` = 283 of 302s. Parse once per entry (or a per-run memo):
   **31s → 6.0s** date-only, **113s → 6.1s** date+time, identical score and flag count.
   **No process-wide `lru_cache`** — it would retain uploaded values across requests (Zero-Storage).
   Preserve both existing spellings: `parse_date(a) or parse_date(b)` vs `parse_date(a or b)`
   treat an unparseable posting date differently. Apply the same to AP (7 sites), Revenue (7),
   Payroll (4), Three-Way Match, Bank Rec.
2. [ ] **Bank-rec split match** (`bank_reconciliation.py:668-690`) brute-forces 2–4-row combos;
   the date filter (`:735`) is skipped at the default tolerance 0, which the route never
   changes. 2.05s per bank-only txn at 80 unmatched rows; 64.7M combos at 200.
   *(Done 2026-10-24 in Sprint 833: lossless trim + a 20-candidate cap, disclosed; nothing is
   cleared by the cap.)*
3. [x] Fuzzy name loops (`ap_testing/analysis.py:1463`, `payroll_testing/analysis.py:1877`,
   `three_way_match_engine.py:1314-1350`): early-exit on `2*min/(la+lb)` and
   `real_quick_ratio()`/`quick_ratio()` upper bounds. **88.1s → 14.2s** on 2,000 vendors,
   identical 670 hits. Keep `SequenceMatcher(a, b)` order — swapping gave 668. In 3WM compute
   vendor score first and skip amount/date work below threshold.
4. [x] Hoist date parsing and tolerance `Decimal` out of inner loops: AP fuzzy duplicates
   `ap_testing/analysis.py:1060-1068`, JE reciprocal `je_testing/analysis.py:2184`.
5. [x] Benchmark test (marked `slow`) pinning the 100k-row JE run under a ceiling, so it can't regress.

**Delivered 2026-10-23 (items 1, 3, 4, 5) — every change result-identical, measured old vs new:**
- **Item 1 — one memo instead of ~30 call-site rewrites.** `shared/parsing_helpers.parse_memo()`
  holds a dict in a `ContextVar` for the duration of one engine run; `parse_date` and JE's
  `_extract_hour` consult it via `memoized_parse`. Every engine entry point and battery
  (JE, AP, Payroll, Revenue, AR, FA, Inventory, Bank Rec, Three-Way Match — 17 functions) is
  decorated `@with_parse_memo`. Keyed by the raw string, so `parse_date(a) or parse_date(b)` vs
  `parse_date(a or b)` keep their different semantics untouched. **Zero-Storage:** the memo
  exists only inside the run and is dropped on exit, including on exceptions — tested; it is not
  a process-wide cache. Measured on JE: **100k rows with timestamps 65.6s → 9.6s**, 20k rows
  4.7s → 1.1s (date-only) and 13.1s → 1.8s (datetime); identical score and identical per-test
  flag counts (hashed).
- **Item 3** — `shared/fuzzy_match.similarity_at_least` checks `real_quick_ratio()` and
  `quick_ratio()` (documented upper bounds) before `ratio()`; argument order preserved. Used in AP
  vendor variations, payroll address matching and both 3WM fuzzy loops (where a sub-threshold
  candidate can never be selected, so its amount/date work is skipped too). **AP on 2,000
  vendors: 65.4s → 13.9s, identical flagged set.** A 3,000-case randomized property test proves
  the gated function equals the plain ratio-and-compare.
- **Item 4** — AP fuzzy-duplicate tolerance `Decimal` hoisted out of the pair loop; the date
  parses in that loop and in JE reciprocal are now memo hits.
- **Item 5** — `@pytest.mark.slow` test pins a 100k-row JE run under 30s (runs in the nightly
  slow job, not PR CI); AST guard asserts every engine entry point carries the memo.

**Commit SHA:** 50b55bc7 (PR #203).

---

### Sprint 817: Dead-code sweep
**Status:** PARTIAL — items 1, 2, 5, 6 done (5 with two findings left for a product call, see
"Delivered 2026-10-27"); items 3–4 await CEO decisions.
**Priority:** P2 — ~7,000 lines with no runtime effect except bundle size and reader cost.
**Source:** Code health review 2026-10-23. Every item grep-verified repo-wide; re-grep before deleting.

1. [x] **Frontend (~6,000 lines), delete with their tests:**
   analytics `TrendSection`, `TrendSummaryCard`, `TrendSparkline`, `IndustryMetricsSection`,
   `RollingWindowSection` + `hooks/useTrends`, `useRollingWindow`, `useIndustryRatios`;
   marketing `ToolSlideshow`, `ToolShowcase`, `ProductPreview`, `ProofStrip` (fix the stale
   comment at `app/(marketing)/page.tsx:34`); workspace `QuickSwitcher`, `CommandBar`,
   `WorkspaceHeader`, `QuickActionsBar`, `RecentHistoryMini` + `quickSwitcherOpen` in
   `WorkspaceContext.tsx:133,166`; `comparison/ComparisonSection`, `adjustments/AdjustmentSection`
   + `hooks/useAdjustments`, `trialBalance/GuestMarketingView`, `shared/ShareExportModal`,
   `hooks/usePriorPeriod`, `engagement/EngagementList`, `shared/PageEmptyState`,
   `auth/ProtectedRoute`, `utils/animations`.
2. [x] **Backend modules:** `shared/derived_metrics.py`, `shared/concentration_metrics.py` (no
   importers, no tests); test-only `shared/alert_checker.py`, `shared/route_errors.py`,
   `shared/report_layout.py` (`wrap_cell`), `shared/tier_display.py`, `billing/guards.py`;
   `shared/round_amounts.detect_round_amount` (unless 819 item 3 adopts it).
3. [ ] **Product decision 4:** `engagement_dashboard_memo.py` (298 lines, no route since Sprint 564)
   and `shared/intercompany_resolver.py` (Sprint 764, never called — `Engagement.intercompany_counterparties`
   is stored and exposed but unused).
4. [ ] **Product decision 1 (bulk upload):** `components/batch/*`, `contexts/BatchUploadContext.tsx`,
   `hooks/useBatchUpload.ts`, `routes/bulk_upload.py`, `shared/bulk_job_store.py` — wire or delete,
   and fix the pricing/UpgradeModal claim to match. **Do not delete the route before Sprint 790 lands.**
5. [x] **Unused helpers/constants:** entitlement `check_client_limit`, `check_tool_access`,
   `check_workspace_access`, `check_activity_log_access` (routes re-implement them inline — keep
   one implementation each); `auth.get_current_user` (unreferenced and skips the password-change
   check — unsafe to adopt); `ratio_engine.calculate_dupont_decomposition`;
   `compute_bank_rec_risk_score` alias; `PAYROLL_SUSPICIOUS_KEYWORDS`; `SOURCE_LEASE`,
   `SOURCE_GOING_CONCERN`, `PREPAID_KEYWORDS`, `STANDARD_ADJUSTMENTS_BY_CODE`,
   `CURRENT_RATIO_THRESHOLD`, `LOW_CONFIDENCE_THRESHOLD`; `export/transport.py:41` no-op and
   unused `"excel"` branch at `:46`; the 10 unused `DEFAULT_*` aliases in
   `w2_reconciliation_engine.py:160-172` and their stale comment (**fix in the current branch before merge**).
6. [x] **Assets/deps:** delete `frontend/public/backgrounds/background4.jpg` (22 MB, unreferenced);
   compress `background5.jpg` (7.1 MB raw CSS background on `pricing/page.tsx:774`);
   remove `ts-jest`, `@eslint/eslintrc`; move `@testing-library/dom` to devDependencies; declare
   `eslint` explicitly; fix or drop `npm run generate:types` (`openapi-typescript` not installed).

**Delivered 2026-10-23:**
- **Item 1:** 26 frontend modules and their 14 test suites deleted (−8,315 lines), each re-verified
  first — every remaining reference was a comment or a barrel re-export. Barrels pruned,
  `quickSwitcherOpen` removed from `WorkspaceContext`, the stale `ToolSlideshow` comment fixed.
  `tsc`, lint, 196 suites / 1,991 tests and `npm run build` all clean.
- **Item 2:** deleted `derived_metrics`, `concentration_metrics`, `billing/guards` (no importers at
  all) and the test-only `alert_checker`, `route_errors`, `report_layout` with their tests.
  **Kept `tier_display`:** test-only, but the pricing-launch validation tests use it as their
  reference for purchasable tiers. `guards/parser_alerts.toml` kept (the format-rollout runbook
  points operators at it); its header no longer claims a checker reads it.
- **Item 5 (most):** removed the `compute_bank_rec_risk_score` alias, `SOURCE_LEASE`,
  `SOURCE_GOING_CONCERN`, `STANDARD_ADJUSTMENTS_BY_CODE`, `CURRENT_RATIO_THRESHOLD`,
  `LOW_CONFIDENCE_THRESHOLD`, the module-level `calculate_dupont_decomposition` wrapper (DuPont
  itself lives on `RatioEngine.calculate_dupont`) and ten of the eleven W-2 `DEFAULT_*` aliases.
  **Removed `auth.get_current_user`**: unreferenced, and it skipped the Sprint 199 `pwd_at`
  revocation check, so adopting it would have accepted tokens revoked by a password change.
  **Not deleted, and flagged instead:** `PAYROLL_SUSPICIOUS_KEYWORDS` and `PREPAID_KEYWORDS`. An
  unused *keyword list* can mean a check that was designed and never wired in — a possible
  detection gap, not dead code. Worth a look before deleting. The four duplicated entitlement
  checks and `export/transport.py` remain.
- **Item 6:** `background4.jpg` (22 MB, unreferenced) deleted; `background5.jpg` 7.1 MB → 140 KB
  (1920px, q72 progressive — it renders at 6% opacity).

**Commit SHA:** 1f058c4b (PR #207).

**Delivered 2026-10-27 (items 5 and 6 remainder):**
- **`check_client_limit`:** `POST /clients` re-implemented it inline; the route now calls the shared
  function. New `TestCreateClientLimit` (4 HTTP tests in `test_clients_api.py`: under limit, exact
  403 body at limit, soft mode, unlimited tier) was run green against the *old* inline route first,
  then against the new one. Only difference: soft mode now also logs the standard "SOFT entitlement
  block" warning (the inline copy was silent). Hard-mode 403 body byte-identical.
- **`check_tool_access`:** deleted. The live implementation is `shared.testing_route.enforce_tool_access`
  (21 call sites); the factory had no route callers and a different message. Its unit tests were
  ported to `enforce_tool_access` (exact 403 body, soft mode, no-db fallback); the runbook line in
  `format-rollout.md` that pointed at it now names `enforce_format_access`.
- **`check_workspace_access` / `check_activity_log_access`: kept, and flagged — CEO/product call.**
  There is no inline duplicate: *nothing* on the backend enforces the `workspace` or `activity_logs`
  entitlements. Free tier is `workspace=False`, yet every `/engagements` route depends only on
  `require_current_user`. (Team activity is reachable only through `/admin/*`, gated by
  `admin_dashboard`, which has the same tier values — so `activity_logs` is effectively covered;
  `workspace` is not.) Wiring the check would change what Free users get, so it is not done here.
  Decide: wire `check_workspace_access` onto the engagement routes, or delete both and drop the
  flags from `TierEntitlements`.
- **`export/transport.py`:** removed the no-op `extension = fmt if fmt != "xlsx" else "xlsx"` and the
  `"excel"` alias (every caller passes a literal `pdf`/`xlsx`/`csv`; `"excel"` would also have
  produced a `.excel` filename). New `test_export_transport.py` (7).
- **`PREPAID_KEYWORDS`: deleted as dead.** Added in Sprint 513, never referenced. The engine filters to
  liability-classified accounts before any keyword runs, and prepaid balances are assets, so there is
  no detection it could have fed. `TestPrepaidAccountsNotInScope` pins the output, and the
  engine's `to_dict()` on that fixture was byte-identical before and after the deletion.
- **`PAYROLL_SUSPICIOUS_KEYWORDS`: kept — looks like an unwired check, needs a product call.** Added
  in Sprint 86 with weights in the `classification_rules` tuple shape, under "Keywords for ghost
  employee pattern detection", and never read. PR-T9's "No department assignment" indicator only
  fires on an *empty* department, so placeholder values the list names (`"N/A"`, `"Unassigned"`,
  `"No Department"`, `"Unknown"`) pass as assigned departments, and the status words (`terminated`,
  `inactive`) have no field to match since `PayrollEntry` carries no status column. Wiring it changes
  PR-T9 output. Decide: wire (placeholder-department matching at minimum), or delete.
- **npm:** removed `ts-jest` (Jest uses `next/jest`/SWC) and `@eslint/eslintrc` (flat config, no
  `FlatCompat`); `@testing-library/dom` moved to devDependencies (no `src` import — it is the peer of
  `@testing-library/react`/`jest-dom`); `eslint` declared (`^9.39.5`). **`generate:types` dropped**
  with `scripts/generate-types.sh`: `src/types/api-generated.ts` does not exist and nothing consumes
  it, and the script would `npm install -D openapi-typescript` on the fly, mutating the lockfile.
  **Lockfile audited:** 882 → 871 entries; 0 added; 11 removed (ts-jest and its private tree:
  `bs-logger`, `handlebars`, `lodash.memoize`, `make-error`, `neo-async`, `source-map@0.6.1`,
  `uglify-js`, `wordwrap`, nested `semver`/`type-fest`); 2 changed (`eslint`, `@eslint/js`
  9.39.4 → 9.39.5); 49 flag-only. Of those, 34 are the eslint chain losing `peer: true` — it is now a
  real devDependency tree rather than peer-derived, which is the fragility the 786b jest-dom note
  hit with `--legacy-peer-deps` — and 15 are the `@testing-library/dom` subtree becoming `dev`.
  Nothing unexpected.

**Verification (2026-10-27):** backend full suite 9,979 passed / 0 failed; frontend tsc, eslint,
2,072 Jest tests and `npm run build` (65 `ƒ` routes + Proxy) all clean. Full detail is in the Sprint 786
"typescript 6 → 7" entry. **Commit SHA:** 2a6504e4.

---

### Sprint 818: Pricing has one source of truth
**Status:** PARTIAL — items 1–2 done; item 3 held for a CEO/counsel decision (see below).
**Priority:** P2 — the copies have already drifted.
**Source:** Code health review 2026-10-23, frontend pass.

`app/(marketing)/pricing/page.tsx:13-133,354-512,544` redefines everything `domain/pricing.ts`
exports, and `components/pricing/PricingEstimator.tsx` + `PricingCard.tsx` — built on the domain
module — are imported nowhere (verified). Drift: the page has `badge: 'Most Popular'`, the domain
copy does not, so tests of the domain module test code that never renders.

- [x] Page renders `PricingEstimator` + `PricingCard` from `domain/pricing` (~450 lines out).
- [x] Point `app/(auth)/checkout/page.tsx:23-27`, `components/billing/UpgradeModal.tsx:20-45` and
      the terms tier table (`terms/page.tsx:616-626`) at the same module.
- [ ] Consolidate the "what we store / never store" lists (`trust/page.tsx:239-254` vs
      `approach/page.tsx:94-109`, worded differently) into one `content/` source — it is
      Zero-Storage compliance copy.

**Delivered 2026-10-23 (items 1–2):**
- The review's direction had to be **reversed** for the card: `PricingCard` was the stale copy
  (no badge, pre-Sprint-703/708 typography), so rendering it would have regressed the live page.
  The page's live markup moved *into* `PricingCard`; `PricingEstimator` was already equivalent
  (and derives its seat description instead of hard-coding it). The page now renders both and
  imports tiers, FAQ, promo copy and types from `domain/pricing` — **935 → 289 lines**. The
  `'Most Popular'` badge now lives in the domain tier, which was the drift.
- New id-keyed lookups in `domain/pricing` (`getTier`, `tierPriceDollars`, `baseSeats`,
  `maxAdditionalSeats`, `seatPriceDollars`). Checkout and `UpgradeModal` read every price, seat
  count, seat limit and seat rate from them; the modal keeps only its short feature blurbs as
  modal-specific copy.
- **Terms of Service kept literal on purpose** — it is a versioned legal document, so a price
  change should force a deliberate edit to it. `PricingSingleSource.test.ts` fails when its tier
  table disagrees with the domain, and fails if any of the three surfaces re-declares a price,
  seat or tier literal (2 of its 6 tests fail on the pre-change files).

**Item 3 — decided 2026-10-24 (CEO decision 8) and moved to Sprint 834.** Original note: Consolidating the two
"we store / we never store" lists means choosing one wording for Zero-Storage compliance copy.
More importantly, **both lists may be inaccurate**: they promise Paciolus never stores
"individual account balances" or "anomaly details tied to specific accounts or amounts", while
the 2026-10-19 DECISION block above records that the database persists
`uncorrected_misstatements.accounts_affected_json` (account names with DR/CR amounts),
`analytical_expectations` (expected and actual values) and `diagnostic_summaries` (aggregate
totals). That is a question for the CEO and counsel before anyone edits the copy.

**Commit SHA:** c6cc8e7c (PR #204).

---

### Sprint 819: Backend deduplication
**Status:** PARTIAL — items 3–10 done 2026-10-27 (branch `sprint-819-backend-dedup`, pending CI + merge); items 1 and 2 (result base classes, `.empty()`/`.from_flags()`) not started — see below.
**Priority:** P2.
**Source:** Code health review 2026-10-23, engines + routes + exports passes.

**Output-preservation harness (built first, on unmodified code):** `tests/test_sprint819_output_snapshots.py`
(engine `to_dict()` for JE, AP, Payroll + PR-T9 ghost/HR-master, Revenue, AR, FA, Inventory, three-way
match, currency, and hand-mapped column overrides; seeded data, frozen clock, key order pinned) and
`tests/test_sprint819_route_snapshots.py` (six promoted JSON tools incl. error paths + ToolRun rows,
their CSV exports, form-input / engagement / admin exports, the diagnostic export pipeline incl. log
events and error paths, testing-tool CSVs + memo PDFs by page text). Goldens in `tests/snapshots/sprint819/`;
regenerate only with `SPRINT819_UPDATE_SNAPSHOTS=1` when a change is intended. Every refactor below kept them green.

1. [ ] Generic result base classes in `shared/` for the per-tool `FlaggedEntry` / `TestResult` /
   `DataQuality` / `CompositeScore` (~650 lines across 7 tools; e.g. `je_testing/analysis.py:546-665`).
   **JSON output must not change**: Payroll stores severity/tier as strings and rounds
   `completeness_score` to 2 dp; AR adds `skipped`/`skip_reason`; Payroll `top_findings` is list-of-dicts.
   *(Not started 2026-10-27: out of safe room in this pass. The snapshot harness above now covers every
   tool's `to_dict()`, so this is unblocked; do it one tool at a time against those goldens.)*
2. [ ] `.empty(...)` / `.from_flags(...)` constructors replacing 76 zero-result blocks (~800 lines)
   and ~110 hand-computed `flag_rate`s. AR's `_skipped_result` (`ar_aging/analysis.py:1801`) is the model.
   *(Not started; depends on item 1's base classes. Mind `flag_rate` variants — `x / max(n, 1)` vs
   `x / n if n else 0.0` agree only for n ≥ 1.)*
3. [x] Round-amount test copied 4× → `shared/round_amounts.py::match_round_amount` (Decimal tier match) +
   `keep_most_severe` (count all, keep most severe then largest; stable). Payroll now matches via the 4-tier
   table but keeps its own wording, string severity and amount-only details.
4. [x] `parse_date(..., formats=...)`; default list is now `DEFAULT_DATE_FORMATS` (unchanged). AR `as_of_date`
   and the rate-table `effective_date` pass their existing narrow sets (memo keyed per set); FA already used
   the shared default since Sprint 827. Guard tests prove nothing new is accepted.
5. [x] `AuditEngineBase` default `apply_column_overrides` from class-level `OVERRIDABLE_COLUMNS` + an
   `after_column_overrides` hook (JE debit/credit-vs-amount + dual dates, AP dual dates + check numbers).
   Inventory uses it too; Payroll keeps its suffix-less override. FA and Revenue now run as
   `FixedAssetTestingEngine` / `RevenueTestingEngine`. **AR not migrated:** two input files (TB + optional
   sub-ledger) do not fit the single-input `run_pipeline`; it stays a lint migration target.
6. [x] *(`_to_decimal` half done 2026-10-23.)* `shared/testing_route.py::run_json_tool` owns enforce →
   quota → compute → record for the six promoted tools; SoD keeps re-raise-unchanged via `reraise_errors`.
   The two AST guards that enumerate recording/metering sites count it as the delegate.
7. [x] Every file download builds its response in `shared/export_helpers` (`attachment_response` +
   `pdf_/excel_/csv_response`); ~20 hand-rolled blocks and the PDF/ZIP 8 KB chunk generators removed.
   Bodies, Content-Type and Content-Disposition byte-identical (the bare `filename=` form is kept via
   `quote_filename=False`). *(No-store done 2026-10-24.)* **Deliberately still a single-chunk
   `StreamingResponse`, not a plain `Response`:** GZipMiddleware (`minimum_size=500`) gzips every streamed
   body today; a plain `Response` would stop compressing downloads under 500 B — a wire change. Callers are
   typed against `Response`, so that switch is one line if wanted. Only framing change: the formerly
   chunked CSV downloads now also send `Content-Length`.
8. [x] `export/pipeline.py`: eleven functions → `_run_export(...)`; log events, mapped exceptions and
   filenames unchanged.
9. [x] **Env reads through `config.py` only.** *(Done 2026-10-23 for the secret-bearing reads —
   see below.)* Latent bug: `email_service.py:48-50` reads
   `SENDGRID_API_KEY` via `os.getenv` while `config.py:647` validates via `_resolve_secret` —
   a Docker/cloud-secret key passes the startup check and email silently does not send. Also
   `entitlement_checks.py:69,388`, `health.py:269`, `logging_config.py:113,154`,
   `memory_budget.py:40`, `storage_client.py:26`, `export_share_storage.py:47-50`, `retention_cleanup.py:27`.
   **Delivered:** `email_service` now resolves `SENDGRID_API_KEY`, the from-address/name and
   `CONTACT_EMAIL` through `secrets_manager.get_secret` — the chain config validates with — and a
   test proves a key supplied only as a Docker secret reaches it (fails on the old module).
   `/health/redis` reads `config.REDIS_URL`: with the URL in a secrets file, the limiter used Redis
   while the probe reported "not_configured" and healthy. Re-checked the rest of the list:
   `export_share_storage` already reads through `_load_optional`, and the remaining direct reads
   (`REDACT_LOG_TRACEBACKS`, `MEMO_RSS_WARN_MB`) are non-secret tuning flags — left as they are.
10. [x] Long functions split: `run_three_way_match` → exact-PO / fuzzy (+ invoice and receipt scorers) /
   unmatched / summary over a shared `_MatchState`; `convert_trial_balance` → `_detect_account_columns`,
   `_resolve_currency_rates`, one `_flag()` builder, columns read once (`to_numpy`) instead of per-cell `df.at`;
   Payroll PR-T9 → grouping + in-file + HR-master indicator functions.

**Found, not fixed (outside scope, pre-existing):** `/export/pdf` 500s when `risk_summary` is null
(`pdf/sections/diagnostic.py` calls `.get` on the `None` the schema dumps); memo follow-up wording is
seeded with the per-process `str` `hash()` (`shared/memo_template.py`), so the same report's wording
changes between server restarts.

**Verification:** full backend suite 10,022 passed / 0 failed (3f3b74df, 56m44s serial; a first run caught the three-way-match `@with_parse_memo` slip, fixed in 3f3b74df); 22 Sprint 819 snapshot tests green; OpenAPI drift check clean (221 paths, 430 schemas); mypy 204 errors (baseline 1011), none in touched code; `ruff check` + `ruff format --check` clean on touched files.

**Snapshot weight:** the goldens are stored gzipped (`*.json.gz`, `mtime=0` so regeneration is byte-stable): 6.4 MB / ~200k lines of JSON became 441 KB.

**Commit SHA:** 5fa3d72a (PR #216, item 6); 970eb085 (PR #209, item 9); 2026-10-27 branch
`sprint-819-backend-dedup`: 4fe89870 (snapshots), 5601d850 (3), 17bdcf41 (4), e3ba87fe (8), 54ff41c2 + a9c5f5f2 (7),
9f9def4d (6), 1bba4172 + 81976abe + 3f3b74df + 4423c770 (10), 7e3aeded (5).

---

### Sprint 820: Frontend consolidation and bundle weight
**Status:** PARTIAL — items 2–7 done (3 and 5 earlier, 2/4/6/7 and the rest of 3 on 2026-10-27, branch `sprint-820-frontend-consolidation`, pending CI + merge); item 1 (`TestingToolPage` shell) not started — see below.
**Priority:** P2.
**Source:** Code health review 2026-10-23, frontend pass.

1. [ ] `TestingToolPage` shell for the six single-file testing pages (ap, payroll, revenue,
   fixed-assets, inventory, journal-entry — 70–80% identical, ~1,650 lines). Use the existing
   `components/shared/FileDropZone`; build `UpgradeGate` in so 814 item 1 cannot recur. ~1,100 lines out.
   Collapse the ~20 pass-through `*ScoreCard`/`*DataQualityBadge` wrappers.
   **Not done — needs a design call first.** The item asks for both "reuse `FileDropZone`" and
   (this pass) "no visual change", and those conflict: `FileDropZone` is the compact `p-6`
   labelled zone from bank-rec/AR, while the six pages use a large `p-12 rounded-2xl` zone with an
   icon disc and `h3` prompt. The six pages have also drifted apart — JE uses raw `sage-50`/`sage-700`
   classes and plain `<button>`s where the others use theme tokens and `Button`; only AP/Payroll/JE
   have the settings drawer and `SavedSettingsNotice`; spinner and border shades differ per page — so a
   pixel-identical shell would be a slot for nearly every line. Collapsing the wrappers also breaks
   each page test's `jest.mock('@/components/<tool>')` test-ids. Decide which variant is canonical
   (and whether `FileDropZone` gets a large variant), then do the shell with page-test updates.
   `ToolPageGating.test.ts` reads `<UpgradeGate toolName=…>` from each page's source; a shell must
   update that test to recognise the shell's prop.
2. [x] `createJsonAnalysisHook({...})` for `useSOD`, `useForm1099`, `useW2Reconciliation`,
   `useBookToTax`, `useIntercompanyElimination`, `useCashFlowProjector`.
   *(Done 2026-10-27: `hooks/createJsonAnalysisHook.ts` (112 lines) owns status/result/error, the
   engagement link and CSV export; the six hooks are config + extras (SoD rules, B2T standard
   adjustments, W-2 error rewrite, `project` alias) — 554 → 276 lines. Public APIs unchanged;
   existing tests pass unchanged.)*
3. [x] `terms`, `privacy`, `about`, `approach` and `app/(marketing)/layout.tsx` as server components.
   *(Terms + Privacy 2026-10-23 with `Reveal` wrappers. About, Approach and the layout 2026-10-27:
   `'use client'` dropped, motion elements come from `components/ui/motionClient` with the same
   props, so nothing animates differently; About's `custom`-function variant became a per-card static
   variant with the same delay. Page-only client chunk About 12.6 → 0.4 KB, Approach 17.5 → 0.4 KB.)*
4. [x] `trust/page.tsx`: static data → `content/trust.ts`, 4 interactive blocks → `components/trust/*`, page becomes a server component.
   *(Done 2026-10-27: `ArchitectureDiagram`, `ControlMatrix`, `PlaybookPreview`, `CountUp` are
   client components; the page, `ModuleSection` and `ComplianceTimeline` are server components.
   Page-only client chunk 37.6 → 22.6 KB (8.8 → 6.2 KB gz). `test_citation_consistency.py` now
   scans `content/trust.ts` and `components/trust/`.)*
5. [x] `ToastContext.tsx:73` — split stable actions from state so 8 consumers stop re-rendering on
   every toast. *(Done 2026-10-24: actions and state in separate contexts; `useToast()` returns the
   stable actions, `useToastState()` the list for the container. A render-count test pins it.)*
6. [x] `BaseColumnDetection` type; `ARDataQuality` extends `BaseDataQuality`.
   *(Done 2026-10-27: `BaseDataQuality` is the 3 shared fields, the six row-based tools extend
   `RowDataQuality` (+`total_rows`), all six `*ColumnDetection` extend `BaseColumnDetection`. Types only.)*
7. [x] Measure framer-motion (139 importers, no `LazyMotion`); fold the 5 local `fadeUp` copies into `lib/motion.ts`.
   *(Done 2026-10-27. `next experimental-analyze`: framer-motion + motion-dom is 145.8 KB raw on
   every marketing route, 139.3 KB on tool/auth routes — ~12% of client JS. **LazyMotion not
   adopted:** it only pays once all 139 importers move from `motion` to `m` (one `motion` import
   pulls the full feature set back in) — a sweep plus a lint rule, bounded by that ~140 KB. The
   `fadeUp` copies are `marketingFadeUp` / `marketingFadeUpAt` / `marketingFadeUpSoft`, values
   unchanged. `components/ui/motionClient` (7 re-exports) replaces `framer-motion/client`, whose
   170-element module had added +2.4 KB to every route.)*
   Route first-load JS (bytes, `route-bundle-stats.json`) before → after the sprint:
   `/about` 957,024 → 939,647 · `/approach` 962,082 → 939,647 · `/trust` 982,652 → 962,368 ·
   `/pricing` 972,526 → 967,584 · `/` 945,612 → 940,986 · `/terms` 944,120 → 939,341 ·
   tool/auth routes unchanged (±13 bytes). All client chunks 2,877 → 2,830 KB raw.

Also: `jest.config.js` `testPathIgnorePatterns` for `e2e/` and `helpers/` no longer use `<rootDir>` —
on Windows a `\.` in the root path (worktrees under `.claude\`) is read as an escaped dot, so the
Playwright specs ran under Jest and the pre-commit gate failed in every worktree.

**Verification:** `npm run build` passes — 65 routes all `ƒ (Dynamic)` (only `/icon.png` and
`/sitemap.xml` static), `ƒ Proxy (Middleware)` listed; `npm test` 208 suites / 2,072 tests green;
`npx tsc --noEmit` and `npx eslint src` clean; backend `test_citation_consistency` +
`test_storage_claims` + `test_catalog_consistency` 57 passed.

**Commit SHA:** 391f1c14 (PR #211); 2026-10-27: 947825c2, aa6dfd8b, c740c5c7, 3c168aaa, 24a76f71 + this todo commit.

---

### Sprint 793: Both tax tools apply one fixed set of statutory limits to every year
**Status:** SPLIT — **793a COMPLETE** (the W-2 overrides the API never exposed), **793b PENDING**
(the year-keyed tables, which need practitioner-confirmed figures).
**Priority:** **P1** — the two tools that touch IRS filings produce materially wrong output for any
year whose figures differ from the hardcoded set, and both were documented and inventoried as
complete until the PR #184 review.
**Source:** PR #184 review, 2026-10-21. Two P1 findings, both verified against the code.

Both tools accept `tax_year` as a validated field (`ge=2000, le=2099`), pass it through to the
config, and then **never use it to select anything**.

#### W-2 / W-3 Reconciliation

`w2_reconciliation_engine.py:40-51` holds one block of constants, headed
`# --- 2026 reference values (caller override via Form941ComparisonConfig) ---`:

| Constant | Engine value |
|----------|--------------|
| `DEFAULT_SS_WAGE_BASE` | 176,100 |
| `DEFAULT_HSA_SELF_ONLY` / `_FAMILY` | 4,300 / 8,550 |
| `DEFAULT_401K_ELECTIVE_LIMIT` | 23,500 |
| `DEFAULT_SIMPLE_IRA_LIMIT` | 16,500 |

**Three layered problems, in increasing order of how verifiable they are:**

1. **The values do not match the year they are labelled.** The reviewer puts the 2026 figures at
   SS wage base 184,500, HSA 4,400 / 8,750, 401(k) 24,500, SIMPLE 17,000 — citing SSA and IRS
   — and identifies the engine's set as the **2025** figures. That matches my own understanding,
   but it is an external fact about current tax law and should be confirmed by a practitioner
   before the corrected numbers ship. **Sprint 781's CPA validation is the natural place.**
2. **The route exposes no override.** `tasks/archive/sprints-636-640-details.md` states "All
   thresholds are caller-overridable via `W2ReconciliationConfig`" — true at the engine layer and
   **unreachable through the API**: `grep` for `ss_wage_base|hsa_self_only_limit|elective_limit`
   in `routes/w2_reconciliation.py` returns **0**. A customer who knows the right number cannot
   supply it.
3. **This one needs no tax knowledge at all.** The tool accepts any year from 2000 to 2099 and
   applies one fixed set of limits to all of them. That is wrong independent of which year the
   constants represent, and it is the framing to build the fix around.

**Unaffected, and worth saying so:** the per-employee wage comparisons and the 941 reconciliation
compare the customer's own numbers to each other. Only the wage-base cap and the HSA / retirement
over-limit findings depend on the constants.

#### Form 1099 Preparation

`form_1099_engine.py:94-98` — `FORM_THRESHOLDS` is static: NEC 600, MISC 600, INT 10, applied to
any `tax_year` and not varied by sub-category.

The reviewer reports that for 2026 the §6041 / §6041A threshold for NEC and most MISC payments
rose to **$2,000** while royalties remain reportable at **$10**, citing the IRS 1099-MISC/NEC
instructions. Again consistent with my understanding — the 2025 reconciliation act raised the
information-return threshold effective for payments after 2025 — and again an external fact to
confirm before shipping numbers.

**The failure is bidirectional**, which is what makes it P1 rather than P2: vendors paid between
the old and new thresholds are listed as candidates when they are not reportable, **and** a
category whose threshold is *lower* than the flat rate is omitted entirely. A practitioner
filing from the candidate list would both over-report and under-report.

**Unaffected:** vendor aggregation, the corporate safe harbour, the processor exemption and the
data-quality report.

#### Scope

1. **Get the figures confirmed first.** Both sets are customer-facing tax amounts; neither should
   be changed on my reading of the law. Confirm with a practitioner, ideally inside Sprint 781.
2. Replace both constant blocks with a **year-keyed table** — `TAX_YEAR_LIMITS: dict[int, Limits]`
   — selected by the `tax_year` already being passed in.
3. **Decide and implement the unknown-year behaviour explicitly.** A year with no entry must not
   silently fall back to the nearest one. Preferred: return a skipped result naming the missing
   year, the same way the contract-aware and column-dependent tests already degrade. Silent
   fallback is how this defect would recur.
4. Expose the overrides the Sprint 636 record already promised, so a practitioner can correct a
   figure without waiting for a release.
5. Vary the 1099 thresholds **by sub-category**, not just by year — royalties are the case that
   proves a single per-form number is the wrong shape.
6. **A guard for the class:** no engine may hold a bare statutory constant without a year key. The
   broader version is a test that any module naming a tax year in a comment has a year-selected
   table rather than a flat constant.
   - [x] **Guard added 2026-10-27** — `tests/test_statutory_constants_year_keyed.py`. Discovers every
     backend module handling `tax_year` (the three engines + their routes) and AST-scans each
     `Decimal("<n>")` literal and module-level numeric constant: it must sit in (or be referenced by)
     a dict keyed by tax years, or be on an exact `(module, name, value)` allow-list with a reason;
     stale allow-list entries fail. **No figure changed.** The allow-list names the remaining flat
     statutory constants as debt: 1099 `FORM_THRESHOLDS` (tests only), `MISC_BOX_THRESHOLDS`
     (**unreferenced** — delete candidate), `LEGACY_GENERAL_THRESHOLD` (review-band floor) and
     book-to-tax `M3_THRESHOLD_TOTAL_ASSETS` ($10M, never year-keyed). Fail-before: a planted
     `PLANTED_SS_WAGE_BASE = Decimal("184500")` in the W-2 engine fails it. The narrower
     `test_no_table_claims_to_be_2026_until_sprint_793b` is unchanged.

**Acceptance bar:** a 2025 and a 2026 reconciliation of the same payroll produce different
wage-base findings; a year outside the table is reported as unsupported rather than computed; and
both `features/status.json` entries can honestly return to `complete`.

**Interim state shipped in #184, so the documentation does not overclaim while this is pending:**
both chapters carry an explicit caveat telling the reader to confirm the limits for their filing
year and naming what is and is not affected, and both `status.json` entries were downgraded from
`complete` to `partial`.

#### 793a — the overrides Sprint 636 promised and the API never exposed: COMPLETE

Scope item 4, and it needs no tax knowledge at all. `W2ReconciliationConfig` has carried a field
for every statutory limit since Sprint 636, whose record states *"All thresholds are
caller-overridable via `W2ReconciliationConfig`"*. True in the engine, and unreachable through the
API — `grep` for the limit fields in `routes/w2_reconciliation.py` returned **0**. A practitioner
who knew the correct figure for their filing year had no way to supply it.

New optional `statutory_limits` object on the request, covering all eleven engine limits as
decimal strings. **No default changes.** Only fields the caller actually sets are forwarded, so an
omitted field keeps the engine's dataclass default rather than being overwritten with `None` — a
naive `**model_dump()` would have nulled the other ten.

This is the escape hatch while 793b waits on confirmed figures: a practitioner can now correct the
wage base for their year per request instead of waiting for a release.

**Six tests, and they exist because of how the original claim failed.** A capability that is real
one layer down and absent at the layer a customer touches is this repo's recurring defect, so:

- the baseline (wages over the built-in base are flagged);
- an override **raises** the base and the finding disappears;
- an override **lowers** it and a finding appears, with `expected` echoing the supplied value —
  both directions, so the test cannot pass by the override being ignored in a way that happens to
  match;
- supplying one limit does not blank the other ten;
- a malformed override is a 400, not a 500;
- and a structural guard asserting **every** engine limit field is reachable from the request, so
  a new limit cannot reopen the same gap silently.

Regression-proved: against the pre-793a route, **four of the ten fail**, including the structural
guard.

#### A wider hole the PR #189 review surfaced through this sprint

`_to_decimal` only caught failures at **construction** — and `Decimal` accepts `"NaN"`, `"sNaN"`,
`"Infinity"` and `"-Infinity"` without raising. A syntactically valid non-finite value therefore
passed straight through to the engine and raised `InvalidOperation` on the first comparison or
quantisation: an uncaught **500**, from a helper whose entire purpose is to produce a 400.

The reviewer found it through the new overrides, but **the hole is in the helper and predates
them**. That three-line helper is copy-pasted into **nine route modules**, so every monetary
field on all nine was affected — `{"federal_wages": "NaN"}` would have 500'd long before this
sprint existed. The fix belongs in the helper, not the override loop.

Fixed in all nine. The five promoted routes came from reading the review; **the other four —
`account_risk_heatmap`, `depreciation`, `lease_accounting`, `loan_amortization` — were found by
the guard written alongside the fix**, on its first run. The review named five; there were nine.

`test_every_promoted_route_guards_non_finite_decimals` now fails if any module defining
`_to_decimal` lacks the finiteness check, so a tenth route copying the old helper reintroduces
nothing silently. Regression-proved against **`loan_amortization`** — deliberately one of the four
the reviewer did *not* name, rather than one of the five he did, which is the lesson from earlier
today applied instead of merely recorded.

Nine test cases: all four non-finite spellings rejected on an override **and** on a plain payroll
amount (the pre-existing half, which is why the fix sits in the helper), plus one asserting that
`1e30` — large but finite — is still accepted, so the guard rejects non-finite rather than big.

#### The inventory contradicted the API this sprint shipped

Second PR #189 finding, and squarely this session's theme: the 793a record in this file said the
overrides now exist while `features/status.json` still read *"The route exposes no override"* —
the canonical feature inventory directly contradicting the API, one commit after I corrected the
same file for a different reason. Updated, keeping `partial` for 793b and adding a verification
step that exercises the override path.

**Verification:** 20 passed in `test_w2_reconciliation_routes.py`; **full backend suite 9,013
passed / 0 failed** across all nine touched modules; `ruff` clean; OpenAPI drift
reported exactly the two intended additions (`StatutoryLimitOverrides` schema and the
`statutory_limits` field), snapshot regenerated — schemas 422 → 423, paths unchanged at 220.

**Deliberately not done here:** the year-keyed table. Its shape depends on how many years and
which values, and both are the practitioner's call. Shipping a table keyed to a year I cannot
verify would assert the tax fact this sprint explicitly declines to assert.

**Form 1099 deliberately gets no equivalent hatch, and the reason is sharper than "larger
change".** Mechanically it would be small — `prepare_1099s(config)` encloses the one
`FORM_THRESHOLDS[form_type]` read, so a `form_thresholds` config field is a three-line change.
The problem is that a **per-form** override cannot express the shape the thresholds actually have.

The PR #184 review's point was that for 2026 the §6041 threshold rose for NEC and most MISC
payments while **royalties remained reportable at $10** — a sub-category distinction inside a
single form. A practitioner handed a per-form knob would set MISC to the new figure, believe they
had corrected the tool, and silently stop reporting every royalty between $10 and that figure.

**That is worse than no hatch at all**, because it converts a known-wrong tool into one the user
believes is right. The W-2 limits have no equivalent trap — each is a single scalar with one
meaning — which is why the hatch is safe there and not here. Thresholds keyed by *year and
sub-category* are 793b's table work, and they need the confirmed figures regardless.

**Commit SHA:** `519f2b2b` (793a; PR #189, plus review fixes `103d7e5e` and `ba76100c`).

---

### Sprint 741c: Enum labels disagree between the Alembic chain and the ORM
**Status:** PENDING.
**Priority:** P1 — one instance is a live production defect; the rest is a schema-truth problem.
**Source:** PR #177 review + PR #174 review, 2026-10-21.

`Enum(PyEnum)` with no `values_callable` makes SQLAlchemy bind the **member name**. Some
migrations in the chain follow that and some do not, so the labels a database ends up with
depend on *how it was built*:


| Type | Migration labels | ORM binds | Agree? |
|------|------------------|-----------|--------|
| `usertier` (baseline `e2f21cb79a61`) | `FREE`, `PROFESSIONAL`, … | names | yes |
| `toolname` (baseline) | `TRIAL_BALANCE`, … | names | yes |
| `toolname` + flux (`f8a3d1c09b72`, Sprint 308) | `flux_analysis` | `FLUX_ANALYSIS` | **no — live defect** |
| `subscriptionstatus` (`d5e6f7a8b9c0`) | `active`, `past_due`, … | `ACTIVE`, … | **no** |
| `subscriptionstatus` + 4 (`f0a1b2c3d4e5`) | lowercase | uppercase | **no** |

**The live defect:** on any PostgreSQL database carrying Sprint 308's lowercase
`flux_analysis` label, a flux-analysis tool run **cannot be inserted** — the ORM sends
`FLUX_ANALYSIS`, which is not a label. `routes/audit_flux.py` does call the recorder, so
this is reachable today.

**Why production still works, and why that is the uncomfortable part.** The 22P02 that
Sprint 741a fixed proves production's `subscriptionstatus` does **not** contain the label
`active` — so production's labels are the *names*, which is what `create_all` produces, not
what the migration chain produces. Combined with the 42P01 on `dunning_episodes` (Sprint
741b), the evidence is that production's schema was built by `Base.metadata.create_all()`
and then stamped, so it agrees with the ORM and disagrees with its own migration history.

**Consequence worth stating plainly:** a database rebuilt from the documented Alembic chain
— a disaster-recovery restore, a fresh staging environment — would **not** match production,
and subscription writes through the ORM would fail on it. That makes this a restore-drill
blocker, so it belongs with Sprint 778.

**Scope (needs CEO ask D-1, a Neon read, before any change):**
1. Read `information_schema.enum_range` for `subscriptionstatus`, `toolname`, `usertier`,
   `billinginterval` and the billing-event types; record the actual labels.
2. Decide the canonical direction — almost certainly *names*, since that is what production
   has and what the ORM binds with no `values_callable` — and correct the migrations that
   disagree so a fresh chain build matches production.
3. Add the missing uppercase `FLUX_ANALYSIS` label (and any others) to the affected types.
4. ~~Add a test that compares every `sa.Enum(..., name=...)` label set in the migrations
   against the ORM's `.enums` for the same type.~~ **DONE — Sprint 741d.** It needed no database
   after all, being a comparison of two things already in the repo, so it was pulled forward
   ahead of steps 1-3. It confirmed every row above and found 15 more types besides.

   Steps 1-3 still need the Neon read. What 741d changes is that the list can no longer grow
   while that ask is outstanding, and that steps 1-3 now have a measured target instead of a
   hand-assembled one.

**Do not** "fix" this by adding `values_callable` to the models: that would flip every
binding to lowercase and break the current production database, which holds name labels.

---

### Sprint 786: Dependency currency (replaces Sprints 760 and 761)
**Status:** SPLIT — **786a COMPLETE** (venv reconciled, resolution now recorded in CI),
**786b step 2 COMPLETE** (the patch batch), **786b steps 3-4 PARTIAL** — merged: `stripe` 16,
`fastapi` 0.162, SQLAlchemy 2.1 + Alembic 1.20, `jest-dom` 7; `framer-motion` 14 in PR #269;
**`@types/node` 26 is not on `main`** (lockfile still resolves 22.20.5, though the note below calls it
done); **`typescript` 7 BLOCKED** until typescript-eslint supports it (see "typescript 6 → 7").
**Priority:** P2 — the only RED agent in the 2026-10-20 nightly, and 5 of the outdated packages are security-relevant.
**Source:** `reports/next-actions-2026-10-20.md` B-c / B-d. Supersedes Sprints 760 and 761, both written in April and now wrong in their specifics.

**Current drift (2026-10-20 nightly):** 68 backend / 22 frontend packages outdated. Security-relevant: `cryptography` 46.0.7 → 50.0.2 (major), `stripe` 15.0.1 → 16.0.0 (major), `fastapi` 0.136.0 → 0.150.0, `SQLAlchemy` 2.0.49 → 2.1.5, `react` 19.2.5 → 19.3.1.


**Read the numbers through Sprint 777's rule before acting.** `requirements.txt` splits deliberately: `==` for the framework/runtime surface, `>=` floors for the security leaves. The two halves need opposite treatment and the nightly does not distinguish them:
- **Floors self-heal.** `cryptography>=46.0.7` means CI and the production Docker build already resolve to 50.0.2 on every fresh install. There is nothing to bump — the finding is about the venv, not about production.
- **Exact pins cannot self-heal.** `fastapi==0.136.1`, `sqlalchemy==2.0.49`, `stripe==15.1.0` are genuinely what production runs, and each needs a reviewed bump.

**Sub-item that is not a version bump at all (B-d):** `backend/venv` matches neither `requirements.txt` nor production. It holds `fastapi` 0.136.0 and `stripe` 15.0.1 against pins of `==0.136.1` / `==15.1.0`, and sits at the literal floor values (`cryptography` 46.0.7, `pillow` 12.2.0, `pypdf` 6.10.2, `werkzeug` 3.1.8, `pyasn1` 0.6.3) that a fresh resolve passes. The nightly runs `backend/venv/Scripts/python.exe`, so **the daily health signal is measured against an environment that ships nowhere**, and `SESSION_STATE.md` wrongly calls it "the CI-representative env, with the new pins". Reconcile the venv to a fresh resolve and capture `pip freeze` as the evidence record — that recorded resolution is the missing half of Sprint 777's rule, which otherwise leaves "what actually shipped" unanswerable.

**Sequence:**
1. Reconcile `backend/venv` + record the resolution. Re-run the nightly afterwards so the RED is measured against something real.
2. Patches and safe minors in one batch, mirroring the 2026-04-19/22 hygiene pattern.
3. One major per commit, each with its own verification window: `cryptography` 50 (JWT signing, audit chain, password reset), `stripe` 16 (billing — pair with Sprint 780's webhook work), then the frontend majors (`typescript` 7, `framer-motion` 14, `@testing-library/jest-dom` 7) individually.
4. `fastapi` 0.150 and `SQLAlchemy` 2.1 are minor by version number but large by surface; treat each as a major for verification purposes.

**Verification per step:** `pip install -r backend/requirements.txt && pytest -q` clean; `npm install && npm run build && npm test` clean with every route still `ƒ (Dynamic)` and `ƒ Proxy (Middleware)` active; `pip-audit` clean; Render deploy logs show no new ImportError and `/health/ready` 200 with `status: "healthy"` within 60s.

**Out of scope:** the 21 dev-only npm advisories (need `npm audit fix --force`; all three CI audit gates pass `--omit=dev`, so they do not gate).

#### 786b — framer-motion 12 → 14

**`framer-motion` 12.43.0 → 14.8.0** (supersedes Dependabot #249 and #301, and PR #269's 14.7.1 — rebuilt on `main` 2026-11-14 because #269 had gone DIRTY). No source
changes needed; the package is still published as `framer-motion`, so the import stays.

**Breaking changes (CHANGELOG 13.0.0, 14.0.0) checked against usage:**
- **13.0 — optional `@emotion/is-prop-valid` dependency removed** (now opt-in via
  `<MotionConfig isValidProp>`). Not affected: it was never installed (only listed as an optional peer
  in the old lock entry), so 12.x was already using motion's built-in prop filter. Our 3
  `MotionConfig` uses pass only `reducedMotion="user"`. No unknown-prop warnings in the browser check.
- **14.0 — internal APIs restored in 13.5.1 removed** (`observeTimeline` etc.); `motion-dom` /
  `motion-utils` now exact-pinned. Not affected: nothing imports `motion-dom`, `motion-utils` or
  internals; all 127 import sites use the public surface (`motion`, `AnimatePresence`, `MotionConfig`,
  `useInView`, `useReducedMotion`, `useScroll`, `useTransform`, `useMotionValue`, `animate`,
  `Variants`/`Transition`/`MotionValue` types).
- **Not breaking but behaviour-relevant:** 14.2 runs independent transforms (`x`, `y`, `scale`)
  hardware-accelerated via WAAPI, and 14.x reworks `layoutId` (relative to `layoutRoot`). Observed:
  hero stat lines now animate as running WAAPI animations and settle to `opacity: 1; transform: none`.

**Lockfile audited by package:** exactly 3 entries changed, 0 added, 0 removed — `framer-motion`
14.8.0, `motion-dom` 14.8.0, `motion-utils` 14.7.0.

**Jest mocks:** the 81 per-file `jest.mock('framer-motion')` factories stub `motion`,
`AnimatePresence`, `useInView`, `useReducedMotion`, `useScroll`, `useTransform`,
`useMotionValueEvent`; every one is confirmed exported by the real 14.x module.

**Verification:** `tsc --noEmit` 0; eslint 0; **208 suites / 2,072 tests / 5 snapshots** pass;
`npm audit` 0; build passes with 65 `ƒ (Dynamic)` routes + `ƒ Proxy (Middleware)` (static: only
`icon.png`, `sitemap.xml`).

**By eye (Playwright against `npm start`, 12.43 baseline vs 14.7.1, same script — run for #269; 14.8.0 is a minor on top):** 10 public pages ×
{normal, reduced-motion}. Same console output on both (only the expected backend
`ERR_CONNECTION_REFUSED`, plus a React #418 hydration error on `/tools` and `/tools/trial-balance`
under reduced motion that **reproduces identically on 12.43**, so it predates this change). No
scroll-reveal content left below opacity 1 outside the hero film's intentionally hidden phases;
16 of 23 screenshots byte-identical, 4 more 0 px different, and 2 hero shots ~250 px different
(one stat line caught mid-stagger at the 2.5 s capture; settles to identical by 6 s). Hero scrubber steps show identical fully-visible text on both versions;
`/demo` `layoutId` tab indicator lands under all 5 tabs. **Not proven:** animation feel (easing,
spring, stagger timing) and the authenticated-only `layout` lists (adjustments, follow-ups,
toasts, file queue) — eyeball the Vercel preview.


**Re-verified at 14.8.0 (2026-11-14, main checkout):** `tsc --noEmit` 0; eslint 0; Jest **211 suites / 2,105 tests**;
`npm run build` passes with only `icon.png` + `sitemap.xml` static and `ƒ Proxy (Middleware)`.

#### 786b — fastapi 0.136 → 0.16x

`fastapi==0.136.1` → `==0.162.0` (step 4). Starlette stays 1.10.0; the only new transitive dep is
`opentelemetry-api` (FastAPI's native OTel, opt-in since 0.143 — nothing here enables it). Supersedes
Dependabot #261.

**What broke — one upstream change, two consequences.** 0.137 stopped copying an included router's
routes into the parent: `app.routes` now holds one `_IncludedRouter` node per `include_router` (54
nodes instead of 257 routes), and those nodes have no `path`/`methods`/`endpoint`.

1. **Production: the Sprint 840 default rate limit silently switched off.** slowapi's
   `SlowAPIMiddleware` finds the handler by iterating `app.routes` flat; on 0.162 it resolved *no*
   handler for any of the 183 static routes, treated each request as exempt, and
   `/benchmarks/industries` answered 61/61 requests with 200. Decorated routes were unaffected (their
   `@limiter.limit` checks itself). Fixed with `shared.rate_limits.DefaultLimitMiddleware`, a
   `SlowAPIMiddleware` subclass whose lookup uses `fastapi.routing.iter_route_contexts` (0.137.2,
   upstream's public replacement for iterating `router.routes`). One deliberate departure from slowapi:
   the *first* full match wins, as in Starlette dispatch — slowapi took the last, so
   `/clients/industries` was being limited as `/clients/{client_id}`.
2. **Tests: 133 failures in the 62 files that enumerate `app.routes`.** Fixed with one helper,
   `tests/helpers/route_inventory.py` (`all_routes()` / `api_routes()` over `iter_route_contexts`),
   and a mechanical `app.routes` → `all_routes(app)` rewrite. Several of those tests (e.g.
   `test_finding_comments`, `test_three_way_match` route checks) had no `else: fail`, so they would
   have passed vacuously on 0.162. New `tests/test_route_inventory.py` pins the helper to the OpenAPI
   document (inventory == documented operations, ≥240 routes, prefixed paths present), and
   `test_rate_limit_default.py` now checks every undecorated static route resolves to its own endpoint.

**Checked and not affected:** the full OpenAPI document is byte-identical between 0.136.1 and 0.162.0
(drift check clean, no snapshot regeneration); 0.155's removal of `**extra` on params (app imports);
0.147/0.162 bool-form defaults (the one `Optional[bool] = Form(default=None)` in `three_way_match`
behaves as on 0.136 again); 0.148–0.151 default/empty/null handling (no `Body()` params, no
parameter models); 0.136.3 underscore headers (no `Header()` params); 0.145/0.146 `FastAPI()` args
(not used); Sentry 2.73 already reads the 0.137+ effective route path; background tasks still run
before `yield`-dependency teardown (`test_promoted_tool_engagement_wiring`).

**Verification:** baseline on 0.136.1 **9,928 passed / 0 failed**; on 0.162.0 **9,932 passed / 0 failed** (+4 new tests). Before the test
fix, the 62 route-enumerating files gave 133 failures on 0.162.0.
Route inventory 257 before and after (253 path operations). `ruff check .` clean; mypy (non-test)
209 errors on both versions, identical output; `pip-audit` gate CLEAN; app boots and
`/health/ready` returns 200 `healthy` via `httpx.ASGITransport`.

#### 786b — SQLAlchemy 2.1 + Alembic 1.20

**Status:** PR open, not merged. `sqlalchemy` 2.0.49 → 2.1.6, `alembic` 1.18.4 → 1.20.1, one
commit each. Supersedes Dependabot #265.

**The hazard, reproduced rather than inferred:** under 2.1, `create_engine("postgresql://...")`
raises `ModuleNotFoundError: No module named 'psycopg'` — 2.1 moved the driverless default from
psycopg2 to psycopg 3, which is not installed. Production's Neon `DATABASE_URL` is driverless, so a
naive bump breaks the production DB while every SQLite test stays green. CI's PostgreSQL job sets a
driverless `TEST_DATABASE_URL` too, which is how #265 went red.

**Fix: `backend/db_url.py::normalize_database_url`** — `postgresql://` and `postgres://` become
`postgresql+psycopg2://` by scheme-prefix substitution only, so credentials, host and query params
(`sslmode`, `channel_binding`) pass through byte-for-byte. Applied once in `config.py`, so the app
engine, Alembic `env.py`, the Dockerfile's stamp-or-upgrade probe and the admin scripts all read
the same value; `env.py` re-applies it (idempotent) for callers that monkeypatch
`config.DATABASE_URL`; `tests/conftest.py` applies it to `TEST_DATABASE_URL`;
`dr-test-monthly.yml`'s smoke check applies it. psycopg 3 deliberately not adopted here.
`scripts/verify_backup_integrity.py` and the DR workflow's `psycopg2.connect` / `psql` calls take
libpq URLs and are correctly left alone. **Tests:** `tests/test_db_url_normalization.py` (19) —
plain, `postgres://`, explicit drivers unchanged, Neon-style query string + escaped password
preserved, and `engine.dialect.driver == "psycopg2"` for each, including `database.engine` built
in a subprocess from a driverless URL.

**2.1 typing fallout:** `Query`/`Row` tuples are now typed, which surfaced 5 latent mypy errors
(209 → 214 locally): `Decimal` passed to `float` fields in `routes/activity.py` (now explicit
`float()`, identical to Pydantic's lax coercion) and a nullable `BillingEvent.user_id` used as a
dict key in `billing/internal_metrics.py` (now filtered). Net mypy after: 206 (below the 209 starting point).

**Migration-guide review, against the code:** no `MappedAsDataclass`, `composite()`,
`exclude_properties`, `__declare_first__`, `@validates`, `decimal_return_scale`/`asdecimal`, or
`ext.asyncio` usage; `greenlet` (no longer installed by default) is not needed. Unchanged by 2.1
and covered by the suite: `Numeric(19,2)` Decimal round-trips, `use_alter` FKs, `create_all`,
SQLite `PRAGMA foreign_keys=ON` listeners, soft-delete guards. Autoflush-on-every-execution and
`Select.filter_by` ambiguity checks produced no failures.

**Alembic 1.18.4 → 1.20.1:** no `env.py` API change needed. Added `path_separator = os` to
`alembic.ini` — the 1.16+ key, whose absence emitted a `DeprecationWarning` on every Alembic run
(seen in `test_alembic_models_parity`). `alembic upgrade head` on a fresh SQLite DB is clean with
`-W error::DeprecationWarning`. Compared old stack (2.0.49 + 1.18.4) against new on fresh
databases: `alembic check` reports the **identical** pre-existing autogenerate drift (142 ops,
nullable/index differences already allow-listed by the parity test — not touched here), and the
migrated DDL differs only in the order of `FOREIGN KEY` clauses inside batch-recreated tables.

**Verification:** full backend suite on SQLite **9,947 passed / 0 failed** on 2.1.6 + 1.20.1, no
SQLAlchemy deprecation warnings; `pip-audit` gate CLEAN (69 packages); ruff clean. The PostgreSQL 15 path is verified by CI's `Backend Tests (PostgreSQL 15)` job only — no local
Postgres. **After merge: confirm on the Render deploy that `/health/ready` returns 200 with the
database dependency healthy** — the production URL path is the one thing no test here exercises
against the real host.

#### 786b step 3 — @types/node 26 shipped; jest-dom 7 is BLOCKED by an npm bug


**`@types/node` 25.6.0 → 26.6.5: done.** A major the canonical sequence does not list — it names
three frontend majors, `npm outdated` reports four. Type-only, so no runtime surface, and verified
on all three criteria anyway: `tsc --noEmit` exit 0, 207 suites / 2,036 tests / 5 snapshots, build
compiled with 64 dynamic page routes. The lockfile diff was audited rather than trusted: exactly
two entries moved, `@types/node` and its transitive `undici-types` 7.19.2 → 8.9.0.

**`@testing-library/jest-dom` 6.9.1 → 7.0.1: blocked, and not by a dependency conflict.**

Every install path crashes inside npm itself:

```
npm error Cannot read properties of null (reading 'edgesOut')
    at #loadPeerSet (@npmcli/arborist/lib/arborist/build-ideal-tree.js:1289:38)
```

Four approaches tried — `npm install --save-dev @testing-library/jest-dom@7`, a manual
`package.json` edit followed by `npm install`, `npm install --package-lock-only`, and clearing
`node_modules/.package-lock.json` first. All four crash in the same place: arborist's peer-set
loader, on npm 10.9.0 / Node 22.11.0.

**There is no real incompatibility.** jest-dom 7.0.1's peers are `vitest` (optional) and
`@testing-library/dom >=10 <11` (required). This project declares `@testing-library/dom ^10.4.1`
and has 10.4.1 installed, which satisfies it. Checked against the registry metadata rather than
inferred from the error.

**`--legacy-peer-deps` "works" and must not be used.** It completes, because it skips the code path
that crashes — and the resulting lockfile **drops 75 entries**, including `eslint` 9.39.4,
`webpack` 5.112.0, `terser` and the entire eslint plugin chain, because those existed only as
peer-derived entries. Audited by diffing the lockfile rather than by trusting the exit code; the
tree was reverted and rebuilt with `npm ci`, and `tsc` plus 2,036 tests confirm it is back to
baseline.

**What would unblock it**, in preference order:

1. **Upgrade npm.** This is a known arborist defect in the 10.x line, and the fix is not something
   this repository can carry. Needs a decision because it changes the toolchain on the dev machine
   and in CI (`setup-node` pins Node 22 but takes whatever npm ships with it).
2. Wait for a jest-dom release that restructures the peer set.

**Not forced.** A green `npm ci` on a lockfile missing eslint and webpack is exactly the kind of
false green this sprint has spent its time removing — CI would install from it happily and the lint
job would then fail for an unrelated-looking reason.

**Still pending in step 3** *(2026-10-27: typescript 7 tried and blocked by typescript-eslint;
framer-motion 14 is PR #269)*: `typescript` 7 and `framer-motion` 14 (12 → 14, two majors). Both are
independent of jest-dom, so the npm bug does not block them unless it proves to be general rather
than peer-set specific.

#### 786b step 3 — typescript 6 → 7: BLOCKED by typescript-eslint (not forced)

Tried 2026-10-27 on `typescript@7.0.2` (`latest`; 7.1 is still beta). **`tsc --noEmit` passes on
TS 7 with zero errors** — the codebase itself is ready. What blocks it is the toolchain:

- **ESLint cannot load.** `@typescript-eslint/eslint-plugin` 8.72.1 (latest; the 8.72.2 canary is the
  same) declares `typescript >=4.8.4 <6.1.0` and hard-throws `typescript-eslint does not support
  TS 7.0.` at import. TS 7 is the native port: `require('typescript')` exports only `version` /
  `versionMajorMinor` — there is no JS compiler API for typescript-eslint to call. Upstream tracks
  support for TS ≥ 7.1 in typescript-eslint#10940. `npm install` does not catch this (it only warns
  the peer is `invalid`), so a lockfile bump would look green until the lint job ran.
- **Everything else passes on TS 7.** `next build` (16.4.3) succeeds — 65 `ƒ` routes + `ƒ Proxy
  (Middleware)` — and its type-check step went 103 s → 2.2 s. That speed was checked rather than
  trusted: a deliberate `const x: number = "string"` probe fails the TS 7 build with TS2322, so Next
  really type-checks under TS 7. Jest (SWC, no `typescript` dependency) 208 suites / 2,072 tests.
  The lockfile also grew 39 entries — the native per-platform binaries plus duplicated nested
  typescript-eslint trees npm created because the peer range no longer resolves.

**Reverted, nothing committed.** `package.json`/lockfile are back on `typescript ^6.0.2` (6.0.3).

**What would unblock it**, in preference order:
1. Wait for typescript-eslint's TS 7.1 support (#10940), then bump both together.
2. Run side by side, as the TS 7 release notes suggest: keep the TS 6 JS API for the tools that
   need it (`"typescript": "npm:@typescript/typescript6@6.0.2"`, which typescript-eslint and Next
   resolve) and add TS 7 under another name for `tsc`. That is two compilers in the toolchain and
   a CI change — a decision, not a version bump.

`framer-motion` 14 is in PR #269, untouched here.

**Verification (2026-10-27, branch `sprint-817-786-cleanup`: Sprint 817 plus the reverted TS 7 trial):**
backend full suite **9,979 passed / 0 failed** (31 min serial); ruff clean on touched files. Frontend
on TS 6.0.3: `tsc --noEmit` 0, `eslint src --max-warnings 0` 0, Jest 208 suites / 2,072 tests,
`npm run build` 65 `ƒ (Dynamic)` routes + `ƒ Proxy (Middleware)` (static only `/icon.png`,
`/sitemap.xml`). *Local-only quirk:* in this `.claude\worktrees\…` path Jest's `<rootDir>`
ignore patterns break on Windows (the `\.claude` segment is mis-escaped), so plain `npm test`
also collects `e2e/` and `__tests__/helpers/` and reports 3 "failed" suites with 0 failed tests.
Runs were made with explicit `--testPathIgnorePatterns`. Not a repo defect: the main checkout and
Linux CI are unaffected.

#### 786b step 2 — the patch batch: COMPLETE

Five patch-level pins raised in one commit, as the sequence prescribes: `APScheduler` 3.11.3,
`pandas` 3.0.6, `psycopg2-binary` 2.9.13, `python-dotenv` 1.2.4, `slowapi` 0.1.10.

**Verification:** full backend suite **9,103 passed / 0 failed** (9,094 on the bumped versions,
plus the 4 register-guard and 5 bash-probe tests added below), with the sensitive areas run first
and separately — 135 tests across all seven `test_rate_limit_*` files plus
`test_cleanup_scheduler.py` (APScheduler) and `test_float_precision.py` (pandas). `pip-audit`
CLEAN across 71 packages, run through the Sprint 794b gate, which is its first real use.

**Warnings dropped 31 → 29.** `slowapi` 0.1.10 fixes `logger.warn` → `logger.warning`, which was
the deprecation `test_rate_limit_storage_outage.py` had been emitting on every run.

#### The nightly caught what CI could not — 14 failures, no bug in the code under test

The 2026-10-22 nightly went **RED with 14 new failures**, all in the two audit-gate suites from
Sprints 794a/794b. CI was green on both PRs, and the full suite passes locally. The failure set was
the diagnosis: **every test that spawns `bash` failed, and every test that does not spawn bash
passed** — including `test_the_gate_script_and_classifier_exist_and_are_wired_to_each_other`.

Two independent causes, both reproduced rather than inferred.

**1. `skipif(not shutil.which("bash"))` asks whether bash exists, not whether it works.**
This host carries two:

| Path | `bash -c "exit 0"` |
|------|--------------------|
| `C:\Program Files\Git\usr\bin\bash.exe` | returns **0** |
| `C:\Users\...\Local\Microsoft\WindowsApps\bash.exe` | returns **1** |

The second is the Store/WSL launcher, inert without a WSL distribution. `shutil.which` returns
whichever comes first on PATH, and the nightly cron's session orders PATH differently from an
interactive shell. So the skip guard passed and every invocation afterwards returned garbage.

**This is precisely the confusion the audit gates were written to fix.** A check that establishes
*presence* and reports it as *capability* — `which` answering is not the tool answering. The lesson
was written up three times today (778a, 794a, 741d) before being shipped as an instance of itself.

**2. A spawned Git Bash needs `Git\usr\bin` on PATH.** Under a minimal PATH the gate dies with
`dirname: command not found`, because `dirname` and `sed` live beside the binary rather than inside
it. **Invisible on Linux CI**, where coreutils are always present — which is exactly why five green
CI runs said nothing about this.

**The fix: `backend/tests/helpers/shell_support.py`.** `usable_bash()` probes candidates with
`bash -c "exit 0"` and returns the first that actually runs, searching PATH order and then known
Git-for-Windows locations; `bash_support_path()` hands the spawned shell the directories it needs
plus the directory of the interpreter pytest is running under, so the gate's own
`command -v python3 || command -v python` resolves to the same Python rather than to whatever the
ambient environment offers. The suites are now hermetic.

**Regression-proved against the nightly's actual conditions** — broken bash first on PATH, no Git
coreutils, no python on PATH: **60 pass**. The same command gave 12 failures with only fix 1 applied
and 14 in the nightly with neither.

**Plus 5 tests on the probe itself** (`backend/tests/test_shell_support.py`), including a stub
`bash` that exits 1 which it must reject, and a broken-bash-shadowing-a-working-one case. A probe
that silently stopped discriminating would restore the original bug while looking fixed — and the
probe is now the thing 14 tests depend on.

**Worth keeping in view:** the nightly found this and CI structurally could not, because the defect
lives in the difference between the two environments. That is an argument for reading the nightly
rather than treating a green CI as sufficient.

#### The one-character bump that falsified five documents

`slowapi` 0.1.9 → 0.1.10 is one character in `requirements.txt`. The version is **hardcoded in
five other places**, none of them mechanically tied to the pin, and three carry maintenance claims
that the bump falsifies:

| File | Said |
|------|------|
| `docs/compliance/DEPENDENCY_DECISIONS.md` | `Version: 0.1.9` · `Decision: Accept risk. Keep slowapi 0.1.9` |
| `backend/shared/rate_limits.py` | "slowapi (0.1.9) is unmaintained — last release Oct 2022" |
| `docs/runbooks/rate-limiter-modernization.md` | "Unmaintained (last release Oct 2022)" |
| `backend/tests/test_rate_limit_slowapi_health.py` | "slowapi (0.1.9) is unmaintained" |
| `docs/03-engineering/dependency-policy.md` | "why slowapi is pinned at 0.1.9" |

**Verified against PyPI's release history rather than taken from the comments:**
`0.1.7` 2022-11-28 · `0.1.8` 2023-04-07 · `0.1.9` 2024-02-05 · **`0.1.10` 2026-06-13**.

So "last release Oct 2022" was **already wrong by two releases when Sprint 444 wrote it**, and the
figure propagated into a runbook. More usefully: 0.1.10 shipped during this repository's dormancy,
after a two-year gap, and declares support through Python 3.13. **The "unmaintained" premise of the
accepted-risk decision is materially weaker than recorded** — not *responsive*, but not abandoned.
The register now says low-frequency, dates every claim, and keeps the structural argument (the
logic lives in `limits`, not in slowapi's ~200 lines of glue) as what the acceptance really rests
on. The migration plan is unchanged and still deferred.

#### A sixth location, found in review — and this one ran in production

The PR #195 review caught that the grep missed `shared/rate_limits.py`'s **runtime banner**.
`_emit_slowapi_unmaintained_warning()` logs on every module import — WARNING in production, INFO
elsewhere — and said:


So an on-call engineer paged anywhere near rate limiting was being told something false about the
dependency. Two tests **asserted** that wording, and the runbook's Operator Posture section quoted
it, which is three more places enforcing the claim.

**It was missed because the grep was for `0.1.9` and this message never names a version.** The
search was for the thing that changed rather than for the claim that changed — a version bump
falsifies *assertions about* the dependency, not just occurrences of its number.

Fixed across all four: the banner is renamed `_emit_slowapi_dependency_notice()`, says "maintained
at low frequency", points at the accepted-risk record, and **reads its version from
`importlib.metadata` rather than hardcoding a seventh copy**. The tests now assert the stable
prefix `"rate-limiter dependency notice"` instead of the maintenance claim — pinning the claim is
exactly what made two tests enforce a false statement for two years.

The live version and the historical cadence are deliberately kept separable in the wording: a
message reading *"slowapi 0.1.11 (0.1.10 released 2026-06-13)"* would glue a live value to a stale
one the moment upstream ships again.

**The notice is kept, not removed.** The accepted risk is real, just smaller than stated, and
operator visibility of an accepted risk is a deliberate control. Verified by capturing what it
actually emits, and regression-proved by breaking the prefix — two tests fail.

#### The guard, and the measurement that decided its scope

The obvious guard is "every version mentioned in prose must match its pin". **It was measured
before being written, and the numbers killed it:** across 938 files and the 13 exact pins there are
**54 disagreements, and every one inspected was a false positive** — a section heading
(`### 18.4 Stripe Webhook Re-Registration`), a CVSS score (`CVSS ≥ 7.0`), another package's floor
(`limits >= 3.0.0`). Version-shaped strings are simply common in prose, and a guard over that needs
one exclusion per false positive, which is how a check gets tuned until it checks nothing
(Sprint 794b).

`backend/tests/test_dependency_decision_versions.py` (4 tests) therefore covers the one place the
version is **structured data** rather than prose: the register's `- **Version:**` field. Zero
exclusions, and it is the claim carrying compliance weight — a signed-off risk acceptance naming a
version nobody runs is a decision nobody made. Regression-proved: reverting the register to 0.1.9
fails two tests.

**The four prose mentions were corrected by hand and are deliberately left unguarded.** Written
down in the test's docstring so the next reader sees a decision rather than an oversight.

**Not done here:** steps 3 and 4 — `alembic` 1.20, `fastapi` 0.159, `SQLAlchemy` 2.1, `reportlab` 5,
`stripe` 16. One per commit with its own verification window, per the sequence. Note also that the
sprint's deploy-verification criterion ("Render deploy logs show no new ImportError") **cannot be
checked from here** — there is no `RENDER_API_KEY` and no build marker on any endpoint. That half
of the verification is a CEO action, and it matters more for the majors than it did for patches.

**Commit SHA:** `e4f3c1cb` (786b step 2; PR #195), plus `494cf6d8` — the nightly's bash-probe fix —
and `508ee136`, the PR #195 review finding that the stale claim was also running in production.

#### 786b — stripe 15 → 16

`stripe==15.1.0` → `==16.0.1` (16.0.1 = 16.0.0 + Stripe's replaced CA bundle). The SDK now pins
API version **`2026-09-30.endive`** (15.1.0 pinned `2026-04-22.dahlia`). The code never sets
`stripe.api_version`, and **still doesn't, deliberately**: the SDK's types and its pinned version
move together, and pinning an older version under a newer SDK is what Stripe advises against.
Instead `tests/test_stripe_sdk_contract.py` asserts the pinned version, so the next major fails
there first and forces this review again.

**Every billing test mocks `stripe` with a `MagicMock`, so none could see an SDK change.** Reviewing
against the real installed SDK found three money-path defects — two of them already live on 15.x:

1. **Webhooks 500'd on stripe ≥ 15 (pre-existing, live).** stripe 15 (#1762) made `StripeObject`
   stop inheriting from `dict`; `.get()` now raises `AttributeError`. The webhook route calls
   `event.get("id")` on the `construct_event` result outside its try-block, so every genuinely signed
   event would 500; `Subscription.retrieve(...).get(...)` in checkout-completed and seat add/remove
   had the same defect, as did the Sprint 780 price-parity preflight (its `price.get(...)` → every
   price reported "could not retrieve"). Fix: `billing.stripe_client.to_plain_dict()` converts at
   the SDK boundary (route, 3 retrieves, preflight). No Sentry issue in 90 days — consistent with no
   real webhook traffic yet, not with the code working.
2. **Billing period stored as NULL (pre-existing since API basil, live).** `current_period_start/end`
   moved from Subscription to Subscription Item in `2025-03-31.basil`; the sync read only the
   top-level fields. Now reads top-level when present (older webhook-endpoint versions), else the
   base plan item. This also feeds the Sprint 790 upload-quota reset.
3. **Checkout would 400 on endive (new in 16).** endive removes `payment_method_types` from Checkout
   Session create; replaced with `allowed_payment_method_types: ["card"]` (keeps card-only in code,
   not in Dashboard settings).

Checked and unaffected: `Webhook.construct_event` signature, `stripe.error.SignatureVerificationError`
alias (still present, asserted), `Customer/Refund/Subscription/SubscriptionItem.modify/delete` (path
param already positional), `billing_portal.Session.create`, `SubscriptionItem.plan` (still on the
object), `Reversal` rename / `StripeObject.request()` removal (unused).

**CEO / Dashboard (in the PR body):** the webhook endpoint's API version is set in the Dashboard,
not by the SDK; payload handling now accepts both shapes, so upgrading the endpoint is optional but
recommended (Stripe's two-endpoint migration). Re-run `scripts/stripe_price_parity_preflight.py`
before cutover — it could not have passed on 15.x.

**Verification:** 16 new contract tests on the real SDK (offline, signed with a fake secret);
the webhook-accepts test was regression-proved against the old route (fails with AttributeError).
Billing subset 908 passed; full suite 9,944 passed, 0 failed; ruff clean on touched files; mypy 209 ≤
baseline 1011, none in touched files; pip-audit clean.

---

### Sprint 741: cleanup_scheduler real-root structural fix (post-Sprint-740 follow-up)
**Status:** SPLIT after the log read — **741a COMPLETE** (`reset_upload_quotas`), **741b PENDING** (`dunning_grace_period`, needs DB access).
**Priority:** P2 → P1 once Phase 4.1 lands.
**Source:** Sprint 732 / 740 (archived to [`tasks/archive/sprints-732-740-details.md`](archive/sprints-732-740-details.md)).

Sprint 740 unmasked the cascade — `psycopg2.errors.InFailedSqlTransaction` (SQLSTATE 25P02) was the visible symptom; the real first failure inside `cleanup_func(db)` was hidden behind it. After Sprint 740's deploy + 1h, pull `error_orig_fqn` from the next cleanup-cycle failure log. Expected leaf class: probably `psycopg2.errors.SerializationFailure`, `psycopg2.OperationalError` with pgcode `08006` (matches Sentry's SSLEOFError signal), or something genuinely surprising. **That class names the structural fix.**

**Pre-requisite:** Sprint 740 production deploy completed + at least one post-deploy cleanup cycle observed with the new field populated.

**Once root class is known, scope is:**
1. Fix the actual failing statement in the cleanup_func body for whichever job (`reset_upload_quotas`, `dunning_grace_period`, or both).
2. Add a regression test that reproduces the underlying root cause and asserts the cleanup cycle completes without raising.
3. Verify dunning escalation end-to-end on a staging-equivalent fixture once the cascade is fixed.

#### The log read: two bugs, not one

Render logs for `srv-d6ie9l56ubrc73c7eq2g` on 2026-10-20 show the scheduler failing **every
hour**, with two distinct and unrelated errors. Sprint 740 predicted a single root class;
there are two.

| Job | Error | pgcode | Meaning |
|-----|-------|--------|---------|
| `reset_upload_quotas` | `psycopg2.errors.InvalidTextRepresentation` | **22P02** | a literal cannot be cast to its column type |
| `dunning_grace_period` | `psycopg2.errors.UndefinedTable` | **42P01** | a relation in the query does not exist |

Sprint 740's `error_orig_fqn` field is what made this readable — the prediction was
`SerializationFailure` or an `OperationalError`, and it was neither.

#### 741a — `reset_upload_quotas`: COMPLETE

**Root cause, proven offline.** `Subscription.status` is mapped as `Enum(SubscriptionStatus)`
with **no `values_callable`**, so SQLAlchemy persists the enum *member name*. The Postgres
type `subscriptionstatus` therefore carries labels
`['ACTIVE', 'PAST_DUE', 'CANCELED', 'TRIALING', 'INCOMPLETE', 'INCOMPLETE_EXPIRED', 'UNPAID', 'PAUSED']`.
The job's raw SQL filtered `WHERE status = 'active'` — the lowercase `.value`, which is not a
label for that type. Postgres refused the cast: 22P02, hourly, since the job was written.

**This job had never once succeeded in production.** And
`uploads_used_current_period` is reset **nowhere else** — `shared/entitlement_checks.py:153`
holds the only increment and `:113` the only read for quota enforcement. So any subscriber
who reached their monthly upload cap would have stayed capped permanently. No realized
customer impact (there are no paying subscribers yet), which is precisely why it was worth
finding before there are.

**Why 8,728 passing tests missed it.** On SQLite the column is a VARCHAR with no type
constraint, so `WHERE status = 'active'` does not error — it matches **zero rows**, and the
job logs success with `records_processed: 0`. Same shape as the missing `ALTER TYPE`
migration in Sprint 787: when a constraint exists only in the production dialect, the dev
dialect cannot see the defect.

**The fix** binds the enum member through the ORM (`update(Subscription).where(Subscription.status
== SubscriptionStatus.ACTIVE, ...)`), so SQLAlchemy emits whatever representation the mapping
actually uses and the comparison cannot drift from the mapping again. Still one atomic UPDATE,
so the AUDIT-06 read-then-write race fix is unaffected.

**Also extracted** `reset_upload_quotas(db)` to module level, matching
`purge_expired_export_shares(db)` directly below it. The logic had been a closure inside the
job, reachable only through `_run_cleanup_job` — which opens its own session, takes a DB lock,
commits and rolls back. A test that patches all of that is testing the wrapper, not the query.

**Checked for the same bug elsewhere.** `grep` surfaced two more `WHERE status IN ('active',
'trialing')` in `billing/analytics.py` — both inside **docstrings** illustrating "Dashboard
SQL", with the real code using ORM-bound enum members. Not defects, verified by reading the
context rather than trusting the grep.

**Verification:** 9 tests. Behaviour tests rather than SQL-text assertions, so they fail on
the old implementation *under SQLite* — regression-proved by restoring the raw-SQL form: the
two reset-actually-happens tests failed, then passed on restore. One test pins the mapping
invariant (labels are member names) so a future `values_callable` change fails loudly, and one
guards the literal — after its own first draft flagged the function's docstring, which quotes
`WHERE status = 'active'` to explain the bug. It now strips the docstring via `ast`.

#### 741b — `dunning_grace_period`: PENDING, needs the Neon connection string

`process_grace_period_expirations` queries `dunning_episodes`, and production says 42P01:
that relation does not exist. But:

- the table's migration **is** in the chain — `591a_add_dunning_episodes`, reachable from head
  through the `a848ac91d39a` mergepoint;
- `alembic upgrade head` runs on every boot, and the 2026-10-20 startup logs show it applying
  **nothing** ("Context impl PostgresqlImpl", "Will assume transactional DDL", no "Running
  upgrade" lines).

So production's `alembic_version` already claims head while the schema lacks a table that a
chain migration would have created. That is a **stamped-but-not-applied** condition — most
likely the Phase 1 Neon cutover (2026-04-09) created the schema with
`Base.metadata.create_all()` and stamped head, and `dunning_model` was not in the imported
metadata at that moment.

**This cannot be fixed or even confirmed from here** — it needs a read of
`information_schema.tables` and `alembic_version` against Neon, which is CEO ask **D-1**. It
also raises the stakes on **Sprint 738**: that sprint treats the four orphan tables as P3
dormant debt, but if production is stamped ahead of its real schema then the same condition
may affect `password_reset_tokens`, `processed_webhook_events`, `tool_activities` and
`waitlist_signups` — and `waitlist_signups` is the table CEO ask **D-1** wants to count.

**Scope when unblocked:** compare `information_schema.tables` against `Base.metadata`, create
whatever is genuinely missing, and decide whether `alembic_version` needs correcting or the
missing objects need idempotent catch-up migrations (Sprint 738's outcome-1 path).

---

### Sprint 782: Lock in what has already been won
**Status:** SPLIT — **782a COMPLETE** (design-token gate), **782b PENDING** (external monitor, needs CEO signup).
**Priority:** P2 — cheap regression insurance on two hard-won zero states.
**Source:** `reports/launch-readiness-assessment-2026-10-19.md` §D, plus the lesson of the AS 1215 drift.

Two properties reached zero and have no guard, which is precisely how the citation error drifted back into docs after being fixed in code:

1. **Design system at 0 generic Tailwind colour tokens** (down from 150 across 777 files). Add a CI check rejecting any `slate-|gray|zinc|neutral|stone|blue|green|red|yellow|indigo|purple|pink|orange|teal|cyan|amber|lime|emerald|violet|fuchsia|rose|sky` + numeric-scale class in `frontend/src`, with an allowlist file if a genuine exception ever appears. The Oat & Obsidian mandate in `CLAUDE.md` carries an audit penalty for deviation; it should be mechanically enforced rather than discipline-dependent.
2. **External uptime monitor.** `uptime-check.yml` is live and CI-verified, but GitHub disables scheduled workflows after ~60 days idle — so it switches itself off during exactly the quiet period it guards. Stand up Better Stack / Healthchecks.io / UptimeRobot (free tiers are ample) against `/health/ready`, alerting on `status != "healthy"` and **not** merely on a non-200, since Sprint 774 deliberately reports `degraded` behind a 200. Also add the `RENDER_API_KEY` secret so the deploy-drift probe arms — the repo currently has no secrets at all.

#### 782a — design-token gate: COMPLETE

**Hard gate from day one.** `lint_engine_base_adoption.py` runs advisory because a
migration is outstanding; here there is nothing to migrate — the codebase is already at
zero across 777 files — so the lint exits 1 on any finding.

**Where it runs, and why not a new CI job.** `scripts/lint_design_tokens.py` plus
`backend/tests/test_design_token_lint.py`. The Backend Tests gate is already required on
`main` across Python 3.11, 3.12 and PostgreSQL 15, so wiring the check through a test
enforces it on every PR without touching `ci.yml`. The lint is pure stdlib and only reads
files, so it needs nothing from the backend runtime.

**Matching is syntax, not substring.** The pattern requires a colour **utility prefix**
(`bg-`, `text-`, `border-`, `ring-`, `from-`, `fill-`, …) optionally preceded by variant
prefixes (`hover:`, `dark:`, `md:`, `group-hover:`). So `text-blue-500` is a finding while
a comment mentioning `red-500`, a vendor named "Blue-500 Industries", a fixture asserting
`"sky-500"`, and `z-50` / `duration-500` / `leading-500` are not. Commented-out *classes*
are still findings — a bare palette word in prose is a note, `// className="bg-slate-800"`
is a class on its way back in.

**Error messages name the replacement**, because a gate that says "wrong" without saying
"use this" gets suppressed: `bg-red-500` → *use clay-\* (errors, expenses, abnormal
balances)*, `text-emerald-600` → *use sage-\**, `bg-slate-900` → *use obsidian-\**.
Semantic colour is explicitly not an exception — the palette already supplies `sage-*` for
success/income and `clay-*` for error/expense, so "but it's an error state" is not a reason
to reach for `red-500`.

**Allowlist** at `scripts/design_token_allowlist.txt`, `path:class` or bare `path`, ships
**empty** — and a test asserts it stays empty, so any entry has to argue for itself in
review rather than appearing quietly.

**A bug worth recording, found by its own unit tests.** The scale alternation was
`(?:50|[1-9]00|950)`. Regex alternation is leftmost-first, so against `bg-red-500` it
matched `50` and stopped — the file was still flagged, but the finding was *reported* as
`bg-red-50`, a class that does not exist. An error message naming a non-existent class
sends the reader hunting for the wrong thing. Fixed by ordering longest-first and asserting
a trailing boundary so `bg-blue-5000` cannot read as `bg-blue-500`. **The gate firing is
not the same as the gate being right.**

**Verification:** 39 tests, of which 12 pin the false-positive set and 14 the true
positives. Regression-proved end to end by injecting `bg-slate-800 text-blue-500` into a
real frontend file: exit 1, both classes named correctly with correct line number, then
exit 0 on restore.

#### 782b — external uptime monitor: PENDING, needs CEO

Unchanged and still blocked on a signup: stand up Better Stack / Healthchecks.io /
UptimeRobot against `/health/ready`, alerting on `status != "healthy"` in the **body**
rather than on a non-200, since Sprint 774 deliberately reports `degraded` behind a 200.
Plus the `RENDER_API_KEY` secret so the deploy-drift probe arms. The in-repo check cannot
substitute: GitHub disables scheduled workflows after ~60 days idle, so it switches itself
off during exactly the quiet period it guards.

---

