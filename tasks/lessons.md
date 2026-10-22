# Lessons Learned

> **Protocol:** After ANY correction from the CEO or discovery of a better pattern, document it here. Review at session start.

---

## A background task finishes after the client is already acting on the response (Sprint 791 review, 2026-10-21)

I added `refreshToolRuns()` after a successful tool run so the workpaper list the
practitioner is looking at would reflect it. The route recorded the run via
`background_tasks.add_task`. Those two facts do not compose.

Starlette sends the response body at `responses.py:167` and awaits the background task at
`:170`. The client holding the 200 is *ahead* of the insert. So the refresh GET could
return the list as it was before the run, replace the context state with it, and never fire
again — the new entry invisible until a manual reload. The row was written. Nobody looked
again.

Earlier in the same session I had measured the ordering of background tasks against
`yield`-dependency teardown and concluded the pattern was safe. That was the right answer
to a different question. **"The task runs before teardown" and "the task runs before the
client sees the response" are two orderings, and I checked the one that happened to be
favourable.**

**Pattern: if the client reads a value back immediately, writing it in a background task is
a race the client usually loses.** Either write it synchronously, or do not promise the
reader it is there. Here synchronous was obviously right — one INSERT and a commit, after an
analysis that already ran in-process. The background task was buying back latency that
nothing needed and paying for it with a correctness bug.

**And the test shape that works for this.** A timing test against an in-process ASGI
transport passes either way, because the background task runs almost immediately — just not
before the response. So the durable assertion is **structural**: no route may reintroduce
`background_tasks.add_task(maybe_record_tool_run, …)` on the success path. Paired with a
behavioural test that queries with no `await` in between, which documents the intent even
though it cannot fail on its own.

---

## `search()` means "is there a match", not "are the matches all fine" (Sprint 789b review, 2026-10-21)

My new copy checker looped over patterns calling `pattern.search(line)`, took the first
match, compared it to the registry and `break`'d. The older checker in the very same
module used `finditer`.

A line reading `An 18-tool suite — formerly a 12-tool suite` passed cleanly. The first match
is 18, which is correct, so the loop moved to the next pattern and the stale 12 beside it was
never examined.

I had intended "one violation per line" — a real and reasonable choice, since the reader
needs the line rather than every phrasing on it. But `search` implements "one *candidate* per
line", which is a different thing and strictly worse: it decides whether to look at all based
on whichever occurrence happens to come first.

**Pattern: when scanning a line for violations, enumerate the matches and dedupe the
findings. Never dedupe by only looking once.** The two collapse into the same code only when
a line can hold at most one match, which for prose is never a safe assumption.

Worth noting where the correct version already lived: fifty lines up, in the function this
one was modelled on. **The strongest reviewer of a new checker is the old checker beside it** —
diffing mine against `_check_tool_count_in_doc` would have surfaced this before CI did.

---

## Writing docs "from the engine" means from the implementation, not the docstring (PR #184 review, 2026-10-21)

I wrote six user-guide chapters and said, in the sprint record and the PR, that each was
written **from the engine** rather than from the UI. Four of them described behaviour the
code does not have, and the review caught all four:

- RT-17 "flags a blank customer" — `RevenueEntry` has **no customer field**. I had copied
  the first bullet of the function's docstring; the docstring's own closing note says
  "currently the model doesn't have a separate customer_id column". The implementation
  checks three entirely different predicates.
- The 941 comparison "per-quarter differences" — it sums every supplied quarter and
  compares against *annual* payroll, emitting each finding with `quarter=None`.
- The 1099 CSV "with the data-quality flags" — `export_1099_csv` writes `result.candidates`
  and never touches `data_quality` or `w9_collection_list`.
- The cash-flow CSV "horizon summaries and the weekly grid" — it writes 90 **daily** rows
  per scenario and no horizon rows at all.

Three of the four came from reading a docstring or a route description and trusting it. The
fourth came from assuming an export serialises the whole result object.

**Pattern: for a claim about what a function does, read the function. For a claim about
what an export contains, read the writer.** A docstring is a statement of intent by someone
who may have shipped less than they intended — which is the same reason this repo's sprint
records keep turning out to overclaim. I spent the session correcting exactly that failure
in other people's prose and then imported it wholesale into mine.

**Corollary that would have caught all four cheaply:** for an export, the ground truth is
the `writer.writerow` header list. It is one grep and it is unambiguous.

**And the harder lesson about "complete".** The same review found that both tax tools apply
one fixed set of statutory limits to any `tax_year` from 2000 to 2099. I had documented
them and marked them `complete` in `features/status.json` on the strength of the endpoints
working. Working is not correct. A tool that computes confidently against the wrong
constants is worse than one that errors — and for the two tools that touch IRS filings, the
bar for "complete" has to include *which year's figures it applies*. Both downgraded to
`partial` with the reason recorded, and filed as Sprint 793.

---

## The guard I wrote to prevent a defect had the defect (Sprint 792 review, 2026-10-21)

Sprint 792's thesis: a scan scoped by a filename or path list silently stops covering
the thing it was written for. Its deliverable was one test asserting every relocated
engine has the root shim both linters depend on.

My test enumerated `services/audit/*/analysis.py`. The **ADR-018 pilot relocation** is
`services/audit/flux/recon.py` — the one module that predates the `analysis.py`
convention. So deleting its shim left my test green while `lint_domain_relocation.py`
lost the ability to see that engine: exactly the regression the test exists to catch,
missed by the test's own filter.

I had regression-proved it, too — by removing `flux_engine.py`, which *is* an
`analysis.py` case. The proof confirmed the test worked on the shape I had thought of
and said nothing about the shape I had not.

**Pattern: when you write a guard against a class of defect, the first thing to check is
whether the guard is a member of that class.** It usually is, because the same habit of
mind produced both. Enumerate by the structural fact (a directory of per-tool modules),
not by the naming convention (`analysis.py`) — conventions have exceptions and the
exception is nearly always the oldest thing, which is nearly always the thing with the
least test coverage.

**And on regression-proving specifically: injecting the violation you expected proves
less than it feels like.** Pick the injection case you consider *least* likely to be
covered. Here that was the pilot, and it would have taken thirty seconds.

---

## Un-suppressing a code path means shipping code that has never run (Sprint 778a review, 2026-10-21)

`DR Test (Monthly)`'s liveness probe was guarded by `if: env.DATABASE_URL_READONLY != ''`
against a variable defined only in that step's own `env:` block. A step-level `if` is
evaluated against the job and workflow contexts, so the condition was permanently false
and **the probe had never executed once**. I fixed the guard and treated it as a one-line
correction.

It was not. The step's body had never run in production, and it contained a bug: `>
probe_result.json` creates the file before python starts, so a failed probe leaves an
empty file, and `if [ -f probe_result.json ]` then wrote *"Database responded to probe"*
into the same report that carried `probe=FAIL`. My fix made that contradiction reachable
for the first time, and the review caught it.

**Pattern: re-enabling a suppressed path is not a fix, it is a deployment.** Code behind a
dead guard has the test coverage of code that does not exist — nobody has ever seen its
output, and whatever is wrong with it has had no opportunity to surface. Read the whole
body with the scrutiny you would give new code, because to production it *is* new code.

**The tell was available and I walked past it.** I wrote in the same commit message that
"defect 2 concealed defect 4" — the verdict ignoring the probe's output is why nobody
noticed the probe never ran. Having said out loud that two defects were hiding each other,
I should have asked what *else* that silence had been hiding. Suppression is rarely
load-bearing for exactly one bug.

---

## Making a check honest can disable what the honesty protects (Sprint 778a review, 2026-10-21)

The point of Sprint 778a was to stop `DR Test (Monthly)` reporting success while its own
report said FAIL. I added a step that fails the job on any non-PASS verdict.

`restore-validation` declares `needs: dr-test`. A `needs:` dependency implies the
prerequisite **succeeded** unless the condition uses a status function like `always()`. So
the moment the job started failing — which is the expected state until the backup work
lands — GitHub silently stopped running the manual restore drill.

Sprint 778's own text calls that drill "the half of the risk a second mechanism does not
address". I made the reporting honest and, in the same commit, disabled the thing the
honesty exists to protect. **A false-green at least left the drill runnable.**

**Pattern: when you change a job from always-passing to sometimes-failing, enumerate what
depends on it.** The dependents were written against a job that could not fail, so none of
them needed a status function, and none of them will tell you when they stop running — a
skipped job is not a failed job and shows up as a quiet grey tick.

**And the narrower trap:** the drill never consumed `dr-test`'s output at all. It
provisions its own instance and runs its own `pg_restore`. The coupling was accidental,
inherited from `needs:` being the easy way to express ordering — which is precisely the
kind of dependency that breaks without anyone having decided it should matter.

---

## One broken check can hide another indefinitely (Sprint 778a, 2026-10-21)

`DR Test (Monthly)` had five defects. Two of them were load-bearing for the rest.

The verdict read three signals and branched on one, so the backup check and the
liveness probe could not affect the outcome. Separately, the liveness probe's guard
was `if: env.DATABASE_URL_READONLY != ''` against a variable defined only in that
step's own `env:` block — a step-level `if` is evaluated against the job and workflow
contexts, so the condition was permanently false and **the probe had never run once**.

Those two compose into something worse than either. A step that never executes
produces no output; an output nobody reads produces no symptom. Each defect made the
other invisible, and three consecutive monthly runs reported success while the report
they generated said FAIL.

**Pattern: when a check aggregates several signals, assert that each signal can
independently change the outcome.** A verdict function with an unused input is not a
style problem — it is a silent coverage hole, and it conceals whatever is wrong with
the input it ignores. The regression case that proves it here is one line:
`render=PASS, backup=false, probe=false` used to return PASS.

**Corollary on "unverified".** The old logic had two outcomes, so a missing credential
had to be reported as either a pass or a failure. It chose failure and wrote *"Instance
status: api_error (expected: available)"*, which reads as a database outage and sends
the reader after the wrong fix. **Three outcomes — PASS, FAIL, UNVERIFIED — is the
honest shape for any check that depends on credentials or external systems**, and the
job should still exit non-zero for UNVERIFIED, because an unverified disaster-recovery
posture is not a passing one.

**And the one that generalises furthest:** a verdict that cannot fail its job is a
comment. `overall=FAIL` gated only the issue-creation step. Whenever a workflow computes
a result, check what consumes it — if the answer is "a notification", the check is
advisory no matter how it reads.

---

## A parser-based guard can shrink without any test noticing (Sprint 786c review, 2026-10-21)

Third time in one session, and the first two were already written up directly above.

I added a guard asserting every GitHub Action is pinned to an immutable SHA. Its
parser was `^\s*uses:` — and YAML list items are written `- uses: actions/checkout@…`.
So it matched **15 of 64** references. Every `setup-node` and `download-artifact` use
and 25 of 27 `checkout` uses were invisible. Five tests, all green, inspecting 23% of
the file.

I regression-proved it. The line I picked happened to be one of the 15.

**And I had already written the lesson.** Sprint 792's entry says: *"injecting the
violation you expected proves less than it feels like. Pick the injection case you
consider least likely to be covered."* I wrote that, shipped it, and then picked a
convenient line a few hours later.

**The new thing here, beyond "pick a hostile case": a parser-based scan can narrow
silently, because the cases it stops seeing stop being asserted.** A file-list guard at
least fails loudly when a path disappears. A regex that quietly matches less produces
no signal at all — every downstream assertion keeps passing, on less.

So the durable fix is not a better regex. It is a **coverage self-check**: count the
candidates the naive way, require the parser to account for all of them, and assert
nothing about what they contain. Narrowing the regex back now fails with *"accounts for
15 external + 0 local = 15 of 64"*.

**The general rule: any guard that parses before it checks needs a test that it parsed
everything.** The check and the parse are two separate claims, and only one of them was
ever being tested.

---

## Audit the class once you have seen the instance three times (Sprint 792, 2026-10-21)

By the seventh finding of the same shape in one day — a gate scoped by a file list
that silently stops covering what it is named after — fixing the eighth was clearly
worth less than enumerating the class.

So every gate in the repo got inspected rather than waiting for the next one to
surface. The result was mostly reassuring, and that is itself the finding worth
keeping: four gates are structurally immune or genuinely comprehensive, and knowing
*which* ones is what stops the next reader re-deriving it.

The distinction that predicted everything:

- **Immune** — `check_openapi_drift.py` derives its target set from the running app.
  There is no list to rot.
- **Comprehensive** — `lint_design_tokens.py` rglobs all of `frontend/src`. A glob over
  a tree has no gaps, only a suffix filter.
- **Fragile** — anything with an explicit tuple of paths or names. All seven of the
  day's findings were in this category, every one of them.

**Pattern: prefer deriving the scan set from the system over listing it; failing that,
a glob; failing that, a hand-maintained list *with a test that it still matches
something*.** The ranking is about how the thing fails when the codebase moves
underneath it, not about how it reads.

**The one real find was a trap rather than a defect**, which is the whole value of
looking early. Both engine linters enumerate `BACKEND_ROOT.glob("*_engine.py")`, and
ADR-018 moved the implementations to `services/audit/<tool>/analysis.py`. They still
reach them only because every relocated engine left a root shim behind — and nothing
asserted the shims exist. All ten currently do, so there was no bug; an engine created
directly at the relocated path would simply have been unlinted, with both linters
reporting success on an empty scan.

**Corollary worth more than the fix: "the gate is green" and "the gate scanned
something" are different claims.** Every new scan now asserts it found work, because a
glob that matches nothing is indistinguishable from a glob that matches nothing wrong.

---

## Do not edit the tree while a suite runs against it (2026-10-21)

I started a full backend suite in the background, then kept working — switched
branches, inserted six user-guide chapters, edited the standards registry. The run
came back **1 failed, 8969 passed** on `test_every_cited_standard_is_registered`.

Nothing was broken. The suite read `USER_GUIDE.md` after I had added chapters citing
`AU-C 265`, while still on the branch where that standard was not yet registered. A
state that existed on no branch and in no commit — only on disk, for about a minute.

Diagnosing it cost more than the run was worth, and the dangerous version of this is
the opposite outcome: a mid-run edit that makes a real failure *pass*. A green
background run against a tree you are still editing is not evidence of anything.

**Pattern: a long verification run is the last thing before committing, not something
to do while you keep working.** If a run and an edit must overlap, run from a clean
worktree (`git worktree add`) so the suite has a tree nobody is touching.

---

## A gate on a file is not a gate on the file's claims (Sprint 784c, 2026-10-21)

`doc_consistency_guard.py` has read `USER_GUIDE.md` on every CI run since Sprint 784. Six
of the seven per-tool test counts in that file were stale anyway, two of them by four
tests, and several tier breakdowns described tests the engines do not have.

The guard was not broken. It checks *aggregate* catalog claims — "18 diagnostic tools",
"12-tool suite" — and the per-tool numbers are a different kind of claim living in the same
document. "This file is guarded" felt like coverage and was not.

This is the third instance of the same shape in one session:

- Sprint 789b: the guard read `(marketing)/demo/layout.tsx` and not `demo/page.tsx` beside
  it. Metadata current, visible page body stale.
- Sprint 789: the catalog registry, the frontend ledger and the docs all agreed with each
  other, and none of them agreed with what the API actually allowed.
- Here: the right file, the wrong claim.

**Pattern: when adding a consistency gate, write down which claims it covers — and when
inheriting one, do not read its file list as its scope.** The scope is the patterns, not the
paths. A gate whose coverage you cannot state in a sentence is a gate you will over-trust.

**Corollary — a guard's error message is a specification, so implement it.** This one's
message told the reader to "update the heading **and** the test list beneath it", and
nothing checked the list. A corrected number above an unchanged list would have passed
cleanly. If the message names two things, check two things; summing the tier sub-counts is
four lines and it closes exactly the gap the sentence admits.

**And the mapping bug worth remembering.** My first draft reported five of six, because
`GUIDE_TOOL_HEADINGS` said `"AR Aging"` against a chapter titled `"AR Aging Analysis"`. A
hand-maintained mapping needs a test that it still maps — the same lesson as the per-file
allowlist I had replaced in this very module hours earlier. **Replacing one hand-maintained
list with a glob does not stop you from introducing a different hand-maintained list two
functions down.**

---

## "No references in the file" is evidence of delegation, not of a defect (Sprint 791, 2026-10-21)

Twice in one session I grepped a file for a symbol, found nothing, and concluded the
behaviour was missing.

The first time it was a test: my guard asserting "every route accepting `engagement_id`
must record the run" flagged nine false positives, because the testing routes delegate to
`run_single_file_testing` and the diagnostics routes to `execute_file_tool`. I fixed the
guard and wrote up the lesson.

Hours later I did it again in prose. I wrote that **`createTestingHook.ts` has zero
engagement references** and concluded the nine tools behind it were as broken as the six
I was fixing — put it in a sprint filing *and* in a reply to the reviewer. It delegates to
`useAuditUpload`, which has auto-injected `engagement_id` since Sprint 103 and calls
`refreshToolRuns()` afterwards. The nine tools were fine. I had just fixed a guard for
exactly this and then reasoned the same way by hand.

**Pattern: before concluding a file lacks a behaviour, follow what it calls.** A thin
wrapper is *supposed* to have no references to the thing its callee handles — absence
there is the design working. The check is one level down, and it takes one grep.

The correction cost: a `CORRECTION` block in the sprint entry and a public follow-up on the
review thread. Cheap, and much cheaper than the sprint I nearly scoped at fifteen hooks
instead of six.

**Why the second instance is the more interesting one.** The guard version failed loudly —
nine findings I had to investigate. The prose version would have failed silently: I would
have "fixed" nine working hooks, the tests would have passed, and the sprint record would
have carried a false account of what was broken. **A wrong belief encoded in a test gets
caught by the test. The same belief written in prose gets believed.**

---

## A declared contract nobody implements is a bug with documentation (Sprint 787b review, 2026-10-21)

`shared/tool_run_recorder.py` opened with a confident statement of intent:

> `maybe_record_tool_run` is deliberately never the transactional boundary: it calls
> `db.add` but does not commit, letting the route handler own the commit.

**Not one of the thirteen call sites ever committed it.** `get_db` ends in a bare
`db.close()`, so for every run without an `engagement_id` the pending `ToolActivity`
insert was discarded. Measured through a real `get_db` generator: zero rows survive. The
multi-tool dashboard feed has been silently losing engagement-less runs for as long as the
feed has existed.

The reason nobody noticed is almost worse than the bug. Runs *with* a resolving engagement
did persist — because `EngagementManager.record_tool_run` commits, and that commit flushed
the activity row along with it. So the feature worked in exactly the case anyone would
test and failed in the default case.

**Pattern: a docstring that assigns a responsibility to callers is a claim about thirteen
other files, and it should be tested like one.** Either enforce it (a test asserting every
caller commits) or do not make it — put the commit where the knowledge is. The comment
cost nothing to write and bought a defect that outlived every sprint that touched the
module.

**Corollary on test-session overrides.** Our route tests install `get_db` as
`lambda: db_session` — a plain callable, so FastAPI never runs teardown, and the
`db_session` fixture's savepoint plus autoflush makes pending inserts visible to the next
query in the same session. That is the right fixture for route behaviour and the *wrong*
one for durability: it cannot distinguish "written" from "committed". **When the property
under test is that data survives the request, the test has to drive the real dependency
generator and read back from an independent session.** My own
`test_activity_row_written_even_without_engagement` asserted exactly the thing that was
broken and passed.

---

## Ordering a write before its validation turns bad input into a 500 (Sprint 787b review, 2026-10-21)

`maybe_record_tool_run` wrote the `ToolActivity` row carrying the caller-supplied
`engagement_id`, *then* queried for that engagement to decide whether to file a workpaper
entry. The query's autoflush pushed the pending insert, and a nonexistent id violated the
`tool_activity.engagement_id` foreign key.

Consequences, both confirmed empirically rather than reasoned about:

- Every one of the thirteen wired routes returned **500** to any client holding a stale
  engagement id, on the success path *and* the failure path.
- On the failure path it was worse than a 500 in the abstract: the intended response was a
  **400 about malformed input**, and a side effect of *recording* the failure replaced it
  with a server error. The error handler broke the error handling.

**Pattern: resolve before you write, especially when the value came from the request
body.** The fix is pure reordering — look the engagement up first, attach it only if it
resolved, and let an unresolvable id degrade to an unlinked row. That matched semantics the
function already had for an engagement owned by a different user; the two cases differed
only in which one happened to crash.

**And the near-miss worth keeping.** My test for this surface used an engagement that
*existed but belonged to someone else* — which exercises the ownership branch and never
reaches the foreign-key constraint. "Not authorized" and "does not exist" look like one
test and are two. A guard on attacker-supplied identifiers needs both: the valid-but-not-
yours case and the not-a-real-row case.

---

## Three sprints in a row claimed a path they had each only half-built (Sprint 787b review, 2026-10-21)

- **Sprint 787** added the six tools to `ToolName` and said they were trackable. The PR #174
  review caught it: no route called the recorder.
- **Sprint 787b** wired the six routes and said the runs were tracked. The PR #182 review
  caught it: no frontend hook sends `engagement_id`, so a browser user still produces
  nothing. `createTestingHook.ts`, which backs nine *other* tools, has zero engagement
  references either.
- Both sprints wrote tests that passed, and both sets of tests were scoped to the layer the
  sprint had changed.

Each sprint verified its own layer and inferred the rest. The inference was reasonable each
time and wrong each time, and the tests could not catch it because a layer-local test is
exactly what you write when you believe the other layers are fine.

**Pattern: when a feature spans layers, the acceptance test has to span them too — and
until it does, say "the backend half" rather than "complete."** The cost of the honest
status line is one sentence. The cost of the optimistic one is that the next sprint builds
on a precondition it believes is a conclusion.

I was fixing exactly this mistake when I made it again, in the same shape, one layer out.
The tell was available: my tests constructed `engagement_id` in the payload by hand, which
is precisely the step a real caller has to perform and that nothing in the product performs.
**When a test has to supply the input the product is supposed to supply, that is the gap,
not a fixture detail.**

---

## Dry-run a new guard across the real tree, and read the passes too (Sprint 789b, 2026-10-21)

Before wiring a widened tool-count pattern into `doc_consistency_guard.py`, I ran it as a
read-only probe across the candidate file globs and printed **both** lists: claims that
disagreed with the registry, and claims that agreed.

The disagreement list had three entries. I had only known about two. The third —
`HeroProductFilm.tsx:105`, "analysis across 12 testing tools" — renders on the
**homepage**, and my original grep had missed it because I searched for the strings I
expected ("twelve", "18 tools") rather than for the *shape of a claim*.

The agreement list mattered just as much: 36 hits, every one a genuine and correct catalog
claim, zero false positives. That is what made it safe to ship a widened pattern at all.
A guard validated only against the cases you wrote by hand tells you nothing about the
tree it will actually run on.

**Pattern: a new static check is three steps, not one — probe the real tree, review the
passes as carefully as the failures, then wire it in.** The probe costs one throwaway
script and it is the only step that can find what you did not know to look for.

**Corollary on per-file allowlists.** The guard already covered two frontend files, one of
them `(marketing)/demo/layout.tsx` — the page *metadata* for the very route whose page
*body* was stale. Metadata correct at 18, body beside it saying twelve, gate green. A
hand-maintained per-file list only ever guards the files someone remembered to add, and
it fails silently and indefinitely. Prefer a glob plus a test asserting the glob matches
something; a glob that matches nothing covers nothing, which is the same failure wearing
different clothes.

---

## A fixture can be orthogonal to the property it claims to protect (Sprint 789b, 2026-10-21)

I widened a regex and justified the widening with "the adjective list stays closed, and
`test_customer_copy_ignores_non_catalog_claims` pins that — loosen it to `[a-z-]+` and
several of these go red."

Then I loosened it to `[a-z-]+`. **All 58 tests passed.**

Every string in the fixture had *no adjective at all*: "18 tools", "six tools", "All 10
file formats", `{toolRuns.length}/18 tools`. The pattern rejects all of those whether the
adjective class is open or closed. The fixture was a perfectly good false-positive test
and completely orthogonal to the property the comment said it guarded.

The fix needed cases that *discriminate* — "the 6 remaining tools", "7 new tools", "9
competing tools" — an arbitrary word between a wrong count and the noun. Plus a second
test asserting those three really are matched by the open variant, so the discriminator is
verified rather than assumed. (Without that, someone later edits the fixture, the
discriminating power quietly evaporates, and we are back here.)

**Pattern: when a test is cited as the reason a risky choice is safe, break the choice and
watch that specific test fail.** Not the suite — that test. "The suite passes" and "this
test protects this property" are different claims, and only the second one is load-bearing
when someone later wants to relax the constraint.

This is the second time in one session that regression-proving caught a guard that was
green and vacuous (Sprint 787b's delegation check was the first), and in both cases the
code comment confidently asserted the protection it did not provide. **The comment is not
evidence. The failing run is.**

Related, same sprint: I added `core` to the adjective list speculatively. `grep` found
only "Core tools & exports", which carries no count — so the alternative was inert and
widened the pattern for nothing. Dropped. Every alternative in a pattern should be
traceable to a real occurrence.

---

## Counting the catalog twice is not the same as checking it works (Sprint 789, 2026-10-21)

`test_catalog_consistency.py` ties `tools_registry.py` to the frontend tool ledger.
`test_citation_consistency.py` ties the standards registry to the cited standards.
`doc_consistency_guard.py` ties six markdown documents to the canonical tool count.
Sprint 717 built the SSOT, Sprint 784 swept the prose 12 → 18, Sprint 788 fixed the
navigation, Sprint 787 fixed the enum. Four sprints and three CI gates, all green.

Segregation of Duties returned **403 to Solo and Professional the whole time**, while the
Terms of Service tier table, the pricing page, the pricing FAQ, the page's own SEO
metadata and the upgrade modal shown at checkout all promised "all 18 tools" to both.

Every one of those gates compares **one description of the system to another description
of the system**. The registry agreed with the ledger; the ledger agreed with the docs; the
docs agreed with the count. Nothing compared any of them to *what a request actually
does*. The count was correct and the access was wrong, and correctness of the count is
what was being measured.

**Pattern: for anything sold, assert against the behaviour, not against a second
description of it.** The test that finally caught this is four lines — POST the endpoint
as each paid tier and assert 200. The same shape as Sprint 780's lesson about
self-referential pricing assertions, one layer out: there the table was compared to
itself, here the catalog was compared to its own reflection.

**The structural fix is cheaper than the test.** `routes/sod.py` held the only hardcoded
`user.tier != UserTier.X` comparison in any route module. One route deciding entitlement
for itself is what made indefinite disagreement possible — every other route asks
`enforce_tool_access`, so for them the entitlements table cannot be contradicted. An AST
guard banning route-local tier comparisons closes the class; the per-tier HTTP tests close
the instance. Both are worth having, but the guard is what stops the next one.

**Corollary on sprint handoffs.** Sprint 689b's filing noted "Already Enterprise-gated" as
a convenience — one less thing to build. That sentence is where the defect entered: it
recorded the gate as a fact rather than as a question about whether the gate still matched
the pricing model it was about to be sold under. When promoting something into a catalog,
the inherited constraints need re-deciding, not just noting.

---

## A guard that cannot fail is worse than no guard (Sprint 787b, 2026-10-21)

I wrote a test asserting that every route accepting an `engagement_id` on a run actually
records that run. First draft: nine false positives, because most routes delegate to
`run_single_file_testing` or `execute_file_tool` rather than calling the recorder
themselves, and because `engagement_id` arriving as `Query(...)` is a filter on a read,
not a run.

So I resolved imports one hop: does the route import from a module that calls the
recorder? Green. All 35 tests passed.

**It was testing nothing.** `shared/testing_route.py` contains both
`run_single_file_testing` *and* `enforce_tool_access` — which nearly every route in the
codebase imports. "Imports from a module that calls the recorder" was therefore true for
almost every route, unconditionally. The guard had become a tautology, and it looked
exactly like a guard that works.

What caught it was **regression-proving**: strip `maybe_record_tool_run` out of
`routes/form_1099.py`, leave `engagement_id` accepted, re-run. The guard passed. A guard
that stays green while you break the thing it guards is not a slow guard or a lenient
guard — it is not a guard.

**Pattern: a new guard is not done when it passes. It is done when you have watched it
fail on an injected violation and then pass on restore.** Cheap — two file edits and two
test runs. It has now caught two distinct bugs in two consecutive sprints: Sprint 782a's
design-token lint named a class that existed nowhere (`bg-red-50` for `bg-red-500`), and
this one passed vacuously. Those are opposite failures and both invisible from a green run.

**Second pattern: resolve delegation by the function called, not the module imported.**
Module-level resolution is too coarse whenever one module holds both a widely-imported
utility and the thing being looked for — which is common, because utilities cluster. The
fix is an explicit allowlist of delegating functions plus a second test asserting those
functions really do what the allowlist claims, so the allowlist cannot rot into a lie
while the first guard keeps passing on its authority.

This is the fifth first-draft detector in this repository to match the wrong thing. The
previous four all matched prose *describing* the defect — a docstring quoting the bad SQL,
a comment naming the old assertion. This one is a new failure mode and a worse one: the
earlier four were loud and wrong, this one was quiet and wrong.

---

## When two passes over the same data disagree, the quiet one wins (Sprint 785, 2026-10-21)

`scripts/archive_sprints.sh` is mandated by `CLAUDE.md` and enforced by a commit-msg hook, so
it runs on roughly every sprint. It makes three passes over the Active Phase of
`tasks/todo.md`: one **counts** completed sprints, one **extracts** them into an archive file,
one **removes** them from `todo.md`. Counting and removal both handled a `### Sprint` heading
arriving while a block was still open. Extraction did not — awk's first matching rule reset
the accumulator without emitting it, which also made a whole branch of the next rule
unreachable. It reported "Archiving sprints 762–788", wrote 10 of 13, and deleted all 13.
Three finished sprint records were destroyed and only survived because the run was diffed
before committing.

