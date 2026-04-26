# Sprint Plan: 728 (ISA 520) + 729 (ISA 450)

> **Status:** PROPOSED — awaiting CEO approval before code is cut on 728a.
> **Author:** IntegratorLead, 2026-04-26.
> **Pre-requisite work:** Sprint 715 closed (commit `a933e238`).

---

## CEO decisions confirmed (2026-04-26)

1. **Path A — Snapshot model.** New entities (`AnalyticalExpectation`, `UncorrectedMisstatement`) hold *audit decisions* (expectations, results, conclusions). The CPA captures snapshots at the moment they identify them. Existing zero-storage invariants for `AdjustingEntry` and sampling output are preserved.
2. **All six sub-sprints in scope.** 728a → 729a → 728b → 729b → 728c → 729c, executed sequentially with one atomic commit per sub-sprint.
3. **Tool wiring (728c) in scope.** Flux / ratio / multi-period TB engines will accept a pre-supplied expectation parameter and return variance flags inline; entity captures both inputs and result.

---

## Why the snapshot model is the right architecture

ISA 450 §A14 / AU-C 450 §A23 frame the SUM as a *workpaper of audit decisions* — the auditor's record of which misstatements were identified, how they were classified, and how they were dispositioned. It is **not** a database join over the raw misstatements. ISA 520 §A4–A8 frame analytical expectations the same way: the auditor documents the expectation, the precision threshold, the corroboration basis, and the conclusion drawn — not the full numeric trail.

Practical consequence for the design: the entity is a thin, structured workpaper that lives alongside `Engagement` / `FollowUpItem` / `ToolRun`. Tool engines stay zero-storage. The CPA's act of capturing a snapshot ("this AJE was passed, going onto the SUM") is the same physical motion they make with paper workpapers today.

---

## Sub-sprint specifications

Each sub-sprint is one PR, one atomic commit, with its own verification gate (pytest + npm build/test where relevant).

### 728a — Backend core for ISA 520 expectations
**Complexity:** Medium · **Estimated diff:** ~700–900 LoC · **Tests added:** ~25–35

**Scope:**
- New SQLAlchemy entity `AnalyticalExpectation` in `backend/engagement_model.py` (or sibling file `backend/analytical_expectations_model.py` if `engagement_model.py` is already crowded — decision at implementation time).
  - Fields: `id`, `engagement_id` (FK → `engagements.id`), `procedure_target_type` (enum: `ACCOUNT`, `BALANCE`, `RATIO`, `FLUX_LINE`), `procedure_target_label` (str), `expected_value` (Numeric 19,2, nullable), `expected_range_low` / `expected_range_high` (Numeric 19,2, nullable), `precision_threshold_amount` (Numeric, nullable) / `precision_threshold_percent` (Float, nullable — XOR validation), `corroboration_basis_text` (Text), `corroboration_tags` (JSON: list of `INDUSTRY_DATA` / `PRIOR_PERIOD` / `BUDGET` / `REGRESSION_MODEL` / `OTHER`), `cpa_notes` (Text, nullable), `result_actual_value` (Numeric, nullable), `result_variance_amount` (Numeric, nullable), `result_status` (enum: `WITHIN_THRESHOLD`, `EXCEEDS_THRESHOLD`, `NOT_EVALUATED`), `created_at`, `created_by` (FK → `users.id`), `updated_at`, `updated_by` (FK → `users.id`), `SoftDeleteMixin`.
- Alembic migration in `backend/migrations/alembic/versions/` following the existing `{rev_id}_{slug}.py` convention — slug `add_analytical_expectations_table`.
- CRUD route module `backend/routes/analytical_expectations.py` (auth: `require_current_user`, rate-limited via existing `RATE_LIMIT_AUTH` family or the engagement-scoped equivalent):
  - `GET /engagements/{id}/analytical-expectations` — list
  - `GET /engagements/{id}/analytical-expectations/{exp_id}` — fetch
  - `POST /engagements/{id}/analytical-expectations` — create
  - `PATCH /engagements/{id}/analytical-expectations/{exp_id}` — update (CPA capture of result_actual_value happens here too, but Sprint 728c will tighten this with tool wiring)
  - `DELETE /engagements/{id}/analytical-expectations/{exp_id}` — soft-delete via SoftDeleteMixin
