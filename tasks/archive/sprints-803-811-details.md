# Sprints 803–811 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-23.

---

### Sprint 803: Every exported EBITDA equals operating income, and no cash flow statement has ever shown depreciation
**Status:** COMPLETE.
**Priority:** **P1** — a wrong number in every exported ratio PDF, from a one-line key bug.
**Finding:** A-5. **Size:** hours.

`financial_statement_builder.py:970` reads `acct.get("name", "")`. The serialized account dicts
carry the key **`account`** — never `name` (`lead_sheet_mapping.py:633-652` passes `s.accounts`
through verbatim). So `_extract_depreciation()` compares every keyword against the empty string
and returns 0.0 for every trial balance ever uploaded. Three consequences:

1. The ASC 230 / IAS 7 indirect-method statement **never** carries the D&A add-back — the
   largest non-cash reconciling item the method has.
2. `pdf/sections/ratios.py:84-91` computes `ebitda = operating_income + depreciation_amount`,
   so **every exported ratio PDF reports EBITDA equal to operating income** and EBITDA margin
   equal to operating margin.
3. The failure is disguised as a note about the customer's file — *"Depreciation not separately
   identified in trial balance"* — which reads as an observation about the input.

The sibling `_extract_interest_expense` twenty lines later reads
`acct.get("name", "") or acct.get("account", "")`. It was fixed; this one was not.

- [x] Correct the key read in `_extract_depreciation` to match its already-fixed sibling
- [x] Delete `_account_descriptions` (`:410-416`) — built from the same wrong key, never read
- [x] **Scan order and contra guard.** Once the key works, lead sheet E matches
      `accumulated depreciation` — a cumulative contra-asset. Returning that as the add-back
      would be a *worse* number than 0.0. Scan N/O (expense) before E/F, skip any account whose
      name contains `accum`, and sum each matching account once rather than returning the first
      match, so a TB carrying separate depreciation and amortisation lines adds back both
- [x] Test: add-back appears for a TB containing a depreciation account
- [x] Test: `EBITDA > operating_income` whenever depreciation is present
- [x] Test: a TB whose **only** depreciation-ish account is `Accumulated Depreciation` adds
      back nothing — pins the guard above


**Review notes (COMPLETE).** The key correction was one line, as the report said. Two things
implementation added that the report had not reached:

1. **A contra guard the fix made necessary.** With the key corrected, lead sheet E matches
   `accumulated depreciation` — a *cumulative* contra-asset. The old code returned on first
   match, so it would have added back accumulated depreciation instead of period expense: a
   **worse** number than the 0.0 the defect produced. Scan order is now expense sheets (N, O)
   before asset sheets (E, F), any account containing `accum` is skipped, and matches are
   summed rather than first-wins so a TB carrying separate depreciation and amortisation lines
   adds back both. Measured: 30,000 + 10,000 = 40,000, with a 60,000 accumulated balance
   correctly excluded.
2. **Why it survived its own test.** `tests/test_financial_statements.py` had a passing test
   asserting `depreciation_amount == 10000.0`. Its fixture keys the depreciation account
   `"name"` while **both of its siblings** are keyed `"account"` — so the one account the
   depreciation test reads was the only one in the whole fixture keyed the way production never
   emits. The test passed against a dict shape that does not exist. The fixture is corrected,
   and the six new tests go through `group_by_lead_sheet` → `lead_sheet_grouping_to_dict` so
   they exercise the real serialisation rather than a hand-written approximation of it.


---

### Sprint 804: 19% of an ordinary chart of accounts never reaches the statements, and four accounts reach the wrong one with high confidence
**Status:** COMPLETE.
**Priority:** **P1** — wrong net income on plain-vanilla charts of accounts. The product's foundation.
**Findings:** A-3, A-4. **Size:** 1 sprint.

Driving `group_by_lead_sheet` with a 68-account chart built from standard names put **13 of 68
(19%)** on lead sheet Z at confidence 0.50 with zero keywords matched: the entire compensation
block, plus `Lease Liability` (in a product that ships a lease engine) and `Owner's Draw` (in
every S-corp and partnership). Unclassified accounts are excluded from both statements: on a
balanced TB carrying `Salaries and Wages Expense` of $300,000, the builder returned **net income
$460,000 against a true $160,000**, and a balance sheet out by $280,000.

