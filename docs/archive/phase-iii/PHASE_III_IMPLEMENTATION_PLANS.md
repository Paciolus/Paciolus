# Phase III Feature Implementation Plans
## FrontendExecutor Analysis: 5 Phase III Features

**Document Date:** 2026-02-04
**Project:** Paciolus Phase III (Sprints 40+)
**Prepared By:** FrontendExecutor (Pragmatic Builder)
**Status:** Complete Implementation Strategy Ready

---

## Executive Summary

The Accounting Expert Auditor has recommended 5 features for Phase III. All 5 can be implemented across 4 sprints (instead of 5) through strategic grouping:

- **Sprint 40** (2 weeks): Balance Sheet Equation Validator + Suspense Account Detector
- **Sprint 41** (2 weeks): Concentration Risk Detector + Rounding Anomaly Scanner
- **Sprint 42** (2 weeks): Contra-Account Validator
- **Unblocked Path:** No critical dependencies; all features operate on existing `category_totals` and trial balance data.

**Key Insight:** All 5 features share a common architecture pattern established by `flux_engine.py` and `recon_engine.py`. We can reuse this pattern with 3 new engines.

---

## Feature Analysis

### Feature 1: Balance Sheet Equation Validator
**Complexity: 1/5** | **Sprint: 40** | **Dependencies: None**

#### Description
Validates the fundamental accounting equation: Assets = Liabilities + Equity
Flags if difference exceeds materiality threshold.

#### Implementation Plan

**Backend (audit_engine.py + new validator)**
1. Create `BalanceSheetValidator` class in new file `balance_sheet_validator.py`
2. Method: `validate(category_totals: CategoryTotals) -> BalanceSheetResult`
3. Logic:
   ```
   diff = total_assets - (total_liabilities + total_equity)
   if abs(diff) < materiality_threshold:
       status = "valid"
       severity = "info"
   else:
       status = "invalid"
       severity = "high"
   ```
4. Return: Dataclass with `difference`, `display_amount`, `status`, `severity`
5. **Zero-Storage:** No financial data persisted; only aggregate comparison stored

**Frontend Integration (AuditResults component)**
1. Add new section: `<ValidatorSection title="Balance Sheet Validation" />`
2. Display as single informational card (not staggered list like AnomalyCard)
3. Show:
   - "Equation Balance: Valid ✓" or "Invalid ✗"
   - Difference amount in mono font
   - Explanation text: "Assets are [under/over] accounted by ${amount}"
4. Color: Sage for valid, Clay for invalid

**API Route**
- Integration point: Already processed in `audit_trial_balance_streaming()`
- Add to result dict at key `balance_sheet_validation`
- Include in PDF export (classical ledger format with institutional checkmark)

#### Blockers
- None; uses existing `category_totals` from ratio_engine

#### UI Wireframe
```
┌─────────────────────────────────────┐
│ Balance Sheet Validation            │
├─────────────────────────────────────┤
│ Status: ✓ Valid                     │
│ Assets - (Liabilities + Equity) = $0│
│                                     │
│ "Accounting equation is balanced."  │
└─────────────────────────────────────┘
```

#### Sprint Estimate
- Backend: 3 hours (simple arithmetic)
- Frontend: 2 hours (single card component)
- Testing: 2 hours (unit tests for edge cases)
- **Total: 1 sprint (can combine with Feature 2)**

---

### Feature 2: Suspense Account Detector
**Complexity: 1/5** | **Sprint: 40** | **Dependencies: None**

#### Description
Identifies accounts with suspense-like keywords that have non-zero balances.
Flags as potential clearing accounts requiring investigation.

#### Implementation Plan

**Backend (audit_engine.py)**
1. Create `SuspenseDetector` class in new file `suspense_detector.py`
2. Keywords list:
   ```python
   SUSPENSE_KEYWORDS = [
       "suspense", "clearing", "miscellaneous", "sundry", "other",
       "unallocated", "temporary", "pending", "holds", "rounding"
   ]
   ```
3. Logic: For each account in abnormal_balances:
   - If account_name contains keyword AND balance != 0: flag it
   - Assign severity: "high" (suggests incomplete work)
