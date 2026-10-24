"""
Sprint 821 — check-then-act sequences that the blocked event loop used to
serialise within a worker (PR #217 review).

Once the handlers left the event loop, two requests in one worker could
interleave exactly as two requests in two workers always could. These tests
drive the interleaving deterministically with two separate sessions on a
file-backed SQLite database — the shape of two production requests.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def two_sessions(tmp_path):
    from database import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'race.db'}")
    Base.metadata.create_all(engine)
    make = sessionmaker(bind=engine)
    a, b = make(), make()
    yield a, b
    a.close()
    b.close()
    engine.dispose()


def test_a_single_use_share_is_served_once_when_two_downloads_interleave(two_sessions):
    from export_share_model import ExportShare
    from models import User
    from routes.export_sharing import _finalize_download

    a, b = two_sessions
    user = User(email="owner@example.com", hashed_password="x", is_verified=True)
    a.add(user)
    a.flush()
    a.add(
        ExportShare(
            user_id=user.id,
            share_token_hash="h" * 64,
            tool_name="ap_testing",
            export_format="csv",
            export_data=b"secret,data\n",
            single_use=True,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    a.commit()

    # Both requests resolve the share before either finalises — the race.
    first = a.query(ExportShare).one()
    second = b.query(ExportShare).one()
    assert first.revoked_at is None and second.revoked_at is None

    _finalize_download(first, None, a)
    with pytest.raises(HTTPException) as exc_info:
        _finalize_download(second, None, b)
    assert exc_info.value.status_code == 404


def test_seat_check_locks_the_organization_row_on_postgres():
    """SQLite has no row locks, so the guarantee is checked on the SQL itself:
    on Postgres the seat check must run behind ``SELECT ... FOR UPDATE``."""
    from unittest.mock import MagicMock

    from sqlalchemy.dialects import postgresql
    from sqlalchemy.orm import Query

    from organization_model import Organization
    from routes.organization import _lock_org_for_seat_check

    captured: dict[str, Query] = {}

    class _Recorder(Query):
        def first(self):
            captured["q"] = self
            return None

    db = MagicMock()
    db.query.side_effect = lambda *ent: _Recorder(ent)
    _lock_org_for_seat_check(db, 7)

    sql = str(captured["q"].statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in sql
    assert Organization.__tablename__ in sql


@pytest.mark.parametrize("handler", ["create_invite", "accept_invite"])
def test_both_seat_consuming_handlers_lock_before_counting(handler):
    import ast
    import inspect

    import routes.organization as org_routes

    tree = ast.parse(inspect.getsource(org_routes))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == handler)
    nodes = sorted(
        (n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)),
        key=lambda n: (n.lineno, n.col_offset),
    )
    calls = [n.func.id for n in nodes]
    assert "_lock_org_for_seat_check" in calls
    assert calls.index("_lock_org_for_seat_check") < calls.index("check_seat_limit_for_org")