**The failure was not the awk bug. It was that nothing compared the two numbers.** The script
already knew the right answer — the counting pass computed 13 and printed it on the first line
of output. The extraction pass produced 10. Both numbers were in the same process, one line of
shell apart, and no one subtracted them. A destructive step ran downstream of an undetected
shortfall.

**Pattern: when a pipeline computes the same quantity twice by different means, assert they
agree, and put the assert *before* the irreversible step.** This is cheaper than making either
pass correct and it catches the next bug too, not just this one. The fix adds exactly that
gate: extract, compare archived-section count against the counted count, exit 1 with both
numbers before `todo.md` is touched. The awk fix alone would have closed this instance; the
gate closes the class.

**Corollary on predicates.** The same script's three passes used two different definitions of
"complete" — extraction accepted `— COMPLETE` or `**Status:** COMPLETE`, removal accepted only
the second. That asymmetry silently duplicates records in the other direction. If two passes
must agree on a count, they must first agree on what they are counting; the predicate belongs
in one place.

**What exposed it** was a self-inflicted trigger: resolving eight `tasks/todo.md` rebase
conflicts as unions dropped the `---` separators between consecutive sprint blocks, which is
the exact shape the extraction bug needed. The lesson there is narrower but real — **a union
merge of two markdown sections is not safe just because no text is lost.** Section delimiters
are content. Structure that other tooling parses must be re-validated after a mechanical
merge, not assumed intact because the prose survived.

---

## A test that only checks a table against itself proves nothing (Sprint 780, 2026-10-20)

`tests/test_pricing_launch_validation.py` carried ~20 assertions over the pricing table and
had been green for months. It asserted that `PRICE_TABLE["solo"]["monthly"] == 10000` — that
the table equals the number written in the test. No assertion in the codebase had ever
touched Stripe, so nothing connected *intent* to *what a customer is charged*.

The gap was not hypothetical. Stripe test mode sat at the v2 price list (Solo $50) while the
code and the pricing page said $100, and the documented plan was to build live mode fresh —
so the first real card would also have been the first end-to-end test of current pricing.

**Pattern: a self-referential assertion is a tautology wearing a test's clothes.** Ask what
external system the value has to agree with, and assert against *that*. The new preflight
imports the canonical tables rather than restating any amount, then retrieves the Price
objects, so the assertion crosses the boundary that matters.

**Two findings on its first run**, neither of which any existing test could have produced:
the local test-mode secret key is **expired**, and only 4 of 10 price IDs resolve because
`backend/.env` still carries v2 variable names (`STRIPE_PRICE_TEAM_*`) that `price_config.py`
no longer reads. Writing the check was worth it before it ever ran in anger.

**Check the property that actually breaks money, not just the number.** The amount is the
obvious assertion. The one I nearly left out is `recurring.interval`: a correct $100 on a
yearly cadence bills right once and then wrongly forever, and no amount comparison catches
it. Same reasoning added `livemode` agreement, which is the specific accident that wires a
live deployment to test prices.

## Dead code found by trying to test it (same sprint)

Both access-restoration handlers wrap `UserTier(sub.tier)` in `except ValueError`. Writing a
test for that branch is how I learned it **cannot fire**: `Subscription.tier` is a
constrained DB enum, so a value outside `UserTier` never survives a round-trip — SQLAlchemy's
Enum raises on *result processing*, before the handler reads the row — and both handlers flush
after the conversion anyway.

The right response was not to contort the test until it reached the branch. It was to assert
the constraint that makes the branch redundant, so the test fails and names the cause if
`subscription_tier` and `UserTier` ever diverge. **When a defensive branch is unreachable,
test the thing making it unreachable.**

## Run a tool from the directory its config lives in (same sprint, twice)

`ruff.toml` lives in `backend/` and sets `line-length = 120`. CI runs ruff with
`working-directory: backend`, and the pre-commit hook does `cd ../backend && ruff format`. I
ran it from the repo root instead, where no config is found, so it silently used ruff's
default **88** — and reformatted files to a width the hook would immediately undo.

This bit me twice in one day. In Sprint 779 it exploded a three-element tuple across four
lines, which moved an `# allow-deny-phrase` annotation off the line it was annotating and
made the boundary guard fail; I diagnosed that as a line-length problem without noticing the
limit I was reasoning about was not the project's. Running `ruff check backend/ scripts/`
from the root also reported **92 errors** that CI does not see, because the root has no rule
configuration either.

**Before trusting a formatter or linter result, confirm it loaded the project's config** —
`ruff check --show-settings` prints it. A tool run from the wrong directory does not fail; it
quietly answers a different question.
## A `>=` floor is a standing decision to accept majors you never see (Sprint 786a, 2026-10-20)

`backend/requirements.txt` splits deliberately (Sprint 777): `==` for the framework surface,
`>=` floors for security leaves. The floors exist so a CVE fix lands without waiting for a
human, which is correct and worth keeping.

Reconciling the long-lived `backend/venv` to a fresh resolve made the other half of that
trade concrete. Twelve packages moved, and three of the moves were majors already live in
production: **`cryptography` 46 → 50**, **`pillow` 12 → 13**, **`redis` 7 → 8**. CI and the
production Docker build each do a fresh `pip install`, so those have been running for months.
Nothing broke. Nobody chose them either.

Sprint 777 wrote that risk down in plain words — *"production can take an unreviewed upstream
major at any time, with no lockfile and no record of what actually shipped"* — and then the
project kept no record, so the prediction came true invisibly. **Writing a risk down is not
the same as instrumenting it.** The follow-through was one CI step capturing `pip freeze`.

**A stale virtualenv makes a test suite lie in the safest-looking direction.** The nightly ran
against a venv pinned at every floor's *minimum*, so for months it was validating versions
that ship nowhere: green, reassuring, and about the wrong software. That is worse than a red
signal, because a red signal gets investigated.

**Ask whether a floor suits the package, not just the policy.** `cryptography` is the ideal
floor candidate: narrow API, currency is the entire point. `pillow` and `redis` are image
decoding and a cache client — majors there change behaviour, and the CVE argument is weaker.
A uniform rule applied to a non-uniform set produces exactly this: the right answer for some
packages and an unreviewed behaviour change for others. Raised with the CEO rather than
decided unilaterally, since it revises a decision rather than applying one.
## A guard firing is not the same as a guard being right (Sprint 782a, 2026-10-20)

The design-token lint flags Tailwind's generic colour classes. Its scale pattern was
`(?:50|[1-9]00|950)`. Regex alternation is leftmost-first, so against `bg-red-500` it
matched `50` and stopped: the file was correctly flagged, the exit code was correctly 1,
and the reported finding was **`bg-red-50`** — a class that appears nowhere in the file.

Every end-to-end check passed. The gate caught the violation. Only a unit test asserting
the exact `match` string caught that the message named the wrong thing, which would have
sent whoever hit it searching for a class that does not exist.

**Pattern: assert the content of a finding, not just its existence.** `assert findings` is
satisfied by a guard that is right for the wrong reason. The cheap habit is one test per
guard pinning file, line and matched text — those three are what a human acts on.

**Order alternations longest-first, and assert boundaries.** `(?:950|[1-9]00|50)` with a
trailing `(?!\d)` is the correct form; it also stops `bg-blue-5000` reading as
`bg-blue-500`. Any alternation of overlapping literals has this failure mode, and it
degrades the message rather than the verdict, so it survives casual testing.

**Error messages are part of the guard.** This lint names the replacement token for every
palette it rejects — `red` → `clay-*`, `emerald` → `sage-*`, `slate` → `obsidian-*` — and
says outright that semantic states are already covered, because "but it's an error state"
is the most plausible reason someone would reach for `red-500`. A gate that says "wrong"
without saying "use this instead" gets suppressed, and a suppressed gate is worse than no
gate: it still costs CI time and now also lies about coverage.

---

## A test that hardcodes a count defends the drift it was meant to catch (Sprint 787, 2026-10-20)

Sprint 689 expanded the tool catalog 12 → 18. `engagement_model.ToolName` was never
updated, and the gap survived six months — long enough that the Anomaly Summary PDF was
telling practitioners there were "13 available tools" while every marketing surface said
18, and long enough that a run of any of the six newer tools could not be recorded against
an engagement at all.

The interesting question is not how the enum was missed. It is **why nobody fixed it.**

`assert len(ToolName) == 13` existed in four separate test files, plus
`len(CONVERGENCE_EXCLUDED) == 6` in a fifth. Expanding the enum correctly turns all five
red. So anyone who started the right fix was met with five failing tests and a reasonable
inference: *I must be wrong.* The tests did not fail to catch the drift — they **defended**
it, and they would have defended it against the next person too.

**Pattern: a test may only hardcode a value it owns.** A count that belongs to another
module is that module's to state; asserting a literal copy of it converts every future
correct change into an apparent regression. Five tests now derive from
`tools_registry.MARKETING_AUDIT_TOOL_COUNT`, and one new test bans the literal outright so
the next copy cannot be added quietly.

**The denominator was never right, not merely stale.** `len(ToolName)` includes
`flux_analysis`, which is not a sold tool. It counts *trackable run types*, not *tools a
customer buys* — so it printed 13 when the catalog held 12, and 13 again when it held 18.
A number being wrong in a new way after a change is worth a second look: it often means the
quantity was mismeasured from the start.

**Classification needed a rule, not a judgement call.** Six tools were unclassified in the
convergence taxonomy, and "pick one" was tempting. The honest answer was already in the
code: `CONVERGENCE_TOOLS` is exactly the key set of `ACCOUNT_EXTRACTORS`, because a tool can
only contribute to a convergence index if something can extract GL accounts from its
result. All six lack extractors, so all six are excluded — and the equivalence is now
asserted, so the next tool cannot be classified without the extractor that justifies it.
**Where two lists have been kept in step by hand, the invariant is worth writing down as a
test; it is usually simpler than the maintenance it replaces.**

**Native enums hide behind SQLite.** `tool_runs.tool_name` is a Postgres enum type. Adding a
Python member without an `ALTER TYPE` migration passes every local and CI test — SQLite
stores enums as VARCHAR with no constraint — and fails on insert in production. The parity
suite now checks that every value added after the type's creation appears in some migration.
When a schema object exists only in the production dialect, tests on the dev dialect cannot
see it; the guard has to read the migrations.
## Dead code with a stale copy of real data misdirects the next reader (Sprint 788, 2026-10-20)

I filed Sprint 788 as "tool navigation bar lists 12 of 18 tools" and named
`components/shared/ToolNav.tsx`. The symptom was real. The file was wrong: `ToolNav` had been
superseded by `AuthenticatedShell` in **Sprint 475** and rendered on no page — its only
remaining reference was its own test.

What misled me was not absence of information but presence of *plausible* information. A
component named `ToolNav`, holding a tidy `TOOLS` array with twelve entries and an
`INLINE_COUNT` constant, reads as the authoritative nav definition. I confirmed the count was
wrong and stopped looking. The live surface — `UnifiedToolbar/toolbarConfig.ts` — had the same
defect, so the sprint's conclusion survived its false premise, which is luck rather than
method.

**Pattern: before fixing a component, confirm something renders it.** One grep for imports,
excluding its own test, would have cost seconds and redirected the whole sprint. The cheap
check is not "does this file contain the bug" but "does this file reach a user".

**And delete dead code that duplicates live data.** Unused code is ordinary debt; unused code
holding a stale copy of a list that exists elsewhere is a trap, because it looks like a source
of truth and ages invisibly. `ToolNav` is gone, along with two docblocks elsewhere that still
cited it as the model for the command palette's tool entries.

**Hardcoded layout constants have the same failure mode.** `MegaDropdown` used
`grid-cols-4` for "three tool columns plus Account". Adding a fourth tool column would have
pushed Account onto a second row with no error anywhere — a silent visual break. The grid now
derives from `TOOL_COLUMNS.length + 1`. Where a constant encodes a count of something that can
change, derive it or it will be wrong exactly once, quietly.

---

## A constraint that exists only in production is invisible to the test suite (Sprint 741a, 2026-10-20)

`reset_upload_quotas` had failed in production **every hour since it was written**, with
`22P02 InvalidTextRepresentation`. Its raw SQL filtered `WHERE status = 'active'`, but
`Subscription.status` is mapped `Enum(SubscriptionStatus)` with no `values_callable`, so
SQLAlchemy persists the enum member *name* — the Postgres type's labels are `ACTIVE`,
`PAST_DUE`, … and the lowercase `.value` is not among them.

8,728 tests passed throughout. On SQLite that column is a VARCHAR with no type constraint,
so the comparison does not raise — it matches **zero rows**, and the job logs success with
`records_processed: 0`. A test suite on the dev dialect cannot see a defect that only a
production-dialect constraint can produce.

This is the second instance today of the same shape. Sprint 787's missing `ALTER TYPE`
migration had the identical property: adding a Python enum member without it passes every
SQLite test and fails on insert in Postgres.

**Pattern: when behaviour depends on a dialect-specific constraint — native enums, check
constraints, collations, strict types — the test must assert the mapping, not the
behaviour.** `assert Subscription.__table__.c.status.type.enums == [...]` runs identically
on both dialects and states the fact the raw SQL depended on. Behaviour tests on SQLite can
only show that *something* happened, and "zero rows matched" looks like success.

**Corollary: `records_processed: 0` is not evidence of success.** The job reported a clean
run with zero rows for months. A cleanup job that is *always* a no-op is indistinguishable
from a healthy one unless something asserts it has work to do and does it.

**The other half of the diagnosis cost nothing because Sprint 740 built it.** That sprint
added `error_orig_fqn` / `error_orig_pgcode` to the failure log specifically so the next
failure would name its own root class. It did — and it named **two** unrelated classes
across the two jobs (22P02 and 42P01), where Sprint 740 had predicted one. Instrumentation
designed to answer a question answered a different, better question.

**And extract the closure.** The query lived inside the job function, reachable only through
`_run_cleanup_job` — own session, DB lock, commit, rollback, close. Patching all of that to
reach the query produces a test about the wrapper. Moving it to a module-level
`reset_upload_quotas(db)` (matching the function directly below it, which was already shaped
that way) made the regression test three lines long.

---

## A guard that cannot fail on the surface that matters is decoration (Sprint 784, 2026-10-20)

Sprint 784 added a `tool_count_consistency` rule to the documentation guard, because Sprint 689
expanded the catalog 12 → 18 and the prose never followed — including, for six months, the
**public** OpenAPI description served at `/docs`.

Writing the rule was easy. Two things about validating it were not.

**1. Running a guard is not the same as proving it.** The first draft passed on the fixed tree,
which looked like success. Then I re-introduced the defect to prove it would catch it — reverted
`backend/main.py` to `"12-Tool Audit Intelligence Suite"` — and the guard stayed **green**. It
scanned a list of documentation files and nothing else. I had guarded five internal docs and
missed the one string customers actually see.

**Pattern: regression-prove a guard against the surface you most care about, not a convenient
one.** If the proof case is the cheap one, a passing proof means very little. A
`_check_api_description` rule now covers `main.py`, and its failure message names
`scripts/openapi-snapshot.json`, because changing that string also moves the snapshot the
OpenAPI drift gate compares against — a guard should tell you about the second edit it forces
rather than letting CI discover it.

