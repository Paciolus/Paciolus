"""The nightly's timeout budgets must nest, and must report a timeout honestly.

Run from project root:  ``python -m pytest scripts/overnight/tests/``

Lesson 674 called a nightly pytest subprocess timeout "a ticking clock, not a
background concern". The clock is real but not yet close — measured
2026-10-22:

===========================  =======  ===========  =========
Budget                       Seconds  Observed     Headroom
===========================  =======  ===========  =========
qa_warden inner pytest          1200      690.7s       1.74x
coverage_sentinel pytest+cov    1500    ~900-1035s    ~1.45x
orchestrator per-agent          1700      757.2s       2.25x
===========================  =======  ===========  =========

At 9,126 collected tests and ~76 ms/test the inner pytest budget is reached
near ~15,800 tests, and coverage_sentinel's (1.3-1.5x slower with
instrumentation) near ~14,000 — the nearer of the two.

What this file pins is the part that can break silently: the **ordering**. If
the inner budget ever exceeds the outer one, the agent is killed before it can
say why it was slow, and the brief degrades from "pytest exceeded its budget"
to "the agent died". Both are RED, but only one is actionable at 02:00.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Project root on sys.path so the `scripts` namespace package imports cleanly,
# matching the other suites in this directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.overnight import orchestrator  # noqa: E402
from scripts.overnight.agents import coverage_sentinel, qa_warden  # noqa: E402


def test_qa_warden_inner_budgets_fit_inside_its_outer_budget():
    outer = orchestrator.AGENT_TIMEOUT_OVERRIDES["qa_warden"]
    inner_total = qa_warden.PYTEST_TIMEOUT_S + qa_warden.JEST_TIMEOUT_S
    assert inner_total < outer, (
        f"qa_warden's inner budgets total {inner_total}s against an outer budget of "
        f"{outer}s. The orchestrator would kill the agent before pytest's own timeout "
        f"could report what was slow."
    )
    assert outer - inner_total >= 120, (
        f"only {outer - inner_total}s of margin between qa_warden's inner budgets and its "
        f"outer one — too little for interpreter start-up and result writing."
    )


def test_coverage_sentinel_inner_budget_fits_inside_its_outer_budget():
    outer = orchestrator.AGENT_TIMEOUT_OVERRIDES["coverage_sentinel"]
    inner = coverage_sentinel.PYTEST_TIMEOUT_S
    assert inner < outer, (
        f"coverage_sentinel's pytest budget ({inner}s) is not inside its outer budget "
        f"({outer}s)."
    )


def test_every_agent_with_a_long_inner_budget_has_an_override():
    """An agent whose work exceeds the default must say so in one place.

    `DEFAULT_AGENT_TIMEOUT_S` is 900s. Both suite-running agents need more,
    and both are listed. A third one added without an override would be
    killed mid-run and reported as a crash.
    """
    default = orchestrator.DEFAULT_AGENT_TIMEOUT_S
    for name, inner in (
        ("qa_warden", qa_warden.PYTEST_TIMEOUT_S + qa_warden.JEST_TIMEOUT_S),
        ("coverage_sentinel", coverage_sentinel.PYTEST_TIMEOUT_S),
    ):
        if inner >= default:
            assert name in orchestrator.AGENT_TIMEOUT_OVERRIDES, (
                f"{name} needs {inner}s but has no entry in AGENT_TIMEOUT_OVERRIDES, so it "
                f"runs on the {default}s default and will be killed."
            )


def test_a_timed_out_backend_run_reports_did_not_run_not_a_pass(monkeypatch):
    """Three outcomes, not two.

    Before Sprint 802 the inner `subprocess.run(..., timeout=1200)` had no
    handler, so a timeout propagated and the agent crashed. The brief was
    still honest — `briefing_compiler` renders a missing agent as RED with
    `DID_NOT_RUN` — but it could not say *why*. The important property is the
    one asserted here: a timeout must never be summarised as 0 failed, which
    the status classifier would read as green.
    """
    def _boom(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=qa_warden.PYTEST_TIMEOUT_S)

    monkeypatch.setattr(qa_warden.subprocess, "run", _boom)
    # Ensure the stale-json-report branch cannot short-circuit the call.
    monkeypatch.setattr(
        qa_warden, "REPORTS_DIR", Path(__file__).resolve().parent / "__nonexistent__"
    )

    result = qa_warden._run_backend_tests()

    assert result["collection_error"], (
        "a timed-out pytest run produced no collection_error — the status classifier "
        "treats 0 passed / 0 failed with no error as GREEN"
    )
    assert "budget" in result["collection_error"].lower()
    assert result["passed"] == 0 and result["failed"] == 0


def test_the_timeout_message_names_both_constants_that_must_move_together():
    """Raising one budget without the other re-breaks the nesting.

    The error message is the only place a 02:00 reader will look, so it has
    to name the second edit rather than letting them discover it next month.
    """
    import inspect

    source = inspect.getsource(qa_warden._run_backend_tests)
    assert "PYTEST_TIMEOUT_S" in source
    assert "AGENT_TIMEOUT_OVERRIDES" in source, (
        "the timeout message should tell the reader that the orchestrator's outer budget "
        "has to move too"
    )
