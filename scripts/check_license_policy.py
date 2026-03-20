#!/usr/bin/env python3
"""
License policy enforcement script.
Reads pip-licenses JSON and license-checker JSON outputs, compares against
the policy file, and exits non-zero if any prohibited license is found.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def load_policy(policy_path: str) -> dict:
    with open(policy_path, encoding="utf-8") as f:
        return json.load(f)


def extract_spdx_ids(license_str: str) -> set[str]:
    """Split a compound SPDX expression into individual license identifiers.

    Handles expressions like "Apache-2.0 AND LGPL-3.0-or-later",
    "MIT OR BSD-2-Clause", and semicolon/comma-separated lists.
    """
    # Normalize separators: AND, OR, semicolons, commas, parentheses
    parts = re.split(r"\s+AND\s+|\s+OR\s+|[;,()]+", license_str, flags=re.IGNORECASE)
    return {p.strip() for p in parts if p.strip()}


def is_prohibited(license_str: str, prohibited: set[str]) -> str | None:
    """Return the first prohibited match found, or None."""
    prohibited_lower = {p.lower() for p in prohibited}
    for spdx_id in extract_spdx_ids(license_str):
        if spdx_id.lower() in prohibited_lower:
            return spdx_id
    return None


def check_python_licenses(licenses_path: str, policy: dict) -> list[dict]:
    violations = []
    with open(licenses_path, encoding="utf-8") as f:
        packages = json.load(f)
    allowlist = {entry["package"].lower() for entry in policy.get("allowlist", [])}
    prohibited = set(policy.get("prohibited", []))
    for pkg in packages:
        name = pkg.get("Name", "").lower()
        license_str = pkg.get("License", "UNKNOWN")
        if name in allowlist:
            continue
        match = is_prohibited(license_str, prohibited)
        if match:
            violations.append({
                "ecosystem": "python",
                "package": pkg.get("Name"),
                "version": pkg.get("Version"),
                "license": license_str,
                "prohibited_match": match,
            })
    return violations


def check_node_licenses(licenses_path: str, policy: dict) -> list[dict]:
    violations = []
    with open(licenses_path, encoding="utf-8") as f:
        packages = json.load(f)
    allowlist = {entry["package"].lower() for entry in policy.get("allowlist", [])}
    prohibited = set(policy.get("prohibited", []))
    for pkg_key, pkg_data in packages.items():
        name = pkg_key.rsplit("@", 1)[0].lower()
        license_str = pkg_data.get("licenses", "UNKNOWN")
        if name in allowlist:
            continue
        match = is_prohibited(license_str, prohibited)
        if match:
            violations.append({
                "ecosystem": "node",
                "package": pkg_key,
                "license": license_str,
                "prohibited_match": match,
            })
    return violations


def main():
    parser = argparse.ArgumentParser(description="License policy enforcement")
    parser.add_argument("--python-licenses", required=True)
    parser.add_argument("--node-licenses", required=True)
    parser.add_argument("--policy", required=True)
    args = parser.parse_args()

    policy = load_policy(args.policy)
    violations = []
    violations += check_python_licenses(args.python_licenses, policy)
    violations += check_node_licenses(args.node_licenses, policy)

    if violations:
        print("LICENSE POLICY VIOLATIONS FOUND:")
        for v in violations:
            print(
                f"  [{v['ecosystem']}] {v['package']} — "
                f"{v['license']} (matches prohibited: {v['prohibited_match']})"
            )
        print(
            "\nTo resolve: either upgrade to a version with a compatible license, "
            "replace the dependency, or add a reviewed entry to "
            "docs/compliance/LICENSE_POLICY.json allowlist."
        )
        sys.exit(1)
    else:
        print(f"License policy check passed. {len(violations)} violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
