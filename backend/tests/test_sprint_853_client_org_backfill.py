"""Sprint 853: the ``clients.organization_id`` backfill follows the CEO decision.

A client whose creator belongs to a firm when the migration runs becomes that
firm's client; a client whose creator has no firm stays personal (NULL).
Runs the real migration chain on a scratch SQLite file: upgrade to the
revision before, insert rows, upgrade to the Sprint 853 revision, check.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, text

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_BEFORE = "b9d3f6a2c418"
_SPRINT_853 = "c853a1f0e2d4"


def _upgrade(db_url: str, revision: str) -> None:
    from alembic import command
    from alembic.config import Config

    import config

    original = config.DATABASE_URL
    config.DATABASE_URL = db_url
    try:
        cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", db_url)
        cfg.set_main_option("script_location", str(_BACKEND_ROOT / "migrations" / "alembic"))
        cfg.config_file_name = None  # keep pytest's log capture (see test_alembic_models_parity)
        command.upgrade(cfg, revision)
    finally:
        config.DATABASE_URL = original


def _user(conn, uid: int) -> None:  # noqa: ANN001
    conn.execute(
        text(
            "INSERT INTO users (id, email, hashed_password, is_active, is_verified, tier, "
            "failed_login_attempts, created_at, updated_at) "
            "VALUES (:id, :email, 'x', 1, 1, 'PROFESSIONAL', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ),
        {"id": uid, "email": f"u{uid}@example.com"},
    )


def _client(conn, cid: int, uid: int) -> None:  # noqa: ANN001
    conn.execute(
        text(
            "INSERT INTO clients (id, user_id, name, industry, fiscal_year_end, reporting_framework, "
            "entity_type, jurisdiction_country, settings, created_at, updated_at) "
            "VALUES (:id, :uid, :name, 'OTHER', '12-31', 'AUTO', 'OTHER', 'US', '{}', "
            "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ),
        {"id": cid, "uid": uid, "name": f"Client {cid}"},
    )


def test_backfill_assigns_firm_members_clients_and_leaves_the_rest_personal(tmp_path, caplog):
    db_url = f"sqlite:///{(tmp_path / 'backfill.db').as_posix()}"
    _upgrade(db_url, _BEFORE)

    engine = create_engine(db_url)
    with engine.begin() as conn:
        for uid in (1, 2, 3):
            _user(conn, uid)
        conn.execute(text("INSERT INTO organizations (id, name, slug, owner_user_id) VALUES (10, 'Firm', 'firm', 1)"))
        conn.execute(text("INSERT INTO organization_members (organization_id, user_id, role) VALUES (10, 1, 'OWNER')"))
        conn.execute(text("INSERT INTO organization_members (organization_id, user_id, role) VALUES (10, 2, 'MEMBER')"))
        _client(conn, 100, 1)  # owner's client  -> firm
        _client(conn, 101, 2)  # member's client -> firm
        _client(conn, 102, 3)  # no firm         -> personal
    engine.dispose()

    with caplog.at_level(logging.INFO, logger="alembic.runtime.migration"):
        _upgrade(db_url, _SPRINT_853)

    engine = create_engine(db_url)
    with engine.connect() as conn:
        rows = dict(conn.execute(text("SELECT id, organization_id FROM clients ORDER BY id")).all())
    engine.dispose()

    assert rows == {100: 10, 101: 10, 102: None}
    assert "2 clients assigned to a firm, 1 stayed personal" in caplog.text
