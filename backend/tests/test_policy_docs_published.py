"""Sprint 862: the website shows the compliance documents exactly as written.

`docs/04-compliance/` is the single source. `scripts/sync_policy_docs.py`
copies the Security Policy, Subprocessor List and Data Handling Architecture
into `frontend/src/content/policies.generated.ts`, which the `/security`,
`/subprocessors` and `/data-handling` pages render. If someone edits a
document and forgets to re-run the script, the site would show stale text —
this test fails instead.
"""

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load_sync_script():
    spec = importlib.util.spec_from_file_location("sync_policy_docs", REPO / "scripts" / "sync_policy_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_module_matches_the_documents():
    sync = _load_sync_script()
    # Git may check the file out with CRLF on Windows; compare content, not line endings.
    generated = (REPO / "frontend/src/content/policies.generated.ts").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert generated == sync.render(), (
        "frontend/src/content/policies.generated.ts is out of date with docs/04-compliance/. "
        "Run: python scripts/sync_policy_docs.py"
    )


def test_each_published_document_has_a_page():
    sync = _load_sync_script()
    for _name, (_filename, route) in sync.PUBLISHED.items():
        page = REPO / "frontend/src/app/(marketing)" / route.lstrip("/") / "page.tsx"
        assert page.exists(), f"{route} has no page at {page.relative_to(REPO)}"
