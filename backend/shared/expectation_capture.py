"""Explicit capture of a proposed actual into an expectation (Sprint 879b, DH-04).

An analysis run with an engagement used to write each matching account's
balance into ``AnalyticalExpectation.result_actual_value`` by itself. Now the
analysis only *proposes* actuals; the auditor saves one — or every proposal from
a run — with an explicit action.

The server keeps nothing between the run and the capture, so each proposal
carries a **capture token**: an HMAC-signed statement of (user, engagement,
expectation, actual, source tool, source run, expiry). The capture endpoint
verifies it, so the value saved is the value the run measured and the run it is
attributed to is the run that measured it — the browser cannot substitute
either. The token holds nothing the response does not already show the user.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from sqlalchemy.orm import Session

CAPTURE_TOKEN_TTL_SECONDS = 24 * 60 * 60
_CONTEXT = b"paciolus:expectation-actual-capture:v1"

# Where an actual came from (``AnalyticalExpectation.actual_source``).
SOURCE_MANUAL = "manual"
CAPTURE_SOURCES = frozenset({"flux_analysis", "multi_period", "industry_ratios"})


class CaptureTokenError(ValueError):
    """The token is malformed, forged, expired or not this caller's."""


@dataclass(frozen=True)
class CaptureClaim:
    user_id: int
    engagement_id: int
    expectation_id: int
    actual: Decimal
    source: str
    tool_run_id: Optional[int]
    expires_at: int


def _key() -> bytes:
    from config import JWT_SECRET_KEY

    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is required to sign capture tokens")
    return hmac.new(JWT_SECRET_KEY.encode("utf-8"), _CONTEXT, hashlib.sha256).digest()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign_capture(
    *,
    user_id: int,
    engagement_id: int,
    expectation_id: int,
    actual: float | Decimal,
    source: str,
    tool_run_id: Optional[int],
    now: Optional[float] = None,
) -> str:
    if source not in CAPTURE_SOURCES:
        raise ValueError("unknown capture source")
    payload = {
        "u": user_id,
        "g": engagement_id,
        "e": expectation_id,
        "a": str(Decimal(str(actual)).quantize(Decimal("0.01"))),
        "s": source,
        "r": tool_run_id,
        "x": int((now if now is not None else time.time()) + CAPTURE_TOKEN_TTL_SECONDS),
    }
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = _b64(hmac.new(_key(), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_capture(token: str, *, user_id: int, engagement_id: int, now: Optional[float] = None) -> CaptureClaim:
    try:
        body, sig = token.split(".")
        expected = _b64(hmac.new(_key(), body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise CaptureTokenError("invalid capture token")
        p = json.loads(_unb64(body))
        claim = CaptureClaim(
            user_id=int(p["u"]),
            engagement_id=int(p["g"]),
            expectation_id=int(p["e"]),
            actual=Decimal(p["a"]),
            source=str(p["s"]),
            tool_run_id=int(p["r"]) if p.get("r") is not None else None,
            expires_at=int(p["x"]),
        )
    except CaptureTokenError:
        raise
    except (ValueError, KeyError, TypeError, InvalidOperation, json.JSONDecodeError):
        raise CaptureTokenError("invalid capture token") from None
    if claim.expires_at < (now if now is not None else time.time()):
        raise CaptureTokenError("capture token expired — run the analysis again")
    if claim.user_id != user_id or claim.engagement_id != engagement_id:
        raise CaptureTokenError("capture token does not belong to this engagement or user")
    if claim.source not in CAPTURE_SOURCES:
        raise CaptureTokenError("invalid capture token")
    return claim


def capture_actuals(db: Session, *, user_id: int, engagement_id: int, tokens: list[str]) -> list[dict[str, Any]]:
    """Save each proposal; one result per token, in order.

    Verifies every token before saving any (one bad token → nothing saved).
    An expectation that already has an actual is skipped, not overwritten — the
    auditor clears it first ("Re-evaluate"), as for a manual capture.
    """
    from analytical_expectations_manager import AnalyticalExpectationsManager
    from analytical_expectations_model import ExpectationResultStatus

    claims = [verify_capture(t, user_id=user_id, engagement_id=engagement_id) for t in tokens]
    mgr = AnalyticalExpectationsManager(db)
    results: list[dict[str, Any]] = []
    seen: set[int] = set()
    for claim in claims:
        exp = mgr.get_expectation(user_id, claim.expectation_id)
        if exp is None or exp.engagement_id != engagement_id or exp.archived_at is not None:
            results.append({"expectation_id": claim.expectation_id, "status": "skipped", "reason": "not_found"})
            continue
        if claim.expectation_id in seen or exp.result_status != ExpectationResultStatus.NOT_EVALUATED:
            results.append({"expectation_id": claim.expectation_id, "status": "skipped", "reason": "already_captured"})
            continue
        mgr.update_expectation(
            user_id=user_id,
            expectation_id=claim.expectation_id,
            result_actual_value=claim.actual,
            actual_source=claim.source,
            actual_source_tool_run_id=claim.tool_run_id,
        )
        seen.add(claim.expectation_id)
        results.append({"expectation_id": claim.expectation_id, "status": "captured", "reason": None})
    return results
