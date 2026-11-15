# Sprints archived 2026-11-15

Completed or superseded sprints moved verbatim out of `tasks/todo.md`.

### Sprint 866: What each tool takes, does and gives
**Status:** COMPLETE 2026-11-15. **Source:** reports/website-review-2026-11-14.md S-04 (left open by Sprint 864). **Owner:** C.

- [x] `frontend/src/content/tool-io.ts`: one row per tool — what you provide, what Paciolus computes, what you get —
      each established from the code (evidence comment per row; research by a background agent with file:line
      citations, then spot-checked: JE minimum entries `je_testing/analysis.py:105`, revenue contract tests skipped
      without contract columns `revenue_testing/analysis.py:1847`).
- [x] Rendered on `/sources` above "Tool by tool"; `__tests__/ToolIO.test.ts` fails if a tool lacks a row or a stated
      test count drifts from the catalog.
- **Facts surfaced:** six tools (SoD, Intercompany, W-2, 1099, Book-to-Tax, Cash Flow Projector) have no PDF memo
  and no Excel export — CSV only; the table says so. No customer-facing copy claimed otherwise (checked). The backend
  accepts 11 upload formats (adds DOCX) where the site says ten — an understatement, left as is. `CLAUDE.md`'s
  "18 memo PDFs" is an internal count, not customer-facing.

**Commit SHA:** TBD.

### Sprint 865: Product screenshots, sample memo, and the memo wording behind them
**Status:** COMPLETE 2026-11-15. **Source:** reports/website-review-2026-11-14.md S-01, S-07, G-05. **Owner:** C (Chrome, CEO-signed-in production session, synthetic data only).

- [x] Screenshots from the live app on a synthetic, balanced trial balance ("Meridian Capital Group", fixtures in
      `backend/tests/anomaly_framework`): hero (`/screenshots/tb-flagged-accounts.png`), Fig. 1 upload check
      (`tb-upload-columns.png`), Fig. 2 JE memo page (`je-memo-proof-summary.png`). Captions say synthetic data.
- [x] Sample JE Testing memo (`/samples/paciolus-sample-je-testing-memo.pdf`) generated from `main`'s code with the
      default layout (sign-off off), "SAMPLE — synthetic data" stamped on every page; linked from the homepage and
      the Demo page. A sample XLSX was not added: JE Testing exports CSV only (Sprint 866 table), and the TB Excel
      export carries the balance-sheet defect (Sprint 867).
- [x] **Found while capturing — every memo PDF ended with the retired claim** "Zero-Storage Architecture: … not
      persisted to any storage medium. No client financial data is retained by Paciolus" (`shared/memo_base.py`,
      `pdf/sections/diagnostic.py`; the TB and financial-statement PDFs also said "never stored"). The claims guards
      only scanned the website. Replaced with the approved storage sentence + `paciolus.com/data-handling`.
- [x] Also removed from customer documents: "Diagnostic Intelligence" (memo/report footers, the TB report title,
      the ZIP disclaimer, email footer, public OpenAPI description); "Paciolus®" (two PDF footers — the ® asserts a
      registration nobody has confirmed); "Tests Clear" → "Tests With No Exceptions Flagged"; "Findings" in memo
      headings, tables and narrative → "Items Flagged" / "Item" / "flags" (the auditor-reserving disclaimers reworded,
      not deleted). `tests/test_memo_banned_phrases.py` now bans all of these in rendered output and source.
- [x] Trial-balance page footer used a partial "what we keep" line; now the shared `UploadHandlingNotice`.
- **Product defects found (filed above):** Sprint 867 balance sheet; Sprint 868 15-minute sessions; Sprint 869 JE
  calibration and the lines-vs-entries count.

**Commit SHA:** TBD.

### Sprint 738: Alembic migration drift cleanup
**Status:** **SUPERSEDED by Sprint 797 (2026-10-22)** — delivered in full, and now actually
verified. The parity test that backs the claim below was itself measuring the wrong thing on
PostgreSQL (see the 2026-10-23 hotfix entry); the schema claim survived the correction — the
chain and the ORM do agree on all three `use_alter` foreign keys. Migration
`c9e4a1b73f20` creates all 4 tables, 6 columns and 3 FKs; both allow-lists in
`test_alembic_models_parity.py` are empty and pinned empty by
`test_drift_allowlists_stay_empty`. A chain-built database now reaches 29 of 29 tables
with zero column and zero foreign-key drift.


