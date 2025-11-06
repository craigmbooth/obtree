"""Custom SQLAlchemy types for cross-database compatibility."""
import uuid
from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    String(36), storing as stringified hex values.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        else:
            return str(value) if isinstance(value, uuid.UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value
