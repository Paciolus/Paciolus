# Duplicate Entry Detection Contract

> **Authority:** Documents the current per-tool duplicate detection capabilities
> and known gaps. This file is informational — it does not change any detection
> logic.
>
> **Source:** AUDIT-06 Phase 3 findings (2026-03-20).

---

## Tools That Detect Duplicate Entries

### 1. Journal Entry Testing — `je_testing_engine.py :: test_duplicate_entries()` (T3)

| Aspect | Detail |
|---|---|
| **Comparison key** | `(posting_date or entry_date, account.lower(), round(debit, 2), round(credit, 2), description.lower())` |
| **Tolerance** | Exact match only (amounts rounded to 2 decimal places before comparison) |
| **Minimum count** | > 1 entry sharing the same key → all members flagged |
| **Severity** | MEDIUM |
| **Confidence** | 0.90 |
| **Output** | `FlaggedEntry` with `duplicate_count` and `row_numbers` in details |
| **Limitations** | Requires JE-format data (posting_date, account, debit, credit, description). Will not detect near-duplicates (different descriptions, slightly different amounts). Date field is optional — entries missing dates may cluster as false duplicates on the empty-string key. |

### 2. AP Testing — `ap_testing_engine.py :: test_exact_duplicate_payments()` (AP-T1)

| Aspect | Detail |
|---|---|
| **Comparison key** | `(vendor_name.lower(), invoice_number.lower(), round(amount, 2), payment_date)` |
| **Tolerance** | Exact match only (amounts rounded to 2 decimal places) |
| **Minimum count** | > 1 payment sharing the same key → all members flagged |
| **Severity** | HIGH (always — exact duplicates in AP are presumed overpayments) |
| **Confidence** | 0.95 |
| **Output** | `FlaggedPayment` with `duplicate_count`, vendor, invoice_number, amount, payment_date |
| **Limitations** | Requires AP-format data. Missing invoice numbers fall back to empty string — may cause false matches among payments without invoice references. |

### 3. AP Testing — `ap_testing_engine.py :: test_fuzzy_duplicate_payments()` (AP-T6)

| Aspect | Detail |
|---|---|
| **Comparison key** | Same vendor + amount within `duplicate_tolerance` (default 0.01) + different dates within `duplicate_days_window` (default 30 days) |
| **Tolerance** | `config.duplicate_tolerance` (default `0.01`) for amount; `config.duplicate_days_window` (default `30`) for date proximity |
| **Minimum count** | Pairwise — any two payments matching the criteria are flagged |
| **Severity** | HIGH if amount > $10,000; MEDIUM otherwise |
| **Confidence** | 0.85 |
| **Output** | `FlaggedPayment` with vendor, amount, days_apart, matched_row |
| **Limitations** | O(n²) per vendor group. Excludes same-date pairs (handled by AP-T1). Post-processing deduplicates entries flagged multiple times. |

---

## Tools That Do NOT Detect Duplicate Entries

### TB Anomaly Rules (`audit/rules/`)

The trial balance anomaly detection pipeline does **not** include a duplicate-row
detector. The six rule modules (balance, rounding, suspense, relationships,
concentration, equity) operate on aggregated `account_balances` — a dict keyed by
account identifier with summed debit/credit values. By the time the rules run,
duplicate rows have already been collapsed into their account totals.

**Is this intentional?** Partially. The TB is a summary-level artifact; duplicate
*rows* in a TB upload are unusual and typically indicate an upload/parsing issue
rather than a recording fraud. However, the synthetic `DuplicateEntryGenerator`
injects duplicate TB rows that cause an imbalance — the engine detects this as
`balanced=False` but does not attribute the cause to duplication.

### Other Testing Tools

Revenue Testing, AR Aging, Fixed Assets, Inventory, Payroll, Bank Reconciliation,
Three-Way Match, Multi-Period TB, Statistical Sampling, and Multi-Currency do not
include duplicate detection logic. These tools focus on domain-specific tests
(cutoff, aging brackets, depreciation schedules, etc.) and assume the underlying
data has been deduplicated or is inherently unique.

---

## Current Detection Gaps

| Gap | Description | Impact |
|---|---|---|
| **Balance-preserving TB duplicates** | If a pair of offsetting entries is duplicated (e.g., a debit and its matching credit are both copied), the TB remains balanced and no anomaly is raised at the TB level. | Silent — no detection path exists for this scenario in the TB pipeline. |
| **TB-level duplicate attribution** | When duplicates cause `balanced=False`, the engine reports the imbalance but does not identify which rows are duplicated. The user must investigate manually. | Low — the imbalance is surfaced, but root cause is not attributed. |
| **Cross-tool duplicate detection** | A transaction duplicated across JE and AP data (e.g., a payment recorded in both the journal and the AP subledger) is not cross-referenced. Each tool operates on its own dataset. | Medium — cross-tool reconciliation is out of scope for individual tool testing but represents a real audit risk. |
| **Non-JE/AP transaction duplicates** | Payroll, revenue, inventory, and other domain tools do not check for duplicates within their datasets. | Low — these tools process structured data where duplicates are less common, but the gap exists. |
