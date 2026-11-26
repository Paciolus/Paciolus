# Paciolus Development Roadmap

> **Protocol:** See [`tasks/PROTOCOL.md`](PROTOCOL.md) for lifecycle rules, post-sprint checklist, and archival thresholds.
>
> **Completed eras:** See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for all historical phase summaries.
>
> **Executive blockers:** See [`tasks/EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) for CEO/legal/security pending decisions.
>
> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md).

---

## Hotfixes

> Non-sprint commits that fix accuracy, typos, or copy issues without new features or architectural changes. One line per entry: `- [date] commit-sha: description (files touched)`.
>
> Pre-April 2026 entries archived to [`tasks/archive/hotfix-log-pre-april-2026.md`](archive/hotfix-log-pre-april-2026.md).

> Completed entries are archived (CEO 2026-11-25: this file lists pending items only): 2026-10-26 → 2026-11-25 in
> [`archive/hotfix-log-2026-10-to-2026-11.md`](archive/hotfix-log-2026-10-to-2026-11.md); older entries: [`archive/hotfix-log-2026-04-to-2026-10.md`](archive/hotfix-log-2026-04-to-2026-10.md).

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |
| `PeriodFileDropZone.tsx` deferred type migration | TODO open for 3+ consecutive audit cycles. Benign incomplete type migration, not a hack. Revisit when touching the upload surface for another reason. | Project-Auditor Audit 35 (2026-04-14) |
| `useTrialBalanceUpload` decomposition into composable hooks | Hook's state machine (progress indicator, recalc debounce, mapping-required preflight handoff) is tightly coupled to consumer semantics. Not a drop-in extraction — needs Playwright coverage of the mapping-required flow before a split is safe. | Refactor Pass 2026-04-20 |
| `routes/auth_routes.py` cookie/CSRF helper extraction | Module is already reasonably thin; cookie/token primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) are security-critical. Touching them without a specific bug or audit finding is net-negative. Revisit only if a follow-up auth/CSRF audit produces an actionable finding. | Refactor Pass 2026-04-20 |
| PDF fonts for Chinese, Japanese and Korean (lowest priority) | Sprint 885 (10G) embeds openly licensed fonts for Latin with accents, Greek and Cyrillic; other scripts print a visible replacement character with a note in the document. CJK fonts are large (10–20 MB each) and deferred by CEO decision 2026-11-18. | Sprint 885 / review OUT-25 |

---

## Refactor Intake

> Visible landing zone for new architectural-debt findings between
> initiatives. Surface via the advisory CI lints, the quarterly arch
> health review, or organic discovery during product work. Reviewed
> quarterly; items reaching critical mass (e.g., 5+ targeting the same
> surface) roll up into a sprint entry under `## Active Phase`.
>
> Same shape as the `## Deferred Items` table above — the discipline
> is that intake is visible and gets reviewed.

| Item | Reason | Source |
|------|--------|--------|
| Postgres enum-case drift (Alembic vs prod) | Production Postgres enum types store **uppercase** values (`FREE, SOLO, PROFESSIONAL, ENTERPRISE`); every Alembic migration in `backend/migrations/alembic/versions/` references **lowercase** literals. No user impact today (SQLAlchemy reads/writes consistently), but: (1) future migrations touching enum literals fail on prod with `22P02` (observed during 2026-04-22 CEO Phase 3 tier upgrade — `UPDATE users SET tier = 'enterprise'` was rejected); (2) `alembic upgrade head` against a fresh DB emits lowercase, so DR rebuild produces an enum shape the app can't populate; (3) same drift likely exists on every Postgres enum (`subscription_tier`, `userrole`, `subscriptionstatus`, etc.). Sprint scope when triggered: enumerate prod enums, decide canonical direction (`values_callable=[e.name]` vs `[e.value]`), one-shot reconciliation migration + rollback path, drift-guard pytest. Originally filed as PR #99 (closed — slot stale; Sprint 715 was actually used for SendGrid 403 investigation). | 2026-04-22 production tier-upgrade incident |
| ~22 engines awaiting per-tool relocation per ADR-018 | 10 relocated total (recon + flux + cutoff_risk + 7 testing engines AP/AR/FA/Inv/JE/Payroll/Revenue). Remaining are mostly calculators/indicators where ADR-018 says "default keep flat" — per-tool relocation justified only when reorganization adds clear value beyond a shim. | `lint_domain_relocation.py` (advisory CI) — count 22 |
| 16 route handlers still importing engine orchestration symbols | Engine relocations alone don't fix this. Each route needs a service-layer extraction (`services/audit/<tool>/service.py` with orchestrator + thin route delegate) per ADR-015. Heavier per-tool refactor work; pattern is established by Sprint 745 (`activity.py`) + Sprint 746 (auth services). | `lint_route_layer_purity.py` (advisory CI) — count 16 |
| 9 testing engines not subclassing `AuditEngineBase` | Pre-existing backlog from Sprint 726 | `lint_engine_base_adoption.py` (advisory CI) |

---

## Active Phase
> **▶ START HERE — LAUNCH 2026-12-15.** Rewritten 2026-11-15. The older plan blocks (2026-10-20 worklist, 2026-10-24
> claims review, 2026-10-27 security review, 2026-10-28 council action plan) are archived verbatim in
> [`archive/plans-2026-10-to-11.md`](archive/plans-2026-10-to-11.md); their CEO decisions still apply unless superseded here.
> Long sprint histories are in [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) and
> [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md) — this file lists **pending items only**
> (CEO 2026-11-25); everything completed is archived.
>
> **Standing decisions**
> - **Claims (CEO, 2026-11-14):** a claim we cannot prove from the code or a published document is removed, not
>   reworded. Guards: `test_marketing_claims.py` (site + app), `test_memo_banned_phrases.py` (PDFs), `test_storage_claims.py`.
> - **Launch scope (Q1):** Solo purchasable; Professional/Enterprise "Contact us" until Sprint 853.
> - **Legal entity:** Paciolus LLC. **Repository:** public until launch, then revisit (GitHub Team or a CI diet).
> - **Tax tables:** per-tax-year rule with an annual CEO sign-off (Sprint 860). "Independent assurance" is never claimed.
> - **Freeze:** no new refactor, dedup, perf or feature sprints until Sprint 781 reports or 30 days after Phase 3
>   completes, whichever first. Exempt: security defects, launch blockers, and any defect a CPA hits in a Sprint 781
>   session. Tracked risk: `slowapi==0.1.10` is unmaintained and sits on the rate-limit path (see Sprint 870).
>
> **P0 before 2026-12-15 — in order**
> - [ ] **Sprint 860** — PR #336 awaits the CEO's sign-off of the 2026 W-2 and 1099 figures (before 2026-12-15).
> - [ ] **Sprint 868 / Phase 4.3** — re-scope after 874 is live: what is left is browsers that block the third-party
>       refresh cookie (Safari). `api.paciolus.com` is also the Stripe webhook target.
> - [ ] **Phase 4.1 / Sprint 447** — Stripe live at Pricing v3, Solo only; one real-money checkout verified, then refunded.
>       Blocked on 4.3 (Sprint 871 is merged).
> - [ ] **Sprint 863** — Privacy/Terms redline (`counsel-redline-863`) merges only after counsel signs off.
> - [ ] **Sprint 893 G** — a fresh PostgreSQL builds from the migrations: needs the CEO's enum-label decision.
>
> **Post-merge checks on production (from merged sprints)**
> - [ ] Sprint 874: sign in, reload twice, idle 20 minutes, act — still signed in.
> - [ ] Sprint 867: the 2026-11-15 pre-closing TB shows a balanced balance sheet (current-period earnings in equity).
> - [ ] Sprint 859: the daily Render log line reads `tls=pooler-skip, sslmode=require`.
> - [ ] Sprints 897–899 (PR for branch `council-2026-11-25-remaining`): the Render steps under Sprint 897; a test-mode
>       checkout lands on `/checkout/success` and shows "Your new plan is active" only once the webhook has run.
>
> **Then (C)**
> - [ ] Sprint 869 JE calibration decision ("unusual account combinations" minimum — PR #322 note). Dependabot: eslint 10
>       (#298) is the one bump left out of the 2026-11-25 batch (a major).
> - [ ] Alarm for GitHub disabling scheduled workflows after 60 idle days (the other half of the PR #312 item; the
>       Nov 1 checklist covers it manually until then).
> - [ ] **Finding 2026-11-16 — the "E2E Smoke Tests (Playwright)" check has never run a test.** `SMOKE_USER` /
>       `SMOKE_PASS` are not set, so `ci.yml` skips the test step and the job reports success on every PR. Setting
>       them would not help: the job starts a fresh SQLite backend with no users. Recommendation: seed a throwaway
>       verified user inside the job (no secrets needed) and fail the job when the suite does not run. Not done
>       overnight — CI work, freeze status for the CEO to call.
> - [ ] Neon point-in-time restore drill (Sprint 778 remainder): the R2 restore drill passed 2026-11-14; a PITR restore
>       has not been drilled — only its 7-day window is checked.
> - Partial sprints parked by the freeze are listed below with their open items.
>
> **CEO asks**
> - [ ] **Sprint 781 demand validation:** the `waitlist_signups` count; unguided CPA sessions on their own TB; the
>       price question. Success: ≥1 Solo checkout paid by someone outside the CEO's network within 30 days of Stripe going live.
> - [ ] **Counsel package:** Terms + Privacy + Sprint 863 note (`reports/counsel-note-2026-11-14.md`). Decide: disclose
>       the 12-month backup retention, or shorten it so the draft DPA's 30-day deletion promise holds.
> - [ ] Confirm the four `R2_EXPORTS_*` env vars on Render (sharing now refuses rather than falling back to the database).
> - [ ] Refund policy · registered address / agent / EU-rep + DPO decisions · Stripe Billing Portal: no plan switching to
>       Professional/Enterprise (Sprint 858 note) · H12: verify or relabel the ISA 315 "Appendix 1 matrix" citation.
> - [ ] Sprint 876 PR note: completed and archived engagements stay writable after the completion gate passes once.
>       Recommendation: an `_ensure_mutable` guard with an explicit reopen transition.
> - [ ] Sprint 884 follow-up: should the TB response carry the currency conversion it computes (today it is dropped)?
> - [ ] Sprint 887: review the PR-T12/PR-T13 drafts and `reports/sprint-887-wording.md`; decide where `57c79d91` lives
>       and whether the anomaly summary gets a download button. Engineering follow-ups are listed under the sprint.
> Completed sprints: `tasks/archive/sprints-870-896-details.md` and `tasks/archive/todo-cleanup-2026-11-25.md`.

### Sprint 897: Launch operations (council 2026-11-25, Scout)
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] **CEO on Render after merge:** Settings → Health Checks → path `/health/live`; if `WEB_CONCURRENCY` is set in
      the service env, set it to `2`; confirm the live deploy SHA = `main`; decide on a second instance (cost).
- [ ] Load test: two parallel 100 MB uploads against the 2-worker, 2-parse-slot setting (O-2 follow-up).
- [ ] O-3: external monitor on `/health/ready` with a body match on `"status":"healthy"` (CEO: account); Sentry 5xx alert.
- [ ] O-5 (CEO: cost): Key Value with persistence + `noeviction`, or impersonation revocations in Postgres.

### Sprint 898: Sampling and ratio methodology (council 2026-11-25, Accounting Expert)
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] A-F1 follow-up (CEO/practitioner): take credits out of the population value, or a separate understatement stratum?
- [ ] A-F5 (CEO decision): is an uploaded TB always 12 months? If not, a period-length input and "not annualized" labels.

### Sprint 899: Checkout, claims and accessibility (council 2026-11-25, Designer + Compliance)
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] Counsel package: L-3 (rate-table rows kept 2 h), L-4 (security events kept unlinked), L-8 (GDPR Art. 12(3)).
- [ ] P3 later: G-04 (IP counter reset on own login), C-05, C-06, D-7…D-10.
- [ ] C-04 (P2, performance — needs the freeze lifted): TB and six routes do blocking DB work in `async def`.

