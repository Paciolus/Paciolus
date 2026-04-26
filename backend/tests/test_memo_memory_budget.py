"""Sprint 722 — memory budget probe + soft threshold.

Tests the ``shared.memory_budget`` module that wraps every memo generator in
``routes.export_memos._memo_export_handler``. The prevention story is:

- ``track_memo_memory`` always calls ``gc.collect()`` in the ``finally`` block
  (a removal regresses ``test_gc_collect_runs_on_normal_exit`` and
  ``test_gc_collect_runs_on_exception``).
- Threshold breaches emit a Sentry warning + breadcrumb (regressed by
  ``test_threshold_breach_emits_sentry_warning``).
- Repeated invocations of a representative memo generator stay bounded; if the
  ``gc.collect()`` is removed or the generator leaks, RSS grows monotonically
  past the soft headroom budget. Catches regressions that ``maxRequestsPerWorker``
  alone would mask in production.
"""

from __future__ import annotations

import gc
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import memory_budget
from shared.memory_budget import get_rss_mb, track_memo_memory

# ---------------------------------------------------------------------------
# Probe correctness
# ---------------------------------------------------------------------------


class TestGetRssMb:
    def test_returns_positive_float(self):
        rss = get_rss_mb()
        assert isinstance(rss, float)
        assert rss > 0

    def test_grows_after_known_allocation(self):
        before = get_rss_mb()
        # Allocate ~50 MB and hold the reference so it can't be reclaimed.
        ballast = bytearray(50 * 1024 * 1024)
        after = get_rss_mb()
        # Don't tighten the bound — Python may pre-allocate / arenas vary.
        # Just assert RSS rose by at least 10 MB (much less than the 50 MB we asked for).
        assert after - before > 10
        # Keep ``ballast`` alive past the assertion.
        assert len(ballast) == 50 * 1024 * 1024


# ---------------------------------------------------------------------------
# Logging contract
# ---------------------------------------------------------------------------


class TestLoggingContract:
    def test_emits_before_and_after_lines(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger=memory_budget.logger.name):
            with track_memo_memory("Test memo"):
                pass

        before_records = [r for r in caplog.records if r.message.startswith("memo.memory.before")]
        after_records = [r for r in caplog.records if r.message.startswith("memo.memory.after")]
        assert len(before_records) == 1
        assert len(after_records) == 1
        assert "label=Test memo" in before_records[0].message
        assert "label=Test memo" in after_records[0].message
        assert "delta_mb=" in after_records[0].message
        assert "elapsed_ms=" in after_records[0].message

    def test_after_log_emits_on_exception(self, caplog: pytest.LogCaptureFixture):
        with caplog.at_level(logging.INFO, logger=memory_budget.logger.name):
            with pytest.raises(ValueError, match="boom"):
                with track_memo_memory("Failing memo"):
                    raise ValueError("boom")

        after_records = [r for r in caplog.records if r.message.startswith("memo.memory.after")]
        assert len(after_records) == 1, "after-log must emit even when generator raises"


# ---------------------------------------------------------------------------
# gc.collect runs unconditionally
# ---------------------------------------------------------------------------


class TestGcCollectRuns:
    def test_gc_collect_runs_on_normal_exit(self, monkeypatch: pytest.MonkeyPatch):
        calls: list[None] = []
        original_collect = gc.collect

        def _spy_collect(*args, **kwargs):
            calls.append(None)
            return original_collect(*args, **kwargs)

        monkeypatch.setattr(memory_budget.gc, "collect", _spy_collect)
        with track_memo_memory("Normal-exit memo"):
            pass
        assert len(calls) == 1, "gc.collect must run exactly once on normal exit"

    def test_gc_collect_runs_on_exception(self, monkeypatch: pytest.MonkeyPatch):
        calls: list[None] = []
        original_collect = gc.collect

        def _spy_collect(*args, **kwargs):
            calls.append(None)
            return original_collect(*args, **kwargs)

        monkeypatch.setattr(memory_budget.gc, "collect", _spy_collect)
        with pytest.raises(RuntimeError, match="kaboom"):
            with track_memo_memory("Failing memo"):
                raise RuntimeError("kaboom")
        assert len(calls) == 1, "gc.collect must still run when generator raises"


# ---------------------------------------------------------------------------
# Threshold breach → Sentry warning
# ---------------------------------------------------------------------------


