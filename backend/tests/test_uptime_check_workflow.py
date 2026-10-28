"""Sprint 852 (security review L10): the uptime probe fails on a degraded body.

Sprint 774 made a rate-limit storage outage non-fatal: each worker falls back
to its own in-memory counters, which loosens every limit by the worker count,
and ``/health/ready`` reports ``"status": "degraded"`` behind an HTTP 200. A
status-code-only monitor never sees it. This runs the real ``/health/ready``
probe step from ``.github/workflows/uptime-check.yml`` under bash, with
``curl`` stubbed, and checks the verdict for each body.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.helpers.shell_support import NEEDS_BASH, bash_support_path, usable_bash

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "uptime-check.yml"
BASH = usable_bash()


def _probe_script() -> str:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["uptime"]["steps"]
    (step,) = [s for s in steps if s.get("id") == "api"]
    return step["run"]


def _run_probe(tmp_path: Path, body: str, http_code: str) -> tuple[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (tmp_path / "body.json").write_text(body, encoding="utf-8")
    # The step calls `curl -sS ... -w '\n%{http_code}'`: body, newline, code.
    curl = bin_dir / "curl"
    curl.write_text(
        f'#!/usr/bin/env bash\ncat "{(tmp_path / "body.json").as_posix()}"\nprintf "\\n{http_code}"\n',
        encoding="utf-8",
    )
    # The step parses with `python3`, which Windows does not ship under that name.
    python3 = bin_dir / "python3"
    python3.write_text(f'#!/usr/bin/env bash\nexec "{Path(sys.executable).as_posix()}" "$@"\n', encoding="utf-8")
    for stub in (curl, python3):
        stub.chmod(0o755)
    script = tmp_path / "probe.sh"
    script.write_text(_probe_script(), encoding="utf-8")
    output = tmp_path / "github_output"
    output.write_text("", encoding="utf-8")

    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(bin_dir), *bash_support_path(), env.get("PATH", "")])
    env["API_BASE"] = "https://api.invalid"
    env["GITHUB_OUTPUT"] = str(output)
    result = subprocess.run([BASH, str(script)], capture_output=True, text=True, env=env, cwd=str(tmp_path), timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return output.read_text(encoding="utf-8").strip(), (tmp_path / "report.md").read_text(encoding="utf-8")


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_healthy_body_passes(tmp_path):
    result, _ = _run_probe(tmp_path, '{"status": "healthy", "dependencies": {}}', "200")
    assert result == "result=PASS"


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_degraded_body_behind_a_200_fails(tmp_path):
    body = '{"status": "degraded", "dependencies": {"rate_limit_storage": {"status": "unhealthy"}}}'
    result, report = _run_probe(tmp_path, body, "200")
    assert result == "result=FAIL"
    assert '"degraded"' in report


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
@pytest.mark.parametrize(("body", "code"), [("not json", "200"), ('{"status": "healthy"}', "503"), ("{}", "200")])
def test_other_bad_responses_fail(tmp_path, body, code):
    result, _ = _run_probe(tmp_path, body, code)
    assert result == "result=FAIL"


def test_overall_verdict_fails_the_run_on_an_api_failure():
    """A FAIL from the probe must reach the final ``exit 1`` step."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = {s.get("id") or s.get("name"): s for s in workflow["jobs"]["uptime"]["steps"]}
    assert '[ "$API" = "FAIL" ]' in steps["final"]["run"]
    fail_step = steps["Fail the run so GitHub notifies"]
    assert fail_step["if"] == "steps.final.outputs.overall == 'FAIL'"
    assert "exit 1" in fail_step["run"]
