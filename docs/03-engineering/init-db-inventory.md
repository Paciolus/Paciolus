# `init_db()` Schema-Patch Inventory

> **Sprint 736 deliverable.** Read-only inventory of `backend/database.py::init_db()` branches, classified as idempotent-init, schema-patch, or migration-disguised-as-init. No code changes in this sprint; the recommendation is the deliverable.

## Source under review

`backend/database.py::init_db()` — lines 108–359 (file is 360 lines total; `init_db()` accounts for ~70%).

## Classification

| # | Lines | Branch | Classification | Notes |
|---|-------|--------|----------------|-------|
| 1 | 130–142 | Model imports + `Base.metadata.create_all(bind=engine)` | **idempotent-init** | Imports every model module so cross-FK metadata is complete, then creates any missing tables. `create_all()` is a no-op on existing tables. |
| 2 | 150–163 | SQLite: `users.organization_id` patch | **migration-disguised-as-init** | `ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id)` + index. Mirrors the organizations work in Phase LXVII–LXVIII. |
| 3 | 165–175 | SQLite: `users.is_superadmin` patch | **migration-disguised-as-init** | `ALTER TABLE users ADD COLUMN is_superadmin BOOLEAN NOT NULL DEFAULT 0`. Comment cites Sprint 590 as the migration source. |
| 4 | 177–196 | SQLite: `refresh_tokens` session-metadata patch (`last_used_at`, `user_agent`, `ip_address`) | **migration-disguised-as-init** | 3× `ALTER TABLE refresh_tokens ADD COLUMN`. Comment **explicitly cites Alembic revision `b6c7d8e9f0a1`** as the source migration. |
| 5 | 198–215 | Postgres: `users.organization_id` patch | **migration-disguised-as-init** | Same intent as #2, Postgres dialect; production-facing. |
| 6 | 217–231 | Postgres: `users.is_superadmin` patch | **migration-disguised-as-init** | Same intent as #3, Postgres dialect; production-facing. |
| 7 | 233–257 | Postgres: `refresh_tokens` session-metadata patch | **migration-disguised-as-init** | Same intent as #4, Postgres dialect; production-facing. Hardcoded `(col_name, col_type)` allowlist with a `# safe for DDL` comment — explicit guard against DDL injection from interpolation. |
| 8 | 261–278 | Postgres: `usertier` enum `ENTERPRISE` value patch | **migration-disguised-as-init** | `ALTER TYPE usertier ADD VALUE 'ENTERPRISE'`, requires `raw_connection().autocommit = True` because `ALTER TYPE … ADD VALUE` cannot run in a transaction block. Comment cites Phase LXIX. |
| 9 | 280–352 | TLS verification + version logging (Postgres) / WAL+FK info log (SQLite) | **idempotent-init** | Legitimate startup health-check. Includes fail-closed `RuntimeError` when `DB_TLS_REQUIRED` is set and TLS cannot be verified. The `_is_pooled_hostname` skip path (Sprint 673) is a documented pooler-TLS-blindspot accommodation, not a schema concern. |
| 10 | 356–359 | `log_secure_operation("database_init_complete", …)` | **idempotent-init** | Completion marker. |

## Summary

| Classification | Count |
|---|---|
| `idempotent-init` | 3 (model imports/`create_all`, TLS check, completion log) |
| `schema-patch` (no Alembic revision cited) | 0 |
| `migration-disguised-as-init` (cites or mirrors a specific Alembic revision / Sprint / Phase) | **7** |

**Every schema-altering branch in `init_db()` is migration-disguised-as-init.** All 7 reference a specific migration source (Alembic revision ID, Sprint number, or Phase number) and exist because Alembic does not run on startup.

## Why this pattern exists

Comment block at `backend/database.py:148–149`:

> `create_all()` creates new tables but does NOT add columns to existing tables. Patch missing columns that were added by migrations after the table was first created.

The dual-path was originally added (per `tasks/archive/phases-xix-xxiii-details.md:172`) when running Alembic at startup was deferred for "adds latency, needs multi-worker race testing" reasons. **Sprint 544c reversed that deferral** (`tasks/archive/sprints-542-546-details.md:31`) by wiring `alembic upgrade head` into the Dockerfile `CMD` before gunicorn starts. The in-process patcher was not removed at that time — it stayed as belt-and-suspenders.

**Verified production behavior** (`backend/Dockerfile` CMD):

```sh
python -c "<check if alembic_version table exists>"
  if exists: alembic upgrade head
  if not:    alembic stamp head
then:        gunicorn main:app ...
```

By the time `init_db()` runs in production, schema is already at head. The patches in `init_db()` are dead code in the production path.

**Test path** (`backend/tests/conftest.py`): uses `Base.metadata.create_all()` directly against current models. Produces current schema. The patches are dead code in CI too.

The only path that exercises the patches is a developer with a stale local SQLite file booting the app without first running `alembic upgrade head` and without going through the Dockerfile.

## Cost / risk profile

> **Reframe:** the patches are dead code in production and tests today. The cost framing below is therefore primarily about *maintenance* and *cognitive overhead*, not runtime risk to the live system.

### Costs (real, present)

