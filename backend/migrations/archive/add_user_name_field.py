"""
Migration: Add name field to users table
Sprint 48: User Profile Settings

Run this script to add the 'name' column to existing databases.
Safe to run multiple times (checks if column exists first).
"""

import os
import sqlite3
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL


def run_migration():
    """Add name column to users table if it doesn't exist."""
    db_path = DATABASE_URL.replace("sqlite:///", "")

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Migration not needed (will be created with new schema).")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'name' in columns:
        print("Column 'name' already exists in users table. Migration not needed.")
        conn.close()
        return

    # Add the column
    print("Adding 'name' column to users table...")
    cursor.execute("ALTER TABLE users ADD COLUMN name VARCHAR(100)")
    conn.commit()

    print("Migration complete: 'name' column added successfully.")
    conn.close()


if __name__ == "__main__":
    run_migration()
