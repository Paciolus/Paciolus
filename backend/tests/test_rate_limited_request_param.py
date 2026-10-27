"""
Sprint 812 guard — every rate-limited route must receive a real ``Request``.

slowapi's ``@limiter.limit`` reads the endpoint's ``request`` argument and
raises if it is not a ``starlette.requests.Request``. A handler that declares
``request: Any = None`` compiles, type-checks and passes every test — the
global conftest disables the limiter — while FastAPI quietly treats
``request`` as an optional **query parameter**. In production slowapi then
receives ``None`` and every call returns 500.

That shape sat on 19 Professional/Enterprise routes (organization, admin
dashboard, branding, export sharing, bulk upload) for seven months after the
2026-03-21 mypy cleanup (``8372073a``). These checks are mechanical so it
cannot recur silently.
"""

import sys
from pathlib import Path

from tests.helpers.route_inventory import api_routes

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.routing import RouteContext

from main import app
from shared.rate_limits import limiter


def _api_routes() -> list[RouteContext]:
    return api_routes(app)


def _limited_routes() -> list[RouteContext]:
    marked = limiter._Limiter__marked_for_limiting  # slowapi's registry of decorated endpoints
    return [r for r in _api_routes() if f"{r.endpoint.__module__}.{r.endpoint.__name__}" in marked]


def _label(route: RouteContext) -> str:
    return f"{sorted(route.methods)} {route.path} ({route.endpoint.__module__}.{route.endpoint.__name__})"


def test_guard_scans_the_rate_limited_population():
    """Vacuity check: the guard below must actually see the decorated routes."""
    assert len(_limited_routes()) >= 150, (
        f"only {len(_limited_routes())} rate-limited routes resolved — the registry lookup "
        "has drifted from slowapi's internals and the guard below is scanning nothing"
    )


def test_every_rate_limited_route_injects_the_request():
    missing = [_label(r) for r in _limited_routes() if not r.dependant.request_param_name]
    assert not missing, (
        "rate-limited routes whose `request` FastAPI will not inject — declare it as "
        "`request: Request` (from fastapi), never `request: Any = None`:\n  " + "\n  ".join(missing)
    )


def test_no_route_exposes_request_as_a_client_parameter():
    leaked = [
        _label(r)
        for r in _api_routes()
        if any(p.name == "request" for p in (*r.dependant.query_params, *r.dependant.body_params))
    ]
    assert not leaked, "routes exposing `request` as a query/body parameter:\n  " + "\n  ".join(leaked)
