"""
Tests for shared.db_unit_of_work (Sprint 745).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from shared.db_unit_of_work import db_transaction


def test_commits_on_clean_exit() -> None:
    db = MagicMock()
    with db_transaction(db, log_label="test_clean"):
        db.add("thing")
    db.add.assert_called_once_with("thing")
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_rolls_back_and_raises_500_on_sqlalchemy_error() -> None:
    db = MagicMock()
    db.commit.side_effect = OperationalError("stmt", {}, Exception("conn dropped"))

    with pytest.raises(HTTPException) as excinfo:
        with db_transaction(db, log_label="test_rollback"):
            db.add("thing")

    assert excinfo.value.status_code == 500
    db.rollback.assert_called_once()


def test_propagates_non_sqlalchemy_exception_without_rollback() -> None:
    """ValueError from caller code must propagate; commit/rollback skipped."""
    db = MagicMock()

    with pytest.raises(ValueError, match="business logic"):
        with db_transaction(db, log_label="test_propagate"):
            raise ValueError("business logic")

    db.commit.assert_not_called()
    db.rollback.assert_not_called()


def test_rollback_runs_on_integrity_error_during_commit() -> None:
    db = MagicMock()
    db.commit.side_effect = IntegrityError("stmt", {}, Exception("FK violation"))

    with pytest.raises(HTTPException) as excinfo:
        with db_transaction(db, log_label="test_integrity"):
            pass

    assert excinfo.value.status_code == 500
    db.rollback.assert_called_once()


def test_sanitized_detail_does_not_leak_sql() -> None:
    db = MagicMock()
    db.commit.side_effect = SQLAlchemyError("INSERT INTO users (email) VALUES ('leak@example.com') failed")

    with pytest.raises(HTTPException) as excinfo:
        with db_transaction(db, log_label="test_sanitize"):
            pass

    detail = excinfo.value.detail
    assert isinstance(detail, str)
    assert "INSERT" not in detail
    assert "leak@example.com" not in detail


def test_log_message_override_is_used(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    db = MagicMock()
    db.commit.side_effect = OperationalError("stmt", {}, Exception("dropped"))

    with caplog.at_level(logging.ERROR, logger="shared.db_unit_of_work"):
        with pytest.raises(HTTPException):
            with db_transaction(
                db,
                log_label="test_label",
                log_message="custom message goes here",
            ):
                pass

    assert any("custom message goes here" in r.message for r in caplog.records)


def test_default_log_message_uses_label(caplog: pytest.LogCaptureFixture) -> None:
    import logging

    db = MagicMock()
    db.commit.side_effect = OperationalError("stmt", {}, Exception("dropped"))

    with caplog.at_level(logging.ERROR, logger="shared.db_unit_of_work"):
        with pytest.raises(HTTPException):
            with db_transaction(db, log_label="my_op"):
                pass

    assert any("my_op" in r.message for r in caplog.records)
