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

- [2026-11-20] (this commit): Sprint 887 open items split into CEO and engineering checklists; START HERE gains the Sprint 887 CEO line. No code changed (tasks/todo.md)
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
> - [ ] **Sprint 872** — session and sign-in boundaries (cross-account cache, CSRF owner binding, unverified invite
>       acceptance, impersonation token storage, error shape). Security; code complete, local branch, not pushed.
> - [ ] **Sprint 878** — plan features and upload allowances enforced on the server (workspace, CSV exports,
>       preview-token format bypass, upload ledger, JE sampling). Security; code complete on a local branch, stacked on #331.
> - [ ] **Sprint 879** — what we log, save and cache matches the published data statement (log values, saved
>       balances in expectations, activity summary schema, preview cache lifetime, XLSX temp files). Security; code complete,
      local branch stacked on 878, not pushed.
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
> - [ ] **Sprint 886** (in review) — exported documents match the screen: dropped fields, uncomputed scores, wrong scales,
>       materiality origin, reporting framework (review OUT-09–12/14–16/18). Local branch, stacked on Sprint 885.
> - [ ] **Sprint 887** (in review) — generated wording: no audit conclusions, no contradiction of the results, correct
>       citations (review OUT-07/08/13/17/20/21/22/29/30/31/32 + expense-category table). Local branch, stacked on 886.
> - [ ] **Sprints 888–892** (CEO briefs 13–17, 2026-11-20) — one local branch each, stacked on Sprint 887 in this
>       order: 888 published claims match the code · 889 tests that can fail · 890 frontend/API/background edges ·
>       891 one catalog, one plan file, docs, dead code · 892 behaviour-neutral refactors. The CEO's briefs supersede
>       the freeze for this work. Merge after 883–887.
> - [ ] **Sprint 893** (2026-11-21) — fixes for the defects and open items Sprints 888–892 found. Local branch
>       `sprint-893-defect-fixes`, stacked on 892.
> - [ ] **Sprint 871** — Stripe dispute webhooks never find the customer (#273). Gates Sprint 447.
> - [ ] **Sprint 860** — annual tax tables, fetcher, invariant tests; CEO signs off the 2026 W-2 and 1099 tables.
> - [ ] **Phase 4.1 / Sprint 447** — Stripe live at Pricing v3, Solo only; one real-money checkout verified, then refunded.
>       Blocked on 4.3 and 871.
> - [ ] **Sprint 863** — Privacy/Terms redline (`counsel-redline-863`) merges only after counsel signs off.
>
> **Then (C)**
> - [ ] Sprint 869 (JE calibration) · Sprint 859 (pooler-aware TLS check) · Dependabot batch (open: #297–#306, #311).
> - [x] **Next.js upgrade** (Sprint 894 B, 16.4.6) — `next build` compiles but exits 1 on alternate runs with Next's `SecurityFatalError`
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
> - [x] Sprint 853 (firm-owned client data) — CEO decided 2026-11-16; in progress (see Sprint 853).
> - [ ] Sprint 884 follow-up: should the TB response carry the currency conversion it computes (today it is dropped)?
> - [ ] Sprint 887: review the PR-T12/PR-T13 drafts and `reports/sprint-887-wording.md`; decide where `57c79d91` lives
>       and whether the anomaly summary gets a download button. Engineering follow-ups are listed under the sprint.

### Sprint 872: Session and sign-in boundaries (DH-01, AZ-10, AZ-11, AZ-13, AZ-14)
**Status:** IN REVIEW — code complete 2026-11-16 on local branch `sprint-872-session-boundaries` (off Sprint 853's
branch; not pushed). **Priority:** P0/P1 security (freeze-exempt: security defects). **Source:** read-only review at `ef5e567`.
**Agents:** Guardian (lead), Executor, Critic.

**872a — browser cache survives a change of account (DH-01, Critical)**
- [x] Confirmed at `3c34926a`: cache key = endpoint + custom headers; the frontend "token" is the constant `'cookie'`
      sentinel, so it carries no identity; `clearAuthSessionData()` was empty; in-flight dedup shared the same key.
- [x] `utils/sessionScope.ts`: the signed-in account id prefixes every cache and in-flight key; ending a signed-in
      session (logout, refresh failure/auth failure, network failure on refresh, account switch on refresh/login/`/auth/me`,
      account deletion via logout) empties both stores and bumps a session generation.
- [x] Generation guard: a response is cached only if its request's generation is still current (normal, 401-retry and
      background-revalidation paths); a late in-flight cleanup no longer deletes a newer entry.
- [x] `SessionBoundary` (inside `AuthProvider`) remounts everything below it when a signed-in session ends, so
      Engagement/Diagnostic/Mapping/Workspace/BatchUpload contexts and page-level fetch state start empty. Signing in
      from signed-out does not remount.
- [x] Tests: `sessionCacheIsolation.test.tsx` (real AuthProvider + apiClient, fake server answering per cookie): A→logout→B
      on clients/history/engagements; A's request held until after B signs in (no dedup onto it, no cache refill);
      account switch on refresh; auth failure; remount on logout only.

**872b — CSRF not bound to the refresh cookie's owner (AZ-10, High)**
- [x] Confirmed: with no bearer/access cookie, `expected_user_id = None`; A's CSRF token + B's refresh cookie → 200 on
      refresh and logout (also with A's expired access cookie).
- [x] The CSRF middleware hands the (signature-checked) token's user to the handler (`request.state.csrf_user_id`);
      `auth.rotate_refresh_token` / `revoke_refresh_token` look up the refresh token in the request's own session and
      refuse a different owner with 403 before any rotation, revocation or reuse-detection side effect. CSRF tokens stay
      stateless; no extra `SessionLocal()`. Dev/test X-Requested-With fallback (no CSRF token) carries no identity —
      production requires the token.
- [x] Tests: `test_csrf_refresh_owner_binding.py` — A's CSRF + B's refresh cookie → 403 on refresh and logout, with no
      access cookie and with A's expired access cookie; B's token untouched; B's own CSRF works on both.

**872c — invitation accepted by an unverified address (AZ-11, High)**
- [x] Confirmed: `accept_invite` depended on `require_current_user`; an unverified account registered with the
      invited address joined the firm (200). The address check was also skipped when `invitee_email` was empty.
- [x] Now `require_verified_user`, and the account's address (which only changes once a new address is verified —
      `pending_email` holds unverified changes) must equal the invitation's, always compared. Expiry, org lock, seat
      check and the single-membership rule unchanged.
- [x] Tests: `test_invite_accept_verified.py` (real tokens) — unverified matching → 403, invite still PENDING, no
      membership; verified matching → accepted; verified other address → 403; unverified pending change to the invited
      address → 403. `test_organization_routes.py` capacity test now overrides `require_verified_user`.
- Note: no frontend page or email link calls the accept endpoint today.

**872d — impersonation token in sessionStorage (AZ-13, High)**
- [x] Confirmed: the admin customer page wrote the impersonation token, customer email and expiry to sessionStorage;
      the banner read them (only on mount, so it never noticed a session started without a reload).
- [x] `lib/impersonationState.ts`: in-memory store (`useSyncExternalStore`); the page calls `startImpersonation`, the
      banner subscribes; End Session still revokes server-side first and keeps the token if that fails; any end of the
      admin's signed-in session (logout, auth failure) clears it via `sessionScope.onSessionEnd`. A reload loses it.
- [x] Tests: `impersonationMemoryOnly.test.tsx` — start + end writes no token/email/key to any browser storage
      (`Storage.prototype.setItem` spy + storage scan), revocation called with the in-memory token, failure keeps it,
      logout clears it, source guard on page/banner/store; `ImpersonationBanner.test.tsx` seeds the store instead.
- Not changed: logout does not revoke a live impersonation token server-side; it expires within its 15 minutes.

**872e — middleware errors bypass the common error shape (AZ-14)**
- [x] Confirmed: CSRF and body-size middleware returned `{"detail": ...}`; impersonation 403 had no `request_id`;
      429s came from SlowAPI's `{"error": "Rate limit exceeded: ..."}`; 500s and default-limit 429s are rendered outside
      `RequestIdMiddleware`, so they could not carry the request ID.
- [x] `shared/error_responses.py`: one constructor (`error_response`, raw-ASGI `send_error`) → `{code, message,
      request_id, detail}` + `X-Request-ID`. Request ID resolved from the scope (`RequestIdMiddleware` now stores it
      there), the context var, a valid client `X-Request-ID`, or a new one. Used by every `main.py` handler, the CSRF,
      impersonation and body-size middleware, and a new sync rate-limit handler (slowapi's middleware path calls it
      synchronously). 422 `error_code` alias dropped (`code` carries it; frontend reads `code` first).
- [x] Frontend: parser unchanged; the 429 text added to `SAFE_PASSTHROUGH` (the old body had no `message`, so the UI
      fell back to its own 429 text — without this it would have shown the generic error).
- [x] Tests: `test_error_envelope.py` through the real stack — 401, CSRF 403, impersonation 403, 400/413 body size, 422,
      429 (default-limit and decorated paths), unhandled 500, client request-ID echo; exact key set, ID = header, no
      internals. `errorEnvelopeParsing.test.ts`. Two Sprint 819 route snapshots re-recorded — the diff is only
      `HTTP_500`→`INTERNAL_ERROR` (29×) and the removed `error_code` (2×).

**Verification (872a):** frontend build green (all pages `ƒ`), 213 suites / 2,113 tests, `tsc`, eslint clean.

**Verification (872b):** backend 10,673 passed, 1 skipped (the pre-existing `main` failure
`test_sprint819_route_snapshots.py::test_engagement_export_routes_unchanged` deselected); ruff clean; mypy adds no errors.

**Verification (872e / final tree):** backend 10,684 passed, 1 skipped, 4 failed → after fixes, the only failure is the
pre-existing `main` failure `test_engagement_export_routes_unchanged` (gzip vs null); the other three were this
sprint's (order-dependent CSRF test, two snapshots) and are fixed. Frontend 215 suites / 2,125 tests, build, `tsc`,
eslint green; ruff clean; mypy adds no errors.

**Verification (872d):** frontend build green (pages `ƒ`), 215 suites / 2,125 tests, `tsc`, eslint clean.

**Verification (872c):** invite/org/firm-record/role-gate/access-log tests 50 passed; ruff clean.

**Commit SHA:** 872a `9f66d506` · 872b `89f752c2` · 872c `f866d242` · 872d `caf05f5a` · 872e `c9622ce2`.

### Sprint 878: Plan features and upload allowances enforced on the server (AZ-02..06, ST-04)
**Status:** IN REVIEW — code complete 2026-11-16 on local branch `sprint-878-plan-enforcement` (off Sprint 853's
branch `sprint-firm-owned-records`, rebased onto Sprint 872 2026-11-16; not pushed; merges after #331 and 872). **Priority:** P0/P1 security (freeze-exempt: security defects).
**Source:** read-only review at `ef5e567`. **Agents:** Guardian (lead), Executor, Critic.

**CEO decisions (2026-11-16):** the engagement workspace is Solo and above. An account that drops to Free keeps read
access to its existing engagements and workpapers but cannot create or change them. A firm subscription's usage counts
against one allowance shared by the firm. A JE sampling preview uses no upload; a sampling run does.

**878a — workspace routes never check the workspace entitlement (AZ-02, ST-04, High)**
- [x] Confirmed at `3c34926a`: `check_workspace_access` had no caller; all 15 workspace writes (engagement
      create/update/archive; follow-up item create/update/delete; comment create/update/delete; expectation and
      misstatement create/update/archive) answered 2xx for a Free and a lapsed-Solo account.
- [x] `Depends(check_workspace_access)` on all 15 writes (route-level, runs before the handler). Reads unchanged, so a
      downgraded account still reads its own records; the firm check and role gates are unchanged.
- [x] Tests: `test_sprint_878_workspace_entitlement.py` — 15 writes × {active Solo, lapsed Solo, Free} on records the
      owner made while on Solo (state compared before/after); the same writes against another firm's ids (404 for Solo,
      403 for Free/lapsed, nothing moves); 17 reads of own records → 200 in all three states; another firm's → 404;
      structural guard that every write route on the five workspace routers carries the gate.

**878b — four CSV exports skip the export gate (AZ-03, High)**
- [x] Confirmed at `3c34926a`: `/audit/account-risk-heatmap/export.csv`, `/audit/depreciation/export.csv`,
      `/audit/lease-accounting/export.csv` and `/export/csv/bank-rec` depended only on `require_verified_user`; a
      verified Free account (and a PAST_DUE Solo) got the CSV. The coverage test scanned six export modules only.
- [x] `Depends(check_export_access)` on those four. An app-wide scan by suffix also found six CSV downloads with only
      the in-body tool gate (cash-flow projector, book-to-tax, 1099, SoD, W-2, intercompany): already closed to Free by
      the tool gate, but given the export gate too so every download carries it.
- [x] Tests: `test_sprint_878_export_gates.py` — Free and lapsed Solo → 403 with the generator never called; active
      Solo → 200 `text/csv` attachment, for all four. `TestEveryExportRouteIsGated` gains an app-wide scan (paths ending
      `.csv`/`.xlsx`/`.pdf` or with an `export` segment), with two reasoned exemptions: the GDPR account export and the
      admin team-activity CSV (behind the stricter admin-dashboard gate).

**878c — a preview token gets a PDF past the Free format limit (AZ-04, High)**
- [x] Confirmed at `3c34926a`: a Free account's PDF preview returned 200 with a token; the analysis checked the
      placeholder upload's name and processed the cached PDF; a Solo preview followed by a lapse also analysed the PDF.
      A second path: a PDF uploaded with no extension skipped the check entirely (the parser detects PDF from the bytes).
- [x] `enforce_format_access` takes the bytes and, when the name has no extension, uses `detect_format` as the parser
      does. The preview checks before parsing or caching. The analysis resolves its real input first (cached file or
      upload) and checks that, against the plan at analysis time.
- [x] Tests: `test_sprint_878_preview_format_gate.py` — Free preview → 403, nothing parsed; Free preview-then-analysis
      with a cached PDF token + `placeholder.csv` → 403, engine never runs; Solo preview → lapse → analysis → 403;
      Solo preview → analysis reaches the engine with `tb.pdf`; extensionless PDF bytes on Free → 403; Free CSV still runs.

**878d — the upload allowance depends on history the user can skip or clear (AZ-05, High)**
- [x] Confirmed at `3c34926a`: a Free account ran 11 analyses with no `/activity/log` call, all 200; with the browser's
      log calls the 11th was refused, and after `DELETE /activity/clear` the count read 0 again; a firm member with no
      subscription row ran against the firm's allowance without moving its counter (`increment_upload_count` returned
      early with no row of their own).
