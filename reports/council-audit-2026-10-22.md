# Paciolus Digital Excellence Council Report
Date: 2026-10-22
Commit/Branch: `103ce557` / `sprint-786b-frontend-devtype-majors`
Trigger: Comprehensive Council Review — full-spectrum audit commissioned after five months of dormancy and two days of rapid change, with CI green throughout. Review-only pass; no production code changed.

Scope note: this review was run single-threaded rather than via `/agents run` (the session harness forbids spawning subagents unless asked). The nine council roles were applied as review lenses by one reviewer. Section 5 states which lenses got real coverage and which did not.

---

> ## REMEDIATION STATUS — all 14 findings addressed, same day
>
> This report was written as a review-only pass; the CEO then directed that every finding
> be fixed. **Sprints 795–802 landed on branch `dec-review-2026-10-22-remediation`**, with
> each claim regression-proved by breaking the thing it checks. The findings below are left
> as written — they describe the state at `a946de8e`, which is what the measurements were
> taken against — and this block records what changed.
>
> | Finding | Status | Evidence |
> |---|---|---|
> | F-001 depreciation ignores `macrs_system` | **FIXED** (795) | Dispatch keyed on the system; unsupported combinations refused by name. 10 new tests fail on the pre-fix engine |
> | F-002 loan schedule / unbalanced JE | **FIXED** (796) | 21.51% → **0.00%**, 24.90% → **0.00%**, 10.0% → **0.00%** on the same sweeps |
> | F-003 no correct DB build path | **FIXED** (797) | Chain 25 → **29** tables, 0 column/FK drift; Dockerfile boot 27 → **29** |
> | F-004 monetary gate inspects 0% | **FIXED** (799) | Narrowing the parser now fails `0 of 53 / 0 of 16 / 0 of 18` = the measured 87 |
> | F-005 presence-only entitlement tests | **FIXED** (800) | Four classes rewritten, all four regression-proved |
> | F-006 branch protection vs `ci.yml` | **PARTIAL** (800) | Manifest + guard shipped. **The four `gh api` calls are a repository-settings change and were left for the CEO** — see below |
> | F-007 DuPont unreachable / flag 0.15% | **FIXED** (798) | Shipped per CEO decision; flag **0.15% → 100%** over 2,000 trial balances |
> | F-008 internal Zero-Storage doc stale | **FIXED** (801) | Rewritten; `flagged_accounts` invariant now has 23 enforcing tests |
> | F-009 depreciation docstring | **FIXED** (801) | Cut back to the dispatch table; mid-month refused rather than approximated |
> | F-010 parity-test scope | **FIXED** (802) | FKs now compared; nullability/types scoped out *in the docstring*, with the reason |
> | F-011 `hard_delete` 2.0 blind spot | **FIXED** (802) | Both 2.0 forms regression-proved; measured 0 live instances, so pattern-only |
> | F-012 unwired scripts | **FIXED + CORRECTED** (802) | `check_route_wiring` wired into a *required* job. **`weekly_security_digest.py` was NOT unwired** — see correction below |
> | F-013 nightly timeout headroom | **FIXED** (802) | `TimeoutExpired` caught and named; nesting pinned by test |
> | F-014 retired tier in compliance doc | **FIXED** (801) | Live doc corrected; archive left historical |
>
> ### Correction to F-012
>
> The report said `scripts/weekly_security_digest.py` "has no caller anywhere". **That is
> wrong.** It is referenced by `docs/04-compliance/SECURITY_POLICY.md`, the weekly
> security-review template and a completed review — a documented manual operator tool
> invoked with `METRICS_URL=...`, not an unwired guard. The grep that produced the claim
> timed out and returned partial results, and I reported the partial result as a complete
> one. No change was made to that script.
>
> ### Three things found while fixing, not while reviewing
>
> * **The depreciation engine had F-002's rounding defect too** — a $123,456.78 asset
>   reported $123,456.77 of total depreciation against an ending book value of 0.00.
>   Found by a new test, not by reading. Its deferred-tax column also disagreed with its
>   own cumulative in 17 of 48 configurations.
> * **`scripts/overnight/tests/` ran nowhere.** The regression tests for the nightly
>   agents — including the Sprint 712 false-green guard — were in no workflow. Now in
>   `backend-tests`.
> * **Prior-period DuPont deltas are unreachable**: both `calculate_analytics` call sites
>   pass `previous_totals=None`. Caught before it reached the user guide, which would have
>   reproduced F-007 in miniature.
>
> ### Still outstanding — one CEO action
>
> Four gates produce a red X and merge anyway: **Accounting Policy**, **Documentation
> Consistency**, **Report Standards**, **OpenAPI Schema Drift**. Making them block is a
> change to repository settings rather than to code, so it was not made unilaterally:
>
> ```
> gh api -X PATCH repos/:owner/:repo/branches/main/protection/required_status_checks \
>   -f 'checks[][context]=Accounting Policy Gate' \
>   -f 'checks[][context]=Documentation Consistency Gate' \
>   -f 'checks[][context]=Report Standards Gate' \
>   -f 'checks[][context]=OpenAPI Schema Drift Check'
> ```
>
> All four pass on this branch. Until the call is made, `ci.yml`'s gate manifest says so
> explicitly and `test_ci_gate_manifest.py` keeps it saying so.
>
> **Verification:** backend **9,209 passed / 0 failed** (821.8s, up from 9,126 collected);
> frontend **2,041 passed / 0 failed**, build emits `ƒ (Dynamic)`; `ruff check` clean; all
> eight gates green.

---

## 1) Executive Summary

- **Total Findings: 14**
  - P1 (High): 4
  - P2 (Medium): 4
  - P3 (Low): 4
  - Informational: 2
  - P0 (Stop-Ship): 0 — nothing here stops a *current* paying customer from using the product, but two findings produce wrong numbers in shipped tools and one makes a rebuild-from-scratch unsound.

- **Top risk themes:**
  - **A selected input that is accepted, echoed back, and ignored.** The depreciation tool offers "GDS 150% DB" and "GDS Straight-Line" in a shipped dropdown; both return the 200% declining-balance table. One input, three labels, one answer (F-001).
  - **Columns rounded independently never foot.** The loan amortization schedule disagrees with itself in ~22% of rows, and the suggested journal entry it hands the practitioner is out of balance in 10% of loan configurations (F-002).
  - **No database build path produces a correct schema.** The Alembic chain is missing 4 tables and 6 columns; the Dockerfile's fresh-environment path permanently misses 2 *different* tables. Three paths, none right (F-003).
  - **A guard whose parser matches 0 of 87 declarations in its own protected classes.** The Phase XLV monetary-precision invariant has had no working enforcement since the SQLAlchemy 2.0 migration, and its unit tests pass because they are written in a syntax the codebase does not use (F-004).
  - **Presence reported as capability, at the entitlement boundary.** Four test classes named after enforcement properties assert only that a function is `callable`; one is named for a property `SESSION_STATE` already records as false (F-005).
  - **The enforcement story and the enforcement disagree.** `ci.yml`'s own header claims a required check that branch protection does not require, and four gates — including the accounting-invariant gate — do not block merge (F-006).