- **Hidden contract.** The original framing assumed every new Alembic migration needs a parallel patch block here. With Sprint 544c's Dockerfile wiring, that contract is no longer load-bearing — but a future contributor reading the patcher would reasonably believe it *is* load-bearing and add a parallel patch on every migration. That's onboarding cost on a dead-code path.
- **Footprint.** Each patch is 15–25 lines of dialect-aware boilerplate. The patch block is ~130 lines (lines 148–278), ~36% of `database.py`. All of it dead-code maintenance.
- **Two-dialect maintenance.** SQLite blocks need to track every Postgres change to keep them parallel. All maintenance for a path that doesn't fire.
- **Footgun in the enum patch.** Patch #8 requires `raw_connection().autocommit = True` because `ALTER TYPE … ADD VALUE` cannot run in a transaction. A copy-paste of this pattern for a regular `ALTER TABLE` would silently change transaction semantics. Removing the block removes the bait.

### Runtime risks (current — most are not active)

- **Idempotency is correct.** All 7 patches are existence-guarded; repeat boot is safe.
- **Silent failure mode.** All 7 patches catch broad `Exception` and only log at warning level. If they did fire and failed, schema would end up half-migrated without blocking startup. **Currently inert** because the patches don't fire on the production or test paths.
- **No drift detection.** No assertion compares Alembic head vs. `Base.metadata`. A developer can add a model column without an Alembic migration and a SQLite test will silently lack it. **This risk is independent of the patches** — it lives in the absence of CI drift detection, not in the patches themselves.

### Risks (future, post-removal)

- **If Render's Dockerfile alembic step ever stops firing** (env regression, deploy script change, manual override), production boots without the patches *and* without an alembic upgrade. Tables would lack the columns added by recent migrations. This is the "patches are load-bearing again" failure mode, and it's why Sprint 737 step 1 is a verification gate (confirm alembic still fires on the last 3 deploys before deleting anything).
- **A stale-local-SQLite developer experience regression.** A developer with an old local SQLite file who pulls and boots without running alembic gets a less-friendly failure (column-not-found errors) instead of silent self-heal. Mitigation: documentation in CONTRIBUTING.

## Recommendation

**(b) Consolidate behind Alembic-only.**

> **Note:** an earlier draft of this doc recommended (c) "leave alone." That recommendation was based on incomplete evidence — specifically, on not having verified that Sprint 544c's Dockerfile wiring is still firing in production. That evidence is below. With it confirmed, the patches are reclassified as dead code today, and (b) becomes the correct call.

### Why (b) is the right call

- **The patches are dead code in production today.** Dockerfile CMD runs `alembic upgrade head` (or `alembic stamp head` for fresh DBs) before gunicorn starts. By the time `init_db()` runs, schema is already at head.
- **The patches are dead code in CI today.** `conftest.py` uses `Base.metadata.create_all()` against current models, which produces current schema directly.
- **The "operational coverage for fail-closed mode" cost from the original (c) recommendation evaporates.** Dockerfile already fail-closes on alembic failure, and `docs/runbooks/emergency-playbook.md` §4 ("Production deploy refuses to start on `alembic upgrade head`") already covers that mode. Option (b) does not introduce a new fail-closed path; it removes a now-superfluous safety net.
- **Doing it before Phase 4.1 is fine** because the patches are not load-bearing today. Removing dead code in the cutover window is qualitatively different from refactoring live behavior in the cutover window. The verification gate in Sprint 737 step 1 confirms "is the deploy path actually doing what we think" before any deletion.

### What (b) consists of

Executable plan lives in `tasks/todo.md` Sprint 737. Summary:

1. **Verification gate** — confirm last 3 Render deploys ran `alembic upgrade head` (`Running: alembic upgrade head` log line in startup). If yes → proceed. If no → Sprint 737 pivots to "restore alembic-on-deploy" before any deletion.
2. **Deletion** — remove the 7 patch blocks (lines 148–278 of `backend/database.py`, ~130 lines).
3. **CI drift test** — `alembic upgrade head` against fresh SQLite produces a schema matching `Base.metadata.create_all()`. Catches "model column added without an Alembic migration."
4. **Documentation** — `CONTRIBUTING.md` (or equivalent dev setup doc) gets a one-line note: "After pulling, run `python -m alembic upgrade head` if you have a local SQLite file."

### What stays in `init_db()`

- Model imports + `Base.metadata.create_all()` (idempotent table creation for fresh DBs — still legitimate).
- TLS verification + version logging (load-bearing startup health check, includes fail-closed `RuntimeError` on `DB_TLS_REQUIRED`).
- Completion log marker.

Post-Sprint-737 size estimate: `database.py` drops from 360 lines to ~230.

### Explicitly out of scope for (b)

- **No startup migration-version assertion.** Dockerfile already fail-closes; a runtime assertion would duplicate that mode and add operational complexity (runbook, alert routing) for marginal benefit. Reopen if the Dockerfile guarantee weakens.
- **No changes to existing Alembic migrations.**
- **No changes to `conftest.py`.** Current `create_all()` setup is correct; the new CI drift test guarantees Alembic-vs-models parity.

### Reopen criteria — when reverting to (a) "keep dual-path" would become justified

Revert only if:

1. Render deploy reliably stops running `alembic upgrade head` (env regression, deploy-script change) and the project chooses stale-startup-recovers convenience over fail-closed boot.
2. A third boot path emerges (e.g., embedded SQLite in a desktop build, a serverless lambda startup) that can't run Alembic.
3. The Alembic infrastructure itself becomes unreliable (recurring migration corruption, etc.) and the patches are needed as a backstop.

None of these are projected.

## Out of scope for Sprint 736

- No code changes to `backend/database.py`.
- No new tests.
- No migration-policy decision (the recommendation above is the *input* to a future decision sprint, not the decision itself).
- No CI assertion implementation.
- No decision on whether to add the documentation comment at line 148 — that is a future hotfix, not part of this sprint's deliverable.
