"""Sprint 897 (O-2): concurrent upload parses are bounded per process."""

from __future__ import annotations

import threading
import time

import pytest

from shared import parse_concurrency as pc


@pytest.fixture(autouse=True)
def _restore_limit():
    original = (pc.PARSE_CONCURRENCY, pc.PARSE_WAIT_SECONDS)
    yield
    pc.configure(*original)


def test_at_most_n_parses_run_at_once():
    pc.configure(2, wait_seconds=5)
    running = 0
    peak = 0
    lock = threading.Lock()

    @pc.limit_parse_concurrency
    def parse() -> None:
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        time.sleep(0.05)
        with lock:
            running -= 1

    threads = [threading.Thread(target=parse) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert peak == 2


def test_no_slot_in_time_answers_503_with_retry_after():
    pc.configure(1, wait_seconds=0.05)
    release = threading.Event()
    started = threading.Event()

    def hold() -> None:
        with pc.parse_slot():
            started.set()
            release.wait(2)

    holder = threading.Thread(target=hold)
    holder.start()
    started.wait(2)
    try:
        with pytest.raises(pc.ParseCapacityExceeded) as exc:
            with pc.parse_slot():
                pass
        assert exc.value.status_code == 503
        assert exc.value.headers["Retry-After"]
    finally:
        release.set()
        holder.join()


def test_nested_guarded_calls_do_not_deadlock():
    pc.configure(1, wait_seconds=0.2)

    @pc.limit_parse_concurrency
    def inner() -> str:
        return "ok"

    @pc.limit_parse_concurrency
    def outer() -> str:
        return inner()

    assert outer() == "ok"
    # The slot is released afterwards.
    with pc.parse_slot():
        pass


def test_slot_released_when_parse_raises():
    pc.configure(1, wait_seconds=0.2)

    @pc.limit_parse_concurrency
    def broken() -> None:
        raise ValueError("bad file")

    with pytest.raises(ValueError):
        broken()
    with pc.parse_slot():
        pass


def test_upload_and_tb_entry_points_are_guarded():
    from audit.pipeline import audit_trial_balance_multi_sheet, audit_trial_balance_streaming
    from shared.upload_pipeline import parse_uploaded_file_by_format

    for fn in (parse_uploaded_file_by_format, audit_trial_balance_streaming, audit_trial_balance_multi_sheet):
        assert getattr(fn, "__wrapped__", None) is not None, f"{fn.__name__} is not behind the parse limit"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 2), ("3", 3), ("0", 2), ("-1", 2), ("abc", 2)],
)
def test_concurrency_env_parsing(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv("UPLOAD_PARSE_CONCURRENCY", raising=False)
    else:
        monkeypatch.setenv("UPLOAD_PARSE_CONCURRENCY", raw)
    assert pc._read_int("UPLOAD_PARSE_CONCURRENCY", pc.DEFAULT_PARSE_CONCURRENCY) == expected