**2. A loose pattern is worse than no pattern, because it gets disabled.** The first pattern set
fired **14 times, 13 of them false.** Markdown heading anchors were the bulk: `## 5. Tool 3:
Journal Entry Testing` becomes `](#5-tool-3-journal-entry-testing)` in every link to it, so a
table of contents reads as a dozen different tool counts. One more false hit was a sentence I had
just written myself — "six tools are shown inline" — a true statement about the nav bar, not a
catalog claim.

A 14-violation wall of noise on a first run is how a gate gets commented out. The fix was to strip
link targets and inline code first, then match only three narrow catalog-claim forms. The 14 unit
tests added with it pin the **false-positive classes**, not just the true positives — anchors,
subset counts, version-history rows, per-tier allowances — so the next person to widen the
pattern finds out immediately.

**Corollary: parse the derived constant, never a literal.** The guard counts
`is_marketing_audit_tool=True` in `tools_registry.py` rather than hardcoding 18, and one test
asserts the text parser agrees with `MARKETING_AUDIT_TOOL_COUNT` itself. A guard carrying its own
copy of the number is just a fourth place for the number to drift.

**And ordinals are drift waiting to happen.** `ARCHITECTURE.md` labelled tools "Tool 1" … "Tool
11", an ordering the registry never promised and which must be renumbered on every catalog change.
Those labels are gone; the lists now carry names in registry order. Where a structural device
encodes something the data does not guarantee, the device is the bug.

**What the sweep found by looking.** Chasing counts surfaced three gaps that are not copy at all,
each filed rather than quietly fixed: the engagement layer's `ToolName` enum still has 13 members,
so the Anomaly Summary PDF tells practitioners there are 13 available tools (Sprint 787); the tool
navigation bar on every tool page lists 12 (Sprint 788); and the user guide documents 12 chapters
(Sprint 784b). A stale number is often a marker for a stale system, not just stale prose.
## A guard scoped to the shipped path lets the demo path drift (Sprint 779, 2026-10-20)

`test_memo_boundary_phrasing.py` has protected memo wording since Sprint 721. Its scope
was `backend/*_memo_generator.py` — a glob. `generate_sample_reports.py` does not match
that glob, and for months it emitted *"systemic review of procure-to-pay controls
recommended"*: a root-cause conclusion the shipped generators had already been cleaned
of, in the one file whose output a prospect is most likely to read first.

The deny pattern that catches the phrase (`\bsystemic\s+review.*recommended\b`) was
already in the test. Nothing was missing from the rules. Only the file list.

**Pattern: when a guard's scope is a glob, ask what produces the same class of output
and does not match it.** Here the answer was six files — the sample generator, the
anomaly-summary generator, the engagement dashboard, and three shared text modules.
Widening the scope surfaced nine more hits immediately:

- **Eight were legitimate** — ISA 265 *negative* use. Phrases like "does not constitute
  an audit opinion" and "classification … is a matter of auditor judgment" contain
  deny-list words precisely because they disclaim them, plus the literal title of PCAOB
  AS 1305. Those carry `# allow-deny-phrase: <reason>`, matching the existing precedent.
- **One was real** — `shared/follow_up_procedures.py` told the auditor a misposting
  "requires correction", which is a conclusion about the entity's records rather than an
  indicator. Reworded to "warrants further review".

A 9-to-1 signal-to-noise ratio is the shape to expect when widening a mature guard, and
it is worth it: the one real hit was in shared procedure text reused across tools.

**Corollary — exempt by category, not by annotation.** The widened scan also flagged
`anomaly_summary_generator.py`'s module docstring, where a `GUARDRAIL` note names the
ISA 265 sections the template deliberately refuses to produce. Naming them is the entire
point of the note. Annotating that line put a pseudo-comment inside docstring prose, so
the scanner now skips the module-docstring line range via `ast` instead: a module
docstring is maintainer documentation and never reaches a rendered PDF. When a guard
fires on something structurally incapable of causing the harm, fix the scope, not the
source.

**Correction to the sprint brief.** The brief said to rephrase the sample line to match
"the shipped wording", quoted as *"engagement team should evaluate whether procure-to-pay
procedures warrant expansion"*. That wording exists nowhere in the codebase — the brief
described a fix that had never landed. The actual shipped tier commentary in
`three_way_match_memo_generator.py:112` is *"Below best practice — investigate
patterns"*, and `tests/test_twm_memo.py:166` asserts the shipped finding text carries no
recommendation clause at all. Aligned to what ships, not to what the brief remembered.
**Verify the target wording exists before copying it; a brief is a memory, not a source.**

**The same scoping lesson, in a second guard.** `test_citation_consistency.py` scanned
customer-facing surfaces only. Sprint 717 swept the AS 1215 / JE Testing miscitation from
all five of them — and it then sat untouched for six months in
`docs/03-product/REPORT_STANDARDS_SPEC.md`, `docs/01-product/USER_PERSONAS.md` and
`docs/02-technical/ARCHITECTURE.md`. The AS-1215 adjacency check now runs over internal
docs too, on a **wider scope than the registration check**, which stays customer-facing
deliberately: internal docs legitimately discuss unregistered standards in post-mortems
and lexicon examples, and failing on those would make the guard noisy enough to get
disabled. Scope each assertion to the drift it is actually preventing.

Both guards were regression-proved before commit: the defects were re-introduced, each
test was confirmed to fail naming the offending file, then restored to green.

---

## Verify a dependency's failure contract; never let a mock define it (Sprint 774, 2026-10-19)

A ~5.5-month total production outage came down to three compounding mistakes, each of which looked like diligence at the time.

**1. A mock encoded a false model of the library, and the test validated the fiction.**

Sprint 696 added a fail-closed guarantee: in production, refuse to start if the configured Redis is unreachable. The implementation was:

```python
try:
    storage = RedisStorage(REDIS_URL)
    storage.check()
    return REDIS_URL
except Exception as exc:
    if RATE_LIMIT_STRICT_MODE:
        raise RuntimeError(...)
```

But `limits`' `Storage.check()` is literally `try: return self.get_connection().ping() except: return False`. **It never raises.** It signals failure by returning `False`, which the code discarded. So the fail-closed guarantee never once fired; a dead backend was silently classified as healthy at boot.

The tests passed — because they asserted against a mock built from the same wrong assumption:

```python
mock_storage_cls.return_value.check.side_effect = ConnectionError("Connection refused")
```

Real `RedisStorage` cannot produce that behavior. The test proved the code handled an impossible event while the actual failure mode went unhandled. Two tests, one for each failure path, both green, both meaningless.

**Pattern: when you mock a third-party boundary, the mock is a claim about someone else's code — and claims need evidence.** Before writing `side_effect = SomeError`, read the function. Cheapest possible check here was three lines in a REPL: construct the real storage against a refused port and print what `check()` actually returns. That would have taken under a minute and would have invalidated the whole design. The regression test now does exactly this — exercises a *genuinely* dead Redis (`redis://127.0.0.1:1`, connection-refused with no DNS wait) rather than a mock, with a control case asserting the failure path still fails without the fix, so the test cannot quietly stop proving anything.

**2. Fail-closed on a non-integrity control, with no self-heal path, is an availability bug.**

