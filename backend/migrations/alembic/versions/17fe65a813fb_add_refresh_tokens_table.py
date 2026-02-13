"""add refresh_tokens table

Revision ID: 17fe65a813fb
Revises: e2f21cb79a61
Create Date: 2026-02-13 10:26:18.416107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17fe65a813fb'
down_revision: Union[str, None] = 'e2f21cb79a61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('refresh_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('replaced_by_hash', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_refresh_tokens_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_refresh_tokens_token_hash'), ['token_hash'], unique=True)
        batch_op.create_index(batch_op.f('ix_refresh_tokens_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_refresh_tokens_user_id'))
        batch_op.drop_index(batch_op.f('ix_refresh_tokens_token_hash'))
        batch_op.drop_index(batch_op.f('ix_refresh_tokens_id'))

    op.drop_table('refresh_tokens')