- [x] New table `upload_usage_events` (model `upload_usage_model.py`, Alembic `d878a5c1e9b2`, no backfill): one row per
      successful metered run for users without an active metered subscription; no route reads or writes it directly
      (structural test). `_meter_subscription` mirrors `get_effective_entitlements`: own ACTIVE/TRIALING subscription →
      its counter; non-owner firm member with no row of their own → the firm's subscription counter (one shared
      allowance, updated by subscription id); otherwise the ledger. `uploads_used_this_period` and
      `increment_upload_count` both use it, so check and consume read one source. ActivityLog no longer meters anything.
- [x] Account erasure deletes the ledger rows; the account export includes them. Data Handling Architecture §2.1 lists
      the table (regenerated `policies.generated.ts`).
- [x] Tests: `test_sprint_878_upload_ledger.py` — 10 Free runs without log calls accepted, 11th refused; clearing
      history after logging leaves the count at 10 and the 11th refused; a failed run consumes nothing; a lapsed plan
      meters on the ledger, not its frozen counter; a firm member's run moves the firm's counter, owner and member share
      500. `test_sprint_790_upload_metering.py` Free test now asserts one ledger row per run (it asserted no count before).
      `test_account_erasure.py` seeds and checks a ledger row.
- [x] Follow-up (full-suite run): five older tests simulated Free usage with ActivityLog rows
      (`test_audit_api.py` ×2, `test_audit_flux_routes.py`, `test_entitlement_checks_unit.py` ×2) and now seed ledger
      rows; the unit test that pinned "no subscription = no-op" now asserts one ledger row.

**878e — JE sampling skips the tool gate and the allowance (AZ-06, High)**
- [x] Confirmed at `3c34926a`: a Free account got 200 from both `/audit/journal-entries/sample` and `/sample/preview`;
      a Solo account at 100/100 could still sample; a run did not move the counter.
- [x] Both routes call `enforce_tool_access(..., "journal_entry_testing", db)`. The run also calls
      `check_upload_limit` and, on success, `tool_run_recorder.consume_upload` (made public: the one metering entry
      point; no ToolActivity row, so sampling does not show as a JE test run). The preview uses no allowance.
      `test_sprint_790_upload_metering.py`'s symmetry scan recognises `consume_upload` (watched it fail with the call removed).
- [x] Tests: `test_sprint_878_je_sampling_gate.py` — Free and lapsed Solo → 403 on both routes, nothing parsed; Solo at
      its cap → 403 `uploads` on the run, counter unchanged; a successful run +1; a failed run +0; the preview at the
      cap → 200, counter unchanged.

**Verification (878a):** workspace/engagement/firm/entitlement suites 822 passed + new file 97 passed; ruff clean;
mypy 212 errors (baseline 1,011), none in changed files.

**Verification (878b):** tool/export/route-snapshot suites 882 passed; new tests 26 passed; ruff clean; mypy 212 (baseline 1,011).

**Verification (878c):** upload/format/preflight/entitlement/pricing suites 1,391 passed, 1 skipped; new tests 6
passed; ruff clean; mypy 212 (baseline 1,011).

**Verification (878d):** metering/billing/usage/activity/admin/org/migration/erasure suites 450 passed; Sprint 790
metering + JE suites 580 passed; policy-doc guards 13 passed; new tests 6 passed; ruff clean; mypy 212 (baseline 1,011);
frontend build green (pages `ƒ`), jest 212 suites / 2,107 tests.

**Verification (878e, whole sprint):** full backend suite 10,798 passed, 1 skipped (the first full run found 6
failures: the five ActivityLog-seeded tests fixed in `455ad1e3`, and the "only the recorder calls
`increment_upload_count`" guard, resolved by metering sampling through `consume_upload`); new tests 8 passed; ruff
clean; mypy 212 (baseline 1,011). Frontend unchanged since 878d's green build + jest.

**Not changed (noted):** the engagement pages have no plan gate in the UI — a Free account now gets a 403 when it
tries to create or change workspace records, with no upgrade prompt (frontend follow-up). The heatmap, depreciation and
lease *analysis* routes (not their CSVs) carry no tool gate and are not registry tools, so Free can run them on screen —
a product call, not decided here. Ledger rows are kept until
account deletion; no retention job prunes old months.

**Commit SHA (rebased onto Sprint 872 on 2026-11-16; pre-rebase tip `b8a427d9`):** 878a `c9fea367` · 878b `621d3117` · 878c `d78a4a86` · 878d `7b67bd03` + test follow-up `02da4934` · 878e `e3998368`. After the rebase: backend suite and
frontend 215 suites / 2,125 tests green; `alembic heads` = `d878a5c1e9b2` only.

### Sprint 879: Logs, saved records and caches match the data statement (DH-03..07)
**Status:** COMPLETE — 2026-11-16 on local branch `sprint-879-data-statement` (stacked on Sprint 878, which is
stacked on 872 → #331; not pushed). **Priority:** P0/P1 (freeze-exempt: security defects). **Source:** read-only review at
`ef5e567`. **Agents:** Guardian (lead), Executor, Critic.

**The statement:** uploaded files are processed in memory and not kept after analysis (up to 10 minutes in memory);
we save the account, client list, analysis summaries (totals, ratios, counts, flagged account names — never balances,
transaction rows or file contents) and anything the user enters in an engagement.

**CEO decisions (2026-11-16):** analysis no longer saves an account's actual balance into an expectation; the auditor
captures it with an explicit action. The preview cache stays in each worker's memory (no Redis/disk); on a miss at
analysis time the browser re-sends the file.

**879a — uploaded values reach the application logs (DH-03, Critical)**
- [x] Confirmed: the TB and file-tool rejection handlers logged the exception object (`%s`, `exc_info=True`); the OFX
      parser logged currency, account suffix, account type and date range; DEBUG logged the upload's filename
      (`upload_pipeline.validate_file_size`) and 422 inputs (`main.validation_exception_handler`); a PDF page failure
      logged the filename. `TracebackRedactionFilter` ran on two handlers, only in production, and
      `REDACT_LOG_TRACEBACKS=false` turned it off.
- [x] `logging_config.install_safe_log_records()` — a log-record factory (installed on import and by `setup_logging`):
      an exception object passed as the message or an argument becomes its type name; `exc_text` is pre-set to type +
      innermost frame, so no formatter renders the message or traceback. `exc_info` stays on the record for Sentry
      (its scrubber already blanks the message). The filter and the env opt-out are removed (Dockerfile, env docs).
- [x] Call sites: fixed event + type name only in both rejection handlers; OFX logs dialect + counts; no filename in
      the format-detection or PDF-page lines; the 422 debug line logs a count.
- [x] Tests: `test_sprint_879_log_redaction.py` — OFX (SGML) and QBO (XML) bank statements with marker account
      suffix/currency/type and filenames, a malformed OFX, an out-of-balance TB with marker cell and account name, parser
      errors quoting a marker on both rejection handlers, a 422 carrying a marker; through the real `setup_logging()` at
      INFO/DEBUG × production/development, with Loki's push and a Sentry transport captured (logging integration at
      DEBUG, stricter than production). No marker anywhere. Failed first with 6 markers leaking.
- Found, not fixed (out of scope): an out-of-balance TB returns a **500** — the `tb_out_of_balance` structural anomaly
  lacks six fields `TrialBalanceResponse.abnormal_balances` requires (`debit`, `credit`, `category`,
  `matched_keywords`, `requires_review`, `suggestions`). Needs its own sprint.

**Verification (879a):** full backend suite 10,822 passed / 1 skipped / 1 failed — the failure
(`test_cleanup_scheduler::test_failure_log_includes_traceback_exc_info`) caught the first version stripping `exc_info`,
which would have cost Sentry its stack frames; fixed (pre-set `exc_text` instead), and the logging/Sentry/Loki/cleanup
suites re-run green (103 passed). ruff clean; mypy 212 (gate 1,011), none in changed files.

**879b — analysis saves account balances into expectations (DH-04, Critical)**
- [x] Confirmed: `shared/expectation_evaluation.evaluate_expectations_against_measurements` called
      `update_expectation(result_actual_value=…)` for every match, committed in the analysis request — from
      `/audit/flux`, both multi-period routes, **and** `/clients/{id}/industry-ratios` (`routes/trends.py`, not in the
      review). No frontend screen read the result, so the save was silent.
- [x] `propose_expectation_actuals` reads only and returns `proposed_actuals` (replaces `expectations_evaluated`), each
      with a signed `capture_token` (HMAC over user, engagement, expectation, actual, source tool, run, 24 h expiry —
      `shared/expectation_capture.py`), so the saved value and its run cannot be substituted by the browser.
      `maybe_record_tool_run` now returns the run id.
- [x] `POST /engagements/{id}/analytical-expectations/capture-actuals` (workspace-gated, like every workspace write):
      one token or a whole run's; all verified before any save; an already-captured expectation is skipped, never
      overwritten. New columns `actual_source` / `actual_source_tool_run_id` / `actual_captured_at` /
      `actual_captured_by` (migration `e879b2d4a6c1`); a typed-in actual records `manual`; clearing clears them.
- [x] Memo: no actual → "not captured" in Actual and Variance; each row says where its actual came from. Expectations
      panel no longer shows `$0.00` for a missing actual. Multi-period page: `ProposedActualsPanel` — "Save actual value
      for <account>" and "Save all N actual values from this run".
- [x] Tests: `test_sprint_879_expectation_capture.py` (run + rerun save nothing; failed run saves nothing; capture one
      records the run; capture all; forged/other-user/Free refused; helper writes nothing; manual source; memo PDF text),
      `ProposedActualsPanel.test.tsx`; 728c tests converted; 878's workspace matrix now covers the capture route.
- Not changed: actuals auto-saved before this sprint stay, with a NULL source (indistinguishable from typed ones).
  The flux page does not send an engagement id, so flux proposals have no UI yet (API only).

**Verification (879b):** expectation/flux/multi-period/trends/memo/snapshot/parity/workspace suites 351 + 103 passed;
memo render snapshot re-recorded (analytical-expectations entries only: "—" → "not captured"); ruff clean; mypy 212;
frontend `tsc` + eslint clean, 4 suites / 32 tests.

**879c — the activity summary accepts any content (DH-05, Critical)**
- [x] Confirmed: `POST /activity/tool-log` took `summary` as a free 2,000-char query string and stored it verbatim;
      `_log_tool_activity` serialised any dict. Only `trial_balance` passes a summary internally
      (`was_balanced`, `anomaly_count`). **No frontend code calls `/activity/tool-log`** — no caller to update.
- [x] `shared/activity_summary.py`: one schema per tool (18 engagement tools + 4 diagnostics), approved scalar
      aggregates only (`extra="forbid"`, strict types, bounded counts, score 0–100); unknown tools, unknown/nested
      fields, lists and strings rejected; the error lists allowed fields and never echoes input. Used by the API
      (typed JSON body `ToolLogRequest`, query parameters gone) and the recorder (raises before writing). The feed
      drops any stored summary that fails it. Migration `f879c3e5b7d2` sets every failing stored summary to NULL (rows
      kept — less destructive than the permitted delete).
- [x] Tests: `test_sprint_879_activity_summary.py` — balances, transaction/payroll rows, file text, nested, key-as-value
      rejected at both entry points with nothing stored; valid round-trip through API and feed; query string ignored;
      no submitted value in logs at DEBUG; migration run against SQLite. 7 failed before the fix.
- [x] `scripts/openapi-snapshot.json` regenerated — covers 879b's fields too (879b's commit left it stale; the drift
      check is advisory in CI).

