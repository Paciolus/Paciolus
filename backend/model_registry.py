"""Single source of truth for "which modules define ORM models".

WHY THIS EXISTS
---------------
Three hand-maintained copies of this list existed, and they had drifted:

===================================================  ========
Location                                             Modules
===================================================  ========
``database.init_db()``                                     11
``migrations/alembic/env.py``                              15
``tests/test_alembic_models_parity.py``                    15
===================================================  ========

The comment above the 11-entry list read *"Ensure ALL model modules are
imported so Base.metadata sees every table"*, and the parity test's read
*"Keep this list in sync with init_db() and env.py"*. Neither was true.

The consequence was not cosmetic. ``Dockerfile`` runs ``alembic stamp head``
— not ``upgrade`` — when a database has no ``alembic_version`` table, so a
brand-new environment gets its schema entirely from ``create_all()``. With
four modules missing from ``init_db()``, measured results were:

* ``init_db()`` alone                     → 25 of 29 tables
* ``import main`` then ``init_db()``      → 27 of 29 tables

The two that survived even the real entrypoint were ``admin_audit_logs``
(the superadmin audit trail, Sprint 590) and ``dunning_episodes`` (the
failed-payment workflow, Sprint 591) — and because ``stamp head`` had already
marked their migrations as applied, no later deploy would ever create them.
A new region or a fresh staging environment booted healthy and 500'd the first
time an admin action was logged or a payment failed.

HOW THE SET IS DERIVED
----------------------
By convention every ORM module in this package is either ``models.py`` or
``*_model.py`` at the backend root. :func:`model_module_names` globs for
exactly that, so the set grows automatically when a module is added.

A glob is weaker than deriving from the system and stronger than a hand list
(the Sprint 792 ranking). The remaining gap — a module that defines models but
does not match the naming convention — is closed by
``tests/test_model_registry.py``, which AST-scans the whole backend for classes
inheriting ``Base`` and asserts the glob found every module that has one. The
oldest module is usually the one that breaks a convention, so the convention
alone is not enough to rely on.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

BACKEND_ROOT = Path(__file__).resolve().parent

# Modules matching the glob that are not ORM model modules. Empty today; kept
# explicit so an exclusion has to be argued for rather than silently added to
# a pattern.
_NOT_MODEL_MODULES: frozenset[str] = frozenset()


def model_module_names() -> list[str]:
    """Return the sorted import names of every ORM model module."""
    names = {"models"}
    for path in BACKEND_ROOT.glob("*_model.py"):
        names.add(path.stem)
    return sorted(names - _NOT_MODEL_MODULES)


def import_all_models() -> list[ModuleType]:
    """Import every ORM model module so ``Base.metadata`` is complete.

    Call this before ``Base.metadata.create_all()`` or before Alembic
    autogenerate. Returns the imported modules so a caller can assert on the
    count if it wants to.
    """
    return [importlib.import_module(name) for name in model_module_names()]
