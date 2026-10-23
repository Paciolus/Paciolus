# Paciolus Full-Spectrum Improvement Review — 2026-10-22

**Scope:** accounting methodology, technical quality, design/UX, compliance.
**Basis:** every finding below was produced by running the code, not by reading it. Probe
scripts were written to the session scratchpad; no repository file was modified.
**Tree reviewed:** `dec-review-2026-10-22-remediation` at `c12a6dcb`.

## Why this review went where it did

The Digital Excellence Council review landed earlier the same day and remediated all 14 of its
findings. Its own Agent Coverage Report named the areas it did **not** cover, and §6 listed
seven things it could not verify. This review deliberately targets those gaps rather than
re-walking covered ground:

| DEC coverage | This review |
|---|---|
| "Runtime behaviour of the 18 tools — **no tool was exercised against a real trial balance end-to-end**" | Drove the lead-sheet classifier, statement builder, cash flow, ratio and sampling engines directly |
| AccountingExpertAuditor: ISA 530 projection math "**deliberately not adjudicated**" | Checked the Stringer bound and expansion factors against published tables |
| DX & Accessibility Lead: "**Thin** — design-token lint verified clean; no a11y, no component review" | Measured contrast, theming, token validity, responsive overflow |
| Performance Alchemist: "**Thin**" | Build, bundle, font loading, index coverage, pandas usage |
| Frontend: "778 source files; only two tool pages examined" | Import-graph traced theme/token correctness across all 62 routes |

**One correction to a DEC statement.** The DEC recorded "Money correctness: WARNING" on the
basis of two form-input engines. Exercising the trial-balance path — the product's core —
found the defects below, which are larger in blast radius than either of those. The DEC was
right that the *storage* layer is sound; the defects are in classification and composition.

---

## Executive summary

**22 findings: 7 P1, 8 P2, 7 P3/product-gap.**

Four themes, each confirmed by measurement:

1. **The trial-balance path drops and misfiles ordinary accounts.** 19% of a plain-vanilla
   chart of accounts lands in `Unclassified` — including the entire compensation block — and
   four more accounts are filed to the wrong statement *with high confidence*. Unclassified
   accounts fall out of the income statement, so net income is wrong by their sum.
2. **Two wrong numbers reach client-facing PDFs.** Every exported EBITDA equals operating
   income, because the depreciation add-back is structurally unreachable. The statistical
   sampling tool can report **PASS where the Stringer bound says FAIL**.
3. **Authoritative citations sit on top of non-authoritative numbers.** Two sampling tables
   cite the AICPA Audit Sampling Guide and match neither the published 95% nor 90% series.
4. **Two subprocessors process customer data and appear on no list** — while the DPA commits
   in writing to maintaining that list.

**What is genuinely well-built** (measured, and recorded so the next reviewer doesn't re-derive
it): FK index coverage; pandas vectorisation; the ratio engine's refusal behaviour on empty
input; the out-of-balance warning; `jsx-a11y` wiring; the Sprint 795 depreciation fix, which
*refuses rather than substitutes*.

---

# 1. Accounting

### A-1 — Statistical sampling can report PASS where the Stringer bound says FAIL — **P1**

`sampling_engine.py:53–83` holds `INCREMENTAL_FACTORS_95` / `_90`, cited to "AICPA Audit
Sampling Guide, Table C-1". The Stringer bound's incremental allowance is built from the
*increments of the Poisson reliability factors*. Those increments are arithmetic, so they can
be checked exactly:

| Misstatement rank | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Published, 95% (RF 3.00 → 4.75 → 6.30 → 7.76 → 9.16 → 10.52 → 11.85 → 13.15) | 1.75 | 1.55 | 1.46 | 1.40 | 1.36 | 1.33 | 1.30 |
| **In code (`INCREMENTAL_FACTORS_95`)** | **1.58** | **1.30** | **1.15** | **1.06** | **1.00** | **0.95** | **0.92** |
| Published, 90% | 1.58 | 1.44 | 1.36 | 1.31 | 1.28 | 1.26 | 1.24 |
| **In code (`INCREMENTAL_FACTORS_90`)** | **1.10** | **0.92** | **0.82** | **0.76** | **0.71** | **0.68** | **0.65** |

Three compounding consequences:

