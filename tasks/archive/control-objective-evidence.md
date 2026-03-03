# Control Objective Implementation Evidence

**Project:** Paciolus — Professional Audit Intelligence Platform
**Phase:** LI (Sprints 378-379) — Accounting-Control Policy Gate
**Date:** 2026-02-21
**Version:** 2.1.0
**Prepared By:** IntegratorLead (Agent Council)

> This document provides auditor-ready evidence for 5 control objectives enforced through automated tests and CI gates. It maps each finding to its technical control, test proof, and monitoring signal.

---

## 1. Control Narratives

| # | Control Objective | Owner | Frequency | Evidence Artifact |
|---|---|---|---|---|
| CO-1 | Revenue recognition timing must respect ASC 606/IFRS 15 contract satisfaction dates; contract fields must be retained | `revenue_testing_engine.py` + `guards/checkers/contract_fields.py` | Every CI run (push/PR to `main`) + every revenue upload | `test_control_objective_integration.py::TestRevenueContractRecognitionTiming` (9 tests) + `test_accounting_policy_guard.py::TestContractFields` (4 tests) |
| CO-2 | Adjusting entries must follow PROPOSED->APPROVED->POSTED workflow; POSTED is terminal; SoD between preparer and approver must be detectable | `adjusting_entries.py` + `guards/checkers/adjustment_gating.py` | Every CI run + every adjustment status change | `test_control_objective_integration.py::TestAdjustmentApprovalWorkflowSoD` (11 tests) + `test_accounting_policy_guard.py::TestAdjustmentGating` (4 tests) |
| CO-3 | Audit trail records (5 protected models) must never be hard-deleted; only soft-delete (archive) is permitted | `shared/soft_delete.py` + `guards/checkers/hard_delete.py` | Every CI run + ORM `before_flush` event (runtime) | `test_control_objective_integration.py::TestAuditHistoryWipeBlocked` (8 tests) + `test_accounting_policy_guard.py::TestHardDelete` (5 tests) |
| CO-4 | IFRS-reported ratios compared against GAAP-sourced benchmarks must carry `framework_note` metadata for comparability disclosure | `benchmark_engine.py` + `guards/checkers/framework_metadata.py` | Every CI run + every benchmark comparison | `test_control_objective_integration.py::TestIFRSBenchmarkComparability` (8 tests) + `test_accounting_policy_guard.py::TestFrameworkMetadata` (4 tests) |
| CO-5 | All monetary values must survive DB roundtrip at Decimal precision (Numeric(19,2), ROUND_HALF_UP); debit/credit balance must hold post-quantization | `shared/monetary.py` + `guards/checkers/monetary_float.py` | Every CI run + every DB write boundary | `test_control_objective_integration.py::TestDecimalPersistenceRoundtrip` (9 tests) + `test_accounting_policy_guard.py::TestMonetaryFloat` (5 tests) |

---

## 2. Exception Handling Procedure

### 2.1 Detection

| Layer | Mechanism | Response |
|---|---|---|
| **CI Gate (pre-merge)** | `accounting-policy` job in `.github/workflows/ci.yml` runs `python -m guards.accounting_policy_guard`; exit 1 = violation | PR blocked from merge; `::error` annotations point to exact file:line |
| **Runtime Guard (in-process)** | `register_deletion_guard()` ORM `before_flush` listener raises `AuditImmutabilityError` | Transaction rolled back; deletion physically prevented |
| **Test Suite (regression)** | 45 control-objective tests + 23 guard tests in `pytest` | CI `backend-tests` job fails; PR blocked |

### 2.2 Review and Escalation

| Step | Responsible Party | Timeline | Action |
|---|---|---|---|
| 1. CI failure notification | GitHub Actions | Immediate (on push/PR) | Automated email/notification to PR author |
| 2. Root cause triage | PR Author | Within 1 business day | Identify which control objective violated; document in PR comments |
| 3. Remediation | PR Author + Reviewer | Within 2 business days | Fix violation at source; re-run CI; confirm green |
| 4. Exception review (if bypass needed) | CEO (Project Owner) | Before any bypass | Explicit written approval required in PR comment; document rationale |
| 5. Post-incident lesson | IntegratorLead | On merge | Add entry to `tasks/lessons.md` if pattern is novel |