### Sprint 871: Stripe dispute webhooks never find the customer (#273)
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] **CEO / needs Stripe test-mode access:** verify end to end in Stripe **test mode** (`stripe trigger charge.dispute.created`): account suspended + `DISPUTE_CREATED` recorded. Close #273.

### Sprint 895: Re-running a trial balance with new settings answered "duplicate"
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] **After merge:** on production, upload a TB, move the materiality slider → results update (no error); upload
      the identical file again → the new message and button.

### Sprint 873: Coverage observations listed as "Material Risks"
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] **After merge:** on production, a TB with a dominant revenue account shows the concentration row under
      Informational Notes, and the TB PDF shows "Materiality Coverage Analysis".

### Sprint 874: Every reload signs production users out — the CSRF rule on /auth/refresh cannot be satisfied
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] After deploy (CEO approved and merged 2026-11-24): sign in, reload twice, wait 20 minutes, act — still signed in.
      Then re-scope Sprint 868 to what remains (browsers that block the third-party refresh cookie, e.g. Safari).
- [ ] Related, not changed: `CORSMiddleware` is added first in `main.py`, so it sits inside `CSRFMiddleware` and CSRF
      403s carry no CORS headers — the browser reports them as network errors (how the PR #313 spinner presented).

### Sprint 875: Concurrent wrong passwords bypassed the 5-attempt lockout
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] Not in this PR (same review, Low): re-entering the current password on email change / password change / account
      delete has no attempt limit (`auth.py:667,727`, `auth_routes.py:570`); a revoked impersonation token can stay
      valid if a worker's first Redis probe fails (`shared/impersonation_revocation.py`); refresh-token chains have no
      absolute maximum and remember-me is lost after the first rotation (`auth.py:886`).

