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

- [2026-10-23] Sprint 797 follow-up — `test_alembic_head_matches_base_metadata_foreign_keys` ran in-process and was therefore measuring another fixture's dialect. First push of this branch went green on both SQLite jobs and **red on PostgreSQL 15**, reporting `organizations.subscription_id`, `tool_activities.engagement_id` and `users.organization_id` as "in Alembic but not in model". **The drift was never real.** Those three are the ORM's `use_alter=True` FKs (they break the organizations → users → subscriptions cycle), and `use_alter` changes how `create_all()` emits a constraint per dialect: SQLite inlines it because it cannot `ALTER TABLE ADD CONSTRAINT`, PostgreSQL emits a separate ALTER. `Base.metadata` is process-global, so the session `db_engine` fixture's `create_all()` against Postgres left the shared metadata in a state where the test's *own* SQLite `create_all()` stopped emitting all three — and both halves of the test use SQLite, so only the models half lost them. Reproduced locally with a mock PG engine (no server): the old test fails with the three CI errors verbatim, the fixed one passes. Now runs in a clean subprocess, for the same reason — and with the same docstring warning — that `test_init_db_alone_creates_every_table` beside it already did. Sprint 797 learned that lesson for one test and not its neighbour. Files: `backend/tests/test_alembic_models_parity.py`, `tasks/todo.md`, `tasks/lessons.md`.
- [2026-10-23] carry-forward consolidation — after PRs #198 + #199 merged (28 findings from the two 2026-10-22 reviews), recorded every known-unaddressed item in one `CARRIED FORWARD` block so the next session starts from a list rather than re-deriving one: the two items needing a practitioner or a roadmap call (793b's 2026 figures, A-8's §179/§168(k)/real-property scope), the four parked with owners named (T-1, T-2, T-5, D-6), the seven surfaces neither review examined — **auth/CSRF/JWT/injection/rate-limiting is the largest** — and three contrast items that were blocked on the route→theme map and are **now unblocked** because Sprint 809 built it. Also filed **Sprint 823**: measured that only 11 of the 18 tools have synthetic generators, and **six of the seven uncovered ones are exactly the tools Sprint 689 added** — the framework predates that 12→18 expansion and was never extended to it. Notes that `ceo-actions.md:65` cannot be executed as written, because 14 of the 18 tools do not take a trial balance. No code changed. Files: `tasks/todo.md`.
- [2026-10-20] nightly audit artifacts — 2026-10-20 batch (daily brief + 6 sentinel JSONs + run_log) plus `.baseline.json` refreshed to the new QA Warden values (8,700 backend / 2,013 frontend, 0 failures — the first all-green baseline since 2026-05-31). Overall verdict RED on **Dependency Sentinel alone**: 68 backend / 22 frontend outdated, 5 security-relevant. Scanned for secrets before staging (no `sk_live`/`sk_test`/private-key/credentialed-URL matches). Files: `reports/nightly/*`.
- [2026-10-20] worklist consolidation — assessed `reports/launch-readiness-assessment-2026-10-19.md` and the 2026-10-20 worklist in `SESSION_STATE.md`, re-verified every load-bearing claim against current source (all still true, including the three Sprint 779 liability targets, the 59.9% webhook coverage, the empty secret store and the 404 on `api.paciolus.com`), and filed the result as `reports/next-actions-2026-10-20.md` — seven tracks, ten findings neither document covered. **Three documents disagreed about the backup decision:** `SESSION_STATE.md` still carried the version deferred "before the second paying customer", justified by the premise Sprint 783 had just disproved, while `EXECUTIVE_BLOCKERS.md`, this file's DECISION block and the assessment addendum all said pre-launch. Since `AGENTS.md` makes `SESSION_STATE.md` the first file a session reads, the stale copy was the one being acted on — corrected, along with Sprint 778's heading, which contradicted its own scope item 1. Also filed Sprints **784** (tool-count cohesion 12 → 18; `backend/main.py:243` ships "12-Tool Audit Intelligence Suite" in the public OpenAPI description against a canonical 18), **785** (nine real-work PRs went `MERGEABLE` → `CONFLICTING` when the 10-19/20 merges rewrote this file; seven finished sprints stranded) and **786** (dependency currency, superseding 760/761 — both written in April and wrong in their specifics; includes reconciling `backend/venv`, which matches neither `requirements.txt` nor production yet is what the nightly measures). Sprint 741 marked unblocked: its prerequisite log read was impossible while prod returned 500 for 5.5 months. No code changed. Files: `reports/next-actions-2026-10-20.md`, `tasks/todo.md`, `SESSION_STATE.md`, `tasks/ceo-actions.md`.
- [2026-10-19] review gate removed + two CEO-delegated decisions recorded — CEO confirmed a soft launch date and delegated the open decisions (`reports/launch-readiness-assessment-2026-10-19.md` §I). **(a) Branch protection:** `required_pull_request_reviews` removed from `main` via the Actions API; all 12 required status checks retained with `strict: true`. Rationale: GitHub forbids self-approving your own PR, so a 1-review requirement is unsatisfiable solo and every merge was clearing it with `gh pr merge --admin` — which, because `enforce_admins` is `false`, bypasses **the status checks too**, not just the review. The bypass was strictly more dangerous than the gate was useful. With reviews removed, merges take the normal path and CI genuinely blocks; `--admin` should no longer be needed, and needing it is now a signal. Note `required_linear_history` remains `true`, so merges must be **squash or rebase** — merge commits were only ever possible via the bypass. `enforce_admins` left `false` deliberately as a break-glass for a solo operator. **(b) Neon backup posture:** decided — see Sprint 778 and `tasks/EXECUTIVE_BLOCKERS.md`. No code changed.
- [2026-10-19] frontend CVE sweep clearing the red Node CI gates — `npm audit fix` (no `--force`, so every change stayed inside the existing semver ranges and **`package.json` was not touched**; lockfile only). Production dependency vulnerabilities went **22 → 0** (was 1 critical, 7 high, 13 moderate, 1 low). The critical was **Next.js itself**: 16.2.4 sat inside the `9.3.4-canary.0 – 16.3.7` advisory range. Also moved: `postcss` 8.5.10→8.5.31 (three advisories for arbitrary file read / path traversal via attacker-controlled `sourceMappingURL` in CSS comments), `sharp` 0.34.5→0.35.5 (inherited libvips CVE-2026-33327/33328/35590/35591, libheif GHSA-g89c-p67h-r497 + GHSA-2jg2-4ch7-h545, librsvg CVE-2026-96889), `source-map-js` 1.2.1→1.2.2 (event-loop DoS via indexed source-map section offsets), `nanoid` 3.3.11→3.3.20, `browserslist` 4.28.2→4.29.4, `fast-uri` 3.1.0→3.1.8. Net lockfile churn −622 lines (dedup). **Why this mattered beyond hygiene:** `ci.yml` runs `Node Dependency Audit (blocking)` as `npm audit --omit=dev --audit-level=high`, and it had been failing — so together with the PyJWT/python-multipart bump above, all six red dependency/CVE jobs now pass, which is what had every one of the 13 non-dependabot PRs sitting at `mergeStateStatus: BLOCKED`. Verified: `npm audit --omit=dev --audit-level=high` → 0 vulnerabilities (exit 0); `npx tsc --noEmit` → exit 0; `npm run build` → clean, and every route still renders `ƒ (Dynamic)` with `ƒ Proxy (Middleware)` active, so the nonce-based CSP contract is intact across the Next.js minor bump; `npm test` → 207 suites / 2,013 tests / 5 snapshots, 0 failures. 21 dev-only advisories remain (20 moderate + 1 high, the `babel-jest` → `@jest/transform` → `babel-plugin-istanbul` chain); all three CI audit gates pass `--omit=dev`, so they do not gate, and clearing them needs `npm audit fix --force` (breaking major bumps) — deliberately left. Final confirmation of the Next.js bump should be a Vercel preview deploy, since build output cannot prove runtime nonce propagation. Files: `frontend/package-lock.json`.
- [2026-10-19] nightly audit artifacts — 109-day backlog (2026-05-02 → 2026-10-19) committed in one batch: 795 files, 3.3 MB (109 daily `.md` briefs + 109 `.run_log` + 109 coverage, 108 sprint_shepherd, 108 scout, 105 dependency_sentinel, 104 report_auditor, 43 qa_warden sentinels), plus `.baseline.json` refreshed to the 2026-10-14 QA Warden / 2026-10-19 Report Auditor values. The overnight cron kept running through the entire 2026-05-01 → 2026-10-19 repo dormancy; nobody committed its output. Scanned for secrets before staging (no `sk_live`/`sk_test`/private-key/credentialed-URL matches). **Notable asymmetry:** only 43 of 109 nights produced a `qa_warden` sentinel, i.e. the test-suite agent failed to run on ~66 nights — which is exactly what PR #145 (`fix: raise qa_warden orchestrator timeout to 1700s`, opened 2026-05-11) was written to fix and never merged. The backend suite takes ~715–780s and the orchestrator's timeout sat below that, so the one agent that would have reported a red suite was the one most likely to time out. A concrete, measurable cost of the unmerged-PR backlog. Also confirms the nightly runs against `backend/venv` (`run_log` shows `backend\venv\Scripts\python.exe`), not system Python — relevant because the two environments have drifted apart. Files: `reports/nightly/*`.
- [2026-10-19] security dep bumps clearing the red `dependency-compliance` CI gate — `PyJWT[crypto]` 2.12.1→2.15.1 and `python-multipart` 0.0.26→0.0.32. The weekly `dependency-compliance` job ("Python CVE & License Audit", `pip-audit --desc --ignore-vuln CVE-2026-3219`) had been failing every run through 2026-08-24 (then stopped only because GitHub disables cron workflows after ~60 days of repo inactivity) with **12 known vulnerabilities in 2 packages** — and those were the *only* two packages flagged. PyJWT 2.12.1 carried PYSEC-2026-175..179, all fixed in 2.13.0; python-multipart 0.0.26 carried PYSEC-2026-3036/3037 (QuerystringParser treated `;` as a separator contrary to WHATWG, plus a quadratic rescan), PYSEC-2026-3039 (unbounded multipart part-header count/size → CPU DoS) and PYSEC-2026-3040 (`parse_form()` did not validate `Content-Length`; a negative value turned the bounded chunked read into read-until-EOF, loading the whole body into memory in one read) — all four land by 0.0.31. **Paciolus was not exploitable on the PyJWT advisories:** `decode()` always passes `algorithms=["HS256"]`, a single symmetric algorithm, so the asymmetric/HMAC key-confusion in PYSEC-2026-179 cannot trigger, and `PyJWKClient`/`jku` are unused so the PYSEC-2026-175 SSRF surface does not exist. **Nor, on closer inspection, was it exploitable on most of the python-multipart advisories.** PYSEC-2026-3040 is fully mitigated by our own `MaxBodySizeMiddleware`, which rejects a negative `Content-Length` with 400 *before* any body bytes are read (`security_middleware.py:162`) and independently caps streamed bytes in a second layer, so the read-until-EOF path is unreachable. PYSEC-2026-3036/3037 target `QuerystringParser` (`application/x-www-form-urlencoded`); Paciolus's `Form()` parameters are all paired with `UploadFile`, i.e. `multipart/form-data` handled by `MultipartParser`, and those endpoints require auth — reachable only if a client deliberately posts urlencoded, and the impact (field-separator differential on column mappings and IDs) is immaterial. The one genuinely relevant advisory is **PYSEC-2026-3039** (unbounded multipart part-header count/size): reachable across the ~50 `UploadFile` endpoints and only *partially* mitigated — the global body cap bounds total bytes, so it bounds how many headers fit, but does not eliminate CPU cost within that budget. Net: no historical compromise window; the bump is correct hygiene and unblocks the gate. **Root-cause insight worth keeping:** these were the only two CVE-flagged packages because they were the only two pinned with exact `==`. Every other CVE-carrying dependency (`cryptography`, `pillow`, `pypdf`, `pyasn1`, `werkzeug`) is pinned with a `>=` floor, and the transitives (`starlette`, `urllib3`, `anyio`, `idna`, `mako`) are unpinned, so a fresh `pip install -r requirements.txt` — which is what CI and the production Docker build both do — resolves them to latest and they self-heal. Exact pins buy reproducibility and rot; floors buy CVE currency and unreviewed upstream churn. requirements.txt currently mixes both without a stated rule; see Sprint 777 for the deliberate decision. Verified: venv auth suite 116/116, upload suite 223/223, and `pip-audit` no longer reports pyjwt or python-multipart. Files: `backend/requirements.txt`.
- [2026-10-19] inventory fixture date time-bomb — `test_inventory_testing.py::TestCompositeScore::test_clean_data_low_score` had been RED in every nightly since 2026-05-31 with no commit behind it. `sample_inv_rows()` hardcoded `Last Movement Date` literals in late 2025; IN-06 (slow-moving) compares against `date.today()` with a 180-day default threshold, so as wall-clock time advanced all 5 "clean" rows crossed it, flagged 100% slow-moving, and escalated `risk_tier` LOW→MODERATE (the `score < 25` assertion still passed at 10.5 — only the tier assertion caught it). Replaced the literals with a `_days_ago(n)` helper, matching the relative-date pattern the dedicated `TestSlowMovingInventory` cases already used; offsets 30/31/46/72/121 preserve the original fixture's relative ordering and spread while staying well inside the threshold. Also fixed the same latent bug in `make_large_dataset()` (all 20 rows shared `2025-11-01`; not yet tripped). Root cause of the *delay* in noticing: `TestSlowMovingInventory::test_recent_movement_no_flags` never asserted `entries_flagged == 0` despite its name, so fixture staleness stayed invisible there — assertion added with a diagnostic message. Backend: 134/134 inventory tests pass (was 133/134). Files: `backend/tests/test_inventory_testing.py`.
- [2026-05-11] qa_warden orchestrator timeout fix — `DEFAULT_AGENT_TIMEOUT_S` (900s) was less than qa_warden's own internal subprocess budget (1200s pytest + 300s jest = 1500s worst case). Buffer eroded as backend test count grew: 2026-05-07 ran 817s/83s spare, 2026-05-08 ran 843s/57s spare, 2026-05-11 tipped to TIMEOUT (killed at 900s, agent did not run, nightly went RED). Added `qa_warden: 1700` to `AGENT_TIMEOUT_OVERRIDES` (same pattern as `coverage_sentinel`); 200s of margin over the agent's worst-case internal budget. File: `scripts/overnight/orchestrator.py`. **Merged 2026-10-19, five months late** — the 109-day artifact backlog committed the same day quantifies the cost: only 43 of 109 dormant nights produced a `qa_warden` sentinel, so the agent failed to run on roughly 66 nights, and the one agent that would have reported a red suite was the one most likely to time out. Timeout re-validated against current runtimes before merge: the backend suite now takes ~865s (8,700 tests) against the 1200s internal pytest budget, so the 1700s orchestrator ceiling still holds with margin.
- [2026-05-07] ADR-018 shim sweep — `contract_fields.py` default fallback updated from `revenue_testing_engine.py` (dynamic-namespace shim) → `services/audit/revenue_testing/analysis.py`; 4 stale diagnostic labels in `test_accounting_policy_guard.py` updated to canonical path. No other shim-blind scripts found (lint_domain_relocation, lint_route_layer_purity, framework_metadata/adjustment_gating targets are all non-shims). PR #134.
- [2026-05-01] nightly audit artifacts — 2026-04-30 + 2026-05-01 batch (2 daily reports + 12 sentinel JSONs + 2 run_logs + `.baseline.json` updated to 2026-05-01 values: backend 8685 passed, frontend 2013 passed, coverage 93.33% — backend grew +88 tests since 2026-04-29 baseline, mostly Sprint 768 security fixtures). Also removed root-level `tmp_report.py` scratch file (`x=1`, accidentally checked in during prior session). Files: `reports/nightly/*`, `tmp_report.py`. **Rebased onto `main` 2026-10-21 (Sprint 785):** the `.baseline.json` half of this commit was dropped — main already carries the 2026-10-21 values (8,818 backend / 2,010 frontend, coverage 93.5%), which supersede the 2026-05-01 snapshot. The two daily briefs, twelve sentinel JSONs, two run_logs and the `tmp_report.py` removal all landed.
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
> **Heading corrected 2026-10-20.** This sprint was briefly titled "off-provider backup deferred", which contradicted its own scope item 1. The deferral was withdrawn the same day it was made (see the DECISION block above and `tasks/EXECUTIVE_BLOCKERS.md` → Resolved Decisions). The backup ships pre-launch.
> Sprints 762–788 archived to `tasks/archive/sprints-762-788-details.md`.
> **CORRECTION (2026-10-21, before any code was written).** The first version of this entry said
> the gap was app-wide and singled out **`hooks/createTestingHook.ts`** for having "zero
> engagement references", concluding that the nine testing tools behind it were equally broken.
> **That was wrong.** `createTestingHook` delegates to `useAuditUpload`, and
> `useAuditUpload.ts:102` has auto-injected `engagement_id` into the FormData since **Sprint
> 103** (`// Auto-inject engagement_id when linked to a workspace`), then calls
> `refreshToolRuns()` and `triggerLinkToast()` afterwards. The nine testing tools inherit all of
> that and work correctly. "No engagement references in the file" was evidence of delegation, not
> of a defect — the same mistake, in the same session, as the Sprint 787b guard that resolved
> delegation badly. I reported the overclaim on PR #182 rather than leave it standing.
>
> The scope is therefore **the six JSON-body hooks only**, which genuinely do not use
> `useAuditUpload` — they post via `apiPost` with their own fetch logic.
> Sprints 784–791 archived to `tasks/archive/sprints-784-791-details.md`.
> **FULL-SPECTRUM IMPROVEMENT REVIEW — 2026-10-22.** Full report:
> [`reports/full-spectrum-review-2026-10-22.md`](../reports/full-spectrum-review-2026-10-22.md).
> 22 findings (7 P1 / 8 P2 / 7 P3-or-product-gap), every one produced by **running** the code
> rather than reading it, against `c12a6dcb`. It deliberately targeted the gaps the DEC review
> named as uncovered the same day — above all the one the DEC stated plainly: *"no tool was
> exercised against a real trial balance end-to-end."*
>
> Sprints 803–811 below are its actionable output. Order follows the report's own sequencing:
> **what reaches a customer or an auditor relying on an output**, not what is most interesting.
>
> **Out of scope for these sprints, and why:**
> - **A-7 (2026 statutory figures)** and **A-8 (§179, §168(k), real property, ADS)** need a
>   practitioner to confirm the numbers and a roadmap call on scope. Sprint 793b still owns the
>   figures; **Sprint 811 takes the structural half** (year-keyed tables, refuse rather than
>   fall back), which needs no confirmation.
> - **T-1 (mypy baseline)** — parked deliberately by the 2026-10-20 worklist. Unchanged.
> - **T-5 (dependency drift)** — Sprint 786 owns it. Unchanged.
> - **T-2 (generator coverage floors)** and **D-6 (route loading/error states)** — real, but
>   they are test/UX volume rather than defects. Left in the backlog rather than padding a
>   correctness sprint with them.
> Sprints 803–811 archived to `tasks/archive/sprints-803-811-details.md`.
>
> **CODE HEALTH REVIEW — 2026-10-23.** Four parallel read-only passes (backend engines,
> memos/PDF/exports, routes/data layer, frontend) plus repo hygiene, against
> `dec-review-2026-10-22-remediation`. Asked for cleanup and efficiency; it also turned up
> **live defects**, which come first. Sprints 812–822 below are its output, ordered by what a
> paying customer hits, then by measured cost, then by lines removed.
>
> **Verified by direct re-check, not just reported:** 812 (19 routes enumerated on the live
> `main.app`), 813 item 1 (five `doc.build` calls without `onLaterPages`), 814 item 1 (no
> `UpgradeGate` in AP/JE pages), 818 (`PricingEstimator`/`PricingCard` imported nowhere),
> 817 item 6 (`background4.jpg` referenced nowhere). Performance figures in 815 were measured
> on synthetic data; benchmark scripts were kept in the session scratchpad only.
>
> **CEO decisions this review needs** (each blocks the named item, nothing else):
> 1. **Bulk upload — wire it or remove it** (blocks 817 item 4). ~2,000 frontend lines are
>    unmounted and the backend route is a stub, yet Enterprise is sold on it. **Interacts with
>    Sprint 790:** `routes/bulk_upload.py:154` is the *only* caller of `increment_upload_count`,
>    so removing the route without 790's recorder-based increment leaves quota counting nowhere.
> 2. **Bank-rec split-match bound** (blocks 815 item 2) — any bound changes which matches can be found.
> 3. **Round-amount cap ordering** (blocks 819 item 3) — JE/AP/Revenue cap-then-sort, Payroll
>    sort-then-cap; under the cap they flag different rows.
> 4. **`engagement_dashboard_memo.py` and `shared/intercompany_resolver.py`** — ship or delete (817 item 3).
> 5. **`reports/nightly/`** — 1,149 of 3,261 tracked files. Keep committing, or move to CI artifacts?

