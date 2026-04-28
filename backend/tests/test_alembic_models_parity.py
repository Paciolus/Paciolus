"""Sprint 737: Alembic head schema must match `Base.metadata`.

After Sprint 737 deleted the in-process schema-patch blocks from
`init_db()`, Alembic is the single authority for schema evolution. This
test catches the failure mode where a developer adds a column to a model
without writing the corresponding Alembic migration — the only real risk
the consolidation creates.

Failure mode it catches:
- Engineer adds `users.new_field` to `models.User` without an Alembic
  migration. Tests using `Base.metadata.create_all()` (conftest.py) pass
  because create_all sees the model. Production deploy runs `alembic
  upgrade head` and the column is missing — first request to the field
  blows up. Pre-Sprint-737, the in-process patcher would have papered over
  this in some environments; post-Sprint-737, this test is the safety net.

The test compares fresh SQLite databases built two ways and asserts the
table set + per-table column set match.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

# Ensure backend root is on the path so model imports work
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


def _alembic_upgrade_head(db_url: str) -> None:
    """Run `alembic upgrade head` against the given database URL.

    Programmatic equivalent of the production Dockerfile's
    ``alembic upgrade head`` invocation. Monkeypatches ``config.DATABASE_URL``
    before alembic loads ``env.py`` so the migration targets our test DB
    instead of the real one — env.py reads ``DATABASE_URL`` at import time
    and overrides whatever URL was set on the alembic Config object.
    """
    from alembic import command
    from alembic.config import Config

    import config

    original_url = config.DATABASE_URL
    config.DATABASE_URL = db_url
    try:
        alembic_ini = _BACKEND_ROOT / "alembic.ini"
        cfg = Config(str(alembic_ini))
        cfg.set_main_option("sqlalchemy.url", db_url)
        # alembic.ini's `script_location = migrations/alembic` is relative to
        # the cwd where alembic runs (production CMD runs it from /app where
        # /app == backend/). Tests run from the repo root, so resolve the
        # script_location to an absolute path so the test is cwd-independent.
        cfg.set_main_option("script_location", str(_BACKEND_ROOT / "migrations" / "alembic"))
        # CRITICAL: skip env.py's `fileConfig(config.config_file_name)` call —
        # it has `disable_existing_loggers=True` by default and wipes pytest's
        # caplog handler for every subsequent test in the same process. Setting
        # `config_file_name = None` makes env.py's `if config.config_file_name
        # is not None: fileConfig(...)` branch a no-op while preserving everything
        # else loaded from alembic.ini at Config init time (sections, etc.).
        # Without this guard, ~16 tests across 7 files fail with empty caplog
        # text after this drift test runs — see the CI failures on the original
        # Sprint 737 commit (af00a7ce) for the full list.
        cfg.config_file_name = None
        # env.py is reloaded by alembic on each command invocation, so the
        # monkeypatch above will be visible to the `from config import
        # DATABASE_URL` line in env.py.
        command.upgrade(cfg, "head")
    finally:
        config.DATABASE_URL = original_url


def _create_all_against(engine: Engine) -> None:
    """Run ``Base.metadata.create_all()`` after importing every model module.

    Mirrors the model-import set in ``database.init_db()`` and
    ``backend/migrations/alembic/env.py`` so Base.metadata is fully
    populated before create_all fires.
    """
    # Order doesn't matter; what matters is that every model module is
    # imported so its tables register on Base.metadata. Keep this list in
    # sync with `init_db()` and `migrations/alembic/env.py`.
    import admin_audit_model  # noqa: F401
    import analytical_expectations_model  # noqa: F401
    import dunning_model  # noqa: F401
    import engagement_model  # noqa: F401
    import export_share_model  # noqa: F401
    import firm_branding_model  # noqa: F401
    import follow_up_items_model  # noqa: F401
    import models  # noqa: F401
    import organization_model  # noqa: F401
    import scheduler_lock_model  # noqa: F401
    import subscription_model  # noqa: F401
    import team_activity_model  # noqa: F401
    import tool_session_model  # noqa: F401
    import uncorrected_misstatements_model  # noqa: F401
    import upload_dedup_model  # noqa: F401
    from database import Base

    Base.metadata.create_all(bind=engine)


# Tables defined in models but with NO corresponding Alembic migration.
# Created today by `init_db()`'s `Base.metadata.create_all()` call —
# Sprint 737 did not change that, the in-process schema patches it removed
# only ever touched columns on existing tables, not whole table creation.
# These four tables represent pre-existing tech debt discovered during
# Sprint 737's drift-test build-out, filed for cleanup in Sprint 738.
#
# Until Sprint 738 lands migrations for each, this test treats them as
# documented exceptions: skipped from the table-set comparison, but
# everything else must match exactly.
PRE_EXISTING_DRIFT_TABLES = frozenset(
    {
        "password_reset_tokens",  # backend/models.py
        "processed_webhook_events",  # backend/subscription_model.py
        "tool_activities",  # backend/models.py
        "waitlist_signups",  # backend/models.py
    }
)

# Columns defined on a model but with NO Alembic migration adding them.
# Same Sprint 737 → Sprint 738 logic as the table allow-list above:
# Sprint 737's scope was the in-process patch-block deletion, which never
# touched these columns (the patcher's hardcoded set was just users +
# refresh_tokens). These columns are pre-existing drift surfaced by the
# new parity test. Sprint 738 will write the missing migrations.
#
# Format: {table_name: frozenset({column_name, ...}, ...)}
PRE_EXISTING_DRIFT_COLUMNS: dict[str, frozenset[str]] = {
    # backend/engagement_model.py — Engagement.completed_at / completed_by
    "engagements": frozenset({"completed_at", "completed_by"}),
    # backend/models.py — DiagnosticSummary cash-conversion-cycle ratios
    "diagnostic_summaries": frozenset({"ccc", "dio", "dpo", "dso"}),
}


def _table_columns(engine: Engine) -> dict[str, set[str]]:
    """Return ``{table_name: {column_name, ...}, ...}`` skipping bookkeeping
    tables and pre-existing documented drift (Sprint 738 backlog)."""
    inspector = inspect(engine)
    skip = {"alembic_version"} | PRE_EXISTING_DRIFT_TABLES
    return {
        table: {col["name"] for col in inspector.get_columns(table)}
        for table in inspector.get_table_names()
        if table not in skip
    }


def _drop_drifted_columns(schema: dict[str, set[str]]) -> dict[str, set[str]]:
    """Remove allow-listed pre-existing-drift columns from a schema dict
    so the comparison only sees the columns Alembic and models actually agree on."""
    return {table: cols - PRE_EXISTING_DRIFT_COLUMNS.get(table, frozenset()) for table, cols in schema.items()}


def test_alembic_head_matches_base_metadata(tmp_path):
    """Fresh SQLite + ``alembic upgrade head`` must produce the same tables
    and columns as a fresh SQLite with ``Base.metadata.create_all()``.

    If this fails, the most likely cause is that someone added a column
    (or table) to a model without writing the matching Alembic migration.
    """
    alembic_db = tmp_path / "alembic.db"
    models_db = tmp_path / "models.db"

    alembic_url = f"sqlite:///{alembic_db}"
    models_url = f"sqlite:///{models_db}"

    _alembic_upgrade_head(alembic_url)

    models_engine = create_engine(models_url)
    _create_all_against(models_engine)

    alembic_engine = create_engine(alembic_url)
    alembic_schema = _drop_drifted_columns(_table_columns(alembic_engine))
    models_schema = _drop_drifted_columns(_table_columns(models_engine))

    only_in_alembic_tables = set(alembic_schema) - set(models_schema)
    only_in_models_tables = set(models_schema) - set(alembic_schema)

    assert not only_in_alembic_tables, (
        "Tables exist in Alembic head but not in current Base.metadata: "
        f"{sorted(only_in_alembic_tables)}. Either delete the migration "
        "that creates them, or restore the model that was removed."
    )
    assert not only_in_models_tables, (
        "Tables exist in Base.metadata but not in Alembic head: "
        f"{sorted(only_in_models_tables)}. Add an Alembic migration for "
        "the new table(s) — Sprint 737 removed the in-process schema-patch "
        "fallback that previously hid this drift."
    )

    column_drift: list[str] = []
    for table in sorted(alembic_schema):
        alembic_cols = alembic_schema[table]
        models_cols = models_schema[table]
        only_in_alembic_cols = alembic_cols - models_cols
        only_in_models_cols = models_cols - alembic_cols
        if only_in_alembic_cols:
            column_drift.append(f"  {table}: in Alembic but not in model: {sorted(only_in_alembic_cols)}")
        if only_in_models_cols:
            column_drift.append(f"  {table}: in model but not in Alembic: {sorted(only_in_models_cols)}")

    assert not column_drift, (
        "Column drift between Alembic head and current Base.metadata:\n"
        + "\n".join(column_drift)
        + "\n\nFix: either add an Alembic migration for the missing column(s), "
        "or revert the model change. Sprint 737 removed the in-process "
        "schema-patch fallback in `init_db()`, so production deploys will now "
        "lack the column instead of self-healing."
    )