**Verification (879c):** activity/authorization/route-snapshot/parity suites 86 + 69 passed; OpenAPI drift clean;
ruff clean; mypy 212.

**879d — previewed files outlive 10 minutes (DH-07, High)**
- [x] Confirmed: `_evict_expired()` ran only inside `put()`; `get`/`take` expired only the token read; cap 100 entries,
      no byte limit; per-process cache × 4 Gunicorn workers.
- [x] `shared/preflight_cache.py`: a daemon sweeper per process (started by the first `put`, again after a fork) removes
      expired entries every 15 s, so a preview is gone within 10 min + 15 s with no other cache call; 256 MiB byte
      budget per process (oldest evicted; a file over the budget is not cached → no token); 2 previews per user
      (their oldest evicted). Owner binding and single use unchanged.
- [x] Logout and account deletion: `shared/preflight_purge.request_purge` drops the user's previews in the handling
      worker at once and writes `preview_purge_requests` (user id + time, migration `a879d4f6c8e3`); every other
      worker's sweeper applies it on its next tick (DB read only when that worker holds previews) and deletes requests
      older than the lifetime. Logout purges only after 872's CSRF-owner check has passed.
- [x] Miss path — **already handled, no new response**: the browser always sends the file with the token
      (`buildTrialBalanceFormData` appends `file`), and the route falls back to it on a miss. Pinned by a test.
- [x] Tests: `test_sprint_879_preview_cache.py` — abandoned preview swept with no cache calls (fake clock); fork starts a
      new sweeper; byte budget under six large previews; over-budget file not cached; per-user limit; wrong owner;
      single use; purge_owner; another worker's purge request; logout and deletion through the app; miss completes.
      11 of 12 failed before the fix (the miss test passes on the old code by design).
- Observation for the CEO: because the browser always re-sends the file, the cache saves a re-parse at most, never a
  re-upload. Removing it would retire DH-07 entirely; kept per the 2026-11-16 decision.

**Verification (879d):** preview-cache + preflight/preview/workbook/auth/erasure/CSRF/parity suites 12 + 191 passed;
ruff clean; mypy 212.

**879e — XLSX exports write worksheet XML to temp files (DH-06, High)**
- [x] Confirmed in the installed openpyxl 3.1.5: `ExcelWriter.write_worksheet` builds `WorksheetWriter(ws)` with no
      `out`, so `create_temporary_file()` → `NamedTemporaryFile(prefix='openpyxl.', delete=False)`; removed on success or
      at exit only. Every export wrote one per sheet; a forced worksheet failure left `openpyxl.*` on disk.
- [x] Approach approved by the CEO 2026-11-16: `shared/xlsx_in_memory.workbook_to_bytes` — an `ExcelWriter` subclass
      writes each sheet into a `BytesIO` and `writestr`s it (nothing on disk, nothing to clean up on failure); on import,
      openpyxl's temp-file factory is replaced by one that raises. Used by `excel_generator` (workpaper + financial
      statements), `leadsheet_generator`, `loan_amortization_excel`, and the unused `security_utils.dataframe_to_bytes`
      Excel branch (pandas' writer would have hit the guard). Output unchanged (Excel render snapshot identical).
- [x] Tests: `test_sprint_879_xlsx_no_disk.py` — a Python audit hook records every write-open and temp file during each
      of the four exports with marker names/amounts (none), forced failures inside worksheet writing and inside
      packaging (none), the guard raises on a bypassing `wb.save`, the override is pinned to openpyxl 3.1.5, an AST scan
      finds no other workbook save / `to_excel` in production code, `dataframe_to_bytes` writes nothing. Red before.
- Test-only exemption: `conftest._allow_openpyxl_tempfiles_for_fixtures` lifts the guard for the session, because 15
  test files build XLSX *uploads* with `wb.save()`/`to_excel`. The guard test re-enables it; the bypass scan covers
  production code.

**Verification (879e):** 879e + export/excel/leadsheet/loan/financial-statement/memo-render + every XLSX-fixture suite
640 passed; ruff clean; mypy 212.

**Commit SHA:** 879a `a8970d8a` · 879b `918037d9` · 879c `925fcc05` · 879d `59497810` · 879e `88d3776d`.
**Final verification (2026-11-16, on `88d3776d`, detached check worktree):** full backend suite **10,897 passed /
1 skipped / 0 failed** (18m29s). Alembic single head `a879d4f6c8e3`. Migrations to apply on deploy: `e879b2d4a6c1`,
`f879c3e5b7d2`, `a879d4f6c8e3`.
**Open (CEO):** pre-879 auto-saved actuals with NULL `actual_source` (clear or keep); flux proposals have no UI (the
flux page sends no engagement id); the preview cache never saves an upload (the browser re-sends the file), so removing
it would retire DH-07 — kept per CEO decision; remove `REDACT_LOG_TRACEBACKS` on Render if set (now a no-op).

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
- [x] **Remaining `float` monetary response fields.** (Sprint 894 C.) Sprint 884 moved `MonetaryDecimal` and the payroll / FA /
      inventory / 3WM entry fields to exact numbers; other routes' response schemas still declare amounts as `float`
      (and finding `details` stay floats by design, Sprint 829). Sweep `shared/*response_schemas.py` for amount fields.
- [x] **Next.js upgrade** (see "Then (C)" above). Sprint 894 B.
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

### Sprint 886: Each exported document shows what the screen showed for the same run
**Status:** IN REVIEW (2026-11-19) — code complete on local branch `sprint-886-export-fidelity`, stacked on Sprint 885
(`7251e22c`); not pushed. Merge 883, 884, 885 first. **Priority:** P0 (High findings: a PDF can say "none identified" for an indicator the screen shows as
triggered). **Source:** read-only review at `ef5e567` (OUT-09/10/11/12/14/15/16/18 + comparison table).
**Agents:** Executor, Critic, Accounting Expert.
**Rule (CEO, 2026-11-19):** a value not supplied prints "not available" / "not evaluated" — never 0, Low or "none
identified". Every fix is tested through the real HTTP export route.
**Decided (CEO, 2026-11-19):** three-way match drops the uncomputed score and uses the engine's own Low/Medium/High
classification and wording on screen, PDF and CSV. Asked during the sprint: bank rec tests, score and aging go **on
screen** too; a memo with no client or engagement linked uses FASB **labelled as the default**; scores print with
**one decimal everywhere**.
- [x] **11A / OUT-09 — TB export keeps going concern, analytics and materiality source.** `AuditResultInput` now
      declares `going_concern` (`GoingConcernInput`: triggered/checked counts must match the indicator list, else 422),
      `analytics` (`AnalyticsInput`: typed ratios, category totals as Decimals) and `materiality_source`. PDF: absent
      going-concern data prints "were not evaluated for this report", evaluated-none still prints "No going concern
      indicators identified"; the executive summary adds "Materiality Source" (absent → "Not available"). Excel:
      ratios formatted by an explicit `unit` the ratio engine now emits (`RATIO_UNITS`: ratio/percent/times/days) —
      the old `value > 1` guess wrote a 0.5% gross margin as 50%; a ratio without a unit is written as the screen's
      `display_value` text; analytics absent → "Not available" (not "Insufficient data" / $0); source beside the
      threshold on the summary and flagged-accounts sheets. Tests: `test_sprint886_tb_export_fidelity.py` (9; 7 failed
      first) — real `/audit/trial-balance` upload with a triggered net-liability indicator and an engagement
      materiality, its response posted unchanged to `/export/pdf` and `/export/excel`. Sprint 819
      `route_export_pipeline` re-recorded: the source line, the "not evaluated" sentence, three sheet digests.
- [x] **11B / OUT-10 — bank reconciliation memo and CSV keep tests, score, aging and thresholds.** One result model,
      `BankRecExportResult` (typed `RecTestInput`, `OutstandingAgingInput`, `BankRecCompositeInput`,
      `BankRecThresholdsInput`), for both the memo (`BankRecMemoInput`) and the CSV (`BankRecExportInput`); the page
      sends every result (`bankRecExportBody`). Memo: Section IV reads the engine's real `outstanding_aging` (bank only /
      ledger only, over 10 and 30 days, oldest item) — the old code read an `aging_summary`/`outstanding_deposits`
      structure the engine never emits; methodology prints "Thresholds applied" (materiality, performance materiality,
      tolerances, each with "entered for this run" / "Paciolus default"); a missing score prints "Not available" and
      "Not evaluated", never LOW (0/100); score one decimal beside the tier. CSV gains RECONCILIATION TESTS, OUTSTANDING
      ITEMS AGING, DIAGNOSTIC SCORE and THRESHOLDS APPLIED sections. Engine `tests_run` was a hard-coded 8 for 5 tests;
      now `len(rec_tests)` (old test rewritten). **CEO decision 2026-11-19: show them on screen** — new
      `BankRecTestsPanel` (score, tier, per-test counts, aging). Shared: the memo Proof Summary takes per-tool
      `ProofFigures` and prints "Not available" for a figure the export did not carry (was 0%; two old tests encoded
      that and were rewritten); `mean_confidence` / `meanConfidence` give screen and PDF one column-confidence rule;
      bank rec's screen proof uses the run's real tests. Tests: `test_sprint886_bank_rec_export.py` (6; 5 failed
      first) — real `/audit/bank-reconciliation` with stale, high-value and unmatched items and custom thresholds;
      Jest `BankRecTestsPanel.test.tsx` (4) and two export-body tests in `BankRecPage.test.tsx` (failed on the old
      page). Sprint 819 `route_form_exports` re-recorded (the four new CSV sections only).
