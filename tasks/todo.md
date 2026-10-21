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

### Sprint 787b: Wire the six Sprint-689 tools into engagement tracking
**Status:** COMPLETE for the backend half. **The UI half does not exist** — see the correction at
the end of this entry, and **Sprint 791**.
**Priority:** P2 — the catalog counts are honest after Sprint 787; the runs were still not recorded.
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

#### What landed

All six routes now take `engagement_id` in the request body and record through
`maybe_record_tool_run`. These are JSON-body routes, so the reference pattern is
`multi_period.py` (`payload.engagement_id`) rather than `ar_aging.py`'s multipart
`Form(default=None)` — otherwise identical: `background_tasks.add_task(...)` on the success
path, a synchronous `success=False` call in each error arm.

| Route | Endpoint wired | Error arms recorded |
|-------|----------------|---------------------|
| `sod.py` | `/audit/sod/analyze` | 1 (new `try`, see below) |
| `intercompany_elimination.py` | `/audit/intercompany-elimination` | 2 |
| `w2_reconciliation.py` | `/audit/w2-reconciliation` | 2 |
| `form_1099.py` | `/audit/form-1099` | 2 |
| `book_to_tax.py` | `/audit/book-to-tax` | 2 |
| `cash_flow_projector.py` | `/audit/cash-flow-projector` | 2 |

The `export.csv` endpoints are deliberately **not** wired. A CSV re-render of an analysis the
caller already ran is not a second run, and 689c–g already made the same split for
`check_upload_limit`.

**The design question, answered: `None` for both parameters on all six.** Not an omission —
none of the six engines computes a composite score (verified: zero occurrences of
`composite_score` across all six `*_engine.py` files), and `shared/account_extractors.py` has
no extractor for any of them because none produces GL-account-level output. Sprint 787 already
established that equivalence mechanically: `CONVERGENCE_TOOLS` is exactly the key set of
`ACCOUNT_EXTRACTORS`. A test pins both as `None` so a later change cannot start writing a
fabricated score into a workpaper quietly.

**`sod.py` needed a `try` the other five already had.** Its engine does not raise on bad
input; `_build_extra_rule` does, as a 400 for an unrecognised severity. That is still a failed
run from the engagement's point of view, so the call is wrapped and the failure recorded
rather than dropped.

#### Tests — `tests/test_promoted_tool_engagement_wiring.py`, 37 tests

Four parametrized cases per tool (24) plus failure-path, activity-feed and guard coverage:
run-creates-ToolRun, omitting `engagement_id` records nothing, repeat runs increment
`run_number`, and **a foreign `engagement_id` is ignored rather than recorded** — worth its own
case on all six because the wiring passes an attacker-chosen integer straight from the request
body into the recorder, which resolves it through `EngagementManager.get_engagement(user_id, …)`.
Also covered: `ToolActivity` rows are written even with no engagement link, which is what makes
these six appear on the multi-tool dashboard at all.

**Two guards, both of which failed to work on their first draft.** Recording this because it is
now the fifth instance of the same class in this repo:

1. *"Every route that accepts an `engagement_id` on a run must record it."* First draft flagged
   **nine false positives** — it required a direct `maybe_record_tool_run` call, but the six
   testing routes delegate to `shared/testing_route.py::run_single_file_testing` and the
   diagnostics routes to `services/audit/file_tool_scaffold.py::execute_file_tool`, both of
   which record. It also counted `engagement_id` arriving as `Query(...)` — a filter on a read
   in `activity.py` and `trends.py`, where nothing should be recorded.
2. Fixing it by resolving imports one hop made it **vacuous**. `shared/testing_route.py` holds
   both `enforce_tool_access`, which nearly every route imports, and `run_single_file_testing`
   — so "imports from a module that calls the recorder" was true for almost every route. The
   guard went green and tested nothing. **Regression-proving caught it**: stripping the recorder
   out of `routes/form_1099.py` left the guard passing. The check is now on the called function
   from an explicit two-name allowlist, and a second test asserts those two helpers really do
   record, so the allowlist cannot rot into a lie.

Both guards were then regression-proved in both directions — injected violation fails and names
the right file, restore passes.

**The open question about the background-task session — resolved, then pinned.** The success
path hands a request-scoped `Session` to `background_tasks.add_task(maybe_record_tool_run, db, …)`,
which is only safe if the task runs *before* `get_db`'s `finally: db.close()`. These tests cannot
settle it: `_override` installs `get_db` as `lambda: db_session`, a plain callable rather than a
generator, so no teardown happens at all.

