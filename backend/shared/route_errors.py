"""
Shared route error response utility (Sprint 745 — Phase 1.2).

Centralizes the "raise sanitized `HTTPException` with structured-log
metadata" pattern that's been copy-pasted across route modules. Wraps:

  - `sanitize_error` — strips internal details (paths, SQL fragments, secrets).
  - `log_secure_operation` — structured log entry for incident triage.

Consumers should reach for `db_transaction` (in `shared.db_unit_of_work`)
for the database commit/rollback/500 case. `raise_http_error` covers the
other 4xx + service-error cases:

    # 4xx with user-facing message:
    raise_http_error(400, label="upload_format", user_message="Bad file format.")

    # 4xx derived from a caller-passed exception (passthrough mode):
    try:
        do_business_logic()
    except ValueError as e:
        raise_http_error(400, label="business_logic", exception=e, allow_passthrough=True)

    # 5xx for non-DB service errors (e.g. third-party API):
    try:
        stripe_call()
    except StripeError as e:
        raise_http_error(502, label="stripe_charge", exception=e, operation="default")
"""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException

from security_utils import log_secure_operation
from shared.error_messages import sanitize_error


def raise_http_error(
    status_code: int,
    *,
    label: str,
    user_message: str | None = None,
    exception: Exception | None = None,
    operation: str = "default",
    allow_passthrough: bool = False,
) -> NoReturn:
    """
    Raise `HTTPException` with sanitized detail and structured-log metadata.

    Args:
        status_code: HTTP status (400, 403, 404, 409, 500, 502, ...).
        label: Stable label for log routing / incident triage.
        user_message: Explicit user-facing message. Wins over derived
            messages when supplied. If both `user_message` and `exception`
            are provided, the exception is logged but the user sees only
            `user_message`.
        exception: Caught exception. Used for sanitization + log content
            when `user_message` is omitted.
        operation: One of `"export"`, `"upload"`, `"analysis"`, `"default"`
            — controls fallback message in `sanitize_error` when neither
            a known pattern nor passthrough applies.
        allow_passthrough: When True and `user_message` is not provided,
            `sanitize_error` may surface the exception's message verbatim
            if it doesn't contain internal details (paths, SQL, secrets).
            Use for business-logic `ValueError` whose message is already
            user-facing.

    Raises:
        HTTPException: Always.
    """
    if exception is not None and user_message is None:
        detail = sanitize_error(
            exception,
            operation=operation,
            log_label=label,
            allow_passthrough=allow_passthrough,
        )
    else:
        if exception is not None:
            log_secure_operation(label, str(exception))
        detail = user_message or "An error occurred."

    raise HTTPException(status_code=status_code, detail=detail)