- The allowance is applied as `max(factor - 1.0, 0.0)` (`sampling_engine.py:497`). Every code
  factor from rank 5 onward is ≤ 1.00, so **the 5th and every subsequent misstatement
  contributes exactly zero incremental allowance.**
- `_get_incremental_factors` returns the 95% table for any `confidence_level >= 0.95`, so **97%
  and 99% engagements silently use the 95% series** (published 99% rank-1 increment is 2.03).
- The error is one-directional: it **understates** the upper error limit, which is the
  unconservative direction — it increases the risk of incorrect acceptance.

**Measured.** BV $10,000,000, TM $500,000, EM $100,000, 95% confidence (n=117, interval
$86,021.51), misstatements each tainted 0.10:

| Misstatements | Product UEL | Conclusion | Correct Stringer UEL | Correct conclusion |
|---|---|---|---|---|
| 20 | $439,484 | pass | $486,624 | pass |
| **22** | **$456,688** | **pass** | **$508,301** | **fail** |
| **24** | **$473,892** | **pass** | **$529,978** | **fail** |
| **26** | **$491,097** | **pass** | **$551,656** | **fail** |
| 28 | $508,301 | fail | $573,333 | fail |

At 22–26 misstatements the tool tells the auditor the population is acceptable when the method
it names rejects it. The memo generator prints the formula and cites a Poisson table to the
practitioner (`sampling_memo_generator.py:1559,1565`), so the wrong factor reaches the
workpaper as cited authority.

**Fix:** replace both tables with the published reliability-factor increments; key by
confidence level including 97%/99%; drop the `max(factor - 1.0, 0)` clamp once the values are
right (it is only masking the bad tail today). Pin the table against the RF series in a test
so an increment can never again be a free-floating literal.

### A-2 — Expansion-factor table is not the published AICPA table — **P2**

`shared/aicpa_tables.py` tabulates expansion factors two-dimensionally by
`(confidence_level, expected/tolerable)`, rising to 3.00, cited to "Appendix A Table A-1".
The published AICPA expansion factor depends **only on risk of incorrect acceptance** —
1.9 / 1.6 / 1.5 / 1.4 / 1.3 / 1.25 / 1.2 / 1.15 / 1.0 for 1%…50% — and enters the formula as
`n = BV × RF / (TM − EM × EF)`, i.e. it scales *expected misstatement*, not the reliability
factor.

**Measured** (BV $10,000,000, TM $500,000, 95%):

| e/TM | Product n | AICPA-formula n | Ratio |
|---|---|---|---|
| 0.05 | 70 | 66 | 1.06× |
| 0.10 | 84 | 72 | 1.17× |
| 0.25 | 140 | 100 | **1.40×** |
| 0.50 | 360 | 300 | 1.20× |

The direction is conservative, so no audit conclusion is endangered — but the client is billed
for up to 40% more sample items than the standard requires, under a citation that does not
support the figure. Note that Sprint 684's own commit message argues the *previous* homemade
`1 + e/TM` approximation under-sized samples; at e/TM = 0.25 that approximation actually
reproduced the AICPA formula exactly. **Sprint 684 replaced a correct result with an incorrect
one on the strength of a table that does not exist in the form described.**

**Fix:** restore the one-dimensional published table keyed to risk of incorrect acceptance and
move it into the denominator. Treat this as the template case for A-9 below.

### A-3 — 19% of an ordinary chart of accounts is left Unclassified, and drops out of the statements — **P1**

Driving `group_by_lead_sheet` with a 68-account chart of accounts built from standard names:

**13 of 68 (19%) → lead sheet Z `Unclassified`, confidence 0.50, zero keywords matched:**

> Salaries and Wages Expense · Salaries Expense · Wages Expense · Officer Compensation ·
> Employee Benefits · Commissions Expense · Contract Labor · Legal and Accounting ·
> Charitable Contributions · Postage and Delivery · Lease Liability · Owner's Draw ·
> Consulting Income

The compensation block is the whole of it for most entities — payroll is typically the largest
expense line in a service business. `Lease Liability` is notable because the product ships a
lease-accounting engine. `Owner's Draw` exists in every S-corp and partnership.

**Root cause for the salary family** is precise and small: `lead_sheet_mapping.py:365–366`
registers `"salary expense"` and `"wage expense"` as **singular phrases**. Real charts of
accounts overwhelmingly use the plural — "Salaries Expense", "Wages Expense", "Salaries and
Wages". Neither matches. `"payroll expense"` *is* registered and does match, which is why the
gap has stayed invisible.

