# Sprints 762–788 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-21.

---

### Sprint 784: Tool-count cohesion sweep — 12 → 18
**Status:** COMPLETE.
**Priority:** P2 — one instance was public-facing; the rest internal cohesion.
**Source:** `reports/next-actions-2026-10-20.md` B-e. Supersedes the narrower copy question raised as `reports/launch-readiness-assessment-2026-10-19.md` §I item 4.

`backend/tools_registry.py` is the canonical catalog at **18** tools (Sprint 689 expanded 12 → 18; Sprint 717 reconciled the frontend ledger). The prose did not follow. `tests/test_catalog_consistency.py` guards the registry against the frontend ledger — it does not read documentation, so none of this was caught.

**Confirmed stale surfaces:**
- `backend/main.py:243` — FastAPI `description="12-Tool Audit Intelligence Suite for Financial Professionals"`. **This is public**: it renders in the OpenAPI schema and on the docs page.
- `AGENTS.md:5` — "a 12-tool zero-storage AI audit intelligence SaaS". The agent entry point, so every session starts from a wrong number.
- `docs/01-product/PRODUCT_VISION.md` — 6 occurrences including the executive-summary hero line and the footer.
- `docs/02-technical/ARCHITECTURE.md:13` and `:178`.
- `docs/07-user-facing/USER_GUIDE.md` — "Twelve specialized tools".
- `tasks/ceo-actions.md` Phase 3 — the validation checklist the CEO is meant to work through lists 12 tools with their old test counts.

**Out of scope:** `COHESION_REMEDIATION.md` and `tasks/archive/**` are historical records of the 12-tool era and keep their numbers. `CLAUDE.md`'s era table line for Sprints 255–278 is also historical and correct as written.

**Verification:** extend the documentation-consistency gate so a prose tool count that disagrees with `tools_registry.MARKETING_AUDIT_TOOL_COUNT` fails CI. **Use that name** — it is the backend constant (`tools_registry.py:248`, computed from the `is_marketing_audit_tool` flag). `CANONICAL_TOOL_COUNT` is the *frontend* ledger's literal (`tool-ledger.ts:221`), already tied to the backend value by `tests/test_catalog_consistency.py`; a backend gate importing it would fail. Without the guard this recurs — exactly as the AS 1215 citation did after being fixed in code (Sprint 779 item 3).

#### What landed

**The public surface.** `backend/main.py:243` now reads `18-Tool Audit Intelligence Suite`, and
`scripts/openapi-snapshot.json` was regenerated in the same change (the OpenAPI Schema Drift Check gate
compares against it; `check_openapi_drift.py` reports no drift, paths 220 / schemas 422 unchanged).

**Prose counts** in `AGENTS.md`, `README.md` (hero line + feature bullet), `docs/01-product/PRODUCT_VISION.md`
(5 sites), `docs/02-technical/ARCHITECTURE.md` (5 sites) and `docs/07-user-facing/USER_GUIDE.md` (3 sites).

**Two prose *lists*, not just counts — wider than the brief anticipated.** `PRODUCT_VISION.md`'s feature table
and `README.md`'s feature bullet each enumerated twelve tools, and the table's per-tool test counts had drifted
independently of the registry: **AP 13→14, Payroll 11→13, Revenue 16→18, AR 11→12, Fixed Assets 9→11,
Inventory 9→10.** Both now mirror `tools_registry.py` — display names, test counts, standards and summaries all
derived from it. Also corrected the JE row, which cited only AS 2315 (Audit Sampling) where the fraud standard
is AS 2401; it now cites both, with AS 2315 scoped to the sampling aspect.

**Ordinals dropped from `ARCHITECTURE.md`.** Its directory tree and route table labelled tools "Tool 1" …
"Tool 11" — an ordering the registry does not guarantee and which has to be renumbered on every catalog
change. Both lists now carry names in registry order, expanded to the real 23 tool routes (18 audit tools +
Multi-Currency side-car + composite-risk, account-risk-heatmap, depreciation, loan-amortization). This also
fixed a wrong route: the doc claimed `/tools/fixed-asset-testing`; the directory is `fixed-assets`.

**Stale frontend comments** in `demo/page.tsx`, `(marketing)/page.tsx`, `ToolShowcase.tsx` (×2) and
`ToolSlideshow.tsx` said "12-tool" while the components render from `TOOL_LEDGER` (18). Comments now point at
the ledger instead of carrying a literal.

**Historical records deliberately left alone:** `COHESION_REMEDIATION.md`, `docs/archive/**`,
`tasks/archive/**`, `CLAUDE.md`'s era table, and every revision-history row. Each describes what was true at a
past version.

#### The guard

`backend/guards/doc_consistency_guard.py` gained a fourth rule, `tool_count_consistency`, parsing
`tools_registry.py` as text (the guard is stdlib-only and runs without project deps) and counting
`is_marketing_audit_tool=True` — i.e. it mirrors `MARKETING_AUDIT_TOOL_COUNT` rather than trusting a literal.

**Two things the first draft got wrong, both caught by running it:**

