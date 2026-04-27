"""Sprint 720 — AST guardrail: no module-global mutable state in routes/.

Pre-Sprint-720 ``routes/bulk_upload.py`` carried job state in a module-
level ``_bulk_jobs: OrderedDict[str, dict]``. Per-worker, per-process,
lost on deploy. The 2026-04-24 Guardian audit (#1.4) flagged it.

This test scans every file under ``backend/routes/`` for any new such
pattern so the bug class can't silently come back. Same pattern as
``tests/test_no_process_local_auth_state.py`` but scoped to routes.

Allowed at module scope:
- Constants (Final[...], SCREAMING_SNAKE_CASE, primitive scalars).
- Logger instances (``logger = logging.getLogger(__name__)``).
- ``router = APIRouter(...)`` and similar framework registrations.
- Lazily-initialized object refs whose value is None (Redis client
  pattern in ``shared/impersonation_revocation.py``).
- ``threading.Lock()`` / ``threading.RLock()`` for guarding lazy init.

Forbidden at module scope (without an explicit allowlist comment):
- ``dict()``, ``{}``, ``OrderedDict()``, ``defaultdict(...)``
- ``list()``, ``[]``
- ``set()``
- Any custom mutable-container factory listed in MUTABLE_FACTORY_NAMES.

Mechanism: walk ``ast.parse`` of each scanned file, inspect every
top-level ``Assign`` / ``AnnAssign``, and fail if the RHS is a literal
mutable container OR a known-mutable factory call.

Allowlist syntax: a ``# allow-module-mutable: <reason>`` comment on the
same line as the assignment exempts it. Use sparingly.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTES_DIR = REPO_ROOT / "backend" / "routes"

MUTABLE_LITERAL_TYPES: tuple[type[ast.AST], ...] = (ast.Dict, ast.List, ast.Set)
MUTABLE_FACTORY_NAMES: frozenset[str] = frozenset(
    {
        "dict",
        "list",
        "set",
        "OrderedDict",
        "defaultdict",
        "deque",
        "Counter",
    }
)


def _is_mutable_assignment(value_node: ast.AST | None) -> bool:
    """Return True if `value_node` constructs a mutable container."""
    if value_node is None:
        return False
    if isinstance(value_node, MUTABLE_LITERAL_TYPES):
        return True
    if isinstance(value_node, ast.Call):
        func = value_node.func
        if isinstance(func, ast.Name) and func.id in MUTABLE_FACTORY_NAMES:
            return True
        if isinstance(func, ast.Attribute) and func.attr in MUTABLE_FACTORY_NAMES:
            return True
    return False


def _line_has_allowlist(source_text: str, lineno: int) -> bool:
    """Check whether the source line at `lineno` (1-indexed) carries an allowlist comment."""
    lines = source_text.splitlines()
    if 0 < lineno <= len(lines):
        return "# allow-module-mutable" in lines[lineno - 1]
    return False


def _is_constant_naming(name: str) -> bool:
    """SCREAMING_SNAKE_CASE convention indicates 'this is a constant'."""
    bare = name.lstrip("_")
    return bool(bare) and bare.isupper()


def _scan_file(path: Path) -> list[tuple[int, str]]:
    """Return list of (lineno, target_name) for every disallowed top-level mutable assignment."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    findings: list[tuple[int, str]] = []

    for node in tree.body:
        targets: list[str] = []
        value_node: ast.AST | None = None

        if isinstance(node, ast.Assign):
            value_node = node.value
            for target in node.targets:
                if isinstance(target, ast.Name):
                    targets.append(target.id)
        elif isinstance(node, ast.AnnAssign):
            value_node = node.value
            if isinstance(node.target, ast.Name):
                targets.append(node.target.id)
        else:
            continue

        if not targets:
            continue
        if not _is_mutable_assignment(value_node):
            continue
        if _line_has_allowlist(source, node.lineno):
            continue
        if all(_is_constant_naming(name) for name in targets):
            continue
        for name in targets:
            if not _is_constant_naming(name):
                findings.append((node.lineno, name))

    return findings


def _route_files() -> list[Path]:
    """Every .py file in backend/routes/, excluding __init__.py and __pycache__."""
    return sorted(p for p in ROUTES_DIR.glob("*.py") if p.name != "__init__.py" and p.is_file())


# ───────────────────────── Tests ─────────────────────────


def test_routes_directory_exists():
    """Sanity check: backend/routes/ exists and has files."""
    files = _route_files()
    assert files, "backend/routes/ scan produced zero files"


@pytest.mark.parametrize("path", _route_files(), ids=lambda p: p.name)
def test_no_module_global_mutable_state(path: Path):
    """Module-level dict/list/set assignments are forbidden in route modules.

    Move state to a ``shared/`` Redis-with-fallback module (see
    ``shared/bulk_job_store.py``, ``shared/ip_failure_tracker.py``,
    ``shared/impersonation_revocation.py`` for templates) so it is
    visible across workers and survives deploys.

    To override (rare — only for genuinely process-local caches with
    no cross-worker correctness implications), add
    ``# allow-module-mutable: <reason>`` on the same line as the
    assignment.
    """
    findings = _scan_file(path)
    if findings:
        lines = [f"Module-level mutable state in backend/routes/{path.name}:"]
        for lineno, name in findings:
            lines.append(f"  line {lineno}: {name}")
        lines.append(
            "Per Sprint 720 (multi-worker discipline): mutable state in route modules is per-worker, "
            "lost on deploy, and breaks under multi-worker Render. Move to a shared/ Redis-with-fallback "
            "module, or add `# allow-module-mutable: <reason>` if the storage is intentionally local."
        )
        pytest.fail("\n".join(lines))
