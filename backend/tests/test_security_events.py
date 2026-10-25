"""Sprint 840 (claims review S5): security events are logged and kept.

``log_secure_operation`` used to append to an in-memory list nothing read.
These tests pin the replacement: security events reach the ``paciolus.security``
logger with redacted details, the critical ones are persisted to
``security_events``, routine tracing never logs its (often filename-bearing)
details, and a persistence failure never breaks the request.
"""

import logging
from datetime import UTC, datetime, timedelta

from auth import authenticate_user, hash_password
from retention_cleanup import purge_old_security_events
from security_event_model import SECURITY_EVENT_RETENTION_DAYS, SecurityEvent
from security_middleware import MAX_FAILED_ATTEMPTS, record_failed_login
from security_utils import PERSISTED_EVENTS, SECURITY_EVENTS, log_secure_operation


def _events(db, event_type=None):
    q = db.query(SecurityEvent)
    if event_type:
        q = q.filter(SecurityEvent.event_type == event_type)
    return q.all()


class TestPersistence:
    def test_unknown_email_login_is_persisted(self, db_session):
        assert authenticate_user(db_session, "nobody@example.com", "x") is None
        (event,) = _events(db_session, "auth_failed")
        assert event.user_id is None
        assert "nobody@example.com" not in (event.details or "")

    def test_wrong_password_is_persisted_with_the_user(self, db_session, make_user):
        user = make_user(email="sec_evt_pw@example.com", hashed_password=hash_password("Correct-Horse-1"))
        assert authenticate_user(db_session, user.email, "wrong") is None
        (event,) = _events(db_session, "auth_failed")
        assert event.user_id == user.id

    def test_lockout_sequence_is_persisted(self, db_session, make_user):
        user = make_user(email="sec_evt_lock@example.com")
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_login(db_session, user.id)
        assert len(_events(db_session, "login_failed")) == MAX_FAILED_ATTEMPTS - 1
        (locked,) = _events(db_session, "account_locked")
        assert locked.user_id == user.id

    def test_ip_is_hashed_never_stored_raw(self, db_session):
        log_secure_operation("ip_blocked", "Threshold exceeded", db=db_session, ip_address="203.0.113.9")
        (event,) = _events(db_session, "ip_blocked")
        assert event.ip_hash and "203.0.113.9" not in event.ip_hash

    def test_unpersisted_security_event_writes_no_row(self, db_session):
        assert "csrf_blocked" in SECURITY_EVENTS and "csrf_blocked" not in PERSISTED_EVENTS
        log_secure_operation("csrf_blocked", "x", db=db_session)
        assert _events(db_session) == []

    def test_persistence_failure_does_not_raise(self, caplog):
        class _BrokenSession:
            def add(self, _row):
                raise RuntimeError("db down")

            def rollback(self):
                pass

        with caplog.at_level(logging.ERROR, logger="paciolus.security"):
            log_secure_operation("auth_failed", "x", db=_BrokenSession())
        assert "persist failed [RuntimeError]" in caplog.text


class TestLogging:
    def test_security_event_reaches_the_security_logger(self, caplog):
        with caplog.at_level(logging.WARNING, logger="paciolus.security"):
            log_secure_operation("csrf_blocked", "Origin mismatch")
        assert "security_event csrf_blocked" in caplog.text
        assert "Origin mismatch" in caplog.text

    def test_details_are_redacted(self, caplog):
        with caplog.at_level(logging.WARNING, logger="paciolus.security"):
            log_secure_operation(
                "content_sniff_rejected", "File 'Acme Holdings TB 2025.xlsx' from jane.doe@acme.com rejected"
            )
        assert "Acme Holdings" not in caplog.text
        assert "jane.doe@acme.com" not in caplog.text
        assert "'[redacted]'" in caplog.text

    def test_routine_operation_never_logs_its_details(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="paciolus.security"):
            log_secure_operation("pdf_generate_start", "Generating memo for client_acme_tb.xlsx")
        assert "pdf_generate_start" in caplog.text
        assert "client_acme" not in caplog.text

    def test_persisted_events_are_security_events(self):
        assert PERSISTED_EVENTS <= SECURITY_EVENTS


class TestRetention:
    def test_old_events_are_purged_recent_kept(self, db_session):
        old = datetime.now(UTC) - timedelta(days=SECURITY_EVENT_RETENTION_DAYS + 1)
        db_session.add(SecurityEvent(event_type="auth_failed", created_at=old))
        db_session.add(SecurityEvent(event_type="auth_failed"))
        db_session.commit()
        assert purge_old_security_events(db_session) == 1
        assert len(_events(db_session)) == 1