### Sprint 876: Industry-ratio evaluation could write to another client's engagement
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] **CEO decision (same review, Low):** completed and archived engagements stay writable — materiality edits,
      new misstatements / follow-up items / expectations, tool runs — after the completion gate passed once. Recommend an
      `_ensure_mutable(engagement)` guard on every child write and on non-status fields of `update_engagement`, with an
      explicit reopen transition. Changes workflow, so not done overnight.
- [ ] Notes from the same review: `shared/intercompany_resolver.py:80` looks up an engagement unscoped — no caller
      today; scope it before wiring it in. Workpaper index uses owner-only access while the ZIP export checks org-wide
      access first (fails closed) — fold into Sprint 853. Admins can mint admins via invites (`routes/organization.py:70`)
      — fold into Sprint 853 / L12.

### Sprint 863: Privacy Policy, Terms and Security Policy — counsel draft
**Status:** DRAFTED 2026-11-14 — awaiting CEO + counsel. **Priority:** P0 (legal pages before launch). **Owner:** C drafts; **CEO + counsel approve. Nothing merges without counsel sign-off.**

- [ ] Counsel signs off the redline (branch `counsel-redline-863`, PR marked do-not-merge; note for counsel:
      `reports/counsel-note-2026-11-14.md`); then merge. Full history in `archive/todo-cleanup-2026-11-25.md`.

