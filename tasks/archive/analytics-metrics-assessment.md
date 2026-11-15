# Analytics Engine & Metrics Assessment

> **Date:** 2026-02-28
> **Scope:** Full inventory of current metrics, gap analysis, and recommendations for additional derivable metrics
> **Methodology:** Code-level audit of all 22 backend engines, frontend display surfaces, data models, and response schemas — cross-referenced against ISA/PCAOB/IFRS/GAAP analytical procedure requirements

---

## 1. Current Metrics Inventory

### 1.1 Core Financial Ratios (12) — `ratio_engine.py`

| # | Ratio | Formula | Category |
|---|-------|---------|----------|
| 1 | Current Ratio | Current Assets / Current Liabilities | Liquidity |
| 2 | Quick Ratio | (Current Assets - Inventory) / Current Liabilities | Liquidity |
| 3 | Debt-to-Equity | Total Liabilities / Total Equity | Solvency |
| 4 | Gross Margin | (Revenue - COGS) / Revenue | Profitability |
| 5 | Net Profit Margin | (Revenue - Total Expenses) / Revenue | Profitability |
| 6 | Operating Margin | Operating Income / Revenue | Profitability |
| 7 | Return on Assets | Net Income / Total Assets | Profitability |
| 8 | Return on Equity | Net Income / Total Equity | Profitability |
| 9 | Days Sales Outstanding | (AR / Revenue) x 365 | Efficiency |
| 10 | Days Payable Outstanding | (AP / COGS) x 365 | Efficiency |
| 11 | Days Inventory Outstanding | (Inventory / COGS) x 365 | Efficiency |
| 12 | Cash Conversion Cycle | DSO + DIO - DPO | Efficiency |

### 1.2 Industry-Specific Ratios (~110) — `industry_ratios.py`
- 8-10 ratios per industry x 12 industries (Technology, Healthcare, Financial Services, Manufacturing, Retail, Professional Services, Real Estate, Construction, Hospitality, Nonprofit, Education, Other)
- Includes asset turnover, inventory turnover, receivables turnover (but only for specific industries — not universally exposed)

### 1.3 TB Diagnostic Analytics (8 Engines)

| Engine | File | Key Outputs |
|--------|------|-------------|
| Population Profile | `population_profile_engine.py` | Gini coefficient, magnitude buckets (6-tier), top-10 accounts, account density (9-section) |
| Flux Analysis | `flux_engine.py` | Per-account delta ($ + %), risk classification, sign flips, new/removed accounts, reclassification detection |
| Pre-Flight Report | `preflight_engine.py` | Readiness score (0-100), column confidence, data quality issues |
| Expense Category | `expense_category_engine.py` | ISA 520 5-category decomposition (COGS, Payroll, D&A, Interest/Tax, Other OpEx), ratios-to-revenue |
| Accrual Completeness | `accrual_completeness_engine.py` | Run-rate ratio, threshold comparison |
| Lease Diagnostic | `lease_diagnostic_engine.py` | IFRS 16/ASC 842 4-test consistency battery |
| Cutoff Risk | `cutoff_risk_engine.py` | ISA 501 3-test deterministic battery |
| Going Concern | `going_concern_engine.py` | ISA 570 6-indicator profile |

### 1.4 Testing Tool Batteries (98+ Tests, 9 Tools with Composite Scores)

| Tool | Tests | Standards | Composite Score |
|------|-------|-----------|-----------------|
| Journal Entry Testing | 19 (structural + statistical + advanced + holiday) | ISA 240, PCAOB AS 2401 | Yes |
| AP Payment Testing | 13 (structural + statistical + fraud indicators) | ISA 500 | Yes |
| Revenue Testing | 16 (structural + statistical + advanced + ASC 606/IFRS 15 contract) | ISA 240, ASC 606 | Yes |
| AR Aging | 11 (structural + statistical + advanced) | ISA 500/540 | Yes |
| Payroll Testing | 11 (structural + statistical + fraud indicators) | ISA 240 | Yes |
| Fixed Asset Testing | 9 (structural + statistical + advanced) | IAS 16/ASC 360 | Yes |
| Inventory Testing | 9 (structural + statistical + advanced) | IAS 2/ASC 330 | Yes |
| Three-Way Match | 2-tier PO-Invoice-Receipt matching | ISA 500 | No (match rate) |
| Statistical Sampling | MUS + random, Stringer bound | ISA 530/PCAOB AS 2315 | No (Pass/Fail) |

