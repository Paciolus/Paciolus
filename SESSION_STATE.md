# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## Last Session

**Date:** 2026-10-22
**Branch:** merged. **Five PRs landed on `main`** — #187, #188, #189, #190, #191 — every one rebase-merged per `required_linear_history`.

**Context:** a continuation session, picking up with three PRs in flight and working down the unblocked backlog. The through-line continued from the previous session and sharpened: **a check that cannot distinguish "no problem" from "I did not look".**

### What landed

| PR | Sprint | What |
|----|--------|------|
| #187 | **778a** | The monthly DR workflow reported success while its own verdict said FAIL |
| #188 | **786c** | Six GitHub Actions SHA pins refreshed; a guard so they cannot rot unnoticed |
| #189 | **793a** | The statutory-limit overrides the W-2 API never exposed |
| #190 | **794a** | A registry outage was reporting itself as a vulnerability |
| #191 | **741d** | 19 drifting enum types frozen so the set cannot grow |

**Six review findings across #187–#191 were acted on. Every one was real** — continuing the previous session's fourteen-for-fourteen. Counted from the PRs themselves rather than from memory: #187 two, #188 one, #189 two, #190 none, #191 one. Two changed the *result* rather than the wording — #188's pin guard was inspecting 23% of its target, and #191's enum guard reported drift on a type that agrees.

**Production:** healthy throughout. `/health/ready` reports `status: "healthy"`, DB ~9 ms, `rate_limit_storage` redis not degraded; `paciolus.com` returns 200. Checked the **body**, not just the 200 — Sprint 774 puts `degraded` behind a 200.

