"""Add export_shares, team_activity_logs, and firm_branding tables.

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-03-02

Phase LXIX: Pricing Restructure v3 (Phases 6–8).
- export_shares: temporary shared export links with 48h TTL
- team_activity_logs: lightweight team activity audit trail (90-day purge)
- firm_branding: custom PDF branding for Enterprise tier
"""

import sqlalchemy as sa
from alembic import op

revision = "a5b6c7d8e9f0"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- export_shares ---
    op.create_table(
        "export_shares",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True, index=True),
        sa.Column("share_token_hash", sa.String(64), unique=True, index=True, nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("export_format", sa.String(20), nullable=False),
        sa.Column("export_data", sa.LargeBinary(), nullable=False),
        sa.Column("shared_by_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
    )

    # --- team_activity_logs ---
    # Enum for action_type
    team_action_type = sa.Enum("upload", "export", "share", "login", name="teamactiontype")
    op.create_table(
        "team_activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("action_type", team_action_type, nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=True),
        sa.Column("file_identifier_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- firm_branding ---
    op.create_table(
        "firm_branding",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), unique=True, nullable=False, index=True
        ),
        sa.Column("logo_s3_key", sa.String(500), nullable=True),
        sa.Column("logo_content_type", sa.String(50), nullable=True),
        sa.Column("logo_size_bytes", sa.Integer(), nullable=True),
        sa.Column("header_text", sa.String(200), nullable=True),
        sa.Column("footer_text", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("firm_branding")
    op.drop_table("team_activity_logs")
    sa.Enum(name="teamactiontype").drop(op.get_bind(), checkfirst=True)
    op.drop_table("export_shares")
