# Phase III Features - Quick Reference
## Failure Mode Summary for QualityGuardian Review

**Date:** 2026-02-04
**Analyst:** QualityGuardian (Failure-Mode Analyst)
**Status:** Analysis Complete, 201 Tests Defined

---

## Feature Comparison Matrix

| Aspect | Suspense Detector | Balance Sheet Validator | Concentration Risk | Rounding Anomaly | Contra-Account Validator |
|--------|:-:|:-:|:-:|:-:|:-:|
| **Complexity** | 5/10 | 6/10 | 8/10 | 7/10 | 9/10 |
| **Test Count** | 34 | 34 | 43 | 43 | 47 |
| **Risk Level** | LOW | LOW-MED | MED-HIGH | MEDIUM | HIGH |
| **Implementation Days** | 3-4 | 3-4 | 7-8 | 5-6 | 10-14 |
| **Dependencies** | None | Feat 1 | Feat 1,2,4 | Feat 1,2 | All Features |
| **Zero-Storage Risk** | HIGH | MEDIUM | HIGH | MEDIUM | HIGH |
| **Recommended Seq** | 1st | 1st (parallel) | 4th | 3rd | 5th (last) |

---

## Failure Mode Counts by Feature

### Feature 1: Suspense Account Detector
- **Total Failure Modes:** 9
- **Test Scenarios:** 26 (core, edge, unicode, materiality, multi-sheet, zero-storage, defensive)
- **Critical Risks:** 2 (unicode names, materiality blindness)
- **File:** `PHASE3_FAILURE_MODES.md` → "Feature 1"

### Feature 2: Balance Sheet Validator
- **Total Failure Modes:** 10
- **Test Scenarios:** 27 (core, missing categories, multi-sheet, materiality, floating-point, defensive)
- **Critical Risks:** 2 (floating-point precision loss, missing equity category)
- **File:** `PHASE3_FAILURE_MODES.md` → "Feature 2"

### Feature 3: Concentration Risk Detector
- **Total Failure Modes:** 10
- **Test Scenarios:** 30 (core, cardinality, materiality, industry, zero-storage, defensive)
- **Critical Risks:** 3 (single-account category, threshold customization, industry variance)
- **File:** `PHASE3_FAILURE_MODES.md` → "Feature 3"

### Feature 4: Rounding Anomaly Scanner
- **Total Failure Modes:** 10
- **Test Scenarios:** 34 (divisibility, materiality, negative balances, temporal, edge cases, defensive)
- **Critical Risks:** 2 (legitimate round numbers, tax estimation ambiguity)
- **File:** `PHASE3_FAILURE_MODES.md` → "Feature 4"

### Feature 5: Contra-Account Validator
- **Total Failure Modes:** 12
- **Test Scenarios:** 36 (matching, ratio anomalies, depreciation methods, consolidation, defensive)
- **Critical Risks:** 3 (fuzzy matching ambiguity, depreciation method variance, fully depreciated assets)
- **File:** `PHASE3_FAILURE_MODES.md` → "Feature 5"

---

## High-Risk Failure Modes (Highest Priority Tests)

### Tier 1: Critical (Must Test First)

| Feature | Failure Mode | Test ID | Mitigation |
|---------|--------------|---------|-----------|
| Suspense | Unicode account names not matched | 1.11-1.14 | Fuzzy matching + UTF-8 normalization |
| Balance Sheet | Floating-point precision loss at large scales | 2.19-2.20 | Relative tolerance formula |
| Concentration | Single-account category = 100% (false positive) | 3.10-3.12 | Cardinality note in result |
| Rounding | Legitimate round number (revenue $1M) flagged | 4.11-4.14 | Materiality filter (<0.1%) |
| Contra | Fuzzy matching "Equipment" ≠ "Equipment Rental" | 5.11-5.15 | Confidence threshold >70% |

### Tier 2: High (Test Early)

| Feature | Failure Mode | Test ID | Mitigation |
|---------|--------------|---------|-----------|
| Suspense | Empty trial balance crashes detector | 1.10 | Check len(df) > 0 before processing |
| Balance Sheet | Negative equity confuses validation | 2.4 | Allow negative equity as valid state |
| Concentration | Category total = 0 causes division error | 3.4 | Check if total != 0 before division |
| Rounding | Negative balance -$1,000 should flag | 4.15 | Use abs() for divisibility check |
| Contra | Accumulated depreciation > gross asset | 5.8 | Flag as critical (impossible state) |

