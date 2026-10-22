# Sprints 741–802 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-22.

---

### Sprint 795: The depreciation tool ignores the MACRS system the customer selects
**Status:** COMPLETE
**Result:** The selected MACRS system now reaches the percentage lookup; unsupported combinations are refused by name rather than silently served the 200% DB table. Frontend dropdown narrowed to what the backend can compute, with class options scoped per system. Also fixed the same rounding-composition defect found here (a $123,456.78 asset reported $123,456.77 of total depreciation) and the deferred-tax column, which disagreed with its own cumulative in 17 of 48 configurations. **10 new tests fail on the pre-fix engine.**
**Priority:** **P1** — a customer-facing tax number, wrong by up to 2x, selectable from a shipped
dropdown and carried into a filing.
**Source:** DEC review 2026-10-22, F-001. CONFIRMED by running the engine.
**Agents:** AccountingExpertAuditor (lead), Executor, Guardian.

`depreciation_engine.py:457` `_macrs_percentages` dispatches on **convention and property class
only**. `config.macrs_system` is declared (`:206`), validated for non-null (`:232`), echoed back in
the response `inputs` block (`:308`), and used to decide *whether* a tax schedule exists
(`:511`, `:585`) — and never reaches the percentage lookup.

Measured on a $100,000 5-year asset, half-year convention:

| `macrs_system` | Year-1 tax depreciation |
|---|---|
| `gds_200db` | $20,000.00 |
| `gds_150db` | $20,000.00 |
| `gds_sl`    | $20,000.00 |

The dropdown offering all three ships at `frontend/src/app/tools/depreciation/page.tsx:292-293`.

**Why nothing caught it:** the only test touching `GDS_150`
(`tests/test_depreciation_engine.py:192`) uses property class 15, where the 150DB table is the
*only* table available — it passes for a reason unrelated to `macrs_system`.

- [ ] **Step 0 — practitioner confirmation (blocking for the table values only).** The defect is a
      code fact; the correct GDS-SL and GDS-150DB percentages per property class are current tax
      law and must not be adjudicated from a code review. Natural home: Sprint 781 / 793b.
- [ ] Key `_macrs_percentages` on `(macrs_system, convention, class)`.
- [ ] Reject unsupported combinations with a named error rather than silently substituting a table.
- [ ] Test that the three systems produce **different** output from each other — the cheapest
      assertion that cannot pass vacuously. One test per system is not enough; the current one proves it.
- [ ] Verify: `npm run build`, `pytest`.

**Not affected (verified against IRS Pub 946):** GDS-200DB half-year classes 3/5/7/10, 150DB
classes 15/20, and mid-quarter 5-year Tables A-2…A-5. Those values are correct as published.


---

### Sprint 796: The loan amortization schedule does not foot, and its journal entry does not balance
**Status:** COMPLETE
**Result:** Schedule now amortizes on cent-quantized balances: interest and payment are rounded, principal and ending balance derived. Rows that do not foot went 21.51% -> **0.00%**, balance breaks 24.90% -> **0.00%**, unbalanced period-1 journal entries 10.0% -> **0.00%** over the same 420-configuration sweep. **3 of 8 new integrity tests fail on the pre-fix engine** (4,431 balance breaks, 9 unbalanced JEs).
**Priority:** **P1** — a CPA rejects an amortization schedule whose columns disagree, and an
unbalanced journal entry is unusable rather than untidy.
**Source:** DEC review 2026-10-22, F-002. CONFIRMED by sweep.
**Agents:** AccountingExpertAuditor, Executor, Critic.

`loan_amortization_engine.py:369-371` quantizes each column independently, so the row compares
`_q(a) + _q(b)` against `_q(a+b)`. Measured over 48 standard loans / 6,912 schedule rows:

| Property | Rows violating |
|---|---:|
| `interest + principal == scheduled_payment` | **1,487 (21.51%)** |
| `beginning_balance - principal - extra == ending_balance` | **1,721 (24.90%)** |

$250,000 / 6.99% / 360 monthly, period 2: `interest 1,455.05 + principal 206.52 = 1,661.57`
against a payment column reading `1,661.58`.

`_build_journal_entry_templates` (`:456-473`) is built from those same columns, so across 420 loan
configurations the period-1 template's debits do not equal its credits in **42 (10.0%)**. Example:
$100,000 / 5.00% / 60 monthly → debits $1,887.13, credits $1,887.12.

`test_journal_entry_templates_balance` (`tests/test_loan_amortization_engine.py:211`) does assert
`total_dr == total_cr` — on $50,000 / 5% / 12 monthly, one of the 90% that happen to balance.

- [ ] Close the row arithmetically by construction: quantize `interest` and `payment`, then derive
      `principal = payment - interest`. Same for `ending_balance = beginning - principal - extra`.
- [ ] Re-check the totals still tie (`total_interest` and `total_payments` currently *do* equal
      their columns — do not regress that while fixing the rows).
- [ ] Property test over a generated sweep: every row foots, every JE balances. Not one loan.
- [ ] Confirm the CSV / XLSX / PDF exports inherit the fix (`loan_amortization_excel.py:87-88`).
- [ ] Verify: `pytest`.


---

### Sprint 797: No database build path produces a correct schema
**Status:** COMPLETE
**Result:** `backend/model_registry.py` replaces three hand-maintained import lists (11 / 15 / 15) with one derived set. Migration `c9e4a1b73f20` adds the 4 tables, 6 columns and 3 FKs the chain never had, guarded by an inspector so it is a no-op against production. Dockerfile now runs `upgrade head` on an empty database instead of `stamp head`. **Chain-built DB: 25 -> 29 tables, 0 column drift, 0 FK drift. Fresh Dockerfile boot: 27 -> 29 tables.** Up/down/up proved on both DB shapes. Allow-lists emptied and pinned empty. **Supersedes Sprint 738**, which was never actually blocked on the Neon string.
**Priority:** **P1** — a restore or a new environment silently lacks Stripe webhook idempotency and
the superadmin audit trail. Supersedes and absorbs **Sprint 738**, which is **not** blocked on the
Neon connection string.
**Source:** DEC review 2026-10-22, F-003. CONFIRMED by chain replay + functional probe.
**Agents:** Systems Architect (lead), Guardian, Scout.

