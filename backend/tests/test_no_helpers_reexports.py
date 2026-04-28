"""Sprint 724 — re-export shim guardrail.

After Sprint 724 removed the back-compat re-export block from
``backend/shared/helpers.py``, the module owns only a small set of native
helpers. This test prevents the shim from accidentally returning: it scans
every backend file for ``from shared.helpers import X`` and fails CI if X is
not in the explicit native-symbol allowlist.

Without this gate, a future PR could "fix" an import error by re-adding
``from shared.upload_pipeline import memory_cleanup as memory_cleanup`` to
``shared/helpers.py``, silently restoring the shim and re-introducing the
62-call-site forking pattern that motivated Sprint 724.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

sys.path.insert(0, str(BACKEND_ROOT))


# These are the symbols Sprint 724 deliberately keeps in shared.helpers. Any
# name imported from shared.helpers that is NOT in this set means either:
#   (a) someone re-introduced the shim (the bad case Sprint 724 banned), or
#   (b) someone added a new native helper without updating this allowlist
#       (acceptable; bump the allowlist with the addition).
ALLOWED_HELPER_NAMES: frozenset[str] = frozenset(
    {
        "try_parse_risk",
        "try_parse_risk_band",
        "parse_json_list",
        "parse_json_mapping",
        "is_authorized_for_client",
        "get_accessible_client",
        "require_client",
        "require_client_owner",  # Sprint 735 — direct-only client access dependency
    }
)


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for p in BACKEND_ROOT.rglob("*.py"):
        if "__pycache__" in p.parts or ".venv" in p.parts:
            continue
        # The helpers module itself is allowed to define anything — only
        # external imports of disallowed names are the concern.
        if p.resolve() == (BACKEND_ROOT / "shared" / "helpers.py").resolve():
            continue
        files.append(p)
    return files


def _imports_from_helpers(source: str) -> list[str]:
    """Return the list of symbol names imported from ``shared.helpers``.

    Aliased imports (``foo as bar``) are reported by the source name (``foo``)
    since that's the symbol exported from helpers; the alias is irrelevant to
    the allowlist.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = (node.module or "").lstrip(".")
            # Match both ``shared.helpers`` and (if some path tweak) ``backend.shared.helpers``.
            if mod in {"shared.helpers", "backend.shared.helpers"}:
                for alias in node.names:
                    imported.append(alias.name)
    return imported


class TestNoHelpersReexports:
    """The Sprint 724 guardrail."""

    def test_no_disallowed_imports(self):
        violations: list[tuple[Path, str]] = []
        for path in _iter_python_files():
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for name in _imports_from_helpers(source):
                if name not in ALLOWED_HELPER_NAMES:
                    violations.append((path.relative_to(REPO_ROOT), name))

        if violations:
            lines = [
                "Disallowed imports from shared.helpers detected:",
                "",
                "  Import the symbol from its owning module instead:",
                "    upload_pipeline symbols → shared.upload_pipeline",
                "    filename/CSV symbols    → shared.filenames",
                "    safe_background_email   → shared.background_email",
                "    maybe_record_tool_run / _log_tool_activity → shared.tool_run_recorder",
                "",
                "  If you genuinely added a new native helper to shared.helpers,",
                "  update ALLOWED_HELPER_NAMES in this test file alongside the addition.",
                "",
                "  Violations:",
            ]
            for path, name in violations:
                lines.append(f"    {path}: {name}")
            pytest.fail("\n".join(lines))

    def test_allowlist_matches_helpers_module_publics(self):
        """The allowlist should equal the actual public surface of shared.helpers.

        Catches drift the other direction: if someone removes a native helper
        from shared.helpers without updating the allowlist, this test reminds
        them to take it off the list.
        """
        from shared import helpers

        # Public surface = top-level names that don't start with underscore and
        # are defined in the module (not re-imports). We use ``getattr`` +
        # ``__module__`` to filter out re-imported names (FluxRisk, RiskBand, etc.).
        public_natives: set[str] = set()
        for name in dir(helpers):
            if name.startswith("_"):
                continue
            obj = getattr(helpers, name)
            obj_module = getattr(obj, "__module__", None)
            # Functions defined in the module itself have ``__module__ == "shared.helpers"``.
            # Re-imported types/enums (FluxRisk, etc.) have a different module.
            if obj_module == "shared.helpers" and callable(obj):
                public_natives.add(name)

        # The allowlist is the contract; the module must publish exactly that surface.
        missing_from_module = ALLOWED_HELPER_NAMES - public_natives
        extra_in_module = public_natives - ALLOWED_HELPER_NAMES

        msgs: list[str] = []
        if missing_from_module:
            msgs.append(
                f"Allowlist names not exported by shared.helpers: {sorted(missing_from_module)}. "
                "Either restore the helper or remove the name from ALLOWED_HELPER_NAMES."
            )
        if extra_in_module:
            msgs.append(
                f"shared.helpers exports names not in allowlist: {sorted(extra_in_module)}. "
                "Either add to ALLOWED_HELPER_NAMES or move the helper to its owning module."
            )
        if msgs:
            pytest.fail("\n".join(msgs))