Settled empirically against the installed FastAPI 0.136.1 with a throwaway app carrying a real
`yield` dependency. Observed order: `handler body` → `task ran` → `teardown`. **Background tasks
run first, so the session is still open.** The house pattern is correct, not accidentally
surviving — my initial read of the FastAPI 0.106 change was wrong.

Worth more than a note, because **Sprint 786b plans FastAPI 0.136 → 0.150.** If a release in that
range flips the ordering, all 13 wired routes stop filing success-path tool runs and *every other
test in this file still passes*, since they all override `get_db` with a non-generator.
`TestBackgroundTaskOrderingContract` therefore asserts the ordering directly, with a failure
message that names the consequence and points at 786b. Built on a throwaway app rather than
`main.app` deliberately — the property belongs to FastAPI's dependency machinery, and routing it
through the real app would drag in auth, rate limiting and the database for no added signal.

#### Four review findings on PR #182 — all four real, two fixed here

An automated reviewer raised three P1s and a P2. Every one was verified against the code or
empirically before acting; **all four hold**, and two of them falsify claims made above.

**Fixed in this PR**, because both live in `shared/tool_run_recorder.py` — the module six new
callers were just added to — and both made assertions in this sprint's own test file untrue:

1. **The `ToolActivity` row was never durable for an engagement-less run.** The module docstring
   declared the recorder "is deliberately never the transactional boundary… letting the route
   handler own the commit." **No route handler has ever committed it.** `get_db` ends in a bare
   `db.close()`, so the pending insert was discarded — measured at **zero rows surviving**
   through a real `get_db` generator. Runs *with* a resolving engagement persisted only because
   `EngagementManager.record_tool_run` commits and flushed the activity row along with it. So the
   multi-tool dashboard feed has been losing every engagement-less run across **all thirteen**
   wired routes, not just the six added here. The recorder now owns that commit, consistent with
   `record_tool_run` on the same session.

2. **A stale `engagement_id` returned 500 from every wired route.** The recorder wrote
   `ToolActivity` carrying the caller-supplied id *first*, then queried for the engagement — and
   that query's autoflush pushed the insert into a `tool_activity.engagement_id` foreign-key
   violation. Confirmed empirically to raise `IntegrityError` on **both** the success and the
   failure path, which is worse than reported: on the failure path it replaced an intended 400
   about malformed input with a server error. Resolution now happens before the write, and an
   unresolvable id degrades to an *unlinked* activity row — the same "skip the workpaper trail"
   semantics already applied to an engagement owned by someone else.

   Nine new tests cover both, all nine regression-proved: they fail against the old recorder
   (`FOREIGN KEY constraint failed`, zero surviving rows) and pass with the fix.

**Corrected, not fixed — filed instead:**

3. **The quota claim in Sprint 789 was false.** See the correction in that entry. `check_upload_limit`
   only reads; nothing increments the counter outside bulk upload. Filed as **Sprint 790**.

4. **Nothing in the UI ever sends `engagement_id` for these six tools.** None of the six hooks
   references engagement at all. This sprint delivered the backend precondition and the tests
   construct `engagement_id` directly, so **a browser user still cannot produce a `ToolRun`** —
   the exact shape of overclaim the PR #174 review caught in Sprint 787, repeated one layer out.
   Status above corrected accordingly.

   The gap is app-wide and pre-existing rather than introduced here: only four hooks
   (`useAuditUpload`, `usePreflight`, `useStatisticalSampling`, `useTrialBalanceUpload`) plus the
   multi-period page call `useOptionalEngagementContext`, and `createTestingHook.ts` — which
   backs the nine testing tools — has **zero** engagement references, even though those backends
   have accepted `engagement_id` as a `Form` field for sprints. Filed as **Sprint 791**.

**Verification:** 46 tests in `test_promoted_tool_engagement_wiring.py` (37 + 9 for the review
findings); 1,336 passed across every recorder-dependent suite; full backend suite green;
`ruff check .` clean; no new mypy findings in the six changed modules;
`scripts/check_openapi_drift.py` reported exactly the six intended `engagement_id` additions and
nothing else, snapshot regenerated (paths 220, schemas 422, both unchanged).

**Commit SHA:** filled at merge.

---

### Sprint 789: Two paying tiers were sold a tool the API refused to run
**Status:** COMPLETE.
**Priority:** **P1** — a contractual surface promised a tool the backend 403'd. Revenue-relevant
and liability-relevant, not cosmetic.
**Source:** found while surveying `routes/sod.py` for Sprint 787b, which had flagged it only as
"no `db: Session`". CEO decision 2026-10-21: remove the gate.

