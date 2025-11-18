from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, ForeignKey, String, Float, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID


class LocationFieldValue(Base):
    """Location field value model - stores field values for locations.

    Uses polymorphic storage pattern: value_string OR value_number
    depending on the field's type. Similar to EventFieldValue pattern.
    """

    __tablename__ = "location_field_values"
    __table_args__ = (
        UniqueConstraint('location_id', 'field_id', name='uq_location_field'),
    )

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    location_id = Column(GUID, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(GUID, ForeignKey("location_type_fields.id", ondelete="CASCADE"), nullable=False, index=True)
    value_string = Column(String, nullable=True)  # Used for STRING type fields
    value_number = Column(Float, nullable=True)   # Used for NUMBER type fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    location = relationship("Location", back_populates="field_values")
    field = relationship("LocationTypeField", back_populates="field_values")