Even had the guarantee fired, the behavior was `sys.exit`/`raise` at import. The orchestrator then restart-loops forever. There is no path back without a human who already knows to look. Rate limiting is an *abuse* control, not an *integrity* control: brief under-enforcement is strictly less harmful than total unavailability. The fix (slowapi's `in_memory_fallback_enabled`) keeps enforcing the same limit values in-process and auto-restores shared counters when Redis returns — and at `numInstances: 1` the enforcement delta is exactly zero, so fail-closed was buying literally nothing while risking everything.

**Ask of any fail-closed decision: what restores service, and who has to be awake for it?** If the answer is "a human notices," the blast radius is however long it takes someone to notice. Here that was 5.5 months.

**3. A probe that shares a failure domain with its subject is not a probe.**

`/health/live` is documented as "zero I/O... if the process can serve this, it is alive." It was also decorated with `@limiter.limit(...)`, so it went through Redis. When Redis died, liveness returned 500 — indistinguishable from a wedged process. Every diagnostic surface (`/health`, `/health/live`, `/health/ready`, `/metrics`) failed in the same way for the same reason, so the system could not report its own illness. Render's dashboard showed the service healthy and unsuspended throughout.

**Check what a health endpoint actually touches, including via decorators and middleware — not just what its body does.** The docstring described the body; the decorator was the dependency.

**4. A failed deploy where the old instance keeps serving is indistinguishable from success.**

The Sprint 768 deploy exited 1 at startup (an unset `AUDIT_CHAIN_SECRET_KEY` that Sprint 768 itself had just promoted from a silent fallback to a hard-fail). Render correctly kept the previous image serving — so from outside, nothing changed. Sprint 768's P1 security fixes sat undeployed for 5.5 months while `tasks/todo.md` recorded the sprint as COMPLETE with a commit SHA. The sprint *was* complete; it just was not in production. The following PR then never deployed at all, because its files fell outside Render's `backend` rootDir and the commit was ignored.

**"Merged" is not "deployed," and "CI green" is not "running."** Post-merge verification must assert the live deploy SHA equals `main` and that the deploy status is live. Also note that a hard-fail guard added for good reasons is a deploy-breaking change if the corresponding env var is not set *first* — introduce the variable, then the guard.

**Meta-lesson.** All three of the first items were introduced by a security-hardening sprint doing the right thing in the abstract. Hardening changes the failure mode of a system, and the new failure mode needs the same scrutiny as the vulnerability it replaced. The question is never just "is this stricter?" but "what happens on the day this strictness triggers, and how do we find out?"

---

## Broaden your search before declaring victory; treat silence as a hypothesis (Sprint 732 Step 2c, 2026-04-28)

Sprint 732 chased a recurring `Cleanup job failed: InternalError` cleanup_scheduler bug for two days. Step 1 added `error_type_fqn` (resolved bare-class ambiguity to `sqlalchemy.exc.InternalError`); Step 2b added `error_orig_fqn` + `error_orig_pgcode` to surface the wrapped psycopg2 leaf class. Step 2c was supposed to read the leaf-class field on the next post-deploy cleanup cycle.

Two surprises blew up that plan in different ways.

**Surprise 1 — the pattern appeared to stop, but the silence was deploy-churn artifact, not a fix.** Post-Sprint-737-deploy at 13:00 UTC, zero `Cleanup job failed` events through the next 3h. I drafted a close-out doc treating Sprint 737 as the most-parsimonious-explanation structural fix, with a 24h verification window as the disambiguator between "structural fix" and "coincidence." **The window closed coincidence-positive earlier than 24h:** the 16:08 UTC `reset_upload_quotas` cycle (the first uninterrupted 60-min cycle after Sprint 739's 15:08 UTC deploy — every prior PR merge had reset the timer before a clean 60-min window could elapse) fired the same `InternalError` with the new observability fields populated: `psycopg2.errors.InFailedSqlTransaction` / SQLSTATE 25P02. Sprint 737 was NOT the fix. The 3h silence was entirely explained by deploy churn (4 successive merges in 2h, each resetting the scheduler's interval timer).

**Surprise 2 — a parallel failure was firing in plain sight throughout.** While querying Loki for `Cleanup job failed` (the specific Sprint 732 pattern), I missed `Bulk upload cleanup failed: ImportError` firing 4× per ~30-min cycle from the SAME `cleanup_scheduler` logger. Different error message, different code path, both pre-Sprint-737 *and* post-Sprint-737. It had been broken in production since Sprint 720 (8+ sprints) — Sprint 720's `bulk_job_store` refactor removed `_evict_stale_jobs` from `routes/bulk_upload.py` but the cleanup_scheduler call site at `cleanup_scheduler.py:403` was orphaned. My Sprint 732 queries' specificity hid it. Surfaced only when I broadened the query from `text=["Cleanup job failed"]` to `text=["cleanup_scheduler"]` for unrelated post-deploy verification. Fixed in Sprint 739 (~30 lines deleted).

**Pattern A: when investigating a logger's failure class, run at least one *broad* query before narrowing.** Count the distinct failure messages from the logger over a representative window — not just the one you're hunting. If two error messages from the same logger have different texts, neither's silence implies the other's. Sprint 732's queries were filtering for `Cleanup job failed`; the bulk_upload bug logged `Bulk upload cleanup failed`. Same logger, different text, both alive, only one chased.

**Pattern B: treat silence as a hypothesis, not a result. (VINDICATED.)** When a failure pattern stops, the question isn't "is this fixed?" but "do we have enough data to tell apart a structural fix from coincidence?" Define the verification window upfront — duration, what would resume the failure, what counts as "still working." Sprint 732's draft close-out picked a 24h window; the window closed at ~3h instead because Sprint 739's deploy was the first to leave a clean 60-min cycle uninterrupted, and the cycle fired with the failure intact. If I'd skipped the verification window and merged the close-out doc as "RESOLVED," it would have been wrong within hours. **The discipline is: write the disambiguator BEFORE celebrating, even if you have to update the close-out doc once it triggers.**

**Pattern C: an unexpected fix can be the right answer — but only if the disambiguator confirms it. (DISPROVEN-FOR-THIS-CASE.)** I'd hypothesized Sprint 737's removal of dead-code in-process schema patches plausibly closed a connection-pool/transactional issue bleeding into cleanup-scheduler sessions. The verification window disproved that: pattern resumed once a deploy had a clean 60-min window. Sprint 737 was a clean dead-code removal, full stop, with zero connection to Sprint 732's bug. **The lesson holds the other direction too:** when a "dead-code removal" appears to fix something, don't accept the attribution without the disambiguator confirming. Both directions of the lesson are about resisting easy explanations. The actual root cause turned out to be a transaction-state cascade in the lock-release path (`InFailedSqlTransaction` SQLSTATE 25P02 — the cleanup_func body fails first, the `with_scheduler_lock` finally block's DELETE then fails on the aborted session, and the masked-symptom 25P02 is what ends up in the log). Filed as Sprint 740 for the structural fix.

**Companion pattern from Sprint 736's lesson** (above): "verify the safety net is actually firing before recommending 'leave alone.'" That lesson and these three together describe the full discipline — verify both the *presence* of what you think is happening (the safety net firing) and the *absence* of what you think isn't (the parallel failure you didn't search for). Specificity is a feature when you know what you're looking for and a bug when you don't.

---

## Keep github in sync with local so Claude and Codex don't disagree (2026-04-28)

CEO uses two AI roles in this project:

- **Claude** (this assistant) — main brain + coder, has full local filesystem access and runs locally
- **Codex** — code reviewer, has github-only access

When local audit artifacts, todo.md updates, lessons.md updates, or doc changes accumulate locally without being pushed, **Codex's recommendations are based on stale state while Claude is reasoning from ground truth.** The CEO has reported asking Codex for input and getting back recommendations Claude flagged as outdated. The asymmetry isn't a Codex bug — it's a workflow gap.

Surfaced concretely on 2026-04-28 when 6 days of nightly audit artifacts (`reports/nightly/2026-04-{23..28}.md` + 36 sentinel JSONs + run logs + agent sweep reports) had accumulated locally but never pushed. Codex reviewing the project at any point in that window would have been advising on a 6-day-stale audit picture. Cleared via `fix:` batch commit (PR #124, ~5,800 lines / 59 files).

**Pattern:** Operational artifacts that the project's audit trail depends on — `reports/nightly/*`, `reports/audit-*.md`, `tasks/sprint-plan-*.md`, `tasks/lessons.md`, `tasks/todo.md`, `docs/03-engineering/*` — are decision-state, not just file-state. They MUST get to github promptly. Local-only retention is a sync hazard.

**Discipline (Claude side):**

1. **At session-end OR any natural checkpoint** (between merges, while CI runs, when waiting on a deploy), run `git status` and check for untracked or modified files in `reports/`, `tasks/`, `docs/`. Surface them to the CEO with "want to commit?" — even if the CEO didn't explicitly ask. Don't accumulate.
2. **The hotfix batch-commit pattern is the right shape** (`fix: nightly audit artifacts <date> batch + agent sweep reports`). Match the precedent (`9820bb2`, `7915d77`, `22e16dc`).
3. **Ephemerals (`.hypothesis/`, `frontend/playwright-report/`, scratch like `tmp_report.py`) stay out** — those aren't decision-state, they're just noise. Don't commit them; consider proposing `.gitignore` additions if they keep showing up.

**Why this matters more than it seems:** the CEO's prompt that produced this lesson was about a 2-hour log-off window. The workflow gap is an everyday tax — every time he asks Codex for input on something Claude has already worked through locally, the recommendations either contradict or miss the load-bearing context. Closing the gap is cheaper than reconciling the recommendations after.

**Companion to the Sprint 716 lesson** ("Verify the code is deployed before debugging 'why isn't runtime doing X'"): same shape, different surface. Sprint 716's version is "deployed code lags local code"; this one is "github code lags local code"; both produce the same class of failure mode where the AI is reasoning from one state and reality is a different state. Default to: state = github = local = production, in that order of canonicalness, and any divergence is a smell.

---

## Verify the safety net is actually firing before recommending "leave alone" (Sprint 736)

CEO asked for a comprehensive backend/frontend refactor pass authored by Codex. I correctly surfaced the directive's conflicts with the Deferred Items table (Sprint 710 had already done much of it; four targets were explicitly deferred or rejected with reasons). For the one piece I scoped into a research sprint — `init_db()`'s 7 in-process schema-patch blocks — I produced an inventory and recommended option **(c) "leave alone, document the contract"**. My rationale leaned on "consolidating to Alembic-only would create a new fail-closed mode that needs runbook coverage" — i.e., the patches are a real safety net we'd be removing.

CEO pushed back with one sentence: "what do you mean cost vs pain, I'd rather just do this right and have it fixed." That forced me to verify the premise instead of paraphrase it. One grep for `alembic upgrade` and one read of `backend/Dockerfile` later, the picture flipped: Sprint 544c had already wired `alembic upgrade head` into the Dockerfile CMD. By the time `init_db()` runs in production, schema is at head. `conftest.py` uses `Base.metadata.create_all()` against current models, which produces current schema directly. The patches don't fire on the production path or the test path. They are not a safety net I was about to remove — they are ~130 lines of dead code I was about to recommend keeping. The "operational coverage for a new fail-closed mode" cost I cited was for a fail-closed mode that already existed and was already documented in `docs/runbooks/emergency-playbook.md` §4.

The recommendation flipped from (c) to (b) and Sprint 737 was added to execute the consolidation pre-4.1. CEO's pushback wasn't preference — it was correct on the merits, and I would not have caught it without being asked.

**Pattern:** Whenever a recommendation reduces to "leave the safety net in place," the *next sentence* in the analysis must be evidence that the safety net is currently firing — not "it's there if needed" but actually *firing*, in the actual deploy or test path, on the current schedule. Cheap probes: `grep` for the invocation in Dockerfile/Procfile/start scripts; check `conftest.py` for which init path tests use; read the last N production startup logs for the safety net's signature. If the safety net hasn't fired in months and would only fire on a hypothetical, it isn't a safety net — it's dead code wearing a costume, and "leave alone" defaults to keeping the costume.

**Companion pattern:** When the CEO pushes back on a defensive framing ("cost vs pain", "blast radius", "muddier triage"), treat it as a request to re-derive the cost from evidence rather than restate the framing. The pushback is doing free QA on the rigor of the recommendation; either the recommendation survives the rederivation (and gets stronger), or it flips (and the team avoids a wrong call). The 2026-04-27 Codex-directive triage is the cleanest in-repo example: pushback caught both the framing weakness AND a years-old dead-code path that would otherwise have shipped Sprint 737 too late or not at all.

---

## Log-emission tests must inspect message content, not just count records (Sprint 715)

Sprint 713 added a SendGrid-403 warn-path: catch `SendGridHTTPError`, return `EmailResult(success=False, message="Email delivery failed (SendGrid 403).")`, let `safe_background_email` log a `WARNING`. The accompanying test (`test_background_email_logs_warning_not_error_on_failure`) asserted `len(warning_records) >= 1` and `error_records == []` — and stopped there. It never read the warning's `getMessage()`. The wrapper had a typo (`getattr(result, "error", "unknown")` against an `EmailResult` whose attribute is `message`), so every production warning would have read `Background register_verification send failed: unknown` — useless for the very investigation Sprint 715 was scheduled to perform 24h later. The bug only surfaced because Sprint 715 traced the emission chain end-to-end before reading logs; if 403s had been frequent, we'd have stared at "unknown" for weeks.

**Pattern:** When a test asserts "a log line was emitted at level X," it must also assert the message contains the *facts the line exists to communicate*. For an exception-handler warn-path, that's the exception's identifying detail (status code, error class name, masked recipient — whichever the path is supposed to surface). Counting records protects against "ERROR was raised when WARNING was expected" but not against "WARNING fires with empty content" — and the latter is silent in production until someone reaches for the logs.

The Sprint 715 test now asserts the warning came from `shared.background_email`, contains the label, contains `"403"`, and does *not* fall back to `"unknown"`. Apply the same shape to any new log-emission contract: `severity + emitter + identifying detail + absence of fallback sentinel`.

---

## Two-form code paths need parity tests, not just a one-form test (Sprint 718)

The CSRF middleware's `_extract_user_id_from_auth` was tested against Bearer-header inputs and shipped years ago. The production browser path was later moved to HttpOnly cookies — but the function was never updated to read the cookie. Result: every browser POST/PUT/DELETE/PATCH ran with `expected_user_id=None`, silently disabling the CSRF user-binding check at line 427. The 2026-04-24 security review found it; the test suite didn't because there was no test that asserted "Bearer and cookie produce the same answer."

**Pattern:** Anywhere an interface accepts the same input through two surface forms (Bearer/cookie, query/body, header/cookie, single-event/duplicate-event, single-worker/multi-worker), there must be a parametrized parity test that runs both forms through the same helper and asserts equivalence. Adding a new form without the parity test is the failure mode — it's not "I forgot to write a test for the new form," it's "I ran the existing tests, they passed, I shipped."

The Sprint 718 fixture: `tests/test_auth_parity.py` parametrizes over `(bearer, cookie)` for every auth-extracting helper. The same shape will be used for Sprint 719's webhook idempotency contract (single-event + duplicate-event), Sprint 720's multi-worker bulk upload (single-worker + multi-worker), and any future security-helper that extends to a new input form.

**Companion guardrail:** Sprint 718 also added an AST-scan test (`test_no_process_local_auth_state.py`) that fails if any module-level mutable container is introduced into `auth.py` or `security_middleware.py`. The IP-failure tracker bug class was "in-process state in a request handler"; the fix was a Redis-backed shared module + a scanner that prevents reintroduction. Same shape will repeat in Sprint 720 (no module-global state in `routes/`).

---

## Pair every "stated truth" with a CI-enforced source-of-truth (Sprint 717)

Sprint 689g flipped `CANONICAL_TOOL_COUNT` 12 → 18 on the backend in one bulk pass that was supposed to also update every marketing/legal/doc surface. The pass missed `frontend/src/content/tool-ledger.ts` (still 12 entries), `BottomProof.tsx` ("Twelve audit-focused tools"), `ToolLedger.tsx` (header said "Eighteen" but aria-label said "Twelve"), the pricing/terms pages, and `tools/page.tsx` test counts. Two days later the agent sweep flagged 11 drift surfaces with three different numbers visible on production simultaneously. The root cause wasn't carelessness in 689g — it was that "stated tool count" had no canonical source; every surface was a hand-typed mirror, so any bulk-edit that missed one stayed silently wrong.

The same shape produced AS 1215 fabrication: the CLAUDE.md "Key Capabilities" line cited PCAOB AS 1215 as a JE-testing standard for over a year, propagating to USER_GUIDE.md, status.json, the Trust page, and the standards-specimen file. AS 1215 governs audit *documentation* — not procedures — but with no mechanical check, the wrong citation traveled wherever the marketing copy did.

**Pattern:** Anything whose "truth" gets quoted in more than one place — counts, citations, version numbers, pricing — needs a single Python/TS source-of-truth module *and* a CI test that fails when human-edited surfaces disagree. In Sprint 717: `backend/tools_registry.py`, `backend/standards_registry.py`, `tests/test_catalog_consistency.py`, `tests/test_citation_consistency.py`. The CI tests caught 4 unregistered standards (ASC 842, IFRS 16, ASC 326, IAS 1) on first run — exactly the kind of slow-drift the registry is designed to surface immediately.

The discipline: **whenever you find yourself updating the same fact in 3+ files, stop and add the registry + test before finishing the edit**. Don't try to be more careful next time — be unable-to-be-wrong next time.

---

## Verify the code is deployed before debugging "why isn't runtime doing X" (Sprint 716)

During Sprint 716's Grafana Loki rollout, after setting the `LOKI_*` env vars on Render I spent ~15 minutes chasing hypotheses about why Loki showed zero streams: wrong label (`service_name` vs `service`?), cardinality rejections, handler thread dying silently on an unhandled exception. Opened Render's Web Shell, ran `python -c "from config import LOKI_ENABLED"` and got `ImportError: cannot import name 'LOKI_ENABLED' from 'config'`. The deployed image was Sprint 713's commit `2b92b771` — Sprint 716's commit `8e65d30e` was local-only; I'd never pushed to GitHub. Render's env-var-save redeploy rebuilt the OLD main, not the new code. **Pattern:** Before diving into "the app isn't doing X despite the code saying X," spend 30 seconds proving the target code is actually on the running instance. Cheap probes: Render Web Shell `python -c "from <module> import <new_symbol>"`, a `grep -c` on a known new log line in Render's log tail, or a `curl /health` that returns a version SHA. Especially true at the end of a sprint where commits and env-var changes can arrive out of order — the env var set is often what people *remember* as "shipping," but on Render it only redeploys the main branch's current tip. The same failure mode hit the Sprint 551-era Stripe deploy pattern; worth generalising into a sprint-close template step.

---

## Render Log Streams ≠ Grafana Cloud Loki — check protocol before scheduling (Sprint 716)

Sprint 716 was initially scoped as "wire Render's built-in HTTPS log drain → Loki." Mid-provisioning, once the Render Add Log Stream form loaded, the `e.g., logs.papertrailapp.com:34302` placeholder revealed Render's integration surface is TCP/syslog only — Datadog, Papertrail, Logtail, LogDNA, Cribl. Grafana Cloud Loki only ingests HTTPS POST at `/loki/api/v1/push`. The two don't bridge without a sidecar. The sprint was re-scoped mid-flight to an in-process Python handler (`backend/loki_handler.py`) that pushes HTTPS directly, which kept the "free + no new infra" constraint intact and required no Render log drain config at all. **Pattern:** Before scheduling any observability sprint that involves "service X forwards to service Y," verify the *protocol* match (TCP/syslog vs. HTTPS push vs. OTLP vs. gRPC) up front, not just that both services exist and are "free." Destinations advertised as "integrations" on one side often require a specific wire format the other side doesn't speak natively. One 2-minute check of the target platform's "Supported destinations" list — or, if that's absent, the example endpoint placeholder — would have caught this before the sprint plan was committed to `todo.md`.

---

## `logger.exception()` on a user-facing 400 is a Sentry escalation (Sprint 713)

Sentry SDK's default `LoggingIntegration(event_level=ERROR)` promotes every `logger.exception()` call into a Sentry error event — regardless of whether the exception is a 500-class bug or a handled 4xx user-error. Three Sentry issue classes surfaced during Sprint 711's Phase-3 triage turned out to be caught, 400-mapped upload errors that `logger.exception` had promoted from "user sent bad bytes" to "something the app did wrong." The fix: `logger.warning("... rejected [%s]: %s", type(e).__name__, e, exc_info=True)`. Traceback still lands in Render logs via `exc_info=True`; Sentry stays quiet because WARNING is below the event threshold (captured only as a breadcrumb). **Pattern:** Reserve `logger.exception` for code paths where the exception represents an actual app defect the dev team should look at. For caught-and-mapped-to-HTTP-4xx branches in route handlers and the scaffold layer, use `logger.warning(..., exc_info=True)`. Sentry's error-events feed should mean "the app did something wrong," not "a user uploaded a malformed file" — conflating the two makes the real incidents impossible to triage. This is the third sprint in three weeks to touch Sentry log-level semantics (711 added explicit `capture_exception` for a silent swallow, 712 fixed a false-green from a log-level-independent parse bug, 713 downgraded user-error escalations) — worth a lint rule on future route handlers.

---

## Screenshotting a Render env-var edit form leaks secrets into the tool log (session 2026-04-23)

During R2 provisioning, after pasting the `paciolus-exports-rw` Access Key ID and Secret Access Key into a Render env-var Edit form, I took a screenshot to show the "Save, rebuild, and deploy" button location — and Render's edit mode renders every value as a plain `<textarea>` with the raw text exposed, so both secrets landed in the screenshot and therefore in the tool-result log. The view-mode surface is safe (values are masked as `••••••••••` until the eye icon is explicitly clicked), but the edit-mode surface is not. Mitigation took a full Cloudflare token roll (Roll → re-copy → re-paste) before the compromised values could be saved to Render. The earlier 2026-04-22 DATABASE_URL screenshot leak during the orphan-DB investigation was the same failure mode; this is a recurring class of bug that warrants a standing rule.

**Pattern:** Never screenshot a cloud-provider env-var page (Render, Vercel, Cloudflare Workers, AWS, etc.) while in edit mode. To drive a button on an edit form, use `find` + `ref_id` click, or DOM-based `querySelector` + JS coordinate extraction, never a pixel screenshot. Before every screenshot on a credentials-adjacent surface, ask "is any form field on this page in edit mode?" If yes, do not screenshot — use JS DOM extraction with a strict allowlist (labels/counts only, never values, never lengths that imply value shape beyond generic format classes). Safe alternatives: masked view-mode screenshots (values show as dots), JS-only length-and-regex checks (e.g. `valueLength: 32, looksLikeHex32: true`), or narrating the UI position from DOM rect data. When a credential does leak: the remediation order is **(1) do not Save the form** (containment — keep the exposure DOM-only), **(2) rotate the credential at the issuer**, **(3) re-paste into the still-open form with the rotated value**, **(4) only then Save** — this prevents the compromised value from reaching the secrets store, where recovery is much harder than rolling a single token.

---

## A coverage-sentinel gap can be dead code, not a testing gap (Sprint 676)

Sprint 676 targeted three 0%-coverage files from the nightly Coverage Sentinel report. Investigation showed `services/organization_service.py` (180 statements, 0%) had **zero imports anywhere** — Sprint 546's archive claimed "Refactor 5: organization.py → services/organization_service.py + thin routes" but only created the service module, never wired the routes to use it. Writing tests for the orphan would have inflated the coverage number without improving safety; deletion was the right move. **Pattern:** Before writing tests to fix a coverage gap, `grep -r <module_name>` across the whole repo. If nothing imports it, the gap isn't a test gap — it's dead code from an incomplete refactor. The sentinel report doesn't distinguish between "untested" and "unused"; you have to.

---

## Overnight scanners can scan the wrong Python (Sprint 675)

The Dependency Sentinel was executing `pip list --outdated` against `C:/Python312/python.exe` (system Python), not `backend/venv/Scripts/python.exe` (the venv that mirrors production `requirements.txt`). System Python had drifted: `fastapi 0.135.2` vs. venv `0.135.3`, `stripe 15.0.0` vs. venv `15.0.1`, `SQLAlchemy 2.0.48` vs. venv `2.0.49`. The nightly report flagged packages as "outdated" that were actually current in production — three nights of false YELLOW. Root cause: a pre-existing `PYTHON_BIN` constant in `scripts/overnight/config.py` pointed at the venv but was unused; `SYSTEM_PYTHON` was used instead. **Pattern:** Any CI/nightly tool that scans the environment (pip, npm, bundler) must scan the *same* environment that production installs into. When two Python interpreters exist on a machine, pin the scanner to the one backing the app, and make the fallback explicit.

---

## A nightly pytest subprocess timeout is a ticking clock, not a background concern (Sprint 674)

2026-04-17 nightly ran RED because backend pytest hit the 600s subprocess timeout at 601.8s — first time ever. 2026-04-18 completed in 581.2s. Test count growth was 7,405 → 7,804 across three days. At that growth rate, a fixed per-suite timeout will fail again inside a sprint or two. **Pattern:** When the nightly driver subprocess timeout is within 5% of the observed runtime, treat it as a same-week fix, not a future problem — the next test-adding sprint will re-trigger it. The bias should be toward *more* headroom (2×–3× of current runtime), not less; a sleeping wait that could have been shorter costs nothing, but a re-triggered timeout costs a lost nightly signal.

---

## Diagnostic ingestion bypasses the parser dispatcher (Sprint 665)

While building the Sprint 665 remediation harness, every PDF and DOCX input failed the diagnostic pipeline with an incongruous pandas error (`'io.excel.zip.reader'` / `Excel file format cannot be determined`). Root cause: `backend/audit/pipeline.py:73` calls `process_tb_chunked(file_bytes, filename, chunk_size)` in `security_utils.py:201`, which only attempts `read_csv_chunked` → falls back to `read_excel_chunked`. It never dispatches to `parse_uploaded_file_by_format` (`backend/shared/helpers.py:797`), which is the correct entry point that knows about PDF, DOCX, ODS, OFX, QBO, IIF, TSV, TXT. PreFlight uses the dispatcher; diagnostic does not. Every file format the brief says is "supported" is actually only supported on the preflight side. **Pattern:** Two-pipeline features (preflight + diagnostic) need the same ingestion entry point, not parallel copies that drift apart. When a format is added, `grep` every place that accepts `file_bytes + filename` to ensure *all* ingestion paths route through the shared dispatcher.

---

## Remediation harness over pytest when expected values are moving (Sprint 665)

For CEO-facing sequential remediation work where each sprint will change the expected output of the preceding sprint, a pytest regression suite is the wrong tool. Hardcoded expected values in assertions would fight us across six sprints. Instead: a single Python script that parses, runs both pipelines, and writes one diffable JSON per test file per sprint (`reports/remediation/sprint-NNN/<stem>.json`). Diff is done in review, not in code. Expected results live in the sprint review sections, not in `assert` lines. **Pattern:** When the "expected" side of a test is going to change N times in the next N sprints, capture state to diffable artifacts instead of asserting. Pytest is for regression; this pattern is for progression.

---

## Audit the file before auditing the code on a misdiagnosed bug report (Sprint 666)

The CEO remediation brief v6 Issue 9 attributed `tb_unusual_accounts.csv`'s $306,262 variance to "RFC 4180 quoted field handling" — claiming account names with embedded commas caused column shift and phantom imbalances. Before touching the CSV parser I ran pandas directly on the file: every quoted field parses cleanly (none actually contain embedded commas — just parentheses, question marks, slashes which are not CSV-special), every row lands in the right columns, and the data-only sum is $5,791,962 debit / $5,490,500 credit for a genuine $301,462 imbalance. The file was never built to balance. The totals row in the file claims $5,681,962 each side but the actual data sums to different numbers. After Sprint 666's totals-row exclusion the reported variance is $306,262 — unchanged from baseline but now for the right reason (real data imbalance, not a totals-inclusive artifact).

**Pattern:** When a bug report attributes a number to a parser/algorithm cause, verify the number by computing it against the source data by hand before writing a "fix." A misdiagnosed report can waste a sprint building defenses against a non-existent bug, leaving the real cause untouched. The right first step on any "parser is mishandling X" claim is a 5-minute manual sum in a REPL — not a dive into `pd.read_csv` options.

---

## Silent-success bugs surface only when you explicitly test the failure mode (Sprint 666)

The Sprint 666 zero-row guard uncovered a pre-existing pytest case (`test_audit_core::TestEdgeCases::test_empty_file`) that was *validating* the silent-success bug itself — it asserted `status == "success"`, `balanced == True`, `row_count == 0` on a headers-only file. The test was green for however many sprints that bug existed, because nobody had asked "is returning 'balanced' on a zero-row ingestion the right behavior?" The bug was structural, the test was its fossil record. **Pattern:** When fixing a silent-success class of bug, grep for tests that assert the silent-success shape and rewrite them to the post-fix contract BEFORE running the full suite. A green test that encodes a wrong invariant is worse than a missing test — it will actively defend the bug against any fix. Look for tests with names like `test_empty_*`, `test_zero_*`, `test_missing_*` when the bug is about input edge cases.

---

## Breaking API shape changes require simultaneous backend + frontend + test updates (Sprint 544)

When changing a response shape (e.g., `clients` → `items` in PaginatedResponse), ALL consumers must be updated atomically: backend routes, frontend types, frontend hooks, AND test mocks. In Sprint 544, changing the list key from domain-specific (`clients`, `engagements`, `activities`) to generic (`items`) required updating 4 routes, 4 hooks, 3 type files, and 4 test files. Missing any one creates silent data loss (hook reads `data.items` but API returns `data.clients` → empty list). **Pattern:** Before making a breaking shape change, `grep` for ALL consumers of the old key across both backend and frontend.

---

## Mypy error counts can explode silently with test file growth (Sprint 543)

A deferred item from Sprint 475 said "68 errors across 2 files." By Sprint 543, the same `mypy tests/` command showed 804 errors across 135 files because 133 test files had been added since the original estimate. **Pattern:** Deferred items with numeric estimates should include a "last measured" date. Re-measure before committing to a sprint scope.

---

## Cover page metadata must propagate through ALL code paths, not just one (Sprint 541)

When a fix is applied to a shared field (like `fiscal_year_end` on `ReportMetadata`), verify every code path that constructs that metadata — not just the one that triggered the bug report. Sprint 540 fixed `fiscal_year_end` for financial statements only (`pdf_generator.py`), missing the 17 testing/tool memo generators that construct `ReportMetadata` via a different path (`generate_testing_memo()` + custom generators). **Pattern:** When fixing a shared data structure, `grep` for ALL constructor call sites. If N call sites exist and only 1 was fixed, the remaining N-1 are still broken.

---

## New severity tiers require three-layer propagation: engine → score → UI (Sprint 538)

1. **Tier cascade ordering must respect keyword intent over general-purpose rules.** Sprint 537 added an "informational" tier for transactional accounts (Cash, AR, AP), but placed the keyword check AFTER the 10%-of-TB escalation. For entities with concentrated cash positions (>10% of TB), Cash would be escalated to "material" before the informational check could downgrade it — defeating the Sprint 537 design intent entirely. **Pattern:** When adding a new classification tier with explicit keyword lists, the keyword check must precede any general-purpose escalation rule. Keyword assignments are specific; escalation rules are general. Specific should override general.

2. **New severity tiers need score contribution caps.** Each informational finding contributed +1 risk point with no cap. For a bank with 30 transactional accounts, that's 30 points from informational findings alone — pushing the score into "elevated" (threshold: 26). Informational findings are definitionally low-signal; their aggregate should never independently change the risk tier. **Pattern:** When adding a new lowest-severity tier, always cap its score contribution (e.g., `min(count, 5)`) so the tier cannot overwhelm the scoring model.

3. **Bare substring keywords need scope validation against other detection systems.** The bare keyword `"cash"` in the informational list matched "Cash Clearing" (a suspense concern) and "Cash — Intercompany" (a related-party concern). Similarly, `"loan"` in the suppress list matched "Shareholder Loan" (a related-party concern). **Pattern:** When adding keywords to any classification list, grep all other keyword lists (suspense, related-party, carve-outs) for conflicts. If the same account name triggers contradictory signals, narrow the keyword or add a carve-out.

---

## PDF report totals must match displayed detail rows (Sprint 522)

The Minor Observations total was summing `abs(amount)` while detail rows displayed signed values. Any CPA would catch a total of $107,900 when the visible amounts sum to $58,900. **Pattern:** When a total row summarizes a visible column, the aggregation function must match the display function exactly — no silent transformations. If signed display is confusing in context, add a footnote rather than silently changing the math.

---

## Risk scores require transparency — unexplained numbers are arbitrary (Sprint 522)

A composite risk score (52/100 — HIGH RISK) presented without decomposition invites skepticism. Returning factor-level contributions from `compute_tb_risk_score()` as a tuple `(score, factors)` was a minimal change (10 lines) that made the output auditable. **Pattern:** Any computed metric in a professional deliverable should expose its inputs. If the scoring function returns a single number, refactor it to return `(result, explanation)`.

---

## Directive Protocol is non-negotiable — urgency does not waive documentation (Audit 29)

Sprint 520 fixed a CRITICAL cross-tenant data leakage vulnerability and 3 other billing security findings — the most security-sensitive sprint in the project's history — with zero todo.md presence. Sprint 516 (DEC remediation, 17 findings) had the same gap. Both bypassed the Directive Protocol entirely: no plan, no checklist, no verification section, no commit SHA recorded, no lessons captured. Sprint 519 (architectural refactoring) in the same cycle got full lifecycle tracking.

**Root cause:** Urgency bias. Security-critical work feels time-sensitive, creating a "just commit it" impulse that skips documentation. But security sprints warrant MORE documentation discipline, not less — they are the sprints most likely to be audited, questioned, or referenced later.

**Enforcement:** A `commit-msg` hook now rejects any commit matching `Sprint N:` unless `tasks/todo.md` is staged. This makes the protocol mechanically enforced, not discipline-dependent. Hotfix commits (`fix:` prefix) are exempt by design.

**Pattern:** Never skip the Directive Protocol for any sprint-classified work. If the work is urgent, write a minimal todo.md entry (sprint number, goal, verification result, SHA) — 5 lines takes 2 minutes and creates an audit trail. The commit-msg hook is the backstop, not the primary discipline.

---

## Billing security patterns — tenant isolation, Stripe line items, webhook idempotency (Sprint 520)

1. **Billing analytics endpoints must scope queries by user_id/org_id from the start.** The analytics module (`billing/analytics.py`) had 5 metric queries that returned global aggregates — any verified user could see all customers' billing data. The fix (`_resolve_scoped_user_ids()`) resolves org membership and scopes every query. **Rule:** When writing any new billing analytics query, always accept a `user_id` or `user_ids` parameter and filter by it. Never write an unscoped aggregate in billing code.

2. **Stripe subscription line items must be matched by price ID, not by index.** `add_seats` and `remove_seats` assumed the seat add-on was always `subscription.items[0]`. For subscriptions with multiple line items (plan + seat add-on), this targeted the wrong item — mutating the plan price instead of the seat quantity. **Rule:** Use `_find_seat_addon_item()` with `get_all_seat_price_ids()` to find the correct line item. Only fall back to `items[0]` for single-item subscriptions. Raise `ValueError` for ambiguous multi-item subscriptions rather than guessing.

3. **Webhook handlers must deduplicate by event ID before dispatch.** Stripe can replay webhook events (retries, manual resends). Without deduplication, the same event could be processed twice — creating duplicate billing events, double-counting revenue, or applying discounts twice. **Rule:** Record `stripe_event_id` in a `ProcessedWebhookEvent` table before dispatch. Return 200 immediately for duplicates. This is a Stripe best practice that should have been implemented from Sprint 362 (initial webhook handler).

4. **Billing event enum variants must match Stripe event semantics precisely.** `handle_subscription_trial_will_end` was recording `TRIAL_EXPIRED` — but the trial hasn't expired yet, it's about to end. This mislabels the billing timeline and corrupts analytics. **Rule:** When mapping Stripe webhook event types to internal enums, the enum value must describe the state AT the time the event fires, not a future state.

---

## Procedure text and score labels must be contextually differentiated, not template-driven (Sprint 524)

Sprint 522 introduced suggested procedures and risk decomposition, but the initial implementation used generic templates. All round-dollar findings got the same procedure language regardless of whether it was a single $100K balance or an 8-occurrence pattern. Score decomposition showed "Material exceptions (3 × 8)" — a formula, not a finding. A CPA reviewer reads the procedure as guidance for their next step; if two findings with different risk profiles receive identical procedures, the output looks machine-generated rather than analytically informed.

**Pattern:** When generating professional deliverable text (procedures, labels, descriptions), the function must inspect enough anomaly context (anomaly_type, account name, transaction_count, issue text) to produce differentiated output. If two findings produce identical text, that's a design defect. Split procedure keys by relevant sub-patterns (single vs. repeated, AR vs. general asset) and use data-driven dispatch.

---

## Council deferral vs. CEO override — respect the decision hierarchy (Sprint 519)

The council (Critic + Guardian) recommended deferring Phase 5 service extraction due to diminishing ROI. The CEO overrode: "I also want architectural purity." The council's analysis was sound — the extractions were incremental, not transformative — but the CEO's architectural preference is a legitimate priority that outweighs marginal ROI calculations. **Pattern: council advises, CEO decides. When the CEO overrides, execute fully without half-measures. Log the override in todo.md for future context.**

---

## Task Management Archival Discipline (Audit 28 / Council Decision)

1. **Passive thresholds fail during sustained campaigns**: The 5-sprint archival threshold rule existed but was silently violated 12 times across 12 consecutive directive cycles during the Report Enrichment campaign (Sprints 499-515). A passive rule with no active trigger point is insufficient when sprint velocity is high. Fix: a proactive self-check added to Directive Protocol step 1 — "If Active Phase has 4+ completed sprints, archive first."

2. **The protocol assumed phased delivery; the project shifted to continuous delivery**: The Phase Lifecycle Protocol was designed for named phases with clear start/end boundaries. When work runs as a continuous campaign without phase declarations, the "wrap phase → archive" trigger never fires. The 5-sprint standalone threshold was designed as a patch for this gap but depends on agents counting sprints — which they don't do naturally. The self-check guardrail fires at step 1 of every directive, creating a reliable trigger.

3. **Non-sprint commits need a lightweight tracking mechanism**: The Directive Protocol's binary model (everything is a sprint) creates overhead aversion for small fixes. Commit `fb8a1fa` (22 insertions across 16 files) was a content accuracy fix that didn't warrant a full sprint lifecycle. Fix: a `## Hotfixes` section in todo.md with one-line entries, and a classification rule (step 1b) distinguishing sprint-level work from hotfix-level work.

---

## Anomaly Summary Report (Sprint 515)

1. **Auditing standards vs. FASB codification**: The anomaly summary is an engagement-level aggregation report, not a tool-specific diagnostic. Its authoritative references should cite auditing procedure standards (AU-C § 265/330/520, PCAOB AS 1305/2305) rather than FASB ASC codification entries. Render these directly in the generator rather than through the YAML content library, since they don't follow the codification/statement schema.

2. **Phantom trailing pages from standalone disclaimers**: When a report ends with a standalone `Paragraph(DISCLAIMER_TEXT, ...)`, the PDF renderer may place it on a new page — creating a phantom blank page with only a disclaimer. Since `draw_page_footer` already renders the disclaimer on every page footer, the trailing standalone disclaimer is redundant and should be removed.

3. **Cross-reference mappings should be exhaustive**: When adding WP-XXX-001 cross-references for findings, map every ToolName enum value — not just the tools that happened to have findings in the sample data. This prevents KeyError when a new tool generates findings in production.

---

## Accrual Completeness Estimator (Sprint 513)

1. **Account classification ordering matters**: When classifying liability accounts into analytical buckets, check the most specific patterns first. "Deferred Revenue" must match before generic "deferred" to avoid misclassifying it as "Deferred Liability". The ordering (deferred revenue → accrued → provision → generic deferred) is critical.

2. **MemoSubsection style doesn't exist**: The `create_memo_styles()` from `memo_base.py` does not include a "MemoSubsection" style. For subsection headings within a section, use `<b>Bold text</b>` within a "MemoBody" paragraph instead of referencing a nonexistent style key.

3. **Analytical ratio integrity**: When a ratio calculation includes unrelated account types (e.g., Deferred Revenue in an accrual completeness ratio), the conclusion can flip from "fail" to "pass" — a material analytical error. Always validate that only accounts relevant to the metric feed into the calculation.

---

## Population Profile Report (Sprint 511)

1. **Sample data self-consistency**: When hardcoding sample report data, verify mathematical invariants (e.g., bucket sums = total, all accounts in a bucket meet the bucket's threshold). The original data had 7 accounts in the >$1M bucket summing to $4,250,000 — an impossibility since 7 accounts each >$1M must sum to at least $7M. Work backward from the total when designing bucket distributions.

2. **Gini threshold changes break Literal types**: Changing Gini interpretation labels (removing "Very High") requires updating Pydantic response schema Literal types, not just engine constants. Always search for the old labels in schema files.

3. **Shared modules enable rapid feature development**: The existing `shared/benford.py` module let us add Benford's Law to the population profile in minutes. Worth investing in shared engine modules when a feature will appear in multiple reports.

---

## Data Quality Pre-Flight Report (Sprint 510)

1. **Test data for balanced TB**: When adding a TB balance check, existing test data that was "clean" may no longer be clean if debits != credits. The original clean file test had debits=1500, credits=3500 — unbalanced. Always verify test fixture data satisfies ALL quality checks, not just the ones originally tested.

2. **Weight redistribution requires test assertion updates**: When redistributing scoring weights (e.g., adding a new 25% component), existing tests that assert on score thresholds will break. A column_detection HIGH issue with weight 30 produces score 70, but with weight 20 produces score 80 — changing the pass/fail boundary. Update score threshold assertions whenever weights change.

3. **`_calculate_readiness` should return breakdown alongside score**: Rather than computing score separately and then reconstructing the breakdown, having the function return both as a tuple ensures the displayed breakdown is always mathematically consistent with the displayed total. This prevents the "displayed score doesn't match displayed components" bug pattern.

---

## Multi-Currency Conversion Report (Sprint 509)

1. **Sample data counts must match list lengths**: The sample data had `unconverted_count: 12` with only 4 items in `unconverted_items`. The engine keeps these in sync, but hardcoded sample data didn't. The memo generator now defensively derives the displayed count from `len(truly_unconverted)` rather than trusting the separate count field. When a scope metric references a detail table, always derive the metric from the actual data, not a separate field.

2. **Rate source attribution belongs to the caller, not the generator**: The memo generator cannot know whether rates came from Reuters, Bloomberg, or manual entry. The methodology text should describe what the system does ("converts using provided closing rates") not claim a specific data source. The `source_context_note` field is the caller's responsibility.

---

## Statistical Sampling Evaluation Report (Sprint 508)

1. **Sample report values must be computed from engine formulas, not hardcoded**: The sampling evaluation sample data had Basic Precision = $25,000 (1 × SI), but the engine computes BP = SI × CF = $25,000 × 3.0 = $75,000. With EM = 0, BP always equals TM, making any PASS conclusion with errors arithmetically impossible. When hardcoding sample data for report generators, verify self-consistency by computing values through the actual engine formulas (or at minimum, manual arithmetic that matches the engine).

2. **Sampling interval depends on expected misstatement**: With EM > 0, the engine computes SI = (TM - EM) / (CF × (1 + EM/TM)), which is smaller than the EM = 0 case (SI = TM/CF). This smaller interval produces BP < TM, allowing room for errors while maintaining a PASS conclusion. Sample data that sets both EM > 0 and SI = TM/CF is self-contradictory.

3. **Phase-gated content prevents wrong-context sections**: The evaluation report was showing design-phase next steps ("select and test items") even though testing was already complete. Using an `is_evaluation` flag to swap entire section content (not just tweak wording) ensures each report phase is coherent end-to-end.

---

## Analytical Procedures Report (Sprint 505)

1. **Keyword matching for financial categories must exclude contra-items**: "Deferred Revenue" was matching the revenue keyword ("revenue" substring), inflating revenue totals and corrupting GPM ratios (59.2% instead of 58.6%). Add explicit exclusion lists (`_REVENUE_EXCLUSIONS = ["deferred revenue", "unearned revenue"]`) and prefer `account_type` field when available over keyword matching.

2. **Ratio computations must use the full TB population, not just significant movements**: The significant_movements list is a filtered subset (~30 of 247 accounts). Computing ratios from this subset produces materially wrong results because it misses revenue lines that aren't individually significant but aggregate to the full balance. Always pass `all_movements` to ratio functions.

---

## Revenue Report Enrichment (Sprint 501)

1. **Sample data test_keys must match engine canonical keys**: The revenue sample report used human-friendly test_keys (`round_amounts`, `cut_off_risk`, `recognition_timing`) that didn't match the engine's canonical keys (`round_revenue_amounts`, `cutoff_risk`, `recognition_before_satisfaction`). This caused blank methodology descriptions and missing follow-up procedures in sample PDFs. Always copy test_keys from the engine, not from the test names.

2. **Follow-up procedures need ALL test_key variants**: The revenue engine added 4 contract-aware tests (ASC 606) in Sprint 352 but never added their test_keys to `follow_up_procedures.py`. Every new test added to any engine must have a corresponding entry in the shared follow-up procedures dict.

---

## Payroll Report Enrichment (Sprint 500)

1. **Sample report risk_tiers were systematically inverted**: All 7 standard testing reports had hardcoded `risk_tier` values that didn't match the `score_to_risk_tier()` function boundaries. Scores 15-25 were labeled "elevated" (should be "moderate") and 28.3 was labeled "moderate" (should be "elevated"). When using synthetic data in sample generators, always derive the risk_tier from the score using the same function the engine uses, rather than hardcoding.

2. **Finding formatter must not duplicate data already in issue text**: When `amount` is both embedded in the finding `issue` string and also provided as a separate `amount` field, the formatter will show the amount twice. Either put the amount in the issue text OR in the amount field, never both.

3. **Scope builder closures enable payroll-specific enrichments without modifying the shared template**: Using closure-based `build_scope` callbacks that capture the full result dict allows tool-specific sections (GL reconciliation, headcount, department summary) to be added within the standard Scope section without changing the shared `memo_template.py` interface.

---

## Digital Excellence Council Remediation (Sprint 497)

1. **Pricing model changes cascade across 10+ test files**: Renaming `diagnostics_per_month` → `uploads_per_month` and changing Solo from limited→all-access broke tests in entitlements, parity, audit API, billing routes, and pricing launch validation. When entitlement fields are renamed or tier capabilities change, grep all test files for the old field name — don't rely on import errors alone since tests often reference field names as strings in assertions.

2. **Patching internal functions requires checking if they were refactored**: `_load_seat_price_ids` was split into `_load_pro_seat_price_ids` and `_load_ent_seat_price_ids` during Pricing v3, but 5 test patches still referenced the old function. When refactoring internal helpers, search for all `patch("module._function_name"` references in tests.

3. **ISA sub-paragraph citations (e.g., ISA 240.A40) are risky**: Application material paragraphs like ".A40" are renumbered between ISA revisions, making them fragile citations. Prefer citing the standard number only (ISA 240) unless quoting a specific, stable paragraph in a known revision.

4. **Audit terminology must stay neutral**: Replacing "exhibits a HIGH risk profile" with "returned HIGH flag density across the automated tests" is important — the platform flags data patterns, it doesn't assess audit risk (ISA 315 domain). Language that implies the tool performs risk assessment crosses the assurance boundary.

5. **SQLite schema drift causes silent lockout**: When models add new columns (like `organization_id`), the file-based `paciolus.db` doesn't auto-migrate. This causes `OperationalError` on queries touching the new column. Adding explicit SQLite migration in `init_db()` catches this at startup.

---

## Engineering Process Hardening (Sprint 496)

1. **1,345 frontend tests were never gated in CI**: The test suite existed locally but `ci.yml` only ran `npm run build` and `eslint`. A developer could break tests and merge without CI catching it. Always add test execution as a blocking CI job the same sprint you establish the test suite.

2. **mypy achieved 0 errors but wasn't enforced**: Achieving zero errors is wasted effort if CI doesn't prevent regression. Type checking must be a blocking CI gate, not just a developer-run tool.

3. **Secrets scanning is a CI primitive, not an afterthought**: Without automated secrets scanning, committed credentials (Stripe keys, JWT secrets) rely entirely on `.gitignore` and developer discipline. TruffleHog in CI + pattern matching in pre-commit provides two-layer defense.

4. **GitHub Actions default permissions are `write-all`**: Without an explicit `permissions:` block, every workflow job gets write access to repository contents, packages, and more. Always declare least-privilege permissions at the workflow level.

5. **CODEOWNERS without branch protection is advisory-only**: The file only enforces review requirements when "Require review from Code Owners" is enabled in branch protection settings. Document this CEO action.

---

## Data Hardening Security Audit (Sprint 494)

1. **DATABASE_URL credential exposure in startup logs**: The `print_config_summary()` function truncated DATABASE_URL at 50 chars — but PostgreSQL URLs like `postgresql://user:password@host:5432/db` fit within 50 chars and expose plaintext credentials. Always mask credentials in connection strings before logging, regardless of truncation.

2. **`detail=str(e)` is the #1 error leakage vector**: Six route endpoints passed raw exception messages directly to API clients. Even custom domain exceptions (InvalidTransitionError, RateValidationError) should route through `sanitize_error()` with `allow_passthrough=True` rather than raw `str(e)`, because upstream callers might catch broader exception types that include library internals.

3. **`allow_passthrough` in `sanitize_error()` needs a safety net**: Business-logic passthrough still needs to block messages containing file paths, SQL fragments, or stack traces. The pattern check should happen *before* passthrough, not just on the "known dangerous" patterns.

4. **FastAPI docs/OpenAPI must be disabled in production**: Swagger UI at `/docs` exposes all endpoints, parameter schemas, and internal model structures. Set `docs_url=None, redoc_url=None, openapi_url=None` in production.

5. **`logger.error("...%s", e)` can leak Stripe/AWS credentials**: Even though Stripe SDK generally redacts keys, the full exception string can contain customer IDs, request IDs, or error metadata that aids attackers. Log `type(e).__name__` instead.

6. **Excel formula injection applies to openpyxl too, not just CSV**: `sanitize_csv_value()` must wrap ALL user-controlled strings written to Excel cells via `ws.cell(value=...)` or `ws["A1"] = ...`. In openpyxl, a string starting with `=` becomes a formula. Cover: entity names, account names, prepared_by/reviewed_by, filenames, and financial statement labels. Indentation (spaces prepended) naturally prevents formula interpretation, but sanitize the raw value before indentation for defense-in-depth.

7. **UNKNOWN format fallback should reject known binaries**: When `detect_format()` returns UNKNOWN and the filename doesn't match Excel extensions, the fallback parses as CSV. This produces garbage data if the file is actually a binary format (XLSX/XLS/PDF) that slipped through detection. Add magic byte checks before the CSV fallback.

8. **In-memory stores need scheduled cleanup, not just eviction-on-insert**: `OrderedDict` job stores with TTL eviction only on new inserts can accumulate stale entries during quiet periods. Add a scheduled cleanup job to supplement insertion-time eviction.

---

## Access Hardening Security Audit (Sprint 493)

1. **FastAPI dependency functions cannot be called manually with positional args matching DI**: Functions like `check_seat_limit(user, db)` use `Annotated[User, Depends(require_current_user)]` which FastAPI resolves automatically. When calling manually, you must pass the actual User object and Session — the Depends metadata is ignored. Multiple entitlement checks were broken because they were called as `check_func(db, user.id)` instead of `check_func(user, db)`.

2. **Registration duplicate-email messages enable account enumeration**: A distinct "email already exists" error lets attackers probe for valid accounts. Use a generic message ("Unable to create account") that doesn't reveal whether the email is registered.

3. **Organization invite tokens should be bound to the invitee email**: Without email matching, any authenticated user who obtains a leaked invite URL can join the organization. Always verify `user.email == invite.invitee_email` on acceptance.

4. **Billing analytics endpoints need explicit role checks**: `require_verified_user` alone is insufficient for sensitive business data endpoints — any verified free-tier user could access global billing metrics without an admin/owner role check.

5. **Content-Disposition filenames from user input need sanitization**: User-controlled strings in `Content-Disposition` headers can inject control characters (`\r\n`). Sanitize with `re.sub(r'[^\w\-]', '_', name)` before embedding in headers.

---

## Formula Consistency & Efficiency Hardening (Sprint 492)

1. **Operating margin fallback must guard negative derived opex**: When `total_expenses < COGS` and `operating_expenses == 0`, the derivation `total_expenses - COGS` produces negative operating expenses, yielding economically invalid 100% margins. Guard: return N/A when derived value < 0 or total_expenses == 0.

2. **`calculate_all_ratios` computes CCC components twice**: DSO/DPO/DIO are computed individually and again inside `calculate_ccc()`. Fix: compute once and pass via keyword arguments. Same pattern applies to any composite metric built from sub-metrics.

3. **Existing edge-case tests may assert buggy behavior**: The `test_operating_margin_negative_derived_opex` test asserted `is_calculable is True` for a clearly invalid input. When hardening edge cases, audit existing tests for assertions that enshrine incorrect behavior.

4. **Test fixtures missing key fields affect edge-case tests**: `test_very_large_numbers` omitted `total_expenses`, which hit the new opex guard. Always include all expense-related fields in fixtures testing comprehensive ratio calculation.

---

## Digital Excellence Council Remediation (Sprint 491)

1. **Scout agent claims require independent verification**: The Scout flagged "16 untested engine modules" as CRITICAL. Actual count: 11 engine test files already existed. Always grep-verify quantitative claims before planning work based on them.

2. **Assurance-boundary language is a legal risk, not a security risk**: The Guardian agent gave a clean security audit while the Critic found 5 phrases that could expose the platform to auditor-judgment boundary challenges. Cross-domain risks (legal, regulatory, reputational) don't map cleanly to single-agent domains — the IntegratorLead must synthesize across agent perspectives.

3. **Standard citations matter more than feature work**: The JE memo cited PCAOB AS 1215 (Audit Documentation) as the governing standard for journal entry fraud testing. The correct standard is PCAOB AS 2110 (Risk Assessment). A PCAOB-registered firm would immediately flag this. Two-line fix, but the credibility risk was the highest-impact finding in the entire council session.

4. **Batch common patterns, then do tool-specific work**: The follow-up procedures gap affected 12+ tools. Batching all 52 new procedures in one sprint (37→89 total) is far more efficient than the one-report-at-a-time approach used in Sprints 488-490.

---

## HeroProductFilm Redesign (Sprint 480)

1. **Never hard-gate on `prefers-reduced-motion`**: The previous pattern (`if (prefersReducedMotion) return <StaticFallback />`) hid the entire scrubber UI from users whose OS disabled animations (Windows 11 default). The correct approach: always render the full UI, use `<MotionConfig reducedMotion="user">` to let framer-motion handle the preference gracefully (instant transitions instead of no UI).

2. **Phase-based animation in crossfade layers**: Layers driven by opacity MotionValues are always in the DOM. Internal animations should NOT use `whileInView` (fires once on viewport entry, not on step activation). Instead, pass `isActive` boolean and use `usePhaseTimer` to drive sequential animation phases that reset/replay on each step visit.

3. **`useCountAnimation` with rAF**: For counting animations (0→108 tests, 0→2.4MB), `requestAnimationFrame` with ease-out cubic produces smoother results than `setInterval` with fixed steps. The rAF approach also naturally syncs with the display refresh rate.

---

## Remediation Completeness (Sprint 482 / Audit 25)

**Pattern:** When fixing a pattern-based finding (e.g., f-string SQL, `status_code=200`, `animate-pulse`), partial fixes are marked COMPLETE without verifying that ALL instances were addressed. Sprint 479 fixed f-string SQL in `test_timestamp_defaults.py` but left 3 instances — caught by the council audit. Sprint 479 removed `status_code=200` from 3 endpoints but missed the accrual-completeness endpoint — caught by the council audit.

**Rule:** Before marking any pattern-based remediation finding as complete, run a codebase-wide grep for ALL remaining instances of the pattern. If the grep returns results, fix them or document why they are intentionally excluded. A partial fix is an incomplete remediation, not a closed finding.

**Prevention:** After applying a fix, immediately run: `grep -r "<pattern>" <scope>` to verify zero remaining instances. Record the grep command and "0 results" in the sprint checklist.

---

## Verification Gate Discipline

### npm test Must Run Full Suite — Never Targeted Subsets
**Recurrence:** Audit 20 identified the npm test gap. Audit 21 confirmed the gate was added but not executed. Audit 22 confirmed recovery (52 failures caught). Audit 23 found non-execution again with targeted suites (31/31 affected) used instead of full suite — exactly the pattern Audit 22 predicted as "gate fatigue." **Rule:** For ANY commit touching `.tsx`, `.ts`, or test files, run `npx jest --no-coverage` (full suite) and record "npm test: X suites, Y tests passing" in the todo.md verification section. Targeted suite results (e.g., "31/31 affected suites") are insufficient — cross-file regressions only surface in the full suite. This gate has the same mandatory status as `npm run build`.

### Ad-Hoc Creative Work Still Requires Todo Entries
Component rewrites, copy revisions, and visual redesigns are non-trivial work even when they feel like creative sessions rather than engineering sprints. The VaultTransition rewrite (345 changed lines), HeroProductFilm rewrite (574 changed lines), and About page revision (119 changed lines) were all committed without todo.md entries, creating audit trail gaps despite strong code quality. **Rule:** Any commit that modifies more than ~50 lines or rewrites a component gets a brief todo.md entry (goal, status, verification, commit SHA) — regardless of whether it was planned in advance or done ad-hoc. A retroactive entry immediately after commit is acceptable; no entry at all is not.

---

## Motion System Migration

### Reveal Component Requires Hook Mocks in Tests
When the `<Reveal>` component (or any wrapper) uses `useInView` and `useReducedMotion` from framer-motion, all test files that render components containing `<Reveal>` — even transitively — must include these hooks in their framer-motion mock. The standard framer-motion mock pattern (`motion: { div: ..., span: ... }, AnimatePresence: ...`) is insufficient. Add `useInView: () => true, useReducedMotion: () => false` to every framer-motion mock that renders components using Reveal.

### Deprecation Over Deletion for Shared Token Files
When consolidating motion tokens from 4 files into 1, mark superseded exports with `@deprecated` JSDoc rather than deleting them immediately. This allows consumers that import directly (not through barrel files) to continue working while providing IDE warnings. Remove barrel re-exports first (breaking the "easy path"), then deprecate source exports (warning the "direct path").

---

## Pricing Restructure (Sprint 452)

### Pydantic Schema Bound Changes Break Downstream Validation Tests
When changing a Pydantic field constraint (e.g., `seat_count: int = Field(le=22)` → `le=60`), existing tests that rely on the OLD boundary being rejected will silently fail — the value that was invalid is now valid. Always search for hardcoded boundary values in all test files when changing Pydantic `le`/`ge`/`max_length` constraints. In this case, `test_team_seat_23_rejected_by_schema` expected `seat_count=23` to raise `ValidationError`, but after the constraint changed to `le=60`, it no longer did.

### Tool Set Changes Cascade to Tier-Parity Tests
When moving tools between tiers (e.g., `revenue_testing` from Solo→Team), tests asserting "Professional mirrors Solo tools" will break if they check for the moved tool specifically. Parity tests should either (a) test the full set equality, or (b) test for tools that REMAIN in the tier, not tools being moved out.

---

## Brand Voice Alignment

### Performance Claims Must Reference a Canonical Source
Marketing copy contained four different timing claims (`< 1s`, `< 2s`, `< 3s`, `< 5s`) across different pages with no canonical constant backing any of them. The deployment architecture doc (`DEPLOYMENT_ARCHITECTURE.md`) defines the only measurable targets: p95 alert threshold >3 seconds, verification target <5 seconds for 10K rows. All marketing performance claims should derive from and reference this document. Creating a canonical constant or config value would prevent future drift.

### Storage Claims Must Distinguish Server-In-Memory from Browser-Only
The HeroProductFilm component claimed "Processed entirely in your browser. Your data never left this tab." — factually false since analysis runs on FastAPI servers. This contradicted the existing lessons.md entry about the same issue. Copy review processes should cross-reference lessons.md known errors before sign-off.

### Self-Assessed vs. Independently Attested Compliance Must Be Visually Distinguished
The trust page listed GDPR and CCPA as "Compliant" alongside SOC 2 Type II "In Progress" without clarifying that GDPR/CCPA compliance was self-assessed. For a product targeting financial professionals (who understand audit distinctions), this ambiguity erodes trust. Always separate "implemented controls" from "independently attested" status.

### "Zero-Knowledge" Is a Cryptographic Term — Don't Apply It to In-Memory Processing
"Zero-knowledge" has a precise cryptographic meaning (zero-knowledge proofs / ZKPs): a prover demonstrates knowledge of a secret without revealing it. Applying it to "data processed in-memory and discarded" is a factual error. The correct term for Paciolus's architecture is "Zero-Storage" — data is never written to disk or database, but the processing is server-side, not cryptographically zero-knowledge. Always audit marketing copy for cryptographic term misuse.

### Never Claim Client-Side Processing for Server-Side Work
FeaturePillars previously stated "All analysis happens locally in your browser / processed client-side." Paciolus analysis runs on FastAPI servers — only the UI is client-side. The correct claim is that data is processed in-memory on the server and immediately discarded. The security guarantee is zero retention, not zero server contact. Marketing copy must match the actual architecture.

### Concrete Outcomes Beat Generic Benefits in Brand Copy
"Enterprise-grade diagnostic intelligence without the enterprise complexity" is a category cliché — every enterprise software product uses this framing. "What used to take days now takes seconds" is concrete, verifiable, and specific to the actual problem being solved. Lead with the outcome, not the category.

---

## Security Sprint: Billing Redirect Integrity

### Server-Side URL Derivation > Allowlist Validation for Redirect Security
When a redirect URL is only ever one of two values (`/checkout/success` and `/pricing`), the correct control is to derive both server-side from `FRONTEND_URL` — not to validate user-supplied strings against an allowlist. Allowlist approaches require URL parsing and are vulnerable to Unicode normalization, subdomain squatting, and path traversal bypasses. Full derivation eliminates the attack surface entirely because no user input touches the field at all.

### Pydantic `model_validator(mode='before')` Fires Before `extra='ignore'` Strips Fields
A `model_validator(mode='before')` receives the raw input dict including extra fields that `extra='ignore'` will subsequently discard. This makes it the correct place to monitor for injection attempts: the validator increments a Prometheus counter for each URL field detected, then returns the dict unchanged. Pydantic's field-stripping happens afterward, so the final model object never has those fields. This pattern gives both detection and elimination.

### Old Required-Field Tests Must Be Replaced When Fields Are Removed
Two tests in `test_pricing_launch_validation.py` expected `ValidationError` when `success_url`/`cancel_url` were omitted — because they were formerly required fields. After removing those fields, those tests silently passed with no assertion. The fix: replace with positive assertions that verify the new behavior (fields not on model, silently ignored when supplied). Always check for inverted-expectation tests (`pytest.raises(ValidationError)`) when removing required fields.

---

## Zero-Storage Architecture v2.1 Consistency Pass

### "Zero-Storage" Is a Scope Claim, Not an Absolute Claim
The phrase "zero-storage" can be misread as "we store nothing at all." In reality it means "no persistence of line-level financial data." Compliance documents must explicitly disambiguate this — a "Terminology Clarity" callout and a "Scope Boundaries" preamble in the compliance implications section prevent overstated claims and reduce legal exposure. When adding marketing-friendly labels to architecture docs, always include a definition box that states what the term covers and what it does not.

### Cross-Doc Retention Alignment Is a Recurring Maintenance Task
Every time a retention value changes (e.g., "2 years" → "365 days"), all 4 compliance docs (Zero-Storage, Privacy, Security, ToS) must be updated in lockstep. A grep for the old value across `docs/04-compliance/` is the minimum verification step before closing a retention-related directive. The v2.0 pass already fixed "2 years" → "365 days" everywhere, so the v2.1 pass found nothing to fix — but the verification step confirmed consistency and should never be skipped.

### Control Verification Tables Add Auditor-Ready Evidence
Listing automated safeguards (retention cleanup, ORM deletion guard, memory_cleanup, Sentry stripping, CI policy guard) in a structured table with mechanism + frequency columns gives auditors and enterprise customers a concrete checklist to verify. This is more useful than narrative descriptions because each row maps to a specific code path they can inspect.

---

## Phase LXIV: HttpOnly Cookie Session Hardening

### CSRF_EXEMPT_PATHS Changes Require a Test Audit Pass
When adding or removing a path from `CSRF_EXEMPT_PATHS` in `security_middleware.py`, the CSRF test suite in `test_csrf_middleware.py` contains tests that directly assert membership in that set. These tests will fail silently if not updated — "silently" meaning they fail the suite but the intent (asserting the *old* policy) is wrong. When `/auth/logout` was removed from `CSRF_EXEMPT_PATHS`, four test cases needed updating: `test_auth_logout_exempt` (inverted to `not in`), `test_all_new_exempt_paths_pass` (path removed from tested list), `test_logout_exempt_documented` (checked for old comment text), and `test_exempt_set_is_frozen` (expected set updated). **Rule:** Any `CSRF_EXEMPT_PATHS` change must be followed by `grep -n "auth/logout\|CSRF_EXEMPT" backend/tests/test_csrf_middleware.py` (substituting the affected path) to find all assertions before running the suite.

### Mandatory Directive Protocol Applies to Security Sprints Too
Security hardening sprints (auth migration, CSRF changes, cookie policy) are often well-planned but executed with urgency, creating a tendency to skip the todo.md entry. The plan file (`.claude/plans/`) is not a substitute — the mandatory directive protocol requires writing the plan to `tasks/todo.md` as a checklist before implementation begins, regardless of sprint type. Skipping this step leaves no incremental tracking record, no review section with commit SHA, and no deferred item closure trail. The code quality is unaffected; the auditability is not.

---

## Sprint 448: pandas 3.0 Evaluation

### pandas 3.0 String Dtype: `dtype == object` Guard Breaks for CSV String Columns
**Correction:** pandas 3.0 uses `pd.StringDtype()` (displayed as `str`) for string columns read from CSV, replacing the old `object` dtype. Any guard of the form `if df[col].dtype == object:` silently skips string columns entirely, disabling the check.
**Root Cause:** The `dtype == object` pattern was valid for pandas 2.x but is not forward-compatible with pandas 3.0's new default string storage.
**Impact Found:** `shared/helpers.py:571` — cell-length protection for CSV uploads was bypassed. A cell with 100,001 characters would pass through without raising `HTTPException(400)`.
**Fix:** Replace `df[col].dtype == object` with `pd.api.types.is_string_dtype(df[col])`. This API returns True for both `object` dtype (pandas 2.x) and `pd.StringDtype()` / `str` dtype (pandas 3.0+).
**Prevention Rule:** Never use `dtype == object` to identify string columns. Always use `pd.api.types.is_string_dtype()`. Grep for `dtype == object` after any pandas major version bump.

### Dependabot Merges of Deferred Risky Dependencies Still Require the Evaluation Sprint
A dependency listed in the Deferred Items table as "needs dedicated evaluation sprint" is not closed by a green test suite alone — it requires the explicit evaluation (CoW audit, dtype verification, perf baseline). The test suite passing is a necessary condition but not sufficient. Merging via dependabot does not substitute for the evaluation. **Rule:** When a deferred item's dependency is merged, immediately schedule the evaluation sprint and run it before the next unrelated sprint begins. Update the Deferred Items table with evaluation findings.

### pandas 3.0 CoW Patterns That Are Safe (Verified 2026-02-27)
- `df = df.copy()` before column mutation — SAFE
- `df.iloc[start:end].copy()` for chunked processing — SAFE
- `df.drop(columns=[...], inplace=True)` for `drop` specifically — SAFE (not deprecated in 3.0)
- Dict-based `accumulator[key]["field"] += value` — SAFE (not a DataFrame operation)
- `df[col] = df[col].apply(...)` column reassignment — SAFE (not chained indexing)

---

## Phase LXII: Export & Billing Test Coverage (Sprint 447)

### ORM Model Must Be Imported at Collection Time for `create_all()` to Create Its Table
When writing tests for a model that isn't imported by `conftest.py` (e.g., `Subscription` from `subscription_model.py`), the `db_engine` session-scoped fixture runs `Base.metadata.create_all()` before the model is ever imported — so the table is missing. **Fix:** Add a top-level import in the test file (`import subscription_model  # noqa: F401`) so the model registers with `Base.metadata` during pytest collection, before the session fixture runs. This is a one-line fix, but the failure mode (`OperationalError: no such table`) is opaque.

### Route Integration Tests Must Mock Generators, Not Routes
Export routes that delegate to PDF/Excel generators (`generate_audit_report`, `generate_workpaper`, etc.) cannot be tested end-to-end without the full library chain. The correct pattern is to patch the generator at the import location in the route module (e.g., `patch("routes.export_diagnostics.generate_audit_report", return_value=b"%PDF-1.4 fake")`) and verify the HTTP status + response headers. This achieves >90% route coverage without requiring PDF/Excel test fixtures.

### Entitlement Factory Dependencies Can Be Called Directly as Python
`check_tool_access("tool_name")` returns an inner function `_dependency(user)`. In tests, call it as `dep = check_tool_access("tool_name"); dep(user=user)` — no FastAPI DI needed. This produces clean unit tests that run in milliseconds without a TestClient or database.

---

## Sprints 445–446: Coverage Analysis + Usage Metrics Review

### React 19 userEvent + Blur Validation: Same Pattern Applies Beyond Submit
The React 19 `userEvent` timing issue documented in Phase LXI also affects blur-triggered validation. A test using `user.type(input, 'A')` + `user.tab()` fails to trigger the `onBlur` validation error because the state update from typing may not flush before the tab event fires. **Fix:** Use `fireEvent.change(input, { target: { value: 'A' } })` + `fireEvent.blur(input)` — same synchronous fireEvent pattern as the submit fix. All input validation tests should use `fireEvent` not `userEvent` when testing value-dependent blur behavior.

### Route Coverage vs Engine Coverage Are Decoupled
Backend route files (`routes/export_diagnostics.py` at 17%, `routes/billing.py` at 35%) can have very low coverage even when their underlying engines are 100% covered. This is because route tests (HTTP-level) require a running TestClient and database fixtures, while engine tests (unit-level) only need Python imports. Route coverage gaps are high-risk because they miss auth guard enforcement, request parsing errors, response model validation, and middleware interactions — things the engine tests don't exercise.

### `pytest-cov` Is Not in Default Dev Dependencies
The `pytest-cov` and `coverage` packages were not installed in the backend venv. They must be installed manually for coverage runs. Add to `requirements-dev.txt` if one exists, or document in CONTRIBUTING.md as a prerequisite for local coverage analysis.

---

## Phase LXI: Technical Upgrades (Sprints 441–444)

### React 19 + jsdom: Form Submission Testing Pattern
React 19 changes how `requestSubmit()` works in jsdom, breaking tests that use `userEvent.click()` on submit buttons. `userEvent.type()` + `userEvent.click()` causes stale values because React batches state updates and the submit fires before re-render completes. **Fix:** Use `fireEvent.change()` (sets values synchronously) + `act()`-wrapped `fireEvent.submit(form)`. This pattern bypasses keyboard simulation timing issues entirely.

### useEffect Must Return on All Paths with `noImplicitReturns`
When `tsconfig.json` has `noImplicitReturns: true`, a `useEffect` with a cleanup return inside an `if` branch but no return on the else branch fails the build. Use early-return guard (`if (!condition) return;`) instead of wrapping the body in `if (condition) { ... return cleanup; }`.

### Test Suites Can Mask Schema Drift
`test_timestamp_defaults.py` used raw SQL `INSERT INTO clients` that was missing 3 NOT NULL columns added in later migrations (`reporting_framework`, `entity_type`, `jurisdiction_country`). Tests passed before because the columns were added after the test was written. When upgrading SQLAlchemy, stricter constraint enforcement can surface these mismatches. Keep raw SQL inserts in sync with current schema.

---

## Sprint 440: Billing Smoke Test

### Stripe API Errors Must Be Caught at the Route Level
All 6 billing endpoints that call Stripe (checkout, cancel, reactivate, add-seats, remove-seats, portal) were missing try/except around the Stripe SDK calls. When Stripe returns an error (e.g., business name not set, invalid subscription ID), the exception propagated to the global handler and produced a generic 500. Wrap all external API calls in try/except at the route level and return 502 ("Payment provider error") so users and frontend get actionable status codes. This is especially important because Stripe has many configuration prerequisites (business name, product creation, webhook setup) that may not be met in all environments.

### SQLAlchemy `Enum(PythonEnum)` Stores Member NAMES, Not Values
When using `Column(Enum(SubscriptionStatus))` with a Python `str` enum like `class SubscriptionStatus(str, Enum): ACTIVE = "active"`, SQLAlchemy stores the enum **member name** (`ACTIVE`) in the DB, not the value (`active`). Raw SQL inserts must use `'ACTIVE'` not `'active'`, or the ORM will fail with a `KeyError` when loading the row. This applies to all `Enum()` column types that reference Python enums.

---

## Sprint 439: BillingEvent Migration + Runbook Fix

### Model-Without-Migration Is a Silent Production Bomb
Phase LX defined `BillingEvent` in `subscription_model.py` and wired it into `analytics.py` + `webhook_handler.py`, but never created the Alembic migration. SQLite tests passed because the test harness uses `Base.metadata.create_all()`, which creates all tables from models directly — masking the missing migration. In PostgreSQL production, the table wouldn't exist. Lesson: after adding any new SQLAlchemy model, immediately verify it has a corresponding Alembic migration AND is imported in `env.py`. The test suite's `create_all()` is not a substitute for a real migration.

### Runbook Staleness After Enum Renames
The `starter → solo` rename (d9e0f1a2b3c4) updated `.env.example`, code, and tests, but missed `docs/runbooks/billing-launch.md` and `pricing-rollback.md` which still referenced `STRIPE_PRICE_STARTER_*`. Lesson: when renaming an enum value, grep ALL documentation (not just code + tests) for the old name. Runbooks and deployment guides are especially dangerous because they're used manually in production by people who won't get a compiler error.

---

## Pricing Launch Validation Matrix

### Frontend Tests: Prefer `getAllByText` Over `getByText` for Prices
When testing pages where the same text appears in multiple locations (e.g., `$50/mo` in both a plan summary header and a price breakdown line), `getByText` throws "Found multiple elements." Use `getAllByText` with a `.length` assertion instead: `expect(screen.getAllByText('$50/mo').length).toBeGreaterThanOrEqual(1)`.

### Frontend Tests: DOM Navigation for Seat Counters
Numeric seat counters (e.g., "1", "5") collide with other DOM text. Instead of `getByText('5')`, navigate the DOM relative to a unique aria-labeled button: `screen.getByLabelText('Add seat').previousElementSibling`. This avoids multi-match errors while staying structurally coupled to the component layout.

---

## Phase LIX Sprint F: Integration Testing + Feature Flag Rollout

### Prometheus Counter Names Strip `_total` in `collect()`
`prometheus_client` internally appends `_total` to Counter metric names per OpenMetrics convention. When iterating `REGISTRY.collect()`, the returned `Metric.name` is the base name (e.g., `paciolus_pricing_v2_checkouts`), not the full `_total` suffixed name. Tests that verify counter presence on a registry must match the base name, not the `_total` variant.

---

## Phase LIX Sprint B: Seat Model + Stripe Product Architecture

### SQLAlchemy Column `default=` Does NOT Apply on Bare Instantiation
`Column(Integer, default=1)` only fires on `INSERT` (via `db.add()` + `db.flush()`). A bare `Subscription()` object will have `seat_count = None`, not `1`. Tests that verify defaults must either: (a) test in DB context with `db_session.flush()`, or (b) test the property/method that handles `None` gracefully (e.g., `total_seats` uses `self.seat_count or 1`). This is distinct from `server_default` which only applies at the SQL level.

---

## Phase LIX Sprint A: Pricing Model Overhaul

### Test Fixture Defaults Cascade Through Entire Suite
When changing `UserTier.PROFESSIONAL` entitlements from all-tools to starter-level, the `conftest.py` default `make_user(tier=UserTier.PROFESSIONAL)` would have broken ~30 test files. The fix was to update the default to `UserTier.TEAM` and mechanically update all explicit `tier=UserTier.PROFESSIONAL` call sites. Lesson: test fixture defaults are a high-leverage coupling point — changing the semantics of a tier value requires auditing every fixture that uses it as a default.

### Display-Name Layer Prevents DB Enum Lock-In
PostgreSQL enum values can be added but not easily removed or renamed. Using a thin display-name mapping (`tier_display.py`) instead of renaming the enum lets us change public branding without touching the DB schema, Stripe metadata, or Alembic migrations. This pattern should be used for any future renaming of enums that are persisted in PostgreSQL.

---

## Sprint 6: Source Document Transparency

### Cross-Cutting Sprints Require Import Verification on Every File
When adding function calls (e.g., `create_leader_dots()`) to existing files during a cross-cutting sprint, always verify the function is already imported. `currency_memo_generator.py` used `create_leader_dots` in its inline source line but lacked the import — caught by regression tests (`TestCurrencyMemoLongInputs`) not by the new Sprint 6 tests. Lesson: regression suites across existing test files catch missing imports that targeted new tests may miss.

### Three Generator Categories Need Different Integration Patterns
The 20+ PDF generators fall into 3 categories: (A) cover-page via `build_cover_page()` + `ReportMetadata`, (B) header via `build_memo_header()`, (C) custom inline headers. Each category requires a different source-transparency integration pattern — (A) gets fields on the dataclass, (B) gets leader-dot lines after the header, (C) needs conditional replacement of hardcoded "Source File" lines. Identifying the categories upfront and applying the right pattern to each saved significant rework.

### PDF Binary Search Assertions Are Unreliable
ReportLab compresses text in PDF content streams, so `b"expected text" in pdf_bytes` will fail even when the text is correctly rendered. End-to-end PDF tests should assert `pdf_bytes[:5] == b"%PDF-"` (valid PDF header) and `isinstance(pdf_bytes, bytes)` rather than searching for raw text in the binary. Use unit tests on story flowables (pre-build) for text content assertions.

---

## Sprint 5: Heading Readability & Typographic Consistency

### Letter-Spaced Headings Were Confined to One File
Initial assumption was that spaced-caps headings ("E X E C U T I V E   S U M M A R Y") might be spread across many files. In reality, all 13 instances were in `pdf_generator.py` only. Memo generators used ALL-CAPS but not letter-spacing. A thorough audit upfront saved wasted effort searching wrong files.

### ALL-CAPS Headings Were Universal Across All 17 Memo Generators
While memo generators didn't use letter-spacing, every single one used ALL-CAPS section headers ("I. SCOPE", "II. METHODOLOGY"). The shared `memo_base.py` builders set the pattern, but many individual generators also had their own hardcoded headings. Converting to title case required touching 17 files — but because the pattern was consistent, the changes were mechanical and low-risk.

### Parametrized Test Discovery Catches Regressions Automatically
Writing tests that discover generator files via glob and parametrize assertions means new generators added in future sprints will automatically be checked for heading consistency — no manual test updates needed.

---

## Sprint 4: Text Layout Hardening

### Paragraph Wrapping Replaces String Slicing for PDF Tables
8 different memo generators independently used `[:N]` string slicing (with or without "..." ellipsis) to force text into fixed-width table columns. This pattern hides user data and creates inconsistent behavior (some add "...", some silently truncate). ReportLab's `Paragraph` flowable already auto-wraps text within its column width and dynamically expands row height — the slicing was unnecessary. Fix: wrap all text-heavy cells in `Paragraph(text, style)` and let ReportLab handle layout.

### repeatRows=1 Prevents Header Loss on Page Breaks
None of the 20+ PDF tables used `repeatRows=1`. When a large table spans multiple pages, the header row only appears on the first page, making subsequent pages unreadable. Adding `repeatRows=1` to all multi-row data tables ensures the header repeats on every page. Minimal effort, significant readability improvement.

### VALIGN TOP Is Critical for Mixed-Height Rows
Two tables (currency memo, sampling memo) were missing `VALIGN: TOP`. When some cells wrap to 2-3 lines while others are single-line, the default middle alignment causes misaligned text across columns. Always include `("VALIGN", (0, 0), (-1, -1), "TOP")` in any table that may have wrapped cells.

---

## Sprint 0: Report Standards Alignment

### Two Parallel Style Systems Are More Divergent Than Expected
Audit of all 20 PDF generators revealed two completely independent style systems (`create_classical_styles` with 16 styles vs `create_memo_styles` with 11 styles) that share zero code. They differ in title size (28pt vs 24pt), body text color (OBSIDIAN_600 vs OBSIDIAN_DEEP), section header size (12pt vs 11pt), and signoff column widths. The currency and flux expectations memos additionally use Helvetica (a third font family) and dark-background GRID tables — a pattern found nowhere else. Lesson: when shared primitives exist (memo_base.py), generators still drift if there is no enforced spec. The standards doc now locks every font, size, color, and margin to prevent future drift.

### Diagnostic Extension Memos Use Hardcoded Workpaper Codes
Five diagnostic memos (preflight, population profile, expense category, accrual completeness, flux expectations) use static `WP-PF-001`-style codes instead of dynamic `generate_reference_number()`. This creates duplicate reference numbers across different clients and periods. Migration plan assigns unique prefixes (PFL-, PPR-, ECA-, ACE-, FEX-) and requires dynamic generation.

---

## Sprint 420: Verification & Cleanup Release

### Redundant sr-only Inputs With Custom ARIA Checkboxes
Sprint 412c added `role="checkbox" aria-checked tabIndex={0} onKeyDown` to custom checkbox divs in login/register, but left the original `<input type="checkbox" class="sr-only">` in place. This created duplicate checkbox roles — `getByRole('checkbox')` found two elements, breaking tests. When upgrading a custom control to proper ARIA attributes, remove the hidden native input it was originally wrapping. The ARIA div IS the accessible control now.

---

## Sprint 415: Accessibility Semantic Fixes

### Modal Backdrops Should Use role="presentation", Not role="button"
Sprint 412c added `role="button" tabIndex={-1}` to a modal backdrop for ESLint compliance, but this is semantically incorrect — a backdrop is not an interactive control. The `tabIndex={-1}` contradicts the button role (removes from tab order), and the `onKeyDown` handler is unreachable. Correct pattern: `role="presentation"` with just `onClick` for click-outside-to-close. The backdrop's close behavior is a convenience, not an accessibility control — the real close mechanism is the modal's Cancel button or Escape key (via useFocusTrap).

---

## Phase XLIX: Diagnostic Feature Expansion (Sprints 356–361)

### Multiple FKs to Same Table Require foreign_keys Disambiguation
When adding `completed_by = ForeignKey("users.id")` to the Engagement model which already had `created_by = ForeignKey("users.id")`, the User model's `engagements` relationship needed `foreign_keys="[Engagement.created_by]"` and the Engagement model's `creator` relationship needed `foreign_keys=[created_by]`. Same pattern from Phase XLVI's SoftDeleteMixin, but this time for a non-mixin column. Always add `foreign_keys=` disambiguation when a model has 2+ FKs to the same target table.

### Allowlist Constants Must Be Updated When Adding Model Fields
Sprint 354 added `approved_by`/`approved_at` to AdjustingEntry but didn't update `ALLOWED_ADJUSTMENT_ENTRY_KEYS` in `tool_session_model.py`. This caused a pre-existing test failure that persisted across 6 sprints until caught in the Phase XLIX wrap. When adding fields to a model with an allowlist/blocklist sanitizer, always search for the allowlist constant and update it.

### Revenue Decline `else` Branch Missing Severity Assignment
In `going_concern_engine.py`, the `_test_revenue_decline()` function had `severity` assigned in the `if triggered:` branch but not in the `else:` branch, causing `UnboundLocalError`. When writing branching logic that builds a return value, ensure ALL branches initialize ALL variables used in the return statement.

---

## Phase XLVI: Audit History Immutability (Sprint 345–349)

### SoftDeleteMixin Creates Ambiguous ForeignKeys
When a mixin adds `archived_by = Column(Integer, ForeignKey("users.id"))`, any model that already has a FK to `users.id` (e.g., `user_id`) will cause SQLAlchemy `AmbiguousForeignKeysError` on relationships. The fix is to explicitly declare `foreign_keys=[user_id]` on every relationship pointing to User from an affected model, and `foreign_keys="[Model.user_id]"` on the reverse relationship in User. This affected 3 models (ActivityLog, DiagnosticSummary, FollowUpItemComment) and 2 User reverse relationships.

### ToolRun Ordering Needs Secondary Sort
`get_tool_run_trends()` ordered by `run_at.desc()` only. When two ToolRuns are recorded in the same test nearly simultaneously, they can get the same `run_at` timestamp, making the ordering non-deterministic. Adding `ToolRun.id.desc()` as a secondary sort key guarantees deterministic ordering. This was a pre-existing flaky test exposed by the full suite run.

## Phase XLV: Monetary Precision Hardening (Sprint 340–344)

### BALANCE_TOLERANCE as Decimal, Not Float
The float literal `BALANCE_TOLERANCE = 0.01` was used in 10 locations for balance comparisons. Comparing `abs(float_diff) < 0.01` has subtle issues: the float 0.01 itself is inexact (`Decimal(0.01)` = `0.01000000000000000020816681711721685228163...`). Replacing with `Decimal("0.01")` and comparing `abs(Decimal(str(diff))) < BALANCE_TOLERANCE` eliminates this.

### Alembic Multiple Heads
When the migration chain has multiple heads (two independent branches), you must merge them first (`alembic merge heads -m "message"`) before creating a new migration. Otherwise Alembic refuses to generate a new revision.

### SQLite + Alembic ALTER COLUMN
SQLite doesn't support ALTER COLUMN natively. Alembic's `batch_alter_table` creates a temp table, copies data, drops original, and renames. This works but is slow on large tables. For the dev SQLite DB, the models define the schema via `init_db()` not Alembic, so `alembic stamp head` is needed to mark the DB as current.

### Python round() Uses Banker's Rounding
`round(2.225, 2)` = `2.22` (ROUND_HALF_EVEN), not `2.23`. For financial applications, always use `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`. The `quantize_monetary()` shared utility encapsulates this.

---

## Process & Strategy

### Commit Frequency Matters
Each sprint = at least one atomic commit. Format: `Sprint X: Brief Description`. Stage specific files, never `git add -A`.

### Verification Before Declaring Complete
Before marking ANY sprint complete: `npm run build` + `pytest` (if tests modified) + Zero-Storage compliance check.

### Stability Before Features
Prioritize: 1) Stability (error handling, security) → 2) Code Quality (extraction, types) → 3) User Features (new functionality). Quick wins first within each tier.

### Test Suites Before Feature Expansion
Before expanding a module, create comprehensive tests for existing functionality. Cover edge cases (div-by-zero, negatives, boundaries).

### Test Fixture Data Must Match Requirements
Shared fixtures for common scenarios. Test-specific data for edge cases. Don't rely on shared fixtures for division-by-zero tests.

### Phase Wrap Sprints Are Pure Verification
**Observed across:** Sprints 110, 120, 130, 163. Write zero lines of application code. Run full backend test suite, frontend build, and guardrail checks. Documentation updates only. This pattern consistently catches inconsistencies.

### Extract Shared Components at the Right Time
Sprint 81 extracted ToolNav after 5 copies existed. Sprint 90 extracted shared enums before building Tool 7. Sprint 136-141 extracted testing components after 7+ copies stabilized. **Rule:** Extract after the second consumer appears for small utilities; extract after patterns stabilize across 7+ consumers for large component sets. During rapid feature delivery, cloning is correct — schedule a deduplication phase once feature velocity slows.

### Product Review Pays for Itself in Sprint 1
The 4-agent product review (Phase XIII) identified 51 findings. Sprint 121 alone fixed 7 P0 items. Without the review, issues like Tailwind shade gaps affecting 74 files would have accumulated silently.

---

## Architecture & Backend Patterns

### Engagement Management ≠ Engagement Assurance
Distinguish clearly between workflow features (tracking tools, organizing follow-ups — project management) and assurance features (risk scoring, deficiency classification — auditor judgment). Paciolus detects data anomalies; auditors assess control deficiencies. Never auto-classify using audit terminology (Material Weakness, Significant Deficiency). Use "Data Anomalies" and "Follow-Up Items" instead.

### Disclaimers Cannot Rescue Misaligned Features
If a feature's implied workflow crosses professional standards boundaries, rename and redesign the feature — don't just add warning text. Regulators (PCAOB, FRC) assess the tool's purpose, not its disclaimers.

### Zero-Storage Boundary: Metadata vs Transaction Data
Auth DB = emails + hashes only. DiagnosticSummary = aggregate totals only. Client table = name + industry only. Financial data is always ephemeral.

### Two-Phase Flow for Complex Uploads
When uploads need user decisions: 1) Inspection endpoint (fast metadata) → 2) Modal for user choice → 3) Full processing with selections.

