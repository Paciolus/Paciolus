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

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

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
- [2026-03-26] e04e63e: full sweep remediation — sessionStorage financial data removal, CSRF on /auth/refresh, billing interval base-plan fix, Decimal float-cast elimination (13 files, 16 tests added)
- [2026-03-21] 8b3f76d: resolve 25 test failures (4 root causes: StyleSheet1 iteration, Decimal returns, IIF int IDs, ActivityLog defaults), 5 report bugs (procedure rotation, risk tier labels, PDF overflow, population profile, empty drill-downs), dependency updates (Next.js 16.2.1, Sentry, Tailwind, psycopg2, ruff)
- [2026-03-21] 8372073: resolve all 1,013 mypy type errors — Mapped annotations, Decimal/float casts, return types, stale ignores (#49)
- [2026-03-20] AUDIT-07-F5: rate-limit 5 unprotected endpoints — webhook (10/min), health (60/min), metrics (30/min); remove webhook exemption from coverage test
- [2026-03-19] CI fix: 8 test failures — CircularDependencyError (use_alter), scheduler_locks mock, async event loop, rate limit decorators, seat enforcement assertion, perf budget, PG boolean literals
- [2026-03-18] 7fa8a21: AUDIT-07-F1 bind Docker ports to loopback only (docker-compose.yml)
- [2026-03-18] 52ddfe0: AUDIT-07-F2 replace curl healthcheck with python-native probe (backend/Dockerfile)
- [2026-03-18] 5fc0453: AUDIT-07-F3 create /app/data with correct ownership before USER switch (backend/Dockerfile)
- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |
| `PeriodFileDropZone.tsx` deferred type migration | TODO open for 3+ consecutive audit cycles. Benign incomplete type migration, not a hack. Revisit when touching the upload surface for another reason. | Project-Auditor Audit 35 (2026-04-14) |
| `routes/billing.py::stripe_webhook` decomposition (signature-verify / dedup / error-mapping triad) | Already touched lightly in the 2026-04-20 refactor pass; full extraction pairs better with the deferred webhook-coverage sprint flagged in Sprint 676 review (handler is currently exercised by 6 route-test files but lacks unit coverage). Bundle both then. | Refactor Pass 2026-04-20 |
| `useTrialBalanceUpload` decomposition into composable hooks | Hook's state machine (progress indicator, recalc debounce, mapping-required preflight handoff) is tightly coupled to consumer semantics. Not a drop-in extraction — needs Playwright coverage of the mapping-required flow before a split is safe. | Refactor Pass 2026-04-20 |
| Move client-access helpers (`is_authorized_for_client`, `get_accessible_client`, `require_client`) out of `shared/helpers.py` shim | Three helpers depend on `User` / `Client` / `OrganizationMember` / `require_current_user`; a dedicated `shared/client_access.py` module isn't justified under the "prefer moving code, avoid new abstractions" guidance. Revisit if a fourth helper joins them, or if the shim grows another responsibility. | Refactor Pass 2026-04-20 |
| `routes/auth_routes.py` cookie/CSRF helper extraction | Module is already reasonably thin; cookie/token primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) are security-critical. Touching them without a specific bug or audit finding is net-negative. Revisit only if a follow-up auth/CSRF audit produces an actionable finding. | Refactor Pass 2026-04-20 |

---

## Active Phase
> **Launch-readiness Council Review — 2026-04-16.** 8-agent consensus: code is launch-ready; gating path is CEO calendar (Phase 3 validation → Phase 4.1 Stripe cutover → legal sign-off). **Recommended path: ship on ~3-week ETA** with two engineering amendments — Sprint 673 below removes the 2026-05-09 TLS-override fuse before it collides with launch week, and Guardian's 5-item production-behavior checklist runs in parallel with Phase 3/4.1 (tracked in [`ceo-actions.md`](ceo-actions.md) "This Week's Action Map"). Full verdict tradeoff map in conversation transcript.
> **Prior sprint detail:** All pre-Sprint-673 work archived under `tasks/archive/`. See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for the era index and archive file pointers.
> **CEO remediation brief 2026-04-15** — Sprints 665–671 cleared the blocking TB-intake issues from the six-file test sweep. Sprints 668–671 remaining pending items archived alongside — no longer blocking launch.
> Sprints 673–677 archived to `tasks/archive/sprints-673-677-details.md`.
> Sprint 611 + Sprints 677–714 archived 2026-04-24 to `tasks/archive/sprints-611-714-details.md` (eight post-Sprint-673 batches: Post-Audit Remediation, Anomaly Framework Hardening, Security Hardening Follow-Ups, Design Refresh, Production Bug Triage, Nightly Agent Remediation, Branding Coverage Completion, P2 Sentry Sweep). Only Sprint 715 remains pending.
> Sprints 716–720 archived to `tasks/archive/sprints-716-720-details.md`.

