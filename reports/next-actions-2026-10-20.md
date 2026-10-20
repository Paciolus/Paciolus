# Next Actions — Consolidated Worklist

**Date:** 2026-10-20
**Assessed:** `reports/launch-readiness-assessment-2026-10-19.md` (the launch-readiness doc) and the 2026-10-20 worklist recorded in `SESSION_STATE.md` → *Next Priority* (the next-moves doc).
**Readable version:** https://claude.ai/code/artifact/cdbdd9eb-3039-44cf-a97b-23bc5c598543
**Basis:** every status re-verified against current source, live endpoints, GitHub API and today's nightly brief. Where a document's claim no longer holds, the evidence is named.

> Not an audit opinion, assurance conclusion, or regulatory compliance determination.

---

## A. Verdict on the two documents

**The launch-readiness assessment holds up.** Spot-checked its load-bearing claims against the tree and the network today — all still true:

| Claim (2026-10-19) | Status today | Evidence |
|---|---|---|
| AS 1215 still miscited in 3 internal docs | **Still open** | `REPORT_STANDARDS_SPEC.md:440`, `USER_PERSONAS.md:273`, `ARCHITECTURE.md:380` |
| Sample generator emits "systemic review of procure-to-pay controls" | **Still open** | `backend/generate_sample_reports.py:2266` |
| Risk-tier qualifier never added | **Still open** | zero matches for "automated flag density" anywhere in `backend/` |
| `billing/webhook_handler.py` at 59.9%, 174 uncovered | **Unchanged** | 2026-10-20 nightly Coverage Sentinel |
| Repo has no secrets at all | **Unchanged** | `gh secret list` → empty |
| `api.paciolus.com` 404s | **Unchanged** | `curl` → 404 (onrender API 200, `paciolus.com` 200) |
| Suites green, coverage flat | **Confirmed** | nightly: backend 8,700/0, frontend 2,013/0, coverage 93.34% (+0.01pp) |
| Lead scout returns zero | **Confirmed** | nightly: 0 leads across 5 themes |

**The worklist's order is right and I am not re-opening it.** Demand first, liability cheap and early, money path before the first charge, legal started immediately because it finishes last. One correction and two contradictions, all in the same place:

1. **The worklist still carries a withdrawn decision.** `SESSION_STATE.md` → *Next Priority* states: *"Neon PITR is sufficient for launch. Off-provider `pg_dump` → R2 deferred, binding trigger: before the second paying customer. Zero-Storage means no client financial data is persisted."* That decision was **reversed the same day** — see `tasks/EXECUTIVE_BLOCKERS.md` → Resolved Decisions, the assessment's own addendum, and the `tasks/todo.md` Active Phase preamble, all three of which say the backup ships **pre-launch**. Worse, the sentence justifies the deferral with the exact premise Sprint 783 spent two commits disproving: the database *does* persist client financial content (`diagnostic_summaries`, `uncorrected_misstatements`, `analytical_expectations`). `AGENTS.md` makes `SESSION_STATE.md` the **first file a new session reads**, so as written the next session acts on the wrong decision for the wrong reason.
2. **`tasks/todo.md` Sprint 778's heading contradicts its own body** — titled *"rescoped 2026-10-19 — off-provider backup deferred"* while scope item 1 is *"Implement the `pg_dump` → R2 cron"*.
3. **Worklist item 05 understates Sprint 778** as *"Neon restore drill + fix DR false-green"*. The sprint is that **plus** building the backup that does not exist.

**What neither document covers:** the ten items in §B. Five of them are new facts (two dated today), five were simply out of scope.

---

## B. Changed or missed since 2026-10-19