### Dynamic Materiality: Formula Storage vs Data Storage
Store the formula config (type, value, thresholds). Never store the data it operates on. Evaluate at runtime with ephemeral data. Priority chain: session override → client → practice → system default.

### Factory Pattern for Industry-Specific Logic
Abstract base class + factory map for per-industry implementations. Unmapped industries fall back to GenericCalculator.

### Multi-Tenant Data Isolation
Always filter by `user_id` at the query level: `Client.user_id == user_id`. Never fetch-then-check.

### Optional Dependencies for External Services
External APIs (SendGrid, Stripe) should be optional imports with graceful fallback. Tests should run without API keys.

### Vectorized Pandas vs iterrows()
Replace `.iterrows()` with `groupby().agg()`. For 10K+ rows, iterate unique accounts (~500) instead of all rows. 2-3x improvement.

### Config-Driven Shared Modules for Cross-Engine Patterns
**Discovered:** Sprint 152. Use config objects (FieldQualityConfig, accessor callables) to parameterize shared functions rather than forcing all engines into one shape. Partial adoption (AR: CS only, TWM: neither) is better than force-fitting. This pattern powered column_detector (9 engines), memo_template (7 generators), testing_route (6 routes), data_quality (7 engines), and test_aggregator (7 engines).

### Callback-Based Factory Over Parameter-Heavy Abstraction
**Discovered:** Sprint 156. The `run_single_file_testing()` factory takes a `run_engine` callback rather than parameterizing all engine signature variations. Each route provides a lambda with its specific kwargs. Exclude multi-file routes (TWM, AR) where the factory adds more complexity than it removes.