Three build paths were replayed. None is correct.

| Path | Tables | Wrong |
|---|---:|---|
| `alembic upgrade head` on an empty DB | 25 / 29 | 4 tables, 6 columns, 3 FKs missing |
| Dockerfile on an empty DB → `stamp head` + `create_all()` | 27 / 29 | `admin_audit_logs`, `dunning_episodes` missing **permanently** |
| Production today | 29 (assumed) | **unverified — see step 1** |

**(a) Chain gaps.** The identifiers `password_reset_tokens`, `processed_webhook_events`,
`tool_activities`, `waitlist_signups`, `completed_at`, `completed_by`, `dso`, `dpo`, `dio`, `ccc`
appear in **zero** of the 45 migration files. All eight functional probes against a chain-built DB
fail. `processed_webhook_events` is the Stripe webhook idempotency table.

**(b) Fresh-environment gap.** `Dockerfile:79-89` runs `alembic stamp head` — not `upgrade` — when
`alembic_version` is absent, so all 45 migrations are marked applied without running and the schema
comes entirely from `create_all()`. `database.init_db()` imports **11** model modules; `env.py` and
the parity test import **15**. Measured: `init_db()` alone → 25 tables; `import main` + `init_db()`
(the real path) → **27**. `admin_audit_logs` (Sprint 590) and `dunning_episodes` (Sprint 591) are
never created, and `stamp head` already marked the migrations that would create them as applied.
The comment at `database.py:128` reads *"Ensure ALL model modules are imported"* and lists 11 of 15.

- [ ] **Step 1 (do first, costs a minute).** Against production:
      `SELECT tablename FROM pg_tables WHERE tablename IN ('admin_audit_logs','dunning_episodes','tool_activities','processed_webhook_events','password_reset_tokens','waitlist_signups');`
      If the first two are absent, this is a live incident, not a rebuild hazard.
- [ ] Replace all three hand-maintained import lists with one derived import (or a single
      `models/__init__.py` the others import) — derive over list, per Sprint 792's ranking.
- [ ] Add the parity assertion none of the three lists can fail: `init_db()`'s resulting table set
      must equal `Base.metadata`.
- [ ] Write the ten missing migrations (4 tables, 6 columns, 3 FKs), idempotently — production
      already holds these objects via `create_all()`, so a bare `CREATE TABLE` breaks the deploy.
- [ ] Empty `PRE_EXISTING_DRIFT_TABLES` / `PRE_EXISTING_DRIFT_COLUMNS` in
      `tests/test_alembic_models_parity.py:118,135` as each lands.
- [ ] Decide separately whether `stamp head` on an empty DB is wanted at all. Once the chain is
      complete, `upgrade head` is the correct behaviour and the branch can go.
- [ ] Verify: fresh `alembic upgrade head` on an empty DB produces all 29 tables and matches
      `Base.metadata`; then the same assertion for the Dockerfile path.

**Reclassification flagged for CEO confirmation:** Sprint 738 is recorded as blocked on the Neon
read-only string (CEO ask D-1). It is not. Production was built by `create_all()` from
`Base.metadata`, so it holds everything the ORM declares; the only genuine unknown is step 1, which
is one query. Sprint 741d already demonstrated that its "needs a database" step did not.


---

### Sprint 798: DuPont is promised in the user guide, reachable by nobody, and verifies 0.15% of the time
**Status:** COMPLETE
**Result:** **Shipped** (CEO decision 2026-10-22). DuPont now rides on `calculate_analytics`, so it appears wherever the ratios it decomposes appear, and renders in a new Key Metrics panel. `verification_matches` went from **0.15% -> 100%** across 2,000 random trial balances: it compared full-precision output against a percentage rounded to 1dp, on a different equity basis. USER_GUIDE and `features/status.json` corrected. **5 new tests fail on the pre-fix engine** (498 of 500 sweep cases).
**Priority:** P2
**Source:** DEC review 2026-10-22, F-007. CONFIRMED.
**Agents:** Critic, AccountingExpertAuditor, Executor.

`calculate_dupont` / `calculate_dupont_decomposition` (`ratio_engine.py:1380-1447`, `:2298`) have
exactly one caller in the repository: a test. No route, no PDF, no frontend reference, zero
occurrences of "dupont" in `scripts/openapi-snapshot.json`.

Meanwhile `docs/07-user-facing/USER_GUIDE.md:168` tells customers a DuPont decomposition "is
available", and `features/status.json:425-437` marks `financial-ratios` `"complete"` with the
verification step *"Verify DuPont decomposition breakdown"*, `last_verified: 2026-03-18` — a step
that cannot have been performed through any surface.

Its `verification_matches` flag (`:1417`) is broken on both ends: it compares a full-precision
`decomposed_roe` at `rel_tol=1e-6` against `round(roe, 1)` of a **percentage** (`:877`), and Sprint
681 made ROE use *average* equity while the equity multiplier still uses *ending* equity. Measured
over 2,000 random realistic trial balances: **3 True / 1,997 False (0.15%)**.
`test_dupont_verification_matches_with_isclose` (`tests/test_ratio_core.py:767`) pins it with
revenue 1M / expenses 800K / assets 1.5M / equity 500K — ROE exactly 40.0% — and its docstring
asserts "legitimate decompositions always verify."

- [ ] **Decision (CEO):** ship DuPont, or delete it?
- [ ] **Required either way, and not blocked by the decision:** correct `USER_GUIDE.md:168` and
      `features/status.json`. A user-guide promise with no product behind it surfaces during a demo.
- [ ] *If ship:* wire a route + UI; compare against the unrounded ROE; make the equity basis
      consistent between numerator and multiplier, or state the basis in the output.
- [ ] *If delete:* remove the engine code and the test.


---

