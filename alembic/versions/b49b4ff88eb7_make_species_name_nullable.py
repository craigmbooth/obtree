"""make_species_name_nullable

Revision ID: b49b4ff88eb7
Revises: 8fc5eefb335e
Create Date: 2025-11-20 20:43:37.096152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b49b4ff88eb7'
down_revision: Union[str, Sequence[str], None] = '8fc5eefb335e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make species_name nullable
    with op.batch_alter_table('species') as batch_op:
        batch_op.alter_column('species_name',
                              existing_type=sa.String(),
                              nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make species_name not nullable again
    with op.batch_alter_table('species') as batch_op:
        batch_op.alter_column('species_name',
                              existing_type=sa.String(),
                              nullable=False)