### 1.5 Trend & Variance Analysis — `ratio_engine.py`
- `TrendAnalyzer`: Linear regression, slope, R², mean/min/max/stddev per ratio across up to 36 periods
- `RollingWindowAnalyzer`: 3/6/12-month moving averages and volatility bands
- `VarianceAnalyzer`: Period-over-period dollar and percentage variance with direction classification

### 1.6 Engagement-Level Metrics
- Cross-tool account convergence index (flagged account overlap across tools)
- Per-tool composite score trends (run-over-run direction: improving/stable/degrading)
- Materiality cascade (overall → performance → trivial)
- Follow-up items tracking by severity/disposition
- Engagement completion gate (follow-up resolution enforcement)

### 1.7 Billing Analytics — `billing/analytics.py`
- 5 decision metrics: trial starts, trial-to-paid rate, paid-by-plan distribution, avg seats by tier, cancellations by reason
- Weekly review aggregation with period-over-period deltas

### 1.8 Benchmark Comparison — `benchmark_engine.py`
- Percentile ranking (P10/P25/P50/P75/P90) against industry data
- Per-ratio comparison with over/under assessment

---

## 2. Assessment: Strengths

1. **Comprehensive TB utilization.** The 12 core ratios + 8 diagnostic engines extract extensive value from trial balance data. The `CategoryTotals` structure captures the right aggregates.

2. **Standards alignment.** Every engine references specific ISA/PCAOB/IFRS/GAAP standards. The guardrail approach (factual/descriptive, no auditor judgment) is well-maintained.

3. **Testing depth.** 98+ automated tests across 9 tools with composite scoring provides genuine audit procedure support. The Benford's Law implementation with pre-check validation is rigorous.

4. **Zero-Storage compliance.** All computation is ephemeral. Only aggregate metadata (sums, ratios, scores) is persisted. The design is clean and consistent.

5. **Trend infrastructure.** The `TrendAnalyzer` and `RollingWindowAnalyzer` classes provide institutional-grade time-series analysis. The existing but unused `MOMENTUM_ACCELERATION` and `MOMENTUM_CHANGE` constants signal the architecture anticipated expansion.

---

## 3. Assessment: Gaps

### 3.1 Storage Gap
- **DSO, DPO, DIO, CCC are computed but NOT stored** in `DiagnosticSummary`. This means they cannot be trended across periods. The 4 most important working capital efficiency metrics lack historical persistence.

### 3.2 Missing Core Ratios
- **Equity Ratio** (Total Equity / Total Assets) — the solvency complement to debt-to-equity
- **Long-term Debt Ratio** (Non-current Liabilities / Total Assets) — derivable by subtraction (`total_liabilities - current_liabilities`)
- **Asset Turnover** (Revenue / Total Assets) — exists in `industry_ratios.py` for some sectors but not universally exposed in core `RatioEngine`
- **Inventory Turnover** (COGS / Inventory) — referenced in `benchmark_engine.py` RATIO_DIRECTION map but not implemented in core engine
- **Receivables Turnover** (Revenue / AR) — same as inventory turnover

### 3.3 Missing Decomposition & Bridge Analytics
- No DuPont decomposition (Net Margin x Asset Turnover x Equity Multiplier = ROE)
- No working capital decomposition (AR/Inventory/AP contribution percentages)
- No per-category population statistics (Gini coefficient is computed globally but not broken down by account category)
- Common-size analysis partially implemented (5 BS + 4 IS percentages) but missing AR, AP, inventory, non-current asset, and expense sub-category percentages
- Ratio momentum (second derivative — rate of change of change) anticipated by existing constants but not implemented

### 3.4 Missing Structural Metrics
- No deferred revenue coverage ratio (deferred revenue / total revenue)
- No prepaid-to-expense ratio
- No non-current asset composition breakdown (PP&E vs intangibles vs investments)
- No effective tax rate plausibility check
- No expense structure rigidity index (fixed vs variable cost proportions)

### 3.5 Missing Cross-Period & Cross-Tool Analytics
- No flagged account persistence tracking (same account flagged across consecutive engagements)
- No tool coverage velocity (time to N% coverage)
- No cross-tool composite score dispersion
- No normalized anomaly density rate (flagged items / total rows)
- No working capital trend persistence (consecutive periods of decline)

### 3.6 Language & Positioning Risks

