#!/usr/bin/env python3
"""Decide what a `pip-audit` run actually told us — Sprint 794b.

The Python half of Sprint 794a. `pip-audit` exits 1 when it finds a
vulnerability **and** when it cannot reach the service it needs, exactly as
`npm audit` does. Captured from pip-audit 2.10.1:

    nothing vulnerable    exit 0   {"dependencies": [{..., "vulns": []}], "fixes": []}
    real vulnerability    exit 1   same shape, "vulns" non-empty
    service unreachable   exit 1   nothing on stdout at all

So the exit code cannot separate rows 2 and 3, and the payload can.

A fourth record shape exists and must not be mistaken for a broken one: when
pip-audit cannot resolve a dependency (an editable install, a URL
requirement, a package absent from PyPI) it emits `{"name", "skip_reason"}`
with no `version` and no `vulns`, and still exits 0. Only `--strict` turns a
skip into a failure. Reading that as a malformed schema — as the first draft
did — silently enables strict mode.

Same three verdicts as the npm classifier:

    CLEAN       a report came back and it lists no vulnerabilities
    VULNERABLE  a report came back and it lists some
    UNVERIFIED  no usable report came back — the audit did not happen

Deliberately a separate module from `classify_npm_audit.py` rather than a
shared abstraction: the two tools emit different schemas, and npm has a
severity threshold while pip-audit has none (these gates fail on *any*
finding). The shared part is the three-verdict vocabulary, which is a
convention rather than code. Unifying the retry shell would have meant
rewiring three CI call sites that are already verified green, for no change
in behaviour.

Whether UNVERIFIED should block is not decided here (Sprint 794 step 3); the
caller decides. This module's only job is to stop the two from being confused.
"""

from __future__ import annotations

import argparse
import json
import sys

CLEAN = "CLEAN"
VULNERABLE = "VULNERABLE"
UNVERIFIED = "UNVERIFIED"

# How many package names to name before summarising the rest.
_MAX_NAMED = 5


def classify(raw: str, pip_exit: int) -> tuple[str, str]:
    """Return (verdict, human-readable reason).

    `pip_exit` is used only as a cross-check once a report has been parsed —
    never to distinguish failure modes, which is the bug being fixed.
    """
    text = (raw or "").strip()
    if not text:
        return (
            UNVERIFIED,
            "pip-audit produced no report on stdout — the audit did not run.",
        )

    try:
        report = json.loads(text)
    except ValueError:
        return (
            UNVERIFIED,
            "pip-audit output was not valid JSON — the audit did not complete.",
        )

    if not isinstance(report, dict):
        return UNVERIFIED, "pip-audit output was not an audit report object."

    dependencies = report.get("dependencies")
    if not isinstance(dependencies, list):
        return (
            UNVERIFIED,
            "the report has no `dependencies` list — shape not recognised.",
        )

    affected: list[str] = []
    skipped: list[str] = []
    audited = 0
    total_vulns = 0
    for dep in dependencies:
        if not isinstance(dep, dict):
            return (
                UNVERIFIED,
                "a dependency entry was not an object — shape not recognised.",
            )

        # A skipped dependency is a SUPPORTED record, not a malformed one.
        # pip-audit's JSON formatter emits `{"name", "skip_reason"}` with no
        # `version` and no `vulns` when it cannot resolve a package — an
        # editable install, a URL requirement, something absent from PyPI. It
        # still exits 0; only `--strict` turns a skip into a failure.
        #
        # Treating the missing `vulns` key as a broken schema (as the first
        # draft did — PR #193 review) made every such run UNVERIFIED, retried
        # it three times, and failed the blocking gates. That is `--strict`
        # behaviour smuggled in under a change that claimed to leave the
        # gating policy alone.
        if "skip_reason" in dep:
            skipped.append(
                f"{dep.get('name', '<unnamed>')} ({dep.get('skip_reason', 'no reason given')})"
            )
            continue

        vulns = dep.get("vulns")
        if vulns is None:
            # Not skipped and no `vulns`: the schema always emits one or the
            # other, so this really is a shape we do not recognise.
            return (
                UNVERIFIED,
                f"dependency {dep.get('name', '<unnamed>')!r} has neither `vulns` nor `skip_reason`.",
            )
        if not isinstance(vulns, list):
            return UNVERIFIED, "a `vulns` field was not a list — shape not recognised."
        audited += 1
        if vulns:
            # Deduplicate by advisory id. pip-audit 2.10.1 emits each advisory
            # once per vulnerability source, so a jinja2 2.11.3 audit returns
            # eight entries for four distinct advisories. Counting raw entries
            # would report double the real number in a line a human reads to
            # decide how alarmed to be.
            seen: list[str] = []
            for v in vulns:
                if not isinstance(v, dict):
                    continue
                vid = str(v.get("id", "?"))
                if vid not in seen:
                    seen.append(vid)
            affected.append(
                f"{dep.get('name', '<unnamed>')} {dep.get('version', '')}".strip()
                + f" ({', '.join(seen)})"
            )
            total_vulns += len(seen)

    skip_note = ""
    if skipped:
        shown_skips = skipped[:_MAX_NAMED]
        more_skips = len(skipped) - len(shown_skips)
        skip_note = (
            f" {len(skipped)} package(s) were skipped and are therefore unchecked: "
            + "; ".join(shown_skips)
            + (f"; and {more_skips} more" if more_skips else "")
            + "."
        )

    if affected:
        shown = affected[:_MAX_NAMED]
        more = len(affected) - len(shown)
        summary = "; ".join(shown) + (f"; and {more} more" if more else "")
        return (
            VULNERABLE,
            f"the audit found {total_vulns} vulnerability(ies) in {len(affected)} package(s): {summary}.{skip_note}",
        )

    # A parsed, empty report alongside a non-zero exit means pip-audit failed
    # for a reason the report does not describe. Do not call that clean.
    if pip_exit != 0:
        return (
            UNVERIFIED,
            f"pip-audit exited {pip_exit} but the report lists no vulnerabilities — "
            f"the two disagree, so the result is not trustworthy.{skip_note}",
        )

    # Skips do not fail the gate — but a report in which *everything* was
    # skipped establishes nothing, and calling that CLEAN would be the exact
    # failure this sprint exists to prevent: reporting safety that was never
    # checked. This is a narrow rule, not `--strict`: any single audited
    # package is enough to keep the normal verdict.
    if audited == 0 and skipped:
        return (
            UNVERIFIED,
            f"every one of the {len(skipped)} package(s) in the report was skipped, so nothing "
            f"was actually audited.{skip_note}",
        )

    return CLEAN, f"no known vulnerabilities across {audited} package(s).{skip_note}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pip-exit", type=int, required=True, help="exit status pip-audit returned"
    )
    args = parser.parse_args()

    verdict, reason = classify(sys.stdin.read(), args.pip_exit)
    print(verdict)
    print(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