### Sprint 724: shared/helpers.py Shim Removal
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 8, the import-discipline cleanup.
**Priority:** P2 (architectural cleanup; reduces forking pattern that motivated the agent-sweep critic flag).
**Source:** Agent sweep 2026-04-24, punch list 3.2 + BackendCritic 7/10.

**Problem class:** The 2026-04-20 decomposition split `shared/helpers.py` into domain modules but left a 35-symbol re-export shim for back-compat. 60+ call sites went through the shim vs 6 direct — the shim was winning because nothing pressured callers to migrate. Bug fixes routing through the shim missed signal that domain ownership had moved.

**Scope landed:**
- [x] `scripts/migrate_helpers_imports.py` — one-shot migration script with a symbol→owner map. Parses `from shared.helpers import (...)` blocks (single- and multi-line), splits symbols by owner, rewrites as multiple imports preserving indent and trailing comments. Idempotent; reports unknown symbols. Dry-run + apply modes.
- [x] **47 files migrated, 56 imports rewritten** across `routes/`, `tests/`, `services/`, `shared/`, `billing/`, `export/`, and engine modules. Native helpers (`try_parse_risk`, `try_parse_risk_band`, `parse_json_list`, `parse_json_mapping`, `is_authorized_for_client`, `get_accessible_client`, `require_client`) stay in `shared/helpers.py` per the deferred-items decision (not enough native callers to justify a `shared/client_access.py` extraction).
- [x] `backend/shared/helpers.py` — re-export block (~50 lines, 35+ symbols across 4 owning modules) removed. Module docstring rewritten to reflect the post-shim role: a small native-helpers module, not a back-compat facade.
- [x] `backend/tests/test_no_helpers_reexports.py` — AST-walking guardrail with two complementary tests:
  1. `test_no_disallowed_imports`: scans every backend `.py` for `from shared.helpers import X`; fails if X is not in `ALLOWED_HELPER_NAMES`. Catches accidental shim resurrection.
  2. `test_allowlist_matches_helpers_module_publics`: cross-checks the allowlist against `dir(shared.helpers)` so neither side drifts. If a native helper is removed, this test reminds you to drop it from the allowlist.
- [x] `backend/tests/test_refactor_2026_04_20.py` — class docstring updated to reflect the post-shim contract: symbols resolve at their owning module, not at `shared.helpers`. Auto-migrated imports inside the test verify exactly that.

**Recurrence prevention (the durable artifact):**
1. **AST guardrail makes shim resurrection impossible to merge** — a PR re-adding `from shared.upload_pipeline import memory_cleanup` to `shared/helpers.py` would not regenerate the re-export shim by itself, but the *moment* a downstream caller imports it via `from shared.helpers import memory_cleanup`, the new test fails CI. The guardrail bites at the import surface, not the helpers module's internals, so any sneaky re-export attempt that someone might use to "smooth a rebase" gets caught.
2. **Allowlist is a contract** — `ALLOWED_HELPER_NAMES` is the single source of truth for what `shared/helpers.py` exports. Adding a new native helper requires updating the allowlist + adding the helper, in the same PR. Removing a helper requires the same. The two-way check prevents drift.
3. **Migration script is preserved as historical evidence** — `scripts/migrate_helpers_imports.py` is a one-shot but kept in-repo for: (a) future similar refactors have a template, (b) it documents the symbol→owner mapping that defines the boundary, (c) running it on `main` is a no-op (idempotent), proving the migration is complete.