### Inline Imports in Methods Defeat Return Type Annotations
**Discovered:** Sprint 414. `def _make_evidence(self, ...) -> "ContractEvidenceLevel":` with `from engine import ContractEvidenceLevel` inside the method body triggers ruff F821 (undefined name) because the string annotation references a name not in module scope. Either move the import to module level or remove the return type annotation. Prefer module-level imports in test files — there's no circular import risk.

### Account Classifier Lives in `account_classifier.py`
The `AccountClassifier` class and `create_classifier()` factory are in `account_classifier.py`, NOT `classification_rules.py`. The latter only has `ClassificationRule`, `ClassificationResult`, and `AccountCategory`. Sprint 289 learned this the hard way.

### Priority Ordering in Greedy Column Assignment
**Discovered:** Sprint 151. When multiple field configs match the same column name (e.g., "cost" matches both `cost` and `accum_depr`), lower `priority` numbers are assigned first. Always assign the most specific columns first.

### Guardrail Tests Must Inspect Module, Not Function
**Discovered:** Sprint 157. After refactoring memo generators to delegate to shared template, `inspect.getsource(function)` no longer contains ISA references — they're in module-level config. Use `inspect.getsource(inspect.getmodule(function))` instead. Source-code guardrail tests are brittle under refactoring.

