"""add hybrid fields to plants

Revision ID: f4f96d601b89
Revises: 795d2190152a
Create Date: 2025-11-20 15:11:19.348933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.types import GUID


# revision identifiers, used by Alembic.
revision: str = 'f4f96d601b89'
down_revision: Union[str, Sequence[str], None] = '795d2190152a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns directly (foreign keys will be managed by SQLAlchemy ORM)
    op.add_column('plants', sa.Column('is_hybrid', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('plants', sa.Column('parent_species_1_id', GUID(length=36), nullable=True))
    op.add_column('plants', sa.Column('parent_species_2_id', GUID(length=36), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop columns
    op.drop_column('plants', 'parent_species_2_id')
    op.drop_column('plants', 'parent_species_1_id')
    op.drop_column('plants', 'is_hybrid')
