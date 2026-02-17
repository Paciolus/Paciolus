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
from sqlalchemy.orm import Session, sessionmaker

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Base
from engagement_model import Engagement, EngagementStatus, MaterialityBasis, ToolName, ToolRun, ToolRunStatus
from follow_up_items_model import FollowUpDisposition, FollowUpItem, FollowUpItemComment, FollowUpSeverity
from models import Client, Industry, RefreshToken, User, UserTier

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

    # Enable FK constraints for SQLite (required for ON DELETE RESTRICT/CASCADE)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
# Rate limiter fixture — centralized (post-release stabilization)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _disable_rate_limiter():
    """Disable SlowAPI rate limiter for all tests by default.

    SlowAPI's in-memory backend accumulates hits across tests in the same
    process, causing spurious 429s when a test file has more requests than the
    endpoint's per-minute limit.  Disabling globally keeps API integration
    tests deterministic.

    Tests that explicitly need to validate 429 behaviour can re-enable via:
        limiter.enabled = True   (in their own fixture or setup)
    """
    from shared.rate_limits import limiter
    limiter.enabled = False
    yield
    limiter.enabled = True


# ---------------------------------------------------------------------------
# CSRF token fixture (Sprint 200, refactored Sprint 245)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def bypass_csrf():
    """Bypass CSRF middleware validation in API integration tests.

    Sprint 200: CSRF middleware blocks mutation requests without a valid token.
    Sprint 245: Made opt-in (removed autouse=True). Apply via:
        @pytest.mark.usefixtures("bypass_csrf")

    API tests that make POST/PUT/DELETE via httpx.AsyncClient need this.
    CSRF is tested explicitly in test_csrf_middleware.py (which imports
    validate_csrf_token directly, so this patch does NOT affect it).
    """
    import security_middleware
    original = security_middleware.validate_csrf_token
    security_middleware.validate_csrf_token = lambda token: True
    yield
    security_middleware.validate_csrf_token = original


# ---------------------------------------------------------------------------
# Auth override fixture (Sprint 245)
# ---------------------------------------------------------------------------

@pytest.fixture()
def override_auth_verified(db_session):
    """Override require_verified_user + get_db for route integration tests.

    Creates a verified user and overrides FastAPI dependencies.
    Clears overrides after test. New API tests should use this fixture
    instead of duplicating the override pattern.
    """
    from auth import require_verified_user
    from database import get_db
    from main import app

    user = User(
        email="fixture_verified@example.com",
        name="Fixture Verified User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    yield user
    app.dependency_overrides.clear()


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
def make_engagement(db_session: Session, make_client):
    """Factory fixture that creates Engagement records in the test DB."""
    from datetime import UTC, datetime

    def _make_engagement(
        client: Client | None = None,
        user: User | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        status: EngagementStatus = EngagementStatus.ACTIVE,
        materiality_basis: MaterialityBasis | None = None,
        materiality_percentage: float | None = None,
        materiality_amount: float | None = None,
        performance_materiality_factor: float = 0.75,
        trivial_threshold_factor: float = 0.05,
    ) -> Engagement:
        if client is None:
            if user is not None:
                client = make_client(user=user)
            else:
                client = make_client()
        created_by = client.user_id
        if period_start is None:
            period_start = datetime(2025, 1, 1, tzinfo=UTC)
        if period_end is None:
            period_end = datetime(2025, 12, 31, tzinfo=UTC)

        engagement = Engagement(
            client_id=client.id,
            period_start=period_start,
            period_end=period_end,
            status=status,
            materiality_basis=materiality_basis,
            materiality_percentage=materiality_percentage,
            materiality_amount=materiality_amount,
            performance_materiality_factor=performance_materiality_factor,
            trivial_threshold_factor=trivial_threshold_factor,
            created_by=created_by,
        )
        db_session.add(engagement)
        db_session.flush()
        return engagement

    return _make_engagement


@pytest.fixture()
def make_tool_run(db_session: Session, make_engagement):
    """Factory fixture that creates ToolRun records in the test DB."""

    def _make_tool_run(
        engagement: Engagement | None = None,
        tool_name: ToolName = ToolName.TRIAL_BALANCE,
        run_number: int = 1,
        status: ToolRunStatus = ToolRunStatus.COMPLETED,
        composite_score: float | None = None,
    ) -> ToolRun:
        if engagement is None:
            engagement = make_engagement()
        tool_run = ToolRun(
            engagement_id=engagement.id,
            tool_name=tool_name,
            run_number=run_number,
            status=status,
            composite_score=composite_score,
        )
        db_session.add(tool_run)
        db_session.flush()
        return tool_run

    return _make_tool_run


@pytest.fixture()
def make_follow_up_item(db_session: Session, make_engagement):
    """Factory fixture that creates FollowUpItem records in the test DB."""

    def _make_follow_up_item(
        engagement: Engagement | None = None,
        tool_run: ToolRun | None = None,
        description: str = "Test follow-up item",
        tool_source: str = "trial_balance",
        severity: FollowUpSeverity = FollowUpSeverity.MEDIUM,
        disposition: FollowUpDisposition = FollowUpDisposition.NOT_REVIEWED,
        auditor_notes: str | None = None,
    ) -> FollowUpItem:
        if engagement is None:
            engagement = make_engagement()
        item = FollowUpItem(
            engagement_id=engagement.id,
            tool_run_id=tool_run.id if tool_run else None,
            description=description,
            tool_source=tool_source,
            severity=severity,
            disposition=disposition,
            auditor_notes=auditor_notes,
        )
        db_session.add(item)
        db_session.flush()
        return item

    return _make_follow_up_item


@pytest.fixture()
def make_comment(db_session: Session, make_follow_up_item, make_user):
    """Factory fixture that creates FollowUpItemComment records in the test DB."""

    def _make_comment(
        follow_up_item: FollowUpItem | None = None,
        user: User | None = None,
        comment_text: str = "Test comment",
        parent_comment_id: int | None = None,
    ) -> FollowUpItemComment:
        if follow_up_item is None:
            follow_up_item = make_follow_up_item()
        if user is None:
            user = make_user(email=f"commenter_{id(follow_up_item)}@example.com")
        comment = FollowUpItemComment(
            follow_up_item_id=follow_up_item.id,
            user_id=user.id,
            comment_text=comment_text,
            parent_comment_id=parent_comment_id,
        )
        db_session.add(comment)
        db_session.flush()
        return comment

    return _make_comment


@pytest.fixture()
def make_refresh_token(db_session: Session, make_user):
    """Factory fixture that creates RefreshToken records in the test DB."""
    import hashlib
    import secrets
    from datetime import UTC, datetime, timedelta

    def _make_refresh_token(
        user: User | None = None,
        token_hash: str | None = None,
        expires_at: datetime | None = None,
        revoked_at: datetime | None = None,
        replaced_by_hash: str | None = None,
    ) -> tuple[str, RefreshToken]:
        if user is None:
            user = make_user(email=f"refresh_{secrets.token_hex(4)}@example.com")
        raw_token = secrets.token_urlsafe(48)
        if token_hash is None:
            token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        if expires_at is None:
            expires_at = datetime.now(UTC) + timedelta(days=7)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked_at=revoked_at,
            replaced_by_hash=replaced_by_hash,
        )
        db_session.add(rt)
        db_session.flush()
        return raw_token, rt

    return _make_refresh_token


@pytest.fixture()
def sample_user(make_user) -> User:
    """Convenience fixture: a single pre-made user."""
    return make_user()


@pytest.fixture()
def sample_client(make_client) -> Client:
    """Convenience fixture: a single pre-made client."""
    return make_client()