**Downstream, measured.** Unclassified accounts are excluded from both statements. On a
balanced trial balance containing `Salaries and Wages Expense` of $300,000, the builder
returned **net income $460,000 against a true $160,000** — overstated by exactly the dropped
salary line — and a balance sheet out by $280,000.

**Mitigating control, credited:** the UI does warn when the balance sheet does not foot
(`FinancialStatementsPreview.tsx:178–191`), and an offsetting-accounts case was tested and
*did* still trigger the warning. The warning is a real backstop. See D-7 for its weakness.

**Fix:** add the plural and compound compensation forms, plus the ten other names above; then
add a regression test that asserts a reference chart of accounts classifies at ≥ 98%, so the
keyword table is measured against a population rather than spot-checked.

### A-4 — Four accounts are filed to the wrong statement *with high confidence* — **P1**

Worse than A-3, because `unclassified_count` does not count these and the product reports
confidence 0.80–0.90:

| Account | Classified to | Confidence | Matched on | Should be |
|---|---|---|---|---|
| Payroll Tax Expense | **H — Current Liabilities** | 0.90 | `payroll tax` | Operating expense |
| Bank Service Charges | **A — Current Assets** | 0.90 | `bank` | Operating expense |
| Software Expense | **F — Non-Current Assets** | 0.80 | `software` | Operating expense |
| Vehicle Expense | **E — Non-Current Assets** | 0.90 | `vehicle` | Operating expense |

Each is an expense posted to the balance sheet: net income overstated, assets or liabilities
overstated, and no signal to the user. The mechanism is a substring keyword winning over the
word "Expense" in the same account name.

**Fix:** make an explicit `expense`/`income` suffix outrank a balance-sheet substring, or
weight terminal words above embedded ones. Then run the A-3 reference-chart test, which would
have caught all four.

### A-5 — The cash-flow depreciation add-back is unreachable, and every exported EBITDA equals operating income — **P1**

`financial_statement_builder.py:970` reads the account name as `acct.get("name", "")`. The
serialized account dicts carry the key **`account`**, never `name`
(`lead_sheet_mapping.py:633–652` passes `s.accounts` through verbatim). Proven directly:

```
serialized account dict keys: ['account','credit','debit','is_override',
                               'lead_sheet','lead_sheet_confidence','lead_sheet_keywords','type']
has 'name'? False   |   has 'account'? True
```

So `_extract_depreciation()` compares every keyword against the empty string and **always
returns 0.0**, for every trial balance. Consequences:

- The ASC 230 / IAS 7 indirect-method statement **never** contains the depreciation and
  amortisation add-back — the single largest non-cash reconciling item in the method. Confirmed
  on a trial balance containing an account named exactly `Depreciation Expense`, classified to
  lead sheet N at confidence 0.95: no add-back appeared.
- The failure is disguised as a data-quality note about the customer's file:
  *"Depreciation not separately identified in trial balance"* (line 1055). It reads as an
  observation about the input, not a defect in the tool.
- `pdf/sections/ratios.py:84–91` computes `ebitda = operating_income + depreciation_amount`.
  Since that term is always 0.0, **every exported ratio PDF reports EBITDA equal to operating
  income, and EBITDA margin equal to operating margin.**

**The decisive detail:** the sibling function `_extract_interest_expense` at line 1003 reads
`acct.get("name", "") or acct.get("account", "")` — it was fixed. `_extract_depreciation`
twenty lines earlier was not. Two functions of identical shape, one corrected, one left. The
same wrong key also makes `_account_descriptions` (line 415) a list of empty strings; it is
built and never read, so it is dead code carrying the same bug.

**Fix:** one-line key correction in both places; delete `_account_descriptions`; add a test
asserting the add-back appears for a TB containing a depreciation account, and a second
asserting `EBITDA > operating_income` when depreciation is present.

### A-6 — Negative equity is reported as "Conservative leverage position", in green — **P1**

`ratio_engine.py:458` tests `if ratio <= DTE_CONSERVATIVE` with no sign guard, and assigns
`health = "above_threshold"`. Measured on an insolvent entity (assets $500k, liabilities $700k,
equity **−$200k**, current ratio 0.25, net loss):