### 2.3 Sign-Off Protocol

- **No bypass mechanism exists in CI.** The `accounting-policy` job has no `continue-on-error: true` flag.
- **Guard rules cannot be disabled at runtime.** The ORM deletion guard is registered at app startup (`main.py` lifespan) and in test fixtures (`conftest.py`).
- **Policy config changes** (`guards/accounting_policy.toml`) are version-controlled and subject to the same PR review process.
- **Exception:** Adding a column to `float_allowlist` in TOML requires explicit justification (ratio/percentage columns only, never monetary).

---

## 3. Release Checklist — High-Risk Finding to Control Mapping

| # | High-Risk Finding | Technical Control | Test Proof | Monitoring Signal |
|---|---|---|---|---|
| F-1 | Float used for monetary column in ORM model | `guards/checkers/monetary_float.py` — AST walker scans `models.py`, `engagement_model.py`, `subscription_model.py` for `Column(Float)` on protected classes outside `float_allowlist` | `TestMonetaryFloat` (5 tests): float flagged, ratio passes, Numeric passes, non-protected ignored, multiple violations detected | CI job `accounting-policy` exit code; `::error file=models.py,line=N` annotation |
| F-2 | `db.delete()` called on audit-protected model | `guards/checkers/hard_delete.py` — regex scanner in all `.py` files (excluding `tests/`, `shared/soft_delete.py`) for `db.delete()` importing protected models | `TestHardDelete` (5 tests): db.delete flagged, non-protected passes, soft_delete passes, query.delete flagged, comments ignored | CI job `accounting-policy` + runtime `AuditImmutabilityError` on ORM flush |
| F-3 | Contract field removed from `RevenueEntry` or `RevenueColumnDetection` | `guards/checkers/contract_fields.py` — AST walker verifies 6 required fields present in 3 classes; `total_contract_fields` must equal 6 | `TestContractFields` (4 tests): all present passes, missing field flagged, wrong total flagged, missing class flagged | CI job `accounting-policy` |
| F-4 | PROPOSED status accessible in official mode; POSTED not terminal | `guards/checkers/adjustment_gating.py` — AST walker verifies `VALID_TRANSITIONS[POSTED]` maps to `set()` and PROPOSED is conditional in `apply_adjustments` | `TestAdjustmentGating` (4 tests): terminal passes, non-terminal flagged, conditional passes, unconditional flagged | CI job `accounting-policy` |
| F-5 | `framework_note` field missing from comparison dataclass | `guards/checkers/framework_metadata.py` — AST walker checks 4 target classes across 3 files for `framework_note` annotation | `TestFrameworkMetadata` (4 tests): present passes, missing flagged, class-not-found flagged, multi-class same file | CI job `accounting-policy` |
| F-6 | Premature revenue recognition (before obligation satisfaction) | `revenue_testing_engine.py` RT-13 test (`recognition_before_satisfaction`) flags entries recognized > 7 days before `obligation_satisfaction_date` | `TestRevenueContractRecognitionTiming::test_rt13_flags_premature_recognition` — 30-day gap entry produces HIGH severity flag | Revenue upload response includes `flagged_entries` with severity + entry reference |
| F-7 | Adjustment posted without approval (skip APPROVED state) | `adjusting_entries.py` `validate_status_transition()` raises `InvalidTransitionError` on PROPOSED->POSTED | `TestAdjustmentApprovalWorkflowSoD::test_skip_approval_blocked` — direct PROPOSED->POSTED raises exception | Runtime `InvalidTransitionError`; HTTP 400 in API route |
| F-8 | Hard deletion of audit trail record | `shared/soft_delete.py` `register_deletion_guard()` ORM `before_flush` listener | `TestAuditHistoryWipeBlocked` — 5 tests verify each protected model (ActivityLog, DiagnosticSummary, ToolRun, FollowUpItem, FollowUpItemComment) raises `AuditImmutabilityError` | Runtime exception; transaction rollback; row count never decreases |
| F-9 | Decimal drift after DB roundtrip | `shared/monetary.py` `quantize_monetary()` at all write boundaries; `Numeric(19,2)` column types | `TestDecimalPersistenceRoundtrip` — ActivityLog + DiagnosticSummary DB roundtrip, balance invariant, trillion-scale | Debit/credit equality assertion in `audit_engine.py` balance checks |
| F-10 | SoD violation (same user prepares and approves) | `adjusting_entries.py` stores `prepared_by` and `approved_by` on `AdjustingEntry`; equality detectable | `TestAdjustmentApprovalWorkflowSoD::test_sod_violation_detectable` — `prepared_by == approved_by` detected | Application-level check before posting; consumer responsibility to enforce |