Root cause for the salary family is small and precise: `lead_sheet_mapping.py:365-366` registers
`"salary expense"` and `"wage expense"` as **singular** phrases. Real charts overwhelmingly use
the plural. `"payroll expense"` *is* registered and does match, which is why the gap stayed
invisible.

A-4 is worse, because `unclassified_count` does not count it and the product reports confidence
0.80-0.90: `Payroll Tax Expense` → H Current Liabilities · `Bank Service Charges` → A Current
Assets · `Software Expense` → F Non-Current Assets · `Vehicle Expense` → E Non-Current Assets.
Each is an expense posted to the balance sheet, with no signal to the user. The mechanism is a
substring keyword beating the word "Expense" in the same account name.

- [x] Add the plural and compound compensation forms, plus the other ten names measured
- [x] **Terminal-token arbitration** in `assign_lead_sheet`: when the winning rule points at a
      balance-sheet sheet (A-K) but the account name's terminal token is an income-statement
      signal (`expense(s)`, `income`, `revenue`), the terminal token wins — unless the winning
      rule's own keyword contains that token, which is what keeps `Prepaid Expense` → D,
      `Accrued Expenses` → G and `Unearned Revenue` → H correct. Re-scan restricted to L-O and
      take the best; fall back to N (expense) / L (revenue) at reduced confidence if nothing
      matches
- [x] Explicit rules for the four A-4 names as well, so the structural guard is a backstop and
      not the only thing standing between an expense and the balance sheet
- [x] **Regression test against a population, not spot checks:** a reference chart of accounts
      fixture asserting ≥98% classification, and a second asserting no account whose terminal
      token is `expense` lands on a balance-sheet lead sheet
- [x] Test the three exemptions by name (`Prepaid Expense`, `Accrued Expenses`, `Unearned Revenue`)


**Review notes (COMPLETE).** Reproduced the review's measurement exactly — all 13 names
unclassified, all four misfiles — against a new 95-account reference chart
(`backend/tests/reference_chart_of_accounts.py`). After the fix: **100% classified, 0
disagreements**, with the two legitimate exemptions (`Prepaid Expense` → D, `Accrued Expenses`
→ G) preserved.

**A fifth misfile the review missed.** The reference-chart measurement found
`Notes Payable - Bank` → lead sheet **A (Cash)** at confidence 0.90: the single-word `bank`
rule (0.9) outweighed the `notes payable` phrase (0.85), so **long-term debt was filed as
cash**. Same mechanism as A-4, one sheet over. Fixed by raising the phrase to 0.95. This is the
argument for measuring against a population rather than a list of known-bad names — the
population found a case nobody had thought to look for.

**The arbitration is symmetric, which the report did not ask for but the data demanded.**
`Accrued Payroll Expense` was reaching N, because `payroll expense` (0.90) outranks `accrued`
(0.85) — a liability on the income statement, the mirror image of A-4. Since
`BALANCE_SHEET_MARKER_TOKENS` already encodes the opinion that a leading `accrued` / `prepaid`
/ `deferred` makes an account a balance-sheet account, the rule now applies in both directions,
and only when a balance-sheet rule actually matches the name. `Deferred Tax Expense` therefore
stays on the income statement, correctly, because no balance-sheet rule fits it.


---

### Sprint 805: The sampling tool reports PASS where the method it cites says FAIL
**Status:** COMPLETE.
**Priority:** **P1** — wrong audit conclusion, under a citation that reaches the workpaper.
**Findings:** A-1, A-2, and the registry from A-9 that both land in. **Size:** days.

`sampling_engine.py:53-83` holds `INCREMENTAL_FACTORS_95` / `_90`, cited to "AICPA Audit Sampling
Guide, Table C-1". The Stringer bound's incremental allowance is built from the *increments of the
Poisson reliability factors*, which are arithmetic and therefore checkable exactly. The code's
figures are neither the 95% nor the 90% series:

| Rank | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Published 95% (RF 3.00→4.75→6.30→7.76→9.16→10.52→11.85→13.15) | 1.75 | 1.55 | 1.46 | 1.40 | 1.36 | 1.33 | 1.30 |
| **In code (95%)** | **1.58** | **1.30** | **1.15** | **1.06** | **1.00** | **0.95** | **0.92** |
| Published 90% | 1.58 | 1.44 | 1.36 | 1.31 | 1.28 | 1.26 | 1.24 |
| **In code (90%)** | **1.10** | **0.92** | **0.82** | **0.76** | **0.71** | **0.68** | **0.65** |

