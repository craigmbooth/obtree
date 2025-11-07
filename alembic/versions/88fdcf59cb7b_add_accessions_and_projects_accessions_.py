"""add accessions and projects_accessions tables

Revision ID: 88fdcf59cb7b
Revises: 60247aee9f81
Create Date: 2025-11-07 15:57:12.479821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.types import GUID


# revision identifiers, used by Alembic.
revision: str = '88fdcf59cb7b'
down_revision: Union[str, Sequence[str], None] = '60247aee9f81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create accessions table
    op.create_table('accessions',
    sa.Column('id', GUID(length=36), nullable=False),
    sa.Column('accession', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('species_id', GUID(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', GUID(length=36), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['species_id'], ['species.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_accessions_id'), 'accessions', ['id'], unique=False)

    # Create projects_accessions association table
    op.create_table('projects_accessions',
    sa.Column('project_id', GUID(length=36), nullable=False),
    sa.Column('accession_id', GUID(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['accession_id'], ['accessions.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('project_id', 'accession_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop projects_accessions first (has foreign keys to accessions)
    op.drop_table('projects_accessions')

    # Drop accessions table
    op.drop_index(op.f('ix_accessions_id'), table_name='accessions')
    op.drop_table('accessions')
