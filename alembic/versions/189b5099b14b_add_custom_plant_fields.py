"""add custom plant fields

Revision ID: 189b5099b14b
Revises: 63021185d508
Create Date: 2025-11-10 16:55:07.695987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.types import GUID


# revision identifiers, used by Alembic.
revision: str = '189b5099b14b'
down_revision: Union[str, Sequence[str], None] = '63021185d508'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create project_plant_fields table
    op.create_table('project_plant_fields',
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
    op.create_index(op.f('ix_project_plant_fields_id'), 'project_plant_fields', ['id'], unique=False)
    op.create_index(op.f('ix_project_plant_fields_project_id'), 'project_plant_fields', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_plant_fields_is_deleted'), 'project_plant_fields', ['is_deleted'], unique=False)

    # Create plant_field_values table
    op.create_table('plant_field_values',
        sa.Column('id', GUID(length=36), nullable=False),
        sa.Column('plant_id', GUID(length=36), nullable=False),
        sa.Column('field_id', GUID(length=36), nullable=False),
        sa.Column('value_string', sa.Text(), nullable=True),
        sa.Column('value_number', sa.Numeric(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['project_plant_fields.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plant_id', 'field_id', name='uq_plant_field')
    )
    op.create_index(op.f('ix_plant_field_values_id'), 'plant_field_values', ['id'], unique=False)
    op.create_index(op.f('ix_plant_field_values_plant_id'), 'plant_field_values', ['plant_id'], unique=False)
    op.create_index(op.f('ix_plant_field_values_field_id'), 'plant_field_values', ['field_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop plant_field_values first (has foreign keys to project_plant_fields)
    op.drop_index(op.f('ix_plant_field_values_field_id'), table_name='plant_field_values')
    op.drop_index(op.f('ix_plant_field_values_plant_id'), table_name='plant_field_values')
    op.drop_index(op.f('ix_plant_field_values_id'), table_name='plant_field_values')
    op.drop_table('plant_field_values')

    # Drop project_plant_fields table
    op.drop_index(op.f('ix_project_plant_fields_is_deleted'), table_name='project_plant_fields')
    op.drop_index(op.f('ix_project_plant_fields_project_id'), table_name='project_plant_fields')
    op.drop_index(op.f('ix_project_plant_fields_id'), table_name='project_plant_fields')
    op.drop_table('project_plant_fields')