- [x] **11C / OUT-11 — three-way match: no uncomputed score; the engine's classification everywhere.** The memo read
      `composite.get("score", 0)` from a composite the engine never emits, so every memo printed "(0/100)" and "Composite
      Diagnostic Score: 0.0/100", and renamed MEDIUM → MODERATE, HIGH → ELEVATED. Removed: the score, the tier mapping,
      the never-reached Results Summary and Key Findings sections (both read the absent composite) and
      `compute_twm_diagnostic_score` (no caller). Memo, CSV and screen now say "Risk Assessment: LOW / MEDIUM / HIGH"
      (`summary.risk_assessment`), and the memo states the engine's rule; missing → "Not available"/no claim. Sections
      renumbered I–VII. Proof Summary uses the screen's figures. **Found on the way:** unmatched documents are a
      free-form dict in the response, so their Decimal amounts left the API as strings — the memo 500'd on any unmatched
      PO or invoice, and the screen's unmatched panel showed $0.00; now exact JSON numbers (as Sprint 884 did for lead
      sheets). Tests: `test_sprint886_twm_classification.py` (7, Low/Medium/High through `/audit/three-way-match`, memo
      and CSV; all failed first, High with the 500); Jest `MatchSummaryCardRisk.test.tsx` (3). `test_twm_memo.py`
      encoded the old contract (MODERATE mapping, score function, composite findings): those tests were replaced by
      tests of the engine's levels.
- [x] **11D / OUT-12 — AP, payroll and AR supplemental schedules reach the memo.** Dropped at three layers, not one:
      the analysis **response models** did not declare them (so the browser never received them), the pages did not send
      them, and the export models did not declare them. Now typed at each layer: AP `duplicate_payment_summary`; payroll
      `payroll_register_total`, `department_summary`, `headcount_rollforward`; AR `aging_schedule` (sub-ledger runs).
      The payroll department table summed exact Decimals into a float and 500'd once the schedule arrived — summed as
      Decimal. Tests: `test_sprint886_supplemental_schedules.py` (7; all failed first) — real AP / payroll / AR runs,
      their responses posted to the memo routes, each section and its figures checked; invalid schedules are a 422.
      Jest: the shared page-scenario harness gains `memoBodyFields` (each page must send the schedule) — 3 failed on
      the old pages.
- [x] **11E / OUT-14 — payroll completeness on the 0–100 scale.** `assess_payroll_data_quality` divided the shared
      0–100 score by 100, so a complete register showed as 1% in the badge, proof summary and memo. Now 0–100 like every
      tool (rounded to one decimal like the others). Range enforced: `DataQualityResponse` / `ARDataQualityResponse`
      (`ge=0, le=100`) and every testing export model (`_CompletenessInRange`: 422 outside 0–100). The memo scope line
      "Data Quality Score" prints "Not available" when not supplied (was 0%). Tests:
      `test_sprint886_payroll_completeness_scale.py` (7; 4 failed first — 100 not 1, the memo at 0/50/100 exactly, 150
      refused); Jest `PayrollCompletenessScale.test.tsx` (badge and proof summary at 0/50/100; the screen code was
      already right — the API scale was the bug).
- [x] **11F / OUT-15 — AR memo column confidence matches the screen.** The shared Proof Summary read
      `result["column_detection"]`; AR carries `tb_column_detection` and `sl_column_detection`, so every AR memo said 0%.
      The AR memo now passes `ProofFigures` with `mean_confidence(tb, sl)` (the screen's rule: mean of the detections
      carried, one alone on a TB-only run); `generate_testing_memo` takes `proof_figures`. No detection: "Not available"
      on both (the screen showed 0.00). Tests: `test_sprint886_ar_column_confidence.py` (3, through `/export/ar-aging-memo`:
      0.8 + 1.0 → 90%, TB-only 0.8 → 80%, none → Not available; 2 failed first); Jest `ARProofColumnConfidence.test.ts`
      (0.90 / 0.80 / Not available). Screen shows 0.90 and the PDF 90%: the same figure in each surface's existing
      format.
- [x] **11G / OUT-16 — documents name the materiality amount, its purpose and its origin.** Trial balance: the page
      sends `materiality_origin` ("default" / "engagement" / "entered"); `resolve_materiality_basis` checks each claim
      (the user's **saved** practice setting — the settings API returns a fixed $500 even when nothing was saved, so only
      a stored `default_materiality` counts; the engagement's performance materiality; the $500 software default) and
      reports anything it cannot confirm, or no claim, as entered for this run. The response carries
      `materiality_basis` {amount, purpose, origin}; `materiality_source` is now the origin (was "manual" for any
      amount). PDF and Excel print e.g. "Test threshold — Saved firm setting", "Performance materiality — Engagement";
      an analysis without a basis prints "Not available" (its old "manual" said nothing true). Bank rec (done in 11B):
      materiality and performance materiality each print "entered for this run" or "Paciolus default". Tests:
      `test_sprint886_materiality_origin.py` (9: first-use default, saved firm setting, engagement, explicit entry —
      each named in PDF and Excel; unconfirmable claims → entered; all failed first); Jest
      `useTrialBalanceUploadOrigin.test.ts` (4: the hook sends the right origin) and a form-data case.
- [x] **11H / OUT-18 — memos use the client's reporting framework and say which.** Every memo request may carry
      `engagement_id` (or `client_id`) — `WorkpaperMetadata`; the pages send the linked engagement
      (`withLinkedEngagement`: the shared testing-export hook, bank rec, the four TB memos, multi-period, flux). The memo
      route checks access (404 for an engagement or client the user may not see), resolves the framework with
      `resolve_reporting_framework` (`shared/export_framework.py`), passes `resolved_framework` to the generator — the
      seven testing generators gained the parameter — and every memo's scope prints "Reporting Framework: GASB — the
      client is a governmental entity" (or "FASB (US GAAP) — set on the client", …). **Nothing linked (CEO decision):**
      "FASB (US GAAP) — default; no client or engagement was linked to this run". Tests:
      `test_sprint886_reporting_framework.py` (10; all failed first) — otherwise identical FASB and GASB engagements
      through `/export/ap-testing-memo` and `/export/bank-rec-memo` get different scope text and references; client_id
      alone resolves; another user's engagement is a 404; all 18 memo generators take the framework and all memo inputs
      can name an engagement or client. Jest `linkedEngagement.test.ts` (3).
- [x] **11I — labels say what each figure counts.** (1) TB PDF: "Above/Below Materiality" were the high/low
      **severity** counts and medium was missing — now "High / Medium / Low Severity" (all three); counts the analysis
      did not carry print "Severity counts: Not available" (was a guess from material/immaterial). The screen's risk
      dashboard added low into "Medium" — now three badges. (2) Testing tools: `total_flagged` counts distinct rows,
      severity counts and the CSV count flags — memo "Payments Flagged (distinct payments)" + "Flags Raised (one per
      test per payment)" + a one-line explanation; CSV summary "… Flagged (distinct …)", "Flags Raised (one row above
      per flag)", "Flag Rate (distinct flagged / total)"; screen "… flagged (distinct)" and "Flags H / M / L (one per
      flag)". (3) Fixed assets: the roll-forward, depreciation-rate and category sections read ten fields the engine
      never computes (and the export dropped), so they printed only in the sample memo, with an "FY2025" fallback —
      **removed** (the tool has no data for them; category composition could be computed from the register later),
      with the sample data and the six tests that fed them made-up fields. (4) Multi-period: the page now sends the
      dormant account names (a count without names prints "Not available"); the memo states that each lead sheet's
      account detail is on screen and in the movements CSV, not in the memo. (5) **One score format (CEO): one
      decimal everywhere** — screen score card (`CountUp decimals`), every "TIER (n.n/100)" label (memo base, TB PDF,
      anomaly summary, engagement dashboard, multi-period), CSV already .1f. Tests: `test_sprint886_labels_and_units.py`
      (6; 5 failed first), `test_sprint886_fixed_asset_sections.py` (2), `test_sprint886_multi_period_detail.py` (3; 2
      failed first — the third failed on the page, see Jest); Jest `RiskDashboardSeverity.test.tsx`,
      `TestingScoreCard.test.tsx` (10.5 stays 10.5), `useMultiPeriodMemoExport.test.ts` (dormant names; failed on the
      old hook). The bank-rec sample data now uses the engine's real aging and threshold shapes.
      Also in this commit: snapshot re-records for all of 11B–11I (`memo_render_snapshot.json`; Sprint 819
      `route_export_pipeline`, `route_testing_exports`, and engine `payroll`/`payroll_ghost` for 11E's 0–100 scale —
      every diff read: framework line, units, decimals, removed/added sections, page breaks); OpenAPI snapshot
      regenerated (additive only); `RecFlaggedItemInput` named (a private base showed in the API schema); three mypy
      fixes to 11B/11H code.
**Commits:** `b8c86f34` (11A), `fc49317b` (11B), `d506d883` (11C), `c94424ce` (11D), `865e99dc` (11E), `86861042`
(11F), `2a564021` (11G), `0f951860` (11H), 11I + record: see the commit after `0f951860`. Commits 11B–11H were split
from one working tree by hunk; each passed the pre-commit Jest gate, and the backend was verified on the final tree.
**Verified (final tree):** backend full suite 11,239 passed, 3 failed — two were old-contract tests of 11C found only
by the full run (`test_export_pdf_contract` required a TWM "Composite" label; `test_export_testing_routes` sent
"Low Risk" as the engine value) and are rewritten in the 11I commit (50/50 pass), plus the pre-existing Sprint 819
`test_engagement_export_routes_unchanged` (fails on `main`). ruff clean on every changed file; mypy 288 = the Sprint 885
baseline (ten new errors found and fixed). Frontend: Jest 219 suites / 2,138 passed; `tsc` and eslint clean; `next
build` compiled every route (`ƒ`) — first run exited 1 on Next.js's `SecurityFatalError` advisory gate, retry passed.
OpenAPI snapshot: additive only.
**Samples regenerated (follow-up commit):** `sample-reports/` (all 21) and the public `frontend/public/samples/paciolus-sample-je-testing-memo.pdf` (same Sprint 865 synthetic file, now run through `/audit/journal-entries` and `/export/je-testing-memo` as the page does; stamped as before). The sample generator's TB data still carried the OUT-09 mislabel (3 "high"/5 "low" were material/immaterial counts; the eight items are 3 high, 1 medium, 4 low) and no materiality basis; its AR data carried `column_detection` instead of the TB and sub-ledger detections; both fixed so no sample prints "Not available". Memo render snapshot re-recorded for those two (tb_diagnostic, ar_aging, Excel workpaper).
**Open for the CEO:** (1) done, see above; (2) fixed-asset category composition could be computed from the register's category
column if wanted (removed sections had no data source); (3) the payroll sample still feeds `gl_salaries_wages`, which
the engine never computes — same class as the removed fixed-asset sections, not in this review.

