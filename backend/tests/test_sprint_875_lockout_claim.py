"""Sprint 875: concurrent wrong passwords cannot exceed the lockout limit.

The login pipeline used to read the lockout state, run bcrypt (~250 ms) and only
then add one to the failure counter in Python. N concurrent guesses all passed
the check before any was counted, and lost increments to each other, so an
attacker got hundreds of guesses per 15-minute lockout instead of five. The
attempt is now claimed atomically in the database before bcrypt runs.
"""

import pytest
from fastapi import HTTPException

from auth import hash_password
from security_middleware import (
    MAX_FAILED_ATTEMPTS,
    claim_login_attempt,
    reset_failed_attempts,
    reset_ip_failures,
)
from services.auth.identity import authenticate_login

PASSWORD = "Correct-Horse-9-Battery"
IP = "198.51.100.77"


@pytest.fixture
def user(make_user, db_session):
    u = make_user(email="sprint875@example.com", hashed_password=hash_password(PASSWORD))
    u.failed_login_attempts = 0
    u.locked_until = None
    db_session.commit()
    reset_ip_failures(IP)
    yield u
    reset_ip_failures(IP)


def _login(db_session, password: str):
    return authenticate_login(
        db_session, email="sprint875@example.com", password=password, client_ip=IP, user_agent=None, request_host=None
    )


def test_claims_stop_at_the_limit_however_many_arrive(db_session, user):
    """N attempts in flight at once: exactly MAX_FAILED_ATTEMPTS get a password check."""
    granted = [claim_login_attempt(db_session, user.id) for _ in range(MAX_FAILED_ATTEMPTS + 20)]
    assert granted.count(True) == MAX_FAILED_ATTEMPTS
    assert granted[:MAX_FAILED_ATTEMPTS] == [True] * MAX_FAILED_ATTEMPTS


def test_while_the_slots_are_taken_even_the_right_password_is_refused(db_session, user):
    for _ in range(MAX_FAILED_ATTEMPTS):
        assert claim_login_attempt(db_session, user.id)
    with pytest.raises(HTTPException) as exc:
        _login(db_session, PASSWORD)
    assert exc.value.status_code == 401
    db_session.refresh(user)
    assert user.locked_until is not None  # the refusal applies the lock


def test_sequential_wrong_passwords_lock_then_refuse_the_right_one(db_session, user):
    for _ in range(MAX_FAILED_ATTEMPTS):
        with pytest.raises(HTTPException):
            _login(db_session, "wrong-password")
    db_session.refresh(user)
    assert user.failed_login_attempts == MAX_FAILED_ATTEMPTS  # counted once each, not twice
    assert user.locked_until is not None
    reset_ip_failures(IP)  # isolate the per-user lock from the per-IP block
    with pytest.raises(HTTPException):
        _login(db_session, PASSWORD)


def test_a_success_resets_the_counter(db_session, user):
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        with pytest.raises(HTTPException):
            _login(db_session, "wrong-password")
    issuance = _login(db_session, PASSWORD)
    assert issuance.access_token
    db_session.refresh(user)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_reset_after_lock_restores_claims(db_session, user):
    for _ in range(MAX_FAILED_ATTEMPTS):
        claim_login_attempt(db_session, user.id)
    assert not claim_login_attempt(db_session, user.id)
    reset_failed_attempts(db_session, user.id)
    assert claim_login_attempt(db_session, user.id)


# ---------------------------------------------------------------------------
# Independent review of PR #328: real concurrency, lock expiry, unknown emails
# ---------------------------------------------------------------------------


@pytest.fixture
def file_db(tmp_path):
    """A file-backed SQLite database so each thread gets its own connection."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database import Base
    from models import User

    engine = create_engine(f"sqlite:///{tmp_path / 'lockout.db'}", connect_args={"timeout": 30})
    Base.metadata.create_all(engine)
    make = sessionmaker(bind=engine)
    with make() as s:
        u = User(email="race875@example.com", hashed_password="x", is_active=True, is_verified=True)
        s.add(u)
        s.commit()
        uid = u.id
    yield make, uid
    engine.dispose()


def test_threads_racing_on_their_own_connections_get_exactly_the_limit(file_db):
    import threading

    make, uid = file_db
    n = 20
    barrier = threading.Barrier(n)
    results: list[bool] = []
    lock = threading.Lock()

    def worker():
        with make() as s:
            barrier.wait()
            granted = claim_login_attempt(s, uid)
        with lock:
            results.append(granted)

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count(True) == MAX_FAILED_ATTEMPTS


def test_expired_lock_resets_and_a_stale_reset_cannot_wipe_new_claims(file_db):
    from datetime import UTC, datetime, timedelta

    from models import User
    from security_middleware import check_lockout_status

    make, uid = file_db
    with make() as s:
        u = s.get(User, uid)
        u.failed_login_attempts = MAX_FAILED_ATTEMPTS
        u.locked_until = datetime.now(UTC) - timedelta(minutes=1)
        s.commit()

    stale = make()
    stale_user = stale.get(User, uid)  # reads the expired lock and keeps it in its identity map
    assert stale_user.locked_until is not None

    with make() as fresh:  # another request: resets the expired lock, then claims three slots
        assert check_lockout_status(fresh, uid)[0] is False
        for _ in range(3):
            assert claim_login_attempt(fresh, uid)

    assert check_lockout_status(stale, uid)[0] is False  # the stale request's reset matches nothing now
    stale.close()
    with make() as s:
        u = s.get(User, uid)
        assert u.locked_until is None
        assert u.failed_login_attempts == 3  # the three claims survived


def test_unknown_email_touches_no_account(db_session, user):
    with pytest.raises(HTTPException) as exc:
        authenticate_login(
            db_session, email="nobody875@example.com", password="x", client_ip=IP, user_agent=None, request_host=None
        )
    assert exc.value.status_code == 401
    db_session.refresh(user)
    assert user.failed_login_attempts == 0
