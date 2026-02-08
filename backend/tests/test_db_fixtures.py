"""
Sprint 96.5: Database fixture validation tests.

These tests verify the in-memory SQLite test infrastructure works correctly.
They serve as a template for Phase X engagement model tests.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, Client, ActivityLog, DiagnosticSummary, Industry, UserTier


class TestDatabaseFixtures:
    """Verify conftest.py DB fixtures work correctly."""

    def test_session_provides_clean_db(self, db_session):
        """Each test should start with an empty database."""
        users = db_session.query(User).all()
        assert users == []

    def test_make_user_creates_user(self, db_session, make_user):
        """Factory fixture creates a user with an assigned ID."""
        user = make_user(email="alice@test.com", name="Alice")
        assert user.id is not None
        assert user.email == "alice@test.com"
        assert user.name == "Alice"

    def test_make_user_defaults(self, db_session, make_user):
        """Factory fixture applies sensible defaults."""
        user = make_user()
        assert user.tier == UserTier.PROFESSIONAL
        assert user.is_active is True
        assert user.is_verified is True

    def test_make_client_creates_client(self, db_session, make_client):
        """Factory fixture creates a client linked to a user."""
        client = make_client(name="BigCo", industry=Industry.MANUFACTURING)
        assert client.id is not None
        assert client.name == "BigCo"
        assert client.industry == Industry.MANUFACTURING
        assert client.user_id is not None

    def test_transaction_isolation(self, db_session, make_user):
        """Data from other tests should not leak into this one."""
        users = db_session.query(User).all()
        assert len(users) == 0, "Transaction rollback should clear prior test data"

    def test_sample_user_fixture(self, sample_user):
        """Convenience fixture provides a ready-made user."""
        assert sample_user.id is not None
        assert sample_user.email == "test@example.com"

    def test_sample_client_fixture(self, sample_client):
        """Convenience fixture provides a ready-made client."""
        assert sample_client.id is not None
        assert sample_client.name == "Acme Corp"


class TestUserCRUD:
    """Template CRUD tests for the User model."""

    def test_create_user(self, db_session, make_user):
        user = make_user(email="crud@test.com")
        found = db_session.query(User).filter_by(email="crud@test.com").first()
        assert found is not None
        assert found.id == user.id

    def test_read_user_by_id(self, db_session, make_user):
        user = make_user()
        found = db_session.get(User, user.id)
        assert found is not None
        assert found.email == user.email

    def test_update_user(self, db_session, make_user):
        user = make_user(name="Original")
        user.name = "Updated"
        db_session.flush()
        found = db_session.get(User, user.id)
        assert found.name == "Updated"

    def test_delete_user(self, db_session, make_user):
        user = make_user(email="delete@test.com")
        db_session.delete(user)
        db_session.flush()
        found = db_session.query(User).filter_by(email="delete@test.com").first()
        assert found is None

    def test_unique_email_constraint(self, db_session, make_user):
        make_user(email="unique@test.com")
        with pytest.raises(Exception):
            make_user(email="unique@test.com")
            db_session.flush()

    def test_user_tier_enum(self, db_session, make_user):
        user = make_user(tier=UserTier.ENTERPRISE)
        found = db_session.get(User, user.id)
        assert found.tier == UserTier.ENTERPRISE

    def test_user_to_repr(self, make_user):
        user = make_user(email="repr@example.com")
        assert "repr@exam" in repr(user)


class TestClientCRUD:
    """Template CRUD tests for the Client model."""

    def test_create_client(self, db_session, make_client):
        client = make_client(name="TestCo")
        found = db_session.query(Client).filter_by(name="TestCo").first()
        assert found is not None

    def test_client_user_relationship(self, db_session, make_user, make_client):
        user = make_user(email="owner@test.com")
        client = make_client(name="OwnedCo", user=user)
        assert client.user_id == user.id

    def test_client_to_dict(self, make_client):
        client = make_client(name="DictCo", industry=Industry.RETAIL)
        d = client.to_dict()
        assert d["name"] == "DictCo"
        assert d["industry"] == "retail"
        assert d["fiscal_year_end"] == "12-31"

    def test_client_industry_enum(self, db_session, make_client):
        client = make_client(industry=Industry.HEALTHCARE)
        found = db_session.get(Client, client.id)
        assert found.industry == Industry.HEALTHCARE

    def test_multiple_clients_per_user(self, db_session, make_user, make_client):
        user = make_user(email="multi@test.com")
        c1 = make_client(name="Co1", user=user)
        c2 = make_client(name="Co2", user=user)
        clients = db_session.query(Client).filter_by(user_id=user.id).all()
        assert len(clients) == 2

    def test_delete_client(self, db_session, make_client):
        client = make_client(name="DeleteMe")
        db_session.delete(client)
        db_session.flush()
        found = db_session.query(Client).filter_by(name="DeleteMe").first()
        assert found is None


class TestActivityLogCRUD:
    """Template CRUD tests for the ActivityLog model."""

    def test_create_activity_log(self, db_session, make_user):
        user = make_user()
        log = ActivityLog(
            user_id=user.id,
            filename_hash="abc123",
            filename_display="test.csv...",
            record_count=100,
            total_debits=50000.0,
            total_credits=50000.0,
            materiality_threshold=1000.0,
            was_balanced=True,
            anomaly_count=3,
            material_count=1,
            immaterial_count=2,
        )
        db_session.add(log)
        db_session.flush()
        assert log.id is not None

    def test_activity_log_to_dict(self, db_session, make_user):
        user = make_user()
        log = ActivityLog(
            user_id=user.id,
            filename_hash="hash456",
            record_count=50,
            total_debits=25000.0,
            total_credits=25000.0,
            materiality_threshold=500.0,
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()
        d = log.to_dict()
        assert d["record_count"] == 50
        assert d["was_balanced"] is True

    def test_activity_log_user_relationship(self, db_session, make_user):
        user = make_user(email="logger@test.com")
        log = ActivityLog(
            user_id=user.id,
            filename_hash="rel123",
            record_count=10,
            total_debits=1000.0,
            total_credits=1000.0,
            materiality_threshold=100.0,
            was_balanced=True,
        )
        db_session.add(log)
        db_session.flush()
        assert log.user_id == user.id
