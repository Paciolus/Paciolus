r"""Find a `bash` that actually runs — Sprint 786b.

WHY THIS EXISTS
`backend/tests/test_npm_audit_gate.py` and `test_pip_audit_gate.py` exercise
their gate scripts end to end, so they need a working bash. They originally
guarded that with

    BASH = shutil.which("bash")
    @pytest.mark.skipif(not BASH, reason=...)

which asks whether bash **exists**, not whether it **works**. On this Windows
host two bash flavours sit on PATH:

    C:\\Program Files\\Git\\usr\\bin\\bash.exe              works
    C:\\Users\\...\\AppData\\Local\\Microsoft\\WindowsApps\\bash.exe   exits 1 on `-c "exit 0"`

The second is the Store/WSL launcher, inert without a WSL distribution
installed. Interactively, Git's bash comes first and everything passes. The
2026-10-22 nightly runs from a different session with a different PATH order,
picked up the WindowsApps stub, and **every one of the 14 tests that spawns
bash failed** — while every test that does not spawn bash passed, including
the one asserting the gate scripts exist. The nightly went RED on a tooling
difference with nothing wrong in the code under test.

That is the same confusion the gates themselves were written to fix: a check
that establishes presence and reports it as capability. `which` answering is
not the tool answering.

So this probes. The first candidate that returns 0 from `bash -c "exit 0"`
wins; if none does, callers skip rather than fail, because "no usable bash on
this host" is a real and acceptable state for a developer machine — unlike
"bash is right there and every invocation returns garbage", which is a lie.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

# Git for Windows ships bash in both of these; neither is always on PATH.
_FALLBACKS = (
    r"C:\Program Files\Git\usr\bin\bash.exe",
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\usr\bin\bash.exe",
    "/bin/bash",
    "/usr/bin/bash",
)


def _candidates() -> list[str]:
    """Every plausible bash, best-guess order, de-duplicated."""
    found: list[str] = []

    def add(path: str | None) -> None:
        if path and path not in found:
            found.append(path)

    add(shutil.which("bash"))
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        for name in ("bash.exe", "bash"):
            candidate = Path(directory) / name
            if candidate.exists():
                add(str(candidate))
    for fallback in _FALLBACKS:
        if Path(fallback).exists():
            add(fallback)
    return found


def _runs(path: str) -> bool:
    try:
        result = subprocess.run([path, "-c", "exit 0"], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


@lru_cache(maxsize=1)
def usable_bash() -> str | None:
    """Path to a bash that executes a trivial command successfully, or None.

    Probed once per process — the subprocess cost is small but it is paid at
    import time by `skipif` decorators in several modules.
    """
    for candidate in _candidates():
        if _runs(candidate):
            return candidate
    return None


NEEDS_BASH = "no working bash on this host (a bash on PATH that cannot execute does not count)"


def bash_support_path() -> list[str]:
    r"""Directories a spawned bash needs on PATH to be useful.

    Invoking Git Bash on Windows is not enough on its own: `dirname`, `sed`
    and friends live beside the binary in `Git\usr\bin`, and a script that
    calls them fails with `dirname: command not found` if that directory is
    absent. Reproduced by running the gate suites under a minimal PATH — the
    gate exited 2 on exactly that error.

    On Linux CI this is moot, which is precisely why it was invisible there
    and surfaced only in the nightly on this Windows host.

    Also includes the directory of the interpreter running the tests, so the
    gate's own `command -v python3 || command -v python` resolves to the
    same Python pytest is using rather than to whatever the ambient
    environment happens to offer.
    """
    entries: list[str] = []

    bash = usable_bash()
    if bash:
        entries.append(str(Path(bash).parent))

    entries.append(str(Path(sys.executable).parent))
    return [e for e in entries if e]