**Out of scope:**
- Moving the native client-access helpers (`is_authorized_for_client`, `get_accessible_client`, `require_client`) to a new `shared/client_access.py` module. The deferred-items list (2026-04-20) explicitly decided against this: the three helpers depend on `User`/`Client`/`OrganizationMember`/`require_current_user`, and a dedicated module isn't justified for three functions under the "prefer moving code, avoid new abstractions" guidance. Revisit if a fourth helper joins them.
- ruff `flake8-tidy-imports` rule — the AST test in `test_no_helpers_reexports.py` is the equivalent guard, runs in the same CI step as other backend tests, and gives better failure messages than ruff. The agent-sweep plan's mention of a ruff rule is satisfied by the AST test.

**Validation:**
- 56 imports migrated cleanly; zero remaining re-export imports in backend (verified by `grep "from shared.helpers import"` showing only native-helper imports).
- 318 tests pass on the migrated subset (parser, format, injection, like-escape, refactor, upload_validation).
- 457 tests pass on the broader smoke set (memo + coverage_floors + memory_budget added).
- AST guardrail passes (2 tests); a synthetic violation (manually adding `from shared.helpers import memory_cleanup` to a backend file) fails as expected.
- Coverage floor on `shared/helpers.py` not affected (file shrank, % went up; floor not declared on this file).

**Lesson tie-in:** Same prevention shape as Sprint 717's catalog gate and Sprint 723's coverage floors: an AST/lint check at the import surface that catches the regression class at PR time rather than nightly. Migration scripts that ship in-repo (like `scripts/archive_sprints.sh` from Sprint 661) are part of the codebase's institutional memory — the symbol→owner map in `migrate_helpers_imports.py` is now documentation that survives the migration itself.

---

### Sprint 723: Coverage Floor Enforcement (Foundational)
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 7, the coverage-discipline foundational sprint.
**Priority:** P1 (foundational — Sprint 723 is a prerequisite for the architectural cleanup sprints 724–727; floors prevent silent regressions during refactors).
**Source:** Agent sweep 2026-04-24, punch list 3.5 + Coverage Sentinel report.

**Problem class:** The 10 lowest-coverage files in the codebase are also the most production-critical (parsers, generators, webhook handler, billing). The aggregate `--cov-fail-under=80` gate misses *targeted* regressions because moving coverage between files leaves the average unchanged. Coverage Sentinel surfaces drift nightly but is informational; degradation goes unblocked at PR time.

**Scope landed:**
- [x] `backend/coverage_floors.toml` — TOML floor declarations for the 9 worst-covered production-critical files (sourced from the 2026-04-25 sentinel report). Floors set ~1pp below current to absorb noise without false-failing CI: `excel_generator.py`=44, `billing/webhook_handler.py`=58, `population_profile_memo.py`=38, `workbook_inspector.py`=17, `pdf/sections/diagnostic.py`=63, `leadsheet_generator.py`=10, `config.py`=56, `main.py`=43, `routes/internal_admin.py`=54.
- [x] `scripts/check_coverage_floors.py` — TOML loader, path normalization (forward/backslash + lowercase + `./` strip), breach detection, CLI with `--missing-ok` flag for file-rename windows. Exit codes: 0 OK, 1 floor breach, 2 usage error.
- [x] `backend/tests/test_coverage_floors.py` — 26 tests: path normalization (4), TOML loader well-formed/malformed/range-validated (6), coverage loader with summary edge cases (3), core check logic including at-floor-passes and missing-ok-warns (6), CLI integration with all exit codes (6), repo floors parse cleanly (1). Greenfield, all green.
- [x] `.github/workflows/ci.yml` — wired into both `backend-tests` (SQLite) and `backend-tests-postgres` jobs as a step after pytest. Reads `coverage.json` produced by the existing `pytest --cov` run; no new CI-job-level cost beyond the floor check itself.
- [x] `docs/runbooks/coverage-floors.md` — runbook covering: daily failure flow, raise-floor process (the natural cadence — backfill + ratchet up), lower-floor governance (CODEOWNERS-approved, with rationale), add-floor process for new high-risk modules, path matching semantics, common failure modes, why TOML over YAML.
- [x] `backend/tests/fixtures/adversarial/README.md` — directory + pattern stub for the adversarial fixture corpus that future per-file backfill sprints will populate. No fixtures land in Sprint 723 itself; the boundary is established so subsequent sprints have a recognizable shape.

