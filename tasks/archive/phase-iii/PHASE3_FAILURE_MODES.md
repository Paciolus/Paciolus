# Phase III Feature Failure-Mode Analysis
## QualityGuardian Review of 5 Proposed Features

**Analysis Date:** 2026-02-04
**Current Test Coverage:** 232 backend tests
**Target Coverage:** +80 tests for Phase III features
**Analysis Role:** QualityGuardian (Failure-Mode Analyst)

---

## Feature 1: Suspense Account Detector

### Purpose
Flag non-zero balances in suspense, clearing, or miscellaneous accounts that should typically be zero.

### Failure Modes

| Failure Mode | Trigger | Impact | Detection |
|--------------|---------|--------|-----------|
| **False Positive: Legitimate Suspense** | Account named "Suspense Account" but legitimately used for timing differences | User alarm fatigue, wasted investigation time | High keyword confidence without context |
| **False Negative: Misspelled Keywords** | "Spenss", "Supenss", "Clearing_Temp" accounts not matched | Real errors missed | Rigid substring matching |
| **Negative Balance Bypass** | Suspense account with -$5,000 (debit side, unusual) | Flagged as normal zero, actual problem undetected | Only checks if != 0, not account abnormality |
| **Empty Trial Balance Edge Case** | CSV with only header or no suspense accounts | Crashes or returns confusing empty result | Division by zero or index error on zero results |
| **Unicode Account Names** | "Suspense (一時)" or "釈明勘定" (Japanese for suspense) | Keywords not matched, errors ignored | ASCII-only keyword list |
| **Multi-Sheet: Different Keywords Per Sheet** | Sheet1: "Suspense", Sheet2: "Clearing" (identical account semantically) | Inconsistent flagging across sheets | No cross-sheet normalization |
| **Materiality Interaction** | $0.01 balance vs $0 threshold tolerance | Flagged for trivial rounding difference | Floating-point comparison without tolerance |
| **Zero is a Valid State** | Some orgs use suspense accounts as permanent holding areas | All zero-balance suspense accounts required but flagged as suspicious | No domain knowledge override mechanism |
| **Negative Equity Scenario** | Company with suspense account as equity plug to balance negative retained earnings | Legitimate but flagged as error | No balance sheet equation context |

### Test Scenario Checklist

#### Core Detection
- [ ] Test 1.1: Single suspense account with $10,000 debit balance → **MUST flag**
- [ ] Test 1.2: Single suspense account with $0 balance → **MUST NOT flag**
- [ ] Test 1.3: "Clearing Account" with $5,000 credit balance → **MUST flag**
- [ ] Test 1.4: "Miscellaneous Holding" with $0 balance → **MUST NOT flag**
- [ ] Test 1.5: Multiple suspense accounts, some zero, some non-zero → **MUST flag only non-zero**

#### Edge Cases: Data Quality
- [ ] Test 1.6: Suspense account with -$1,000 balance → **MUST flag as abnormal balance**
- [ ] Test 1.7: Suspense account with $0.00 (exactly) → **MUST NOT flag**
- [ ] Test 1.8: Suspense account with $0.01 (floating-point rounding) → **SHOULD NOT flag** (tolerance < 0.05)
- [ ] Test 1.9: Suspense account with extremely large balance ($999,999,999.99) → **MUST flag with severity indicator**
- [ ] Test 1.10: Empty trial balance (0 rows after header) → **MUST return empty results, not error**

#### Unicode & Internationalization
- [ ] Test 1.11: Account name "一時勘定" (Japanese: suspense) → **MAY NOT flag** (baseline test)
- [ ] Test 1.12: Account name "Suspense (備忘)" (Mixed English/Japanese) → **MUST flag** (English keyword present)
- [ ] Test 1.13: Account name "Kto. Przejściowe" (Polish: suspense) → **MAY NOT flag** (baseline)
- [ ] Test 1.14: Account with emoji "🔄 Suspense Sweep" → **MUST flag** (after emoji strip)

#### Materiality & Context
- [ ] Test 1.15: Suspense account with $100 vs. $100M total assets (0.0001% materiality) → **FLAG with low-severity note**
- [ ] Test 1.16: Suspense account representing 25% of total equity → **FLAG with high-severity note**
- [ ] Test 1.17: Suspense account with debit balance in liability section → **FLAG as abnormal + suspense issue**

#### Multi-Sheet Behavior
- [ ] Test 1.18: 2 sheets, Sheet1 has "Suspense", Sheet2 has "Clearing" → **Flag both independently**
- [ ] Test 1.19: 3 sheets, only 1 has suspense account → **Flag only the sheet with it**
- [ ] Test 1.20: Consolidated trial balance (summed suspense accounts) → **Flag aggregate if non-zero**

#### Zero Storage Compliance
- [ ] Test 1.21: No suspense account identifiers stored in database, only flag counts → **Verify no account names in logs**
- [ ] Test 1.22: Multiple suspense accounts in same run → **Store count only, not details**

#### Defensive Coding
- [ ] Test 1.23: Keyword list is case-insensitive ("SUSPENSE", "Suspense", "suspense") → **All match**
- [ ] Test 1.24: Whitespace tolerance ("Suspense Account", "  Suspense  Account") → **Both match**
- [ ] Test 1.25: Substring matching ("Suspense_WIP", "MySuspenseAct") → **Both match**
- [ ] Test 1.26: Non-matches ("Pensure", "Soupspense", "Suspend") → **None match**

### Defense Strategy

**Defensive Coding Requirements:**

```
1. KEYWORD MATCHING
   - [ ] Use set for O(1) lookup (keywords: "suspense", "clearing", "miscellaneous", "holding", "temporary")
   - [ ] Case-insensitive comparison: account_name.lower() in keyword_list
   - [ ] Whitespace normalization: account_name.strip()
   - [ ] Fuzzy match fallback for misspellings (Levenshtein distance ≤ 2, see: account_classifier.py)

2. BALANCE VALIDATION
   - [ ] Tolerance check: abs(balance) > 0.01 (not just != 0)
   - [ ] Direction check: abnormal balance in suspense = higher severity
   - [ ] Materiality check: flag_severity = determine_severity(balance / total_assets)

3. ERROR HANDLING
   - [ ] Empty DataFrame check BEFORE keyword search
   - [ ] Try/except around numeric conversions
   - [ ] Log any account names that don't parse as float (do NOT store the names)

4. ZERO-STORAGE
   - [ ] Do NOT store: account_name, account_number, specific_balance
   - [ ] Store ONLY: suspicious_count (int), severity_level (enum), timestamp

5. UNICODE SAFETY
   - [ ] Decode UTF-8 with error='replace' for non-UTF8 files
   - [ ] Strip emoji/special chars before matching: re.sub(r'[^\w\s]', '', name)
   - [ ] Test on database: ensure no account names in queries
```

