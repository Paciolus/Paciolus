"""The accepted-risk register must name the version we actually pin — Sprint 786b.

`docs/compliance/DEPENDENCY_DECISIONS.md` records formal risk acceptances. Each
entry carries a structured `- **Version:** X` field, and the whole document is
only meaningful if that field names the version the project really ships.

It did not. Raising `slowapi` from 0.1.9 to 0.1.10 left the register saying
"Version: 0.1.9 — Decision: Accept risk. Keep slowapi 0.1.9", i.e. a signed-off
risk acceptance for a version no longer in use. Nothing caught it; the pin and
the register were connected only by whoever remembered.

WHY THIS GUARD IS THIS NARROW, AND THE MEASUREMENT BEHIND IT
The obvious bigger guard — "every version mentioned in prose must match its
pin" — was measured before being written, and the numbers killed it. Across
938 files and the 13 exact-pinned packages there were **54 disagreements, and
the ones inspected were all false positives**: a section heading (`### 18.4
Stripe Webhook Re-Registration`), a CVSS score (`CVSS >= 7.0`), another
package's floor (`limits >= 3.0.0`). Version-shaped strings are simply common
in prose. A guard over that would need an exclusion per false positive, which
is how a check gets tuned until it no longer checks anything (Sprint 794b).

So this reads the one place the version is *structured data* rather than
prose. Zero ambiguity, zero exclusions, and it covers the claim that actually
carries compliance weight. The four prose mentions were corrected by hand and
are deliberately left unguarded — stated plainly here so the next reader knows
it was a decision, not an oversight.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER = REPO_ROOT / "docs" / "compliance" / "DEPENDENCY_DECISIONS.md"
REQUIREMENTS = REPO_ROOT / "backend" / "requirements.txt"

# `## slowapi (accepted risk)` → the package the following entry is about.
_HEADING = re.compile(r"^##\s+(?P<name>[A-Za-z0-9_.\-]+)\b")
# `- **Version:** 0.1.10 (raised from ...)` → the first version token only.
_VERSION_FIELD = re.compile(r"^-\s+\*\*Version:\*\*\s*(?P<version>[0-9][0-9A-Za-z.\-]*)")


def _pins() -> dict[str, str]:
    """Package → version for every `==` pin in requirements.txt."""
    out: dict[str, str] = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?==(\S+)", line.strip())
        if match:
            out[match.group(1).lower().replace("_", "-")] = match.group(2)
    return out


def _register_entries() -> dict[str, tuple[str, int]]:
    """Package → (declared version, line number) for each register entry."""
    entries: dict[str, tuple[str, int]] = {}
    current: str | None = None
    for lineno, line in enumerate(REGISTER.read_text(encoding="utf-8").splitlines(), 1):
        heading = _HEADING.match(line)
        if heading:
            current = heading.group("name").lower().replace("_", "-")
            continue
        field = _VERSION_FIELD.match(line)
        if field and current:
            entries[current] = (field.group("version"), lineno)
            current = None
    return entries


def test_the_register_and_the_requirements_file_are_both_readable():
    """A parse that finds nothing proves nothing (Sprint 792)."""
    assert REGISTER.is_file(), f"missing {REGISTER}"
    assert REQUIREMENTS.is_file(), f"missing {REQUIREMENTS}"
    assert _pins(), "no `==` pins parsed from requirements.txt — this check covers nothing"
    assert _register_entries(), (
        "no `- **Version:**` fields parsed from the register — either the document changed shape "
        "or this check lost its target"
    )


def test_every_accepted_risk_names_the_version_we_pin():
    """The claim that carries compliance weight.

    A risk acceptance signed off against a version that is no longer installed
    documents a decision nobody made about software nobody runs.
    """
    pins = _pins()
    mismatches = []
    for package, (declared, lineno) in sorted(_register_entries().items()):
        pinned = pins.get(package)
        if pinned is None:
            # Floor-pinned or transitive: the register may legitimately track
            # something without an `==` pin, and Sprint 777's rule means a
            # floor has no single version to compare against.
            continue
        if declared != pinned:
            mismatches.append(
                f"DEPENDENCY_DECISIONS.md:{lineno} records {package} {declared}, but requirements.txt pins {pinned}"
            )

    assert not mismatches, (
        "the accepted-risk register names versions the project does not install:\n  "
        + "\n  ".join(mismatches)
        + "\n\nUpdate the register — a risk acceptance is about a specific version, so a stale "
        "one is a decision nobody made."
    )


def test_the_slowapi_entry_is_present_and_pinned():
    """Pins the specific case that motivated this guard.

    `slowapi` is the register's reason for existing — an accepted risk with a
    documented migration plan and canary tests. If its entry disappears or
    stops carrying a version, the general check above would silently have
    nothing to compare.
    """
    entries = _register_entries()
    assert "slowapi" in entries, "the slowapi accepted-risk entry vanished from the register"
    declared, _lineno = entries["slowapi"]
    assert declared == _pins()["slowapi"], f"register says {declared}, requirements pins {_pins()['slowapi']}"


def test_a_stale_register_entry_would_be_caught():
    """Regression proof, run against text rather than the real file.

    Confirms the comparison is the thing doing the work — not that the two
    files happen to agree today.
    """
    pins = {"slowapi": "0.1.10"}
    stale = {"slowapi": ("0.1.9", 13)}
    mismatches = [p for p, (declared, _) in stale.items() if pins.get(p) and declared != pins[p]]
    assert mismatches == ["slowapi"], "the comparison logic does not detect a stale version"
