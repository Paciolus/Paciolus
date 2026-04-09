"""
Grant or revoke superadmin status for a user.

Sprint 590: Platform-level superadmin designation — CLI only, no UI.

Usage (from backend/):
    python scripts/set_superadmin.py --email user@example.com
    python scripts/set_superadmin.py --email user@example.com --revoke

Environment:
    Reads DATABASE_URL from .env (same as the app).
"""

import argparse
import sys
from pathlib import Path

# Ensure backend root is on sys.path so local imports work
_backend_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend_root))

# Import all model modules so SQLAlchemy can resolve relationships
import engagement_model  # noqa: F401
import follow_up_items_model  # noqa: F401
import subscription_model  # noqa: F401
import tool_session_model  # noqa: F401
from auth import get_user_by_email
from database import SessionLocal
from models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant or revoke superadmin status")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--revoke", action="store_true", help="Revoke superadmin (default: grant)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # Sprint 594: `get_user_by_email` normalizes email case so a
        # mixed-case registration can still be located from the CLI.
        user = get_user_by_email(db, args.email)
        if not user:
            total_users = db.query(User).count()
            print(f"ERROR: No user found with email '{args.email}'")
            print(f"       Total user rows in DB: {total_users}")
            sys.exit(1)

        if args.revoke:
            user.is_superadmin = False
            db.commit()
            print(f"Superadmin REVOKED for {args.email} (user_id={user.id})")
        else:
            user.is_superadmin = True
            db.commit()
            print(f"Superadmin GRANTED to {args.email} (user_id={user.id})")

    finally:
        db.close()


if __name__ == "__main__":
    main()