4. Return: List of `SuspenseItem` dataclass
5. **Zero-Storage:** Only patterns flagged; no account balance data persisted

**Frontend Integration (AnomalyCard extension)**
1. Add special marker to AnomalyCard when `is_suspense_account = true`
2. Badge text: "Suspense/Clearing Account"
3. Color indicator: Clay orange (warning, not error)
4. Tooltip: "This account type typically contains temporary entries awaiting proper posting."

**API Route**
- New endpoint: `POST /audit/{audit_id}/suspense-scan`
- Or integrate into main audit response under `suspense_accounts`
- Include in activity_log for historical tracking

#### Blockers
- Keyword matching is case-insensitive (ensure account_name normalized)
- Some accounts may have legitimate "Other" names (e.g., "Other Income"); use threshold strategy:
  - Flag only if balance > 0 AND account_name matches keyword

#### UI Wireframe
```
AnomalyCard with additional section:
┌─────────────────────────────────────┐
│ Miscellaneous Expense               │
│ (OTHER INCOME)                      │
│                                     │
│ [Badge: SUSPENSE ACCOUNT]           │
│ Amount: $(15,000)                   │
│                                     │
│ Issue: Balance not yet cleared      │
│ Dr: $15,000 | Cr: $0                │
│                                     │
│ ⚠️ This account type typically      │
│    contains temporary entries...    │
└─────────────────────────────────────┘
```

#### Sprint Estimate
- Backend: 2 hours (simple keyword matching)
- Frontend: 1.5 hours (AnomalyCard extension)
- Testing: 1.5 hours (keyword coverage)
- **Total: 1 sprint (can combine with Feature 1)**

#### Combined Sprint 40 Plan
**Feature 1 + Feature 2 = 1 Complete Sprint**
- Day 1-2: Balance Sheet Validator backend + tests
- Day 3: Suspense Detector backend + tests
- Day 4-5: Frontend integration (single dashboard section)
- Day 6: PDF export updates
- **Estimate: 10-12 hours total work**

---

### Feature 3: Concentration Risk Detector
**Complexity: 2/5** | **Sprint: 41** | **Dependencies: Feature 1 completion**

#### Description
For each account category (assets, liabilities, etc.), calculates each account's
percentage of total. Flags if any account exceeds 25% concentration.

#### Implementation Plan

**Backend (ratio_engine.py extension)**
1. Create `ConcentrationAnalyzer` class in new file `concentration_analyzer.py`
2. Method: `analyze(category_totals: CategoryTotals, abnormal_balances: list) -> ConcentrationResult`
3. Logic for each category:
   ```
   for category in [ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE]:
       category_total = get_category_total(category)
       for account in accounts_in_category:
           pct = abs(account.balance) / abs(category_total)
           if pct > 0.25:  # 25% threshold
               flag_risk(account, pct)
   ```
4. Return: `ConcentrationResult` with:
   - `items: List[ConcentrationItem]` (account, category, percentage, severity)
   - `category_breakdown: Dict[str, ConcentrationSummary]`
   - `summary_stats: ConcentrationStats`
5. **Zero-Storage:** Only percentages and thresholds; no raw amounts persisted

**Frontend Integration**
1. New dashboard section: `<ConcentrationRiskSection />`
2. Display as staggered card list (like AnomalyCard)
3. For each high-concentration account:
   - Account name + category
   - Percentage bar (visual from 0-50%, capped)
   - Risk indicator: "High (25%+)" in Clay
4. Summary stats: "X accounts exceed 25% concentration"

**API Route**
- New endpoint: `GET /audit/{audit_id}/concentration-analysis`
- Or integrate into main audit response under `concentration_risks`
- Include in sensitivity toolbar (recalculate on threshold change)

#### Blockers
- Must ensure category_totals calculation is correct (already validated in Sprint 25)
- Threshold (25%) is configurable via settings (future)
- Edge case: Category total = 0 (no division by zero)