`routes/sod.py` carried a bespoke `require_enterprise_tier` dependency that returned 403 to
every tier below Enterprise — **the only hardcoded tier comparison in any route module.**
Meanwhile every other surface sold Segregation of Duties to Solo and Professional:

| Surface | What it said | File |
|---------|--------------|------|
| **Terms of Service** tier table | "All 18 tools" for Solo *and* Professional | `(marketing)/terms/page.tsx:616,621` |
| Pricing page tier features | "All 18 diagnostic tools" on both paid tiers | `(marketing)/pricing/page.tsx:381,401` |
| Pricing page **FAQ** | "Both Solo and Professional include all 18 diagnostic tools" | `(marketing)/pricing/page.tsx:482` |
| Pricing page SEO metadata | "All paid tiers include all 18 diagnostic tools" | `(marketing)/pricing/layout.tsx:5,8` |
| `UpgradeModal` — shown at purchase | "All 18 tools" on Solo and Professional | `billing/UpgradeModal.tsx:27,35` |
| Backend entitlements table | `tools_allowed=_ALL_TOOLS` (empty = all) for every paid tier | `shared/entitlements.py:88,107` |
| Tool catalog (SSOT) | `sod_checker`, `is_marketing_audit_tool=True` | `tools_registry.py:170` |
| `UpgradeGate` docstring | "All paid tiers … have access to all 18 tools" | `shared/UpgradeGate.tsx:10` |

**Why it survived.** Sprint 689b's own filing says "Already Enterprise-gated" — the gate was
known and carried forward when the tool was promoted into the marketed catalog. Sprint 717 then
added it to `tools_registry.py`, and Sprints 784/788 swept the prose from 12 → 18. Every one of
those made the count correct and the *access* wrong, because nothing cross-checked a tier gate
against the entitlements table. `test_catalog_consistency.py` ties the registry to the frontend
ledger; nothing tied either to what the routes actually allow. The frontend even documented the
discrepancy without resolving it: `tools/sod/page.tsx` layered `FeatureGate` on top of
`UpgradeGate` with the comment "the standard UpgradeGate only blocks Free tier, so this page
layers … to block Solo/Professional as well."

**What landed.**
- `routes/sod.py` — `require_enterprise_tier` deleted; `require_verified_user` + `db: Session`
  with the standard `enforce_tool_access(current_user, "sod_checker", db)` and
  `check_upload_limit(current_user, db)`. SoD was the only one of the six promoted tools calling
  neither, so it is now consistent with its five siblings.

  > **CORRECTION (PR #182 review).** This bullet first claimed the `check_upload_limit` addition
  > "closed a second, independent defect: its runs never counted against the monthly upload
  > quota." **That is wrong, and the real defect is larger.** `check_upload_limit` only *reads*
  > the counter — `increment_upload_count` is the only thing that writes it, and its sole caller
  > in the entire repository is `routes/bulk_upload.py:154`. So **no single-tool run anywhere
  > increments `Subscription.uploads_used_current_period`**, and the advertised 100/500 monthly
  > allowances are not enforced for any paid tier. Free tier *is* metered, because it falls back
  > to counting `ActivityLog` rows. Adding the check to SoD makes it consistent, not enforced.
  > Filed as **Sprint 790**. This also explains why Sprint 741a found "no realized impact" from
  > the broken `reset_upload_quotas` job: the counter it resets is almost never incremented.
- `/audit/sod/rules` → `require_verified_user`, no entitlement check. It exposes the rule
  library, not an analysis of customer data — mirrors `/audit/book-to-tax/standard-adjustments`.
- `/audit/sod/analyze.csv` → `enforce_tool_access` without `check_upload_limit`, the same split
  689c–g use for their exports.
- Frontend: `FeatureGate` → `UpgradeGate(toolName="sod_checker")`; `sod_checker` removed from
  `FeatureGate`'s union, tier map and display-name map entirely, since that component's own
  docstring says it gates features and that tools belong to `UpgradeGate`; `GuestCTA` copy
  "verified Enterprise account" → "verified account on a paid plan"; the "Enterprise plan."
  suffix dropped from the `/tools` catalog description; the `useSOD` header comment corrected.

**A second defect the tests found.** `tools/sod/page.tsx` claimed "**Twelve** standards-backed
SoD rules". `DEFAULT_SOD_RULES` has **11** (AP-01…03, JE-01/02, PR-01/02, REV-01/02, INV-01,
ADM-01). Corrected to Eleven, and the test now pins the count *exactly* with the full code set
rather than `>= 12` — a `>=` assertion would not have caught this and, for the months the claim
was live, nothing did.

