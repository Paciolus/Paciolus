"""Reporting framework of a memo export — Sprint 886 (review OUT-18).

A memo request may name the engagement (or client) its run belongs to. The
framework is resolved from that client with ``resolve_reporting_framework`` —
after checking the user may see it — and passed to the generator. Every memo
prints which framework it used and why (``build_scope_statement``), via the
disclosure set here for the duration of the export, the same pattern as the
Sprint 679 branding context.

Nothing linked: FASB, labelled as the default (CEO decision, 2026-11-19).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from shared.framework_resolution import ResolutionReason, ResolvedFramework, resolve_reporting_framework

FRAMEWORK_LABELS = {
    ResolvedFramework.FASB: "FASB (US GAAP)",
    ResolvedFramework.GASB: "GASB",
}

_REASONS = {
    ResolutionReason.EXPLICIT_FASB: "set on the client",
    ResolutionReason.EXPLICIT_GASB: "set on the client",
    ResolutionReason.ENTITY_TYPE_GOVERNMENTAL: "the client is a governmental entity",
    ResolutionReason.ENTITY_TYPE_FOR_PROFIT: "the client is a for-profit entity",
    ResolutionReason.ENTITY_TYPE_NONPROFIT_US: "the client is a US nonprofit (FASB ASC 958)",
    ResolutionReason.JURISDICTION_US_DEFAULT: "US client; entity type not set",
    ResolutionReason.FALLBACK_FASB: "no rule matched the client's jurisdiction; FASB used by default",
}

UNLINKED = "default; no client or engagement was linked to this run"


@dataclass(frozen=True)
class ExportFramework:
    framework: ResolvedFramework
    disclosure: str  # e.g. "GASB — the client is a governmental entity"


def _enum_value(value: Any, default: str) -> str:
    return str(getattr(value, "value", value) or default)


def resolve_export_framework(
    user: Any,
    db: Session,
    engagement_id: Optional[int] = None,
    client_id: Optional[int] = None,
) -> ExportFramework:
    """The framework for a memo export, from the authorized engagement or client.

    An engagement or client the user may not see is a 404 (as on every other
    engagement and client route), never a silent fall-back to FASB.
    """
    client = None
    if engagement_id is not None:
        from engagement_manager import EngagementManager

        engagement = EngagementManager(db).get_engagement(user.id, engagement_id)
        if engagement is None:
            raise HTTPException(status_code=404, detail="Engagement not found")
        if client_id is not None and client_id != engagement.client_id:
            raise HTTPException(status_code=422, detail="client_id does not match the engagement's client")
        client = engagement.client
    elif client_id is not None:
        from shared.client_access import get_accessible_client

        client = get_accessible_client(user, client_id, db)
        if client is None:
            raise HTTPException(status_code=404, detail="Client not found")

    if client is None:
        return ExportFramework(ResolvedFramework.FASB, f"{FRAMEWORK_LABELS[ResolvedFramework.FASB]} — {UNLINKED}")

    resolved = resolve_reporting_framework(
        _enum_value(client.reporting_framework, "auto"),
        _enum_value(client.entity_type, "other"),
        client.jurisdiction_country or "US",
        client.jurisdiction_state,
    )
    reason = _REASONS.get(resolved.resolution_reason, "resolved from the client")
    return ExportFramework(resolved.framework, f"{FRAMEWORK_LABELS[resolved.framework]} — {reason}")


_disclosure: ContextVar[Optional[str]] = ContextVar("export_framework_disclosure", default=None)


@contextmanager
def apply_framework_disclosure(disclosure: Optional[str]) -> Iterator[None]:
    """Make ``disclosure`` the Reporting Framework line of memos built inside the block."""
    token = _disclosure.set(disclosure)
    try:
        yield
    finally:
        _disclosure.reset(token)


def framework_disclosure(framework: ResolvedFramework) -> str:
    """The Reporting Framework line: the export's disclosure, else the framework's name."""
    return _disclosure.get() or FRAMEWORK_LABELS.get(framework, str(framework.value).upper())