- Memo generator `backend/analytical_expectation_memo_generator.py` — class with `generate_pdf(user_id, engagement_id, resolved_framework=ResolvedFramework.FASB) -> bytes`, mirroring `AnomalySummaryGenerator`. Output sections: cover, ISA 520 §A1–A8 reference, expectation table (target, expected, threshold, basis tags, result, variance, status, conclusion), CPA notes appendix.
- Export route in `backend/routes/engagements_exports.py`: `POST /engagements/{id}/export/analytical-expectations`, `require_verified_user`, `check_export_access`, `apply_pdf_branding`, `StreamingResponse`.
- Completion-gate update in `backend/engagement_manager.py` `update_engagement` (around line 269): if engagement has any non-archived `AnalyticalExpectation` rows with `result_status == NOT_EVALUATED`, block completion with a clear error message. The gate is **conditional** — engagements that did no analytical procedures stay un-gated.
- Documentation: `docs/04-compliance/isa-520-coverage.md` (new file) — methodology coverage statement, links to memo generator, schema reference.
- Tests:
  - `backend/tests/test_analytical_expectations_model.py` — entity defaults, soft-delete behavior, XOR threshold validation
  - `backend/tests/test_analytical_expectations_routes.py` — CRUD route happy-path + auth + ownership boundary
  - `backend/tests/test_analytical_expectations_memo.py` — PDF render against a fixture (asserts known section headings present, PDF byte signature)
  - `backend/tests/test_engagement_completion_with_expectations.py` — completion-gate adds + skips conditional check correctly
  - `backend/tests/test_engagement_export_analytical_expectations.py` — export route + branding + 404 path
- Verification gate: `pytest backend/tests/test_analytical_expectations_*.py backend/tests/test_engagement_completion*.py` clean; full suite still green; Alembic upgrade + downgrade exercised in CI.

**Risk register:**
- *Migration on Neon*: this is the first new engagement-scoped table since Sprint 692-era work — verify migration pattern matches what Render's auto-deploy will execute on `main` merge. Mitigation: CI runs the migration upgrade before tests.
- *Materiality coupling*: Sprint 728's "precision threshold" is *not* the same as engagement materiality (CPA judgment per procedure). Avoid wiring it to `engagement.materiality_amount`. Test asserts independence.

---

### 729a — Backend core for ISA 450 SUM schedule
**Complexity:** Medium · **Estimated diff:** ~800–1000 LoC · **Tests added:** ~30–40

**Scope:**
- New SQLAlchemy entity `UncorrectedMisstatement` in same module choice as 728a's entity.
  - Fields: `id`, `engagement_id` (FK), `source_type` (enum: `ADJUSTING_ENTRY_PASSED`, `SAMPLE_PROJECTION`, `KNOWN_ERROR`), `source_reference` (Text — free-form description of the AJE, sample, or known error), `description` (Text), `accounts_affected` (JSON: list of `{account: str, debit_credit: "DR"|"CR", amount: Decimal}`), `classification` (enum: `FACTUAL`, `JUDGMENTAL`, `PROJECTED`), `fs_impact_net_income` (Numeric 19,2 — signed), `fs_impact_net_assets` (Numeric 19,2 — signed), `cpa_disposition` (enum: `AUDITOR_PROPOSES_CORRECTION`, `AUDITOR_ACCEPTS_AS_IMMATERIAL`, `NOT_YET_REVIEWED`), `cpa_notes` (Text, nullable), `created_at` / `created_by` / `updated_at` / `updated_by`, `SoftDeleteMixin`.
- Alembic migration `add_uncorrected_misstatements_table`.
- CRUD route module `backend/routes/uncorrected_misstatements.py` (same auth pattern as 728a).
- **Aggregation endpoint** `GET /engagements/{id}/sum-schedule`: returns the full SUM payload — list of misstatements, computed aggregates (factual + judgmental as one line, projected separately per ISA 450 §A4), and the materiality bucket. Bucket logic:
  - If `|aggregate| ≤ trivial_threshold` → `CLEARLY_TRIVIAL`
  - Else if `|aggregate| ≤ performance_materiality` → `IMMATERIAL`
  - Else if `|aggregate| ≤ overall_materiality` → `APPROACHING_MATERIAL`
  - Else → `MATERIAL`
