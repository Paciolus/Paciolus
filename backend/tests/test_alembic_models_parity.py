"""Sprint 737: Alembic head tables/columns/FKs must match `Base.metadata`.

WHAT THIS COVERS, AND WHAT IT DOES NOT
--------------------------------------
Covered: the **table set**, the **column-name set** per table, and (since
Sprint 797) **foreign keys**, primary keys and unique constraints.

**Not covered: nullability, column types, and server defaults.** That is a
decision, not an oversight, and it is written here because the previous
docstring said "schema must match `Base.metadata`" while comparing only names
— so "this schema is guarded" read as more coverage than it was.

* *Nullability* — 50 columns disagree. Every one is a column the ORM declares
  NOT NULL via a non-Optional ``Mapped[...]`` annotation while its migration
  created it nullable, and every one has a Python-side default, so no code
  path can emit NULL. Fifty migrations of churn for no behaviour change, and a
  fifty-row failure wall is how a gate gets switched off.
* *Types* — SQLite has no enum type, so a chain-built SQLite database reports
  VARCHAR where PostgreSQL has a native enum. Comparing types on this dialect
  would compare an artifact. Enum **labels** are covered separately and
  properly by ``guards/enum_label_drift.py`` / ``tests/test_enum_label_drift``.

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

The tests compare fresh SQLite databases built two ways and assert the table
set, the per-table column set and the foreign keys match. Sprint 797 added a
third check that drives ``init_db()`` itself, because the Dockerfile stamps
rather than upgrades on an empty database — so on a brand-new environment
``create_all()`` is the whole schema, and comparing two *other* builds says
nothing about it.
"""

from __future__ import annotations

