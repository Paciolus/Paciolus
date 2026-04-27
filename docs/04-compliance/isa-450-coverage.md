# ISA 450 / AU-C 450 Coverage — Summary of Uncorrected Misstatements

**Sprint:** 729a · **Effective:** 2026-04-26 · **Owner:** Engineering

---

## Purpose

Document how Paciolus supports ISA 450 (and the AICPA equivalent AU-C 450) at engagement completion. The standard requires the auditor to record each misstatement identified during the audit that was not corrected, classify it (factual / judgmental / projected), evaluate the aggregate against materiality, and reach a documented disposition. Before Sprint 729a the platform had no SUM workpaper; auditors reached for one at engagement-close and found nothing.

---

## Architectural decision: snapshot model

`AdjustingEntry` is an in-memory dataclass (`backend/adjusting_entries.py`); sampling output is also ephemeral (`backend/sampling_engine.py`). The original sprint plan called for "auto-aggregation from passed AJEs and sampling UEL" but doing so would have required persisting either AJE or sampling state, breaking the platform's zero-storage invariant.

CEO-confirmed 2026-04-26: SUM is a CPA-captured workpaper of *audit decisions*. The auditor records each misstatement as they identify it (or carries forward Sprint 729c capture-helper buttons that pre-fill the form from the AJE / sampling tool when those land). Tool engines stay zero-storage; the entity holds the documented decisions.

This is consistent with how ISA 450 §A14 and AU-C 450 §A23 frame the SUM — as a workpaper, not a database join.

---

## Data model

| Entity | Module | Storage | Retention |
|---|---|---|---|
| `UncorrectedMisstatement` | `backend/uncorrected_misstatements_model.py` | Persisted (Postgres / SQLite) | Engagement lifecycle; `SoftDeleteMixin` |

### Fields

| Field | Type | ISA 450 reference |
|---|---|---|
| `source_type` | enum: `ADJUSTING_ENTRY_PASSED` / `SAMPLE_PROJECTION` / `KNOWN_ERROR` | §A4 sources |
| `source_reference` | text — narrative pointer to the AJE / sample / known-error | §A6 ("identify the misstatement") |
| `description` | text | §A6 |
| `accounts_affected` | JSON list `[{account, debit_credit: "DR"|"CR", amount}]` | §A8 |
| `classification` | enum: `FACTUAL` / `JUDGMENTAL` / `PROJECTED` | §A6 classification |
| `fs_impact_net_income` / `fs_impact_net_assets` | Decimal, signed | §A8 ("quantitative effect") |
| `cpa_disposition` | enum: `NOT_YET_REVIEWED` / `AUDITOR_PROPOSES_CORRECTION` / `AUDITOR_ACCEPTS_AS_IMMATERIAL` | §A12-A15 |
| `cpa_notes` | text — optional rationale | §A15 ("auditor's evaluation"); also serves as the override-documentation field for the MATERIAL-bucket completion gate |

### Validation invariants

- `accounts_affected` must be non-empty; each row requires `account`, `debit_credit ∈ {DR, CR}`, positive `amount`.
- `cpa_disposition` defaults to `NOT_YET_REVIEWED` on create.
- F/S impacts are signed; the bucket comparison uses `|aggregate|`.

---

## Materiality bucket (computed at read time)

`UncorrectedMisstatementsManager.compute_sum_schedule(...)` computes:

- **Subtotals** — factual + judgmental impact, projected impact (per ISA 450 §A4 grouping).
- **Aggregate** — sum of subtotals, separately for net-income and net-assets impact.
- **Driver** — `max(|agg_income|, |agg_assets|)` (worst-case across the two F/S surfaces the auditor must evaluate).
- **Bucket** — derived from the materiality cascade `EngagementManager.compute_materiality(...)` returns:

| Driver value | Bucket |
|---|---|
| `≤ trivial_threshold` | `CLEARLY_TRIVIAL` |
| `≤ performance_materiality` | `IMMATERIAL` |
| `≤ overall_materiality` | `APPROACHING_MATERIAL` |
| `> overall_materiality` | `MATERIAL` |

**"Approaching material" is the platform's UX bucket** between performance and overall materiality. ISA 450 itself does not name this band; we surface it because auditors typically watch the gap closely once misstatements pass performance materiality. The label is documented here so peer reviewers can verify the cascade math.

---

## API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/engagements/{id}/uncorrected-misstatements` | Create |
| GET | `/engagements/{id}/uncorrected-misstatements` | List (paginated, filterable by `classification`, `source_type`, `disposition`) |
| GET | `/engagements/{id}/sum-schedule` | Aggregation: items + subtotals + aggregate + materiality cascade + bucket + unreviewed count |
| GET | `/uncorrected-misstatements/{id}` | Fetch |
| PATCH | `/uncorrected-misstatements/{id}` | Update |
| DELETE | `/uncorrected-misstatements/{id}` | Soft-delete |
| POST | `/engagements/{id}/export/sum-schedule` | Workpaper PDF (Enterprise branding applied) |

Auth: CRUD uses `require_current_user`; export uses `require_verified_user` + `check_export_access`.

---

## Engagement-completion gate

`backend/engagement_manager.py::update_engagement` blocks `ACTIVE → COMPLETED` if **either** rule fails:

1. Any non-archived misstatement has `cpa_disposition == NOT_YET_REVIEWED`.
2. SUM aggregate is in `MATERIAL` bucket *and* no item carries `cpa_notes` documenting the override rationale.

Rule 2 implements ISA 450 §11: when uncorrected misstatements exceed materiality, the auditor must affirmatively decide. We don't auto-block (would force correction even when the auditor's documented judgment is "accept and communicate to TCWG") and we don't auto-pass (would violate §11). The override-required-for-MATERIAL design surfaces the choice and requires it be written down.

The gate runs **after** the existing follow-up-item disposition gate and the ISA 520 expectation gate, so the user sees the most-fundamental failure first.

---

## Memo / workpaper

`backend/sum_schedule_memo_generator.py::SumScheduleMemoGenerator.generate_pdf` produces the PDF. Sections:

1. Disclaimer banner
2. Cover page (client, period, reference)
3. Engagement overview (period + materiality cascade + unreviewed count)
4. Misstatement items grouped by classification — table per classification (Source, Description, Net Income Δ, Net Assets Δ, Disposition) + per-row reference + auditor notes block
5. Aggregate evaluation — subtotals/aggregate table + materiality bucket box (clay color when `MATERIAL` or `APPROACHING_MATERIAL`, sage otherwise; per the design-mandate constraint that "approaching material" lacks a yellow token, we use `clay` since both buckets warrant elevated attention)
6. Authoritative References (AU-C §450, ISA 450, AU-C §320, ISA 320, PCAOB AS 2810)
7. Sign-off block — DRAFT watermark when items remain unreviewed

---

## Out of scope (intentional)

- **Materiality-recompute snapshot history.** The bucket reads engagement materiality *at workpaper-generation time*. If the auditor changes materiality mid-engagement, previously-saved items don't recompute — the bucket update happens on the next aggregation read.
- **Multi-currency F/S impact.** Assumes engagement currency.
- **Auto-aggregation from AJE / sampling tools.** Manual capture in 729a; capture-helper buttons land in 729c.
- **Materiality-tier-specific bucket boundaries.** Single overall threshold drives the bucket; firms that want a custom 5-tier split can override per engagement once the tier-config sprint lands (not currently scoped).
