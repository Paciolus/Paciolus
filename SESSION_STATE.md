# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## START HERE — what the next session should pick up

**1. Two branches are open and neither is merged.**
- **PR #197** — `sprint-786b-frontend-devtype-majors`, three commits (`@types/node` 26, the
  dynamic-route invariant, the jest-dom blocker). Unchanged by this session; verify and merge.
- **`dec-review-2026-10-22-remediation`** — this session's work. Branched off `main`, so it is
  independent of #197 and touches `ci.yml` and `tasks/todo.md` in regions #197 does not.
  Needs a PR, review and merge.

**2. One CEO action, and it is the only thing left from the review.** Four CI gates produce a
red X and merge anyway — **Accounting Policy**, **Documentation Consistency**, **Report
Standards** and **OpenAPI Schema Drift**. Making them block is a repository-settings change,
so it was not made unilaterally. The exact `gh api` call is in
`reports/council-audit-2026-10-22.md` under "Still outstanding". All four pass on this branch.

**3. The Digital Excellence Council review is done and so is its remediation.**
`reports/council-audit-2026-10-22.md` — 14 findings, 27 measurements, all CONFIRMED by
running the code. Sprints 795–802 fixed every one (F-006 partially; see item 2) and are
archived to `tasks/archive/sprints-741-802-details.md`.

**4. Still blocked on a decision, not on engineering** — unchanged from the previous session:
**Sprint 793b** (statutory tax limits — needs a practitioner) and **Sprint 790** (upload
allowances unenforced on paid tiers — needs a metering-unit decision). Sprint 800 did add an
honest test that *pins the 790 gap* rather than papering over it: when
`increment_upload_count` gains a second caller, the test fails and tells you to update it.

**5. Sprint 738 is no longer blocked — it is done.** It sat for a year recorded as waiting on
the Neon connection string. It never needed one. Sprint 797 delivered it. **Worth reading the
entry before trusting any other inherited blocker.**

**6. `jest-dom` 7 still blocked by the npm arborist bug**, and `reportlab` 5 / `stripe` 16
still want `RENDER_API_KEY` before deploying. Unchanged.

## This Session — Digital Excellence Council review, then remediation

**Date:** 2026-10-22
**Branch:** `dec-review-2026-10-22-remediation` (off `main` at `a946de8e`)

A full-spectrum review followed by a same-day instruction to fix everything it found.

### What the review found

14 findings — 4 P1, 4 P2, 4 P3, 2 informational — every one confirmed by running the code or
by injecting a violation, with 27 measurements recorded. The four that mattered:

| # | Finding | Measurement |
|---|---------|-------------|
| F-001 | The depreciation tool **ignored the MACRS system the customer selected** | `gds_200db` / `gds_150db` / `gds_sl` all returned $20k year-one on a $100k 5-year asset. The dropdown offered all three |
| F-002 | The loan amortization schedule **did not foot** | 21.51% of 6912 schedule rows; 10.0% of 420 configurations produced a **journal entry whose debits did not equal its credits** |
| F-003 | **No database build path produced a correct schema** | Chain: 25 of 29 tables. Dockerfile on an empty DB: 27 of 29, permanently |
| F-004 | The monetary-precision gate **inspected 0% of its target** | 0 `Column(` vs 169 `mapped_column(`; 0 of 87 in its own protected classes |

### The through-line

The previous session's was *a check that cannot distinguish "no problem" from "I did not
look"*. This one narrowed it: **three populations that were supposed to be the same thing and
were not** — the guard, its tests, and its target. `monetary_float.py` matched `Column(`; the
codebase had migrated to `mapped_column(`; the unit tests were written in `Column(`. All three
green, inspecting nothing. The SQLAlchemy 2.0 migration moved every declaration and the guard
watching them was not in the diff.

Same shape elsewhere: three model-import lists holding 11 / 15 / 15 entries under comments
instructing the reader to keep them in sync; `ci.yml`'s header claiming eleven required checks
against a live twelve that were not the same twelve.

### What I got wrong, and what caught it