> **CARRIED FORWARD — 2026-10-23.** Everything known and unaddressed after the two
> 2026-10-22 reviews landed (PRs #198 + #199, 28 findings). Recorded here so the next
> session starts from a complete list rather than re-deriving it. Nothing below is in
> flight; each line is either a named sprint, a CEO decision, or an unexamined surface.
>
> **Needs a practitioner or a roadmap call — not engineering:**
> - **Sprint 793b — 2026 statutory figures.** Live consequence: Sprint 811 made the W-2
>   tool **refuse** a 2026 engagement unless the caller supplies the figures per request.
>   That is deployed. It stays that way until 793b lands confirmed numbers.
>   `test_no_table_claims_to_be_2026_until_sprint_793b` guards against adding an
>   unconfirmed row in the meantime.
> - **A-8 — depreciation coverage.** Absent today: 150% DB election for 3/5/7/10-year
>   property, GDS straight-line election, ADS, real property (27.5-year residential,
>   39-year nonresidential), mid-quarter for anything but 5-year, **§179**, and
>   **§168(k) bonus** (no reference to either anywhere in the backend). Bonus and §179
>   appear on most US fixed-asset schedules; real property covers every rental and
>   commercial client. Needs figures *and* a scope decision.
>
> **Deliberately parked, with the owner named:**
> - **T-1 — mypy baseline of 1,011 errors.** Parked by the 2026-10-20 worklist. The
>   `Decimal/float boundary` entry in that baseline is the concerning one, given A-1
>   through A-6 were all composition defects. Burn down per-module, starting with the
>   engines that compute money.
> - **T-5 — dependency drift.** Sprint 786 owns it. `argon2-cffi-bindings` 25.1 → 26.1
>   is the priority (it hashes the export-share passcodes).
> - **T-2 — coverage floors for the output layer.** Backend is 93.57% overall but the
>   misses concentrate in what the customer receives: `excel_generator.py` 45.7%,
>   `leadsheet_generator.py` 11.3%, `workbook_inspector.py` 18.6%,
>   `population_profile_memo.py` 39.7%, `pdf/sections/diagnostic.py` 64.9%. Finding A-5
>   was a defect in exactly this layer that a test would have caught.
> - **D-6 — re-measured 2026-10-23, much smaller than recorded.** Counting boundaries the App
>   Router *inherits* from parent segments: all 62 pages have an error boundary (root `error.tsx` +
>   `global-error.tsx`), and all 18 tool routes have a loading skeleton via `tools/loading.tsx`.
>   The 23 without one are marketing, auth, internal admin, `dashboard` and `shared/[token]`;
>   only the last two plausibly earn one. Original note follows.
> - **D-6 — route-level loading and error states.** 62 pages, 20 `loading.tsx`, 9
>   `error.tsx`, 1 `not-found.tsx`. 42 routes have no streaming skeleton. Prioritise the
>   18 tool routes, where a long upload-and-analyse cycle is where a skeleton earns its
>   place.
>
> **Now unblocked by work that just landed — worth doing early:**
> - **DONE 2026-10-23 (Sprint 828):** every `text-oatmeal-700` migrated by surface —
>   `obsidian-500` (5.63:1) on the light badge/page surfaces, `oatmeal-600` (5.33:1) on dark
>   marketing routes, `oatmeal-500` for the error digest on `global-error`'s #303030 panel — and
>   the lint exemption deleted, so the gate now enforces it. The text below is the original note.
> - **48 × `text-oatmeal-700` fail WCAG AA on both page surfaces** (4.38:1 dark /
>   3.89:1 light). No oatmeal shade reaches AA on the light page — oatmeal *is* the light
>   palette — so each usage needs to know its surface. That was blocked on the route→theme
>   map, and **Sprint 809 built it** (`frontend/src/lib/theme-routes.ts`, asserted against
>   the filesystem). The blocker is gone; `scripts/lint_design_tokens.py` prints this
>   exemption on every run and says in terms that it is **not permanent**.
> - **CHECKED 2026-10-23 — no change needed:** there are no `text-clay-500` usages left, and all
>   nine `hover:text-sage-600` usages render on routes the theme map resolves to light (settings,
>   workspace, portfolio, and `tools/layout.tsx`), where it passes. Original note follows.
> - **`clay-500` on dark surfaces** (3.69:1) and `hover:text-sage-600` (2.85:1 on dark)
>   are the same class and the same unblocking. The contrast gate deliberately does not
>   flag either, because both pass on light and it had no theme map to decide with.
>
> **Surfaces neither 2026-10-22 review examined** (from the full-spectrum report's own
> "what this review did not cover", with status updated):
> 1. **Auth, CSRF, JWT, the 61 injection tests, rate limiting, the passcode throttle** —
>    **the largest untouched surface across both reviews.** The DEC rated the area
>    "Moderate" with these same items listed as uncovered. Nothing has looked at it.
> 2. **Materiality cascade and the ISA 315 Appendix 1 RMM matrix** — not examined.
> 3. **Benford's law application.** The thresholds were verified against Nigrini (2012)
>    and match, and the three expected distributions are computed rather than tabulated —
>    but the *application* of those thresholds was never exercised.
> 4. **Real browser rendering.** Contrast, theming and overflow were computed from source
>    and the compiled stylesheet, never observed. D-1's theme flash is now fixed and
>    verified server-side in production (`/tools/trial-balance` and `/settings` serve
>    `data-theme="light"`), so this is narrower than it was — but the 68 tables and the
>    overflow wrappers have still never been looked at in a viewport.
> 5. **Per-route bundle sizes.** Next 16 emits no size table. Total client JS is 2.9 MB
>    across 110 chunks with a 347 KB largest chunk; First Load JS per route is unknown.
> 6. **Production's schema** — the DEC's §6 item 1, and **substantially answered since**:
>    Sprint 797's `alembic upgrade head` now gates startup on every boot and ran against
>    production Postgres successfully on 2026-10-23 (deploy `dep-dbdphrrm8hqs73cprs3g`,
>    live in 44s), so the chain and production agree. A confirming read is now cheap
>    rather than load-bearing.
> 7. **The other 14 tools' runtime behaviour** — now **Sprint 823** below.
>
> **Operational, small:** three stray untracked `nul` files (dated 2026-02-13) at the repo
> root, `backend/` and `frontend/` crash `mypy`'s path resolver on Windows, so no local
> whole-project mypy run is possible. Harmless in CI (Linux). Delete when convenient.

### Sprint 823: Seven of the eighteen tools have never been exercised against realistic input
**Status:** PARTIAL — discovery done 2026-10-23 (**58 findings, 21 P1**, register in
[`reports/sprint-823-discovery-2026-10-23.md`](../reports/sprint-823-discovery-2026-10-23.md));
remediation split into Sprints 824–827. Generator registration (items 3 and 5) not yet done.
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

> `fixed_asset_testing` · `sod_checker` · `intercompany_elimination` ·
> `w2_reconciliation` · `form_1099` · `book_to_tax` · `cash_flow_projector`

**Six of those seven are exactly the tools Sprint 689 added** when the catalog went 12 → 18.
The synthetic framework predates that expansion and was never extended to it. So the tools
the framework has never looked at are the *newest* ones — the least-exercised code in the
product, reached through a UI that presents them identically to the mature eleven.

- [x] Build a realistic fixture per uncovered tool, from each engine's own input dataclass
      (the pattern used for `W2ReconciliationConfig` in Sprint 811)
- [x] Drive each of the seven engines end-to-end and record the output, not just the absence
      of an exception — A-5 returned `0.0` happily for the life of the product
- [ ] Register each generator in `tests/anomaly_framework/registry.py` and add its row to
      `COVERAGE_MAP.md`, which `test_coverage_map.py` already enforces
- [x] File each abnormal output as a finding with its measurement, in the A-1…A-6 style
- [ ] Then the remaining eleven, which have generators but whose *application* was never
      exercised end-to-end either
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



### Sprint 824: Statistical sampling evaluation and the shared amount parser
**Status:** IN REVIEW — 2026-10-23. Sprint 823 findings P-1, P-2, S1, S2, S4, S5, S7, S8, S9.
**Priority:** **P1** — S1 changed an audit conclusion.

- [x] **S1 — top stratum.** An item at or above the sampling interval is examined with certainty,
      so its actual misstatement enters the projection with no tainting projection and no
      allowance. Reproduced and fixed: the review case now reports UEL **$260,000 "fail"**
      (was $234,500 "pass"). Five existing fixtures placed their errors on items *exactly equal*
      to the interval — top-stratum items under the corrected rule — and were rescaled to
      sub-interval items with identical taintings, so every figure they assert is unchanged.
- [x] **S2/S7 — sample value.** `_parse_evaluation_errors` now totals every evaluated item; MUS
      reports it as sample value and the random ratio estimate uses it as its denominator.
- [x] **S4/S5 — unreadable audited amounts** are unassessed (counted in
      `skipped_missing_audited`), not a 100% misstatement or an infinite one.
- [x] **S8** — MUS echoes the expected misstatement it was given.
- [x] **S9** — both sampling routes reject non-finite form values with a 422.
- [x] **P-1/P-2 — shared parser.** `safe_decimal` and `safe_float` test for parentheses after
      dropping `$` and spaces, and return the default for any non-finite result.
- Tests: 6 engine tests (all fail on the old code), 4 route tests, `test_safe_decimal.py`.

**Not done here — methodology decisions (Sprint 825):** S3 (zero-error random evaluation always
passes) and S6 (understatements evaluated as overstatements) need a chosen method — e.g. a
classical-variables evaluation with a sample standard deviation, and a separate understatement
bound — not a patch.

**Commit SHA:** TBD.

---

### Sprint 825: Sampling methodology decisions (S3, S6)
**Status:** PENDING — needs a practitioner's choice of method. See the Sprint 823 report.

**Commit SHA:** TBD.

---

### Sprint 826: Tax tools — 1099 rules, W-2 coverage, book-to-tax loss years
**Status:** PENDING. Sprint 823 findings F0–F8, W1–W10, B1–B6.
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
- [ ] **W1/W2 — design question first.** Both need new statutory fields (SIMPLE catch-up 50+ and
      60–63; HSA age-55 catch-up). Adding them to `StatutoryLimits` means a 2026 request that
      today fully overrides the 11 existing fields would be refused (the new fields would be
      "missing", and Sprint 811 deliberately refuses rather than falls back). Decide with 793b:
      optional fields that disable only their own check when absent, or a breaking change to
      the override contract.
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
- [ ] F5, F9, W4 (W-3 vs 941), W8, W9, B1, B2, B5, B6.

**Commit SHA:** TBD.

---

### Sprint 827: Fixed assets, intercompany, SoD, cash flow projector
**Status:** IN PROGRESS. Sprint 823 findings A1–A8, I1–I5, D1–D2, C1–C6, P-3.
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
      tested rather than silently skipped. (`01-Jan-2019` is still outside the shared parser.)
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
      should make a user high-risk is a scoring decision, not a bug fix.
- [ ] Open: A4, A5, A8 (FA conventions/units), D2 (tiering; degenerate custom rules),
      C2–C6 (cash flow scenario deferral, footing, edge cases), I4's investment/payable pairing,
      P-3 (non-USD / EU number formats — needs a locale decision).

**Commit SHA:** TBD.

---

### Sprint 829: Discovery round 2 — the eleven tools Sprint 823 did not cover
**Status:** IN PROGRESS. A second round of discovery agents ran the original tools (TB, JE, AP,
payroll, revenue, AR, inventory, bank rec, three-way match) against realistic synthetic input.
**Priority:** **P1** — several findings produce wrong output on correct input.

- [x] **AR-1** — aging uses the shared `parse_date`, so Excel date cells are aged (a whole
      .xlsx sub-ledger was landing in Current).
- [x] **AR-2** — a sub-ledger with only an invoice date is aged from it, with a note.
- [x] **AR-3** — non-trade receivables (notes, loans, officers, related party, tax, …) and
      non-earned revenue (deferred, unearned, cost of) are no longer classified as trade AR/revenue.
- [x] **IN-5** — `selling_price_column` is detected and overridable, so IN-T10 (LCM/NRV) can run.
- [x] **T1** — currency-formatted debit/credit cells ("$1,234.00", "(500)") in a CSV/Excel TB are
      parsed instead of coerced to zero.
- [x] **T6** — DuPont and common-size values serialize as JSON numbers, not strings.
- [x] **JE-1** — reciprocal entries no longer pair an entry's own debit and credit lines
      (61% of a clean GL was flagged HIGH).
- [x] **JE-2** — just-below-threshold counts rows, not flags (flag rate reached 2.0), and its
      split pass sums debits and credits separately.
- [x] **JE-3** — unbalanced entries floor the composite: any → Moderate, any over $1,000 →
      Elevated. A GL with a $250K out-of-balance entry was rated LOW.
- [x] **JE-4** — after-hours treats a file whose every timestamp is exactly midnight as
      date-only (100% of an .xlsx GL was flagged as 00:00 postings).
- [x] **JE-5** — numbering gaps read the trailing sequence per series, so year-prefixed IDs
      ("JE-2025-0001") are tested.
- [ ] Open P1s: payroll xlsx pay dates; payroll PR-T9 on a single-period register; AP-T14 PO
      column unmapped; JE date formats skipped silently; revenue RT-04 sign convention; TB T2–T5;
      bank rec B1/B3; three-way match W1/W2.

**Commit SHA:** TBD.

---

### Sprint 812: Nineteen rate-limited routes 500 on every call
**Status:** IN REVIEW — code complete 2026-10-23; post-deploy verification pending.
**Priority:** **P0** — every Professional/Enterprise org feature is down in production.
**Source:** Code health review 2026-10-23, routes pass. Re-verified on the live app object.

The handlers declare `request: Any = None` under `@limiter.limit`. FastAPI therefore treats
`request` as a **query parameter**, slowapi receives `None`, and raises
`parameter 'request' must be an instance of starlette.requests.Request` → 500. Reproduced on
`GET /admin/overview`. Introduced by `8372073a` (2026-03-21 mypy cleanup). Tests never saw it
because `tests/conftest.py:166` sets `limiter.enabled = False`.

Affected (19): `routes/organization.py:86,134,156,233,262,364,395`,
`routes/admin_dashboard.py:81,140,179,215`, `routes/branding.py:83,103,161`,
`routes/bulk_upload.py:47`, `routes/export_sharing.py:312,458,495,522`.

**Scope:**
- [x] Change each to `request: Request`. Enumerated on the live app object first: exactly 19
      `APIRoute`s carried `request` as a query param, matching the list above one-for-one.
- [x] Guard test `tests/test_rate_limited_request_param.py`: every route in slowapi's
      decorated-endpoint registry must have `dependant.request_param_name` set, and no route may
      expose `request` as a query/body param. Includes a vacuity check (≥150 limited routes
      resolved; 201 today) so a drift in slowapi internals cannot turn it into a scan of nothing.
- [x] Limiter **enabled** for the whole of the five affected routers' existing suites via a new
      opt-in `limiter_enabled` conftest fixture (`pytestmark` in each module) — stronger than one
      test per router. **Proved:** with the route fix reverted, 43 of those 71 tests fail; with it, 71/71.
- [x] OpenAPI snapshot regenerated — the diff is exactly the 19 bogus `?request=` params (−202 lines).
      Note the drift check did **not** flag their removal (it reports only metadata drift), so the
      snapshot gate would never have caught this either.
- [ ] After deploy: confirm live SHA = `main`, then hit `/organization` and `/branding/` on prod.

**Side effect worth knowing:** `export_sharing.py:511` threads `request.client.host` into the
Sprint 698 per-IP passcode throttle. With `request=None` that branch could never run — though
the route 500'd before reaching it anyway, so the throttle was not bypassed, merely unreachable.

**Commit SHA:** TBD.

---

### Sprint 813: Memo PDFs — missing footers, ignored branding, and the hand-built skeleton behind both
**Status:** PARTIAL — the customer-facing defects (items 1, 2, 6, 8, 10 + two found on the way) are
fixed and pinned by an output-level test; the structural cleanups (3, 4, 5, 7, 9) remain.
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
3. [ ] Extract `render_memo(title, ref_prefix, body_builder, *, running_header=None, margins=...)`
   in `shared/memo_base.py`; route the 14 hand-built memos **and** `generate_testing_memo`
   through it. Keep each memo's current margins as parameters (they drift 0.75in/1.0in today)
   so output does not move. ~500–700 lines; closes 1 and 2 permanently.
4. [ ] `ledger_table_style()` is copied inline 47× — add `font_size`/`extra` params, replace copies.
5. [ ] `source_line(...)` helper for the 6-line Source block repeated in 10 memos; keep
   "Source File" vs "Source" as a parameter (no wording change).
6. [x] `tests/test_memo_boundary_phrasing.py:101` matches only `*_memo_generator.py`, so
   accrual/expense/flux/population-profile `*_memo.py` are never scanned. Widen the glob.
7. [ ] `tests/test_citation_consistency.py` never scans backend PDF producers. Add them; register
   the unregistered codes cited in customer PDFs (AS 1305, AS 1105, AS 2810, AU-C 320/330/520/570,
   IFRS 9, ASC 275, ASC 450, 14 ASC codes in the FASB YAML). `anomaly_summary_generator.py:109-115`
   hard-codes its list — read the registry. No wording changes.
8. [x] Engagement ZIP (`engagements_exports.py` ~`:85-110`) ships the anomaly summary **unbranded**
   while the standalone route brands it; also passes neither engagement nor client, so access
   check + client lookup run twice.
9. [ ] Small: cache `create_memo_styles()`; module-constant fonts/fills in `excel_generator.py:327,401`;
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

**Commit SHA:** TBD.

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

**Commit SHA:** TBD.

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
   **Blocked on CEO decision 2** (cap the pool / date window when tolerance is 0 / meet-in-the-middle).
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

**Commit SHA:** TBD.

---

### Sprint 816: Engine correctness follow-ups surfaced by the performance pass
**Status:** COMPLETE 2026-10-23 — all four verified by measurement before fixing; three were real
as described, one (item 3) was worse than described, and item 4 turned out to be an **accuracy**
defect, not only a reproducibility one.
**Priority:** P2 → item 4 is effectively **P1** (see below).
**Source:** Code health review 2026-10-23, engines pass.

- [x] **JE reciprocal entries counted flags, not rows.** Measured: 3 debits × 3 credits of one
      amount → `entries_flagged` **18 of 6 entries, `flag_rate` 3.0 (300%)** in the customer's
      output. Now counts distinct rows; the per-pair flags stay in `flagged_entries`. Regression
      test in `test_je_tier3.py`. `test_tool_anomaly_detection.py` now asserts
      `entries_flagged ≤ total_entries` and `0 ≤ flag_rate ≤ 1` for **every** test result of every
      generator run, not just the targeted one — no generator builds a multi-partner case, so
      that invariant would not have caught this one, but it now covers the whole population.
- [x] **JE `apply_column_overrides` never set `has_dual_dates`.** Confirmed. Impact is limited to
      the reported column detection (parsing reads the explicit columns), but it was wrong. Fixed
      the AP way; test added.
- [x] **Currency NaN — worse than described.** An empty amount cell (float NaN) became
      `Decimal("NaN")`; when that row was *also* unconvertible (missing currency code or missing
      rate) the severity pass raised **`InvalidOperation`** — an `ArithmeticError` the TB
      post-processor's fallback did not catch. And `Decimal(str(x))` turned `$1,234.56` and
      `(500.00)` into a **silent 0**. Now parsed through `safe_decimal` (NaN/inf → 0, currency and
      parenthetical formats parsed); the post-processor fallback also catches `ArithmeticError`.
      3 tests, all failing on the old code.
- [x] **FA/Inventory reference date — an accuracy defect.** No caller ever passed
      `reference_date`, so FA-T11 divided accumulated depreciation (stated **as of period end**)
      by years elapsed **to today**. Measured: a register depreciated exactly on schedule to
      2025-12-31, tested on 2026-10-23, had **6 of 6 assets flagged**. Audit fieldwork happens
      after year-end, so on real engagements this test was a false-positive generator. IN-06
      (slow-moving) had the same dependency. Fix: `shared/reference_date.resolve_reference_date`
      — explicit `as_of_date` form field > linked engagement's `period_end` > processing date,
      the same cascade shape as materiality — threaded into both configs, and the date used plus
      its source is now stated in each test's description (so it reaches the UI and the memo with
      no schema change). Engagement-linked uploads get period end automatically, because
      `useAuditUpload` already injects `engagement_id`. Unparseable `as_of_date` → 400, never a
      silent fallback. `_asset_age_years` was never called outside its own tests — deleted with them.

