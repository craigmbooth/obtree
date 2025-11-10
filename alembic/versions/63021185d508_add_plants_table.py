"""add plants table

Revision ID: 63021185d508
Revises: 4ef2d86e29a6
Create Date: 2025-11-10 16:03:56.776480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.types import GUID


# revision identifiers, used by Alembic.
revision: str = '63021185d508'
down_revision: Union[str, Sequence[str], None] = '4ef2d86e29a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('plants',
    sa.Column('id', GUID(length=36), nullable=False),
    sa.Column('plant_id', sa.String(length=255), nullable=False),
    sa.Column('accession_id', GUID(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', GUID(length=36), nullable=True),
    sa.ForeignKeyConstraint(['accession_id'], ['accessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('plants')
