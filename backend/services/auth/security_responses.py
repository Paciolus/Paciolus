"""
Auth security response helpers (Sprint 747).

Normalizes the duplicated security-response patterns scattered across
`routes/auth_routes.py`:

- **Enumeration-safe credential rejection** (HTTPException 401 with the
  same body whether the email exists or not, plus WWW-Authenticate header).
  AUDIT-07 F4 contract: existing-wrong-password, locked account, and
  non-existent email all return identical responses to defeat enumeration.
- (Future) **Pre-auth gate** combining IP block + lockout into one check
  (Sprint 747b — not in this commit; the routes still call the primitives
  directly so the security-middleware contract is preserved verbatim).

The helpers do NOT touch cookies or CSRF state — that's the route layer's
job per the boundary established in ADR-015.
"""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException

# Stable detail payload — AUDIT-07 F4: same body for existing-wrong-password,
# locked account, IP-blocked, and non-existent email.
_INVALID_CREDENTIALS_DETAIL: dict[str, str] = {"message": "Invalid email or password"}


def raise_invalid_credentials() -> NoReturn:
    """
    Raise the enumeration-safe 401 used for any login failure.

    Returns the same body / headers regardless of why the credential check
    failed (wrong password, unknown email, locked account, IP blocked).
    Defeats account enumeration attacks per AUDIT-07 F4.

    Raises:
        HTTPException(401): always.
    """
    raise HTTPException(
        status_code=401,
        detail=_INVALID_CREDENTIALS_DETAIL,
        headers={"WWW-Authenticate": "Bearer"},
    )