### Zero-Storage Risk Assessment

**CRITICAL:** Account names must NEVER be stored.

- **Risk Level:** HIGH
- **Current Mitigation:** audit_engine.py uses `log_secure_operation()` which hashes sensitive data
- **Action:**
  - [ ] Ensure detector logs only `"flagged_suspense_count": 5`, NOT account names
  - [ ] Add test: Query database, verify no account names in any suspense detection logs
  - [ ] Use same `log_secure_operation()` pattern as audit_engine.py

### Estimated Test Count
- **Unit tests:** 26 tests (keyword matching, balance validation, tolerance, unicode)
- **Integration tests:** 5 tests (multi-sheet, consolidated, empty cases)
- **Security tests:** 3 tests (zero-storage compliance)
- **Total:** **34 tests**

---

## Feature 2: Balance Sheet Equation Validator

### Purpose
Verify that Assets = Liabilities + Equity within accounting tolerance.

### Failure Modes

| Failure Mode | Trigger | Impact | Detection |
|--------------|---------|--------|-----------|
| **Rounding Error Misidentification** | A = L + E with $0.01 difference (normal floating-point) | False failure flag, user distrust | Exact equality check (0.00) |
| **Wrong Tolerance Selection** | Tolerance set to $1.00 but TB is $500M (0.0000002% error) | Legitimate TB flagged as imbalanced | Hardcoded tolerance, not relative |
| **Missing Account Category** | Trial balance has Assets and Liabilities but NO Equity accounts | "Equity = 0" assumption breaks validation logic | Implicit assumption, not validated |
| **Negative Equity (Insolvent Company)** | A = $1M, L = $2M, E = -$1M (valid in insolvency) | Correctly validates but confuses users | No explanatory context |
| **Multi-Sheet Consolidation Error** | Sheet1: A=$100K, L=$60K, E=$40K; Sheet2: A=$50K, L=$30K, E=$20K; but consolidated shows A=$150K, L=$90K, E=$50K | Equation balances but shouldn't because consolidation is wrong | Individual sheet validation missed |
| **Currency Mixing** | Asset in USD ($100K), Liability in EUR (€60K ≈ $65K), Equity in USD ($35K) | Equation "balances" but cross-currency without FX handling | Assumes all values same currency |
| **Intercompany Elimination Not Applied** | Parent company consolidation without eliminating intercompany receivables | Equation balances but contains redundant accounts | No consolidation audit trail |
| **Dividend Payable Timing** | Dividend declared but not yet paid: affects equity but not asset/liability immediately | Creates apparent imbalance until correct classification | Classification dependency not checked |
| **Post-Closing Trial Balance** | TB taken after closing entries with zero revenue/expense but retained earnings updated | Validation depends on trial balance TYPE (pre/post-closing) | No trial balance phase detection |
| **Very Large Numbers** | A = $9.99999999999999E+15, L = $5E+15, E = $4.99999999999999E+15 | Floating-point precision loss causes spurious failures | Standard float64 precision at large scales |

### Test Scenario Checklist

#### Core Validation
- [ ] Test 2.1: Perfect balance (A=$1M, L=$600K, E=$400K) → **VALID**
- [ ] Test 2.2: Off by $0.01 (A=$1M, L=$600K, E=$399,999.99) → **VALID** (within tolerance)
- [ ] Test 2.3: Off by $1,000 (A=$1M, L=$600K, E=$399K) → **INVALID, flag with gap=$1K**
- [ ] Test 2.4: Negative equity (A=$1M, L=$1.5M, E=-$500K) → **VALID** (still balances)
- [ ] Test 2.5: Zero equity (A=$500K, L=$500K, E=$0) → **VALID**

#### Edge Cases: Missing Categories
- [ ] Test 2.6: No equity accounts in TB (A=$1M, L=$600K, E=$0) → **INVALID, report missing equity with gap=$400K**
- [ ] Test 2.7: No liability accounts (A=$1M, L=$0, E=$1M) → **VALID** (sole proprietor, no debt)**
- [ ] Test 2.8: No asset accounts (impossible, but test error handling) → **INVALID, report missing assets**
- [ ] Test 2.9: Empty trial balance → **INVALID, report all zeros with message "No accounts found"**
- [ ] Test 2.10: Only one account (A=$1M, others zero) → **INVALID, gap=$1M (unless single-entity)**

#### Multi-Sheet Consolidation
- [ ] Test 2.11: Two balanced sheets, unbalanced consolidation → **INVALID, report sheet-level and consolidated balances**
- [ ] Test 2.12: Two sheets, one missing equity → **INVALID, identify which sheet**
- [ ] Test 2.13: Three sheets all balanced, consolidation missing elimination → **FLAG with "possible intercompany elimination needed"**
- [ ] Test 2.14: Consolidated TB has suspense account with huge balance (consolidation error) → **Flag separately**

#### Materiality & Relative Tolerance
- [ ] Test 2.15: Small TB ($10K) off by $1 (10% error) → **INVALID**
- [ ] Test 2.16: Large TB ($10B) off by $1,000 (0.00001% error) → **VALID** (relative tolerance)
- [ ] Test 2.17: Audit materiality is 5% of equity; equation off by 3% → **FLAG as immaterial gap**
- [ ] Test 2.18: Equation off by exactly audit materiality percentage → **Boundary test: VALID or FLAG?**

#### Floating-Point Precision
- [ ] Test 2.19: Very large numbers ($9.99E+15) with small relative error → **VALID** (not false negative from precision loss)
- [ ] Test 2.20: Mixed magnitude (A=$1E+12, L=$1E-6, E=$1E+12) → **Validation still correct despite precision issues**
- [ ] Test 2.21: Accumulation of rounding errors (100,000 transactions summed) → **Within tolerance**

#### Trial Balance Phase Detection
- [ ] Test 2.22: Pre-closing TB with revenue/expense accounts included → **Separate validation rule (not applicable)**
- [ ] Test 2.23: Post-closing TB (revenue/expense = 0, retained earnings updated) → **VALID if A = L + E**
- [ ] Test 2.24: Intermediate TB (partially closed accounts) → **FLAG as "unusual account state", require manual review**

#### Zero Storage Compliance
- [ ] Test 2.25: Account names not stored when equation fails → **Verify no account details in logs**
- [ ] Test 2.26: Only equation status stored (valid/invalid, gap amount) → **Verify only aggregate data**

#### Defensive Coding
- [ ] Test 2.27: Division by zero when all totals are zero → **MUST NOT crash, return special "empty TB" result**
- [ ] Test 2.28: Negative total assets (possible with classification errors) → **Validate each category independently, flag unusual signs**
- [ ] Test 2.29: NaN or infinity values in category totals → **Catch, log, return validation_error**

