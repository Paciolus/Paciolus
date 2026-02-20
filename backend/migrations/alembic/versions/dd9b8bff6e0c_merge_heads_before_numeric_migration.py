"""merge_heads_before_numeric_migration

Revision ID: dd9b8bff6e0c
Revises: b7d2f1e4a903, f8a3d1c09b72
Create Date: 2026-02-20 18:01:20.913211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd9b8bff6e0c'
down_revision: Union[str, None] = ('b7d2f1e4a903', 'f8a3d1c09b72')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
