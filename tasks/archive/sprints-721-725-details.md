# Sprints 721–725 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-25.

---

### Sprint 725: Export Endpoint Consolidation
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 9, the export-pattern unification.
**Priority:** P2 (architectural cleanup; reduces 6+ copy-pasted CSV endpoints to one shared pattern).
**Source:** Agent sweep 2026-04-24, punch list 3.3 + BackendCritic 7/10.

**Problem class:** `routes/export_diagnostics.py` (689 LoC) had 6 hand-written CSV endpoints that all replicated the same pipeline: `StringIO()` → `csv.writer` → custom rows → `getvalue().encode("utf-8-sig")` → `safe_download_filename` → `streaming_csv_response` wrapped in `try/except (ValueError, KeyError, TypeError, UnicodeEncodeError)`. Sister `routes/export_testing.py` had collapsed the equivalent pattern via `csv_export_handler()` (Sprint 539), but the helper lived in the route module rather than `shared/`, so diagnostics couldn't borrow it. Two flagged-entry-shape testing routes (TWM, sampling-selection) also had inline boilerplate that didn't fit the schema-driven helper.

**Scope landed:**
- [x] **Promoted `csv_export_handler` to `backend/shared/csv_export.py`** so both `export_testing` and `export_diagnostics` import from one canonical helper.
- [x] **Added `diagnostic_csv_export(body_writer, ...)` helper** in `shared/csv_export.py` for the free-form diagnostic shape (sectioned bodies, custom totals, per-row drill-down). Caller supplies a `body_writer(csv.writer)` callable; helper handles transport boilerplate identically to `csv_export_handler`.
- [x] **Refactored 6 CSV endpoints in `routes/export_diagnostics.py`** to use `diagnostic_csv_export`: `/export/csv/trial-balance`, `/export/csv/anomalies`, `/export/csv/preflight-issues`, `/export/csv/population-profile`, `/export/csv/expense-category-analytics`, `/export/csv/accrual-completeness`. File shrank from 696 → ~570 LoC (~125 LoC of duplicated boilerplate removed).
- [x] **Refactored 2 CSV endpoints in `routes/export_testing.py`**: `/export/csv/three-way-match` and `/export/csv/sampling-selection` — both had free-form bodies that fit `diagnostic_csv_export` better than the schema-driven `csv_export_handler`. Removed `csv`, `StringIO`, `HTTPException`, `sanitize_error`, `streaming_csv_response`, `safe_download_filename` from the import list (now indirected through `shared/csv_export`).
- [x] **`backend/tests/test_csv_export_helpers.py`** — 7 direct unit tests for the helpers: body-writer invocation, UTF-8-BOM encoding, filename fallback, `ValueError`/`KeyError`/`TypeError` → `HTTPException(500)` with sanitized detail (no raw exception leak), unhandled exceptions propagate. Async-iterator drain pattern documented in `_read_streaming_response_body`.
- [x] **`docs/03-engineering/export-pattern.md`** — picks-the-helper guide for new endpoint authors. Two helpers, two shapes, what's covered, what's not (PDF/Excel exports remain inline).

**Recurrence prevention (the durable artifact):**
1. **Single canonical location** — `shared/csv_export.py` is the only place these helpers live. Moving them out of `routes/export_testing.py` removes the "I didn't know diagnostics could use it" friction that kept the duplication alive.
2. **Two-helper split is principled** — schema-driven (testing-tool flagged-entry) vs free-form body (diagnostic). Documented in the export-pattern doc with concrete examples. New endpoint authors pick the one that fits the shape; "build a third helper" is explicitly out-of-scope unless duplication accumulates again.
3. **Direct unit tests of the helpers** — covers regression in body-writer invocation, encoding, filename sanitization, exception → HTTPException pipeline. Live alongside the route-level end-to-end tests rather than replacing them.
4. **Sanitized-detail invariant verified by test** — `assert "boom in body writer" not in detail` ensures raw exception text doesn't leak through `sanitize_error()`. Catches a future refactor that accidentally exposes the raw `str(e)`.

**Out of scope:**
- **AST lint rule** for "every `routes/export_*.py` `@router.{get,post}` handler must call one of the approved factories." The agent-sweep plan suggested this; deferred because there are legitimate exceptions (PDF/Excel routes shouldn't use the CSV helpers) and the rule would need a curated allowlist that's net-negative for clarity. The export-pattern doc + CODEOWNERS reviewers are sufficient until duplication starts accumulating again.
- **`/export/leadsheets` and `/export/financial-statements`** (Excel) consolidation. They use `streaming_excel_response` directly; their boilerplate is two lines, not enough to justify a helper. Revisit if a third Excel export lands.
- **Removing `log_secure_operation` start-of-export audit logs** from the diagnostic endpoints. Those logs serve a different purpose (security event audit trail) than the per-export observability captured by the access log; keeping them is intentional. Removed only the `*_complete` byte-size logs since access log + Sentry breadcrumbs cover that signal.

**Validation:**
- 7/7 helper unit tests pass (`tests/test_csv_export_helpers.py`)
- 286/286 broader smoke set pass (export-routes + export-testing + export-diagnostics + injection-regression + no-helpers-reexports + coverage-floors + memo-memory-budget + refactor)
- 8 endpoints converted; remaining 2 endpoints in `export_testing.py` (TWM, sampling-selection) also collapsed onto `diagnostic_csv_export` rather than left inline — opportunistic cleanup.
- Both helpers exposed as `__all__` from `shared.csv_export`; both have docstrings linking back to Sprint 539/725 history.

**Lesson tie-in:** Same shape as Sprint 717 (registry SSOT) and Sprint 722 (memo memory probe at the chokepoint): the helper sits at the chokepoint, not at each caller. New endpoints inherit the right behavior because the type signature (`body_writer` or `schema`) is the only thing they have to provide. Reduces both authoring time and audit surface.


---

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