| Ratio | Value | Interpretation returned |
|---|---|---|
| debt_to_equity | **−3.5** | **"Conservative leverage position"** |
| equity_ratio | −0.4 | "Low equity ratio - high reliance on debt financing" |
| return_on_equity | 75.0 | "Warning: Negative equity with losses" ✅ |
| interest_coverage | −2.5 | "Operating loss — earnings do not cover interest" ✅ |

`threshold_status: "above_threshold"` maps to `text-sage-600`
(`IndustryMetricsSection.tsx:105–106`) — the positive colour. So an entity with
**balance-sheet insolvency**, a going-concern indicator under ISA 570, displays the most
favourable leverage language in the vocabulary, rendered green. ROE and interest coverage both
carry the negative-equity guard; D/E and equity ratio do not. Same one-of-three pattern as A-5.

The equity ratio's "Low … high reliance on debt financing" is sign-correct but materially
understated: a negative equity ratio means liabilities exceed assets.

**Fix:** guard the sign ahead of the threshold ladder in both ratios and return an explicit
insolvency interpretation with `below_threshold`. Add a parametrised negative-equity test
across all 17 ratios — this is the scenario a going-concern tool must get right.

### A-7 — Statutory payroll limits are a single hardcoded year, labelled as a different year — **P2**

`w2_reconciliation_engine.py:39–50` is headed `# --- 2026 reference values ---`. Every figure
in it is the 2025 statutory set:

| Constant | In code | 2025 | 2026 |
|---|---|---|---|
| `DEFAULT_SS_WAGE_BASE` | 176,100 | 176,100 | 184,500 |
| `DEFAULT_401K_ELECTIVE_LIMIT` | 23,500 | 23,500 | 24,500 |
| `DEFAULT_401K_CATCHUP_50` | 7,500 | 7,500 | 8,000 |
| `DEFAULT_HSA_SELF_ONLY` / `_FAMILY` | 4,300 / 8,550 | 4,300 / 8,550 | 4,400 / 8,750 |
| `DEFAULT_SIMPLE_IRA_LIMIT` | 16,500 | 16,500 | 17,000 |

> The 2026 column must be practitioner-confirmed before it is actioned — it is stated here as
> the reason to prioritise Sprint 793b, not as an authority. **The structural finding needs no
> confirmation:** `tax_year` is a required input accepted for any year 2000–2099
> (`routes/w2_reconciliation.py:120`) and **no statutory constant is keyed by it**. The route's
> own docstring says so plainly. A mislabelled block is worse than a stale one, because the
> comment defeats the next reader's check.

**Fix (Sprint 793b):** year-keyed tables, reject tax years with no table rather than falling
back, and print the statutory set's effective year on the memo so the workpaper carries its own
provenance. Sprint 793a's per-request overrides are the right stopgap and should stay.

### A-8 — Depreciation coverage is a fraction of US fixed-asset practice — **product gap**

The Sprint 795 fix is **the right shape and should be the template** — it refuses with a named
error rather than substituting a different system. The tables it does hold were verified
against IRS Pub 946 and are correct: 200% DB half-year for 3/5/7/10-year (exact to the
hundredth, each summing to 100.00), 150% DB for 15/20-year, and all four mid-quarter 5-year
quarters.

What a practitioner cannot do today: 150% DB election for 3/5/7/10-year property · GDS
straight-line election · ADS · real property (27.5-year residential, 39-year nonresidential) ·
mid-quarter for anything but 5-year · **Section 179** · **§168(k) bonus depreciation** (no
reference to either anywhere in the backend).

Bonus depreciation and §179 appear on most US fixed-asset schedules; real property covers every
rental and commercial client. **Fix:** practitioner-confirmed figures, then land them in the
A-9 registry.

### A-9 — Structural: statutory and authoritative figures are scattered literals — **P2**

A-1, A-2, A-7 and A-8 are four instances of one weakness: **published figures live as bare
literals next to a prose citation, with nothing tying them to the authority they name.** Where
that pattern exists, a free-floating literal is indistinguishable from a verified one, and both
read as cited.

The DEC's F-004 found the same shape in the monetary-precision guard. The repo already has the
better pattern twice — `backend/standards_registry.py` and `backend/tools_registry.py` are
single sources of truth enforced by `test_citation_consistency.py`.