### Sprint 799: The monetary-precision gate inspects 0% of its target
**Status:** COMPLETE
**Result:** `monetary_float.py` now matches `mapped_column` as well as `Column`, with a **coverage self-check whose oracle is the `Mapped[...]` annotation rather than the parser's own factory list** — an oracle built from `COLUMN_FACTORIES` would have reported full coverage of nothing. Narrowing the parser back now fails with `0 of 53 / 0 of 16 / 0 of 18`, summing to the measured 87. Unit fixtures rewritten in the syntax the repo uses; the 1.x form keeps its own class. Scan-list and protected-class rot are now violations too.
**Priority:** **P1** (control) — no live defect behind it; the invariant is currently satisfied by
discipline and nothing would say so if it stopped being.
**Source:** DEC review 2026-10-22, F-004. CONFIRMED by injection.
**Agents:** Guardian (lead), Verification Marshal, Critic.

The Phase XLV invariant ("Monetary precision — Float to Numeric", `CLAUDE.md` completed phases) is
enforced by rule 1 of the Accounting Policy Gate. `guards/checkers/monetary_float.py:47` recognises
exactly one syntax: `func.id == "Column"`. Every model is SQLAlchemy 2.0 style.

**Measured across the three files the rule scans: 0 `Column(...)`, 169 `mapped_column(...)`. Within
its four protected classes: 0 and 87.** Regression-proved — a `Float` monetary column injected into
`DiagnosticSummary` (a named protected class, in a named file) produced
`Accounting Policy Guard: ALL 5 RULES PASSED`, exit 0.

The unit tests pass because `tests/test_accounting_policy_guard.py` builds synthetic sources with
**10** uses of `Column(` and **0** of `mapped_column(`. Tests and target are disjoint sets, both green.

All five rules were injection-tested: 3 fire correctly, `no_hard_delete` fires for the 1.x form only
(see Sprint 802), `no_float_monetary` does not fire at all.

- [ ] Match `mapped_column` as well as `Column`; resolve the type from the first positional arg or
      the `Mapped[...]` annotation.
- [ ] Add a **coverage self-check** — count column declarations the naive way, require the parser to
      account for all of them, assert nothing about contents. This is the Sprint 786c fix shape and
      it is the part that generalises.
- [ ] Rewrite the unit fixtures in the syntax the repo uses; keep one `Column(` case for legacy.
- [ ] Regression-prove by re-running the injection above and confirming it now fails, naming
      `models.py` and the line.
- [ ] Verify: `python -m guards.accounting_policy_guard`, `pytest tests/test_accounting_policy_guard.py`.

**Measured and deliberately out of scope:** all 17 `Float` columns across the 15 model modules were
enumerated. 15 are in-scope and allow-listed by name; the 2 outside the rule's file list
(`AnalyticalExpectation.precision_threshold_percent`, `ToolRun.composite_score`) are a percentage
and a score. Money is `Numeric(19,2)` everywhere. Do **not** widen the scope list in this sprint —
the measurement says it would find nothing.


---

### Sprint 800: Controls that cannot fail, and gates that cannot block
**Status:** COMPLETE
**Result:** Four presence-only test classes replaced with behavioural ones; **all four regression-proved against injected violations.** Export gating went from '>=1 route per module, 4 of 6 modules' to all 84 routes, with 4 reasoned exemptions that must still exist. The AST guard banning route-local tier comparisons that Sprint 789 called for is built. `ci.yml` header replaced with a gate manifest + `test_ci_gate_manifest.py`. **Two of my own first drafts were wrong and the tests caught them** — a guessed '>=20' floor (reality 18) and an allowlist claiming `execute_file_tool` gates entitlement, which it does not.
**Priority:** P2
**Source:** DEC review 2026-10-22, F-005 + F-006. Both CONFIRMED (one by reading, one by the
GitHub branch-protection API).
**Agents:** Verification Marshal (lead), Guardian.

**(a) Four entitlement test classes assert presence, not enforcement**
(`tests/test_post_audit_2026_04_20_batch2.py:265,286,321,338`):

| Class | Claims | Asserts |
|---|---|---|
| `TestEntitlementHelpersExist` | helpers are wired | `callable(...)` x3 |
| `TestExportRoutesAreGated` | export modules gated | at least 1 route per module, 4 of 6 modules |
| `TestFormatAccessWiredOnUploadRoutes` | format gate invoked on upload entry points | `callable(check_format_access("qbo"))` |
| `TestToolRoutesCheckUploadLimit` | "the 11 testing-tool routes enforce upload limits" | `hasattr(testing_route, "enforce_tool_access")` |

The last is named for a property **Sprint 790 already records as false**. `hasattr` here is
`shutil.which` wearing a different hat — the Sprint 786b nightly lesson at the entitlement boundary.
Behaviour is currently fine (measured: 79/84 export routes gated, the other 5 gate in-body at
`routes/export_sharing.py:318`; 0 route-local tier comparisons remain).

**(b) Branch protection and `ci.yml`'s own header disagree.** `ci.yml:4-7` lists 11 required checks;
the live `required_status_checks.contexts` has 12, and they are not the same set.
`OpenAPI Schema Drift Check` is **claimed required and is not**. `Backend Tests (PostgreSQL 15)` is
required and not claimed. Not required and not claimed: **Accounting Policy Gate**, **Documentation
Consistency Gate**, **Report Standards Gate**, **Backend Slow Tests**. `CLAUDE.md`'s authority
hierarchy calls `ci.yml` "mechanically enforced and final"; for those four it is advisory. The
Husky `pre-commit` hook does not run them either.

- [ ] Replace each of the four test classes with the behavioural assertion its name promises —
      POST as each tier, assert the status code. `tests/test_sod_routes.py` is the model.
- [ ] Build the **AST guard banning route-local tier comparisons** that Sprint 789's lesson called
      for and that was never written. It is the half that stops the next instance.
- [ ] Decide one list for required checks and derive the other; add the four gates to branch
      protection, or demote them in the header with the reason stated.
- [ ] Add a test asserting `ci.yml`'s header block and the branch-protection API agree. This is a
      claim with an expiry date, which is exactly what Sprint 786b says to guard.
