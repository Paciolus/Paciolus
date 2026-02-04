# Accounting Standards Reference

## Overview

Paciolus diagnostic tools support trial balances prepared under both **US GAAP** (Generally Accepted Accounting Principles) and **IFRS** (International Financial Reporting Standards). This document outlines key differences that may affect ratio calculations and account classification.

---

## Financial Ratio Considerations

### Current Ratio & Quick Ratio (Liquidity)

| Aspect | US GAAP | IFRS |
|--------|---------|------|
| **Current/Non-current Classification** | Required on balance sheet | Required, but allows liquidity-based presentation |
| **Operating Cycle** | 12 months or operating cycle, whichever is longer | Same principle applies |
| **Inventory Valuation** | LIFO permitted (affects Quick Ratio) | LIFO prohibited; FIFO or weighted average only |

**Paciolus Note:** The Quick Ratio excludes inventory. LIFO reserves under US GAAP may create comparability issues with IFRS-prepared statements.

### Debt-to-Equity Ratio (Leverage)

| Aspect | US GAAP | IFRS |
|--------|---------|------|
| **Redeemable Preferred Stock** | Often classified as equity | May be classified as liability if redeemable |
| **Compound Instruments** | Typically all equity or all debt | Split between debt and equity components |
| **Treasury Stock** | Contra-equity (reduces equity) | Same treatment |

**Paciolus Note:** Equity composition may differ, affecting D/E calculations. Review instrument classification for cross-standard comparisons.

### Gross Margin (Profitability)

| Aspect | US GAAP | IFRS |
|--------|---------|------|
| **Revenue Recognition** | ASC 606 (5-step model) | IFRS 15 (substantially converged with ASC 606) |
| **Cost of Sales** | Direct costs + allocated overhead | Similar treatment |
| **Freight-Out Costs** | Often in operating expenses | May be in cost of sales |

**Paciolus Note:** Revenue recognition is largely converged post-2018. Historical data may show differences.

### Net Profit Margin & Operating Margin

| Aspect | US GAAP | IFRS |
|--------|---------|------|
| **Extraordinary Items** | Prohibited (post-2015) | Never permitted |
| **Operating Profit Line** | Not required | Not specifically required |
| **R&D Costs** | Expensed as incurred | Development costs may be capitalized if criteria met |
| **Interest Classification** | Operating (typically) | Can be operating or financing |

**Paciolus Note:** R&D capitalization under IFRS can shift expenses between periods, affecting margins.

### Return on Assets (ROA)

| Aspect | US GAAP | IFRS |
|--------|---------|------|
| **Asset Revaluation** | Not permitted (historical cost) | Permitted for PPE and intangibles |
| **Impairment Reversal** | Not permitted | Permitted (except goodwill) |
| **Lease Accounting** | ASC 842 (similar to IFRS 16) | IFRS 16 |

**Paciolus Note:** IFRS revaluations can inflate asset base, reducing apparent ROA. Historical cost provides more consistent comparisons.

### Return on Equity (ROE)

| Aspect | US GAAP | IFRS |
|--------|---------|------|
| **OCI Reclassification** | Some differences in recycling rules | Different recycling for certain items |
| **Actuarial Gains/Losses** | Recognized in OCI, recycled | Recognized in OCI, not recycled |

**Paciolus Note:** OCI treatment can affect retained earnings trajectory differently under each framework.

---

## Account Classification Differences

### Deferred Revenue / Unearned Revenue

- **Both Standards:** Classified as liability until performance obligation satisfied
- **Key Difference:** IFRS 15 may accelerate recognition for certain contract modifications
- **Paciolus Classification:** LIABILITY (0.90 confidence for "deferred revenue")

### Leases (Post-2019)

| Element | US GAAP (ASC 842) | IFRS (IFRS 16) |
|---------|-------------------|----------------|
| **Right-of-Use Asset** | Asset | Asset |
| **Lease Liability** | Liability | Liability |
| **Operating Lease Expense** | Single expense (lessees) | Depreciation + Interest (lessees) |

**Paciolus Classification:**
- "Right-of-use asset" → ASSET
- "Lease liability" → LIABILITY
- Operating lease expense patterns may differ

### Inventory

| Method | US GAAP | IFRS |
|--------|---------|------|
| **LIFO** | Permitted | Prohibited |
| **Lower of Cost or Market** | Yes | Lower of cost or NRV only |

**Paciolus Note:** LIFO reserves should be considered when comparing US GAAP inventory to IFRS.

### Research & Development

| Treatment | US GAAP | IFRS |
|-----------|---------|------|
| **Research Costs** | Expense as incurred | Expense as incurred |
| **Development Costs** | Expense as incurred | Capitalize if 6 criteria met |

**Paciolus Classification:**
- "R&D expense" → EXPENSE
- "Capitalized development" → ASSET (under IFRS)

### Contingencies and Provisions

| Threshold | US GAAP | IFRS |
|-----------|---------|------|
| **Recognition** | "Probable" (~75%+) | "More likely than not" (>50%) |
| **Measurement** | Most likely amount | Best estimate (expected value) |

**Paciolus Note:** IFRS may recognize more provisions as liabilities than US GAAP for the same underlying events.

---

## Interpretation Guidelines

### When Ratios May Not Be Directly Comparable

1. **Cross-Standard Comparison:** Comparing a US GAAP company to an IFRS company
2. **Historical Trend Analysis:** Standards changes (e.g., lease accounting in 2019)
3. **Industry-Specific Rules:** Banking, insurance, and extractive industries have unique standards

### Paciolus Approach

- **Classification:** Uses terminology common to both frameworks
- **Ratio Thresholds:** Based on general financial analysis principles, not standard-specific
- **Interpretation:** Flags areas where professional judgment is needed
- **No Standard Assumption:** Paciolus does not assume which standard applies

---

## References

- **US GAAP:** FASB Accounting Standards Codification (ASC)
- **IFRS:** IFRS Foundation Standards
- **Convergence Projects:** FASB-IASB joint projects (Revenue, Leases)

---

*This document provides general guidance. Specific accounting treatments should be verified with authoritative standards and professional advisors.*