**Fix:** extend that pattern to numbers. One registry per authority (IRS Pub 946, AICPA Audit
Sampling Guide, IRC statutory limits) carrying value, source, edition/tax year, and a
`verified_by` + `verified_on` field. Derive relationships rather than tabulating them — the
Stringer increments from the RF series, so the two can never disagree. Then a single test can
assert that every citation in a memo resolves to a registry entry with a verification stamp.

---

# 2. Technical

### T-1 — mypy is a ratchet over 1,011 errors — **P2**
`mypy.ini` sets `disallow_untyped_defs`, `disallow_incomplete_defs`, `warn_return_any`,
`strict_equality`. `ci.yml:475–505` then gates on `.github/lint-baseline.json`, where
`mypy.total_errors = 1011` with the note *"Systemic: Column[int] type leakage, Decimal/float
boundary, missing annotations across 131 files"*. Ruff and ESLint baselines are both 0; only
mypy carries debt. **"Decimal/float boundary"** is the concerning entry given A-1 through A-6
are all composition defects. **Fix:** burn down by module with per-module floors, starting with
the engines that compute money.

### T-2 — The least-tested code is what the customer receives — **P2**
Backend coverage is 93.57% overall, but concentrated misses sit in the output layer:
`excel_generator.py` 45.7% (328 of 604 statements uncovered) · `leadsheet_generator.py` 11.3% ·
`workbook_inspector.py` 18.6% · `population_profile_memo.py` 39.7% · `pdf/sections/diagnostic.py`
64.9%. These produce the artifacts a practitioner hands to a client — and A-5 is a defect in
exactly this layer that a test would have caught. **Fix:** per-file floors for the generators.

### T-3 — The presence-as-capability pattern is larger than the four classes fixed — **P2**
The DEC's F-005 corrected four test classes asserting `callable(...)`. **27 occurrences remain
across 10 files**, including `test_billing_routes.py`, `test_pricing_integration.py`,
`test_rate_limit_tiered.py`, `test_retention_cleanup.py` — billing and rate limiting.
**Fix:** triage all 27; each becomes a behavioural assertion or a documented exemption.

### T-4 — The nightly brief publishes a verdict its own tree has already invalidated — **P2**
`reports/nightly/2026-10-22.md` reports **🔴 RED** with 14 new failures in
`test_npm_audit_gate.py` / `test_pip_audit_gate.py`. Re-run on the current tree: **60 passed, 0
failed.** The suite ran at 02:00; the fixes landed later the same day. The DEC report records
the identical timing artifact for the prior day — **two consecutive days where the headline
verdict was wrong by clock**. A RED that is routinely a timing artifact trains its reader to
discount RED, which is how a real one gets missed. **Fix:** stamp each brief with the SHA it
tested, and have the compiler mark itself superseded when `HEAD` has moved past that SHA —
`briefing_compiler.py` already has the three-outcome shape to express it.

### T-5 — Dependency drift, with the audit gate as the only thing holding the line — **P3**
60 backend and 22 frontend packages outdated; 4 security-relevant. `anthropic` 0.96 → 2.1 and
`argon2-cffi-bindings` 25.1 → 26.1 are majors; Argon2id hashes the export-share passcodes. Per
the pinning rule at the top of `requirements.txt`, exact pins cannot self-heal, so the weekly
`dependency-compliance` pip-audit staying green is load-bearing. **Fix:** continue Sprint 786b
steps 3–4; treat the Argon2 binding as the priority.

### T-6 — Measured and sound; recorded so it is not re-derived
- **FK indexing:** of 44 FK columns, 17 lack an index — and all 17 are audit-attribution
  columns (`created_by`, `updated_by`, `archived_by`, `invited_by_user_id`). Every FK that is
  actually a query predicate is covered, mostly as the leading column of a composite. The one
  apparent exception, `tool_activities.engagement_id`, is **never** used as a predicate. No work
  required.
- **pandas:** exactly **one** `.iterrows()` in the entire non-test backend. Vectorisation is real.
- **Ratio engine on empty input:** every one of 18 ratios returns `None` with an explicit
  reason (*"Cannot calculate: No equity identified"*). This is the correct behaviour and the
  direct counter-example to D-7 — one engine refuses to answer, the statement builder answers
  "balanced".

---

# 3. Design & UX

