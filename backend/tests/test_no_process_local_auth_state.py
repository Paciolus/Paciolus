"""Sprint 718 — AST guardrail: no module-global mutable state in auth modules.

Pre-Sprint-718 the IP failure tracker lived as a module-level
``_ip_failure_tracker: dict[str, list[float]] = {}`` in
``security_middleware.py``. Per-worker, per-process, lost on deploy. This
test scans the auth-relevant modules for any new such pattern so the
class of bug can't silently come back.

Allowed at module scope:
- Constants (Final[...], all-caps names, primitive scalars).
- Plain string / int / float assignments (configuration constants).
- Logger instances (``_logger = logging.getLogger(__name__)``).
- Lazily-initialized object refs whose value is None (Redis client
  pattern in ``shared/impersonation_revocation.py``).
- ``threading.Lock()`` / ``threading.RLock()`` for guarding the
  lazy-init dance — Locks are not mutable state per se.

Forbidden at module scope (without an explicit allowlist comment):
- ``dict()``, ``{}``, ``OrderedDict()``, ``defaultdict(...)``
- ``list()``, ``[]``
- ``set()``, ``frozenset()`` is OK if the contents are static
- Any custom mutable container

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
BACKEND_DIR = REPO_ROOT / "backend"

# Files where module-mutable scans are most load-bearing.
SCANNED_FILES: tuple[Path, ...] = (
    BACKEND_DIR / "auth.py",
    BACKEND_DIR / "security_middleware.py",
)

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
    """SCREAMING_SNAKE_CASE convention indicates 'this is a constant, do not mutate'.

    Names matching this pattern are exempt from the mutable-state scan; the
    convention is socially load-bearing and PRs that mutate them get flagged
    by reviewers. The scan targets the *real* hazard: lowercase-named
    mutable globals used as per-process counters / caches.
    """
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
        # SCREAMING_SNAKE_CASE = constant convention; not the hazard we target.
        if all(_is_constant_naming(name) for name in targets):
            continue
        for name in targets:
            if not _is_constant_naming(name):
                findings.append((node.lineno, name))

    return findings


# ───────────────────────── Tests ─────────────────────────


@pytest.mark.parametrize("path", SCANNED_FILES, ids=lambda p: p.name)
def test_no_module_global_mutable_state(path: Path):
    """Module-level dict/list/set assignments are forbidden in auth modules.

    To override (rare), add ``# allow-module-mutable: <reason>`` on the
    same line as the assignment.
    """
    assert path.is_file(), f"Scanned file does not exist: {path}"
    findings = _scan_file(path)
    if findings:
        lines = [f"Module-level mutable state in {path.relative_to(REPO_ROOT)}:"]
        for lineno, name in findings:
            lines.append(f"  line {lineno}: {name}")
        lines.append(
            "Move state to `shared/ip_failure_tracker.py`-style Redis-with-fallback module, "
            "or add `# allow-module-mutable: <reason>` if the storage is intentionally local."
        )
        pytest.fail("\n".join(lines))
