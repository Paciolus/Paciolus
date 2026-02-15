"""Add failed_login_attempts and locked_until to users

Sprint 261: DB-backed account lockout replaces in-memory _lockout_tracker.

Revision ID: 0b17eb7cb88c
Revises: ea6c8f7cc976
Create Date: 2026-02-15 17:17:33.182973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b17eb7cb88c'
down_revision: Union[str, None] = 'ea6c8f7cc976'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('locked_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_login_attempts')
