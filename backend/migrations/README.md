# Paciolus Database Migrations

Database migrations are managed with [Alembic](https://alembic.sqlalchemy.org/).

## Setup

Alembic is configured at `backend/alembic.ini` with migration scripts in `backend/migrations/alembic/`.

The `env.py` auto-imports all models from `models.py` so autogenerate can detect schema changes.

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

## Initial Migration

The initial migration (`ae18bcf1ba02`) captures the baseline schema:
- `users` — authentication and user profile
- `activity_logs` — audit summary metadata
- `clients` — multi-tenant client identification
- `diagnostic_summaries` — aggregate category totals and ratio tracking
- `email_verification_tokens` — single-use email verification