**Recurrence prevention (the durable artifact):**
1. **Per-file gate runs at PR time, not nightly** — the existing `coverage_sentinel` is informational. Sprint 723 added the PR-time complement so a coverage regression in a floored file blocks merge. The aggregate gate stays in place; together they catch both shapes of regression.
2. **Floors are versioned config, not magic numbers** — `coverage_floors.toml` lives in the repo with rationale comments. A reviewer can see why each file is on the list. A PR raising a floor is a self-contained artifact alongside the backfill tests; lowering one requires CODEOWNERS approval per the runbook.
3. **Path matching is robust to Windows/Linux dev splits** — the normalizer handles backslash and forward-slash equally, so a Windows-authored coverage.json compared against a forward-slash floors.toml does not false-fail.
4. **`--missing-ok` flag for transition windows** — when a floored file is renamed, the rename PR can use `--missing-ok` to land without a panicked floor edit. The next PR cleans up the floor entry.

**Out of scope:**
- **Test backfills for the 9 floored files** — that's the multi-sprint work of raising floors. Sprint 723 establishes the gate and locks in current state; backfill sprints (one per file) raise floors as tests land. The runbook documents the process.
- **AST detection of "new high-risk module without floor entry"** — the agent-sweep plan called for this. Deferred because it requires curating a "high-risk module" classifier (parser/generator/route+billing) and the current curated-floor approach is fine for the 9 known files. Reconsider if the floor list grows past ~20.
- **Auto-PR for floor raises after a backfill** — possible future enhancement; today the engineer raises the floor manually (3-line edit) which is fine.

**Validation:**
- 26/26 floor checker tests pass (`pytest tests/test_coverage_floors.py`)
- TOML parses cleanly (`load_floors(coverage_floors.toml)` returns 9 entries, all in 0..100)
- Live coverage check against today's pytest run: ✅ all 9 floors met (validated against generated `coverage.json`)
- CI step lands in both SQLite and Postgres pytest paths so the gate fires on every PR build

**Lesson tie-in:** Continues the Sprint 717/722 "wire it once at the chokepoint" pattern. Coverage already runs in `pytest --cov`; the floor check piggybacks on that same job rather than spawning a parallel coverage job. Adds 1–2s to the CI step, not 10 minutes. Same shape applies to Sprint 731's dependency-cadence gate.

---

### Sprint 722: Memory Budget for Memo Generation
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 6, the OOM-mitigation pre-Phase-3-completion sprint.
**Priority:** P1 (Render Standard 2 GB / worker; CEO running 18 memos back-to-back in Phase 3 was the OOM trigger Guardian flagged).
**Source:** Agent sweep 2026-04-24, punch list 2.1.

**Problem class:** ReportLab + openpyxl accumulate in RAM. Single-memo footprint is fine, but multiple sequential memo exports on the same worker climb past the soft headroom we keep for request payloads, SQLAlchemy session caches, and OS slab. The pressure is invisible until OOM-kill hits.

**Scope landed:**
- [x] `backend/shared/memory_budget.py` — `get_rss_mb()` probe + `track_memo_memory(label)` context manager: structured before/after RSS logging, unconditional `gc.collect()`, Sentry warning + breadcrumb when post-RSS > `MEMO_RSS_WARN_MB` (default 1500 MB).
- [x] `backend/routes/export_memos.py::_memo_export_handler` — wraps `entry.generator(...)` in `track_memo_memory(entry.log_label)`. All 18 memo PDF endpoints inherit the probe automatically; new endpoints registered via `_STANDARD_REGISTRY` get coverage for free.
- [x] `backend/requirements.txt` — pinned `psutil>=7.0.0` (was a transitive dep, now a direct one).
- [x] `backend/tests/test_memo_memory_budget.py` — 11 tests (10 fast + 1 `slow`-marked): probe correctness, before/after log contract, unconditional gc on normal-and-exception paths, threshold breach → Sentry capture (with fake sentry_sdk), under-threshold → no emit, env-var fallback on invalid/zero values, bounded RSS across 5 sequential JE memo generations.
- [x] `docs/runbooks/memory-pressure.md` — symptom-keyed response sequences, LogQL queries for the `memo.memory.*` log lines, configuration reference, rationale for the handler-level wiring.
- [x] Stale-test cleanup: `tests/test_security_hardening_2026_04_20.py` — two assertions left over from Sprint 718's enumeration-collapse (passcode-protected GET) updated 403 → 404. Pre-existing failures on main; bundled here because they blocked Sprint 722's pytest verification.

