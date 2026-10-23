"""Alembic environment configuration for Paciolus database migrations."""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure backend root is on the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import DATABASE_URL
from database import Base
from model_registry import import_all_models

# Import every ORM model module so Base.metadata knows about them.
#
# Sprint 797: this was a hand-written list of 15 imports, while the equivalent
# list in `database.init_db()` held 11 and the one in the parity test held 15.
# Three copies, two of them disagreeing. The set is now derived — see
# `backend/model_registry.py`.
import_all_models()

# Alembic Config object
config = context.config

# Override the ini-file DB URL with the canonical one from config.py
# so Alembic always points at the same database as the application.
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Set up Python logging from the .ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at our model metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL scripts without connecting)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