**Review (2026-11-14):** redline on branch `counsel-redline-863` (Privacy + Terms only; **do not merge without
counsel sign-off**); note for counsel `reports/counsel-note-2026-11-14.md`. Two more items found while editing and
put to counsel rather than reworded: the Privacy Policy says Paciolus relies on SCCs for EEA transfers while the
Subprocessor List says transfer mechanisms are "being confirmed"; and the draft DPA §6 promises deletion "within 30
days" of termination, which the 12-month backup retention contradicts — **CEO decision: disclose 12 months, or
shorten backup retention.** DPA left unchanged pending that decision.

**Commit SHA:** TBD (redline merges only after sign-off).

### Sprint 884: Rounding, precision loss and totals that disagree with their detail
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] **Currency conversion never reaches the user.** `apply_currency_conversion` computes `currency_conversion`, but
      `TrialBalanceResponse` has no such field (`extra="ignore"` drops it) and no frontend code calls the currency
      memo route. Needs the CEO decision above; if yes, add the field (amounts via `ExactMoney`) and a screen/export.
- [ ] **Revenue memo "High-Risk Entries" can exceed 100% of revenue.** With no `total_revenue` in the payload, the
      memo takes its denominator from the first test detail carrying `total_revenue`/`gross_revenue` (sample:
      $9,860,237.81 = 144.1%). Decide the denominator (engine total revenue, gross vs net) and send it in the result.
- [ ] **Browser display above ~70 trillion.** The API sends exact digits, but a JavaScript number shows amounts above
      ~2^46 one cent off. Only if that range matters: send monetary fields as strings and format them in the frontend.

### Sprint 887: Generated wording states no audit conclusions, matches the results, cites correctly
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] Review the drafted PR-T12 / PR-T13 suggestions (12D) and the 163-row old/new procedure table
      (`reports/sprint-887-wording.md`).
- [ ] Decide on `57c79d91` (Sprint 886 sample regeneration, committed by another session onto this branch): leave it
      here, or move it onto `sprint-886-export-fidelity` (still at `61312c4e`) before 886 is pushed.
- [ ] Decide whether the anomaly summary gets a download button (today no page offers it; `fill_from_saved` is API-only).
**Open — engineering**
- [ ] Merge order 883 → 884 → 885 → 886 → 887, then push.
- [ ] On deploy: migration `c3e7a1f9d524` (`tool_runs.flag_count`) runs; runs recorded before it show "Results
      unavailable" — confirm the live deploy SHA and the migration head.
- [ ] Regenerate `sample-reports/` and the public JE sample memo (wording changed again).

### Sprint 888: What we publish about plans, billing and data handling matches the code
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] Terms and DPA promise deletion within 30 days of termination; no job does it (erasure is manual or self-serve).
- [ ] Confirm on Render: `S3_BUCKET_NAME` set (logos), `FORMAT_ODS_ENABLED` unset/false (copy now omits ODS), no
      `RATE_LIMIT_{STARTER,TEAM,ORGANIZATION}_*` variables (now ignored).