- [ ] Verify: re-read the protection API; confirm a deliberately-failing gate blocks a draft PR.


---

### Sprint 801: Stale claims, ranked by who reads them under pressure
**Status:** COMPLETE
**Result:** `metadata_persistence_policy.md` rewritten: the table inventory removed rather than corrected (8 of 29 and unmaintainable), the three deliberate persistence exceptions stated plainly, and a decision rule put in their place. **`tests/test_account_extractors_zero_storage.py` enforces the `flagged_accounts` promise for the first time** — 23 tests, regression-proved. Depreciation docstring cut back to the dispatch table. Retired `team` tier removed from the live compliance doc (archive left historical).
**Priority:** P2 / P3
**Source:** DEC review 2026-10-22, F-008 + F-009 + F-014. All CONFIRMED.
**Agents:** Scout, Guardian, AccountingExpertAuditor.

- [ ] **F-008 (P2) — `backend/shared/metadata_persistence_policy.md`.** The *internal* policy a
      developer opens when deciding what may persist lists **8** tables under a heading that reads
      exhaustive (schema has **29**) and states *"There is no foreign key or reference to any
      specific account, amount, or transaction"* — contradicted by `ToolRun.flagged_accounts` and
      `UncorrectedMisstatement.accounts_affected_json` + `fs_impact_*`, both of which the
      *customer-facing* `ZERO_STORAGE_ARCHITECTURE.md` correctly discloses. The externally-audited
      document is right and the internal engineering guidance is wrong in the permissive direction.
      Rewrite it to derive its table list, or delete it and point at the compliance doc.
- [ ] **F-008b — the unenforced half.** `ZERO_STORAGE_ARCHITECTURE.md:122` promises
      `flagged_accounts` holds "identifiers only, no balances". Measured: all 7 extractors in
      `shared/account_extractors.py` append an account-name field and nothing else — sound today,
      with **no test**. Add one asserting no persisted `flagged_accounts` string carries an amount.
- [ ] **F-009 (P3) — `depreciation_engine.py:13-20`.** The docstring advertises mid-month,
      27.5-year residential and 39-year nonresidential real property, and "Table A-6". No A-6 table
      exists and `validate()` at `:206` rejects every class outside `(3,5,7,10,15,20)` — the field
      comment on the same line lists `27.5, 39`. `_macrs_real_property_percentages` (`:471`) is
      therefore reachable only via `mid_month` + a personal-property class, where it computes
      mid-month SL over the **book** life: a $100,000 5-year asset returns
      `[19166.67, 20000, 20000, 20000, 20000, 833.33]` — plausible-looking and meaningless. Reject
      `mid_month` at the schema until real-property tables exist; delete the dead
      `if cls not in (15, 20): pass` block; cut the docstring to what ships.
- [ ] **F-014 (Info) — `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md:128,129`.** Two examples
      read `"Tier: team"`; Team is a retired tier. Customer-facing.
- [ ] Verify: `python -m guards.doc_consistency_guard`, `pytest`.


---

### Sprint 802: Gate hygiene — scope statements, a latent blind spot, and two unwired scripts
**Status:** COMPLETE
**Result:** `check_route_wiring.py` wired via a test inside `backend-tests` (a *required* check) rather than a new advisory job — and its three-outcome exit 2 is now pinned. **`scripts/overnight/tests/` ran nowhere and is now in CI**: the tests protecting the thing that watches the build were themselves unwatched. `qa_warden` catches `TimeoutExpired` and names both budgets that must move together. Parity-test scope stated honestly. **CORRECTION: `weekly_security_digest.py` is not unwired** — it is a documented manual tool referenced by SECURITY_POLICY.md and the review template; the review's F-012 was half wrong.
**Priority:** P3
**Source:** DEC review 2026-10-22, F-010 + F-011 + F-012 + F-013. All CONFIRMED.
**Agents:** Verification Marshal, Observability.

- [ ] **F-010 — `tests/test_alembic_models_parity.py`** is titled "Alembic head schema must match
      `Base.metadata`" and compares table names and column names only. Measured unguarded
      dimensions: **nullability 50**, **foreign keys 3**
      (`analytical_expectations.archived_by`, `engagements.completed_by`,
      `uncorrected_misstatements.archived_by`); PK 0, unique 0. **Fix the docstring** to state the
      covered dimensions — that alone closes the honesty gap. Optionally extend to FKs, the one
      dimension with integrity consequence. **Do not** fix the 50 nullability drifts: every one is
      a `Mapped[...]` NOT NULL against a nullable migration column with a Python-side default, so
      none can emit NULL, and a 50-row wall is how a gate gets switched off.
- [ ] **F-011 — `guards/checkers/hard_delete.py:15-16`** matches `db.delete(` and
      `.query(M)...delete(` but not `db.execute(delete(M))`. Regression-proved both ways.
      **Measured: 0 such call sites exist today** — latent, not live. Add the 2.0 pattern; do not
      rewrite to AST, the measurement does not justify it.
- [ ] **F-012 — two scripts are wired into nothing.** `scripts/check_route_wiring.py` passes today
      (60 modules, 50 direct + 10 aggregated) and has the correct three-outcome shape — exit 2 for
      "cannot locate `backend/routes/`", the very pattern Sprint 794's lesson holds up as the one to
      copy — and nothing calls it. `scripts/weekly_security_digest.py` has no caller anywhere. Wire
      the first into the gate block (it costs seconds) or delete it; decide what the second is for.
- [ ] **F-013 (Info) — nightly timeout headroom.** `qa_warden` inner pytest 1200 s vs 690.7 s
      observed (1.74x); `coverage_sentinel` 1500 s vs ~900-1035 s (~1.45x); orchestrator 1700 s vs
      757.2 s. At 9,126 tests / ~76 ms per test the first cap arrives near ~15,800 tests and the
      second near ~14,000 — the nearer clock. Nesting is correct. Add
      `except subprocess.TimeoutExpired` to `qa_warden.py:47,78` so the brief can say *why*, not
      only *that*. Also note: the nightly runs against whatever branch is checked out.