| # | Finding | Evidence |
|---|---|---|
| B-a | **All 9 real-work PRs are now CONFLICTING.** `SESSION_STATE.md` records "all 25 open PRs report `MERGEABLE`" — true on 10-19, false now. The 10-19/10-20 merges (which rewrote `tasks/todo.md` wholesale) conflicted every one of them. | `gh pr view` → `DIRTY`/`CONFLICTING` for #134, #137–#144 |
| B-b | **7 finished sprints are stranded on those branches** — 762, 769, 771a, 772a, 773, 773b, 773c — plus #134 (ADR-018 lint) and #144 (the 2026-04-30 + 05-01 nightly briefs, genuinely still missing from the tree). Each needs rebase-or-close; they were blocked by red CVE gates that have since been fixed, so the original reason not to merge is gone. | `ls reports/nightly/2026-04-30.md` → absent |
| B-c | **Dependency drift is far worse than either doc assumes, and Sprints 760/761 are now obsolete specs.** Today's nightly is RED on this alone: 68 backend / 22 frontend outdated, 5 security-relevant (`cryptography` 46→50, `stripe` 15→16, `fastapi` 0.136→0.150, `SQLAlchemy` 2.0→2.1, `react` 19.2→19.3). Sprint 761 is written against `cryptography==47.0.0`, two majors stale; Sprint 760's 19-package list is six months old. | nightly Dependency Sentinel |
| B-d | **The nightly measures a venv that matches neither `requirements.txt` nor production.** `backend/venv` holds `fastapi` 0.136.0 and `stripe` 15.0.1 against exact pins of `==0.136.1` / `==15.1.0`, and sits at the literal floor values (`cryptography` 46.0.7, `pillow` 12.2.0, `pypdf` 6.10.2, `werkzeug` 3.1.8, `pyasn1` 0.6.3) that CI and the production Docker build resolve past on every fresh install. `SESSION_STATE.md` calls this venv "the CI-representative env, with the new pins". It is neither. CI is green and authoritative; the nightly's dependency RED is partly self-inflicted. | `pip list` vs `backend/requirements.txt` |
| B-e | **Tool-count copy is still at 12 against a canonical 18.** The assessment raised only the FastAPI description as a "copy decision"; it is broader and one instance is public. `backend/main.py:243` sets the OpenAPI description to "12-Tool Audit Intelligence Suite"; `AGENTS.md:5`, `PRODUCT_VISION.md` (6 places incl. the hero line), `ARCHITECTURE.md:13`/`:178`, `USER_GUIDE.md` and `ceo-actions.md`'s own Phase 3 checklist all still say 12. `tests/test_catalog_consistency.py` guards the registry, not prose. | grep across repo |
| B-f | **Sprint 741 is no longer blocked.** It waits on a post-deploy read of the `cleanup_scheduler` failure class — impossible while every endpoint 500'd for 5.5 months. Production has been live since 2026-10-19, so the scheduler has been running and the log read can now happen. | SESSION_STATE recovery record |
| B-g | **PR #169 (Sprint 783) was open and unmerged** when this assessment was written — 20 checks green, 3 backend matrices still running. It has since gone green and **merged as `7ca466b4`**, so the Zero-Storage accuracy fix is on `main`. Kept as a finding because it is why Track 0.1 exists. | `gh pr checks 169` |
| B-h | **Today's nightly artifacts are untracked** — 8 files plus a modified `.baseline.json`. Same drift that accumulated into a 795-file backlog during dormancy. | `git status` |
| B-i | **Ordering trap in `ceo-actions.md` 4.1:** it instructs pointing the Stripe webhook at `https://api.paciolus.com/billing/webhook`, which 404s because 4.3 (custom domain) has not run. Configuring the signing secret against a dead endpoint silently breaks every webhook. Either 4.3 precedes 4.1 or 4.1 uses the onrender URL. | `curl` 404 |
| B-j | **`ceo-actions.md` — the self-declared "single source of truth for every action required to launch" — is stale.** Header reads "Status as of 2026-04-24", "Your next action: Phase 3", "12 testing tools"; §4.4 still frames the backup as optional belt-and-suspenders; nothing records the 2026-10-19 outage, the recovery, the removed review gate, or the new worklist order. | file read |

---

## C. The consolidated action list

Seven tracks. Owner and size on each. Track 5 runs in parallel from today and gates the most expensive decisions.

### Track 0 — In flight, today (Claude, ~1h)

| # | Action | Notes |
|---|---|---|
| 0.1 | ~~Merge PR #169~~ — **DONE**, squash-merged as `7ca466b4` after all required checks passed | Linear history is on, so squash or rebase only. This had to land first: the Sprint 783 commit rewrote `tasks/todo.md` wholesale, so any branch editing that file in parallel would conflict. |
| 0.2 | **Fix the withdrawn decision and the two contradictions** (§A 1–3) | `SESSION_STATE.md` *Next Priority* bullet 2 → the pre-launch decision with the corrected premise; Sprint 778's heading; worklist item 05's wording. Hotfix. |
| 0.3 | **Commit the 2026-10-20 nightly artifacts** | 8 files + `.baseline.json`. Hotfix. |
| 0.4 | **Refresh `ceo-actions.md`** (B-j) and fix the webhook-endpoint ordering trap (B-i) | It is the CEO-facing source of truth; it should not be six months behind the launch plan. |

