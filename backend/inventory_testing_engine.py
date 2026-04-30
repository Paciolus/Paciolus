"""Backward-compatibility shim for the inventory_testing_engine module.

The implementation moved to ``services.audit.inventory_testing.analysis``
per ADR-018 (testing-engine relocation batch). This module re-exports
the full namespace — every non-dunder symbol on the canonical path
(public + underscore-prefixed test helpers) — so existing
``from inventory_testing_engine import ...`` statements continue to work.

Why dynamic re-export instead of explicit ``__all__``: the canonical
analysis module exposes 35+ public symbols plus several
underscore-prefixed test helpers that ``tests/test_inventory_testing*.py``
imports directly. Listing each by hand would invite drift; the
namespace copy below stays in sync automatically.

New code should import from ``services.audit.inventory_testing.analysis``.
"""

import sys as _sys

from services.audit.inventory_testing import analysis as _impl

_module = _sys.modules[__name__]
for _name in dir(_impl):
    # Skip dunders + the loop-local names themselves.
    if _name.startswith("__"):
        continue
    if _name in ("_impl", "_sys", "_module", "_name"):
        continue
    setattr(_module, _name, getattr(_impl, _name))

# Cleanup loop-local names so they don't pollute the shim's public surface.
del _sys, _module, _name, _impl