#### UI Wireframe
```
┌──────────────────────────────────────────┐
│ Concentration Risk Analysis              │
├──────────────────────────────────────────┤
│ 5 accounts exceed 25% concentration      │
│                                          │
│ ┌─ [Asset] Inventory Account      ┐     │
│ │ 42% of Total Assets             │     │
│ │ [████████░░░░░░░░░░] 42%        │     │
│ │ Status: HIGH CONCENTRATION      │     │
│ └─────────────────────────────────┘     │
│                                          │
│ ┌─ [Liability] Senior Debt  ┐            │
│ │ 38% of Total Liabilities   │            │
│ │ [███████░░░░░░░░░░░░] 38%  │            │
│ │ Status: HIGH CONCENTRATION │            │
│ └────────────────────────────┘            │
│                                          │
│ Category Breakdown:                      │
│ • Assets: 2 high-risk accounts          │
│ • Liabilities: 2 high-risk accounts     │
│ • Revenue: 1 high-risk account          │
└──────────────────────────────────────────┘
```

#### Sprint Estimate
- Backend: 4 hours (percentage calculation + thresholds)
- Frontend: 3 hours (dashboard component + staggered animations)
- Testing: 2 hours (edge cases, category breakdowns)
- **Total: 1.5 sprints (can combine with Feature 4)**

---

### Feature 4: Rounding Anomaly Scanner
**Complexity: 2/5** | **Sprint: 41** | **Dependencies: None**

#### Description
Checks if account balances are divisible by 1000, 10000, 100000, etc.
Assigns "roundness score" (higher = more suspicious).
Flags as potential estimates/manual entries.

#### Implementation Plan

**Backend (audit_engine.py)**
1. Create `RoundingAnalyzer` class in new file `rounding_analyzer.py`
2. Method: `analyze(abnormal_balances: list) -> RoundingResult`
3. Logic for each account:
   ```
   balance_abs = abs(balance)
   if balance_abs == 0: roundness = 0
   elif balance_abs % 100000 == 0: roundness = 5 (highest suspicion)
   elif balance_abs % 10000 == 0: roundness = 4
   elif balance_abs % 1000 == 0: roundness = 3
   elif balance_abs % 100 == 0: roundness = 2
   else: roundness = 1 (lowest)

   if roundness >= 3:
       flag_as_suspicious()
   ```
4. Return: `RoundingResult` with:
   - `items: List[RoundingItem]` (account, balance, roundness_score, severity)
   - `high_roundness_count: int`
   - `materiality_summary: Dict[str, int]` (count by roundness level)
5. **Zero-Storage:** Only roundness scores; no balance data persisted

**Frontend Integration**
1. New dashboard section: `<RoundingAnomalySection />`
2. Display as tabbed breakdown:
   - Tab 1: "Perfectly Round (100k)" - highest suspicion
   - Tab 2: "Round to 10k"
   - Tab 3: "Round to 1k"
3. For each item:
   - Account name + amount
   - Roundness indicator (visual: more filled = more round)
   - Tooltip: "This balance may indicate an estimate or manual entry."

**API Route**
- New endpoint: `GET /audit/{audit_id}/rounding-analysis`
- Or integrate into main audit response under `rounding_anomalies`
- Could integrate with ReconEngine (already uses rounding; see recon_engine.py line 127)

#### Blockers
- None; operates on existing balance data
- Note: ReconEngine already scores roundness (line 127-132); this feature extends it
- Could refactor to avoid duplication (use RoundingAnalyzer in ReconEngine)

#### UI Wireframe
```
┌──────────────────────────────────────────┐
│ Rounding Anomaly Analysis                │
├──────────────────────────────────────────┤
│ [Perfectly Round (100k)] [10k] [1k]      │
│                                          │
│ 3 accounts are perfectly round (100k):   │
│                                          │
│ ┌─ Cash Miscellaneous          ┐         │
│ │ $500,000 (5 × 100k)           │         │
│ │ Suspicion: Very High          │         │
│ │ [█████████████░] 5.0 score    │         │
│ └───────────────────────────────┘         │
│                                          │
│ ┌─ Equipment Reserve   ┐                 │
│ │ $1,000,000           │                 │
│ │ Suspicion: Very High │                 │
│ │ [█████████████░] 5.0 │                 │
│ └──────────────────────┘                 │
└──────────────────────────────────────────┘
```