Three compounding consequences: the allowance is applied as `max(factor - 1.0, 0.0)` (`:497`), so
every code factor from rank 5 on is ≤ 1.00 and **the 5th and every later misstatement contributes
exactly zero**; `_get_incremental_factors` returns the 95% table for any `confidence_level >= 0.95`,
so **97% and 99% engagements silently use the 95% series**; and the error **understates** the upper
error limit — the unconservative direction, raising the risk of incorrect acceptance. Measured at
BV $10M / TM $500k / EM $100k / 95%, the tool says *pass* at 22, 24 and 26 misstatements where the
Stringer bound says *fail*, and `sampling_memo_generator.py:1559,1565` prints the formula and cites
the Poisson table to the practitioner.

A-2: `shared/aicpa_tables.py` tabulates expansion factors two-dimensionally by
`(confidence_level, expected/tolerable)`. The published AICPA expansion factor depends **only** on
risk of incorrect acceptance (1.9/1.6/1.5/1.4/1.3/1.25/1.2/1.15/1.0 for 1%…50%) and enters the
formula as `n = BV × RF / (TM − EM × EF)` — it scales *expected misstatement*, not the reliability
factor. Direction is conservative, so no conclusion is endangered, but samples run up to **1.40×**
oversized under a citation that does not support the figure. Note that Sprint 684's own commit
message argued the *previous* `1 + e/TM` approximation under-sized samples; at e/TM = 0.25 that
approximation reproduced the AICPA formula exactly. **Sprint 684 replaced a correct result with an
incorrect one on the strength of a table that does not exist in the form described.**

- [x] **Derive, don't tabulate.** Hold the Poisson reliability factors and compute the Stringer
      increments from them, so the two can never disagree again
- [x] Key by confidence level including 97% and 99%; refuse an unsupported level rather than
      silently substituting the nearest table
- [x] Drop the `max(factor - 1.0, 0)` clamp once the values are right — today it only masks the bad tail
- [x] Restore the one-dimensional published expansion-factor table keyed to risk of incorrect
      acceptance, and move it into the **denominator**
- [x] **A-9, scoped to what these two sprints touch:** a figures registry carrying value, source,
      edition and a `verified_by` / `verified_on` stamp — the `standards_registry.py` pattern
      extended from citations to numbers. Both tables above land in it. A free-floating literal
      next to a prose citation is indistinguishable from a verified one, and both read as cited
- [x] Test pinning each increment against the RF series it derives from
- [x] Test reproducing the five measured UEL rows from the report


**Review notes (COMPLETE).** The product now reproduces the review's "correct Stringer UEL"
column **exactly** at all five measured rows — $486,624 / $508,301 / $529,979 / $551,656 /
$573,333 — and the conclusions match (pass at 20; fail at 22, 24, 26, 28). A-2's sample sizes
match the published AICPA formula exactly at every measured e/TM ratio: 66 / 72 / 100 / 300,
against the 70 / 84 / 140 / 360 the product returned before.