### Sprint 887: Generated wording states no audit conclusions, matches the results, cites correctly
**Status:** IN REVIEW (2026-11-20) — code complete on local branch `sprint-887-generated-wording`, stacked on Sprint 886
(`57c79d91`, which another session committed onto this branch after it was cut from `61312c4e`); not pushed. **Priority:** P0. **Source:** read-only review at `ef5e567` (OUT-07/08/13/17/20/21/22/29/30/31/32 +
comparison table). **Agents:** Executor, Critic, Accounting Expert.
**Position (CEO, 2026-11-20):** Paciolus runs tests and reports what they flagged; the auditor evaluates and concludes.
Nothing flagged is "no exceptions flagged" — never passed, clean or verified. Software output is "items flagged", not
"findings". Suggested procedures are suggestions. Titles of standards and disclaimers reserving judgment stay.
**Decided (CEO, 2026-11-20):** engagement indicator = "Follow-Up Item Points", bands "Under 8 points" / "8–14 points" /
"15 points or more" (points only, no /100, no risk or tier words, no high-count overrides); every tier's summary text
replaced (not only Low); expense-category % change and threshold result computed by the engine and shown on screen, CSV
and PDF ("Risk Level" and "Explanation Req." removed); `tool_runs.flag_count` added (nullable).
- [x] **12A / OUT-07 — multi-period memo summary states results, not conclusions.** All four tier texts (Low: "No
      additional substantive procedures are indicated"; the others recommended procedures) replaced by one summary:
      score and tier, movement counts, the thresholds applied, "The auditor evaluates these results." The engine's
      `active_thresholds` now includes `materiality_threshold`; `MultiPeriodMemoInput.active_thresholds` is typed and
      the page sends it (absent → "Not available"; no materiality → "none supplied"). Tests:
      `test_sprint887_multi_period_summary.py` (7, all failed first — real `/audit/compare-periods` → memo, Low with
      and without flags, every tier); old BUG-002 tests that required the conclusion wording rewritten; Jest case in
      `useMultiPeriodMemoExport.test.ts` (failed on the old hook). Memo snapshot and OpenAPI (additive) re-recorded.
- [x] **12B / OUT-08 — accrual memo: above/below the threshold and where it came from.** "…meets the 50% minimum
      threshold, indicating accrual balances are within a reasonable range…" / "…may require additional completeness
      procedures" / "the engagement team should perform additional completeness procedures" replaced by "The ratio is
      n%, at or above / below the t% threshold. Threshold source: Paciolus default (a software setting, not a
      professional standard) | entered for this run." The route's `threshold_pct` is now optional (None = default), the
      engine reports `threshold_source`; the label "Meets Minimum Accrual Threshold (≥50%)" (hard-coded 50 even for
      another threshold) is "At or Above Threshold (≥t%)". The flagged-items register's "Action Required" directives
      ("Perform additional completeness procedures", "Inquire … regarding completeness") are suggestions under
      "Suggested Procedure". Tests: `test_sprint887_accrual_threshold_wording.py` (4, all failed first — real
      `/audit/accrual-completeness` above/below/entered/absent → memo).
- [x] **12C / OUT-13 — testing memo summaries agree with what the tests flagged.** The seven memos chose a per-tier text
      (`risk_assessments`); Low said "No anomalies exceeding the configured thresholds were detected" even with flags,
      the others said what to review or investigate. All 28 texts removed; `build_testing_results_summary` (shared
      template) prints the score and tier, "k of n tests executed flagged d distinct <units> (f flags: h high, m
      medium, l low severity)" — or "No exceptions flagged: the n tests executed flagged no <units>." only when no
      executed test flagged anything — skipped tests, then "The auditor evaluates these results." ISA 501 was cited
      only inside the inventory High text ("physical inventory counting"): registry usage updated. Tests:
      `test_sprint887_testing_memo_summary.py` (19, all failed first — 7 tools × Low with/without flags, other tiers,
      results absent, a real AP run); three old tests that pinned the tier texts replaced. Memo snapshot and Sprint
      819 `route_testing_exports` re-recorded (summary wording and page reflow only).
