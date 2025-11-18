"""add_site_admin_invite_support

Revision ID: e5115b55874f
Revises: 18c800399016
Create Date: 2025-11-18 12:21:58.541714

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5115b55874f'
down_revision: Union[str, Sequence[str], None] = '18c800399016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type for invite type
    invite_type_enum = sa.Enum('ORGANIZATION', 'SITE_ADMIN', name='invitetype')
    invite_type_enum.create(op.get_bind(), checkfirst=True)

    # Add invite_type column with default 'ORGANIZATION' for existing rows
    op.add_column('invites', sa.Column('invite_type', invite_type_enum, nullable=False, server_default='ORGANIZATION'))

    # Make organization_id nullable (site admin invites won't have an org)
    # Using batch mode for SQLite compatibility
    with op.batch_alter_table('invites', schema=None) as batch_op:
        batch_op.alter_column('organization_id',
                              existing_type=sa.UUID(),
                              nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove all site admin invites first (they would violate NOT NULL constraint)
    op.execute("DELETE FROM invites WHERE invite_type = 'SITE_ADMIN'")

    # Make organization_id NOT NULL again (using batch mode for SQLite)
    with op.batch_alter_table('invites', schema=None) as batch_op:
        batch_op.alter_column('organization_id',
                              existing_type=sa.UUID(),
                              nullable=False)

    # Drop invite_type column
    op.drop_column('invites', 'invite_type')

    # Drop enum type
    invite_type_enum = sa.Enum('ORGANIZATION', 'SITE_ADMIN', name='invitetype')
    invite_type_enum.drop(op.get_bind(), checkfirst=True)
