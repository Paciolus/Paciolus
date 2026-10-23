# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## START HERE — what the next session should pick up

**1. Land the open stack, bottom-up.** Branch protection requires up-to-date branches
(`strict: true`) and linear history, so each merge forces the next PR to rebase and re-run CI.
Stacked PRs only get a 5-check CI subset until they target `main`.

| PR | Sprints | Base | State at session end |
|----|---------|------|----------------------|
| #203 | 815 engine performance | `main` | CI re-running after rebase; merge when green |
| #205 | 823 discovery + 824 sampling/parser fixes | #203's branch | rebase onto `main` after #203 merges, retarget, close/reopen to trigger full CI |
| #206 | 826 (1099) + 827 (IC, FA-T11, SoD, cash flow) | #205's branch | same, after #205 |
| #207 | 817 dead-code sweep (+ this file) | `main` | independent of the stack |
| #197 | 786b frontend dev-type majors | `main` | unchanged from the previous session |

After a squash-merge below a stacked PR: `git rebase --onto origin/main <old-parent-tip>`,
force-push, `gh pr edit N --base main`, then `gh pr close N && gh pr reopen N`.

**2. Production.** Sprint 812 (19 rate-limited org/admin/branding/sharing/bulk routes 500'd on
every call) is **live and verified**: the public `GET /export-sharing/{token}` probe flipped
500 → 404 three minutes after merge. #202 (memo PDFs, upload routes, engine correctness) and
#204 (pricing) also merged; Vercel deployed #202's frontend. **The Render deploy of #202 was
not verified** — the Render MCP needs a workspace selected, which is the CEO's call.

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
  65.6s → 9.6s; gated fuzzy matching: AP on 2,000 vendors 65.4s → 13.9s; identical results.
- **816** — JE reciprocal entries reported a 300% flag rate; **FA-T11 measured to today, not
  period end — 6 of 6 correct assets flagged ten months after year-end**; currency NaN raised.
- **817** — ~9,700 lines and 22 MB of dead code removed, incl. an unreferenced
  `auth.get_current_user` that skipped the password-change revocation check.
- **818** — pricing page, checkout and upgrade modal read one domain module; the ToS table is
  pinned to it by a test.
- **823** — drove the under-exercised tools with realistic data: **58 findings, 21 P1**, register
  in `reports/sprint-823-discovery-2026-10-23.md`. Worst: MUS sampling could turn a "fail" into
  a "pass"; FA-T11 flagged every correct DDB asset; intercompany revenue/expense eliminations
  were reversed; 1099 ignored payment dates and TIN aggregation; `$(2,000.00)` parsed as +2,000
  in every engine.
- **824/826/827** — fixed the unambiguous ones (see the register's status column).

## Environment notes

- The backend suite takes ~14 min locally (9,437 passed on the 824 branch). Worktrees were used
  for parallel branches; they need a copied `backend/.env` and a `node_modules` junction, and
  Turbopack cannot build through the junction (build from the main checkout instead).
- `generate_sample_reports.py` rewrites `sample-reports/` — run it deliberately, not by accident.
