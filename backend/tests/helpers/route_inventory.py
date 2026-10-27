"""Route inventory for tests — every route the app serves, prefixes applied.

FastAPI 0.137 stopped copying included routers' routes into the parent:
``app.routes`` now holds one ``_IncludedRouter`` node per ``include_router``
call, so iterating it directly sees ~54 nodes instead of ~257 routes, and the
nodes have no ``path``/``methods``/``endpoint``. A ``hasattr(r, "path")``
filter over that list silently yields almost nothing, which is how a route
inventory test passes while checking zero routes.

``fastapi.routing.iter_route_contexts`` (0.137.2) is the upstream replacement
for "iterate ``router.routes``". Each ``RouteContext`` exposes the *effective*
route: ``path`` carries the include prefix, ``dependencies``/``dependant``
include router-level dependencies, and ``endpoint``/``methods``/``name`` are
the original route's. ``original_route`` is the underlying ``APIRoute``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from fastapi.routing import APIRoute, RouteContext, iter_route_contexts
from starlette.routing import BaseRoute


class _HasRoutes(Protocol):
    @property
    def routes(self) -> Sequence[BaseRoute]: ...


def all_routes(app_or_router: _HasRoutes) -> list[RouteContext]:
    """Every route reachable from an app or router, nested includes flattened."""
    return list(iter_route_contexts(app_or_router.routes))


def api_routes(app_or_router: _HasRoutes) -> list[RouteContext]:
    """Only the path operations (``APIRoute``), excluding docs/static/mount routes."""
    return [r for r in all_routes(app_or_router) if isinstance(r.original_route, APIRoute)]
