"""A small, stateful stand-in for the parts of the Stripe SDK billing uses (Sprint 881).

``MagicMock`` answers every call with success, so it cannot show that a second
checkout expired the first one, or that a completed session cannot be expired.
This fake keeps Customers, Checkout Sessions and Subscriptions in dicts and
behaves like Stripe for the calls billing makes: ``Session.expire`` on a
``complete`` session raises, ``Session.list`` filters by customer and status,
``Subscription.list`` returns the customer's subscriptions, and
``Session.create`` honours ``idempotency_key``.

It never talks to the network. ``complete_session`` plays the customer paying.
"""

from __future__ import annotations

import itertools
import threading
import time
from types import SimpleNamespace
from typing import Any


class FakeStripeError(Exception):
    """Raised where Stripe would answer with an error."""


class _Customers:
    def __init__(self, owner: FakeStripe) -> None:
        self._o = owner

    def create(self, email: str, metadata: dict | None = None, **_: Any) -> SimpleNamespace:
        if self._o.customer_create_delay:
            time.sleep(self._o.customer_create_delay)  # network latency, outside the lock
        with self._o.lock:
            cid = f"cus_fake{next(self._o.seq):06d}"
            self._o.customers[cid] = {"id": cid, "email": email, "metadata": metadata or {}}
            return SimpleNamespace(id=cid)

    def delete(self, customer_id: str) -> None:
        with self._o.lock:
            self._o.customers.pop(customer_id, None)


class _Sessions:
    def __init__(self, owner: FakeStripe) -> None:
        self._o = owner

    def create(self, idempotency_key: str | None = None, **params: Any) -> SimpleNamespace:
        if self._o.session_create_delay:
            time.sleep(self._o.session_create_delay)  # network latency, outside the lock
        with self._o.lock:
            if idempotency_key and idempotency_key in self._o.idempotent:
                sid = self._o.idempotent[idempotency_key]
            else:
                sid = f"cs_test_fake{next(self._o.seq):06d}"
                self._o.sessions[sid] = {
                    "id": sid,
                    "object": "checkout.session",
                    "status": "open",
                    "customer": params.get("customer"),
                    "client_reference_id": params.get("client_reference_id"),
                    "metadata": params.get("metadata", {}),
                    "subscription_data": params.get("subscription_data", {}),
                    "discounts": params.get("discounts", []),
                    "line_items": params.get("line_items", []),
                    "expires_at": params.get("expires_at"),
                    "subscription": None,
                    "url": f"https://checkout.stripe.com/c/pay/{sid}",
                }
                if idempotency_key:
                    self._o.idempotent[idempotency_key] = sid
            self._o.created_sessions.append(sid)
            return SimpleNamespace(id=sid, url=self._o.sessions[sid]["url"])

    def list(self, customer: str | None = None, status: str | None = None, **_: Any) -> dict:
        with self._o.lock:
            data = [
                dict(s)
                for s in self._o.sessions.values()
                if (customer is None or s["customer"] == customer) and (status is None or s["status"] == status)
            ]
        return {"object": "list", "data": data, "has_more": False}

    def retrieve(self, session_id: str, **_: Any) -> dict:
        with self._o.lock:
            if session_id not in self._o.sessions:
                raise FakeStripeError(f"No such checkout.session: {session_id}")
            return dict(self._o.sessions[session_id])

    def expire(self, session_id: str, **_: Any) -> dict:
        with self._o.lock:
            session = self._o.sessions.get(session_id)
            if session is None:
                raise FakeStripeError(f"No such checkout.session: {session_id}")
            if session["status"] != "open":
                raise FakeStripeError(
                    f"Only Checkout Sessions with a status of open can be expired ({session['status']})"
                )
            session["status"] = "expired"
            self._o.expired_sessions.append(session_id)
            return dict(session)


