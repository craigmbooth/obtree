"""merge migration branches

Revision ID: dd46f6024d35
Revises: 2e274636ea10, 5253f04e4e0c
Create Date: 2025-11-07 13:45:48.329065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd46f6024d35'
down_revision: Union[str, Sequence[str], None] = ('2e274636ea10', '5253f04e4e0c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
