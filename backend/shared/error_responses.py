"""One constructor for every error response (Sprint 872, AZ-14).

Every error the API returns — from a route, an exception handler, a
middleware, or the raw ASGI body-size guard — has the same body::

    {"code": str, "message": str, "request_id": str, "detail": ...}

and an ``X-Request-ID`` header equal to ``request_id``. ``detail`` keeps
its historical meaning (the ``HTTPException.detail`` value, which the
frontend reads for coded errors) and defaults to ``message``.

The request ID is resolved here rather than trusted to the middleware
order: rate-limit rejections from ``DefaultLimitMiddleware`` and unhandled
500s are rendered *outside* ``RequestIdMiddleware``, where the context
variable is not set. Resolution order: the ID ``RequestIdMiddleware``
stored on the request scope, the context variable, a well-formed client
``X-Request-ID``, then a fresh ID.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Mapping, MutableMapping
from typing import Any, Optional

from starlette.responses import JSONResponse

from logging_config import request_id_var
from shared.schemas import ErrorResponse

REQUEST_ID_RE = re.compile(r"^[a-zA-Z0-9\-]{1,64}$")
SCOPE_STATE_KEY = "request_id"

STATUS_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    410: "GONE",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}

_UNSET: Any = object()


def default_code(status_code: int) -> str:
    return STATUS_CODES.get(status_code, f"HTTP_{status_code}")


def resolve_request_id(scope: Optional[MutableMapping[str, Any]] = None) -> str:
    """The request's correlation ID — see the module docstring for the order."""
    if scope is not None:
        state = scope.get("state")
        stored = state.get(SCOPE_STATE_KEY) if isinstance(state, Mapping) else None
        if stored:
            return str(stored)
    from_var = request_id_var.get("-")
    if from_var and from_var != "-":
        return from_var
    rid: str
    if scope is not None:
        for key, value in scope.get("headers", []):
            if key.lower() == b"x-request-id":
                candidate = value.decode("latin-1")
                if REQUEST_ID_RE.match(candidate):
                    rid = candidate
                    break
        else:
            rid = uuid.uuid4().hex[:12]
    else:
        rid = uuid.uuid4().hex[:12]
    if scope is not None:
        state = scope.setdefault("state", {})
        if isinstance(state, MutableMapping):
            state[SCOPE_STATE_KEY] = rid
    return rid


def error_body(
    status_code: int,
    message: str,
    *,
    request_id: str,
    code: Optional[str] = None,
    detail: Any = _UNSET,
) -> dict[str, Any]:
    body = ErrorResponse(code=code or default_code(status_code), message=message, request_id=request_id).model_dump()
    body["detail"] = message if detail is _UNSET else detail
    return body


def error_response(
    status_code: int,
    message: str,
    *,
    scope: Optional[MutableMapping[str, Any]] = None,
    code: Optional[str] = None,
    detail: Any = _UNSET,
    headers: Optional[Mapping[str, str]] = None,
) -> JSONResponse:
    """Build the error response. Pass ``request.scope`` (or the ASGI scope)."""
    rid = resolve_request_id(scope)
    body = error_body(status_code, message, request_id=rid, code=code, detail=detail)
    response = JSONResponse(status_code=status_code, content=body, headers=dict(headers) if headers else None)
    response.headers["X-Request-ID"] = rid
    return response


async def send_error(
    send: Any,
    scope: MutableMapping[str, Any],
    status_code: int,
    message: str,
    *,
    code: Optional[str] = None,
) -> None:
    """Raw-ASGI variant for middleware that runs below Starlette's Response."""
    rid = resolve_request_id(scope)
    payload = json.dumps(error_body(status_code, message, request_id=rid, code=code)).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(payload)).encode()],
                [b"x-request-id", rid.encode("latin-1")],
            ],
        }
    )
    await send({"type": "http.response.body", "body": payload})