- [ ] Until `counsel-redline-863` merges, Privacy/Terms on this branch still say "up to 48 hours" and list bulk upload.

### Sprint 889: Tests that fail when a number or a rule is wrong
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] 14G PostgreSQL job runs `alembic upgrade head`; enum round-trip; schema parity; upgrade from existing rows.
**Open — CEO**
- [ ] 14G go-ahead: rebuild the migration chain (squashed baseline from the models) so a fresh PostgreSQL can be built.
- [ ] 14H: three upload E2E tests fail locally because the session does not survive a page load. Cause found by
      Sprint 874 (#327): `/auth/refresh` needs a CSRF token the page loses on reload — re-run after it deploys.

### Sprint 890: The edges between frontend, API and background work
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] 15D: multi-sheet files are not converted (only the single-sheet engine captures currencies). Wanted?
- [ ] 15C: engine strings are not uniformly formatted (M-3 `"0"`, intercompany copies input decimals).

### Sprint 892: Behaviour-neutral refactors (Excel reads, organization services, testing page shell, large units)
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] 17C one testing page shell (Fixed Assets and Inventory first).
      Done: `components/shared/testing/SingleFileTestingPage.tsx`; Fixed Assets moved (old vs new page HTML compared in
      six states — guest, unverified, idle, loading, error, success — identical).
      Done: Inventory moved (same six-state comparison, identical).
      Done in Sprint 893 (F): AP and Payroll moved (same comparison, identical).
      Remaining: JE and Revenue. Each differs from the shell visually (see Sprint 893 F), so moving either needs
      more shell options than it saves, or an approved restyle onto the theme tokens. AR aging stays outside the
      shell (two files).
- [ ] 17D split the largest units (one at a time).
      Order by recent changes (commits since 2026-10-01): sampling_memo_generator (13), population_profile_memo (9),
      payroll analysis (9), JE analysis (8), revenue analysis (7), audit/pipeline (6), ratio_engine (6).
      Done: `sampling_memo_generator` — Section I (Scope) and the method label out of `_generate_sampling_memo`
      (memo equivalence and output snapshots unchanged). Remaining: its sections II–Next Steps, then the next units.

### Sprint 893: Fixes for what Sprints 888–892 found
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] G. 14G: a fresh PostgreSQL builds from the migrations — **not started, needs the CEO.** It decides the enum
      labels a migration-built database gets (production holds the member NAMES `create_all` wrote; the old chain
      creates lowercase values), and a squash must reproduce the schema at production's revision, not at this
      stack's tip (886's `c3e7a1f9d524` has not deployed). Recommended: a baseline revision that reuses production's
      head id and creates that schema with production's labels, old files moved to `versions/_archive/`, then the
      PostgreSQL job (upgrade head, enum round trip, model parity). Nothing changes for production.

### Sprint 868: Sessions die every 15 minutes when the refresh cookie is not sent
**Status:** PENDING. **Priority:** P0 (before launch). **Owner:** C + CEO (DNS).
Seen 2026-11-15: in a browser that does not send the `paciolus-api.onrender.com` refresh cookie from
`paciolus.com` (third-party cookie), every reload signs the user out, and the session ends when the 15-minute access
token expires — mid-analysis ("Please sign in to run diagnostics"). The API on a separate site is the cause; Phase 4.3
(`api.paciolus.com`, first-party) is the fix. Re-test reload and 20-minute idle after the move. The spinner half of
this was fixed in PR #313.

### Sprint 869: JE Testing calibration and the entries count
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] **CEO decision — "Unusual account combinations" minimum population.** It flagged 52 of 58 entries on a small
      synthetic ledger; on 204 entries it flagged 2. The test runs once 20 entries have an entry ID
      (`unusual_combo_min_total_entries`, `services/audit/je_testing/analysis.py:166`) and flags pairings seen ≤ 2
      times. In a small ledger almost every pairing is rare, so the flag rate measures size, not risk.
      **Recommendation:** raise the minimum to 300 entries (the Benford convention already used in this tool),
- [ ] **After merge:** the public sample `/samples/paciolus-sample-je-testing-memo.pdf` (Sprint 865) still prints
      "Total Journal Entries Tested" — regenerate it the Sprint 865 way, and check `je-memo-proof-summary.png`.

### Sprint 856: First run, public-page accessibility, and one look in a browser
**Status:** PENDING. **Priority:** P1 (Phase 1 — before the first Sprint 781 CPA session). **Source:** 2026-10-28 council (Designer, Accounting Expert, Executor).

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 856).