**Recurrence prevention (the durable artifact):**
1. **Wired at the handler chokepoint, not per-generator** — `_memo_export_handler` is the single function all 18 memo PDFs pass through. New memo endpoints registered through `_STANDARD_REGISTRY` inherit RSS probing without explicit per-generator opt-in. There is one path to forget, and it's already wired.
2. **Slow-marked regression test bites if `gc.collect()` is removed** — `TestRepeatedGenerationStaysBounded::test_je_memo_repeated_generation` fails if RSS grows >100 MB across 5 sequential JE memo invocations. Removing the gc sweep regresses it.
3. **Sentry warning has a working fake** — `_FakeSentry` in the test gives us confidence the threshold path emits without needing a real DSN at PR time.
4. **Soft threshold tunable via env** — `MEMO_RSS_WARN_MB` allows per-environment override (lower in staging to flush leaks, higher in prod if instance class changes). Invalid/zero values fall back to 1500 MB rather than disabling the alert.

**Out of scope:**
- Render `maxRequestsPerWorker` / `gunicorn.max_requests` — Render service config is dashboard-managed, not in repo. Recommended values documented in the runbook (§2). Operator action item, not a code deliverable.
- Sentry alert rule wiring in the Sentry UI — the `capture_message(level="warning")` is the right code shape; the alert routing rule lives in the Sentry project config and is a separate operator step (also documented in the runbook).
- `engagement_export.py::generate_zip` instrumentation — that path generates a single anomaly-summary PDF, not 18 memos. Wrapping it would be premature; runbook §5 documents the boundary so a future bundling sprint knows to extend the probe.
- 18-memo full-fixture parametrized regression test — would require 18 bespoke fixture builders and breaks under any memo schema evolution. The single representative (JE) is enough to catch the gc-removal regression; production monitoring catches per-memo growth.

**Validation:**
- 10/10 fast tests pass (`pytest tests/test_memo_memory_budget.py -m "not slow"`)
- 1/1 slow test passes (`pytest tests/test_memo_memory_budget.py -m slow`)
- 100/100 existing memo tests still green (smoke: `tests/test_je_testing_memo.py`, `tests/test_ap_testing_memo.py`, `tests/test_ar_aging_memo.py`, `tests/test_memo_boundary_phrasing.py`)
- Full backend pytest: 7231 passed, 1 unrelated pre-existing failure cleared by the bundled stale-test cleanup; 3 remaining failures (`TestCSRFRefreshLogout::test_production_rejects_x_requested_with_only`, `TestRateLimitFailClosed::test_strict_mode_defaults_true_in_production`, `TestRateLimitFailClosed::test_valid_override_allowed`) confirmed pre-existing on main — Stripe-key-validation fixtures need updating; tracked separately, not Sprint 722 scope.

**Lesson tie-in:** Continues the Sprint 717 "wire it once at the chokepoint" pattern — the registry-based memo handler already exists, so the probe lands as a 2-line edit rather than 18 per-generator decorators. This is the pattern to reuse for Sprint 723's coverage floors and Sprint 730's health endpoints.

---

### Sprint 721: Memo Output Quality & ISA 265 Boundary
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 5, the methodology-language fix.
**Priority:** P1 (boundary-language exposure visible to PCAOB-registered firms; not Stripe-blocking but pre-Phase-3-completion)
**Source:** 8-agent sweep 2026-04-24. Accounting Methodology Audit Rank-2 (boundary phrasing in three_way_match + ar_aging memos).

**Problem class:** Memo generators contain language that drifts toward auditor-judgment territory (deficiency classification, misstatement conclusions, prescriptive remediation). The hardest cases were already caught by the existing `BANNED_PATTERNS` regex; soft phrases (`systemic review … recommended`, `potential understatement of credit loss expense`) slipped through. Sprint 721 closes the soft-phrase gap and makes the deny list a CI guardrail.

