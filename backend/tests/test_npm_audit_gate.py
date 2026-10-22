"""The npm audit gate — Sprint 794.

`npm audit` exits 1 both when it finds a vulnerability and when it cannot
reach the advisory endpoint. On 2026-10-22, PR #189's "Node CVE & License
Audit" went red on a 503 from registry.npmjs.org. Nothing was vulnerable. The
red X was the same one a genuine CRITICAL produces, so the only honest reading
of that signal was "something is wrong, go find out which thing".

That is the third instance this session of one defect shape: **a check with
two outcomes where reality has three — pass, fail, and "did not actually
run".** Sprint 778a was the same bug inverted (a job that could not report a
failure it had detected); Sprint 792 audited the family.

Two claims are tested here, because fixing this needs both and only one of
them is about the classifier:

1. The classifier tells the three outcomes apart, on payload shape rather than
   exit code — the exit code being exactly what cannot tell them apart.
2. **No workflow calls `npm audit` directly any more.** Without this, the fix
   silently un-applies the first time someone adds a job by copying an older
   one, and nothing would notice: the new job would be green until the day the
   registry hiccups, which is the failure that started all this.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

from tests.helpers.shell_support import NEEDS_BASH, bash_support_path, usable_bash

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
GATE = REPO_ROOT / "scripts" / "npm_audit_gate.sh"
CLASSIFIER = REPO_ROOT / "scripts" / "classify_npm_audit.py"


def _load_classifier():
    spec = importlib.util.spec_from_file_location("classify_npm_audit", CLASSIFIER)
    assert spec and spec.loader, "could not load the classifier module"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


classify = _load_classifier().classify


# ---------------------------------------------------------------------------
# Real payload shapes, captured from npm 10.9.0 rather than imagined
# ---------------------------------------------------------------------------

CLEAN_REPORT = """
{"auditReportVersion": 2, "vulnerabilities": {},
 "metadata": {"vulnerabilities": {"info": 0, "low": 0, "moderate": 0, "high": 0,
                                  "critical": 0, "total": 0},
              "dependencies": {"prod": 188, "total": 942}}}
"""

# What npm actually returns when the registry is unreachable. Captured by
# pointing npm at a closed port; the 503 body from the live incident has the
# same shape — a `message`, an empty `error`, and crucially NO
# `auditReportVersion` and NO `metadata`.
REGISTRY_FAILURE = """
{"message": "request to https://registry.npmjs.org/-/npm/v1/security/audits/quick failed, reason: 503",
 "error": {"summary": "", "detail": ""}}
"""

VULNERABLE_REPORT = """
{"auditReportVersion": 2,
 "metadata": {"vulnerabilities": {"info": 0, "low": 1, "moderate": 2, "high": 3,
                                  "critical": 1, "total": 7}}}
