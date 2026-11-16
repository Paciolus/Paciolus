# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

_Format rule (Sprint 857, enforced in CI by `scripts/check_state_docs.py`): keep exactly one line of the form
``**Main SHA:** `<short sha>` `` naming the current `origin/main` commit (`git rev-parse --short origin/main`). It
must be an ancestor of HEAD. Refresh it after every merge._

**Main SHA:** `ef5e5676`

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

**4. Production.** `main` `ef5e5676` (PR #315) is live on Render (deploy `dep-dbt4kc7f3r2c73f39lgg`, verified
2026-11-16) and Vercel (status `success`; homepage headline and `/samples/paciolus-sample-je-testing-memo.pdf` 200).
Render workspace `tea-d6ie7bngi27c738fa2ag`, service `srv-d6ie9l56ubrc73c7eq2g` — pass `workspaceId` to the Render MCP.

**5. Open PRs from the 2026-11-16 overnight session — none merged; each needs CEO review.** Merge order: **#327 first if
approved** (it changes what 868 is for), #316 → #317 → the rest in any order. Every one touches `tasks/todo.md`, so expect
small rebases.
| PR | What | After merge |
|---|---|---|
| #316 | `SESSION_STATE.md` Main SHA → `ef5e5676` | — |
| #317 | Sprint 870 part A: rate-limit key probe + `trusted_proxies_configured` on `/health/ready` | burst ~70 at `/benchmarks/industries`, read `rate_limit_key_probe` lines → part B (the fix) |
| #318 | Sprint 867: pre-closing TB balances; SOCE fixes (incl. pre-existing: SOCE dropped all real equity accounts) | re-run the 2026-11-15 TB |
| #319 | Sprint 871: dispute webhooks resolve the customer via the charge (#273) | Stripe test-mode trigger |
| #320 | Sprint 859: pooler-aware daily DB TLS check | next daily log reads `tls=pooler-skip` |
| #321 | Credentials inventory + Nov 1 rotation checklist; E2E-smoke-never-runs finding | fill **unknown** expiries |
| #322 | Sprint 869: JE count says "GL lines"; calibration left as a CEO decision | regenerate the public sample memo |
| #323 | Sprint 872: TB recalculation within 5 min no longer "duplicate" | move the materiality slider on production |
| #325 | Sprint 873: coverage rows not "Material Risks"; API keeps `coverage_analysis` / `cross_reference_note`; class gate | check TB PDF coverage section |
| #327 | **Sprint 874 (CEO decision): every reload signed production users out** — CSRF rule on `/auth/refresh` could not be satisfied; reverses the 2026-04-20 rule | reload twice + 20-min idle stays signed in; re-scope 868 |
| #328 | Sprint 875: concurrent wrong passwords no longer bypass the 5-attempt lockout | — |
| #329 | Sprint 876: industry-ratio evaluation only against the same client's engagement | — |
| #326 | lessons + this file | — |

## This Session — 2026-11-16 (overnight, CEO away; nothing merged except #315)

- Merged #315 (rebase) after fixing its Secrets Scan: the placeholder DB URL lived in an earlier commit of the PR, so
  the branch was rewritten (tree identical). Production verified on both Render and Vercel.
- Sprint 870 diagnosis: a 300-request burst → 300 × 200 rules out per-worker counters; the key is the suspect;
  `TRUSTED_PROXY_IPS` has never been confirmed on Render. The probe (#317) is what proves it.
- Fixed and in PRs: 867, 871, 859, 869 (label half), 872 (new), 873 (new). Accounting-expert agent reviewed 867
  independently; two of its findings were taken.
- Found: exported SOCEs dropped every equity account (since Sprint 638); the API stripped `coverage_analysis` and
  `cross_reference_note`; the TB dedup key broke every recalculation; the E2E smoke check has never run a test.
- CEO decisions written up with recommendations: JE unusual-combinations minimum (300); E2E smoke check (CI, freeze);
  "Fraud Indicators" tier label left as is; scheduled-workflow alarm needs an external heartbeat (an Actions
  workflow cannot report Actions being disabled) — e.g. a Sentry cron monitor, which needs a DSN secret.
- Audits (two independent read-only agents, every finding verified against the code before acting): auth/session/CSRF
  → Sprints 874 (P0) and 875; tenant isolation → no cross-tenant IDOR, Sprint 876 + notes. Remaining auth Lows and the
  "completed engagements stay writable" decision are listed under Sprints 875/876 in `tasks/todo.md`.
- **Sprint 874 changes the plan:** the sign-outs blamed on the third-party cookie (868) are mostly a CSRF bootstrap
  defect; merge 874 first, then re-scope 868.
- Lessons: 7 new entries in `tasks/lessons.md` → Recent lessons.

## Verification

**Backend tests:** on each 2026-11-16 branch the full suite passes locally (per-branch counts are in each PR) except
`test_sprint819_route_snapshots::test_engagement_export_routes_unchanged` (`content_encoding` gzip vs null), which is
local-only and passes in CI. **Frontend tests:** full Jest suite and `npm run build` pass on each branch.
On Windows, `--basetemp` must point inside an existing directory.

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