import os
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

    Uses the same derived import as ``database.init_db()`` and
    ``migrations/alembic/env.py``. Sprint 797: this used to be a third
    hand-written copy of the module list, with a comment instructing the
    reader to keep it in sync with the other two — which held 11 and 15
    entries respectively while this one held 15. The instruction to stay in
    sync is what a shared function is for.
    """
    from database import Base
    from model_registry import import_all_models

    import_all_models()
    Base.metadata.create_all(bind=engine)


# EMPTIED BY SPRINT 797 — keep them empty.
#
# These held four tables and six columns that the ORM defined and no migration
# created. They were recorded as documented exceptions in Sprint 737 and filed
# for Sprint 738, which then sat for a year recorded as blocked on a production
# connection string. It was not blocked: production was built by `create_all()`
# from `Base.metadata`, so it already held every one of those objects, and
# writing the DDL needed no database read.
#
# Migration `c9e4a1b73f20` creates all ten, guarded by an inspector so it is a
# no-op against production and a catch-up against a chain-built database.
#
# An allow-list is the weakest form of a guard: it fails silently and
# indefinitely, and it cannot tell you when the thing it excuses has been
# fixed. If you are about to add an entry here, write the migration instead —
# and if you genuinely cannot, `test_drift_allowlists_stay_empty` below says
# so out loud rather than letting the exception disappear into a constant.
PRE_EXISTING_DRIFT_TABLES: frozenset[str] = frozenset()

# Format: {table_name: frozenset({column_name, ...}, ...)}
PRE_EXISTING_DRIFT_COLUMNS: dict[str, frozenset[str]] = {}


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


# =============================================================================
# Sprint 797 additions
# =============================================================================


def _foreign_keys(engine: Engine) -> dict[str, set[tuple[str, str, str]]]:
    """``{table: {(local_col, referred_table, referred_col), ...}}``."""
    inspector = inspect(engine)
    out: dict[str, set[tuple[str, str, str]]] = {}
    for table in inspector.get_table_names():
        if table == "alembic_version":
            continue
        keys: set[tuple[str, str, str]] = set()
        for fk in inspector.get_foreign_keys(table):
            for local, referred in zip(fk["constrained_columns"], fk["referred_columns"]):
                keys.add((local, fk["referred_table"], referred))
        out[table] = keys
    return out


def test_drift_allowlists_stay_empty():
    """An allow-list is the weakest guard: it fails silently and forever.

    Sprint 737 recorded four tables and six columns here as documented
    exceptions pending Sprint 738. Sprint 738 then sat for a year, recorded as
    blocked on a production connection string it did not need. Migration
    ``c9e4a1b73f20`` created all ten.

    If you are adding an entry, write the migration instead. If you truly
    cannot, this test failing is the point — the exception has to be argued
    for in review rather than disappearing into a constant.
    """
    assert PRE_EXISTING_DRIFT_TABLES == frozenset(), (
        f"Tables re-added to the drift allow-list: {sorted(PRE_EXISTING_DRIFT_TABLES)}. "
        f"Write an Alembic migration instead — see c9e4a1b73f20 for the guarded pattern "
        f"that is a no-op against a create_all()-built production database."
    )
    assert PRE_EXISTING_DRIFT_COLUMNS == {}, (
        f"Columns re-added to the drift allow-list: {PRE_EXISTING_DRIFT_COLUMNS}. Write an Alembic migration instead."
    )


def test_alembic_head_matches_base_metadata_foreign_keys(tmp_path):
    """Foreign keys, which the name/column comparison above cannot see.

    Three were missing before Sprint 797 — ``engagements.completed_by`` and
    the two ``archived_by`` columns — and nothing reported it, because the
    test next door compares column *names* under a docstring that claimed to
    compare the schema.
    """
    alembic_url = f"sqlite:///{tmp_path / 'alembic_fk.db'}"
    models_url = f"sqlite:///{tmp_path / 'models_fk.db'}"

    _alembic_upgrade_head(alembic_url)
    models_engine = create_engine(models_url)
    _create_all_against(models_engine)

    alembic_fks = _foreign_keys(create_engine(alembic_url))
    models_fks = _foreign_keys(models_engine)

    drift: list[str] = []
    for table in sorted(set(alembic_fks) & set(models_fks)):
        only_alembic = alembic_fks[table] - models_fks[table]
        only_models = models_fks[table] - alembic_fks[table]
        if only_models:
            drift.append(f"  {table}: in model but not in Alembic: {sorted(only_models)}")
        if only_alembic:
            drift.append(f"  {table}: in Alembic but not in model: {sorted(only_alembic)}")

    assert not drift, "Foreign-key drift between Alembic head and Base.metadata:\n" + "\n".join(drift)


def test_init_db_alone_creates_every_table(tmp_path):
    """The assertion none of the three import lists could ever fail.

    ``Dockerfile`` runs ``alembic stamp head`` — not ``upgrade`` — on a
    database with no ``alembic_version`` table, so a brand-new environment
    gets its schema entirely from ``init_db()``'s ``create_all()``. Before
    Sprint 797 that call imported 11 of 15 model modules, and measured
    results were 25 of 29 tables alone and **27 of 29** even through
    ``import main`` (which loads every route module). The two that never
    appeared were ``admin_audit_logs`` and ``dunning_episodes`` — and since
    ``stamp head`` had already marked their migrations applied, no later
    deploy would create them either.

    **This has to run in a subprocess, and the first version did not.**
    ``Base.metadata`` is process-global, so by the time any in-process test
    calls ``init_db()`` the conftest and every previously-imported test module
    have already registered all 29 tables. Reverting ``init_db()`` to its
    11-module hand list left the in-process version of this test **green** —
    it was measuring import order, not the function. A clean interpreter that
    imports only ``database`` is the only way to observe what ``init_db()``
    guarantees on its own.
    """
    import json
    import subprocess

    db_url = f"sqlite:///{(tmp_path / 'init_db.db').as_posix()}"
    program = (
        "import json, sys\n"
        "import database\n"
        "from sqlalchemy import inspect\n"
        "database.init_db()\n"
        "created = sorted(t for t in inspect(database.engine).get_table_names()\n"
        "                 if t != 'alembic_version')\n"
        "from model_registry import import_all_models\n"
        "import_all_models()\n"
        "from database import Base\n"
        "expected = sorted(Base.metadata.tables)\n"
        "sys.stdout.write('@@' + json.dumps({'created': created, 'expected': expected}))\n"
    )
    env = {**os.environ, "DATABASE_URL": db_url, "PYTHONPATH": str(_BACKEND_ROOT)}
    proc = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        cwd=str(_BACKEND_ROOT),
        env=env,
        timeout=180,
    )
    assert proc.returncode == 0, f"probe subprocess failed:\n{proc.stdout}\n{proc.stderr}"
    assert "@@" in proc.stdout, f"probe produced no result marker:\n{proc.stdout}\n{proc.stderr}"
    payload = json.loads(proc.stdout.split("@@", 1)[1])

    missing = sorted(set(payload["expected"]) - set(payload["created"]))
    assert not missing, (
        f"init_db() did not create {len(missing)} table(s): {missing}. On a fresh deployment "
        f"the Dockerfile stamps rather than upgrades, so these tables would never exist. "
        f"Check backend/model_registry.py."
    )


def test_model_registry_is_what_init_db_and_env_py_both_use():
    """One list, not three.

    The three copies previously held 11, 15 and 15 entries. This asserts the
    single derived source is non-empty and sees every module that defines an
    ORM model — the AST cross-check lives in ``tests/test_model_registry.py``.
    """
    from model_registry import model_module_names

    names = model_module_names()
    assert len(names) >= 15, f"model registry found only {len(names)} modules: {names}"
    assert "models" in names
    # The four that init_db() used to omit. Named explicitly because they are
    # the ones whose absence was invisible for a year.
    for omitted in (
        "admin_audit_model",
        "dunning_model",
        "analytical_expectations_model",
        "uncorrected_misstatements_model",
    ):
        assert omitted in names, f"{omitted} missing from the derived model set"
