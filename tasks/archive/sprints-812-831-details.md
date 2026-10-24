# Sprints 812–831 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-24.

---

### Sprint 831: CEO methodology decisions 2–4 — risk-score floors, holidays, month-end
**Status:** COMPLETE 2026-10-24 — see Review for the PR and commit SHA.
**Priority:** P1 — the composite could rate a population full of HIGH-severity flags LOW.
**Source:** CEO decisions 2026-10-24 ("as conservative as possible"), recorded in `tasks/ceo-actions.md`
and the decision doc https://claude.ai/artifact/9zuEgMNHBTstNTJSxHcGeQ.

- [x] **Decision 2 — severity floors (all seven testing composites).** `shared/test_aggregator.py`: any
      row with a HIGH flag → ≥ 11 (Moderate); HIGH rows ≥ 1% and ≥ 2 → ≥ 26 (Elevated); ≥ 5% and ≥ 5 →
      ≥ 51 (High). Each floor that fires is reported in a new `score_basis` list (API, all seven score
      cards under "Why this score", and the memo results section). The score and floors are labelled
      Paciolus conventions everywhere they appear. Extended beyond JE to AP, Payroll, Revenue, AR, FA and
      Inventory because they share the aggregator and the same flaw — a deliberate scope call under the
      conservative mandate.
- [x] **Decision 2 — JE non-monotonicity (JE-8).** A test that flags no entries is weighted LOW in the
      average, so a Benford failure no longer lowers the score; a nonconforming distribution floors the
      score at Moderate on its own.
- [x] **Calibration exposed by the floors.** On the anomaly-framework fixtures the floors turned two
      masked false positives into HIGH ratings, so both were fixed rather than the floors weakened:
      JE T15 split detection flagged every busy account HIGH (fourteen $100–$1,500 cash entries in a day
      is not structuring) — now HIGH only for ≤ 5 pieces each ≥ 10% of the threshold, MEDIUM otherwise;
      JE T18 rare pairings were HIGH in a 25-entry ledger where every pairing is rare — HIGH now needs
      ≥ 100 journal entries. Detection is unchanged in both. Before/after on the fixtures: clean JE, AP
      and Revenue stay LOW; injected anomalies rate higher. FA and Inventory clean fixtures rate HIGH
      because their fixture dates have aged past the depreciation and 180-day thresholds — the engines
      measure to the as-of date the auditor supplies and disclose it, so this is fixture age, not an
      engine fault.
- [x] **Decision 3 — holidays.** List cited to 5 U.S.C. 6103. Columbus Day and Veterans Day postings are
      flagged LOW whatever the amount. New `holiday_calendar` form field on `/audit/journal-entries`
      (`{"exclude": [...], "closed_dates": [...]}`), malformed input → 400 rather than ignored; a
      "Client holiday calendar" panel on the JE upload screen.
- [x] **Decision 4 — month-end.** The fixed 2× test keeps running (LOW; MEDIUM above 4×). A new
      client-baseline view flags a month whose month-end share is an outlier against the client's own
      other months (modified z ≥ 3.5, Iglewicz & Hoaglin 1993, plus a 5-point gap) at MEDIUM, HIGH above
      4×; needs 6 months, and the description says when it did not run.
- [x] **Sprint 819 item 3 (round-amount cap ordering, CEO default).** Revenue and Payroll now count every
      round amount and keep the largest, like JE and AP.

**Found, not fixed (filed):** the JE/AP/Payroll/TWM threshold settings saved from the tool settings
drawer (`practice_settings.je_testing_config` etc.) are never passed to the engines — the routes run
with `config=None`. A customer who changes a threshold sees no effect. Needs its own sprint.

**Verification:** backend suite green (see Review); `test_sprint_831_methodology.py` (18), new
`TestSeverityFloors` (6); frontend `tsc` clean, JE page / holiday panel / score card jest green.

**Review:** commit SHA recorded on merge.


---

### Sprint 824: Statistical sampling evaluation and the shared amount parser
**Status:** COMPLETE 2026-10-23 — merged as PR #205. S3/S6 moved to Sprint 825 (methodology decision).
**Priority:** **P1** — S1 changed an audit conclusion.

- [x] **S1 — top stratum.** An item at or above the sampling interval is examined with certainty,
      so its actual misstatement enters the projection with no tainting projection and no
      allowance. Reproduced and fixed: the review case now reports UEL **$260,000 "fail"**
      (was $234,500 "pass"). Five existing fixtures placed their errors on items *exactly equal*
      to the interval — top-stratum items under the corrected rule — and were rescaled to
      sub-interval items with identical taintings, so every figure they assert is unchanged.
