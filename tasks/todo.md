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

- [2026-11-15] (this PR): tasks/ cleanup — `todo.md` restructured (old plan blocks, completed/superseded sprints and long sprint histories archived verbatim; every unchecked item kept; PR #312's two bugs carried in as Sprints 870/871), `lessons.md` replaced by standing rules (original archived), older hotfix entries archived, eight one-off `tasks/` reports archived, `WEBSITE_REVIEW.md` moved to `reports/`, `SESSION_STATE.md` brought current (tasks/, reports/, SESSION_STATE.md, CLAUDE.md, audit-journal.md)
- [2026-11-15] 016be822 (PR #313): signed-in pages spun forever when the session refresh failed at the network level — `AuthSessionContext` now clears the session so the page redirects to /login; regression test added. Found while trying to take Sprint 865 screenshots; production API was healthy (Render logs: 403, not 503) (frontend/src/contexts/AuthSessionContext.tsx, frontend/src/__tests__/AuthContext.test.tsx)
- [2026-11-14] 29cb4c29: website claims review — `reports/website-review-2026-11-14.md` written, CEO approved all 19 recommendations, Sprints 861–865 filed with a START HERE block; live-site check found `/security` and `/subprocessors` 404 and a public `/status` page with hard-coded "Passed" results. No site code changed (reports/website-review-2026-11-14.md, tasks/todo.md, tasks/ceo-actions.md)
- [2026-10-28] (this PR): 2026-10-28 action plan — 8-agent assessment → draft → council review and majority vote (7 questions, 21 of 23 amendments adopted); new START HERE block at the top of Active Phase, Sprints 854–858 filed, 843 merge gate and 778b checkout gate recorded, the "Stripe parked until pricing validated" line superseded, and the 2026-10-24 START HERE demoted. Live deploy verified at `1435b0e4`. No code changed (tasks/todo.md)
- [2026-10-27] (this PR): `/export/pdf` returned 500 when `risk_summary` or `column_detection` was sent as `null` (`.get(k, {})` yields `None` for a present-but-null key); now `or {}`. Found by the Sprint 819 snapshot work. Same pattern remains in 5 memo generators, left alone to avoid conflicting with PR #285 (pdf/sections/diagnostic.py, tests/test_export_diagnostics_routes.py)
- [2026-10-27] (this PR): `@testing-library/jest-dom` 6.9.1→7.0.1 (Dependabot #248) and `lint-staged` 16.4.0→17.6.0 (#252), both unblocked by upgrading the dev machine to Node 22.23.4 / npm 10.9.9 — the arborist `edgesOut` crash no longer reproduces, and lint-staged 17 needs Node ≥ 22.22.1. `npm audit fix` cleared 2 high (`brace-expansion` 1.1.14→1.1.21, `zod` 4.3.6→4.6.7); in-range patches for `@typescript-eslint/*` 8.72.1, `postcss` 8.5.32, `framer-motion` 12.43.0. Lockfile audited, not trusted: 0 added, 24 removed — all lint-staged 16's own terminal-UI deps (`listr2`, `log-update`, …), no peer-derived entries lost. Verified: build (all pages `ƒ`), 208 suites / 2,072 tests, `tsc`, eslint, 0 audit findings (frontend/package.json, frontend/package-lock.json)
- [2026-10-29] Restored from PR #254's pre-rebase tip `3cc6061e` (dropped by the 2026-10-28 restack, never on `main`): the four 2026-10-26 entries below, and the pooler-TLS finding re-filed as Sprint 859 (its number 847 was taken by the merged security sprint #276). The open-items-only cut of this file was not restored — the 2026-10-28 plan is built on the full file (tasks/todo.md)
- [2026-10-26] PR #255: Sentry PII opt-outs moved to explicit `dataCollection` (v11 drops `sendDefaultPii` and collects everything by default); Dependabot ignores `@types/node`/`typescript` majors and ungroups fastapi/sqlalchemy/alembic (frontend/sentry.*.config.ts, .github/dependabot.yml)
- [2026-10-26] Sprint 741b closed by log read: no `42P01`/missing-table error from the hourly cleanup jobs since 2026-10-24 (Render logs); `dunning_episodes` now exists via Sprint 797's `import_all_models`

> Older entries: [`archive/hotfix-log-2026-04-to-2026-10.md`](archive/hotfix-log-2026-04-to-2026-10.md).

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |
| `PeriodFileDropZone.tsx` deferred type migration | TODO open for 3+ consecutive audit cycles. Benign incomplete type migration, not a hack. Revisit when touching the upload surface for another reason. | Project-Auditor Audit 35 (2026-04-14) |
| `routes/billing.py::stripe_webhook` decomposition (signature-verify / dedup / error-mapping triad) | Already touched lightly in the 2026-04-20 refactor pass; full extraction pairs better with the deferred webhook-coverage sprint flagged in Sprint 676 review (handler is currently exercised by 6 route-test files but lacks unit coverage). Bundle both then. | Refactor Pass 2026-04-20 |
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
| `routes/billing.py::stripe_webhook` decomposition | Bundled with deferred webhook coverage sprint | `## Deferred Items` |

---

## Active Phase
> **▶ START HERE — LAUNCH 2026-12-15.** Rewritten 2026-11-15. The older plan blocks (2026-10-20 worklist, 2026-10-24
> claims review, 2026-10-27 security review, 2026-10-28 council action plan) are archived verbatim in
> [`archive/plans-2026-10-to-11.md`](archive/plans-2026-10-to-11.md); their CEO decisions still apply unless superseded here.
> Long sprint histories are in [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) — each
> open sprint below keeps its status and every unchecked item.
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
> - [ ] **Sprint 870** — rate limits never fire in production (#274). Security; do first.
> - [ ] **Sprint 868 / Phase 4.3** — `api.paciolus.com` (first-party API): sessions currently die every 15 minutes in
>       browsers that don't send the cross-site refresh cookie; it is also the Stripe webhook target.
> - [ ] **Sprint 867** — balance sheet shows "OUT OF BALANCE" for a balanced, pre-closing trial balance.
> - [ ] **Sprint 883** — preflight, TB analysis and the testing tools read amounts and totals rows differently, so one
>       file can balance in one place and not another (review ST-01, ST-02; ST-09 mapping 500s). Local branch.
> - [ ] **Sprint 884** — rounding, precision loss and totals that disagree with their detail (review TQ-12, TQ-13,
>       OUT-04/05/06/19/23). Local branch, stacked on Sprint 883 — merge 883 first, then push both. Follow-ups are
>       listed under the sprint.
> - [ ] **Sprint 885** — exported CSV/Excel/PDF files: formula injection, PDF restyling, non-ASCII download names,
>       fonts and page fit (review OUT-01/02/24–28/33/34). Local branch, stacked on Sprint 884.
> - [ ] **Sprint 871** — Stripe dispute webhooks never find the customer (#273). Gates Sprint 447.
> - [ ] **Sprint 860** — annual tax tables, fetcher, invariant tests; CEO signs off the 2026 W-2 and 1099 tables.
> - [ ] **Phase 4.1 / Sprint 447** — Stripe live at Pricing v3, Solo only; one real-money checkout verified, then refunded.
>       Blocked on 4.3 and 871.
> - [ ] **Sprint 863** — Privacy/Terms redline (`counsel-redline-863`) merges only after counsel signs off.
>
> **Then (C)**
> - [ ] Sprint 869 (JE calibration) · Sprint 859 (pooler-aware TLS check) · Dependabot batch (open: #297–#306, #311).
> - [ ] **Next.js upgrade** — `next build` compiles but exits 1 on alternate runs with Next's `SecurityFatalError`
>       ("your version of Next.js is affected by a known security vulnerability"). Security; seen in Sprint 884.
> - [ ] Runbook: credentials inventory in `docs/runbooks/backup-restore.md` (names, scope, where created, expiry —
>       never values) + one yearly **Nov 1** rotation/sign-off day shared with Sprint 860 + an alarm for GitHub
>       disabling scheduled workflows after 60 idle days. (Carried from PR #312.)
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
> - [ ] Sprint 853 (firm-owned client data) is blocked on a CEO decision.
> - [ ] Sprint 884 follow-up: should the TB response carry the currency conversion it computes (today it is dropped)?

### Sprint 870: Rate limits never fire in production (#274)
**Status:** PENDING — filed 2026-11-14 as "Sprint 861" in PR #312; renumbered 2026-11-15 because 861 was used for the
website claims sprint on `main`. **Priority:** P0 security (freeze-exempt). **Source:** issue #274 (2026-10-27).
**Agents:** Guardian (lead), Executor, Critic.

Production has returned **zero 429s since 2026-10-01**: 80 requests in 3 s to an undecorated route all got 200. The
same commit run locally returns 60 × 200 then 429s, so the code works and the production environment differs. Every
limit is affected — login, password reset, export-share passcode brute-force (Sprints 697/698), uploads — because
they share the key function and storage.

- [ ] **Diagnose on production first, don't guess.** Hypotheses from #274, in order:
      (1) rate-limit **key**: `security_middleware.get_client_ip` trusts `X-Forwarded-For` only from `TRUSTED_PROXY_IPS`;
      behind Cloudflare + Render the peer may differ per request, so every request gets its own bucket;
      (2) **Redis counters** on Render Key Value `paciolus-ratelimit` not written/read — inspect `LIMITS:` keys + TTLs during a burst;
      (3) gunicorn's 4 workers silently falling back to per-worker memory.
- [ ] Fix the cause; keep the Sprint 774 `degrade` storage-failure policy intact.
- [ ] Regression test for the identified cause (e.g. proxied requests from one client share a bucket).
- [ ] **Verify on production:** a burst on an undecorated public route returns 429 after 60, and Render logs show the 429s. Close #274.

**Commit SHA:** TBD.

### Sprint 871: Stripe dispute webhooks never find the customer (#273)
**Status:** PENDING — filed 2026-11-14 as "Sprint 862" in PR #312; renumbered 2026-11-15. **Priority:** P1 — **gates
Sprint 447** (live Stripe). **Source:** issue #273 (found in the Stripe 15 → 16 upgrade, #272). **Agents:** Executor
(lead), Guardian, Accounting Expert (dispute policy).

`handle_dispute_created` / `handle_dispute_closed` (`backend/billing/webhook_handler.py`) read `customer` off the Dispute
(Stripe's Dispute object has none) and fall back to `charge` only when it is an expanded dict (webhooks send a `ch_…`
string). Both log `could not resolve customer_id` and return on every real dispute, so the AUDIT-08-F5 policy is never
enforced: no suspension on open, no restore/cancel on close, no `DISPUTE_*` billing events.

- [ ] Resolve the customer from `dispute["charge"]` (or `payment_intent`) via the SDK client wrapper + `to_plain_dict()` (#272); keep the expanded-dict branch.
- [ ] A failed Stripe lookup returns non-2xx so Stripe redelivers — never a silent drop.
- [ ] Fix test fixtures to Stripe's real dispute shape (no `customer`, `charge` as a string) + a contract test in
      `test_stripe_sdk_contract.py` built from a real `stripe.Dispute`.
- [ ] Verify end to end in Stripe **test mode** (`stripe trigger charge.dispute.created`): account suspended + `DISPUTE_CREATED` recorded. Close #273.

**Commit SHA:** TBD.

### Sprint 863: Privacy Policy, Terms and Security Policy — counsel draft
**Status:** DRAFTED 2026-11-14 — awaiting CEO + counsel. **Priority:** P0 (legal pages before launch). **Owner:** C drafts; **CEO + counsel approve. Nothing merges without counsel sign-off.**

- [x] Redline (branch + PR marked do-not-merge) covering: "not written to disk" (`privacy/page.tsx:340, 373`;
      `SECURITY_POLICY.md:27`); flat "48 hours" → 24 h Professional / 48 h Enterprise (`privacy:230, 373, 420`;
      `terms:429`); "encrypted" for shared reports; summary retention (archived after 365 days, removed on account
      deletion; "Clear history" hides); preview-cache scope; flagged account names may include a person's name.
- [x] Also found during Sprint 861: Privacy security list says "TLS 1.2 or higher (1.3 where supported)" — not
      provable from code (`privacy/page.tsx:551`); Privacy says the upload is "released" "when the response
      completes" (`:352`); Terms says "Uploaded files were never kept" (`terms/page.tsx:871`).
- [x] Also found during Sprint 862: Privacy says deleting your account "removes" summaries — backups keep copies up
      to 12 months; Privacy lists Vercel as "United States (Virginia)" while the Subprocessor List (correctly) says
      "United States / global edge"; Privacy's subprocessor table lacks GitHub and the backup bucket; Security Policy
      3.1's factual edits (made so the published page is accurate) need counsel's read.
- [x] One-page note for counsel listing each change and the code fact behind it.
- [x] CEO action logged in `tasks/ceo-actions.md`.

**Review (2026-11-14):** redline on branch `counsel-redline-863` (Privacy + Terms only; **do not merge without
counsel sign-off**); note for counsel `reports/counsel-note-2026-11-14.md`. Two more items found while editing and
put to counsel rather than reworded: the Privacy Policy says Paciolus relies on SCCs for EEA transfers while the
Subprocessor List says transfer mechanisms are "being confirmed"; and the draft DPA §6 promises deletion "within 30
days" of termination, which the 12-month backup retention contradicts — **CEO decision: disclose 12 months, or
shorten backup retention.** DPA left unchanged pending that decision.

**Commit SHA:** TBD (redline merges only after sign-off).

### Sprint 867: Balance sheet out of balance for a balanced, pre-closing trial balance
**Status:** PENDING. **Priority:** P0 (before launch — auditors upload pre-closing TBs). **Owner:** C.
Reproduced 2026-11-15 on production with a balanced synthetic TB (debits = credits = $1,253,800.25): Financial
Statements shows "OUT OF BALANCE by -$4,699.50" and blames "a mapping or sign issue". -$4,699.50 is the period's net
income, which the balance sheet leaves out of equity; the Key Metrics panel on the same page already says "Equity
includes -$4,699.50 of unclosed current-period earnings". Fix: present current-period earnings in equity on the
balance sheet (and the Excel/PDF exports); test with a pre-closing TB.

### Sprint 883: One amount policy and one totals-row rule across preflight, TB analysis and testing tools
**Status:** IN REVIEW (2026-11-18) — code complete on local branch `sprint-883-amount-parsing` off `main` `ef5e5676`;
not pushed. Frontend build/Jest not run (no frontend file changed; the run was stopped by the machine for low memory).
**Priority:** P0 (High findings: the same file can balance in preflight and not in analysis). **Source:** read-only
review at `ef5e567` (ST-01, ST-02, ST-09). **Agents:** Executor, Critic.
**Decided (CEO, 2026-11-18):** "$(2,000.00)" = −2000, "1,234.56-" = −1234.56, "€1,234.56" = 1234.56, "Infinity" and
"NaN" are invalid, never numbers. Locale support no wider than that.
- [x] **8A / ST-01 — one amount policy.** `shared/parsing_helpers.parse_amount` (blank → 0; invalid → 0 by default or
      `InvalidAmountError` with `on_invalid="error"`); `safe_decimal` is built on it. Preflight (`_coerce_to_decimal`
      removed), intake (`_to_decimal` removed), the streaming auditor and the legacy `audit/ingestion.py` call it;
      `pd.to_numeric` is gone from the TB path. Reproduced first: 42 failures in `test_amount_parsing_policy.py`
      (one table × 7 paths). Also found: "Infinity" crashed the streaming auditor (`InvalidOperation`) and "NaN"
      crashed preflight; preflight read "€ 1.234,56" as 1.23456.
      **Other results that changed (before → after):** `safe_decimal`: "--5" −5→0, "1 234.56" 1234.56→0, "45%" 45→0,
      "£1,234.56" 0→1234.56, `Decimal("Infinity")` Infinity→0. All paths: "1,2,3" 123→0. `safe_decimal` + preflight:
      "1_000" 1000→0, Arabic-Indic digits "١٢٣" 123→0. Preflight: "€ 1.234,56" 1.23456→0, "(1,234.56)-" and
      "-(1,234.56)" 0→−1234.56. Streaming: "($2,000.00)", "-$2,000.00", "$-2,000.00" 0→−2000.
      Verified on the 8A tree: backend full suite 10,887 passed; 1 failure is the pre-existing
      `test_sprint819_route_snapshots.py::test_engagement_export_routes_unchanged` (fails on `main` too).
- [x] **8B / ST-02 — one totals-row rule.** `shared/intake_utils.py` owns it: `is_totals_row_candidate` (every
      account-identifier column blank, debit and credit both non-zero), `TOTALS_ROW_WINDOW` = 3 and
      `select_totals_row` (the last candidate among the file's last three rows); `detect_totals_row` (preflight) is
      built from them. The streaming auditor no longer zeroes every blank-account two-sided row in every chunk: it
      holds back only candidate rows until three more rows have arrived, and `finish_ingestion()` (called by both
      pipelines, and by `get_balance_result` / the `account_balances` property) applies intake's choice. The excluded
      row reaches none of: balance totals, account aggregation, `missing_names_count`, `missing_balances_count`
      (the old code counted the zeroed totals row as a zero-balance row). `row_count` stays rows submitted, with
      `totals_rows_excluded` beside it. Reproduced first: 34 of 39 cases in `test_totals_row_agreement.py` failed
      (same file through preflight's parser and the chunked reader at chunk sizes 1, 2, 3, 4, 1000: totals shape at
      the start kept, at the end dropped, mid-file on a chunk boundary kept, blank name with a code kept, a genuine
      two-sided account kept, only the last of two candidates dropped; plus the pipeline entry point).
      **Found on the way (pre-existing, pandas 3):** `astype(str)` now keeps a missing cell as NA, not "nan", so the
      streaming auditor's blank test never matched a CSV blank — the old totals exclusion and `missing_names_count`
      were dead for CSV input. Blank detection fixed. **Not changed, needs a decision:** rows whose account cell is
      blank are still left out of `account_balances` (pandas drops NA group keys) although they count in the balance
      totals; before pandas 3 they were grouped under an account literally named "nan".
      Verified on the 8B tree: backend full suite 10,933 passed; only failures are the pre-existing Sprint 819
      snapshot test and the not-yet-implemented 8C tests.
- [x] **8C / ST-09 — mapping JSON of the wrong shape is one 400.** `shared/helpers.parse_json_mapping` accepts only
      a JSON object whose values are strings; anything else supplied (`[]`, `null`, `"text"`, `{"a": 1}`, malformed
      JSON) is a 400 "Invalid <field>: expected a JSON object whose keys and values are strings." Not supplied stays
      `None`. Malformed JSON used to be silently treated as "no mapping" (the run went ahead on auto-detected
      columns); it is now the same 400. `parse_json_list` gets the same treatment, with `item_type=str` for
      `selected_sheets` (TB) and `stratify_by` (JE sample + preview). Callers name their field (bank rec
      `bank_/ledger_column_mapping`, AR aging `tb_/sl_column_mapping`). Reproduced first: 79 of 86 tests in
      `test_json_form_parsing.py` fail on the old helper (500s over HTTP at all nine callers: TB, AP via
      `testing_route`, JE, JE sample, JE preview, bank rec, AR aging, sampling design, sampling evaluate).
      `test_refactor_2026_04_20.py` asserted the old "malformed → None" contract; now asserts "not supplied → None".
      **Not changed (outside the listed callers):** `routes/audit_pipeline.py` parses `account_type_overrides` with
      its own `json.loads` + `len(...)`, so `"5"` there is still a 500.
      Verified on the final tree: backend full suite 11,012 passed; 1 failure, the pre-existing Sprint 819 snapshot
      test. mypy (CI command): 212 errors, the same set as `main` (baseline 1,011).

**Commits:** `dc934594` (8A, ST-01), `346d291d` (8B, ST-02), `fa03cd73` (8C, ST-09); this record + lessons.
**Open for the CEO:** (1) blank-account rows are counted in the balance totals but left out of `account_balances`
(8B note) — group them under one "(blank account)" line, or exclude them from the totals too? (2) the
`account_type_overrides` 500 (8C note) — fold into this sprint or file separately.

### Sprint 884: Rounding, precision loss and totals that disagree with their detail
**Status:** IN REVIEW (2026-11-18) — code complete on local branch `sprint-884-rounding-totals`, stacked on Sprint 883
(`f5215465`); not pushed. Backend full suite 11,095 passed; 1 failure, the pre-existing Sprint 819 engagement
snapshot (fails on `main`). Frontend: Jest 212 suites / 2,107 passed; `next build` compiles all 70 routes, but exits 1
on alternate runs on Next.js's own security-advisory gate ("SecurityFatalError … retry"), on this tree and on the
unchanged one; no frontend file changed. A Next.js upgrade is the fix; not done here. **Priority:** P0 (three Critical findings: a total that is not the sum of the rows printed above it).
**Source:** read-only review at `ef5e567` (TQ-12, TQ-13, OUT-04, OUT-05, OUT-06, OUT-19, OUT-23). **Agents:** Executor, Critic.
**Decided (CEO, 2026-11-18):** one rounding rule — half-up to cents (`shared/monetary.py`); a total shown beneath
detail is computed from the detail as displayed.
- [x] **9A / TQ-13 — one rounding rule in the currency engine.** Converted amounts go straight from the exact product
      to cents, half-up (`quantize_monetary`); the 4dp intermediate double-rounded (1.00 × 1.00495 → 1.0050 → 1.01).
      Exposure totals, percentages and the rate inversion are half-up. The memo formats through `quantize_monetary`,
      always to the cent (it dropped cents at ≥ 1,000,000 with float `:,.0f`), puts the sign before the symbol
      (`-$1.01`), and its totals row is the sum of the printed rows (amount and %, no hard-coded "100.0%").
      Reproduced first: 8 of 10 in `test_sprint884_currency_rounding.py` failed. Snapshots re-recorded
      (`sprint819/currency.json.gz`, `memo_render_snapshot.json` currency cases only) — every diff is a cent.
      **Not as described:** the TB API response never carries the conversion — `TrialBalanceResponse` has no
      `currency_conversion` field and `extra="ignore"` drops it — and no other export exists, so "API response" and
      "export" have nothing to show; the memo route is tested over HTTP instead.
- [x] **9B / TQ-12, OUT-19 — amounts stay exact from engine to export.** **Decided (CEO, 2026-11-18):** largest
      supported amount 999,999,999,999,999.99; the API sends exact JSON numbers (still numbers, no frontend type
      change); Excel gets an exact text copy where it cannot hold a value.
      - Limit: `shared/monetary.MAX_SUPPORTED_AMOUNT`; `parse_amount`/`safe_decimal` raise `AmountTooLargeError`
        above it (never a silent 0); `sanitize_error` passes its message through; an app handler makes it a 400
        `AMOUNT_TOO_LARGE`. The intercompany route snapshot's "huge" cases now carry that message (both were already
        400; one said "An unexpected error occurred").
      - Exact JSON: `shared/exact_json.py` — `exact_number()` gives a plain float when the float is exact (every
        everyday amount, so responses are unchanged), otherwise a marker with a per-process secret that
        `ExactNumberMiddleware` (innermost, before GZip) rewrites as the bare number. `MonetaryDecimal` uses it, as do
        the payroll / fixed-asset / inventory / three-way-match response fields (`ExactMoney`; they were `float`).
        The TB route sends `lead_sheet_grouping` through `exact_numbers()` (its account amounts used to go out as
        JSON *strings*; now numbers, matching the frontend types).
      - Engines: `lead_sheet_grouping_to_dict` returns Decimals at cents half-up (totals from the shown summaries);
        `FinancialStatementBuilder` is Decimal throughout (zero lines print `$0.00`, not `$-0.00`); payroll, FA,
        inventory, PO, invoice and 3WM summary `to_dict` return Decimals (amounts at cents, unit prices and pay rates
        unrounded; 3WM summary used `round()`, i.e. half-even).
      - Exports: `shared/excel_exact.py` makes openpyxl write Decimal cells digit for digit (it wrote every number
        with `"%.16g"`, so even a Decimal lost digits) and adds "Exact: … approximate" notes beside values over 15
        significant digits; used by the loan workbook (`_to_float` removed) and the FS workbook. The FS export route
        reads its JSON body with `parse_float=Decimal` (`DecimalBodyRoute`; same path/method/position).
      - Tests: `test_sprint884_exact_amounts.py` (28): 90,071,992,547,409.93, 1,234.005 → 1,234.01, −1,234.005 →
        −1,234.01 and 100 one-cent balances through engine, API response text, PDF text and workbook XML; the FS
        export through the real builder and renderer (PDF and Excel). Reproduced first: collection failed (no limit);
        then 14 of 28 failed before the engine changes. Old-contract test rewritten: `tests/qa/test_decimal_serialization.py`
        (required floats from the engine; now Decimals in the engine, JSON numbers at the API). Two FS tests adapted to
        Decimal; `pdf/sections/ratios.py` takes `float()` for its debt-to-equity ratio only.
      - Snapshots re-recorded after checking values: fixed_assets, inventory, payroll, payroll_ghost,
        three_way_match, column_overrides (float → Decimal, every value identical); route_form_exports (loan xlsx
        cells identical, number text e.g. `200000.00`); route_export_pipeline (FS `$-0.00` → `$0.00` only);
        route_intercompany_elimination (limit message).
      - **Not done (outside the named files):** finding `details` dicts stay floats by design (Sprint 829);
        other routes' `float` response fields are unchanged; a browser still shows amounts above ~70 trillion one
        cent off (JS numbers) — follow-up if that range matters.
- [x] **9C / OUT-05 — detail and total rounded separately.** Accrual completeness: `AccrualAccount` holds its
      balance at cents, half-up, so `total_accrued_balance`, `total_deferred_revenue`, the checklist balances and the
      deferred analysis are sums of the rows shown (was Python `round()`, i.e. half-even, on the row and again on the
      unrounded total: 0.014 + 0.014 showed 0.01 + 0.01 over 0.03). The memo's TOTAL and Deferred Revenue Balance are
      the sum of the rows it prints, even from a client payload whose total disagrees. **Same pattern found and
      fixed:** expense categories (each category rounded before `total_expenses`; memo TOTAL amount and % are the sum
      of the printed rows) and the financial statements (each lead-sheet balance rounded to cents on intake, so every
      subtotal and total is the sum of the lines above it; depreciation and interest add-backs too). The screen shows
      the engine's totals, so it agrees once they do. Reproduced first: 18 of 19 in `test_sprint884_detail_totals.py`
      (sub-cent, half-cent, mixed-sign and negative half-cent inputs) failed.
- [x] **9D / OUT-04 — the "Trial Balance" export is the trial balance.** The export request (`AuditResultInput`) gains
      `all_accounts` — the full account list the TB analysis response already returns. CSV (`/export/csv/trial-balance`):
      every account once, a Flagged column ("Yes (n)" = its flag count), TOTALS summed from the rows as shown
      (half-up). Workbook: "Standardized TB" → **"Trial Balance"** (same layout: every account once, Flagged column,
      totals from its rows); "Flagged Anomalies" → **"Flagged Accounts"** (one row per flag as before, plus a subtotal
      per material/immaterial section and a total of both). The old snapshot shows the bug exactly: a CSV of just a
      header and `TOTALS,,100000.00,100000.00`. **Default chosen (not decided):** without `all_accounts` the CSV route
      is a 400 naming the field, and the workbook's Trial Balance tab says the list was not supplied and shows no
      totals — rather than a partial TB. No frontend code calls either route today, so no frontend change.
      Reproduced first: 8 of 8 in `test_sprint884_tb_export.py` failed (unflagged accounts + one account flagged
      twice). Old-contract tests rewritten (`test_export_csv_serializers.py`, `test_export_routes.py`,
      `test_export_diagnostics_routes.py`: their fixtures now carry `all_accounts`); `route_export_pipeline` and the
      Excel case of `memo_render_snapshot.json` re-recorded; `USER_GUIDE.md` tab names updated. OpenAPI snapshot
      (`scripts/openapi-snapshot.json`) regenerated for the new field in a follow-up commit.
- [x] **9E / OUT-06 — loan totals under their own columns.** `AmortizationResult.column_totals()` sums the scheduled
      payment, interest, principal and extra-principal columns from the rows; the workbook's Schedule totals row puts
      each under its own column and a separate "Final Ending Balance" row shows the last balance (column 8 used to
      hold total payments). **Same bug found in the CSV export** (`Total Payments` under "Ending Balance"): fixed the
      same way. The PDF schedule gains the same totals row. Reproduced first: 9 of 12 in
      `test_sprint884_loan_totals.py` failed (ordinary, extra-payment and balloon loans; schedule, annual summary,
      inputs sheet, PDF and CSV compared). `test_loan_amortization_exports.py` row count +1; the Sprint 819 form-export
      snapshot re-recorded (diff: the loan CSV/PDF totals rows and the xlsx sheet digest only).
**Commits:** `c781e7e2` (9A), `cc19befb` (9C), `b0faf6d4` (9E), `f0d19362` + `06c7e560` (9F), `924d36a1` + `394aa48a` (9D), `6edac9f7` (9B); this record.
**Open for the CEO:** (1) the TB API response drops `currency_conversion` (9A note) — expose it or not; (2) revenue memo denominator (9F note); (3) Next.js upgrade for the build advisory gate.

**Follow-ups (filed 2026-11-18, to do later):**
- [ ] **Currency conversion never reaches the user.** `apply_currency_conversion` computes `currency_conversion`, but
      `TrialBalanceResponse` has no such field (`extra="ignore"` drops it) and no frontend code calls the currency
      memo route. Needs the CEO decision above; if yes, add the field (amounts via `ExactMoney`) and a screen/export.
- [ ] **Revenue memo "High-Risk Entries" can exceed 100% of revenue.** With no `total_revenue` in the payload, the
      memo takes its denominator from the first test detail carrying `total_revenue`/`gross_revenue` (sample:
      $9,860,237.81 = 144.1%). Decide the denominator (engine total revenue, gross vs net) and send it in the result.
- [ ] **Browser display above ~70 trillion.** The API sends exact digits, but a JavaScript number shows amounts above
      ~2^46 one cent off. Only if that range matters: send monetary fields as strings and format them in the frontend.
- [ ] **Remaining `float` monetary response fields.** Sprint 884 moved `MonetaryDecimal` and the payroll / FA /
      inventory / 3WM entry fields to exact numbers; other routes' response schemas still declare amounts as `float`
      (and finding `details` stay floats by design, Sprint 829). Sweep `shared/*response_schemas.py` for amount fields.
- [ ] **Next.js upgrade** (see "Then (C)" above).
- [x] **9F / OUT-23 — revenue memo counts a transaction once.** "High-Risk Entries (HIGH severity)" now sums the
      HIGH tests' flagged entries once per source `row_number` (`_sum_flagged_amounts_once`); an entry with no row
      number (0 is the aggregate-finding sentinel) counts as its own item. Reproduced first: one transaction flagged
      by two HIGH tests showed $2,500.00 (25.0%) for $1,500.00 (15.0%) of distinct entries
      (`test_sprint884_revenue_high_risk.py`, 1 of 3 failed). Sprint 819 `route_testing_exports` snapshot re-recorded
      in a follow-up commit: the sample memo's figure fell from $20,986,691.82 (306.7%) to $9,860,237.81 (144.1%).
      **Still over 100%, not from double counting:** the sample payload carries no `total_revenue`, so the memo takes
      its denominator from the first test detail with `total_revenue`/`gross_revenue`, which is smaller than the
      flagged entries' absolute amounts. Not changed; needs its own item.

### Sprint 885: Exported CSV, Excel and PDF files are safe to open and render correctly
**Status:** IN REVIEW (2026-11-18) — code complete on local branch `sprint-885-export-safety`, stacked on Sprint 884
(`4eaac54f`); not pushed. Merge 883 and 884 first.
**Priority:** P0 (two Critical findings: uploaded text becomes a live spreadsheet formula). **Source:** read-only review
at `ef5e567` (OUT-01, OUT-02, OUT-33, OUT-24, OUT-28, OUT-34, OUT-25, OUT-26, OUT-27). **Agents:** Executor, Guardian, Critic.
**Decided (CEO, 2026-11-18):** PDF fonts cover Latin with accents, Greek and Cyrillic now, with openly licensed fonts;
Chinese/Japanese/Korean deferred (lowest priority, `## Deferred Items`).
- [x] **10A / OUT-01 — convergence CSV through the safe writer.** `export_convergence_csv` wrote
      `f"{account},{count},{tools}
"`, so "Operating Expense,=1+1" became two cells, the second a live formula, and a
      quote or line break broke the record. Each row now goes through `safe_csv_writer` as three values (count an int).
      Reproduced first: 3 of 3 in `test_sprint885_convergence_csv.py` failed over HTTP (commas, quotes, LF, CRLF,
      `;@`, `=HYPERLINK`, `,+1,-2`).
- [x] **10B / OUT-02 — every Excel cell through one typed writer.** `shared/excel_cells.py`: `put` / `put_ref` /
      `append_row` decide by Python type — `str` is written as text (`t="s"`, never a formula; text starting with a
      formula trigger also gets Excel's invisible `quotePrefix`, so the cell stays text if re-entered; no visible `'`),
      int/float/Decimal stay numbers (non-finite refused), `date` is a date cell, anything else is a `TypeError`;
      XML-illegal control characters print as U+FFFD instead of a 500. A codemod routed all 170 writes in
      `excel_generator.py`, `leadsheet_generator.py` and `loan_amortization_excel.py` through it and removed their
      `sanitize_csv_value` wrappers (which put a visible `'` in the cell). Second layer: `assert_no_formulas(wb)`
      before every save (it caught the cash-flow sheet writes the first codemod pass missed). Dates: `workpaper_date`
      is `Optional[date]` on `AuditResultInput` and `FinancialStatementsInput` (a 422 for "=1+1"; the generators also
      refuse a non-ISO string) and is written as a date cell; the PDFs still get the same ISO text. Models replace the
      untyped nested inputs: `FlaggedAccountInput` (`abnormal_balances`), `TrialBalanceAccountInput` (`all_accounts`),
      `LeadSheetGroupingInput`/`LeadSheetSummaryInput`/`LeadSheetAccountInput` (`lead_sheet_grouping`, prior too),
      `selected_sheets: list[str]` — typed fields, `extra="allow"` for the keys the PDFs read, numbers coerced to text
      for text fields; exporters read them via `model_dump(exclude_unset=True)` so unsent keys stay absent. Guard test
      fails the build if a generator writes a cell any other way. Tests: `test_sprint885_excel_typed_cells.py` (19;
      15 failed first). Old contract rewritten: `test_export_csv_serializers.py` (non-dict list entries were silently
      skipped; now a validation error). `route_export_pipeline` snapshot re-recorded: every cell value, type and number
      format compared before/after — identical; only the style table differs (`quotePrefix`). OpenAPI snapshot
      regenerated. **Not typed (PDF-only, not read by any workbook):** `classification_summary`, `column_detection`,
      `risk_summary`, `sheet_results`.
- [x] **10C / OUT-33 — CSV text protected by column, not by content.** `SafeCsvWriter` left any str matching
      `_PLAIN_NUMBER` bare, so a text identifier "+00123"/"-00123" became a number. Now every `str` is text and is
      escaped; numbers, Decimals and `NumberCell` pass bare. `number_cell(value, spec, suffix)` gives exactly the old
      `f"{value:spec}{suffix}"` text, marked numeric (falls back to escaped text for "nan"/"inf"). Every numeric CSV
      column was converted (codemod of `f"{x:.2f}"`-style cells plus vetted `str(amount)`/`f"{amount}"` cells in 17
      modules); before converting, a full-suite run logging every number-looking str reaching the writer found the
      exercised sites (cash flow, testing-tool CSVs, multi-period, TB, depreciation). The client-supplied share
      re-write has no column types, so it keeps the content rule (`SafeCsvWriter(untyped=True)`).
      No CSV output changed in the Sprint 819 route/output snapshots. `test_csv_formula_guard.py`'s
      "plain-number strings stay numeric" asserted the old contract; rewritten. Tests: `test_sprint885_csv_text_by_column.py`
      (13; 5 failed first). **Note:** a CSV can only escape "+00123" with the visible `'` mark (same as every other
      escaped cell); "00123" goes out exactly, but whether a spreadsheet then drops its zeros is the spreadsheet's choice.
- [x] **10D / OUT-24 — uploaded text cannot restyle a PDF.** `shared/safe_paragraph.user_text()` escapes a value
      completely before it is joined to template markup (idempotent: returns `EscapedText`, a str subclass);
      `sanitize_markup` stays as the second layer; `template_markup()` marks the rare deliberate markup value.
      Detector first (`test_sprint885_pdf_markup_escape.py`): every memo `generate_sample_reports.py` renders (21), plus
      the analytical-expectations, SUM-schedule and engagement-dashboard memos, rendered with
      `<font color="#ffffff">…</font>` appended to every free-text input; every marker must print with its tag.
      Before: all 21 sample memos leaked (~950 values parsed as markup — cover metadata, scope lines, test tables,
      drill-down rows, descriptions, names, currency codes, file names). Fixed by: three codemods (escape every
      interpolated value in `Paragraph(f"…")`; escape `Paragraph(<subscript/attribute/.get()>)` data reads; escape the
      values in any f-string whose literal text is markup) and hand fixes for values built in variables (cover
      metadata, intelligence stamp, drill-down cells, memo test tables, FS line labels, TB/FS cover subtitles,
      narratives, preflight messages, sampling conclusions, currency lists). `create_leader_dots` now escapes its value,
      counts dots from the characters a reader sees (so "PP&amp;E" counts 4, not 8 — three memo lines gain dots and
      now align with their neighbours; the only snapshot text change), and returns `EscapedText`. Template text
      (titles, scope/methodology registry, constants) is left as markup. Sample data had pre-escaped "&amp;" in a
      footnote to suit the old behaviour; now a plain "&". Tests: 31 (all 21 sample memos + 3 record-built memos
      leaked first); `memo_render_snapshot.json` re-recorded (4 cases, dots only); Sprint 819 route snapshots
      unchanged.
- [x] **10E / OUT-28 — non-ASCII download names.** One builder, `shared/filenames.content_disposition`, used by
      `attachment_response` (every ordinary download) and the share download: a plain `[A-Za-z0-9._-]` name is sent
      exactly as before; any other gets an ASCII fallback (accents dropped, other characters `_`) plus
      `filename*=UTF-8''…` (RFC 6266/5987). Stems from client names are capped at 120 UTF-8 bytes (download and share),
      so a long name cannot make a huge header. Reproduced first over HTTP: Chinese and Cyrillic names 500'd
      (`UnicodeEncodeError` in the header), "Café" went out as raw Latin-1 bytes, a 720-char name made a 773-char
      header. Tests: `test_sprint885_download_filenames.py` (15: CSV, PDF and shared downloads; Chinese, Cyrillic,
      accented, quoted, very long).
- [x] **10F / OUT-34 — document properties name Paciolus, not the libraries.** `shared/document_properties.py`:
      `pdf_document_properties(title, author)` on all four `SimpleDocTemplate`s (memos, TB diagnostic, financial
      statements, loan schedule) — creator and producer "Paciolus", a title, subject empty, author only what the firm
      entered as "Prepared by" (memos: the cover's `prepared_by`; reports: only with sign-off on), otherwise empty;
      `save_workbook(wb, title, author)` for all four workbook saves — creator and last-modified-by "Paciolus", title,
      a firm-entered author kept separately in the description, and `docProps/app.xml` rewritten to
      `<Application>Paciolus</Application>` (openpyxl always writes its own name and version there). It also runs
      `assert_no_formulas`. Reproduced first: 7 of 9 in `test_sprint885_document_properties.py` failed (ReportLab
      producer, "anonymous" author/creator, openpyxl creator/application); the test also checks no machine user name,
      home path or working directory appears. Sprint 819 `route_form_exports` / `route_export_pipeline` re-recorded:
      only `docProps/*.xml` digests and byte counts changed.
- [x] **10G / OUT-25 — PDF fonts for accented Latin, Greek and Cyrillic.** `shared/pdf_fonts.py` embeds the
      Liberation fonts 2.1.5 (SIL OFL 1.1, `backend/fonts/liberation/`, licence shipped, 4.2 MB) **under the standard
      names** Times-*, Helvetica-* and Courier-* (all four styles each). They are metric-compatible with those
      families, so every existing style, table, canvas call and ReportLab default gets the embedded font with no
      layout change (checked: no memo's page count changed; text boxes moved < 0.5pt). `<b>`/`<i>` resolve through
      the registered families. Template symbols Liberation lacks (✓ ✗ ⚠ ❧ ◆ ▢) are drawn from DejaVu Sans 2.37
      (`backend/fonts/dejavu/`, Bitstream Vera licence, 0.76 MB) via `symbol_fallback` in the safe `Paragraph` — the
      standard fonts never had them either: the old PDFs printed a substitute ■. A character neither font has prints
      as □ (`CoverageTTFont`), and `build_pdf` (now used by all four PDF builders) adds "Note: some characters in
      this document are not supported by its fonts and are shown as □." at the end of the document only when that
      happened. Reproduced first: 7 of 8 in `test_sprint885_pdf_fonts.py` failed (accented/Greek/Cyrillic extract
      exactly, bold and italic embedded, Courier/Helvetica covered, Chinese → □ + note, no note otherwise).
      Snapshots re-recorded (`memo_render_snapshot.json`, Sprint 819 `route_testing_exports` /
      `route_export_pipeline`); text changes are all corrections: bullets extract as "•" (were ``), "∆" → Greek
      "Δ", ⚠/▢/─ instead of substitute ■. **Cost:** PDFs embed font subsets — the TB diagnostic PDF 42.7 → 43.0 KB,
      the financial statements 47.7 → 185 KB.
- [x] **10H / OUT-26 — analytical-expectations table fits the page.** The schedule's seven columns are now shares
      of the real frame width (`_SCHEDULE_COLUMN_SHARES`, same proportions as before) instead of fixed widths totalling
      7.5in on a 7in frame; the header row repeats on every page (`repeatRows=1`); the section heading, its rule and
      each type heading keep with the next flowable. Reproduced first: 3 of 3 in `test_sprint885_analytical_table_fit.py`
      failed (columns 540pt on a 504pt frame; centred table text began 12pt left of the margin; no header on later
      pages) with a 45-row schedule of long labels and 12-digit amounts. `memo_render_snapshot.json` re-recorded for
      this memo: same page count and text, layout only.
- [x] **10I / OUT-27 — long branding text stays on the page.** `shared/branding_text.py`: `draw_fitted_text` keeps
      the Enterprise header (≤ 200 chars) and footer (≤ 300) inside a `TextBand` — inside the 0.75in side margins,
      baselines clear of the gold rule, page number and Paciolus disclaimer: one line at the normal size when it fits
      (short text is drawn exactly as before), otherwise wrapped onto the lines the band holds while shrinking to 5pt,
      then an ellipsis; words without spaces break between characters. Used by the memo/report chrome
      (`shared/report_chrome.py`, bands `MEMO_HEADER_BAND`/`MEMO_FOOTER_BAND`) and the financial-statements chrome
      (`pdf/chrome.py`, `FS_*_BAND`; with a custom footer the FS disclaimer moves from 15.8pt to 12pt, as the memos
      already had). Reproduced first: the 200-char header ran from x = −449 to x = 1,061 on a 612pt page; 3 of 4 in
      `test_sprint885_branding_text_fit.py` failed (memo and FS; spaced and unspaced "W"/"Ж" text at the maximum
      lengths), checked by measuring every drawn run in the PDF. `memo_render_snapshot.json` re-recorded for
      `financial_statements[branded]` only (the disclaimer's new position). **Note:** at the 300-character maximum in
      the widest letters the footer still needs 3 lines at 5pt; the band holds 2, so the end is cut with "…".
**Commits:** `02fa6e36` (10A), `6849d097` (10C), `d2b4464c` (10B), `d081c433` (10E), `7ef84ac8` (10D), `8f649de2` (10F),
`1b94a7d5` (10G), `8a745dc8` (10H), `58bf4cfa` (10I); this record + lessons.
**Verified (final tree):** backend full suite 11,200 passed, 1 failure — the pre-existing Sprint 819
`test_engagement_export_routes_unchanged` (fails on `main`); ruff clean on every changed file; mypy 288 = the branch
baseline (no new errors). Frontend (no file changed): Jest 212 suites / 2,107 passed; `next build` compiled all 70
routes (`ƒ`) — the first run exited 1 on Next.js's own `SecurityFatalError` advisory gate, the retry passed (same
intermittent gate as Sprint 884; the Next.js upgrade is the fix).
**Open for the CEO:** (1) the 4.96 MB of bundled fonts (Liberation 4.2 MB + DejaVu Sans 0.76 MB) and larger PDFs
(financial statements 47.7 → 185 KB); (2) at the 300-character maximum in the widest letters the branded footer is cut
with "…" (two lines at 5pt fit) — allow a third line by moving the disclaimer, or cap footer length lower;
(3) CJK fonts (deferred, `## Deferred Items`).

### Sprint 868: Sessions die every 15 minutes when the refresh cookie is not sent
**Status:** PENDING. **Priority:** P0 (before launch). **Owner:** C + CEO (DNS).
Seen 2026-11-15: in a browser that does not send the `paciolus-api.onrender.com` refresh cookie from
`paciolus.com` (third-party cookie), every reload signs the user out, and the session ends when the 15-minute access
token expires — mid-analysis ("Please sign in to run diagnostics"). The API on a separate site is the cause; Phase 4.3
(`api.paciolus.com`, first-party) is the fix. Re-test reload and 20-minute idle after the move. The spinner half of
this was fixed in PR #313.

### Sprint 869: JE Testing calibration and the entries count
**Status:** PENDING. **Priority:** P2. **Owner:** C.
- "Unusual account combinations" flagged 52 of 58 entries on a small synthetic ledger (flag rate 100%); on 204
  entries it flagged 2. Consider a minimum population, like Benford's 300.
- The memo's "Total Journal Entries Tested" printed 408 for a file of 204 entries (408 lines) — label or count.

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

### Sprint 859: daily DB TLS check is not pooler-aware — false "unencrypted" evidence
**Status:** PENDING. **Priority:** P2 (security evidence integrity; freeze-exempt). Filed as "Sprint 847" on 2026-10-26, lost in a rebase, re-filed 2026-10-29. Found 2026-10-26 in Render logs. `_job_verify_database_tls` (`backend/cleanup_scheduler.py:520`)
reads `pg_stat_ssl`, which Neon's pooled endpoint does not populate, so it logs `tls=INACTIVE — database
connection is unencrypted` daily **and signs that into its evidence artifact**. The startup check already handles
this (`tls=pooler-skip`, Sprint 673), so the connection itself is fine.
- [ ] Reuse the startup check's pooler detection in the daily job; record `pooler-skip` (plus the enforced
      `sslmode`) instead of INACTIVE. Test both branches.

**Commit SHA:** TBD.



### Sprint 853: Firm-owned client data and role gates (M7, L12)
**Status:** BLOCKED on CEO decision. **Priority:** P2 (largest change; data-model migration). **Source:** security review M7, L12.

Still open:
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

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 853).

### Sprint 834: Storage wording says what is stored; bulk upload no longer sold
**Status:** PARTIAL — Trust/Approach lists and USER_GUIDE §22 corrected 2026-10-24 (PR #225). **Superseded by Sprints 841 and 844**, which fix every remaining storage sentence, the Terms and Privacy included (CEO 2026-10-24: correct wrong facts now; counsel reviews the finished legal pages at website-final).
**Priority:** P1 — a trust page that overstates what is never stored is a legal exposure.
**Source:** CEO decision 8 (Sprint 818 item 3) and code-health decision 1, 2026-10-24.

- [x] **Trust page and Approach page** "What we store / never store" lists rewritten against the models:
      stored = account and client metadata, aggregate totals per analysis (`diagnostic_summaries`,
      `activity_logs`), flagged account names without amounts (`tool_runs.flagged_accounts`), engagement
      content the auditor enters (materiality, follow-up notes, intercompany mappings,
      `analytical_expectations`, `uncorrected_misstatements`), shared report files for up to 48 hours
      (`export_shares` / R2); never stored = uploaded files, line-level rows, journal entries, invoices,
      payments, payroll records, flagged-entry details. "No database to breach — zero financial data at
      rest" removed from the Approach page.
- [x] **USER_GUIDE §22** rewritten the same way (it said account names and balances are never stored).
- [x] **Bulk upload** removed from the Enterprise feature list, comparison table, FAQ, feature picker
      label, `UpgradeModal` and USER_GUIDE tier table. The route is a stub (marks files "complete"
      without analysis); Sprint 790 stops it consuming allowance. Route and entitlement kept until 817
      item 4 decides wire-or-delete.
- [ ] **Counsel:** Terms of Service §5.3 ("Paciolus never stores … individual account numbers,
      descriptions, or balances"), the Terms tier table ("bulk upload" under Enterprise), the Privacy
      Policy commitment "We never store your financial data" and its "No database to breach" line.
      Not edited because they are versioned legal documents. Proposed replacement for §5.3: *"Paciolus
      never stores the files you upload or the line-level records in them (trial balance rows, journal
      entries, invoices, payments, payroll records). It stores aggregate results of each analysis, the
      names of accounts a tool flagged (without amounts), content you enter into an engagement
      (including materiality, analytical expectations and uncorrected misstatements), and report files
      you share by link for up to 48 hours."* Same facts for the Privacy commitment.

**Commit SHA:** recorded on merge.

---

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
- [ ] F5, F9, B1, B2, B5, B6. (W4 W-3 vs 941, W8, W9 done in Sprint 855.)

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
**Status:** PARTIAL — the async-handler item done 2026-10-23 (41 handlers, AST guard, plus the share-claim and seat-reservation races the review found); the rest pending.
**Priority:** P3 — low traffic today; cheap now, expensive at scale.
**Source:** Code health review 2026-10-23, routes pass.

- [x] *(Done 2026-10-23: 41 found by AST scan, 31 touching the DB, all converted; AST guard added.
      One test had relied on the blocking — see its docstring. The three offloading cases below remain.)*
      ~30 `async def` handlers with no `await` that make sync DB calls (organization ×10,
      admin_dashboard ×4, branding ×3, diagnostics ×3, prior_period ×3, …) → plain `def`.
      Offload the blocking part of `branding.py:102` (S3 upload), `billing.py:347` (Stripe
      retrieve + DB), `export_sharing.py` passcode verify (Argon2id).
- [x] Subscription row queried 3× per testing upload (`enforce_tool_access` →
      `get_effective_entitlements`, then `check_upload_limit` twice incl. `entitlement_checks.py:111`) — load once per request.
      *(Done 2026-10-24: `_user_subscription` keeps the row in the request session's `info`,
      re-validated on each use — deleted, detached or re-pointed rows are re-queried. 1 query, was 3.)*
- [x] `billing/internal_metrics.py:601-663` per-day snapshot loop with per-user queries; cap the
      range in `routes/internal_metrics.py:129`; batch dunning lookups (`:365,384,402,538`,
      `dunning_engine.py:162,168`). *(History part done 2026-10-24: three queries total, points
      evaluated in memory, 400-point cap and end-before-start → 400. The old per-point function
      also crashed comparing SQLite's naive timestamps with aware dates. Dunning metrics batched
      2026-10-24 too: one subscription query per category instead of one per episode.)*
- [ ] One Alembic migration dropping the 26 `primary_key=True, index=True` duplicate indexes and
      the single-column indexes covered by composites (`ToolActivity.user_id`, `TeamActivityLog.organization_id`).
      Mind Sprint 741c/797 chain-vs-ORM guards.
- [ ] Convert `RequestId`, `SecurityHeaders`, `Impersonation` middleware from `BaseHTTPMiddleware`
      to pure ASGI — **benchmark first**; impact unmeasured.

**Commit SHA:** 4d0c979d (PR #217).

---

### Sprint 822: CI and repository weight
**Status:** PARTIAL — the pip-audit item done 2026-10-23; `reports/nightly/` untracked 2026-10-24 (Sprint 831 PR); root clutter pending.
**Priority:** P3.
**Source:** Code health review 2026-10-23, repo pass.

- [x] `reports/nightly/` is 1,149 of 3,261 tracked files — **CEO decision 5, decided 2026-10-24.**
      The default offered was "move to CI artifacts with 90-day retention", but the nightly does not
      run in CI — `scripts/overnight/orchestrator.py` runs from Windows Task Scheduler on the CEO's
      machine. Equivalent applied: the directory is untracked (`git rm --cached`, `.gitignore`), the
      files stay on that machine, and the orchestrator prunes report files older than 90 days after
      each run (`.baseline.json` is kept).
- [x] *(Done 2026-10-23: the advisory audit is now a non-failing `if: always()` step inside the
      required `Python Dependency Audit (blocking)` job; that job's name is unchanged.)*
      `ci.yml` runs pip-audit twice (`pip-audit-blocking` `:660`, `pip-audit-advisory` `:690`), each
      installing the full `requirements.txt`: one job, two invocations of `scripts/pip_audit_gate.sh`.
- [x] Root clutter: `PHASE_III_QUICK_REFERENCE.txt`, `README_PHASE_III_DELIVERY.txt`,
      `SECURITY_CHANGES.md`, `SECURITY_HARDENING_SUMMARY.md`, `COHESION_REMEDIATION.md`,
      `EXECUTIVE_SUMMARY_NONTECH.md`, root `MEMORY.md` — check each for live references, then move to
      `docs/` or `tasks/archive/`.
      *(Done 2026-10-24: the two Phase III files → `tasks/archive/phase-iii/`; the four docs →
      `docs/archive/` (code comments re-pointed). Root `MEMORY.md` stays — it is the deliberate
      redirect stub that the historical references resolve through.)*

**Commit SHA:** 0463165e (PR #210).

---

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

### Sprint 741: cleanup_scheduler real-root structural fix (post-Sprint-740 follow-up)
**Status:** SPLIT after the log read — **741a COMPLETE** (`reset_upload_quotas`), **741b PENDING** (`dunning_grace_period`, needs DB access).
**Priority:** P2 → P1 once Phase 4.1 lands.
**Source:** Sprint 732 / 740 (archived to [`tasks/archive/sprints-732-740-details.md`](archive/sprints-732-740-details.md)).

(No unchecked items — see the status above and the full history.)

Full history: [`archive/open-sprint-history-2026-11.md`](archive/open-sprint-history-2026-11.md) (Sprint 741).

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
