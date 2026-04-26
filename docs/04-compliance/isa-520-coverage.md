# ISA 520 / AU-C 520 Coverage — Analytical Procedure Workpapers

**Sprint:** 728a · **Effective:** 2026-04-26 · **Owner:** Engineering

---

## Purpose

Document how Paciolus supports ISA 520 (and the AICPA equivalent AU-C 520) when an auditor uses analytical procedures as substantive evidence. The standard requires the auditor to record, for each analytical procedure, the *expectation*, the *precision threshold*, the *corroboration basis*, and the *conclusion drawn*. Before Sprint 728a the platform produced variances but had no workpaper for the auditor's expectation.

This document describes the persisted entity that closes that gap and how it relates to existing audit tools.

---

## Scope

**In scope:** ISA 520 §A4–A8 expectation formation and documentation; AU-C 520.A8–A10 precision threshold; PCAOB AS 2305 substantive analytical procedures.

**Not in scope:** ISA 315 risk assessment analytics (covered separately by the engagement risk model), ISA 540 estimates, ISA 530 sampling.

---

## Data model

| Entity | Module | Storage | Retention |
|---|---|---|---|
| `AnalyticalExpectation` | `backend/analytical_expectations_model.py` | Persisted (Postgres / SQLite) | Lifecycle of engagement; soft-delete via `SoftDeleteMixin` |

The entity holds **only** the auditor's documented expectation and the comparison result — never raw transactional data. Underlying tool outputs (flux line items, ratio inputs, multi-period TB rows) remain ephemeral per the platform's zero-storage architecture.

### Fields

| Field | Type | ISA 520 reference |
|---|---|---|
| `procedure_target_type` | enum: `ACCOUNT` / `BALANCE` / `RATIO` / `FLUX_LINE` | §A4 ("relationships among financial data") |
| `procedure_target_label` | str | §A6 ("identify the area being tested") |
| `expected_value` *or* `expected_range_low` + `expected_range_high` | Decimal | §A4 ("develop an expectation") |
| `precision_threshold_amount` *or* `precision_threshold_percent` | Decimal / float | §A8 ("acceptable difference"), AU-C §520.A11 |
| `corroboration_basis_text` | text | §A12 ("source of data used") |
| `corroboration_tags` | JSON list of `INDUSTRY_DATA` / `PRIOR_PERIOD` / `BUDGET` / `REGRESSION_MODEL` / `OTHER` | §A12–A13 |
| `cpa_notes` | text | §A18 ("auditor's response to differences") |
| `result_actual_value` | Decimal | §A8 (the platform-recorded actual) |
| `result_variance_amount` | Decimal | §A8 (computed: actual − expected, or nearest-edge for ranges) |
| `result_status` | enum: `NOT_EVALUATED` / `WITHIN_THRESHOLD` / `EXCEEDS_THRESHOLD` | §A8 ("if the difference exceeds the auditor's threshold") |

### Validation invariants

- **Expected XOR.** Either `expected_value` or both range bounds, never both, never neither.
- **Threshold XOR.** Either `precision_threshold_amount` or `precision_threshold_percent`, never both, never neither.
- **Range order.** When using a range, `expected_range_high > expected_range_low`.
- **Tags whitelist.** Only the five enum values above are accepted; unknown tags rejected.
- **Percent threshold against zero.** Rejected — the auditor must use an amount threshold when the expected reference is zero (avoids divide-by-zero "always within").

---

## API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/engagements/{id}/analytical-expectations` | Create |
| GET | `/engagements/{id}/analytical-expectations` | List (paginated, filterable by `result_status` and `target_type`) |
| GET | `/analytical-expectations/{id}` | Fetch |
| PATCH | `/analytical-expectations/{id}` | Update (capturing `result_actual_value` recomputes variance + status) |
| DELETE | `/analytical-expectations/{id}` | Soft-delete |
| POST | `/engagements/{id}/export/analytical-expectations` | Workpaper PDF (Enterprise branding applied if available) |

All CRUD routes use `require_current_user`. The export route uses `require_verified_user` and `check_export_access` (entitlement gate). Rate limits follow the existing engagement-layer conventions (`RATE_LIMIT_WRITE`, `RATE_LIMIT_EXPORT`).

---

## Engagement-completion gate

`backend/engagement_manager.py::update_engagement` blocks transition from `ACTIVE` → `COMPLETED` if the engagement has any non-archived `AnalyticalExpectation` rows with `result_status == NOT_EVALUATED`. The gate is **conditional** — engagements that did not record any analytical expectations are unaffected (mirrors how a paper engagement file omits the workpaper if the procedure wasn't performed).

The gate co-exists with the prior follow-up-item disposition gate: both must be satisfied to complete.

---

## Memo / workpaper

`backend/analytical_expectation_memo_generator.py::AnalyticalExpectationMemoGenerator.generate_pdf` produces the workpaper PDF. Sections:

1. Disclaimer banner (data analytics report — not an audit communication)
2. Cover page (client, period, reference)
3. Engagement overview (period, materiality cascade if set)
4. Expectations table grouped by target type (target, expected, threshold, basis tags, actual, variance, status)
5. Per-expectation corroboration narrative + auditor notes
6. Authoritative references (AU-C §520, ISA 520, PCAOB AS 2305, AU-C §330, ISA 320)
7. Sign-off block — DRAFT watermark when expectations remain unevaluated

The memo applies Enterprise PDF branding via `apply_pdf_branding(load_pdf_branding_context(...))` at the route layer, consistent with all engagement-export memos.

---

## Tool integration roadmap

Sprint 728a ships only the entity, routes, memo, and completion gate. The flux / ratio / multi-period TB engines are **not yet wired** to read/persist expectations — that lands in Sprint 728c. Until then, auditors capture `result_actual_value` manually via PATCH (the platform computes variance + status server-side using the same `evaluate_status` helper that the tool wiring will use).

---

## Out of scope (intentional)

- **Materiality recompute history.** A captured result's status uses the engagement's *current* threshold. If the auditor revises materiality mid-engagement, status is not retroactively recomputed for already-evaluated expectations. Recompute is an explicit action: clear the result (`PATCH` with `clear_result=true`) and re-evaluate.
- **Multi-currency.** Expected, actual, and threshold values use the engagement currency. Cross-currency comparisons are out of scope.
- **Auto-population from tools.** Per Sprint 728c.
- **Retroactive backfill.** Engagements completed before Sprint 728a do not get auto-generated expectations.
