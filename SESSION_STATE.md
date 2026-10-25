# Session State

_Updated at the end of every Claude Code session. Overwrite the previous state — this is not a history log._

## START HERE — what the next session should pick up

**1. Work Sprints 840 → 845 in `tasks/todo.md`** (the "NEXT SESSION — START HERE" block in Active Phase). They
come from the 2026-10-24 legal-and-security claims review the CEO commissioned and approved. Every finding, with
file:line, a reason and safer wording, is in `reports/claims-review-2026-10-24.md`; the CEO-readable version is
https://claude.ai/artifact/MFTYHezjA4zakoiKwgnNb2.

- **840** security defects first: any paying customer can read company-wide revenue metrics
  (`routes/internal_metrics.py`), Sentry captures local variables (client figures), impersonation isn't truly
  read-only, six CSV exports lack formula escaping, security events are discarded, parser errors log filenames.
- **841** one honest storage statement everywhere (about 30 "never stored" absolutes, including every
  verification and password-reset email, the Terms, Privacy and DPA) + a guard test.
- **842** billing truthfulness (the trial says "no credit card required" but checkout takes a card; "Most Popular";
  two contradictory refund policies; wrong test counts and speed claims).
- **843** professional positioning ("The Workpapers Write Themselves", "audit-ready", standard-setter badges, memo
  "Conclusion"/"immaterial" wording, "Form 1099 Preparation") + the standard disclaimer set.
- **844** privacy promises (account deletion is promised but doesn't exist — build it; DPO; entity name;
  providers/regions; a DPA customers accept at checkout but can't read).
- **845** the public repo's compliance docs (SOC 2 "in progress", pen test, PGP, PagerDuty, SLA, backups, CFAA
  language) rewritten honestly.

**CEO direction:** no "tricky" language; correct wrong facts now, including in the legal pages. Counsel reviews
the Terms, Privacy and DPA **once the website is finalized** — don't block on it. Open CEO decisions and the
defaults to use are listed in the todo start block (refund policy, legal entity and repo visibility are "ask").

**Before the first `Sprint N:` commit:** Active Phase holds 4 COMPLETE sprints; run `sh scripts/archive_sprints.sh`.

**2. Production.** `main` is `5f82d818` (#230) and live on Render (deploy SHA verified; Render workspace
`tea-d6ie7bngi27c738fa2ag`, service `srv-d6ie9l56ubrc73c7eq2g`; pass `workspaceId` to the Render MCP). The new
`GET /audit/w2-reconciliation/supported-years` returns `[2025]` in production. The public `/sources` page is live
on paciolus.com.

**3. Still open from earlier:** Sprint 793b (CEO, a CPA, confirms the 2025/2026 statutory figures — W-2 limits,
2026 1099 $2,000 threshold, sampling formulas); Sprint 839 leftovers (column-mapping UI for bank rec and TWM; the
bank-rec memo doesn't print `active_thresholds`); Sprint 778 (off-provider backups).

## This Session — 2026-10-24, methodology decisions and claims review

- The CEO approved all nine methodology decisions on the most conservative reading and asked that every
  accounting citation be documented. Shipped and live: **#225** (831 risk-score severity floors, holidays,
  client-relative month-end; 834 storage wording; 822 nightly reports untracked), **#227** (825 sampling basic
  precision and two-sided bounds; 832 equity incl. unclosed earnings; 826 W-2 catch-ups; 833 SoD tiering and
  bank-rec split bound + split-match 500 fix; 790 upload metering, with webhook-ordering and annual-plan lock-out
  fixes), **#228** (835 `/sources` methodology catalog of 219 rules; 837 ~40 citation corrections and 1099
  thresholds by tax year), **#229** (836 saved thresholds reach the engines and are disclosed; 838 bank-rec CSV
  splits, W-2 CSV escaping, memo descriptions), **#230** (839 bank-rec materiality, TWM run settings and column
  mappings, W-2 supported years).
- Then a three-part claims review (marketing/legal copy, security vs code, professional positioning) → Sprints
  840–845.

## Verification

**Backend tests:** **9843 passed / 0 failed** — full suite on the Sprint 839 tree before merge, 13.2 min locally.
**Frontend tests:** **2063 passed / 0 failed**, 207 suites, on the same tree; `tsc` clean.

## Environment notes

- The backend suite takes ~13–14 min locally; run it before pushing anything stacked (CI only runs on PRs into
  `main`). Delete a stale local `backend/paciolus.db` if tests report a missing `uploads_window_start` column.
- Worktrees need a copied `backend/.env` and a `frontend/node_modules` junction. **`rmdir` the junction before
  `git worktree remove --force`**, or the main checkout's node_modules is deleted (happened 2026-10-24; `npm ci`
  restored it). Turbopack cannot build through the junction — build from the main checkout.
- Retarget a stacked PR to `main` before merging its base; deleting the base branch closes the stacked PR.
- `generate_sample_reports.py` rewrites `sample-reports/` — run it deliberately, not by accident.