- **Critical system status:**
  - **Money correctness: WARNING.** Two shipped tools produce numbers a CPA would reject on sight (F-001, F-002). The underlying monetary *storage* layer is sound — measured, 0 Float monetary columns exist.
  - **Zero-Storage integrity: PASS.** Measured all 7 account extractors; every one persists an account-name field only. No financial detail reaches the database on any path examined. The customer-facing compliance doc is accurate and current; the *internal* policy doc engineers read is the stale one (F-008).
  - **Auth / CSRF / entitlement enforcement: PASS with a caveat.** 79 of 84 export routes carry `check_export_access`; the 5 that do not are `export_sharing`, which gates in-body via `check_export_sharing_access`. No route-local tier comparisons remain. The *tests* asserting this are weak (F-005), but the behaviour is correct.
  - **Recoverability: FAIL.** See F-003. This is the finding most likely to cause a very bad day.
  - **Test suite health: 9,126 backend tests collected, suite green.** Today's nightly RED is a timing artifact — it ran at 02:00, the fix landed 04:36; the two suites pass 60/60 now. `SESSION_STATE` is accurate on this point.
  - **False confidence: this is where the review found most of its weight.** Four of the fourteen findings are controls that cannot fail, or can fail and not block.
  - **Design mandate (Oat & Obsidian): PASS.** `lint_design_tokens.py` runs on the real tree via a required test suite and reports 0 violations. Well-built; no finding.

- **Prior DEC:** 2026-03-31 (seven months ago, across the dormancy). Its eight findings are not re-tracked here — the codebase has moved too far for that comparison to mean anything. Section 7 notes which of its themes resolved.

---

## 2) Hypothesis List (from `tasks/lessons.md`) and What Each Returned

The brief asked that `lessons.md` be treated as a hypothesis list, not history. It was. Ten patterns, each hunted as an open population:

| # | Pattern | Result |
|---|---------|--------|
| H1 | Two exit codes where reality has three | **1 new instance** — `check_route_wiring.py` has the right three-outcome shape and runs nowhere (F-012). The nightly briefing compiler handles `DID_NOT_RUN` correctly — a *positive*. |
| H2 | Parser-based guard silently covering a fraction | **1 new instance, the worst yet** — `monetary_float.py` covers 0% (F-004). |
| H3 | Hand-maintained list that stopped matching | **Measured; mostly clean.** `PRE_EXISTING_DRIFT_TABLES`/`COLUMNS` still match exactly. The `no_float_monetary` scope list misses 2 of 17 Float columns — both legitimately non-monetary. Measurement says *do not widen it yet*. |
| H4 | Self-referential test | **1 new instance** — the DuPont verification test (F-007). |
| H5 | SQLite-invisible Postgres constraint | **Enum guard verified honest** (19 known, 19 found, 26/26 parsed). Extended the technique to tables/columns/FKs → F-003. |
| H6 | Declared contract nobody implements | **2** — `database.py:128` comment (F-003), depreciation module docstring (F-009). |
| H7 | Presence read as capability | **4 instances in one file** (F-005). |
| H8 | Stale claim logged at runtime | **Zero.** The slowapi class is fully cleaned — verified by grepping the claim vocabulary, not the version number. Credit to Sprint 786b / PR #195. |
| H9 | Layer-local verification | **1** — DuPont is engine-complete and reachable by nothing (F-007). |
| H10 | Float where Decimal is required | **Zero in storage.** Measured 17 Float columns; all ratios/scores. The money defects found are *rounding-composition*, not Float (F-002). |

---

## 3) Findings

### F-001: Depreciation tool ignores the MACRS system the customer selects — P1, CONFIRMED

- **Severity:** P1 · **Category:** Money correctness / customer-facing tax output
- **File:** `backend/depreciation_engine.py:457` (`_macrs_percentages`), with the input declared at `:206`, validated at `:232`, echoed at `:308`, and gating at `:511`/`:585`
- **UI:** `frontend/src/app/tools/depreciation/page.tsx:292-293`

`_macrs_percentages` dispatches on **convention and property class only**. `config.macrs_system` is never read by it. The field is accepted by the API (`routes/depreciation.py:59`, `Literal["gds_200db","gds_150db","gds_sl"]`), echoed back in the response `inputs` block, used only to decide *whether* a tax schedule exists — and never affects a single number.

**Failure scenario (run, not reasoned):** a $100,000 5-year asset, half-year convention.

| `macrs_system` selected | Year-1 tax depreciation returned |
|---|---|
| `gds_200db` | $20,000.00 |
| `gds_150db` | $20,000.00 |
| `gds_sl` | $20,000.00 |

The dropdown offering those three choices is shipped at `page.tsx:292-293`. A practitioner electing straight-line GDS receives 200% declining-balance figures labelled as their election, and carries them into a return.

> **Practitioner confirmation required, and deliberately not adjudicated here.** The *defect* — an input accepted, echoed, and ignored — is a pure code fact. The *correct* GDS-SL and GDS-150DB percentages for each property class are current tax law and must be confirmed by a CPA before any table is written. Sprint 793b/781 is the right home. What is **not** affected: the GDS-200DB half-year path (Table A-1 values verified against Pub 946 for classes 3/5/7/10), the 150DB classes 15/20, and the mid-quarter 5-year tables — all correct as published.

**Why no test caught it:** the only test touching `GDS_150` (`tests/test_depreciation_engine.py:192`) uses property class 15, where the 150DB table is the *only* table available. It passes for a reason unrelated to `macrs_system` — setting `GDS_200` on class 15 returns identical numbers. A check that works for a reason you did not design.

**Fix shape:** key `_macrs_percentages` on `(macrs_system, convention, class)`; reject unsupported combinations with a named error rather than silently substituting. Add one test per system asserting the *systems differ from each other* — the cheapest assertion that cannot pass vacuously.

---

### F-002: Loan amortization schedule does not foot, and the suggested journal entry does not balance — P1, CONFIRMED

