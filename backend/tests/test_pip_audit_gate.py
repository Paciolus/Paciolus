"""The pip-audit gate — Sprint 794b.

The Python counterpart to `test_npm_audit_gate.py`. `pip-audit` exits 1 when
it finds a vulnerability **and** when it cannot reach the service it needs —
the same conflation that made PR #189's npm CVE gate report a 503 as a
high-severity finding.

Captured from pip-audit 2.10.1 rather than assumed:

    nothing vulnerable    exit 0   {"dependencies": [{..., "vulns": []}], "fixes": []}
    real vulnerability    exit 1   same shape, "vulns" non-empty
    service unreachable   exit 1   nothing on stdout at all

The exit code cannot separate the last two. The payload can.

Two claims are tested, as in the npm file, because fixing this needs both:

1. The classifier tells the three outcomes apart, on payload rather than exit
   code.
2. **No workflow calls `pip-audit` directly any more.** Three call sites had
   this bug because three jobs each ran the bare command; a fourth added by
   copy-paste would be green until the next index outage.
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
GATE = REPO_ROOT / "scripts" / "pip_audit_gate.sh"
CLASSIFIER = REPO_ROOT / "scripts" / "classify_pip_audit.py"


def _load_classifier():
    spec = importlib.util.spec_from_file_location("classify_pip_audit", CLASSIFIER)
    assert spec and spec.loader, "could not load the classifier module"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


classify = _load_classifier().classify


# ---------------------------------------------------------------------------
# Real payload shapes, captured from pip-audit 2.10.1
# ---------------------------------------------------------------------------

CLEAN_REPORT = '{"dependencies": [{"name": "packaging", "version": "24.1", "vulns": []}], "fixes": []}'

# jinja2 2.11.3. Note the DUPLICATES: pip-audit emits each advisory once per
# vulnerability source, so four distinct advisories arrive as eight entries.
VULNERABLE_REPORT = """
{"dependencies": [{"name": "jinja2", "version": "2.11.3", "vulns": [
  {"id": "PYSEC-2026-1473", "fix_versions": ["3.1.3"], "aliases": ["CVE-2024-22195"], "description": "x"},
  {"id": "PYSEC-2026-1474", "fix_versions": ["3.1.4"], "aliases": [], "description": "x"},
  {"id": "PYSEC-2026-1475", "fix_versions": ["3.1.5"], "aliases": [], "description": "x"},
  {"id": "PYSEC-2026-1471", "fix_versions": ["3.1.6"], "aliases": [], "description": "x"},
  {"id": "PYSEC-2026-1473", "fix_versions": ["3.1.3"], "aliases": [], "description": "x"},
  {"id": "PYSEC-2026-1474", "fix_versions": ["3.1.4"], "aliases": [], "description": "x"},
  {"id": "PYSEC-2026-1475", "fix_versions": ["3.1.5"], "aliases": [], "description": "x"},
  {"id": "PYSEC-2026-1471", "fix_versions": ["3.1.6"], "aliases": [], "description": "x"}
]}], "fixes": []}
"""

# What an unreachable index produces: exit 1, and nothing at all on stdout.
SERVICE_FAILURE = ""


def test_a_clean_report_is_clean():
    verdict, reason = classify(CLEAN_REPORT, pip_exit=0)
    assert verdict == "CLEAN", reason


def test_a_service_failure_is_not_a_vulnerability():
    """The whole point. pip-audit exits 1 here, as it does for a real finding."""
    verdict, reason = classify(SERVICE_FAILURE, pip_exit=1)
    assert verdict == "UNVERIFIED", reason
    assert "did not run" in reason


def test_real_findings_are_reported_as_findings():
    verdict, reason = classify(VULNERABLE_REPORT, pip_exit=1)
    assert verdict == "VULNERABLE", reason
    assert "jinja2" in reason


def test_duplicate_advisories_are_counted_once():
    """pip-audit emits each advisory once per source.

    The captured jinja2 report has eight entries for four distinct advisories.
    Counting raw entries doubles the number in a line a human reads to decide
    how alarmed to be — measured against the real output, not assumed.
    """
    verdict, reason = classify(VULNERABLE_REPORT, pip_exit=1)
    assert verdict == "VULNERABLE"
    assert "4 vulnerability" in reason, f"expected a deduplicated count of 4, got: {reason}"
    assert "8 vulnerability" not in reason
    assert reason.count("PYSEC-2026-1473") == 1


@pytest.mark.parametrize(
    "payload",
    [
        "",
        "   ",
        "ERROR:pip_audit._cli:Failed to install packages",
        "[]",
        "{}",
        '{"dependencies": "not-a-list"}',
        '{"dependencies": [{"name": "x", "version": "1"}]}',
        '{"dependencies": [{"name": "x", "version": "1", "vulns": "nope"}]}',
    ],
)
def test_anything_unreadable_is_unverified_never_clean(payload):
    """An answer we cannot read is not a clean bill of health.

    Defaulting the other way would let a change in pip-audit's output format
    silently disarm the gate — the Sprint 792 defect class through a different
    door.

    `{"name": "x", "version": "1"}` with no `vulns` **and** no `skip_reason`
    is genuinely malformed: the formatter always emits one or the other. A
    record carrying `skip_reason` is a different matter entirely — see
    `test_a_skipped_dependency_is_not_a_broken_schema`.
    """
    verdict, _ = classify(payload, pip_exit=1)
    assert verdict == "UNVERIFIED"


def test_a_nonzero_exit_with_a_clean_report_is_not_trusted():
    verdict, reason = classify(CLEAN_REPORT, pip_exit=1)
    assert verdict == "UNVERIFIED", reason
    assert "disagree" in reason


# ---------------------------------------------------------------------------
# The anti-drift check — the half that keeps the fix applied
# ---------------------------------------------------------------------------


def _workflow_files() -> list[Path]:
    return sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml"))


def _commands_in(line: str) -> list[str]:
    """The shell commands a workflow line invokes, if any.

    Substring matching is not good enough here, and the first draft proved it:
    `pip-audit` appears in a job key (`pip-audit-blocking:`), in a step name
    (`Install pip-audit and project dependencies`) and in an install line
    (`pip install pip-audit`), none of which run the tool. A check that flags
    those is noise, and noise gets suppressed with ever-looser exclusions
    until it stops checking anything.

    So: find the command position. A line is either `run: <cmd>` or a
    continuation inside a `run: |` block, and a command may be chained with
    `&&`, `||`, `;` or a pipe. No YAML parse, deliberately — `pyyaml` is only
    transitively installed here, not a declared dependency, and a guard should
    not acquire one.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return []
    if stripped.startswith("- run:"):
        stripped = stripped[len("- run:") :]
    elif stripped.startswith("run:"):
        stripped = stripped[len("run:") :]
    elif ":" in stripped.split(" ")[0] and not stripped.startswith("-"):
        # A YAML key such as `pip-audit-blocking:`, not a command.
        return []
    elif stripped.startswith("- name:") or stripped.startswith("name:"):
        return []

    parts = [stripped]
    for sep in ("&&", "||", ";", "|"):
        parts = [bit for part in parts for bit in part.split(sep)]
    return [p.strip() for p in parts if p.strip()]