**Follow-up (frontend, not done):** the FA and inventory pages do not yet offer an as-of date
input, so an upload **not** linked to an engagement still measures to the processing date —
now disclosed in the test description rather than silent.

**Commit SHA:** TBD.

---

### Sprint 817: Dead-code sweep
**Status:** PARTIAL — items 1, 2, 6 done and most of 5; items 3–4 await CEO decisions; the
`package.json` half of item 6 waits for PR #197 (it rewrites the same lockfile).
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
5. [ ] **Unused helpers/constants:** entitlement `check_client_limit`, `check_tool_access`,
   `check_workspace_access`, `check_activity_log_access` (routes re-implement them inline — keep
   one implementation each); `auth.get_current_user` (unreferenced and skips the password-change
   check — unsafe to adopt); `ratio_engine.calculate_dupont_decomposition`;
   `compute_bank_rec_risk_score` alias; `PAYROLL_SUSPICIOUS_KEYWORDS`; `SOURCE_LEASE`,
   `SOURCE_GOING_CONCERN`, `PREPAID_KEYWORDS`, `STANDARD_ADJUSTMENTS_BY_CODE`,
   `CURRENT_RATIO_THRESHOLD`, `LOW_CONFIDENCE_THRESHOLD`; `export/transport.py:41` no-op and
   unused `"excel"` branch at `:46`; the 10 unused `DEFAULT_*` aliases in
   `w2_reconciliation_engine.py:160-172` and their stale comment (**fix in the current branch before merge**).