### Defense Strategy

**Defensive Coding Requirements:**

```
1. TOLERANCE MECHANISM
   - [ ] Use RELATIVE tolerance: tolerance = max(ABSOLUTE_MIN, total_assets * RELATIVE_PERCENT)
   - [ ] ABSOLUTE_MIN = $0.01 (for small TBs)
   - [ ] RELATIVE_PERCENT = 0.01% (0.0001 in decimal)
   - [ ] Formula: is_balanced = abs(gap) <= max(0.01, total_assets * 0.0001)

2. CATEGORY VALIDATION
   - [ ] Check each category (total_assets, total_liabilities, total_equity) != null
   - [ ] If any category is missing (None or zero without accounts), report "incomplete trial balance"
   - [ ] Do NOT assume zero equity if no equity accounts found

3. GAP CALCULATION
   - [ ] gap = total_assets - (total_liabilities + total_equity)
   - [ ] Track sign of gap (assets deficit vs. equity deficit)
   - [ ] Round gap to 2 decimals AFTER subtraction (not before)

4. MULTI-SHEET HANDLING
   - [ ] Validate each sheet independently first
   - [ ] Then validate consolidated totals
   - [ ] Report per-sheet gaps if any sheet is invalid

5. ERROR HANDLING
   - [ ] Try/except for float operations (NaN, inf)
   - [ ] Validate inputs are numeric BEFORE equation check
   - [ ] Graceful degradation: if any category is non-numeric, report "classification error"

6. ZERO-STORAGE
   - [ ] Store ONLY: equation_valid (bool), gap_amount (float), gap_percentage (float)
   - [ ] Do NOT store: category names, account names, individual account balances
   - [ ] Use audit timestamp for trend (not account details)

7. CONTEXT PRESERVATION
   - [ ] Return structured result with:
     * is_balanced: bool
     * gap_amount: float (positive = asset deficit, negative = equity surplus)
     * gap_percentage: float (gap / total_assets)
     * material_per_audit_threshold: bool (if materiality provided)
     * notes: list[str] (e.g., "negative_equity_detected", "missing_equity_accounts")
```

### Zero-Storage Risk Assessment

**Risk Level:** MEDIUM (category totals are already stored in DiagnosticSummary; just ensure no new account details leaked)

- **Current Mitigation:** DiagnosticSummary.to_dict() stores only totals, no account details
- **Action:**
  - [ ] Validator outputs only: { is_balanced, gap_amount, gap_percentage }
  - [ ] Test: Ensure no new columns added to DiagnosticSummary for this feature
  - [ ] Verify: Return value never includes account_name or account_number

### Estimated Test Count
- **Unit tests:** 23 tests (equation validation, tolerance, category checks, floating-point)
- **Integration tests:** 8 tests (multi-sheet, consolidation, materiality interaction)
- **Security tests:** 3 tests (zero-storage compliance, category filtering)
- **Total:** **34 tests**

---

## Feature 3: Concentration Risk Detector

### Purpose
Flag accounts that represent > 25% of their category total (e.g., single customer 30% of AR).

### Failure Modes

| Failure Mode | Trigger | Impact | Detection |
|--------------|---------|--------|-----------|
| **Single-Account Category** | Only 1 AR account with $100K in company; threshold is 25% → 100% concentration | False flag: concentration = 100%, normal for small companies | Ignores category cardinality |
| **Negative Balance Artifacts** | Accounts Receivable Allowance (contra-asset, normal balance) causes category total to drop below account balance | Flag triggers falsely; AR Allowance shows 120% concentration | Does not account for contra-accounts |
| **Zero Category Total** | Category has accounts but all zero balances; one account with 0.01 (rounding) → division by zero | Crashes or returns inf/NaN | Division by zero unhandled |
| **Materiality Blindness** | $10 account = 50% of $20 category total, below company materiality threshold | Flagged despite immaterial | Uses account concentration, ignores company materiality |
| **Mixed Signs in Category** | Assets category: AR +$100K, Allowance -$30K (total $70K), AR shows 142% concentration | Misleading: gross concentration, not net risk | Net vs. gross concentration confusion |
| **Multi-Currency in Same Category** | Receivable in USD ($100K) + Receivable in EUR (€100K ≈ $110K) same category | Currency rate-dependent threshold (25% in EUR, 47% in USD) | Assumes single currency |
| **Consolidation Elimination Leakage** | Intercompany receivable not eliminated in consolidation; appears as 80% of AR | Legitimate risk flagged, but due to consolidation error | No intercompany marker |
| **Account Aggregation Level** | GL shows AR at top level ($100K, 30% of category), but should be summed from subledger (10 customers, each <10%) | Gross concentration masked by GL aggregation | Assumes GL level is detail sufficient |
| **Threshold Customization** | Regulation requires 20% threshold for banking sector, 50% for manufacturing | Hardcoded 25% threshold not configurable per industry | No industry/regulatory override |
| **Negative Concentration** | Allowance account (contra-asset) showing "concentration" in negative | Nonsensical metric, but flagged as risk | No account type/polarity context |

### Test Scenario Checklist

#### Core Detection
- [ ] Test 3.1: 5 AR accounts: $100K, $80K, $70K, $60K, $50K (total $360K) → Flag $100K (27.8%) → **MUST flag**
- [ ] Test 3.2: Same 5 accounts but each < 25% of category → **MUST NOT flag**
- [ ] Test 3.3: Single AR account, $100K, category total $100K → 100% concentration → **MUST flag, but note "only account"**
- [ ] Test 3.4: Category total = $0, one account = $0 → **MUST NOT flag or return error gracefully**
- [ ] Test 3.5: 10 expense accounts, one = 26% of total → **MUST flag**

#### Edge Cases: Negative Balances & Contra-Accounts
- [ ] Test 3.6: AR = $1M, AR Allowance = -$100K (contra, net AR = $900K) → AR shows 111% concentration → **Should measure net, not gross**
- [ ] Test 3.7: Accounts Receivable (asset) with credit balance (abnormal) showing concentration → **Concentration still valid metric, flag separately as abnormal balance**
- [ ] Test 3.8: All accounts in category negative (e.g., all liabilities are actually expense reversals) → **Concentration still valid if all same sign**
- [ ] Test 3.9: Mixed signs: AR $100K (debit) + AR contra -$50K (credit) → Net = $50K, check concentration against $50K not $100K → **Net calculation required**

#### Category Cardinality
- [ ] Test 3.10: Category with 100 accounts, largest = 26% → **Flag as legitimate risk**
- [ ] Test 3.11: Category with 1 account, 100% → **Flag with note "single account category"**
- [ ] Test 3.12: Category with 2 accounts (50/50 split) → **Both flag at 50% (expected for bipolar category)**
- [ ] Test 3.13: Category with 1000 accounts, largest = 0.2% → **MUST NOT flag (below 25%)**