class _FakeScope:
    """Minimal stand-in for ``sentry_sdk.push_scope()`` used by the probe."""

    def __init__(self, sink: dict[str, object]):
        self._sink = sink

    def set_tag(self, k: str, v: object) -> None:
        self._sink.setdefault("tags", {})[k] = v  # type: ignore[index]

    def set_extra(self, k: str, v: object) -> None:
        self._sink.setdefault("extras", {})[k] = v  # type: ignore[index]


class _FakeSentry:
    def __init__(self):
        self.breadcrumbs: list[dict] = []
        self.captured: list[tuple[str, str]] = []
        self.scope_state: dict[str, object] = {}

    def add_breadcrumb(self, **kwargs):
        self.breadcrumbs.append(kwargs)

    def push_scope(self):
        scope = _FakeScope(self.scope_state)

        class _Ctx:
            def __enter__(self_):
                return scope

            def __exit__(self_, *exc):
                return False

        return _Ctx()

    def capture_message(self, msg: str, level: str = "info"):
        self.captured.append((msg, level))


class TestThresholdBreach:
    def test_threshold_breach_emits_sentry_warning(self, monkeypatch: pytest.MonkeyPatch):
        # Force every invocation to breach by setting threshold to 1 MB.
        monkeypatch.setenv("MEMO_RSS_WARN_MB", "1")
        fake = _FakeSentry()
        monkeypatch.setitem(sys.modules, "sentry_sdk", fake)

        with track_memo_memory("Over-budget memo"):
            pass

        assert len(fake.captured) == 1
        msg, level = fake.captured[0]
        assert level == "warning"
        assert "Over-budget memo" in msg
        assert any(b.get("category") == "memo.memory" for b in fake.breadcrumbs)

    def test_under_threshold_no_sentry_emit(self, monkeypatch: pytest.MonkeyPatch):
        # 100 GB threshold — never breached on this host.
        monkeypatch.setenv("MEMO_RSS_WARN_MB", "100000")
        fake = _FakeSentry()
        monkeypatch.setitem(sys.modules, "sentry_sdk", fake)

        with track_memo_memory("Under-budget memo"):
            pass

        assert fake.captured == []
        assert fake.breadcrumbs == []

    def test_invalid_threshold_falls_back_to_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MEMO_RSS_WARN_MB", "not-a-number")
        # Should not raise — falls back to 1500.
        with track_memo_memory("Resilient memo"):
            pass

    def test_zero_threshold_falls_back_to_default(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MEMO_RSS_WARN_MB", "0")
        with track_memo_memory("Resilient memo"):
            pass


# ---------------------------------------------------------------------------
# Bounded RSS across repeated memo generations (the prevention story)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestRepeatedGenerationStaysBounded:
    """Generate a representative memo 5 times and assert RSS doesn't grow unboundedly.

    Marked ``slow`` so it only runs in nightly CI, not on every PR. The 100 MB
    growth budget is generous — a leak that ``gc.collect()`` papers over today
    would still trip this once it crosses the threshold.
    """

    def test_je_memo_repeated_generation(self):
        # Reuse the canonical fixture builder from the JE memo's own test suite —
        # avoids drift between this regression test and the generator's contract.
        from je_testing_memo_generator import generate_je_testing_memo
        from tests.test_je_testing_memo import _make_je_result

        je_result = _make_je_result()
        common_kwargs = {
            "filename": "test.xlsx",
            "client_name": "Test Client",
            "period_tested": "FY2025",
            "prepared_by": "Tester",
            "reviewed_by": "Reviewer",
            "workpaper_date": "2026-01-01",
            "source_document_title": "Trial Balance",
            "source_context_note": "Test context",
            "fiscal_year_end": "2025-12-31",
            "include_signoff": True,
        }

        rss_after_each: list[float] = []
        for i in range(5):
            with track_memo_memory(f"JE memo iteration {i}"):
                pdf_bytes = generate_je_testing_memo(je_result=je_result, **common_kwargs)
                assert pdf_bytes  # generator produced output
                assert pdf_bytes[:4] == b"%PDF"
            rss_after_each.append(get_rss_mb())

        # First→last growth must stay under 100 MB after the gc sweep.
        # Looser headroom isn't needed; a real leak swamps this fast.
        growth = rss_after_each[-1] - rss_after_each[0]
        assert growth < 100, (
            f"RSS grew {growth:.1f} MB across 5 JE memo generations — possible leak. "
            f"Per-iteration RSS: {[f'{v:.0f}' for v in rss_after_each]}"
        )