def _invokes(line: str, tool: str) -> bool:
    return any(cmd == tool or cmd.startswith(tool + " ") for cmd in _commands_in(line))


def test_no_workflow_calls_pip_audit_directly():
    """Every invocation must go through the gate."""
    offenders = []
    for path in _workflow_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "pip_audit_gate.sh" in line:
                continue
            if _invokes(line, "pip-audit"):
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")

    assert not offenders, (
        "these call `pip-audit` directly, so a service outage there is "
        "indistinguishable from a real finding — route them through "
        "scripts/pip_audit_gate.sh:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize(
    "line,expected",
    [
        ("        run: pip-audit -r requirements.txt", True),
        ("          pip-audit --ignore-vuln CVE-1", True),
        ("        run: pip install pip-audit && pip-audit -r r.txt", True),
        ("  pip-audit-blocking:", False),
        ("      - name: Install pip-audit and project dependencies", False),
        ("          pip install pip-audit", False),
        ("        # pip-audit is wrapped by the gate", False),
        ("        run: bash ../scripts/pip_audit_gate.sh --mode blocking -- -r requirements.txt", False),
    ],
)
def test_the_invocation_detector_distinguishes_commands_from_prose(line, expected):
    """The detector itself needs testing — it is the whole check.

    Every False row here is a real line from these workflows that a substring
    match flags. A detector tuned by adding exclusions until the noise stops
    eventually excludes the thing it was looking for.
    """
    assert _invokes(line, "pip-audit") is expected


def test_the_workflow_scan_actually_scans_something():
    """A glob that matches nothing proves nothing (Sprint 792)."""
    files = _workflow_files()
    assert files, f"no workflow files under {WORKFLOWS_DIR} — the check above covers nothing"
    assert any("pip_audit_gate.sh" in p.read_text(encoding="utf-8") for p in files), (
        "no workflow references the gate — either it was unwired or this test lost its target"
    )


def test_the_gate_script_and_classifier_exist_and_are_wired_to_each_other():
    assert GATE.is_file(), f"missing {GATE}"
    assert CLASSIFIER.is_file(), f"missing {CLASSIFIER}"
    assert "classify_pip_audit.py" in GATE.read_text(encoding="utf-8")


