# Sprints 715–729 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-27.

---

### Sprint 728: ISA 520 Expectation-Formation Workflow (parent — 728a/b/c)
**Status:** COMPLETE 2026-04-26 — all three sub-sprints landed atomically per the CEO-approved plan `tasks/sprint-plan-728-729.md`.
**Priority:** P3 (post-launch product gap; differentiator).
**Source:** Agent sweep 2026-04-24, punch list 4.1 + Accounting Methodology Audit.

Architecture decision (CEO-confirmed 2026-04-26): **snapshot model.** New entity holds *audit decisions* (expectation, threshold, corroboration, result, conclusion); flux / ratio / multi-period TB engines stay zero-storage. ISA 520 §A4–A8 frames this as a workpaper of decisions, not a database join.

#### Sprint 728a — Backend core
**Status:** COMPLETE 2026-04-26.
**Delivered:**
- `backend/analytical_expectations_model.py` — new `AnalyticalExpectation` entity (FK → engagements, soft-delete, JSON tag list, expected XOR range, threshold XOR percent, result status enum).
- `backend/analytical_expectations_manager.py` — CRUD manager with engagement-scoped multi-tenant ownership; pure-function `evaluate_status(actual, expected, threshold) → (variance, status)` reused later by 728c tool wiring.
- `backend/migrations/alembic/versions/f2a8e7d6c5b4_add_analytical_expectations.py` — Alembic migration; chains off prior head `e1a2b3c4d5f6`; upgrade + downgrade exercised end-to-end.
- `backend/schemas/analytical_expectation_schemas.py` — Pydantic Create/Update/Response.
- `backend/routes/analytical_expectations.py` — 5 CRUD endpoints (`POST` + `GET` list on `/engagements/{id}/analytical-expectations`, `GET` + `PATCH` + `DELETE` on `/analytical-expectations/{id}`); registered in `routes/__init__.py`.
- `backend/analytical_expectation_memo_generator.py` — ISA 520 workpaper PDF (cover, engagement overview, expectations table grouped by target type, authoritative references, sign-off block with DRAFT watermark when items remain unevaluated). Enterprise branding via `apply_pdf_branding`.
- `backend/routes/engagements_exports.py` — added `POST /engagements/{id}/export/analytical-expectations`.
- `backend/engagement_manager.py` — completion gate updated; engagements with non-archived `NOT_EVALUATED` expectations are blocked from completion (conditional — engagements with no expectations stay un-gated).
- `docs/04-compliance/isa-520-coverage.md` — methodology coverage doc.
- 6 test files, +61 tests covering model schema/defaults/soft-delete, manager CRUD/validation/`evaluate_status`, route happy-path + ownership + CSRF, memo PDF render, completion-gate matrix, export route.

**Verification:** Full backend `pytest` 8386 passed; the 4 unrelated failures in `test_security_hardening_2026_04_20.py` are pre-existing (`STRIPE_PUBLISHABLE_KEY` is `pk_test_*` while `IS_PRODUCTION=true` in dev env — clears once Sprint 447 cutover lands). Alembic upgrade head + downgrade -1 verified end-to-end against SQLite.

**Out of scope (carried to 728b/c):**
- Frontend section, capture form, hook (728b).
- Flux / ratio / multi-period TB engine wiring + auto-persist of result on tool run (728c).

#### Sprint 728b — Frontend
**Status:** COMPLETE 2026-04-26.
**Delivered:**
- `frontend/src/types/analytical-expectations.ts` — types + label/color maps mirroring backend schemas.
- `frontend/src/hooks/useAnalyticalExpectations.ts` — fetch / create / update / archive hook (paginated list).
- `frontend/src/components/engagement/AnalyticalExpectationsPanel.tsx` — full list + create modal + capture-actual inline form + re-evaluate button + archive. Form enforces XOR (value vs range, amount vs percent) with inline validation.
- `frontend/src/app/(workspace)/portfolio/[clientId]/workspace/[engagementId]/page.tsx` — added `expectations` tab between `follow-up` and `workpaper` in the workspace detail page; wires hook + panel + PDF download via `apiDownload` + `downloadBlob`.
- `frontend/src/__tests__/AnalyticalExpectationsPanel.test.tsx` — 8 component tests covering empty state, status badges, status counts, capture-actual flow, clear-result, archive, and modal open.

