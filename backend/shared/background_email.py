"""Background-task wrapper for SendGrid email dispatches.

Catches all exceptions so a failed background send is observable via
structured logs but never crashes the ASGI server.
"""

import logging
from collections.abc import Callable
from typing import Any

from security_utils import log_secure_operation

logger = logging.getLogger(__name__)


def safe_background_email(send_func: Callable[..., Any], *, label: str = "email", **kwargs: Any) -> None:
    """Dispatch a SendGrid call safely from a FastAPI BackgroundTasks queue."""
    try:
        result = send_func(**kwargs)
        if not result.success:
            logger.warning(
                "Background %s send failed: %s",
                label,
                getattr(result, "error", "unknown"),
            )
            log_secure_operation(
                f"background_{label}_failed",
                f"Background email send failed: {getattr(result, 'error', 'unknown')}",
            )
    except Exception as e:
        logger.exception("Background %s exception", label)
        log_secure_operation(
            f"background_{label}_error",
            f"Background email exception: {type(e).__name__}",
        )