**Scope landed:**
- [x] `backend/three_way_match_memo_generator.py:113` — "Below 80% threshold — systemic review of procure-to-pay controls recommended" → "match-rate anomaly indicator; auditor judgment required to determine cause".
- [x] `backend/ar_aging_memo_generator.py:34` — "potential understatement of credit loss expense per ASC 326" → "allowance-coverage anomaly indicator under ASC 326. Sufficiency of the allowance estimate is an auditor judgment; this test surfaces a quantitative signal only."
- [x] `docs/03-engineering/auditing-lexicon.md` — canonical allow/deny phrase tables organized by ISA/AS reference. Includes inline `# allow-deny-phrase: <reason>` annotation syntax for legitimate exceptions (quoting standards' titles, etc.).
- [x] CI test `backend/tests/test_memo_boundary_phrasing.py` — parametrized scan over every `*_memo_generator.py` source file. 13 deny patterns from the lexicon; word-boundary regex matching; allowlist annotation respected. 15 cases (1 smoke + 13 generators + 1 lexicon-doc-exists check), all green.

**Recurrence prevention (the durable artifact):**
1. **Auditing lexicon as canonical reference** — single doc that engineers, models, and reviewers all consult. Adding a new memo generator means reading the lexicon first.
2. **Per-generator parametrized test** — every `*_memo_generator.py` is automatically scanned; new generators inherit the guardrail without explicit wiring.
3. **Word-boundary deny patterns** — soft phrases like "systemic review" and "potential understatement" now fail CI. The existing `BANNED_PATTERNS` regex (which catches the hard cases at runtime) is now complemented by a static-source guardrail at PR time.
4. **Inline allowlist syntax** — legitimate exceptions (e.g., quoting a standard's title) are annotated, not silently allowed. PR review centers on the *reason*, not the existence.

**Out of scope:**
- Snapshot tests of rendered memo PDFs (would require ReportLab fixtures + golden file management). The source-string scan catches the same phrases without the PDF runtime cost. Sprint 723's coverage-floor work may bring us to a place where this is worth adding.
- Strengthening the existing runtime `BANNED_PATTERNS` regex — that catches the hardest cases already; the static scan is the new defense layer.

**Validation:**
- 15/15 boundary-phrasing tests pass (13 memo generators all clean post-fixes)
- Existing memo tests still pass (smoke-tested on ar_aging + three_way_match)

**Lesson tie-in:** Continues the Sprint 717 "single source of truth" pattern — the lexicon is the canonical phrase taxonomy that the CI test grounds against. Same shape as `tools_registry.py` / `standards_registry.py`: human-readable doc + machine-readable check.

---

### Sprint 715: SendGrid 403 root-cause investigation (24h post-deploy watch)
**Status:** PENDING — investigable starting **2026-04-25 ~14:29 UTC** (24h after Sprint 713 merge `2b92b771` on 2026-04-24 14:29 UTC).
**Priority:** P2 (observability follow-up — no user-facing impact, but worth knowing which recipient/path triggers the 403)
**Source:** Sprint 713 Bug C review — the fix caught the exception but did not investigate the root cause. The 403 means SendGrid is refusing a specific send; until we know *why*, users on the affected path silently never receive their email.

**Why pending (not "now"):** Sprint 713's warn-path (`log_secure_operation("email_error", f"SendGrid HTTPError status=403")`) is what makes the root cause investigable. We need 24h of production traffic with the new logs in place to see *which* send triggers the 403 and *how often*. Pre-deploy, we'd be guessing.

**Plan when triggered (CEO signal: if warn log count > 0 after 24h):**
- Pull Render logs for `"SendGrid HTTPError status=403"` over the post-deploy window. Identify the sender function (verification / password-reset / contact / email-change) and recipient masking pattern.
- Check SendGrid Dashboard → Suppressions → Blocks / Bounces / Spam Reports for the 403 recipients. Most likely cause: addresses on the global bounce list from the pre-Domain-Authentication era (SendGrid carried the `@gmail.com` bounce history into the paciolus.com domain).
- Check SendGrid API key scope on the Paciolus production key — `Mail Send: Full Access` is required; a read-only or Marketing-scoped key would 403 on transactional sends.
- Fix depends on finding: suppression-list cleanup (one-time; then add a `/admin/email-suppressions` endpoint to view current state), API key re-scope, or sender-domain re-verification.

**Out of scope:**
- Proactive suppression-list sync (would need a scheduled cron polling SendGrid API; not worth the infrastructure until we see meaningful 403 volume).
- Email deliverability SLA tracking (a separate observability sprint if Sentry breadcrumbs aren't sufficient).

---

