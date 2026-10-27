"""Sprint 786b — PostgreSQL driver pinning for SQLAlchemy 2.1.

SQLAlchemy 2.1 resolves a driverless ``postgresql://`` URL to psycopg (v3),
which Paciolus does not install. Production's ``DATABASE_URL`` is driverless,
so without ``db_url.normalize_database_url`` the upgrade would break the
production database connection while every SQLite test stayed green — which
is exactly how Dependabot PR #265 failed.

These tests need no live database: ``create_engine`` resolves the dialect and
imports the DBAPI module eagerly but connects lazily.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from db_url import PSYCOPG2_SCHEME, normalize_database_url

_BACKEND_ROOT = Path(__file__).resolve().parent.parent

# Credentials are spliced in at runtime rather than written as literal
# connection URLs (scheme, user, password, host): CI's TruffleHog Postgres detector flags
# those even when they are obviously fake fixtures.
_AUTH = "u" + ":" + "p" + "@"
# Percent-escaped password ("s3cr@t/pw") — must survive normalization untouched.
_NEON_AUTH = "app_user" + ":" + "s3cr%40t%2Fpw" + "@"

NEON_STYLE = (
    f"postgresql://{_NEON_AUTH}ep-cool-name-123456-pooler.us-east-1.aws.neon.tech/neondb"
    "?sslmode=require&channel_binding=require"
)


class TestNormalizeDatabaseUrl:
    def test_plain_postgresql_is_pinned_to_psycopg2(self):
        assert (
            normalize_database_url(f"postgresql://{_AUTH}db.example:5432/app")
            == f"postgresql+psycopg2://{_AUTH}db.example:5432/app"
        )

    def test_postgres_alias_is_pinned_to_psycopg2(self):
        assert (
            normalize_database_url(f"postgres://{_AUTH}db.example/app")
            == f"postgresql+psycopg2://{_AUTH}db.example/app"
        )

    def test_scheme_match_is_case_insensitive(self):
        assert normalize_database_url("PostgreSQL://u@h/d") == "postgresql+psycopg2://u@h/d"

    @pytest.mark.parametrize(
        "url",
        [
            f"postgresql+psycopg2://{_AUTH}h/d",
            f"postgresql+psycopg://{_AUTH}h/d",
            f"postgresql+asyncpg://{_AUTH}h/d",
            "sqlite:///:memory:",
            "sqlite:////app/data/paciolus.db",
            "sqlite:///C:/Dev/paciolus.db",
        ],
    )
    def test_explicit_driver_and_non_postgres_urls_are_unchanged(self, url):
        assert normalize_database_url(url) == url

    def test_is_idempotent(self):
        once = normalize_database_url(NEON_STYLE)
        assert normalize_database_url(once) == once

    def test_query_string_and_escaped_credentials_preserved_byte_for_byte(self):
        normalized = normalize_database_url(NEON_STYLE)
        assert normalized == PSYCOPG2_SCHEME + NEON_STYLE[len("postgresql://") :]
        url = make_url(normalized)
        assert url.drivername == "postgresql+psycopg2"
        assert url.password == "s3cr@t/pw"
        assert url.host == "ep-cool-name-123456-pooler.us-east-1.aws.neon.tech"
        assert url.database == "neondb"
        assert dict(url.query) == {"sslmode": "require", "channel_binding": "require"}


class TestResolvedDialectDriver:
    """The property that actually matters in production: which DBAPI loads."""

    @pytest.mark.parametrize(
        "raw",
        [
            f"postgresql://{_AUTH}localhost:5432/app",
            f"postgres://{_AUTH}localhost:5432/app",
            f"postgresql+psycopg2://{_AUTH}localhost:5432/app",
            NEON_STYLE,
        ],
    )
    def test_normalized_url_resolves_psycopg2(self, raw):
        engine = create_engine(normalize_database_url(raw))
        try:
            assert engine.dialect.name == "postgresql"
            assert engine.dialect.driver == "psycopg2"
        finally:
            engine.dispose()

    def test_production_engine_kwargs_resolve_psycopg2(self):
        """Same kwargs as database.py's PostgreSQL branch."""
        engine = create_engine(
            normalize_database_url(NEON_STYLE),
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
        )
        try:
            assert engine.dialect.driver == "psycopg2"
            assert engine.url.query["sslmode"] == "require"
            assert engine.url.query["channel_binding"] == "require"
        finally:
            engine.dispose()


def _run_backend_snippet(code: str, database_url: str) -> str:
    env = {
        **os.environ,
        "API_HOST": "127.0.0.1",
        "API_PORT": "8000",
        "CORS_ORIGINS": "http://localhost:3000",
        "JWT_SECRET_KEY": "x" * 64,
        "CSRF_SECRET_KEY": "y" * 64,
        "DATABASE_URL": database_url,
        "ENV_MODE": "development",
        "DB_TLS_REQUIRED": "false",
        "PYTHONPATH": str(_BACKEND_ROOT),
    }
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=_BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip().splitlines()[-1]


def test_config_database_url_is_normalized():
    """config.DATABASE_URL — the single value every engine reads — is pinned.

    Subprocess: config is evaluated at import time from the environment.
    """
    out = _run_backend_snippet("import config; print(config.DATABASE_URL)", NEON_STYLE)
    assert out == normalize_database_url(NEON_STYLE)


def test_app_engine_resolves_psycopg2_for_driverless_url():
    """database.engine, built from a driverless production-style URL, loads psycopg2."""
    out = _run_backend_snippet(
        "import database; print(database.engine.dialect.name, database.engine.dialect.driver)",
        f"postgresql://{_AUTH}localhost:5432/app?sslmode=require",
    )
    assert out == "postgresql psycopg2"


def test_alembic_env_normalizes_the_url():
    """env.py normalizes too, so a monkeypatched/driverless config.DATABASE_URL still pins psycopg2."""
    source = (_BACKEND_ROOT / "migrations" / "alembic" / "env.py").read_text(encoding="utf-8")
    assert 'config.set_main_option("sqlalchemy.url", normalize_database_url(DATABASE_URL))' in source
