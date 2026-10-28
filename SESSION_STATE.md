# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## START HERE — what the next session should pick up

**1. Work the 2026-10-28 action plan** — the "START HERE — ACTION PLAN 2026-10-28" block at the top of
`## Active Phase` in `tasks/todo.md`. It was built from an 8-agent assessment (mean ~6/10: engineering strong,
commercial side unstarted) and ratified by council majority vote. Order: Phase 0 state + alarms (Sprint 854) →
Phase 1 buyer-facing truth (#235 → #236 → #237, Sprint 855 = old PR #254, Sprint 856) → Phase 2 backup (778b,
**gates the first live checkout**) → Phase 3 Solo-only Stripe live (Sprint 858, then Phase 4.1) → Phase 4 firm
tier (853). A **freeze** applies to every other refactor/feature sprint until Sprint 781 reports or 30 days after
Phase 3, whichever is first.

**2. CEO track (parallel, blocks named items):** `waitlist_signups` count + 3 unguided CPA sessions by
2026-11-07 (Sprint 781); `RENDER_API_KEY` repo secret; R2 backups token + Neon connection string (778b); refund
policy, legal entity, repo visibility; custom domain `api.paciolus.com` (before Stripe); confirm or decline the
council's counsel-timing recommendation (Q4); ISA 315 citation (H12).

**3. Production.** `main` is `1435b0e4` and live on Render — deploy `dep-dbh0plavcj2c73e057bg` verified
2026-10-28 (workspace `tea-d6ie7bngi27c738fa2ag`, service `srv-d6ie9l56ubrc73c7eq2g`; pass `workspaceId` to the
Render MCP). `/health/ready` healthy (database + rate-limit storage).

## This Session — 2026-10-28, council assessment → action plan

- Ran all 8 agent personas; synthesised; drafted a plan; all 8 reviewed it and voted (7 questions; 21 of 23
  amendments adopted). Plan written into `tasks/todo.md`, Sprints 854–858 filed.
- The 2026-10-28 nightly was RED because `backend/venv` lagged `requirements.txt` (FastAPI 0.136 vs 0.162 →
  99 collection errors). Shared venv re-synced from `requirements-dev.txt`; 10,297 tests collect. Sprint 854
  makes the orchestrator self-heal.
- Archived Sprints 813 and 848 (merged in `1435b0e4`); fixed `.claude/agents/designer.md` (asked for Inter /
  navy / slate); CLAUDE.md phase table extended.

## Verification

**Backend tests:** 10,006 passed / 0 failed in the 2026-10-27 nightly; 10,297 collected on `main` 2026-10-28.
**Frontend tests:** 2,078 passed / 0 failed (2026-10-27 nightly).

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
