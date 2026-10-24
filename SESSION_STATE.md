# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## START HERE — what the next session should pick up

**1. The PR queue is empty.** Every PR from the 2026-10-23 session is merged: #201–#218 (Sprints
812–829). The one exception is #197 (786b frontend dev-type majors), from an earlier session, which still has two open bot threads.
Branch protection requires up-to-date branches (`strict: true`), linear history and **resolved
review conversations**. An automated Codex reviewer comments on every PR, and a green PR stays
`BLOCKED` until its threads are resolved. Merge serially: `gh pr update-branch N --rebase`, wait
for CI, merge. Updating every PR at once starves the runners.

**2. Production.** Render's live deploy is `106c5782` (#218). Every merge this session was
confirmed live by deploy SHA (Render workspace `tea-d6ie7bngi27c738fa2ag`, service
`srv-d6ie9l56ubrc73c7eq2g`; pass `workspaceId` explicitly to the Render MCP). Sprint 812's fix is
verified by the public `GET /export-sharing/{token}` probe returning 404 instead of 500.

**Discovery round 2 (Sprint 829)** ran the eleven original tools against realistic input and
fixed about 40 wrong-output findings. The register is `reports/sprint-829-discovery-round2-2026-10-23.md`.
Four methodology calls came out of it and are listed at the top of `tasks/ceo-actions.md`.

**3. Decisions this session surfaced** (each blocks only its own item):
- **Sprint 790** — reset paid-tier upload counters at deploy, or enforce from next period?
- **Sprint 825** — sampling methodology: zero-error random evaluation always "passes" (S3);
  understatements evaluated as overstatements (S6).
- **Sprint 826 W1/W2** — adding SIMPLE and HSA catch-up fields to the statutory table would make
  today's fully-overridden 2026 requests fail (Sprint 811 refuses rather than falls back). Choose:
  optional fields that disable only their own check, or a contract change. Belongs with 793b.
- **Sprint 818 item 3** — the Trust and Approach pages promise Paciolus never stores
  "individual account balances" or "anomaly details tied to specific accounts or amounts", while
  `uncorrected_misstatements` persists account names with amounts. CEO + counsel.
- **SoD tiering** — one HIGH conflict scores "moderate". Policy, not a bug.
- **Sprint 817** — two unused keyword lists (`PAYROLL_SUSPICIOUS_KEYWORDS`, `PREPAID_KEYWORDS`) may
  be checks that were never wired in. Look before deleting.

## This Session — 2026-10-23, todo burn-down

Worked the code-health backlog (Sprints 812–822) and Sprint 823's discovery, highest customer
impact first. Every fix was reproduced before it was made and has a test that fails on the old
code.

- **812 (P0)** — `request: Any = None` under `@limiter.limit` made FastAPI treat `request` as a
  query param; slowapi got `None` → 500. Tests never saw it because conftest disables the
  limiter. Guard test + the five routers' suites now run with the limiter on.
- **813** — six memos shipped every content page without page number/disclaimer; eleven ignored
  Enterprise branding. Output-level test over all 21 sample PDFs: 6/12 → 0/0. Also fixed a
  24pt title overprinted by its subtitle.
- **814** — `UpgradeGate` missing on AP, JE **and multi-period**; fuzzing found 5 of 6 testing
  tools 500'd on `Infinity` in an ID column (root cause in the shared parser); flux ran no
  gates (quota/format); 11 tool-run recordings raced the client refresh.
- **815** — run-scoped parse memo (not a process-wide cache — Zero-Storage): 100k-row JE
  65.6s → 9.6s; gated fuzzy matching: AP with 2k vendors 65.4s → 13.9s; identical results.
- **816** — JE reciprocal entries reported a 300% flag rate; **FA-T11 measured to today, not
  period end — 6 of 6 correct assets flagged ten months after year-end**; currency NaN raised.
- **817** — dead code removed (one 22 MB image among it), incl. an unreferenced
  `auth.get_current_user` that skipped the password-change revocation check.
- **818** — pricing page, checkout and upgrade modal read one domain module; the ToS table is
  pinned to it by a test.
- **823** — drove the under-exercised tools with realistic data: **58 findings, 21 P1**, register
  in `reports/sprint-823-discovery-2026-10-23.md`. Worst: MUS sampling could turn a "fail" into
  a "pass"; FA-T11 flagged every correct DDB asset; intercompany revenue/expense eliminations
  were reversed; 1099 ignored payment dates and TIN aggregation; a parenthetical negative after a `$` sign parsed as positive
  in every engine.
- **824/826/827** — fixed the unambiguous ones (see the register's status column).

## Verification

**Backend tests:** **9585 passed / 0 failed** — full suite on the Sprint 829 branch, 12.3 min locally.
**Frontend tests:** **2114 passed / 0 failed**, 211 suites. `npm run build` clean.

## Environment notes

- The backend suite takes ~14 min locally. Worktrees were used
  for parallel branches; they need a copied `backend/.env` and a `node_modules` junction, and
  Turbopack cannot build through the junction (build from the main checkout instead).
- `generate_sample_reports.py` rewrites `sample-reports/` — run it deliberately, not by accident.
