"""Add description field to organizations

Revision ID: 4deb0f562b2f
Revises: 490490843fb4
Create Date: 2025-11-06 06:25:16.274218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4deb0f562b2f'
down_revision: Union[str, Sequence[str], None] = '490490843fb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('organizations', sa.Column('description', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('organizations', 'description')