### Track 1 — Liability and self-truth (Claude, ~2h)

| # | Action | Notes |
|---|---|---|
| 1.1 | **Sprint 779 — boundary-language + citation residue** | All three targets re-verified open today. Plus the two CI guards: hold `generate_sample_reports.py` to the banned-phrase rules, and extend `test_citation_consistency.py` over `docs/`. The guards are the point — this is the class of defect that drifted back once already. |
| 1.2 | **Sprint 784 (new) — tool-count cohesion sweep, 12 → 18** | B-e. Closes assessment §I item 4 and goes wider than it: the public OpenAPI description plus the product docs. Extend the documentation-consistency gate to prose counts so it cannot drift again. |

### Track 2 — The money path (Claude, ~1d)

| # | Action | Notes |
|---|---|---|
| 2.1 | **Sprint 780 — Stripe price-parity preflight** | Must cover all 6 base prices (`STRIPE_PRICE_{SOLO,PROFESSIONAL,ENTERPRISE}_{MONTHLY,ANNUAL}`) **and** all 4 seat prices (`STRIPE_SEAT_PRICE_{PRO,ENT}_{MONTHLY,ANNUAL}`) — env var names verified against `price_config.py:36,185,195`, and the canonical amounts are `PRICE_TABLE[tier][interval]` + `PROFESSIONAL_SEAT_PRICE` / `ENTERPRISE_SEAT_PRICE`, not `TIER_PRICES`. Side benefit: run locally it immediately names the stale v2 variables in `backend/.env` (`STRIPE_PRICE_TEAM_*`, `STRIPE_SEAT_PRICE_MONTHLY`) that the code no longer reads. |
| 2.2 | **Sprint 780 — webhook handler coverage 59.9% → 85%+** | Signature verification, event dedup (`processed_webhook_events`), subscription state transitions. Deferred twice; it is the least-tested path that moves money. |

### Track 3 — Survive losing the database (Claude + CEO console, ~½d)

| # | Action | Notes |
|---|---|---|
| 3.1 | **Sprint 778 — build the `pg_dump` → R2 cron** | Into `paciolus-backups`, provisioned and empty since April. Decision is settled pre-launch; do not reopen. |
| 3.2 | **Verify the real Neon PITR retention window** | Rather than trusting `DEPLOYMENT_ARCHITECTURE.md:724`. |
| 3.3 | **One real restore drill per mechanism, with recorded evidence** | Schema parity + row counts against production. An untested backup is not a backup — and this is the half a second mechanism does not fix. |
| 3.4 | **Rewrite both DR workflows against Neon + R2** and fix the false-green | They currently query the Render Postgres API for a DB deleted 2026-04-22; `DR Test (Monthly)` reports success while its own verdict is FAIL. Missing credentials must report "unverified", not die opaquely. |

### Track 4 — Lock in what is already won (Claude ~2h + one CEO signup)

| # | Action | Notes |
|---|---|---|
| 4.1 | **Sprint 782 — design-token CI guard** | 0 generic Tailwind colours across 777 files, currently protected by nothing but discipline. |
| 4.2 | **Sprint 782 — external uptime monitor** | GitHub disables cron workflows after ~60 days idle, so the in-repo check switches itself off during exactly the quiet period it guards. Must alert on `status != "healthy"` in the **body**, not on non-200 — Sprint 774 deliberately reports `degraded` behind a 200. |
| 4.3 | **Add `RENDER_API_KEY`** so the deploy-drift probe arms | The repo has no secrets at all; the probe currently SKIPs. |

### Track 5 — CEO, starts today, runs in parallel