- [ ] Verify: `pytest`, and run each wired gate once.


---

### Sprint 794: A registry outage makes the CVE gate report "vulnerable"
**Status:** COMPLETE — **794a** (the three npm call sites) and **794b** (the three pip-audit
call sites). Step 3, the gating-policy question, remains open and is a CEO call.
**Priority:** P3 — no security exposure, but it is a blocking gate that cannot distinguish two very
different answers, and it produces a scary-sounding failure for an upstream hiccup.
**Source:** observed live on PR #189, 2026-10-22.

`Node CVE & License Audit` failed with:

```
npm warn audit 503 Service Unavailable - POST https://registry.npmjs.org/-/npm/v1/security/audits/quick
npm error audit endpoint returned an error
##[error]Process completed with exit code 1.
```

No vulnerability. npm's audit endpoint was down for seven minutes. The job name says "CVE &
License Audit" and the red X says the same thing it says for a genuine CRITICAL, so the signal
a reader gets is "this PR has a high-severity vulnerability" when the truth is "we could not
check."

**Same shape as Sprint 778a's false-green, inverted.** There the job could not report a failure
it had detected; here it reports a failure it has not detected. Both come from a check with two
outcomes where the reality has three: pass, fail, and **unverified**.

**Two blocking instances**, plus one advisory:

| File | Step | Gating |
|------|------|--------|
| `ci.yml:656` | `npm audit --omit=dev --audit-level=high` | **blocking** |
| `dependency-compliance.yml:56` | same | **blocking** |
| `ci.yml:699` | `npm audit --omit=dev` | advisory |

**Scope:**
1. **Retry first.** A 503 is usually seconds long; two or three attempts with backoff removes most
   of the problem and needs no policy decision. This alone is probably 80% of the value.
2. Distinguish the outcomes. `npm audit --json` returns a parseable report on success and an
   error object on failure; branch on which arrived rather than on the exit code alone.
3. **Decide the gating policy for "unverified", and write the reason down.** This is the part
   that is genuinely a judgement call rather than a bug fix: should an npm outage block a merge?
   Failing closed is the safe default for a security gate and matches the 778a precedent — but
   778a gates a monthly report, and this gates every PR, so an hour-long npm incident would stop
   all work. A bounded compromise: fail closed, but say *"registry unavailable — not a
   vulnerability finding"* in the error so the reader knows to re-run rather than hunt a CVE.
4. Check whether the Python side has the same hole — `pip-audit` also calls out to an advisory
   service.

**Not urgent:** the immediate incident was cleared by re-running the job, and the underlying
posture is unaffected either way — the audit was green on the previous run and on the re-run.


---

### Sprint 792: Audit every gate for the scope gap that produced seven findings
**Status:** COMPLETE.
**Priority:** P2 — preventive. Fixing instance #8 is worth less than enumerating the class.
**Source:** 2026-10-21. Seven separate findings that day were the same defect.

**The class.** A consistency gate scoped by a *file list* silently stops covering what it is named
after, and reports success. Seven instances in one day:

| Gate | What it read | What it missed |
|------|-------------|----------------|
| `doc_consistency_guard` `CODE_SURFACE_CHECKS` | `(marketing)/demo/layout.tsx` | `demo/page.tsx` beside it — metadata correct at 18, visible body saying *twelve* |
| `doc_consistency_guard` `TOOL_COUNT_DOCS` | `USER_GUIDE.md`, aggregate claims only | six of seven per-tool test counts in the same file |
| `test_citation_consistency` `SCANNED_GLOBS` | `app/(marketing)/**` | `app/tools/**` — AU-C 265 unregistered since Sprint 689b |
| `test_catalog_consistency` | registry↔ledger, registry↔standards | `features/status.json`, missing all six promoted tools |
| `test_catalog_consistency` + friends | descriptions of the catalog | what the API actually allows — SoD 403'd two paying tiers |
| `scripts/archive_sprints.sh` | counted 13, extracted 10 | nothing compared the two numbers; three records destroyed |
| Sprint 787b's own new guard | imports of a module | the function actually called — went vacuously green |

**So instead of waiting for the eighth, every gate in the repo was inspected.** Result: the two
with real gaps were already fixed (789b, 784c/784b). The rest are genuinely comprehensive, and the
finding is worth recording so the next reader does not re-derive it:

| Gate | Enumeration | Verdict |
|------|-------------|---------|
| `scripts/lint_design_tokens.py` | `frontend/src` full `rglob` + suffix filter | **comprehensive** — no path list to rot |
| `scripts/lint_route_layer_purity.py` | `routes/*.py` | comprehensive; no `APIRouter` lives outside `routes/` (checked) |
| `scripts/check_route_wiring.py` | `routes/*.py` + known aggregators | comprehensive; handles the aggregator indirection |
| `scripts/check_openapi_drift.py` | the live app's own schema | **structurally immune** — derived from the app, not a path list |
| `scripts/lint_engine_base_adoption.py` | `BACKEND_ROOT.glob("*_engine.py")` | **latent gap — closed here** |
| `scripts/lint_domain_relocation.py` | same | same gap, same fix |

**The one real find, closed preemptively.** Both engine linters enumerate `*_engine.py` at the
backend root. ADR-018 moved the implementations to `services/audit/<tool>/analysis.py`, and the
linters still reach them only because every relocated engine left a root shim behind — which
PR #126 taught the adoption lint to follow. **Nothing asserted the shims exist.** An engine created
directly at `services/audit/<tool>/analysis.py` with no shim would be scanned by neither linter,
and both would report success on an empty scan.

All ten relocated engines currently have their shim, so this is a trap rather than a defect.
`test_every_relocated_engine_has_a_root_shim` now fails if one is ever missing, names the tool, and
states both remedies (add the shim, or teach both linters the relocated path). It also asserts the
scan found work at all — a glob that matches nothing covers nothing, which is the same failure
wearing different clothes.

Regression-proved: moving `flux_engine.py` aside fails with
`report success while scanning nothing: ['flux']`; restoring passes.

