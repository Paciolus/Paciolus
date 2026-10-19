#!/usr/bin/env python3
"""Print the commit SHA of the currently-live Render deploy.

Used by .github/workflows/uptime-check.yml to detect deploy drift — a
deploy that was merged but never actually landed. Render keeps the previous
image serving when a new deploy fails at startup, so from outside nothing
appears to change: that is how the Sprint 768 security fixes sat undeployed
for ~5.5 months.

Reads from stdin the JSON body of:
    GET https://api.render.com/v1/services/{serviceId}/deploys?limit=N

Prints the SHA of the first deploy whose status is "live", or nothing at all
if there is none. Exits 0 either way — an empty line is the caller's signal
to treat the result as unknown, so a Render API hiccup is distinguishable
from a real drift.

The Render API returns either a list of {"deploy": {...}} wrappers or a bare
list of deploy objects depending on endpoint version, so both are handled.
"""

import json
import sys


def live_sha(payload: object) -> str:
    """Return the commit SHA of the first live deploy, or "" if none."""
    if not isinstance(payload, list):
        return ""
    for row in payload:
        if not isinstance(row, dict):
            continue
        deploy = row.get("deploy", row)
        if not isinstance(deploy, dict):
            continue
        if deploy.get("status") != "live":
            continue
        commit = deploy.get("commit")
        if isinstance(commit, dict):
            return str(commit.get("id") or "")
        return ""
    return ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — unparseable body is "unknown", not fatal
        print("")
        return
    print(live_sha(payload))


if __name__ == "__main__":
    main()