- [x] **12D / OUT-17 — each flag keeps its test and its suggested procedure.** The memo guessed a flag's test from
      its words (`_resolve_test_key`, removed). `follow_up_procedures.PROCEDURES` is keyed by (ToolName value, the
      `test_key` the engine emits): JE `round_amounts` now finds its text (the library had `round_dollar_amounts`); AP
      round-dollar, revenue Benford/duplicates, fixed-asset and inventory missing-fields/negative-values get their own
      texts, not JE's. Selection: CRC-32 of (client, tool, test) — not `hash()`, not the flag's position; the "As a
      priority follow-up action," prefixes are gone. Engines emit `composite_score.top_flags` [{tool, test_key, text}]
      (declared on the response models so the page forwards them); payroll flags carry `tool`, `test_key`,
      `employee_id`; bank-rec tests carry `test_key` (the memo's name→key map is gone). A text-only flag is listed with
      no suggestion. **Drafted for the CEO:** PR-T12 and PR-T13 entries (see the summary). Samples carry explicit ids
      (inventory's sample memo went from 0 to 4 suggestions, AR 2→3). Tests: `test_sprint887_procedure_identifiers.py`
      (13; collection failed first on the new API) — library keys vs engine keys, a "Benford Law Gross Pay" employee,
      reorder + rename, three processes with different `PYTHONHASHSEED`, a real AP run. The full suite also found three
      tests still passing `risk_assessments` (12C), the aggregator mocks without `test_key`, and the 12A thresholds
      dict (now with `materiality_threshold`) — all updated here. Engine and route snapshots re-recorded: additions
      of `top_flags` / ids only (checked by stripping them), memo text = suggestion choice only.
- [x] **12E / OUT-20 — the anomaly summary reports each tool's real state.** New nullable `tool_runs.flag_count`
      (migration `c3e7a1f9d524`), written by the testing tools, AR (`total_flagged`), TB (`anomaly_count`), multi-period
      (material + significant) and bank rec; other tools record none. One "Tool Results" table per catalog tool, from
      its latest successful run: Failed / Not evaluated / Results unavailable / No exceptions flagged / n items flagged,
      each with its "captured follow-up items". Removed: "Tools with Clean Results", "No anomalies identified.
      Population passed all configured test thresholds.", "Total Anomalies", "Assessments Completed: 0", the
      "Unexecuted tools may represent coverage gaps requiring alternative procedures" note, the narrative telling the
      auditor to prioritize High items, and the DRAFT note. Section III is "Practitioner Worksheet — for the firm to
      complete", blank by default; `POST …/export/anomaly-summary?fill_from_saved=true` fills disposition and notes from
      Paciolus with the date each was last recorded. **No page offers this report today** (API only). Tests:
      `test_sprint887_anomaly_summary_states.py` (4, all failed first: only-failed runs, flagged run with no items, a
      rerun, a true zero, an unrecorded count, worksheet default/filled).
- [x] **12F / OUT-21 — Follow-Up Item Points.** Replaces "Engagement Risk Indicator: TIER (n/100)": points = 3/2/1 per
      high/medium/low captured follow-up item + 1.5 per catalog tool not run (rounded down); bands by points alone
      ("Under 8 points" / "8–14 points" / "15 points or more"; the 1-high and 3-high overrides removed, so every
      band is reachable); weights, band edges and the per-line breakdown printed. `RISK_TIER_BASIS_NOTE_ENGAGEMENT`
      removed. Tests: `test_sprint887_follow_up_points.py` (12; collection failed first) — zero, coverage only, each
      edge, overrides gone, a large count, the memo text; old tier tests in `test_anomaly_summary.py` replaced. The
      sample anomaly summary now carries run status and flag counts (payroll zero, bank rec failed then rerun).
- [x] **12G / OUT-22 — the population memo states skew and outliers only from a statistic.** The memo always called
      the maximum "a significant outlier at {max/mean}x the mean", 500'd on an all-zero population (division by zero)
      and called mean = median "left-skewed". The engine now reports `skewness` (adjusted Fisher–Pearson G1; None
      below 3 balances or with no dispersion), `upper_fence` (Tukey P75 + 1.5 × IQR) and `accounts_above_upper_fence`;
      the memo states them, "Every account balance … is $0.00" for all-zero, "All n balances equal $x; there is no
      dispersion" for uniform, and "Skewness and outlier statistics: Not available." when an old payload lacks them;
      the "high/moderate dispersion" judgment from CV > 100% is gone (the CV is stated). Tests:
      `test_sprint887_population_statistics.py` (5, all failed first — real `/audit/population-profile` → memo:
      all-zero, uniform, symmetric, skewed, old payload). Sample given consistent statistics; snapshot re-recorded.
- [x] **12H / OUT-29 — every signature block is off by default; no invented dates.** One switch,
      `include_signoff` (default False): the flux expectations memo printed its sign-off table (with a Partner row)
      regardless — now only when enabled, with only the supplied names; the analytical-expectations and SUM-schedule
      workpapers always printed "Auditor: ____ Date: ____" — now behind the same switch (`SignoffRequest`; the two
      engagement routes take `include_signoff`, `prepared_by`, `reviewed_by`, `workpaper_date` query parameters).
      Their "Sign-Off" headings are "Completion Status" (the DRAFT/completion note stays). Dates: the shared memo
      block, the TB/financial-statement PDF section and both Excel sign-offs filled today's date when none was
      supplied, the reviewer's included — now the supplied date beside the preparer only, blank otherwise. Tests:
      `test_sprint887_signoff_off_by_default.py` (10; 9 failed first). Memo snapshot re-recorded (block removed).
- [x] **12I / OUT-30 — leftover vocabulary, and a scan that keeps it out.** TestResultGrid "Clean" → "No exceptions
      flagged"; BenfordChart "Pre-check not passed" → "Requirements for the analysis not met"; population memo
      "Prechecks not passed." → "The requirements for the analysis were not met."; sampling memo "clean sample" → "a
      sample with no misstatement found"; preflight "verified against debit/credit pair" → "compared with the
      debit/credit pair"; TB diagnostic factors "additional/minor findings", "Material exceptions (n findings)" →
      "items flagged"; all 163 procedure and benchmark texts in `follow_up_procedures.py` open "The auditor may
      consider" with no Obtain/Verify/Investigate/must (163-row old/new table: `reports/sprint-887-wording.md`); the
      TB diagnostic copy of the "To further substantiate the finding," prefix rotation removed. Tests:
      `test_memo_banned_phrases.py` now also bans clean / (not) passed / verified / finding(s) and scans the procedure
      library, TB diagnostic constants, preflight labels and the anomaly summary, plus a rule that every suggestion
      opens "The auditor may consider" (failed first on 6 files + the rule; "Passed AJE", the audit term, allowed);
      Jest `resultVocabulary.test.ts` scans 23 result-component folders (failed first on exactly the two strings).
      **Not changed (outside the brief, follow-up):** the TB diagnostic and accrual/expense engines' own suggested
      procedures are still imperative.
- [x] **12J / OUT-31 — ASC 606-10-32 is Measurement.** Title was "… — Contract Costs" (that is ASC 340-40, which no
      procedure cites). Paragraphs checked against what the revenue tests and procedures cite: 25-13, 25-23 and 25-30
      were outside the listed "25-1 through 25-5" — now listed; 32-33 sits in the allocation paragraphs, now listed as
      "32-28 through 32-41". Tests: `test_sprint887_citations.py` (2, both failed first — the title, and every cited
      606-10 paragraph appears in the YAML). Memo snapshot and `route_testing_exports` re-recorded (title only).
- [x] **12K / OUT-32 — compensated absences cite GASB 101 and 16 by period.** Statement 16 was listed as "Current".
      Now: Statement No. 101 "Compensated Absences", "Current — fiscal years beginning after December 15, 2023";
      Statement No. 16, "Superseded by Statement No. 101 — applies to fiscal years beginning on or before December 15,
      2023". The memo has no reliable fiscal-year start to pick one, so both print with their periods. Tests: 3 in
      `test_sprint887_citations.py` (2 failed first; one renders a GASB payroll memo).
- [x] **12L — expense category: one computation, the same bands and thresholds on screen, CSV and PDF.** The PDF
      computed its own % change, HIGH/MODERATE/LOW "Risk Level" and "Explanation Req." from 10%/20% thresholds
      (`_assign_risk`, removed), plus a ⚠ marker over 15%, none shown elsewhere. The engine now emits `pct_change`,
      `change_band` ("Change ≥ 20% and over materiality" / "Change ≥ 10% or over materiality" / "Change < 10% and
      within materiality"; none when % change cannot be computed) and `change_thresholds`; the screen gains % Change
      and Change Band columns and a thresholds line, the CSV gains both columns and a "Change Band Thresholds" row,
      the PDF prints the bands and thresholds ("Paciolus defaults"), its Items Flagged table shows "Basis" instead
      of Risk/Priority, its procedures drop the Priority column, and the decomposition flag states its own 10%/15%
      thresholds and is a suggestion. % change shows two decimals everywhere (9.987% read "+10.0%" beside "< 10%").
      Tests: `test_sprint887_expense_category_bands.py` (9, all failed first — real route → screen, CSV, PDF; band
      cases); Jest `ExpenseCategoryChangeBand.test.tsx` (3; 2 failed first); old `_assign_risk` / arrow tests
      rewritten. Sample bands derived with the engine's `change_band`; snapshot re-recorded.

**Commits:** `7bcc0a04` (12A), `72c1467d` (12B), `14139462` (12C), `27050859` (12D), `c2baa10f` (12E + 12F), `503d5e6a`
(12G), `c7a06ff5` (12H), `970a65c0` (12I), `25e000e6` (12J), `41e37fd9` (12K), `5ee0ae1c` (12L); record + four contract
tests + one mypy cast: the commit after `5ee0ae1c`.
**Verified (final tree):** backend full suite 11,317 passed, 5 failed → the four were contract tests of intended changes
(TB factor name 12I, expense CSV header 12L, flux section label 12H, recorder signature 12E), updated in the record commit
(133/133 pass); the fifth is the pre-existing Sprint 819 `test_engagement_export_routes_unchanged` (fails on `main`; its
golden will also differ by the 12E anomaly-summary changes once re-recorded). An earlier full run (after 12D) found
three tests still passing `risk_assessments` (12C), the aggregator mocks and the 12A thresholds dict — fixed in 12D.
ruff clean on every changed file; mypy 288 = baseline. Frontend: Jest 2,145 passed (pre-commit gate), `tsc` and eslint
clean on changed files; `next build` compiled every route (`ƒ`; `/icon.png`, `/sitemap.xml` static) — first run exited
1 on Next.js's `SecurityFatalError` advisory gate, retry passed. OpenAPI snapshot regenerated (additive only).
**Open — CEO**
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
- [x] Re-record Sprint 819 `test_engagement_export_routes_unchanged` (fails on `main` already; the 12E anomaly-summary
      changes alter its golden too). Done in Sprint 893 (H).
- [x] Follow-up (outside this brief): the TB diagnostic, accrual and expense engines' own suggested procedures are still
      imperative — reword to "The auditor may consider…" and extend the `test_memo_banned_phrases.py` procedure rule.
      Done in Sprint 893 (L); CEO review table `reports/sprint-893-procedure-wording.md`.
- [x] Follow-up: the bank-rec memo's "No items requiring further investigation were identified." states a conclusion —
      reword to "No exceptions flagged" form. Done in Sprint 893 (I); the phrase is now banned in memo sources.

### Sprint 888: What we publish about plans, billing and data handling matches the code
**Status:** IN REVIEW (2026-11-20) — code complete on local branch `sprint-888-published-claims`, stacked on Sprint 887;
legal copy on `counsel-redline-863` (`e4175662`, do not merge without counsel).
**Priority:** P0 (launch copy). **Source:** CEO brief 13 (review AZ-12, TQ-08 + plan and data-handling tables, at
`ef5e567`). **Agents:** executor, guardian (copy vs code), critic (no new promises).
**Decisions (CEO):** paid features pause at the first failed payment (copy changes, not behaviour); bulk upload will
be built — until it analyses files, Terms does not list it and the endpoint says it is not available; approved data
statement replaces "Zero-Storage" wording. Privacy/Terms/DPA edits go in one legal-copy commit on top of
`counsel-redline-863`, not on this branch.

- [x] 13A: FAQ + every dunning email say paid features pause at the first failed payment, cancellation later, access
      returns on payment, records stay readable. Webhook-driven entitlement test + FAQ/email timing copy check.
- [x] 13B: FAQ upload unit (one analysis run), monthly reset, enabled formats (README, FAQ, USER_GUIDE), shared-link
      24 h / 48 h, bulk upload (endpoint + todo feature), runbooks superseded, retired tier aliases.
      Done: bulk upload 501 + build plan; FAQ/README/guide facts (`test_sprint_888_plan_facts.py`); both pricing
      runbooks marked superseded; rate-limit aliases starter/team/organization and "Team" plan comments removed.
- [x] 13C: 10-minute cache claim, Data Handling contradictions, retired wording + old sample PDFs, log content claim,
      closure/cancellation report, "what we keep" drafts, subprocessor list.
      Done: three parser log lines no longer carry the filename, OFX currency/account/type/dates or IIF dates
      (`test_sprint_888_logs_carry_no_upload_content.py`).
      Data Handling v3.2 (flagged names, adjusting entries, rate rows, Key Value) and Subprocessor List v2.2 (S3 logos,
      Key Value security counters, SendGrid contact form) corrected.
      README and three OpenAPI descriptions use the approved statement; guard extended to README, the API
      snapshot and the brief's retired phrases. The 22 sample PDFs carry no retired wording (checked).
- [x] 13D: billing tests use real `/billing/usage` shapes and the real UsageMeter; misleading test renamed;
      Professional 499 allowed / 500 refused.
- [x] Legal-copy commit (Privacy, Terms, DPA) on `counsel-redline-863`; each change listed for the CEO.

**Found (13A), for the CEO — not fixed:** `invoice.paid` sets the subscription ACTIVE but leaves `user.tier` on Free,
and its write moves `updated_at`, so Stripe's `customer.subscription.updated` for the same recovery (same second or
earlier) is skipped as stale. A subscriber who pays after a failure can stay on Free. Pinned by a strict xfail in
`tests/test_sprint_888_payment_failure.py`. Proposed fix: `invoice.paid` restores `user.tier` from `sub.tier` (and org
members) when it moves PAST_DUE → ACTIVE.

**Review (2026-11-20).** Commits: `767fa4cc` 13A · `0759f02c` 13D · `6e1c65e2` bulk 501 · `d0d3bae5` plan facts ·
`004cf558` runbooks · `7fdd43eb` tier aliases · `3be7cd65` parser logs · `ab86bd97` Data Handling + Subprocessors ·
`f005917f` README/API wording · (record commit) history-page filename wording. Legal copy `e4175662` on the redline.
Verification: backend `-m "not slow"` 11,335 passed, 1 xfailed (the recovery defect above), 1 failed — Sprint 819
`test_engagement_export_routes_unchanged`, already failing on `main` (Sprint 887 follow-up); frontend Jest 2,145+
(pre-commit gate) and `next build` (second run; first exits on Next's `SecurityFatalError` advisory gate).

**Open — CEO** (detail in the session summary)
- [x] Recovery defect above: approve the `invoice.paid` fix. Fixed in Sprint 893 (A).
- [x] Preview cache: unused entries are evicted lazily (next preview or restart), so "held for up to 10 minutes, then
      released" is not strictly true. Fix the code (a one-minute sweep) or reword to "can be reused for up to 10 minutes".
      Fixed in Sprint 893 (C): a 30-second sweeper.
- [ ] Terms and DPA promise deletion within 30 days of termination; no job does it (erasure is manual or self-serve).
- [x] Firm logos stay in S3 after account erasure (`erase_account` deletes the row, not the object). Fixed in
      Sprint 893 (D).
- [ ] Confirm on Render: `S3_BUCKET_NAME` set (logos), `FORMAT_ODS_ENABLED` unset/false (copy now omits ODS), no
      `RATE_LIMIT_{STARTER,TEAM,ORGANIZATION}_*` variables (now ignored).
- [x] Seven stale `.docx` exports under `docs/` still carry "Zero-Storage" (USER_GUIDE.docx, ARCHITECTURE.docx, …):
      delete or regenerate. Deleted in Sprint 893 (J), as Sprint 845 did for the compliance exports.
- [ ] Until `counsel-redline-863` merges, Privacy/Terms on this branch still say "up to 48 hours" and list bulk upload.

### Sprint 889: Tests that fail when a number or a rule is wrong
**Status:** IN REVIEW (2026-11-20) — code complete on local branch `sprint-889-tests-that-fail`, stacked on
Sprint 888, except 14G (blocked on a CEO go-ahead).
**Priority:** P1. **Source:** CEO brief 14 (review TQ-04/06/07/09/10/14/15/16 at `ef5e567`). **Agents:** critic
(could this test pass with the bug?), executor, guardian (14G schema). Expected values are worked out by hand; each new
test is shown to fail under a temporary mutation, then the mutation is reverted.
**Decision (CEO):** NOL recognition is out of scope; a loss year states that no NOL deferred tax asset or valuation
allowance is computed and never presents the provision as complete. (Closes Sprint 826 B1.)

- [x] 14A heatmap fixed expectations (engine, API, CSV) — 3.000 / 4.000 / materiality 90 / count 2.
- [x] 14B multi-period + sampling cases assert the account and result; generators derive change from prior.
      **Found (CEO):** `movement_type` is classed on the debit-positive net, so revenue that falls 60% shows the
      "Increase" badge and counts under "Increases" beside a -60% display change (strict xfail
      `test_revenue_that_falls_is_labelled_a_decrease`). Also: the sign-change generator recorded the current AR
      (83,900.84) as its prior (78,412.00) — corrected.
- [x] 14C if-guarded assertions become assertions.
- [x] 14D frontend activity mapper + JE success case from real response shapes.
- [x] 14E lease 173.55 / 11,677.03, systematic selection rows 5…95, cent-level book-to-tax.
- [x] 14F loss-year limitation in result and every output; scope note says no NOL carryforward input.
- [ ] 14G PostgreSQL job runs `alembic upgrade head`; enum round-trip; schema parity; upgrade from existing rows.
      **BLOCKED — CEO go-ahead needed (brief: stop on a real mismatch).** Probed on an embedded PostgreSQL 16
      (pgserver, scratch only): `alembic upgrade head` on an empty database has never completed. Each failure was
      patched in a scratch copy only (reverted) to find the next:
      (1) `a7b8c9d0e1f2` adds `clients.reporting_framework` / `entity_type` without creating the enum types
          (`type "reportingframework" does not exist`);
      (2) `d9e0f1a2b3c4` adds enum value `solo` and uses it in the same transaction (`UnsafeNewEnumValueUsage`; the
          chain also runs as one transaction, so `c4d5e6f7a8b9`'s `starter` hits the same rule), and adds `solo` to
          `usertier` but not `subscription_tier`;
      (3) `c1d2e3f4a5b6` writes `'enterprise'`, a label the rebuilt `usertier` no longer has.
      Production was built by `create_all` and stamped, so it is unaffected today; a disaster-recovery rebuild from
      migrations is not possible. Plus the known label drift (ORM writes `FREE`, migrations create `free`). Proposed:
      a squashed baseline migration generated from the models (labels decided once), the old chain kept for history,
      then the round-trip and parity tests in the PostgreSQL job.
- [x] 14H mapping E2E in PR CI; financial-correctness slow tests before merge; workflow check.
      Both specs now run on every PR against a local backend seeded with a fixed account
      (`scripts/seed_e2e_user.py`; no secrets — the repo has none, so both specs used to skip). Slow tests: none of
      the 7 checks financial results (all timing/memory), so nothing needed moving before merge.
      **Found (engineering):** run locally (Chromium, `next start` + uvicorn on SQLite), login and export pass but the
      three upload tests fail — after a full-page navigation the session is gone (`/auth/refresh` 401, no 200s),
      though the same refresh succeeds from curl. Same symptom as Sprint 868; investigate there. The job stays
      advisory, so this does not block merges. The `.test` email domain is rejected by the validator — the CI
      account uses `example.com`.

**Review (2026-11-20).** Commits: `3868d262` 14A · `8bdb1dc1` 14B · `31f68b94` 14C · `b50686d9` 14D · `b5e43307` 14E ·
`54b84081` 14F · `58b2d9a2` 14H · (record commit) Sprint 819 book-to-tax golden re-recorded for 14F's two added fields
and the CSV's Limitations rows (diffed: nothing else changed). Every new test was shown to fail under the brief's
mutation (scratch script, file restored after each run); for 14A, 14B, 14C and the MUS shift in 14E the old suite
passed the same mutation. Verification: backend `-m "not slow"` 11,362 passed, 2 xfailed (CEO findings in 888 and
14B), 1 failed — Sprint 819 `test_engagement_export_routes_unchanged`, already failing on `main`; frontend Jest via the
pre-commit gate on every commit.

**Open — CEO**
- [ ] 14G go-ahead: rebuild the migration chain (squashed baseline from the models) so a fresh PostgreSQL can be built.
- [x] 14B finding: should falling revenue be labelled "decrease" (movement_type on the display basis)? Yes —
      fixed in Sprint 893 (B).
- [ ] 14H: three upload E2E tests fail locally because the session does not survive a page load. Cause found by
      Sprint 874 (#327): `/auth/refresh` needs a CSRF token the page loses on reload — re-run after it deploys.

### Sprint 890: The edges between frontend, API and background work
**Status:** IN REVIEW (2026-11-20) — code complete on local branch `sprint-890-edges`, stacked on Sprint 889.
**Priority:** P1. **Source:** CEO brief 15 (review ST-08/05/10/11/03 at `ef5e567`), in the brief's order. **Agents:**
executor, critic (no new framework), guardian (sessions never shared across threads). 15E absorbs Sprint 821's
offloading items and brief 17B's webhook move.
**Decision (CEO):** 15D converts at one closing rate for every account, labelled a convenience conversion, with rate,
date and source beside each figure — not ASC 830 / IAS 21 translation.

- [x] 15A failed saves and exports are reported; preferences ignore late responses; stable onError.
- [x] 15B backend serves upload limits and enabled formats; frontend derives pickers, checks, labels, messages.
- [x] 15C typed nested TB account models; five promoted routes get response models; wire types checked.
      Done: `all_accounts` / `account_balances` typed (`TrialBalanceAccountResponse`, `AccountBalanceResponse`).
      Done: response models for the five promoted JSON tools (`shared/promoted_tool_response_schemas.py`).
- [x] Found in 15D and fixed: every multi-sheet TB analysis returned 500 (no `classification_summary`).
- [x] 15D lead sheets grouped once; currency conversion completed (closing rate, convenience label); helper moved.
      Done: lead sheets grouped once, in both engines; post-processor adds section density only; rate-table
      helper moved to `shared/currency_rate_store.py`.
- [x] 15E blocking work off the event loop: webhook, logo, upload validation, file-tool DB units.
      Done: step 1 webhook (`billing/webhook_service.py`; the Deferred/Intake webhook-decomposition rows removed).
      Done: step 2 logo upload (`routes/branding.authorize_logo_write` + `store_logo` in the thread pool).
      Done: step 3 upload validation (`shared/upload_pipeline.validate_upload_bytes` in the thread pool).
      Done: step 4 file tools (`run_single_file_testing`, `execute_file_tool`: gate, engine + `to_dict`, recording;
      materiality and reference-date lookups) as synchronous units with their own sessions.

**Review (2026-11-20).** Commits: `63ad0d8d` 15A · `126e065b` 15B · `5ec3c339` + `42d7657c` + `61519e66` 15C ·
`e4fabf44` multi-sheet 500 fix · `9ed9aeb6` + `3b2ad532` 15D · `1047a24b` / `ac696133` / `2c7a1aee` / `e9591f9e` 15E
steps 1–4 · (record commit). Verification: backend `-m "not slow"` 11,415 passed, 2 xfailed, 1 failed — Sprint 819
`test_engagement_export_routes_unchanged` (already failing on `main`); frontend Jest via the pre-commit gate on every
commit; `next build` passes (second run, Next's advisory gate). mypy: no errors in the changed files.

**Open — CEO**
- [ ] 15D: multi-sheet files are not converted (only the single-sheet engine captures currencies). Wanted?
- [x] 15A: other callers of `apiPut`/`apiDownload` (19 files) were not audited for the `ok: false` pattern. Done
      in Sprint 893 (E).
- [ ] 15C: engine strings are not uniformly formatted (M-3 `"0"`, intercompany copies input decimals).

### Sprint 891: One tool catalog, one plan file, accurate instructions, dead code removed
**Status:** IN REVIEW (2026-11-20) — code complete on local branch `sprint-891-one-catalog`, stacked on Sprint 890
(16A's remaining tables listed below).
**Priority:** P2. **Source:** CEO brief 16 (review ST-07/06/17/18 at `ef5e567`). Supersedes the freeze for this work.
**Agents:** executor, critic (no behaviour change in 16B's first commit), guardian (copy matches the storage statement).

- [x] 16A registry gains page URL, short label and dashboard details; `tool-catalog.generated.ts` (generator +
      staleness test) drives the dashboard list; activity labels from the registry (Flux Analysis an explicit
      override); workspace counts distinct completed marketed tools against the catalog. Command-palette links are
      checked against the catalog. Not yet derived (listed for a later pass): workpaper index, `tool-ledger.ts`,
      `app/tools/page.tsx`, `toolbarConfig.ts` (workpaper refs and export capabilities not yet in the registry).
- [x] 16B one plan file (`shared/plans.json`): Python loads it, TypeScript generated; first commit changes no value.
      Done: step 1 — `backend/shared/plans.json` loaded by `price_config.py` and `entitlements.py`; every value
      compared before/after (`test_sprint_891_plan_file.py` + fixture).
      Done: steps 2–3 — `content/plans.generated.ts` (generator + staleness test); `pricing.ts` tier prices, feature
      lines, comparison rows and `SEAT_CONFIGS`, and the upgrade modal's feature lines, derive from it; backend seat
      ceilings read the one `max_team_seats`. Not changed: the Terms page's plan table (legal copy, counsel review)
      and the estimator's answer buckets (wording, not plan facts).
- [x] 16C entry docs point at the real commands; inventories from the registry; tax notes current; old baseline archived.
- [x] 16D unused declarations removed; flags wired or removed; leftovers listed.
      Removed (no consumer, git-grepped): `TokenResponse`, `get_all_base_price_ids`, `IngestionResult` /
      `AnomalyFinding` / `AnomalyResult`, `_looks_like_bcrypt`, `compute_tb_risk_score` / `get_risk_tier` aliases, and
      the `INTELLIGENCE_WATERMARK` and `FORMAT_ODS` flags (formats now come from `/upload/capabilities`).
      **Left for a decision (not touched):**
      - Unmounted batch-upload frontend (`BatchUploadContext`, `BatchDropZone`, `useBatchUpload`): mount it when the
        bulk-upload feature is built (see "Feature to build: Bulk upload"), or delete with that entry.
      - `engagement_dashboard_engine.py` + `engagement_dashboard_memo.py`: no route calls them. Finishing needs a route,
        a page and a memo export test; removing is two files and their tests.
      - `shared/intercompany_resolver.py` + `Engagement.intercompany_counterparties`: only `audit/rules/relationships.py`
        and one test read them; finishing needs a UI to enter counterparties; removing needs a migration to drop the
        column.
      - bcrypt verify branch for share passcodes: shares live ≤48 h, so it is dead once no unexpired share row has a
        bcrypt hash. Removal needs one read-only production query (count of unexpired `export_shares` whose hash starts
        `$2`) returning 0.

**Review (2026-11-20).** Commits: `201d6613` 16A · `fcef659b` + `e2286e27` 16B · `a1df9ed4` 16C · `b5749f85` 16D ·
(record commit). Verification: backend `-m "not slow"` 11,430 passed, 2 xfailed, 1 failed (Sprint 819 export golden,
already failing on `main`); frontend Jest via the pre-commit gate. 16B's first commit compared every price, seat
rate, ceiling, limit and gate before and after (fixture) — identical.

### Sprint 892: Behaviour-neutral refactors (Excel reads, organization services, testing page shell, large units)
**Status:** PARTIAL (2026-11-20) — local branch `sprint-892-refactors`, stacked on Sprint 891. Partial completion
is allowed by the brief. **Source:** CEO brief 17 (review ST-15/12/13/14). Each step must leave every output
unchanged (snapshot, PDF contract and memo equivalence tests run per step).

- [x] 17A Excel: measure peak memory; one open per workbook; reuse bytes read for hashing; row limit in the parser.
      Baseline (100k rows x 2 sheets, 4 MB): `read_excel_chunked` peak 32.7 MB; multi-sheet 33.6 MB / 89 s;
      `parse_uploaded_file` 42.9 MB. The XLSX pre-parse estimate re-opens the workbook and returns 0 for unsized
      sheets (a no-op that costs a full load).
      Done: step 1 — row-limit check on the parser's own open (`_estimate_xlsx_row_count` removed); same message.
      Done: step 2 — multi-sheet reader opens the workbook once (89.3 s -> 63.8 s, peak 33.6 MB unchanged).
      Done: step 3 — the TB route validates the bytes it read for hashing (`validate_upload_contents`).
      Kept: chunk `.copy()` in both readers (callers modify chunks). 17A complete.
- [x] 17B organization workflows into services (create, invite, accept, remove).
      Done: create organization (`services/organization_workflows.py`).; invite; accept; remove member. `routes/organization.py` 441 -> 283 lines. The webhook half of 17B was done in 15E step 1.
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

**Review (2026-11-20).** Commits: `4cb6966e` / `e77eb970` / `d0ce7824` 17A · `ca50d8f3` / `7f278f35` / `5e878409` /
`c9c35d16` 17B · `09b41267` / `f7cadada` 17C · `b38952ed` 17D step 1 · (record commit). Each step ran the output
snapshots, the PDF contract and memo equivalence, plus the suites for the code it touched; 17C steps compared old and
new page HTML in six states. Full run at the end: backend `-m "not slow"` 11,437 passed, 2 xfailed, 1 failed (Sprint
819 export golden, already failing on `main`); `next build` passes. Stopped here (the brief allows partial):
17C AP / Payroll / JE / Revenue and 17D's remaining sections and units are listed above.

### Sprint 893: Fixes for what Sprints 888–892 found
**Status:** IN REVIEW (2026-11-21) — local branch `sprint-893-defect-fixes`, stacked on Sprint 892; G waits on the CEO. CEO 2026-11-21:
"make any fixes you can at this time, including pending items on the todo". One commit per item.
- [x] A. `invoice.paid` recovery restores the plan tier (owner and org members' cached tiers). The Sprint 888 strict
      xfail is now a plain test; a second test covers recovery by `invoice.paid` alone with an org member. Both fail
      without the fix.
- [x] B. Falling revenue labelled "Increase" (Sprint 889 14B xfail). Increase / decrease now follow the display basis
      for credit-normal accounts (revenue, liabilities, equity except contra). The xfail is a plain test; a liability /
      expense case is added. Sprint 819 `route_form_exports` re-recorded: only the revenue row's label and the two
      counts changed. Left as is: the movement CSV prints raw (debit-positive) change % beside the label.
- [x] C. Preview cache: release unused entries after 10 minutes without waiting for the next preview. A daemon
      sweeper in `shared/preflight_cache.py` (started on first `put`) runs every 30 s; an entry cannot be read after
      10 minutes and is released within 10.5. The published "up to 10 minutes, then released" wording now holds
      (to the sweep interval). Test fails with the sweeper disabled.
- [x] D. Account erasure deletes the firm logo from S3 (after shared reports, before Stripe; each key cleared and
      committed once its object is gone). If S3 cannot be reached (or `S3_BUCKET_NAME` is unset while a logo row
      exists) the account is kept and the error says so, as for shared reports. Two tests; both fail without it.
- [x] E. 15A: audit the other `apiPut` / `apiDownload` callers for the `ok: false` pattern. Silent on failure, now
      an error toast via `utils/deliverDownload`: the eight trial-balance exports, bank-rec CSV and memo, the
      workspace expectations and SUM schedule PDFs, the convergence CSV, the multi-period memo. Clearing currency rates
      now sets an error. Already handled (no change): depreciation, loan amortization, JSON-analysis CSVs, heatmap,
      flux, report button, FS preview, account export, admin CSV, multi-period CSV, and every `apiPut` / `apiPatch` /
      `apiDelete` caller (all check `ok` and set an error).
- [x] F. 17C: AP and Payroll pages onto the shared testing page shell. The shell gains `settingsToolKey` (settings
      button + drawer), `extraExportFields` and `upload.iconPath`; each renders nothing when unused. A temporary test
      compared old and new HTML for AP, Payroll, Fixed Assets and Inventory in six states (24 cases, result components
      stubbed to print their props): identical; removing AP's settings key fails 6 of them. AP (step 3) and Payroll
      (step 4) committed separately. Stopped there: JE differs from the shell in a dozen classes (`sage-50` badge
      and drop zone, icon colours), keeps the extension in its export filename and adds a holiday calendar and a
      lazy Benford chart; Revenue adds contract inputs. Moving either without a visual change needs more shell
      options than it saves, or an approved restyle onto the theme tokens. AR aging stays outside (two files).
- [ ] G. 14G: a fresh PostgreSQL builds from the migrations — **not started, needs the CEO.** It decides the enum
      labels a migration-built database gets (production holds the member NAMES `create_all` wrote; the old chain
      creates lowercase values), and a squash must reproduce the schema at production's revision, not at this
      stack's tip (886's `c3e7a1f9d524` has not deployed). Recommended: a baseline revision that reuses production's
      head id and creates that schema with production's labels, old files moved to `versions/_archive/`, then the
      PostgreSQL job (upgrade head, enum round trip, model parity). Nothing changes for production.
- [x] H. Sprint 819 `test_engagement_export_routes_unchanged` re-recorded: the diff is the 886/887 anomaly-summary
      wording only. The package route's `content_encoding` depends on the Starlette version (1.10+ does not gzip
      `application/zip`; this venv has 1.0.0, CI installs the newest), so the test records it as CI sees it.
- [x] I. Bank-rec memo: "No items requiring further investigation were identified." → "No exceptions flagged: the
      reconciliation tests flagged no items."; `test_memo_banned_phrases.py` bans the old phrase (fails on the old text).
- [x] J. Seven stale `.docx` exports deleted (all last changed 2026-02-04, five "Zero-Storage" claims each; none
      linked). Five have a `.md` source; `FEATURE_ROADMAP.docx` and `API_REFERENCE.docx` (API v0.16.0, replaced by
      `API_REFERENCE_GENERATED.md`) had none and stay in git history. Sprint 845 did the same for the compliance set.
- [x] K. 16A follow-up: `app/tools/page.tsx` test counts come from the ledger (`testCountFor`); a new test checks no
      count is typed in again and every row the catalog lists has the catalog's href and category (counts, hrefs and
      categories all matched before the change). Still hand-written: its descriptions and references, the five rows
      the catalog does not list under those keys, the workpaper index, `tool-ledger.ts` and `toolbarConfig.ts`.
- [x] L. Engine suggested procedures reworded (55 texts: TB diagnostic 44, accrual 5, population profile 6; the expense
      engine has none) to "The auditor may consider …"; new `test_engine_procedures_are_suggestions` (fails on all 56
      original texts). Memo render snapshot re-recorded: only the two `tb_diagnostic` memos, procedure wording only (one
      footnote moved from page 6 to 7). Softest change: the out-of-balance TB's "STOP — do not proceed" is now a fact
      plus a suggestion. Also fixed: the per-account accrual procedure printed "schedule.. Compare". Old/new table for
      review: `reports/sprint-893-procedure-wording.md`. Left imperative (outside scope, listed there): the accrual
      `recommended_action` map, the population-profile `risk_note`, one intercompany benchmark note, the sample generator.
**Review (2026-11-21).** Commits: `e820787b` A · `8df978a0` B · `2dedbc79` C · `98930dd3` D · `877039b9` E ·
`c61e6a3f` + `ecc28a85` F · `34d2ebd4` H · `debab250` I · `422f9ed9` J · `a4c3f5f4` K · `ede24624` L · (record commit).
Full run at the end: backend `-m "not slow"` 11,448 passed, 0 failed, 0 xfailed (both Sprint 888/889 xfails fixed, the
Sprint 819 golden re-recorded); frontend Jest 2,170 via the pre-commit gate; `next build` passes.
- Already done elsewhere, waiting on the CEO's merge (not redone here): 867 (#318, also inside 882), 871 (#319),
  859 (#320), 869 (#322), 870 part A (#317), 853 (#331).

### Sprint 894: Todo bookkeeping, Next.js security upgrade, exact amounts in response schemas
**Status:** IN PROGRESS (2026-11-24) — local branch `sprint-894-next-and-amounts`, stacked on Sprint 893.
**Agents:** Executor (lead), Guardian (Next.js advisory), Critic (amount sweep).
- [x] A. Checkboxes Sprint 893 already closed but left open under 888, 889, 890 and 892 ticked, with where each was done.
- [x] B. Next.js 16.4.3 → 16.4.6 (in range): clears the advisories that make `next build` exit on Next's
      `SecurityFatalError` on alternate runs (884 follow-up and "Then (C)"). Lockfile: only `next` and its `@next/*`
      binaries changed. `npm audit`: `next` gone; the 26 moderates left are Jest's `glob`/`minimatch` chain (needs a
      Jest major, already on `main`). `next build` run twice back to back: both exit 0, pages `ƒ` as before.
- [x] C. Remaining `float` monetary fields in `shared/*response_schemas.py` move to exact amounts (884 follow-up);
      finding `details` stay floats by design (Sprint 829). 122 fields (80 diagnostic, 42 testing): balances, totals,
      debits/credits, adjustments, variances in currency, sampling misstatements and limits. A float the engine sends
      goes out unchanged (same JSON); a Decimal now keeps its cents above 2^53. Left as `float` on purpose: ratios,
      percentages, scores, confidences, quantities, hours, statistics (mean, median, std dev, Gini), bucket bounds,
      and three mixed fields that can hold a count or a quantity (`DiagnosticVarianceResponse`, ISA 520
      `ExpectationEvaluationResponse`, three-way-match `MatchVarianceResponse`). Note: `ExactMoney` refuses `inf`/`NaN`
      where `float` let them through, so no ratio-like field was moved. Test: `TestSprint894AmountFields` (63 fail on
      the old schemas). mypy unchanged (289, baseline 1,011).

### Feature to build: Bulk upload (Enterprise)
**Status:** PLANNED — CEO decision 2026-11-20 (brief 13B): we will build it. Until it performs real analysis the Terms
page does not list it and `POST /upload/bulk` answers 501 "Bulk upload is not available yet." (Sprint 888).
- [ ] Run each file through the tool it belongs to (engine, not a name-and-size record), with per-file results.
- [ ] Meter it like every other gated route (one successful run per file, or a CEO-chosen unit) — the Sprint 790
      guard (`test_sprint_790_upload_metering.py`) will require it once the route checks the quota again.
- [ ] Job state: no full filenames in Redis unless the "what we keep" page says so; job TTL stated.
- [ ] Mount and test the batch frontend (`BatchUploadContext`, `BatchUploadPanel`), one limit (backend 5 files;
      `types/batch.ts` says 10).
- [ ] Then: Terms and pricing list it again; remove the 501.

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
**Status:** IN REVIEW — code complete 2026-11-16 on a local branch (not pushed); unblocked by the CEO decision below. **Priority:** P2 security (freeze-exempt:
security defect). **Source:** security review M7, L12; read-only review at `ef5e567` (AZ-01, DH-02, AZ-15, TQ-05).
**Agents:** Guardian (lead), Executor, Critic.

**CEO decision (2026-11-16):** a client whose creator belongs to a firm today becomes that firm's client; a client
whose creator has no firm stays personal. Joining or leaving a firm never moves records (so the opt-in "bring my
clients" join flow and the interim reassign-to-owner fallback are dropped). Deleting a client, or archiving an
engagement, expectation or misstatement, needs the firm's owner or an admin; members can still create and edit.
Only the owner can remove an admin.

**853a — records follow the firm (AZ-01, DH-02, TQ-05)**
- [x] Confirmed at `ef5e5676`: access came from `Client.user_id` + the creator's *current* membership in five
      copy-pasted helpers; removal cleared the membership only; a firm-B owner read a firm-A client (200).
- [x] `Client.organization_id` (FK `organizations.id`, `RESTRICT`), set from the creator's firm when the client is
      created; Alembic `c853a1f0e2d4` adds it and backfills per the decision, logging the firm/personal split.
- [x] One rule, `shared.client_access.client_scope` (firm client → the firm's current members; personal client →
      its creator), used by the client, engagement, follow-up item/comment, expectation and misstatement managers,
      `require_client`, `require_client_owner` (saved summaries, trends, prior periods) and the summary save route.
- [x] Workpaper index and expectation evaluation moved onto the same rule (firm teammates got a 400 before).
- [x] Member removal revokes the member's live share links made inside the firm. No cache holds an authorization:
      the user is reloaded per request and the engagement analytics cache is read only after the access check —
      a test pins that.
- [x] "Not yours" answers 404 everywhere (`RecordNotFound`); five engagement child-list routes and the workpaper
      index used to answer 400.
- [x] Tests: `test_firm_owned_records.py` (API-level, real tokens: removal, re-join to firm B, lists, exports,
      shared links, personal client, warm analytics cache), `test_sprint_853_client_org_backfill.py` (real chain).

**853b — role gates (AZ-15)**
- [x] Confirmed at `ef5e5676`: members could delete clients and archive engagements (also via `PUT status=archived`),
      expectations and misstatements; one admin could remove another.
- [x] One shared check beside the firm check, `shared.client_access.require_destructive_role` (`FirmRoleRequired`,
      403): delete client, archive engagement (DELETE *and* `status=archived` update), archive expectation, archive
      misstatement → owner/admin. Another firm still gets 404 from the firm check first; personal clients need no role.
- [x] Owner-only removal of an admin (`remove_member` → `require_owner` when the target is an admin).
- [x] Tests: `test_firm_role_gates.py` — role (owner/admin/member/other firm) × each action separately (20 cells,
      record state checked after each), members still edit every record, solo user deletes/archives own records,
      admin-removal matrix, admin still removes a member.

**Verification (853a):** backend 10,628 passed / 6 failed before test updates; 5 of the 6 were tests asserting the
old rule (firm clients built without `organization_id`, a 400 that is now 404) and were updated. The 6th,
`test_sprint819_route_snapshots.py::test_engagement_export_routes_unchanged` (`content_encoding` gzip vs null),
**fails on unmodified `main` too** — pre-existing, not touched here. Frontend build + 2,107 tests green; OpenAPI
snapshot unchanged; ruff clean; mypy adds no errors in changed modules.

**Verification (853b):** backend 10,660 passed, 1 failed — the same pre-existing `main` failure above; ruff clean;
frontend untouched since its green run.

**Not changed (noted):** client-count quotas (`usage_service`, `entitlement_checks`, `activity`) still count by
creator — a quota, not access.

**Commit SHA:** 853a `16ba3989` · 853b (this commit). Local branch `sprint-firm-owned-records`, not pushed.

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