### D-1 — Every app page paints the wrong theme, then flips — **P2**
`layout.tsx:49` server-renders `<html lang="en" data-theme="dark">`. `ThemeProvider` resolves
the real theme from the pathname inside a `useEffect` (`ThemeProvider.tsx:38–41`). **49 of 62
routes are light** — every tool, engagement and settings page. All of them are served dark,
painted dark, and flipped to light after hydration. `await headers()` in the root layout forces
dynamic rendering for CSP nonces, so no static prerender softens it. **Fix:** resolve the theme
server-side in the layout and set the attribute in the server-rendered HTML; the pathname is
available without a client effect.

### D-2 — `text-content-muted` is not a token, and the gate cannot tell — **P2**
`tailwind.config.js:86–91` defines `content.primary/secondary/tertiary/disabled`. There is no
`muted`, and no `--text-muted` in `globals.css`. **36 usages exist** — `(auth)/checkout`,
`settings/billing`, `settings/team`, `settings/shares`, `settings/branding`,
`settings/admin-dashboard`, `internal/admin`, `billing/PlanCard`, `billing/UpgradeModal`.
Proven against the compiled stylesheet:

```
text-content-primary    8 occurrences
text-content-secondary  4
text-content-tertiary  12
text-content-disabled   4
text-content-muted      0      <-- emits no CSS
```

Those 36 elements get no colour rule and inherit, silently losing the muted tier of the
hierarchy across the billing and settings surfaces. `lint_design_tokens.py` — correctly
described by the DEC as the best-built guard in the repo — passes it, because it bans *generic
Tailwind* colours and never asks whether a brand token exists. **Fix:** define the token or
migrate the 36 to `tertiary`; then extend the gate to resolve every `content-*` / `surface-*` /
`border-*` class against the config, which closes the whole class.

### D-3 — The mandate's two semantic tokens fail AA where they are used unqualified — **P2**
Computed per WCAG 2.1 against the real surfaces (`#121212` dark page, `#F5F4F2` light page):

| Token | On dark page | On light page | Role in the mandate |
|---|---|---|---|
| `sage-500` | 3.85:1 **FAIL** | 4.42:1 **FAIL** | "SUCCESS states use sage-*" |
| `clay-500` | 3.69:1 **FAIL** | 4.62:1 AA | "ERROR/EXPENSE states use clay-*" |
| `text-primary` | 15.44:1 AAA | 14.65:1 AAA | — |
| `sage-700` / `clay-700` | — | 8.18 / 7.65 AAA | — |

**61 usages of `text-sage-500` / `text-clay-500` carry no theme qualifier** — zero have a
`dark:` variant — so `sage-500` as text fails AA in *both* themes. Credit where due: the
codebase overwhelmingly uses the theme-correct shades (298 × `sage-400`, 159 × `sage-600`,
118 × `sage-700`), and an import-graph trace of all 62 routes found only **4 files** carrying a
shade illegible on a theme they actually render in. The system is disciplined; the 500 shades
are the hole.

Two claims overstate this: `CLAUDE.md:108` says "WCAG AAA" and
`docs/08-internal/DESIGN_GUIDELINES.md:523` says "AA baseline, AAA in several areas". AAA is
reached only by `text-primary` and the 700-shades. **Fix:** correct both claims to AA;
reassign the 61 unqualified usages to 600/700 on light and 400/300 on dark; add a contrast
check to `lint_design_tokens.py` — it already knows every token's value, so the pairing check
is the natural extension.

### D-4 — The route→theme map is a hand-maintained exact-match list, and four shipped routes are missing — **P3**
`ThemeProvider.tsx:16–34` is an array compared with `DARK_ROUTES.includes(pathname)`. Absent:
`/forgot-password`, `/reset-password`, `/checkout`, `/checkout/success`. Today the `(auth)`
layout paints `bg-gradient-obsidian` itself, which masks the omission for the two password
routes. **`/checkout` does not benefit:** it paints its own `bg-surface-page` / `bg-surface-card`
and uses 33 semantic tokens, so it resolves the **light** palette and renders as a light page
inside the dark auth shell — on the page where customers pay. This is the DEC's own H3 pattern
("hand-maintained list that stopped matching"). **Fix:** derive the theme from the route group
rather than a literal list, and assert every route resolves to exactly one theme.