**Verification:** TypeScript typecheck clean (`npx tsc --noEmit`), 8 component tests passing, `npm run build` succeeds.

#### Sprint 728c — Tool wiring
**Status:** COMPLETE 2026-04-26.
**Delivered:**
- `backend/shared/expectation_evaluation.py` — `evaluate_expectations_against_measurements(...)` matches measurements (typed `[(target_type, target_label, actual)]` triples) to NOT_EVALUATED expectations on the engagement, computes variance + status via the pure `evaluate_status` from 728a, persists the result via the manager (so the audit-trail log fires consistently), and returns evaluation records the route surfaces inline. Three extractors: `extract_flux_measurements` (emits BALANCE+ACCOUNT+FLUX_LINE per item), `extract_multi_period_measurements` (BALANCE+ACCOUNT per movement), `extract_ratio_measurements` (RATIO; accepts dict or list shape).
- `backend/routes/audit_flux.py` — calls helper after `run_flux_analysis` when `engagement_id` is present; returns `expectations_evaluated` array in the response.
- `backend/routes/multi_period.py` — same wiring on `/audit/compare-periods` and `/audit/compare-three-way`.
- `backend/routes/trends.py` — `/clients/{id}/industry-ratios` now accepts optional `engagement_id` query param; auto-evaluates ratio-typed expectations when present.
- `backend/shared/diagnostic_response_schemas.py` — new `ExpectationEvaluationResponse` Pydantic model added as `expectations_evaluated: list[ExpectationEvaluationResponse] = []` to `FluxAnalysisResponse`, `MovementSummaryResponse`, `ThreeWayMovementSummaryResponse`. `IndustryRatiosResponse` (defined in `routes/trends.py`) extended similarly.
- 17 tests across 2 new files: `test_expectation_evaluation.py` (15 tests — extractors + evaluator covering match cases, case-insensitive labels, target-type mismatches, already-evaluated no-op, ownership, first-match-wins) + `test_multi_period_expectation_wiring.py` (2 tests — route emits `expectations_evaluated` when `engagement_id` is supplied; field is empty when absent).

**Verification:** Sprint 728c-targeted tests + adjacent — 45 passing.

**Pattern note:** Engines stay zero-storage. The route layer is the only place that knows about engagements + expectations. Adding wiring to a new tool = (a) accept `engagement_id` (already true for the engagement-aware tools); (b) extract measurements via the appropriate helper; (c) call `evaluate_expectations_against_measurements`; (d) embed result in the response. No engine changes required.


---

### Sprint 729: ISA 450 SUM Schedule (parent — 729a/b/c)
**Status:** COMPLETE 2026-04-26 — all three sub-sprints landed atomically per the CEO-approved plan `tasks/sprint-plan-728-729.md`.
**Priority:** P3 (post-launch product gap; differentiator).
**Source:** Agent sweep 2026-04-24, punch list 4.2 + Accounting Methodology Audit.

Architecture decision: **snapshot model.** Because `AdjustingEntry` is in-memory (zero-storage dataclass per `backend/adjusting_entries.py`) and sampling output is ephemeral, the original "auto-aggregate from passed AJEs / sample projections" plan was infeasible without breaking zero-storage. CEO confirmed 2026-04-26: SUM is a CPA-captured workpaper of decisions, with 729c capture helpers added for ergonomics.