6. [ ] **Assets/deps:** delete `frontend/public/backgrounds/background4.jpg` (22 MB, unreferenced);
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

**Commit SHA:** TBD.

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

**Item 3 — not done, and it needs a decision rather than a refactor.** Consolidating the two
"we store / we never store" lists means choosing one wording for Zero-Storage compliance copy.
More importantly, **both lists may be inaccurate**: they promise Paciolus never stores
"individual account balances" or "anomaly details tied to specific accounts or amounts", while
the 2026-10-19 DECISION block above records that the database persists
`uncorrected_misstatements.accounts_affected_json` (account names with DR/CR amounts),
`analytical_expectations` (expected and actual values) and `diagnostic_summaries` (aggregate
totals). That is a question for the CEO and counsel before anyone edits the copy.

**Commit SHA:** TBD.

---

### Sprint 819: Backend deduplication
**Status:** PENDING.
**Priority:** P2.
**Source:** Code health review 2026-10-23, engines + routes + exports passes.

1. [ ] Generic result base classes in `shared/` for the per-tool `FlaggedEntry` / `TestResult` /
   `DataQuality` / `CompositeScore` (~650 lines across 7 tools; e.g. `je_testing/analysis.py:546-665`).
   **JSON output must not change**: Payroll stores severity/tier as strings and rounds
   `completeness_score` to 2 dp; AR adds `skipped`/`skip_reason`; Payroll `top_findings` is list-of-dicts.
   Snapshot-test every tool's response before and after.
