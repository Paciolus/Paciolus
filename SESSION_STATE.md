# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## Last Session

**Date:** 2026-10-21
**Branch:** merged. **Six PRs landed on `main`** — #179, #181, #182, #183, #184, #185 — every one rebase-or-squash per `required_linear_history`, and every backend merge verified deployed.

**Context:** a continuation session. Began by landing the Sprint 780 PR already in flight, then worked the 2026-10-20 worklist. The through-line turned out to be a single defect class, found seven times before it was worth auditing for rather than reacting to.

### What landed

| PR | Sprint | What |
|----|--------|------|
| #179 | **780** | Stripe price-parity preflight + webhook coverage 55% → 88% |
| #181 | **785** | Nine stranded branches recovered — **open PR count 25 → 0** |
| #182 | **789** | **P1:** SoD was 403ing Solo and Professional while Terms, pricing, the FAQ and the checkout modal all promised it |
| #182 | **787b** | Six promoted tools wired into engagement tracking (backend) |
| #183 | **789b** | Three stale tool counts on live marketing pages, one on the homepage; the gate extended to customer copy |
| #183 | **791** | The six promoted tools' hooks now send `engagement_id` |
| #184 | **784b + 784c** | Six new user-guide chapters; six stale per-tool test counts corrected |
| #185 | **792** | Preventive audit of every gate for the scope gap — the guard itself had the defect, caught in review |

**Fourteen review findings across #182–#185 were acted on. Every one was real.** Six became code fixes, four corrected documentation, three falsified claims I had written into sprint records, and one found that the guard written to prevent a defect class was itself a member of it. All recorded as corrections rather than quietly amended.

**Production:** healthy throughout. Live deploy SHA **==** `origin/main`; `/health/ready` reports `status: "healthy"`, DB ~7–9 ms, `rate_limit_storage` redis not degraded. Checked the **body**, not just the 200 — Sprint 774 puts `degraded` behind a 200.

### The pattern — read this before adding or trusting a gate

**Seven findings were the same defect: a consistency gate scoped by a file list silently stops covering what it is named after, and reports success.** Sprint 792 stopped fixing instances and audited the class. The ranking that predicted every outcome:

- **Immune** — `check_openapi_drift.py` derives its targets from the running app. No list to rot.
- **Comprehensive** — `lint_design_tokens.py` rglobs all of `frontend/src`; the route linters cover `routes/*.py` including aggregator indirection.
- **Fragile** — an explicit tuple of paths. **All seven findings were here, without exception.**

The operating rules, now in `tasks/lessons.md`:
- Prefer deriving the scan set from the system; failing that a glob; failing that a hand-maintained list **with a test that it still matches something**.
- "The gate is green" and "the gate scanned something" are different claims.
- For anything sold, assert against **behaviour**, not a second description of it.
- When inheriting a gate, do not read its *file list* as its *scope* — the scope is the patterns.

### Open P1s that need a decision, not more engineering

**Sprint 793 — both tax tools apply one fixed set of statutory limits to every year.** Found by the #184 review and the most serious thing in the session.

`w2_reconciliation_engine.py:40-51` and `form_1099_engine.py:94-98` both accept `tax_year` (validated 2000–2099), pass it into the config, and **never use it to select anything**. The W-2 constants are headed "2026 reference values" and are the 2025 figures; the 1099 thresholds are static at $600/$600/$10 and do not vary by sub-category.

**No numbers were changed.** These are customer-facing tax amounts driving filing decisions, and I should not adjudicate current law from a code review — Sprint 793 makes practitioner confirmation step 1, and **Sprint 781's CPA validation is the natural place**. The framing needing no tax knowledge: one fixed set across a hundred-year range is wrong regardless of which year it represents.

