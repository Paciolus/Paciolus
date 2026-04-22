"""Sprint 712: tests for QA Warden's false-green guard.

The guard must escalate to a populated ``collection_error`` whenever pytest
exits non-zero AND produced no parseable test counts — the exact shape that
caused the 2026-04-22 false-green incident.

Run from project root:  ``python -m pytest scripts/overnight/tests/``
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root on sys.path so the `scripts` package imports cleanly.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.overnight.agents import qa_warden


def _fake_completed(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    mock = MagicMock(spec=subprocess.CompletedProcess)
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


def test_collection_error_populated_on_pytest_exit_2(tmp_path):
    """Collection errors (exit 2) with no summary line → collection_error set."""
    collection_stderr = (
        "ERROR tests/test_metrics_api.py\n"
        "!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!\n"
        "1 warning, 1 error in 2.30s\n"
    )
    fake_result = _fake_completed(returncode=2, stdout="", stderr=collection_stderr)

    # Point json_report at a path that doesn't exist so the fallback regex path is taken.
    with patch.object(qa_warden, "REPORTS_DIR", tmp_path), \
         patch.object(qa_warden.subprocess, "run", return_value=fake_result):
        backend = qa_warden._run_backend_tests()

    assert backend["passed"] == 0
    assert backend["failed"] == 0
    assert backend["errors"] == 0
    assert backend["collection_error"] is not None
    assert "Interrupted" in backend["collection_error"]


def test_no_collection_error_on_clean_pass(tmp_path):
    """Clean pass (exit 0, real summary) → collection_error is None."""
    summary = "\n8046 passed in 421.50s (0:07:01)\n"
    fake_result = _fake_completed(returncode=0, stdout=summary, stderr="")

    with patch.object(qa_warden, "REPORTS_DIR", tmp_path), \
         patch.object(qa_warden.subprocess, "run", return_value=fake_result):
        backend = qa_warden._run_backend_tests()

    assert backend["passed"] == 8046
    assert backend["failed"] == 0
    assert backend["collection_error"] is None


def test_exit_5_no_tests_collected_is_not_escalated(tmp_path):
    """Exit 5 ("no tests collected") is legitimate — don't treat as collection error."""
    fake_result = _fake_completed(returncode=5, stdout="no tests ran in 0.01s\n", stderr="")

    with patch.object(qa_warden, "REPORTS_DIR", tmp_path), \
         patch.object(qa_warden.subprocess, "run", return_value=fake_result):
        backend = qa_warden._run_backend_tests()

    assert backend["passed"] == 0
    assert backend["collection_error"] is None


def test_status_red_when_collection_error_present(tmp_path):
    """run() must escalate to RED when backend carries a collection_error — even
    if failed+errors == 0, which is the exact false-green shape we're guarding."""
    backend = {
        "passed": 0, "failed": 0, "errors": 0,
        "duration_s": 0.0, "failing_tests": [],
        "collection_error": "ERROR tests/test_metrics_api.py\n... 1 error in 2.3s",
    }
    frontend = {"passed": 1848, "failed": 0, "duration_s": 43.9}

    # Isolate baseline I/O to tmp_path so the test doesn't touch real reports.
    fake_baseline = tmp_path / "baseline.json"
    with patch.object(qa_warden, "REPORTS_DIR", tmp_path), \
         patch.object(qa_warden, "BASELINE_FILE", fake_baseline), \
         patch.object(qa_warden, "_run_backend_tests", return_value=backend), \
         patch.object(qa_warden, "_run_frontend_tests", return_value=frontend):
        result = qa_warden.run()

    assert result["status"] == "red"
    assert "collection FAILED" in result["summary"]


def test_venv_python_preferred_when_present(tmp_path):
    """When PYTHON_BIN exists, qa_warden invokes it instead of SYSTEM_PYTHON."""
    # PYTHON_BIN is a real path under the repo — it exists in dev environments
    # that have provisioned the venv. Just assert the resolution logic.
    from scripts.overnight.config import PYTHON_BIN, SYSTEM_PYTHON

    captured: dict = {}

    def _capture(cmd, **kwargs):  # noqa: ARG001
        captured["cmd"] = cmd
        return _fake_completed(returncode=0, stdout="0 passed in 0.1s\n")

    with patch.object(qa_warden, "REPORTS_DIR", tmp_path), \
         patch.object(qa_warden.subprocess, "run", side_effect=_capture):
        qa_warden._run_backend_tests()

    # Whichever python was selected, it must be one of the two canonical paths —
    # never a hardcoded reference that drifts from config.
    chosen = captured["cmd"][0]
    assert chosen in (str(PYTHON_BIN), str(SYSTEM_PYTHON))
    # In a provisioned dev environment (which this test runs from), the venv
    # must win over SYSTEM_PYTHON.
    if PYTHON_BIN.exists():
        assert chosen == str(PYTHON_BIN), (
            "venv python must be preferred over system python when the venv is provisioned"
        )