### Centralized Error Sanitization
**Discovered:** Sprint 122. Use regex patterns to match common exception types (pandas, openpyxl, SQLAlchemy, reportlab) and map to user-friendly messages. `except ValueError` is safe (controlled messages); `except Exception` leaks tracebacks and needs sanitization. **Refinement (Sprint 252):** `allow_passthrough=True` mode for CRUD validation routes — dangerous patterns still caught, but safe business-logic messages pass through unchanged. Without this, all ValueErrors become generic "An unexpected error occurred."

### Rate Limiting Requires `Request` as First Parameter
Slowapi's `@limiter.limit()` decorator requires FastAPI `Request` as first positional parameter. When a Pydantic body model is already named `request`, rename it to `payload`.

### Upload Validation in Two Layers
Content-type and extension checks in `validate_file_size` (before bytes consumed). Encoding fallback and row count checks in `parse_uploaded_file` (during parsing). Short-circuit early.

### Memo Generator API Signatures Must Match
**Discovered:** Sprint 259. The shared memo base functions have specific signatures: `build_memo_header(story, styles, doc_width, title, reference, client_name)`, `build_workpaper_signoff(story, styles, doc_width, ...)`, and `generate_reference_number()` (no args). Always read the actual signature before using — the style key is `MemoSection` (not `MemoSectionHeader`), and color tokens are `OBSIDIAN_700` / `OATMEAL_400` (not `_LIGHT` / `_DARK`).

---

## Frontend Patterns

### framer-motion Type Assertions
TypeScript infers `'spring'` as `string`, but framer-motion expects literal types. Always use `as const` on transition properties. Applies to ALL framer-motion transitions extracted to module-level consts.

### framer-motion Performance Rules (Sprint 240)
- **Never animate `width`/`height` for visual-only effects** — use `scaleX`/`scaleY` + `transformOrigin` instead. Progress bars: `scaleX: progress/100` with `w-full` and `transformOrigin: 'left'`. Light-leak effects: set width statically, animate `scaleX`.
- **Infinite `boxShadow` animations in JS are expensive** — `boxShadow` forces repaint every frame. Move to CSS `@keyframes` where the browser can optimize off main thread. Limit decorative pulses to 3 cycles.
- **`AnimatePresence` children must be `motion.*` elements** — plain `<div>` inside `AnimatePresence mode="popLayout"` won't fire exit animations. The immediate child must be a motion component.
- **`AnimatePresence` is pointless on always-rendered content** — if early returns prevent the component from mounting, the exit animation never fires.
- **`<MotionConfig reducedMotion="user">` in root providers** — single line that makes all framer-motion animations respect `prefers-reduced-motion`. Highest-ROI accessibility fix.
- **`key={index}` in `AnimatePresence` causes wrong exit animations** — use stable IDs (counter ref or UUID) for list items that can be deleted from the middle.
- **Add `layout` prop to filterable/deletable list items** — prevents remaining items from jumping position when siblings are removed.

### God Component Decomposition — Extract Hook First
**Discovered:** Sprint 159. When decomposing a god component: (1) extract the custom hook with ALL logic first, (2) extract self-contained presentational sub-components, (3) the page becomes a thin layout shell. Tests pass without modification because jest.mock applies at module level.

### useEffect Referential Loop Prevention
Use `useRef` to track previous values. Compare prev vs current before triggering effects. For multiple params, use composite hash comparison.

### Memoize `initialValues` When Passed to Hooks That Derive Callbacks
**Discovered:** Sprint 414b. `useFormValidation({ initialValues: getInitialValues() })` creates a new object every render. If the hook's `reset` callback depends on `initialValues` (via `useCallback([initialValues])`), then `reset` is also recreated every render. Adding `reset` to a `useEffect` dep array causes an infinite re-render loop — the effect calls `reset()`, which updates state, which re-renders, which creates new `initialValues`, which creates new `reset`, which re-triggers the effect. A `useRef` guard only prevents the body from executing, not the effect from re-scheduling. **Fix:** `useMemo` the `initialValues` object on the actual primitive fields (`client?.name`, `client?.industry`, etc.) so the hook's derived callbacks are referentially stable.

### Modal Result Handling
Always check async operation result before closing modal. `if (await action()) closeModal()` — never fire-and-forget. Show errors IN the modal, not after it closes.

### Next.js Suspense Boundary for useSearchParams
Pages using `useSearchParams()` must wrap content in `<Suspense>`. Build-time requirement in Next.js 14+.

### TypeScript Type Guards with Array.filter()
`.filter(x => x)` doesn't narrow types. Use type predicate: `.filter((entry): entry is { key: string } => entry !== undefined)`.

### Ghost Click Prevention
File inputs with `position: absolute; inset: 0` capture unintended clicks. Fix: `pointer-events-none` + `tabIndex={-1}` when not in idle state.

### TypeScript `interface` vs `type` for Index Signature Compatibility
**Discovered:** Sprint 227. `interface Foo { a: string }` does NOT satisfy `Record<string, unknown>` because TypeScript interfaces lack implicit index signatures. `type Foo = { a: string }` DOES satisfy it. When a generic constraint requires `Record<string, unknown>` (e.g., `TEntry extends Record<string, unknown>`), all concrete types passed as `TEntry` must be `type` aliases, not `interface` declarations. This affected 11 types across the codebase (7 entry data types + 4 form value types).

### Severity Type Mismatch
Frontend `Severity` is `'high' | 'low'` only. `medium_severity` exists only as a count in RiskSummary. Always verify TypeScript types before assuming backend enum values map 1:1.

### useOptionalEngagementContext for Backward Compatibility
**Discovered:** Sprint 103. Returns `null` instead of throwing when no provider is present. Lets `useAuditUpload` auto-inject `engagement_id` when wrapped, silently skip when standalone.

### Hook-Level Integration Minimizes Page Changes
**Discovered:** Sprint 103. By injecting engagement logic into `useAuditUpload`, 5 of 7 tools got engagement support with zero page changes. Only TB (custom fetch) and Multi-Period (JSON body) needed explicit changes.

### Data-Driven Config Sections Beat Code Duplication
**Discovered:** Sprint 160. Four 170-line testing config sections collapsed into one 218-line shared component + 4 config arrays (~55 lines). Key: `ThresholdField[]` with `displayScale`, `prefix`/`suffix`, and `children` slot for edge cases.

### Factory Functions for Identical Hook Wrappers
**Discovered:** Sprint 161. 9 testing hooks (35-45 lines each) collapsed to `createTestingHook<T>()` factory (36 lines). Multi-file hooks pass custom `buildFormData` — no special casing needed.

### Centralize Environment Variables as Constants
**Discovered:** Sprint 161. 14 files declared `const API_URL = process.env.NEXT_PUBLIC_API_URL` locally. A single `utils/constants.ts` with fallback handles all cases. `minutes()` / `hours()` helpers make TTL configs self-documenting.

### `useState` Initializer Is NOT `useEffect`
**Discovered:** Sprint 162. `useState(() => { fetchIndustries() })` abuses the lazy initializer — runs synchronously during render. Always use `useEffect` for mount-time data fetching.

### Generic TypeScript Interfaces via Type Parameters and Slots
**Discovered:** Sprint 137. `BaseCompositeScore<TFinding = string>` handles Payroll's structured findings. `DataQualityBadge`'s `extra_stats?: ReactNode` slot handles AR's unique display. `FlaggedEntriesTable`'s `ColumnDef<T>` handles 7 table schemas. Use `object` constraint with explicit cast for generic form components (Sprint 160).

### CSS Custom Properties Don't Support Tailwind Opacity Modifiers
**Discovered:** Sprint 124. `bg-surface-card/50` doesn't work. Design semantic tokens with opacity built into the variable, or use separate tokens for different opacity needs.

### Modal Overlays Are NOT Dark-Theme Remnants
`bg-obsidian-900/50` is correct on both themes — semi-transparent dark backdrops dim whatever's behind the modal.

### Dark-Pinned Components Use `data-theme="dark"` Attribute
**Discovered:** Sprint 124. ToolNav and ToolLinkToast stay dark on light pages via `data-theme="dark"` on their wrapper element.

### JSX String Apostrophe Escaping
**Discovered:** Sprint 131. Background agents create TSX with unescaped apostrophes (`what's`, `it's`, `Children's`). Always scan agent output and fix with `\u0027` or `&apos;`.

### Warm-Toned Shadows for Premium Light Themes
**Discovered:** Sprint 325. Neutral gray shadows (`rgba(33,33,33,...)`) feel clinical. Using warm-toned shadows (`rgba(139,119,91,...)`) with the same alpha values creates a parchment-adjacent feel that matches Oat & Obsidian's warm palette. Apply to light theme only — dark theme shadows should stay neutral.

### Card Hierarchy via CSS Custom Properties
**Discovered:** Sprint 325. Three tiers — `surface-card` (default white), `surface-card-elevated` (same white, bigger shadow), `surface-card-inset` (slightly tinted, inset shadow) — provide clear visual nesting without adding extra borders or backgrounds. The `.card-inset` utility class bundles bg + border + shadow for one-liner application.

### Left-Border Accent Pattern for Visual Rhythm
**Discovered:** Sprint 326. `border-l-4` with color-coded accents (sage for positive, clay for negative, oatmeal for neutral) creates consistent visual rhythm across stat cards, summary cards, and metric displays without adding bulk. Map colors to the component's health/status data via `themeUtils.ts` for consistency.

### CSS-Only Textures Over Image Assets
**Discovered:** Sprint 328. SVG `feTurbulence` encoded as a data URI provides paper-like texture at 0.015 opacity — no image downloads, no CDN dependency, fully CSS-contained. Always pair decorative textures with `prefers-reduced-motion: reduce` media query to disable them.

---

## Testing Patterns

### Layout Refactors Must Update Test Assertions
When moving components from pages to layouts (e.g., Sprint 207 moved ToolNav/VerificationBanner to `app/tools/layout.tsx`), the corresponding page-level test assertions become stale. Tests that mock `@/components/shared` at the page level will silently pass the mock setup but fail the assertion because the page no longer imports those modules. **Rule:** Any component relocation must include a grep for test mocks targeting the old import path.

### Z-Score Fixtures Need Large Populations
With only 20 entries, a single outlier shifts the mean and stdev significantly. Use 100+ base entries to produce expected z-scores for HIGH severity thresholds.

### Benford Test Data Must Span Orders of Magnitude
Amounts must span 2+ orders of magnitude to pass prechecks. Use amounts like 50+, 500+, 5000+.

### Scoring Calibration: Comparative Over Absolute
Use `assert clean_score.score < moderate_score.score < high_score.score` rather than asserting absolute tiers, which change as tests are added.

### SignificanceTier Enum vs String in Tests
When constructing test dataclasses that use enums, always use the enum member, not its string value.

### Pytest Collection of Engine Functions
Functions named `test_*` in engine files are collected by pytest. Either don't use `test_` prefix, or import with aliases: `from engine import test_foo as run_foo_test`.

### `jest.clearAllMocks()` Does NOT Reset `mockReturnValue`
Must explicitly re-set default mock values in `beforeEach` after `clearAllMocks()`.

### Mock Result Shapes Must Match Inline Property Access
Even when child components are mocked, the page evaluates prop expressions like `result.summary.matches` before passing to the mock. Always check page source for inline property chains.

### framer-motion Test Mock Must Strip Motion Props
Spreading all props from `motion.div` onto a real `<div>` passes invalid HTML attributes. Destructure out `initial`, `animate`, `exit`, `transition`, `variants`, `whileHover`, etc. before spreading rest props.

### Mock Barrel Exports Must Include ALL Named Exports
When mocking a barrel file (`@/components/shared`), include ALL named exports the page uses, not just one.

### Mock the Import Path the Component Actually Uses
**Discovered:** Sprint 249. If a page imports from `@/components/engagement` (barrel), mocking `@/components/engagement/EngagementList` (individual file) does nothing — Jest resolves mocks by the exact import path string. Always mock the barrel path when that's what the source file imports.

### `getByText` Fails on Duplicated Page Text (Nav + Heading)
**Discovered:** Sprint 249. Pages with breadcrumb navigation often render the same text in both `<span>` (nav) and `<h1>` (heading). Use `getByRole('heading', { name: '...' })` to target the heading specifically, or `getAllByText` when both are valid.

### Named vs Default Export Mocks Are Not Interchangeable
**Discovered:** Sprint 249. `import { CommentThread } from './CommentThread'` requires mock `{ CommentThread: ... }`. Using `{ __esModule: true, default: ... }` silently resolves to `undefined` and causes "Element type is invalid" at render time — the error appears on click (expand), not on initial render, making it hard to diagnose.

### Hook Method Names Must Match Page Destructuring
Always verify the page's `const { ... } = useHook()` line before writing mock return values.

### SQLite FK Constraints Need PRAGMA
FK constraints NOT enforced by default. Need `PRAGMA foreign_keys=ON` via engine event listener in conftest.py.

### SQLite Strips Timezone from Datetime Columns
Compare with `.replace(tzinfo=None)` when mixing DB-loaded and fresh timezone-aware datetime values.