2. [ ] `.empty(...)` / `.from_flags(...)` constructors replacing 76 zero-result blocks (~800 lines)
   and ~110 hand-computed `flag_rate`s. AR's `_skipped_result` (`ar_aging/analysis.py:1801`) is the model.
3. [ ] Round-amount test copied 4× (JE `:1087`, AP `:904`, Revenue `:922`, Payroll `:1163`) — adopt
   one Decimal-safe helper. **Ordering blocked on CEO decision 3.**
4. [ ] Optional `formats=` on `parse_date`; AR (`:862,873`), FA (`:1429`), currency (`:567`) pass
   their **current** lists — do not widen what they accept.
5. [ ] Default `apply_column_overrides` driven by a class-level column list (JE `:2857`, AP `:1996`
   hand-written); keep Payroll's suffix-less keys (API contract). Finish `AuditEngineBase`
   adoption for FA, Revenue, AR (feeds the Refactor Intake item).
6. [x] *(`_to_decimal` half done 2026-10-23: nine byte-identical copies → `shared/request_decimal.py`;
   the guard that scanned each copy for the finiteness fix now forbids new copies and checks the
   shared helper. `run_json_tool` not done.)* `_to_decimal` copied verbatim into 9 route files → one `shared/` helper; a `run_json_tool(...)`
   wrapper for the 6 promoted-tool routes' enforce → quota → record sequence.
