"""
Sprint 821 — no route handler is ``async def`` without awaiting anything.

FastAPI runs ``def`` handlers in a threadpool and ``async def`` handlers on the
event loop. An ``async def`` that never awaits but makes synchronous database
calls blocks the loop for every request in the process while it runs. 41 route
handlers had that shape (31 of them touching the database); they are now plain
``def``. A handler that genuinely awaits something stays ``async``.
"""

import ast
from pathlib import Path

ROUTES = Path(__file__).resolve().parent.parent / "routes"


def _is_route(node: ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(d, ast.Call)
        and isinstance(d.func, ast.Attribute)
        and isinstance(d.func.value, ast.Name)
        and d.func.value.id == "router"
        for d in node.decorator_list
    )


def test_no_async_route_handler_without_an_await():
    offenders = []
    scanned = 0
    for path in sorted(ROUTES.glob("*.py")):
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.AsyncFunctionDef) and _is_route(node):
                scanned += 1
                if not any(isinstance(n, (ast.Await, ast.AsyncFor, ast.AsyncWith)) for n in ast.walk(node)):
                    offenders.append(f"{path.name}:{node.lineno} {node.name}")
    assert scanned > 20, f"only {scanned} async route handlers found — the scan has lost its target"
    assert offenders == [], "async route handlers that never await (make them `def`):\n  " + "\n  ".join(offenders)