#### Sprint Estimate
- Backend: 3 hours (roundness calculation)
- Frontend: 2.5 hours (dashboard component + tabs)
- Testing: 1.5 hours (edge cases, precision handling)
- **Total: 1.5 sprints (can combine with Feature 3)**

#### Combined Sprint 41 Plan
**Feature 3 + Feature 4 = 1.5 Sprints**
- Day 1-2: Concentration Analyzer backend + tests
- Day 3: Rounding Analyzer backend + tests
- Day 4-5: Frontend concentration risk component + rounding component
- Day 6-7: PDF export updates, integration into SensitivityToolbar (threshold recalc)
- **Estimate: 12-14 hours total work**

---

### Feature 5: Contra-Account Validator
**Complexity: 2/5** | **Sprint: 42** | **Dependencies: None**

#### Description
Matches "accumulated depreciation" accounts with their corresponding asset accounts.
Calculates accumulated depreciation ratio and flags if <10% or >90%.
Helps identify over/under-depreciated assets.

#### Implementation Plan

**Backend (audit_engine.py)**
1. Create `ContraAccountValidator` class in new file `contra_account_validator.py`
2. Keywords matching:
   ```python
   ASSET_KEYWORDS = ["equipment", "plant", "property", "building", "vehicle", "furniture"]
   CONTRA_KEYWORDS = ["accumulated depreciation", "accum depr", "deprec reserve"]
   ```
3. Method: `validate(abnormal_balances: list) -> ContraAccountResult`
4. Logic:
   - For each contra account found:
     - Match to base asset account (fuzzy matching by name)
     - Calculate ratio: accumulated_depr / gross_asset
     - If ratio < 0.10 or > 0.90: flag as unusual
     - Assign severity based on deviation from expected range
   ```
   ratio = abs(accumulated_depr) / abs(gross_asset)
   if 0.10 <= ratio <= 0.90:
       status = "normal"
       severity = "low"
   elif ratio < 0.10:
       status = "under-depreciated"
       severity = "medium"
   else:  # ratio > 0.90
       status = "over-depreciated"
       severity = "high"
   ```
5. Return: `ContraAccountResult` with:
   - `pairs: List[ContraPair]` (gross_account, contra_account, ratio, status)
   - `unmatched_contra: List[str]` (contra accounts with no match)
   - `summary: ContraAccountSummary`
6. **Zero-Storage:** Only ratios and matching logic; no balance data persisted

**Frontend Integration**
1. New dashboard section: `<ContraAccountSection />`
2. Display as table-like structure (one row per matched pair)
3. Columns: Asset Name | Depreciation | Ratio | Status
4. Color coding:
   - Sage (green): Normal range (10-90%)
   - Clay (red): Under-depreciated (<10%)
   - Clay (red): Over-depreciated (>90%)
5. Expansion: Show unmatched contra accounts with alert

**API Route**
- New endpoint: `GET /audit/{audit_id}/contra-account-analysis`
- Or integrate into main audit response under `contra_accounts`
- Include in PDF export (separate section for asset reconciliation)

#### Blockers
- Fuzzy matching may fail for unusual asset naming conventions
  - Mitigation: Show "unmatched" list for manual review
- May not apply to service-based companies (no fixed assets)
  - Mitigation: Show "No depreciation accounts found" message gracefully
- Contra accounts may be on balance sheet (visible) or in sub-account groups
  - Current implementation works with flat trial balance

#### UI Wireframe
```
┌────────────────────────────────────────────────┐
│ Contra-Account Validation                      │
├────────────────────────────────────────────────┤
│ 4 matched asset pairs detected                 │
│                                                │
│ Asset Account  | Accumulated Depr | Ratio     │
│ ────────────────────────────────────────────── │
│ Equipment      | $(45,000)        | 25% ✓     │
│ Vehicles       | $(120,000)       | 60% ✓     │
│ Building       | $(50,000)        | 5% ⚠️     │
│ Furniture      | $(8,000)         | 95% ⚠️    │
│                                                │
│ Alerts:                                        │
│ • Building is under-depreciated (5% vs 10%)   │
│ • Furniture is over-depreciated (95% vs 90%)  │
│                                                │
│ Unmatched Accounts:                           │
│ • Accumulated Amortization (no match)         │
└────────────────────────────────────────────────┘
```

