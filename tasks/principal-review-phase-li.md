# Principal-Level Review — Phase LI Controls

**Date:** 2026-02-21 | **Reviewer:** IntegratorLead (Agent Council) | **Scope:** Sprints 378-380

---

## Executive Summary

**Residual Risk Rating: LOW**

All 6 criteria pass with zero exceptions. The control environment is enforced at three layers: static analysis (CI gate), runtime guards (ORM hooks), and regression tests (68 dedicated tests). No bypass mechanisms exist for any control. No open issues.

---

## Criteria Assessment

| # | Criterion | Verdict | Evidence |
|---|---|:---:|---|
| 1 | No unresolved high-severity control gaps | **PASS** | 5/5 guard rules pass; 45/45 CO integration tests pass; 23/23 guard unit tests pass. All runs completed in <1s. |
| 2 | CI financial integrity guard enabled and passing | **PASS** | `accounting-policy` job at `ci.yml:200` — active, no `continue-on-error`. Guard output: `ALL 5 RULES PASSED`. Job is blocking (merge-gated). |
| 3 | No mutable audit-history deletion path remains | **PASS** | All `db.delete()` calls in production code target non-protected models only (RefreshToken, EmailVerificationToken, Client, ToolSession). 5 protected models (ActivityLog, DiagnosticSummary, ToolRun, FollowUpItem, FollowUpItemComment) guarded by ORM `before_flush` listener in both `main.py:77` and `conftest.py:77`. All "delete" routes use `soft_delete()` or `soft_delete_bulk()`. No raw SQL DELETE on protected tables. 8/8 immutability tests pass on re-run. |
| 4 | No official output path can include unapproved adjustments | **PASS** | `apply_adjustments(mode="official")` initializes `valid_statuses = {APPROVED, POSTED}` only. PROPOSED added exclusively inside `if is_simulation:` block (`adjusting_entries.py:589-590`). POSTED maps to `set()` (terminal, line 50). Route schema enforces `mode: Literal["official", "simulation"]` with default `"official"`. Response always tagged with `is_simulation` flag. Approval gate at `routes/adjustments.py:309-313` blocks posting without prior approval. Only 1 route imports `apply_adjustments()`. AST guard verifies both invariants at CI time. |
| 5 | Revenue module has explicit handling for missing ASC 606/IFRS 15 evidence fields | **PASS** | `assess_contract_evidence()` returns `level="none"` when 0 of 6 fields detected. `_run_contract_tests()` returns 4 skipped results with explicit `skip_reason="No contract data columns detected"`. Partial evidence degrades confidence (0.70 modifier). Each individual test (RT-13 through RT-16) has per-field null guards before access. Skipped tests excluded from composite score (line 2029). Zero unhandled exception paths (13 safe patterns verified). |
| 6 | Precision and roundtrip tests pass consistently | **PASS** | 9/9 `TestDecimalPersistenceRoundtrip` tests pass on both run 1 (0.38s full suite) and run 2 (0.27s isolated). DB roundtrip verified for ActivityLog + DiagnosticSummary at `Numeric(19,2)`. Debit/credit balance invariant holds post-quantization. `math.fsum` handles 10,000-item sums. Trillion-scale (`9999999999999.99`) roundtrips without overflow. |

---

## Deep-Dive Findings

### Criterion 3: Audit-History Immutability

**Scope:** Verify zero mutable deletion paths on 5 protected models.

| Check | Result |
|---|---|
| `db.delete()` on protected models in production code | **0 instances** — all calls target RefreshToken, EmailVerificationToken, Client, ToolSession |
| `.query(Model).delete()` on protected models | **0 instances** |
| Raw SQL DELETE on protected tables | **0 instances** |
| `register_deletion_guard()` in `main.py` lifespan | **Present** (line 77, 5 models registered) |
| `register_deletion_guard()` in `conftest.py` | **Present** (line 77, same 5 models) |
| ORM `before_flush` raises `AuditImmutabilityError` | **Verified** (`soft_delete.py:119-126`) |
| All delete routes use `soft_delete()` | **Verified** — `routes/activity.py:210`, `follow_up_items_manager.py:202,485` |
| Retention cleanup uses archive, not delete | **Verified** — `retention_cleanup.py:42-51,69-82` uses `.update(archived_at=...)` |
| Engagement deletion uses status archival | **Verified** — `routes/engagements.py:333-348` calls `archive_engagement()` |