1. **13 false positives out of 14.** The patterns were too loose: every markdown TOC anchor of the form
   `](#5-tool-3-journal-entry-testing)` matched "5-tool", and a true subset statement ("six tools are shown
   inline") matched a bare count. Now link targets and inline code are stripped first, and only three narrow
   catalog-claim forms match — `N-tool` compound adjective, `all N tools`, and `N {audit|diagnostic|specialized|testing} tools`.
2. **It did not guard the one surface that matters most.** Regression-proving it by reverting `main.py` to
   "12-Tool" left the guard **green** — it covered documentation only. A `_check_api_description` rule now
   covers the FastAPI description and its failure message names the snapshot that must be regenerated with it.
   Guarding the docs but not the shipped API string would have protected the least important copy and missed
   the public one.

Escape hatch for genuine history: `<!-- doc-consistency: historical -->` on the line.

#### Verification

- Guard: `ALL CHECKS PASSED`. **Regression-proved twice** — reverting `main.py` and reverting a
  `PRODUCT_VISION.md` line each produced exactly one violation naming the file and line, then restored.
- `tests/test_doc_consistency_guard.py`: **35 passed** (was 21). The 14 new tests pin both the true positives
  and every false-positive class above, plus a test asserting the text parser agrees with
  `tools_registry.MARKETING_AUDIT_TOOL_COUNT` — so the two can never disagree silently.
- `tests/test_catalog_consistency.py` + `tests/test_citation_consistency.py`: 50 passed.
- `check_openapi_drift.py`: no drift. `npx tsc --noEmit`: exit 0. `ruff check backend/guards/`: clean.

#### Scope correction (PR #174 review) — the enum is necessary, not sufficient

The sprint said a run of any of the six tools "could not be recorded against an engagement
at all". True, and the enum was a hard blocker. But **the enum alone does not make them
trackable**, and the review caught me implying it did.

None of `routes/sod.py`, `intercompany_elimination.py`, `w2_reconciliation.py`,
`form_1099.py`, `book_to_tax.py` or `cash_flow_projector.py` calls
`maybe_record_tool_run` — and none of them even accepts an `engagement_id`
parameter (`sod.py` has no `db: Session` dependency either). Compare `ar_aging.py`,
`bank_reconciliation.py`, `multi_period.py`, `sampling.py`, `three_way_match.py` and
`audit_flux.py`, which all do.

So what Sprint 787 delivered is the **precondition**: the enum, the migration, the label
tables and the taxonomy classification, so that a recorded run *can* exist and the catalog
counts are honest. Wiring the fourteen endpoints is **Sprint 787b** — it changes API
signatures across six routes and needs a per-tool decision about what a composite score
means for a role matrix or a cash projection, which is design work rather than a fix.

#### Two further migration findings from the same review

**My migration's labels were wrong.** `d8b945d0b4e5` added lowercase slugs
(`sod_checker`, …) copied from `tools_registry`. `ToolRun.tool_name` is `Enum(ToolName)`
with no `values_callable`, so SQLAlchemy binds the **member name** — it sends
`SOD_CHECKER`. The baseline migration gets this right
(`sa.Enum('TRIAL_BALANCE', 'MULTI_PERIOD', …)`); I copied the wrong list. Corrected to
member names.

**The coverage fraction counted 19 against 18.** Changing the denominator to
`MARKETING_AUDIT_TOOL_COUNT` while leaving the numerator over every `ToolName` member meant
an engagement that ran every catalog tool plus flux analysis would print "Tools Executed:
19 of 18", and the not-executed coverage penalty counted a tool the sentence does not
describe. Both sides are now scoped to `CATALOG_TOOL_SLUGS`; non-catalog runs still appear
in "Total Tool Runs".

#### Three gaps this sweep uncovered — filed, not silently fixed

Each is a product gap rather than a copy fix, so none belongs in a cohesion sprint: **787** (engagement layer
tracks 13 of 18 tools), **788** (nav bar lists 12 of 18), **784b** (user guide documents 12 of 18).



---

### Sprint 787: Engagement layer tracks 13 of 18 tools
**Status:** COMPLETE.
**Priority:** P1 — one symptom was customer-visible in a shipped PDF.
**Source:** Sprint 784 discovery, 2026-10-20.

`ToolName` in `backend/engagement_model.py` has **13 members** — the original 12 tools plus `flux_analysis`.
Sprint 689 expanded the catalog to 18 and Sprint 717 reconciled the frontend ledger, but this enum was never
touched. Consequences:

- **Customer-visible:** `anomaly_summary_generator.py:329` renders `Tools Executed: {n} of {len(ToolName)}
  available tools` — so the Anomaly Summary PDF tells a practitioner there are **13** available tools while
  every marketing surface, the pricing page and now the API description say 18.
- `workpaper_index_generator.TOOL_LABELS` likewise has 13 entries, so the six newer tools cannot appear in a
  workpaper index.
- Engagement tool-run tracking, the completion gate and the diagnostic package ZIP are all keyed on
  `ToolName`, so a run of any Sprint-689 tool cannot be recorded against an engagement at all.

**Scope:** expand the enum, add the Alembic migration for the Postgres enum type (check how
`tool_runs.tool_name` is stored first — a native enum needs `ALTER TYPE`, a varchar does not), extend
`TOOL_LABELS`, and replace `len(ToolName)` with the registry count so the count has one source. Verify the
Anomaly Summary PDF and workpaper index both render the full catalog.

**Note:** `flux_analysis` is in this enum but is not one of the 18 marketing tools, so `len(ToolName)` was
never the right denominator even at 12 tools. Use `tools_registry.MARKETING_AUDIT_TOOL_COUNT`.

#### What landed

**The enum.** Six members added to `ToolName`, values matching `tools_registry.py` slugs
because `shared/tool_run_recorder.py` constructs `ToolName(slug)` from the route. Plus the
Alembic migration (`d8b945d0b4e5`) adding those values to the Postgres `toolname` type —
PostgreSQL rejects an unlisted enum value on insert while SQLite accepts anything, so
without the migration every local and CI test would pass and production would fail.

**The customer-visible count.** Three strings in the anomaly summary read
`len(ToolName)` and now read `tools_registry.MARKETING_AUDIT_TOOL_COUNT`.

Worth being precise about why `len(ToolName)` was *never* correct, not merely stale: the
enum includes `flux_analysis`, which is not one of the 18 sold tools. It counts **trackable
run types**, a different quantity from **tools a customer buys**. At 12 catalog tools it
would have printed 13; at 18 it printed 13 as well, for a different reason.

**Label and reference tables** extended for all six: `TOOL_LABELS`,
`TOOL_LEAD_SHEET_REFS`, `TOOL_CROSS_REFERENCES`, `TOOL_DISPLAY_LABELS`. A missing entry
degrades silently to a raw slug in a filed workpaper.

**Stale per-tool ranges in the same tables, fixed while there:** `JE-1 through JE-18` → 19,
`AP-1 through AP-13` → 14, `PR-1 through PR-11` → 13, `RT-1 through RT-12` → 18,
`AR-1 through AR-11` → 12, `FA-1 through FA-9` → 11, `IN-1 through IN-9` → 10. These print
in the workpaper index a practitioner files, so a short range understates work performed.

#### The convergence taxonomy — a real decision, not a formality

The full suite surfaced that `domain_config/tool_taxonomy.py` classifies every tool as
convergence-capable or convergence-excluded, and six were unclassified. An unclassified tool
drops out of the Convergence Index silently rather than raising.

The rule turned out to be mechanical: **`CONVERGENCE_TOOLS` is exactly the key set of
`shared/account_extractors.ACCOUNT_EXTRACTORS`.** A tool can contribute to convergence only
if something can pull GL account identifiers out of its result. None of the six has an
extractor, and none produces GL-account-level output — role matrices, vendor thresholds,
entity balances, forward projections — so all six are excluded. Intercompany Elimination is
the one plausible future candidate, but that needs an extractor written; classification
cannot substitute for one. That equivalence is now asserted rather than maintained by hand.

#### Five stale literals that were *defending* the drift

`assert len(ToolName) == 13` existed in **four** test files — `test_ar_aging`,
`test_engagement`, `test_fixed_asset_testing`, `test_inventory_testing` — plus
`len(CONVERGENCE_EXCLUDED) == 6` in `test_convergence`.

These did not merely fail to catch the Sprint 689 drift. They **defended** it: the correct
enum expansion turns all five red, so whoever attempted it saw failing tests and had reason
to conclude the expansion was wrong. That is the most likely explanation for why a six-month
gap in a core enum went unfixed. All five now derive from the registry.

#### The guard

`tests/test_toolname_catalog_parity.py` — 12 tests closing the third edge of a triangle
whose other two edges already existed. `test_catalog_consistency.py` ties the registry to the
frontend ledger; nothing tied either to `ToolName`. It asserts: every catalog tool is
trackable; every enum member is a catalog tool or a declared non-catalog exception; the
taxonomy covers the enum; `CONVERGENCE_TOOLS` equals the extractor key set; every label table
is complete; workpaper references are unique; **a Python enum member added without an
`ALTER TYPE` migration fails here** rather than in production; and no test may hardcode a
`len(ToolName)` literal again.

That last detector was wrong on its first draft — it flagged four lines, all false: three of
my own docstrings *quoting* the old assertion to explain its removal, and one
`assert len(not_started) == len(ToolName) - 2`, which is the correct derived form. Substring
matching again. Now a regex requiring an actual `assert` against a numeric literal,
regression-proved by re-introducing the real thing.

#### Verification

- Full backend suite **8,728 passed / 0 failed** on an untouched tree.
- **Recovery note.** The parity test was briefly committed to the wrong branch. An early
  `git stash push` omitted `-u`, so the then-untracked `test_toolname_catalog_parity.py`
  followed me across two branch switches and was swept into Sprint 780's coupon-fix commit
  by a `git add -A backend/tests`. Caught while rebasing: Sprint 787's own PR did not
  contain its headline test. Moved back, 12/12 passing here. **A stash without `-u` is not
  a clean tree** — new files stay behind and get attributed to whatever is committed next.
- `ruff check` and `ruff format` clean under `backend/ruff.toml`.
- `alembic heads` reports a single head (`d8b945d0b4e5`); the models/migration parity test
  passes.
- Note: `ruff format` also collapsed two unrelated dict literals in `test_convergence.py`
  that had been formatted at a narrower width — the pre-commit hook would have done the same.

#### Not in scope

Writing an account extractor for Intercompany Elimination, which would move it into
`CONVERGENCE_TOOLS`. That is a feature with its own design question (which balances count as
GL accounts in a consolidation), not part of a catalog reconciliation.


---

### Sprint 788: Tool navigation bar lists 12 of 18 tools
**Status:** COMPLETE — **but filed against the wrong file.** See the correction below.
**Priority:** P2 — the tools were reachable elsewhere, just not from the bar on every tool page.
**Source:** Sprint 784 discovery, 2026-10-20.

`frontend/src/components/shared/ToolNav.tsx` hardcodes a 12-entry `TOOLS` array and a 12-member `ToolKey`
union. The six Sprint-689 tools (Segregation of Duties, Intercompany Elimination, W-2/W-3, Form 1099,
Book-to-Tax, Cash Flow Projector) are absent.

They are **not** unreachable — `app/tools/page.tsx` (23 routes), `lib/commandRegistry.ts` (21 routes),
`content/tool-ledger.ts` (18) and `ToolShowcase.tsx` all include them. But a practitioner working inside one
tool sees a bar that silently omits a third of what they are paying for.

**Scope:** drive `TOOLS` from `tool-ledger.ts` instead of a second hardcoded list — that is what makes this
stay fixed, since `test_catalog_consistency.py` already ties the ledger to the registry. Decide the overflow
treatment: `INLINE_COUNT = 6` leaves twelve items in the More dropdown, which likely wants grouping
(diagnostics / testing / tax & controls) rather than a flat list.

#### Correction: this sprint named a dead component

As filed, the sprint targeted `frontend/src/components/shared/ToolNav.tsx`. **That component
was replaced by `AuthenticatedShell` in Sprint 475** and was referenced only by its own test
file — it rendered on no page at all. Its hardcoded 12-tool list is exactly what produced the
wrong filing: I read the list, correctly concluded that six tools were missing from tool
navigation, and incorrectly concluded that this was the file responsible.

The live surface is `UnifiedToolbar` → `MegaDropdown` → `TOOL_COLUMNS` in
`UnifiedToolbar/toolbarConfig.ts`. The defect was real there: twelve audit tools plus Flux and
Reconciliation Intel, with all six Sprint-689 tools absent from every column.

#### What landed

**A fourth column.** `TOOL_COLUMNS` gained **Tax & Filings** (W-2/W-3, Form 1099, Book-to-Tax),
Segregation of Duties joined **Testing Suite** as controls testing, and Intercompany
Elimination + Cash Flow Projector joined **Advanced**. Grouping follows what each tool does,
not where there was room.

**The grid is derived, not hardcoded.** `MegaDropdown` had `grid-cols-4` — three tool columns
plus Account — so adding a column would have silently overflowed the row. It now computes
`repeat(TOOL_COLUMNS.length + 1, minmax(0, 1fr))`, and the panel widened 64rem → 76rem to
carry the fifth column.

**Two `toolKey` values corrected.** `journal_entry` → `journal_entry_testing` and
`fixed_assets` → `fixed_asset_testing`. The field's own comment promises it matches backend
entitlement names; both were wrong. It is currently vestigial — `MegaDropdown` renders only
`label` and `href` — so this fixes nothing today and prevents a future gating change from
inheriting two wrong keys.

**Dead `ToolNav` deleted** along with its test, its re-export from `components/shared/index.ts`,
and two docblocks in `lib/commandRegistry.ts` that still described it as the model for tool
commands. Dead code carrying a stale copy of real data is worse than dead code: it reads as
authoritative, and it misdirected this sprint's own filing.

#### The guard

Four tests in `__tests__/MegaDropdown.test.tsx` close the last open edge of the catalog chain:

- every tool in `TOOL_LEDGER` appears in the navigation;
- the navigation offers no tool outside the ledger, except two explicitly named non-ledger
  destinations (`/flux`, `/recon`) — so an href typo cannot pass as an intentional extra;
- each tool appears exactly once across all columns;
- `toolKey` matches the ledger id for every ledger-backed item.

`backend/tests/test_catalog_consistency.py` already tied the registry to the ledger, so the
chain is now **registry → ledger → navigation**, closed end to end. Regression-proved by
removing Book-to-Tax from the nav: the coverage test failed naming it, then passed on restore.

#### Verification

- Frontend suite **206 suites / 2,010 tests, 0 failures** (was 207/2,013 — `ToolNav`'s 7 tests
  removed, 4 added to MegaDropdown).
- `npx tsc --noEmit` exit 0. `npm run build` clean, every app route still `ƒ (Dynamic)` with
  `ƒ Proxy (Middleware)` active, so the nonce-based CSP contract is intact.
- **Not verified in a browser.** The five-column layout is checked by test and by arithmetic —
  the longest label is 24 characters at `text-sm` in a ~219px column — but the toolbar lives
  behind authentication and I did not render it. The derived grid means a future column cannot
  overflow silently; column *width* at five columns is the part that rests on that arithmetic.


---

### Sprint 785: Dispose of the PR backlog
**Status:** COMPLETE.
**Priority:** P2 — seven finished sprints were rotting on branches, and every day on `main` widened the conflict.
**Source:** `reports/next-actions-2026-10-20.md` B-a / B-b.

`SESSION_STATE.md` recorded on 2026-10-19 that all 25 open PRs were `MERGEABLE` and that the only thing blocking them was six red CVE gates. The gates were fixed that day — but the 2026-10-19/20 merges then rewrote `tasks/todo.md` wholesale, and **all nine real-work PRs reported `DIRTY` / `CONFLICTING`**: #134, #137, #138, #139, #140, #141, #142, #143, #144.

**Stranded work (all nine recovered):** Sprint 769 (context memoization), 771a (Button primitive), 772a (lazy Recharts + command palette), 773 (type disambiguation + dead code), 773b (React.memo subtrees), 773c (perf finishers), 762 (flux_expectations memo contract test, closing 17/18 → 18/18), #134 (ADR-018 shim awareness in lint/policy scripts) and #144 (the 2026-04-30 + 2026-05-01 nightly briefs, plus a `tmp_report` cleanup).

**What the rebase actually found — the conflicts were not where the filing predicted.** Every one of the nine branches rebased onto current `main` with **zero code conflicts**. Eight of nine conflicted only in `tasks/todo.md`, and in every case at the same end-of-file append point; the ninth (#144) also conflicted in `reports/nightly/.baseline.json`. Git even merged Sprints 773 and 773b cleanly against each other despite both editing `tools/account-risk-heatmap/page.tsx` and `tools/composite-risk/page.tsx`. The `DIRTY` status GitHub reported was an artifact of merge-commit simulation against a ledger file, not a signal about the code.

**Delivery shape, and why it is one PR rather than nine.** Branch protection on `main` has `required_status_checks.strict = true`, so each branch must be up to date with `main` before it can merge — landing nine PRs serially means nine full ~20-minute CI matrices where eight of them re-verify an already-verified tree. All nine commits were therefore replayed onto one branch and landed with **`gh pr merge --rebase`**, which preserves each original commit, message, author and date on `main` individually (linear history is required, and rebase satisfies it). This is not the "cherry-pick or re-do from the diff" the sprint warned against: the warning was about reconstructing work from a branch-tip diff, which for these pre-dormancy branches reads as ~125k spurious deletions. A cherry-pick replays the commit's own diff against its own parent — bit-identical to what rebasing each branch produces. Proof: the integrated tree was diffed against a separately-built integration branch and matched byte-for-byte outside `tasks/todo.md`.

**Ledger conflict resolutions:**
- `tasks/todo.md` — resolved as a union in all eight cases. Each branch appended a distinct sprint record; nothing was overwritten. `PR #TBD` in the #134 hotfix line was resolved to `PR #134`, which made the branch's follow-up commit `1df22a3f` a no-op (skipped).
- `reports/nightly/.baseline.json` (#144) — `main` wins outright. The branch carried the 2026-05-01 snapshot (8,685 backend / 2,013 frontend / 93.33%); `main` already carries 2026-10-21 (8,818 / 2,010 / 93.5%). The two daily briefs, twelve sentinel JSONs, two run_logs and the `tmp_report.py` removal all landed; only the stale baseline was dropped, and the hotfix-log entry records that.

**Dependabot triage — all 15 closed as superseded** (#77, #78, #90, #106–#114, #156, #157, #158), on two distinct grounds:
- **The nine pip PRs (#106–#114, #157) are churn by construction.** Every package they touch is pinned with a `>=` floor, and Sprint 777's rule says floors self-heal: CI and the production Docker build both run a fresh `pip install -r requirements.txt` and already resolve past these targets. Raising a floor from `>=5.0.0` to `>=7.4.0` changes what *a fresh resolve is allowed to pick*, not what it picks. Nothing ships differently.
- **The four GitHub Actions PRs (#77, #78, #90, #156) are real work that these PRs cannot do.** Action pins do *not* self-heal — the workflows pin by commit SHA, which is correct practice. But every one of the four targets a version that is itself now stale: `checkout` 7.0.0 against 7.0.1 available, `setup-node` 6.4.0 against **7.1.0**, `upload-artifact` 7.0.1 against 7.0.2, `github-script` 9.0.0 against 9.0.0. Merging a six-month-old bump would land a second-stalest version and burn a CI matrix doing it. Filed as **Sprint 786c** with current SHAs instead.
- #158 (npm minor-and-patch group, 15 updates) is superseded by the 2026-10-19 `npm audit fix` sweep, which moved production vulnerabilities 22 → 0 inside the existing semver ranges.

**Verification:**
- Nine commits replayed; integrated tree byte-identical to an independently-built integration branch outside `tasks/todo.md`.
- `npx tsc --noEmit` → exit 0.
- `npx jest --watch=false` → **206 suites / 2,009 tests / 5 snapshots, 0 failures.** `main` measures 2,010 on the same command. The **−1 is expected and accounted for**: Sprint 773 deletes the `DISTANCE` map and with it `motionTokens.test.ts`'s single `it('has inlined distance values')` case. Sprint 772a adds a `jest.mock` for the direct `BenfordChart` path (the `next/dynamic` import bypasses the barrel mock) but no new test case. No other count change — the sprint's "still reports 2,013" bar was written against the pre-rebase number and the correct restatement is 2,010 → 2,009 by exactly one deliberate deletion.
- `npm run build` → clean; every route still `ƒ (Dynamic)` with `ƒ Proxy (Middleware)` active, so the nonce-based CSP contract is intact.
- `pytest tests/test_accounting_policy_guard.py tests/test_export_pdf_contract.py` → **42 passed** (the two backend-touching commits: #134's guard default and #142's 18/18 memo contract).
- Open non-Dependabot PR count after the sweep: **0**. Open Dependabot PR count: **0**.

**Found and fixed in passing — `scripts/archive_sprints.sh` silently destroyed three sprint records.**

The protocol-mandated archiver ran at the end of this sprint (13 completed sprints in Active Phase against a threshold of 5). It reported archiving 13 and wrote 10. Sprints **769, 771a and 772a** were deleted from `tasks/todo.md` and never written to the archive file — gone from the tree entirely, recoverable only because the run was diffed before committing.

The script makes three passes over the Active Phase. The **counting** pass and the **removal** pass both handle a `### Sprint` heading arriving while another sprint block is open — counting calls `emit_if_complete()` before resetting, removal flushes the open block before resetting. The **extraction** pass did not:

```awk
/^### Sprint [0-9]+/ { in_sprint = 1; block = $0 "
"; next }   # <- discards the open block
in_sprint && /^### |^---$/ {
  if (block ~ COMPLETE) printf ...
  if (/^### Sprint [0-9]+/) { block = $0 "
" }                 # <- unreachable: rule 1 wins
  ...
}
```

awk evaluates rules in order, so rule 1 always fires first on a sprint heading and overwrites `block` without emitting it. The `if (/^### Sprint/)` branch inside rule 2 had never once executed. A completed sprint was archived **only** if its block happened to be terminated by a `---` line before the next heading — and removal deleted it either way. Counting and extraction disagreeing is precisely the condition under which work is lost, and nothing checked for it.

The trigger here was self-inflicted: the eight `tasks/todo.md` union resolutions above dropped the `---` separators between consecutive appended sprint blocks, which is what put four blocks back-to-back. The separators were restored. But the latent bug is older than this sprint and would have fired on any hand-edited `todo.md` with the same shape.

**Fixed in `scripts/archive_sprints.sh`:**
- Extraction rewritten around the same `emit_if_complete()` helper the counting pass already used, so a block is emitted before it is discarded. The dead branch is gone.
- An **integrity gate** added between extraction and removal: if the number of `### Sprint` sections written to the archive does not equal the number the counting pass found, the script prints both counts and exits 1 **before `todo.md` is touched**. Losing a record now requires the two passes to agree on a wrong number, not merely to disagree.
- The two passes' "is this complete?" predicates were also inconsistent — extraction accepted `— COMPLETE` or `**Status:** COMPLETE`, removal accepted only the latter. A heading-style completion would have been archived *and* kept, duplicating it. Both now use the same predicate.

Re-run after the fix: `13 sprint sections, matches count`; 13 archived + 12 remaining = 25, the pre-archival heading count.

**Commit SHA:** filled at merge.


---

### Sprint 762: flux_expectations memo PDF contract test (close 17/18 → 18/18)
**Status:** COMPLETE — landed 2026-10-21 via Sprint 785's backlog sweep (was PR #142, stranded since 2026-05-01).
**Priority:** P3.
**Source:** Post-Sprint-754b memo contract test sweep (commit `60946271`). 17/18 memos covered; flux_expectations skipped because its dataclass nests `FluxExpectationLine` Pydantic sub-models that need a non-trivial fixture.

**What landed:**
- `backend/tests/test_export_pdf_contract.py::test_flux_expectations_memo_pdf_contains_all_required_section_labels` — single test mirroring the established memo-contract pattern, plus inline `_FLUX_EXPECTATIONS_FLUX_FIXTURE` and `_FLUX_EXPECTATIONS_EXPECTATIONS_FIXTURE` and a `FLUX_EXPECTATIONS_MEMO_REQUIRED_SECTIONS` tuple covering ISA, Scope, Variance, Conclusion, Sign-Off, Disclaimer anchors.
- Discovery: `generate_flux_expectations_memo` accepts plain dicts for both inputs (the route's Pydantic input is unwrapped before the call), so the worry about nested-Pydantic fixtures was misplaced — the fixture is flat like every other memo. Comment in the test file updated to record this finding for future maintainers.
- Coverage banner updated from "Sprint 754b finishing pass: 17/18 memos" to "Sprint 762: 18/18 memos covered."

**Verification:**
- `python -m pytest tests/test_export_pdf_contract.py -v` — **19 passed, 0 failed** (18 contract tests + 1 smoke check; was 18, now +1 with flux_expectations).

**Out of scope:**
- Refactoring the memo generator — pure test addition.
- Adding contract tests for the 3 non-memo report PDFs (combined audit, financial statements, anomaly summary) — separate filing if needed.

**Commit SHA:** filled at commit time.


---

### Sprint 779: Boundary-language and citation residue (liability pass)
**Status:** COMPLETE.
**Priority:** P1 — pure liability reduction, no dependencies.
**Source:** `reports/launch-readiness-assessment-2026-10-19.md` B-1 and B-3.

The highest-consequence category of defect in this product is language that edges from *diagnostic indicator* toward *audit conclusion*, because that is the boundary the whole liability posture rests on. Three pieces of residue survive:

1. **`generate_sample_reports.py:2266`** still emits "systemic review of procure-to-pay controls recommended". The production memo generator was fixed; the sample generator was not — and it produces the sample output a prospect may well see first. Rephrase to match the shipped wording ("engagement team should evaluate whether procure-to-pay procedures warrant expansion").
2. **Risk-tier labels are unqualified.** Every testing memo auto-assigns low/elevated/moderate/high from flag density, and the label is visually prominent enough for a practitioner to read it as an ISA 315 risk-assessment conclusion. Append the qualifier the April audit asked for: "(automated flag density — auditor judgment required per ISA 315)".
3. **AS 1215 is still miscited as a JE Testing standard in three internal docs** — `docs/03-product/REPORT_STANDARDS_SPEC.md:440`, `docs/01-product/USER_PERSONAS.md:273`, `docs/02-technical/ARCHITECTURE.md:380`. Customer-facing surfaces are already correct and CI-guarded; this is the leftover. AS 1215 is *Audit Documentation*; the JE fraud standard is AS 2401. Ten-minute fix, worth doing because the customer-facing version of this exact error was ranked the single most dangerous finding in the system.

**Verification:** extend `test_memo_boundary_phrasing.py` to assert the sample generator is held to the same banned-phrase rules as the shipped generators — otherwise this recurs. Extend `test_citation_consistency.py` to cover `docs/` so the citation cannot drift back.

#### What landed

**1. Sample-report phrasing (`generate_sample_reports.py:2266`).** The root-cause clause is gone.

**Correction to this brief:** it instructed rephrasing to match "the shipped wording", quoted as
*"engagement team should evaluate whether procure-to-pay procedures warrant expansion"*. **That wording
exists nowhere in the codebase** — the brief described a fix that never landed. The shipped tier
commentary is `three_way_match_memo_generator.py:112` *"Below best practice — investigate patterns"*, and
`tests/test_twm_memo.py:166` asserts the shipped finding text carries no recommendation clause at all.
Aligned to what ships: *"Below 80% best practice threshold; investigate matching patterns (auditor
judgment required to determine cause)"*.

**2. Risk-tier qualifier — one constant, not eight edits.** `RISK_TIER_BASIS_NOTE` in `shared/memo_base.py`
reads *"Basis: automated flag density — auditor judgment required per ISA 315. The diagnostic tier is an
indicator, not a risk assessment or a conclusion on internal control."* It is **composed into
`RISK_SCALE_LEGEND`**, which is already rendered on every surface that prints a tier — the shared
`build_results_summary_section` path plus bank rec, engagement dashboard, multi-period, three-way match and
the TB diagnostic PDF. So surfaces added later inherit the qualifier without a code change.

`anomaly_summary_generator.py` was the one gap: it builds its label straight from `RISK_TIER_DISPLAY` and
never rendered the legend, so its §I summary line and its prominent §IV "ENGAGEMENT RISK INDICATOR" box
now render the note explicitly.

**3. AS 1215 → AS 2401 / ISA 240** in `docs/03-product/REPORT_STANDARDS_SPEC.md:440`,
`docs/01-product/USER_PERSONAS.md:273` and `docs/02-technical/ARCHITECTURE.md:380`. Matched to
`tools_registry.py`, whose canonical JE standards are `("ISA 240", "AS 2401", "Nigrini 2012")` — note the
docs also claimed ISA 530, which is sampling, not the fraud standard. Fixed an adjacent count drift in the
same line while there: JE is a 19-test battery, not 18.

#### The two guards, and what widening them found

**Boundary scan scope was the actual defect.** `test_memo_boundary_phrasing.py` has protected memo wording
since Sprint 721, and the pattern that catches this exact phrase (`\bsystemic\s+review.*recommended\b`)
was already in it. Nothing was missing from the rules — only from the file list, which was the glob
`backend/*_memo_generator.py`. Added `EXTRA_SCANNED_FILES`: the sample generator, anomaly summary,
engagement dashboard, and three shared text modules, with a test asserting every path in it still resolves
so a rename cannot silently drop coverage.

Widening surfaced nine more hits — **eight legitimate, one real**:
- Eight are ISA 265 *negative* use: "does not constitute an audit opinion", "classification … is a matter
  of auditor judgment", and the literal title of PCAOB AS 1305. Annotated `# allow-deny-phrase: <reason>`,
  matching the precedent at `analytical_expectation_memo_generator.py:58`.
- One was real: `shared/follow_up_procedures.py:153` told the auditor a misposting "requires correction" —
  a conclusion about the entity's records, in text reused across tools. Now "warrants further review".

**Scanner refinement:** the scan also fired on `anomaly_summary_generator.py`'s module docstring, where a
`GUARDRAIL` note names the ISA 265 sections the template deliberately refuses to produce. Naming them is
the point, and annotating it put a pseudo-comment inside docstring prose. `_scan_source` now skips the
module-docstring line range via `ast` — a module docstring is maintainer documentation and never reaches a
rendered PDF.

**Citation scan scope, same lesson.** `test_citation_consistency.py` covered customer-facing surfaces only,
which is exactly why Sprint 717's sweep held on all five of those and then drifted back in three internal
docs for six months. The AS-1215 adjacency check now runs over `DOC_SCANNED_GLOBS` as well. The
**registration** check deliberately stays customer-facing: internal docs legitimately cite unregistered
standards in post-mortems and lexicon examples, and failing on those would make the guard noisy enough to
get disabled.

#### Verification

- Both guards **regression-proved**: each defect re-introduced, the corresponding test confirmed to fail
  naming the offending file, then restored to green. 29/29 on the two guard suites.
- Targeted sweep over every memo / report / citation / boundary / PDF-contract suite: **1,197 passed**.
  The 18 memo PDF contract tests render through ReportLab, which is what validates the `<br/>` in the
  recomposed legend.
- Full backend suite green; `ruff check` clean, `ruff format` applied; `mypy` reports no new errors in the
  touched modules.
- No frontend files touched.


---

### Sprint 780: Stripe price-parity preflight + webhook coverage (money path)
**Status:** COMPLETE.
**Priority:** P1 — had to land before the first live charge. Independent of pricing decisions, so it was safe to build before Sprint 781 reports.
**Source:** `reports/launch-readiness-assessment-2026-10-19.md` §F and §C.

1. **Price-parity preflight.** `billing/price_config.py` holds the canonical amounts and `test_pricing_launch_validation.py` carries ~20 assertions — but they only check the table *against itself*. Nothing fetches the Stripe Price object to confirm the amount a customer is actually charged matches the amount the product intends and the page displays. Test mode is documented as still sitting at the previous price list, so displayed and charged price **already disagree** in the only environment where billing has ever run. Add a script that reads every `STRIPE_PRICE_*` and `STRIPE_SEAT_PRICE_*` env var, retrieves the Price object, and asserts `currency == "usd"` plus the correct expected amount, failing loudly and naming every mismatch. **Use the real constant names** — the canonical base amounts are `PRICE_TABLE[tier][interval]` (not `TIER_PRICES`, which does not exist), and the four seat amounts live separately in `PROFESSIONAL_SEAT_PRICE[interval]` and `ENTERPRISE_SEAT_PRICE[interval]`. All six base prices and all four seat prices must be covered; mapping only the base table would silently skip the seat add-ons the same requirement calls for. Wire it into the Phase 4.1 checklist ahead of the webhook preflight.
2. **Webhook handler coverage.** `billing/webhook_handler.py` is the least-covered critical path at **59.9% / 174 uncovered statements** — and it is the one that moves money. This is the webhook-coverage sprint deferred in Sprint 676 and again in the 2026-04-20 refactor pass. Target 85%+ on the handler, prioritising signature verification, event dedup (`processed_webhook_events`), and the subscription state transitions that drive entitlements.

**Out of scope:** building live-mode prices. That waits on pricing feedback from Sprint 781.

#### What landed

**1. `scripts/stripe_price_parity_preflight.py`** — the first thing in this codebase that
compares intent against Stripe. It imports `PRICE_TABLE`, `PROFESSIONAL_SEAT_PRICE` and
`ENTERPRISE_SEAT_PRICE` (never restates an amount), retrieves each Price object, and checks
six properties per price:

| Check | Why it is there |
|-------|-----------------|
| `unit_amount` equals the canonical cents | the v2-vs-v3 case: Solo at $50 against a $100 table |
| `currency == "usd"` | a non-USD price charges a plausible-looking wrong number |
| `recurring.interval` matches the env var | **a correct amount on the wrong cadence bills right once and wrong forever** |
| `active is not False` | an archived price fails checkout at the worst moment |
| `livemode` agrees with the key's mode | stops a live deployment wired to test prices |
| retrievable at all | an expired or wrong-account key is a cutover blocker |

Coverage is **all ten** price objects (6 base + 4 seat) plus both coupons. `--require-all`
turns unset IDs into a failure for use immediately before cutover. Exit codes separate
mismatch (1) from misconfiguration (2), and a mismatch outranks unset IDs so a real defect
is never masked.

**Two facts it surfaced on its first run** against `backend/.env`:
- The local test-mode secret key is **expired** (`AuthenticationError: Expired API Key`), so
  the abandoned test mode is doubly dead — it is at v2 prices *and* unreachable.
- Only 4 of 10 price IDs resolve locally, because `backend/.env` still carries the v2 names
  (`STRIPE_PRICE_TEAM_*`, `STRIPE_SEAT_PRICE_MONTHLY`) that `price_config.py` no longer
  reads. Running the preflight is now the cheapest way to detect that class of drift.

**2. Webhook handler coverage: 55% → 88%** on the billing-focused subset (target was 85%).
Five handlers and four helpers had **no** coverage at all; 43 new tests in
`tests/test_webhook_handler_coverage.py` cover `handle_subscription_created`,
`handle_invoice_payment_succeeded`, `handle_dispute_created`, `handle_dispute_closed`,
`handle_invoice_created`, `_downgrade_org_members_to_free`, `_apply_dpa_from_metadata`,
`_portal_url_for_user`.

The tests are written around money-relevant invariants rather than line coverage:
- **Entitlement state after every event** — status *and* `user.tier`, since those are two
  separate writes and only the pair is the entitlement.
- **Org blast radius.** A dispute or a lost dispute must downgrade every org member, not just
  the subscription owner; two tests assert colleagues lose access too.
- **Idempotency.** Stripe retries, so `invoice.payment_succeeded` on an already-ACTIVE
  subscription must record nothing, and `customer.subscription.created` arriving after
  `checkout.session.completed` must not double-count the creation in analytics.
- **Refusal to guess.** `customer.subscription.created` with an unresolvable tier aborts
  without syncing — better to do nothing than to sync a subscription to the wrong tier.
- **Dispute resolution is three paths, not two.** `won` restores, `lost` cancels, and
  anything else (e.g. `warning_closed`) must leave the subscription suspended rather than
  silently restoring access.

**A dead branch found while testing.** Both restore paths wrap `UserTier(sub.tier)` in
`except ValueError`, but that branch is **unreachable**: `Subscription.tier` is a constrained
DB enum, so a value outside `UserTier` cannot survive a round-trip (the Enum type raises on
*result processing*, before any handler reads it), and both handlers flush after the
conversion. Rather than contort a test to reach dead code, there is now one test pinning the
constraint that makes the defence redundant — it fails and names the cause if the
`subscription_tier` enum and `UserTier` ever diverge.

**Still uncovered** (deliberately, and recorded rather than left implicit):
`_auto_create_organization` internals (lines 40–67), branches inside
`handle_checkout_completed` (237–259) and `handle_subscription_updated` (305–377), and three
single lines in `trial_will_end`. Those paths are exercised end-to-end by the existing route
tests; the remaining gap is branch-level, and 88% already clears the sprint's bar.

#### Verification

- `tests/test_stripe_price_parity_preflight.py` — **25 tests**, every one driving a fake
  `stripe` module, so no network and no keys. Each failure mode is asserted independently,
  plus a test that the preflight's expectations equal `price_config`'s tables, so the two
  cannot drift apart.
- `tests/test_webhook_handler_coverage.py` — 43 tests.
- Full backend suite green; `ruff check` and `ruff format` clean under `backend/ruff.toml`.

#### Out of scope, unchanged

Building the live-mode products and prices. That still waits on Sprint 781 — there is no
point creating prices for a number no practising CPA has agreed to.


---

### Sprint 769: Frontend context memoization (render-perf hotfix)
**Status:** COMPLETE — landed on branch `sprint-769-frontend-context-memoization`.
**Priority:** P2. No user-visible bug, but cascade re-renders measurably affect interactive latency in tools mounted under DiagnosticProvider/EngagementProvider.
**Source:** Frontend efficiency audit (2026-05-01) findings 1.1 + 1.2.

`DiagnosticContext` and `EngagementContext` were building a fresh `value` object literal on every provider render. With `setResult` / `clearResult` also fresh closures, every consumer re-rendered whenever the provider's parent re-rendered, regardless of whether the carried state actually changed.

**What landed:**
- `DiagnosticContext.tsx` — `setResult` / `clearResult` wrapped in `useCallback([])`; provider `value` wrapped in `useMemo([result, isLoading, setResult, clearResult])`. (`setIsLoading` is the React-stable `useState` setter, omitted from deps per React semantics.)
- `EngagementContext.tsx` — `contextValue` wrapped in `useMemo` with the full 10-key dep array (5 state values + 5 already-memoized handlers).
- Inline rationale block added above the URL-sync `useEffect` (`EngagementContext.tsx:115`) documenting why `searchParams` / `selectEngagement` / `activeEngagement` are deliberately excluded from deps: including `searchParams` would loop because `selectEngagement`'s own `router.replace` rotates the value; `selectEngagement` itself re-creates whenever `searchParams` change (same loop); and `activeEngagement` is the load-bearing one-shot guard inside the body. The eslint-disable is intentional, not a stale-closure bug.

**Verification:**
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npx jest --watch=false --testPathPatterns="(Diagnostic|Engagement)"` → **52 passed, 0 failed** (7 suites). Pre-existing `act()` warnings on `EngagementBanner.tsx:35` are not regressions and originate from `useEffect`-triggered `setClientName` in test renders unrelated to Sprint 769's surface.
- `cd frontend && npm run build` → exit 0; all routes correctly dynamic (`ƒ`).

**Out of scope:**
- Splitting either context into state-vs-dispatch halves — bigger refactor, not warranted by current symptoms.
- Other render-perf findings (row mappings, table memoization, result-subtree wraps) — bundled in Sprint 773.

**Commit SHA:** see branch `sprint-769-frontend-context-memoization` (filled at PR merge).


---

### Sprint 771a: Button primitive (subset of Sprint 771)
**Status:** COMPLETE — landed on branch `sprint-771a-button-primitive`.
**Priority:** P3.
**Source:** Frontend efficiency audit (2026-05-01) finding 2.2.

Splitting Sprint 771 into 771a (Button primitive — this sprint) and 771b (the three Tool* primitives — `ToolHeroHeader` / `ToolLoadingState` / `ToolErrorState`, deferred to a follow-up). 771a is the lowest-risk, highest-leverage subset: ~30 hand-rolled `bg-sage-600 …` and `bg-surface-card border border-oatmeal-300 …` button class-string copies are the most common offender, and a centralized primitive removes that drift point ahead of the hero/loading/error rollup.

**What landed:**
- `frontend/src/components/ui/Button.tsx` (new, ~60 lines) — `forwardRef` button with `variant: 'primary' | 'secondary' | 'ghost'` and `size: 'sm' | 'md' | 'lg'`. Single base class string covers font, transition, disabled state, focus ring; variant/size class maps compose on top. Inline doc-comment explains each variant's intended use (primary = page-commit action, secondary = tertiary alongside primary, ghost = inline toolbar).
- 5 tool pages migrated from inline class strings to `<Button>`:
  - `app/tools/ap-testing/page.tsx`
  - `app/tools/fixed-assets/page.tsx`
  - `app/tools/inventory-testing/page.tsx`
  - `app/tools/payroll-testing/page.tsx`
  - `app/tools/revenue-testing/page.tsx`
- Each of the 5 pages had the same 4-button shape: 1 secondary "Try Again" in the error state + 3 buttons in the success-state action bar (primary "Download Testing Memo", secondary "Export Flagged CSV", secondary "New Test"). 20 total buttons replaced.

**What did NOT change (deferred):**
- AR aging (`px-8 py-3 rounded-xl` "Run AR Aging Analysis" hero CTA) — different size variant; needs `size="lg"` migration in 771b alongside the dual-FileDropZone landing of Sprint 770.
- Statistical sampling — its primary button differs slightly (no `disabled:opacity-50` suffix); migrate alongside 771b.
- `account-risk-heatmap`, `composite-risk` — buttons embedded in row-editor mini-components flagged for `React.memo` extraction in Sprint 773 follow-up; migrate when those subtrees are touched.
- `ToolSettingsDrawer` — full-width primary button; migrate alongside 771b.
- The other Sprint 771 primitives (ToolHeroHeader, ToolLoadingState, ToolErrorState) — deferred to 771b.

**Verification:**
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npx jest --watch=false` → see commit-message tail.
- `cd frontend && npm run build` → see commit-message tail.

**Out of scope:**
- ESLint rule banning the inline class strings the new primitive replaces — useful future fence, not this sprint.

**Commit SHA:** see branch `sprint-771a-button-primitive` (filled at PR merge).


---

### Sprint 772a: Lazy-load Recharts + GlobalCommandPalette
**Status:** COMPLETE — landed on branch `sprint-772a-lazy-recharts-cmdk`.
**Priority:** P2.
**Source:** Frontend efficiency audit (2026-05-01) findings 3.1 + 3.2.

Splits Sprint 772 into 772a (this commit — Recharts + CommandPalette lazy-loads) and 772b (LazyMotion evaluation, deferred to a follow-up so the framer-motion footprint can be measured against this baseline). Audit's claim that `TrendSparkline` was eagerly loaded by dashboard/multi-period turned out to be stale (`grep` confirmed zero page-level consumers of `TrendSparkline` / `TrendSummaryCard` / `TrendSection` outside of test files); `BenfordChart` is the only real recharts entry point.

**What landed:**
- `frontend/src/components/shared/skeletons/ChartSkeleton.tsx` (new) — lightweight 200px shimmer placeholder; matches BenfordChart's render footprint closely enough that there's no visible layout shift on swap-in. Re-exported from `skeletons/index.ts`.
- `app/tools/journal-entry-testing/page.tsx` — `BenfordChart` removed from the eager barrel import; replaced with `next/dynamic({ ssr: false, loading: () => <ChartSkeleton /> })` against the direct `@/components/jeTesting/BenfordChart` path. The chart only loads its recharts chunk when the success branch actually renders it.
- `app/providers.tsx` — `GlobalCommandPalette` removed from the eager barrel import; replaced with `next/dynamic({ ssr: false })` against the direct path. The Cmd+K listener already lives in `CommandPaletteContext` (verified at `CommandPaletteContext.tsx:107`) so the eager event-handler registration is preserved while the palette UI itself code-splits.
- `__tests__/JournalEntryTestingPage.test.tsx` — added `jest.mock('@/components/jeTesting/BenfordChart', …)` direct-path stub to mirror the barrel mock. Without it, the dynamic import bypasses the barrel mock under jsdom and renders the real component, which crashes on `benford.total_count.toLocaleString()` against the test fixture.

**Verification:**
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npx jest --watch=false --testPathPatterns="JournalEntryTesting"` → **8 passed, 0 failed**.
- `cd frontend && npx jest --watch=false` (full suite) → see commit-message tail.
- `cd frontend && npm run build` → see commit-message tail.

**Out of scope / deferred:**
- LazyMotion evaluation (audit 3.3) — deferred to 772b; needs `next build --analyze` baseline against this lazy-load baseline to measure actual bundle delta.
- Hoisting CommandPalette mount to be conditional on `isOpen` — would save the chunk fetch entirely for users who never press Cmd+K, but adds complexity and the dynamic-import path already keeps the chunk off the main bundle.
- Removing the `GlobalCommandPalette` re-export from `components/shared/index.ts` — currently unused-via-barrel after this change, but removing the re-export risks breaking unrelated consumers we haven't enumerated.

**Commit SHA:** see branch `sprint-772a-lazy-recharts-cmdk` (filled at PR merge).


---

### Sprint 773c: Render-perf finishers (sort comparator + motion literal hoists)
**Status:** COMPLETE — landed on branch `sprint-773c-render-perf-finishers`.
**Priority:** P3.
**Source:** Frontend efficiency audit (2026-05-01) findings 1.7 + 1.8 sub-items remaining after Sprint 773 + 773b.

Two surgical hoists. Pure perf wins, zero behavior change.

**What landed:**
- `components/multiPeriod/AccountMovementTable.tsx` — sort comparator hoisted from inside the `useMemo` body to a module-scope `getSortValue(m, sortKey)` function. Each memo run was previously rebuilding two parallel ternary chains per row. Now the sort callback is a thin wrapper around the hoisted helper. Audit finding 1.8 sub-item.
- `components/shared/testing/FlaggedEntriesTable.tsx` — `motion.tr` `initial`/`animate`/`transition` literals hoisted to module-scope `ROW_INITIAL` / `ROW_ANIMATE` / `ROW_TRANSITION` (`as const`). Each rendered row was previously allocating three fresh objects; with `ITEMS_PER_PAGE = 25`, that's ~75 object allocations per render → 0. Audit finding 1.7 sub-item.

**Verification:**
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npx jest --watch=false --testPathPatterns="(FlaggedEntries|AccountMovement|multiPeriod)"` → **32 passed, 0 failed** (4 suites).
- `cd frontend && npm run build` → exit 0; routes correctly dynamic (`ƒ`).

**Out of scope (deferred):**
- `<RowEditor>` / `<SignalRow>` extraction in composite-risk + heatmap pages — bigger surgery, separate filing.
- `Reveal` placement inside memoized result subtrees — requires careful reasoning about scroll-trigger interaction with memo stability.
- `RiskBadge` / `StatTile` mini-component unification (audit 2.5/2.6).

**Commit SHA:** see branch `sprint-773c-render-perf-finishers` (filled at PR merge).


---

### Sprint 773: Type disambiguation + dead-code (subset)
**Status:** COMPLETE — landed on branch `sprint-773-type-disambig-dead-code-subset`.
**Priority:** P3.
**Source:** Frontend efficiency audit (2026-05-01) findings 1.3, 1.4, 1.8.

Scoped down from the original Sprint 773 grab-bag to the three lowest-risk sub-items: type-collision disambiguation (`Severity`, `RiskLevel`) and one dead-code removal (`DISTANCE` map). Render-perf wraps and inline mini-component extraction deferred to a follow-up filing — the audit's findings 1.5/1.6/1.7/2.5/2.6 + 4.1 remain on the table.

**What landed:**
- `types/accountRiskHeatmap.ts` — `Severity` (3-value `'high' | 'medium' | 'low'`) renamed to `HeatmapSeverity` to remove the collision with the canonical 4-value `Severity` in `types/shared.ts`. Disambiguating doc-comment added explaining why the heatmap input is stricter (backend aggregator only emits 3 buckets).
- `utils/themeUtils.ts` — `RiskLevel` (4-value `'high' | 'medium' | 'low' | 'none'`) renamed to `ThresholdRiskLevel`. Disambiguating doc-comment cross-references the other two `RiskLevel` definitions in the codebase.
- `types/compositeRisk.ts` — `RiskLevel` (4-value `'low' | 'moderate' | 'elevated' | 'high'`) renamed to `CompositeRiskLevel`. Same disambiguating doc-comment pattern.
- `utils/motionTokens.ts` — deprecated `DISTANCE` map deleted. `DISTANCE.state` was the only entry referenced (twice, both inside the file itself in `STATE_CROSSFADE`); inlined as the literal `8` at the call sites. The other entries (`subtle`, `standard`, `dramatic`) were already unused — entrance distances moved to `lib/motion`'s `lift` per the deprecation note. Companion test block in `__tests__/motionTokens.test.ts` removed.
- Consumers updated: `app/(diagnostic)/recon/page.tsx`, `app/(diagnostic)/flux/page.tsx`, `app/tools/account-risk-heatmap/page.tsx`, `app/tools/composite-risk/page.tsx`, `utils/index.ts` (re-export rename).

**What did NOT change (deferred):**
- `contexts/DiagnosticContext.tsx:10` re-export of `RiskLevel` from `types/diagnostic.ts` (the third `RiskLevel` definition — an enum). Renaming the source enum would ripple across more consumers than this surgical sprint warrants — bundle with a future engagement-tooling cleanup if/when one arises.
- `MechanicalGauge.tsx`'s local `RiskLevel` (file-scoped, no leak).
- `useWorkspaceInsights.ts`'s local `RiskLevel` (hook-scoped, separate domain).
- All Sprint 773 audit-finding render-perf wraps (`React.memo` for `MovementSummaryCards`, `BudgetSummaryCards`, `HeatmapResults`, `CompositeRiskResults`, row editors), motion-literal hoists, and inline mini-component extraction.

**Verification:**
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npx jest --watch=false` → see commit-message tail.
- `cd frontend && npm run build` → see commit-message tail.

**Commit SHA:** see branch `sprint-773-type-disambig-dead-code-subset` (filled at PR merge).


---

### Sprint 773b: React.memo wraps for result subtrees
**Status:** COMPLETE — landed on branch `sprint-773b-react-memo-result-subtrees`.
**Priority:** P3.
**Source:** Frontend efficiency audit (2026-05-01) findings 1.5 + 1.6 — render-perf wraps deferred from Sprint 773's grab-bag scope reduction.

Wraps four post-result subtrees with `React.memo` so dashboard filter/sort interactions and other parent state changes don't cascade through them. None change behavior — pure render-perf.

**What landed:**
- `components/multiPeriod/MovementSummaryCards.tsx` — wrapped in `memo(…)`. Hoisted the `cards` array and `borderAccentMap` to module-scope `CARDS` / `BORDER_ACCENT_MAP` (`as const`) so they're not re-created per render. Audit finding 1.5 + finding hoist sub-item.
- `components/multiPeriod/BudgetSummaryCards.tsx` — wrapped in `memo(…)`.
- `app/tools/account-risk-heatmap/page.tsx` — page-private `HeatmapResults` (line 397) wrapped in `memo(…)`. Imports `memo` from `react`.
- `app/tools/composite-risk/page.tsx` — page-private `CompositeRiskResults` (line 354) wrapped in `memo(…)`. Imports `memo` from `react`.

**Verification:**
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npx jest --watch=false --testPathPatterns="(multiPeriod|MovementSummary|BudgetSummary|composite|heatmap)"` → **43 passed, 0 failed** (7 suites).
- `cd frontend && npm run build` → exit 0; routes correctly dynamic (`ƒ`).

**Out of scope (deferred):**
- Row-editor `<RowEditor>` / `<SignalRow>` extraction in composite-risk + heatmap (audit 1.6 sub-item) — bigger surgery, separate filing.
- `FlaggedRow` / `FlaggedEntriesTable` motion-literal hoists (audit 1.7) — separate filing.
- `AccountMovementTable` sort-comparator hoist (audit 1.8 sub-item).
- `Reveal` placement inside memoized subtrees (audit 1.7).
- `RiskBadge` / `StatTile` mini-component unification (audit 2.5/2.6).

**Commit SHA:** see branch `sprint-773b-react-memo-result-subtrees` (filled at PR merge).


---