#### Materiality Interaction
- [ ] Test 3.14: Concentration account = 30% of category, but category = 0.5% of assets (immaterial) → **Should note "material concentration of immaterial category"**
- [ ] Test 3.15: Concentration account = 30% of category, category = 50% of assets → **Flag as high-risk (30% * 50%)**
- [ ] Test 3.16: Concentration threshold = 25%, actual = 25.0000001% → **Boundary test: should flag (>25%)**
- [ ] Test 3.17: Concentration threshold = 25%, actual = 24.9999999% → **Boundary test: should NOT flag (<25%)**

#### Multi-Sheet Consolidation
- [ ] Test 3.18: Sheet1: AR = 20% of assets; Sheet2: AR = 30% of assets; Consolidated: AR = 25% of assets → **Flag per-sheet and consolidated**
- [ ] Test 3.19: Consolidation with intercompany elimination missing → **Intercompany AR not flagged as concentration (needs marker)**
- [ ] Test 3.20: Two subsidiaries, both have same customer as 15%, consolidated = 30% → **Flag consolidated, not individual sheets (unless cross-subsidiary)**

#### Industry Customization
- [ ] Test 3.21: Manufacturing industry with 50% threshold (vs. default 25%) → **Uses industry-specific threshold**
- [ ] Test 3.22: Retail with 30% threshold, account = 29% → **MUST NOT flag (below 30%)**
- [ ] Test 3.23: No industry specified → **Uses default 25% threshold**

#### Zero Storage Compliance
- [ ] Test 3.24: Flagged concentration account name not stored, only count and percentage → **Verify no account names in DB**
- [ ] Test 3.25: Result stores category_name (safe: not financial data), but not account_name → **Validate schema**

#### Defensive Coding
- [ ] Test 3.26: Category total = 0, flag threshold = 25% → **Graceful error, not division-by-zero crash**
- [ ] Test 3.27: Account balance = NaN or inf → **Catch, log, skip that account**
- [ ] Test 3.28: Category with only null/NaN accounts → **Return empty results, not error**
- [ ] Test 3.29: Threshold = 0% (everything is concentration) → **Validation: threshold must be >0 and <100%**
- [ ] Test 3.30: Threshold = 150% (impossible) → **Validation: threshold must be <=100%**

### Defense Strategy

**Defensive Coding Requirements:**

```
1. CATEGORY AGGREGATION
   - [ ] Group accounts by category (use AccountClassifier.classify())
   - [ ] For each category, sum account balances (net of contra-accounts)
   - [ ] Skip categories with total = 0 (return empty for that category)

2. CONCENTRATION CALCULATION
   - [ ] For each account in category:
     * concentration = abs(account_balance) / abs(category_total)
     * percentage = concentration * 100
     * flag if percentage > threshold (default 25%)
   - [ ] Use absolute values to handle negative balances uniformly

3. THRESHOLD MANAGEMENT
   - [ ] Default threshold: 25%
   - [ ] Allow override per industry (from Client.industry)
   - [ ] Allow override per session (materiality sensitivity settings)
   - [ ] Validate: 0 < threshold <= 100

4. CONTRA-ACCOUNT HANDLING
   - [ ] Detect contra-accounts using keyword matching (e.g., "Allowance", "Provision", "Discount")
   - [ ] When calculating category total, add contra-accounts separately
   - [ ] Track gross vs. net: return both metrics in result
   - [ ] Flag concentration against NET total (more conservative)

5. CARDINALITY NOTE
   - [ ] If category has only 1 account: include note "single account category" in result
   - [ ] If category has only 2 accounts: include note "bipolar category (2 accounts)" in result
   - [ ] Context helps users interpret concentration risk

6. ERROR HANDLING
   - [ ] Try/except for division (category_total = 0)
   - [ ] Validate account_balance is numeric before division
   - [ ] If any account is NaN/inf, skip and log (do NOT store name)

7. ZERO-STORAGE
   - [ ] Store ONLY: concentration_count (int), high_concentration_percent (float), category_name (str)
   - [ ] Do NOT store: account_name, account_number, specific_balance
   - [ ] Log via log_secure_operation() like audit_engine.py

8. MULTI-SHEET HANDLING
   - [ ] Calculate concentration per sheet independently
   - [ ] Also calculate for consolidated totals
   - [ ] Return per-sheet and consolidated results separately
```

### Zero-Storage Risk Assessment

**Risk Level:** HIGH (must avoid storing concentrated account names)

- **Critical:** Do NOT log account names when flagging concentration
- **Current Mitigation:** None yet; need new logging pattern
- **Action:**
  - [ ] Create new function: `flag_concentration_secure(category_name, concentration_pct, threshold)`
  - [ ] Test: Query logs, verify no account names appear
  - [ ] Verify: Result schema has no account_name field

### Estimated Test Count
- **Unit tests:** 30 tests (concentration calculation, contra-accounts, thresholds, cardinality)
- **Integration tests:** 10 tests (multi-sheet, materiality interaction, industry-specific)
- **Security tests:** 3 tests (zero-storage compliance, keyword filtering)
- **Total:** **43 tests**

---

## Feature 4: Rounding Anomaly Scanner

### Purpose
Detect accounts with balances that are exact multiples of 1000/10000/100000 (possible manual entry placeholder).

### Failure Modes

| Failure Mode | Trigger | Impact | Detection |
|--------------|---------|--------|-----------|
| **Legitimate Round Numbers** | Revenue = $1,000,000 exactly (common for lump-sum contracts) | Flagged as suspicious placeholder | No context that round = legitimate |
| **Currency Rounding Differences** | EUR: $10,000 = €9,500 (legitimately round in EUR, not USD) | False positive in multi-currency environment | Assumes USD rounding rules |
| **Accounting Software Defaults** | QuickBooks or Xero may auto-round large numbers to nearest $1000 | Legitimate software behavior flagged as error | No ERP/software awareness |
| **Divisibility Multiple Ambiguity** | $5,000 is divisible by 1000, 100, 10, 1; which multiple is "suspicious"? | Unclear which multiple threshold triggers flag | Multiple thresholds cause confusion |
| **False Negative: Clever Placeholder** | Placeholder = $1,000,001 (just above $1M to avoid detection) | Misses intentional obfuscation | Only checks exact multiples |
| **Periodic Entries** | Accrual = $12,000 (legitimate: $1000/month * 12) | Flagged as possible placeholder | No temporal context |
| **Negative Placeholders** | Reversal = -$1,000,000 (may be legitimate reversal) | Flagged, but direction should be tracked | No polarity context |
| **Tax Estimation Threshold** | Tax provision = $100,000 exactly (conservative estimate, rounded for safety) | Flagged as placeholder when it's actually best estimate | No domain knowledge of tax accounting |
| **Materiality Inflation** | $1000 rounding flag on $50M TB (0.002% error) | Low-value finding distracts from material issues | No materiality filter |
| **Multi-Round Detection** | $1,000,000 is divisible by both 1000 AND 100000 (flags twice?) | Unclear flagging logic for overlapping multiples | No deduplication of multiple thresholds |

