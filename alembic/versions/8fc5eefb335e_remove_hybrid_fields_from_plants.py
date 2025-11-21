"""remove_hybrid_fields_from_plants

Revision ID: 8fc5eefb335e
Revises: 3ac48cef7032
Create Date: 2025-11-20 20:23:08.361047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fc5eefb335e'
down_revision: Union[str, Sequence[str], None] = '3ac48cef7032'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove hybrid fields from plants table
    op.drop_column('plants', 'is_hybrid')
    op.drop_column('plants', 'parent_species_1_id')
    op.drop_column('plants', 'parent_species_2_id')


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add hybrid fields to plants table
    op.add_column('plants', sa.Column('is_hybrid', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('plants', sa.Column('parent_species_1_id', sa.String(length=36), nullable=True))
    op.add_column('plants', sa.Column('parent_species_2_id', sa.String(length=36), nullable=True))
