"""
Migration: Add email verification fields to users table and create verification tokens table
Sprint 57: Verified-Account-Only Model

Run this script to add email verification support to existing databases.
Safe to run multiple times (checks if columns/tables exist first).

Also grandfathers existing users as verified (no disruption).
"""

import sqlite3
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL


def run_migration():
    """Add email verification fields and grandfather existing users."""
    db_path = DATABASE_URL.replace("sqlite:///", "")

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Migration not needed (will be created with new schema).")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check existing columns in users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    changes_made = False

    # Add tier column if missing
    if 'tier' not in columns:
        print("Adding 'tier' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN tier VARCHAR(20) DEFAULT 'free'")
        changes_made = True

    # Add email_verification_token column if missing
    if 'email_verification_token' not in columns:
        print("Adding 'email_verification_token' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN email_verification_token VARCHAR(64)")
        changes_made = True

    # Add email_verification_sent_at column if missing
    if 'email_verification_sent_at' not in columns:
        print("Adding 'email_verification_sent_at' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN email_verification_sent_at DATETIME")
        changes_made = True

    # Add email_verified_at column if missing
    if 'email_verified_at' not in columns:
        print("Adding 'email_verified_at' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN email_verified_at DATETIME")
        changes_made = True

    # Check if email_verification_tokens table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_verification_tokens'")
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        print("Creating 'email_verification_tokens' table...")
        cursor.execute("""
            CREATE TABLE email_verification_tokens (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token VARCHAR(64) NOT NULL UNIQUE,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                used_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX ix_email_verification_tokens_token ON email_verification_tokens(token)")
        cursor.execute("CREATE INDEX ix_email_verification_tokens_user_id ON email_verification_tokens(user_id)")
        changes_made = True

    # Grandfather existing users as verified
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        UPDATE users
        SET is_verified = 1, email_verified_at = ?
        WHERE is_verified = 0 OR is_verified IS NULL
    """, (now,))
    grandfathered_count = cursor.rowcount

    if grandfathered_count > 0:
        print(f"Grandfathered {grandfathered_count} existing user(s) as verified.")
        changes_made = True

    conn.commit()

    if changes_made:
        print("Migration complete: Email verification fields added successfully.")
    else:
        print("All email verification fields already exist. Migration not needed.")

    conn.close()


if __name__ == "__main__":
    run_migration()
