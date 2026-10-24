# Sprint 829 — runtime discovery, round 2: the original tools (2026-10-23)

Sprint 823 drove the seven tools that had never had realistic input. This round drove the eleven
original ones the same way: JE, AP, payroll, revenue, AR aging, inventory, TB diagnostics, bank
reconciliation and three-way match. Each pass built a realistic dataset, worked out the right
answers by hand, ran each engine through the upload path and compared every output. Every finding
below was re-run and reproduced before it was recorded. Regression cases are in
`backend/tests/test_sprint_829_round2.py`, and each new test fails on the old code.

Severity is as in the Sprint 823 register. **P1** means a wrong number a practitioner would rely
on, or a test that cannot run. **P2** means misleading but bounded. **P3** means cosmetic.

## Shared

| ID | Sev | Finding | Status |
|---|---|---|---|
| D-1 | P1 | `parse_date` returned None for datetime/Timestamp cells. Every payroll pay date from an .xlsx register was missing; PR-T2 flagged 240/240 rows "blank" and the composite read 100. | Fixed |
| D-2 | P1 | `08-Jan-2025`, `Jan 08, 2025`, `20250108`, `01/08/25`, `08.01.2025`, ISO `…Z` and 12-hour times were skipped silently. The weekend test went from 142 flags to 0 with no warning. | Fixed |
| S-1 | P2 | Flagged-entry `details` mixed Decimals and floats, so the same field reached the client as a number from one test and a string from another. | Fixed |

## Journal entry testing

| ID | Sev | Finding | Status |
|---|---|---|---|
| JE-1 | P1 | Reciprocal entries paired an entry's own debit and credit lines: 61% of a clean GL was flagged HIGH. | Fixed |
| JE-2 | P1 | Just-below-threshold counted rows twice (flag rate 2.0). Its split pass summed debits and credits together. | Fixed |
| JE-3 | P1 | A GL out of balance by $499,995 still scored LOW. | Fixed (floor). The broader scoring rework is a CEO call. |
| JE-4 | P1 | After-hours flagged 100% of an .xlsx GL ("posted at 00:00"). | Fixed |
| JE-5 | P1 | Numbering gaps read the leading digits, so year-prefixed IDs (`JE-2025-0001`) all parsed as 2025. | Fixed |
| JE-6 | P2 | Round amounts stopped at 50 flags in file order: a $500K entry after fifty $10K entries was missed. | Fixed |
| JE-7 | P2 | Unusual amounts: a z-score that includes the outlier can never exceed (n−1)/√n, so groups of 10 or fewer could never flag. | Fixed (leave-one-out) |
| JE-8 | P2 | The composite is not monotone: a Benford failure that flags no entries lowers the score. | CEO call (scoring) |
| JE-9 | P2 | Month-end clustering flags 7 of 12 months of a normal close; Columbus Day and Veterans Day are treated as holidays. | CEO call |

## AP, payroll

| ID | Sev | Finding | Status |
|---|---|---|---|
| AP-1 | P1 | AP-T14 could never run: `po_number_column` was detected and then dropped, and it could not be overridden. | Fixed |
| AP-2 | P2 | Fixed monthly payments (lease, insurance) were fuzzy duplicates: 20 flags and $129K of "recovery value". | Fixed (recurring series excluded) |
| AP-3 | P2 | Same round-amount cap and small-group z-score ceiling as JE. | Fixed |
| PR-1 | P1 | PR-T9 flagged every employee in a single-period register as "single pay entry". | Fixed |
| PR-2 | P2 | PR-T7 flagged every interval of monthly staff in a biweekly population. | Fixed |

## Revenue, AR aging, inventory

| ID | Sev | Finding | Status |
|---|---|---|---|
| RT-1 | P1 | RT-04 flagged 100% of a register that lists sales as positive, including the project's own clean fixture. | Fixed |
| RT-2 | P2 | RT-07 trended the sum of absolute amounts, so returns added to revenue. RT-08's base included contra activity. | Fixed |
| RT-3 | P2 | RT-02 ignored `period_end`. RT-09 took the period from the first and last entries, so those entries were always flagged. | Fixed |
| AR-1 | P1 | .xlsx due dates were never aged, so 100% of AR landed in Current. | Fixed |
| AR-2 | P1 | A sub-ledger with only an invoice date was never aged and nothing warned. | Fixed |
| AR-3 | P1 | Notes from officers, deferred revenue and sales tax payable were classified as AR or revenue. The allowance read 0.91% (true 5%) and DSO 118 (true 36.5). | Fixed |
| AR-4 | P2 | Not-yet-due invoices were flagged as date errors and dropped from the aging buckets. | Fixed |
| AR-5 | P2 | Customer credit balances shrank the concentration base. | Fixed |
| IN-1 | P1 | IN-T10 (LCM/NRV) could never run: `selling_price_column` was not detected or overridable. | Fixed |
| IN-2 | P2 | IN-03 skipped zero extended values and used only a percentage tolerance. | Fixed |
| IN-3 | P2 | IN-08 grouped on cost and description only: one SKU in two warehouses was a "duplicate", and so was every $25 item when no description was supplied. | Fixed |

## TB diagnostics, bank rec, three-way match

| ID | Sev | Finding | Status |
|---|---|---|---|
| T1 | P1 | `"1,234.56"` in a CSV/Excel TB was zeroed and the TB reported as balanced. | Fixed |
| T2 | P1 | Every unclosed TB failed A = L + E by its net income ("significant imbalance", high). | Fixed. The ratio half is a CEO call. |
| T3 | P1 | Current vs non-current was decided by substring: Mortgage Payable counted as current, Deferred Revenue and Line of Credit did not, and the allowance was left out of net AR. | Fixed |
| T4 | P1 | 59 of 138 accounts were unclassified and dropped from the ratios, and the ratios said nothing. | Fixed (stated on the ratios). Classifier coverage is still open. |
| T5 | P1 | Lead sheets ignored a supplied account type; keywords won. | Fixed |
| T6 | P1 | DuPont and common-size values were sent as strings. | Fixed |
| T7 | P2 | An inventory reserve with a credit balance was flagged as a natural-balance violation. | Fixed |
| T8 | P3 | A single Net/Balance column TB is rejected with the wrong reason; "CASH" and "Cash" stay separate accounts. | Open |
| B1 | P1 | Split matching ignored a zero date tolerance and combined mixed signs, so real outstanding items disappeared. | Fixed |
| B2 | P2 | The summary ignored SPLIT matches (0 matched, $0 on both sides). | Fixed |
| B3 | P1 | Stale-deposit and stale-check tests used the wrong populations and aged items to today. | Fixed |
| W1 | P1 | Multi-line PO lines were paired in file order: 4 false material variances on a correct PO. | Fixed |
| W2 | P1 | Invoice quantity was never compared with quantity received. | Fixed |
| W3 | P2 | Partial deliveries were not combined. | Fixed |
