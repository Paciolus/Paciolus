"""Every CI job must be classified as required or advisory, with a reason.

WHY
---
`ci.yml`'s header claimed eleven jobs were required status checks. The live
`required_status_checks.contexts` for `main` held twelve, and the two sets
were not the same twelve:

* `openapi-drift-check` was **claimed required and was not**, so a PR could
  change the public API surface without regenerating the snapshot and merge
  with that job red.
* `backend-tests-postgres` **was required and was not claimed** — a real
  strengthening the header never recorded.
* Four jobs were neither listed nor required, including `accounting-policy`,
  which carries the monetary-precision, audit-immutability, ASC 606 and
  adjustment-gating invariants.

Meanwhile `CLAUDE.md`'s document authority hierarchy opens with "Executable
enforcement — ci.yml, Husky hooks. These are mechanically enforced and final."

WHAT THIS CAN AND CANNOT CHECK
------------------------------
It checks the manifest against the **workflow file**: every job key defined in
`ci.yml` appears in exactly one section of the header, and every name in the
header is a real job. That catches the drift that actually happens — a job
added or renamed and nobody deciding whether it blocks a merge.

It deliberately does **not** call the GitHub API. A check that needs a token
has three outcomes, not two (Sprint 794), and a gate that silently degrades to
"could not look" on an unauthenticated runner is worse than no gate. The live
contexts are recorded in the header with the date they were read, which is a
dated claim a human can re-verify, rather than a check that lies when the
token is missing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CI_PATH = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _read_ci() -> list[str]:
    assert CI_PATH.is_file(), f"{CI_PATH} not found — the manifest guard cannot run"
    return CI_PATH.read_text(encoding="utf-8").splitlines()


def _job_keys(lines: list[str]) -> set[str]:
    """Job keys: two-space-indented `name:` entries under the top-level `jobs:`.

    Parsed structurally rather than by searching the whole file for anything
    that looks like a job, because a parser that quietly matches less produces
    no signal at all — every downstream assertion keeps passing, on less.
    """
    jobs: set[str] = set()
    in_jobs = False
    for line in lines:
        if re.match(r"^jobs:\s*$", line):
            in_jobs = True
            continue
        if in_jobs:
            # A new top-level key ends the jobs block.
            if line and not line[0].isspace() and not line.startswith("#"):
                break
            m = re.match(r"^  ([A-Za-z0-9][A-Za-z0-9_-]*):\s*$", line)
            if m:
                jobs.add(m.group(1))
    return jobs


def _manifest_sections(lines: list[str]) -> dict[str, set[str]]:
    """Parse the REQUIRED / ADVISORY lists out of the header comment."""
    sections: dict[str, set[str]] = {"required": set(), "advisory": set()}
    current: str | None = None
    for line in lines:
        if not line.startswith("#"):
            if sections["required"] or sections["advisory"]:
                break
            continue
        body = line.lstrip("#").strip()
        if body.startswith("REQUIRED"):
            current = "required"
            continue
        if body.startswith("ADVISORY"):
            current = "advisory"
            continue
        if body.startswith("─") or body.startswith("GATE MANIFEST"):
            continue
        if current is None:
            continue
        m = re.match(r"^([a-z0-9][a-z0-9-]*)\b", body)
        if m and (body == m.group(1) or body[len(m.group(1)) :].lstrip().startswith("—")):
            sections[current].add(m.group(1))
    return sections


def test_the_manifest_parses_something():
    """A parser that matches nothing is indistinguishable from a clean run."""
    lines = _read_ci()
    jobs = _job_keys(lines)
    sections = _manifest_sections(lines)
    assert len(jobs) >= 15, f"only parsed {len(jobs)} job keys from ci.yml: {sorted(jobs)}"
    assert len(sections["required"]) >= 10, f"parsed {sections['required']} as required"
    assert len(sections["advisory"]) >= 7, f"parsed {sections['advisory']} as advisory"


def test_every_job_is_classified():
    lines = _read_ci()
    jobs = _job_keys(lines)
    sections = _manifest_sections(lines)
    classified = sections["required"] | sections["advisory"]

    unclassified = sorted(jobs - classified)
    assert not unclassified, (
        f"{len(unclassified)} CI job(s) appear in no section of the gate manifest: "
        f"{unclassified}. Add each to the REQUIRED or ADVISORY list in the ci.yml header "
        f"— deciding whether a gate blocks a merge is the point of the manifest."
    )


def test_the_manifest_names_no_job_that_does_not_exist():
    lines = _read_ci()
    jobs = _job_keys(lines)
    sections = _manifest_sections(lines)
    classified = sections["required"] | sections["advisory"]

    phantom = sorted(classified - jobs)
    assert not phantom, (
        f"the gate manifest names {phantom}, which are not jobs in ci.yml. A manifest entry "
        f"for a renamed job silently stops describing anything."
    )


def test_no_job_is_in_both_sections():
    sections = _manifest_sections(_read_ci())
    both = sorted(sections["required"] & sections["advisory"])
    assert not both, f"{both} classified as both required and advisory"


@pytest.mark.parametrize(
    "job",
    ["accounting-policy", "doc-consistency", "report-standards", "openapi-drift-check"],
)
def test_known_should_be_required_gates_are_still_flagged(job):
    """The four gates that produce a red X and merge anyway.

    This asserts the header keeps *saying so* until branch protection is
    changed. When one is made required, move it to the REQUIRED list and
    delete it from this parametrize — the test failing is the reminder.
    """
    lines = _read_ci()
    sections = _manifest_sections(lines)
    text = "\n".join(lines)
    assert job in sections["advisory"], (
        f"{job} is no longer listed as advisory. If it was added to branch protection, "
        f"move it to REQUIRED and drop it from this test."
    )
    assert re.search(rf"{re.escape(job)}\s+— SHOULD BE REQUIRED", text), (
        f"{job} is advisory but the manifest no longer says it should be required — "
        f"either it was deliberately downgraded (say why) or the note was lost."
    )