7. [ ] ~20 export endpoints hand-roll `StreamingResponse`/`Content-Disposition` (list in the review:
   `engagements_exports.py`, `loan_amortization.py`, `bank_reconciliation.py:193`,
   `multi_period.py:281`, `depreciation.py:243`, `lease_accounting.py:216`, …) → use
   `shared/export_helpers`. Decide `Cache-Control: no-store` for all financial exports (only
   `export_sharing.py:222` sets it). In-memory PDFs: plain `Response`, not 8 KB chunking.
8. [ ] `export/pipeline.py:47-262` — 11 near-identical functions → one `_run_export(...)` (~120 lines).
9. [ ] **Env reads through `config.py` only.** Latent bug: `email_service.py:48-50` reads
   `SENDGRID_API_KEY` via `os.getenv` while `config.py:647` validates via `_resolve_secret` —
   a Docker/cloud-secret key passes the startup check and email silently does not send. Also
   `entitlement_checks.py:69,388`, `health.py:269`, `logging_config.py:113,154`,
   `memory_budget.py:40`, `storage_client.py:26`, `export_share_storage.py:47-50`, `retention_cleanup.py:27`.
10. [ ] Split long functions: `three_way_match_engine.py:1210` (268 lines, 64 branches),
   `currency_engine.py:821` (254 lines; lookup copied 3×, per-cell `df.at` loop under a
   "Vectorized" comment), `payroll_testing/analysis.py:1659` (145 lines).

**Commit SHA:** TBD.

---

### Sprint 820: Frontend consolidation and bundle weight
**Status:** PENDING.
**Priority:** P2.
**Source:** Code health review 2026-10-23, frontend pass.

1. [ ] `TestingToolPage` shell for the six single-file testing pages (ap, payroll, revenue,
   fixed-assets, inventory, journal-entry — 70–80% identical, ~1,650 lines). Use the existing
   `components/shared/FileDropZone`; build `UpgradeGate` in so 814 item 1 cannot recur. ~1,100 lines out.
   Collapse the ~20 pass-through `*ScoreCard`/`*DataQualityBadge` wrappers.
2. [ ] `createJsonAnalysisHook({...})` for `useSOD`, `useForm1099`, `useW2Reconciliation`,
   `useBookToTax`, `useIntercompanyElimination`, `useCashFlowProjector` (~530 → ~90 lines).
3. [ ] `terms` and `privacy` pages: drop `'use client'` (no hooks; ~2,000 lines of legal text in
   the JS bundle), wrap the 4 animated sections in `components/ui/Reveal`. Same for `about`,
   `approach`, and `app/(marketing)/layout.tsx`. Compatible with the `headers()`-dynamic root.
4. [ ] `trust/page.tsx`: static data → `content/trust.ts`, 4 interactive blocks → `components/trust/*`, page becomes a server component.
5. [ ] `ToastContext.tsx:73` — split stable actions from state so 8 consumers stop re-rendering on
   every toast. Memoize `CanvasAccent`/`AuthSession`/`UserProfile`/`Verification`/`Mapping` values
   only if profiling shows cost.
6. [ ] `BaseColumnDetection` type; `ARDataQuality` extends `BaseDataQuality`.
7. [ ] Measure first: bundle analyzer on framer-motion (139 importers, no `LazyMotion`); 5 local
   `fadeUp` copies → `lib/motion.ts:71`.

**Commit SHA:** TBD.

---

### Sprint 821: Database and event-loop efficiency
**Status:** PENDING.
**Priority:** P3 — low traffic today; cheap now, expensive at scale.
**Source:** Code health review 2026-10-23, routes pass.