### SQLAlchemy Backref Passive Deletes
When deleting a parent with related children, use `backref=backref("items", passive_deletes=True)` to let DB handle CASCADE instead of SQLAlchemy's default SET NULL behavior.

### Test Import Redirection Preserves Compatibility
When extracting helpers into shared modules, test files can use `from shared.module import func as _old_name` — same alias, zero test body changes.

### Ghost Employee Tests Affect "Clean" Fixture Design
Tests that flag single-entry employees mean clean fixtures must ensure each employee has 2+ entries across different months.

### BaseHTTPMiddleware Cannot Raise HTTPException
Starlette's `BaseHTTPMiddleware` wraps exceptions in `ExceptionGroup`, so raising `HTTPException` inside `dispatch()` produces opaque errors. Return a `Response(content=..., status_code=..., media_type="application/json")` instead — matches the pattern in `MaxBodySizeMiddleware`.

### CSRF Middleware Breaks API Integration Tests
Registering CSRF middleware blocks all test POST/PUT/DELETE requests that don't include a CSRF token. Solution: add an autouse session fixture in conftest.py that patches `validate_csrf_token = lambda token: True`, then restore the original in `test_csrf_middleware.py` setup/teardown for explicit CSRF testing.

---

## Design & Deployment

### Premium Restraint for Alerts
Left-border accent (not full background), subtle glow at low opacity, typography hierarchy over color.

### CSS Custom Properties Bridge Tailwind and Runtime Theming
Define semantic CSS variables in `:root` (dark defaults) with `[data-theme="light"]` overrides in `globals.css`, reference via Tailwind token aliases. Route-based theming via `usePathname`, not user toggle.

### ScoreCard Tier Gradients → Left-Border Accents on Light Theme
Dark theme used gradient backgrounds for risk tier encoding. On light backgrounds, use `border-l-4 border-l-{tier-color}` instead.

### RISK_TIER_COLORS Must Use Solid Fills for Light Theme
Replace opacity colors (`bg-sage-500/10`) with solid palette fills (`bg-sage-50`, `text-sage-700`, `border-sage-200`).

### `prefers-reduced-motion` Should Skip, Not Slow Down
Don't show a faster animation — skip it completely and call `onComplete` immediately.

### Memo "Download Memo" as Primary, "Export CSV" as Secondary
PDF memos are the higher-value audit artifact. Make memo button visually primary (sage-600 filled) to guide users toward the more useful export.

### Memo Data Shape Must Match Tool Output
Always check the frontend data shape (hook response) before designing a memo generator. Design the Pydantic input model from the hook's TypeScript types first.

### Multi-Stage Docker Builds
Separate deps → builder → runner stages. Only runtime in final image. Non-root users. Health checks. `sqlite:////app/data/paciolus.db` (4 slashes = absolute path). Use `pip install --prefix=/install` in builder to avoid copying pip/setuptools/wheel (~20MB) into production stage. Prefer `curl -f` for healthchecks over spawning a full Python interpreter every 30 seconds.

### .dockerignore Prevents Secrets in Build Context
Without `.dockerignore`, `docker build` sends everything (`.env`, `paciolus.db`) to the daemon, even if not COPY'd.

### Docker Compose Defaults Drift from Backend Config
**Discovered:** Sprint 250. `docker-compose.yml` had `JWT_EXPIRATION_MINUTES:-1440` (24h) but `config.py` was hardened to 30 minutes in Phase XXV Sprint 198. Compose env defaults silently override backend config module defaults. **Rule:** After any security hardening phase that changes config defaults, grep `docker-compose.yml` for the same env var and update the compose default to match.

### Gunicorn Worker Recycling for Pandas Memory
**Discovered:** Sprint 250. Long-running Gunicorn workers processing large DataFrames via Pandas accumulate memory over time. `--max-requests 1000 --max-requests-jitter 50` restarts workers after ~1000 requests, preventing slow memory leaks. Jitter prevents all workers from restarting simultaneously (thundering herd).

### Dockerfile HEALTHCHECK vs Compose healthcheck Duplication
**Discovered:** Sprint 250. Defining healthchecks in both `Dockerfile` and `docker-compose.yml` causes the compose definition to silently override the Dockerfile's `HEALTHCHECK`. Pick one location: Dockerfile for self-contained images, compose for orchestration-specific tuning. Don't duplicate.

### ReportLab Best Practices
Use get-or-create for styles (avoid "already defined" error). Use `onFirstPage`/`onLaterPages` callbacks for repeating elements. Wrap table cell text in `Paragraph` objects. Prefer built-in fonts. **Sprint 196:** Only reference styles that exist in the style dict being used (`create_classical_styles()` vs `create_memo_styles()` have different names). Only use fonts registered with `pdfmetrics` — `Times-*` and `Courier` are built-in; custom fonts like `Merriweather`/`Lato` require explicit registration. Always close BytesIO buffers after `getvalue()`.

### Tailwind Silently Drops Undefined Color Shades
Classes referencing undefined shades simply produce no CSS — no warnings. Always define the full shade range (50-900) when a scale is used extensively.

### Single Version Source of Truth
Extract version to `backend/version.py` with `__version__`. Import everywhere. Future bumps require exactly one edit.

---

## Adding New Tools — Cascade Checklist

### ToolName Enum Cascade (4-file, N-assertion update)
**Observed across:** Sprints 104, 107, 114. When adding a new `ToolName`: (1) add to enum, (2) add to `TOOL_LABELS`, (3) add to `TOOL_LEAD_SHEET_REFS`, (4) grep tests for hardcoded tool counts (e.g., `== 9`). Update `test_anomaly_summary.py`, `test_engagement.py`, `test_workpaper_index.py`.

### Frontend Tool 4-Location Cascade
**Observed across:** Sprints 106, 109, 116, 119. New tool frontend requires: (1) `ToolNav.tsx` (ToolKey type + TOOLS array), (2) `app/page.tsx` (toolCards + nav + tool count copy), (3) `types/engagement.ts` (ToolName + TOOL_NAME_LABELS + TOOL_SLUGS), (4) tool's own files (types, hook, 4 components, page).

### Frontend Tool Pages Are a 4-File Formula
**Observed across:** Sprints 106, 116, 119. Types file → Hook (thin `useAuditUpload` wrapper via `createTestingHook`) → 4 components (ScoreCard, TestResultGrid, DataQualityBadge, FlaggedTable) → Page.

### Memo Generators Are Config-Driven (5 minutes)
**Observed across:** Sprints 105, 115, 118. With `shared/memo_template.py`: define test descriptions dict, methodology intro, risk-tier conclusions, ISA references. ~90 lines per generator.

---

## Phase Retrospectives — Consolidated

> Distilled from 15+ individual phase retrospectives (VI–LXIX). Only unique lessons not already captured in categorical sections above.

### Feature Delivery Cadence (Phases VI–XII)
- Frontend auth gating must be 3-state (guest/authenticated/verified), not 2-state
- Extract shared utilities BEFORE building the next tool; the clone pattern compounds — each tool ships faster
- Classification validators: structural-only (detect, not advise) to avoid liability

### Refactoring & Hardening (Phases XV–XXIII, XXVIII)
- `def` is the correct FastAPI default; auto-threadpools sync handlers. Use `asyncio.to_thread()` for CPU-bound Pandas in `async def`.
- Error-in-body anti-pattern (200 with `{"error": "..."}`) leaks into frontend types — convert to HTTPException
- `min_length=1` on Pydantic list fields can break legitimate empty-list cases (e.g., multi-period all-new accounts)
- `@model_validator(mode='before')` enables backward-compatible model decomposition
- Static analysis (ruff) catches bugs on error-handling paths that 2,900+ tests miss
- `float('inf')` is not valid JSON — use `None` for zero-prior percentages

### Design & Theme (Phases XLII–XLIII)
- Verify which route (dark Lobby vs light Vault) a component renders on before migrating tokens
- Dual-theme components (e.g., RiskDashboard on both themes) work automatically with CSS custom properties
- Always update tests alongside color token migrations (`toContain('text-oatmeal')` → `text-content-primary`)
- Fixed-position backgrounds need `pointer-events-none`; content needs `relative z-10`

### Security (Sprint 476 + Hardening)
- `conftest.py` must import ALL ORM models with FK relationships — even unused ones trigger `create_all` errors
- CSV `sanitize_csv_value()` must cover ALL export functions — satellite exports (bank_rec, multi_period, admin) get missed
- `_FORMULA_TRIGGERS` must include `|` (pipe) per OWASP CWE-1236 — always cross-reference full standard
- Webhook handlers: one logical operation = one `db.commit()` — multiple commits create crash-consistency windows
- Adding auth/validation to an endpoint → grep all test call sites, not just add new tests

### PDF & Report Generation
- Circular imports between generators and shared chrome → resolve via lazy imports
- `StyleSheet1.get(key)` raises `KeyError` (not `None`) — use `_safe_style(styles, *names)` helper
- PDF binary: text is compressed — never `b"TITLE" in pdf_bytes`; assert structurally (page count, `/Type /Page`)
- `.tsx` extension required for files containing JSX (even if primarily constants)

### Digital Excellence Council Audit (Sprint 479)
- `time.sleep()` in tests is inherently flaky — use deterministic timestamps (set to a known past value) instead of waiting for the clock to advance
- f-string SQL in test fixtures, even with integer literals, establishes a copy-paste hazard — always use `.bindparams()` even in tests
- ExportShare's 48h derived-data retention is a controlled exception to zero-storage that must be formally documented in the security policy with compensating controls listed
- framer-motion `as const` convention needs CI enforcement (grep-based gate), not just documentation — 11 violations accumulated despite CLAUDE.md mandate
- APScheduler per-instance behavior under Gunicorn needs ops documentation, not just code comments — operators won't read source during incidents

### Financial Statements Report Enhancements (Sprint 488)
- `_extract_depreciation` relied solely on `net_balance` field from account dicts, but test fixtures (and possibly real data) sometimes only have `debit`/`credit` without a pre-computed `net_balance`. Added fallback: `debit - credit` when `net_balance` is 0.0. Same pattern applied to `_extract_interest_expense`. Always handle both dict shapes for TB account data.

### JE Testing Memo Fixes (Sprint 489)
- **Index-based finding-to-procedure mapping breaks when `top_findings` and `flagged_tests` have different orderings.** The `top_findings` list may be sorted by severity/importance while `flagged_tests` is sorted by flag_rate. Fixed with `_resolve_test_key()`: a word-overlap scorer that weights words by cross-test distinctiveness (unique words score 2x, common words like "entries" score less). Generic words in test names (entries, amounts, postings) cause false matches with naive substring matching.
- **Disclaimer template `f"automated {domain} testing procedures"` doubled "testing" when `domain` already ended with "testing"** (e.g., "journal entry testing testing procedures"). Four of seven testing memo domains hit this bug. Fix: conditional `domain_clause` that skips appending "testing" when domain already ends with it.
- **Sample report data can diverge from real engine output.** The Benford `expected_distribution` used a wrong formula `(0.30103 - 0.02 * (d - 2))` instead of `log10(1 + 1/d)`. The real engine (`shared/benford.py`) was always correct — only the hardcoded sample data was wrong. Always derive sample data from the same constants/functions used by the engine.

### AP Testing Memo Fixes (Sprint 490)
- **Test-specific table layouts are essential for high-severity drill-downs.** A generic 6-column table can't meaningfully display data from tests with fundamentally different schemas (duplicates need payment pairs, threshold tests need below-by amounts, invoice reuse needs two-vendor comparison). Each high-severity test type benefits from a purpose-built column layout with a generic fallback for unexpected test keys.
- **Vendor name variation pairs generate duplicate flagged_entries** (A→B and B→A). The deduplication via `seen_pairs` with `tuple(sorted([name_a, name_b]))` is required, otherwise every pair appears twice in the table. Sort by combined total_paid descending and cap at top 5 to keep the table actionable.

### Fixed Asset Report Fixes (Sprint 502)
- **Recurring bug pattern: sample data `test_key` values diverge from engine canonical keys.** Revenue sprint had `round_amounts` vs `round_revenue_amounts`; fixed assets had `cost_outliers` vs `cost_zscore_outliers` and `residual_anomalies` vs `residual_value_anomalies`. The methodology description lookup uses test_key, so mismatches produce blank descriptions. **Always verify sample data test_keys match `*_TEST_DESCRIPTIONS` dict keys exactly.**
- **ReportLab Paragraph uses XML/HTML parser.** Raw `&` in strings passed to `Paragraph()` must be escaped as `&amp;`. The `PP&E` abbreviation caused rendering artifacts because `&E` was interpreted as a malformed XML entity. Payroll memo already had correct `&amp;` usage (`"Payroll &amp; Employee Testing Memo"`) — the pattern was available but not applied consistently.
- **When adding a new test to an engine, grep the entire test suite for hardcoded counts** (`== 9`, `tests_run=9`). Four separate assertions across two test files needed updating from 9 to 10 after adding the FA-10 lease indicator test.

### Docker deployment breaks static asset discovery (Sprint 526)
- **Logo files at project root and `frontend/public/` are invisible inside the backend container.** The Dockerfile copies only `backend/` into `/app`, so `Path(__file__).parent.parent.parent / "frontend"` resolves to a non-existent path. **Fix:** Copy assets to `backend/assets/` which is the third search path in `_find_logo_file`. Any asset needed by the backend PDF generator must live inside the `backend/` directory tree.

### Greedy column detection priority ordering can steal columns from higher-importance roles (Sprint 526)
- **When `account_name_column` (priority 8) ran BEFORE `account_column` (priority 10), it claimed "Account Name" headers — leaving account_column null.** This broke all downstream features because the account identifier was missing. **Pattern:** In a greedy assignment algorithm, give the most critical role the lowest priority number (first pick). Optional/supplementary roles should run after required ones. Specifically: `account_column` (priority=8) must run before `account_name_column` (priority=12).

### Substring keyword matching can cause false positives on unrelated account names (Sprint 537)
- **"rent" is a substring of "current"**, so `"rent" in "2520 — current portion — long term debt".lower()` returned True, incorrectly classifying a debt account as informational (transactional). **Fix:** Added `"current portion"` and `"long term debt"` to `ROUND_NUMBER_TIER1_SUPPRESS` so these accounts are suppressed before reaching the informational keyword check. **Pattern:** When using `kw in lower` substring matching, always test against account names that contain the keyword as a substring of a larger word. Consider whether phrase-level matching or word-boundary checks would be safer for short keywords (≤4 chars).

### Stale test assertions survive across sprint boundaries (Sprint 537)
- **`test_allowance_round_suppressed` expected `len(rounding) == 0`**, but Sprint 536 changed contra-asset handling from suppress (return `None`) to minor observation (return `"minor"`). The test was already failing before Sprint 537 started. **Pattern:** When a sprint changes classification/tiering logic, grep for all tests that assert on the affected return values — not just the tests in the sprint's own test file. Run the full `pytest` suite before starting new work to establish a clean baseline.

### Subagent findings must be verified against live code before acting (Sprint 598)
- **During the 2026-04-14 weekly weakness hunt, a parallel `Explore` subagent tasked with finding test coverage gaps reported that `ratio_engine.py`, `accrual_completeness_engine.py`, and `three_way_match_engine.py` had "no test suite" or "no dedicated test file." All three claims were wrong** — each module has 1–3 dedicated test files (`test_ratio_core.py`, `test_ratio_analysis.py`, `test_ratio_trends.py`, `test_accrual_completeness.py`, `test_three_way_match.py`, `test_three_way_comparison.py`). The same agent also reported fake line counts ("44,081 lines", "55,283 lines") which were actually byte counts. A sibling security-hunt agent produced verifiable findings with correct line:line references; the coverage agent hallucinated structure. **Pattern:** Any subagent claim of the form "file X does not exist", "function Y is untested", or "N lines/rows/items" MUST be verified against live code (Glob/Grep/wc) before being acted on or surfaced to the user. If the claim can be invalidated by a single shell command, run that command before repeating the claim. Line-level findings with specific `file:line` references are higher-trust than structural ("no test file exists") claims — the specific ones are visible in the agent's context window, the structural ones require accurate mental model of a repo the agent only partially read. **Systemic fix:** replace LLM-introspected coverage analysis with `pytest --cov --cov-report=json` piped into the nightly brief so the coverage pillar stands on machine-checkable data rather than model output. Sprint 599 wires this in.

---

## Sprint 794 — "pass / fail" is the wrong shape for any check that can be prevented from running

**What happened.** `Node CVE & License Audit` failed on PR #189. The log said
`npm error audit endpoint returned an error` after a 503 from registry.npmjs.org. No vulnerability
existed. `npm audit` exits 1 both when it finds something and when it cannot look, and the red X is
the same X, so the signal a reader receives is "this PR ships a high-severity vulnerability."

**This is the third instance of one shape in a single day.**

| Sprint | The check | What it could not say |
|--------|-----------|-----------------------|
| 778a | Monthly DR test | "I detected a failure" — the job exited 0 regardless |
| 794 | npm CVE gate | "I could not check" — a 503 is reported as a finding |
| 775 (by design) | Deploy-drift probe | correctly says `SKIP` when `RENDER_API_KEY` is absent |

The third row is the one to copy. It is the only one of the three that was built knowing the
answer has three states, and it is the only one that never lied.

**The rule.** *Any check that depends on something outside the commit has three outcomes, not two:
pass, fail, and did-not-run.* If the implementation has only two exit codes, one of those three
truths is being reported as a different one — and it is almost always "did not run" being reported
as fail (noisy, erodes trust in the gate) or as pass (silent, much worse).

**Spotting it before it bites:** ask "what does this check do when the thing it calls is down?"
Network calls, external APIs, and anything reading a credential that might be unset are the whole
population. If the answer is "the same as a real failure", the check cannot be read.

**Deciding the third state's policy is separate from exposing it** — and much easier once the retry
is in. Sprint 794a deliberately kept the existing fail-closed behaviour and changed only the words,
so no policy decision gated the fix. Retrying first removed most of the occurrences; the remaining
policy question ("should an npm outage block every PR?") is now rare enough to be answered calmly
rather than during an incident.

**Also:** discriminate on the payload, never on the exit code, when the exit code is the thing that
cannot tell the cases apart. And default the unrecognised case to "did not run", never to "clean" —
a format change upstream must not silently disarm a security gate. That is Sprint 792's defect
class arriving through a different door.

**And the now-standard second test.** The fix needs two claims proved, not one: that the classifier
discriminates, *and* that no workflow still calls the bare command. Three call sites had this bug
because three jobs each ran `npm audit` directly; a fourth added by copy-paste would reintroduce it
and stay green until the next outage. After PR #188 (a guard that inspected 23% of its target) and
Sprint 792, writing the anti-drift test up front is cheaper than discovering in review that the fix
quietly stopped applying.

---

## Sprint 741d — a hand-read sample is not a measurement

**What happened.** Sprint 741c's record carries a table of enum label drift between the Alembic
chain and the ORM: three types, five rows, assembled by hand from two PR reviews. Building the
same comparison mechanically found **twenty** drifting types out of twenty-six.

Every row in the hand-written table was correct. It was simply the subset that happened to get
noticed, presented in a format that reads like an inventory. Nothing marked it as a sample.

**The rule.** When a record enumerates instances of a defect, say whether the list is *everything*
or *what was found so far*. They look identical on the page and they support completely different
decisions — "fix these three" versus "there is a systemic problem here." Sprint 741c's step 2
("correct the migrations that disagree") was scoped against three types.

**The corollary that actually saves time:** if a defect class is mechanically detectable, measure
it before scoping the fix. The measurement here took about twenty minutes and moved the estimate
by a factor of six — and surfaced `engagementstatus.COMPLETED`, a label the ORM binds that **no
migration ever adds**, which nobody had noticed at all. It is the same instinct as Sprint 792:
stop fixing instances, go find the population.

**And the reason it had to be static.** SQLite has no enum types, so every label is accepted and
~9,000 passing tests say nothing about this. Third time this shape has appeared — Sprint 787's
missing `ALTER TYPE`, Sprint 741a's 22P02, now this. **When a constraint exists only in the
production dialect, no amount of green test suite is evidence about it.** Worth asking of any
schema-level claim: which dialect would have to be running for this test to be able to fail?

**The guard was wrong three times before it was right**, each time by silently covering less than
it claimed: it read 5 of 26 ORM types (`import models` misses sibling `*_model.py` modules), it
could not read a constant declared with a type annotation (`AnnAssign`, not `Assign`), and it
recorded an f-string's `{value}` placeholder as a real label. All three were caught only because
the module reports what it *cannot* resolve rather than skipping it. If the first draft had
shipped it would have passed CI and printed a confident verdict over a fifth of the schema.

**So: make unparseable input an error, not a skip.** This is the operational form of the rule from
Sprint 794 — the parse and the check are two different claims, and a parser that degrades quietly
converts a guard into a rubber stamp. Every guard written this session that lacked this had the
defect; every one that had it caught its own bugs before review did.

### The addendum the PR #191 review forced, which is the sharper version

The guard shipped with a coverage self-check, and it passed. It counted `Enum(..., name=...)` AST
calls and confirmed the parser saw all 26. The review then found that the parser had **no handler
for `CREATE TYPE ... AS ENUM`** — raw SQL inside `op.execute()`, which that check cannot see. One
migration rebuilds two enum types that way, so one reported drift was a phantom and any future
drift introduced by a rebuild would have been invisible.

**Coverage of one construct family reads exactly like coverage of the subject.** "I verified the
parser sees every `Enum()` call" and "I verified the parser sees every way this chain defines an
enum" are different sentences, and only the first was true. The fix was a second coverage check
over the SQL path — but the generalisable move is: *before writing the coverage test, enumerate
the construct families the input can use, and check the list is complete.* Here they were inline
literals, starred constants, `ALTER TYPE` loops, and raw `CREATE TYPE`. Three were covered.

**And model the thing, not the text.** A migration chain is a *sequence of operations*, not a bag
of labels. Unioning everything mentioned in the files answers "what labels appear anywhere",
which is not the question. A fifth defect fell straight out of the same mistake: scanning raw file
text replayed `downgrade()` too, and that migration's downgrade recreates the types with the old
labels — so the guard was describing a database nobody has. Replaying `upgrade()` bodies in
revision order fixed both at once.

Five defects in one guard, four of them the same shape. The ones found before review were found
because the module reports what it cannot parse; the one found in review was in the part that
parsed *successfully* and simply never looked. **Reporting unparseable input protects against
constructs you half-handle, not against constructs you never considered.** Only enumerating the
input space does that.