### Criterion 4: Adjustment Approval Gating

**Scope:** Verify no official output includes PROPOSED adjustments.

| Check | Result |
|---|---|
| `apply_adjustments()` default mode | `"official"` (line 550) |
| Official `valid_statuses` | `{APPROVED, POSTED}` only (line 586) |
| PROPOSED addition | Conditional: `if is_simulation:` block only (line 589-590) |
| `VALID_TRANSITIONS[POSTED]` | `set()` — terminal (line 50) |
| Route schema mode type | `Literal["official", "simulation"]` (line 65) |
| Approval-before-posting gate | `routes/adjustments.py:309-313` — HTTPException if no `approved_by`/`approved_at` |
| `is_simulation` response tag | Always present in `AdjustedTrialBalance.to_dict()` (line 540) |
| Import isolation | Only `routes/adjustments.py` imports `apply_adjustments()` |
| AST guard enforcement | `guards/checkers/adjustment_gating.py` verifies both invariants at CI |
| Direct status bypass paths | **0 found** — all assignments go through `validate_status_transition()` |

### Criterion 5: Revenue ASC 606/IFRS 15 Handling

**Scope:** Verify explicit handling for missing contract evidence fields.

| Check | Result |
|---|---|
| `ContractEvidenceLevel` levels | 4 states: `full` (1.0), `partial` (0.70), `minimal` (0.50), `none` (0.0) |
| `total_contract_fields` | Hardcoded `6` (line 534) |
| 6 required fields on `RevenueEntry` | All `Optional[str]`: `contract_id`, `performance_obligation_id`, `recognition_method`, `contract_modification`, `allocation_basis`, `obligation_satisfaction_date` |
| All fields missing (`level="none"`) | 4 contract tests return `skipped=True` with `skip_reason` (lines 1588-1610) |
| Partial evidence degradation | Per-test field checks; confidence multiplied by `evidence.confidence_modifier` |
| RT-13 field guard | Checks `"obligation_satisfaction_date" in evidence.detected_fields` before access |
| RT-14 field guard | Checks `contract_id` and `performance_obligation_id` presence |
| RT-15 field guard | Requires both `contract_id` and `contract_modification` |
| RT-16 field guard | Requires both `contract_id` and `allocation_basis` |
| Unhandled exception paths | **0 found** — 13 safe patterns verified (membership checks, null guards) |
| Skipped tests in composite score | Excluded via `[r for r in results if not r.skipped]` (line 2029) |

---

## Test Execution Evidence

| Suite | Tests | Result | Time | Runs |
|---|:---:|:---:|:---:|:---:|
| Accounting Policy Guard (static) | 5 rules | ALL PASSED | <1s | 1 |
| Control Objective Integration | 45 | 45 passed | 0.38s | 1 (full) + 2 (targeted re-runs) |
| Guard Unit Tests | 23 | 23 passed | 0.72s | 1 |
| **Total verified** | **73** | **73 passed, 0 failed** | | |

### Regeneration Commands

```bash
# Full control-objective suite
cd backend && pytest tests/test_control_objective_integration.py -v

# Guard unit tests
cd backend && pytest tests/test_accounting_policy_guard.py -v

# Static analysis gate
cd backend && python -m guards.accounting_policy_guard
```

---

## Open Issues

**None.** All 6 criteria satisfied with zero exceptions, workarounds, or deferred items.

---

*Review conducted 2026-02-21. Residual risk: LOW.*
