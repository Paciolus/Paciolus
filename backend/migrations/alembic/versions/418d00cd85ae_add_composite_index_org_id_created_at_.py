"""add_composite_index_org_id_created_at_team_activity

Revision ID: 418d00cd85ae
Revises: f0a1b2c3d4e5
Create Date: 2026-03-19 16:06:24.526378

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "418d00cd85ae"
down_revision: str | None = "f0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("team_activity_logs", schema=None) as batch_op:
        batch_op.create_index("ix_team_activity_org_created", ["organization_id", "created_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("team_activity_logs", schema=None) as batch_op:
        batch_op.drop_index("ix_team_activity_org_created")
