"""Account erasure and data export (Sprint 844 — claims review Part 5).

The Privacy Policy promised self-service account deletion and the Terms
promised deletion on termination; neither existed. Every "delete" in the app
was a soft delete (``archived_at``). This module is the one place that
physically removes a user's data, and the one place that exports it.

WHY THIS MAY HARD-DELETE PROTECTED TABLES
----------------------------------------
``activity_logs``, ``diagnostic_summaries``, ``tool_runs``,
``follow_up_items`` and ``follow_up_item_comments`` are under the Phase XLVI
audit-immutability invariant: ordinary code paths must soft-delete them. An
erasure request is the exception the law makes — the user's own records, on
the user's own request (GDPR Art. 17, CCPA §1798.105) — and the CEO approved
it on 2026-10-24. The exemption is narrow: this file is listed in
``guards/accounting_policy.toml`` ``no_hard_delete.exclude_patterns`` with this
justification, and nothing else is.

WHAT IS KEPT
------------
* ``billing_events`` rows are kept with ``user_id`` set to NULL — they are
  revenue history with no personal data once unlinked. Stripe keeps the
  invoices and payment records the law requires; we cannot delete those.
* ``security_events`` rows are kept (``user_id`` becomes NULL by FK rule).
* A ``security_events`` row records that an erasure happened.

WHAT IS REFUSED (``ErasureBlocked``)
-----------------------------------
* A superadmin: the admin audit log references them and must survive.
* An organization owner while other members remain: ownership has to move or
  the members leave first, or the firm's shared data would be orphaned.
* A user who authored workpaper entries inside an engagement someone else
  owns (expectations, misstatements, engagements under another user's
  client): deleting them would delete a colleague's records, and the columns
  are NOT NULL so they cannot be anonymised. Handled by privacy@ by hand.

Order matters: R2 share objects are removed (each share row with it, durably)
and then Stripe is cancelled, **before** any other row is deleted. A provider
failure therefore leaves the account in place, and the error says exactly what
was already removed. A late Stripe webhook for the erased account is ignored by
``billing.webhook_handler._resolve_user_id``.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import Table, delete, select, update
from sqlalchemy.orm import Session

from database import Base
from model_registry import import_all_models

logger = logging.getLogger(__name__)


class _CodedErasureError(Exception):
    """An erasure failure with a stable ``code`` the frontend maps to safe text.

    PR #254 review: the transport never shows raw backend strings (its
    allowlist cannot match messages carrying counts), so the route sends
    ``{"code", "message"}`` and the UI explains the case from the code.
    """

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


class ErasureBlocked(_CodedErasureError):
    """The account cannot be erased self-service; the message says why."""


class ErasureProviderError(_CodedErasureError):
    """Stripe or R2 refused. ``ERASURE_PARTIAL_CLEANUP`` when shared links were
    already removed (R2 deletes cannot be rolled back); otherwise nothing was
    deleted (``ERASURE_PROVIDER_FAILED``)."""

    def __init__(self, message: str, code: str = "ERASURE_PROVIDER_FAILED") -> None:
        super().__init__(message, code)


def _t(name: str) -> Table:
    return Base.metadata.tables[name]


def _ids(db: Session, table: str, column: str, values: list[int]) -> list[int]:
    if not values:
        return []
    t = _t(table)
    return [row[0] for row in db.execute(select(t.c.id).where(t.c[column].in_(values)))]


# Columns that point at users.id and may simply be cleared when the row belongs
# to someone else (e.g. "archived_by" on a colleague's engagement record).
_NULLABLE_USER_REFS: tuple[tuple[str, str], ...] = (
    ("activity_logs", "archived_by"),
    ("diagnostic_summaries", "archived_by"),
    ("engagements", "completed_by"),
    ("organization_invites", "accepted_by_user_id"),
    ("organization_invites", "invited_by_user_id"),
    ("organization_members", "invited_by_user_id"),
    ("analytical_expectations", "archived_by"),
    ("analytical_expectations", "updated_by"),
    ("tool_runs", "archived_by"),
    ("uncorrected_misstatements", "updated_by"),
    ("uncorrected_misstatements", "archived_by"),
    ("follow_up_items", "assigned_to"),
    ("follow_up_items", "archived_by"),
    ("follow_up_item_comments", "archived_by"),
    ("billing_events", "user_id"),
)


def _owned_scope(db: Session, user_id: int) -> dict[str, list[int]]:
    import_all_models()
    client_ids = _ids(db, "clients", "user_id", [user_id])
    engagement_ids = _ids(db, "engagements", "client_id", client_ids)
    item_ids = _ids(db, "follow_up_items", "engagement_id", engagement_ids)
    sub_ids = _ids(db, "subscriptions", "user_id", [user_id])
    return {"clients": client_ids, "engagements": engagement_ids, "items": item_ids, "subscriptions": sub_ids}


def check_erasable(db: Session, user: Any) -> None:
    """Raise ``ErasureBlocked`` if this account cannot be erased self-service."""
    import_all_models()
    if getattr(user, "is_superadmin", False):
        raise ErasureBlocked("Superadmin accounts cannot be deleted from the app.", "ERASURE_SUPERADMIN")

    orgs = _t("organizations")
    members = _t("organization_members")
    owned_orgs = [r[0] for r in db.execute(select(orgs.c.id).where(orgs.c.owner_user_id == user.id))]
    for org_id in owned_orgs:
        others = db.execute(
            select(members.c.id).where(members.c.organization_id == org_id, members.c.user_id != user.id)
        ).first()
        if others is not None:
            raise ErasureBlocked(
                "You own an organization that still has other members. Transfer ownership or remove "
                "the members first, then delete your account.",
                "ERASURE_ORG_HAS_MEMBERS",
            )

    scope = _owned_scope(db, user.id)
    owned = set(scope["engagements"])
    for table in ("analytical_expectations", "uncorrected_misstatements"):
        t = _t(table)
        foreign = db.execute(
            select(t.c.id).where(t.c.created_by == user.id, t.c.engagement_id.notin_(owned or [-1]))
        ).first()
        if foreign is not None:
            raise ErasureBlocked(
                "You have entries in engagements owned by someone else. Email privacy@paciolus.com and "
                "we will handle the deletion with the engagement owner.",
                "ERASURE_FOREIGN_ENTRIES",
            )
    eng = _t("engagements")
    foreign_eng = db.execute(
        select(eng.c.id).where(eng.c.created_by == user.id, eng.c.client_id.notin_(scope["clients"] or [-1]))
    ).first()
    if foreign_eng is not None:
        raise ErasureBlocked(
            "You created engagements for clients owned by someone else. Email privacy@paciolus.com and "
            "we will handle the deletion with the client owner.",
            "ERASURE_FOREIGN_ENGAGEMENTS",
        )


def _cancel_stripe(db: Session, user_id: int) -> None:
    subs = _t("subscriptions")
    row = db.execute(select(subs.c.stripe_subscription_id, subs.c.status).where(subs.c.user_id == user_id)).first()
    if row is None or not row[0]:
        return
    status = getattr(row[1], "value", row[1])
    if status == "canceled":
        return
    from billing.stripe_client import get_stripe, is_stripe_enabled

    if not is_stripe_enabled():
        # PR #236 review: a live subscription with Stripe unconfigured is not a
        # cancellation. Deleting the local rows here would leave Stripe billing
        # a customer who can no longer reach their billing settings.
        logger.error("Account erasure: live Stripe subscription but Stripe is not configured")
        raise ErasureProviderError("We could not reach our payment provider to cancel your subscription.")
    try:
        get_stripe().Subscription.cancel(row[0])
    except Exception as exc:  # noqa: BLE001 — any provider failure aborts the erasure
        logger.error("Account erasure: Stripe cancel failed [%s]", type(exc).__name__)
        raise ErasureProviderError("We could not cancel your subscription with our payment provider.") from exc


def _delete_share_objects(db: Session, user_id: int, org_ids: list[int]) -> int:
    """Remove shared-report objects from R2, one share at a time. Returns the count.

    PR #237 review: R2 deletions cannot be rolled back, so the provider phase is
    not all-or-nothing. Each share's row is deleted (and committed) as soon as
    its object is gone, so a failure part-way leaves no rows pointing at missing
    reports, and a retry resumes where it stopped.
    """
    from shared import export_share_storage

    shares = _t("export_shares")
    cond = shares.c.user_id == user_id
    if org_ids:
        cond = cond | shares.c.organization_id.in_(org_ids)
    removed = 0
    for share_id, key in list(db.execute(select(shares.c.id, shares.c.object_key).where(cond))):
        if key and not export_share_storage.delete(key):
            done = f" {removed} shared link(s) were removed first." if removed else ""
            raise ErasureProviderError(
                f"We could not remove a shared report from storage.{done} Your account and other data were "
                "not deleted; please try again.",
                "ERASURE_PARTIAL_CLEANUP" if removed else "ERASURE_PROVIDER_FAILED",
            )
        db.execute(delete(shares).where(shares.c.id == share_id))
        db.commit()
        removed += 1
    return removed


def erase_account(db: Session, user: Any) -> dict[str, int]:
    """Physically delete ``user`` and everything they own. Returns row counts.

    Call ``check_erasable`` first. Commits on success; on any failure nothing is
    committed.
    """
    import_all_models()
    check_erasable(db, user)
    user_id = int(user.id)
    scope = _owned_scope(db, user_id)
    orgs = _t("organizations")
    owned_orgs = [r[0] for r in db.execute(select(orgs.c.id).where(orgs.c.owner_user_id == user_id))]

    # Providers first, so a provider failure leaves the account in place.
    # Shared links go first (each removed durably, see _delete_share_objects);
    # Stripe last, so a storage failure never leaves a cancelled subscription
    # on an account that still exists.
    shares_removed = _delete_share_objects(db, user_id, owned_orgs)
    try:
        _cancel_stripe(db, user_id)
    except ErasureProviderError as exc:
        if shares_removed:
            raise ErasureProviderError(
                f"{exc} Your {shares_removed} shared link(s) were removed; your subscription and account were "
                "not changed. Please try again.",
                "ERASURE_PARTIAL_CLEANUP",
            ) from exc
        raise ErasureProviderError(f"{exc} Nothing was deleted; please try again.") from exc

    counts: dict[str, int] = {}

    def _del(table: str, where: Any) -> None:
        result = db.execute(delete(_t(table)).where(where))
        counts[table] = counts.get(table, 0) + int(result.rowcount or 0)

    e_ids, item_ids, c_ids = scope["engagements"], scope["items"], scope["clients"]
    try:
        for table, column in _NULLABLE_USER_REFS:
            t = _t(table)
            db.execute(update(t).where(t.c[column] == user_id).values({column: None}))

        comments = _t("follow_up_item_comments")
        _del("follow_up_item_comments", comments.c.user_id == user_id)
        if item_ids:
            _del("follow_up_item_comments", comments.c.follow_up_item_id.in_(item_ids))
        if e_ids:
            for table in ("follow_up_items", "tool_runs", "analytical_expectations", "uncorrected_misstatements"):
                _del(table, _t(table).c.engagement_id.in_(e_ids))
            _del("tool_activities", _t("tool_activities").c.engagement_id.in_(e_ids))
            _del("engagements", _t("engagements").c.id.in_(e_ids))
        for table in (
            "tool_activities",
            "activity_logs",
            "diagnostic_summaries",
            "tool_sessions",
            "refresh_tokens",
            "email_verification_tokens",
            "password_reset_tokens",
            "export_shares",
            "team_activity_logs",
            "organization_members",
        ):
            _del(table, _t(table).c.user_id == user_id)
        if c_ids:
            _del("clients", _t("clients").c.id.in_(c_ids))

        users = _t("users")
        db.execute(update(users).where(users.c.id == user_id).values(organization_id=None))
        if owned_orgs:
            db.execute(update(users).where(users.c.organization_id.in_(owned_orgs)).values(organization_id=None))
            for table in ("organization_invites", "organization_members", "firm_branding", "team_activity_logs"):
                _del(table, _t(table).c.organization_id.in_(owned_orgs))
            _del("export_shares", _t("export_shares").c.organization_id.in_(owned_orgs))
            _del("organizations", orgs.c.id.in_(owned_orgs))

        if scope["subscriptions"]:
            _del("dunning_episodes", _t("dunning_episodes").c.subscription_id.in_(scope["subscriptions"]))
            _del("subscriptions", _t("subscriptions").c.id.in_(scope["subscriptions"]))
        _del("users", users.c.id == user_id)

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.expunge_all()
    from security_utils import log_secure_operation

    log_secure_operation("account_erased", f"Account erased; {sum(counts.values())} rows removed", db=db, user_id=None)
    return counts


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

# Never exported: credentials and token material.
_SECRET_COLUMNS = frozenset(
    {"hashed_password", "token_hash", "passcode_hash", "export_data", "object_key", "share_token_hash"}
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bytes):
        return None
    return value


def _rows(db: Session, table: str, where: Any) -> list[dict[str, Any]]:
    t = _t(table)
    out = []
    for row in db.execute(select(t).where(where)).mappings():
        out.append({k: _jsonable(v) for k, v in row.items() if k not in _SECRET_COLUMNS})
    return out


def export_account(db: Session, user: Any) -> dict[str, Any]:
    """Everything Paciolus stores about ``user``, as JSON-safe dicts (GDPR Art. 15/20)."""
    import_all_models()
    user_id = int(user.id)
    scope = _owned_scope(db, user_id)
    e_ids = scope["engagements"] or [-1]
    data: dict[str, Any] = {
        "exported_at": datetime.now(UTC).isoformat(),
        "note": (
            "Everything Paciolus stores about your account. Uploaded files are not kept, so none are included. "
            "Card and invoice records are held by Stripe."
        ),
        "account": _rows(db, "users", _t("users").c.id == user_id),
        "subscription": _rows(db, "subscriptions", _t("subscriptions").c.user_id == user_id),
        "clients": _rows(db, "clients", _t("clients").c.user_id == user_id),
        "engagements": _rows(db, "engagements", _t("engagements").c.id.in_(e_ids)),
        "analytical_expectations": _rows(
            db, "analytical_expectations", _t("analytical_expectations").c.engagement_id.in_(e_ids)
        ),
        "uncorrected_misstatements": _rows(
            db, "uncorrected_misstatements", _t("uncorrected_misstatements").c.engagement_id.in_(e_ids)
        ),
        "follow_up_items": _rows(db, "follow_up_items", _t("follow_up_items").c.engagement_id.in_(e_ids)),
        "follow_up_item_comments": _rows(
            db, "follow_up_item_comments", _t("follow_up_item_comments").c.user_id == user_id
        ),
        "tool_runs": _rows(db, "tool_runs", _t("tool_runs").c.engagement_id.in_(e_ids)),
        "diagnostic_summaries": _rows(db, "diagnostic_summaries", _t("diagnostic_summaries").c.user_id == user_id),
        "activity_logs": _rows(db, "activity_logs", _t("activity_logs").c.user_id == user_id),
        "tool_activities": _rows(db, "tool_activities", _t("tool_activities").c.user_id == user_id),
        "export_shares": _rows(db, "export_shares", _t("export_shares").c.user_id == user_id),
        "sessions": _rows(db, "refresh_tokens", _t("refresh_tokens").c.user_id == user_id),
        # PR #236 review: saved adjusting-entry and currency-rate sessions are
        # stored data too, and erasure deletes them.
        "tool_sessions": _rows(db, "tool_sessions", _t("tool_sessions").c.user_id == user_id),
    }
    return data
