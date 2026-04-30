"""
Auth service layer (Sprint 746 onward).

Hosts business-logic services extracted from `routes/auth_routes.py` so
route handlers stay thin (validate → call service → return typed response).

Sub-modules:
  - `recovery` — password reset lifecycle (Sprint 746a).

Future sub-modules (Sprint 746b/c/d, scoped per workflow):
  - `identity` — login/logout/refresh/me + token issuance.
  - `registration` — registration + email verification lifecycle.
  - `sessions` — session inventory + revocation.

**Boundary discipline:** these services do not touch cookie/CSRF
primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) per the
deferred-items guidance — those are security-sensitive and stay owned
by the route layer.
"""