### Sprint 860: Annual tax tables — fetched, tested, signed off once a year
**Status:** PENDING — scheduled 2026-11-14, target merge by 2026-11-21. **Priority:** P1 (launch gate — the W-2 and
1099 tools must not go dark on launch day). **Source:** CEO directive 2026-11-14; supersedes council Q6 and the
remainder of Sprint 793b. **Complexity:** 6/10 (2–3 days; the fetcher is the fiddly part). **Agents:** Executor
(build), Accounting Expert (figure map + invariants), Guardian (fail-closed gate), Critic (fetcher brittleness).

**Problem.** The W-2 tool holds one tax-year table (2025) and refuses every other year, so the first post-launch
season (2026 W-2s, due 2027-01-31) cannot run. The 1099 2026 table rests on secondary sources. Sprint 856 then
disables both tools after 2026-12-15 unless a practitioner confirms — a one-off date that recurs every year with
no process behind it.

**Design (CEO-approved 2026-11-14).**
- [ ] **One table file per tax year** (`backend/tax_tables/<year>.py`): every figure with its citation and source URL,
      plus a sign-off record (`signed_off_by`, `signed_off_on`, `sources_final: bool`). The W-2 and 1099 engines read
      from these files; the hard-coded `STATUTORY_LIMITS_BY_YEAR` / `THRESHOLDS_BY_TABLE_YEAR` blocks go away. 2025
      moves over unchanged.
- [ ] **Fetcher** (`scripts/tax_tables/fetch.py` + weekly scheduled workflow, Oct–Jan): reads SSA's wage-base
      announcement, the IRS retirement-limits notice, the HSA Rev. Proc. and the 1099-NEC/MISC/INT instructions;
      extracts each figure with the sentence it came from; opens a PR proposing the next year's table (value, prior
      year, source excerpt, URL). Fails loudly and names the document when a figure can't be read cleanly — never
      guesses. Draft IRS instructions are marked `draft`, so `sources_final` stays false until the final version.
- [ ] **Invariant tests** — the reviewer skims, the tests do the math: SS max tax = wage base × rate; age 60–63
      catch-ups = max(statutory floor, 150% of the regular catch-up); indexed limits never fall year over year;
      any move over ~10% is flagged; every figure has a citation; every table in use has a sign-off.
- [ ] **Per-year gate replaces the 2026-12-15 disable**: a tool refuses a tax year whose table is missing or unsigned,
      with an explicit code the frontend maps to "unavailable until this year's figures are signed off" (also closes
      the #308 Codex finding: `TAX_FIGURES_UNCONFIRMED` fell through to "Something went wrong" in
      `frontend/src/utils/transport.ts`). Cover the analysis and export error flows. Banners name the signed-off years.
- [ ] **Early warning**: CI warns from Nov 1 when next year's table is missing or unsigned; fails from Jan 1.
- [ ] **First run**: build the **2026** W-2 table and confirm the 2026 1099 table (incl. MISC box 10 attorney
      proceeds, now `needs_confirmation`) from primary sources. **CEO signs off before 2026-12-15.**
- [ ] Runbook `docs/runbooks/annual-tax-tables.md`: the yearly calendar (SSA mid-Oct, IRS limits ~Nov, HSA ~May,
      1099 instructions late in year), and the ~15-minute CEO sign-off steps.

**Out of scope:** Book-to-Tax, Depreciation and Loan apply no year-indexed figures (verified in Sprint 856).

**Commit SHA:** TBD.