- [x] **S2/S7 — sample value.** `_parse_evaluation_errors` now totals every evaluated item; MUS
      reports it as sample value and the random ratio estimate uses it as its denominator.
- [x] **S4/S5 — unreadable audited amounts** are unassessed (counted in
      `skipped_missing_audited`), not a 100% misstatement or an infinite one.
- [x] **S8** — MUS echoes the expected misstatement it was given.
- [x] **S9** — both sampling routes reject non-finite form values with a 422.
- [x] **P-1/P-2 — shared parser.** `safe_decimal` and `safe_float` test for parentheses after
      dropping `$` and spaces, and return the default for any non-finite result.
- Tests: 6 engine tests (all fail on the old code), 4 route tests, `test_safe_decimal.py`.

**Not done here — methodology decisions (Sprint 825):** S3 (zero-error random evaluation always
passes) and S6 (understatements evaluated as overstatements) need a chosen method — e.g. a
classical-variables evaluation with a sample standard deviation, and a separate understatement
bound — not a patch.

**Commit SHA:** 40044bc7 (PR #205).


---

### Sprint 829: Discovery round 2 — the eleven tools Sprint 823 did not cover
**Status:** COMPLETE 2026-10-23 — merged as PR #218 and live on Render. The four methodology calls it surfaced (equity in ratios, JE scoring, holiday list, month-end threshold) are tracked in `tasks/ceo-actions.md`.
**Priority:** **P1** — several findings produce wrong output on correct input.

- [x] **AR-1** — aging uses the shared `parse_date`, so Excel date cells are aged (a whole
      .xlsx sub-ledger was landing in Current).
- [x] **AR-2** — a sub-ledger with only an invoice date is aged from it, with a note.
- [x] **AR-3** — non-trade receivables (notes, loans, officers, related party, tax, …) and
      non-earned revenue (deferred, unearned, cost of) are no longer classified as trade AR/revenue.
- [x] **IN-5** — `selling_price_column` is detected and overridable, so IN-T10 (LCM/NRV) can run.
- [x] **T1** — currency-formatted debit/credit cells ("$1,234.00", "(500)") in a CSV/Excel TB are
      parsed instead of coerced to zero.
- [x] **T6** — DuPont and common-size values serialize as JSON numbers, not strings.
- [x] **JE-1** — reciprocal entries no longer pair an entry's own debit and credit lines
      (61% of a clean GL was flagged HIGH).
- [x] **JE-2** — just-below-threshold counts rows, not flags (flag rate reached 2.0), and its
      split pass sums debits and credits separately.
- [x] **JE-3** — unbalanced entries floor the composite: any → Moderate, any over $1,000 →
      Elevated. A GL with a $250K out-of-balance entry was rated LOW.
- [x] **JE-4** — after-hours treats a file whose every timestamp is exactly midnight as
      date-only (100% of an .xlsx GL was flagged as 00:00 postings).
- [x] **JE-5** — numbering gaps read the trailing sequence per series, so year-prefixed IDs
      ("JE-2025-0001") are tested.
- [x] **Dates** — the shared `parse_date` accepts datetime/Timestamp cells (every payroll pay
      date from an .xlsx register was None) and `01-Jan-2025`, `Jan 5, 2025`, `20250105` and
      fractional-second forms that JE and others skipped silently.
- [x] **PR-T9** — "single pay entry" is a ghost indicator only in a multi-period register where
      most employees were paid more than once; a single pay run flagged the whole payroll.
- [x] **AP-T14** — `po_number_column` is copied onto the detection result, serialized and
      overridable; Invoice-Without-PO always reported "skipped".
- [x] **RT-04** — the file's dominant sign is the normal side; a register listing sales as
      positive had 100% of rows flagged as debit balances.
- [x] **T2 (equation)** — A = L + E includes current-period earnings, so a pre-closing TB is not
      a "significant imbalance" of its net income.
- [x] **B1** — bank split matches take only same-sign ledger rows, and a zero date tolerance
      means the same date (it disabled the date filter).
- [x] **B3** — deposits in transit are ledger-only receipts (the test read bank-only items),
      outstanding checks are ledger-only payments, and both age to the statement's last date.
- [x] **W1** — a multi-line PO's lines pair with the closest invoice/receipt line (description,
      quantity, price) instead of file order.