- [x] *(Done 2026-10-23: 41 found by AST scan, 31 touching the DB, all converted; AST guard added.
      One test had relied on the blocking — see its docstring. The three offloading cases below remain.)*
      ~30 `async def` handlers with no `await` that make sync DB calls (organization ×10,
      admin_dashboard ×4, branding ×3, diagnostics ×3, prior_period ×3, …) → plain `def`.
      Offload the blocking part of `branding.py:102` (S3 upload), `billing.py:347` (Stripe
      retrieve + DB), `export_sharing.py` passcode verify (Argon2id).
- [ ] Subscription row queried 3× per testing upload (`enforce_tool_access` →
      `get_effective_entitlements`, then `check_upload_limit` twice incl. `entitlement_checks.py:111`) — load once per request.
- [ ] `billing/internal_metrics.py:601-663` per-day snapshot loop with per-user queries; cap the
      range in `routes/internal_metrics.py:129`; batch dunning lookups (`:365,384,402,538`,
      `dunning_engine.py:162,168`).
- [ ] One Alembic migration dropping the 26 `primary_key=True, index=True` duplicate indexes and
      the single-column indexes covered by composites (`ToolActivity.user_id`, `TeamActivityLog.organization_id`).
      Mind Sprint 741c/797 chain-vs-ORM guards.
- [ ] Convert `RequestId`, `SecurityHeaders`, `Impersonation` middleware from `BaseHTTPMiddleware`
      to pure ASGI — **benchmark first**; impact unmeasured.

**Commit SHA:** TBD.

---

### Sprint 822: CI and repository weight
**Status:** PENDING.
**Priority:** P3.
**Source:** Code health review 2026-10-23, repo pass.

- [ ] `reports/nightly/` is 1,149 of 3,261 tracked files — **CEO decision 5**.
- [ ] `ci.yml` runs pip-audit twice (`pip-audit-blocking` `:660`, `pip-audit-advisory` `:690`), each
      installing the full `requirements.txt`: one job, two invocations of `scripts/pip_audit_gate.sh`.
- [ ] Root clutter: `PHASE_III_QUICK_REFERENCE.txt`, `README_PHASE_III_DELIVERY.txt`,
      `SECURITY_CHANGES.md`, `SECURITY_HARDENING_SUMMARY.md`, `COHESION_REMEDIATION.md`,
      `EXECUTIVE_SUMMARY_NONTECH.md`, root `MEMORY.md` — check each for live references, then move to
      `docs/` or `tasks/archive/`.

**Commit SHA:** TBD.

---
> **DIGITAL EXCELLENCE COUNCIL REVIEW — 2026-10-22.** Full report:
> [`reports/council-audit-2026-10-22.md`](../reports/council-audit-2026-10-22.md). 14 findings
> (4 P1 / 4 P2 / 4 P3 / 2 Info), all CONFIRMED by measurement or injection; 27 measurements
> recorded. Sprints 795–802 below are its actionable output, ranked by what breaks for a paying
> customer or an auditor relying on an output — **not** by how interesting the defect is.
>
> **Before any of them:** run the one query in §6 item 1 of the report. It decides whether
> Sprint 797 is a rebuild hazard or a live production incident, and it costs a minute.
>
> Three measurements argued *against* work and are recorded as results rather than sprints:
> widening the Float-column guard scope (2 of 17 columns outside it, both non-monetary),
> rewriting `hard_delete` to AST (0 current instances of its blind spot), and fixing the 50
> chain-vs-ORM nullability drifts (all benign; a 50-row failure wall is how a gate gets disabled).
> `THIS IS NOT A VULNERABILITY FINDING.`
> `The audit could not be completed after 3 attempts...`
> **PR #185 review — the guard had the defect it was written to prevent.** The first draft
> enumerated `services/audit/*/analysis.py`, which excluded
> `services/audit/flux/recon.py` — the **ADR-018 pilot relocation**, and the one module that
> predates the `analysis.py` convention. Deleting its shim `recon_engine.py` left the test
> green while `lint_domain_relocation.py` lost the ability to enumerate that engine: precisely
> the regression the test exists to catch, missed by the test's own filename filter.
>
> That is this sprint's thesis reproduced inside the sprint's own deliverable — a scan whose
> scope silently excludes the thing it was written for. Enumeration is now by **directory**:
> every non-`__init__` module under a per-tool subdirectory, with the shim name taken from the
> module stem (`recon.py` → `recon_engine.py`) except for the conventional `analysis.py`, which
> takes its directory's (`ap_testing/analysis.py` → `ap_testing_engine.py`). The rule resolves
> correctly for all 11 modules. Top-level `services/audit/*.py` — `contracts.py`,
> `file_tool_scaffold.py`, `flux_service.py` — are shared infrastructure, not per-tool engines,
> and stay excluded.
>
> A second test pins the pilot **by name**, so a future narrowing of the glob cannot drop it
> silently again. Re-proved: removing `recon_engine.py` now fails with
> `scanning nothing: ['services/audit/flux/recon.py (expected recon_engine.py)']`.
> **Corrected after the PR #191 review** — the first measurement said twenty, and `subscription_tier`
> was a phantom. See "A fourth parser defect, found in review" below.
> **The table below understates the problem by a factor of six.** It was assembled by hand from
> two PR reviews. Sprint 741d built the comparison mechanically and found **20 drifting enum
> types, not 3** — see that sprint for the measured list. The rows here are correct; they are
> simply the ones that happened to be noticed. Kept as written because the reasoning that
> follows them is still the right reasoning, and because the gap between a hand-read sample and
> a measured population is the point.
> **Re-measured 2026-10-22, against the reconciled venv.** The figures above are two days stale and
> one is wrong by nine minor versions: `fastapi` is at **0.159.1**, not 0.150.0. Measured state is
> **60 outdated**, of which only **10 are exact-pinned** and therefore actionable — the rest are
> floors that self-heal (1) or transitive (49). The actionable set:
>
> | Package | Pinned | Latest | Kind |
> |---------|--------|--------|------|
> | `APScheduler` | 3.11.2 | 3.11.3 | patch |
> | `pandas` | 3.0.2 | 3.0.6 | patch |
> | `psycopg2-binary` | 2.9.12 | 2.9.13 | patch |
> | `python-dotenv` | 1.2.2 | 1.2.4 | patch |
> | `slowapi` | 0.1.9 | 0.1.10 | patch |
> | `alembic` | 1.18.4 | 1.20.1 | minor |
> | `fastapi` | 0.136.1 | 0.159.1 | minor (large surface) |
> | `SQLAlchemy` | 2.0.49 | 2.1.6 | minor (large surface) |
> | `reportlab` | 4.4.10 | 5.1.0 | **MAJOR** |
> | `stripe` | 15.1.0 | 16.0.0 | **MAJOR** |
>
> `reportlab` 5 was not on the original list at all and is the highest-risk item here: it renders
> all 18 memo PDFs and 3 report PDFs.
> `rate-limiter dependency notice: slowapi is unmaintained (last release Oct 2022)`
> Sprints 741–802 archived to `tasks/archive/sprints-741-802-details.md`.

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

### Sprint 790: The monthly upload allowance is not enforced on any paid tier
**Status:** PENDING.
**Priority:** **P1** — revenue-relevant and advertised. Every paid tier's headline quota is
unenforced.
**Source:** PR #182 review finding, verified 2026-10-21. It falsified a claim in Sprint 789.

`check_upload_limit` **reads** `Subscription.uploads_used_current_period` and raises 403 when it
is at the cap. `increment_upload_count` is the only thing that writes it, and its sole caller in
the repository is `routes/bulk_upload.py:154`.

So a Solo, Professional or Enterprise subscriber's counter never moves on normal tool use, and
the advertised allowances — **100/mo (Solo), 500/mo (Professional)**, stated on the pricing page,
in the Terms of Service tier table and in `UpgradeModal` — are not enforced at all. The gate
exists on roughly fifty upload endpoints and is inert on every one of them for paying users.

**Free tier is the exception, and the asymmetry is the giveaway.** With no `Subscription` row the
check falls back to counting `ActivityLog` rows for the current month, which genuinely grows. So
the 10-upload free cap works while the paid caps do not — the tier that generates no revenue is
the only one being metered.

**Two consequences worth stating:**
- This is why Sprint 741a concluded its `reset_upload_quotas` fix had "no realized impact beyond
  there being no paying subscribers yet." The deeper reason is that the counter it resets is
  almost never incremented, so a subscriber would never have hit the cap for the reset to matter.
- Enforcement has never been exercised end to end for a paid tier, so turning it on is a
  behaviour change for existing accounts, not just a bug fix.