### Test Scenario Checklist

#### Core Detection
- [ ] Test 4.1: Account balance = $1,000 (divisible by 1000) → **SHOULD flag** (possible placeholder)
- [ ] Test 4.2: Account balance = $1,500 (not divisible by 1000) → **SHOULD NOT flag**
- [ ] Test 4.3: Account balance = $10,000,000 (divisible by 1000, 10000, 100000) → **Flag once, not 3x**
- [ ] Test 4.4: Account balance = $9,999 (not round) → **SHOULD NOT flag**
- [ ] Test 4.5: Account balance = $100,000 (divisible by 100000) → **SHOULD flag**

#### Divisibility Thresholds
- [ ] Test 4.6: Define thresholds: 1000, 10000, 100000 → Test each independently
- [ ] Test 4.7: $5,000 = divisible by 1000 only → **Flag with divisor=1000**
- [ ] Test 4.8: $50,000 = divisible by 1000, 10000 only → **Flag, highest divisor=10000**
- [ ] Test 4.9: $1,000,000 = divisible by 1000, 10000, 100000 → **Flag once, divisor=100000**
- [ ] Test 4.10: $3,000 = divisible by 1000 only → **Flag with divisor=1000**

#### Materiality Filter
- [ ] Test 4.11: Rounding flag on $1000 account (0.001% of $100M TB) → **SHOULD NOT flag (immaterial)**
- [ ] Test 4.12: Rounding flag on $100,000 account (1% of $10M TB) → **Should flag (material enough)**
- [ ] Test 4.13: Rounding flag on $50,000 account (5% of $1M TB) → **SHOULD flag (high %)**
- [ ] Test 4.14: Audit materiality = 5%; account is 3% of assets but $100K round → **FLAG with "near materiality" note**

#### Negative Balances
- [ ] Test 4.15: Account balance = -$1,000 (round, negative) → **SHOULD flag (reversals can be placeholders)**
- [ ] Test 4.16: Account balance = -$1,500 (negative, not round) → **SHOULD NOT flag**
- [ ] Test 4.17: Asset with -$100,000 (abnormal balance + round) → **FLAG both issues separately**

#### Temporal Context (Accruals & Provisions)
- [ ] Test 4.18: Accrual = $12,000 (monthly provision $1000 * 12) → **Should NOT flag (explain pattern)**
- [ ] Test 4.19: Estimated tax = $50,000 (best estimate, happens to be round) → **MAY flag with context "estimate"**
- [ ] Test 4.20: Monthly revenue exactly $50,000 (accrual pattern, not placeholder) → **Context helps avoid false positive**

#### Edge Cases
- [ ] Test 4.21: Balance = $0 (divisible by everything) → **SHOULD NOT flag (zero is expected)**
- [ ] Test 4.22: Balance = $1 (indivisible) → **SHOULD NOT flag**
- [ ] Test 4.23: Balance = $999.99 (rounding noise, not placeholder) → **SHOULD NOT flag (< $1000)**
- [ ] Test 4.24: Empty category (no accounts) → **Return empty results, not error**
- [ ] Test 4.25: Balance = very large ($9.99E+15, floating-point rounding) → **Distinction: legitimate rounding vs. placeholder**

#### Multi-Sheet Behavior
- [ ] Test 4.26: Sheet1 has $100K round account; Sheet2 has $1M round account → **Flag both separately per sheet**
- [ ] Test 4.27: Consolidation sums: $100K + $1M = $1.1M (not round) → **Consolidated NOT flagged, but individual sheets are**
- [ ] Test 4.28: All sheets have same $1M account → **Flag once per sheet, aggregate count in summary**

#### Zero Storage Compliance
- [ ] Test 4.29: Flagged account names not stored, only count and divisor → **Verify no account details in logs**
- [ ] Test 4.30: Multiple flagged accounts: store count=5, not individual names → **Check database schema**

#### Defensive Coding
- [ ] Test 4.31: Division by zero when checking divisibility (threshold = 0) → **Validation: threshold > 0**
- [ ] Test 4.32: Account balance = NaN or inf → **Catch, log (no name), skip**
- [ ] Test 4.33: Negative threshold (e.g., divisor = -1000) → **Validation: divisors must be positive**
- [ ] Test 4.34: Account balance is string, not float → **Try/except on numeric conversion**

### Defense Strategy

**Defensive Coding Requirements:**

```
1. DIVISIBILITY THRESHOLDS
   - [ ] Define list: thresholds = [1000, 10000, 100000]
   - [ ] For each account balance:
     * highest_divisor = None
     * for threshold in thresholds:
     *   if account_balance % threshold == 0: highest_divisor = threshold
     * if highest_divisor is not None: flag it (once per balance, not per threshold)
   - [ ] Result: { account_balance, highest_divisor, is_flagged=True }

2. MATERIALITY FILTER
   - [ ] Calculate materiality as % of total assets (or largest category)
   - [ ] If flag_balance / total_assets < MATERIALITY_THRESHOLD: suppress flag
   - [ ] MATERIALITY_THRESHOLD = 0.1% (0.001) by default; configurable per audit
   - [ ] Store reason: "immaterial rounding ($100 = 0.001% of $10M)"

3. ZERO BALANCE HANDLING
   - [ ] If balance = 0: skip (divisible by everything, not a placeholder indicator)
   - [ ] If balance < 1: skip (below rounding threshold)

4. NEGATIVE BALANCE HANDLING
   - [ ] Use absolute value for divisibility check
   - [ ] Track sign separately: "suspicious_reversal_-$100,000"
   - [ ] Combine with abnormal balance detection

5. MULTI-THRESHOLD DEDUPLICATION
   - [ ] Only report highest divisor (e.g., if divisible by 1000, 10000, 100000, report 100000)
   - [ ] Reason: higher divisor = stronger indicator of placeholder

6. ERROR HANDLING
   - [ ] Try/except for float % modulo operation
   - [ ] Validate thresholds are positive integers
   - [ ] Validate account_balance is numeric (try float conversion)
   - [ ] If account is NaN/inf: log (no name), skip, continue

7. ZERO-STORAGE
   - [ ] Store ONLY: flagged_count (int), highest_divisor_used (int array), timestamp
   - [ ] Do NOT store: account_name, account_number, account_balance
   - [ ] Use log_secure_operation() pattern

8. MULTI-SHEET HANDLING
   - [ ] Check each sheet independently
   - [ ] Sum flagged accounts across sheets for consolidated summary
   - [ ] Report per-sheet and consolidated results
```

