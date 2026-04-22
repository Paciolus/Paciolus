"""
Create a pre-verified developer account for testing.

Usage (from backend/):
    # Interactive (will prompt; input is not echoed):
    python scripts/create_dev_user.py

    # Non-interactive (CI / scripted):
    DEV_USER_PASSWORD='MyStrongDevP@ss' python scripts/create_dev_user.py

    # Optional override of the email / name / tier:
    DEV_USER_EMAIL=me@example.com \\
    DEV_USER_NAME='Alice' \\
    DEV_USER_TIER=PROFESSIONAL \\
    DEV_USER_PASSWORD='MyStrongDevP@ss' \\
    python scripts/create_dev_user.py

Environment:
    Reads DATABASE_URL from .env (same as the app).
    Works with both SQLite (local) and PostgreSQL (production-style).

Security guards (2026-04-20):
    * No hardcoded password.  DEV_USER_PASSWORD must be provided via env
      var, or entered interactively (``getpass``, no echo).
    * Refuses to run unless ``ENV_MODE=development``.  Override with
      ``--i-know-this-is-dangerous`` to run against a non-development
      database; prints a loud banner when doing so.
    * Applies the same password-complexity policy as normal registration.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path so local imports work
_backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend_root))

from datetime import UTC, datetime

# Import all model modules so SQLAlchemy can resolve relationships
import engagement_model  # noqa: F401, E402
import follow_up_items_model  # noqa: F401, E402
import subscription_model  # noqa: F401, E402
import tool_session_model  # noqa: F401, E402
from auth import _check_password_complexity, hash_password  # noqa: E402
from config import ENV_MODE  # noqa: E402
from database import SessionLocal, engine  # noqa: E402
from models import Base, User, UserTier  # noqa: E402

# Defaults (safe — email and tier only, NO password) -----------------------
_DEFAULT_EMAIL = "dev@paciolus.com"
_DEFAULT_NAME = "Developer"
_DEFAULT_TIER = UserTier.ENTERPRISE
# --------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a pre-verified developer user.")
    parser.add_argument(
        "--i-know-this-is-dangerous",
        action="store_true",
        help=(
            "Allow the script to run against a non-development ENV_MODE. Intended only for disaster-recovery workflows."
        ),
    )
    return parser.parse_args(argv)


def _prompt_password() -> str:
    """Prompt for a password (no echo).  Enforces minimal UX sanity."""
    while True:
        pw = getpass.getpass("Dev user password: ")
        if not pw:
            print("Password cannot be empty.", file=sys.stderr)
            continue
        confirm = getpass.getpass("Confirm password: ")
        if pw != confirm:
            print("Passwords did not match; try again.", file=sys.stderr)
            continue
        return pw


def _resolve_password() -> str:
    """Return the password from env or interactive prompt."""
    env_pw = os.environ.get("DEV_USER_PASSWORD")
    if env_pw is not None:
        return env_pw
    if not sys.stdin.isatty():
        print(
            "ERROR: DEV_USER_PASSWORD env var is required in non-interactive mode.",
            file=sys.stderr,
        )
        sys.exit(2)
    return _prompt_password()


def _resolve_tier(raw: str | None) -> UserTier:
    if raw is None:
        return _DEFAULT_TIER
    try:
        return UserTier[raw.upper()]
    except KeyError:
        # Fallback to .value lookup (e.g. "professional")
        try:
            return UserTier(raw.lower())
        except ValueError as exc:
            raise SystemExit(f"Unknown DEV_USER_TIER '{raw}'.") from exc


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    # --- Safety gate ------------------------------------------------------
    if ENV_MODE != "development" and not args.i_know_this_is_dangerous:
        print(
            f"\nERROR: ENV_MODE is '{ENV_MODE}', not 'development'.\n"
            "Refusing to create a dev user against a non-development database.\n"
            "If you really mean to do this (disaster recovery only), re-run with:\n"
            "    python scripts/create_dev_user.py --i-know-this-is-dangerous\n",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.i_know_this_is_dangerous and ENV_MODE != "development":
        print(
            "\n" + "!" * 70 + "\n"
            f"DANGER: running create_dev_user against ENV_MODE={ENV_MODE}.\n"
            "This creates a privileged verified user in a non-development\n"
            "database.  You are responsible for whatever happens next.\n" + "!" * 70 + "\n"
        )

    email = os.environ.get("DEV_USER_EMAIL", _DEFAULT_EMAIL).strip().lower()
    name = os.environ.get("DEV_USER_NAME", _DEFAULT_NAME)
    tier = _resolve_tier(os.environ.get("DEV_USER_TIER"))
    password = _resolve_password()

    # Validate complexity using the same rules as registration.
    try:
        _check_password_complexity(password)
    except ValueError as exc:
        print(f"ERROR: password does not meet complexity policy: {exc}", file=sys.stderr)
        sys.exit(2)

    # Ensure tables exist (safe no-op if they already do)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            print(f"User '{email}' already exists (id={existing.id}).")
            changed = False

            if not existing.is_verified:
                existing.is_verified = True
                existing.email_verified_at = datetime.now(UTC)
                changed = True
                print("  -> Marked as verified.")

            if existing.tier != tier:
                existing.tier = tier
                changed = True
                print(f"  -> Tier upgraded to {tier.value}.")

            if not existing.is_active:
                existing.is_active = True
                changed = True
                print("  -> Re-activated.")

            # Reset password to the supplied value (never echoed).
            existing.hashed_password = hash_password(password)
            changed = True
            print("  -> Password reset to the supplied value.")

            if changed:
                db.commit()
                print("  [OK] User updated.")
            else:
                print("  [OK] No changes needed.")
        else:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                name=name,
                is_active=True,
                is_verified=True,
                tier=tier,
                email_verified_at=datetime.now(UTC),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[OK] Created dev user (id={user.id}):")

        print()
        print("  +----------------------------------------+")
        print(f"  |  Email:    {email:<26}|")
        print(f"  |  Password: (hidden — see env/prompt){'':<4}|")
        print(f"  |  Tier:     {tier.value:<26}|")
        print(f"  |  Verified: Yes{'':<22}|")
        print("  +----------------------------------------+")

    finally:
        db.close()


if __name__ == "__main__":
    main()
