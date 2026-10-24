"""
Sprint 819 — every file download is sent with Cache-Control: no-store.

A downloaded export is client financial data; only the export-share download
set no-store, so the other ~20 export endpoints left caching to the browser.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

sys.path.insert(0, str(Path(__file__).parent.parent))


def _app():
    from security_middleware import SecurityHeadersMiddleware

    async def export(_request):
        return Response(
            b"a,b\n1,2\n",
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="tb.csv"'},
        )

    async def own_policy(_request):
        return Response(
            b"x",
            headers={"Content-Disposition": 'attachment; filename="x.pdf"', "Cache-Control": "private, max-age=0"},
        )

    async def json_route(_request):
        return Response(b"{}", media_type="application/json")

    app = Starlette(routes=[Route("/export", export), Route("/own", own_policy), Route("/json", json_route)])
    app.add_middleware(SecurityHeadersMiddleware, production_mode=False)
    return app


@pytest.mark.anyio
async def test_attachments_are_no_store_and_a_route_policy_is_kept():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=_app()), base_url="http://t") as client:
        assert (await client.get("/export")).headers["cache-control"] == "no-store"
        assert (await client.get("/own")).headers["cache-control"] == "private, max-age=0"
        assert "cache-control" not in (await client.get("/json")).headers