**Tests — `tests/test_sod_routes.py`, 10 tests.** Free blocked on analyze and on CSV export with
the standard `TIER_LIMIT_EXCEEDED` shape (not the old bespoke `{"error": "tier_locked"}`
payload); **Solo, Professional and Enterprise all pass**, parametrized — Enterprise is included
so a future change cannot narrow the gate back to a single tier and still go green; the rule
library readable by Free as reference data.

Plus an AST guard: **no route module may compare `<...>.tier` against a `UserTier` member.** The
defect was not that SoD was Enterprise-only, it was that one route decided tier access for
itself instead of asking `enforce_tool_access`, which let the entitlements table, the catalog
and a contract page disagree with it indefinitely with nothing failing. `routes/sod.py` was the
only offender; this keeps it that way. Regression-proved by injecting a comparison into
`routes/book_to_tax.py` — the guard failed and named `book_to_tax.py:143` exactly, then passed
on restore. (Firing is not the same as being right; Sprint 782a's gate named a class that
existed nowhere on its first draft.)

**Verification:** 10 new backend tests; 237 passed across the affected backend suites; frontend
`SODPage.test.tsx` 4 → 6 tests, full suite 2,009 → **2,011** passed, 0 failures; `tsc --noEmit`
exit 0; `npm run build` clean with every route `ƒ (Dynamic)` and `ƒ Proxy (Middleware)` active;
`ruff check .` clean; the 120 CI-gate tests (design-token lint, doc consistency, accounting
policy, citation consistency) all pass.

**Not in scope, deliberately:** the two stale "twelve tools" strings on live marketing pages that
this sprint's grep uncovered, and the reason nothing caught them. Filed as **Sprint 789b**.

**Commit SHA:** `d21542a3`. Note that `routes/sod.py` carries both this sprint's gating change
and Sprint 787b's engagement wiring in the same function signature, so the whole file landed in
this commit; 787b's other five routes are the commit after.

---

### Sprint 789b: The doc-consistency gate does not read the website
**Status:** PENDING.
**Priority:** **P1 for the two strings** (live, customer-facing, wrong), P2 for the guard
extension.
**Source:** Sprint 789. A grep for spelled-out tool counts turned up three stale "twelve"s, two
of them on public marketing pages.

| File | Current text | Should be |
|------|--------------|-----------|
| `(marketing)/demo/page.tsx:79` | "Explore all **twelve** audit diagnostic tools using synthetic data." | eighteen |
| `marketing/ToolSlideshow.tsx:514` | "**Twelve** purpose-built tools. Explore each one to see exactly what you get." | eighteen |
| ~~`tools/sod/page.tsx:93`~~ | ~~"Twelve standards-backed SoD rules"~~ | fixed in Sprint 789 (the library has 11) |

**The interesting part is why these survived three separate sweeps.**
`backend/guards/doc_consistency_guard.py` exists precisely for this — its own docstring says
AGENTS.md, README.md, PRODUCT_VISION.md, ARCHITECTURE.md and USER_GUIDE.md "all still said
twelve" — and it already carries a spelled-out numeral map including `"twelve": 12`. But its
`GUARDED_DOCS` list is **six markdown files plus two compliance documents**. It never looks at
`frontend/src/**/*.tsx`.

So the gate guards the documentation and ignores the thing customers actually read. Sprint 784
(tool-count cohesion, 12 → 18) and Sprint 788 (tool navigation) both ran and both missed these,
because both were scoped by what the guard measures.

**Scope:**
1. Fix the two strings.
2. Extend the guard to a customer-facing frontend copy set — the marketing route group, the
   pricing/terms pages, `components/marketing/**`, `components/billing/UpgradeModal.tsx` — using
   the numeral map that already exists. Keep JSX out of scope for the *digit* patterns where it
   would false-positive (`toolRuns.length}/18`, `number: 13` in the ledger) and prove the
   false-positive set with tests, as Sprint 782a's design-token lint does.
3. Decide the boundary explicitly and write it down: the guard should read copy a customer can
   see, and skip code comments and historical records. A `/* 12-tool era */` comment is a note;
   "Explore all twelve tools" is a claim.

**Acceptance bar:** the two strings corrected; the extended guard, run against the tree *before*
the fix, reports exactly those two and no false positives; a test pins the false-positive set so
the next count change cannot be waved through.

**Commit SHA:** TBD.

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

### Sprint 791: The engagement link exists in every API and in almost no UI
**Status:** PENDING.
**Priority:** P2 — the engagement layer's workpaper trail is largely empty in practice, and three
sprints have now claimed engagement tracking that a browser user cannot actually produce.
**Source:** PR #182 review finding, verified 2026-10-21.

