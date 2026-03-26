"""Sprint 590: Add is_superadmin to users, create admin_audit_logs table.

Revision ID: 590a_superadmin
Revises: 418d00cd85ae
Create Date: 2026-03-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "590a_superadmin"
down_revision: str | None = "418d00cd85ae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add is_superadmin column to users table
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default=sa.text("0")))

    # Create admin_audit_logs table
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "action_type",
            sa.Enum(
                "plan_override",
                "trial_extension",
                "credit_issued",
                "refund_issued",
                "force_cancel",
                "impersonation_start",
                "impersonation_end",
                "session_revoke",
                name="adminactiontype",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column("target_org_id", sa.Integer(), nullable=True, index=True),
        sa.Column("target_user_id", sa.Integer(), nullable=True, index=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("admin_audit_logs")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_superadmin")