- **Severity:** P1 · **Category:** Money correctness / customer-facing output
- **File:** `backend/loan_amortization_engine.py:369-371` (independent per-column quantization), `:456-473` (`_build_journal_entry_templates`)
- **UI:** `frontend/src/app/tools/loan-amortization`

Each column is quantized independently (`_q(interest)`, `_q(payment_amount)`, `_q(principal_portion)`), so `_q(a) + _q(b)` is compared against `_q(a+b)` and the two differ by a cent whenever both halves round the same way.

**Measured across 48 standard loans / 6,912 schedule rows:**

| Property | Rows violating |
|---|---|
| `interest + principal == scheduled_payment` | **1,487 (21.51%)** |
| `beginning_balance − principal − extra == ending_balance` | **1,721 (24.90%)** |

Concrete row — $250,000, 6.99%, 360 monthly payments, period 2:

```
begin=249,794.67  payment=1,661.58  interest=1,455.05  principal=206.52  end=249,588.15
                                    1,455.05 + 206.52 = 1,661.57   ← payment column says 1,661.58
```

The **journal entry** built from those same columns is worse, because an unbalanced JE is not a presentation nit — it is unusable. Across 420 loan configurations (6 principals × 7 rates × 5 terms × 2 frequencies), the period-1 template's debits ≠ credits in **42 cases (10.0%)**. Example: $100,000 / 5.00% / 60 monthly → debits $1,887.13, credits $1,887.12.

**Why no test caught it:** 18 engine tests, none asserting a row foots. `test_journal_entry_templates_balance` (`tests/test_loan_amortization_engine.py:211`) *does* assert `total_dr == total_cr` — using $50,000 / 5% / 12 monthly, which is one of the 90% that happen to balance. The convenient fixture again.

**Fix shape:** derive one column from the others after rounding — quantize `interest` and `payment`, then set `principal = payment − interest` — so the row is arithmetically closed by construction. Then one property test over a generated sweep asserting every row foots and every JE balances, rather than one hand-picked loan.

---

### F-003: No database build path produces a correct schema — P1, CONFIRMED

- **Severity:** P1 · **Category:** Recoverability
- **Files:** `backend/migrations/alembic/versions/` (45 migrations), `backend/Dockerfile:79-89`, `backend/database.py:128-141`

Sprint 741d found 19 drifting enum types and `engagementstatus.COMPLETED` with no migration. The brief said to assume there is more. There is, and it is structural. Three build paths were replayed mechanically:

| Build path | Tables | What is wrong |
|---|---:|---|
| `alembic upgrade head` on an empty DB (the documented chain) | 25 / 29 | 4 tables, 6 columns, 3 FKs missing |
| Dockerfile on an empty DB → `alembic stamp head` + `create_all()` | 27 / 29 | `admin_audit_logs` and `dunning_episodes` missing **permanently** |
| Production today | 29 (assumed) | Built by `create_all()` then incrementally upgraded — **not verified, see §6** |

**(a) The chain is missing four tables and six columns.** Verified three ways: schema reflection after a real `alembic upgrade head`; a grep showing the identifiers appear in **zero** migration files; and a functional probe. All eight probes fail:

```
FAIL  Stripe webhook idempotency insert (processed_webhook_events)  — no such table
FAIL  Tool-activity feed insert (tool_activities)                   — no such table
FAIL  Password-reset token insert (password_reset_tokens)           — no such table
FAIL  Waitlist signup insert (waitlist_signups)                     — no such table
FAIL  Engagement completion gate (engagements.completed_at)         — no such column
FAIL  Engagement completion gate (engagements.completed_by)         — no such column
FAIL  TB diagnostic cash-cycle write (diagnostic_summaries.dso)     — no such column
FAIL  TB diagnostic cash-cycle write (diagnostic_summaries.ccc)     — no such column
```

`processed_webhook_events` is the **Stripe webhook idempotency table**. On a chain-built environment, every webhook replay is reprocessed. The `engagements.completed_*` columns are the exact column-level counterpart of Sprint 741d's `engagementstatus.COMPLETED` finding — same feature, same restore, second mechanism.

This drift is **known and allow-listed** since Sprint 737 (`tests/test_alembic_models_parity.py:118,135`) and filed as Sprint 738. The new facts are: (i) it is still exactly 4 and 6 — the allow-list has *not* rotted, which is worth knowing; and (ii) **Sprint 738 is recorded as blocked on the Neon connection string, and it is not.** Writing migrations for four known tables and six known columns needs no production read. Sprint 741d already demonstrated that its "needs a database" step did not. The real design question — making the new migrations idempotent so production, which already has these objects, does not fail on `CREATE TABLE` — is answerable from the repo.

**(b) The Dockerfile's fresh-environment path misses two *different* tables, forever.** `Dockerfile:79-89` runs `alembic stamp head` — not `upgrade` — when `alembic_version` is absent. So on a brand-new database all 45 migrations are marked applied without running, and the schema comes entirely from `init_db()`'s `create_all()`. That call imports **11 model modules**; `env.py` and the parity test import **15**.

Measured:
- `init_db()` in isolation → **25 of 29 tables**.
- `import main` (the real entrypoint, which loads every route module) then `init_db()` → **27 of 29**. Still missing `admin_audit_logs` (superadmin audit trail, Sprint 590) and `dunning_episodes` (failed-payment workflow, Sprint 591).

Because `stamp head` already marked `590a_superadmin` and `591a_dunning` as applied, no later deploy will create them. A new region, a fresh staging environment, or a DR rebuild into an empty database boots reporting healthy and 500s the first time an admin action is logged or a payment fails.

The comment at `database.py:128` reads *"Ensure ALL model modules are imported so Base.metadata sees every table."* It lists 11 of 15. The parity test's own comment says *"Keep this list in sync with `init_db()` and `migrations/alembic/env.py`"* — three lists, 11 / 15 / 15.

**Fix shape:** (1) replace all three hand-maintained import lists with one derived import (walk `backend/*_model.py` + `models.py`), or a single `models/__init__.py` that the others import — the Sprint 792 ranking, derive over list; (2) add a parity assertion that `init_db()`'s resulting table set equals `Base.metadata`, which is the check none of the three lists can fail; (3) unblock Sprint 738 and write the ten missing migrations idempotently; (4) separately decide whether `stamp head` on an empty DB is the behaviour you want at all — `upgrade head` would be correct once (3) lands.

---

### F-004: The monetary-precision gate inspects 0% of its target, and does not block merge — P1, CONFIRMED