### D-5 — 13 files render tables with no horizontal overflow container — **P3**
68 `<table>` elements, 41 `overflow-x-*` wrappers. Unwrapped: `(marketing)/privacy`
(**10 tables**) · `(marketing)/terms` · `settings/admin-dashboard` · `settings/shares` ·
`(diagnostic)/flux` · `(diagnostic)/recon` · `MappingTraceTable` (inherently wide — it traces
accounts to statement lines) · `LeadSheetCard` · `ComparisonTable` · `SamplingPanel` ·
`CategoryMovementSection` · and 1 of 3 in `tools/loan-amortization` (a 360-row schedule).
The privacy page matters most: marketing pages take the most mobile traffic. **Fix:** wrap each
in `overflow-x-auto`; add a lint rule, since this will recur.

### D-6 — Route-level loading and error states are sparse — **P3**
62 pages · 20 `loading.tsx` · 9 `error.tsx` · 1 `not-found.tsx`. A root `ErrorBoundary` in
`providers.tsx` catches what segments don't, so failures are contained — but they surface as a
whole-page fallback rather than a scoped one, and 42 routes have no streaming skeleton.
**Fix:** prioritise the 18 tool routes, where a long upload-and-analyse cycle is exactly where a
skeleton earns its place.

### D-7 — The out-of-balance warning hedges about information it already holds — **P2**
`FinancialStatementsPreview.tsx:188` renders: *"Balance Sheet is out of balance by $X. This may
indicate unclassified accounts or mapping gaps."* The payload already carries
`unclassified_count` (13 in the A-3 measurement) and the lead-sheet Z summary **lists the
accounts by name**. A diagnostic product is telling the user something *may* be wrong while
holding the exact answer.

This is the highest-leverage UX fix in this report, because it converts A-3 and A-4 from silent
wrong numbers into a visible, actionable list. **Fix:** name the unmapped accounts inline with a
one-click override into the existing classification validator — the override path already
exists (`group_by_lead_sheet(accounts, overrides=...)`). Gate the statements on resolution, or
at minimum badge them as provisional until the count is zero.

---

# 4. Compliance & privacy

### C-1 — Two subprocessors process customer data and appear on no list — **P1**
`docs/04-compliance/SUBPROCESSOR_LIST.md` carries exactly five: Render, Vercel, Stripe, Sentry,
SendGrid. Two are missing:

- **Cloudflare (R2).** `shared/export_share_storage.py` writes export-share **file bytes** to
  the `paciolus-exports` bucket via boto3, keyed `shares/<share_token_hash>` (Sprint 611).
  That is actual customer financial export content — the most sensitive payload the product
  handles. Cloudflare appears in `BUSINESS_CONTINUITY_DISASTER_RECOVERY.md` only as a DNS
  provider and a hypothetical CDN fallback, **never as a processor**.
- **Google LLC.** `globals.css:2` loads Merriweather, Lato and JetBrains Mono via
  `@import url('https://fonts.googleapis.com/...')`, and `proxy.ts:55,57` allowlists
  `fonts.googleapis.com` in `style-src` and `fonts.gstatic.com` in `font-src`. Every visitor's
  IP address and User-Agent are transmitted to Google on every page load.

`DATA_PROCESSING_ADDENDUM.md:208` commits in writing to *"Maintain an up-to-date list of
subprocessors at SUBPROCESSOR_LIST.md"*, and :210 to a documented vendor risk assessment before
engagement. For a product whose positioning is Zero-Storage privacy, an unlisted processor
holding export bytes is the single finding most likely to surface in a customer security review
or a DPA negotiation. **Fix:** add both rows with transfer mechanism, data categories and
assessment date; or eliminate the Google row entirely per C-2. Then extend the Documentation
Consistency Gate to assert that every external host in the CSP allowlist and every configured
storage bucket maps to a subprocessor entry — this is a mechanisable check.

### C-2 — Self-host the fonts: removes a subprocessor, two CSP entries, and a blocking request — **P2**
A CSS `@import` of a third-party stylesheet is the slowest way to load fonts: it blocks
stylesheet parsing, then needs DNS + TLS + two serial round trips to a second origin before any
text paints. `next/font` self-hosts at build time and eliminates all of it. One change resolves
a compliance finding (C-1), a performance finding, and shrinks the CSP surface by two hosts.
Sprint 703's notes planned exactly this (`internal/typography-preview`, "will integrate the
chosen serif via `next/font` in the root layout"); it was never executed. **Fix:** migrate to
`next/font/google` with local hosting, drop both CSP entries, drop the `@import`.

