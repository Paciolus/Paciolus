"""
Threshold-gated string similarity (Sprint 815).

The fuzzy loops in AP vendor-variation, payroll address matching and the
three-way-match fallback compare every pair of names — quadratic — and only
use ``SequenceMatcher.ratio()`` when it clears a threshold. ``ratio()`` is the
expensive call. ``real_quick_ratio()`` and ``quick_ratio()`` are documented
upper bounds on it, so a pair that fails either bound cannot pass; checking
them first changes no result. Measured on 2,000 vendors: 88.1s → 14.2s, the
same 670 hits.

Argument order is preserved deliberately: ``ratio()`` is not symmetric, and
swapping ``a`` and ``b`` changed the hit count (668 vs 670) in that measurement.
"""

from difflib import SequenceMatcher
from typing import Optional


def similarity_at_least(a: str, b: str, threshold: float) -> Optional[float]:
    """Return ``SequenceMatcher(None, a, b).ratio()`` if it is >= ``threshold``, else None."""
    matcher = SequenceMatcher(None, a, b)
    if matcher.real_quick_ratio() < threshold or matcher.quick_ratio() < threshold:
        return None
    ratio = matcher.ratio()
    return ratio if ratio >= threshold else None
