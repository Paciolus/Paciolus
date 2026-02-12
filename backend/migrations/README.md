# Paciolus Database Migrations

Database migrations are managed with [Alembic](https://alembic.sqlalchemy.org/).

## Setup

Alembic is configured at `backend/alembic.ini` with migration scripts in `backend/migrations/alembic/`.

The `env.py` auto-imports all models from `models.py` and `follow_up_items_model.py` so autogenerate can detect schema changes.

## Common Commands

All commands run from the `backend/` directory:

```bash
# Check current migration status
python -m alembic current

# Generate a new migration after modifying models.py
python -m alembic revision --autogenerate -m "description_of_change"

# Apply all pending migrations
python -m alembic upgrade head

# Roll back one migration
python -m alembic downgrade -1

# View migration history
python -m alembic history
```

## Workflow

1. Edit `models.py` to add/modify tables or columns
2. Run `python -m alembic revision --autogenerate -m "description"`
3. Review the generated migration in `migrations/alembic/versions/`
4. Run `python -m alembic upgrade head` to apply
5. Commit the migration file with your model changes

## SQLite Notes

- `render_as_batch=True` is enabled in `env.py` for SQLite ALTER TABLE support
- SQLite doesn't support all ALTER operations natively; batch mode handles this
- In-memory SQLite databases (used in tests) don't need migrations — `create_all()` is used instead

## Baseline Migration

The baseline migration (`e2f21cb79a61`) captures the full schema as of v1.2.0:
- `users` — authentication, profile, email verification, tier
- `activity_logs` — audit summary metadata
- `clients` — multi-tenant client identification
- `diagnostic_summaries` — aggregate category totals and ratio tracking
- `email_verification_tokens` — single-use email verification
- `engagements` — diagnostic workspace sessions with materiality cascade
- `tool_runs` — per-tool execution records within engagements
- `follow_up_items` — narrative follow-up items linked to engagements
- `follow_up_item_comments` — threaded comments on follow-up items

## Archived Scripts

The `archive/` directory contains historical manual migration scripts that were used before Alembic was fully operational. These are superseded by the baseline migration and retained for reference only:

- `add_user_name_field.py` — Sprint 48: Added `users.name` column
- `add_email_verification_fields.py` — Sprint 57: Added email verification columns and `email_verification_tokens` table