Backends accept `engagement_id` on roughly every analysis endpoint. The browser almost never
sends it. Only **four hooks** — `useAuditUpload`, `usePreflight`, `useStatisticalSampling`,
`useTrialBalanceUpload` — plus the multi-period page call `useOptionalEngagementContext`.

Most consequential: **`hooks/createTestingHook.ts` has zero engagement references**, and it backs
nine tools (JE, AP, Payroll, Revenue, AR Aging, Fixed Assets, Inventory, Bank Rec, Three-Way
Match). Their routes have accepted `engagement_id` as a `Form` field for sprints. The six
promoted tools wired in Sprint 787b are in the same position.

So a practitioner who opens a tool from inside an active engagement — the `/tools/*` layout does
supply `EngagementProvider`, and the workspace URL does carry `?engagement=…` — produces a run
that is filed nowhere. The workpaper index, the Anomaly Summary coverage fraction and the
completion gate are all counting a population the UI cannot populate.

**This is the third sprint in a row to claim engagement tracking without the whole path.** Sprint
787 added the enum and claimed the tools were trackable; the PR #174 review caught it. Sprint 787b
wired the routes and claimed the tools were tracked; the PR #182 review caught it. The pattern is
that each sprint verified its own layer and inferred the rest, so the fix has to include a test
that spans the layers rather than another layer-local one.

**Scope:**
1. `createTestingHook.ts` — read `useOptionalEngagementContext` and append `engagement_id` to the
   FormData when an engagement is active. One change covers nine tools.
2. The six promoted tools' hooks — add it to the JSON payload.
3. An end-to-end test per tool family, from a rendered page with an active engagement to a
   `ToolRun` row. Layer-local tests are what let this through twice.
4. Audit the remaining tools for the same gap and record which deliberately have none.

**Acceptance bar:** with an active engagement selected, running any tool from its page produces a
`ToolRun` row — asserted through the UI, not by constructing the payload in a test.

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

### Sprint 786c: Refresh the six GitHub Actions SHA pins
**Status:** PENDING.
**Priority:** P3 — CI-only. No production surface, but action pins are the one dependency class in this repo that **cannot self-heal**, so they rot silently.
**Source:** Sprint 785 Dependabot triage. Replaces the four stale Dependabot action PRs (#77, #78, #90, #156), all closed as superseded.

`ci.yml` and the other workflows pin every action by commit SHA rather than tag — correct practice, since a tag is mutable and a compromised action runs with repository credentials. The cost is that nothing updates them automatically, and Dependabot's own PRs for them sat unmerged for six months until their targets went stale too.

**Current pins and current releases (measured 2026-10-21):**

| Action | Pinned | = tag | Latest |
|--------|--------|-------|--------|
| `actions/checkout` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` | v6.0.2 | **v7.0.1** |
| `actions/github-script` | `ed597411d8f924073f98dfc5c65a23a2325f34cd` | v8.0.0 | **v9.0.0** |
| `actions/setup-node` | `53b83947a5a98c8d113130e565377fae1a50d02f` | v6.3.0 | **v7.1.0** |
| `actions/setup-python` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` | v6.2.0 | **v7.0.0** |
| `actions/upload-artifact` | `bbbca2ddaa5d8feaa63e36b76fdaad77386f024f` | v7.0.0 | **v7.0.2** |
| `actions/download-artifact` | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` | v8.0.1 | **v8.0.2** |

Four of the six are **major** bumps. `upload-artifact` and `download-artifact` are patch-level and safe to batch.

**Approach:**
1. Batch the two patch bumps (`upload-artifact` 7.0.0 → 7.0.2, `download-artifact` 8.0.1 → 8.0.2) in one commit.
2. One major per commit, each resolved to its release SHA (not the tag) with the tag recorded in a trailing comment so the next reader can tell what the SHA is without an API call. `checkout` v7 first (every job uses it, so a break is immediate and obvious), then `setup-python` v7, `setup-node` v7, `github-script` v9 last — it is used in the failure-issue step of `uptime-check.yml`, which is the hardest to exercise on a PR.
3. Read each major's release notes for runner-version and Node-runtime requirements before bumping; the v6 → v7 wave across the `actions/*` org is largely a Node runtime move.

**Verification:** every workflow that references the bumped action runs green on the PR. `github-script` cannot be proven by a normal PR run (its only use is in a failure path), so dispatch `uptime-check.yml` manually on the branch and confirm the failure-issue step still *skips* correctly rather than erroring.

**Out of scope:** switching from SHA pins to tags. The pins are deliberate and stay.

**Commit SHA:** TBD.

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

### Sprint 778: Build the off-provider backup, then prove recovery works
**Status:** PENDING.
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

