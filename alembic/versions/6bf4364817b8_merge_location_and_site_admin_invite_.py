"""merge location and site admin invite heads

Revision ID: 6bf4364817b8
Revises: 98d464c324f3, e5115b55874f
Create Date: 2025-11-19 21:14:19.854482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bf4364817b8'
down_revision: Union[str, Sequence[str], None] = ('98d464c324f3', 'e5115b55874f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