- [x] **W2** — invoice quantity is compared with quantity received (`billed_quantity`
      variance); the memo and results card show quantities as units against the receipt.
- [ ] Open: **T2 (ratios)** — ROE / D-E / equity multiplier use equity without current-period
      earnings on an unclosed TB; `CategoryTotals` is a public input shape, so the fix needs a
      decision on where "effective equity" is derived.
- [x] **T3** — named non-current balances (non-current, long-term, mortgage, deferred tax) stay
      out of current; deferred revenue, customer deposits and lines of credit count as current
      liabilities; the AR allowance nets into receivables and current assets.
- [x] **Dates (2)** — `01/08/25`, `08.01.2025`, ISO `…Z`, fractional ISO and 12-hour times parse;
      JE after-hours reads the same forms.
- [x] **P2s** — bank-rec summary counts SPLIT matches; RT-07 trends net revenue and RT-08 uses the
      normal-side base; AR-03 no longer flags not-yet-due invoices and the schedule buckets them
      in Current; AR-08 excludes customers in credit from the base; IN-03 catches zero extended
      values and large absolute differences; IN-08 ignores one SKU across locations and never
      groups on cost alone; AP fuzzy duplicates skip fixed-amount recurring series; round-amount
      caps list the largest and count all; JE/AP unusual amounts use leave-one-out z-scores.
- [x] **RT-02 / RT-09 / T7** — the year-end window ends at the configured period end (else
      the last entry's month-end); inferred cut-off periods round out to whole months; asset
      reserves ("reserve for", "inventory reserve", "provision for") are contra accounts.
- [x] **W3** — receipts delivered in instalments against one PO line are combined (every
      receipt on a single-line PO; same-description receipts on a multi-line PO).
- [x] **PR-T7** — an employee with a regular cadence *longer* than the population's (monthly
      staff in a biweekly payroll) is measured against it; shorter regular cadences stay flagged.
