r"""The bash probe — Sprint 786b.

`tests/helpers/shell_support.py` exists because `shutil.which("bash")` answers
the wrong question. It reports that *a* bash is on PATH; the gate suites need
one that *runs*. On this Windows host both are present:

    C:\Program Files\Git\usr\bin\bash.exe                        works
    C:\Users\...\Local\Microsoft\WindowsApps\bash.exe            exits 1

The second is the Store/WSL launcher, inert with no WSL distribution. Which
one `which` returns depends on PATH order, which differs between an
interactive session and the nightly cron. On 2026-10-22 the nightly picked the
inert one and **all 14 tests that spawn bash failed**, while every test that
does not spawn bash passed — including the one asserting the gate scripts
exist. The nightly went RED with nothing wrong in the code under test.

The probe is now the thing those suites depend on, so it needs its own tests:
a helper that silently stops discriminating would restore the original bug
while looking fixed.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.helpers import shell_support
from tests.helpers.shell_support import bash_support_path, usable_bash


def test_the_probe_returns_a_bash_that_actually_runs():
    """Whatever it returns must satisfy the property it is probing for."""
    found = usable_bash()
    if found is None:
        pytest.skip("no working bash on this host")
    result = subprocess.run([found, "-c", "exit 0"], capture_output=True, timeout=30)
    assert result.returncode == 0, f"{found} was returned but does not run"


def test_a_bash_that_exists_but_fails_is_rejected(tmp_path, monkeypatch):
    """The whole point, reproduced rather than described.

    A stub named `bash` that exits 1 is exactly what the WindowsApps launcher
    does. `shutil.which` is happy with it; the probe must not be.
    """
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    for name in ("bash", "bash.exe"):
        stub = bin_dir / name
        stub.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        stub.chmod(0o755)

    monkeypatch.setenv("PATH", str(bin_dir))
    shell_support.usable_bash.cache_clear()
    try:
        found = usable_bash()
        assert found != str(bin_dir / "bash"), "the probe accepted a bash that exits 1"
        assert found != str(bin_dir / "bash.exe"), "the probe accepted a bash that exits 1"
        # It may legitimately return None (nothing else reachable) or a real
        # bash located through the fallback list. Either is correct; accepting
        # the broken stub is not.
        if found is not None:
            assert subprocess.run([found, "-c", "exit 0"], capture_output=True, timeout=30).returncode == 0
    finally:
        shell_support.usable_bash.cache_clear()


def test_the_probe_looks_past_the_first_candidate(tmp_path, monkeypatch):
    """A broken bash first on PATH must not shadow a working one behind it.

    This is the nightly's exact situation: `which` returns the inert launcher
    because it happens to come first.
    """
    real = usable_bash()
    if real is None:
        pytest.skip("no working bash on this host")

    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    for name in ("bash", "bash.exe"):
        stub = bin_dir / name
        stub.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        stub.chmod(0o755)

    monkeypatch.setenv("PATH", os.pathsep.join([str(bin_dir), str(Path(real).parent)]))
    shell_support.usable_bash.cache_clear()
    try:
        found = usable_bash()
        assert found is not None, "a working bash was on PATH but the probe gave up at the broken one"
        assert subprocess.run([found, "-c", "exit 0"], capture_output=True, timeout=30).returncode == 0
    finally:
        shell_support.usable_bash.cache_clear()


def test_support_path_includes_the_bash_directory_and_the_interpreter():
    """What the gate scripts actually need in order to work.

    `dirname` and `sed` live beside bash in `Git\\usr\\bin`; without that
    directory the gate dies with `dirname: command not found` — reproduced
    under a minimal PATH, which is how this was found.
    """
    entries = bash_support_path()
    assert entries, "bash_support_path returned nothing"
    assert str(Path(sys.executable).parent) in entries, (
        "the interpreter running the tests must be reachable, so the gate's "
        "`command -v python3 || command -v python` resolves to it"
    )
    found = usable_bash()
    if found is not None:
        assert str(Path(found).parent) in entries, "the bash directory must be on the support path"


def test_the_probe_is_cached_so_it_does_not_fork_per_decorator():
    """`skipif` evaluates at import in several modules; probe once."""
    assert hasattr(shell_support.usable_bash, "cache_clear"), "the probe should be lru_cache'd"
    shell_support.usable_bash.cache_clear()
    first = usable_bash()
    info = shell_support.usable_bash.cache_info()
    second = usable_bash()
    assert first == second
    assert shell_support.usable_bash.cache_info().hits > info.hits
