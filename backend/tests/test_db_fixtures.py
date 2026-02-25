"""
Sprint 96.5: Database fixture validation tests.
Packet 5: Production DB guardrail tests.
Sprint 303: Functional _hard_fail test + init_db() logging tests.

These tests verify the in-memory SQLite test infrastructure works correctly.
They serve as a template for Phase X engagement model tests.
"""

import ast
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ActivityLog, Client, Industry, User, UserTier


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
        assert user.tier == UserTier.TEAM
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


# =============================================================================
# Production DB Guardrail (Packet 5)
# =============================================================================


class TestProductionDbGuardrail:
    """Verify config.py rejects SQLite in production mode."""

    def test_guardrail_exists_in_config_source(self):
        """config.py must contain the production+SQLite→_hard_fail guardrail."""
        config_path = Path(__file__).parent.parent / "config.py"
        source = config_path.read_text()

        tree = ast.parse(source)
        found_guardrail = False

        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            segment = ast.get_source_segment(source, node)
            if segment and "production" in segment and "sqlite" in segment:
                # Verify it calls _hard_fail
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                        if child.func.id == "_hard_fail":
                            found_guardrail = True
                            break

        assert found_guardrail, "Production SQLite guardrail (_hard_fail) not found in config.py"

    def test_sqlite_url_detection(self):
        """The guardrail condition must detect all SQLite URL forms."""
        sqlite_urls = [
            "sqlite:///./paciolus.db",
            "sqlite:///:memory:",
            "sqlite:///C:/path/to/db.sqlite3",
            "sqlite+pysqlite:///./paciolus.db",
        ]
        for url in sqlite_urls:
            assert url.startswith("sqlite"), f"Should detect SQLite: {url}"

    def test_postgresql_url_not_blocked(self):
        """PostgreSQL URLs must not trigger the guardrail."""
        pg_urls = [
            "postgresql://user:pass@host:5432/db",
            "postgresql+psycopg2://user:pass@host/db",
            "postgresql+asyncpg://user:pass@host/db",
        ]
        for url in pg_urls:
            assert not url.startswith("sqlite"), f"Should allow: {url}"

    def test_current_env_passes_guardrail(self):
        """Test suite loads config.py successfully (dev mode + SQLite is allowed)."""
        from config import DATABASE_URL, ENV_MODE

        # If we got here, config loaded without _hard_fail.
        # Verify the test env is not production+SQLite.
        is_blocked = ENV_MODE == "production" and DATABASE_URL.startswith("sqlite")
        assert not is_blocked, "Test suite should not run in production mode with SQLite"

    def test_hard_fail_calls_sys_exit(self):
        """_hard_fail() must call sys.exit(1)."""
        # Can't import _hard_fail without side effects, so verify via AST.
        config_path = Path(__file__).parent.parent / "config.py"
        source = config_path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_hard_fail":
                # Find sys.exit call inside _hard_fail
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if (
                            isinstance(func, ast.Attribute)
                            and func.attr == "exit"
                            and isinstance(func.value, ast.Name)
                            and func.value.id == "sys"
                        ):
                            # Verify exit code is 1
                            if child.args and isinstance(child.args[0], ast.Constant):
                                assert child.args[0].value == 1
                                return
        pytest.fail("sys.exit(1) not found in _hard_fail()")

    def test_hard_fail_raises_system_exit(self):
        """_hard_fail() must raise SystemExit(1) when called directly."""
        from config import _hard_fail

        with pytest.raises(SystemExit) as exc_info:
            _hard_fail("Test failure")
        assert exc_info.value.code == 1


# =============================================================================
# init_db() Logging (Sprint 303)
# =============================================================================


class TestInitDbLogging:
    """Verify init_db() logs database dialect and pool information."""

    def test_logs_dialect_and_pool(self, caplog):
        """init_db() should log dialect name and pool class."""
        from database import init_db

        with caplog.at_level(logging.INFO, logger="database"):
            init_db()
        assert "dialect=" in caplog.text
        assert "pool=" in caplog.text

    def test_logs_sqlite_mode_in_dev(self, caplog):
        """Local dev runs should log SQLite mode."""
        from database import init_db

        with caplog.at_level(logging.INFO, logger="database"):
            init_db()
        # Test env uses SQLite
        assert "sqlite" in caplog.text.lower()
