"""Database URL normalization (Sprint 786b — SQLAlchemy 2.1).

SQLAlchemy 2.1 changed the default DBAPI for a driverless ``postgresql://``
URL from ``psycopg2`` to ``psycopg`` (v3). Paciolus installs
``psycopg2-binary`` only, and production's ``DATABASE_URL`` (Neon, set on
Render) is a plain ``postgresql://...`` URL. Left alone, the 2.1 bump would
make every PostgreSQL engine fail with ``ModuleNotFoundError: psycopg`` while
the SQLite test suite stayed green.

``normalize_database_url`` pins the driver explicitly. It is applied once, in
``config.py``, so the application engine (``database.py``), Alembic
(``migrations/alembic/env.py``), the Dockerfile's stamp-or-upgrade probe and
the admin scripts all see the same normalized URL. The test engine
(``tests/conftest.py``, ``TEST_DATABASE_URL``) applies it too.

The rewrite is a scheme-prefix substitution on the raw string — nothing else
in the URL is parsed or re-rendered, so credentials (including percent-escaped
passwords), host, port, database and query parameters such as ``sslmode`` and
``channel_binding`` are preserved byte-for-byte.

Do NOT pass a normalized URL to libpq tools (``psql``, ``pg_dump``) or to
``psycopg2.connect``: ``postgresql+psycopg2://`` is SQLAlchemy syntax only.
"""

from __future__ import annotations

# Driverless PostgreSQL schemes. ``postgres://`` is the Heroku/Render-style
# alias; SQLAlchemy has rejected it since 1.4, so normalizing it is purely
# additive.
_DRIVERLESS_POSTGRES_SCHEMES = ("postgresql://", "postgres://")

PSYCOPG2_SCHEME = "postgresql+psycopg2://"


def normalize_database_url(url: str) -> str:
    """Return ``url`` with a driverless PostgreSQL scheme pinned to psycopg2.

    - ``postgresql://...`` / ``postgres://...`` -> ``postgresql+psycopg2://...``
    - URLs that already name a driver (``postgresql+psycopg2://``,
      ``postgresql+psycopg://``, ``postgresql+asyncpg://``) are unchanged.
    - Non-PostgreSQL URLs (``sqlite:///...``) are unchanged.
    """
    lowered = url.lower()
    for scheme in _DRIVERLESS_POSTGRES_SCHEMES:
        if lowered.startswith(scheme):
            return PSYCOPG2_SCHEME + url[len(scheme) :]
    return url
