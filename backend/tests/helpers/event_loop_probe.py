"""Probe: does a route keep the event loop free while its blocking work runs? (Sprint 890, CEO brief 15E)

``blocking_stand_in()`` returns a function to patch over a blocking dependency (a Stripe call, an S3
put, a ZIP inspection, a database check). It signals when it is entered, then waits until the test
releases it. ``run_probe()`` starts the blocking request, waits until the stand-in is entered, then
sends a lightweight request (``GET /health/live``) and requires it to finish while the stand-in is
still held. If the blocking work ran on the event loop, the light request cannot run, the stand-in's
wait times out, and the probe fails.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

HOLD_SECONDS = 3.0


class BlockingStandIn:
    def __init__(self, result: Any = None) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        self.timed_out = False
        self.result = result

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.entered.set()
        if not self.release.wait(HOLD_SECONDS):
            self.timed_out = True
        return self.result() if callable(self.result) else self.result


def blocking_stand_in(result: Any = None) -> BlockingStandIn:
    return BlockingStandIn(result)


async def run_probe(
    stand_in: BlockingStandIn,
    send_blocking_request: Callable[[httpx.AsyncClient], Awaitable[httpx.Response]],
) -> httpx.Response:
    """Return the blocking request's response, after asserting the loop stayed free."""
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        task = asyncio.create_task(send_blocking_request(client))
        entered = await asyncio.to_thread(stand_in.entered.wait, HOLD_SECONDS + 2)
        assert entered, "the blocking dependency was never reached"
        light = await client.get("/health/live")
        still_held = not stand_in.release.is_set() and not stand_in.timed_out
        stand_in.release.set()
        response = await task
    assert light.status_code == 200
    assert still_held and not stand_in.timed_out, (
        "a lightweight request could not run while the blocking work was held: it runs on the event loop"
    )
    return response
