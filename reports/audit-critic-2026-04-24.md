# BackendCritic — Complexity Debt Audit
**Date:** 2026-04-24
**Branch:** `sprint-716-complete-status`
**Scope:** Backend routes/shared/engines, frontend components/hooks, Alembic migrations, overnight agents
**Persona:** Technical Skeptic; veto threshold = Complexity Score >7

---

## Methodology

I ranked candidates by `wc -l`, then sampled the top 25 backend routes, top 25 shared modules, all 19 testing engines (`*_engine.py`), the largest frontend pages/contexts, all 41 Alembic migrations, and the 6 overnight agents. I steelmanned each finding (acknowledging the design pressure that produced it) before scoring it. Items below score 5 were dropped from the report — only debt that genuinely blocks future sprint velocity made the cut.

A general note before the list: **most of the backend is in surprisingly good shape.** `engine_framework.py` (`AuditEngineBase`) is a clean ABC, `routes/export_testing.py` already collapsed 7 near-identical CSV endpoints onto a `csv_export_handler()`, and the routes package has been split sensibly (~21 routers with cohesive boundaries). The debt below is concentrated in three places: an unfinished engine refactor, a half-applied CSV-export refactor, and a `shared.helpers` shim that has outlived its usefulness.

---

## Findings (ranked by Complexity Score)

### 1. Inconsistent engine pattern — `AuditEngineBase` adopted by only 3 of 12 testing engines
- **Complexity Score:** 8 / 10 — **VETO** further engine work until reconciled
- **Identified Debt:**
  - `backend/engine_framework.py` defines a clean abstract `AuditEngineBase` with a 10-step pipeline (detect → override → parse → quality → enrich → tests → score → build → cleanup).
  - **Only `je_testing_engine.py`, `ap_testing_engine.py`, `payroll_testing_engine.py` import and subclass it** (3 of 12 engines).
  - The other 9 — `revenue_testing_engine.py` (2,509 LoC), `ar_aging_engine.py` (2,179), `fixed_asset_testing_engine.py` (1,666), `inventory_testing_engine.py` (1,534), `three_way_match_engine.py` (1,476), `accrual_completeness_engine.py`, `population_profile_engine.py`, `sampling_engine.py`, `cash_flow_projector_engine.py` — each ship a **module-level top-level function** (`run_revenue_testing()`, `run_ar_aging()`, `run_inventory_testing()`, etc.) that re-implements the same pipeline as procedural code.
  - Result: when Sprint 689 expands from 12 → 18 tools, every new engine has two valid templates to copy from. `ratio_engine.py` is 2,591 lines and is itself an outlier (no class structure at all). The "shared base class" is shared only with the three tools that existed when it was written (Sprint 519).
- **Steelman:** Refactoring 9 engines mid-flight is risky on a production-live platform; the procedural form is genuinely simpler when you don't need per-engine state. The base class also forces a tuple-return hack (`extract_test_results`) for JE's Benford output, which is a smell.
- **Alternative Proposal:**
  1. **Demote `AuditEngineBase` to a thin functional pipeline.** Replace the ABC with a single `def run_audit_pipeline(detect_fn, parse_fn, quality_fn, tests_fn, score_fn, build_fn, *, rows, columns, mapping)` orchestrator. No subclassing — engines pass functions. This matches the procedural style the other 9 already use.
  2. Migrate the 3 OO engines to the functional form (small change — strip `class` wrapper, lift methods to module-level).
  3. Mandate the functional pipeline for all new tools in Sprint 689a–g via a `scripts/check_engine_pattern.py` lint that fails CI if a `*_engine.py` file lacks a `run_*()` entry point matching the signature.
  4. Document the pattern in `backend/engine_framework.py` (3 paragraphs) so the next engine author has a single template.

### 2. `shared.helpers.py` is a re-export shim that has earned its own removal
- **Complexity Score:** 7 / 10
- **Identified Debt:**
  - `backend/shared/helpers.py` (189 LoC, but ~50 lines of import re-exports). The module's own docstring says it "used to be a ~1,100-line grab bag" and was decomposed into 4 cohesive modules during the 2026-04-20 refactor pass.
  - The file then re-exports **35+ symbols** from `shared.upload_pipeline`, `shared.filenames`, `shared.background_email`, and `shared.tool_run_recorder` for backward compat — **including private symbols** like `_XLS_MAGIC`, `_parse_csv`, `_validate_xlsx_archive`, `_log_tool_activity`. Re-exporting a `_private` symbol is a contradiction in terms.
  - Counts: 62 call sites still go through the shim (`from shared.helpers import …`); only 6 use the real targets directly. The shim is winning.
  - Risk: every new sprint adds another `from shared.helpers import X` import because the docstring says "new code should import from the target module directly" but no enforcement exists. The shim is becoming permanent.