> **PR #185 review — the guard had the defect it was written to prevent.** The first draft
> enumerated `services/audit/*/analysis.py`, which excluded
> `services/audit/flux/recon.py` — the **ADR-018 pilot relocation**, and the one module that
> predates the `analysis.py` convention. Deleting its shim `recon_engine.py` left the test
> green while `lint_domain_relocation.py` lost the ability to enumerate that engine: precisely
> the regression the test exists to catch, missed by the test's own filename filter.
>
> That is this sprint's thesis reproduced inside the sprint's own deliverable — a scan whose
> scope silently excludes the thing it was written for. Enumeration is now by **directory**:
> every non-`__init__` module under a per-tool subdirectory, with the shim name taken from the
> module stem (`recon.py` → `recon_engine.py`) except for the conventional `analysis.py`, which
> takes its directory's (`ap_testing/analysis.py` → `ap_testing_engine.py`). The rule resolves
> correctly for all 11 modules. Top-level `services/audit/*.py` — `contracts.py`,
> `file_tool_scaffold.py`, `flux_service.py` — are shared infrastructure, not per-tool engines,
> and stay excluded.
>
> A second test pins the pilot **by name**, so a future narrowing of the glob cannot drop it
> silently again. Re-proved: removing `recon_engine.py` now fails with
> `scanning nothing: ['services/audit/flux/recon.py (expected recon_engine.py)']`.

**The operating rule, written down where the next reader will find it:** when inheriting a
consistency gate, do not read its file list as its scope — **the scope is the patterns**, and the
file list is a separate thing that can be wrong on its own. A gate whose coverage you cannot state
in one sentence is a gate you will over-trust. Prefer a glob plus a test that the glob matches
something; prefer deriving the target set from the app (as `check_openapi_drift.py` does) over
listing it.

**Verification:** 17 passed in `test_engine_base_lint.py`; `ruff check .` clean. No production code
changed.