---

## 4. Evidence Index — Regeneration Commands

All commands run from `backend/` directory.

### 4.1 Full Test Suite

```bash
# All backend tests (includes control-objective + guard tests)
cd backend && pytest tests/ -v --tb=short -q

# Control-objective integration tests only (45 tests)
cd backend && pytest tests/test_control_objective_integration.py -v

# Accounting policy guard tests only (23 tests)
cd backend && pytest tests/test_accounting_policy_guard.py -v
```

### 4.2 Accounting Policy Gate (Static Analysis)

```bash
# Run all 5 guard rules against current codebase (exit 0 = pass)
cd backend && python -m guards.accounting_policy_guard

# Expected output on clean codebase:
# [PASS] no_float_monetary — 0 violations
# [PASS] no_hard_delete — 0 violations
# [PASS] revenue_contract_fields — 0 violations
# [PASS] adjustment_gating — 0 violations
# [PASS] framework_metadata — 0 violations
# All 5 rules passed.
```

### 4.3 Frontend Build Verification

```bash
# Build + lint (no runtime tests affected by backend controls)
cd frontend && npm run build && npm run lint
```

### 4.4 CI Pipeline Evidence

```bash
# View latest CI run status
gh run list --workflow=ci.yml --limit=5

# View specific job results
gh run view <run-id> --log

# Re-trigger CI
gh workflow run ci.yml
```

### 4.5 Individual Control Objective Evidence

```bash
# CO-1: Revenue contract recognition timing
cd backend && pytest tests/test_control_objective_integration.py::TestRevenueContractRecognitionTiming -v

# CO-2: Adjustment approval workflow + SoD
cd backend && pytest tests/test_control_objective_integration.py::TestAdjustmentApprovalWorkflowSoD -v

# CO-3: Audit history immutability
cd backend && pytest tests/test_control_objective_integration.py::TestAuditHistoryWipeBlocked -v

# CO-4: IFRS benchmark comparability
cd backend && pytest tests/test_control_objective_integration.py::TestIFRSBenchmarkComparability -v

# CO-5: Decimal persistence roundtrip
cd backend && pytest tests/test_control_objective_integration.py::TestDecimalPersistenceRoundtrip -v
```

---

## 5. Traceability Map — Finding to CI Gate

```
FINDING                          FIX                                    TEST                                         CI GATE
-------------------------------  -------------------------------------  -------------------------------------------  ---------------------------
F-1 Float monetary column        Numeric(19,2) in models.py             TestMonetaryFloat (5)                        accounting-policy job
                                 quantize_monetary() at write           TestDecimalPersistenceRoundtrip (9)          backend-tests job
                                 boundaries

F-2 Hard-delete audit record     SoftDeleteMixin on 5 models            TestHardDelete (5)                           accounting-policy job
                                 register_deletion_guard() ORM hook     TestAuditHistoryWipeBlocked (8)              backend-tests job

F-3 Contract field removal       6 fields on RevenueEntry +             TestContractFields (4)                       accounting-policy job
                                 RevenueColumnDetection +               TestRevenueContractRecognitionTiming (9)     backend-tests job
                                 ContractEvidenceLevel.total=6

F-4 Adjustment gating bypass     VALID_TRANSITIONS[POSTED]=set()        TestAdjustmentGating (4)                     accounting-policy job
                                 PROPOSED conditional in official mode   TestAdjustmentApprovalWorkflowSoD (11)       backend-tests job

F-5 Missing framework_note       framework_note field on 4 classes      TestFrameworkMetadata (4)                    accounting-policy job
                                 (Benchmark, PeriodComparison,          TestIFRSBenchmarkComparability (8)            backend-tests job
                                 MovementSummary, ThreeWay)

F-6 Premature recognition        RT-13 recognition_before_satisfaction  test_rt13_flags_premature_recognition        backend-tests job
                                 in revenue_testing_engine.py           test_rt13_does_not_flag_over_time

F-7 Unapproved posting           validate_status_transition() raises    test_skip_approval_blocked                   backend-tests job
                                 InvalidTransitionError                 test_posted_is_terminal

F-8 Audit trail deletion         AuditImmutabilityError on flush        5x delete_raises tests                       backend-tests job
                                                                        test_soft_delete_preserves_record
                                                                        test_row_count_never_decreases

F-9 Decimal drift                quantize_monetary(ROUND_HALF_UP)       test_activity_log_db_roundtrip               backend-tests job
                                 Numeric(19,2) column types             test_diagnostic_summary_db_roundtrip
                                 math.fsum for large sums               test_debit_credit_balance_invariant

F-10 SoD violation               prepared_by / approved_by metadata     test_sod_violation_detectable                backend-tests job
                                 on AdjustingEntry                      test_sod_clean_path
```