### Tier 3: Medium (Test Throughout)

| Feature | Failure Mode | Test ID | Mitigation |
|---------|--------------|---------|-----------|
| Suspense | Negative balance not flagged as abnormal | 1.6 | Combine with abnormal balance detector |
| Balance Sheet | Multi-sheet consolidation unbalanced | 2.11 | Validate per-sheet + consolidated |
| Concentration | Mixed currency AR (USD + EUR) | 3.x | Document assumption: single currency |
| Rounding | Accrual $12,000 = $1K/month (legitimate) | 4.18-4.20 | Context tracking (temporal pattern) |
| Contra | Leasehold improvements vs. ROU asset | 5.13 | Separate matching rules per asset type |

---

## Zero-Storage Compliance Checklist

### Each Feature Must Satisfy

- [ ] **Account Names:** NEVER stored in database or logs
- [ ] **Account Numbers:** NEVER stored in database or logs
- [ ] **Account Balances:** NEVER stored individually (only aggregates)
- [ ] **Logging Pattern:** Use `log_secure_operation()` from security_utils.py
- [ ] **API Response:** Contains only counts, percentages, timestamps (no account identifiers)
- [ ] **Database Schema:** Verify no new columns with sensitive data
- [ ] **Test Coverage:** Dedicated test to query DB and verify no account names appear

### Template for Each Feature
```python
# CORRECT: Zero-storage compliant
log_secure_operation(
    "suspense_detector",
    f"Found {flagged_count} suspense accounts with non-zero balances"
)
# Store: { flagged_count, severity_level, timestamp }
# Do NOT store or log: account names, balances, GL codes

# WRONG: Zero-storage violation
log_secure_operation(
    "suspense_detector",
    f"Flagged: Cash - Suspense Holding ($5000), Equipment Reserve ($2000)"
)
# This stores account names - VIOLATION
```

---

## Defensive Coding Patterns (Reusable Across All Features)

### Pattern 1: Safe Numeric Conversion
```python
try:
    balance = float(account_balance)
except (ValueError, TypeError):
    log_secure_operation("detector_error", "Failed numeric conversion (name not logged)")
    continue  # Skip this account, don't crash
```

### Pattern 2: Division by Zero Guard
```python
if category_total == 0:
    return {"status": "skipped", "reason": "zero_category_total"}
# Or if computation is critical:
if category_total == 0:
    raise ValueError("Cannot validate: zero category total")
```

### Pattern 3: NaN/Infinity Detection
```python
import math
if math.isnan(balance) or math.isinf(balance):
    log_secure_operation("detector_error", "Invalid numeric value (name not logged)")
    return None
```

### Pattern 4: Floating-Point Tolerance
```python
ABSOLUTE_MIN = 0.01
RELATIVE_PERCENT = 0.0001  # 0.01%
tolerance = max(ABSOLUTE_MIN, total_assets * RELATIVE_PERCENT)
is_balanced = abs(gap) <= tolerance
```

### Pattern 5: Multi-Sheet Aggregation
```python
results_per_sheet = []
for sheet_name, sheet_df in workbook.items():
    result = validate_sheet(sheet_df)
    results_per_sheet.append({
        "sheet_name": sheet_name,
        "result": result
    })
consolidated = aggregate_results(results_per_sheet)
return {"per_sheet": results_per_sheet, "consolidated": consolidated}
```

---

## Test Fixture Requirements

All features share common fixtures in `conftest.py`:

```python
@pytest.fixture
def healthy_trial_balance():
    """Clean, balanced trial balance for baseline tests"""
    # Assets: $1M, Liabilities: $600K, Equity: $400K

@pytest.fixture
def unbalanced_trial_balance():
    """TB with $1000 imbalance for validation testing"""
    # Assets: $1M, Liabilities: $600K, Equity: $400.5K

@pytest.fixture
def unicode_trial_balance():
    """Account names in multiple languages"""
    # Japanese, Polish, mixed Unicode characters

@pytest.fixture
def empty_trial_balance():
    """No data rows (only header)"""
    # Must handle gracefully, not crash

@pytest.fixture
def single_account_tb():
    """Only one account (edge case)"""
    # Single asset = $1M, no other categories

@pytest.fixture
def large_tb_100000_rows():
    """Large file for performance/chunking tests"""
    # Tests streaming, memory management

@pytest.fixture
def multi_sheet_workbook():
    """Excel with 3+ sheets, different TB per sheet"""
    # Tests per-sheet validation + consolidation

@pytest.fixture
def negative_equity_tb():
    """Insolvent company: liabilities > assets"""
    # Assets: $1M, Liabilities: $2M, Equity: -$1M

@pytest.fixture
def fully_depreciated_tb():
    """Old asset, 100% accumulated depreciation"""
    # Equipment: $1M, A.D.: $1M (valid for old asset)

@pytest.fixture
def mixed_currency_tb():
    """USD + EUR accounts in same category"""
    # Tests currency assumption/documentation
```

---

## Implementation Checklist (Pre-Code)

Before writing ANY feature code:

### Codebase Review (2 hours)
- [ ] Read `ratio_engine.py` lines 1-150 (CategoryTotals structure)
- [ ] Read `account_classifier.py` lines 95-150 (fuzzy matching pattern)
- [ ] Read `audit_engine.py` lines 1-50 (error handling pattern)
- [ ] Read `security_utils.py` (log_secure_operation() function)

### Test Structure Setup (1 hour)
- [ ] Copy conftest.py template
- [ ] Create test_suspense_detector.py skeleton (class structure only)
- [ ] Verify pytest.ini configuration

### Database Schema Validation (1 hour)
- [ ] Review models.py DiagnosticSummary class
- [ ] Confirm no new fields needed for features
- [ ] Plan storage: Feature results in memory only, or new table?

### API Response Schema (2 hours)
- [ ] Define Pydantic model for each feature's result
- [ ] Add to main.py FastAPI endpoints (placeholder)
- [ ] Document in docstrings

### Total Pre-Code Time: ~6 hours
**Then:** Ready to write first feature

---

## Success Metrics

### By Feature
| Feature | All Tests Pass | Zero-Storage Verified | Code Review Approved |
|---------|:---:|:---:|:---:|
| Suspense | 34/34 | ✓ | ✓ |
| Balance Sheet | 34/34 | ✓ | ✓ |
| Concentration | 43/43 | ✓ | ✓ |
| Rounding | 43/43 | ✓ | ✓ |
| Contra-Account | 47/47 | ✓ | ✓ |
| **TOTAL** | **201/201** | **✓** | **✓** |

### Project Metrics
- **Test Coverage:** 232 → 433 tests (86% increase)
- **Audit Score:** 8.2 → 9.7 (1.5 point improvement)
- **Production Ready:** Phase III features fully hardened

---

## Documents & References

### Main Analysis
- **PHASE3_FAILURE_MODES.md** - Complete failure-mode analysis (5 features)
  - 76 failure modes identified
  - 201 test scenarios detailed
  - Zero-storage compliance verified
  - Defensive coding patterns defined

### Implementation Plan
- **PHASE3_IMPLEMENTATION_PLAN.md** - Sequencing & risk mitigation
  - Feature sequencing (1 → 5)
  - Test architecture
  - Agent Council decision points
  - Success criteria

### This Document
- **PHASE3_QUICK_REFERENCE.md** - Quick lookup (you are here)
  - Feature comparison matrix
  - High-risk failure modes
  - Zero-storage checklist
  - Reusable patterns

---

## Next Steps

1. **Agent Council Review:** Discuss decision points in PHASE3_IMPLEMENTATION_PLAN.md
2. **CEO Approval:** Confirm customization scope (Features 3, 5) and test budget
3. **Implementation:** Start with Feature 1 (Suspense Detector)
4. **Validation:** All 201 tests must pass before merge to main

**Expected Timeline:**
- Sprints 36-37: Features 1 + 2 (7 days)
- Sprint 38: Feature 4 (5 days)
- Sprints 39-40: Feature 3 (8 days)
- Sprints 41-44: Feature 5 (14 days)
- **Total:** 34 days (5 weeks)

---

**Analysis Complete. Ready for Implementation.**