Interim honesty shipped: both chapters carry caveats naming what is and is not affected (the wage comparisons and 941 reconciliation are sound — they compare the customer's own numbers to each other), and both `features/status.json` entries went `complete` → `partial`.

**Sprint 790 — the advertised 100/500 monthly upload allowances are unenforced on every paid tier.** `check_upload_limit` only *reads*; `increment_upload_count`'s sole caller is `routes/bulk_upload.py:154`. Free tier *is* metered via its `ActivityLog` fallback — the only metered tier is the one making no money. Needs two CEO decisions: what counts as one upload when a tool takes two files, and what happens to existing accounts whose counters bulk upload left non-zero.

## Current Environment State

**App status:** working — production live and verified.
**Backend tests:** **8,989 passed / 0 failed** (11m26s, `backend/venv`, clean tree), up from 8,700 at session start.
**Frontend:** 207 suites / **2,036 tests** / 5 snapshots, 0 failures; `tsc --noEmit` exit 0; `npm run build` clean with every route `ƒ (Dynamic)` and `ƒ Proxy (Middleware)` active.
**Lint:** `ruff check .` clean; `eslint src/hooks` clean.
**Open PRs:** **0**, down from 25. All 15 Dependabot PRs closed as superseded — the nine pip ones are churn (every package is a `>=` floor that self-heals per Sprint 777); the four Actions ones are real work those PRs cannot do, refiled as **Sprint 786c** with current SHAs.

> **Two process traps hit this session, both now in `lessons.md`:**
> - A background full-suite run returned `1 failed` purely because the tree was edited mid-run. Nothing was broken. The inverse makes a real failure pass — treat a long verification run as the last thing before committing, or run it from a separate `git worktree`.
> - The union-resolution helper for markdown conflicts silently dropped `---` separators three times. The first instance let `scripts/archive_sprints.sh` destroy three sprint records. The helper is hardened; the archiver now has an integrity gate that aborts before touching `todo.md` if the counted and extracted totals disagree. It reported `6 sprint sections, matches count` on its first real use.

**Open blockers:**
- **Sprint 793 (P1)** and **Sprint 790 (P1)** — both need a decision, described above.
- **Sprint 778** — the off-provider `pg_dump` → R2 backup still does not exist; Neon PITR is the only thing behind production data. Ships pre-launch per the 2026-10-19 decision.
- Phase 4.1 Stripe cutover, 4.2 legal sign-off, 4.3 custom domain (`api.paciolus.com` still 404s) — CEO-gated.
- `RENDER_API_KEY` repo secret still unset, so the deploy-drift probe SKIPs rather than alarms.
- **Sprint 741c / 738** need the Neon connection string (CEO ask D-1); both are restore-drill blockers for 778.
- 21 dev-only npm advisories (babel-jest chain); they do not gate CI (`--omit=dev`).

## Next Priority

The 2026-10-20 worklist (`reports/next-actions-2026-10-20.md`) is largely discharged — tracks 1, 2, 4 and 6 are done.

| # | Item | Owner |
|---|------|-------|
| 01 | **Sprint 793 (P1)** — confirm the statutory figures with a practitioner, then year-key both tables | CEO/CPA confirms, Claude implements |
| 02 | **Sprint 790 (P1)** — decide the metering unit and the existing-account question, then enforce | CEO decides, Claude implements |
| 03 | **Sprint 778** — build the `pg_dump` → R2 backup, one restore drill per mechanism, fix the DR false-green | Claude + CEO console, ½d |
| 04 | Legal to counsel; waitlist count; 5–10 CPAs through the demo (**Sprint 781**) — also the natural home for 793's figures | **CEO — longest lead** |
| 05 | **Sprint 786b / 786c** — the reviewed major bumps, and the six Actions SHA pins | Claude |
| 06 | **Sprint 782b** — external uptime monitor | Claude + one CEO signup |
| 07 | **Sprint 741c / 738** — Alembic ↔ ORM enum drift, migration drift | Blocked on CEO ask D-1 |

**Still parked:** B-6…B-9 until Sprint 781 reports · the live Stripe build until pricing is validated · the 22-engine relocation · the mypy baseline · dev-only npm advisories · the deferred SOC 2 set.

## Recent Git Context

```
main HEAD == live deploy
 ├─ #185  792  — preventive gate-scope audit (no production code)
 ├─ #184  784b + 784c — user guide; 6 review findings, 2 filed as 793
 ├─ #183  789b + 791 — customer-copy gate, engagement hooks; 2 review fixes
 ├─ #182  789 + 787b — SoD tier parity (P1), engagement wiring; 4 review fixes
 ├─ #181  785  — nine stranded branches recovered, backlog 25 -> 0
 └─ #179  780  — Stripe preflight + webhook coverage
```
