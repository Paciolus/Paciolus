"""Sentry event scrubbing (Sprint 275; widened Sprint 840).

What Sentry may receive is part of what we tell customers, so it lives in one
importable place with tests against the real functions — the first version sat
inline in ``main.py`` and the test suite exercised a hand-copied mirror of it.

Sprint 840 (claims review S2): ``send_default_pii=False`` does not stop the SDK
attaching **stack-frame local variables** (on by default, strings up to 100,000
characters), **exception messages** or **breadcrumbs** built from log lines.
An unhandled exception in an upload route could therefore ship ``file_bytes``,
a DataFrame repr, or a parser error quoting cell values. All three are now
removed, both at SDK level (``SENTRY_INIT_OPTIONS``) and again per event here,
so a future SDK default cannot silently re-enable them.

Kept: exception *type*, module, function, file and line number — enough to
find the bug, nothing from the customer's file.
"""

from __future__ import annotations

from typing import Any

SAFE_EXTRA_KEYS = frozenset({"sentry_logger", "sys.argv", "celery-job"})
SAFE_CONTEXT_KEYS = frozenset({"runtime", "os", "device", "browser", "trace", "threadpool"})
SAFE_HEADER_KEYS = frozenset({"user-agent", "content-type", "content-length", "accept", "host"})

REDACTED = "[redacted]"

# Passed to sentry_sdk.init alongside dsn/environment/sample rate.
SENTRY_INIT_OPTIONS: dict[str, Any] = {
    "send_default_pii": False,
    "include_local_variables": False,
    "include_source_context": False,
    "max_value_length": 1024,
    "max_breadcrumbs": 0,
}


def _scrub_frames(container: dict[str, Any] | None) -> None:
    if not container:
        return
    stacktrace = container.get("stacktrace")
    if not stacktrace:
        return
    for frame in stacktrace.get("frames") or []:
        frame.pop("vars", None)
        frame.pop("pre_context", None)
        frame.pop("context_line", None)
        frame.pop("post_context", None)


def before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    """Strip everything that could carry customer data from an error event."""
    req = event.get("request")
    if req:
        req.pop("data", None)
        req.pop("query_string", None)
        req.pop("cookies", None)
        headers = req.get("headers")
        if isinstance(headers, dict):
            req["headers"] = {k: v for k, v in headers.items() if k.lower() in SAFE_HEADER_KEYS}

    extra = event.get("extra")
    if extra:
        event["extra"] = {k: v for k, v in extra.items() if k in SAFE_EXTRA_KEYS}

    contexts = event.get("contexts")
    if contexts:
        event["contexts"] = {k: v for k, v in contexts.items() if k in SAFE_CONTEXT_KEYS}

    # Exception messages routinely quote the input ("could not convert
    # 'Acme Holdings 4,210.55' to float"). Keep the type; drop the text.
    exception = event.get("exception")
    if exception:
        for value in exception.get("values") or []:
            if value.get("value"):
                value["value"] = REDACTED
            _scrub_frames(value)

    threads = event.get("threads")
    if threads:
        for thread in threads.get("values") or []:
            _scrub_frames(thread)

    # A logged error becomes an event whose message is the *formatted* log
    # line. Keep the template ("Upload failed for %s"), drop the arguments.
    logentry = event.get("logentry")
    if logentry:
        logentry.pop("params", None)
        if "message" in logentry:
            logentry.pop("formatted", None)
        elif logentry.get("formatted"):
            logentry["formatted"] = REDACTED
    if isinstance(event.get("message"), str) and event["message"]:
        template = logentry.get("message") if logentry else None
        event["message"] = template or REDACTED

    event.pop("breadcrumbs", None)
    return event


def before_send_transaction(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any]:
    """Strip query strings from transaction names."""
    if "transaction" in event:
        txn = event["transaction"]
        qidx = txn.find("?")
        if qidx != -1:
            event["transaction"] = txn[:qidx]
    req = event.get("request")
    if req:
        req.pop("data", None)
        req.pop("query_string", None)
        req.pop("cookies", None)
    event.pop("breadcrumbs", None)
    return event