- **Severity:** P1 · **Category:** False confidence / control integrity
- **File:** `backend/guards/checkers/monetary_float.py:47`
- **Config:** `backend/guards/accounting_policy.toml:5-30`
- **Tests:** `backend/tests/test_accounting_policy_guard.py:34,51-53,74,84-86`
- **CI:** `.github/workflows/ci.yml:552` (job `accounting-policy`)

The Phase XLV invariant — "Monetary precision (Float→Numeric)", listed in `CLAUDE.md`'s completed-phases table and the headline of Sprints 340–344 — is enforced by rule 1 of the Accounting Policy Gate. Rule 1 recognises exactly one syntax:

```python
if isinstance(func, ast.Name) and func.id == "Column":   # monetary_float.py:47
```

Every model in this codebase is SQLAlchemy 2.0 style. **Measured across the three files the rule scans: 0 `Column(...)` declarations, 169 `mapped_column(...)`. Within its four protected classes: 0 and 87.** The rule inspects nothing and prints `ALL 5 RULES PASSED`.

**Regression-proved.** A `Float` monetary column was injected directly into `DiagnosticSummary` — one of the rule's four named `protected_classes`, in one of its three named `files`:

```
injected Float monetary column DiagnosticSummary.bogus_total_cash
Accounting Policy Guard: ALL 5 RULES PASSED
exit=0
```

(Tree restored; `git diff` clean.)

**Why the unit tests pass.** `test_accounting_policy_guard.py` builds synthetic source strings — 10 uses of `Column(`, **0** uses of `mapped_column(`. The tests exercise a syntax the codebase never uses; the codebase uses a syntax the checker cannot see. The two sets are disjoint, and both are green.

All five rules were regression-proved by injection:

| Rule | Invariant | Fires on an injected violation? |
|---|---|---|
| `no_float_monetary` | Phase XLV monetary precision | **NO** — 0 of 87 declarations visible |
| `no_hard_delete` | Phase XLVI audit immutability | Yes for `db.delete(x)`; **NO** for `db.execute(delete(M))` → F-011 |
| `revenue_contract_fields` | ASC 606 / IFRS 15 | Yes (2 violations) |
| `adjustment_gating` | Phase XLVIII approval gating | Yes (1 violation) |
| `framework_metadata` | `framework_note` presence | Yes (1 violation) |

**Mitigating measurement, and it matters for severity:** there is **no live defect behind this gate**. All 17 `Float` columns across the 15 model modules were enumerated; 15 are inside the rule's scope and allow-listed by name, and the 2 outside it (`AnalyticalExpectation.precision_threshold_percent`, `ToolRun.composite_score`) are a percentage and a score. Money is `Numeric(19,2)` everywhere, including in the modules the rule never looks at. So this is a **control failure, not a correctness failure** — the invariant is currently satisfied by discipline, and nothing would say so if it stopped being.

**Fix shape:** match `mapped_column` as well as `Column`, resolve the type from the first positional arg *or* the `Mapped[...]` annotation, and — the part that generalises — add a **coverage self-check**: count column declarations the naive way and require the parser to account for all of them, asserting nothing about their contents. The Sprint 786c fix shape, applied to the gate that needed it most. Then rewrite the unit fixtures in the syntax the repo actually uses, and keep one `Column(` case for legacy coverage.

---

### F-005: Four entitlement test classes assert presence, not enforcement — P2, CONFIRMED

- **Severity:** P2 · **Category:** False confidence / security
- **File:** `backend/tests/test_post_audit_2026_04_20_batch2.py:265,286,321,338`

| Class | What its name claims | What it asserts |
|---|---|---|
| `TestEntitlementHelpersExist` (`:265`) | Sprint 678 helpers are wired | `callable(check_export_access)` ×3 |
| `TestExportRoutesAreGated` (`:286`) | export modules are gated | **at least one** route per module, for 4 of 6 export modules |
| `TestFormatAccessWiredOnUploadRoutes` (`:321`) | "`check_format_access` should be invoked on the TB/bulk upload entry points" | `callable(check_format_access("qbo"))` — its own comment calls this "minimal smoke" |
| `TestToolRoutesCheckUploadLimit` (`:338`) | "The 11 testing-tool routes should enforce upload limits" | `hasattr(testing_route, "enforce_tool_access")` |

The last is the sharp one: it is named for a property `SESSION_STATE` **already records as false** (Sprint 790 — the advertised 100/500 monthly upload allowances are unenforced on every paid tier; `check_upload_limit` only reads). A green test class named after a known-broken property is worse than no test, because the next reader greps for coverage, finds it, and moves on.

`hasattr(x, "enforce_tool_access")` is `shutil.which` wearing a different hat — the exact Sprint 786b nightly lesson, at the entitlement boundary.

**Measured, and the good news:** the *behaviour* is fine. 79 of 84 export routes carry `check_export_access`; the 5 that do not are `export_sharing`, which gates in-body at `routes/export_sharing.py:318` via `check_export_sharing_access(user, db)`. And no route-local tier comparison remains anywhere in `routes/` — Sprint 789's instance is closed. So this is tests that cannot fail protecting code that is currently right.

**Fix shape:** replace each with the behavioural assertion the class name already promises — POST as each tier, assert the status code. Sprint 789's `test_sod_routes.py` is the model and it is four lines per case. Additionally: Sprint 789's own lesson called for an **AST guard banning route-local tier comparisons** so the class cannot recur; that guard was never built. It is the cheaper half.

---

### F-006: Branch protection and `ci.yml`'s own header disagree; four gates do not block merge — P2, CONFIRMED

- **Severity:** P2 · **Category:** False confidence / governance
- **Files:** `.github/workflows/ci.yml:4-10`, GitHub branch-protection API

`ci.yml:4-7` lists eleven jobs as "MUST pass before merge (required status checks)". The live `required_status_checks.contexts` for `main` is twelve. They are not the same twelve.

- **Claimed required, actually not:** `OpenAPI Schema Drift Check`. A PR that changes the public API surface without regenerating `scripts/openapi-snapshot.json` can merge with that job red. Sprint 784's fix specifically relied on the snapshot forcing a second edit.
- **Actually required, not claimed:** `Backend Tests (PostgreSQL 15)` — a real strengthening the header never recorded.
- **Not required and not claimed — the ones that matter:**
  - `Accounting Policy Gate` — the five AST checkers for monetary precision, audit immutability, ASC 606 fields and adjustment gating.
  - `Documentation Consistency Gate` — every tool-count guard from Sprints 784 / 789b.
  - `Report Standards Gate`.
  - `Backend Slow Tests`.