| Location | Issue | Risk |
|----------|-------|------|
| `ratio_engine.py` `health_status` field | "healthy"/"warning"/"concern" are evaluative | Inconsistent with factual guardrail |
| `going_concern_engine.py` `severity` field | Ordinal severity on indicators alongside disclaimer | Creates contradiction with ISA 570 disclaimer |
| `flux_engine.py` `FluxRisk.HIGH` comment | "Significant unexplained variance" — word "unexplained" implies audit inference | Platform cannot know if variance is explained |
| `expense_category_engine.py` `exceeds_materiality` | Implies materiality determination (ISA 320 — auditor judgment) | Should be `exceeds_threshold` |
| `benchmark_engine.py` `HEALTH_SCORE_*` constants | Composite health score across ratios is risk scoring | CLAUDE.md notes this as deferred/rejected |

---

## 4. Recommended Additional Metrics

### Priority 0 — Immediate (Low Effort, High Impact)

#### R1: DSO/DPO/DIO/CCC Storage in DiagnosticSummary
- **What:** Add 4 columns to `DiagnosticSummary` to persist the already-computed cash cycle ratios
- **Why:** Without storage, these cannot be trended. CCC trend is among the most powerful working capital indicators for ISA 520
- **Effort:** 4 new Numeric columns + Alembic migration + save in diagnostics route
- **Data source:** Already computed in `ratio_engine.py` `calculate_dso()`, `calculate_dpo()`, `calculate_dio()`, `calculate_ccc()`

#### R2: Revenue-to-Expense Growth Differential
- **What:** Compare revenue growth rate vs expense growth rate between consecutive periods
- **Why:** ISA 520 core analytical procedure — margin compression is a leading indicator
- **Formula:** `(revenue_growth_% - expense_growth_%)`
- **Data source:** Two consecutive `DiagnosticSummary` records, same client

#### R3: Anomaly Density Rate (Normalized)
- **What:** `total_flagged / total_rows` as a per-tool normalized density
- **Why:** Makes anomaly counts comparable across different-sized populations
- **Data source:** Already computed — both values exist in every tool response

### Priority 1 — Near-Term (Low-Medium Effort, High Impact)

#### R4: Extended Solvency Ratio Set
- **What:** Equity Ratio, Long-term Debt Ratio, Asset Turnover added to core `RatioEngine`
- **Why:** ISA 315.A111 — entity-level solvency indicators. Auditors currently calculate these manually
- **Data source:** All inputs in `CategoryTotals` — three one-line additions to `calculate_all_ratios()`

#### R5: Inventory Turnover + Receivables Turnover (Core Promotion)
- **What:** Move from industry-specific to universal core ratios
- **Why:** Already referenced in `benchmark_engine.py` RATIO_DIRECTION map but not implemented in core engine
- **Formula:** COGS / Inventory; Revenue / AR
- **Data source:** `CategoryTotals.inventory`, `cost_of_goods_sold`, `accounts_receivable`, `total_revenue`

#### R6: Working Capital Trend Persistence
- **What:** Count consecutive periods where working capital has declined
- **Why:** ISA 570.A2 — consecutive decline is a stronger going concern signal than single-period snapshot
- **Data source:** Sequential `DiagnosticSummary` records (`current_assets - current_liabilities`)

#### R7: Equity Erosion Rate
- **What:** Period-over-period equity change as % of beginning equity
- **Why:** ISA 570.A3 — equity erosion is an explicit going concern indicator. Currently the engine checks point-in-time net liability, not the rate of change
- **Data source:** Sequential `DiagnosticSummary.total_equity`

#### R8: Composite Score Dispersion
- **What:** Standard deviation of composite scores across all tools in an engagement
- **Why:** A client with uniform 60s across tools is different from 20-90 range — dispersion signals uneven control quality
- **Data source:** `ToolRun.composite_score` for latest run per tool

### Priority 2 — Medium-Term (Medium Effort, High Impact)

#### R9: DuPont Decomposition
- **What:** ROE = Net Margin x Asset Turnover x Equity Multiplier with per-component prior-period deltas
- **Why:** ISA 315 Appendix 2 cites DuPont as an example analytical procedure. Traces ROE changes to source (margin vs efficiency vs leverage)
- **Data source:** `CategoryTotals` — requires R4 (Asset Turnover) as prerequisite

#### R10: Common-Size Analysis Expansion
- **What:** Extend partially implemented `CommonSizeAnalyzer` with AR%, Inventory%, Non-current Assets%, AP% of totals + income statement sub-category percentages from `expense_category_engine.py`
- **Why:** Common-size is a standard ISA 520 procedure. Current implementation covers only 9 line items; full coverage needs ~17
- **Data source:** `CategoryTotals` + classifier output + `expense_category_engine.py` sub-category amounts

