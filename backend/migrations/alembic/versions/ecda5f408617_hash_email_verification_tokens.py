"""Hash email verification tokens at rest

Revision ID: ecda5f408617
Revises: b590bb0555c3
Create Date: 2026-02-27 00:00:00.000000

Security hardening: store SHA-256 hash of email verification tokens instead
of plaintext. Mirrors the refresh token hashing pattern (Sprint 197).

All existing tokens are deleted on upgrade — any in-flight verifications
will require a new resend. Users are not affected beyond needing to click
"Resend verification email" once after this migration runs.

Also removes the denormalized `users.email_verification_token` plaintext
column (sprint 57 artifact, never used for lookup).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ecda5f408617"
down_revision: str | None = "b590bb0555c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Delete all existing plaintext tokens — cannot be migrated (raw value unknown).
    # Any in-flight verifications are invalidated; users re-request via resend.
    op.execute("DELETE FROM email_verification_tokens")

    with op.batch_alter_table("email_verification_tokens", schema=None) as batch_op:
        batch_op.add_column(sa.Column("token_hash", sa.String(length=64), nullable=False, server_default=""))
        batch_op.drop_index(batch_op.f("ix_email_verification_tokens_token"))
        batch_op.drop_column("token")
        batch_op.create_index(
            batch_op.f("ix_email_verification_tokens_token_hash"),
            ["token_hash"],
            unique=True,
        )
        # Remove server_default after column is created (not needed at runtime)
        batch_op.alter_column("token_hash", server_default=None)

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_email_verification_token"))
        batch_op.drop_column("email_verification_token")


def downgrade() -> None:
    # Plaintext columns restored empty — hashes cannot be reversed.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email_verification_token", sa.String(length=64), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_users_email_verification_token"),
            ["email_verification_token"],
            unique=False,
        )

    with op.batch_alter_table("email_verification_tokens", schema=None) as batch_op:
        batch_op.add_column(sa.Column("token", sa.String(length=64), nullable=False, server_default=""))
        batch_op.drop_index(batch_op.f("ix_email_verification_tokens_token_hash"))
        batch_op.drop_column("token_hash")
        batch_op.create_index(
            batch_op.f("ix_email_verification_tokens_token"),
            ["token"],
            unique=True,
        )
        batch_op.alter_column("token", server_default=None)