**One correction to the report's recommended fix.** §A-1 says to "drop the `max(factor - 1.0,
0)` clamp once the values are right". The `max(…, 0)` part is right to drop — with the correct
series every increment exceeds 1.0, so it can never bind. **The `- 1.0` must stay**, and the
first implementation of this sprint removed it, which inflated every UEL by roughly 35%. The
arithmetic settles it: for a fully-tainted sample the Stringer bound must equal
`interval x RF(k)`, and that identity only holds if the allowance term contributes
`(dRF_i - 1.0)`, because the projected-misstatement term already contributes
`tainting x interval` per misstatement. `TestStringerBoundIdentity` now pins that identity
across three confidence levels and six misstatement counts, so the `- 1.0` cannot be removed
again by the same reasoning.

**A third copy of the wrong table.** The report named two (`INCREMENTAL_FACTORS_95` and `_90`).
`sampling_memo_generator.py:75` held a **third**, `_INCREMENTAL_FACTORS_95`, commented *"must
match sampling_engine.py"* — and hardcoded to the 95% series regardless of the engagement's
actual confidence level. The memo is the artifact that reaches the workpaper citing a Poisson
table to the practitioner, so that copy was printing wrong factors under a citation. All three
now resolve through `shared/audit_figure_registry.py`.

**A-9, delivered for the figures these two sprints touch.**
`backend/shared/audit_figure_registry.py` holds published figures with `source`, `edition`,
`verified_by` and `verified_on`, and refuses to construct a figure set without a verification
stamp. The Stringer increments are **derived** from the reliability-factor series rather than
tabulated, so the two can never disagree again — which is the specific failure A-1 was. The
95%/90%/99% rows are corroborated by the review's independent restatement of their first
differences; the 97%/85%/80% rows are marked as not independently restated, rather than
presented as though they were.


---

### Sprint 806: An insolvent balance sheet is reported as "Conservative leverage position", in green
**Status:** COMPLETE.
**Priority:** **P1** — demo-visible, and ISA 570 going-concern territory.
**Finding:** A-6. **Size:** hours.

`ratio_engine.py:458` tests `if ratio <= DTE_CONSERVATIVE` with no sign guard and assigns
`health = "above_threshold"`. Measured on an insolvent entity (assets $500k, liabilities $700k,
equity **−$200k**, current ratio 0.25, net loss), `debt_to_equity` came back **−3.5** →
*"Conservative leverage position"*. `threshold_status: "above_threshold"` maps to `text-sage-600`
(`IndustryMetricsSection.tsx:105-106`) — the positive colour. So **balance-sheet insolvency
displays the most favourable leverage language in the vocabulary, rendered green.**

`return_on_equity` and `interest_coverage` both carry the negative-equity guard. `debt_to_equity`
and `equity_ratio` do not. Same one-of-three pattern as A-5.

- [x] Sign guard ahead of the threshold ladder in both ratios, returning an explicit insolvency
      interpretation with `below_threshold`
- [x] Strengthen the equity-ratio text: "high reliance on debt financing" is sign-correct but
      materially understated when liabilities exceed assets
- [x] Parametrised negative-equity test across all 17 ratios — this is the scenario a
      going-concern tool must get right


**Review notes (COMPLETE).** Both ratios now return an explicit insolvency interpretation
naming ISA 570, with `threshold_status: "below_threshold"`.

**Measured across the whole ratio surface, not just the two that were wrong.** On the review's
insolvent entity, four ratios still read favourably — DSO, DIO, inventory turnover and
receivables turnover. That is **correct**: they are efficiency measures that do not depend on
the sign of equity, and a distressed entity genuinely can collect receivables and turn
inventory quickly. Recorded as a result rather than remediated, and
`test_the_favourably_reading_ratios_are_only_the_equity_independent_ones` pins the set — so if
a *leverage* or *return* ratio ever joins it, the suite says so.


---

### Sprint 807: Two subprocessors hold customer data and appear on no list, while the DPA commits in writing to the list
**Status:** COMPLETE.
**Priority:** **P1** — a written DPA commitment the artifact does not honour.
**Findings:** C-1, C-2. **Size:** hours.

`docs/04-compliance/SUBPROCESSOR_LIST.md` carries five: Render, Vercel, Stripe, Sentry, SendGrid.
Two are missing:
- **Cloudflare (R2).** `shared/export_share_storage.py` writes export-share **file bytes** to
  `paciolus-exports` keyed `shares/<share_token_hash>` (Sprint 611) — actual customer financial
  export content, the most sensitive payload the product handles. Cloudflare appears in the BCP/DR
  only as a DNS provider and hypothetical CDN fallback, **never as a processor**.
- **Google LLC.** `globals.css:2` loads three families via `@import url('https://fonts.googleapis.com/…')`
  and `proxy.ts:55,57` allowlists both Google font hosts. Every visitor's IP and User-Agent goes to
  Google on every page load.

`DATA_PROCESSING_ADDENDUM.md:208` commits to *"Maintain an up-to-date list of subprocessors"*, and
:210 to a documented vendor risk assessment before engagement. For a product positioned on
Zero-Storage privacy, an unlisted processor holding export bytes is the finding most likely to
surface in a customer security review or a DPA negotiation.

C-2 resolves the Google half by deletion rather than disclosure: a CSS `@import` of a third-party
stylesheet is the slowest possible font load (blocks parsing, then DNS + TLS + two serial round
trips to a second origin before any text paints). `next/font` self-hosts at build time. One change
closes a compliance finding, a performance finding, and two CSP hosts. Sprint 703 planned exactly
this and never executed it.

- [x] Add the Cloudflare R2 row: transfer mechanism, data categories, assessment date
- [x] Migrate the three families to `next/font` with local hosting; drop the `@import` and both
      CSP entries — which removes the Google row rather than adding it
- [x] **Mechanise the check:** extend the Documentation Consistency Gate to assert that every
      external host in the CSP allowlist and every configured storage bucket maps to a
      subprocessor entry. This finding exists because nothing was watching
- [x] Verify the build still emits `ƒ (Dynamic)` and that fonts render in both themes


**Review notes (COMPLETE).** Cloudflare (R2) added with its **actual** engagement date of
2026-04-23 rather than today's, so the record is accurate rather than flattering, and the
change log says plainly that this is a retroactive disclosure. Google was resolved by
elimination: `next/font/google` self-hosts the three families at build time, so the `@import`
is gone, both Google hosts are out of the CSP, and Google never became a row on the list. Build
verified: exit 0, still emitting `ƒ (Dynamic)`.

**The mechanised check is the deliverable.** `scripts/lint_subprocessors.py` reads every
external host out of the CSP in `proxy.ts`, every `@import url(...)` host out of `globals.css`,
and every configured storage bucket out of the backend, and fails if any does not map to an
entry in the Active Subprocessors table. An unmapped host is a **failure**, not a pass —
defaulting to "allowed" would reproduce the hand-maintained-list failure that C-1 and D-4 both
are. The `@import` hosts are scanned separately from the CSP on purpose: that is exactly how
the Google Fonts dependency got in, invisible to anyone reading the CSP.

Two parsing bugs worth recording, because the first draft of this gate reported English words
as undisclosed hosts: `//` comment lines must be stripped before extracting string literals
(prose, and the backticks it uses to quote code, otherwise parse as CSP sources), and CSP
directive strings are delimited by `"` or a backtick **only** — never a single quote, because
CSP *values* contain single quotes (`'self'`), and treating `'` as a delimiter mis-pairs the
quotes and captures whatever sits between two directives.


