"""
Create a pre-verified developer account for testing.

Usage (from backend/):
    python scripts/create_dev_user.py

Environment:
    Reads DATABASE_URL from .env (same as the app).
    Works with both SQLite (local) and PostgreSQL (production).

The script will:
    1. Create a user with the specified email/password
    2. Mark the account as verified (skips email verification)
    3. Set the tier to ORGANIZATION (full tool access)
    4. If the user already exists, update verification + tier instead
"""

import sys
from pathlib import Path

# Ensure backend root is on sys.path so local imports work
_backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend_root))

from datetime import UTC, datetime

# Import all model modules so SQLAlchemy can resolve relationships
import engagement_model  # noqa: F401
import follow_up_items_model  # noqa: F401
import subscription_model  # noqa: F401
import tool_session_model  # noqa: F401
from auth import hash_password
from database import SessionLocal, engine
from models import Base, User, UserTier

# -- Configuration --------------------------------------------------------
DEV_EMAIL = "dev@paciolus.com"
DEV_PASSWORD = "DevPass1!"
DEV_NAME = "Developer"
DEV_TIER = UserTier.ORGANIZATION
# -------------------------------------------------------------------------


def main() -> None:
    # Ensure tables exist (safe no-op if they already do)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == DEV_EMAIL).first()

        if existing:
            print(f"User '{DEV_EMAIL}' already exists (id={existing.id}).")
            changed = False

            if not existing.is_verified:
                existing.is_verified = True
                existing.email_verified_at = datetime.now(UTC)
                changed = True
                print("  -> Marked as verified.")

            if existing.tier != DEV_TIER:
                existing.tier = DEV_TIER
                changed = True
                print(f"  -> Tier upgraded to {DEV_TIER.value}.")

            if not existing.is_active:
                existing.is_active = True
                changed = True
                print("  -> Re-activated.")

            # Reset password to known value
            existing.hashed_password = hash_password(DEV_PASSWORD)
            changed = True
            print("  -> Password reset to default.")

            if changed:
                db.commit()
                print("  [OK] User updated.")
            else:
                print("  [OK] No changes needed.")
        else:
            user = User(
                email=DEV_EMAIL,
                hashed_password=hash_password(DEV_PASSWORD),
                name=DEV_NAME,
                is_active=True,
                is_verified=True,
                tier=DEV_TIER,
                email_verified_at=datetime.now(UTC),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[OK] Created dev user (id={user.id}):")

        print()
        print("  +----------------------------------------+")
        print(f"  |  Email:    {DEV_EMAIL:<26}|")
        print(f"  |  Password: {DEV_PASSWORD:<26}|")
        print(f"  |  Tier:     {DEV_TIER.value:<26}|")
        print(f"  |  Verified: Yes{'':<22}|")
        print("  +----------------------------------------+")

    finally:
        db.close()


if __name__ == "__main__":
    main()