- Memo generator `backend/sum_schedule_memo_generator.py`. Output sections: cover, ISA 450 §A14–A23 reference, SUM table grouped by classification, aggregate computation, materiality comparison, CPA disposition column, sign-off line.
- Export route in `engagements_exports.py`: `POST /engagements/{id}/export/sum-schedule`.
- Completion-gate update: blocks completion if any `UncorrectedMisstatement` has `cpa_disposition == NOT_YET_REVIEWED`. **Additionally**: if aggregate exceeds `overall_materiality` AND no entry has `cpa_notes` documenting an override rationale, block with a "MATERIAL aggregate requires documented override" message. (Override path is by design — auditors must affirmatively decide; we don't auto-pass nor auto-block.)
- Documentation: `docs/04-compliance/isa-450-coverage.md`.
- Tests: parallel to 728a's structure plus dedicated bucket-boundary parametrized tests (4 buckets × signed positive/negative aggregate).

**Risk register:**
- *Materiality bucket boundary semantics*: ISA 450 doesn't prescribe exact bucket names; we're using "approaching material" as a UX bucket between performance materiality and overall materiality. Document this in the ISA 450 coverage doc so it's defensible against a peer-review challenge.
- *Sign convention for FS impact*: net-income and net-assets are signed; the bucket compares against `|aggregate|`. Test parametrizes positive and negative.

---

### 728b — Frontend for analytical expectations
**Complexity:** Medium · **Estimated diff:** ~500–700 LoC · **Tests added:** ~15–20

**Scope:**
- New section on engagement page (`frontend/src/app/engagements/[id]/...`): "Analytical Expectations" collapsible card following the existing Section/Card pattern.
- Form: create/edit modal with target type, target label, expected value/range, precision threshold (amount XOR percent), corroboration tags (multi-select), basis text, CPA notes.
- Hook `frontend/src/hooks/useAnalyticalExpectations.ts` mirroring existing engagement-data hooks.
- Types `frontend/src/types/analytical-expectations.ts`.
- "Download workpaper" button triggers the export route.
- Oat & Obsidian tokens enforced (per design mandate); financial numbers `font-mono`; headers `font-serif`.
- Tests: hook fetch/mutate, form validation, list rendering, button disabled state when expectations are unevaluated.

**Risk register:**
- *XOR validation in form*: precision threshold amount XOR percent is awkward UX. Prototype in form first; if confusing, simplify by picking one default + a toggle.

---

### 729b — Frontend for SUM schedule
**Complexity:** Medium · **Estimated diff:** ~600–800 LoC · **Tests added:** ~20–25

**Scope:**
- New "Summary of Uncorrected Misstatements" section on engagement page.
- Manual capture form with three source-type variants (passed AJE / sample projection / known error) — form fields adapt to source type.
- Materiality bucket UI: prominent display showing `aggregate / overall_materiality` ratio with bucket label (color-coded — but using Oat & Obsidian tokens: `sage` for trivial/immaterial, `clay` for material/approaching).
- Disposition controls: per-row dropdown to set `cpa_disposition`.
- "Download SUM schedule" button.
- Tests: bucket boundary rendering across 4 cases + boundary edges, form variant switching, disposition mutation flow.

**Risk register:**
- *Bucket color semantics*: per Design Mandate, success = `sage`, error = `clay`. "Approaching material" lands in a yellow zone that doesn't have a token. Resolution: use `clay` with reduced opacity (treat as "warning that's not yet error"), document choice in design notes.

---

### 728c — Tool wiring for analytical expectations
**Complexity:** Medium-High · **Estimated diff:** ~400–600 LoC · **Tests added:** ~25–30

**Scope:**
- Flux engine (`backend/flux_engine.py`): accept optional `expectations: list[AnalyticalExpectationInput]` parameter; for each flux line that matches a target_label, compute variance against the expectation, return result inline in the response payload.
- Ratio engine (`backend/industry_ratios.py` or sibling): same pattern keyed by ratio name.
- Multi-period TB engine (whichever module — locate at sprint start; Explore reported the engine file location was unclear): same pattern keyed by account.
- Backend wiring: when a tool route is invoked with `engagement_id`, server-side fetches matching `AnalyticalExpectation` rows where `result_status == NOT_EVALUATED`, supplies them to the engine, and on response **persists the result back** to the entity (`result_actual_value`, `result_variance_amount`, `result_status`).
- Frontend: tool result pages display "Satisfied expectation #N: variance $X (within / exceeds threshold)" inline with the existing tool output.
- New tests:
  - Per engine: expectation matched → variance computed → result persisted
  - Engagement context absent → engine behavior unchanged (zero-storage path preserved)
  - Variance computation parametrized over (amount threshold, percent threshold, range, signed values)

**Risk register:**
- *Engine entry-point variability*: the three engines may not have a uniform input/output shape. Likely action: define a small `ExpectationEvaluator` helper in `backend/shared/expectation_evaluation.py` that the engines all call. Avoids leaking the entity into engine-internal types.
- *Concurrent run semantics*: if the same expectation is matched by multiple tool runs, last-write-wins is fine for v1 — document this. A future sprint could add a "history" table if needed.
- *Auth on the persist step*: the engine writes to the entity on behalf of the route's user. Use `created_by` of the original expectation as the `updated_by` floor (never escalate ownership).

---

### 729c — Capture helpers on AJE + sampling tools
**Complexity:** Low · **Estimated diff:** ~150–300 LoC · **Tests added:** ~10

**Scope:**
- AJE workflow (`backend/adjusting_entries.py` + frontend AJE components): "Mark as passed → add to SUM" button. Pre-fills the SUM capture form with the AJE's accounts, amounts, and a structured `source_reference`.
- Sampling tool (`backend/sampling_engine.py` + frontend): when UEL exceeds tolerable misstatement, prompt with "Capture as projected misstatement" CTA → pre-fills the SUM form with `source_type=SAMPLE_PROJECTION`, `classification=PROJECTED`, and the projected amount.
- Tests: pre-fill payload correctness, navigation flow.

---

## Execution order, gates, and check-in cadence

| Step | Sub-sprint | Verification gate | Check-in with CEO |
|---|---|---|---|
| 1 | 728a | pytest + Alembic up/down + lint | ✅ post-commit summary, before 729a starts |
| 2 | 729a | pytest + Alembic up/down + lint | ✅ post-commit summary, before 728b starts |
| 3 | 728b | npm build + npm test + visual smoke in browser | ✅ post-commit summary, before 729b starts |
| 4 | 729b | npm build + npm test + visual smoke in browser | ✅ post-commit summary, before 728c starts |
| 5 | 728c | full backend pytest + frontend tests + manual tool exercise on a fixture engagement | ✅ post-commit summary, before 729c starts |
| 6 | 729c | full backend pytest + frontend tests + AJE/sampling smoke | ✅ closing report — both sprints DONE |

After each sub-sprint commit, I report:
1. The commit SHA
2. Tests added (delta vs. baseline)
3. Any deviations from this plan and why
4. The next sub-sprint's first action

The CEO can redirect at any check-in. If a sub-sprint's actual scope diverges materially from the plan, I pause and re-plan rather than push through.

---

## Out of scope (explicitly deferred)

- **Materiality recompute history** — Sprint 729 reads the engagement's *current* materiality. If the CPA changes materiality mid-engagement, existing SUM rows don't recompute their bucket. Acceptable for v1; a `materiality_snapshot_at` field can be added later if peer review demands it.
- **Multi-currency handling on FS impact** — assumes engagement currency. Sprint 699's multi-currency side-car remains the only currency-handling path.
- **PDF Sprint-679 branding edge cases** — same `apply_pdf_branding` path as existing memos; if the branding context fails, memo generation falls through with no branding (consistent with current memos).
- **ISA 530 sample-size impact on SUM materiality** — projected misstatements interact with sample size in subtle ways; we record `classification=PROJECTED` and let the CPA reason about it. A future Sprint could surface this in the bucket logic.

---

## Test-count expectations

Baseline (per memory): 7,363 backend + 1,751 frontend.
After all six sub-sprints land:
- Backend: ~7,488 → ~7,498 (≈+125–135 tests)
- Frontend: ~1,816 → ~1,826 (≈+65–75 tests)

Numbers will be exact in each sub-sprint's commit message.

---

## Approval needed

CEO sign-off on this plan unblocks 728a immediately. If any sub-sprint specification needs revision, please call it out before approval — once approved, deviations require an explicit pause-and-re-plan check-in.