#### Sprint Estimate
- Backend: 4 hours (fuzzy matching + ratio logic)
- Frontend: 3 hours (table component + color coding)
- Testing: 2 hours (matching algorithm tests, edge cases)
- **Total: 1.5 sprints (solo sprint, but can optimize to 1 if needed)**

#### Sprint 42 Optimization
**Feature 5 Only = 1 Sprint (with optimization)**
- If time permits, integrate additional validation (accumulated amortization matching)
- Backend work: 4 hours
- Frontend work: 3 hours
- Testing: 2 hours
- Buffer: 1 hour (for unforeseen issues)
- **Estimate: 10 hours total work**

---

## Architecture Patterns & Code Reuse

### Common Engine Pattern (Established by flux_engine.py & recon_engine.py)

All 5 features follow a standardized architecture:

```python
# Pattern 1: Dataclass for individual items
@dataclass
class FeatureItem:
    # Core fields
    account_name: str
    value: float

    # Result fields
    status: str
    severity: Severity  # Enum: high, medium, low
    flags: List[str]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format"""

# Pattern 2: Engine class with single compute method
class FeatureEngine:
    def __init__(self, materiality_threshold: float = 0.0):
        self.materiality_threshold = materiality_threshold

    def analyze(self, data: InputType) -> ResultType:
        """Main computation method"""
        items: List[FeatureItem] = []
        # ... process items ...
        return ResultType(items=items, summary=...)

# Pattern 3: Result dataclass for aggregation
@dataclass
class FeatureResult:
    items: List[FeatureItem]
    high_count: int
    medium_count: int
    low_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response"""
```

### Integration Points

**1. Backend (audit_engine.py)**
```python
# Existing pattern from StreamingAuditor
def audit_trial_balance_streaming(...) -> dict[str, Any]:
    # ... existing code ...

    # Add new validators after calculate_analytics()
    result["balance_sheet_validation"] = balance_sheet_validator.validate(category_totals)
    result["suspense_accounts"] = suspense_detector.detect(abnormal_balances)
    result["concentration_risks"] = concentration_analyzer.analyze(category_totals, abnormal_balances)
    result["rounding_anomalies"] = rounding_analyzer.analyze(abnormal_balances)
    result["contra_accounts"] = contra_validator.validate(abnormal_balances)

    return result
```

**2. Frontend (AuditResults component)**
```tsx
// New dashboard sections follow existing pattern
<ValidatorSection title="Balance Sheet Validation" data={result.balance_sheet_validation} />
<AnomalySection title="Suspense Accounts" items={result.suspense_accounts} />
<ConcentrationRiskSection data={result.concentration_risks} />
<RoundingAnomalySection data={result.rounding_anomalies} />
<ContraAccountSection data={result.contra_accounts} />
```

### File Structure (New Files)

**Backend:**
```
backend/
├── balance_sheet_validator.py    (Sprint 40)
├── suspense_detector.py          (Sprint 40)
├── concentration_analyzer.py     (Sprint 41)
├── rounding_analyzer.py          (Sprint 41)
├── contra_account_validator.py   (Sprint 42)
└── tests/
    ├── test_balance_sheet_validator.py
    ├── test_suspense_detector.py
    ├── test_concentration_analyzer.py
    ├── test_rounding_analyzer.py
    └── test_contra_account_validator.py
```

**Frontend:**
```
frontend/src/components/
├── validators/
│   ├── BalanceSheetValidationCard.tsx  (Sprint 40)
│   ├── SuspenseAccountBadge.tsx        (Sprint 40)
│   ├── ConcentrationRiskSection.tsx    (Sprint 41)
│   ├── RoundingAnomalySection.tsx      (Sprint 41)
│   └── ContraAccountTable.tsx          (Sprint 42)
└── results/
    └── AuditResultsWithValidators.tsx  (New wrapper component)
```

