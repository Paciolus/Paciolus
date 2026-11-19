# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

_Format rule (Sprint 857, enforced in CI by `scripts/check_state_docs.py`): keep exactly one line of the form
``**Main SHA:** `<short sha>` `` naming the current `origin/main` commit (`git rev-parse --short origin/main`). It
must be an ancestor of HEAD. Refresh it after every merge._

**Main SHA:** `075a35e9`

## START HERE — what the next session should pick up

**1. The START HERE block at the top of `## Active Phase` in `tasks/todo.md`** (rewritten 2026-11-15). Launch is
**2026-12-15**. P0 in order: Sprint 870 (rate limits never fire in production, #274) → Sprint 868 / Phase 4.3
(`api.paciolus.com`; sessions die every 15 min in browsers that don't send the cross-site refresh cookie) →
Sprint 867 (balance sheet "out of balance" on pre-closing TBs) → Sprint 871 (Stripe dispute webhooks, #273) →
Sprint 860 (annual tax tables + CEO sign-off) → Phase 4.1 Stripe live (Solo). The freeze still applies to other
refactor/feature work.

**2. Standing rule (CEO, 2026-11-14):** a claim we cannot prove from the code or a published document is removed,
not reworded. Approved storage wording lives in `frontend/src/content/storage-statement.ts`; guards are
`test_marketing_claims.py`, `test_memo_banned_phrases.py`, `test_storage_claims.py`.

**3. Waiting on the CEO:** counsel sign-off on branch `counsel-redline-863` (do not merge before); backup retention
vs the draft DPA's 30-day promise; confirm the four `R2_EXPORTS_*` env vars on Render; Sprint 781 demand validation.

**4. Production.** `main` `075a35e9` is live on Render (deploy `dep-dbt1semq1p3s73fd48pg`, verified 2026-11-15) and
Vercel (status `success` on the commit). Render workspace `tea-d6ie7bngi27c738fa2ag`, service
`srv-d6ie9l56ubrc73c7eq2g` — pass `workspaceId` to the Render MCP.

## This Session — 2026-11-19, Sprint 886 (exports match the screen)

- Local branch `sprint-886-export-fidelity`, stacked on Sprint 885 (`7251e22c`) → 884 → 883; **not pushed**. Merge
  883, 884, 885 first. Ten commits, one per review item (OUT-09/10/11/12/14/15/16/18 + comparison table); detail in
  `tasks/todo.md` Sprint 886.
- CEO decisions taken this session: three-way match shows the engine's LOW/MEDIUM/HIGH, no score; bank rec tests,
  score and aging shown on screen; unlinked memos say FASB is the default; scores one decimal everywhere.
- Not done here (needs a deliberate run): regenerate `sample-reports/` and the public
  `frontend/public/samples/paciolus-sample-je-testing-memo.pdf` — memo wording changed.

## Verification

**Backend tests:** 10,634 collected 2026-11-15; the only local failure, `test_sprint819_route_snapshots::
test_engagement_export_routes_unchanged` (`content_encoding` gzip vs null), is local-only and passes in CI.
**Frontend tests:** all passing 2026-11-15 (count in `CLAUDE.md`, Completed Phases).

## Environment notes

- The backend suite takes ~13–20 min locally; run it on the chain tip before merging (CI only runs on PRs into
  `main`). Delete a stale local `backend/paciolus.db` if tests report a missing `uploads_window_start` column.
- `D:\Dev\Paciolus\backend\venv` is what the nightly uses — re-sync it (`pip install -r requirements-dev.txt`)
  after any dependency bump merges, until Sprint 854 automates it.
- Worktrees need a copied `backend/.env` and a `frontend/node_modules` junction. **`rmdir` the junction before
  `git worktree remove --force`**, or the main checkout's node_modules is deleted. Turbopack cannot build through
  the junction — build from the main checkout.
- `main` protection: strict up-to-date + linear history + conversation resolution. Batch PRs into one linear
  chain and run CI once; resolve every Codex review thread (fix, reply with SHA, resolve).
- `generate_sample_reports.py` rewrites `sample-reports/` — run it deliberately, not by accident.