#### R11: Per-Category Gini Coefficient
- **What:** Run existing `_compute_gini()` per account category (assets, liabilities, equity, revenue, expenses) instead of only globally
- **Why:** Global Gini = 0.72 doesn't tell the auditor which account class drives concentration. ISA 315 fraud risk assessment needs category-level granularity
- **Data source:** Account balances with classifications already produced by classifier

#### R12: Interperiod Ratio Momentum
- **What:** Second-derivative of key ratios (acceleration/deceleration) using the already-defined but unused `MOMENTUM_ACCELERATION` and `MOMENTUM_CHANGE` constants at `ratio_engine.py` lines 93-94
- **Why:** ISA 520.A8 — trend analysis. A ratio declining at an accelerating rate carries different significance than one with a decelerating decline
- **Data source:** Requires 3+ `DiagnosticSummary` records for same client

#### R13: Expense Structure Rigidity Index
- **What:** Ratio of fixed costs (D&A + Interest) to variable costs (COGS + Payroll + Other) using existing expense category decomposition
- **Why:** Higher fixed-cost structures amplify revenue declines into disproportionate profit impact — relevant for ISA 520 expectation setting and ISA 570 going concern
- **Data source:** Already computed in `expense_category_engine.py`

#### R14: Asset Composition Shift
- **What:** `current_assets / total_assets` ratio and its period-over-period change
- **Why:** Declining current-to-total asset ratio signals capital lockup. Important for ISA 540 estimation contexts
- **Data source:** `CategoryTotals` — single division

### Priority 3 — Longer-Term (Medium-High Effort)

#### R15: Working Capital Decomposition Profile
- **What:** Disaggregate working capital into AR/Inventory/AP/Other contribution percentages
- **Why:** ISA 500 — auditors need composition understanding, not just net totals. Closes the loop between AR Aging/Inventory Testing flags and aggregate TB position
- **Data source:** `CategoryTotals.accounts_receivable`, `inventory`, `accounts_payable`, `current_assets`, `current_liabilities`

#### R16: Non-Current Asset Composition Breakdown
- **What:** PP&E vs Intangibles vs Long-term Investments split using keyword classification
- **Why:** IAS 16/38/40, ASC 350/360 — auditors need separate disclosure. No TB-level mechanism currently exists
- **Data source:** Account names + keyword matching (consistent with existing `account_classifier.py` patterns)

#### R17: Deferred Revenue & Prepaid Profile
- **What:** Deferred Revenue Coverage = deferred_revenue / total_revenue; Prepaid-to-Expense = prepaid / total_expenses
- **Why:** ASC 606/IFRS 15 scrutiny. `cutoff_risk_engine.py` already identifies these accounts but doesn't ratio them
- **Data source:** Accounts identified by existing cutoff-sensitive keyword matcher + `CategoryTotals`

#### R18: Effective Tax Rate Plausibility
- **What:** ETR = income_tax_expense / pre_tax_income, compared to statutory rate range
- **Why:** ASC 740/IAS 12 — ETR plausibility is a standard analytical procedure. Requires isolating tax expense from `CAT_INTEREST_TAX`
- **Data source:** `expense_category_engine.py` sub-category + `CategoryTotals`

#### R19: Vendor/Customer HHI (Herfindahl-Hirschman Index)
- **What:** Sum of squared market shares for vendor (AP) and customer (AR/Revenue) concentration
- **Why:** HHI is the standard concentration metric (< 1500 competitive, 1500-2500 moderate, >2500 concentrated). More granular than top-customer %
- **Data source:** Vendor/customer amount distributions already computed in AP/AR/Revenue testing engines

#### R20: Flagged Account Persistence Score
- **What:** Track how many consecutive runs/engagements each account has been flagged
- **Why:** Persistence signals structural issues vs transient anomalies
- **Data source:** `ToolRun.flagged_accounts` across sequential runs

### Priority 4 — Strategic / Practice Management

#### R21: Client Diagnostic Complexity Score
- **What:** Weighted composite of row_count, account_count, Gini, anomaly_density, tool_count
- **Why:** Engagement pricing, staff allocation, portfolio benchmarking
- **Data source:** All inputs already computed

#### R22: Period-over-Period Improvement Index
- **What:** Weighted average of composite score changes across all tools between engagements
- **Why:** Demonstrates audit-driven control improvement to clients. Retention value
- **Data source:** Sequential `ToolRun.composite_score` across engagements

