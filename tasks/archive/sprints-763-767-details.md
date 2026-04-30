# Sprints 763–767 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-30.

---

### Sprint 763: RPT-10 finish — bank-rec materiality emission + Decimal-typed config
**Status:** COMPLETE — 2026-04-30.
**Priority:** P1. Closes the actual remaining RPT-10 gap after the route already accepts overrides at `routes/bank_reconciliation.py:56–90`.
**Source:** Financial Calculation Correctness audit B; discovery pass confirmed `BankRecConfig.materiality` / `performance_materiality` are still float-typed and the response does not surface which thresholds were active.

**Complexity:** 3/5. Touches the engine config, the runner signature, and the response schema; tests need an override-vs-default pair plus a Decimal-precision boundary case.

**What lands:**
- `BankRecConfig` monetary fields → `Decimal` (`materiality`, `performance_materiality`, `amount_tolerance`). `__post_init__` coerces float/int/str inputs via `safe_decimal` for backward compatibility with existing route plumbing.
- Engine emits `active_thresholds = {"materiality": ..., "performance_materiality": ..., "amount_tolerance": ..., "materiality_source": "caller"|"default"}` in the reconciliation result. Mirrors the `MovementSummary.active_thresholds` pattern from RPT-02.
- Route layer tags `materiality_source = "caller"` when either field is supplied on the request, `"default"` otherwise.
- Tests: caller-supplied override propagates; absent fields default to documented values + `materiality_source == "default"`; Decimal-precision boundary at the `materiality` comparison boundary (e.g., $50,000.00 vs $49,999.99 vs $50,000.01); large-engagement scale (>$1B materiality) round-trips through the response without precision loss.
- Docs: `docs/04-compliance/` cross-reference unchanged; the bank-rec route OpenAPI snapshot regenerated with the new response field.

**Out of scope:**
- Full Decimal port of `bank_reconciliation.py` engine internals (all `BankTransaction.amount` / `LedgerTransaction.amount` etc.) — that is Sprint 766.
- Adding new materiality cascade hooks — caller can already wire engagement materiality at the route layer.

**Verification:**
- `pytest backend/tests/test_recon_engine.py backend/tests/test_bank_rec_split_and_jes.py backend/tests/test_bank_rec_memo.py -v` clean.
- New tests `backend/tests/test_bank_rec_materiality.py` cover the matrix above; ≥4 added cases.
- `npm run build` (frontend) clean if the new field is consumed by the UI; otherwise unchanged.
- `scripts/openapi-snapshot.json` regenerated to absorb the response-schema delta.

**Review:**
- Landed: `BankRecConfig` Decimal-typed with `safe_decimal`-coerced `__post_init__` (rejects negative thresholds explicitly); `_test_high_value_transactions`, `run_reconciliation_tests`, `compute_bank_rec_diagnostic_score` now Decimal-typed at the boundary; `BankRecResult.active_thresholds` populated by `reconcile_bank_statement` from config + `materiality_source` arg; route layer tags `materiality_source = "caller"` only when an override was supplied.
- Tests: 22 new in `test_bank_rec_materiality.py` (config coercion + validation, active_thresholds emission, materiality boundary at $50k ± 1¢, large-engagement scale, Decimal-arithmetic precision at boundary, diagnostic-score boundary). 125 existing bank-rec tests + 269 cross-cutting tests all green.
- OpenAPI snapshot regenerated: paths 220 / schemas 422 (unchanged); `active_thresholds` field added to `BankRecResponse`.
- Frontend impact: none (UI does not yet consume `active_thresholds`; non-breaking additive field).


---

### Sprint 764: Intercompany layered detection (metadata + heuristic + confidence)
**Status:** COMPLETE — 2026-04-30. Metadata-source decision: **(iii) cascade** (request override → engagement default → none).
**Priority:** P2. Real defect: `audit/rules/relationships.py` is 100% heuristic separator-parsing with no metadata path and no explainability on findings.
**Source:** Financial Calculation Correctness audit E; discovery confirmed `_extract_counterparty()` is delimiter-based with no override path.

**Complexity:** 4/5. Adds a new schema surface, a confidence-scored detection layer, and explainability fields on findings.

**What lands:**
- `Engagement.intercompany_counterparties` (Text-typed JSON-encoded mapping) added to `engagement_model.py`; serialized in `to_dict`. Same Text+JSON pattern as `ToolRun.flagged_accounts` for SQLite/Postgres portability.
- Alembic migration `b5c6d7e8f9a0_add_intercompany_counterparties_to_engagements.py` — additive nullable column; downgrade drops it.
- New `shared/intercompany_resolver.py` — `resolve_counterparty_mapping(request_mapping, engagement_id, db)` returns `(mapping, source)` with cascade precedence: request → engagement → none. Mirrors `shared/materiality_resolver.py` shape.
- `audit/rules/relationships.py::detect_intercompany_imbalances` accepts `counterparty_mapping` + `mapping_source` kwargs. Layered detection: metadata-exact (confidence 1.0) → heuristic_separator (0.85) → heuristic_keyword (0.65). Findings carry `detection_method` and `mapping_source`.
- `StreamingAuditor.detect_intercompany_imbalances` forwards both kwargs through. Default values preserve legacy callers.
- Metadata lookup tries multiple key shapes (`display.lower()`, `account_key.lower()`, bare `provided_name.lower()`) so auditors can populate the mapping with the bare provided name without worrying about the em-dash join in `build_display_name`.

