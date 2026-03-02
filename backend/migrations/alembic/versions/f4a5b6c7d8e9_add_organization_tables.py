"""Add organization tables and upload tracking.

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-03-02

Phase LXIX: Pricing Restructure v3.
- organizations table
- organization_members table
- organization_invites table
- organization_id FK on users
- uploads_used_current_period on subscriptions
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4a5b6c7d8e9"
down_revision: str = "e3f4a5b6c7d8"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Create OrgRole enum for PostgreSQL
    if is_pg:
        op.execute("CREATE TYPE orgrole AS ENUM ('owner', 'admin', 'member')")
        op.execute("CREATE TYPE invitestatus AS ENUM ('pending', 'accepted', 'expired', 'revoked')")

    # Organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("owner_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id"), unique=True, nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Organization members table
    org_role_type = sa.Enum("owner", "admin", "member", name="orgrole", create_type=False) if is_pg else sa.String(20)
    op.create_table(
        "organization_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True, nullable=False, index=True),
        sa.Column("role", org_role_type, nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("invited_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )

    # Organization invites table
    invite_status_type = (
        sa.Enum("pending", "accepted", "expired", "revoked", name="invitestatus", create_type=False)
        if is_pg
        else sa.String(20)
    )
    op.create_table(
        "organization_invites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("invite_token_hash", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("invitee_email", sa.String(255), nullable=False, index=True),
        sa.Column("role", org_role_type, nullable=False, server_default="member"),
        sa.Column("status", invite_status_type, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("invited_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )

    # Add organization_id FK to users table
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_users_organization_id", ["organization_id"])
        batch_op.create_foreign_key("fk_users_organization_id", "organizations", ["organization_id"], ["id"])

    # Add uploads_used_current_period to subscriptions
    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.add_column(sa.Column("uploads_used_current_period", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Remove uploads_used_current_period from subscriptions
    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_column("uploads_used_current_period")

    # Remove organization_id from users
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_organization_id", type_="foreignkey")
        batch_op.drop_index("ix_users_organization_id")
        batch_op.drop_column("organization_id")

    # Drop tables in reverse order
    op.drop_table("organization_invites")
    op.drop_table("organization_members")
    op.drop_table("organizations")

    if is_pg:
        op.execute("DROP TYPE IF EXISTS invitestatus")
        op.execute("DROP TYPE IF EXISTS orgrole")