---

### Sprint 808: The out-of-balance warning hedges about information it is already holding
**Status:** COMPLETE.
**Priority:** **P2** — but the highest-leverage UX fix in the report: it converts Sprint 804's
silent wrong numbers into a visible, actionable list. Ship alongside 804.
**Finding:** D-7. **Size:** days.

`FinancialStatementsPreview.tsx:188` renders *"Balance Sheet is out of balance by $X. This may
indicate unclassified accounts or mapping gaps."* The payload already carries `unclassified_count`
(13 in the A-3 measurement) and the lead sheet Z summary **lists the accounts by name**. A
diagnostic product is telling the user something *may* be wrong while holding the exact answer.

Credit where due: the warning is a real backstop and it did still fire on an
offsetting-accounts case. The weakness is what it declines to say.

- [x] Name the unmapped accounts inline, with a one-click override into the existing
      classification validator — the override path already exists
      (`group_by_lead_sheet(accounts, overrides=…)`)
- [x] Badge the statements as provisional until `unclassified_count` is zero
- [x] Tests for the populated list, the zero state, and the override round-trip


**Review notes (COMPLETE).** The warning now names every unclassified account, states the
consequence (`Net Income is wrong by their amount`), points at the Classification Validator,
and the collapsed header carries a `PROVISIONAL` badge so it is visible without expanding.

**Two things the review did not reach.**

1. **The warning was gated on the wrong condition.** It only fired when the balance sheet
   failed to foot. Unclassified accounts are excluded from **both** statements, so net income
   is wrong by their sum regardless — a dropped expense line and a dropped revenue line of
   equal size leave the balance sheet footing perfectly. The list now appears independently of
   `isBalanced`, and the imbalance warning gets *different words* depending on whether anything
   is unclassified, because a coverage gap and a mapping error are different problems.
2. **A live contract mismatch meant the count had never rendered at all.**
   `frontend/src/types/leadSheet.ts` declared `unmapped_count` and `total_accounts`, and
   `lead_sheet_grouping_to_dict` sent **neither** — it sends `unclassified_count`.
   `LeadSheetSection.tsx:164` guarded its unclassified badge on `data.unmapped_count > 0`, i.e.
   `undefined > 0`, which is always false, and the header rendered `{data.total_accounts}
   accounts`, which printed an empty count. **So the one place the UI tried to surface the
   unclassified count had never once rendered for any upload.** That is why the hedging warning
   was the only signal a practitioner ever got, and it reframes D-7 from a wording problem to a
   broken contract. The backend now sends `total_accounts` and a new `unclassified_accounts`
   name list; the frontend type matches the API; and the UI falls back to the lead sheet Z
   summary so an older cached payload still names the accounts.


