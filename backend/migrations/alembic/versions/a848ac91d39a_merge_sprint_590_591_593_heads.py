"""merge sprint 590 591 593 heads

Revision ID: a848ac91d39a
Revises: 591a_dunning, c2d3e4f5a6b7, d1e2f3a4b5c6
Create Date: 2026-04-08 17:54:13.276496

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "a848ac91d39a"
down_revision: str | None = ("591a_dunning", "c2d3e4f5a6b7", "d1e2f3a4b5c6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