- **Steelman:** A shim is exactly the right pattern *during* a refactor — it keeps the diff small and lets you migrate at leisure. The 2026-04-20 refactor was correct.
- **Alternative Proposal:**
  1. **One-shot codemod**: a 50-line script replaces every `from shared.helpers import X` with the canonical target import (`shared.upload_pipeline`, `shared.filenames`, etc.). This is mechanical — the shim already has the mapping.
  2. Delete the re-export block from `shared/helpers.py`. Keep only the 4 helpers that legitimately live there: `try_parse_risk`, `try_parse_risk_band`, `parse_json_list`, `parse_json_mapping`, and the 3 client-access functions (`is_authorized_for_client`, `get_accessible_client`, `require_client`). File shrinks from 189 → ~80 LoC and stops being a confusing "where does X live?" question for new contributors.
  3. Add a CI check in `scripts/` that fails on `from shared.helpers import _` (any leading-underscore re-export is forbidden).

### 3. `routes/export_diagnostics.py` (689 LoC) — 7 copy-pasted CSV-writer endpoints
- **Complexity Score:** 7 / 10
- **Identified Debt:**
  - `routes/export_diagnostics.py` has 9 endpoints; 7 of them are the same shape: open `StringIO`, instantiate `csv.writer`, write a header row, iterate input items, write `[]`, write SUMMARY rows, encode `utf-8-sig`, call `streaming_csv_response`. Lines 126–290 (TB + Anomalies), 433–470 (preflight), 473–544 (population profile), 547–625 (expense category), 628–689 (accrual completeness).
  - The sister file `routes/export_testing.py` **already solved this** — Sprints 218-219 introduced `csv_export_handler(test_results, schema, composite_score, …)` plus a per-tool `*_COLUMNS` schema, collapsing 7 near-identical endpoints into one-liners. `export_diagnostics.py` did not get the same treatment.
  - Each of those 7 functions has its own `try/except (ValueError, KeyError, TypeError, UnicodeEncodeError)` block, its own `log_secure_operation` call pair, its own `safe_download_filename(…)` invocation. Every bug fix or column addition has to be made 7 times.
- **Steelman:** The diagnostic CSV layouts are heterogeneous (some have summary headers, some have multi-section reports with blank-row separators, some embed prior-period comparisons) — a one-size-fits-all schema like `*_COLUMNS` won't fit cleanly. Resisting premature abstraction is correct.
- **Alternative Proposal:**
  1. Extract a **`csv_section_writer(sections: list[CsvSection])`** helper where `CsvSection = (header: str, columns: list[str], rows: Iterable[list])`. The 7 endpoints become 5–10 lines each declaring their sections; the helper handles `StringIO`/`csv.writer`/`utf-8-sig`/`StreamingResponse`/error mapping uniformly.
  2. Don't try to share the schema with `export_testing.py` — that ABC-style mistake from item 1 is what we're avoiding. Two helpers (one schema-driven for testing, one section-driven for diagnostics) is fine.
  3. Stop new diagnostic CSV endpoints (Sprint 689 will add several for the 6 promoted tools) from being copy-pasted by adding a `pre-commit` lint that flags `csv.writer(output)` outside the helpers.

### 4. Two parallel `FOLLOW_UP_PROCEDURES` dicts in one module
- **Complexity Score:** 6 / 10
- **Identified Debt:**
  - `backend/shared/follow_up_procedures.py` (793 LoC) contains both `FOLLOW_UP_PROCEDURES: dict[str, str]` (line 12) and `FOLLOW_UP_PROCEDURES_ALT: dict[str, list[str]]` (line 545) plus `FINDING_BENCHMARKS` at line 536.
  - `get_follow_up_procedure(test_key, rotation_index)` at line 756 picks between them via the `rotation_index` argument — but the call sites in memo generators almost all pass `rotation_index=0`, so `_ALT` is mostly unused dead weight.
  - This is a "rotate procedures so memos don't read identically" feature. The need is real (auditor-facing copy variety) but the implementation duplicates **600+ lines of prose** that must stay aligned with the canonical wording or memos will contradict themselves.
