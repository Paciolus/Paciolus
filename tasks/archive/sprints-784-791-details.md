# Sprints 784–791 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-21.

---

### Sprint 787b: Wire the six Sprint-689 tools into engagement tracking
**Status:** COMPLETE for the backend half. **The UI half does not exist** — see the correction at
the end of this entry, and **Sprint 791**.
**Priority:** P2 — the catalog counts are honest after Sprint 787; the runs were still not recorded.
**Source:** PR #174 review, 2026-10-21.

Sprint 787 made the six tools *representable* in `ToolName` and classified them in the
taxonomy. It did not wire them up. None of the six routes calls `maybe_record_tool_run`, and
none accepts an `engagement_id`:

| Route | Endpoints | Has `engagement_id` | Has `db: Session` |
|-------|-----------|---------------------|-------------------|
| `sod.py` | 3 | no | **no** |
| `intercompany_elimination.py` | 2 | no | yes |
| `w2_reconciliation.py` | 2 | no | yes |
| `form_1099.py` | 2 | no | yes |
| `book_to_tax.py` | 3 | no | yes |
| `cash_flow_projector.py` | 2 | no | yes |

**Scope:** follow the `ar_aging.py` pattern — optional `engagement_id`, `background_tasks`,
`maybe_record_tool_run(db, engagement_id, user_id, slug, success, score, flagged)` on the
success path and a `success=False` call in the error handler.

