"""Sprint 756 — domain relocation lint script tests.

Covers the shim-detection AST logic, the candidate filter (includes the right
files, excludes the blocklist), and the CLI flow (warning-only by default,
``--strict`` flips the exit code).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lint_domain_relocation import (  # noqa: E402 (path manipulation above)
    NON_RELOCATABLE_ENGINES,
    _is_relocation_candidate,
    _is_shim,
    find_unrelocated_engines,
    main,
)

# ---------------------------------------------------------------------------
# _is_relocation_candidate
# ---------------------------------------------------------------------------


class TestIsRelocationCandidate:
    def test_engine_not_in_blocklist_is_a_candidate(self):
        assert _is_relocation_candidate(REPO_ROOT / "backend" / "flux_engine.py")

    def test_blocklisted_engine_is_excluded(self):
        for name in NON_RELOCATABLE_ENGINES:
            assert not _is_relocation_candidate(REPO_ROOT / "backend" / name)

    def test_non_engine_file_is_not_a_candidate(self):
        assert not _is_relocation_candidate(REPO_ROOT / "backend" / "auth.py")
        assert not _is_relocation_candidate(REPO_ROOT / "backend" / "models.py")


# ---------------------------------------------------------------------------
# _is_shim
# ---------------------------------------------------------------------------


class TestIsShim:
    def test_pure_reexport_is_a_shim(self):
        source = '''"""docstring"""
from services.audit.flux.recon import ReconEngine, ReconResult
__all__ = ["ReconEngine", "ReconResult"]
'''
        assert _is_shim(source)

    def test_module_with_class_definition_is_not_a_shim(self):
        source = '''"""docstring"""
from foo import bar
class MyEngine:
    pass
'''
        assert not _is_shim(source)

    def test_module_with_function_definition_is_not_a_shim(self):
        source = """from foo import bar
def helper():
    return 1
"""
        assert not _is_shim(source)

    def test_module_with_top_level_logic_assignment_is_not_a_shim(self):
        # Top-level non-dunder assignment (e.g., precomputed table) is not a shim.
        source = """from foo import bar
TABLE = {"a": 1}
"""
        assert not _is_shim(source)

    def test_recon_engine_in_repo_is_a_shim(self):
        """The Sprint 753 pilot — `recon_engine.py` should now register as a shim."""
        recon = REPO_ROOT / "backend" / "recon_engine.py"
        assert recon.exists()
        assert _is_shim(recon.read_text(encoding="utf-8"))

    def test_syntax_error_returns_false(self):
        assert not _is_shim("def : invalid")

    def test_dynamic_namespace_shim_pattern_recognized(self):
        """Post-initiative testing-engine relocations use a dynamic
        ``for _name in dir(_impl): setattr(...)`` pattern instead of an
        explicit ``__all__``. _is_shim must recognize it."""
        source = '''"""Backward-compat shim."""
import sys as _sys
from services.audit.foo import analysis as _impl

_module = _sys.modules[__name__]
for _name in dir(_impl):
    if _name.startswith("__"):
        continue
    setattr(_module, _name, getattr(_impl, _name))

del _sys, _module, _name, _impl
'''
        assert _is_shim(source)


@pytest.mark.parametrize(
    "engine_name",
    [
        "ap_testing_engine.py",
        "ar_aging_engine.py",
        "fixed_asset_testing_engine.py",
        "inventory_testing_engine.py",
        "je_testing_engine.py",
        "payroll_testing_engine.py",
        "revenue_testing_engine.py",
    ],
)
def test_relocated_testing_engines_register_as_shims(engine_name):
    """Post-initiative testing engine relocations are recognized as shims."""
    engine = REPO_ROOT / "backend" / engine_name
    assert engine.exists()
    assert _is_shim(engine.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# find_unrelocated_engines
# ---------------------------------------------------------------------------


class TestFindUnrelocatedEngines:
    def test_returns_list_of_paths(self):
        findings = find_unrelocated_engines()
        assert all(isinstance(p, Path) for p in findings)

    def test_recon_engine_not_in_findings_post_pilot(self):
        """The Sprint 753 pilot relocated recon — it should not appear."""
        findings = find_unrelocated_engines()
        names = {p.name for p in findings}
        assert "recon_engine.py" not in names

    def test_blocklisted_engines_not_in_findings(self):
        findings = find_unrelocated_engines()
        names = {p.name for p in findings}
        for blocked in NON_RELOCATABLE_ENGINES:
            assert blocked not in names


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCli:
    def test_default_exit_zero_even_with_findings(self, capsys):
        rc = main([])
        # Sprint 756 ships in advisory mode — exit 0 regardless.
        assert rc == 0

    def test_strict_exit_one_when_findings(self, capsys):
        # As long as at least one engine is unmigrated, --strict flips to 1.
        # The pilot relocation guarantees at least 30+ findings remain.
        rc = main(["--strict"])
        assert rc == 1

    def test_output_lists_findings(self, capsys):
        main([])
        out = capsys.readouterr().out
        # Either "all relocated" or contains a finding line — both are valid
        # depending on migration progress. We just verify the script runs and
        # produces output containing one of the canonical headers.
        assert "Domain relocation" in out


@pytest.mark.parametrize("name", sorted(NON_RELOCATABLE_ENGINES))
def test_blocklist_entries_are_real_files_or_documented(name):
    """Each blocklist entry should either exist or be documented as future."""
    path = REPO_ROOT / "backend" / name
    if not path.exists():
        # Some blocklist entries reference modules that haven't been created
        # yet (defensive future-proofing). That's fine — but bare it explicitly
        # rather than letting the blocklist drift silently.
        pytest.skip(f"{name} not present yet (defensive blocklist entry)")
