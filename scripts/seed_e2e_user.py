#!/usr/bin/env python3
"""Seed the deterministic end-to-end test account into a local, throwaway database.

Sprint 889 (CEO brief 14H, review TQ-16): the Playwright job starts its own backend on a fresh
SQLite file, so an account kept in repository secrets never existed there and both specs skipped.
This creates one verified Solo user with fixed credentials. The credentials are not secrets: they
exist only in the CI runner's temporary database.

Run from ``backend/`` (it imports the app's modules):

    E2E_USER=... E2E_PASS=... python ../scripts/seed_e2e_user.py

Refuses to run against anything but a local SQLite database, or in production mode.
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("sqlite:///"):
        print(
            "seed_e2e_user: refusing — DATABASE_URL is not a local SQLite file",
            file=sys.stderr,
        )
        return 2
    if os.environ.get("ENV_MODE", "development") == "production":
        print("seed_e2e_user: refusing — ENV_MODE is production", file=sys.stderr)
        return 2
    email = os.environ["E2E_USER"]
    password = os.environ["E2E_PASS"]

    sys.path.insert(0, os.getcwd())
    from auth import hash_password
    from database import SessionLocal, init_db
    from models import User, UserTier

    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                name="E2E Test User",
                hashed_password=hash_password(password),
            )
            db.add(user)
        user.hashed_password = hash_password(password)
        user.is_active = True
        user.is_verified = True
        user.tier = UserTier.SOLO
        db.commit()
        print(f"seed_e2e_user: ready ({email})")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