**Scope:**
1. Decide the metering unit first, and write it down. "Upload" currently means different things:
   one file, one analysis run, or one bulk-upload member file (the only path that counts today).
   A tool accepting two files in one request — AR aging TB + sub-ledger, three-way match — must
   not silently cost two.
2. Increment on **success**, not on request. A 400 from malformed input should not consume
   allowance. That argues for the same position as the tool-run recorder, which already runs
   there.
3. Preferred shape: fold the increment into `maybe_record_tool_run`'s success path rather than
   adding a call to fifty routes. The recorder already knows the user, the tool and whether the
   run succeeded, already owns a commit after Sprint 787b, and is already called from every
   metered surface. Verify that mapping covers every endpoint that calls `check_upload_limit`
   before relying on it — a route that checks the limit but never records a run would stay
   unmetered and the asymmetry would be invisible again.
4. A test asserting check-and-increment are symmetric: every endpoint depending on
   `check_upload_limit` must reach an increment on its success path. Mechanical, and it is the
   guard whose absence let this sit.

**CEO decision needed before step 2 ships:** existing accounts have arbitrary counter values.
Enforcing from today risks locking out an account whose counter was left high by bulk upload.
Options: reset all counters at deploy; enforce from the next billing period; or enforce
immediately and handle exceptions manually. No paying subscribers yet, so this is cheap now and
expensive later.

**Commit SHA:** TBD.

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
**786b step 2 COMPLETE** (the patch batch), **786b steps 3-4 PENDING** (the reviewed minors and majors).
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

---

### Sprint 738: Alembic migration drift cleanup
**Status:** **SUPERSEDED by Sprint 797 (2026-10-22)** — delivered in full, and now actually
verified. The parity test that backs the claim below was itself measuring the wrong thing on
PostgreSQL (see the 2026-10-23 hotfix entry); the schema claim survived the correction — the
chain and the ORM do agree on all three `use_alter` foreign keys. Migration
`c9e4a1b73f20` creates all 4 tables, 6 columns and 3 FKs; both allow-lists in
`test_alembic_models_parity.py` are empty and pinned empty by
`test_drift_allowlists_stay_empty`. A chain-built database now reaches 29 of 29 tables
with zero column and zero foreign-key drift.

> **The blocker was misattributed, and that is the part worth keeping.** This sprint sat
> recorded as blocked on the Neon read-only connection string (CEO ask D-1) for a year.
> It never needed one: production was built by `create_all()` from `Base.metadata`, so it
> already held every object in question, and writing the DDL required no database read —
> only the migrations had to be *guarded* so they no-op against production. Sprint 741d
> had already demonstrated the same thing about its own "needs a database" step.
> **Before accepting an inherited blocker, check what the work actually reads.**

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

### Sprint 778: Build the off-provider backup, then prove recovery works
**Status:** SPLIT — **778a COMPLETE** (the DR workflow now reports its own verdict), **778b
PENDING** (the backup itself, the Neon rewrite and the restore drills — all need credentials).
**Priority:** P1 — both halves in scope: build the backup that does not exist **and** verify that recovery works.


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

#### 778a — the DR workflow was reporting success while its own report said FAIL: COMPLETE

Scope item 5, which needed no credentials. **Five defects in one workflow**, all verified before
changing anything, and the last two were not in the original filing.

1. **The false-green itself.** `steps.final.outputs.overall` gated only the "Create failure issue"
   step. Nothing made the *job* fail, so it exited 0 whatever its report said. Three consecutive
   scheduled runs — **2026-07-01, 08-01 and 09-01** — reported workflow success while the Render
   check resolved to FAIL. A verdict that cannot fail the job is a comment, not a check.
2. **The verdict read three signals and branched on one.** `BACKUP_RESULT` and `PROBE_RESULT` were
   assigned and never used; only `RENDER_RESULT` decided the outcome. A failed backup check or a
   dead database could not affect the verdict. Demonstrated: `render=PASS, backup=false,
   probe=false` → old verdict **PASS, exit 0**; new verdict **FAIL, exit 1**.
3. **No UNVERIFIED state.** A missing credential produced `api_error` → `FAIL` → the report line
   *"Instance status: api_error (expected: available)"*, which reads as a database outage. Three
   outcomes now: PASS, FAIL, UNVERIFIED.
4. **The liveness probe had never executed — not once.** Its guard was
   `if: env.DATABASE_URL_READONLY != ''`, but that variable is defined only in the *step's own*
   `env:` block. A step-level `if` is evaluated against the job and workflow env contexts, where
   it does not exist, so the condition was permanently false. Nobody noticed because the verdict
   ignored the probe's output anyway — defect 2 concealed defect 4. The empty case is now handled
   inside the script, which also lets it report UNVERIFIED.
5. **The failure text blamed the wrong thing.** The check targets the **Render** Postgres API;
   production moved to **Neon** in Phase 1 and the orphan Render instance was deleted
   2026-04-22. The report now says so explicitly, so `api_error` is not mistaken for an outage.

**An unverified DR posture is not a passing one.** The job now exits non-zero for FAIL *and* for
UNVERIFIED, and files an issue for both with the verdict in the title. That makes the monthly run
go red until 778b lands — which is correct and is the forcing function the 2026-10-19 note
anticipated. Nothing is known to be broken; nothing has been verified either, and the report says
exactly that.

**Also corrected: `scripts/verify_backup_integrity.py`'s error message.** It exited with
*"ERROR: RENDER_API_KEY is not set"* — which reads as a missing secret a maintainer could fix in
a minute. Setting it would not help: the script queries a deleted Render database. The message now
names the real cause and the real finding (no off-provider backup exists at all), and the exit code
is unchanged at 2.

**Checked and found sound:** `backup-integrity-check.yml` does *not* share the false-green. It uses
`continue-on-error: true` on the check step plus a Summary step that exits 1 — so its job status
has always been honest. Only `dr-test-monthly.yml` was lying. Worth recording so 778b does not
re-audit it.

**Verification:** the verdict logic was extracted and exercised against **12 cases** — all-green,
each signal failing independently, FAIL dominating an earlier UNVERIFIED, skipped steps counting as
UNVERIFIED rather than PASS, and the specific regression where a passing Render check used to mask
two failures. All 12 behave as intended. YAML parses and the job's 9 steps resolve in order.
`verify_backup_integrity.py` compiles and still exits 2. Its 4 ruff findings are pre-existing
import-ordering (identical count before the change) and outside CI's lint scope, which runs from
`backend/`.

**Two more found by the PR #187 review, and the causal chain is the interesting part.**

6. **Fixing defect 4 activated a dormant defect 6.** With the probe finally running, its result
   rendering turned out to be wrong: `> probe_result.json` creates the file *before* python
   starts, so a failed probe leaves an empty file, and the old `if [ -f probe_result.json ]`
   check then wrote *"✅ Database responded to probe"* into the same report that carried
   `probe=FAIL`. The contradiction had been unreachable for as long as the step never executed.
   Now one branch decides both the output and the report line, keyed on the exit status **and** a
   non-empty result, so they cannot disagree. Exercised against all three outcomes: python
   succeeded, python died leaving an empty file, redirection itself failed — the middle one is
   the case the old check got backwards.

7. **Making the job fail silently disabled the restore drill — a regression I introduced.**
   `restore-validation` declares `needs: dr-test` with `if: github.event_name ==
   'workflow_dispatch'`. A `needs:` dependency implies the prerequisite *succeeded* unless the
   condition uses a status function, so the moment `dr-test` began failing on a non-PASS verdict,
   the manual restore drill stopped running — in exactly the UNVERIFIED state the workflow is
   expected to hold until 778b. That is the worst possible timing: **an untested backup is not a
   backup**, and scope item 3 calls the drill the half of the risk a second mechanism cannot
   address. Fixed with `always() && github.event_name == 'workflow_dispatch'`. The drill never
   depended on the verdict anyway — it provisions its own isolated instance and runs its own
   `pg_restore` — so the gate was accidental rather than intended.

**Still blocked, and unchanged:** scope items 1–4 — building the `pg_dump` → R2 cron, confirming
Neon's real PITR retention, the restore drills, and rewriting both workflows against Neon. All need
the Neon connection string (**CEO ask D-1**) and R2 token confirmation.

**Commit SHA:** `f0d7d6ec` (778a; PR #187). 778b remains pending.

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