---

### Sprint 809: Every app page paints the wrong theme then flips, an undefined token emits no CSS, and two contrast claims overstate the product
**Status:** COMPLETE.
**Priority:** **P2** — visible on every page; two overstated claims in our own docs.
**Findings:** D-1, D-2, D-3, D-4. **Size:** days.

- **D-1.** `layout.tsx:49` server-renders `data-theme="dark"`; `ThemeProvider` resolves the real
  theme in a `useEffect`. **49 of 62 routes are light** — every tool, engagement and settings page.
  All are served dark, painted dark, and flipped after hydration. `await headers()` forces dynamic
  rendering for CSP nonces, so no static prerender softens it.
- **D-2.** `text-content-muted` is **not a token** — `tailwind.config.js:86-91` defines
  primary/secondary/tertiary/disabled and there is no `--text-muted`. Proven against the compiled
  stylesheet: it emits **0 occurrences** of CSS. **36 live usages** across checkout, billing, team,
  shares, branding, admin-dashboard and internal/admin silently inherit colour. `lint_design_tokens.py`
  passes it because it bans *generic Tailwind* colours and never asks whether a brand token exists.
- **D-3.** `sage-500` is 3.85:1 on the dark page and 4.42:1 on the light page — **AA FAIL in both**.
  `clay-500` is 3.69:1 on dark. **61 usages of `text-sage-500`/`text-clay-500` carry no theme
  qualifier**; zero have a `dark:` variant. The codebase is otherwise disciplined (298 × `sage-400`,
  159 × `sage-600`, 118 × `sage-700`; an import-graph trace of all 62 routes found only 4 files
  carrying a shade illegible on a theme they render in) — the 500 shades are the hole. Two claims
  overstate it: `CLAUDE.md:108` says "WCAG AAA" and `DESIGN_GUIDELINES.md:523` says "AA baseline,
  AAA in several areas". AAA is reached only by `text-primary` and the 700 shades.
- **D-4.** `ThemeProvider.tsx:16-34` is a hand-maintained exact-match array. Absent:
  `/forgot-password`, `/reset-password`, `/checkout`, `/checkout/success`. The `(auth)` layout
  paints its own gradient, which masks it for the password routes — **`/checkout` does not
  benefit**: it paints `bg-surface-page`/`bg-surface-card` and uses 33 semantic tokens, so it
  resolves the **light** palette inside the dark auth shell, **on the page where customers pay.**
  This is the DEC's own H3 pattern: a hand-maintained list that stopped matching.

- [x] Resolve the theme server-side in the layout; the pathname is available without a client effect
- [x] Derive the theme from the route group rather than a literal list; assert every one of the 62
      routes resolves to exactly one theme
- [x] Define `content-muted` or migrate the 36 usages to `tertiary` — then **extend the gate** to
      resolve every `content-*` / `surface-*` / `border-*` class against the config, which closes
      the whole class rather than this instance
- [x] Reassign the 61 unqualified 500-shade usages to 600/700 on light, 400/300 on dark
- [x] Add a contrast check to `lint_design_tokens.py` — it already knows every token's value, so
      the pairing check is the natural extension
- [x] Correct the AAA claims in `CLAUDE.md` and `DESIGN_GUIDELINES.md` to AA


**Review notes (COMPLETE).** D-1: the theme is resolved server-side from an `x-pathname` header
set by the proxy, so first paint is correct; the client effect remains for client-side
navigations, and both paths call the same `resolveTheme`. D-4: `DARK_ROUTES` moved to
`lib/theme-routes.ts`, and `theme-routes.test.ts` walks `src/app` for every `page.tsx`, derives
each route's URL and route group, and asserts the dark set is **exactly** the pages under
`(marketing)` and `(auth)` — 34 assertions, all passing, including all four routes D-4 measured
as missing. A URL does not carry its route group, so the map must stay data; what it no longer
is, is unchecked.