def test_both_audit_gates_use_the_same_verdict_vocabulary():
    """npm and pip gates are separate scripts; their vocabulary must not drift.

    They were deliberately not merged into one abstraction — different schemas,
    and npm has a severity threshold while pip-audit has none. That makes the
    shared verdict names a convention, and conventions need a test or they are
    just a coincidence.
    """
    npm_classifier = REPO_ROOT / "scripts" / "classify_npm_audit.py"
    assert npm_classifier.is_file()
    npm_src = npm_classifier.read_text(encoding="utf-8")
    pip_src = CLASSIFIER.read_text(encoding="utf-8")
    for verdict in ("CLEAN", "VULNERABLE", "UNVERIFIED"):
        assert f'{verdict} = "{verdict}"' in npm_src, f"npm classifier lost the {verdict} verdict"
        assert f'{verdict} = "{verdict}"' in pip_src, f"pip classifier lost the {verdict} verdict"


# ---------------------------------------------------------------------------
# End-to-end: the gate's exit codes, with pip-audit stubbed
# ---------------------------------------------------------------------------

# Sprint 786b: a bash that EXISTS is not a bash that WORKS. `shutil.which`
# finds the inert WindowsApps/WSL launcher on this host, which exits 1 on
# `bash -c "exit 0"` — so the original `skipif(not shutil.which("bash"))`
# passed and then every subprocess here returned garbage. That is how the
# 2026-10-22 nightly went RED on 14 tests with nothing wrong in the code
# under test. `usable_bash()` probes instead of asking.
BASH = usable_bash()


