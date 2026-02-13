"""add pending_email to users

Revision ID: ea6c8f7cc976
Revises: c324b5d13ed5
Create Date: 2026-02-13 16:57:41.294368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea6c8f7cc976'
down_revision: Union[str, None] = 'c324b5d13ed5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Sprint 203: Add pending_email column for email-change re-verification
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pending_email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('pending_email')
