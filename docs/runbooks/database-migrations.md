# Database migrations — expand, then contract

Sprint 897 (O-9), from `reports/council-audit-2026-11-25.md`.

## Why

The production image runs `alembic upgrade head` at start-up, before Gunicorn
starts (`backend/Dockerfile`). While it runs, **the previous release is still
serving traffic** on the old instance. If the new image then fails to start,
Render keeps the old one serving, possibly for a long time (the Sprint 768
outage lasted 5.5 months). Every migration therefore has to work with the code
that is live *before* it as well as the code that ships *with* it.

## The rule

| Change | Release N (expand) | Release N+1 or later (contract) |
|---|---|---|
| Add a column | Add it nullable (or with a server default). Code may write it. | Make it `NOT NULL` once every row is filled. |
| Remove a column | Stop reading and writing it in code. | `drop_column`. |
| Rename a column | Add the new column, write both, backfill, read the new one. | Drop the old column. |
| Change a column's type | Add a new column of the new type, backfill, switch reads. | Drop the old column. |
| Remove a table | Stop using it in code. | `drop_table`. |
| Change an enum | Add the new value (in its own transaction on PostgreSQL). | Remove the old value. |

Additive changes (new tables, nullable columns, indexes) need nothing special.

## The guard

`scripts/check_destructive_migrations.py`, run by
`backend/tests/test_destructive_migration_guard.py` in the required
`backend-tests` CI job, reads each migration's `upgrade()` and fails on
`drop_table`, `drop_column`, `rename_table`, `alter_column(new_column_name=…)`,
`alter_column(type_=…)` (including inside `batch_alter_table`) and raw SQL with
`DROP TABLE`, `DROP COLUMN`, `RENAME` or `ALTER … TYPE`. `downgrade()` is not
checked.

When the migration **is** the contract step and no serving release reads the
old shape any more, say so in the file:

```python
# expand-contract: contract step — release 2.3 stopped reading users.legacy_flag (Sprint 9xx)
```

The reason is required; a bare marker does not pass.

Run it locally:

```bash
python scripts/check_destructive_migrations.py
```

The five migrations written before this rule are listed in `GRANDFATHERED` in
the script. That list is frozen: they have already run on production.