**The part that is design, not mechanics:** what `composite_score` and `flagged_accounts`
mean for each tool. A role-permission matrix and a 90-day cash projection do not produce
"flagged accounts" in the sense AR aging does. Decide per tool whether to pass `None`, a
domain-appropriate score, or to extend the recorder — do not invent a score to fill the
parameter. `shared/account_extractors.py` deliberately has no extractor for any of the six
(see Sprint 787's convergence classification), so `flagged_accounts=None` is the honest
default until a tool earns one.

**Verification:** a run of each tool against an engagement produces a `ToolRun` row; the
workpaper index and Anomaly Summary both show the tool as executed; the completion gate
counts it.

#### What landed

All six routes now take `engagement_id` in the request body and record through
`maybe_record_tool_run`. These are JSON-body routes, so the reference pattern is
`multi_period.py` (`payload.engagement_id`) rather than `ar_aging.py`'s multipart
`Form(default=None)` — otherwise identical: `background_tasks.add_task(...)` on the success
path, a synchronous `success=False` call in each error arm.

| Route | Endpoint wired | Error arms recorded |
|-------|----------------|---------------------|
| `sod.py` | `/audit/sod/analyze` | 1 (new `try`, see below) |
| `intercompany_elimination.py` | `/audit/intercompany-elimination` | 2 |
| `w2_reconciliation.py` | `/audit/w2-reconciliation` | 2 |
| `form_1099.py` | `/audit/form-1099` | 2 |
| `book_to_tax.py` | `/audit/book-to-tax` | 2 |
| `cash_flow_projector.py` | `/audit/cash-flow-projector` | 2 |

The `export.csv` endpoints are deliberately **not** wired. A CSV re-render of an analysis the
caller already ran is not a second run, and 689c–g already made the same split for
`check_upload_limit`.

**The design question, answered: `None` for both parameters on all six.** Not an omission —
none of the six engines computes a composite score (verified: zero occurrences of
`composite_score` across all six `*_engine.py` files), and `shared/account_extractors.py` has
no extractor for any of them because none produces GL-account-level output. Sprint 787 already
established that equivalence mechanically: `CONVERGENCE_TOOLS` is exactly the key set of
`ACCOUNT_EXTRACTORS`. A test pins both as `None` so a later change cannot start writing a
fabricated score into a workpaper quietly.

**`sod.py` needed a `try` the other five already had.** Its engine does not raise on bad
input; `_build_extra_rule` does, as a 400 for an unrecognised severity. That is still a failed
run from the engagement's point of view, so the call is wrapped and the failure recorded
rather than dropped.

#### Tests — `tests/test_promoted_tool_engagement_wiring.py`, 37 tests

Four parametrized cases per tool (24) plus failure-path, activity-feed and guard coverage:
run-creates-ToolRun, omitting `engagement_id` records nothing, repeat runs increment
`run_number`, and **a foreign `engagement_id` is ignored rather than recorded** — worth its own
case on all six because the wiring passes an attacker-chosen integer straight from the request
body into the recorder, which resolves it through `EngagementManager.get_engagement(user_id, …)`.
Also covered: `ToolActivity` rows are written even with no engagement link, which is what makes
these six appear on the multi-tool dashboard at all.

**Two guards, both of which failed to work on their first draft.** Recording this because it is
now the fifth instance of the same class in this repo:

1. *"Every route that accepts an `engagement_id` on a run must record it."* First draft flagged
   **nine false positives** — it required a direct `maybe_record_tool_run` call, but the six
   testing routes delegate to `shared/testing_route.py::run_single_file_testing` and the
   diagnostics routes to `services/audit/file_tool_scaffold.py::execute_file_tool`, both of
   which record. It also counted `engagement_id` arriving as `Query(...)` — a filter on a read
   in `activity.py` and `trends.py`, where nothing should be recorded.
2. Fixing it by resolving imports one hop made it **vacuous**. `shared/testing_route.py` holds
   both `enforce_tool_access`, which nearly every route imports, and `run_single_file_testing`
   — so "imports from a module that calls the recorder" was true for almost every route. The
   guard went green and tested nothing. **Regression-proving caught it**: stripping the recorder
   out of `routes/form_1099.py` left the guard passing. The check is now on the called function
   from an explicit two-name allowlist, and a second test asserts those two helpers really do
   record, so the allowlist cannot rot into a lie.

Both guards were then regression-proved in both directions — injected violation fails and names
the right file, restore passes.

**The open question about the background-task session — resolved, then pinned.** The success
path hands a request-scoped `Session` to `background_tasks.add_task(maybe_record_tool_run, db, …)`,
which is only safe if the task runs *before* `get_db`'s `finally: db.close()`. These tests cannot
settle it: `_override` installs `get_db` as `lambda: db_session`, a plain callable rather than a
generator, so no teardown happens at all.

Settled empirically against the installed FastAPI 0.136.1 with a throwaway app carrying a real
`yield` dependency. Observed order: `handler body` → `task ran` → `teardown`. **Background tasks
run first, so the session is still open.** The house pattern is correct, not accidentally
surviving — my initial read of the FastAPI 0.106 change was wrong.

Worth more than a note, because **Sprint 786b plans FastAPI 0.136 → 0.150.** If a release in that
range flips the ordering, all 13 wired routes stop filing success-path tool runs and *every other
test in this file still passes*, since they all override `get_db` with a non-generator.
`TestBackgroundTaskOrderingContract` therefore asserts the ordering directly, with a failure
message that names the consequence and points at 786b. Built on a throwaway app rather than
`main.app` deliberately — the property belongs to FastAPI's dependency machinery, and routing it
through the real app would drag in auth, rate limiting and the database for no added signal.

#### Four review findings on PR #182 — all four real, two fixed here

An automated reviewer raised three P1s and a P2. Every one was verified against the code or
empirically before acting; **all four hold**, and two of them falsify claims made above.

**Fixed in this PR**, because both live in `shared/tool_run_recorder.py` — the module six new
callers were just added to — and both made assertions in this sprint's own test file untrue:

1. **The `ToolActivity` row was never durable for an engagement-less run.** The module docstring
   declared the recorder "is deliberately never the transactional boundary… letting the route
   handler own the commit." **No route handler has ever committed it.** `get_db` ends in a bare
   `db.close()`, so the pending insert was discarded — measured at **zero rows surviving**
   through a real `get_db` generator. Runs *with* a resolving engagement persisted only because
   `EngagementManager.record_tool_run` commits and flushed the activity row along with it. So the
   multi-tool dashboard feed has been losing every engagement-less run across **all thirteen**
   wired routes, not just the six added here. The recorder now owns that commit, consistent with
   `record_tool_run` on the same session.

2. **A stale `engagement_id` returned 500 from every wired route.** The recorder wrote
   `ToolActivity` carrying the caller-supplied id *first*, then queried for the engagement — and
   that query's autoflush pushed the insert into a `tool_activity.engagement_id` foreign-key
   violation. Confirmed empirically to raise `IntegrityError` on **both** the success and the
   failure path, which is worse than reported: on the failure path it replaced an intended 400
   about malformed input with a server error. Resolution now happens before the write, and an
   unresolvable id degrades to an *unlinked* activity row — the same "skip the workpaper trail"
   semantics already applied to an engagement owned by someone else.

   Nine new tests cover both, all nine regression-proved: they fail against the old recorder
   (`FOREIGN KEY constraint failed`, zero surviving rows) and pass with the fix.

**Corrected, not fixed — filed instead:**

3. **The quota claim in Sprint 789 was false.** See the correction in that entry. `check_upload_limit`
   only reads; nothing increments the counter outside bulk upload. Filed as **Sprint 790**.

4. **Nothing in the UI ever sends `engagement_id` for these six tools.** None of the six hooks
   references engagement at all. This sprint delivered the backend precondition and the tests
   construct `engagement_id` directly, so **a browser user still cannot produce a `ToolRun`** —
   the exact shape of overclaim the PR #174 review caught in Sprint 787, repeated one layer out.
   Status above corrected accordingly.

   The gap is app-wide and pre-existing rather than introduced here: only four hooks
   (`useAuditUpload`, `usePreflight`, `useStatisticalSampling`, `useTrialBalanceUpload`) plus the
   multi-period page call `useOptionalEngagementContext`, and `createTestingHook.ts` — which
   backs the nine testing tools — has **zero** engagement references, even though those backends
   have accepted `engagement_id` as a `Form` field for sprints. Filed as **Sprint 791**.

**Verification:** 46 tests in `test_promoted_tool_engagement_wiring.py` (37 + 9 for the review
findings); 1,336 passed across every recorder-dependent suite; full backend suite green;
`ruff check .` clean; no new mypy findings in the six changed modules;
`scripts/check_openapi_drift.py` reported exactly the six intended `engagement_id` additions and
nothing else, snapshot regenerated (paths 220, schemas 422, both unchanged).

**Commit SHAs:** `682507a2` (route wiring + 37 tests) · `856fe857` (the background-task
ordering contract) · `ad5ed5a5` (the two recorder fixes + 9 regression tests) · `e2cf0f63`
(scoping that contract to the seven routes it still covers). The review fixes are the
larger half of what this entry describes, so the first SHA alone does not reach them.


---

### Sprint 789: Two paying tiers were sold a tool the API refused to run
**Status:** COMPLETE.
**Priority:** **P1** — a contractual surface promised a tool the backend 403'd. Revenue-relevant
and liability-relevant, not cosmetic.
**Source:** found while surveying `routes/sod.py` for Sprint 787b, which had flagged it only as
"no `db: Session`". CEO decision 2026-10-21: remove the gate.

`routes/sod.py` carried a bespoke `require_enterprise_tier` dependency that returned 403 to
every tier below Enterprise — **the only hardcoded tier comparison in any route module.**
Meanwhile every other surface sold Segregation of Duties to Solo and Professional:

| Surface | What it said | File |
|---------|--------------|------|
| **Terms of Service** tier table | "All 18 tools" for Solo *and* Professional | `(marketing)/terms/page.tsx:616,621` |
| Pricing page tier features | "All 18 diagnostic tools" on both paid tiers | `(marketing)/pricing/page.tsx:381,401` |
| Pricing page **FAQ** | "Both Solo and Professional include all 18 diagnostic tools" | `(marketing)/pricing/page.tsx:482` |
| Pricing page SEO metadata | "All paid tiers include all 18 diagnostic tools" | `(marketing)/pricing/layout.tsx:5,8` |
| `UpgradeModal` — shown at purchase | "All 18 tools" on Solo and Professional | `billing/UpgradeModal.tsx:27,35` |
| Backend entitlements table | `tools_allowed=_ALL_TOOLS` (empty = all) for every paid tier | `shared/entitlements.py:88,107` |
| Tool catalog (SSOT) | `sod_checker`, `is_marketing_audit_tool=True` | `tools_registry.py:170` |
| `UpgradeGate` docstring | "All paid tiers … have access to all 18 tools" | `shared/UpgradeGate.tsx:10` |

**Why it survived.** Sprint 689b's own filing says "Already Enterprise-gated" — the gate was
known and carried forward when the tool was promoted into the marketed catalog. Sprint 717 then
added it to `tools_registry.py`, and Sprints 784/788 swept the prose from 12 → 18. Every one of
those made the count correct and the *access* wrong, because nothing cross-checked a tier gate
against the entitlements table. `test_catalog_consistency.py` ties the registry to the frontend
ledger; nothing tied either to what the routes actually allow. The frontend even documented the
discrepancy without resolving it: `tools/sod/page.tsx` layered `FeatureGate` on top of
`UpgradeGate` with the comment "the standard UpgradeGate only blocks Free tier, so this page
layers … to block Solo/Professional as well."

**What landed.**
- `routes/sod.py` — `require_enterprise_tier` deleted; `require_verified_user` + `db: Session`
  with the standard `enforce_tool_access(current_user, "sod_checker", db)` and
  `check_upload_limit(current_user, db)`. SoD was the only one of the six promoted tools calling
  neither, so it is now consistent with its five siblings.

  > **CORRECTION (PR #182 review).** This bullet first claimed the `check_upload_limit` addition
  > "closed a second, independent defect: its runs never counted against the monthly upload
  > quota." **That is wrong, and the real defect is larger.** `check_upload_limit` only *reads*
  > the counter — `increment_upload_count` is the only thing that writes it, and its sole caller
  > in the entire repository is `routes/bulk_upload.py:154`. So **no single-tool run anywhere
  > increments `Subscription.uploads_used_current_period`**, and the advertised 100/500 monthly
  > allowances are not enforced for any paid tier. Free tier *is* metered, because it falls back
  > to counting `ActivityLog` rows. Adding the check to SoD makes it consistent, not enforced.
  > Filed as **Sprint 790**. This also explains why Sprint 741a found "no realized impact" from
  > the broken `reset_upload_quotas` job: the counter it resets is almost never incremented.
- `/audit/sod/rules` → `require_verified_user`, no entitlement check. It exposes the rule
  library, not an analysis of customer data — mirrors `/audit/book-to-tax/standard-adjustments`.
- `/audit/sod/analyze.csv` → `enforce_tool_access` without `check_upload_limit`, the same split
  689c–g use for their exports.
- Frontend: `FeatureGate` → `UpgradeGate(toolName="sod_checker")`; `sod_checker` removed from
  `FeatureGate`'s union, tier map and display-name map entirely, since that component's own
  docstring says it gates features and that tools belong to `UpgradeGate`; `GuestCTA` copy
  "verified Enterprise account" → "verified account on a paid plan"; the "Enterprise plan."
  suffix dropped from the `/tools` catalog description; the `useSOD` header comment corrected.

**A second defect the tests found.** `tools/sod/page.tsx` claimed "**Twelve** standards-backed
SoD rules". `DEFAULT_SOD_RULES` has **11** (AP-01…03, JE-01/02, PR-01/02, REV-01/02, INV-01,
ADM-01). Corrected to Eleven, and the test now pins the count *exactly* with the full code set
rather than `>= 12` — a `>=` assertion would not have caught this and, for the months the claim
was live, nothing did.

**Tests — `tests/test_sod_routes.py`, 10 tests.** Free blocked on analyze and on CSV export with
the standard `TIER_LIMIT_EXCEEDED` shape (not the old bespoke `{"error": "tier_locked"}`
payload); **Solo, Professional and Enterprise all pass**, parametrized — Enterprise is included
so a future change cannot narrow the gate back to a single tier and still go green; the rule
library readable by Free as reference data.

Plus an AST guard: **no route module may compare `<...>.tier` against a `UserTier` member.** The
defect was not that SoD was Enterprise-only, it was that one route decided tier access for
itself instead of asking `enforce_tool_access`, which let the entitlements table, the catalog
and a contract page disagree with it indefinitely with nothing failing. `routes/sod.py` was the
only offender; this keeps it that way. Regression-proved by injecting a comparison into
`routes/book_to_tax.py` — the guard failed and named `book_to_tax.py:143` exactly, then passed
on restore. (Firing is not the same as being right; Sprint 782a's gate named a class that
existed nowhere on its first draft.)

**Verification:** 10 new backend tests; 237 passed across the affected backend suites; frontend
`SODPage.test.tsx` 4 → 6 tests, full suite 2,009 → **2,011** passed, 0 failures; `tsc --noEmit`
exit 0; `npm run build` clean with every route `ƒ (Dynamic)` and `ƒ Proxy (Middleware)` active;
`ruff check .` clean; the 120 CI-gate tests (design-token lint, doc consistency, accounting
policy, citation consistency) all pass.

**Not in scope, deliberately:** the two stale "twelve tools" strings on live marketing pages that
this sprint's grep uncovered, and the reason nothing caught them. Filed as **Sprint 789b**.

**Commit SHA:** `88ec6d3c` — all of this sprint's code. The quota correction above landed separately in `ad5ed5a5`, which changed this record rather than the implementation. (Recorded pre-merge as `d21542a3`, which never existed on `main` — PR #182 was rebase-merged and the rebase rewrote it.) Note that `routes/sod.py` carries both this sprint's gating change
and Sprint 787b's engagement wiring in the same function signature, so the whole file landed in
this commit; 787b's other five routes are the commit after.


---

### Sprint 789b: The tool-count gate guarded the docs and not the website
**Status:** COMPLETE.
**Priority:** **P1 for the three strings** — all live, all customer-facing, one on the homepage.
P2 for the guard extension.
**Source:** Sprint 789. A grep for spelled-out tool counts turned up stale "twelve"s; the dry-run
of the fix then found a third the grep had missed.

| File | Was | Now | Where a customer sees it |
|------|-----|-----|--------------------------|
| `marketing/hero/HeroProductFilm.tsx:105` | "analysis across **12** testing tools" | 18 | **the homepage** — renders via `HeroScrollSection` in `(marketing)/page.tsx:32` |
| `(marketing)/demo/page.tsx:79` | "Explore all **twelve** audit diagnostic tools" | eighteen | the /demo page body |
| `marketing/ToolSlideshow.tsx:514` | "**Twelve** purpose-built tools." | Eighteen | the tool slideshow |
| ~~`tools/sod/page.tsx:93`~~ | ~~"Twelve standards-backed SoD rules"~~ | Eleven | fixed in Sprint 789 — the library has 11 |

The homepage one is the worst of the three: it understates the catalog by a third, and the
pricing page one click away says eighteen.

#### Why three sprints and a dedicated CI gate all missed them

The filing assumed `doc_consistency_guard.py` simply never reads the frontend. **That was wrong,
and the truth is sharper.** The guard has a `CODE_SURFACE_CHECKS` list that already covers two
frontend files — and one of them is `(marketing)/demo/layout.tsx`, with the pattern
`all (?P<n>\d{1,2}) audit diagnostic tools`.

So the guard author had already thought about this exact phrase, in this exact route. The result:

- `demo/layout.tsx` — **guarded**, and correct at 18.
- `demo/page.tsx` — **unguarded**, the adjacent file in the same route, saying *twelve*.

The metadata was kept current because something checked it. The visible page body beside it was
not. And the gate reported `ALL CHECKS PASSED` throughout.

Two root causes, both structural:

1. **`CODE_SURFACE_CHECKS` is a hand-maintained per-file list with per-file patterns.** A per-file
   allowlist only ever guards the files someone remembered to add. Sprint 784 added
   `demo/layout.tsx` and stopped.
2. **Its patterns are digit-only.** `\d{1,2}` never matches "twelve", even though the *documentation*
   half of the same module has had a `_NUMBER_WORDS` map since Sprint 784. The two halves of one
   guard had different capabilities.

#### What landed

- The three strings corrected.
- **`CUSTOMER_COPY_GLOBS` + `_check_customer_copy`** — a glob scan over copy a customer can read
  (the marketing route group, `components/marketing/**`, `UpgradeModal`, `UpgradeGate`,
  `GuestCTA`), using the same numeral-aware `_TOOL_COUNT_PATTERNS` as the docs instead of bespoke
  per-file regexes. One violation per line, since several patterns can match one claim.
- The two `CODE_SURFACE_CHECKS` entries stay: each needs a genuinely bespoke pattern (a bare
  `'All 18'` table cell; the digit-only metadata string).
- **The boundary, written down.** The gate reads what a customer sees. Workspace and tool pages are
  excluded — they render counts from `tool-ledger.ts` and from live `toolRuns.length`, both already
  tied to the registry by `test_catalog_consistency.py`, so scanning them adds false-positive
  surface (`{toolRuns.length}/18 tools`) and no coverage. Code comments inside scanned files are
  **not** excluded: a comment saying "all 18 tools" is a claim a future editor will trust.
- Pattern widening, each change traceable to a real miss: the adjective group now repeats `{1,2}`
  so a stacked pair cannot slip between count and noun ("all twelve **audit diagnostic** tools"),
  and `purpose-built` joined the list. The list stays **closed** rather than becoming `[a-z-]+`.

#### Two things the dry-run and the tests caught in my own work

**The dry-run found a third stale string.** Before changing the guard, the proposed patterns were
run across the candidate globs as a read-only probe. It reported 3 disagreements and 36 agreements
— and the third disagreement, `HeroProductFilm.tsx:105` ("12 testing tools"), was one my original
grep had missed entirely, because I had searched for "twelve" and for "18 tools" rather than for
the shape of a claim. Worth repeating as a habit: **dry-run a new guard across the real tree before
wiring it in, and read the agreements too** — 36 correct hits with zero false positives is what
made the widened pattern safe to ship.

**The false-positive test did not test what its comment claimed.** I wrote a fixture of
non-catalog strings and a comment saying that loosening the adjective class to `[a-z-]+` would
turn several of them red. Then I actually loosened it: **all 58 tests still passed.** Every case in
the fixture had *no adjective at all* ("18 tools", "six tools", "All 10 file formats"), and the
pattern rejects those whether the class is open or closed — so the fixture was orthogonal to the
property it was supposed to protect. Fixed by adding `ARBITRARY_ADJECTIVES` — "the 6 remaining
tools", "7 new tools", "9 competing tools" — plus a test asserting those three *are* matched by the
open variant, so the discriminator is itself verified rather than assumed. Re-proved: loosening the
class now fails `test_customer_copy_ignores_non_catalog_claims`; restoring passes.

Also dropped `core` from the adjective list. I had added it speculatively; `grep` found only
"Core tools & exports", which carries no count, so the alternative was inert and widened the
pattern for nothing.

#### PR #183 review: `search()` examined only the first match per line

Correct, and it is a false negative in the half of the check that matters. `_check_customer_copy`
used `pattern.search(line)`, so a line holding a **correct** count followed by a **stale** one of
the same form passed cleanly: the first match equalled the registry count, the loop moved on to
the next pattern, and the stale claim beside it was never examined. Verified directly —
`"An 18-tool suite — formerly a 12-tool suite"` yields `search → 18` and
`finditer → ['18', '12']`.

`_check_tool_count_in_doc`, the older sibling in the same module, had always iterated. I wrote the
newer checker with `search` and a `break`, which reads as "one violation per line" and silently
also meant "one *candidate* per line". Now `finditer` with the one-violation-per-line
deduplication kept deliberately — the reader needs the line, not every phrasing on it. Two tests:
the mixed-count line is flagged, and a line with three stale phrasings still yields exactly one
finding.

**Verification:** 15 new tests (46 → **61** in `test_doc_consistency_guard.py`). Regression-proved
in both directions — reverting all three strings produces exactly 3 violations with correct file, line
and quoted text and exit code 1; restoring gives 0 and exit 0. `_check_customer_copy` run against
the live tree is clean. Frontend 2,011 passed, `tsc --noEmit` exit 0. `ruff check .` clean. A test
also asserts every glob matches at least one real file, since a glob matching nothing covers
nothing — the same silent failure as the allowlist it replaced.

**Commit SHAs:** `71f47bb5` (the three stale strings + the customer-copy gate) · `5daa3d6f`
(the `search` → `finditer` fix in `_check_customer_copy`, from the PR #183 review).


---

### Sprint 791: The six promoted tools' hooks never send `engagement_id`
**Status:** COMPLETE.
**Priority:** P2 — six of eighteen tools cannot file a workpaper entry from the UI, and two
sprints in a row have claimed engagement tracking for them.
**Source:** PR #182 review finding, verified 2026-10-21.

The six tools wired in Sprint 787b now accept `engagement_id` in the request body, and nothing in
the product ever puts it there. None of `useSOD`, `useIntercompany`, `useW2Reconciliation`,
`useForm1099`, `useBookToTax` or `useCashFlowProjector` contains the string `engagement` at all.

So a practitioner who opens one of these tools from inside an active engagement — the `/tools/*`
layout does supply `EngagementProvider`, and the workspace URL does carry `?engagement=…` —
produces a run that is filed nowhere. For those six, the workpaper index, the Anomaly Summary
coverage fraction and the completion gate are counting a population the UI cannot populate.

> **CORRECTION (2026-10-21, before any code was written).** The first version of this entry said
> the gap was app-wide and singled out **`hooks/createTestingHook.ts`** for having "zero
> engagement references", concluding that the nine testing tools behind it were equally broken.
> **That was wrong.** `createTestingHook` delegates to `useAuditUpload`, and
> `useAuditUpload.ts:102` has auto-injected `engagement_id` into the FormData since **Sprint
> 103** (`// Auto-inject engagement_id when linked to a workspace`), then calls
> `refreshToolRuns()` and `triggerLinkToast()` afterwards. The nine testing tools inherit all of
> that and work correctly. "No engagement references in the file" was evidence of delegation, not
> of a defect — the same mistake, in the same session, as the Sprint 787b guard that resolved
> delegation badly. I reported the overclaim on PR #182 rather than leave it standing.
>
> The scope is therefore **the six JSON-body hooks only**, which genuinely do not use
> `useAuditUpload` — they post via `apiPost` with their own fetch logic.

**Reference pattern: `useStatisticalSampling`**, a JSON-body hook that already does this properly
— `useOptionalEngagementContext()` → `engagementId` → `engagement_id: engagementId` in the
payload, with `engagementId` in the `useCallback` dependency array.

**Two sprints have now claimed this path without building all of it.** Sprint 787 added the enum
and called the tools trackable; the PR #174 review caught it. Sprint 787b wired the routes and
called the runs tracked; the PR #182 review caught it. Each verified its own layer and inferred
the rest, so this sprint's tests have to span the layers rather than add a third layer-local set.

**Scope:**
1. The six hooks — read `useOptionalEngagementContext` and include `engagement_id` in the
   payload, following `useStatisticalSampling`. Add `engagementId` to the dependency arrays.
2. Decide per hook whether the CSV-export call also carries it. Leaning no: Sprint 787b
   deliberately did not wire the `export.csv` endpoints, since a re-render of an analysis the
   caller already ran is not a second run.
3. Match `useAuditUpload`'s follow-through — `refreshToolRuns()` and `triggerLinkToast()` after a
   successful linked run — so the workspace reflects the new entry instead of going stale.
4. A test per hook asserting the posted payload carries `engagement_id` when an engagement is
   active and omits it when none is, driven through the hook rather than by hand-building the
   body. **The tell that Sprint 787b was incomplete was that its tests had to supply
   `engagement_id` themselves**; a test that constructs the thing the product should construct
   proves nothing about the product.

**Acceptance bar:** with an active engagement selected, running any of the six from its page
produces a `ToolRun` row — asserted through the hook, not by constructing the payload.

**Also worth checking while here:** `usePreflight`, `useTrialBalanceUpload` and the multi-period
page are the other `useOptionalEngagementContext` callers. Confirm no *other* JSON-body hook has
the same gap, and record the result so the next reader does not have to re-derive it.

#### What landed

All six hooks now read `useOptionalEngagementContext` and spread
`engagement_id: engagementId ?? undefined` into the posted payload, with `engagement_id` dropping
out of the JSON entirely when there is no engagement — `undefined` does not survive
`JSON.stringify`, and an explicit `null` would be a different thing on the wire that
`Optional[int]` rejects.

`engagementId` and `engagement` were added to each `useCallback` dependency array, and each hook
now mirrors `useAuditUpload`'s follow-through on a successful **linked** run:
`refreshToolRuns()` + `triggerLinkToast(<tool name>)`. Without that the workpaper list the
practitioner is looking at still shows the pre-run state, so the run would be filed and invisible
— a quieter version of the same bug.

**The `export.csv` calls deliberately do not carry it**, matching Sprint 787b's decision not to
wire the export endpoints: a CSV re-render of an analysis the caller already ran is not a second
run.

**The engagement link stays off the request types.** `SODAnalysisRequest` and friends describe
what the *page* supplies; the hook owns the workspace link. Same split as `useAuditUpload`, which
appends to FormData without the type mentioning it, and `useStatisticalSampling`, which passes
`engagement_id` in a separate params object. A comment in each hook says so, because the natural
next question on reading the spread is "why isn't this on the type?".

#### Tests — `promotedToolEngagementLink.test.ts`, 25 tests

Four cases per tool, asserting **what reached `fetch`** rather than what the hook was given:
sends `engagement_id` when an engagement is active; omits the key entirely when not; refreshes the
workspace after a linked run; does *not* refresh when there is none. Plus one coverage guard
pinning the endpoint set to the six Sprint 787b wired, so a seventh cannot be added without a case
here.

Asserting through `fetch` is the point, not an implementation detail. **The tell that Sprint 787b
was incomplete is that its backend tests constructed `engagement_id` in the payload themselves** —
a test that supplies the thing the product is supposed to supply proves nothing about the product.

Regression-proved: against the un-wired hooks, **12 of 25 fail** — the six "sends it" and six
"refreshes" cases. The other 13 pass, correctly: the negative cases ("omits when absent", "does not
refresh") hold trivially on code that never sends it, which is exactly why a suite of only negative
assertions would have looked green.

One snag worth recording: `jest.mock('@/utils/constants', ...)` with a bare object broke the whole
suite with `(0, _constants.hours) is not a function` — `cachePlugin.ts` imports `hours()`/
`minutes()` from that module and `apiClient` imports `cachePlugin`. Fixed with
`...jest.requireActual`. A wholesale module mock is a bigger hammer than it looks when the module
is a utility grab-bag.

#### PR #183 review: `refreshToolRuns()` raced the recording

Correct finding, and the race was real rather than theoretical. Starlette sends the response
body at `responses.py:167` and awaits the background task at `:170` — so a client holding the
200 is ahead of the pending insert. The hooks added above call `refreshToolRuns()` the moment
the POST resolves, which meant the GET could return a workpaper list that predated the row,
replace the context state with that stale list, and never refresh again. The new entry would
stay invisible until a manual reload.

**Fixed by recording synchronously on the success path** in all six routes:
`background_tasks.add_task(maybe_record_tool_run, …)` → a direct call, with the
`background_tasks` parameter and its import dropped. The write is one INSERT plus a commit,
after an analysis that already ran in-process, so the latency the background task bought back
was never worth the race.

Pinned two ways, because the symptom is invisible server-side — the row *does* appear, just
after the client stopped looking. A structural test asserts none of the six reintroduces
`background_tasks.add_task(maybe_record_tool_run, …)`, since a timing test against an
in-process ASGI transport would pass either way; and a behavioural test queries immediately
after the response with no `await` between. Regression-proved: reverting `form_1099.py` to a
background task fails the structural test by name.

**The same race exists in `useAuditUpload`**, which calls `refreshToolRuns()` after an upload
whose route records via `background_tasks`. That covers the nine testing tools and several
diagnostics endpoints. Pre-existing, not introduced here, and the fix is the same one-line
change per route — folded into **Sprint 790**'s sweep, which already has to touch every
`check_upload_limit` caller.

**Verification:** 25 frontend tests + 8 backend (53 in
`test_promoted_tool_engagement_wiring.py`); frontend suite **2,011 → 2,036 passed** (207
suites), 0 failures; `tsc --noEmit` exit 0; `npx eslint src/hooks` clean; `npm run build` clean
with every route `ƒ (Dynamic)` and `ƒ Proxy (Middleware)` active; `check_openapi_drift.py`
reports no drift (paths 220, schemas 422 — dropping `BackgroundTasks` is not a schema change).

**Audit of the other JSON-body hooks, recorded so it is not re-derived:** `useAuditUpload` (and
therefore `createTestingHook` and the nine testing tools behind it), `usePreflight`,
`useTrialBalanceUpload` and `useStatisticalSampling` all already send `engagement_id`. The six
fixed here were the only gap.

**Commit SHAs:** `77f58aee` (the six hooks + 25 tests) · `5daa3d6f` (making all six routes
record synchronously, which is the fix for the `refreshToolRuns()` race this entry
describes).


---

### Sprint 784c: Six of seven per-tool test counts in the user guide were stale
**Status:** COMPLETE.
**Priority:** P2 — customer-facing documentation understating the product, and a gate reading
the very file it drifted in.
**Source:** found while scoping Sprint 784b, 2026-10-21.

`docs/07-user-facing/USER_GUIDE.md` carries each tool's automated-test count in its chapter
heading — "### 6.2 Test Battery (13 Tests)". **Six of the seven were wrong**, two by four tests:

| Chapter | Guide said | Engine has | Off by |
|---------|-----------|------------|--------|
| Journal Entry Testing | 19 | 19 | ✓ |
| AP Payment Testing | 13 | **14** | −1 |
| Payroll Testing | 11 | **13** | −2 |
| Revenue Testing | 16 | **18** | −2 |
| AR Aging Analysis | 11 | **12** | −1 |
| Fixed Asset Testing | 9 | **11** | −2 |
| Inventory Testing | 9 | **10** | −1 |

Every number understates the product, which is the less damaging direction but still wrong on a
page a prospect reads.

**And the counts were the smaller half.** Several tier breakdowns did not describe the engine at
all. Revenue's "Tier 1 — Structural (5 tests)" listed *"Missing fields, duplicate transactions,
negative revenue, date gaps, unusual customers"*; the engine's Tier 1 is large manual entries,
year-end concentration, round amounts, sign anomalies and unclassified entries. Payroll, AR,
Fixed Assets and Inventory were summary prose that had drifted from the implementation.

**Why the gate missed it.** `USER_GUIDE.md` is already in `TOOL_COUNT_DOCS`, so
`doc_consistency_guard.py` reads the file on every CI run — but that check only matches
*aggregate* catalog claims ("18 diagnostic tools", "12-tool suite"). The per-tool numbers drifted
underneath a guard reading the same file, for the same reason Sprint 789b's three marketing
strings did: the gate was scoped to one kind of claim and the file contains two.

#### What landed

- All six headings corrected, and **every battery section rewritten from the engine's own test
  assembly order** — real test IDs and titles, with the tier each test actually belongs to. The
  tier assignment is the engine's, not mine: `AP-T14`, for instance, sits in **Tier 1
  Structural** rather than the fraud tier its ACFE rationale would suggest, because that is where
  `run_ap_tests` puts it.
- The nine previously-undocumented tests now have entries: AP-T14 (invoice without PO),
  PR-T12 (duplicate employee names), PR-T13 (gross-to-net reconciliation), RT-09b (prior-period
  timing), RT-17 (contract validity, ASC 606 Step 1), AR-01b (sub-ledger negative invoices),
  FA-10 (lease indicators), FA-T11 (depreciation recalculation), IN-T10 (LCM/NRV).
- Conditional tests are now marked as such. Seven AR tests need the sub-ledger file and four
  payroll tests need an optional column; each emits a skipped result with a reason rather than
  failing, and the guide now says so instead of implying every test always runs.

#### The guard — two checks, because one of them cannot see its own warning

1. **Heading vs registry.** `_parse_tool_test_counts` reads `Tool.test_count` from
   `tools_registry.py`, already tied to the frontend ledger by
   `test_catalog_consistency.py`; `_check_tool_test_counts_in_guide` walks the guide in document
   order, tracking which tool chapter is open so a battery heading is attributed to the chapter
   above it rather than to a hand-maintained line number.
2. **Heading vs its own list.** The first check's failure message says "update the heading **and**
   the test list beneath it" — and nothing verified the second half. A corrected number above an
   unchanged list would have passed. So the checker also sums the tier sub-counts
   (`**Tier 1 — Structural (6 tests):**`) and reports the arithmetic when they disagree with the
   heading. A section written as prose, with no tier sub-headings, makes no claim and is not
   treated as summing to zero.

**One bug in my own guard, caught by running it.** The first draft reported five of the six stale
counts. `GUIDE_TOOL_HEADINGS` mapped `ar_aging` to `"AR Aging"` against a chapter titled
`"AR Aging Analysis"`, so that tool dropped out silently — a hand-maintained mapping with no test
that it still maps, which is the exact failure mode of the per-file allowlist Sprint 789b had just
replaced in this same module. `test_guide_tool_headings_all_resolve` now fails if any entry stops
matching a real chapter title, and `test_guide_tool_headings_cover_every_tool_with_a_test_count`
fails if the registry gains a counted tool with no mapping.

**Verification:** 15 new tests (59 → **74** in `test_doc_consistency_guard.py`), including the
false-negative set: both tier-heading styles the guide uses, the `(4 tests, optional)` qualifier
on Revenue's contract tier, a prose section that must not be summed, and tier headings in the
*following* section that must not be counted into this one. Regression-proved in both directions —
dropping one tier sub-count from 6 to 5 is caught with `tier sub-counts total 13 (5 + 5 + 3)`;
reverting a heading is caught against the registry; the clean tree reports `ALL CHECKS PASSED`
with exit 0. `ruff check .` clean.

**A third claim in the same file, found while checking SoD's tier after Sprint 789.** §15.2
"Tool Access by Plan" opens with *"All paid tiers (Solo, Professional, Enterprise) have access to
all 18 tools"* and then lists **twelve rows** — the pre-Sprint-689 catalog. The aggregate-count
check passes, because the sentence agrees with the registry; a reader comparing the sentence to
the table would reasonably conclude the *sentence* was the error. The six promoted tools are now
rows, and `test_user_guide_tier_table_lists_every_catalog_tool` fails if the table ever lists
fewer than the catalog. (With Sprint 789 landed, Segregation of Duties correctly shows Yes for
every paid tier.) Also added the explicit Free-tier line, since the table's dashes say what Free
lacks and not what it has.

Two bad entries in that test's own alias map, caught on its first run: I mapped the guide's
"Multi-Period Comparison" to "Multi-Period TB" and listed "W-2 / W-3 Reconciliation" as an alias
of itself. The registry's display names are the authority and only three names genuinely differ.

**One more correction, found while verifying the deploy.** The Sprint 784 note in this guard's
module docstring described the FastAPI description as part of the **public** OpenAPI schema,
shipping "12-Tool Audit Intelligence Suite" publicly for six months. It is not public:
`main.py:250` sets `openapi_url=None` when `ENV_MODE == "production"`, and
`https://paciolus-api.onrender.com/openapi.json` returns **404** — checked against the live
service. The string still deserved fixing, because it ships in the image and is served by every
non-production deploy and by `/docs` locally, but it was never reachable by a customer. Docstrings
and the violation message corrected, and `_check_api_description` now points the reader at
`CUSTOMER_COPY_GLOBS` for the counts that genuinely are customer-facing.

**Not in scope:** Journal Entry Testing's Tier 3, whose heading count (9) is correct but whose
list shows seven bullets and then "And additional pattern-based tests". The arithmetic is right,
so the guard is satisfied; completing that enumeration belongs with Sprint 784b's authoring pass.

**Commit SHAs:** `18dc0303` (784b and 784c landed in one commit — both rewrite
`USER_GUIDE.md`) · `5736f382` (the six PR #184 review findings: four documentation
corrections, the two `status.json` downgrades, and Sprint 793's filing).


---

### Sprint 784b: User guide chapters for the six newer tools
**Status:** COMPLETE.
**Priority:** P3 — documentation completeness. A third of the catalog had no user documentation.
**Source:** Sprint 784, 2026-10-20. Delivered with **784c**, because both rewrite
`USER_GUIDE.md` and separate branches would have conflicted on every hunk.

`docs/07-user-facing/USER_GUIDE.md` documented twelve tools, one chapter each, and carried an
explicit note that the six tax and controls tools were not written up.

**What landed — six chapters, §15–§20:**

| § | Tool | Standards |
|---|------|-----------|
| 15 | Tool 13: Segregation of Duties | SOC 1, COSO 2013 Principle 10 |
| 16 | Tool 14: Intercompany Elimination | ASC 810, IFRS 10, ISA 600 |
| 17 | Tool 15: W-2 / W-3 Reconciliation | IRC §6051, Forms W-2 / W-3 / 941 |
| 18 | Tool 16: Form 1099 Preparation | IRC §6041, §6041A, Pub 1220 |
| 19 | Tool 17: Book-to-Tax Reconciliation | Schedule M-1 / M-3, ASC 740 |
| 20 | Tool 18: Cash Flow Projector | ASC 230 |

Each follows the established shape — purpose, inputs with the columns that matter, how to read the
output, what the export contains — and each is written **from the engine**, not from the UI:

- SoD's full 11-rule library as a table with codes, plus the actual risk formula
  (`3 × high + 2 × medium + 1 × low`, tiers at ≥ 6 and ≥ 3).
- The 1099 thresholds as implemented: **$600** NEC, **$600** MISC, **$10** INT.
- Book-to-Tax's M-1 / M-3 switch at the real **$10M total assets** heuristic.
- Cash Flow's base-vs-stress AR collection rates as a table, with the point that matters stated:
  the **lowest balance and the day it occurs** is the number to read, because a healthy 90-day
  ending balance can sit on top of a mid-period trough that breaches the minimum.
- Intercompany's `counterparty_entity` called out as the field that makes matching possible at
  all, since without it a balance cannot be paired.

**Each chapter states its boundary**, because five of the six are advisory by design and the
engines say so in their own docstrings: SoD conflicts are candidates for review, not deficiencies
(ISA 265 / AU-C 265); W-2 flags discrepancies without deciding which number is right; 1099
identifies candidates rather than asserting a filing obligation; Book-to-Tax is a calculator, not
a tax opinion; Intercompany shows the gaps rather than asserting elimination is complete.

Export availability is stated honestly per tool — five of the six are CSV-only, and the chapters
say "a PDF memo for this tool is not yet available" instead of implying the full memo set.

**Renumbering:** §15–§24 became §21–§30, with the TOC, the `### N.M` sub-headings and the TOC
anchors updated together. Checked first that nothing outside the TOC links to those anchors —
nothing does, in the guide or in any other doc. Verified after: 30 chapters, 30 TOC entries,
numbering sequential 1–30, every TOC title matching its heading. The three anchors my checker
flagged (`21-billing--plans`, `25-exports--reports`, `17-tool-15-w-2--w-3-reconciliation`) are
correct — GitHub's slugifier drops `&` and `/` and leaves the doubled hyphen, which the two
pre-existing entries confirm.

The interim note is retired: "Sections 3–20 below walk through all eighteen in detail, one chapter
each."

**Two gates caught my new text, which is the point of having them:**

1. `test_user_guide_tier_table_lists_every_catalog_tool` — the test I had written in 784c
   hardcoded `### 15.2 Tool Access by Plan`, and the renumbering moved it to §21.2. A hardcoded
   section number is a dependency on the table of contents rather than on the thing being tested;
   it now matches the title with the number as a wildcard.
2. `test_every_cited_standard_is_registered` — my SoD chapter cites **AU-C 265**, which had no
   entry in `backend/standards_registry.py`. Registered, as the AICPA counterpart to the already-
   registered ISA 265 and with the same boundary usage.

   **And that one exposed a gap worth more than the fix.** `tools/sod/page.tsx` has cited
   "ISA 265 / AU-C 265" in its disclaimer since Sprint 689b, and nothing ever failed — because
   `SCANNED_GLOBS` covered `app/(marketing)/**` and `components/marketing/**` but **not**
   `app/tools/**`. Every tool page carries a `DisclaimerBox` and a `CitationFooter` that a signed-
   in customer reads on each run; that is as customer-facing as a marketing page. Measured before
   widening the glob: exactly **one** unregistered citation across all tool pages, the AU-C 265
   above. So the coverage cost one registry row. Regression-proved — un-registering AU-C 265 now
   fails on both `USER_GUIDE.md` and `tools/sod/page.tsx`, the second only because of the wider
   glob.

**Verification:** `doc_consistency_guard` ALL CHECKS PASSED; 128 passed across the doc-consistency,
citation and catalog suites; `ruff check .` clean; TOC/heading/anchor consistency verified
programmatically.

#### `features/status.json` had the same hole, and it is the first file a session reads

`AGENTS.md` lists it as **step 3** of every session's startup — "full feature inventory, what is
built and what is not". It covered the pre-Sprint-689 catalog: **all six promoted tools were
absent**, six months after they shipped, and every entry still carried `last_verified:
2026-03-18`. Nothing guarded the file — the catalog contract tested registry↔ledger and
registry↔standards, and left this edge out.

Six entries added with real verification steps (the endpoints, the thresholds that matter, the
tier boundary for SoD), each noting CSV-only export where that is the case. Plus three tests in
`test_catalog_consistency.py`, which is where the other catalog edges live:

- every marketing tool has a `status.json` entry, reported with the slug *and* the id it expected;
- entries are well formed — a half-written one reads as coverage without being it;
- **the slug→id alias map contains no redundant entries.** That last one caught two of my own on
  its first run (`ar_aging` → `ar-aging`, `fixed_asset_testing` → `fixed-asset-testing`, both of
  which the slug-derived rule already produces). Dead aliases hide the next rename, which is
  exactly how `GUIDE_TOOL_HEADINGS` silently stopped matching a chapter title in 784c.

Regression-proved: removing the SoD entry fails with
`no entry for: ["sod_checker (expected id 'segregation-of-duties')"]`.

**Out of scope:** Multi-Currency Conversion still has no chapter, correctly — it is a validation
side-car rather than one of the eighteen tools, which the Welcome section already says. Also left
alone: the `last_verified: 2026-03-18` on the other 79 entries. Stamping today's date on features
I have not re-verified would be worse than a stale date that is honest about itself.

**Commit SHAs:** `18dc0303` (784b and 784c landed in one commit — both rewrite
`USER_GUIDE.md`) · `5736f382` (the six PR #184 review findings: four documentation
corrections, the two `status.json` downgrades, and Sprint 793's filing).


---

