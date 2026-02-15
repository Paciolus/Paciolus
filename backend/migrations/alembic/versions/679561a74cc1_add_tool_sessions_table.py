"""Add tool_sessions table

Sprint 262: DB-backed tool session storage replaces in-memory dicts.

Revision ID: 679561a74cc1
Revises: 0b17eb7cb88c
Create Date: 2026-02-15 17:27:08.901528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '679561a74cc1'
down_revision: Union[str, None] = '0b17eb7cb88c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tool_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_name', sa.String(length=50), nullable=False),
        sa.Column('session_data', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'tool_name', name='uq_tool_session_user_tool'),
    )
    op.create_index('ix_tool_sessions_id', 'tool_sessions', ['id'])
    op.create_index('ix_tool_sessions_user_id', 'tool_sessions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_tool_sessions_user_id')
    op.drop_index('ix_tool_sessions_id')
    op.drop_table('tool_sessions')