### Sprint 834: Storage wording says what is stored; bulk upload no longer sold
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] **Counsel:** Terms of Service §5.3 ("Paciolus never stores … individual account numbers,
      descriptions, or balances"), the Terms tier table ("bulk upload" under Enterprise), the Privacy
      Policy commitment "We never store your financial data" and its "No database to breach" line.
      Not edited because they are versioned legal documents. Proposed replacement for §5.3: *"Paciolus
      never stores the files you upload or the line-level records in them (trial balance rows, journal
      entries, invoices, payments, payroll records). It stores aggregate results of each analysis, the
      names of accounts a tool flagged (without amounts), content you enter into an engagement
      (including materiality, analytical expectations and uncorrected misstatements), and report files
      you share by link for up to 48 hours."* Same facts for the Privacy commitment.

### Sprint 823: Seven of the eighteen tools have never been exercised against realistic input
**Status:** PARTIAL — discovery done 2026-10-23 (58 findings, 21 P1; register in `reports/sprint-823-discovery-2026-10-23.md`, merged in PR #205 `40044bc7`); remediation in Sprints 824–827. Generator registration (item 3) done 2026-10-27; item 5 is 10/11 (multi-period remains); the CEO usefulness judgement remains.
**Priority:** **P1 for discovery** — not a known defect, but the highest-yield unexamined
surface in the product. The full-spectrum review found three P1s in its first hour of doing
exactly this, on fewer than 70 synthetic accounts.
**Source:** `tasks/ceo-actions.md:65` + the coverage gap measured 2026-10-23.

Still open:
- [ ] Then the remaining eleven, which have generators but whose *application* was never
      exercised end-to-end either
      **10 of 11 done:** Sprint 829 (discovery round 2, PR #218 `106c5782`) drove JE, AP, payroll,
      revenue, AR, inventory, TB, bank rec and three-way match; statistical sampling was driven by
      823 itself (S1–S9). **Multi-period comparison was driven by neither** — it is the one left.
- [ ] **CEO, after the engineering half:** judge whether the output is professionally useful
      to a practitioner. That part is not mechanisable and is the half the action item was
      really asking for.

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 823).

### Sprint 826: Tax tools — 1099 rules, W-2 coverage, book-to-tax loss years
**Status:** PARTIAL — F0–F8, W3–W7, W10, B3–B5 merged 2026-10-23; W1/W2 done 2026-10-24; B1 and the remaining items below are open.
**Priority:** **P1** — F1–F3 change whether a 1099 is due; W2 flags a correct HSA contribution
HIGH with an excise-tax message.

Still open:
- [ ] F5, F9, B2, B5, B6. (B1 — NOL and valuation allowance — closed by Sprint 889 14F: CEO scope call 2026-11-20,
      a loss year states that no NOL asset or valuation allowance is computed.) (W4 W-3 vs 941, W8, W9 done in Sprint 855.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 826).

### Sprint 827: Fixed assets, intercompany, SoD, cash flow projector
**Status:** PARTIAL — A1–A3, A6, I1–I5, D1, D2 (part), C1, C4 merged 2026-10-23; open items listed below.
**Priority:** **P1** — A1 and I1 produce wrong output on correct input for every DDB register and
every IC revenue/expense pair.

Still open:
- [ ] Open (A4, A5, A8, C2, C3, C5, C6 and I5 done in Sprint 855): D2 (tiering; degenerate custom rules),
      I4's investment/payable pairing,
      P-3 (non-USD / EU number formats — needs a locale decision).

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 827).

### Sprint 814: Upload routes — one scaffold, gating in one place
**Status:** PARTIAL — items 1–4 fixed (each reproduced or measured first; item 1 had a third
case the review missed, item 2 a root cause in the shared parser). Item 5 (one scaffold) remains,
and belongs with Sprint 790.
**Priority:** **P1** — item 1 is a paywall gap; items 2–3 are live inconsistencies.
**Source:** Code health review 2026-10-23, routes + frontend passes.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 814).

### Sprint 815: Engine performance — parse once, prune pairs
**Status:** PARTIAL — items 1, 3, 4, 5 done with identical outputs; item 2 still blocked on CEO decision 2.
**Priority:** **P1** — a 100k-row GL takes up to 113s today.
**Source:** Code health review 2026-10-23, engines pass. Measured on synthetic data.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 815).

### Sprint 817: Dead-code sweep
**Status:** PARTIAL — items 1, 2, 5, 6 done (5 with two findings left for a product call, see
"Delivered 2026-10-27"); items 3–4 await CEO decisions.
**Priority:** P2 — ~7,000 lines with no runtime effect except bundle size and reader cost.
**Source:** Code health review 2026-10-23. Every item grep-verified repo-wide; re-grep before deleting.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 817).

### Sprint 818: Pricing has one source of truth
**Status:** PARTIAL — items 1–2 done; item 3 held for a CEO/counsel decision (see below).
**Priority:** P2 — the copies have already drifted.
**Source:** Code health review 2026-10-23, frontend pass.

Still open:
- [ ] Consolidate the "what we store / never store" lists (`trust/page.tsx:239-254` vs
      `approach/page.tsx:94-109`, worded differently) into one `content/` source — it is
      Zero-Storage compliance copy.

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 818).

### Sprint 819: Backend deduplication
**Status:** PARTIAL — items 3–10 done 2026-10-27 (branch `sprint-819-backend-dedup`, pending CI + merge); items 1 and 2 (result base classes, `.empty()`/`.from_flags()`) not started — see below.
**Priority:** P2.
**Source:** Code health review 2026-10-23, engines + routes + exports passes.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 819).