#### R23: Follow-Up Resolution Velocity
- **What:** Median days from follow-up creation to resolution, segmented by severity
- **Why:** Engagement management — identifies bottlenecks and tracks team responsiveness
- **Data source:** `FollowUpItem.created_at` to disposition-change timestamp

#### R24: Tool Coverage Velocity
- **What:** Days from engagement creation to 50%/80%/100% tool coverage milestones
- **Why:** Engagement planning — helps firms estimate completion timelines
- **Data source:** `ToolRun.run_at` vs `Engagement.created_at`

#### R25: Benford Conformity Trend
- **What:** Period-over-period MAD trend for Benford's analysis
- **Why:** Degrading conformity across periods could signal increasing manual JE intervention (ISA 240)
- **Data source:** Store MAD/chi-squared in ToolRun metadata, compare across runs

#### R26: Materiality Utilization Rate
- **What:** Distribution of flagged item magnitudes relative to materiality thresholds (% below trivial, between trivial and PM, between PM and OM, above OM)
- **Why:** Threshold calibration — if most flags cluster below trivial, testing may be over-scoped
- **Data source:** Flagged item amounts available during session (ephemeral computation)

#### R27: Payroll-to-Revenue + Revenue-per-Employee
- **What:** `total_payroll / total_revenue` burden ratio + `total_revenue / unique_employees`
- **Why:** ISA 520 — payroll burden outside industry norms warrants investigation
- **Data source:** Payroll file (unique employee_id count) + `CategoryTotals.total_revenue`

#### R28: Reconciliation Clearance Velocity
- **What:** Average days from bank transaction date to GL clearance date
- **Why:** Slowing velocity indicates deteriorating cash management. ISA 505 bank confirmation planning context
- **Data source:** Matched transaction pairs in bank reconciliation engine

---

## 5. Metrics That MUST NOT Be Added (Guardrail Enforcement)

| Rejected Metric | Reason |
|-----------------|--------|
| Aggregate Client Risk Score | ISA 315 — inherent/control risk requires auditor judgment |
| Audit Opinion Prediction | ISA 700/705 — opinion formation is exclusively auditor judgment |
| Control Effectiveness Rating | ISA 315.A81 — control testing conclusions require human evaluation |
| Fraud Probability Score | ISA 240 — fraud assessment based on all evidence including inquiries |
| Materiality Recommendation | ISA 320.10 — materiality determination is professional judgment |
| Management Letter Content | ISA 265 — deficiency classification is auditor judgment (REJECTED in CLAUDE.md) |
| Composite Risk Scoring | ISA 315 — requires ISA 315 inputs beyond TB (DEFERRED in CLAUDE.md) |

---

## 6. Language Corrections Required

These existing labels cross from descriptive into evaluative territory and should be corrected for consistency with the platform's guardrail positioning:

| File | Current | Recommended | Reason |
|------|---------|-------------|--------|
| `ratio_engine.py` | `health_status: "healthy"/"warning"/"concern"` | `"above_threshold"/"at_threshold"/"below_threshold"` | Evaluative label |
| `going_concern_engine.py` | `severity: "high"/"medium"/"low"` | Use numeric threshold value instead | Contradicts disclaimer |
| `flux_engine.py` | Comment: "Significant unexplained variance" | "Large variance" | "Unexplained" implies audit inference |
| `expense_category_engine.py` | `exceeds_materiality` field | `exceeds_threshold` | ISA 320 — materiality is auditor judgment |
| `benchmark_engine.py` | `HEALTH_SCORE_STRONG/MODERATE` | Do not expose aggregate health score to clients | Composite risk scoring is rejected per CLAUDE.md |

---

## 7. Summary Priority Matrix

| Priority | Count | Effort Range | Value | ISA/Standards Coverage |
|----------|-------|-------------|-------|------------------------|
| P0 (Immediate) | 3 | Low | Critical | ISA 520, cross-tool comparability |
| P1 (Near-Term) | 5 | Low-Medium | High | ISA 315, ISA 570, engagement dashboard |
| P2 (Medium-Term) | 6 | Medium | High | ISA 315 App.2, ISA 520, ISA 315 fraud |
| P3 (Longer-Term) | 5 | Medium-High | Moderate-High | IAS 16/38/40, ASC 606/740, ISA 505 |
| P4 (Strategic) | 9 | Variable | Moderate | Practice management, retention |
| **Total** | **28** | | | |

**Implementation recommendation:** P0 items (R1-R3) require minimal effort — R1 is 4 new database columns for already-computed values, R2 is a single arithmetic operation, R3 is a division already available in every tool response. These three alone close the most impactful gaps in the platform's analytical coverage.