"""


def test_a_clean_report_is_clean():
    verdict, reason = classify(CLEAN_REPORT, npm_exit=0, audit_level="high")
    assert verdict == "CLEAN", reason


def test_a_registry_failure_is_not_a_vulnerability():
    """The whole point of the sprint.

    npm exits 1 here, identically to the vulnerable case below. If this ever
    returns VULNERABLE the gate is lying, and if it ever returns CLEAN the gate
    is worse than useless — it reports safety it did not establish.
    """
    verdict, reason = classify(REGISTRY_FAILURE, npm_exit=1, audit_level="high")
    assert verdict == "UNVERIFIED", reason
    assert "503" in reason, "the reason should quote what npm said, so the reader can act on it"


def test_real_findings_are_reported_as_findings():
    verdict, reason = classify(VULNERABLE_REPORT, npm_exit=1, audit_level="high")
    assert verdict == "VULNERABLE", reason
    assert "3 high" in reason and "1 critical" in reason


def test_the_threshold_is_respected():
    """`--audit-level=high` must ignore moderate and below, as npm does."""
    moderate_only = """
    {"auditReportVersion": 2,
     "metadata": {"vulnerabilities": {"low": 5, "moderate": 4, "high": 0, "critical": 0}}}
    """
    assert classify(moderate_only, npm_exit=0, audit_level="high")[0] == "CLEAN"
    assert classify(moderate_only, npm_exit=1, audit_level="low")[0] == "VULNERABLE"


@pytest.mark.parametrize(
    "payload",
    [
        "",
        "   ",
        "npm error audit endpoint returned an error",
        "[]",
        '{"auditReportVersion": 2}',
        '{"auditReportVersion": 2, "metadata": {}}',
        '{"auditReportVersion": 2, "metadata": {"vulnerabilities": {"high": "lots"}}}',
    ],
)
def test_anything_unreadable_is_unverified_never_clean(payload):
    """An answer we cannot read is not a clean bill of health.

    Every unrecognised shape must land on UNVERIFIED. Defaulting the other way
    would mean a change in npm's output format silently disarms the gate —
    which is the Sprint 792 defect class, arriving through a different door.
    """
    verdict, _ = classify(payload, npm_exit=1, audit_level="high")
    assert verdict == "UNVERIFIED"


def test_a_nonzero_exit_with_a_clean_report_is_not_trusted():
    """npm failed for a reason its own report does not describe. Do not guess."""
    verdict, reason = classify(CLEAN_REPORT, npm_exit=1, audit_level="high")
    assert verdict == "UNVERIFIED", reason
    assert "disagree" in reason


# ---------------------------------------------------------------------------
# The anti-drift check — the half that keeps the fix applied
# ---------------------------------------------------------------------------


def _workflow_files() -> list[Path]:
    return sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml"))


def test_no_workflow_calls_npm_audit_directly():
    """Every invocation must go through the gate.

    Three call sites had this bug because three jobs each ran the bare
    command. A fourth added by copy-paste would reintroduce it, be green on
    every run until the registry hiccupped, and look like a new problem rather
    than an old one.
    """
    offenders = []
    for path in _workflow_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if "npm audit" not in stripped:
                continue
            if stripped.startswith("#"):
                continue  # prose about the gate, not an invocation
            if "npm_audit_gate.sh" in stripped:
                continue
            offenders.append(f"{path.name}:{lineno}: {stripped}")

    assert not offenders, (
        "these call `npm audit` directly, so a registry outage there is "
        "indistinguishable from a CRITICAL finding — route them through "
        "scripts/npm_audit_gate.sh:\n  " + "\n  ".join(offenders)
    )


def test_the_workflow_scan_actually_scans_something():
    """A glob that matches nothing proves nothing (Sprint 792)."""
    files = _workflow_files()
    assert files, f"no workflow files under {WORKFLOWS_DIR} — the check above covers nothing"
    assert any("npm_audit_gate.sh" in p.read_text(encoding="utf-8") for p in files), (
        "no workflow references the gate — either it was unwired or this test lost its target"
    )


def test_the_gate_script_and_classifier_exist_and_are_wired_to_each_other():
    assert GATE.is_file(), f"missing {GATE}"
    assert CLASSIFIER.is_file(), f"missing {CLASSIFIER}"
    assert "classify_npm_audit.py" in GATE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# End-to-end: the gate's exit codes, with npm stubbed
# ---------------------------------------------------------------------------

# Sprint 786b: a bash that EXISTS is not a bash that WORKS. `shutil.which`
# finds the inert WindowsApps/WSL launcher on this host, which exits 1 on
# `bash -c "exit 0"` — so the original `skipif(not shutil.which("bash"))`
# passed and then every subprocess here returned garbage. That is how the
# 2026-10-22 nightly went RED on 14 tests with nothing wrong in the code
# under test. `usable_bash()` probes instead of asking.
BASH = usable_bash()


def _run_gate(tmp_path: Path, stub_stdout: str, stub_exit: int, *args: str):
    """Run the real gate against a fake `npm` placed first on PATH.

    The stub reads its payload from a file rather than carrying it inline, so
    no JSON ever has to survive a round of shell quoting.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)

    payload_file = tmp_path / "payload.json"
    payload_file.write_text(stub_stdout, encoding="utf-8")

    stub = bin_dir / "npm"
    stub.write_text(
        f'#!/usr/bin/env bash\ncat "{payload_file.as_posix()}"\nexit {stub_exit}\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)

    env = dict(os.environ)
    # The stub first, then the directories bash itself needs (see
    # bash_support_path), then whatever the host already had.
    env["PATH"] = os.pathsep.join([str(bin_dir), *bash_support_path(), env.get("PATH", "")])
    env["NPM_AUDIT_ATTEMPTS"] = "2"
    env["NPM_AUDIT_BACKOFF_SECONDS"] = "0"

    return subprocess.run(
        [BASH, str(GATE), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path),
        timeout=120,
    )


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_passes_on_a_clean_audit(tmp_path):
    result = _run_gate(tmp_path, CLEAN_REPORT, 0, "--mode", "blocking")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "CLEAN" in result.stdout


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_blocks_on_real_findings(tmp_path):
    result = _run_gate(tmp_path, VULNERABLE_REPORT, 1, "--mode", "blocking")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "VULNERABLE" in result.stdout


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_blocks_on_an_unreachable_registry_but_says_so(tmp_path):
    """Unchanged policy — fail closed — with the reason stated.

    The exit code matches the VULNERABLE case above on purpose: a security
    gate that opens when it cannot see is worse than one that blocks. What
    changes is that the reader is told which of the two happened, so they
    re-run the job instead of hunting a CVE that was never there.
    """
    result = _run_gate(tmp_path, REGISTRY_FAILURE, 1, "--mode", "blocking")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "UNVERIFIED" in result.stdout
    assert "NOT A VULNERABILITY FINDING" in result.stdout


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_retries_before_giving_up(tmp_path):
    result = _run_gate(tmp_path, REGISTRY_FAILURE, 1, "--mode", "blocking")
    assert "attempt 1/2" in result.stdout, "a transient 503 must be retried, not reported on first sight"


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_advisory_mode_never_blocks(tmp_path):
    for payload, code in ((VULNERABLE_REPORT, 1), (REGISTRY_FAILURE, 1)):
        result = _run_gate(tmp_path, payload, code, "--mode", "advisory")
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_rejects_a_bad_mode_rather_than_guessing(tmp_path):
    result = _run_gate(tmp_path, CLEAN_REPORT, 0, "--mode", "nonsense")
    assert result.returncode == 2, result.stdout + result.stderr