**Four of my own regression proofs came back green on code I had deliberately broken**, for
four different reasons — process-global `Base.metadata` hiding an import gap, a premise about
cwd that was never true, a guessed `>= 20` floor (reality 18), and a fixture that varied the
property class alongside the system so it could not isolate either. None meant the fix was
wrong; all four meant the proof measured something else.

**And my first coverage self-check had the bug it was written to catch** — it counted
candidates using the parser's own factory list, so narrowing the parser would have dropped both
counts to zero and reported full coverage of nothing. The working oracle is the `Mapped[...]`
annotation, which belongs to the ORM contract rather than to any factory name.

**Two guards argued with me and were right**: one caught an allowlist claiming
`execute_file_tool` enforces entitlement (it is a file-handling scaffold and does not), and
the export-gate test flagged four routes that are *correctly* ungated — a share link is for a
recipient with no account, and gating revocation behind a paid tier would trap data in a link
the user can no longer cancel. Both became reasoned exemptions rather than silent passes.

**One review finding was half wrong and is corrected in the report**: `weekly_security_digest.py`
is not unwired — it is a documented manual tool referenced by `SECURITY_POLICY.md` and the
review template. The grep behind that claim timed out and I reported a partial result as a
complete one.

### Found while fixing, not while reviewing

- The **depreciation engine had the loan engine's rounding defect too** — a $123,456.78 asset
  reporting $123,456.77 of total depreciation against a 0.00 ending book value. Found by a new
  test.
- **`scripts/overnight/tests/` ran in no workflow.** The regression tests for the nightly
  agents, including the Sprint 712 false-green guard, were themselves unwatched.
- **Prior-period DuPont deltas are unreachable** (both call sites pass `previous_totals=None`)
  — caught before it reached the user guide, where it would have reproduced F-007 exactly.

## Current Environment State

**App status:** working. Production untouched by this session — no deploy, no settings change.
**Backend tests:** **9,209 passed / 0 failed** in 821.8s, up from 9,126 collected at session
start (+83). Measured on the final tree with `-p no:randomly`.
**Frontend tests:** **2041 passed / 0 failed**, 207 suites. `npm run build` clean and emitting
`f (Dynamic)`, which CSP nonce injection requires. `tsc --noEmit` exit 0.
**Lint:** `ruff check` clean. `ruff format` applied to the six files I had regressed from clean
and to every file I created; the 84 pre-existing unformatted files were left alone, since
formatting is not a CI gate here and restyling them is churn.
**Gates:** all eight green — accounting policy, doc consistency, enum label drift, report
standards, route wiring, design tokens, OpenAPI drift, overnight agent tests.
**Migrations:** chain replays to 29 of 29 tables with zero column and zero FK drift, proved
up/down/up on both a chain-built and a `create_all()`-built database.

**Open blockers:** unchanged — 793b and 790 need decisions; 778b (off-provider backup) still
unbuilt; 741c steps 1-3 still want the Neon string; Phase 4.1/4.2/4.3 CEO-gated;
`RENDER_API_KEY` still unset.

## Next Priority

| # | Item | Owner |
|---|------|-------|
| 01 | Merge PR #197, then open and merge the remediation branch | Claude |
| 02 | **Make the four advisory gates required** — one `gh api` call, command in the report | **CEO** |
| 03 | **Sprint 793b (P1)** — practitioner-confirmed statutory figures | CEO/CPA, then Claude |
| 04 | **Sprint 790 (P1)** — decide the metering unit, then enforce | CEO decides |
| 05 | **Sprint 778b** — `pg_dump` to R2 backup plus one restore drill. Sprint 797 makes a chain-built restore sound for the first time, so the drill will now mean something | Claude + CEO console |
| 06 | Legal to counsel; waitlist count; 5-10 CPAs through the demo (**Sprint 781**) | **CEO — longest lead** |
| 07 | **Sprint 786b steps 3-4** — remaining dependency majors | Claude |
| 08 | **Sprint 794 step 3** — should an npm/PyPI outage block every PR? | **CEO decides** |

**Still parked:** B-6...B-9 until Sprint 781 reports, the live Stripe build until pricing is
validated, the 22-engine relocation, the mypy baseline, dev-only npm advisories, the
deferred SOC 2 set.
