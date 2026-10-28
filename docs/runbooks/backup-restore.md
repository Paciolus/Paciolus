# Backup and Restore Runbook

**Sprint:** 778b (off-provider backup, restore drill, DR workflows on Neon + R2)

Production Postgres runs on **Neon** (us-east-1). Two independent recovery
mechanisms stand behind it:

| Mechanism | What it is | Where | Recovers from |
|---|---|---|---|
| **Neon PITR** | Neon's history retention: any branch can be restored to any moment inside the window | Neon (same provider) | Bad migration, accidental delete, data corruption — fast, to the second |
| **R2 `pg_dump`** | Daily logical dump, with a manifest, in Cloudflare R2 `paciolus-backups` | Cloudflare (different provider) | Loss of the Neon project or account, or anything older than the PITR window |

An untested backup is not a backup, so both are checked automatically and the
R2 dump is restored into a throwaway database every month.

---

## 1. What runs when

| Workflow | Schedule | Does | Secrets |
|---|---|---|---|
| `backup-pg-dump.yml` | Daily 07:15 UTC + manual | `pg_dump` → R2, writes manifest, verifies upload size, applies retention (30 daily + 12 monthly by default; inputs on manual run) | `NEON_BACKUP_DATABASE_URL` + the four `R2_BACKUPS_*` |
| `backup-integrity-check.yml` | Mondays 06:00 UTC + manual | Newest R2 dump is complete, < 26 h old, sha256 matches its manifest; Neon's **live** PITR window ≥ floor; production branch `ready`. Opens/updates a `dr-failure` issue on non-PASS | four `R2_BACKUPS_*` + `NEON_API_KEY`, `NEON_PROJECT_ID` |
| `dr-test-monthly.yml` | 1st of month 06:00 UTC + manual | The integrity checks **and** the restore drill; combined verdict; report artifact (365 days); `dr-failure` issue on non-PASS | all of the above except `NEON_BACKUP_DATABASE_URL` |
| `backup-restore-drill.yml` | Called monthly by `dr-test-monthly.yml` + manual | Downloads a dump, checks sha256, restores into a Postgres container of the same major version, compares table list, exact row counts, schema fingerprint and alembic revision with the manifest | four `R2_BACKUPS_*` |

Code: `scripts/pg_backup.py` (backup, retention, locate, drill) and
`scripts/verify_backup_integrity.py` (integrity checks). Tests:
`backend/tests/test_backup_scripts.py`.

**Object layout in `paciolus-backups`:**

```
pg_dump/YYYY/MM/paciolus-YYYYMMDDTHHMMSSZ.dump            # pg_dump --format=custom (compressed)
pg_dump/YYYY/MM/paciolus-YYYYMMDDTHHMMSSZ.manifest.json   # written LAST
```

A backup exists only once its manifest exists. The manifest records the dump's
size and sha256, the server version, the alembic revision, a schema
fingerprint (sha256 over public-schema columns and index definitions) and the
exact row count of every public table. Counts and fingerprint are taken in the
**same snapshot** `pg_dump --snapshot` dumps, so they describe exactly the
bytes in the dump even while the app is writing.

**Retention** keeps the newest backup of each of the last *N* days *that have a
backup* (not calendar days — if the cron stops for six weeks, the last copies
are not aged out) and the newest of each of the last *M* months; the newest
backup is always kept. A dump with no manifest older than 24 h is an
interrupted upload and is deleted; a manifest with no dump is kept so the
integrity check flags it. Override with `BACKUP_KEEP_DAILY` /
`BACKUP_KEEP_MONTHLY` or the manual-run inputs; `dry_run_retention` lists what
would go without deleting.

### Verdicts

Every script and workflow uses the same three outcomes, and the job status
**is** the verdict (Sprint 778a's rule — a verdict that cannot fail the job is
a comment, not a check):

| Verdict | Exit code | Job | Meaning |
|---|---|---|---|
| PASS | 0 | green | Checked, and good |
| FAIL | 1 | red | Checked, and bad — or a check crashed |
| UNVERIFIED | 2 | **red** | Could not be checked. The log, step summary and issue title say `UNVERIFIED — missing secret X, Y` |

