# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

_Format rule (Sprint 857, enforced in CI by `scripts/check_state_docs.py`): keep exactly one line of the form
``**Main SHA:** `<short sha>` `` naming the current `origin/main` commit (`git rev-parse --short origin/main`). It
must be an ancestor of HEAD. Refresh it after every merge._

**Main SHA:** `ef5e5676`

## START HERE — what the next session should pick up

**1. The START HERE block at the top of `## Active Phase` in `tasks/todo.md`** (updated 2026-11-24). Launch is
**2026-12-15**. Everything that was code-complete is merged in one chain (2026-11-24); what is left is the deploy
check, Sprint 870 part B, Sprint 868 re-scoped after 874, Sprint 860 sign-off, Stripe live, counsel, and 893 G.

**2. Standing rule (CEO, 2026-11-14):** a claim we cannot prove from the code or a published document is removed,
not reworded. Approved storage wording lives in `frontend/src/content/storage-statement.ts`; guards are
`test_marketing_claims.py`, `test_memo_banned_phrases.py`, `test_storage_claims.py`.

**3. Waiting on the CEO:** counsel sign-off on branch `counsel-redline-863` (do not merge before); backup retention
vs the draft DPA's 30-day promise; Sprint 893 G enum labels; Sprint 869 calibration minimum; Sprint 876's
completed-engagement writability; Sprint 781 demand validation.

**4. Production.** Render workspace `tea-d6ie7bngi27c738fa2ag`, service `srv-d6ie9l56ubrc73c7eq2g` — pass
`workspaceId` to the Render MCP. The 2026-11-24 merge runs nine migrations on deploy (`c3e7a1f9d524` …
`d881b3c5e7f9`); confirm the deploy SHA and `/health/ready` body after it.

## This Session — 2026-11-24, Sprint 894 + integration merge

- Sprint 894: todo checkboxes 893 had closed; Next.js 16.4.6 (build no longer exits on Next's security gate);
  122 response-schema amount fields to `ExactMoney`.
- CEO: "do the merges and the PRs". Replayed 853/872–881 (37 commits), 867+882 (combined, ported to Decimal) and
  PRs #317, #319–#323, #325–#330 onto 883–894 in branch `integration-2026-11-24`; integration fixes listed in the
  todo START HERE block. CEO approved #327 (Sprint 874 CSRF change) the same day.
- Local branches for every merged sprint can be deleted after the merge is verified.

## Verification

See the 2026-11-24 entry in `tasks/todo.md` (START HERE) for the chain's backend, frontend, mypy and build results.

**Backend tests:** 11,954 run on PR #333's first CI pass (Python 3.12, 2026-11-24); its ten failures were
integration mismatches between the merged branches, fixed in the next commit.

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