- **Steelman:** A truly random LLM-generated paraphrase would risk hallucinating procedures (and we explicitly don't trust LLMs in audit copy). Hand-curated alternatives are safer.
- **Alternative Proposal:**
  1. Drop `FOLLOW_UP_PROCEDURES_ALT` entirely until a memo template ships that actually rotates between alternates. No call site today needs the variety.
  2. Move `FINDING_BENCHMARKS` (only one entry as of this audit) to whichever memo generator uses it, or delete if unused.
  3. File shrinks from 793 → ~250 LoC. Keep the rotation hook signature in `get_follow_up_procedure()` so re-introducing `_ALT` later is a one-line additive change.

### 5. Two `TOOL_LABELS` dicts of different sizes in different modules
- **Complexity Score:** 6 / 10
- **Identified Debt:**
  - `routes/activity.py:403` — `TOOL_LABELS: dict[str, str]` with 13 entries keyed by string (`"trial_balance"`, etc.).
  - `workpaper_index_generator.py:TOOL_LABELS` — different shape, keyed by the `ToolName` enum (referenced at `anomaly_summary_generator.py:58, 342, 367, 404, 480, 529, 635` and `tests/test_ar_aging.py:1271`).
  - The two diverge: `routes/activity.py` is missing `multi_currency`, `composite_risk`, all 6 hidden tools that Sprint 689 is about to promote. When Sprint 689g flips marketing copy "12 → 18 tools", **two source files must be edited in lockstep** — the current activity-feed dropdown (`/activity/tool-feed`) won't show labels for the 6 new tools.
- **Steelman:** Different shapes serve different needs (dropdown labels vs. PDF cell paragraphs).
- **Alternative Proposal:**
  1. **One canonical source of truth** in `backend/shared/tool_registry.py`: a `TOOLS: list[ToolMeta]` registry with `(name: ToolName, label: str, route_segment: str, tier_required: TierLevel)`.
  2. Both call sites consume `{t.name.value: t.label for t in TOOLS}` or `{t.name: t.label for t in TOOLS}` as needed — no duplicated literals.
  3. Eliminates the "we forgot to update both maps" risk for Sprint 689g.

### 6. Stale "12-tool" string in production app metadata
- **Complexity Score:** 4 / 10 (cosmetic — flagging because it is the OpenAPI title)
- **Identified Debt:**
  - `backend/main.py:243` — `description="12-Tool Audit Intelligence Suite for Financial Professionals"`.
  - This is the FastAPI app description served at `/openapi.json` (production). Will misrepresent the platform the moment Sprint 689a lands.
- **Alternative Proposal:** Source it from `version.py` or read tool count from the `TOOLS` registry above. One-line fix; mention it during 689g.

### 7. Marketing pages are 1,000+ LoC single-component files
- **Complexity Score:** 6 / 10
- **Identified Debt:**
  - `frontend/src/app/(marketing)/trust/page.tsx` — 1,314 LoC, 7 internal components.
  - `frontend/src/app/(marketing)/privacy/page.tsx` — 1,028 LoC, **1 component** (everything is inline JSX).
  - `frontend/src/app/(marketing)/terms/page.tsx` — 1,021 LoC.
  - `frontend/src/app/(marketing)/pricing/page.tsx` — 935 LoC.
  - These pages mix data definitions (the `ArchitectureNode[]`, `SecurityControl[]`, `ComplianceMilestone[]` arrays in trust/page.tsx are >300 LoC) with JSX rendering, with framer-motion choreography, with TypeScript type definitions. A single edit to a security-policy bullet point requires loading the entire 1,300-line file in the IDE.
  - This is high-touch, low-test-coverage code (no tests under `__tests__/marketing/`). Edits during compliance updates carry real regression risk.
- **Steelman:** Marketing pages are mostly content; they don't need cleverness. Splitting a "static content" page into 14 files can be over-engineering.
- **Alternative Proposal:**
  1. Co-locate per-page data: `trust/data.ts` exports `architectureNodes`, `securityControls`, `complianceMilestones` etc. The page becomes the JSX shell only (~400 LoC).
  2. The 4–7 internal subcomponents in trust/page.tsx (e.g., `<ArchitectureCard>`, `<ControlList>`, `<PlaybookPhase>`) move to `trust/_components/` (Next.js underscore convention — not routed).
  3. Don't introduce a CMS or MDX — that is the wrong cure for "we have one large file."

### 8. Alembic merge migrations stacking
- **Complexity Score:** 5 / 10
- **Identified Debt:**
  - 41 migrations total. Two are merge-only: `a848ac91d39a_merge_sprint_590_591_593_heads.py` and `dd9b8bff6e0c_merge_heads_before_numeric_migration.py`.
  - Merge migrations are normal hygiene when feature branches diverge — these are not bad. **However**, `c1a5f0d7b4e2_harden_export_share_passcode.py:22` and `d1e2f3a4b5c6_add_share_security_columns.py:10-11` both contain comments narrating "renamed pre-merge on 2026-04-08 to unblock the merge train" — i.e., humans are manually re-parenting migrations to dodge head conflicts. That is a process smell, not a code smell.
- **Alternative Proposal:** No code change. Add a CI step (`alembic heads | wc -l`) that fails the build if `> 1` head exists on `main`. This forces every PR to merge cleanly before landing instead of relying on a manual "merge train" merge migration.

### 9. Overnight agents — well-shaped, no debt
- **Complexity Score:** 3 / 10 (passes the bar)
- **Assessment:** `scripts/overnight/` is **not over-engineered.** Six agent modules (avg 250 LoC each), one orchestrator (190 LoC), one briefing compiler (436 LoC). Each agent writes a `.<name>_<date>.json` artifact; `briefing_compiler.py` reads all six and renders the morning markdown. Clean separation of concerns; agents are independent processes; there is no "framework" — just JSON files on disk. **Keep as-is.** The only nit: `briefing_compiler.py` could split its 8 `_format_*_section()` functions into `agents/<name>.py:format_section()` so each agent owns its output rendering. That is a 3 / 10 nice-to-have, not debt.

---

## Items I steelmanned but did NOT flag

- **`testing_response_schemas.py` (1,137 LoC, 71 classes)** — large but cohesive. Each class is a Pydantic response model bound to one route endpoint. Splitting per-tool would help readability marginally but cost `from shared.testing_response_schemas import …` ergonomics. Score: 4 / 10. Not worth a sprint.
- **`upload_pipeline.py` (812 LoC)** — has many private helpers but single-responsibility (file upload validation + parsing dispatch). Already extracted from `helpers.py` cleanly. Score: 4 / 10.
- **`auth_routes.py` (778 LoC)** — large but every endpoint is a distinct auth flow (register/login/refresh/verify/resend/forgot/reset). Splitting auth across files makes security review harder. Score: 4 / 10. **Do not split.**
- **`activity.py` (594 LoC)** — close to the threshold but defensible: activity log + tool feed + user prefs share the same domain (dashboard). Score: 5 / 10. Watch but don't refactor.
- **The 21 routes in `backend/routes/`** — average ~250 LoC, well-bounded by domain. The split is a real architectural win.

---

## Portfolio Verdict: **Paying Debt Down (net positive)**

Reading the codebase end-to-end I see a project that has **been actively reducing complexity**:
- 2026-04-20 refactor decomposed an 1,100-line `helpers.py` into 4 cohesive modules.
- Sprint 519 introduced `AuditEngineBase` to standardize testing engines.
- Sprints 218–219 collapsed 7 testing-export endpoints onto a shared handler.
- The `routes/` package split (21 cohesive routers) is one of the cleanest I've seen at this scale.
- Husky pre-commit hooks (lint, mypy, todo-staging gate) are mechanically enforced — not discipline-dependent.

The debt that remains is **half-finished refactors**: the engine base class adopted by 3 of 12 engines, the CSV handler applied to one of two export modules, the `helpers.py` shim that should be deleted now that the migration targets exist. None of these are crises. All three would be **low-risk one-sprint cleanups before Sprint 689 expands the tool count to 18.**

**Recommendation to IntegratorLead:** Insert a pre-689 cleanup sprint addressing items 1, 2, 3, 5 above (combined Complexity Score 28 / 40 — high). This is exactly the kind of work that pays off when the platform is about to grow by 50% in tool count. Skipping it means Sprint 689a–g will copy-paste from whichever pattern the previous engine used, hardening today's inconsistencies into permanent architecture.

If only one item ships: **#1 (engine pattern reconciliation)**. The mismatch between `AuditEngineBase` and the 9 procedural engines is the single biggest source of "which template do I copy?" risk in the upcoming expansion.
