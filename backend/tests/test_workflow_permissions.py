"""Sprint 852 (security review L13): dependency-compliance runs read-only.

Without a ``permissions:`` block a workflow gets the repository's default
GITHUB_TOKEN scopes, which can include write access. dependency-compliance runs
on every pull request and only reads code, so it is pinned to
``contents: read`` and no job may widen that.
"""

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "dependency-compliance.yml"


def test_dependency_compliance_is_read_only():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert workflow.get("permissions") == {"contents": "read"}
    widened = {name: job["permissions"] for name, job in workflow["jobs"].items() if "permissions" in job}
    assert widened == {}, f"jobs widen the token scope: {widened}"