**Verification:**
- New tests `backend/tests/test_intercompany_layered_detection.py` (18 tests): resolver cascade matrix, `detection_method_label` classifier, layered detection paths, backward-compat for legacy callers, `Engagement.to_dict` round-trip.
- Legacy intercompany tests (`test_contra_and_detection_fixes.py`, anomaly framework) all pass — 82/82 — confirming no regression to the heuristic path.
- `test_alembic_models_parity.py` clean — Alembic catches up to the model.

**Out of scope:**
- ML-based name similarity (semantic embeddings). Keep within deterministic primitives.
- Wiring the resolver from the TB diagnostic route — the engine accepts the kwargs, but the route plumbing to call `resolve_counterparty_mapping()` from the request body is a follow-up sprint. Defaults preserve current behavior until the route is wired.
- Frontend UI for managing the engagement mapping — separate sprint when product wants the auditor surface.


---

### Sprint 765: variance_basis declarative field on multi-period + prior-period responses
**Status:** COMPLETE — 2026-04-30.
**Priority:** P2. Closes the audit's variance-policy ambiguity without a formula change (basis is already `abs(prior)` everywhere — gap is purely declarative).
**Source:** Financial Calculation Correctness audit D; discovery confirmed `prior_period_comparison.py:189–224` and `multi_period_comparison.py` already use `abs(prior)` consistently.

**Complexity:** 2/5. Pure schema/contract addition; no math changes.

**What lands:**
- `MovementSummary` and `PeriodComparison` (and three-way variant) emit `variance_basis: "absolute_prior"` plus a `variance_formula: "(current - prior) / abs(prior) * 100"` doc string.
- New page `docs/04-compliance/variance-formula-policy.md` documenting the chosen basis, rationale, near-zero guard (`NEAR_ZERO = 0.005`), and division-by-zero handling.
- Contract test in `backend/tests/test_variance_basis_contract.py` that asserts every variance-emitting endpoint surfaces `variance_basis` and that the value matches the actual computation.

**Out of scope:**
- Switching the basis itself — production semantics unchanged.


---

### Sprint 766: bank_reconciliation.py full Decimal port + helper consolidation
**Status:** COMPLETE — 2026-04-30.
**Priority:** P2. Hardens the actual remaining float-heavy outlier flagged in the audit's section C.
**Source:** Financial Calculation Correctness audit C; discovery confirmed bank-rec stores all amounts as float and `three_way_match_engine.py` defines its own `MONETARY_EPSILON` rather than importing from `shared/monetary.py`.

**Complexity:** 4/5. Touches every monetary path through bank-rec; risk of subtle parity drift on existing test fixtures.

**What lands:**
- `BankTransaction.amount`, `LedgerTransaction.amount`, all summary aggregates → `Decimal` with `safe_decimal` coercion in `__post_init__`.
- Comparison surfaces (variance bands, materiality gates, tolerance checks) all in Decimal space.
- `three_way_match_engine.MONETARY_EPSILON` removed; module imports `BALANCE_TOLERANCE` from `shared/monetary.py` instead.
- Output serialization quantized to 2dp via `quantize_monetary` at the response boundary (preserves existing JSON shape — Decimal is rendered to fixed-precision string or float per existing schema convention).
- Regression tests: parity with existing fixtures (penny-perfect on every prior-recon output); new precision tests at $0.01 / $0.005 / $1T+ scale.

**Out of scope:**
- Reworking the matching algorithm itself.
- DB-schema changes (none required — bank-rec is stateless / zero-storage).


---

### Sprint 767: multi_period output-boundary quantization
**Status:** COMPLETE — 2026-04-30.
**Priority:** P3. Tightens the float→Decimal→float round-trip flagged in audit section C.
**Source:** Financial Calculation Correctness audit C; discovery confirmed `compare_trial_balances()` uses `Decimal` internally then casts back to `float` at the boundary, losing the precision discipline.

**Complexity:** 2/5. Output-boundary surgery; no decision-logic change.

**What lands:**
- `AccountMovement` / `LeadSheetMovementSummary` / `MovementSummary` monetary fields on `to_dict()` go through `quantize_monetary` rather than raw `float()`.
- Decision-path comparisons (significance classification, sign-change detection) stay in Decimal until the final `to_dict()` boundary.
- Tests: `0.005`-boundary quantization (HALF_UP), penny-precision parity with existing fixtures.

**Out of scope:**
- Changing the response field types from numeric to string — keep wire compat.


---