### Zero-Storage Risk Assessment

**Risk Level:** MEDIUM (account balances are technically aggregate data if only "count" stored)

- **Current Mitigation:** Only store count of flagged accounts, not balance amounts or names
- **Action:**
  - [ ] Ensure database schema has no balance field in rounding_anomalies table
  - [ ] Test: Query database, verify only count and divisor stored, no balance amounts
  - [ ] Verify: API response never includes specific account balances

### Estimated Test Count
- **Unit tests:** 34 tests (divisibility, materiality, thresholds, negative balances, edge cases)
- **Integration tests:** 7 tests (multi-sheet, consolidation, materiality interaction)
- **Security tests:** 2 tests (zero-storage compliance, account name filtering)
- **Total:** **43 tests**

---

## Feature 5: Contra-Account Validator

### Purpose
Match depreciation accounts with corresponding asset accounts and flag ratio anomalies (e.g., accumulated depreciation > gross asset value).

### Failure Modes

| Failure Mode | Trigger | Impact | Detection |
|--------------|---------|--------|-----------|
| **Keyword False Positives** | Account "Depreciation Expense" matches "Depreciation" but isn't accumulated depreciation | Pairs with unrelated assets | Keyword matching without context |
| **Contra-Account Mismatch** | Equipment Asset = $1M, but A.D. Allowance (unrelated) = $800K | Validator pairs wrong asset with wrong contra | Fuzzy keyword matching, no GL reference linking |
| **Partial Contra-Account** | Gross Equipment = $1M, but only 2 of 5 depreciation accounts matched | Incomplete validation; misses some depreciation | Different naming conventions across GL |
| **Asset Fully Depreciated** | Gross Asset = $100K, A.D. = $100K (100% depreciated, normal) | Flagged as ratio anomaly | Assumes A.D. should be <80% or similar |
| **Acquisition Mid-Year** | Asset purchased Sept 1; A.D. = $50K (only 4 months depreciation); ratio = 5% | Flag as "suspiciously low depreciation" | No knowledge of acquisition date |
| **Negative Contra Balance** | Gross Equipment = $1M, A.D. shown as POSITIVE instead of NEGATIVE | Validation breaks; assumes contra always negative | Ledger entry error or classification error |
| **Multiple Depreciation Methods** | Some assets STRAIGHT-LINE (A.D. = 50% over 10 years), others ACCELERATED (A.D. = 70% over 5 years) | Flags accelerated as anomalous | Assumes single depreciation method |
| **Intangible Asset Amortization** | Goodwill Asset = $500K, Amortization Expense = $50K/year; Contra = $150K (3-year accumulation) | Validated as if tangible asset depreciation | Different amortization patterns for intangibles |
| **Leasehold Improvements** | GL shows "Leasehold Improvements", "Right-of-Use Asset (post-ASC842)", "Depreciation Expense" | Both ROU and leasehold improvements depreciate; hard to match | Lease accounting complexity |
| **Consolidated Multi-Entity** | Parent + 2 Subsidiaries; subsidiary A.D. not matched to parent assets | Assumes all assets/contra in same entity | Consolidation hierarchy not modeled |
| **Currency & Scale** | Equipment (USD): $1M, A.D. (stored in cents): $800,000.00 cents = $8,000 | Ratio anomaly flagged due to unit mismatch | No currency normalization |
| **Vintage Ledger Data** | Historical account balance mixed with current; old A.D. from retired asset still on books | A.D. > current asset = ratio anomaly (false) | No accounting for retired assets |

### Test Scenario Checklist

#### Core Matching
- [ ] Test 5.1: Equipment Asset = $1M, Accumulated Depreciation Equipment = $400K → **MUST match, flag if ratio > 80%**
- [ ] Test 5.2: Building Asset = $5M, Accumulated Depreciation Building = $2M → **MUST match, ratio = 40% (OK)**
- [ ] Test 5.3: Equipment = $1M, Vehicles = $500K, A.D. Equipment = $400K, A.D. Vehicles = $100K → **Match pairs independently**
- [ ] Test 5.4: Asset with no corresponding depreciation account → **Flag as "missing depreciation" (asset too new?)**
- [ ] Test 5.5: Depreciation account with no corresponding asset → **Flag as "orphaned depreciation" (asset retired?)**

#### Ratio Anomaly Detection
- [ ] Test 5.6: Gross Asset = $1M, A.D. = $900K (90% depreciated) → **Ratio OK for aging asset, no anomaly**
- [ ] Test 5.7: Gross Asset = $1M, A.D. = $1M (100% depreciated, fully used) → **OK (asset fully depreciated)**
- [ ] Test 5.8: Gross Asset = $1M, A.D. = $1.1M (>100%, impossible) → **FLAG as critical anomaly (ledger error)**
- [ ] Test 5.9: Gross Asset = $1M, A.D. = $50K (5% depreciated, new asset) → **OK (ratio normal)**
- [ ] Test 5.10: Gross Asset = $500K, A.D. = $600K (>100%, impossible) → **CRITICAL FLAG**

#### Matching Tolerance
- [ ] Test 5.11: "Equipment" asset matched with "Deprec. Equip" contra (typo "Deprec") → **SHOULD match (fuzzy)**
- [ ] Test 5.12: "Furniture & Fixtures" asset matched with "Accumulated Depreciation - FF" → **Fuzzy match OK, but confidence?**
- [ ] Test 5.13: "Leasehold Improvements" vs. "ROU Asset" (different but related) → **Should NOT match (different accounts)**
- [ ] Test 5.14: "Intangible Assets" vs. "Accumulated Amortization" → **MAY match if configured (intangibles)**
- [ ] Test 5.15: "Plant Equipment" vs. "Equipment Allowance" → **Fuzzy match confidence threshold test**

#### Acquisition & Vintage Context
- [ ] Test 5.16: New equipment purchased Dec 1 current year; A.D. = $2K (1 month) → **Ratio 0.2% is normal, no anomaly**
- [ ] Test 5.17: Equipment purchased 15 years ago (fully depreciated); A.D. = Gross Asset → **100% depreciation OK**
- [ ] Test 5.18: Equipment vintage mix: some assets 1 year old, some 10 years old → **Average ratio expected, not uniform**
- [ ] Test 5.19: Fully depreciated asset still on books (common practice); A.D. = Gross → **No anomaly, expected for retired assets still tracked**