---

## Zero-Storage Compliance Checklist

Each feature must ensure:
- [ ] No financial data written to database
- [ ] Only aggregate metrics (percentages, ratios, counts) stored
- [ ] Session-only processing in memory
- [ ] No temp files created
- [ ] Sensitive balance amounts logged only in secure logs (not API responses exported)

**Example for Balance Sheet Validator:**
- ✓ Store: difference amount, status, severity
- ✗ Store: individual asset/liability/equity breakdowns
- ✗ Persist: category totals to permanent table

---

## Sprint Timeline & Capacity

### Sprint 40: Balance Sheet Validator + Suspense Detector
**Duration:** 10 days | **Effort:** 10-12 hours
- Backend: Balance Sheet Validator (3h), Suspense Detector (2h)
- Frontend: Integration & cards (3.5h)
- Testing: Unit + integration (2-3h)
- Buffer: 1h

### Sprint 41: Concentration Risk + Rounding Anomaly
**Duration:** 10 days | **Effort:** 12-14 hours
- Backend: Concentration Analyzer (4h), Rounding Analyzer (3h)
- Frontend: Dashboard sections (5.5h)
- Testing: Edge cases + integration (2h)
- Buffer: 1h

### Sprint 42: Contra-Account Validator
**Duration:** 10 days | **Effort:** 10-12 hours
- Backend: Fuzzy matching logic (4h)
- Frontend: Table component (3h)
- Testing: Matching algorithm (2h)
- Documentation: Asset reconciliation guide (1.5h)
- Buffer: 1-1.5h

**Total Phase III: 32-40 hours over 3 sprints**

---

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Fuzzy matching fails for contra accounts | Medium | Medium | Fallback to unmatched list + manual review UI |
| Rounding analysis duplicates ReconEngine logic | High | Low | Refactor ReconEngine to use RoundingAnalyzer |
| Concentration risk threshold (25%) is arbitrary | Medium | Low | Make configurable in practice settings |
| Balance Sheet Equation always validates in balanced TB | High | Low | Test with intentionally unbalanced files |
| Database storage pressure on analytics | Low | Low | Existing architecture stores only aggregates |

---

## Unblocked Path Confirmation

✓ No feature blocks another
✓ All use existing `category_totals` and `abnormal_balances` data
✓ No schema changes required
✓ No auth/permission changes needed
✓ PDF export integration straightforward (follows classical pattern)
✓ Frontend components follow Oat & Obsidian theme

**Go/No-Go Decision:** READY TO BUILD

---

## Dependency Map

```
Sprint 40
├─ Balance Sheet Validator (independent)
└─ Suspense Detector (independent)
    └─ no downstream dependencies

Sprint 41
├─ Concentration Analyzer (independent)
└─ Rounding Analyzer (independent)
    └─ refactor opportunity: use in ReconEngine

Sprint 42
└─ Contra-Account Validator (independent)
    └─ optional: integrate with asset depreciation workflows
```

---

## Next Steps

1. **Code Review & Approval**: Review this plan with Auditor and Guardian
2. **Create Pull Request Template**: Prepare PR for Sprint 40 features
3. **Database Audit**: Confirm ActivityLog schema sufficient for new metrics
4. **Frontend Routing**: Plan where new validator sections appear in AuditResults
5. **Test Matrix**: Create test cases for each feature (10+ tests per engine)
6. **Documentation**: Update CLAUDE.md Phase III section with sprint status

---

## Questions for Project Council

1. **Threshold Configuration**: Should concentration risk (25%) and contra ratio (10-90%) be configurable per practice?
2. **PDF Export Priority**: Should all 5 features appear in PDF, or only high-risk items?
3. **Settings Integration**: Do these features need user-configurable flags (e.g., "Skip suspense detection")?
4. **Historical Tracking**: Should validator results be stored in `DiagnosticSummary` for trend analysis?

---

**Document Status:** Ready for Implementation
**Review Assigned To:** ProjectAuditor (Guardian) + CEO (final approval)
**Target Start Date:** Post-Sprint 39 (Benchmark Framework)