**Commit SHA:** `392d471e` (PR #185), plus the review fix `acdcb900` — the guard itself had the defect it was written to prevent.


---

### Sprint 741d: Freeze the enum label drift so it cannot grow
**Status:** COMPLETE.
**Priority:** P2 — preventive. It fixes nothing; it stops the problem spreading while
[Sprint 741c](#sprint-741c-enum-labels-disagree-between-the-alembic-chain-and-the-orm) waits on
CEO ask D-1.
**Source:** Sprint 741c step 4, pulled forward on realising it needs no database.

Step 4 of 741c was filed behind the Neon read. It does not belong there: comparing the migration
chain's enum labels against the ORM's is a comparison of **two things already in this repository**.
No production connection is involved. So it was done first.

#### What it found: 19 drifting types, not 3

The hand-written table in 741c lists three types across five rows. The mechanical comparison finds
**nineteen**, out of 26 enum types that exist in both places.

> **Corrected after the PR #191 review** — the first measurement said twenty, and `subscription_tier`
> was a phantom. See "A fourth parser defect, found in review" below.

**Seventeen are case-only** — the chain spells labels lowercase, the ORM binds member NAMES:
`adminactiontype`, `billingeventtype`, `billinginterval`, `dunningresolution`, `dunningstate`,
`entitytype`, `expectationresultstatus`, `expectationtargettype`, `invitestatus`,
`misstatementclassification`, `misstatementdisposition`, `misstatementsourcetype`, `orgrole`,
`reportingframework`, `subscriptionstatus`, `teamactiontype`, `usertier`.

"Case-only" sounds cosmetic and is not: `ACTIVE` is simply not a label of a type whose labels are
`active`, and PostgreSQL rejects the write with 22P02. That is the exact error Sprint 741a chased.

**Two are membership differences** — labels genuinely absent rather than misspelled, so no
`values_callable` decision could resolve them:

| Type | Column | The gap |
|------|--------|---------|
| `engagementstatus` | `engagements.status` | the ORM binds **`COMPLETED`** and **no migration ever adds it** |
| `toolname` | `tool_runs.tool_name` | chain carries lowercase `flux_analysis`; the ORM binds `FLUX_ANALYSIS` |

**`engagementstatus` is a new finding and the most interesting one.** Nothing in 741c or its
source reviews mentions it. The engagement completion gate is a shipped feature, so on any
database built from the documented chain, completing an engagement fails. Production is fine
because production was built by `create_all()` — which is precisely what makes this a
**restore-drill blocker** rather than a live incident, and why it belongs with Sprint 778.

`toolname` confirms 741c's live-defect row mechanically.

**One genuinely useful side-finding for 741c's step 2.** `subscription_tier` and `usertier` hold the
same four tiers one table apart, and the ORM binds them **differently** — `subscription_tier`
lowercase, `usertier` as NAMES. So "pick the canonical direction" is not purely a migration edit;
the models disagree with each other first.

#### Why no test could have caught this

SQLite has no enum types. The column is a plain VARCHAR, every label is accepted, and ~9,000
passing tests say precisely nothing about whether the chain and the ORM agree. Same shape as the
missing `ALTER TYPE` in Sprint 787 and the 22P02 in 741a: **when a constraint exists only in the
production dialect, the dev dialect cannot see the defect.** A static comparison is the only
thing that can, short of a PostgreSQL connection.

#### What landed

`backend/guards/enum_label_drift.py` assembles each type's label set from the three constructs
this chain actually uses — inline literals, `sa.Enum(*_CONSTANT, name=...)`, and
`for v in _CONSTANT: op.execute(f"ALTER TYPE t ADD VALUE '{v}'")` — and compares them against
`Base.metadata`. The 20 known-bad types are a `KNOWN_DRIFT` baseline. Anything drifting that is
not on the list fails; anything on the list that stops drifting **also** fails, so 741c's fixes
must shrink it. A baseline that is never tightened is just an allowlist.

#### The guard was wrong three times before it was right

Worth recording, because every one was the failure this session keeps producing — a scan that
silently covers less than it claims and reports success anyway.

1. **It read 5 of 26 ORM types.** `import models` registers only the models in `models.py`; the
   rest live in sibling `*_model.py` modules and are absent from `Base.metadata` until imported.
   Caught only because 5-vs-21 looked implausible.
2. **It could not read `NEW_TOOL_NAMES`.** Declared `NEW_TOOL_NAMES: tuple[str, ...] = (...)` —
   an `AnnAssign`, not an `Assign`. Handling only `Assign` made Sprint 689's six tool labels
   invisible. One type annotation was the difference between reading that migration and not.
3. **It invented a label called `{value}`.** The literal `ALTER TYPE` regex runs over raw source,
   so it matched an f-string's own placeholder text — manufacturing drift on two types while
   hiding their real labels behind it.

Each was found by the module reporting what it could *not* resolve instead of skipping it, which
is why `unresolved` fails the run loudly. **If the first draft had shipped it would have passed
CI**, printed a confident verdict, and compared a fifth of the schema.

#### A fourth parser defect, found in review

The PR #191 review caught what the three self-inflicted bugs below did not: the first version
**unioned every label it saw anywhere in the file**, and that is the wrong model of what a
migration chain does.

`e3f4a5b6c7d8_pricing_v3_enum_restructure` rebuilds both tier enums:

```sql
ALTER TYPE usertier RENAME TO usertier_old
CREATE TYPE usertier AS ENUM ('free', 'solo', 'professional', 'enterprise')
DROP TYPE usertier_old
```

`starter`, `team` and `organization` are **retired**. Unioning keeps them forever — so
`subscription_tier` was reported as drifting when it actually agrees, and any drift a *future*
rebuild introduced would have been invisible. There was no handler for `CREATE TYPE ... AS ENUM`
at all.

**A fifth defect surfaced while fixing it:** the scan read raw file text, so it also replayed
`downgrade()` — and that same migration's downgrade recreates both types with the *old* labels.
The guard was reading a schema nobody has.

Both are fixed by **replaying the chain in revision order** — topological sort on
`revision`/`down_revision`, then `upgrade()` bodies only, operations sorted by line number because
the rebuild is a three-step RENAME/CREATE/DROP dance and `ast.walk` is breadth-first. `CREATE TYPE`
replaces, `ADD VALUE` adds, `RENAME` moves, `DROP` removes, and `sa.Enum(name=...)` inside
`create_table` defines only if absent so it cannot clobber an earlier rebuild.

**Why the coverage test did not catch this, which is the real lesson.** There *was* a coverage
self-check, and it passed: it counted `Enum(..., name=...)` AST calls and confirmed the parser saw
every one. But `CREATE TYPE` is raw SQL inside `op.execute()`, so the check proved nothing about
it. **Coverage of one construct family reads exactly like coverage of the subject.** The new
`test_every_enum_sql_statement_in_every_upgrade_is_accounted_for` counts enum-affecting SQL
statements in each `upgrade()` body and requires a parsed operation for each.

Regression-proved: deleting the `CREATE TYPE` handler fails six tests, including that one.

#### Tests — `backend/tests/test_enum_label_drift.py`, 21

The verdict matches the baseline; the baseline must be tightened when drift is fixed; the parser
resolved everything it found; **every named enum in every migration is accounted for, with no
exemptions** (an earlier draft carved out downgrade-only `Enum(name=...).drop()` calls — measuring
showed the carve-out was dead code, and a dead escape hatch in a coverage check is exactly what
hides the first real miss); no phantom placeholder labels; the AnnAssign constant resolves; the
ORM scan sees models outside `models.py`. Plus both failure directions regression-proved by
monkeypatching the baseline.

**Not given its own CI job.** It runs inside `backend-tests`, which already installs the
dependencies it needs; the `doc-consistency` job runs without them, so a separate job would mean
a redundant full install for no extra signal.

**Does not fix anything.** 741c steps 1-3 still need the Neon read, and the canonical direction is
still almost certainly *names* — do **not** "fix" this by adding `values_callable`, which would
flip every binding to lowercase and break the live database.

**Commit SHA:** `9b5eddd8` (PR #191), plus the review fix `3e129853` — the guard unioned labels a
rebuild had retired.


---

### Sprint 786c: Refresh the six GitHub Actions SHA pins
**Status:** COMPLETE.
**Priority:** P3 — CI-only. No production surface, but action pins are the one dependency class in this repo that **cannot self-heal**, so they rot silently.
**Source:** Sprint 785 Dependabot triage. Replaces the four stale Dependabot action PRs (#77, #78, #90, #156), all closed as superseded.

`ci.yml` and the other workflows pin every action by commit SHA rather than tag — correct practice, since a tag is mutable and a compromised action runs with repository credentials. The cost is that nothing updates them automatically, and Dependabot's own PRs for them sat unmerged for six months until their targets went stale too.

**Current pins and current releases (measured 2026-10-21):**

| Action | Pinned | = tag | Latest |
|--------|--------|-------|--------|
| `actions/checkout` | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` | v6.0.2 | **v7.0.1** |
| `actions/github-script` | `ed597411d8f924073f98dfc5c65a23a2325f34cd` | v8.0.0 | **v9.0.0** |
| `actions/setup-node` | `53b83947a5a98c8d113130e565377fae1a50d02f` | v6.3.0 | **v7.1.0** |
| `actions/setup-python` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` | v6.2.0 | **v7.0.0** |
| `actions/upload-artifact` | `bbbca2ddaa5d8feaa63e36b76fdaad77386f024f` | v7.0.0 | **v7.0.2** |
| `actions/download-artifact` | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` | v8.0.1 | **v8.0.2** |

Four of the six are **major** bumps. `upload-artifact` and `download-artifact` are patch-level and safe to batch.

**Approach:**
1. Batch the two patch bumps (`upload-artifact` 7.0.0 → 7.0.2, `download-artifact` 8.0.1 → 8.0.2) in one commit.
2. One major per commit, each resolved to its release SHA (not the tag) with the tag recorded in a trailing comment so the next reader can tell what the SHA is without an API call. `checkout` v7 first (every job uses it, so a break is immediate and obvious), then `setup-python` v7, `setup-node` v7, `github-script` v9 last — it is used in the failure-issue step of `uptime-check.yml`, which is the hardest to exercise on a PR.
3. Read each major's release notes for runner-version and Node-runtime requirements before bumping; the v6 → v7 wave across the `actions/*` org is largely a Node runtime move.

**Verification:** every workflow that references the bumped action runs green on the PR. `github-script` cannot be proven by a normal PR run (its only use is in a failure path), so dispatch `uptime-check.yml` manually on the branch and confirm the failure-issue step still *skips* correctly rather than erroring.

**Out of scope:** switching from SHA pins to tags. The pins are deliberate and stay.

#### What landed — 64 pins across 5 workflow files

| Action | Was | Now | Occurrences |
|--------|-----|-----|-------------|
| `actions/checkout` | v6.0.2 | **v7.0.1** | 27 |
| `actions/setup-python` | v6.2.0 | **v7.0.0** | 17 |
| `actions/upload-artifact` | v7.0.0 | **v7.0.2** | 8 |
| `actions/setup-node` | v6.3.0 | **v7.1.0** | 6 |
| `actions/github-script` | v8.0.0 | **v9.0.0** | 4 |
| `actions/download-artifact` | v8.0.1 | **v8.0.2** | 2 |

Done in one commit rather than the filed one-major-per-commit, because a single CI run exercises
every job at once and gives the same signal — the sprint's "verification window" per major is a
sequencing idea that buys nothing when one run covers all 27 jobs. If something breaks, the failing
job names the action.

**Every breaking change was checked against our actual usage before bumping, not assumed away:**

- **github-script v9** is the only one with real breaking changes: `require('@actions/github')`
  stops working, and `getOctokit` becomes an injected parameter so a script declaring
  `const getOctokit` now raises `SyntaxError`. Our four usages touch `github.rest.issues.create`,
  `github.rest.issues.listForRepo`, `context.repo` and `require('fs')` — a Node builtin. None of
  the breaking patterns appear.
- **checkout v7** blocks checking out fork PRs under `pull_request_target` and `workflow_run`. We
  use neither trigger anywhere.
- **setup-python v7** removes the `pip-install` input. We never passed it.
- **setup-node v7** removes the dummy `NODE_AUTH_TOKEN` export. We do not reference it.
- The remaining v7 majors are ESM migrations plus dependency upgrades.

**Each SHA was verified against GitHub's tag API** rather than trusted from the release lookup —
`repos/<action>/tags` confirms all six resolve to the claimed version, and each also carries the
floating major tag, which is the expected shape for a release commit.

#### The guard — `tests/test_workflow_action_pins.py`, 5 tests

SHA pinning is the highest-leverage supply-chain control in the repo and **nothing was checking
it.** A tag is mutable: whoever controls an action's repository can repoint `v7` at new code, which
then runs here with this repository's credentials and `GITHUB_TOKEN`.

1. Every external `uses:` is pinned to a 40-character SHA — no tags, no branches.
2. Every pin carries a `# pin: vX.Y.Z` comment. **This is the one that would have prevented the
   sprint.** A bare SHA is unreadable; you cannot tell a six-month-old pin from a current one
   without an API call, which is exactly how all six drifted a full major behind unnoticed.
3. `checkout` and `setup-python` — 27 and 17 occurrences — each resolve to a single SHA, so a
   partial bump cannot leave some jobs behind. The difference would be invisible at a glance,
   being a hex string.
4. Plus the now-standard assertion that the scan found work at all.

Deliberately **not** checked: whether the pins are *current*. That needs a network call and would
fail CI for reasons outside the commit. Currency is Dependabot's job; immutability and readability
are the test's.

Regression-proved in all three directions: replacing one pin with `@v7` fails three tests and names
`uptime-check.yml:73`; dropping a `# pin:` comment fails one; and pointing one `checkout` back at
the old SHA fails with "pinned to 2 different SHAs".

**Verification:** all five workflow files parse, 27 jobs resolve, every `uses:` in the repo is one
of the six and all are SHA-pinned. 5 tests pass; `ruff` clean. Re-verified after rebasing onto
#187, which rewrote `dr-test-monthly.yml` — no stale pin survived the merge.

**What a green CI run does *not* verify, and what does.** `checkout`, `setup-python`,
`setup-node`, `upload-artifact` and `download-artifact` run on every job, so the PR's own CI is a
genuine test of those five. **`github-script` is different: all four usages are conditional**, and
three of them only fire on failure —

| Workflow | Condition |
|----------|-----------|
| `backup-integrity-check.yml:78` | `steps.check.outcome == 'failure'` |
| `dr-test-monthly.yml:221` | `steps.final.outputs.overall != 'PASS'` |
| `uptime-check.yml:223` | `steps.final.outputs.overall == 'FAIL'` |
| `uptime-check.yml:257` | `steps.final.outputs.overall == 'PASS'` ← **runs on success** |

So the v8 → v9 major — the only bump with real breaking changes — is exercised by none of the
PR's checks. The static analysis stands (none of our scripts uses `require('@actions/github')` or
declares `getOctokit`), but static analysis is not execution.

The last row is the answer: `uptime-check.yml` is scheduled **every 15 minutes**, and its
recovery step runs `github-script` on the PASS path. So v9 gets genuinely exercised within a
quarter-hour of this merging, against real GitHub API calls. **Confirm that run is green before
treating this sprint as verified** — today's lesson about un-suppressing untested paths applies
directly, and a conditional step is a path nobody has run.

**Not done deliberately:** manually dispatching `dr-test-monthly` to exercise the failure path.
It would work — the verdict is UNVERIFIED after Sprint 778a, so the issue-creation step fires —
but it files a real `dr-failure` issue in the repository, which is an outward-facing side effect
and the CEO's call rather than a verification step to take unprompted.

**Commit SHA:** `9992c6c8` (PR #188), plus the review fix `423ea080` — the pin guard was inspecting 23% of the file.


---