#### Depreciation Method Variance
- [ ] Test 5.20: Straight-line depreciation: A.D. ≈ 40% for 5-year asset in year 2 → **OK**
- [ ] Test 5.21: Accelerated depreciation: A.D. ≈ 60% for 5-year asset in year 2 → **OK (different method)**
- [ ] Test 5.22: Mixed methods across asset classes: some 40%, some 70% → **No anomaly across classes, only within class**

#### Multi-Entity & Consolidation
- [ ] Test 5.23: Parent + Subsidiary; asset = $2M (consolidated), A.D. = $800K → **Validate at consolidated level**
- [ ] Test 5.24: Intercompany asset sold (removed from one subsidiary, not parent); A.D. mismatch → **Flag with "possible elimination needed"**

#### Negative Balances & Sign Errors
- [ ] Test 5.25: A.D. shown as negative (correct, contra-account sign) → **Handle correctly**
- [ ] Test 5.26: A.D. shown as POSITIVE (ledger entry error) → **Flag as sign anomaly**
- [ ] Test 5.27: Gross Asset = -$500K (classification error, asset shown as negative) → **FLAG separately (abnormal asset balance)**

#### Zero Storage Compliance
- [ ] Test 5.28: Matched asset/contra pairs identified but names not stored → **Verify no account names in logs**
- [ ] Test 5.29: Anomaly count and ratio stored, not account details → **Verify database schema**

#### Edge Cases & Error Handling
- [ ] Test 5.30: Asset balance = $0 (asset fully written off or data error) → **Skip or flag separately**
- [ ] Test 5.31: A.D. balance = $0 (asset not depreciated yet, e.g., purchase of $0 book value) → **OK (early stage)**
- [ ] Test 5.32: Asset balance = NaN or inf → **Catch, log (no name), skip**
- [ ] Test 5.33: Multiple assets with same name (ambiguous matching) → **Flag ambiguity, ask user to clarify**
- [ ] Test 5.34: No depreciation thresholds configured → **Use default 80% max A.D. threshold**
- [ ] Test 5.35: Depreciation threshold = 0% or 200% (invalid) → **Validation: 0 < threshold <= 100%**
- [ ] Test 5.36: Empty trial balance (no asset accounts) → **Return empty results, not error**

### Defense Strategy

**Defensive Coding Requirements:**

```
1. ASSET/CONTRA MATCHING
   - [ ] Use fuzzy keyword matching (Levenshtein distance ≤ 2, see account_classifier.py)
   - [ ] Keywords for assets: ["equipment", "building", "vehicle", "machinery", "furniture", "fixtures", "leasehold", "intangible", "goodwill"]
   - [ ] Keywords for contra: ["accumulated", "depreciation", "amortization", "allowance"]
   - [ ] Match strategy: If asset name contains "Equipment" AND contra name contains "Equipment" + "Depreciation", pair them
   - [ ] Confidence score for each match (0.0 to 1.0)

2. RATIO ANOMALY THRESHOLDS
   - [ ] Normal max A.D. ratio: 80% (asset < 6 years old at 10-year life)
   - [ ] Critical threshold: 100% (A.D. > asset, impossible)
   - [ ] Warning threshold: 95% (nearly fully depreciated)
   - [ ] Configurability: Allow per-asset-class override (e.g., intangibles: 100%)

3. ASSET CLASSIFICATION DEPENDENCY
   - [ ] Only validate assets classified as ASSET (not expense/liability)
   - [ ] Check for contra-accounts (negative normal balance) explicitly
   - [ ] Skip validation if asset classification confidence < 70%

4. VALIDATION LOGIC
   - [ ] For each asset account:
     * Find matching depreciation/amortization accounts (fuzzy match + keyword)
     * If match found: ratio = abs(contra_balance) / abs(asset_balance)
     *   If ratio > 1.0: FLAG as critical (A.D. > asset)
     *   If ratio > 0.8: FLAG as warning (high depreciation)
     *   If ratio = 0.0: FLAG as info (new asset or error?)
     * If no match found: FLAG as "missing depreciation" (asset type-dependent)
     * If match NOT found and asset is OLD: may be OK (retired asset, no depreciation)

5. DEPRECIATION METHOD AWARENESS
   - [ ] Store expected depreciation schedule per asset class (optional)
   - [ ] Straight-line: ratio ≈ age / useful_life
   - [ ] Accelerated: ratio may be 2x higher in early years
   - [ ] If no schedule provided, use generic expectations (0-80% range normal)

6. MULTI-ENTITY HANDLING
   - [ ] Validate each legal entity independently
   - [ ] For consolidated TB, validate consolidated totals
   - [ ] Flag "possible consolidation elimination" if aggregation suspicious

7. ERROR HANDLING
   - [ ] Try/except for division (asset_balance = 0)
   - [ ] Validate balances are numeric
   - [ ] If NaN/inf: log (no name), skip
   - [ ] Check sign of contra (should be opposite of asset normal balance)

8. MATCHING CONFIDENCE
   - [ ] Return match_confidence for each pair (0.0 to 1.0)
   - [ ] If confidence < 50%, flag as "uncertain match, manual review recommended"
   - [ ] If no confident match found, return "no matching depreciation found"

9. ZERO-STORAGE
   - [ ] Store ONLY: paired_count (int), anomaly_count (int), high_ratio_percent (float)
   - [ ] Do NOT store: asset_name, contra_name, account_number, balance amounts
   - [ ] Use log_secure_operation() pattern

10. MULTI-SHEET HANDLING
    - [ ] Validate each sheet independently
    - [ ] For consolidated totals, validate consolidated pairs
    - [ ] Report per-sheet and consolidated results
```

### Zero-Storage Risk Assessment

**Risk Level:** HIGH (account names and matching logic must not leak financial details)

- **Critical:** Do NOT log asset names or depreciation account names when flagging anomalies
- **Current Mitigation:** None yet; need new secure matching pattern
- **Action:**
  - [ ] Create new function: `validate_contra_accounts_secure(category_totals)`
   Returns only: { anomaly_count, high_ratio_count, timestamp }
  - [ ] Test: Query logs/database, verify no account names appear
  - [ ] Verify: Return schema has no account names or identifiers

### Estimated Test Count
- **Unit tests:** 36 tests (matching, ratio anomalies, thresholds, depreciation methods, signs)
- **Integration tests:** 8 tests (multi-sheet, consolidation, mixed asset types)
- **Security tests:** 3 tests (zero-storage compliance, fuzzy matching validation)
- **Total:** **47 tests**

---

## Summary: Test Count Estimate

| Feature | Unit Tests | Integration Tests | Security Tests | **Total** |
|---------|:----------:|:-----------------:|:--------------:|:---------:|
| 1. Suspense Detector | 26 | 5 | 3 | **34** |
| 2. Balance Sheet Validator | 23 | 8 | 3 | **34** |
| 3. Concentration Risk | 30 | 10 | 3 | **43** |
| 4. Rounding Anomaly | 34 | 7 | 2 | **43** |
| 5. Contra-Account Validator | 36 | 8 | 3 | **47** |
| **PHASE III TOTAL** | **149** | **38** | **14** | **201** |
| Current Backend Coverage | - | - | - | **232** |
| **Post-Phase III Total** | - | - | - | **433** |

