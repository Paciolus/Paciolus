# Sprints 552–556 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-18.

---

### Sprint 552 — AUDIT-01 Calculation Correctness Fixes
**Status:** COMPLETE
**Scope:** 5 confirmed defects from AUDIT-01 Financial Calculation Correctness review

- [x] **RPT-12 (CRITICAL):** Multi-Period duplicate normalized account overwrite — aggregate debits/credits instead of single-row overwrite
- [x] **RPT-07 (HIGH):** AR Aging `date.today()` fallback — add `as_of_date` config field, propagate through route → engine → `_compute_aging_days`
- [x] **RPT-10a (HIGH):** Bank Rec hardcoded $50k materiality — add `materiality`/`performance_materiality` to `BankRecConfig`, thread from route Form params
- [x] **RPT-10b (HIGH):** Bank Rec composite risk score missing from API — compute `composite_score` in `reconcile_bank_statement()`, serialize from `BankRecResult.to_dict()`, update `BankRecResponse` schema
- [x] **DASH-01 (HIGH):** Dashboard zero-score fallback — derive risk score from `rec_tests` when `composite_score` absent instead of hardcoding 0

**Review:**
- All 4 affected test suites pass (273 targeted + 278 broad = 551 tests verified)
- Files: `multi_period_comparison.py`, `ar_aging_engine.py`, `routes/ar_aging.py`, `bank_reconciliation.py`, `routes/bank_reconciliation.py`, `engagement_dashboard_engine.py`, `shared/testing_response_schemas.py`

---

