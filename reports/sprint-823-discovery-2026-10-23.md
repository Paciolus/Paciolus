# Sprint 823 — runtime discovery on the under-exercised tools (2026-10-23)

Seven of the eighteen tools had never been driven with realistic input, and the eleven with
generators had never had their *application* checked end to end. Three parallel passes built
realistic datasets per tool family, computed the right answers by hand, drove each engine (and
where relevant the route's request parsing) and compared every output number. Every finding below
was re-run and reproduced before it was recorded. Scripts live in the session scratchpad only.

Severity: **P1** = a wrong number a practitioner would rely on, or a crash on plausible input.
**P2** = misleading but bounded. **P3** = cosmetic or edge-case.

Status column: **Fixed (824)** = remediated in Sprint 824; otherwise the sprint that owns it.

## Shared parser (`shared/parsing_helpers.py`) — reaches every engine

| ID | Sev | Finding | Status |
|---|---|---|---|
| P-1 | P1 | `$(2,000.00)` parsed as **+2,000**: the parenthetical check ran before `$` was stripped. Same in `safe_float`. | Fixed (824) |
| P-2 | P2 | `"Infinity"` / `"-Infinity"` parsed as non-finite Decimals (the guard only knew `"inf"`). | Fixed (824) |
| P-3 | P2 | `€12,500.00` and `USD 12,500.00` → silent 0; `12.500,00` (EU) → 12.5, a 1000× error. | 827 — needs a locale decision |

## Statistical sampling

| ID | Sev | Finding | Status |
|---|---|---|---|
| S1 | P1 | MUS evaluation projected a top-stratum item (recorded ≥ interval) as `tainting × interval` instead of its actual misstatement. Pop $5M, TM $250k, interval $70k, one $50k error on a $250k item: reported UEL **$234,500 "pass"**; correct **$260,000 "fail"**. `sampling_engine.py:476`. | Fixed (824) |
| S2 | P1 | Random-method ratio estimate used only the error rows as the sample base: one $1,000 error in a $1.03M sample projected to **$597,198** instead of ~$4,868. | Fixed (824) |
| S3 | P1 | Random-method evaluation with zero errors always reports UEL $0 and "pass", at any sample size (basic precision = projected × CF/√n, which is 0). | **825 — methodology decision** |
| S4 | P1 | Audited amount `Infinity` → `-inf` misstatement → JSON serialisation failure (500). | Fixed (824) |
| S5 | P2 | Unparseable audited value ("see note") → $0 → scored as a 100% misstatement instead of unassessed. | Fixed (824) |
| S6 | P2 | Understatements evaluated as overstatements (`abs(misstatement)` in tainting). | 825 — methodology decision |
| S7 | P2 | MUS `sample_value` covered only error items; Sprint 684's fix never reached the route. | Fixed (824) |
| S8 | P3 | MUS result always reported `expected_misstatement` 0.0. | Fixed (824) |
| S9 | P1 | `nan`/`inf` form values accepted on both routes; most then 500'd serialising the result, others silently became 0. | Fixed (824) |
| — | ok | Verified correct: MUS design sample size (72) and interval ($70,000) by hand; every item ≥ interval selected; reproducible from the reported random start; Stringer arithmetic for sub-interval errors (UEL $313,390) matches by hand. | — |

## Tax tools

| ID | Sev | Finding | Status |
|---|---|---|---|
| F0 | P2 | `"1e400"` amounts 500 on W-2, 1099 and book-to-tax: finite for `_to_decimal`, then `quantize` raises `InvalidOperation` (an `ArithmeticError`, uncaught). | Fixed (827) |
| F1 | P1 | 1099 royalties use the $600 threshold; the 1099-MISC box 2 threshold is **$10**. `form_1099_engine.py:96-100`. | Fixed (826) |
| F2 | P1 | 1099 `payment_date` is never used: payments from 2024-12 and 2026-01 count toward TY2025. | Fixed (826) |
| F3 | P1 | No aggregation by TIN: two vendor IDs sharing a TIN with $400 each → no 1099 (should be one $800 NEC). | Fixed (826) |
| F4 | P1 | Attorney fees have no correct path: `legal` lands on MISC box 10 (gross proceeds), and NEC + corporation is excluded entirely. | 826 |
| F5 | P1* | TY2026 still uses $600 for NEC/MISC; the agent believes P.L. 119-21 raised it to $2,000 for payments after 2025-12-31. **Unconfirmed — practitioner.** | 793b |
| F6 | P2 | MISC thresholds applied to the combined total, not per box (rents 400 + medical 300 → a 700 MISC). | Fixed (826) |
| F7 | P2 | Category `other` → MISC "box 0" (does not exist; other income is box 3). | Fixed (826) |
| F8 | P2 | Payments to governments and tax-exempt entities reported as NEC. | Fixed (826) |
| W1 | P1 | SIMPLE IRA catch-up uses the 401(k) figures ($7,500 instead of $3,500; age 60–63 $5,250). `w2_reconciliation_engine.py:531-534`. | 826 (figures via 793b) |
| W2 | P1 | HSA limit ignores the age-55 $1,000 catch-up — a correct contribution is flagged HIGH with an excise-tax message. | 826 |
| W3 | P1 | Box 12 codes D/W/S and payroll SS/Medicare **withheld** are read but never compared. | Fixed (826) |
| W4 | P1 | W-3 never checked against the 941s; duplicate and orphan W-2 drafts unflagged (W-3 sums every draft, lookup keeps the last). | Duplicates/orphans/padded IDs fixed (826); W-3 vs 941 still open |
| W5 | P2 | Deferrals not checked when `retirement_plan_type` is absent. | Fixed (826) |
| W6 | P2 | A correctly capped box 3 still draws HIGH `ss_wage_base_exceeded` when payroll reports uncapped SS wages. | 826 |
| W7–W10 | P3 | Informational item counted as a discrepancy; W-3 zeros with no drafts; duplicate/missing 941 quarters undetected; negative tolerance flags everything. | 826 |
| B1 | P1 | Book-to-tax loss years ignore the NOL: book −$200k → tax **expense** +$11,550 instead of a ~$39k benefit. | 826 — needs a scope call (NOL/valuation allowance) |
| B2–B5 | P2 | State tax excluded from deferred; state rate unvalidated (`"5"` → 500%); gross DTA/DTL wrong on DTL reversal; `code` not checked against its catalog direction. | B3 + B4 fixed (826); B2, B5 open |
| — | ok | Verified correct: 2025 SS base $176,100, 6.2%/1.45%, Additional Medicare over $200k per employee, HSA $4,300/$8,550, 401(k) $23,500 + $7,500 + age 60–63 $11,250, SIMPLE base $16,500; 1099 exactly-$600 boundary, corporate exemption, W-9 list; book-to-tax clean case matches by hand (taxable income $958,000, total tax $212,730). | — |

## Fixed assets, SoD, intercompany

| ID | Sev | Finding | Status |
|---|---|---|---|
| A1 | P1 | FA-T11 flags **every correct declining-balance asset** HIGH (66–304% variance): it applies 2/life to *current* NBV × years elapsed, which is not compound DDB; 150% DB goes down the same 2× path. `fixed_asset_testing/analysis.py:1457,1464`. | Fixed (827) |
| A2 | P1 | FA-T11 never caps expected accumulated depreciation at the depreciable base: assets between 1.0× and 1.5× life are mis-flagged (3 of 30 in a clean register). | Fixed (827) |
| A3 | P1 | FA-T11 silently skips every row when dates come from Excel date cells (`"2019-01-01 00:00:00"`) or `2019/01/01`, `01-Jan-2019`: it tries 3 formats instead of the shared `parse_date`. | Excel datetime + `YYYY/MM/DD` fixed (827); `01-Jan-2019` style still unparsed (shared `parse_date`) |
| A4 | P2 | DD/MM/YYYY registers get false flags (ambiguous dates read MM/DD first). | 827 |
| A5 | P2 | Half-year convention not absorbed despite the comment claiming it is (5% tolerance vs exact-day proration). | 827 |
| A6 | P1/P2 | Contra-negative accumulated depreciation (`(5,000.00)`) flags 100% of rows in FA-03 and FA-T11; FA-01/04 use `abs()`. | FA-T11 fixed (827); FA-03 still flags contra balances by design — needs a call |
| A8 | P2 | `Useful Life (Months)` auto-detected as years. | 827 |
| D1 | P1 | SoD long-format input drops conflicts: a role on two rows is overwritten (`sod_engine.py:281`); a user on two rows is two users. | Fixed (827) |
| D2 | P2 | One HIGH SoD conflict scores tier "moderate"; unrecognised permission spellings give a clean result with no warning; degenerate custom rules flag everyone. | Unmatched-permission warning fixed (827); single-HIGH tiering and degenerate custom rules need a policy call |
| I1 | P1 | Intercompany revenue/expense elimination JE is **reversed** (Dr expense / Cr revenue); booking it doubles both sides, and the worksheet disagrees with the JEs. `intercompany_elimination_engine.py:604`. | Fixed (827) |
| I2 | P1 | Multiple IC accounts between the same two entities are cartesian-matched: 2 × $500 balances → 4 pairs, $2,000 eliminated, consolidation "complete". | Fixed (827) |
| I3 | P1 | An explicit counterparty is ignored unless the account name contains an IC keyword → nothing eliminated, "complete". | Fixed (827) |
| I4 | P2 | Keyword substring false positives ("Electric expense", "Clinic revenue", "Due to officers") block completion; counterparty regex takes "Ltd" from "… - Dublin Ltd". | Fixed (827) — except investment/payable pairing |
| I5 | P3 | `"1e26"` → 500 (uncaught `InvalidOperation`); direction mismatch reported twice; `(1000.00)` rejected; negative debits pass through. | 500 and double-count fixed (827); formats + negative debits open |
| — | ok | Verified correct: a clean in-life straight-line register gives 0 flags; planted under-depreciation flagged exactly; SoD rules fire correctly on a 15-user matrix; IC receivable/payable pairs reconcile with the right JE direction and tolerance boundary. | — |

## Cash flow projector

| ID | Sev | Finding | Status |
|---|---|---|---|
| C1 | P2 | "Monthly" recurring flows recur every 30 days, not on calendar months: Jan 31 rent lands Mar 2 and a whole payment drops out of the 90-day horizon. `cash_flow_projector_engine.py:338`. | Fixed (827) |
| C2 | P2 | AP not paid in a scenario is never paid within the horizon, inflating ending cash (the scenario table drops the unpaid share instead of deferring it). | 827 |
| C3–C6 | P3 | Displayed rows don't foot by cents (per-field rounding); `lowest_balance_day` defaults to day 0 at the opening balance; negative aging buckets netted in `ar_total` but ignored in the projection; overdrawn opening balance rejected. | 827 |
| — | ok | Verified correct: roll-forward holds at full precision; lowest balance, first negative day and min-cash breach trigger on the right day in every scenario; dates contiguous across Feb 29 2028; route rejects nan/inf. | — |
