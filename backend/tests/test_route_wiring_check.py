"""Run the dead-route guardrail, which until Sprint 802 ran nowhere.

``scripts/check_route_wiring.py`` was written in Sprint 677 to catch a route
module that exists but is registered by nothing. It passes — 60 modules
scanned, 50 imported directly by ``routes/__init__.py`` and 10 through the
``audit`` / ``engagements`` / ``export`` aggregators — and it has never run in
CI or in a hook. Every ``scripts/*.py`` guard was traced against the
workflows, the Husky hooks and the test suite; it was the only one with no
caller at all.

It is wired here rather than as a new CI job on purpose. A new job would be
advisory (see the gate manifest in ``ci.yml``), whereas ``backend-tests`` is a
required status check, so a test is the stronger placement and costs no extra
runner time.

The script is worth keeping for a second reason: it is one of the few checks
in this repository built knowing its answer has **three** states — exit 2 for
"cannot locate backend/routes", distinct from 0 and 1. That is the shape
Sprint 794's lesson asks for, and the test below pins it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = _REPO_ROOT / "scripts" / "check_route_wiring.py"


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=120,
    )


def test_script_exists():
    assert SCRIPT.is_file(), f"{SCRIPT} is missing — the wiring guard cannot run"


def test_every_route_module_is_wired():
    result = _run(_REPO_ROOT)
    assert result.returncode == 0, (
        "Dead route module(s) detected — a file under backend/routes/ is registered by "
        f"neither routes/__init__.py nor a known aggregator:\n{result.stdout}\n{result.stderr}"
    )


def test_the_check_actually_scanned_the_routes():
    """A scan of zero modules exits 0 just as happily as a clean scan.

    Sprint 792: "the gate is green" and "the gate scanned something" are
    different claims.
    """
    result = _run(_REPO_ROOT)
    assert "Route modules scanned:" in result.stdout, result.stdout
    scanned = int(result.stdout.split("Route modules scanned:")[1].split()[0])
    assert scanned >= 50, f"only {scanned} route modules scanned — the glob has narrowed"


def test_it_reports_did_not_run_separately_from_pass_and_fail(tmp_path):
    """Exit 2 when it cannot find backend/routes — not 0, and not 1.

    Any check that depends on something outside itself has three outcomes,
    and this script is one of the few here built knowing that.

    **Reaching the branch takes more than changing directory.** My first
    version of this test ran the script with ``cwd=tmp_path`` and asserted
    exit 2; it got 0, because ``ROUTES_DIR`` is resolved from ``__file__``
    and is therefore cwd-independent — which is the script being right, not
    wrong. Copying the script so its ``parents[1]`` is an empty tree is what
    actually removes ``backend/routes`` from under it.
    """
    import shutil

    fake_scripts = tmp_path / "scripts"
    fake_scripts.mkdir()
    shutil.copy2(SCRIPT, fake_scripts / SCRIPT.name)

    result = subprocess.run(
        [sys.executable, str(fake_scripts / SCRIPT.name)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=120,
    )
    assert result.returncode == 2, (
        f"expected exit 2 (environment error) when backend/routes is absent, got "
        f"{result.returncode}. Reporting 'did not run' as a pass is how a gate stops "
        f"meaning anything.\n{result.stdout}\n{result.stderr}"
    )
    assert "not found" in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize("aggregator", ["audit", "engagements", "export"])
def test_known_aggregators_are_still_recognised(aggregator):
    """The aggregator list is hand-maintained; assert it still matches.

    If an aggregator is renamed, the modules it mounts become invisible to
    the check and it keeps reporting success on fewer routes.
    """
    result = _run(_REPO_ROOT)
    assert aggregator in result.stdout, (
        f"'{aggregator}' no longer appears in the check's output; the aggregator list in "
        f"scripts/check_route_wiring.py has stopped matching the tree"
    )
