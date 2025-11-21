"""make accession species_id nullable for hybrids

Revision ID: 3ac48cef7032
Revises: 623b22877c4f
Create Date: 2025-11-20 16:38:23.300279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.types import GUID


# revision identifiers, used by Alembic.
revision: str = '3ac48cef7032'
down_revision: Union[str, Sequence[str], None] = '623b22877c4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make species_id nullable for hybrid accessions
    with op.batch_alter_table('accessions', schema=None) as batch_op:
        batch_op.alter_column('species_id',
                              existing_type=GUID(length=36),
                              nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make species_id non-nullable again
    with op.batch_alter_table('accessions', schema=None) as batch_op:
        batch_op.alter_column('species_id',
                              existing_type=GUID(length=36),
                              nullable=False)