**One correction to the report's recommended fix for D-3.** §D-3 says to reassign the 61
unqualified usages "to 600/700 on light and 400/300 on dark", which implies `dark:` variants.
**This codebase has no `dark:` mechanism** — there is no `darkMode` setting in
`tailwind.config.js` and not one `dark:` variant in 778 source files. Theming is entirely
`data-theme` plus CSS custom properties, so a `dark:` variant would bind to the viewer's *OS
preference*, not the app's route-derived theme — correct-looking and wrong. The architecture's
own answer is the semantic tokens, which already flip with `data-theme` and already pass AA in
both themes (dark: sage-300 9.78:1, clay-300 8.53:1; light: sage-600 5.98:1, clay-600 5.80:1).
All 63 usages went to `text-theme-success-text` / `text-theme-error-text`.

**D-2 resolved by migration, not by defining a fifth tier.** The documented hierarchy is
primary/secondary/tertiary/disabled; adding `muted` would invite the same drift. All 36 usages
went to `tertiary`, which is already AA-tuned on light (5.0:1).

**The gate extension found two shades the review did not.** Deriving contrast from the palette
rather than hardcoding it surfaced `oatmeal-700` (4.38:1 dark / 3.89:1 light, **48 usages**) and
`obsidian-400` (4.19:1 / 4.07:1, 11 usages) as failing AA on both surfaces. `obsidian-400` is a
permanent exemption — it is the `--text-disabled` value, and WCAG 2.1 SC 1.4.3 exempts inactive
UI components. `oatmeal-700` is **not** defensible as one, and is not claimed to be: no oatmeal
shade reaches AA on the light page surface (700 is the best at 3.89:1) because oatmeal is the
*light* palette, so each usage needs a per-surface decision that requires the route→theme map.
It is recorded as a non-permanent exemption, printed on every run of the gate, and listed in
`DESIGN_GUIDELINES.md`. **Migrating 48 usages blind would have been a design decision disguised
as a lint fix.**

Both overstated claims corrected: `CLAUDE.md:108` now says WCAG 2.1 AA, and
`DESIGN_GUIDELINES.md:523` states what AAA actually covers (`text-primary` and the 700 shades)
with the measurements.


---

### Sprint 810: Hygiene with teeth — table overflow, presence-as-capability, and a nightly verdict that is wrong by clock
**Status:** COMPLETE.
**Priority:** **P2/P3.**
**Findings:** D-5, T-3, T-4. **Size:** 1 sprint.

- **T-4.** `reports/nightly/2026-10-22.md` published **🔴 RED** with 14 failures in the two audit-gate
  test files. Re-run on the current tree: **60 passed, 0 failed.** The suite ran at 02:00; the fixes
  landed later the same day. The DEC report records the identical artifact for the prior day — **two
  consecutive days where the headline verdict was wrong by clock.** A RED that is routinely a timing
  artifact trains its reader to discount RED, which is how a real one gets missed.
- **T-3.** The DEC's F-005 corrected four test classes asserting `callable(...)`. **27 occurrences
  remain across 10 files**, including `test_billing_routes.py`, `test_pricing_integration.py`,
  `test_rate_limit_tiered.py` and `test_retention_cleanup.py` — billing and rate limiting.
- **D-5.** 68 `<table>` elements, 41 `overflow-x-*` wrappers. 13 files unwrapped, including
  `(marketing)/privacy` with **10 tables** — and marketing pages take the most mobile traffic.

- [x] Stamp each nightly brief with the SHA it tested, and have the compiler mark itself
      **superseded** when `HEAD` has moved past that SHA — `briefing_compiler.py` already has the
      three-outcome shape to express it
- [x] Triage all 27 `callable(...)` assertions: each becomes a behavioural assertion or a
      documented exemption
- [x] Wrap the 13 unwrapped table sites in `overflow-x-auto`, and add a lint rule, since this recurs


**Review notes (COMPLETE).** D-5: all 28 unwrapped tables across 14 files wrapped in
`overflow-x-auto` (the scan found one more file than the review listed — 68 tables, 41 wrappers
before, 69 after, 0 unwrapped). T-4: each brief now carries `**Tested commit:**` and a
supersession line that re-checks HEAD at read time, so a verdict that no longer describes the
tree says so instead of reading as current.