> **Deploy verification has a hole, and it is worth knowing about.** There is no way to confirm from outside that a merge actually deployed: the Render MCP requires selecting a workspace (not Claude's call to make), `/openapi.json` and `/docs` are correctly disabled in production, and **no endpoint exposes a build commit**. The `RENDER_API_KEY` gap is already tracked (`ceo-actions.md:11`), so it was not re-filed. Exposing the commit SHA on `/health` was considered and **deliberately not shipped**: `routes/health.py:61-65` documents a decision to *remove* version from `/health/live` to stop scanners fingerprinting the build, and a commit SHA is strictly more precise. With a public repo and auto-deploy, it would tell an attacker exactly which published fixes are live — and the window where that matters is precisely the silent-failed-deploy case. That tradeoff deserves a decision, not a quiet commit.

### The pattern — three outcomes, not two

Every check that depends on something outside the commit has **three** possible answers: pass, fail, and **did-not-run**. An implementation with two exit codes is reporting one of those three as a different one.

| Sprint | The check | What it could not say |
|--------|-----------|-----------------------|
| 778a | Monthly DR test | "I detected a failure" — the job exited 0 regardless |
| 794a | npm CVE gate | "I could not check" — a 503 is reported as a finding |
| 775 (by design) | Deploy-drift probe | correctly reports `SKIP` when `RENDER_API_KEY` is absent |

The third row is the one to copy: the only one built knowing the answer has three states, and the only one that never lied.

**Deciding the third state's policy is separate from exposing it, and much easier once a retry is in.** Sprint 794a kept the existing fail-closed behaviour and changed only the words, so no policy decision gated the fix.

### The other pattern — coverage of a construct family is not coverage of the subject

Both guards written this session shipped with a coverage self-check, and the enum guard's **passed while the parser had no handler for an entire construct family**. It counted `Enum(..., name=...)` AST calls and confirmed all 26 were seen; `CREATE TYPE ... AS ENUM` is raw SQL inside `op.execute()`, which that check cannot see. The PR #191 review found it.

Five defects in that one guard, four of them the same shape. The four found before review were caught because the module **reports what it cannot parse** rather than skipping it. The fifth was in the part that parsed *successfully* and simply never looked.

> **Reporting unparseable input protects against constructs you half-handle, not against constructs you never considered.** Before writing a coverage test, enumerate the construct families the input can use and check the list is complete. Here they were inline literals, starred constants, `ALTER TYPE` loops, and raw `CREATE TYPE`. Three were covered.

**And model the thing, not the text.** A migration chain is a sequence of operations, not a bag of labels. Unioning every label mentioned answers "what appears anywhere", which is not the question — and the same mistake meant `downgrade()` bodies were replayed too, describing a database nobody has.

### Findings worth the CEO's attention

**`engagementstatus.COMPLETED` is bound by the ORM and added by no migration** (Sprint 741d). The engagement completion gate is a shipped feature, so on any database built from the documented chain — a DR restore, a fresh staging environment — completing an engagement fails. Production is fine because production was built by `create_all()` and stamped. **That is what makes it a restore-drill blocker for Sprint 778 rather than a live incident**, and it is a new finding: nothing in Sprint 741c or its source reviews mentions it.

**Sprint 741c's drift table understated the problem six-fold** — three types by hand, nineteen measured. Every hand-written row was correct; it was simply the subset that got noticed, formatted like an inventory. The fix scope in 741c step 2 was written against three.

**The ORM is internally inconsistent about two parallel tier enums.** `subscription_tier` and `usertier` hold the same four tiers one table apart, and the ORM binds one lowercase and the other as NAMES. So 741c's "pick the canonical direction" is not purely a migration edit — the models disagree with each other first.

### Open P1s that need a decision, not more engineering

**Sprint 793b** — both tax tools apply one fixed set of statutory limits to every year from 2000 to 2099. No numbers were changed: these are customer-facing tax amounts driving filing decisions, and current law should not be adjudicated from a code review. Practitioner confirmation is step 1, and **Sprint 781's CPA validation is the natural home**. Sprint 793a shipped the escape hatch in the meantime — the W-2 API now accepts per-request `statutory_limits` overrides, so a practitioner who knows the right figure can supply it.

**Sprint 790** — the advertised 100/500 monthly upload allowances are unenforced on every paid tier. `check_upload_limit` only *reads*; `increment_upload_count`'s sole caller is `routes/bulk_upload.py:154`. Free tier *is* metered via its `ActivityLog` fallback — the only metered tier is the one making no money. Needs two decisions: what counts as one upload when a tool takes two files, and what happens to existing accounts whose counters bulk upload left non-zero.

## Current Environment State

**App status:** working — production live and verified.
**Backend tests:** **9,055 passed / 0 failed** (11m23s, `backend/venv`, clean tree, run after the last merge with nothing else touching the tree — an earlier run was discarded for exactly that reason). Up from 8,989 at session start; +42 from the two new guards.
**Lint:** `ruff check` clean on everything touched; `ruff format` applied.
**Open PRs:** **0**.

**Open blockers:**
- **Sprint 793b (P1)** and **Sprint 790 (P1)** — both need a decision, described above.
- **Sprint 778b** — the off-provider `pg_dump` → R2 backup still does not exist; Neon PITR is the only thing behind production data. Ships pre-launch per the 2026-10-19 decision. Sprint 741d just added a second reason to care: a chain-built restore does not match production.
- **Sprint 741c steps 1-3 / 738** — need the Neon connection string (CEO ask D-1). Step 4 is done (741d) and needed no database after all.
- **Sprint 794b** — `pip-audit` has the identical conflation to npm's, confirmed empirically (exit 1, no JSON, three more call sites). Unblocked, small.
- **Sprint 786b** — the reviewed dependency majors. Unblocked but large.
- Phase 4.1 Stripe cutover, 4.2 legal sign-off, 4.3 custom domain (`api.paciolus.com` still 404s) — CEO-gated.
- `RENDER_API_KEY` repo secret still unset, so the deploy-drift probe SKIPs rather than alarms — and there is no fallback, per the note above.

## Next Priority

| # | Item | Owner |
|---|------|-------|
| 01 | **Sprint 793b (P1)** — confirm the statutory figures with a practitioner, then year-key both tables | CEO/CPA confirms, Claude implements |
| 02 | **Sprint 790 (P1)** — decide the metering unit and the existing-account question, then enforce | CEO decides, Claude implements |
| 03 | **Sprint 778b** — build the `pg_dump` → R2 backup, one restore drill per mechanism | Claude + CEO console, ½d |
| 04 | Legal to counsel; waitlist count; 5–10 CPAs through the demo (**Sprint 781**) — also the natural home for 793b's figures | **CEO — longest lead** |
| 05 | **Sprint 794b** — give `pip-audit` the same three-outcome treatment | Claude, small |
| 06 | **Sprint 786b** — the reviewed major bumps | Claude |
| 07 | **Sprint 741c steps 1-3** — now has a measured target instead of a hand-assembled one | Blocked on CEO ask D-1 |
| 08 | **Sprint 782b** — external uptime monitor | Claude + one CEO signup |

**Still parked:** B-6…B-9 until Sprint 781 reports · the live Stripe build until pricing is validated · the 22-engine relocation · the mypy baseline · dev-only npm advisories · the deferred SOC 2 set.

## Recent Git Context

```
main HEAD
 ├─ #191  741d — enum label drift frozen at 19 types; 1 review fix (phantom drift)
 ├─ #190  794a — npm audit gate: CLEAN / VULNERABLE / UNVERIFIED
 ├─ #189  793a — W-2 statutory-limit overrides; 2 review fixes
 ├─ #188  786c — six Actions SHA pins refreshed; 1 review fix (guard saw 23%)
 └─ #187  778a — DR workflow reports its own verdict; 2 review fixes
```
