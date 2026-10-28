"""Sprint 854: nightly environment parity.

The 2026-10-28 nightly went RED with no defect in the code:

- `backend/venv` had fastapi 0.136.1 against a `fastapi==0.162.0` pin, so 99
  test modules failed to import (Coverage Sentinel) — reported as a test failure;
- QA Warden crashed at `json.loads(None)` on Jest's stdout and wrote no sentinel;
- Report Auditor ran 0 tests and reported GREEN;
- the brief stamped the commit that was HEAD at 04:00, not the one tested at 02:00.

Run from project root:  ``python -m pytest scripts/overnight/tests/``
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.overnight import briefing_compiler, env_parity, orchestrator
from scripts.overnight.agents import qa_warden, report_auditor

REQUIREMENTS = _PROJECT_ROOT / "backend" / "requirements.txt"


def _completed(returncode: int = 0, stdout: str | None = "", stderr: str | None = "") -> MagicMock:
    mock = MagicMock(spec=subprocess.CompletedProcess)
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


# ── Pin parsing and comparison ─────────────────────────────────────────────


class TestPins:
    def test_follows_includes_and_ignores_floors(self, tmp_path):
        (tmp_path / "base.txt").write_text(
            "# comment\n"
            "fastapi==0.162.0\n"
            "uvicorn[standard]==0.54.0  # inline comment\n"
            "cryptography>=46.0.0\n"
            "Py_JWT[crypto]==2.15.1 ; python_version >= '3.10'\n",
            encoding="utf-8",
        )
        (tmp_path / "dev.txt").write_text("-r base.txt\npytest>=9.1.1\nruff==0.17.2\n", encoding="utf-8")

        pins = env_parity.parse_exact_pins(tmp_path / "dev.txt")

        assert pins == {
            "fastapi": "0.162.0",
            "uvicorn": "0.54.0",
            "py-jwt": "2.15.1",
            "ruff": "0.17.2",
        }

    def test_the_real_requirements_file_pins_fastapi(self):
        pins = env_parity.parse_exact_pins(REQUIREMENTS)
        assert "fastapi" in pins
        assert "cryptography" not in pins, "floors must not be treated as pins"

    def test_the_2026_10_28_drift_is_named(self):
        """The exact shape of the 10-28 failure: one stale framework pin."""
        sync = {"ok": True, "reason": None, "elapsed_s": 12.0}
        result = env_parity.evaluate(
            sync, {"fastapi": "0.162.0", "pandas": "3.1.0"},
            {"fastapi": "0.136.1", "pandas": "3.1.0"}, None,
        )

        assert result["status"] == "red"
        assert result["mismatches"] == [{"package": "fastapi", "pinned": "0.162.0", "installed": "0.136.1"}]
        assert "fastapi pinned 0.162.0, installed 0.136.1" in result["summary"]

    def test_a_missing_package_is_named(self):
        result = env_parity.evaluate({"ok": True}, {"stripe": "16.0.1"}, {}, None)
        assert result["status"] == "red"
        assert "stripe pinned 16.0.1, installed MISSING" in result["summary"]

    def test_matching_environment_is_green(self):
        result = env_parity.evaluate({"ok": True}, {"fastapi": "0.162.0"}, {"fastapi": "0.162.0"}, None)
        assert result["status"] == "green"
        assert result["reasons"] == []

    def test_unlistable_environment_is_red_not_green(self):
        result = env_parity.evaluate({"ok": True}, {"fastapi": "0.162.0"}, None, "could not list: boom")
        assert result["status"] == "red"
        assert "boom" in result["summary"]


# ── The sync step ──────────────────────────────────────────────────────────


class TestSync:
    @pytest.fixture
    def fake_env(self, tmp_path):
        py = tmp_path / "python.exe"
        py.write_text("", encoding="utf-8")
        req = tmp_path / "requirements-dev.txt"
        req.write_text("fastapi==0.162.0\n", encoding="utf-8")
        return py, req

    def test_a_network_hang_fails_red_with_a_reason_instead_of_hanging(self, fake_env, monkeypatch):
        py, req = fake_env
        seen = {}

        def _hang(cmd, **kwargs):
            seen.update(kwargs)
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs["timeout"])

        monkeypatch.setattr(env_parity.subprocess, "run", _hang)
        result = env_parity.sync_venv(py, req, timeout_s=7)

        assert seen["timeout"] == 7, "the sync must be bounded"
        assert result["ok"] is False
        assert "timed out after 7s" in result["reason"]

    def test_pip_failure_reason_carries_pips_own_words(self, fake_env, monkeypatch):
        py, req = fake_env
        monkeypatch.setattr(
            env_parity.subprocess, "run",
            lambda *a, **k: _completed(1, "", "ERROR: Could not find a version that satisfies fastapi==0.162.0"),
        )
        result = env_parity.sync_venv(py, req)

        assert result["ok"] is False
        assert "pip exited 1" in result["reason"]
        assert "Could not find a version" in result["reason"]

    def test_sync_bounds_pip_itself_and_installs_from_the_file(self, fake_env, monkeypatch):
        py, req = fake_env
        captured = {}

        def _ok(cmd, **kwargs):
            captured["cmd"] = cmd
            return _completed(0)

        monkeypatch.setattr(env_parity.subprocess, "run", _ok)
        assert env_parity.sync_venv(py, req)["ok"] is True
        cmd = captured["cmd"]
        assert cmd[:4] == [str(py), "-m", "pip", "install"]
        assert "--timeout" in cmd and "--retries" in cmd
        assert cmd[-2:] == ["-r", str(req)]

    def test_missing_venv_is_a_named_reason(self, tmp_path):
        result = env_parity.sync_venv(tmp_path / "nope.exe", tmp_path / "r.txt")
        assert result["ok"] is False
        assert "venv interpreter not found" in result["reason"]

    def test_failed_sync_is_red_even_if_pins_happen_to_match(self):
        result = env_parity.evaluate(
            {"ok": False, "reason": "venv sync timed out after 600s"},
            {"fastapi": "0.162.0"}, {"fastapi": "0.162.0"}, None,
        )
        assert result["status"] == "red"
        assert "timed out" in result["summary"]

    def test_installed_versions_reads_a_real_interpreter(self):
        """End-to-end against this interpreter: pytest is installed, so it is listed."""
        versions, err = env_parity.installed_versions(Path(sys.executable))
        assert err is None
        assert "pytest" in versions


# ── QA Warden: Jest gives no stdout ────────────────────────────────────────


class TestQaWardenJest:
    def test_none_stdout_reports_did_not_run_instead_of_typeerror(self, tmp_path, monkeypatch):
        """The 10-28 crash: subprocess returned stdout=None."""
        monkeypatch.setattr(qa_warden, "REPORTS_DIR", tmp_path)
        monkeypatch.setattr(qa_warden.subprocess, "run", lambda *a, **k: _completed(1, None, None))

        fe = qa_warden._run_frontend_tests()

        assert fe["did_not_run"]
        assert "no parseable result" in fe["did_not_run"]
        assert fe["passed"] == 0 and fe["failed"] == 0

    def test_jest_is_decoded_as_utf8(self, tmp_path, monkeypatch):
        """The root cause: locale (cp1252) decoding killed the reader thread."""
        monkeypatch.setattr(qa_warden, "REPORTS_DIR", tmp_path)
        captured = {}

        def _run(cmd, **kwargs):
            captured.update(kwargs)
            captured["cmd"] = cmd
            return _completed(0, "", "Tests:       5 passed, 5 total\nTime:        3.2 s\n")

        monkeypatch.setattr(qa_warden.subprocess, "run", _run)
        fe = qa_warden._run_frontend_tests()

        assert captured["encoding"] == "utf-8"
        assert captured["errors"] == "replace"
        assert any(str(a).startswith("--outputFile=") for a in captured["cmd"])
        assert fe == {"passed": 5, "failed": 0, "duration_s": 3.2, "did_not_run": None}

    # The reader-thread UnicodeDecodeError on byte 0x8f *is* the 10-28 failure.
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    def test_the_decode_failure_mechanism_is_real(self):
        """Reproduce why stdout was None: a cp1252 decode of Jest's `●` (E2 97 8F)."""
        child = "import sys; sys.stdout.buffer.write('\\u25cf console.log'.encode('utf-8'))"
        fixed = subprocess.run(
            [sys.executable, "-c", child], capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
        assert fixed.stdout == "● console.log"
        # On Windows the reader thread dies and stdout is None; on POSIX the
        # decode raises in communicate(). Either way, not the text.
        try:
            broken = subprocess.run(
                [sys.executable, "-c", child], capture_output=True, text=True,
                encoding="cp1252", check=False,
            ).stdout
        except UnicodeDecodeError:
            broken = None
        assert broken is None

    def test_results_file_is_preferred(self, tmp_path, monkeypatch):
        monkeypatch.setattr(qa_warden, "REPORTS_DIR", tmp_path)

        def _run(cmd, **kwargs):
            (tmp_path / ".jest_results.json").write_text(json.dumps({
                "numPassedTests": 2041, "numFailedTests": 1, "startTime": 1000,
                "testResults": [{"endTime": 4000}, {"endTime": 9000}],
            }), encoding="utf-8")
            return _completed(1, "> frontend@ test\n> jest", "")

        monkeypatch.setattr(qa_warden.subprocess, "run", _run)
        fe = qa_warden._run_frontend_tests()
        assert fe == {"passed": 2041, "failed": 1, "duration_s": 8.0, "did_not_run": None}

    def test_jest_timeout_is_did_not_run(self, tmp_path, monkeypatch):
        monkeypatch.setattr(qa_warden, "REPORTS_DIR", tmp_path)

        def _boom(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs["timeout"])

        monkeypatch.setattr(qa_warden.subprocess, "run", _boom)
        fe = qa_warden._run_frontend_tests()
        assert "budget" in fe["did_not_run"]

    def _run_with(self, tmp_path, backend, frontend):
        with patch.object(qa_warden, "REPORTS_DIR", tmp_path), \
             patch.object(qa_warden, "BASELINE_FILE", tmp_path / "b.json"), \
             patch.object(qa_warden, "run_stamp", return_value={"tested_sha": "c" * 40, "tested_at": "x"}), \
             patch.object(qa_warden, "_run_backend_tests", return_value=backend), \
             patch.object(qa_warden, "_run_frontend_tests", return_value=frontend):
            return qa_warden.run()

    def test_frontend_did_not_run_is_red_and_says_so(self, tmp_path):
        backend = {"passed": 10, "failed": 0, "errors": 0, "duration_s": 1, "failing_tests": [],
                   "collection_error": None}
        result = self._run_with(tmp_path, backend, qa_warden._jest_did_not_run("Jest produced no parseable result"))

        assert result["status"] == "red"
        assert "Frontend: DID NOT RUN" in result["summary"]
        assert result["tested_sha"] == "c" * 40
        assert (tmp_path / f".qa_warden_{qa_warden.TODAY}.json").exists(), "the sentinel must still be written"

    def test_zero_tests_is_unverified_not_green(self, tmp_path):
        backend = {"passed": 0, "failed": 0, "errors": 0, "duration_s": 0, "failing_tests": [],
                   "collection_error": None}
        frontend = {"passed": 5, "failed": 0, "duration_s": 1, "did_not_run": None}
        result = self._run_with(tmp_path, backend, frontend)
        assert result["status"] == "unverified"


# ── Report Auditor: 0/0 ────────────────────────────────────────────────────


class TestReportAuditor:
    def test_zero_of_zero_is_unverified(self):
        assert report_auditor._classify(0, 0, 0) == "unverified"

    def test_classification_otherwise_unchanged(self):
        assert report_auditor._classify(2, 1, 0) == "red"
        assert report_auditor._classify(2, 0, 4) == "yellow"
        assert report_auditor._classify(2, 0, 0) == "green"

    def test_run_reports_unverified_on_an_empty_smoke_run(self, tmp_path):
        with patch.object(report_auditor, "REPORTS_DIR", tmp_path), \
             patch.object(report_auditor, "BASELINE_FILE", tmp_path / "b.json"), \
             patch.object(report_auditor, "run_stamp", return_value={"tested_sha": None, "tested_at": None}), \
             patch.object(report_auditor, "_scan_source_for_bug", return_value=False), \
             patch.object(report_auditor, "_run_meridian_tests", return_value=(0, 0, [], "")):
            result = report_auditor.run()

        assert result["status"] == "unverified"
        assert result["summary"].startswith("UNVERIFIED")

    def test_meridian_runs_in_the_venv_when_present(self, monkeypatch):
        captured = {}

        def _run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured.update(kwargs)
            return _completed(0, "2 passed in 1.0s\n", "")

        monkeypatch.setattr(report_auditor.subprocess, "run", _run)
        assert report_auditor._run_meridian_tests()[:2] == (2, 0)
        expected = report_auditor.PYTHON_BIN if report_auditor.PYTHON_BIN.exists() else report_auditor.SYSTEM_PYTHON
        assert captured["cmd"][0] == str(expected)
        assert captured["encoding"] == "utf-8"


# ── Briefing: did-it-run, pre-flight, tested-as-of ─────────────────────────


def _all_sentinels() -> dict:
    return {name: {"status": "green", "summary": f"{name} ok"} for name in briefing_compiler.AGENTS}


class TestRunCheck:
    START = "2026-10-28T02:00:02"

    def _manifest(self, **agents):
        recs = {n: {"outcome": "ok"} for n in briefing_compiler.AGENTS}
        recs.update(agents)
        return {"started_at": self.START, "head_sha": "a" * 40, "agents": recs}

    def _fresh(self):
        ts = datetime.datetime.fromisoformat(self.START).timestamp() + 60
        return {n: ts for n in briefing_compiler.AGENTS}

    def test_everything_ran(self):
        assert briefing_compiler._agent_run_check(_all_sentinels(), self._manifest(), self._fresh()) == []

    def test_a_crash_is_named_with_its_exit(self):
        data = _all_sentinels()
        data["qa_warden"] = None
        manifest = self._manifest(qa_warden={
            "outcome": "failed", "exit_code": 1,
            "detail": "TypeError: the JSON object must be str, bytes or bytearray, not NoneType",
        })
        problems = briefing_compiler._agent_run_check(data, manifest, self._fresh())

        assert problems == [{
            "agent": "qa_warden", "problem": "crashed",
            "detail": "exit 1: TypeError: the JSON object must be str, bytes or bytearray, not NoneType",
        }]

    def test_a_missing_sentinel_without_a_manifest_still_counts(self):
        data = _all_sentinels()
        data["scout"] = None
        problems = briefing_compiler._agent_run_check(data, None, {})
        assert [p["problem"] for p in problems] == ["did not run"]

    def test_a_leftover_sentinel_is_stale(self):
        mtimes = self._fresh()
        mtimes["coverage_sentinel"] = datetime.datetime.fromisoformat(self.START).timestamp() - 3600
        problems = briefing_compiler._agent_run_check(_all_sentinels(), self._manifest(), mtimes)
        assert problems[0]["agent"] == "coverage_sentinel"
        assert problems[0]["problem"] == "stale"


class TestOverallStatus:
    def test_preflight_red_makes_the_brief_red(self):
        assert briefing_compiler._overall_status(_all_sentinels(), {"status": "red"}, []) == "red"

    def test_run_problems_make_the_brief_red(self):
        assert briefing_compiler._overall_status(_all_sentinels(), None, [{"agent": "x"}]) == "red"

    def test_unverified_is_never_green(self):
        data = _all_sentinels()
        data["report_auditor"]["status"] = "unverified"
        data["scout"]["status"] = "yellow"
        assert briefing_compiler._overall_status(data) == "unverified"

    def test_legacy_signature_still_works(self):
        assert briefing_compiler._overall_status(_all_sentinels()) == "green"


class TestTestedAsOf:
    def test_prefers_the_run_start_sha(self):
        manifest = {"head_sha": "a" * 40, "started_at": "2026-10-28T02:00:02"}
        data = {"qa_warden": {"tested_sha": "b" * 40, "tested_at": "2026-10-28T02:00:05"}}
        assert briefing_compiler._tested_as_of(manifest, data) == (
            "a" * 40, "2026-10-28T02:00:02", "orchestrator run start",
        )

    def test_falls_back_to_an_agent_stamp(self):
        data = {"qa_warden": {"tested_sha": "b" * 40, "tested_at": "2026-10-28T02:00:05"}}
        sha, _at, source = briefing_compiler._tested_as_of(None, data)
        assert (sha, source) == ("b" * 40, "qa_warden start")

    def test_unrecorded_is_unrecorded(self):
        assert briefing_compiler._tested_as_of(None, {}) == (None, None, "not recorded")


def test_the_brief_leads_with_preflight_and_run_check(tmp_path, monkeypatch):
    """End-to-end: replay the 10-28 night and read the brief a human would read."""
    today = briefing_compiler.TODAY
    data = _all_sentinels()
    data["report_auditor"]["status"] = "unverified"
    for name, payload in data.items():
        if name != "qa_warden":
            (tmp_path / f".{name}_{today}.json").write_text(json.dumps(payload), encoding="utf-8")

    started = (datetime.datetime.now() - datetime.timedelta(hours=2)).replace(microsecond=0)
    manifest = {
        "started_at": started.isoformat(), "head_sha": "a" * 40,
        "agents": {"qa_warden": {"outcome": "failed", "exit_code": 1, "detail": "TypeError: NoneType"}},
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "preflight.json").write_text(json.dumps({
        "status": "red",
        "summary": "Environment pre-flight FAILED: 1 installed version(s) differ from the == pins: "
                   "fastapi pinned 0.162.0, installed 0.136.1.",
    }), encoding="utf-8")

    monkeypatch.setattr(briefing_compiler, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(briefing_compiler, "REPORT_PATH", tmp_path / "brief.md")
    monkeypatch.setattr(briefing_compiler, "RUN_MANIFEST_PATH", tmp_path / "manifest.json")
    monkeypatch.setattr(briefing_compiler, "PREFLIGHT_PATH", tmp_path / "preflight.json")
    monkeypatch.setattr(briefing_compiler, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(briefing_compiler, "_head_sha", lambda: "b" * 40)

    result = briefing_compiler.run()
    brief = (tmp_path / "brief.md").read_text(encoding="utf-8")

    assert result["status"] == "red"
    assert result["tested_sha"] == "a" * 40
    assert f"`{'a' * 40}` as of {started:%Y-%m-%d %H:%M} (orchestrator run start)" in brief
    assert "SUPERSEDED" in brief  # HEAD moved since the run started
    assert "ENVIRONMENT PRE-FLIGHT FAILED" in brief
    assert "fastapi pinned 0.162.0, installed 0.136.1" in brief
    assert "`qa_warden` — **crashed** (exit 1: TypeError: NoneType)" in brief
    assert "UNVERIFIED" in brief
    # The warnings sit above the agent sections, where they will be read.
    assert brief.index("PRE-FLIGHT FAILED") < brief.index("## \U0001f9ea QA Warden")


# ── Orchestrator ───────────────────────────────────────────────────────────


class TestOrchestrator:
    def test_exit_code_is_nonzero_on_any_failure(self):
        assert orchestrator._exit_code([], {"status": "green"}, False) == 0
        assert orchestrator._exit_code(["qa_warden"], {"status": "green"}, False) == 1
        assert orchestrator._exit_code([], {"status": "red"}, False) == 1
        assert orchestrator._exit_code(["qa_warden"], {"status": "red"}, True) == 0

    def test_a_failed_agent_with_no_output_is_recorded_not_raised(self, monkeypatch, tmp_path):
        log = MagicMock()
        captured = {}

        def _run(cmd, **kwargs):
            captured.update(kwargs)
            return _completed(1, None, None)

        monkeypatch.setattr(orchestrator.subprocess, "run", _run)
        outcome = orchestrator._run_agent("qa_warden", "x.py", log)

        assert outcome["outcome"] == "failed"
        assert outcome["exit_code"] == 1
        assert captured["encoding"] == "utf-8"

    def test_preflight_runs_before_the_first_agent(self):
        import inspect

        src = inspect.getsource(orchestrator.main)
        assert src.index("_run_preflight(") < src.index("for name, script, hour, minute in AGENT_SCHEDULE")

    def test_manifest_records_sha_and_start(self, tmp_path, monkeypatch):
        monkeypatch.setattr(orchestrator, "_git_head_sha", lambda: "d" * 40)
        m = orchestrator.RunManifest(tmp_path / "m.json", dry_run=False)
        m.record("qa_warden", {"outcome": "ok"})
        saved = json.loads((tmp_path / "m.json").read_text(encoding="utf-8"))
        assert saved["head_sha"] == "d" * 40
        assert saved["started_at"]
        assert saved["agents"]["qa_warden"]["outcome"] == "ok"
