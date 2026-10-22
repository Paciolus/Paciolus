"""The glob in ``model_registry`` must still match every ORM module.

Sprint 797 replaced three hand-maintained import lists (holding 11, 15 and 15
entries) with one glob over ``models.py`` plus ``*_model.py``. A glob beats a
list because it grows on its own — but it is still a convention, and the
module that breaks a convention is usually the oldest one, which is usually
the one with the least coverage. Sprint 792 learned that the hard way: a
guard enumerating ``services/audit/*/analysis.py`` missed the ADR-018 pilot
at ``services/audit/flux/recon.py``, the single module predating the naming
rule it enumerated by.

So the glob is cross-checked here against an oracle that does not share its
assumption: an AST scan of **every** Python file under ``backend/`` for
classes inheriting ``Base``. If someone adds ``billing/invoice_tables.py``
with three models in it, the glob will not see it and this test will say so
by name.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from model_registry import import_all_models, model_module_names  # noqa: E402

# Directories that cannot contain production ORM models.
_SKIP_PARTS = {"venv", "__pycache__", "_pytest_tmp", "migrations", "tests", "node_modules", "scripts"}


def _modules_defining_orm_models() -> dict[str, list[str]]:
    """AST oracle: ``{module_name: [ClassName, ...]}`` for classes based on ``Base``.

    Deliberately independent of the registry's glob — it looks at what the
    files *declare*, not at what they are *called*.
    """
    found: dict[str, list[str]] = {}
    for path in _BACKEND_ROOT.rglob("*.py"):
        if any(part in _SKIP_PARTS for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            # Report rather than skip: an unparseable file is a hole in the
            # oracle, and a silent hole is how a coverage check becomes a
            # rubber stamp.
            raise AssertionError(f"Could not parse {path} while scanning for ORM models")
        classes = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and any(isinstance(b, ast.Name) and b.id == "Base" for b in node.bases)
        ]
        if classes:
            rel = path.relative_to(_BACKEND_ROOT)
            module = ".".join(rel.with_suffix("").parts)
            found[module] = classes
    return found


def test_glob_finds_every_module_that_defines_an_orm_model():
    declared = _modules_defining_orm_models()
    assert declared, "the AST oracle found no ORM models at all — it has broken, not the registry"

    registered = set(model_module_names())
    missed = sorted(set(declared) - registered)

    assert not missed, (
        f"{len(missed)} module(s) define ORM models but do not match the registry's glob: "
        f"{ {m: declared[m] for m in missed} }. Either rename the module to `*_model.py`, or "
        f"widen `model_registry.model_module_names()` — leaving it unmatched means its tables "
        f"are missing from create_all() on every fresh deployment."
    )


def test_registry_names_no_module_that_defines_no_models():
    """The other direction: a stale entry is dead weight that reads as coverage."""
    declared = _modules_defining_orm_models()
    extra = sorted(set(model_module_names()) - set(declared))
    assert not extra, f"registry names {extra}, which define no ORM models"


def test_import_all_models_populates_every_declared_table():
    """Importing the registry must make Base.metadata complete.

    The property that actually matters — the two tests above compare names,
    this one compares the result.
    """
    import_all_models()
    from database import Base

    declared_classes = sum(len(v) for v in _modules_defining_orm_models().values())
    assert len(Base.metadata.tables) >= declared_classes, (
        f"{declared_classes} ORM classes are declared but Base.metadata holds only {len(Base.metadata.tables)} tables"
    )


def test_registry_is_not_trivially_small():
    """A glob that matches nothing is indistinguishable from one that matches
    nothing wrong. Assert it found work."""
    names = model_module_names()
    assert len(names) >= 15, f"registry shrank to {len(names)}: {names}"