`CLAUDE.md`'s Document Authority Hierarchy opens with *"Executable enforcement — `ci.yml`, Husky hooks. These are mechanically enforced and final."* For these four jobs that is false: they produce a red X that merges. The Husky `pre-commit` hook does not run them either — it runs a secrets pattern scan, Jest when `frontend/src/` is staged, and `lint-staged`.

All three non-required gates were run and all three pass today, so nothing is currently being waved through. Combined with F-004, though: the accounting gate both cannot see its primary target *and* could not block if it did.

**Fix shape:** pick one list and derive the other. Either add the four jobs to branch protection and fix the header, or demote them explicitly in the header with the reason. Then a test that reads `ci.yml`'s header block and the protection API and asserts they agree — this is a claim with an expiry date, which is exactly what Sprint 786b says to guard.

---

### F-007: DuPont decomposition is documented to customers, reachable by nobody, and its self-verification flag is 99.85% false — P2, CONFIRMED

- **Severity:** P2 · **Category:** Stale load-bearing claim / money logic
- **Files:** `backend/ratio_engine.py:1380-1447` (engine), `:869,877` (the ROE it verifies against)
- **Claims:** `docs/07-user-facing/USER_GUIDE.md:168`, `features/status.json:425-437`, `CLAUDE.md` Key Capabilities
- **Test:** `backend/tests/test_ratio_core.py:767`

**(a) Unreachable.** `calculate_dupont` and `calculate_dupont_decomposition` have exactly one caller in the repository: a test. No route, no PDF section, no frontend reference, and zero occurrences of "dupont" in `scripts/openapi-snapshot.json`. Meanwhile `USER_GUIDE.md:168` tells customers *"A DuPont decomposition (Net Profit Margin × Asset Turnover × Equity Multiplier = ROE) is available when all components are calculable"*, and `features/status.json:434` marks `financial-ratios` `"status": "complete"` with the verification step *"Verify DuPont decomposition breakdown"*, `last_verified: 2026-03-18` — a step that cannot have been performed through any surface.

**(b) The verification flag is broken on both ends.** `verification_matches` (`:1417`) compares the full-precision `decomposed_roe` against `direct_roe = roe_result.value / 100.0` using `rel_tol=1e-6`. But `roe_result.value` is `round(roe, 1)` of a **percentage** (`:877`) — three decimals of the fraction. A `rel_tol` of 1e-6 against a value rounded to 0.1 percentage points can only pass when ROE lands almost exactly on the grid. Separately, Sprint 681 made ROE use *average* equity while the equity multiplier still uses *ending* equity, so the two quantities are not the same quantity.

**Measured over 2,000 randomly generated realistic trial balances:**

```
verification_matches TRUE :    3  (0.15%)
verification_matches FALSE: 1997 (99.85%)
```

**(c) The test that pinned it is self-referential.** `test_dupont_verification_matches_with_isclose` uses revenue 1,000,000 / expenses 800,000 / assets 1,500,000 / equity 500,000 — ROE exactly 40.0%, decomposed exactly 0.4. Its docstring asserts *"legitimate decompositions always verify."* The measurement says 0.15% do.

**Fix shape:** decide first whether DuPont ships. If yes: wire a route, compare against the unrounded ROE, and make the equity basis consistent between the two (or state the basis in the output). If no: delete the engine code and correct `USER_GUIDE.md:168` and `features/status.json` — a capability promised in the user guide and absent from the product is the kind of claim that surfaces during a demo.

---

### F-008: The internal Zero-Storage policy the engineers read is the stale one — P2, CONFIRMED

- **Severity:** P2 · **Category:** Stale load-bearing claim / compliance
- **File:** `backend/shared/metadata_persistence_policy.md`

Two documents describe what persists. The **customer-facing** `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md` is accurate and current: it correctly discloses `tool_runs.flagged_accounts`, `uncorrected_misstatements`, and `analytical_expectations` as deliberate retained classes with reasons.

The **internal** `shared/metadata_persistence_policy.md` (Sprint 96.5 vintage) is the one a developer opens when deciding whether a new column is permitted. It:
- lists **8 tables** under a heading, "What Persists (Database Tables)", that reads as exhaustive — the schema has **29**;
- states *"There is **no** foreign key or reference to any specific account, amount, or transaction"* — contradicted by `ToolRun.flagged_accounts` (account names) and `UncorrectedMisstatement.accounts_affected_json` + `fs_impact_net_income` (account names *and* amounts), both of which the customer-facing doc correctly discloses as intentional.

This inverts the usual risk: the externally-audited document is right, and the internal engineering guidance is wrong in the permissive direction — it describes a stricter system than exists, so a reader cannot tell which new persistence is a violation and which is precedent.

**Zero-Storage itself is sound — measured.** All 7 functions in `shared/account_extractors.py` append an account-name field (`account`, `gl_account`, `account_name`) and nothing else; `_dedupe_sort` returns `list[str]`. No amount reaches `flagged_accounts` on any path. There is, however, **no test asserting that invariant** — the documented rule "identifiers only, no balances" (`ZERO_STORAGE_ARCHITECTURE.md:122`) has no enforcement. Seven correct extractors and an eighth is one sprint away.

**Fix shape:** rewrite `metadata_persistence_policy.md` to derive its table list (or delete it and point at the compliance doc — one source beats two). Add one test asserting no string in a persisted `flagged_accounts` payload contains a digit-plus-separator amount pattern; it is the cheap half of the invariant and it is the half with a documented promise behind it.

---

### F-009: Depreciation module docstring advertises three capabilities that do not exist — P3, CONFIRMED

- **Severity:** P3 · **Category:** Stale claim / dead branch
- **File:** `backend/depreciation_engine.py:13-20`, `:206`, `:471-490`

The module docstring claims:
- *"Conventions: half-year (HY), mid-quarter (MQ), mid-month (MM)"* — MQ exists for **5-year property only** (`MACRS_MQ_5YR_200DB`); `_macrs_percentages:467` raises for any other class.
- *"27.5-year residential real, 39-year nonresidential real (mid-month)"* and *"A-6 (residential real / mid-month)"* — **no A-6 table exists**, and `validate()` at `:206` rejects any `macrs_property_class` outside `(3,5,7,10,15,20)`. Confirmed by probe: class 39 → `DepreciationInputError`.
- The `macrs_property_class` field comment says *"3, 5, 7, 10, 15, 20, 27.5, 39"*, contradicting the validator seven lines below it.

`_macrs_real_property_percentages` (`:471`) is therefore reachable only via `convention=mid_month` with a *personal*-property class, where it computes mid-month straight line over the **book** `useful_life_years` — a number with no MACRS meaning. Probed: a $100,000 5-year asset at `mid_month` returns `[19166.67, 20000, 20000, 20000, 20000, 833.33]`, which sums to cost and looks entirely plausible. The function also contains a dead `if cls not in (15, 20): pass` block.