class _Subscriptions:
    def __init__(self, owner: FakeStripe) -> None:
        self._o = owner

    def list(self, customer: str | None = None, status: str | None = None, **_: Any) -> dict:
        with self._o.lock:
            data = [
                dict(s)
                for s in self._o.subscriptions.values()
                if (customer is None or s["customer"] == customer)
                and (status in (None, "all") or s["status"] == status)
            ]
        return {"object": "list", "data": data, "has_more": False}

    def retrieve(self, subscription_id: str, **_: Any) -> dict:
        with self._o.lock:
            return dict(self._o.subscriptions[subscription_id])

    def modify(self, subscription_id: str, idempotency_key: str | None = None, **params: Any) -> dict:
        with self._o.lock:
            sub = self._o.subscriptions[subscription_id]
            self._o.modifications.append((subscription_id, params))
            items = sub["items"]["data"]
            for change in params.get("items", []):
                existing = next((i for i in items if i["id"] == change.get("id")), None)
                if change.get("deleted"):
                    items.remove(existing)
                elif existing is not None:
                    if "price" in change:
                        existing["price"] = {"id": change["price"]}
                        existing["plan"] = {"interval": self._o.price_intervals.get(change["price"], "month")}
                    if "quantity" in change:
                        existing["quantity"] = change["quantity"]
                else:
                    items.append(
                        {
                            "id": f"si_fake{next(self._o.seq):06d}",
                            "price": {"id": change["price"]},
                            "plan": {"interval": self._o.price_intervals.get(change["price"], "month")},
                            "quantity": change.get("quantity", 1),
                        }
                    )
            for key in ("cancel_at_period_end", "metadata"):
                if key in params:
                    sub[key] = params[key]
            return dict(sub)


class FakeStripe:
    """Drop-in for ``billing.stripe_client.get_stripe()``'s return value in tests."""

    def __init__(self, price_intervals: dict[str, str] | None = None) -> None:
        self.lock = threading.RLock()
        self.seq = itertools.count(1)
        self.customers: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.subscriptions: dict[str, dict] = {}
        self.idempotent: dict[str, str] = {}
        self.created_sessions: list[str] = []
        self.expired_sessions: list[str] = []
        self.modifications: list[tuple[str, dict]] = []
        self.price_intervals = price_intervals or {}
        # Seconds Customer.create / Session.create wait before answering, so concurrent
        # checkouts overlap the way real Stripe latency makes them.
        self.customer_create_delay = 0.0
        self.session_create_delay = 0.0
        self.Customer = _Customers(self)
        self.Subscription = _Subscriptions(self)
        self.checkout = SimpleNamespace(Session=_Sessions(self))

    def add_subscription(self, customer: str, price_id: str, status: str = "active", interval: str = "month") -> dict:
        with self.lock:
            sub_id = f"sub_fake{next(self.seq):06d}"
            now = int(time.time())
            self.subscriptions[sub_id] = {
                "id": sub_id,
                "object": "subscription",
                "customer": customer,
                "status": status,
                "cancel_at_period_end": False,
                "metadata": {},
                "items": {
                    "object": "list",
                    "data": [
                        {
                            "id": f"si_fake{next(self.seq):06d}",
                            "object": "subscription_item",
                            "price": {"id": price_id},
                            "plan": {"interval": interval},
                            "quantity": 1,
                            "current_period_start": now,
                            "current_period_end": now + 30 * 86400,
                        }
                    ],
                },
            }
            return dict(self.subscriptions[sub_id])

    def complete_session(self, session_id: str, price_id: str) -> dict:
        """The customer pays: the session completes and its subscription is created."""
        with self.lock:
            session = self.sessions[session_id]
            if session["status"] != "open":
                raise FakeStripeError(f"Session {session_id} is {session['status']}; it cannot be paid")
            trial_days = int(session["subscription_data"].get("trial_period_days") or 0)
            sub = self.add_subscription(session["customer"], price_id, status="trialing" if trial_days else "active")
            stored = self.subscriptions[sub["id"]]
            stored["metadata"] = dict(session["subscription_data"].get("metadata", {}))
            # Stripe carries the checkout's discount and trial onto the subscription.
            stored["discounts"] = [f"di_fake_{d['coupon']}" for d in session["discounts"]]
            if trial_days:
                now = int(time.time())
                stored["trial_start"] = now
                stored["trial_end"] = now + trial_days * 86400
            session["status"] = "complete"
            session["subscription"] = sub["id"]
            return dict(session)
