"""add custom accession fields

Revision ID: 4ef2d86e29a6
Revises: 88fdcf59cb7b
Create Date: 2025-11-07 16:45:46.611143

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.types import GUID


# revision identifiers, used by Alembic.
revision: str = '4ef2d86e29a6'
down_revision: Union[str, Sequence[str], None] = '88fdcf59cb7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create project_accession_fields table
    op.create_table('project_accession_fields',
        sa.Column('id', GUID(length=36), nullable=False),
        sa.Column('project_id', GUID(length=36), nullable=False),
        sa.Column('field_name', sa.String(length=255), nullable=False),
        sa.Column('field_type', sa.Enum('STRING', 'NUMBER', name='fieldtype'), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('regex_pattern', sa.Text(), nullable=True),
        sa.Column('min_value', sa.Numeric(), nullable=True),
        sa.Column('max_value', sa.Numeric(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', GUID(length=36), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_accession_fields_id'), 'project_accession_fields', ['id'], unique=False)
    op.create_index(op.f('ix_project_accession_fields_project_id'), 'project_accession_fields', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_accession_fields_is_deleted'), 'project_accession_fields', ['is_deleted'], unique=False)

    # Create accession_field_values table
    op.create_table('accession_field_values',
        sa.Column('id', GUID(length=36), nullable=False),
        sa.Column('accession_id', GUID(length=36), nullable=False),
        sa.Column('field_id', GUID(length=36), nullable=False),
        sa.Column('value_string', sa.Text(), nullable=True),
        sa.Column('value_number', sa.Numeric(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['accession_id'], ['accessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['project_accession_fields.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('accession_id', 'field_id', name='uq_accession_field')
    )
    op.create_index(op.f('ix_accession_field_values_id'), 'accession_field_values', ['id'], unique=False)
    op.create_index(op.f('ix_accession_field_values_accession_id'), 'accession_field_values', ['accession_id'], unique=False)
    op.create_index(op.f('ix_accession_field_values_field_id'), 'accession_field_values', ['field_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop accession_field_values first (has foreign keys to project_accession_fields)
    op.drop_index(op.f('ix_accession_field_values_field_id'), table_name='accession_field_values')
    op.drop_index(op.f('ix_accession_field_values_accession_id'), table_name='accession_field_values')
    op.drop_index(op.f('ix_accession_field_values_id'), table_name='accession_field_values')
    op.drop_table('accession_field_values')

    # Drop project_accession_fields table
    op.drop_index(op.f('ix_project_accession_fields_is_deleted'), table_name='project_accession_fields')
    op.drop_index(op.f('ix_project_accession_fields_project_id'), table_name='project_accession_fields')
    op.drop_index(op.f('ix_project_accession_fields_id'), table_name='project_accession_fields')
    op.drop_table('project_accession_fields')

    # Drop the enum type
    op.execute('DROP TYPE fieldtype')