UNVERIFIED is red on purpose: nothing is known to be broken, and nothing has
been verified either. FAIL outranks UNVERIFIED; a skipped or silent job counts
as UNVERIFIED (or FAIL if it was supposed to run), never as PASS. Until the
secrets below exist, **all four workflows are red** and the weekly check keeps
one `dr-failure` issue open naming the missing secrets.

---

## 2. Secrets the CEO must add

GitHub → repo → **Settings → Secrets and variables → Actions → New repository secret**.
Names are exact.

| Secret | Value | Where to get it |
|---|---|---|
| `NEON_BACKUP_DATABASE_URL` | Neon **direct** connection string, e.g. `postgresql://<role>:<pw>@ep-xxxx.us-east-1.aws.neon.tech/neondb?sslmode=require` | Neon Console → project → **Connect** → turn **Connection pooling OFF** → copy. The host must **not** contain `-pooler`: the pooled endpoint is PgBouncer in transaction mode, which cannot hold the snapshot `pg_dump` uses, and the job refuses it. Recommended: a dedicated role (`CREATE ROLE backup_ro LOGIN PASSWORD '…'; GRANT pg_read_all_data TO backup_ro;`) — if Neon refuses the grant, use the owner role. |
| `R2_BACKUPS_ENDPOINT` | `https://8fd7f43a3458f2ec09d400e0b7a7a5e8.r2.cloudflarestorage.com` | Already set on Render `paciolus-api` → Environment (same name). |
| `R2_BACKUPS_BUCKET` | `paciolus-backups` | Same. |
| `R2_BACKUPS_ACCESS_KEY_ID` | R2 token access key ID, scoped to `paciolus-backups` (Object Read & Write) | Render `paciolus-api` → Environment, or mint a new one: Cloudflare → R2 → **Manage R2 API Tokens**. Read & Write is required — the backup job uploads and deletes. |
| `R2_BACKUPS_SECRET_ACCESS_KEY` | Matching secret | Same place. Cloudflare shows it once at creation. |
| `NEON_API_KEY` | Neon API key | Neon Console → **Account settings → API keys** (or the organization's API keys, project-scoped if offered) → Create. Used read-only: project and branch metadata. |
| `NEON_PROJECT_ID` | e.g. `cool-name-12345678` | Neon Console → project → **Settings → General → Project ID**. |

Optional repository **variables** are not used; the defaults (26 h freshness,
1-day PITR floor, 30/12 retention) live in the scripts and can be overridden
with env vars `BACKUP_MAX_AGE_HOURS`, `PITR_MIN_DAYS`, `BACKUP_KEEP_DAILY`,
`BACKUP_KEEP_MONTHLY`.

**After adding them:** run, in order, Actions → *Backup — pg_dump to R2 (Daily)*
→ Run workflow; then *DR Test (Monthly)* → Run workflow. The first is green when
a dump and manifest land in R2; the second is green when integrity and the
restore drill both PASS. Record both run URLs in Sprint 778's
`**Verification:**` line in `tasks/todo.md`.

**Keep the scheduled workflows alive.** GitHub disables scheduled workflows
after 60 days without repository activity — that is how the old checks sat
disabled until 2026-10-19. If the repo goes quiet, the weekly integrity check
cannot warn you either. Re-enable from the Actions tab if a workflow shows
"disabled".

---

## 3. Verifying Neon's real PITR window

Do not trust a figure in the docs (`DEPLOYMENT_ARCHITECTURE.md` once said
"7 days free / 30 days paid"); the window is a per-project setting and changes
with the plan. Read it live:

```bash
NEON_API_KEY=… NEON_PROJECT_ID=… \
  python scripts/verify_backup_integrity.py --only neon_pitr_window
```

or directly:

```bash
curl -s -H "Authorization: Bearer $NEON_API_KEY" \
  "https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID" \
  | python -c "import sys,json; p=json.load(sys.stdin)['project']; print(p['history_retention_seconds']/86400, 'days')"
```

The weekly and monthly runs do this automatically and FAIL if the window drops
below `PITR_MIN_DAYS` (default 1 day — the minimum that bridges two daily
dumps). Raise the floor if the plan's window is longer and you want a downgrade
noticed.

### PITR restore drill (manual, once per sprint 778 scope item 3)

Neon restores by creating a branch at a past timestamp — production is not
touched:

1. Neon Console → **Branches → Create branch** → parent `main` (production) →
   **Past data: timestamp** → pick a time inside the window (e.g. 24 h ago) →
   compute **read-only** → Create.
2. Copy that branch's direct connection string and record the evidence:
   `SELECT version_num FROM alembic_version;` and
   `SELECT count(*) FROM users;` (plus any tables you care about), and compare
   with the R2 manifest nearest that timestamp.
3. **Delete the branch.** Branches retain history and cost storage.

---

## 4. Running the restore drill by hand

Actions → **Backup — Restore Drill** → Run workflow. Leave `stem` blank for the
newest backup, or give one (e.g. `pg_dump/2026/10/paciolus-20261028T071500Z`)
to test an older copy. Evidence: the `restore-drill-<run id>` artifact and the
run summary.

Locally (needs Docker and the four `R2_BACKUPS_*` env vars):

```bash
pip install -r scripts/requirements-backup.txt
docker run -d --name drill -e POSTGRES_PASSWORD=drill -e POSTGRES_DB=drill -p 55432:5432 postgres:17
python scripts/pg_backup.py locate                     # prints newest stem + Postgres major
python scripts/pg_backup.py drill --stem <stem> --container drill \
  --target-url postgresql://postgres:drill@localhost:55432/drill \
  --alembic-ini backend/alembic.ini
docker rm -f drill
```

Use the Postgres major `locate` prints for the image tag.

If `pg_restore` fails on something Neon-specific (an extension or role that
does not exist outside Neon), the drill FAILs with the error. That is a real
finding about restorability off Neon — fix the cause, do not loosen the drill.

---

## 5. Emergency: restoring production

Pick the mechanism by what was lost.

### A. Data damaged, Neon healthy → Neon PITR (minutes)

1. Find the last good moment (Sentry, logs, the deploy timeline).
2. Neon Console → branch `main` → **Restore** → *to a point in time* → that
   timestamp. Neon keeps the pre-restore state as a backup branch, so this is
   reversible. (Alternative: create a branch at that time, verify it, then
   point `DATABASE_URL` on Render at it.)
3. Render `paciolus-api` → Manual Deploy → restart so pools reconnect.
4. Smoke test: `curl https://paciolus-api.onrender.com/health/ready` (check the
   **body** says `healthy`), log in, open an engagement.

### B. Neon project/account lost, or the damage is older than the PITR window → R2 dump

1. Create a new Neon project (us-east-1) or any Postgres of the **same major
   version** as the dump's manifest (`server_version`).
2. Download the newest good backup and check it:
   ```bash
   aws s3 cp s3://paciolus-backups/<stem>.dump . --endpoint-url "$R2_BACKUPS_ENDPOINT"
   aws s3 cp s3://paciolus-backups/<stem>.manifest.json . --endpoint-url "$R2_BACKUPS_ENDPOINT"
   sha256sum <file>.dump      # must equal manifest.dump_sha256
   ```
   (`python scripts/pg_backup.py locate` finds the newest stem.)
3. Restore into the **empty** database, using the **direct** (non-pooler) host:
   ```bash
   pg_restore --dbname "$NEW_DIRECT_URL" --no-owner --no-privileges --exit-on-error <file>.dump
   ```
4. Check parity: `SELECT version_num FROM alembic_version;` must equal
   `manifest.alembic_version`; spot-check row counts against `manifest.tables`.
   If the repo has migrations newer than that revision, run
   `cd backend && DATABASE_URL=… alembic upgrade head`.
5. Render `paciolus-api` → Environment → set `DATABASE_URL` to the new
   **pooled** URL → deploy. Confirm the live deploy SHA matches `main`
   (`scripts/latest_live_deploy_sha.py`) and smoke test as in A.4.
6. Update `NEON_BACKUP_DATABASE_URL`, `NEON_PROJECT_ID` (and `NEON_API_KEY` if
   the account changed) so backups resume against the new database, then run
   the backup workflow by hand.

Data written between the dump and the outage is lost under B — at most ~24 h
with the daily schedule. Record the incident per
`docs/04-compliance/INCIDENT_RESPONSE_PLAN.md`.