---

# Recommended sequencing

Ranked by what reaches a customer or an auditor relying on an output.

| # | Finding | Why here | Rough size |
|---|---|---|---|
| 1 | **A-5** depreciation add-back + EBITDA | A wrong number in every exported ratio PDF, from a one-line key bug whose sibling is already fixed | hours |
| 2 | **A-3 / A-4** classifier gaps and misfiles | Wrong net income on ordinary charts of accounts; the product's foundation | 1 sprint |
| 3 | **A-1** Stringer factors | Reports PASS where the method says FAIL; cited to a guide in the workpaper | days |
| 4 | **A-6** negative-equity interpretations | Insolvency shown in green; demo-visible, and ISA 570 territory | hours |
| 5 | **C-1** subprocessor list | A written DPA commitment the artifact does not honour | hours |
| 6 | **D-7** name the unmapped accounts | Converts #2 from silent to visible — ship alongside it | days |
| 7 | **D-2** undefined token + gate extension | 36 live usages on billing/settings; closes the class | hours |
| 8 | **A-2** expansion factors · **A-7** statutory year keying | Over-sized samples; mislabelled statutory block (793b needs a practitioner) | 1 sprint + CEO |
| 9 | **D-1** theme flash · **D-3** contrast + claims | Visible polish on every app page; two overstated claims | days |
| 10 | **A-9** figure registry | Structural fix that prevents A-1/A-2/A-7/A-8 recurring | 1 sprint |
| 11 | **C-2** self-hosted fonts | Resolves compliance + performance + CSP in one change | hours |
| 12 | **T-1…T-5**, **D-4…D-6**, **A-8** | Hygiene, debt burn-down, product gaps | ongoing |

**Two items need the CEO, not engineering:** A-7/A-8 statutory figures need a practitioner
(this is Sprint 793b, and this review raises its priority), and A-8's scope — whether §179 and
bonus depreciation are in the product — is a roadmap call.

**One already-open CEO item is now urgent.** `tasks/ceo-actions.md:65` reads *"Run all 18 audit
tools against a realistic sample trial balance. File bugs for any abnormal output."* A-3, A-4
and A-5 were all found within the first hour of doing exactly that, on a synthetic chart of
accounts of fewer than 70 lines. That checkbox is the highest-yield unchecked item in the repo.

---

## What this review did not cover

Recorded so the next reviewer knows where the dark is, per the DEC's convention.

1. **The other 14 tools' runtime behaviour.** This review drove the trial-balance path
   (classifier → lead sheets → statements → cash flow → ratios) plus sampling and depreciation.
   JE, AP, AR aging, inventory, revenue, payroll, three-way match, SoD, intercompany, W-2/W-3,
   1099, book-to-tax, cash-flow projector and multi-period were **not** exercised. Given the
   hit rate on the paths that were driven, assume findings remain.
2. **Benford's law** thresholds were checked against Nigrini (2012) and match
   (first digit 0.006/0.012/0.015; second 0.008/0.010/0.012; first-two 0.0012/0.0018/0.0022),
   and the three expected distributions are computed rather than tabulated. The *application*
   of those thresholds was not exercised.
3. **Materiality cascade and the ISA 315 Appendix 1 RMM matrix** — not examined.
4. **Auth, CSRF, JWT, the 61 injection tests, rate limiting, the passcode throttle** — not
   examined here; the DEC rated this area "Moderate" with those same items listed as uncovered,
   so it remains the largest untouched surface across both reviews.
5. **Real browser rendering.** Contrast, theming and overflow were computed from source and the
   compiled stylesheet, not observed. D-1's flash in particular should be confirmed visually.
6. **Per-route bundle sizes.** The Next 16 build emits no size table; total client JS is 2.9 MB
   across 110 chunks with a 347 KB largest chunk, but First Load JS per route was not obtained.
7. **Production's schema** — still unanswered, and still one query. The DEC's §6 item 1 is
   unchanged and remains the cheapest high-value check available.

---

*Review conducted 2026-10-22 against `c12a6dcb`. No repository file was modified; all probes
were written to the session scratchpad. `npm run build` was run once (exit 0, emitting
`ƒ (Dynamic)`) to inspect the compiled stylesheet, and `pytest` was run on two test files to
settle T-4.*