| # | Action | Notes |
|---|---|---|
| 5.1 | **Send Terms + Privacy to counsel** | Longest lead of anything on this page and a hard launch blocker. Needs the registered address, registered agent, and the EU-representative/DPO decisions resolved first. Zero engineering dependency — every day unsent is a day added to launch. **Give counsel the Sprint 783 Zero-Storage rewrite too**, since the retention claims now carry explicit carve-outs. |
| 5.2 | **Security Policy §12 emergency phone** | One line. |
| 5.3 | **Read the `waitlist_signups` count** | Still the single most informative number in no report. I cannot reach it: no `DATABASE_URL` locally and the DB is on Neon, which the Render MCP cannot query. Give me the Neon connection string and I will read it, or read it yourself in the Neon console. |
| 5.4 | **Sprint 781 — 5–10 practising CPAs through demo + free tier on their own TB** | Watch where they stall; do not guide. Ask the price question early. This is what ranks B-6…B-9, and nothing in those four should be built before it reports. |
| 5.5 | **Phase 4.3 custom domain before 4.1 webhook config** | See B-i. |

### Track 6 — Backlog debt (Claude, sized after triage)

| # | Action | Notes |
|---|---|---|
| 6.1 | **Sprint 785 (new) — dispose of the PR backlog** | Rebase-or-close the 9 conflicting real-work branches (7 finished sprints + #134 + #144). Branches, not cherry-picks: #144's diff against current `main` reads as 125k deletions because it is based on pre-dormancy `main`. |
| 6.2 | **Sprint 786 (new) — dependency currency, replacing Sprints 760 and 761** | Both are obsolete (B-c). Sequence: the 5 security-relevant first, each major isolated per policy, then reconcile `backend/venv` to a fresh resolve of `requirements.txt` and record the resolution (B-d) — that `pip freeze` evidence is the missing piece Sprint 777's rule depends on. Close 760/761 as superseded. |
| 6.3 | **Triage the 15 Dependabot PRs** | Most are superseded by newer releases; the oldest is from 2026-04-13. Close or let 6.2 absorb them. |
| 6.4 | **Sprint 741 — `cleanup_scheduler` root class** | Now unblocked (B-f): pull `error_orig_fqn` from a post-recovery cleanup cycle, fix the real failing statement, add the regression test. |
| 6.5 | **Sprint 738 — Alembic drift** (P3) | Gated on a production schema read of the 4 orphan tables + 6 columns. Worth noting `waitlist_signups` is one of them, so 5.3 and this touch the same table. |
| 6.6 | **Sprint 762 — flux_expectations memo contract test** | Already written, stranded on a conflicting branch. Folds into 6.1. |

### Parked deliberately (unchanged)

B-6 through B-9 (service-invoice two-way match, impairment screen, judgmental sampling, assertion-coverage worksheet) until 5.4 reports · the live Stripe build until pricing is validated · the 22-engine relocation · the mypy baseline (1,011, baselined, not drifting) · 21 dev-only npm advisories (need `--force`, do not gate CI) · the deferred SOC 2 set.

---

## D. What I need from you

| # | Need | Blocks |
|---|---|---|
| D-1 | Neon connection string (read-only is fine) — or read the count yourself | 5.3, and the production schema read in 6.5 |
| D-2 | `RENDER_API_KEY` as a repo secret | 4.3, and the DR workflow rewrite in 3.4 |
| D-3 | Confirmation that the R2 `paciolus-backups` token still works | 3.1 |
| D-4 | Registered address, registered agent, EU-rep/DPO decisions | 5.1 — and this is the critical path to launch |
| D-5 | Go/no-go on 6.1: rebase the 7 stranded sprints, or close them and re-do the work on current `main` | 6.1 sizing |

Everything in Tracks 0–2 and 4.1–4.2 needs nothing from you and can run now.

---

## E. Ledger changes this list implies

- **Fix:** `SESSION_STATE.md` *Next Priority* bullet 2 · `tasks/todo.md` Sprint 778 heading · worklist item 05 wording · `tasks/ceo-actions.md` header, Phase 3 tool count, §4.4 framing, 4.1/4.3 ordering.
- **New sprints:** 784 (tool-count cohesion) · 785 (PR backlog disposition) · 786 (dependency currency).
- **Close as superseded:** Sprint 760, Sprint 761.
- **Unblock:** Sprint 741.
- **Re-title:** Sprint 778 to match its own scope.

---

*Prepared by Claude Opus 5 · 2026-10-20 · basis: direct source, endpoint and GitHub API verification.*