- [x] **Classifier (T4 follow-up)** — phrase rules match a plural last word ("Customer
      Deposits" was an asset); salaries/wages/advertising/legal fees/bank charges/property and
      payroll taxes/line of credit added, with accrued/payable phrases so liabilities stay
      liabilities. "Salaries - Sales" was revenue.
- [x] **Bank rec bridge** — the results bridge put bank-only items on the bank side and
      ledger-only items on the GL side, so it did not tie; reconciling items now adjust the side
      that has not recorded them. Memo descriptions of bank-only / ledger-only corrected.
- [x] **T8 / serialization** — a Net-column TB is told its columns are missing (not "no data");
      flagged-entry `details` serialize Decimals as numbers.
- [ ] Open P2/P3 (CEO calls in `tasks/ceo-actions.md`): JE composite scoring; month-end and
      holiday noise; equity incl. current earnings in ratios. Case-sensitive account merge
      ("CASH" vs "Cash") left as is — merging keys is a wider change.

Register: `reports/sprint-829-discovery-round2-2026-10-23.md`.
- [x] **T4** — analytics carry `excluded_accounts` (count + absolute balance of unclassified
      accounts), and Key Metrics states what the ratios leave out.
- [x] **T5** — a type the file supplied (and we could read) outranks a lead-sheet keyword of a
      different category; compatible keywords still refine placement within the type.

**Commit SHA:** 106c5782 (PR #218).


---

### Sprint 812: Nineteen rate-limited routes 500 on every call
**Status:** COMPLETE 2026-10-23 — merged as PR #201 and verified live: the public `/export-sharing/{token}` probe flipped 500 → 404 on the deployed SHA.
**Priority:** **P0** — every Professional/Enterprise org feature is down in production.
**Source:** Code health review 2026-10-23, routes pass. Re-verified on the live app object.

The handlers declare `request: Any = None` under `@limiter.limit`. FastAPI therefore treats
`request` as a **query parameter**, slowapi receives `None`, and raises
`parameter 'request' must be an instance of starlette.requests.Request` → 500. Reproduced on
`GET /admin/overview`. Introduced by `8372073a` (2026-03-21 mypy cleanup). Tests never saw it
because `tests/conftest.py:166` sets `limiter.enabled = False`.

Affected (19): `routes/organization.py:86,134,156,233,262,364,395`,
`routes/admin_dashboard.py:81,140,179,215`, `routes/branding.py:83,103,161`,
`routes/bulk_upload.py:47`, `routes/export_sharing.py:312,458,495,522`.

**Scope:**
- [x] Change each to `request: Request`. Enumerated on the live app object first: exactly 19
      `APIRoute`s carried `request` as a query param, matching the list above one-for-one.
- [x] Guard test `tests/test_rate_limited_request_param.py`: every route in slowapi's
      decorated-endpoint registry must have `dependant.request_param_name` set, and no route may
      expose `request` as a query/body param. Includes a vacuity check (≥150 limited routes
      resolved; 201 today) so a drift in slowapi internals cannot turn it into a scan of nothing.
- [x] Limiter **enabled** for the whole of the five affected routers' existing suites via a new
      opt-in `limiter_enabled` conftest fixture (`pytestmark` in each module) — stronger than one
      test per router. **Proved:** with the route fix reverted, 43 of those 71 tests fail; with it, 71/71.
- [x] OpenAPI snapshot regenerated — the diff is exactly the 19 bogus `?request=` params (−202 lines).
      Note the drift check did **not** flag their removal (it reports only metadata drift), so the
      snapshot gate would never have caught this either.
- [ ] After deploy: confirm live SHA = `main`, then hit `/organization` and `/branding/` on prod.

**Side effect worth knowing:** `export_sharing.py:511` threads `request.client.host` into the
Sprint 698 per-IP passcode throttle. With `request=None` that branch could never run — though
the route 500'd before reaching it anyway, so the throttle was not bypassed, merely unreachable.

**Commit SHA:** 6fb9f33c (PR #201).


---

### Sprint 816: Engine correctness follow-ups surfaced by the performance pass
**Status:** COMPLETE 2026-10-23 — all four verified by measurement before fixing; three were real
as described, one (item 3) was worse than described, and item 4 turned out to be an **accuracy**
defect, not only a reproducibility one.
**Priority:** P2 → item 4 is effectively **P1** (see below).
**Source:** Code health review 2026-10-23, engines pass.

- [x] **JE reciprocal entries counted flags, not rows.** Measured: 3 debits × 3 credits of one
      amount → `entries_flagged` **18 of 6 entries, `flag_rate` 3.0 (300%)** in the customer's
      output. Now counts distinct rows; the per-pair flags stay in `flagged_entries`. Regression
      test in `test_je_tier3.py`. `test_tool_anomaly_detection.py` now asserts
      `entries_flagged ≤ total_entries` and `0 ≤ flag_rate ≤ 1` for **every** test result of every
      generator run, not just the targeted one — no generator builds a multi-partner case, so
      that invariant would not have caught this one, but it now covers the whole population.
- [x] **JE `apply_column_overrides` never set `has_dual_dates`.** Confirmed. Impact is limited to
      the reported column detection (parsing reads the explicit columns), but it was wrong. Fixed
      the AP way; test added.
- [x] **Currency NaN — worse than described.** An empty amount cell (float NaN) became
      `Decimal("NaN")`; when that row was *also* unconvertible (missing currency code or missing
      rate) the severity pass raised **`InvalidOperation`** — an `ArithmeticError` the TB
      post-processor's fallback did not catch. And `Decimal(str(x))` turned `$1,234.56` and
      `(500.00)` into a **silent 0**. Now parsed through `safe_decimal` (NaN/inf → 0, currency and
      parenthetical formats parsed); the post-processor fallback also catches `ArithmeticError`.
      3 tests, all failing on the old code.
- [x] **FA/Inventory reference date — an accuracy defect.** No caller ever passed
      `reference_date`, so FA-T11 divided accumulated depreciation (stated **as of period end**)
      by years elapsed **to today**. Measured: a register depreciated exactly on schedule to
      2025-12-31, tested on 2026-10-23, had **6 of 6 assets flagged**. Audit fieldwork happens
      after year-end, so on real engagements this test was a false-positive generator. IN-06
      (slow-moving) had the same dependency. Fix: `shared/reference_date.resolve_reference_date`
      — explicit `as_of_date` form field > linked engagement's `period_end` > processing date,
      the same cascade shape as materiality — threaded into both configs, and the date used plus
      its source is now stated in each test's description (so it reaches the UI and the memo with
      no schema change). Engagement-linked uploads get period end automatically, because
      `useAuditUpload` already injects `engagement_id`. Unparseable `as_of_date` → 400, never a
      silent fallback. `_asset_age_years` was never called outside its own tests — deleted with them.

**Follow-up (frontend, not done):** the FA and inventory pages do not yet offer an as-of date
input, so an upload **not** linked to an engagement still measures to the processing date —
now disclosed in the test description rather than silent.

**Commit SHA:** TBD.


---

