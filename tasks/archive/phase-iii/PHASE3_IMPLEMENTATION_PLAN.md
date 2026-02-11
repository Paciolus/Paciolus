# Phase III Implementation Strategy
## QualityGuardian Sequencing & Risk Mitigation

**Created:** 2026-02-04
**Status:** Ready for Agent Council Review

---

## Implementation Sequence (Recommended Order)

### Sprint A: Foundation (Sprints 36-37, ~14 days)

#### Feature 1: Suspense Account Detector [QUICK START]
- **Complexity:** 5/10 (Simplest)
- **Tests Required:** 34
- **Est. Implementation:** 3-4 days
- **Dependencies:** None
- **Risk:** Low
- **Verdict:** START HERE - Lowest risk, fastest time-to-value

**Key Defensive Patterns:**
- Fuzzy keyword matching (reuse from account_classifier.py)
- Floating-point tolerance (< $0.01)
- Zero-storage: count only, no names

---

#### Feature 2: Balance Sheet Validator [QUICK START]
- **Complexity:** 6/10 (Moderate)
- **Tests Required:** 34
- **Est. Implementation:** 3-4 days
- **Dependencies:** Feature 1 (knowledge of CategoryTotals)
- **Risk:** Low-to-Medium (floating-point precision)
- **Verdict:** PAIR WITH FEATURE 1 (can work in parallel)

**Key Defensive Patterns:**
- Relative tolerance: max(0.01, total_assets * 0.0001)
- Handles negative equity gracefully
- Multi-sheet validation

---

### Sprint B: Analytics (Sprints 38-40, ~21 days)

#### Feature 4: Rounding Anomaly Scanner [MEDIUM EFFORT]
- **Complexity:** 7/10 (Moderate-High)
- **Tests Required:** 43
- **Est. Implementation:** 5-6 days
- **Dependencies:** Feature 1, 2
- **Risk:** Medium (legitimate rounds vs. placeholders)
- **Verdict:** IMPLEMENT SOLO SPRINT (no parallel work)

**Key Defensive Patterns:**
- Materiality filter (suppress < 0.1%)
- Deduplication (report highest divisor only)
- Handles negative balances with sign tracking

**Why After A:** Builds on materiality logic from Features 1-2

---

### Sprint C: Risk Analytics (Sprints 41-44, ~28 days)

#### Feature 3: Concentration Risk Detector [HIGH EFFORT]
- **Complexity:** 8/10 (High)
- **Tests Required:** 43
- **Est. Implementation:** 7-8 days
- **Dependencies:** Features 1, 2, 4
- **Risk:** Medium-High (materiality interaction, industry customization)
- **Verdict:** IMPLEMENT SOLO SPRINT + CEO DECISION POINT

**Key Defensive Patterns:**
- Contra-account net calculation
- Industry-specific thresholds (configurable)
- Cardinality notes (single-account edge case)

**Decision Point Required:**
- Should threshold be hardcoded (25%) or per-industry?
- Should threshold be per-session (user customizable)?

---

#### Feature 5: Contra-Account Validator [EXPERT LEVEL]
- **Complexity:** 9/10 (Highest)
- **Tests Required:** 47
- **Est. Implementation:** 10-14 days
- **Dependencies:** All prior features + Depreciation knowledge
- **Risk:** High (fuzzy matching ambiguity, depreciation methods)
- **Verdict:** IMPLEMENT SOLO SPRINT + ACCOUNTING EXPERT REVIEW

**Key Defensive Patterns:**
- Fuzzy matching (Levenshtein, confidence threshold >70%)
- Ratio anomaly thresholds (warning >80%, critical >100%)
- Supports mixed depreciation methods
- Handles fully depreciated assets

**Why Last:**
- Most complex matching logic
- Needs all prior features' error patterns
- Requires domain expert review (accounting standards)

---

## Test Suite Architecture

### Phase 1: Core Tests (Sprints A-B)
```
backend/tests/
├── conftest.py                           (shared fixtures)
├── test_suspense_detector.py             (34 tests)
├── test_balance_sheet_validator.py       (34 tests)
└── test_rounding_anomaly_scanner.py      (43 tests)
   Total: 111 new tests
```

### Phase 2: Advanced Tests (Sprints C)
```
backend/tests/
├── test_concentration_detector.py        (43 tests)
└── test_contra_account_validator.py      (47 tests)
   Total: 90 new tests
```

### Final Coverage
- **Before Phase III:** 232 tests
- **After Phase III:** 433 tests
- **Coverage Increase:** 86% more test coverage

---

## Risk Mitigation: Edge Cases

### Feature 1: Suspense Detector

