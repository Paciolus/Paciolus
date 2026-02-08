"""
Shared pytest fixtures for Paciolus backend tests.
Sprint 96.5: Database test infrastructure for Phase X engagement layer.

Provides:
- In-memory SQLite database engine and session fixtures
- Transaction rollback pattern (each test gets a clean DB)
- Factory fixtures for User and Client models
"""

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Base
from models import User, Client, Industry, UserTier


# ---------------------------------------------------------------------------
# Engine & session fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_engine():
    """Create a single in-memory SQLite engine shared across the test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """
    Provide a transactional database session that rolls back after each test.

    Pattern: open a connection, begin a transaction, bind a session to it.
    After the test, roll back the transaction so every test starts clean.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    # If the test code itself calls session.commit(), we need to restart
    # the nested savepoint so that our outer rollback still works.
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if trans.nested and not trans._parent.nested:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def make_user(db_session: Session):
    """Factory fixture that creates User records in the test DB."""

    def _make_user(
        email: str = "test@example.com",
        name: str = "Test User",
        hashed_password: str = "$2b$12$fakehashvalue",
        tier: UserTier = UserTier.PROFESSIONAL,
        is_active: bool = True,
        is_verified: bool = True,
    ) -> User:
        user = User(
            email=email,
            name=name,
            hashed_password=hashed_password,
            tier=tier,
            is_active=is_active,
            is_verified=is_verified,
        )
        db_session.add(user)
        db_session.flush()  # Assigns ID without committing
        return user

    return _make_user


@pytest.fixture()
def make_client(db_session: Session, make_user):
    """Factory fixture that creates Client records in the test DB."""

    def _make_client(
        name: str = "Acme Corp",
        industry: Industry = Industry.TECHNOLOGY,
        fiscal_year_end: str = "12-31",
        user: User | None = None,
    ) -> Client:
        if user is None:
            user = make_user()
        client = Client(
            user_id=user.id,
            name=name,
            industry=industry,
            fiscal_year_end=fiscal_year_end,
        )
        db_session.add(client)
        db_session.flush()
        return client

    return _make_client


@pytest.fixture()
def sample_user(make_user) -> User:
    """Convenience fixture: a single pre-made user."""
    return make_user()


@pytest.fixture()
def sample_client(make_client) -> Client:
    """Convenience fixture: a single pre-made client."""
    return make_client()
