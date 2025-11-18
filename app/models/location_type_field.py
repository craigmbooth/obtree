from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, String, ForeignKey, Integer, Boolean, Enum, Float
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.project_accession_field import FieldType


class LocationTypeField(Base):
    """Location type field model - defines fields for location types.

    Similar to EventTypeField, this defines the schema for location fields
    with type-specific validation rules (e.g., blocks, rows, coordinates).
    """

    __tablename__ = "location_type_fields"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    location_type_id = Column(GUID, ForeignKey("location_types.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(255), nullable=False)
    field_type = Column(Enum(FieldType), nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    # String validation
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    regex_pattern = Column(String, nullable=True)

    # Number validation
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    location_type = relationship("LocationType", back_populates="fields")
    creator = relationship("User")
    field_values = relationship("LocationFieldValue", back_populates="field", cascade="all, delete-orphan")

    @property
    def is_locked(self):
        """Check if field is locked (has existing values).

        Locked fields cannot have their type changed to prevent data corruption.

        Returns:
            bool: True if field has values, False otherwise.
        """
        return len(self.field_values) > 0
