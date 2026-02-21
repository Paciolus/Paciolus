"""add subscriptions table

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-02-21 13:00:00.000000

Sprint 363: Subscription model for billing lifecycle management.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: str | None = 'c4d5e6f7a8b9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tier', sa.Enum('free', 'starter', 'professional', 'team', 'enterprise', name='subscription_tier'), nullable=False),
        sa.Column('status', sa.Enum('active', 'past_due', 'canceled', 'trialing', name='subscriptionstatus'), nullable=False),
        sa.Column('billing_interval', sa.Enum('monthly', 'annual', name='billinginterval'), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_subscriptions_id', 'subscriptions', ['id'])
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'], unique=True)
    op.create_index('ix_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'], unique=True)
    op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_subscriptions_stripe_subscription_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_stripe_customer_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_id', table_name='subscriptions')
    op.drop_table('subscriptions')
