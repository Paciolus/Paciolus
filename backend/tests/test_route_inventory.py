"""Sprint 786b — the route inventory helper must see every route the app serves.

~60 test files enumerate routes through ``tests.helpers.route_inventory``.
If the helper ever went blind (as plain ``app.routes`` did on FastAPI 0.137,
dropping from 257 routes to 54 include nodes), those tests would keep passing
while checking almost nothing. This pins the inventory to an independent
source — the generated OpenAPI document — so blindness fails loudly.
"""

from main import app
from tests.helpers.route_inventory import all_routes, api_routes

_HTTP_METHODS = {"get", "put", "post", "delete", "patch", "options", "head", "trace"}


def test_inventory_is_not_vacuous():
    # 253 path operations as of Sprint 786b; the floor leaves room for removals.
    assert len(api_routes(app)) >= 240


def test_inventory_paths_carry_router_prefixes():
    paths = {r.path for r in all_routes(app)}
    assert "/health/ready" in paths
    assert "/auth/refresh" in paths
    # Declared as "/subscription" on APIRouter(prefix="/billing").
    assert "/billing/subscription" in paths


def test_inventory_matches_openapi_operations():
    """Every documented operation is in the inventory, and vice versa."""
    from_inventory = {(method.lower(), r.path) for r in api_routes(app) if r.include_in_schema for method in r.methods}
    from_openapi = {
        (method, path) for path, item in app.openapi()["paths"].items() for method in item if method in _HTTP_METHODS
    }
    assert from_inventory == from_openapi