---

## 6. CI Job Inventory

| Job | Purpose | Blocking | Trigger |
|---|---|---|---|
| `backend-tests` | 4,244 pytest tests (SQLite, Python 3.11 + 3.12 matrix) | Yes | push/PR to `main` |
| `backend-tests-postgres` | Dialect-aware tests against PostgreSQL 15 | Yes | push/PR to `main` |
| `frontend-build` | Next.js build + ESLint | Yes | push/PR to `main` |
| `backend-lint` | ruff check | Yes | push/PR to `main` |
| `bandit` | SAST — medium+ severity security scan | Yes | push/PR to `main` |
| `accounting-policy` | 5 AST-based accounting invariant rules | Yes | push/PR to `main` |
| `pip-audit-blocking` | Python HIGH/CRITICAL CVE scan | Yes | push/PR to `main` |
| `pip-audit-advisory` | Python all-severity CVE scan | No (advisory) | push/PR to `main` |
| `npm-audit-blocking` | Node HIGH/CRITICAL CVE scan | Yes | push/PR to `main` |
| `npm-audit-advisory` | Node all-severity CVE scan | No (advisory) | push/PR to `main` |

**Total blocking gates:** 7 of 10 jobs must pass before merge.

---

## 7. Guard Rule Configuration

**Config file:** `backend/guards/accounting_policy.toml`

| Rule | Protected Scope | Scanned Files | Violation Action |
|---|---|---|---|
| `no_float_monetary` | ActivityLog, DiagnosticSummary, Engagement, Subscription | `models.py`, `engagement_model.py`, `subscription_model.py` | `::error` annotation + exit 1 |
| `no_hard_delete` | ActivityLog, DiagnosticSummary, ToolRun, FollowUpItem, FollowUpItemComment | All `.py` (excl. `tests/`, `shared/soft_delete.py`) | `::error` annotation + exit 1 |
| `revenue_contract_fields` | RevenueEntry, RevenueColumnDetection, ContractEvidenceLevel | `revenue_testing_engine.py` | `::error` annotation + exit 1 |
| `adjustment_gating` | VALID_TRANSITIONS, apply_adjustments | `adjusting_entries.py` | `::error` annotation + exit 1 |
| `framework_metadata` | BenchmarkComparison, PeriodComparison, MovementSummary, ThreeWayMovementSummary | `benchmark_engine.py`, `prior_period_comparison.py`, `multi_period_comparison.py` | `::error` annotation + exit 1 |

---

## 8. Test Coverage Summary

| Test Suite | File | Tests | Focus |
|---|---|---|---|
| Control Objective Integration | `test_control_objective_integration.py` | 45 | 5 control objectives, deterministic fixtures, DB roundtrip |
| Accounting Policy Guard | `test_accounting_policy_guard.py` | 23 | 5 AST-based rules, fixture-driven synthetic code |
| **Total new (Phase LI)** | | **68** | |
| **Total backend** | | **4,244** | Cumulative across all phases |
| **Total frontend** | | **995** | Cumulative across all phases |

---

*Evidence document generated 2026-02-21. Regenerate via commands in Section 4.*