Severity is P3 rather than P1 only because the UI exposes no mid-month option (`page.tsx` offers `half_year` and `mid_quarter`); the API accepts it (`routes/depreciation.py:61`).

**Fix shape:** reject `mid_month` at the schema until real-property tables exist, delete the dead branch, and cut the docstring back to what ships. Per the Sprint 784 lesson, write the docstring from the dispatch table, not from the intent.

---

### F-010: The Alembic parity test's scope is narrower than its title — P3, CONFIRMED

- **Severity:** P3 · **Category:** False confidence
- **File:** `backend/tests/test_alembic_models_parity.py:1` ("Alembic head schema must match `Base.metadata`")

The test compares **table names and column names**. It does not compare nullability, foreign keys, primary keys, unique constraints, column types, or server defaults. Measured on the chain-built database:

| Dimension | Disagreements |
|---|---:|
| Tables | 4 (allow-listed) |
| Column names | 6 (allow-listed) |
| **Nullability** | **50 (unguarded)** |
| **Foreign keys** | **3 (unguarded)** — `analytical_expectations.archived_by`, `engagements.completed_by`, `uncorrected_misstatements.archived_by` |
| Primary keys | 0 |
| Unique constraints | 0 |

The 50 nullability drifts are **benign today** and should not be fixed reflexively: every one is a column the ORM declares `NOT NULL` via a non-`Optional` `Mapped[...]` annotation while the migration created it nullable, and every one has a Python-side `default`, so SQLAlchemy always supplies a value. They are listed here because the test's title claims to cover them and does not. Two of the three FK gaps are on columns the chain is missing entirely (F-003).

This is the Sprint 784c shape exactly: *the right file, the wrong claim.* "This schema is guarded" felt like coverage.

**Fix shape:** state the covered dimensions in the docstring (cheap, honest, and enough on its own), and optionally extend to FKs — the one dimension with real integrity consequence. Leave nullability out or allow-list it wholesale with the reason; a 50-item noise wall is how a gate gets disabled.

---

### F-011: `no_hard_delete` is blind to the SQLAlchemy 2.0 delete form — P3, CONFIRMED (latent)

- **Severity:** P3 · **Category:** False confidence
- **File:** `backend/guards/checkers/hard_delete.py:15-16`

The checker is text-based and matches `db.delete(` and `.query(Model)...delete(`. Regression-proved both ways against `routes/activity.py`:

```
db.delete(row)                      → exit 1, 1 violation   ✓
db.execute(delete(ActivityLog))     → exit 0, ALL 5 PASSED  ✗
```

**Measured: zero `execute(delete(...))` call sites exist in the codebase today.** So this is a latent gap, not a live hole in the Phase XLVI audit-immutability invariant — which is why it is P3 and not P1. It is recorded because the codebase has already migrated to 2.0 style for columns (F-004), and the delete syntax is the next thing to follow.

**Fix shape:** add the 2.0 pattern. Do not rewrite the checker to AST for its own sake — the measurement does not justify it.

---

### F-012: Two guard scripts are wired into nothing — P3, CONFIRMED

- **Severity:** P3 · **Category:** False confidence / dead code
- **Files:** `scripts/check_route_wiring.py`, `scripts/weekly_security_digest.py`

Every `scripts/*.py` guard was checked against `.github/workflows/`, `frontend/.husky/`, and the backend test suite. Eleven are wired. Two are not:

- `check_route_wiring.py` — the dead-route guardrail from Sprint 677. It passes today (60 route modules scanned, 50 direct + 10 via aggregators) and has the *correct three-outcome shape*, documenting exit 2 for "cannot locate `backend/routes/`" — the very pattern Sprint 794's lesson holds up as the one to copy. Nothing calls it.
- `weekly_security_digest.py` — no caller found in any workflow, hook, test, or doc.

`lint_design_tokens.py` initially looked unwired too; it is not — `backend/tests/test_design_token_lint.py:55` calls `linter.scan()` over the real tree inside a required suite, and it reports 0 violations. Verified by running it directly. **No finding there, and it is the best-built guard in the repo**: real-tree scan, empty allowlist asserted, findings pinned by path/line/matched-text.

**Fix shape:** add `check_route_wiring.py` to the `accounting-policy`-style gate block (it costs seconds), or delete it. Decide what `weekly_security_digest.py` is for; if it is run by an external cron, say so in the file.

---

### F-013: Nightly pytest timeout headroom is shrinking — Informational, CONFIRMED

- **Category:** Observability / operational clock
- **Files:** `scripts/overnight/agents/qa_warden.py:47,78`, `scripts/overnight/agents/coverage_sentinel.py:46`, `scripts/overnight/orchestrator.py:66-70`

Lesson 1185 flagged this as "a ticking clock". The current numbers:

| Budget | Value | Last observed | Headroom |
|---|---:|---:|---:|
| `qa_warden` inner pytest | 1200 s | 690.7 s | 1.74× |
| `coverage_sentinel` pytest `--cov` | 1500 s | ~900–1035 s (est. 1.3–1.5× base) | ~1.45× |
| orchestrator per-agent | 1700 s | 757.2 s | 2.25× |

At 9,126 tests and ~76 ms/test, the `qa_warden` cap is reached near ~15,800 tests and the `coverage_sentinel` cap near ~14,000. The suite grew by 114 in a single recent session. Nesting is correct (1700 > 1200 + 300).

**Positives worth recording, because they are the shape the brief asked for:** `coverage_sentinel` catches `TimeoutExpired` and reports it; `qa_warden` has a Sprint 712 false-green guard (`:109`) that escalates a parse-free non-zero exit rather than recording 0/0 as green; and `briefing_compiler.py:52,80` treats a missing agent as **red** and emits `status: "DID_NOT_RUN"`. The nightly is one of the honestly-built checks in this repo.

`qa_warden`'s inner `subprocess.run(..., timeout=1200)` has no `except TimeoutExpired`, but the failure is still honest: the agent crashes, the orchestrator logs it, and the brief shows DID_NOT_RUN red. Worth catching anyway so the brief can say *why*.

**One observation, not a finding:** the nightly runs against whatever is checked out. Tonight it measures `sprint-786b-frontend-devtype-majors`, not `main`.

---

### F-014: A retired tier name in a customer-facing compliance document — Informational, CONFIRMED

- **File:** `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md:128,129`