#### Sprint 729a — Backend core
**Status:** COMPLETE 2026-04-26.
**Delivered:**
- `backend/uncorrected_misstatements_model.py` — `UncorrectedMisstatement` entity (FK → engagements CASCADE, `MisstatementSourceType` / `MisstatementClassification` / `MisstatementDisposition` enums, signed F/S impacts, `accounts_affected_json`, soft-delete).
- `backend/uncorrected_misstatements_manager.py` — CRUD manager + pure-function `compute_materiality_bucket(driver, overall, performance, trivial)` returning the four-bucket enum + `compute_sum_schedule(...)` aggregation (factual+judgmental subtotal vs projected subtotal per ISA 450 §A4 grouping; aggregate driver = `max(|net_income|, |net_assets|)`).
- `backend/migrations/alembic/versions/a3b4c5d6e7f8_add_uncorrected_misstatements.py` — chains off `f2a8e7d6c5b4`. Upgrade + downgrade verified end-to-end.
- `backend/schemas/uncorrected_misstatement_schemas.py` — Create/Update/Response/SumSchedule schemas with `AccountAffected` row.
- `backend/routes/uncorrected_misstatements.py` — 6 endpoints (CRUD + `GET /engagements/{id}/sum-schedule` aggregation); registered.
- `backend/sum_schedule_memo_generator.py` — ISA 450 workpaper PDF (cover, overview, classification-grouped tables, aggregate evaluation with bucket box colored by severity, AU-C/ISA/AS 2810 references, sign-off with DRAFT watermark for unreviewed items).
- `backend/routes/engagements_exports.py` — added `POST /engagements/{id}/export/sum-schedule`.
- `backend/engagement_manager.py` — completion gate now also requires (a) all SUM items have non-`NOT_YET_REVIEWED` disposition, (b) if aggregate is in `MATERIAL` bucket, at least one item must carry `cpa_notes` (override documentation per ISA 450 §11). Gate ordering preserved: follow-up → ISA 520 → ISA 450.
- `docs/04-compliance/isa-450-coverage.md` — coverage doc with bucket-boundary table and architectural-decision rationale.
- 6 test files, +69 tests covering schema, defaults, soft-delete, manager CRUD/validation, bucket boundaries (parametrized including signed/zero/equal-to), aggregation correctness, gate-helper functions, route happy-path + 404, memo render (empty + 3-classification + MATERIAL warning + cross-tenant), completion-gate matrix (no-items / pending / dispositioned / MATERIAL-no-override / MATERIAL-with-override / archived / 520-before-450 ordering), export route happy-path + 404.

**Verification:** Sprint 729a + memo-boundary scanner + adjacent completion-gate tests — 110 passing.

**Out of scope (carried to 729b/c):**
- Frontend SUM page + capture form (729b).
- Capture-helper buttons on AJE workflow + sampling tool (729c).

#### Sprint 729b — Frontend
**Status:** COMPLETE 2026-04-26.
**Delivered:**
- `frontend/src/types/uncorrected-misstatements.ts` — types + label maps + `BUCKET_TONE` mapping (sage / clay-soft / clay).
- `frontend/src/hooks/useUncorrectedMisstatements.ts` — fetch SUM schedule + create/update/archive (mutations re-fetch the schedule so aggregate/bucket update live).
- `frontend/src/components/engagement/SumSchedulePanel.tsx` — bucket box (color from `BUCKET_TONE`; MATERIAL warning copy when bucket is `material`), materiality cascade reference, per-row classification/source/description/F-S-impact display, disposition select, archive action, three-variant capture form with auto-classification helper (sample-projection → projected, AJE-passed → judgmental).
- Workspace detail page now exposes a `sum` tab between `expectations` and `workpaper`; wires the hook + panel + PDF download.
- `frontend/src/__tests__/SumSchedulePanel.test.tsx` — 8 component tests covering empty state, bucket-box label, MATERIAL warning, item rows, disposition mutation, archive, modal open, download disabled state.

**Verification:** TypeScript typecheck clean, 8 component tests passing, `npm run build` succeeds.

#### Sprint 729c — Capture helpers
**Status:** COMPLETE 2026-04-26.
**Delivered:**
- Refactored `frontend/src/components/engagement/SumSchedulePanel.tsx` — extracted the inline `CreateMisstatementModal` to its own file `CreateMisstatementModal.tsx` with an `initialValues` prop so it can be reused with pre-filled data. SumSchedulePanel itself shrank to ~306 LoC (was 553).
- `frontend/src/components/engagement/CaptureToSumButton.tsx` — new component that takes either `prefillFromAdjustingEntry={…}` or `prefillFromSampleProjection={…}` and opens the modal with computed initial values (largest AJE line becomes the canonical account; sample projection emits `source_type=sample_projection`, `classification=projected`, UEL → account amount). Default labels "Add to SUM" / "Capture as SUM projection" / "Capture to SUM".
- `frontend/src/components/adjustments/AdjustmentSection.tsx` + `AdjustmentList.tsx` — pass-through `engagementId` prop. When supplied and an AJE is in `rejected` (passed) status, the row renders an "Add to SUM" button next to "Re-open" / "View Details" / "Delete".
- 7 new component tests (`__tests__/CaptureToSumButton.test.tsx`) — default label, AJE label, projection label, modal pre-fill from AJE (source_reference contains reference + description), largest-line wins, sample-projection pre-fill (source_reference contains UEL).

