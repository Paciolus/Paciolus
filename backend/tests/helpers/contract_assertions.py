"""
Sprint 810 (finding T-3) — assertions that test a contract instead of a presence.

The DEC review's F-005 corrected four test classes whose only assertion was
``assert callable(some_function)``. The full-spectrum review of 2026-10-22 found
**27 occurrences still standing across 10 files**, including
``test_billing_routes.py``, ``test_pricing_integration.py``,
``test_rate_limit_tiered.py`` and ``test_retention_cleanup.py`` — billing and
rate limiting.

Why ``assert callable(f)`` is close to worthless as a test: by the time the
assertion runs, the ``from module import f`` above it has already proved the
symbol exists, and *any* function satisfies ``callable``. It passes if the
parameters are renamed, reordered, or removed; it passes if the body is
``raise NotImplementedError``. It is a tautology dressed as coverage, and it
reads in a report as a tested function.

``assert_signature`` replaces it with something a rename or a dropped parameter
actually fails. That is not as strong as exercising behaviour — where behaviour
is cheap to exercise, do that instead and do not reach for this — but it is a
real contract, and it is applicable to the import-smoke sites where mocking the
whole of Stripe to assert one function exists would not be a good trade.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


def assert_signature(
    fn: Callable[..., Any],
    params: list[str],
    *,
    allow_extra: bool = False,
) -> None:
    """
    Assert `fn` is callable *and* takes exactly the named parameters, in order.

    Args:
        fn: the function or dependency to check.
        params: expected parameter names, in declaration order. ``self`` and
            ``cls`` should be omitted — they are stripped before comparison.
        allow_extra: when True, `params` is a required prefix rather than the
            whole signature. Use for functions that legitimately grow optional
            keyword arguments, and say so at the call site.

    Catches what ``callable()`` cannot: a renamed parameter, a reordered one, a
    removed one, or a symbol that is not a function at all.
    """
    assert callable(fn), f"{getattr(fn, '__name__', fn)!r} is not callable"

    signature = inspect.signature(fn)
    actual = [name for name in signature.parameters if name not in ("self", "cls")]

    name = getattr(fn, "__name__", repr(fn))
    if allow_extra:
        assert actual[: len(params)] == params, (
            f"{name} signature changed: expected it to start with {params}, got {actual}"
        )
    else:
        assert actual == params, f"{name} signature changed: expected {params}, got {actual}"


def assert_returns_dict_with(fn: Callable[..., Any], *keys: str, **kwargs: Any) -> dict[str, Any]:
    """
    Call `fn(**kwargs)` and assert the result is a dict carrying `keys`.

    For the registry and factory cases where invoking is cheap and proves
    something: a function that raises, or returns None, fails here and would
    have passed a `callable` check.
    """
    result = fn(**kwargs)
    assert isinstance(result, dict), f"{getattr(fn, '__name__', fn)} returned {type(result).__name__}, not a dict"
    for key in keys:
        assert key in result, f"{getattr(fn, '__name__', fn)} result is missing {key!r}"
    return result