Two examples read `"Tier: team"` and `"subscription_created, tier: team"`. `AGENTS.md` records Team and Organization as retired; the live tiers are Free / Solo / Professional / Enterprise. Trivial to fix, listed because it sits in a document shown to customers and prospective auditors, and because the same grep found the slowapi claim class fully cleaned — this is the only survivor of its type.

---

## 4) Measurements Taken

Everything below was computed, not estimated. Where a measurement argued against building something, that is recorded as the result.

| # | Measurement | Result |
|---|---|---|
| 1 | Loan schedule rows where `interest + principal ≠ payment` | **1,487 / 6,912 (21.51%)** over 48 loans |
| 2 | Loan schedule rows where `begin − principal − extra ≠ end` | **1,721 / 6,912 (24.90%)** |
| 3 | Loan configs whose period-1 journal entry is out of balance | **42 / 420 (10.0%)** |
| 4 | Depreciation `macrs_system` values producing distinct output | **1 of 3** (all return 200% DB) |
| 5 | DuPont `verification_matches == True` on realistic inputs | **3 / 2,000 (0.15%)** |
| 6 | `Column(...)` vs `mapped_column(...)` in the 3 files rule 1 scans | **0 vs 169**; in its 4 protected classes, **0 vs 87** |
| 7 | `Column(` vs `mapped_column(` in the guard's own unit tests | **10 vs 0** — disjoint from the target |
| 8 | Accounting Policy Gate rules that fire on an injected violation | **3 of 5 fully, 1 partially, 1 not at all** |
| 9 | Tables produced by `alembic upgrade head` on an empty DB | **25 of 29** |
| 10 | Tables produced by `init_db()` alone | **25 of 29** |
| 11 | Tables produced by `import main` + `init_db()` (the real path) | **27 of 29** |
| 12 | Functional probes of chain-built DB for shipped features | **0 of 8 succeed** |
| 13 | Chain-vs-ORM drift by dimension | tables 4 · columns 6 · nullability 50 · FK 3 · PK 0 · unique 0 |
| 14 | Occurrences of the 10 missing identifiers in any migration file | **0** |
| 15 | Required status checks: `ci.yml` header vs GitHub API | **11 claimed vs 12 live**, 1 claimed-not-required, 1 required-not-claimed |
| 16 | Export routes carrying `check_export_access` | **79 / 84** (the 5 gate in-body) |
| 17 | Route-local tier comparisons in `routes/` | **0** — Sprint 789's instance stays closed |
| 18 | `Float` columns across all 15 model modules | **17**; outside rule 1's scope: **2**, both non-monetary → **measurement says do not widen the scope yet** |
| 19 | Account extractors persisting anything but an account name | **0 of 7** → Zero-Storage sound |
| 20 | `execute(delete(...))` call sites (F-011's blind spot) | **0** → latent, not live |
| 21 | ORM model modules missing from `env.py` | **0 of 15** (the gap is in `init_db()`, not `env.py`) |
| 22 | Enum guard honesty re-check | 45 migrations replayed, 26/26 types parsed, 19 drifting / 19 known — **accurate** |
| 23 | `scripts/*.py` guards wired into CI, hooks, or tests | **11 of 13** |
| 24 | Design-token lint violations on the real tree | **0** |
| 25 | Backend tests collected | **9,126**; the 2 gate suites cited RED in today's nightly pass **60/60** |
| 26 | Tables documented in `metadata_persistence_policy.md` vs schema | **8 vs 29** |
| 27 | Stale "unmaintained / last release" claims surviving Sprint 786b | **0** |

**Measurements that said "don't build this":** #18 (widening the Float-column guard scope would currently find nothing), #20 (an AST rewrite of `hard_delete` is unjustified at zero instances), and the nullability half of #13 (50 findings, all benign, and a 50-item wall is how a gate gets switched off).

---

## 5) Agent Coverage Report

| Lens | Coverage | Basis |
|---|---|---|
| Systems Architect (A) | **Deep** | Full chain replay, three build paths, 29-model schema diff |
| Performance Alchemist (B) | **Thin** | Only the nightly timeout arithmetic. No profiling, no query analysis, no bundle review. |
| DX & Accessibility Lead (C) | **Thin** | Design-token lint verified clean; no a11y, no component review |
| Security & Privacy Lead (D) | **Moderate** | Entitlement enforcement measured end-to-end; Zero-Storage measured. **Not covered:** JWT/CSRF primitives, the 61 injection tests, CSP/proxy, rate-limit coverage, passcode throttle |
| Modernity Curator (E) | **Moderate** | SQLAlchemy 2.0 migration gaps found via F-004/F-011; dependency posture deferred to Sprint 786b |
| Observability (F) | **Moderate** | Nightly agents read end-to-end; Sentry/Loki not exercised |
| Zero-Storage Warden (G) | **Deep** | All 7 extractors + both policy documents |
| Type & Contract Purist (H) | **Moderate** | Docstring-vs-implementation sweep found F-009, F-003(b); no mypy review |
| Verification Marshal (I) | **Deep** | This was the review's centre of gravity — 5 gate rules regression-proved, 4 test classes audited, 13 scripts traced |
| AccountingExpertAuditor | **Moderate** | MACRS Table A-1 cross-checked; loan math derived. **Deliberately not adjudicated:** current tax law, the AICPA Table A-1 bucket structure in `shared/aicpa_tables.py`, ISA 530 projection math |

The thin rows are honest gaps, not a judgement that those areas are clean.

---

## 6) What I Could Not Verify, and Why

1. **Production's actual schema.** No Neon connection string. This matters specifically for F-003: production was built by `create_all()` and stamped, then upgraded incrementally. Whether `admin_audit_logs` and `dunning_episodes` exist there depends on *when* the stamp happened relative to migrations `590a_superadmin` and `591a_dunning`. If the stamp came after, **production is missing them too** and this is a live incident rather than a rebuild hazard. One query settles it:
   `SELECT tablename FROM pg_tables WHERE tablename IN ('admin_audit_logs','dunning_episodes','tool_activities','processed_webhook_events','password_reset_tokens','waitlist_signups');`
   Treat that as **PLAUSIBLE, unverified** until run. The same query answers whether the four chain-missing tables are present.

2. **Whether any deploy is live.** No `RENDER_API_KEY`; no endpoint exposes a build commit. Unchanged from `SESSION_STATE`'s write-up and not re-filed.

3. **Stripe.** No live keys. The F-003 `processed_webhook_events` consequence (webhook replay reprocessing on a rebuilt environment) is reasoned from the table's absence, not observed.

4. **PostgreSQL-dialect behaviour of the chain.** The replay was on SQLite. 14 of 45 migrations branch on dialect, so a Postgres replay could differ. Two independent cross-checks make the headline finding dialect-independent: the ten missing identifiers appear in **zero** migration files at all, and `create_all()`'s missing imports are pure Python. The *nullability* and *FK* numbers in F-010 should be re-measured on Postgres before being acted on.

5. **Current tax law.** F-001's defect is confirmed; the correct replacement percentages are not adjudicated here. Same for the AICPA Table A-1 bucket structure in `shared/aicpa_tables.py:43-64` — its docstring describes expansion factors keyed by expected/tolerable ratio, which a practitioner should confirm against the published guide. **Not affected:** sample *selection*, the MUS interval arithmetic, and the Poisson confidence-factor path, none of which this review found fault with.

6. **Runtime behaviour of the 18 tools.** No tool was exercised against a real trial balance end-to-end. The money findings come from the two engines that take structured form input and could be driven directly.

7. **Frontend.** 778 source files; only the two tool pages touching the money findings and the design-token lint were examined. Frontend test quality was not audited.

8. **PR #197.** Read but not reviewed, per the brief. Nothing in this report touches its files.

---

## 7) Council Tensions

**Tension 1 — Is F-004 a P1 when nothing is currently broken behind it?**
*Verification Marshal:* P1. A gate that prints `ALL 5 RULES PASSED` over a 0% scan is worse than a deleted gate, because it is cited as coverage. *Performance Alchemist, steel-manning:* the invariant is satisfied — 17 Float columns, all ratios and scores, money is `Numeric(19,2)` everywhere including the twelve modules the rule never reads. Calling a no-op a P1 while two tools return wrong numbers inverts the brief's own ranking.
**Resolution:** P1, but ranked below F-001 and F-002, and the report states plainly that there is no live defect behind it. The argument that carries it: F-001 and F-002 are both money defects that shipped past a full test suite, and the control that exists to catch that class is the one measured at zero.

**Tension 2 — Fix the 50 nullability drifts?**
*Systems Architect:* they are real divergence between the ORM and the documented chain; a restore gets a schema that accepts rows the application believes impossible. *Verification Marshal:* every one has a Python-side default, so the application never emits NULL; fixing 50 columns is 50 migrations of churn for no behaviour change, and a 50-row failure wall is precisely how a gate gets commented out.
**Resolution:** do not fix. Document the test's scope instead. Recorded as a measurement that argued against work.

**Tension 3 — Does Sprint 738 need the Neon connection string?**
*Systems Architect:* yes — a migration creating a table production already has will fail the deploy, and you cannot know production's state without reading it. *Scout:* you can. Production was built by `create_all()` from `Base.metadata`, so it has everything the ORM declares; the only genuine unknown is the two tables in §6 item 1, and one query answers it. Sprint 741d already proved its "needs a database" step did not.
**Resolution:** reclassify Sprint 738 as unblocked, with the one verification query as its first step. This is a change to a recorded blocker and is flagged for CEO confirmation rather than assumed.

**Tension 4 — Should `verification_matches` be fixed or deleted?**
*AccountingExpertAuditor:* a DuPont decomposition is a standard analytical-review exhibit; fix it and ship it. *Critic:* it has never been reachable, nobody has asked for it in seven months, and the user guide promising it is the actual defect.
**Resolution:** not adjudicated — it is a product call. Filed as Sprint 798 with both options costed; the documentation correction is required either way and is split out so it is not blocked by the decision.

---

## 8) Positive Developments

These are recorded because knowing which controls are trustworthy is what stops the next reviewer re-deriving it.

- **`guards/enum_label_drift.py` is honest.** Re-checked independently: 45 migrations replayed in revision order, 26 of 26 types parsed, 19 drifting against 19 known. It reports what it cannot parse. The PR #191 review's `CREATE TYPE` fix held.
- **`briefing_compiler.py` has the three-outcome shape.** A missing agent is red and emits `DID_NOT_RUN`. This is the pattern Sprint 794's lesson asks for, already shipped.
- **`qa_warden`'s Sprint 712 false-green guard works** — a parse-free non-zero exit escalates rather than recording 0 passed / 0 failed as green.
- **`lint_design_tokens.py` is the best-built guard in the repo** — real-tree scan, empty allowlist asserted as a property, findings pinned by path, line, and matched text (the Sprint 782a lesson, applied).
- **The slowapi stale-claim class is fully closed.** Grepping the *claim* vocabulary — "unmaintained", "last release", "abandoned" — across the whole repo returns only the corrections and the lessons that record them. Zero survivors.
- **Sprint 789's entitlement instance stays closed.** Zero route-local tier comparisons; 79 of 84 export routes gated by the canonical dependency, the other 5 gated in-body.
- **Zero-Storage is genuinely sound at the code level**, and the customer-facing compliance document is the accurate one.
- **`PRE_EXISTING_DRIFT_TABLES` / `_COLUMNS` have not rotted** — still exactly 4 and 6, matching an independent measurement. A hand-maintained list that is still correct after a year is worth noting as much as one that is not.

---

## 9) Recommended Next Steps

Ranked by what breaks for a paying customer or an auditor relying on an output.

| Rank | Finding | Sprint | Why here |
|---|---|---|---|
| 1 | F-001 depreciation `macrs_system` ignored | 795 | A wrong tax number, selectable from a shipped dropdown, carried into a filing |
| 2 | F-002 loan schedule / unbalanced JE | 796 | A CPA rejects an amortization schedule that does not foot; an unbalanced JE is unusable |
| 3 | F-003 no correct build path | 797 | A restore or new environment silently lacks billing idempotency and the admin audit trail |
| 4 | F-004 monetary gate inspects 0% | 799 | The control that exists to catch #1 and #2's class is measured at zero |
| 5 | F-007 DuPont claim + flag | 798 | A user-guide promise with no product behind it; surfaces during a demo |
| 6 | F-005 / F-006 enforcement gaps | 800 | Tests and gates that cannot fail or cannot block |
| 7 | F-008 / F-009 / F-014 stale claims | 801 | Ranked by who reads them under pressure |
| 8 | F-010 / F-011 / F-012 / F-013 | 802 | Hygiene; each is cheap and none is urgent |

**First action, before any sprint:** run the one query in §6 item 1. It costs a minute and decides whether F-003 is a rebuild hazard (as written) or a live production incident.

---

*Review conducted 2026-10-22 against `103ce557`. Review-only — no production code was modified. Four temporary injections were made to regression-prove the Accounting Policy Gate and reverted immediately; `git diff` was confirmed empty after each. All probe scripts were written to the session scratchpad, not the repository.*
