"""add_select_to_fieldtype_enum

Revision ID: 2f16c29081c9
Revises: b49b4ff88eb7
Create Date: 2025-11-20 21:21:50.269732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f16c29081c9'
down_revision: Union[str, Sequence[str], None] = 'b49b4ff88eb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add 'SELECT' to the fieldtype enum (PostgreSQL only)
    # SQLite doesn't have enum types, so this is a no-op for SQLite
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute("ALTER TYPE fieldtype ADD VALUE IF NOT EXISTS 'SELECT'")


def downgrade() -> None:
    """Downgrade schema."""
    # Cannot remove enum values in PostgreSQL, so this is a no-op
    pass