**Out of scope (deferred):**
- Sampling-tool wiring at the route level: the sampling tool's frontend doesn't yet have a UI surface that consumes UEL > tolerable; the `CaptureToSumButton` is ready to drop in there once that surface lands. Pattern is the same as AJE wiring — pass `engagementId` + `prefillFromSampleProjection`.
- Engagement-id propagation into the AJE workflow's parent page: callers of `<AdjustmentSection />` now have an opt-in `engagementId` prop. Wiring it from a specific audit page (`/tools/...` or workspace context) is a one-line change at each call site; deferred until product wires the AJE workflow into engagement-aware pages explicitly.

**Verification:** TypeScript typecheck clean; 30 frontend tests passing across CaptureToSumButton + AdjustmentList + AdjustmentSection + SumSchedulePanel; `npm run build` succeeds.


---

### Sprint 715: SendGrid 403 root-cause investigation (24h post-deploy watch)
**Status:** COMPLETE 2026-04-26.
**Priority:** P2 (observability follow-up).
**Source:** Sprint 713 Bug C review — the fix caught the exception but did not investigate the root cause.

**Investigation outcome:** Render logs over the 48h post-deploy window (2026-04-24 14:29 UTC → 2026-04-26 21:35 UTC) contain **zero matches** for `SendGrid`, `HTTPError`, `email_error`, `Verification email`, `Background … send failed`, and **zero requests** to `/auth/register`, `/auth/forgot-password`, `/contact`. Phase 3 functional validation hasn't exercised email paths yet, so the 403 trigger condition was never met. No root cause to chase.

**Secondary finding (fixed in this sprint):** While tracing the warn-path, discovered `shared/background_email.py` was logging `"Background <label> send failed: unknown"` because it read a non-existent `result.error` attribute. `EmailResult` exposes `success`/`message`/`message_id` — the SendGrid status code lives in `result.message`. Sprint 713's existing test only asserted `len(warning_records) >= 1`, never inspected the message text, so the regression slipped through. **If a 403 had occurred in the past 48h, the log line would not have surfaced the status code** — the warn-path Sprint 713 added was effectively non-investigable.

**Fix:**
- `backend/shared/background_email.py`: read `result.message` (the canonical attribute), with `"unknown"` only as the empty-string fallback.
- `backend/tests/test_sprint_713_sentry_sweep.py::test_background_email_logs_warning_not_error_on_failure`: strengthened to assert the warning is emitted by `shared.background_email`, contains the label, contains `"403"`, and does **not** fall back to `"unknown"`. Future regressions of this shape will fail the test.

**Out of scope (deferred):**
- Proactive SendGrid suppression-list sync (no infra justification until 403 volume is meaningful).
- Email deliverability SLA tracking.
- Cleanup_scheduler `InternalError: scheduled cleanup failed` on `reset_upload_quotas` and `dunning_grace_period`, observed every ~1h during this investigation. Unrelated system, separate signal — captured as a follow-up below.

**Verification:** `pytest tests/test_sprint_713_sentry_sweep.py tests/test_email_verification.py tests/test_contact_api.py tests/test_no_helpers_reexports.py tests/test_refactor_2026_04_20.py tests/test_log_sanitizer.py` — 106 passed.

**Review:** Sprint reframed from "find the 403 root cause" to "verify there *is* a 403 to investigate, then make the warn-path actually surface the status code when one happens". Net delta: 1 LoC fix in production code, +12 LoC of test assertions that prevent the silent-failure shape from re-emerging. Commit SHA recorded at commit time.


---

