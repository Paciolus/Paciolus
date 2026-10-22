#!/usr/bin/env python3
"""Decide what an `npm audit` run actually told us — Sprint 794.

`npm audit` exits 1 both when it finds a vulnerability and when it could not
reach the advisory endpoint. Observed live on PR #189 (2026-10-22):

    npm warn audit 503 Service Unavailable - POST .../security/audits/quick
    npm error audit endpoint returned an error
    ##[error]Process completed with exit code 1.

No vulnerability existed. The job is named "CVE & License Audit" and the red X
is the same one a genuine CRITICAL produces, so the signal a reader gets is
"this PR ships a high-severity vulnerability" when the truth is "we could not
check." Those are different facts and they deserve different words.

So this classifier reports **three** outcomes, not two:

    CLEAN       a report came back and nothing at or above the threshold
    VULNERABLE  a report came back and it contains findings
    UNVERIFIED  no usable report came back — the audit did not happen

Whether UNVERIFIED should block a merge is a policy question and deliberately
NOT decided here (see `tasks/todo.md` Sprint 794 step 3); the caller decides.
This script's only job is to stop the two from being confused.

Discrimination is on the **payload**, not the exit code, because the exit code
is exactly what cannot tell them apart. A real report carries
`auditReportVersion` and `metadata.vulnerabilities`; the registry-failure body
carries `message`/`error` and neither of those. Anything unrecognised is
UNVERIFIED rather than CLEAN — an unreadable answer is not a clean bill of
health, and that is the direction this whole sprint exists to fix.
"""

from __future__ import annotations

import argparse
import json
import sys

# npm's severity ladder, lowest first. `--audit-level=high` means "fail on
# high and critical", so the threshold selects a suffix of this list.
SEVERITIES = ["info", "low", "moderate", "high", "critical"]

CLEAN = "CLEAN"
VULNERABLE = "VULNERABLE"
UNVERIFIED = "UNVERIFIED"


def _at_or_above(level: str) -> list[str]:
    """Severities at or above `level`. Unknown level means count everything."""
    if level not in SEVERITIES:
        return list(SEVERITIES)
    return SEVERITIES[SEVERITIES.index(level) :]


def classify(raw: str, npm_exit: int, audit_level: str) -> tuple[str, str]:
    """Return (verdict, human-readable reason).

    `npm_exit` is used only as a cross-check once a report has been parsed —
    never to distinguish failure modes, which is the bug being fixed.
    """
    text = (raw or "").strip()
    if not text:
        return UNVERIFIED, "npm produced no output at all — the audit did not run."

    try:
        report = json.loads(text)
    except ValueError:
        return UNVERIFIED, "npm output was not valid JSON — the audit did not complete."

    if not isinstance(report, dict):
        return UNVERIFIED, "npm output was not an audit report object."

    # The registry-failure body. Checked before the report shape so its reason
    # can quote npm's own wording back to the reader.
    if "auditReportVersion" not in report and "metadata" not in report:
        detail = report.get("message") or ""
        err = report.get("error")
        if not detail and isinstance(err, dict):
            detail = err.get("summary") or err.get("detail") or ""
        detail = str(detail).strip() or "no audit report was returned"
        return UNVERIFIED, f"the advisory endpoint did not return a report ({detail})."

    metadata = report.get("metadata")
    if not isinstance(metadata, dict):
        return (
            UNVERIFIED,
            "the audit report has no `metadata` block — shape not recognised.",
        )

    counts = metadata.get("vulnerabilities")
    if not isinstance(counts, dict):
        return (
            UNVERIFIED,
            "the audit report has no `metadata.vulnerabilities` — shape not recognised.",
        )

    relevant = _at_or_above(audit_level)
    hits = {}
    for sev in relevant:
        try:
            n = int(counts.get(sev, 0) or 0)
        except (TypeError, ValueError):
            return (
                UNVERIFIED,
                f"vulnerability count for `{sev}` was not a number — shape not recognised.",
            )
        if n:
            hits[sev] = n

    if hits:
        summary = ", ".join(f"{n} {sev}" for sev, n in hits.items())
        return VULNERABLE, f"the audit found {summary} (threshold: {audit_level})."

    # A parsed, empty report alongside a non-zero exit means npm failed for a
    # reason the report does not describe. Do not call that clean.
    if npm_exit != 0:
        return (
            UNVERIFIED,
            f"npm exited {npm_exit} but the report shows nothing at or above `{audit_level}` — "
            "the two disagree, so the result is not trustworthy.",
        )

    return CLEAN, f"no vulnerabilities at or above `{audit_level}`."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--npm-exit", type=int, required=True, help="exit status npm audit returned"
    )
    parser.add_argument(
        "--audit-level", default="high", help="lowest severity that counts as a finding"
    )
    args = parser.parse_args()

    verdict, reason = classify(sys.stdin.read(), args.npm_exit, args.audit_level)
    print(verdict)
    print(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
