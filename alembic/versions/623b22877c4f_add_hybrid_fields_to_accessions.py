"""add hybrid fields to accessions

Revision ID: 623b22877c4f
Revises: f4f96d601b89
Create Date: 2025-11-20 15:30:26.094202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.types import GUID


# revision identifiers, used by Alembic.
revision: str = '623b22877c4f'
down_revision: Union[str, Sequence[str], None] = 'f4f96d601b89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add hybrid fields to accessions table (foreign keys managed by SQLAlchemy ORM)
    op.add_column('accessions', sa.Column('is_hybrid', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('accessions', sa.Column('parent_species_1_id', GUID(length=36), nullable=True))
    op.add_column('accessions', sa.Column('parent_species_2_id', GUID(length=36), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop columns
    op.drop_column('accessions', 'parent_species_2_id')
    op.drop_column('accessions', 'parent_species_1_id')
    op.drop_column('accessions', 'is_hybrid')