def _run_gate(tmp_path: Path, stub_stdout: str, stub_exit: int, *args: str):
    """Run the real gate against a fake `pip-audit` placed first on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)

    payload_file = tmp_path / "payload.json"
    payload_file.write_text(stub_stdout, encoding="utf-8")

    stub = bin_dir / "pip-audit"
    stub.write_text(
        f'#!/usr/bin/env bash\ncat "{payload_file.as_posix()}"\nexit {stub_exit}\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)

    env = dict(os.environ)
    # The stub first, then the directories bash itself needs (see
    # bash_support_path), then whatever the host already had.
    env["PATH"] = os.pathsep.join([str(bin_dir), *bash_support_path(), env.get("PATH", "")])
    env["PIP_AUDIT_ATTEMPTS"] = "2"
    env["PIP_AUDIT_BACKOFF_SECONDS"] = "0"

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
def test_gate_blocks_on_an_unreachable_service_but_says_so(tmp_path):
    """Unchanged policy — fail closed — with the reason stated."""
    result = _run_gate(tmp_path, SERVICE_FAILURE, 1, "--mode", "blocking")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "UNVERIFIED" in result.stdout
    assert "NOT A VULNERABILITY FINDING" in result.stdout


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_retries_before_giving_up(tmp_path):
    result = _run_gate(tmp_path, SERVICE_FAILURE, 1, "--mode", "blocking")
    assert "attempt 1/2" in result.stdout, "a transient outage must be retried, not reported on first sight"


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_advisory_mode_never_blocks(tmp_path):
    for payload, code in ((VULNERABLE_REPORT, 1), (SERVICE_FAILURE, 1)):
        result = _run_gate(tmp_path, payload, code, "--mode", "advisory")
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_rejects_a_bad_mode_rather_than_guessing(tmp_path):
    result = _run_gate(tmp_path, CLEAN_REPORT, 0, "--mode", "nonsense")
    assert result.returncode == 2, result.stdout + result.stderr


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_rejects_format_and_desc_rather_than_producing_a_wrong_answer(tmp_path):
    """`--format` would break the classifier; `--desc` silently does nothing.

    Both are rejected loudly rather than ignored. A caller who passes
    `--format columns` and gets a pass has been told something untrue, and a
    caller who passes `--desc` expecting descriptions should learn that the
    gate builds its own summary instead.
    """
    for bad in ("--desc", "--format"):
        result = _run_gate(tmp_path, CLEAN_REPORT, 0, "--mode", "blocking", "--", bad)
        assert result.returncode == 2, f"{bad} should be rejected: {result.stdout}{result.stderr}"


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_passes_caller_arguments_through(tmp_path):
    """Call sites keep their own `-r` and `--ignore-vuln` flags."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    seen = tmp_path / "args.txt"
    stub = bin_dir / "pip-audit"
    stub.write_text(
        f'#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "{seen.as_posix()}"\nprintf \'%s\' \'{CLEAN_REPORT}\'\nexit 0\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(bin_dir), *bash_support_path(), env.get("PATH", "")])
    env["PIP_AUDIT_ATTEMPTS"] = "1"
    env["PIP_AUDIT_BACKOFF_SECONDS"] = "0"

    result = subprocess.run(
        [BASH, str(GATE), "--mode", "blocking", "--", "--ignore-vuln", "CVE-2026-3219"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path),
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    passed = seen.read_text(encoding="utf-8").split()
    assert "--ignore-vuln" in passed and "CVE-2026-3219" in passed, f"arguments were dropped: {passed}"
    assert "--format" in passed and "json" in passed, "the gate must force JSON output"


# ---------------------------------------------------------------------------
# Skipped dependencies — added after the PR #193 review
#
# pip-audit's JSON formatter emits `{"name", "skip_reason"}` with no `version`
# and no `vulns` when it cannot resolve a package: an editable install, a URL
# requirement, something absent from PyPI. It still exits 0 — only `--strict`
# turns a skip into a failure.
#
# The first draft treated the missing `vulns` key as a broken schema, which
# made every such run UNVERIFIED, retried it three times and failed the
# blocking gates. That is `--strict` smuggled in under a change whose whole
# claim was that the gating policy did not move.
# ---------------------------------------------------------------------------

SKIP_AND_AUDIT = """
{"dependencies": [
  {"name": "packaging", "version": "24.1", "vulns": []},
  {"name": "mylib", "skip_reason": "Dependency not found on PyPI and could not be audited"}
], "fixes": []}
"""

ALL_SKIPPED = """
{"dependencies": [
  {"name": "mylib", "skip_reason": "Dependency not found on PyPI and could not be audited"}
], "fixes": []}
"""

SKIP_AND_VULN = """
{"dependencies": [
  {"name": "jinja2", "version": "2.11.3", "vulns": [{"id": "PYSEC-2026-1473"}]},
  {"name": "mylib", "skip_reason": "Dependency is editable"}
], "fixes": []}
"""


def test_a_skipped_dependency_is_not_a_broken_schema():
    """A skip beside a real audit is CLEAN — pip-audit itself exits 0 here."""
    verdict, reason = classify(SKIP_AND_AUDIT, pip_exit=0)
    assert verdict == "CLEAN", reason


def test_skipped_dependencies_are_named_in_the_reason():
    """Non-blocking, but not invisible.

    The gate's whole purpose is to distinguish what was checked from what was
    not. A package pip-audit could not resolve was not checked, and the reader
    should be told which one and why — without the build failing over it.
    """
    _verdict, reason = classify(SKIP_AND_AUDIT, pip_exit=0)
    assert "skipped" in reason
    assert "mylib" in reason
    assert "not found on PyPI" in reason


def test_a_skip_does_not_mask_a_real_finding():
    verdict, reason = classify(SKIP_AND_VULN, pip_exit=1)
    assert verdict == "VULNERABLE", reason
    assert "jinja2" in reason
    assert "mylib" in reason, "the skip should still be reported alongside the finding"


def test_a_report_where_everything_was_skipped_is_not_clean():
    """The narrow exception, and the one place this differs from pip-audit.

    Skips do not fail the gate. But a report in which *nothing* was audited
    establishes nothing, and calling it CLEAN would be precisely the failure
    this sprint exists to prevent — reporting safety that was never checked.

    This is not `--strict`: a single audited package is enough to restore the
    normal verdict, as the tests above show.
    """
    verdict, reason = classify(ALL_SKIPPED, pip_exit=0)
    assert verdict == "UNVERIFIED", reason
    assert "nothing was actually audited" in reason


def test_the_skip_record_shape_matches_pip_audits_formatter():
    """Pinned to the real structure, not a guess.

    `pip_audit/_format/json.py` builds a skipped entry as exactly
    `{"name": ..., "skip_reason": ...}` — no `version`, no `vulns`. If a
    future version adds `vulns: []` to skipped records this test still
    passes, which is correct: the classifier keys off `skip_reason` being
    present, not off `vulns` being absent.
    """
    import json

    record = json.loads(SKIP_AND_AUDIT)["dependencies"][1]
    assert set(record) == {"name", "skip_reason"}
    verdict, _ = classify(SKIP_AND_AUDIT, pip_exit=0)
    assert verdict == "CLEAN"


@pytest.mark.skipif(not BASH, reason=NEEDS_BASH)
def test_gate_does_not_retry_or_block_on_a_skipped_dependency(tmp_path):
    """End-to-end: the symptom the review described.

    Before the fix this run produced three attempts and exit 1 on a perfectly
    normal exit-0 audit.
    """
    result = _run_gate(tmp_path, SKIP_AND_AUDIT, 0, "--mode", "blocking")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "CLEAN" in result.stdout
    assert "attempt 1/" not in result.stdout, "a skipped dependency must not trigger a retry"