---

## Test Suite Infrastructure Requirements

### New Test Files to Create
```
backend/tests/test_suspense_detector.py          [34 tests]
backend/tests/test_balance_sheet_validator.py    [34 tests]
backend/tests/test_concentration_detector.py     [43 tests]
backend/tests/test_rounding_anomaly_scanner.py   [43 tests]
backend/tests/test_contra_account_validator.py   [47 tests]
backend/tests/conftest.py                        [shared fixtures]
```

### Shared Test Fixtures (conftest.py)

All features will need:

```python
# Multi-scenario fixtures
@pytest.fixture
def healthy_trial_balance()       # Balanced, clean data
@pytest.fixture
def unbalanced_trial_balance()    # Balanced test failure
@pytest.fixture
def unicode_trial_balance()       # UTF-8 account names
@pytest.fixture
def empty_trial_balance()         # No data rows
@pytest.fixture
def single_account_tb()           # 1 account edge case
@pytest.fixture
def large_tb_10000_rows()         # Chunking test
@pytest.fixture
def multi_sheet_workbook()        # Excel with 3 sheets
@pytest.fixture
def negative_equity_tb()          # Insolvency scenario
@pytest.fixture
def fully_depreciated_tb()        # Asset edge case
@pytest.fixture
def mixed_currency_tb()           # USD + EUR scenario
```

### Defensive Coding Patterns

All five features must follow these patterns:

```python
# 1. Zero-Storage Logging
from security_utils import log_secure_operation

log_secure_operation("suspense_detector", f"Found {count} suspense accounts")
# NOT: log_secure_operation("suspense_detector", f"Accounts: {names}")

# 2. Safe Numeric Conversion
try:
    balance = float(account_balance)
except (ValueError, TypeError):
    log_secure_operation("detector_error", f"Failed to parse balance (not storing name)")
    continue

# 3. Graceful Error Handling
if category_total == 0:
    return {"flagged": False, "reason": "zero_category"}
if math.isnan(balance) or math.isinf(balance):
    log_secure_operation("detector_error", "Invalid numeric value (not storing)")
    return None

# 4. Multi-Sheet Aggregation
results_per_sheet = [validate_sheet(sheet) for sheet in workbook.sheets]
consolidated = aggregate_results(results_per_sheet)
return {"per_sheet": results_per_sheet, "consolidated": consolidated}

# 5. Fuzzy Matching (existing pattern)
from account_classifier import fuzzy_match_score
score = fuzzy_match_score(account_name, keyword, max_distance=2)
if score >= 0.6:  # Match confidence threshold
    matched_accounts.append((account_name, score))
```

---

## Critical Checklist: Pre-Implementation

Before implementing ANY feature, verify:

### Codebase Review
- [ ] Read ratio_engine.py for CategoryTotals structure (baseline for all features)
- [ ] Review account_classifier.py fuzzy matching pattern (reuse for features 3, 5)
- [ ] Review audit_engine.py error handling (reuse try/except patterns)
- [ ] Verify security_utils.log_secure_operation() is the logging standard

### Database Schema Validation
- [ ] Ensure no new schema stores account names or balances
- [ ] DiagnosticSummary.to_dict() never includes account details
- [ ] Create new tables if needed (e.g., SuspenseDetectionResult with only: flagged_count, severity, timestamp)

### Test Environment
- [ ] Run existing 232 tests; all must pass before Phase III implementation
- [ ] Verify pytest.ini and conftest.py configuration
- [ ] Set up GitHub Actions (if applicable) to run all 433 tests on commit

### API Response Schema
- [ ] Define Pydantic models for each feature's return value (e.g., SuspenseDetectionResult, BalanceSheetValidation)
- [ ] Ensure no account identifiers in response
- [ ] Add to FastAPI endpoints in main.py

### Frontend Integration (Out of Scope for QualityGuardian, but noted)
- [ ] React components for each feature's result display
- [ ] Tooltip documentation for each finding type
- [ ] "Learn More" links to accounting standards (docs/STANDARDS.md)

---

## Risk Assessment: Highest-Risk Features

### Rank 1: Feature 5 (Contra-Account Validator)
- **Risk:** Fuzzy matching between assets and depreciation can fail silently
- **Mitigation:** Test with 50+ real GL combinations; high confidence threshold (>70%)
- **Complexity Score:** 9/10

### Rank 2: Feature 3 (Concentration Risk Detector)
- **Risk:** False positives on single-account categories; materiality interaction
- **Mitigation:** Extensive cardinality testing; configurable threshold per industry
- **Complexity Score:** 8/10

### Rank 3: Feature 4 (Rounding Anomaly Scanner)
- **Risk:** Legitimate round numbers flagged as placeholders
- **Mitigation:** Materiality filter; context notes (accrual, estimate)
- **Complexity Score:** 7/10

### Rank 4: Feature 2 (Balance Sheet Validator)
- **Risk:** Relative tolerance calculation; floating-point precision at large scales
- **Mitigation:** Comprehensive floating-point tests; relative vs. absolute tolerance
- **Complexity Score:** 6/10

### Rank 5: Feature 1 (Suspense Detector)
- **Risk:** Keyword list may miss international account names
- **Mitigation:** Fuzzy matching; zero-storage strict logging
- **Complexity Score:** 5/10

---

## Next Steps: Agent Council Consensus Needed

This analysis presents 5 features with distinct complexity/risk profiles:

1. **Quick Wins (5-7 days):** Feature 1 (Suspense) + Feature 2 (Balance Sheet) - Lower risk, testable
2. **Medium Effort (7-10 days):** Feature 4 (Rounding) - Clear logic, good test coverage
3. **High Effort (10-14 days):** Feature 3 (Concentration) - Industry-specific, materiality interaction
4. **Expert Level (14-21 days):** Feature 5 (Contra-Account) - Fuzzy matching, depreciation context

**Recommendation:** Implement in order 1 → 2 → 4 → 3 → 5, with feature pairing (1+2, then 4, then 3+5).

---

## Failure-Mode Analysis Complete

**Total Failure Scenarios Identified:** 76
**Total Test Scenarios Recommended:** 201
**Zero-Storage Compliance Checks:** 14
**Defensive Coding Patterns Defined:** 10

All features are **approvable for Phase III implementation** pending:
1. Agent Council consensus on complexity scores and sequencing
2. Approval of 201-test suite approach
3. CEO directive on industry-specific customization (Feature 3, 5)

