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

- [2026-10-20] nightly audit artifacts — 2026-10-20 batch (daily brief + 6 sentinel JSONs + run_log) plus `.baseline.json` refreshed to the new QA Warden values (8,700 backend / 2,013 frontend, 0 failures — the first all-green baseline since 2026-05-31). Overall verdict RED on **Dependency Sentinel alone**: 68 backend / 22 frontend outdated, 5 security-relevant. Scanned for secrets before staging (no `sk_live`/`sk_test`/private-key/credentialed-URL matches). Files: `reports/nightly/*`.
- [2026-10-20] worklist consolidation — assessed `reports/launch-readiness-assessment-2026-10-19.md` and the 2026-10-20 worklist in `SESSION_STATE.md`, re-verified every load-bearing claim against current source (all still true, including the three Sprint 779 liability targets, the 59.9% webhook coverage, the empty secret store and the 404 on `api.paciolus.com`), and filed the result as `reports/next-actions-2026-10-20.md` — seven tracks, ten findings neither document covered. **Three documents disagreed about the backup decision:** `SESSION_STATE.md` still carried the version deferred "before the second paying customer", justified by the premise Sprint 783 had just disproved, while `EXECUTIVE_BLOCKERS.md`, this file's DECISION block and the assessment addendum all said pre-launch. Since `AGENTS.md` makes `SESSION_STATE.md` the first file a session reads, the stale copy was the one being acted on — corrected, along with Sprint 778's heading, which contradicted its own scope item 1. Also filed Sprints **784** (tool-count cohesion 12 → 18; `backend/main.py:243` ships "12-Tool Audit Intelligence Suite" in the public OpenAPI description against a canonical 18), **785** (nine real-work PRs went `MERGEABLE` → `CONFLICTING` when the 10-19/20 merges rewrote this file; seven finished sprints stranded) and **786** (dependency currency, superseding 760/761 — both written in April and wrong in their specifics; includes reconciling `backend/venv`, which matches neither `requirements.txt` nor production yet is what the nightly measures). Sprint 741 marked unblocked: its prerequisite log read was impossible while prod returned 500 for 5.5 months. No code changed. Files: `reports/next-actions-2026-10-20.md`, `tasks/todo.md`, `SESSION_STATE.md`, `tasks/ceo-actions.md`.
- [2026-10-19] review gate removed + two CEO-delegated decisions recorded — CEO confirmed a soft launch date and delegated the open decisions (`reports/launch-readiness-assessment-2026-10-19.md` §I). **(a) Branch protection:** `required_pull_request_reviews` removed from `main` via the Actions API; all 12 required status checks retained with `strict: true`. Rationale: GitHub forbids self-approving your own PR, so a 1-review requirement is unsatisfiable solo and every merge was clearing it with `gh pr merge --admin` — which, because `enforce_admins` is `false`, bypasses **the status checks too**, not just the review. The bypass was strictly more dangerous than the gate was useful. With reviews removed, merges take the normal path and CI genuinely blocks; `--admin` should no longer be needed, and needing it is now a signal. Note `required_linear_history` remains `true`, so merges must be **squash or rebase** — merge commits were only ever possible via the bypass. `enforce_admins` left `false` deliberately as a break-glass for a solo operator. **(b) Neon backup posture:** decided — see Sprint 778 and `tasks/EXECUTIVE_BLOCKERS.md`. No code changed.
- [2026-10-19] frontend CVE sweep clearing the red Node CI gates — `npm audit fix` (no `--force`, so every change stayed inside the existing semver ranges and **`package.json` was not touched**; lockfile only). Production dependency vulnerabilities went **22 → 0** (was 1 critical, 7 high, 13 moderate, 1 low). The critical was **Next.js itself**: 16.2.4 sat inside the `9.3.4-canary.0 – 16.3.7` advisory range. Also moved: `postcss` 8.5.10→8.5.31 (three advisories for arbitrary file read / path traversal via attacker-controlled `sourceMappingURL` in CSS comments), `sharp` 0.34.5→0.35.5 (inherited libvips CVE-2026-33327/33328/35590/35591, libheif GHSA-g89c-p67h-r497 + GHSA-2jg2-4ch7-h545, librsvg CVE-2026-96889), `source-map-js` 1.2.1→1.2.2 (event-loop DoS via indexed source-map section offsets), `nanoid` 3.3.11→3.3.20, `browserslist` 4.28.2→4.29.4, `fast-uri` 3.1.0→3.1.8. Net lockfile churn −622 lines (dedup). **Why this mattered beyond hygiene:** `ci.yml` runs `Node Dependency Audit (blocking)` as `npm audit --omit=dev --audit-level=high`, and it had been failing — so together with the PyJWT/python-multipart bump above, all six red dependency/CVE jobs now pass, which is what had every one of the 13 non-dependabot PRs sitting at `mergeStateStatus: BLOCKED`. Verified: `npm audit --omit=dev --audit-level=high` → 0 vulnerabilities (exit 0); `npx tsc --noEmit` → exit 0; `npm run build` → clean, and every route still renders `ƒ (Dynamic)` with `ƒ Proxy (Middleware)` active, so the nonce-based CSP contract is intact across the Next.js minor bump; `npm test` → 207 suites / 2,013 tests / 5 snapshots, 0 failures. 21 dev-only advisories remain (20 moderate + 1 high, the `babel-jest` → `@jest/transform` → `babel-plugin-istanbul` chain); all three CI audit gates pass `--omit=dev`, so they do not gate, and clearing them needs `npm audit fix --force` (breaking major bumps) — deliberately left. Final confirmation of the Next.js bump should be a Vercel preview deploy, since build output cannot prove runtime nonce propagation. Files: `frontend/package-lock.json`.
- [2026-10-19] nightly audit artifacts — 109-day backlog (2026-05-02 → 2026-10-19) committed in one batch: 795 files, 3.3 MB (109 daily `.md` briefs + 109 `.run_log` + 109 coverage, 108 sprint_shepherd, 108 scout, 105 dependency_sentinel, 104 report_auditor, 43 qa_warden sentinels), plus `.baseline.json` refreshed to the 2026-10-14 QA Warden / 2026-10-19 Report Auditor values. The overnight cron kept running through the entire 2026-05-01 → 2026-10-19 repo dormancy; nobody committed its output. Scanned for secrets before staging (no `sk_live`/`sk_test`/private-key/credentialed-URL matches). **Notable asymmetry:** only 43 of 109 nights produced a `qa_warden` sentinel, i.e. the test-suite agent failed to run on ~66 nights — which is exactly what PR #145 (`fix: raise qa_warden orchestrator timeout to 1700s`, opened 2026-05-11) was written to fix and never merged. The backend suite takes ~715–780s and the orchestrator's timeout sat below that, so the one agent that would have reported a red suite was the one most likely to time out. A concrete, measurable cost of the unmerged-PR backlog. Also confirms the nightly runs against `backend/venv` (`run_log` shows `backend\venv\Scripts\python.exe`), not system Python — relevant because the two environments have drifted apart. Files: `reports/nightly/*`.
- [2026-10-19] security dep bumps clearing the red `dependency-compliance` CI gate — `PyJWT[crypto]` 2.12.1→2.15.1 and `python-multipart` 0.0.26→0.0.32. The weekly `dependency-compliance` job ("Python CVE & License Audit", `pip-audit --desc --ignore-vuln CVE-2026-3219`) had been failing every run through 2026-08-24 (then stopped only because GitHub disables cron workflows after ~60 days of repo inactivity) with **12 known vulnerabilities in 2 packages** — and those were the *only* two packages flagged. PyJWT 2.12.1 carried PYSEC-2026-175..179, all fixed in 2.13.0; python-multipart 0.0.26 carried PYSEC-2026-3036/3037 (QuerystringParser treated `;` as a separator contrary to WHATWG, plus a quadratic rescan), PYSEC-2026-3039 (unbounded multipart part-header count/size → CPU DoS) and PYSEC-2026-3040 (`parse_form()` did not validate `Content-Length`; a negative value turned the bounded chunked read into read-until-EOF, loading the whole body into memory in one read) — all four land by 0.0.31. **Paciolus was not exploitable on the PyJWT advisories:** `decode()` always passes `algorithms=["HS256"]`, a single symmetric algorithm, so the asymmetric/HMAC key-confusion in PYSEC-2026-179 cannot trigger, and `PyJWKClient`/`jku` are unused so the PYSEC-2026-175 SSRF surface does not exist. **Nor, on closer inspection, was it exploitable on most of the python-multipart advisories.** PYSEC-2026-3040 is fully mitigated by our own `MaxBodySizeMiddleware`, which rejects a negative `Content-Length` with 400 *before* any body bytes are read (`security_middleware.py:162`) and independently caps streamed bytes in a second layer, so the read-until-EOF path is unreachable. PYSEC-2026-3036/3037 target `QuerystringParser` (`application/x-www-form-urlencoded`); Paciolus's `Form()` parameters are all paired with `UploadFile`, i.e. `multipart/form-data` handled by `MultipartParser`, and those endpoints require auth — reachable only if a client deliberately posts urlencoded, and the impact (field-separator differential on column mappings and IDs) is immaterial. The one genuinely relevant advisory is **PYSEC-2026-3039** (unbounded multipart part-header count/size): reachable across the ~50 `UploadFile` endpoints and only *partially* mitigated — the global body cap bounds total bytes, so it bounds how many headers fit, but does not eliminate CPU cost within that budget. Net: no historical compromise window; the bump is correct hygiene and unblocks the gate. **Root-cause insight worth keeping:** these were the only two CVE-flagged packages because they were the only two pinned with exact `==`. Every other CVE-carrying dependency (`cryptography`, `pillow`, `pypdf`, `pyasn1`, `werkzeug`) is pinned with a `>=` floor, and the transitives (`starlette`, `urllib3`, `anyio`, `idna`, `mako`) are unpinned, so a fresh `pip install -r requirements.txt` — which is what CI and the production Docker build both do — resolves them to latest and they self-heal. Exact pins buy reproducibility and rot; floors buy CVE currency and unreviewed upstream churn. requirements.txt currently mixes both without a stated rule; see Sprint 777 for the deliberate decision. Verified: venv auth suite 116/116, upload suite 223/223, and `pip-audit` no longer reports pyjwt or python-multipart. Files: `backend/requirements.txt`.
- [2026-10-19] inventory fixture date time-bomb — `test_inventory_testing.py::TestCompositeScore::test_clean_data_low_score` had been RED in every nightly since 2026-05-31 with no commit behind it. `sample_inv_rows()` hardcoded `Last Movement Date` literals in late 2025; IN-06 (slow-moving) compares against `date.today()` with a 180-day default threshold, so as wall-clock time advanced all 5 "clean" rows crossed it, flagged 100% slow-moving, and escalated `risk_tier` LOW→MODERATE (the `score < 25` assertion still passed at 10.5 — only the tier assertion caught it). Replaced the literals with a `_days_ago(n)` helper, matching the relative-date pattern the dedicated `TestSlowMovingInventory` cases already used; offsets 30/31/46/72/121 preserve the original fixture's relative ordering and spread while staying well inside the threshold. Also fixed the same latent bug in `make_large_dataset()` (all 20 rows shared `2025-11-01`; not yet tripped). Root cause of the *delay* in noticing: `TestSlowMovingInventory::test_recent_movement_no_flags` never asserted `entries_flagged == 0` despite its name, so fixture staleness stayed invisible there — assertion added with a diagnostic message. Backend: 134/134 inventory tests pass (was 133/134). Files: `backend/tests/test_inventory_testing.py`.
- [2026-05-11] qa_warden orchestrator timeout fix — `DEFAULT_AGENT_TIMEOUT_S` (900s) was less than qa_warden's own internal subprocess budget (1200s pytest + 300s jest = 1500s worst case). Buffer eroded as backend test count grew: 2026-05-07 ran 817s/83s spare, 2026-05-08 ran 843s/57s spare, 2026-05-11 tipped to TIMEOUT (killed at 900s, agent did not run, nightly went RED). Added `qa_warden: 1700` to `AGENT_TIMEOUT_OVERRIDES` (same pattern as `coverage_sentinel`); 200s of margin over the agent's worst-case internal budget. File: `scripts/overnight/orchestrator.py`. **Merged 2026-10-19, five months late** — the 109-day artifact backlog committed the same day quantifies the cost: only 43 of 109 dormant nights produced a `qa_warden` sentinel, so the agent failed to run on roughly 66 nights, and the one agent that would have reported a red suite was the one most likely to time out. Timeout re-validated against current runtimes before merge: the backend suite now takes ~865s (8,700 tests) against the 1200s internal pytest budget, so the 1700s orchestrator ceiling still holds with margin.
- [2026-04-30] post-PR-128 cleanup — closed 4 stale Apr-22 PRs (#94 superseded, #96 already on main, #97 partially superseded, #99 slot stale) + their remote/local branches. Captured the still-relevant gaps as one `fix:` commit: `.gitignore` adds `.hypothesis/` (root), `.claude/worktrees/`, `frontend/playwright-report/` (the PR #97 leftovers); `tasks/todo.md` adds Refactor Intake row for the Postgres enum-case drift bug originally filed as PR #99 (Sprint 715 slot was already taken by the SendGrid 403 investigation). Files: `.gitignore`, `tasks/todo.md`.
- [2026-04-29] PR #126 follow-up — `lint_engine_base_adoption.py` taught to follow ADR-018 shims to `services/audit/<tool>/analysis.py`. After `fae3e3e9` relocated 7 engines to dynamic-namespace shims, the AST-only check found no classes at the legacy path and false-flagged the 4 already-migrated engines (JE/AP/Payroll/Inventory) as off-pattern, breaking `test_engine_base_lint.py::TestKnownMigrated` on both Python 3.11 and Postgres 15 jobs. New `_resolve_shim_canonical()` helper detects both shim shapes (static `from services.audit.<tool>.analysis import *` and dynamic `from services.audit.<tool> import analysis as _impl`) and re-checks the canonical file. Findings drop 12→8 — the 4 unmigrated targets (AR Aging, FA, Revenue, SoD) and 4 borderline engines remain, matching `test_post_triage_finding_count` expectations. File: `scripts/lint_engine_base_adoption.py`.
- [2026-04-29] 016aafed: PR #126 CI gate alignment — `accounting_policy.toml` `[rules.revenue_contract_fields].file` repointed `revenue_testing_engine.py` → `services/audit/revenue_testing/analysis.py` (the legacy path is now a dynamic-namespace shim after `fae3e3e9` ADR-018 batch, so AST-based class detection found nothing and false-flagged ASC 606/IFRS 15 regression). OpenAPI snapshot regenerated to absorb 4 operation-description refreshes (`/export/{excel,pdf,leadsheets,financial-statements}` Sprint 748b pipeline-delegation docstrings); paths/schemas counts unchanged at 220/422. Files: `backend/guards/accounting_policy.toml`, `scripts/openapi-snapshot.json`.
- [2026-04-28] nightly QA Warden green-restore — `test_security_hardening_2026_04_20.py::TestRateLimitFailClosed` `_prod_env()` fixture now sets `STRIPE_PUBLISHABLE_KEY` and `STRIPE_WEBHOOK_SECRET` placeholders alongside `STRIPE_SECRET_KEY`. Without them, the subprocess env was missing those vars, python-dotenv backfilled from `backend/.env` (developer's test-mode Stripe key), and Sprint 719's production format guard hard-failed config import — surfacing as 2 test failures in the 2026-04-28 nightly. Companion to `e6627567` (helpers-allowlist) — together both nightly RED items resolved. File: `backend/tests/test_security_hardening_2026_04_20.py`.
- [2026-04-24] record Sprint 716 COMPLETE — PR #103 merged as `6802bd63`, Render auto-deploy landed 12:51 UTC, Loki Logs Explorer confirmed 40 ingested lines with correct labels, all 6 saved queries authored. Runbook (`docs/runbooks/observability-loki.md`) §4 LogQL corrected to reflect what actually works against our ingested streams (line-filter + `| json | level="…"` instead of indexed-label selectors for level/logger, since Grafana Cloud's ingest layer doesn't index those at our volume). Lesson captured in `tasks/lessons.md` about verifying deployed code before debugging runtime (I burned ~15 min on label hypotheses before discovering the commit was local-only and Render was still running Sprint 713's image). Files: `tasks/todo.md`, `tasks/lessons.md`, `docs/runbooks/observability-loki.md`.
- [2026-04-23] archive_sprints.sh number-extraction fix + archive of Sprints 673–677 — replaced broken grep-pipeline (which filtered to Status lines first, losing the Sprint number on the preceding header) with an awk block that pairs each `### Sprint NNN` header to its Status body and emits the number when COMPLETE. Dry-run confirmed extraction (673, 674, 675, 676, 677); archival produced `tasks/archive/sprints-673-677-details.md` (142 lines, 5 sprint bodies) and reduced Active Phase to just Sprint 611 (PENDING). Unblocks Sprint 689a's `Sprint 689a:` commit under the archival gate. Files: `scripts/archive_sprints.sh`, `tasks/todo.md`, `tasks/archive/sprints-673-677-details.md`.
- [2026-04-23] Sprint 689 Path B decision — CEO chose full expansion (all 6 hidden backend tools + Multi-Currency standalone → 18-tool catalog). Execution split into 689a–g (one tool per session, single marketing-flip at 689g). Defaults rejected on evidence that the 6 routes carry ~4,500 LoC of real engine code + tests. Plan + deliverables template captured in Sprint 689 entry. Pre-requisite flagged: `scripts/archive_sprints.sh` grep-pipeline bug must be fixed (or sprints 673–677 manually archived) before the first `Sprint 689a:` commit can clear the archival gate.
- [2026-04-23] R2 provisioning — Cloudflare R2 buckets `paciolus-backups` + `paciolus-exports` (ENAM, Standard, private), two Account API tokens (Object R&W, per-bucket scoped). 8 env vars wired on Render `paciolus-api` (`R2_{BACKUPS,EXPORTS}_{BUCKET,ENDPOINT,ACCESS_KEY_ID,SECRET_ACCESS_KEY}`) — 19→27 vars, deploy live in 1 min, zero service disruption (9× /health all 200 <300ms). Unblocks Sprint 611 ExportShare migration + Phase 4.4 pg_dump cron. Mid-provisioning incident: screenshotted Render edit form while EXPORTS credentials were unmasked → rolled `paciolus-exports-rw` token before saving, only uncompromised values persisted. Full pattern captured in `tasks/lessons.md` (2026-04-23 entry). Details in `tasks/ceo-actions.md` "Backlog Blockers" section.
- [2026-04-23] d74db7c: record Sprint 673 COMPLETE — DB_TLS_OVERRIDE removed from Render prod, 2026-05-09 fuse cleared (tasks/todo.md, tasks/ceo-actions.md)
- [2026-04-22] b0ddbf6: dep hygiene + Sprint 684 tail — 3 backend pins bumped (uvicorn 0.44.0→0.45.0, pydantic 2.13.2→2.13.3, psycopg2-binary 2.9.11→2.9.12), 3 backend transitives refreshed in venv (idna 3.11→3.13, pydantic_core 2.46.2→2.46.3, pypdfium2 5.7.0→5.7.1), mypy dev-pin bumped 1.20.1→1.20.2; 4 frontend caret pins bumped (@typescript-eslint/eslint-plugin + parser ^8.58.0→^8.59.0, @tailwindcss/postcss + tailwindcss ^4.2.2→^4.2.4). Sprint 684 deferred memo-copy item landed: `sampling_memo_generator.py` Expected Misstatement Derivation section now cites AICPA Audit Sampling Guide Table A-1 explicitly. Backend `pytest` 8046 passed / 0 failed; frontend `jest` 1887 passed / 0 failed; `npm run build` clean.
- [2026-04-22] nightly audit artifacts — 2026-04-22 batch (original RED report + 4 sentinel JSONs + run_log). Preserved as historical evidence of the false-green incident that motivated Sprint 712. `.qa_warden_2026-04-22.json`, `.coverage_sentinel_2026-04-22.json`, and `.baseline.json` were committed in Sprint 712 (5d29cce) with the post-fix genuine-green values.
- [2026-04-21] 9820bb2: nightly audit artifacts — 2026-04-19, 2026-04-20, 2026-04-21 batch. Commits daily report .md + 6 sentinel JSONs + run_log per day, plus .baseline.json update to capture the Sprints 677–710 test-count growth (8028 backend / 1845 frontend).
- [2026-04-19] 9f00070: nightly dep hygiene (part 2) — remaining 3 majors cleared in venv (numpy 1.26→2.4, pip 25.3→26.0.1, pytz 2025.2→2026.1.post1). Verified zero direct imports for numpy/pytz; pandas 3.0.2 compatible with numpy 2.x; pytz has no current dependents. pytest 7836 passed / 0 failed. Venv-only change (no requirements.txt edits needed).
- [2026-04-19] 8fd93bb: nightly dep hygiene — 26 safe package bumps (19 backend venv: anthropic, anyio, docstring_parser, greenlet, hypothesis, jiter, librt, lxml, Mako, mypy, packaging, prometheus_client, pypdf, pypdfium2, pytest, python-multipart, ruff, sentry-sdk, uvicorn; 6 frontend via npm update: @sentry/nextjs, eslint-plugin-react-hooks, @typescript-eslint/*, postcss, typescript). Deferred: numpy 2.x, pip 26, pytz 2026 (majors). frontend/package-lock.json only.
- [2026-04-18] 7915d77: nightly audit artifacts — commit 2026-04-18 report + sentinel JSONs (qa_warden, coverage, dependency, scout, sprint_shepherd, report_auditor) + run_log (reports/nightly/)
- [2026-04-16] 22e16dc: backlog hygiene — Sprint 611 R2/S3 bucket added to ceo-actions Backlog Blockers; Sprint 672 placeholder for Loan Amortization XLSX/PDF export (Sprint 625 deferred work)
- [2026-04-14] a32f566: hallucination audit hotfix — /auth/refresh handler 401→403 for X-Requested-With mismatch (aligns with CSRF middleware); added .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md
- [2026-04-07] 73aaa51: dependency patch — uvicorn 0.44.0, python-multipart 0.0.24 (nightly report remediation)
- [2026-04-06] 39791ec: secret domain separation — AUDIT_CHAIN_SECRET_KEY independent from JWT, backward-compat verification fallback, TLS evidence signing updated
- [2026-04-04] 29f768e: dependency upgrades — 14 packages updated, 3 security-relevant (fastapi 0.135.3, SQLAlchemy 2.0.49, stripe 15.0.1), tzdata 2026.1, uvicorn 0.43.0, pillow 12.2.0, next watchlist patch

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |
| `PeriodFileDropZone.tsx` deferred type migration | TODO open for 3+ consecutive audit cycles. Benign incomplete type migration, not a hack. Revisit when touching the upload surface for another reason. | Project-Auditor Audit 35 (2026-04-14) |
| `routes/billing.py::stripe_webhook` decomposition (signature-verify / dedup / error-mapping triad) | Already touched lightly in the 2026-04-20 refactor pass; full extraction pairs better with the deferred webhook-coverage sprint flagged in Sprint 676 review (handler is currently exercised by 6 route-test files but lacks unit coverage). Bundle both then. | Refactor Pass 2026-04-20 |
| `useTrialBalanceUpload` decomposition into composable hooks | Hook's state machine (progress indicator, recalc debounce, mapping-required preflight handoff) is tightly coupled to consumer semantics. Not a drop-in extraction — needs Playwright coverage of the mapping-required flow before a split is safe. | Refactor Pass 2026-04-20 |
| `routes/auth_routes.py` cookie/CSRF helper extraction | Module is already reasonably thin; cookie/token primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) are security-critical. Touching them without a specific bug or audit finding is net-negative. Revisit only if a follow-up auth/CSRF audit produces an actionable finding. | Refactor Pass 2026-04-20 |

---

## Architectural Remediation Initiative — COMPLETE 2026-04-29

> **All 18 sprints (742-759) shipped + post-initiative finishing pass closed 4 partial follow-ups.** Detail archived to [`tasks/archive/sprints-742-759-details.md`](archive/sprints-742-759-details.md). Scorecard at `reports/architectural-remediation-scorecard-2026-04-29.md`.
>
> **Outcome (TL;DR):** Phases 0/1/4/6/7/8 fully resolved; Phases 2/3/5 partial with explicit follow-up scope filed in `## Refactor Intake` below. 6 ADRs (014-019 + quality thresholds), 3 advisory CI lints, ~150 new pytest + ~50 new jest tests. Net code shrinkage: `auth_routes.py` 778 → ~270; `routes/export_diagnostics.py` 661 → 218; multi-period page 501 → 423; dashboard page 519 → 383; `useFormValidation.ts` 516 → 280.
>
> **Governance going forward:** quarterly architecture health review (run the 3 advisory lints, check deferred-items triggers, file ≤2 follow-up sprints if warranted); "no new god files" policy (code-review enforced); refactor intake lane visible in `## Refactor Intake` below. Subsequent sprints should be product-driven, not architecture-driven.

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
> **WORKLIST — 2026-10-20 (authoritative order).** Consolidated in [`reports/next-actions-2026-10-20.md`](../reports/next-actions-2026-10-20.md) (readable: https://claude.ai/code/artifact/cdbdd9eb-3039-44cf-a97b-23bc5c598543), which re-verified the 2026-10-19 launch-readiness assessment against current source and found ten items neither that doc nor the 2026-10-20 worklist covered.
>
> | Track | Scope | Sprints | Owner |
> |-------|-------|---------|-------|
> | 0 | In-flight ledger truth: PR #169 merged, decision contradictions fixed, `ceo-actions.md` refreshed, nightly artifacts committed | — (hotfix) | Claude |
> | 1 | Liability + self-truth | 779, **784** | Claude, ~3h |
> | 2 | Money path | 780 | Claude, ~1d |
> | 3 | Survive losing the database | 778 | Claude + CEO console, ~½d |
> | 4 | Lock in the zero states | 782 | Claude + one CEO signup, ~2h |
> | 5 | Legal to counsel, waitlist count, CPA validation, custom domain | 781 + Phase 4.2/4.3 | **CEO — starts today, parallel** |
> | 6 | Backlog debt | **785**, **786**, 741, 738, 762 | Claude |
>
> **Parked deliberately:** B-6…B-9 until Sprint 781 reports · the live Stripe build until pricing is validated · the 22-engine relocation · the mypy baseline · dev-only npm advisories · the deferred SOC 2 set.
>
> **Open asks on the CEO** (each blocks a track): Neon read-only connection string (waitlist count + Sprint 738 schema read) · `RENDER_API_KEY` repo secret (deploy-drift probe + DR workflows) · confirmation the R2 `paciolus-backups` token still works · registered address / agent / EU-rep + DPO decisions (the critical path to launch) · rebase-or-redo call on the 7 stranded sprint branches.
> **Launch-readiness Council Review — 2026-04-16.** 8-agent consensus: code is launch-ready; gating path is CEO calendar (Phase 3 validation → Phase 4.1 Stripe cutover → legal sign-off). Full verdict tradeoff map in conversation transcript.
>
> **Prior sprint detail:** All pre-Sprint-738 work archived under `tasks/archive/`. See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for the era index and archive file pointers. Sprints 732/739/740 archived to [`tasks/archive/sprints-732-740-details.md`](archive/sprints-732-740-details.md). Sprints 742–759 (architectural remediation) archived to [`tasks/archive/sprints-742-759-details.md`](archive/sprints-742-759-details.md).
> **Source:** External Financial Calculation Correctness audit (2026-04-30). Discovery pass confirmed substantial portions of the brief were already remediated (RPT-02 thresholds dataclass, RPT-11 epsilon separation, AR aging non-midpoint bucket bounds). Path B targets the genuinely outstanding defects + Decimal hardening of the bank-rec outlier and the multi-period output boundary. Conflict Loop captured in conversation transcript (2026-04-30).
>
> **Acceptance bar:** monetary decision logic Decimal-safe in the touched surfaces; materiality/threshold behavior dynamic + emitted in responses (active_thresholds + source); variance basis declared explicitly; intercompany layered with metadata + confidence + explainability; tests proving each fix and preventing regression.
> Sprints 763–767 archived to `tasks/archive/sprints-763-767-details.md`.
> **DECISION (2026-10-19, CEO-delegated — REVISED same day after review).** Build the Phase 4.4 `pg_dump` → R2 cron **before launch**. Neon PITR alone is not sufficient.
>
> **The first version of this decision deferred the off-provider backup, on the premise that Zero-Storage meant no client financial data was persisted. That premise was wrong**, and an automated review caught it. The database does persist client financial content:
> - `diagnostic_summaries` — aggregate balance-sheet and income-statement totals as `Numeric(19,2)` (`models.py:353-360`).
> - `uncorrected_misstatements` — `accounts_affected_json` holding account names with DR/CR and amounts, plus signed F/S impact on net income and net assets (`uncorrected_misstatements_model.py:102-121`).
> - `analytical_expectations` — expected values, precision thresholds, and `result_actual_value` / `result_variance_amount` (`analytical_expectations_model.py:103-124`).
>
> That is **auditor workpaper content**, not account scaffolding. A CPA who loses their SUM schedule or expectation documentation mid-engagement has a professional problem, not an inconvenience. With no launch-date pressure, the R2 bucket already provisioned and empty since April, and the work costing roughly half a day, deferring it is not defensible once the blast radius is stated correctly.
>
> **Superseded:** the earlier "revisit before the second paying customer" trigger is withdrawn. The backup ships pre-launch.
>
> What remains true from the first analysis: the *other* half of the risk is that **recovery has never been tested and the checks that would have said so are lying**. A second backup mechanism does not fix that. Both halves are in scope below.
> Sprints 768–783 archived to `tasks/archive/sprints-768-783-details.md`.

### Sprint 784: Tool-count cohesion sweep — 12 → 18
**Status:** COMPLETE.
**Priority:** P2 — one instance was public-facing; the rest internal cohesion.
**Source:** `reports/next-actions-2026-10-20.md` B-e. Supersedes the narrower copy question raised as `reports/launch-readiness-assessment-2026-10-19.md` §I item 4.

`backend/tools_registry.py` is the canonical catalog at **18** tools (Sprint 689 expanded 12 → 18; Sprint 717 reconciled the frontend ledger). The prose did not follow. `tests/test_catalog_consistency.py` guards the registry against the frontend ledger — it does not read documentation, so none of this was caught.

**Confirmed stale surfaces:**
- `backend/main.py:243` — FastAPI `description="12-Tool Audit Intelligence Suite for Financial Professionals"`. **This is public**: it renders in the OpenAPI schema and on the docs page.
- `AGENTS.md:5` — "a 12-tool zero-storage AI audit intelligence SaaS". The agent entry point, so every session starts from a wrong number.
- `docs/01-product/PRODUCT_VISION.md` — 6 occurrences including the executive-summary hero line and the footer.
- `docs/02-technical/ARCHITECTURE.md:13` and `:178`.
- `docs/07-user-facing/USER_GUIDE.md` — "Twelve specialized tools".
- `tasks/ceo-actions.md` Phase 3 — the validation checklist the CEO is meant to work through lists 12 tools with their old test counts.

**Out of scope:** `COHESION_REMEDIATION.md` and `tasks/archive/**` are historical records of the 12-tool era and keep their numbers. `CLAUDE.md`'s era table line for Sprints 255–278 is also historical and correct as written.

**Verification:** extend the documentation-consistency gate so a prose tool count that disagrees with `tools_registry.MARKETING_AUDIT_TOOL_COUNT` fails CI. **Use that name** — it is the backend constant (`tools_registry.py:248`, computed from the `is_marketing_audit_tool` flag). `CANONICAL_TOOL_COUNT` is the *frontend* ledger's literal (`tool-ledger.ts:221`), already tied to the backend value by `tests/test_catalog_consistency.py`; a backend gate importing it would fail. Without the guard this recurs — exactly as the AS 1215 citation did after being fixed in code (Sprint 779 item 3).

#### What landed

**The public surface.** `backend/main.py:243` now reads `18-Tool Audit Intelligence Suite`, and
`scripts/openapi-snapshot.json` was regenerated in the same change (the OpenAPI Schema Drift Check gate
compares against it; `check_openapi_drift.py` reports no drift, paths 220 / schemas 422 unchanged).

**Prose counts** in `AGENTS.md`, `README.md` (hero line + feature bullet), `docs/01-product/PRODUCT_VISION.md`
(5 sites), `docs/02-technical/ARCHITECTURE.md` (5 sites) and `docs/07-user-facing/USER_GUIDE.md` (3 sites).

**Two prose *lists*, not just counts — wider than the brief anticipated.** `PRODUCT_VISION.md`'s feature table
and `README.md`'s feature bullet each enumerated twelve tools, and the table's per-tool test counts had drifted
independently of the registry: **AP 13→14, Payroll 11→13, Revenue 16→18, AR 11→12, Fixed Assets 9→11,
Inventory 9→10.** Both now mirror `tools_registry.py` — display names, test counts, standards and summaries all
derived from it. Also corrected the JE row, which cited only AS 2315 (Audit Sampling) where the fraud standard
is AS 2401; it now cites both, with AS 2315 scoped to the sampling aspect.

**Ordinals dropped from `ARCHITECTURE.md`.** Its directory tree and route table labelled tools "Tool 1" …
"Tool 11" — an ordering the registry does not guarantee and which has to be renumbered on every catalog
change. Both lists now carry names in registry order, expanded to the real 23 tool routes (18 audit tools +
Multi-Currency side-car + composite-risk, account-risk-heatmap, depreciation, loan-amortization). This also
fixed a wrong route: the doc claimed `/tools/fixed-asset-testing`; the directory is `fixed-assets`.

**Stale frontend comments** in `demo/page.tsx`, `(marketing)/page.tsx`, `ToolShowcase.tsx` (×2) and
`ToolSlideshow.tsx` said "12-tool" while the components render from `TOOL_LEDGER` (18). Comments now point at
the ledger instead of carrying a literal.

**Historical records deliberately left alone:** `COHESION_REMEDIATION.md`, `docs/archive/**`,
`tasks/archive/**`, `CLAUDE.md`'s era table, and every revision-history row. Each describes what was true at a
past version.

#### The guard

`backend/guards/doc_consistency_guard.py` gained a fourth rule, `tool_count_consistency`, parsing
`tools_registry.py` as text (the guard is stdlib-only and runs without project deps) and counting
`is_marketing_audit_tool=True` — i.e. it mirrors `MARKETING_AUDIT_TOOL_COUNT` rather than trusting a literal.

**Two things the first draft got wrong, both caught by running it:**

1. **13 false positives out of 14.** The patterns were too loose: every markdown TOC anchor of the form
   `](#5-tool-3-journal-entry-testing)` matched "5-tool", and a true subset statement ("six tools are shown
   inline") matched a bare count. Now link targets and inline code are stripped first, and only three narrow
   catalog-claim forms match — `N-tool` compound adjective, `all N tools`, and `N {audit|diagnostic|specialized|testing} tools`.
2. **It did not guard the one surface that matters most.** Regression-proving it by reverting `main.py` to
   "12-Tool" left the guard **green** — it covered documentation only. A `_check_api_description` rule now
   covers the FastAPI description and its failure message names the snapshot that must be regenerated with it.
   Guarding the docs but not the shipped API string would have protected the least important copy and missed
   the public one.

Escape hatch for genuine history: `<!-- doc-consistency: historical -->` on the line.

#### Verification

- Guard: `ALL CHECKS PASSED`. **Regression-proved twice** — reverting `main.py` and reverting a
  `PRODUCT_VISION.md` line each produced exactly one violation naming the file and line, then restored.
- `tests/test_doc_consistency_guard.py`: **35 passed** (was 21). The 14 new tests pin both the true positives
  and every false-positive class above, plus a test asserting the text parser agrees with
  `tools_registry.MARKETING_AUDIT_TOOL_COUNT` — so the two can never disagree silently.
- `tests/test_catalog_consistency.py` + `tests/test_citation_consistency.py`: 50 passed.
- `check_openapi_drift.py`: no drift. `npx tsc --noEmit`: exit 0. `ruff check backend/guards/`: clean.

#### Scope correction (PR #174 review) — the enum is necessary, not sufficient

The sprint said a run of any of the six tools "could not be recorded against an engagement
at all". True, and the enum was a hard blocker. But **the enum alone does not make them
trackable**, and the review caught me implying it did.

None of `routes/sod.py`, `intercompany_elimination.py`, `w2_reconciliation.py`,
`form_1099.py`, `book_to_tax.py` or `cash_flow_projector.py` calls
`maybe_record_tool_run` — and none of them even accepts an `engagement_id`
parameter (`sod.py` has no `db: Session` dependency either). Compare `ar_aging.py`,
`bank_reconciliation.py`, `multi_period.py`, `sampling.py`, `three_way_match.py` and
`audit_flux.py`, which all do.

So what Sprint 787 delivered is the **precondition**: the enum, the migration, the label
tables and the taxonomy classification, so that a recorded run *can* exist and the catalog
counts are honest. Wiring the fourteen endpoints is **Sprint 787b** — it changes API
signatures across six routes and needs a per-tool decision about what a composite score
means for a role matrix or a cash projection, which is design work rather than a fix.

#### Two further migration findings from the same review

**My migration's labels were wrong.** `d8b945d0b4e5` added lowercase slugs
(`sod_checker`, …) copied from `tools_registry`. `ToolRun.tool_name` is `Enum(ToolName)`
with no `values_callable`, so SQLAlchemy binds the **member name** — it sends
`SOD_CHECKER`. The baseline migration gets this right
(`sa.Enum('TRIAL_BALANCE', 'MULTI_PERIOD', …)`); I copied the wrong list. Corrected to
member names.

**The coverage fraction counted 19 against 18.** Changing the denominator to
`MARKETING_AUDIT_TOOL_COUNT` while leaving the numerator over every `ToolName` member meant
an engagement that ran every catalog tool plus flux analysis would print "Tools Executed:
19 of 18", and the not-executed coverage penalty counted a tool the sentence does not
describe. Both sides are now scoped to `CATALOG_TOOL_SLUGS`; non-catalog runs still appear
in "Total Tool Runs".

#### Three gaps this sweep uncovered — filed, not silently fixed

Each is a product gap rather than a copy fix, so none belongs in a cohesion sprint: **787** (engagement layer
tracks 13 of 18 tools), **788** (nav bar lists 12 of 18), **784b** (user guide documents 12 of 18).


---

### Sprint 787: Engagement layer tracks 13 of 18 tools
**Status:** COMPLETE.
**Priority:** P1 — one symptom was customer-visible in a shipped PDF.
**Source:** Sprint 784 discovery, 2026-10-20.

`ToolName` in `backend/engagement_model.py` has **13 members** — the original 12 tools plus `flux_analysis`.
Sprint 689 expanded the catalog to 18 and Sprint 717 reconciled the frontend ledger, but this enum was never
touched. Consequences:

- **Customer-visible:** `anomaly_summary_generator.py:329` renders `Tools Executed: {n} of {len(ToolName)}
  available tools` — so the Anomaly Summary PDF tells a practitioner there are **13** available tools while
  every marketing surface, the pricing page and now the API description say 18.
- `workpaper_index_generator.TOOL_LABELS` likewise has 13 entries, so the six newer tools cannot appear in a
  workpaper index.
- Engagement tool-run tracking, the completion gate and the diagnostic package ZIP are all keyed on
  `ToolName`, so a run of any Sprint-689 tool cannot be recorded against an engagement at all.

**Scope:** expand the enum, add the Alembic migration for the Postgres enum type (check how
`tool_runs.tool_name` is stored first — a native enum needs `ALTER TYPE`, a varchar does not), extend
`TOOL_LABELS`, and replace `len(ToolName)` with the registry count so the count has one source. Verify the
Anomaly Summary PDF and workpaper index both render the full catalog.

**Note:** `flux_analysis` is in this enum but is not one of the 18 marketing tools, so `len(ToolName)` was
never the right denominator even at 12 tools. Use `tools_registry.MARKETING_AUDIT_TOOL_COUNT`.

#### What landed

**The enum.** Six members added to `ToolName`, values matching `tools_registry.py` slugs
because `shared/tool_run_recorder.py` constructs `ToolName(slug)` from the route. Plus the
Alembic migration (`d8b945d0b4e5`) adding those values to the Postgres `toolname` type —
PostgreSQL rejects an unlisted enum value on insert while SQLite accepts anything, so
without the migration every local and CI test would pass and production would fail.

**The customer-visible count.** Three strings in the anomaly summary read
`len(ToolName)` and now read `tools_registry.MARKETING_AUDIT_TOOL_COUNT`.

Worth being precise about why `len(ToolName)` was *never* correct, not merely stale: the
enum includes `flux_analysis`, which is not one of the 18 sold tools. It counts **trackable
run types**, a different quantity from **tools a customer buys**. At 12 catalog tools it
would have printed 13; at 18 it printed 13 as well, for a different reason.

**Label and reference tables** extended for all six: `TOOL_LABELS`,
`TOOL_LEAD_SHEET_REFS`, `TOOL_CROSS_REFERENCES`, `TOOL_DISPLAY_LABELS`. A missing entry
degrades silently to a raw slug in a filed workpaper.

**Stale per-tool ranges in the same tables, fixed while there:** `JE-1 through JE-18` → 19,
`AP-1 through AP-13` → 14, `PR-1 through PR-11` → 13, `RT-1 through RT-12` → 18,
`AR-1 through AR-11` → 12, `FA-1 through FA-9` → 11, `IN-1 through IN-9` → 10. These print
in the workpaper index a practitioner files, so a short range understates work performed.

#### The convergence taxonomy — a real decision, not a formality

The full suite surfaced that `domain_config/tool_taxonomy.py` classifies every tool as
convergence-capable or convergence-excluded, and six were unclassified. An unclassified tool
drops out of the Convergence Index silently rather than raising.

The rule turned out to be mechanical: **`CONVERGENCE_TOOLS` is exactly the key set of
`shared/account_extractors.ACCOUNT_EXTRACTORS`.** A tool can contribute to convergence only
if something can pull GL account identifiers out of its result. None of the six has an
extractor, and none produces GL-account-level output — role matrices, vendor thresholds,
entity balances, forward projections — so all six are excluded. Intercompany Elimination is
the one plausible future candidate, but that needs an extractor written; classification
cannot substitute for one. That equivalence is now asserted rather than maintained by hand.

#### Five stale literals that were *defending* the drift

`assert len(ToolName) == 13` existed in **four** test files — `test_ar_aging`,
`test_engagement`, `test_fixed_asset_testing`, `test_inventory_testing` — plus
`len(CONVERGENCE_EXCLUDED) == 6` in `test_convergence`.

These did not merely fail to catch the Sprint 689 drift. They **defended** it: the correct
enum expansion turns all five red, so whoever attempted it saw failing tests and had reason
to conclude the expansion was wrong. That is the most likely explanation for why a six-month
gap in a core enum went unfixed. All five now derive from the registry.

#### The guard

`tests/test_toolname_catalog_parity.py` — 12 tests closing the third edge of a triangle
whose other two edges already existed. `test_catalog_consistency.py` ties the registry to the
frontend ledger; nothing tied either to `ToolName`. It asserts: every catalog tool is
trackable; every enum member is a catalog tool or a declared non-catalog exception; the
taxonomy covers the enum; `CONVERGENCE_TOOLS` equals the extractor key set; every label table
is complete; workpaper references are unique; **a Python enum member added without an
`ALTER TYPE` migration fails here** rather than in production; and no test may hardcode a
`len(ToolName)` literal again.

That last detector was wrong on its first draft — it flagged four lines, all false: three of
my own docstrings *quoting* the old assertion to explain its removal, and one
`assert len(not_started) == len(ToolName) - 2`, which is the correct derived form. Substring
matching again. Now a regex requiring an actual `assert` against a numeric literal,
regression-proved by re-introducing the real thing.

#### Verification

- Full backend suite **8,728 passed / 0 failed** on an untouched tree.
- **Recovery note.** The parity test was briefly committed to the wrong branch. An early
  `git stash push` omitted `-u`, so the then-untracked `test_toolname_catalog_parity.py`
  followed me across two branch switches and was swept into Sprint 780's coupon-fix commit
  by a `git add -A backend/tests`. Caught while rebasing: Sprint 787's own PR did not
  contain its headline test. Moved back, 12/12 passing here. **A stash without `-u` is not
  a clean tree** — new files stay behind and get attributed to whatever is committed next.
- `ruff check` and `ruff format` clean under `backend/ruff.toml`.
- `alembic heads` reports a single head (`d8b945d0b4e5`); the models/migration parity test
  passes.
- Note: `ruff format` also collapsed two unrelated dict literals in `test_convergence.py`
  that had been formatted at a narrower width — the pre-commit hook would have done the same.

#### Not in scope

Writing an account extractor for Intercompany Elimination, which would move it into
`CONVERGENCE_TOOLS`. That is a feature with its own design question (which balances count as
GL accounts in a consolidation), not part of a catalog reconciliation.

---

### Sprint 788: Tool navigation bar lists 12 of 18 tools
**Status:** COMPLETE — **but filed against the wrong file.** See the correction below.
**Priority:** P2 — the tools were reachable elsewhere, just not from the bar on every tool page.
**Source:** Sprint 784 discovery, 2026-10-20.

`frontend/src/components/shared/ToolNav.tsx` hardcodes a 12-entry `TOOLS` array and a 12-member `ToolKey`
union. The six Sprint-689 tools (Segregation of Duties, Intercompany Elimination, W-2/W-3, Form 1099,
Book-to-Tax, Cash Flow Projector) are absent.

They are **not** unreachable — `app/tools/page.tsx` (23 routes), `lib/commandRegistry.ts` (21 routes),
`content/tool-ledger.ts` (18) and `ToolShowcase.tsx` all include them. But a practitioner working inside one
tool sees a bar that silently omits a third of what they are paying for.

**Scope:** drive `TOOLS` from `tool-ledger.ts` instead of a second hardcoded list — that is what makes this
stay fixed, since `test_catalog_consistency.py` already ties the ledger to the registry. Decide the overflow
treatment: `INLINE_COUNT = 6` leaves twelve items in the More dropdown, which likely wants grouping
(diagnostics / testing / tax & controls) rather than a flat list.

#### Correction: this sprint named a dead component

As filed, the sprint targeted `frontend/src/components/shared/ToolNav.tsx`. **That component
was replaced by `AuthenticatedShell` in Sprint 475** and was referenced only by its own test
file — it rendered on no page at all. Its hardcoded 12-tool list is exactly what produced the
wrong filing: I read the list, correctly concluded that six tools were missing from tool
navigation, and incorrectly concluded that this was the file responsible.

The live surface is `UnifiedToolbar` → `MegaDropdown` → `TOOL_COLUMNS` in
`UnifiedToolbar/toolbarConfig.ts`. The defect was real there: twelve audit tools plus Flux and
Reconciliation Intel, with all six Sprint-689 tools absent from every column.

#### What landed

**A fourth column.** `TOOL_COLUMNS` gained **Tax & Filings** (W-2/W-3, Form 1099, Book-to-Tax),
Segregation of Duties joined **Testing Suite** as controls testing, and Intercompany
Elimination + Cash Flow Projector joined **Advanced**. Grouping follows what each tool does,
not where there was room.

**The grid is derived, not hardcoded.** `MegaDropdown` had `grid-cols-4` — three tool columns
plus Account — so adding a column would have silently overflowed the row. It now computes
`repeat(TOOL_COLUMNS.length + 1, minmax(0, 1fr))`, and the panel widened 64rem → 76rem to
carry the fifth column.

**Two `toolKey` values corrected.** `journal_entry` → `journal_entry_testing` and
`fixed_assets` → `fixed_asset_testing`. The field's own comment promises it matches backend
entitlement names; both were wrong. It is currently vestigial — `MegaDropdown` renders only
`label` and `href` — so this fixes nothing today and prevents a future gating change from
inheriting two wrong keys.

**Dead `ToolNav` deleted** along with its test, its re-export from `components/shared/index.ts`,
and two docblocks in `lib/commandRegistry.ts` that still described it as the model for tool
commands. Dead code carrying a stale copy of real data is worse than dead code: it reads as
authoritative, and it misdirected this sprint's own filing.

#### The guard

Four tests in `__tests__/MegaDropdown.test.tsx` close the last open edge of the catalog chain:

- every tool in `TOOL_LEDGER` appears in the navigation;
- the navigation offers no tool outside the ledger, except two explicitly named non-ledger
  destinations (`/flux`, `/recon`) — so an href typo cannot pass as an intentional extra;
- each tool appears exactly once across all columns;
- `toolKey` matches the ledger id for every ledger-backed item.

`backend/tests/test_catalog_consistency.py` already tied the registry to the ledger, so the
chain is now **registry → ledger → navigation**, closed end to end. Regression-proved by
removing Book-to-Tax from the nav: the coverage test failed naming it, then passed on restore.

#### Verification

- Frontend suite **206 suites / 2,010 tests, 0 failures** (was 207/2,013 — `ToolNav`'s 7 tests
  removed, 4 added to MegaDropdown).
- `npx tsc --noEmit` exit 0. `npm run build` clean, every app route still `ƒ (Dynamic)` with
  `ƒ Proxy (Middleware)` active, so the nonce-based CSP contract is intact.
- **Not verified in a browser.** The five-column layout is checked by test and by arithmetic —
  the longest label is 24 characters at `text-sm` in a ~219px column — but the toolbar lives
  behind authentication and I did not render it. The derived grid means a future column cannot
  overflow silently; column *width* at five columns is the part that rests on that arithmetic.

---

### Sprint 787b: Wire the six Sprint-689 tools into engagement tracking
**Status:** PENDING.
**Priority:** P2 — the catalog counts are honest after Sprint 787; the runs still are not recorded.
**Source:** PR #174 review, 2026-10-21.

Sprint 787 made the six tools *representable* in `ToolName` and classified them in the
taxonomy. It did not wire them up. None of the six routes calls `maybe_record_tool_run`, and
none accepts an `engagement_id`:

| Route | Endpoints | Has `engagement_id` | Has `db: Session` |
|-------|-----------|---------------------|-------------------|
| `sod.py` | 3 | no | **no** |
| `intercompany_elimination.py` | 2 | no | yes |
| `w2_reconciliation.py` | 2 | no | yes |
| `form_1099.py` | 2 | no | yes |
| `book_to_tax.py` | 3 | no | yes |
| `cash_flow_projector.py` | 2 | no | yes |

**Scope:** follow the `ar_aging.py` pattern — optional `engagement_id`, `background_tasks`,
`maybe_record_tool_run(db, engagement_id, user_id, slug, success, score, flagged)` on the
success path and a `success=False` call in the error handler.

**The part that is design, not mechanics:** what `composite_score` and `flagged_accounts`
mean for each tool. A role-permission matrix and a 90-day cash projection do not produce
"flagged accounts" in the sense AR aging does. Decide per tool whether to pass `None`, a
domain-appropriate score, or to extend the recorder — do not invent a score to fill the
parameter. `shared/account_extractors.py` deliberately has no extractor for any of the six
(see Sprint 787's convergence classification), so `flagged_accounts=None` is the honest
default until a tool earns one.

**Verification:** a run of each tool against an engagement produces a `ToolRun` row; the
workpaper index and Anomaly Summary both show the tool as executed; the completion gate
counts it.

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
4. Add a test that compares every `sa.Enum(..., name=...)` label set in the migrations
   against the ORM's `.enums` for the same type, so the chain cannot drift from the mapping
   again. **This is the check that would have caught all five rows above.**

**Do not** "fix" this by adding `values_callable` to the models: that would flip every
binding to lowercase and break the current production database, which holds name labels.

---

### Sprint 784b: User guide chapters for the six newer tools
**Status:** PENDING.
**Priority:** P3 — documentation completeness; the guide is now accurate about what it does not cover.
**Source:** Sprint 784, 2026-10-20.

`docs/07-user-facing/USER_GUIDE.md` sections 3–14 document twelve tools, one chapter each. Sprint 784 corrected
its counts and added an explicit note that the six tax and controls tools are not yet written up, rather than
leaving the guide claiming eighteen while documenting twelve. Writing those six chapters is content authoring
against each tool's actual UI, not a count fix, so it is filed separately.

**Scope:** one chapter per tool following the established pattern (what it does, required columns, how to read
the output, what the memo contains), for Segregation of Duties, Intercompany Elimination, W-2/W-3
Reconciliation, Form 1099 Preparation, Book-to-Tax Reconciliation and Cash Flow Projector. Renumber the TOC
and remove the interim note.

---

### Sprint 785: Dispose of the PR backlog
**Status:** PENDING.
**Priority:** P2 — seven finished sprints are rotting on branches, and every day on `main` widens the conflict.
**Source:** `reports/next-actions-2026-10-20.md` B-a / B-b.

`SESSION_STATE.md` recorded on 2026-10-19 that all 25 open PRs were `MERGEABLE` and that the only thing blocking them was six red CVE gates. The gates were fixed that day — but the 2026-10-19/20 merges then rewrote `tasks/todo.md` wholesale, and **all nine real-work PRs now report `DIRTY` / `CONFLICTING`**: #134, #137, #138, #139, #140, #141, #142, #143, #144.

**Stranded work:** Sprint 769 (context memoization), 771a (Button primitive), 772a (lazy Recharts + command palette), 773 (type disambiguation + dead code), 773b (React.memo subtrees), 773c (perf finishers), 762 (flux_expectations memo contract test, closing 17/18 → 18/18), plus #134 (ADR-018 shim awareness in lint/policy scripts) and #144 (the 2026-04-30 + 2026-05-01 nightly briefs, still absent from the tree, plus a `tmp_report` cleanup).

**Approach:** rebase each branch onto current `main` — do not cherry-pick or re-do from the diff. #144's diff against current `main` reads as ~125k deletions purely because the branch is based on pre-dormancy `main`; the same distortion affects every branch in the set, so a diff-driven redo would delete live work. Expect conflicts to be concentrated in `tasks/todo.md` and `reports/nightly/`, i.e. ledger files, not code.

**Also in scope:** triage the 15 Dependabot PRs (#77, #78, #90, #106–#114, #156, #157, #158). The oldest is from 2026-04-13 and most target versions that are themselves now stale; close them as superseded and let Sprint 786 take the current releases, rather than merging six-month-old bumps.

**Verification:** each rebased branch passes CI on its own merge; after the sweep, open non-Dependabot PR count is 0 and the frontend suite still reports 2,013 tests (the 7 stranded sprints are refactors and should not change behaviour).

---

### Sprint 786: Dependency currency (replaces Sprints 760 and 761)
**Status:** SPLIT — **786a COMPLETE** (venv reconciled, resolution now recorded in CI), **786b PENDING** (the reviewed major bumps).
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

#### 786a — the venv, and what the reconcile proved: COMPLETE

**The finding is bigger than the hygiene.** Reconciling `backend/venv` to a fresh
`pip install -r requirements.txt --upgrade` moved **12 packages**:

| Package | venv had | fresh resolve | Pin style |
|---------|----------|---------------|-----------|
| `cryptography` | 46.0.7 | **50.0.2** | `>=` floor |
| `pillow` | 12.2.0 | **13.0.0** | `>=` floor |
| `redis` | 7.4.0 | **8.1.0** | `>=` floor |
| `pypdf` | 6.10.2 | 6.21.1 | `>=` floor |
| `pyasn1` | 0.6.3 | 0.6.4 | `>=` floor |
| `Werkzeug` | 3.1.8 | 3.1.9 | `>=` floor |
| `fastapi` | 0.136.0 | 0.136.1 | `==` pin (venv was behind) |
| `stripe` | 15.0.1 | 15.1.0 | `==` pin (venv was behind) |
| `pdfminer.six`, `pdfplumber`, `pypdfium2`, `prometheus_client` | — | — | transitive / floor |

**Sprint 777 named this risk and it has already happened, twice.** That sprint chose the
`==`/`>=` split and wrote down the cost of the floor half: *"production can take an
unreviewed upstream major at any time, with no lockfile and no record of what actually
shipped."* Production has since taken **`pillow` 12 → 13** and **`redis` 7 → 8** — two major
upgrades, neither reviewed, both already live, because CI and the production Docker build
each do a fresh resolve. `cryptography` has moved **four** majors (46 → 50) the same way.

Nothing is broken by them: CI has been green throughout, and the full suite passes on the
reconciled versions. The problem is that nobody chose them.

**So the deliverable is the evidence record, not a version bump.** `ci.yml`'s 3.12 matrix leg
now captures `pip freeze` after install, prints the floor-pinned set into the build log
behind a collapsible group, and uploads the full resolution as a 90-day artifact
(`resolved-requirements-py312`). Sprint 777's rule depended on exactly this and it had never
been built — "what did we test on" was unanswerable after the fact. Retention is 90 days
rather than the 30 used for lint reports, because a CVE disclosure can land months after the
build it concerns.

**What was reconciled, and what deliberately was not.** The venv now matches a fresh resolve,
so the nightly measures something that ships. `requirements.txt` itself is **unchanged** —
the two `==` pins the venv was behind on (`fastapi`, `stripe`) were already correct in the
file, and no floor was raised. Nothing about what production resolves has changed; only the
local environment's agreement with it, and the record of it.

**Correction to `SESSION_STATE.md`.** It called `backend/venv` "the CI-representative env,
with the new pins". It was neither, as the table above shows. Now it genuinely is.

**Also verified while here:** CI's backend-tests job installs `requirements-dev.txt`, whose
first line is `-r requirements.txt`, so CI really does resolve the same production floors —
the "CI is representative on versions" claim holds.

**Verification:** full backend suite green on the reconciled versions — i.e. on what
production actually runs, including `cryptography` 50, `pillow` 13 and `redis` 8, which no
local run had previously exercised. `ci.yml` parses and the two new steps land in the right
job, in the right order, scoped to the 3.12 leg so only one artifact is produced.
`backend/resolved-requirements.txt` is gitignored — it is build output, not source.

#### 786b — the reviewed bumps: PENDING

Unchanged in substance, but now better informed, because the floors have already delivered
`cryptography` 50, `pillow` 13 and `redis` 8 without review. What remains is the **exact-pin**
half, which cannot self-heal and is genuinely stale:

1. `fastapi` 0.136.1 → 0.150.0 and `SQLAlchemy` 2.0.49 → 2.1.5 — minor by version number,
   large by surface; treat each as a major for verification purposes.
2. `stripe` 15.1.0 → 16.0.0 — pair with the Sprint 780 webhook work rather than bumping it
   under a handler that was at 59.9% coverage a day ago.
3. Frontend majors individually: `typescript` 6 → 7, `framer-motion` 12 → 14,
   `@testing-library/jest-dom` 6 → 7.
4. Patches and safe minors in one batch, mirroring the 2026-04-19/22 hygiene pattern.

**Retrospective question worth putting to the CEO, not answering unilaterally:** the floors
are doing their job on CVE currency and have now shipped three unreviewed majors. Sprint 777
accepted that trade deliberately. Whether `pillow` and `redis` in particular should move to
`==` with Dependabot responsibility — they are image and cache libraries whose majors change
behaviour, unlike `cryptography` where currency is the whole point — is a revision of that
decision rather than an application of it.

---

### Sprint 738: Alembic migration drift cleanup
**Status:** PENDING — pre-4.1 sequence position 1.5. Could slip post-4.1 if priority shifts; not customer-visible either way.
**Priority:** P3. Catches up on dormant tech debt surfaced by Sprint 737's drift test.
**Source:** Sprint 737's parity test (`backend/tests/test_alembic_models_parity.py`) discovered 4 tables and 6 columns defined on models with no corresponding Alembic migration.

Write Alembic migrations for the documented drift in `PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS`. As each migration lands, remove the corresponding entry from the allow-list. When both allow-lists are empty, the parity test enforces full Alembic-models equivalence going forward.

**Tables needing CREATE TABLE migrations (4):**
- `password_reset_tokens` — defined in `backend/models.py`
- `processed_webhook_events` — defined in `backend/subscription_model.py`
- `tool_activities` — defined in `backend/models.py`
- `waitlist_signups` — defined in `backend/models.py`

**Columns needing ADD COLUMN migrations (6):**
- `engagements.completed_at` + `engagements.completed_by` — defined in `backend/engagement_model.py`
- `diagnostic_summaries.ccc` + `dio` + `dpo` + `dso` (cash-conversion-cycle ratios) — defined in `backend/models.py`

**Step 1 — production verification gate (FIRST, DO NOT SKIP):** Before writing any migration, query production Postgres via Render MCP `query_render_postgres` (or `psql` against `paciolus-api-db`) to confirm whether each of these 10 schema objects already exists in production. Three possible outcomes per object:
1. **Object exists in production but not in Alembic** → write a migration whose `op.create_table` / `op.add_column` is wrapped in an existence check (or use Alembic's `op.execute` with `IF NOT EXISTS`) so it's idempotent on re-run. The migration's job is to bring Alembic's recorded history into sync with production reality, not to actually mutate production schema.
2. **Object missing in production** → write a normal `op.create_table` / `op.add_column` migration; production gains the column on next deploy.
3. **Object never accessed in production** (model is dead code) → consider removing the model definition instead of writing the migration. Verify via grep + Render request-log analysis.

**Out of scope:**
- No model-side changes (the models are the source of truth; Alembic catches up to them).
- No removal of `Base.metadata.create_all()` from `init_db()` — it currently creates the 4 orphan tables on fresh DBs, and removing it before the migrations exist would break local dev / CI fixtures.

**Verification:**
- After Sprint 738 lands, `PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS` are both empty in `test_alembic_models_parity.py`.
- Test still passes (full parity now enforced).
- Production deploy logs after the migrations run show the relevant `op.create_table` / `op.add_column` log lines (or `already exists, skipping` for outcome (1) cases).

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

### Sprint 760: Dependency hygiene — patches + safe minors (2026-04-29 nightly)
**Status:** SUPERSEDED 2026-10-20 by **Sprint 786**. The 19-package list is six months stale — today's nightly reports 68 backend / 22 frontend outdated, so this batch no longer describes the work. Kept for the per-package rationale and the verification pattern.
**Priority:** P3. Routine maintenance batch; no security urgency at the patch/minor level.
**Source:** `reports/nightly/2026-04-29.md` Dependency Sentinel section.

Bundle the 19 patch + safe-minor updates into one commit, mirroring the 2026-04-19/2026-04-22 hygiene-batch pattern.

**Backend (15):**
- Patches: `click` 8.3.2→8.3.3, `fastapi` 0.136.0→0.136.1 (security-relevant, but patch-level), `hypothesis` 6.152.1→6.152.4, `Mako` 1.3.11→1.3.12, `python-multipart` 0.0.26→0.0.27, `ruff` 0.15.11→0.15.12.
- Minors: `anthropic` 0.96.0→0.97.0, `certifi` 2026.2.25→2026.4.22, `greenlet` 3.4.0→3.5.0, `packaging` 26.1→26.2, `pathspec` 1.0.4→1.1.1, `pip` 26.0.1→26.1, `stripe` 15.0.1→15.1.0 (security-relevant), `tzdata` 2026.1→2026.2, `uvicorn` 0.45.0→0.46.0.

**Frontend (4):** `@sentry/nextjs` 10.49.0→10.50.0, `@typescript-eslint/eslint-plugin` 8.59.0→8.59.1, `@typescript-eslint/parser` 8.59.0→8.59.1, `postcss` 8.5.10→8.5.12.

**Excluded from this sprint:**
- `cryptography` 46.0.7→47.0.0 (MAJOR — own sprint, see 761).
- `pdfminer.six` 20251230→20260107 (deferred, calendar version, review by 2026-04-30).

**Verification:**
- `pip install -r backend/requirements.txt && cd backend && pytest -q` clean.
- `cd frontend && npm install && npm run build && npm test` clean.
- Stripe SDK upgrade: confirm no breaking change in 15.1.0 vs 15.0.1 (CHANGELOG sweep + smoke-test billing webhook fixture).
- FastAPI patch: confirm no behavior change in `Depends`/middleware semantics (regression-suite covers this implicitly).
- Render deploy logs after merge: zero new ImportErrors, /health 200 within 60s.

**Out of scope:**
- Major upgrades (cryptography 47).
- Frontend `next` / `react` major sweeps (no action needed in this nightly).

---

### Sprint 761: cryptography 47.0.0 major upgrade (security-relevant)
**Status:** SUPERSEDED 2026-10-20 by **Sprint 786**. The target version is wrong by two majors — `cryptography` is at 50.0.2, not 47.0.0 — and Sprint 777 rejected this sprint's premise outright: `cryptography` stays a `>=` floor, so a fresh resolve already takes the current release. The isolated-major verification pattern below is still the policy and carries into 786.
**Priority:** P2 (security-relevant; pyca/cryptography ships CVE fixes via majors and the lib underpins JWT signing, password hashing, TLS evidence chain).
**Source:** `reports/nightly/2026-04-29.md` Dependency Sentinel — flagged as security-relevant + major.

**Pre-flight:**
1. Pull pyca/cryptography 47.0.0 release notes; flag any signature on `cryptography.hazmat.primitives.*` we depend on (JWT library, audit_chain TLS evidence, password reset token signing).
2. Audit direct imports: `Grep -r "from cryptography" backend/`. Cross-reference each call site against the 47.0.0 deprecation/removal list.
3. Identify transitive consumers (PyJWT, pyOpenSSL, requests-toolbelt, etc.) and confirm each is compatible with cryptography 47.x — pin floor in `requirements.txt` if any consumer requires <47.

**What lands:**
- `backend/requirements.txt` — `cryptography==47.0.0` (pin exact, not floor; Paciolus convention).
- Any compatibility shims for hazmat primitives that changed signature (unlikely for a properly-maintained version-bump, but possible).
- New regression test if a hazmat surface we depend on changed shape.

**Verification:**
- Backend `pytest` clean (especially: `tests/test_auth*.py`, `tests/test_password_reset*.py`, `tests/test_audit_chain*.py`, `tests/test_csrf*.py`, `tests/test_security_hardening*.py`).
- Manual: register → verify-email → login → logout → refresh-token → password-reset round-trip on a local instance.
- Render preview deploy: 24h soak before promoting to prod (per Paciolus prod-cutover policy for security-critical deps — same caution we used for the FastAPI 0.135.x bump in Sprint 263 era).

**Out of scope:**
- Bundling with the patch/minor batch (Sprint 760). Majors get their own sprint so a regression doesn't taint a 19-package roll-back.
- Migrating to `joserfc` or another JWT library — out of scope; we're upgrading the underlying primitive, not the wrapper.

---

### Sprint 762: flux_expectations memo PDF contract test (close 17/18 → 18/18)
**Status:** PENDING. Closes the lone gap from the post-initiative finishing pass memo-coverage push.
**Priority:** P3.
**Source:** Post-Sprint-754b memo contract test sweep (commit `60946271`). 17/18 memos covered; flux_expectations skipped because its dataclass nests `FluxExpectationLine` Pydantic sub-models that need a non-trivial fixture.

**What lands:**
- `backend/tests/test_export_pdf_contract.py::test_flux_expectations_memo_pdf_contract` — single test mirroring the established memo-contract pattern (asserts: PDF bytes returned, `%PDF-` magic header, ReportLab Story renders without exception, branded variant with logo+colors works).
- Inline fixture for `FluxExpectationsResult` with at least one `FluxExpectationLine` entry; reuse existing `_make_flux_result` helper if shape-compatible.
- Update `tasks/lessons.md` with the nested-Pydantic-fixture pattern if a generalizable lesson emerges.

**Verification:**
- `pytest backend/tests/test_export_pdf_contract.py -v` — 18/18 memo contract tests pass (was 17/18).
- No coverage regression in `flux_expectations_memo_generator.py`.

**Out of scope:**
- Refactoring the memo generator — pure test addition.
- Adding contract tests for the 3 non-memo report PDFs (combined audit, financial statements, anomaly summary) — separate filing if needed.

---

### Sprint 778: Build the off-provider backup, then prove recovery works
**Status:** PENDING.
**Priority:** P1 — both halves in scope: build the backup that does not exist **and** verify that recovery works.

> **Heading corrected 2026-10-20.** This sprint was briefly titled "off-provider backup deferred", which contradicted its own scope item 1. The deferral was withdrawn the same day it was made (see the DECISION block above and `tasks/EXECUTIVE_BLOCKERS.md` → Resolved Decisions). The backup ships pre-launch.

**Source:** 2026-10-19, while re-enabling the inactivity-disabled scheduled workflows (Sprint 775 work).

Re-enabling the three auto-disabled workflows surfaced that two of them cannot pass as written:

- **No repo secrets exist at all.** `gh secret list` returns empty, so `RENDER_API_KEY` and `RENDER_POSTGRES_ID` are unset. `scripts/verify_backup_integrity.py` exits 2 on `RENDER_API_KEY is not set`, which is why `backup-integrity-check` failed every month before being disabled.
- **They point at the wrong provider.** Both `verify_backup_integrity.py` and `dr-test-monthly.yml` query `api.render.com/v1/postgres/$RENDER_POSTGRES_ID`. Production Postgres is on **Neon** (since Phase 1, 2026-04-09) and the orphan Render Postgres was deleted 2026-04-22, so even with secrets these checks interrogate a database that does not exist.
- **`DR Test (Monthly)` is a false-green.** Its last scheduled run (2026-09-01) reported workflow-level **success**, yet its internal `render-check` step resolves `api_error` → `result=FAIL`; the overall verdict only gates issue creation, not the job's exit status. Same class of defect as the 2026-04-22 false-green incident that motivated Sprint 712.
- **Phase 4.4 was never implemented**, so the `paciolus-backups` R2 bucket holds no `pg_dump` artifacts. Neon's own PITR is the only thing standing behind production data; there is no off-provider copy and no restore-drill evidence.

**Scope** (the decision above is settled — do not reopen it):
1. **Implement the `pg_dump` → R2 cron** into the already-provisioned `paciolus-backups` bucket. Options costed in `ceo-actions.md` §4.4: Render Cron Job (~$1/mo), GitHub Action (free), Upstash Scheduled Function.
2. **Verify Neon PITR too** — confirm the actual retention window on the current plan rather than trusting the 7-day/30-day figure in `DEPLOYMENT_ARCHITECTURE.md:724`.
3. **Perform one real restore drill against each mechanism** and record the evidence. Verify schema parity and row counts against production. An untested backup is not a backup — this is the half of the risk a second mechanism does not address.
4. **Rewrite both DR workflows against Neon + R2** instead of the Render Postgres API, which queries a database deleted on 2026-04-22.
5. **Fix the false-green** so a job's exit status reflects its own verdict, and make the missing-credential case report "unverified" explicitly rather than dying on an opaque error.

**Note:** all three workflows were re-enabled on 2026-10-19. `dependency-compliance` now passes (its CVEs were fixed the same day), but **`backup-integrity-check` will fail on the 1st of each month and file a `dr-failure` issue** until this sprint lands. That signal is substantively true — backups genuinely are unverified — but its stated reason will be the misleading "RENDER_API_KEY is not set". Either accept it as a forcing function or disable that one workflow until the rewrite.

---

### Sprint 779: Boundary-language and citation residue (liability pass)
**Status:** COMPLETE.
**Priority:** P1 — pure liability reduction, no dependencies.
**Source:** `reports/launch-readiness-assessment-2026-10-19.md` B-1 and B-3.

The highest-consequence category of defect in this product is language that edges from *diagnostic indicator* toward *audit conclusion*, because that is the boundary the whole liability posture rests on. Three pieces of residue survive:

1. **`generate_sample_reports.py:2266`** still emits "systemic review of procure-to-pay controls recommended". The production memo generator was fixed; the sample generator was not — and it produces the sample output a prospect may well see first. Rephrase to match the shipped wording ("engagement team should evaluate whether procure-to-pay procedures warrant expansion").
2. **Risk-tier labels are unqualified.** Every testing memo auto-assigns low/elevated/moderate/high from flag density, and the label is visually prominent enough for a practitioner to read it as an ISA 315 risk-assessment conclusion. Append the qualifier the April audit asked for: "(automated flag density — auditor judgment required per ISA 315)".
3. **AS 1215 is still miscited as a JE Testing standard in three internal docs** — `docs/03-product/REPORT_STANDARDS_SPEC.md:440`, `docs/01-product/USER_PERSONAS.md:273`, `docs/02-technical/ARCHITECTURE.md:380`. Customer-facing surfaces are already correct and CI-guarded; this is the leftover. AS 1215 is *Audit Documentation*; the JE fraud standard is AS 2401. Ten-minute fix, worth doing because the customer-facing version of this exact error was ranked the single most dangerous finding in the system.

**Verification:** extend `test_memo_boundary_phrasing.py` to assert the sample generator is held to the same banned-phrase rules as the shipped generators — otherwise this recurs. Extend `test_citation_consistency.py` to cover `docs/` so the citation cannot drift back.

#### What landed

**1. Sample-report phrasing (`generate_sample_reports.py:2266`).** The root-cause clause is gone.

**Correction to this brief:** it instructed rephrasing to match "the shipped wording", quoted as
*"engagement team should evaluate whether procure-to-pay procedures warrant expansion"*. **That wording
exists nowhere in the codebase** — the brief described a fix that never landed. The shipped tier
commentary is `three_way_match_memo_generator.py:112` *"Below best practice — investigate patterns"*, and
`tests/test_twm_memo.py:166` asserts the shipped finding text carries no recommendation clause at all.
Aligned to what ships: *"Below 80% best practice threshold; investigate matching patterns (auditor
judgment required to determine cause)"*.

**2. Risk-tier qualifier — one constant, not eight edits.** `RISK_TIER_BASIS_NOTE` in `shared/memo_base.py`
reads *"Basis: automated flag density — auditor judgment required per ISA 315. The diagnostic tier is an
indicator, not a risk assessment or a conclusion on internal control."* It is **composed into
`RISK_SCALE_LEGEND`**, which is already rendered on every surface that prints a tier — the shared
`build_results_summary_section` path plus bank rec, engagement dashboard, multi-period, three-way match and
the TB diagnostic PDF. So surfaces added later inherit the qualifier without a code change.

`anomaly_summary_generator.py` was the one gap: it builds its label straight from `RISK_TIER_DISPLAY` and
never rendered the legend, so its §I summary line and its prominent §IV "ENGAGEMENT RISK INDICATOR" box
now render the note explicitly.

**3. AS 1215 → AS 2401 / ISA 240** in `docs/03-product/REPORT_STANDARDS_SPEC.md:440`,
`docs/01-product/USER_PERSONAS.md:273` and `docs/02-technical/ARCHITECTURE.md:380`. Matched to
`tools_registry.py`, whose canonical JE standards are `("ISA 240", "AS 2401", "Nigrini 2012")` — note the
docs also claimed ISA 530, which is sampling, not the fraud standard. Fixed an adjacent count drift in the
same line while there: JE is a 19-test battery, not 18.

#### The two guards, and what widening them found

**Boundary scan scope was the actual defect.** `test_memo_boundary_phrasing.py` has protected memo wording
since Sprint 721, and the pattern that catches this exact phrase (`\bsystemic\s+review.*recommended\b`)
was already in it. Nothing was missing from the rules — only from the file list, which was the glob
`backend/*_memo_generator.py`. Added `EXTRA_SCANNED_FILES`: the sample generator, anomaly summary,
engagement dashboard, and three shared text modules, with a test asserting every path in it still resolves
so a rename cannot silently drop coverage.

Widening surfaced nine more hits — **eight legitimate, one real**:
- Eight are ISA 265 *negative* use: "does not constitute an audit opinion", "classification … is a matter
  of auditor judgment", and the literal title of PCAOB AS 1305. Annotated `# allow-deny-phrase: <reason>`,
  matching the precedent at `analytical_expectation_memo_generator.py:58`.
- One was real: `shared/follow_up_procedures.py:153` told the auditor a misposting "requires correction" —
  a conclusion about the entity's records, in text reused across tools. Now "warrants further review".

**Scanner refinement:** the scan also fired on `anomaly_summary_generator.py`'s module docstring, where a
`GUARDRAIL` note names the ISA 265 sections the template deliberately refuses to produce. Naming them is
the point, and annotating it put a pseudo-comment inside docstring prose. `_scan_source` now skips the
module-docstring line range via `ast` — a module docstring is maintainer documentation and never reaches a
rendered PDF.

**Citation scan scope, same lesson.** `test_citation_consistency.py` covered customer-facing surfaces only,
which is exactly why Sprint 717's sweep held on all five of those and then drifted back in three internal
docs for six months. The AS-1215 adjacency check now runs over `DOC_SCANNED_GLOBS` as well. The
**registration** check deliberately stays customer-facing: internal docs legitimately cite unregistered
standards in post-mortems and lexicon examples, and failing on those would make the guard noisy enough to
get disabled.

#### Verification

- Both guards **regression-proved**: each defect re-introduced, the corresponding test confirmed to fail
  naming the offending file, then restored to green. 29/29 on the two guard suites.
- Targeted sweep over every memo / report / citation / boundary / PDF-contract suite: **1,197 passed**.
  The 18 memo PDF contract tests render through ReportLab, which is what validates the `<br/>` in the
  recomposed legend.
- Full backend suite green; `ruff check` clean, `ruff format` applied; `mypy` reports no new errors in the
  touched modules.
- No frontend files touched.

---

### Sprint 780: Stripe price-parity preflight + webhook coverage (money path)
**Status:** COMPLETE.
**Priority:** P1 — had to land before the first live charge. Independent of pricing decisions, so it was safe to build before Sprint 781 reports.
**Source:** `reports/launch-readiness-assessment-2026-10-19.md` §F and §C.

1. **Price-parity preflight.** `billing/price_config.py` holds the canonical amounts and `test_pricing_launch_validation.py` carries ~20 assertions — but they only check the table *against itself*. Nothing fetches the Stripe Price object to confirm the amount a customer is actually charged matches the amount the product intends and the page displays. Test mode is documented as still sitting at the previous price list, so displayed and charged price **already disagree** in the only environment where billing has ever run. Add a script that reads every `STRIPE_PRICE_*` and `STRIPE_SEAT_PRICE_*` env var, retrieves the Price object, and asserts `currency == "usd"` plus the correct expected amount, failing loudly and naming every mismatch. **Use the real constant names** — the canonical base amounts are `PRICE_TABLE[tier][interval]` (not `TIER_PRICES`, which does not exist), and the four seat amounts live separately in `PROFESSIONAL_SEAT_PRICE[interval]` and `ENTERPRISE_SEAT_PRICE[interval]`. All six base prices and all four seat prices must be covered; mapping only the base table would silently skip the seat add-ons the same requirement calls for. Wire it into the Phase 4.1 checklist ahead of the webhook preflight.
2. **Webhook handler coverage.** `billing/webhook_handler.py` is the least-covered critical path at **59.9% / 174 uncovered statements** — and it is the one that moves money. This is the webhook-coverage sprint deferred in Sprint 676 and again in the 2026-04-20 refactor pass. Target 85%+ on the handler, prioritising signature verification, event dedup (`processed_webhook_events`), and the subscription state transitions that drive entitlements.

**Out of scope:** building live-mode prices. That waits on pricing feedback from Sprint 781.

#### What landed

**1. `scripts/stripe_price_parity_preflight.py`** — the first thing in this codebase that
compares intent against Stripe. It imports `PRICE_TABLE`, `PROFESSIONAL_SEAT_PRICE` and
`ENTERPRISE_SEAT_PRICE` (never restates an amount), retrieves each Price object, and checks
six properties per price:

| Check | Why it is there |
|-------|-----------------|
| `unit_amount` equals the canonical cents | the v2-vs-v3 case: Solo at $50 against a $100 table |
| `currency == "usd"` | a non-USD price charges a plausible-looking wrong number |
| `recurring.interval` matches the env var | **a correct amount on the wrong cadence bills right once and wrong forever** |
| `active is not False` | an archived price fails checkout at the worst moment |
| `livemode` agrees with the key's mode | stops a live deployment wired to test prices |
| retrievable at all | an expired or wrong-account key is a cutover blocker |

Coverage is **all ten** price objects (6 base + 4 seat) plus both coupons. `--require-all`
turns unset IDs into a failure for use immediately before cutover. Exit codes separate
mismatch (1) from misconfiguration (2), and a mismatch outranks unset IDs so a real defect
is never masked.

**Two facts it surfaced on its first run** against `backend/.env`:
- The local test-mode secret key is **expired** (`AuthenticationError: Expired API Key`), so
  the abandoned test mode is doubly dead — it is at v2 prices *and* unreachable.
- Only 4 of 10 price IDs resolve locally, because `backend/.env` still carries the v2 names
  (`STRIPE_PRICE_TEAM_*`, `STRIPE_SEAT_PRICE_MONTHLY`) that `price_config.py` no longer
  reads. Running the preflight is now the cheapest way to detect that class of drift.

**2. Webhook handler coverage: 55% → 88%** on the billing-focused subset (target was 85%).
Five handlers and four helpers had **no** coverage at all; 43 new tests in
`tests/test_webhook_handler_coverage.py` cover `handle_subscription_created`,
`handle_invoice_payment_succeeded`, `handle_dispute_created`, `handle_dispute_closed`,
`handle_invoice_created`, `_downgrade_org_members_to_free`, `_apply_dpa_from_metadata`,
`_portal_url_for_user`.

The tests are written around money-relevant invariants rather than line coverage:
- **Entitlement state after every event** — status *and* `user.tier`, since those are two
  separate writes and only the pair is the entitlement.
- **Org blast radius.** A dispute or a lost dispute must downgrade every org member, not just
  the subscription owner; two tests assert colleagues lose access too.
- **Idempotency.** Stripe retries, so `invoice.payment_succeeded` on an already-ACTIVE
  subscription must record nothing, and `customer.subscription.created` arriving after
  `checkout.session.completed` must not double-count the creation in analytics.
- **Refusal to guess.** `customer.subscription.created` with an unresolvable tier aborts
  without syncing — better to do nothing than to sync a subscription to the wrong tier.
- **Dispute resolution is three paths, not two.** `won` restores, `lost` cancels, and
  anything else (e.g. `warning_closed`) must leave the subscription suspended rather than
  silently restoring access.

**A dead branch found while testing.** Both restore paths wrap `UserTier(sub.tier)` in
`except ValueError`, but that branch is **unreachable**: `Subscription.tier` is a constrained
DB enum, so a value outside `UserTier` cannot survive a round-trip (the Enum type raises on
*result processing*, before any handler reads it), and both handlers flush after the
conversion. Rather than contort a test to reach dead code, there is now one test pinning the
constraint that makes the defence redundant — it fails and names the cause if the
`subscription_tier` enum and `UserTier` ever diverge.

**Still uncovered** (deliberately, and recorded rather than left implicit):
`_auto_create_organization` internals (lines 40–67), branches inside
`handle_checkout_completed` (237–259) and `handle_subscription_updated` (305–377), and three
single lines in `trial_will_end`. Those paths are exercised end-to-end by the existing route
tests; the remaining gap is branch-level, and 88% already clears the sprint's bar.

#### Verification

- `tests/test_stripe_price_parity_preflight.py` — **25 tests**, every one driving a fake
  `stripe` module, so no network and no keys. Each failure mode is asserted independently,
  plus a test that the preflight's expectations equal `price_config`'s tables, so the two
  cannot drift apart.
- `tests/test_webhook_handler_coverage.py` — 43 tests.
- Full backend suite green; `ruff check` and `ruff format` clean under `backend/ruff.toml`.

#### Out of scope, unchanged

Building the live-mode products and prices. That still waits on Sprint 781 — there is no
point creating prices for a number no practising CPA has agreed to.

---

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

### Sprint 769: Frontend context memoization (render-perf hotfix)
**Status:** COMPLETE — landed on branch `sprint-769-frontend-context-memoization`.
**Priority:** P2. No user-visible bug, but cascade re-renders measurably affect interactive latency in tools mounted under DiagnosticProvider/EngagementProvider.
**Source:** Frontend efficiency audit (2026-05-01) findings 1.1 + 1.2.

`DiagnosticContext` and `EngagementContext` were building a fresh `value` object literal on every provider render. With `setResult` / `clearResult` also fresh closures, every consumer re-rendered whenever the provider's parent re-rendered, regardless of whether the carried state actually changed.

**What landed:**
- `DiagnosticContext.tsx` — `setResult` / `clearResult` wrapped in `useCallback([])`; provider `value` wrapped in `useMemo([result, isLoading, setResult, clearResult])`. (`setIsLoading` is the React-stable `useState` setter, omitted from deps per React semantics.)
- `EngagementContext.tsx` — `contextValue` wrapped in `useMemo` with the full 10-key dep array (5 state values + 5 already-memoized handlers).
- Inline rationale block added above the URL-sync `useEffect` (`EngagementContext.tsx:115`) documenting why `searchParams` / `selectEngagement` / `activeEngagement` are deliberately excluded from deps: including `searchParams` would loop because `selectEngagement`'s own `router.replace` rotates the value; `selectEngagement` itself re-creates whenever `searchParams` change (same loop); and `activeEngagement` is the load-bearing one-shot guard inside the body. The eslint-disable is intentional, not a stale-closure bug.

**Verification:**
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npx jest --watch=false --testPathPatterns="(Diagnostic|Engagement)"` → **52 passed, 0 failed** (7 suites). Pre-existing `act()` warnings on `EngagementBanner.tsx:35` are not regressions and originate from `useEffect`-triggered `setClientName` in test renders unrelated to Sprint 769's surface.
- `cd frontend && npm run build` → exit 0; all routes correctly dynamic (`ƒ`).

**Out of scope:**
- Splitting either context into state-vs-dispatch halves — bigger refactor, not warranted by current symptoms.
- Other render-perf findings (row mappings, table memoization, result-subtree wraps) — bundled in Sprint 773.

**Commit SHA:** see branch `sprint-769-frontend-context-memoization` (filled at PR merge).
### Sprint 771a: Button primitive (subset of Sprint 771)
**Status:** COMPLETE — landed on branch `sprint-771a-button-primitive`.
**Priority:** P3.
**Source:** Frontend efficiency audit (2026-05-01) finding 2.2.

Splitting Sprint 771 into 771a (Button primitive — this sprint) and 771b (the three Tool* primitives — `ToolHeroHeader` / `ToolLoadingState` / `ToolErrorState`, deferred to a follow-up). 771a is the lowest-risk, highest-leverage subset: ~30 hand-rolled `bg-sage-600 …` and `bg-surface-card border border-oatmeal-300 …` button class-string copies are the most common offender, and a centralized primitive removes that drift point ahead of the hero/loading/error rollup.

**What landed:**
- `frontend/src/components/ui/Button.tsx` (new, ~60 lines) — `forwardRef` button with `variant: 'primary' | 'secondary' | 'ghost'` and `size: 'sm' | 'md' | 'lg'`. Single base class string covers font, transition, disabled state, focus ring; variant/size class maps compose on top. Inline doc-comment explains each variant's intended use (primary = page-commit action, secondary = tertiary alongside primary, ghost = inline toolbar).
- 5 tool pages migrated from inline class strings to `<Button>`:
  - `app/tools/ap-testing/page.tsx`
  - `app/tools/fixed-assets/page.tsx`
  - `app/tools/inventory-testing/page.tsx`
  - `app/tools/payroll-testing/page.tsx`
  - `app/tools/revenue-testing/page.tsx`
- Each of the 5 pages had the same 4-button shape: 1 secondary "Try Again" in the error state + 3 buttons in the success-state action bar (primary "Download Testing Memo", secondary "Export Flagged CSV", secondary "New Test"). 20 total buttons replaced.

**What did NOT change (deferred):**
- AR aging (`px-8 py-3 rounded-xl` "Run AR Aging Analysis" hero CTA) — different size variant; needs `size="lg"` migration in 771b alongside the dual-FileDropZone landing of Sprint 770.
- Statistical sampling — its primary button differs slightly (no `disabled:opacity-50` suffix); migrate alongside 771b.
- `account-risk-heatmap`, `composite-risk` — buttons embedded in row-editor mini-components flagged for `React.memo` extraction in Sprint 773 follow-up; migrate when those subtrees are touched.
- `ToolSettingsDrawer` — full-width primary button; migrate alongside 771b.
- The other Sprint 771 primitives (ToolHeroHeader, ToolLoadingState, ToolErrorState) — deferred to 771b.

**Verification:**
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npx jest --watch=false` → see commit-message tail.
- `cd frontend && npm run build` → see commit-message tail.

**Out of scope:**
- ESLint rule banning the inline class strings the new primitive replaces — useful future fence, not this sprint.

**Commit SHA:** see branch `sprint-771a-button-primitive` (filled at PR merge).

---

