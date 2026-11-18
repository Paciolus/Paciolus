"""Exact JSON numbers for monetary Decimals — Sprint 884 (TQ-12 / OUT-19).

Pydantic writes a Decimal into JSON as a string and a float with at most 17
significant digits, so an amount such as 90,071,992,547,409.93 either changed
type or came back as ...409.94. The API keeps amounts as JSON *numbers* (the
frontend reads numbers) but with their exact digits:

- ``exact_number(d)`` returns a plain float when the float's shortest form is
  exactly ``d`` (every everyday amount), so most responses are unchanged.
- Otherwise it returns a marker string carrying the exact digits and a secret
  generated at process start. ``ExactNumberMiddleware`` rewrites each marker in
  a JSON response body into the bare number before the response leaves.

A marker can only be produced by this module, and the secret means no value a
user sends can be mistaken for one. If a marker were ever written somewhere
other than an HTTP response it would read as an odd string, never as a wrong
amount.
"""

from __future__ import annotations

import json
import re
import secrets
from collections.abc import Callable, Coroutine
from decimal import Decimal
from typing import Annotated, Any

from fastapi import Request, Response
from fastapi.routing import APIRoute
from pydantic import PlainSerializer, SerializationInfo, WithJsonSchema
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from shared.monetary import ensure_supported_amount

_SECRET = secrets.token_hex(12)
_PREFIX = f"\x00exact:{_SECRET}:"
_SUFFIX = "\x00"
# A JSON encoder always writes NUL as \u0000.
_ESCAPED_NUL = b"\\" + b"u0000"  # the six characters \u0000 as they appear in JSON text
_MARKER_PROBE = _ESCAPED_NUL + b"exact:" + _SECRET.encode()
_MARKER_RE = re.compile(b'"' + re.escape(_MARKER_PROBE) + rb":(-?[0-9]+(?:\.[0-9]+)?)" + re.escape(_ESCAPED_NUL) + b'"')


def exact_number(value: Any) -> float | str:
    """A JSON-ready form of a monetary amount whose digits survive exactly."""
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    ensure_supported_amount(d)
    as_float = float(d)
    if Decimal(repr(as_float)) == d:
        return as_float
    text = format(d, "f")
    return f"{_PREFIX}{text}{_SUFFIX}"


def exact_numbers(obj: Any) -> Any:
    """``obj`` with every Decimal (at any depth) passed through ``exact_number``."""
    if isinstance(obj, Decimal):
        return exact_number(obj)
    if isinstance(obj, dict):
        return {k: exact_numbers(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [exact_numbers(v) for v in obj]
    return obj


def restore_exact_numbers(body: bytes) -> bytes:
    """Replace each exact-number marker in a JSON body with the bare number."""
    if _MARKER_PROBE not in body:
        return body
    return _MARKER_RE.sub(rb"\1", body)


def _serialize_money(value: Decimal, info: SerializationInfo) -> Any:
    # JSON: the exact number. Python-mode dumps keep the float they always gave.
    return exact_number(value) if info.mode_is_json() else float(value)


# Stores and validates as Decimal; sends as an exact JSON number.
ExactMoney = Annotated[
    Decimal,
    PlainSerializer(_serialize_money, when_used="always"),
    WithJsonSchema({"type": "number"}, mode="serialization"),
]


class ExactNumberMiddleware:
    """Rewrite exact-number markers in JSON responses (see module docstring).

    Registered innermost, so it sees the body before GZip compresses it. Only
    ``application/json`` responses are buffered — they are built whole anyway.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start: Message | None = None
        chunks: list[bytes] = []

        async def wrapped_send(message: Message) -> None:
            nonlocal start
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers") or [])
                if headers.get(b"content-type", b"").startswith(b"application/json"):
                    start = message
                    return
                await send(message)
                return
            if message["type"] == "http.response.body" and start is not None:
                chunks.append(message.get("body", b""))
                if message.get("more_body"):
                    return
                body = restore_exact_numbers(b"".join(chunks))
                headers = [(k, v) for k, v in start.get("headers", []) if k.lower() != b"content-length"]
                headers.append((b"content-length", str(len(body)).encode()))
                await send({**start, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return
            await send(message)

        await self.app(scope, receive, wrapped_send)


class DecimalJSONRequest(Request):
    """A request whose JSON body reads decimal numbers as ``Decimal``, not float.

    Sprint 884 (TQ-12): an export that receives amounts back from the client
    (the financial statements export takes the lead-sheet grouping) lost
    digits when the body was parsed: 90071992547409.93 became ...409.94 before
    the builder saw it.
    """

    async def json(self) -> Any:
        if not hasattr(self, "_json"):
            self._json = json.loads(await self.body(), parse_float=Decimal)
        return self._json


class DecimalBodyRoute(APIRoute):
    """Route class for endpoints whose JSON body must keep exact amounts."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def decimal_body_handler(request: Request) -> Response:
            return await handler(DecimalJSONRequest(request.scope, request.receive))

        return decimal_body_handler