**T-3 triaged all 27, and the split matters.** Fourteen were genuine
presence-as-capability and became `assert_signature` contract assertions via a new
`tests/helpers/contract_assertions.py` — a renamed, reordered or dropped parameter now fails,
which `callable` could never see. The signatures pinned include the checkout and subscription
functions on the money path and the client-access guards that decide whether a user may read
another user's client. Two became behavioural: `RATE_LIMIT_AUTH` is now **called** and its
resolved limit parsed as `<count>/<period>`, and `try_parse_risk` / `try_parse_risk_band` are
exercised (both coerce an unknown value to LOW, which is worth pinning — "unknown risk reads as
low risk" should have to be changed deliberately).

The remaining eleven are **legitimate** and are documented as such: Protocol conformance
(`callable(getattr(cls, "to_dict", None))` — the assertion *is* "this class exposes a to_dict
method"), slowapi's dynamic-limit interface, a dependency-surface check against slowapi itself,
and an allowlist whose whole point is that it names functions that exist.

**The gate is the deliverable, not the 27 edits.** F-005 fixed four of these four months ago and
the pattern came back, because nothing was watching —
the same shape as C-1 and D-4 in the same review. `tests/test_presence_as_capability_gate.py`
requires every remaining `assert callable(...)` to appear in a documented allowlist with a
reason, keyed by **line content rather than line number** so editing a file above an exemption
cannot silently re-arm it. It also asserts the reverse — an exemption with no matching
assertion is dead permission and must be removed — and that the scan itself finds something,
because a regex that silently matches nothing would make the whole gate vacuous.


---

### Sprint 811: `tax_year` is a required input that no statutory constant is keyed by
**Status:** COMPLETE.
**Priority:** **P2** — the structural half of A-7. The figures stay with Sprint 793b.
**Finding:** A-7 (structural only). **Size:** hours.

`w2_reconciliation_engine.py:39-50` is headed `# --- 2026 reference values ---` and every figure in
it is the **2025** statutory set (SS wage base 176,100; 401(k) 23,500; catch-up 7,500; HSA
4,300/8,550; SIMPLE 16,500). The 2026 column needs a practitioner and stays with 793b.

**The structural finding needs no confirmation:** `tax_year` is a required input accepted for any
year 2000–2099 (`routes/w2_reconciliation.py:120`) and **no statutory constant is keyed by it**. The
route's own docstring says so. A mislabelled block is worse than a stale one, because the comment
defeats the next reader's check.

- [x] Year-key the tables and label the 2025 set as 2025
- [x] **Refuse** a tax year with no table rather than silently falling back — Sprint 793a's
      per-request overrides are the documented escape hatch and stay
- [x] Print the statutory set's effective year on the memo, so the workpaper carries its own provenance
- [x] **CEO note:** this makes the W-2 tool refuse a 2026 engagement until 793b lands or the caller
      passes overrides. That is the honest behaviour — today it answers 2026 questions with 2025 law
      and says nothing — but it is a visible behaviour change, not a silent fix


**Review notes (COMPLETE).** Statutory limits are keyed by tax year in
`STATUTORY_LIMITS_BY_YEAR`, the 2025 set is labelled 2025, and `statutory_limits_for_year()`
raises `StatutoryLimitsUnavailableError` for a year it has no table for. Sprint 793a's
per-request overrides remain the escape hatch and are unchanged. The result and the API response
now carry `statutory_basis` — the year whose table produced the findings, or null when the
caller supplied every figure — so the workpaper carries its own provenance.

**The refusal is a `W2ReconciliationInputError` subclass, deliberately.** Both routes already
map that to a verbatim 400. A bare `ValueError` would have been run through the analyze route's
`sanitize_error`, stripping the actionable half of the message, and the CSV export route does
not catch `ValueError` at all — it would have been a 500.

**What the test suite revealed about the mislabelling.** All 17 tests in
`test_w2_reconciliation_engine.py` passed `tax_year=2026` while asserting against figures that
are the **2025** statutory set. They were green because the engine applied one fixed set to
every year, so passing 2026 and asserting 2025 law agreed with itself. All now pass
`tax_year=2025`, which is what they were always testing.

**CEO decision required.** The W-2 tool now **refuses** a 2026 engagement unless the caller
supplies the statutory figures. That is the honest behaviour — today it answers 2026 questions
with 2025 law and says nothing — but it is a visible behaviour change, and it stays that way
until Sprint 793b lands practitioner-confirmed 2026 figures.
`test_no_table_claims_to_be_2026_until_sprint_793b` guards against anyone adding an unconfirmed
2026 row in the meantime, which would recreate exactly the defect being fixed: a figure that
reads as authoritative because it sits in an authoritative-looking table.


---

