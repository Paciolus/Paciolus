"""Sprint 610: LIKE wildcard escape tests.

Asserts:
  1. The helper escapes %, _, and backslash for literal matching.
  2. ClientManager.search_clients treats wildcards as literals.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from client_manager import ClientManager
from database import Base
from models import Client, User
from shared.helpers import escape_like_wildcards


class TestEscapeLikeWildcards:
    def test_empty_string(self):
        assert escape_like_wildcards("") == ""

    def test_plain_text_unchanged(self):
        assert escape_like_wildcards("Acme Corp") == "Acme Corp"

    def test_percent_escaped(self):
        assert escape_like_wildcards("50%") == "50\\%"

    def test_underscore_escaped(self):
        assert escape_like_wildcards("a_b") == "a\\_b"

    def test_backslash_escaped_first(self):
        # Must escape the backslash first, otherwise we double-escape % and _.
        assert escape_like_wildcards("a\\b") == "a\\\\b"

    def test_compound_escape(self):
        assert escape_like_wildcards("100%\\_ok") == "100\\%\\\\\\_ok"


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def user(db_session):
    u = User(email="tester@example.com", hashed_password="x", is_active=True, is_verified=True)
    db_session.add(u)
    db_session.commit()
    return u


class TestClientSearchLikeEscape:
    def test_literal_percent_only_matches_literal(self, db_session, user):
        db_session.add_all(
            [
                Client(user_id=user.id, name="Revenue 50% Growth"),
                Client(user_id=user.id, name="Acme Corp"),
                Client(user_id=user.id, name="Beta Inc"),
            ]
        )
        db_session.commit()

        mgr = ClientManager(db_session)
        results = mgr.search_clients(user.id, "%")
        # Pre-fix, `%` triggered a full-table scan matching all three rows.
        # Post-fix, `%` is escaped and only matches the literal percent row.
        names = {c.name for c in results}
        assert names == {"Revenue 50% Growth"}

    def test_literal_underscore_only_matches_literal(self, db_session, user):
        db_session.add_all(
            [
                Client(user_id=user.id, name="Client_Alpha"),
                Client(user_id=user.id, name="ClientX"),
            ]
        )
        db_session.commit()

        mgr = ClientManager(db_session)
        results = mgr.search_clients(user.id, "_")
        names = {c.name for c in results}
        # Only the row with a literal underscore matches; `_` no longer
        # wildcards to "any single character".
        assert names == {"Client_Alpha"}

    def test_normal_search_still_works(self, db_session, user):
        db_session.add_all(
            [
                Client(user_id=user.id, name="Acme Corp"),
                Client(user_id=user.id, name="Beta Inc"),
            ]
        )
        db_session.commit()

        mgr = ClientManager(db_session)
        results = mgr.search_clients(user.id, "Acme")
        assert [c.name for c in results] == ["Acme Corp"]