**Priority:** P3. Catches up on dormant tech debt surfaced by Sprint 737's drift test.
**Source:** Sprint 737's parity test (`backend/tests/test_alembic_models_parity.py`) discovered 4 tables and 6 columns defined on models with no corresponding Alembic migration.

Write Alembic migrations for the documented drift in `PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS`. As each migration lands, remove the corresponding entry from the allow-list. When both allow-lists are empty, the parity test enforces full Alembic-models equivalence going forward.

**Tables needing CREATE TABLE migrations (4):**
- `password_reset_tokens` — defined in `backend/models.py`
- `processed_webhook_events` — defined in `backend/subscription_model.py`
- `tool_activities` — defined in `backend/models.py`
- `waitlist_signups` — defined in `backend/models.py`

**Columns needing ADD COLUMN migrations (6):**
- `engagements.completed_at` + `engagements.completed_by` — defined in `backend/engagement_model.py`
- `diagnostic_summaries.ccc` + `dio` + `dpo` + `dso` (cash-conversion-cycle ratios) — defined in `backend/models.py`

**Step 1 — production verification gate (FIRST, DO NOT SKIP):** Before writing any migration, query production Postgres via Render MCP `query_render_postgres` (or `psql` against `paciolus-api-db`) to confirm whether each of these 10 schema objects already exists in production. Three possible outcomes per object:
1. **Object exists in production but not in Alembic** → write a migration whose `op.create_table` / `op.add_column` is wrapped in an existence check (or use Alembic's `op.execute` with `IF NOT EXISTS`) so it's idempotent on re-run. The migration's job is to bring Alembic's recorded history into sync with production reality, not to actually mutate production schema.
2. **Object missing in production** → write a normal `op.create_table` / `op.add_column` migration; production gains the column on next deploy.
3. **Object never accessed in production** (model is dead code) → consider removing the model definition instead of writing the migration. Verify via grep + Render request-log analysis.

**Out of scope:**
- No model-side changes (the models are the source of truth; Alembic catches up to them).
- No removal of `Base.metadata.create_all()` from `init_db()` — it currently creates the 4 orphan tables on fresh DBs, and removing it before the migrations exist would break local dev / CI fixtures.

**Verification:**
- After Sprint 738 lands, `PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS` are both empty in `test_alembic_models_parity.py`.
- Test still passes (full parity now enforced).
- Production deploy logs after the migrations run show the relevant `op.create_table` / `op.add_column` log lines (or `already exists, skipping` for outcome (1) cases).

---

### Sprint 760: Dependency hygiene — patches + safe minors (2026-04-29 nightly)
**Status:** SUPERSEDED 2026-10-20 by **Sprint 786**. The 19-package list is six months stale — today's nightly reports 68 backend / 22 frontend outdated, so this batch no longer describes the work. Kept for the per-package rationale and the verification pattern.
**Priority:** P3. Routine maintenance batch; no security urgency at the patch/minor level.
**Source:** `reports/nightly/2026-04-29.md` Dependency Sentinel section.

Bundle the 19 patch + safe-minor updates into one commit, mirroring the 2026-04-19/2026-04-22 hygiene-batch pattern.

**Backend (15):**
- Patches: `click` 8.3.2→8.3.3, `fastapi` 0.136.0→0.136.1 (security-relevant, but patch-level), `hypothesis` 6.152.1→6.152.4, `Mako` 1.3.11→1.3.12, `python-multipart` 0.0.26→0.0.27, `ruff` 0.15.11→0.15.12.
- Minors: `anthropic` 0.96.0→0.97.0, `certifi` 2026.2.25→2026.4.22, `greenlet` 3.4.0→3.5.0, `packaging` 26.1→26.2, `pathspec` 1.0.4→1.1.1, `pip` 26.0.1→26.1, `stripe` 15.0.1→15.1.0 (security-relevant), `tzdata` 2026.1→2026.2, `uvicorn` 0.45.0→0.46.0.

**Frontend (4):** `@sentry/nextjs` 10.49.0→10.50.0, `@typescript-eslint/eslint-plugin` 8.59.0→8.59.1, `@typescript-eslint/parser` 8.59.0→8.59.1, `postcss` 8.5.10→8.5.12.

**Excluded from this sprint:**
- `cryptography` 46.0.7→47.0.0 (MAJOR — own sprint, see 761).
- `pdfminer.six` 20251230→20260107 (deferred, calendar version, review by 2026-04-30).

**Verification:**
- `pip install -r backend/requirements.txt && cd backend && pytest -q` clean.
- `cd frontend && npm install && npm run build && npm test` clean.
- Stripe SDK upgrade: confirm no breaking change in 15.1.0 vs 15.0.1 (CHANGELOG sweep + smoke-test billing webhook fixture).
- FastAPI patch: confirm no behavior change in `Depends`/middleware semantics (regression-suite covers this implicitly).
- Render deploy logs after merge: zero new ImportErrors, /health 200 within 60s.

**Out of scope:**
- Major upgrades (cryptography 47).
- Frontend `next` / `react` major sweeps (no action needed in this nightly).

---

### Sprint 761: cryptography 47.0.0 major upgrade (security-relevant)
**Status:** SUPERSEDED 2026-10-20 by **Sprint 786**. The target version is wrong by two majors — `cryptography` is at 50.0.2, not 47.0.0 — and Sprint 777 rejected this sprint's premise outright: `cryptography` stays a `>=` floor, so a fresh resolve already takes the current release. The isolated-major verification pattern below is still the policy and carries into 786.
**Priority:** P2 (security-relevant; pyca/cryptography ships CVE fixes via majors and the lib underpins JWT signing, password hashing, TLS evidence chain).
**Source:** `reports/nightly/2026-04-29.md` Dependency Sentinel — flagged as security-relevant + major.

**Pre-flight:**
1. Pull pyca/cryptography 47.0.0 release notes; flag any signature on `cryptography.hazmat.primitives.*` we depend on (JWT library, audit_chain TLS evidence, password reset token signing).
2. Audit direct imports: `Grep -r "from cryptography" backend/`. Cross-reference each call site against the 47.0.0 deprecation/removal list.
3. Identify transitive consumers (PyJWT, pyOpenSSL, requests-toolbelt, etc.) and confirm each is compatible with cryptography 47.x — pin floor in `requirements.txt` if any consumer requires <47.

**What lands:**
- `backend/requirements.txt` — `cryptography==47.0.0` (pin exact, not floor; Paciolus convention).
- Any compatibility shims for hazmat primitives that changed signature (unlikely for a properly-maintained version-bump, but possible).
- New regression test if a hazmat surface we depend on changed shape.

**Verification:**
- Backend `pytest` clean (especially: `tests/test_auth*.py`, `tests/test_password_reset*.py`, `tests/test_audit_chain*.py`, `tests/test_csrf*.py`, `tests/test_security_hardening*.py`).
- Manual: register → verify-email → login → logout → refresh-token → password-reset round-trip on a local instance.
- Render preview deploy: 24h soak before promoting to prod (per Paciolus prod-cutover policy for security-critical deps — same caution we used for the FastAPI 0.135.x bump in Sprint 263 era).

**Out of scope:**
- Bundling with the patch/minor batch (Sprint 760). Majors get their own sprint so a regression doesn't taint a 19-package roll-back.
- Migrating to `joserfc` or another JWT library — out of scope; we're upgrading the underlying primitive, not the wrapper.

---

### Sprint 778: Build the off-provider backup, then prove recovery works

> **Closed 2026-11-14 (recorded from PR #312, verified 2026-11-15 against the green DR Test run 43655582429).**
> All 8 repo secrets set; read-only role `backup_ro` used for the dump; R2 token `github-actions-backups` scoped to
> `paciolus-backups`, 1-year TTL (rotate each Nov 1). First *Backup — pg_dump to R2* PASS (run 43655183209: server
> 15.19, 31 tables). First DR Test failed only `neon_pitr_window` (6 h vs the 1-day floor); Neon history raised
> 6 h → 7 d; re-run fully PASS: R2 backup sha256-verified, PITR window 7.0 days, restore drill tables / row counts /
> schema fingerprint / alembic `b9d3f6a2c418` all match. Issues #293, #294, #310 closed.
> **Not done:** a restore *from Neon PITR* (the window is checked, not drilled) — carried to the todo.md "Then" list.
**Status:** SPLIT — **778a COMPLETE** (the DR workflow now reports its own verdict). **778b code COMPLETE (PR #292; test DSNs are assembled at runtime so the CI secret scan stays clean)
2026-10-28; verification PENDING CEO secrets:** `NEON_BACKUP_DATABASE_URL`, `R2_BACKUPS_ENDPOINT`,
`R2_BACKUPS_BUCKET`, `R2_BACKUPS_ACCESS_KEY_ID`, `R2_BACKUPS_SECRET_ACCESS_KEY`, `NEON_API_KEY`,
`NEON_PROJECT_ID` (where each comes from: `docs/runbooks/backup-restore.md` §2).
**2026-10-28 plan:** 778b **gates the first live Stripe checkout** (council Q3, 5–3).
**Priority:** P1 — both halves in scope: build the backup that does not exist **and** verify that recovery works.


**Source:** 2026-10-19, while re-enabling the inactivity-disabled scheduled workflows (Sprint 775 work).

Re-enabling the three auto-disabled workflows surfaced that two of them cannot pass as written:

- **No repo secrets exist at all.** `gh secret list` returns empty, so `RENDER_API_KEY` and `RENDER_POSTGRES_ID` are unset. `scripts/verify_backup_integrity.py` exits 2 on `RENDER_API_KEY is not set`, which is why `backup-integrity-check` failed every month before being disabled.
- **They point at the wrong provider.** Both `verify_backup_integrity.py` and `dr-test-monthly.yml` query `api.render.com/v1/postgres/$RENDER_POSTGRES_ID`. Production Postgres is on **Neon** (since Phase 1, 2026-04-09) and the orphan Render Postgres was deleted 2026-04-22, so even with secrets these checks interrogate a database that does not exist.
- **`DR Test (Monthly)` is a false-green.** Its last scheduled run (2026-09-01) reported workflow-level **success**, yet its internal `render-check` step resolves `api_error` → `result=FAIL`; the overall verdict only gates issue creation, not the job's exit status. Same class of defect as the 2026-04-22 false-green incident that motivated Sprint 712.
- **Phase 4.4 was never implemented**, so the `paciolus-backups` R2 bucket holds no `pg_dump` artifacts. Neon's own PITR is the only thing standing behind production data; there is no off-provider copy and no restore-drill evidence.

**Scope** (the decision above is settled — do not reopen it):
1. **Implement the `pg_dump` → R2 cron** into the already-provisioned `paciolus-backups` bucket. Options costed in `ceo-actions.md` §4.4: Render Cron Job (~$1/mo), GitHub Action (free), Upstash Scheduled Function.
2. **Verify Neon PITR too** — confirm the actual retention window on the current plan rather than trusting the 7-day/30-day figure in `DEPLOYMENT_ARCHITECTURE.md:724`.
3. **Perform one real restore drill against each mechanism** and record the evidence. Verify schema parity and row counts against production. An untested backup is not a backup — this is the half of the risk a second mechanism does not address.
4. **Rewrite both DR workflows against Neon + R2** instead of the Render Postgres API, which queries a database deleted on 2026-04-22.
5. **Fix the false-green** so a job's exit status reflects its own verdict, and make the missing-credential case report "unverified" explicitly rather than dying on an opaque error.

**Note:** all three workflows were re-enabled on 2026-10-19. `dependency-compliance` now passes (its CVEs were fixed the same day), but **`backup-integrity-check` will fail on the 1st of each month and file a `dr-failure` issue** until this sprint lands. That signal is substantively true — backups genuinely are unverified — but its stated reason will be the misleading "RENDER_API_KEY is not set". Either accept it as a forcing function or disable that one workflow until the rewrite.

#### 778a — the DR workflow was reporting success while its own report said FAIL: COMPLETE

Scope item 5, which needed no credentials. **Five defects in one workflow**, all verified before
changing anything, and the last two were not in the original filing.

1. **The false-green itself.** `steps.final.outputs.overall` gated only the "Create failure issue"
   step. Nothing made the *job* fail, so it exited 0 whatever its report said. Three consecutive
   scheduled runs — **2026-07-01, 08-01 and 09-01** — reported workflow success while the Render
   check resolved to FAIL. A verdict that cannot fail the job is a comment, not a check.
2. **The verdict read three signals and branched on one.** `BACKUP_RESULT` and `PROBE_RESULT` were
   assigned and never used; only `RENDER_RESULT` decided the outcome. A failed backup check or a
   dead database could not affect the verdict. Demonstrated: `render=PASS, backup=false,
   probe=false` → old verdict **PASS, exit 0**; new verdict **FAIL, exit 1**.
3. **No UNVERIFIED state.** A missing credential produced `api_error` → `FAIL` → the report line
   *"Instance status: api_error (expected: available)"*, which reads as a database outage. Three
   outcomes now: PASS, FAIL, UNVERIFIED.
4. **The liveness probe had never executed — not once.** Its guard was
   `if: env.DATABASE_URL_READONLY != ''`, but that variable is defined only in the *step's own*
   `env:` block. A step-level `if` is evaluated against the job and workflow env contexts, where
   it does not exist, so the condition was permanently false. Nobody noticed because the verdict
   ignored the probe's output anyway — defect 2 concealed defect 4. The empty case is now handled
   inside the script, which also lets it report UNVERIFIED.
5. **The failure text blamed the wrong thing.** The check targets the **Render** Postgres API;
   production moved to **Neon** in Phase 1 and the orphan Render instance was deleted
   2026-04-22. The report now says so explicitly, so `api_error` is not mistaken for an outage.

**An unverified DR posture is not a passing one.** The job now exits non-zero for FAIL *and* for
UNVERIFIED, and files an issue for both with the verdict in the title. That makes the monthly run
go red until 778b lands — which is correct and is the forcing function the 2026-10-19 note
anticipated. Nothing is known to be broken; nothing has been verified either, and the report says
exactly that.

**Also corrected: `scripts/verify_backup_integrity.py`'s error message.** It exited with
*"ERROR: RENDER_API_KEY is not set"* — which reads as a missing secret a maintainer could fix in
a minute. Setting it would not help: the script queries a deleted Render database. The message now
names the real cause and the real finding (no off-provider backup exists at all), and the exit code
is unchanged at 2.

**Checked and found sound:** `backup-integrity-check.yml` does *not* share the false-green. It uses
`continue-on-error: true` on the check step plus a Summary step that exits 1 — so its job status
has always been honest. Only `dr-test-monthly.yml` was lying. Worth recording so 778b does not
re-audit it.

**Verification:** the verdict logic was extracted and exercised against **12 cases** — all-green,
each signal failing independently, FAIL dominating an earlier UNVERIFIED, skipped steps counting as
UNVERIFIED rather than PASS, and the specific regression where a passing Render check used to mask
two failures. All 12 behave as intended. YAML parses and the job's 9 steps resolve in order.
`verify_backup_integrity.py` compiles and still exits 2. Its 4 ruff findings are pre-existing
import-ordering (identical count before the change) and outside CI's lint scope, which runs from
`backend/`.

**Two more found by the PR #187 review, and the causal chain is the interesting part.**

6. **Fixing defect 4 activated a dormant defect 6.** With the probe finally running, its result
   rendering turned out to be wrong: `> probe_result.json` creates the file *before* python
   starts, so a failed probe leaves an empty file, and the old `if [ -f probe_result.json ]`
   check then wrote *"✅ Database responded to probe"* into the same report that carried
   `probe=FAIL`. The contradiction had been unreachable for as long as the step never executed.
   Now one branch decides both the output and the report line, keyed on the exit status **and** a
   non-empty result, so they cannot disagree. Exercised against all three outcomes: python
   succeeded, python died leaving an empty file, redirection itself failed — the middle one is
   the case the old check got backwards.

7. **Making the job fail silently disabled the restore drill — a regression I introduced.**
   `restore-validation` declares `needs: dr-test` with `if: github.event_name ==
   'workflow_dispatch'`. A `needs:` dependency implies the prerequisite *succeeded* unless the
   condition uses a status function, so the moment `dr-test` began failing on a non-PASS verdict,
   the manual restore drill stopped running — in exactly the UNVERIFIED state the workflow is
   expected to hold until 778b. That is the worst possible timing: **an untested backup is not a
   backup**, and scope item 3 calls the drill the half of the risk a second mechanism cannot
   address. Fixed with `always() && github.event_name == 'workflow_dispatch'`. The drill never
   depended on the verdict anyway — it provisions its own isolated instance and runs its own
   `pg_restore` — so the gate was accidental rather than intended.

**Still blocked, and unchanged:** scope items 1–4 — building the `pg_dump` → R2 cron, confirming
Neon's real PITR retention, the restore drills, and rewriting both workflows against Neon. All need
the Neon connection string (**CEO ask D-1**) and R2 token confirmation.

#### 778b — the backup, the drill, and both DR workflows on Neon + R2: code COMPLETE, verification PENDING

- [x] **Scope 1 — `pg_dump` → R2 cron** (GitHub Actions, the free §4.4 option): `backup-pg-dump.yml`
  daily 07:15 UTC → `scripts/pg_backup.py backup`. Client is the official `postgres:<major>` image,
  the major read from the server at run time (`SHOW server_version_num`), so the client never lags
  Neon. Refuses Neon `-pooler` hosts. Row counts and schema fingerprint are taken **in the snapshot
  `pg_dump --snapshot` dumps**, so the manifest (per-table counts, schema sha256, alembic revision,
  size, sha256) describes exactly the dumped bytes. Manifest written last = commit marker. Retention
  30 daily + 12 monthly (parameters/inputs), counted in backup-days so a stalled cron never ages
  out its last copies; the run's own backup can never be selected for deletion.
- [x] **Scope 2 — Neon PITR window read live** from the Neon API (`history_retention_seconds`);
  `verify_backup_integrity.py --only neon_pitr_window`, floor `PITR_MIN_DAYS` (default 1 day).
  `DEPLOYMENT_ARCHITECTURE.md` §10.1's 7/30-day figure is marked superseded, not trusted.
- [ ] **Scope 3 — one real restore drill per mechanism, with evidence.** Built, not yet run: the R2
  drill (`backup-restore-drill.yml`, monthly via DR Test + manual) restores into a same-major
  service container and compares table list, exact row counts, schema fingerprint and alembic
  revision (also checked against the repo's migration history). The Neon PITR drill is a manual
  runbook step (§3) — automation does not create branches on production. Both need the secrets.
- [x] **Scope 4 — both DR workflows rewritten against Neon + R2.** `dr-test-monthly.yml` = integrity
  + restore drill + combined verdict; `backup-integrity-check.yml` now **weekly** (a monthly check
  lets a month of missing dumps pass) with one deduplicated `dr-failure` issue per title.
  `verify_backup_integrity.py` checks R2 freshness + sha256, Neon PITR window, Neon branch state.
  No `api.render.com` reference remains; the 4 Render-era secrets are retired.
- [x] **Scope 5 — kept from 778a.** Exit 0 PASS / 1 FAIL / **2 UNVERIFIED**; every workflow's job
  status is its verdict, UNVERIFIED is red and names the missing secrets ("UNVERIFIED — missing
  secret X, Y"), a skipped or silent job is never PASS, verdict jobs run under `always()`.
- Runbook: `docs/runbooks/backup-restore.md` (schedule, secrets + where to get each value, drill by
  hand, emergency restore via PITR or R2).

**Found on the way, not fixed (out of scope):** `boto3` is in **no** requirements file, so
`shared/export_share_storage.py` hits its `ImportError` fallback in production — `GET /health/r2`
returns `{"r2":"not_configured"}` live on 2026-10-28. Sprint 611's R2 export-share storage has
therefore never been active; share bytes are still in the Neon row. Needs its own sprint (add
`boto3` to `backend/requirements.txt`, then confirm `/health/r2` says `reachable`).

**Verification:** 78 new tests in `backend/tests/test_backup_scripts.py` pass (retention selection,
manifest + schema fingerprint, restore comparison, drill sha256/pg_restore failure paths, R2 and Neon
checks with fakes, UNVERIFIED naming + exit 2, the DR combine step run under bash for 6 verdict
combinations, workflow parse/pins/secret-set/no `set -x`); actionlint clean on all four workflows;
ruff clean. **Not yet run against production** — PENDING the 7 CEO secrets, then a manual run of
*Backup — pg_dump to R2* followed by *DR Test (Monthly)*; record both run URLs here.

**Commit SHA:** `f0d7d6ec` (778a; PR #187). 778b: see commit `Sprint 778: off-provider backup, restore drill and DR workflows on Neon + R2`.

---

