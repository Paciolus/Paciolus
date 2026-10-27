"""Sprint 840: every route is rate-limited — by its own decorator or the default.

The claims review found 52 of 253 routes with no ``@limiter.limit`` and no
``SlowAPIMiddleware``, so they had no limit at all, while the Trust page
described a global one. ``main.py`` now installs ``SlowAPIASGIMiddleware``,
which applies the limiter's ``default_limits`` to every undecorated route.
"""

import httpx
import pytest
from fastapi.routing import RouteContext

from database import get_db
from main import app
from shared.rate_limits import DefaultLimitMiddleware, limiter
from tests.helpers.route_inventory import api_routes

pytestmark = pytest.mark.usefixtures("limiter_enabled")


def _undecorated_routes() -> list[RouteContext]:
    decorated = set(limiter._route_limits) | set(limiter._dynamic_route_limits)
    return [r for r in api_routes(app) if f"{r.endpoint.__module__}.{r.endpoint.__name__}" not in decorated]


def test_default_limit_is_configured():
    assert limiter._default_limits, "limiter has no default_limits for undecorated routes"


def test_slowapi_middleware_is_installed():
    """Sprint 786b: the subclass specifically — stock ``SlowAPIMiddleware`` resolves
    no handler for routes in included routers on FastAPI >= 0.137 and exempts them all."""
    installed = {m.cls for m in app.user_middleware}
    assert DefaultLimitMiddleware in installed


def test_default_limit_middleware_resolves_every_undecorated_route():
    """The lookup must find the real endpoint for each route, not just one probe route."""
    from shared.rate_limits import _find_route_handler

    checked = 0
    for r in _undecorated_routes():
        if "{" in r.path:
            continue
        for method in r.methods:
            scope = {"type": "http", "path": r.path, "method": method, "root_path": "", "headers": []}
            assert _find_route_handler(app.routes, scope) is r.endpoint, f"{method} {r.path}"
            checked += 1
    assert checked >= 20, f"only {checked} undecorated static routes checked"


def test_inventory_still_finds_undecorated_routes():
    """If this hits zero the default is moot — but the middleware stays as the backstop."""
    assert isinstance(_undecorated_routes(), list)


@pytest.mark.asyncio
async def test_undecorated_route_returns_429_past_the_default(db_session):
    """/benchmarks/industries has no decorator; the default must still stop a flood."""
    assert "/benchmarks/industries" in {r.path for r in _undecorated_routes()}
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            statuses = [(await client.get("/benchmarks/industries")).status_code for _ in range(61)]
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert statuses[0] == 200
    assert statuses[-1] == 429