### Sprint 820: Frontend consolidation and bundle weight
**Status:** PARTIAL — items 2–7 done (3 and 5 earlier, 2/4/6/7 and the rest of 3 on 2026-10-27, branch `sprint-820-frontend-consolidation`, pending CI + merge); item 1 (`TestingToolPage` shell) not started — see below.
**Priority:** P2.
**Source:** Code health review 2026-10-23, frontend pass.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 820).

### Sprint 821: Database and event-loop efficiency
**Open items only** (2026-11-25 cleanup; full history in [`archive/todo-cleanup-2026-11-25.md`](archive/todo-cleanup-2026-11-25.md)).

- [ ] One Alembic migration dropping the 26 `primary_key=True, index=True` duplicate indexes and
      the single-column indexes covered by composites (`ToolActivity.user_id`, `TeamActivityLog.organization_id`).
      Mind Sprint 741c/797 chain-vs-ORM guards.
- [ ] Convert `RequestId`, `SecurityHeaders`, `Impersonation` middleware from `BaseHTTPMiddleware`
      to pure ASGI — **benchmark first**; impact unmeasured.

### Sprint 793: Both tax tools apply one fixed set of statutory limits to every year
**Status:** SPLIT — **793a COMPLETE** (the W-2 overrides the API never exposed), **793b PENDING**
(the year-keyed tables, which need practitioner-confirmed figures).
**Priority:** **P1** — the two tools that touch IRS filings produce materially wrong output for any
year whose figures differ from the hardcoded set, and both were documented and inventoried as
complete until the PR #184 review.
**Source:** PR #184 review, 2026-10-21. Two P1 findings, both verified against the code.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 793).

### Sprint 741c: Enum labels disagree between the Alembic chain and the ORM
**Status:** PENDING.
**Priority:** P1 — one instance is a live production defect; the rest is a schema-truth problem.
**Source:** PR #177 review + PR #174 review, 2026-10-21.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 741c).

### Sprint 786: Dependency currency (replaces Sprints 760 and 761)
**Status:** SPLIT — **786a COMPLETE** (venv reconciled, resolution now recorded in CI),
**786b step 2 COMPLETE** (the patch batch), **786b steps 3-4 PARTIAL** — merged: `stripe` 16,
`fastapi` 0.162, SQLAlchemy 2.1 + Alembic 1.20, `jest-dom` 7; `framer-motion` 14 in PR #269;
**`@types/node` 26 is not on `main`** (lockfile still resolves 22.20.5, though the note below calls it
done); **`typescript` 7 BLOCKED** until typescript-eslint supports it (see "typescript 6 → 7").
**Priority:** P2 — the only RED agent in the 2026-10-20 nightly, and 5 of the outdated packages are security-relevant.
**Source:** `reports/next-actions-2026-10-20.md` B-c / B-d. Supersedes Sprints 760 and 761, both written in April and now wrong in their specifics.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 786).

### Sprint 781: Demand validation (CEO-led, engineering-supported)
**Status:** PENDING — the gating item for all remaining product work.
**Priority:** P0 by expected value, even though it ships no code.
**Source:** `reports/launch-readiness-assessment-2026-10-19.md` §G.

No artifact in 770+ sprints records an unaffiliated practising CPA being asked whether they would pay $100–$1,000/mo. The nightly lead scout returns zero across five themes; Phase 3 is the CEO self-testing. This is the largest unvalidated assumption in the system, and with a soft launch date there is no reason to keep deferring it behind engineering work.

**Sequence:**
1. Read the `waitlist_signups` count. It decides whether outreach is warm or cold and is the single most informative number not currently in any report.
2. Get 5–10 practising CPAs through the marketing demo and then the free tier on **their own** trial balance. Watch where they stall; do not guide them.
3. Ask the price question directly and early.

**Engineering support:** none required up front — the demo path (`DemoZone.tsx`, `demoData.ts`) and the free tier (TB + flux, view-only, 10 uploads, 3 clients) already support exactly this motion.

**What it decides:** B-6 through B-9 (service-invoice two-way match, impairment screen, judgmental sampling, assertion-coverage worksheet) are currently ranked by internal priority scores, which are guesses about user behaviour. Five CPAs replace four guesses with observations. **Do not build any of the four until this sprint reports.**

---

### Sprint 782: Lock in what has already been won
**Status:** SPLIT — **782a COMPLETE** (design-token gate), **782b PENDING** (external monitor, needs CEO signup).
**Priority:** P2 — cheap regression insurance on two hard-won zero states.
**Source:** `reports/launch-readiness-assessment-2026-10-19.md` §D, plus the lesson of the AS 1215 drift.

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 782).