**False Positive Risk:** Legitimate suspense accounts flagged
- **Mitigation:** Add "override_suspense_zero" to client settings
- **Test:** Test 1.15 validates materiality context

**Keyword Coverage:** Non-English account names
- **Mitigation:** Fuzzy matching (account_classifier.py pattern)
- **Test:** Test 1.11-1.14 validate unicode/international names

---

### Feature 2: Balance Sheet Validator

**Precision Loss Risk:** Large TBs (>$1T) lose floating-point precision
- **Mitigation:** Use relative tolerance or Decimal type for amounts
- **Test:** Test 2.19-2.20 validate large number handling

**Missing Category Risk:** Equity accounts missing from GL
- **Mitigation:** Check each category != None; report "incomplete TB"
- **Test:** Test 2.6-2.8 validate missing categories

---

### Feature 3: Concentration Risk Detector

**Single-Account False Positive:** Only 1 AR account = 100% concentration
- **Mitigation:** Note "single account category" in result; allow override
- **Test:** Test 3.10-3.12 validate cardinality awareness

**Threshold Variability:** 25% threshold not right for all industries
- **Mitigation:** Industry-specific override (Client.industry enum)
- **Test:** Test 3.21-3.22 validate industry threshold
- **Decision Required:** CEO approval on customization model

---

### Feature 4: Rounding Anomaly Scanner

**Legitimate Rounds:** Revenue = $1M exactly (normal, not placeholder)
- **Mitigation:** Materiality filter (<0.1% suppressed)
- **Test:** Test 4.11-4.14 validate materiality suppression

**Depreciation Accrual:** Tax provision = $12K/month * 12 = $144K (round)
- **Mitigation:** Context tracking (expense type, temporal pattern)
- **Test:** Test 4.18-4.20 validate temporal context

---

### Feature 5: Contra-Account Validator

**Fuzzy Matching Ambiguity:** "Equipment" matches "Equipment Rental Expense"
- **Mitigation:** Confidence threshold >70%; keyword specificity (contra = "accumulated" + "depreciation")
- **Test:** Test 5.11-5.15 validate confidence scores

**Depreciation Method Variance:** Accelerated depreciation = 70%, straight-line = 40%
- **Mitigation:** Allow per-asset-class threshold override
- **Test:** Test 5.20-5.22 validate method-specific ratios

---

## Agent Council Decision Points

### Tension 1: Customization Complexity vs. Usability

**Feature 3 (Concentration), Feature 4 (Rounding):** How much customization?

**Option A (Simple):** Hardcoded thresholds
- Pros: Faster implementation (5 days instead of 8)
- Cons: Not suitable for all industries

**Option B (Flexible):** Per-industry, per-session thresholds
- Pros: Accurate for manufacturing, retail, banking
- Cons: Slower implementation (8 days), UI complexity

**Decision Needed:** CEO directive on feature scope

---

### Tension 2: Test Coverage Ambition

**Total Phase III Tests:** 201 new tests (86% increase)

**Option A (Lean):** 100 tests (essential paths only)
- Pros: Faster implementation (saves 3-4 days)
- Cons: Edge cases under-tested (unicode, multi-currency, negative equity)

**Option B (Thorough):** 201 tests (all failure modes + edge cases)
- Pros: Phase IV-ready code; audit score gains
- Cons: 3-4 days longer implementation

**Decision Needed:** Test coverage targets for audit score

---

### Tension 3: Implementation Sequencing

**Sprint Schedule:**

**Option A (Parallel):** Features 1+2 in parallel (14 days total)
- Pros: Faster time-to-market
- Cons: Risk of shared dependency conflicts

**Option B (Sequential):** Features 1 → 2 → 4 → 3 → 5 (42 days total)
- Pros: Lower risk; each feature tested in isolation; knowledge accumulates
- Cons: Longer delivery timeline

**Recommendation:** Hybrid approach:
- A: Implement 1 + 2 in parallel (4-day sprint) - SHIP early win
- B: Then 4 (5-day sprint) - ANALYZE rounding patterns
- C: Then 3 + 5 sequential (14-day total) - High-risk features solo

---

## Success Criteria: Phase III Complete

- [ ] All 201 tests passing (100%)
- [ ] Zero-storage compliance verified (no account names in logs/DB)
- [ ] 433 total backend tests (232 + 201)
- [ ] Audit score improvement: +1.5 points (8.2 → 9.7)
- [ ] API documentation updated for 5 new endpoints
- [ ] PHASE3_LESSONS.md updated with learnings
- [ ] All features in Production Ready state

---

## Failure-Mode Analysis Complete

**Status:** Ready for Agent Council Review

**Next Step:** Resolve decision points and approve implementation sequence
