from datetime import datetime
import uuid as uuid_lib
from decimal import Decimal
from typing import Union
from sqlalchemy import Column, DateTime, ForeignKey, Text, Numeric, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.database import Base
from app.models.types import GUID


class AccessionFieldValue(Base):
    """Value for a custom field on an accession."""

    __tablename__ = "accession_field_values"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    accession_id = Column(GUID, ForeignKey("accessions.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(GUID, ForeignKey("project_accession_fields.id"), nullable=False, index=True)

    # Polymorphic value storage - only one should be set based on field type
    value_string = Column(Text, nullable=True)
    value_number = Column(Numeric, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    accession = relationship("Accession", back_populates="field_values")
    field = relationship("ProjectAccessionField", back_populates="field_values")

    # Properties for response serialization
    @property
    def field_name(self) -> str:
        """Get the field name from the related field."""
        return self.field.field_name if self.field else ""

    @property
    def field_type(self):
        """Get the field type from the related field."""
        return self.field.field_type if self.field else None

    @property
    def value(self) -> Union[str, Decimal, None]:
        """Get the value based on field type."""
        from app.models.project_accession_field import FieldType
        if self.field and self.field.field_type == FieldType.STRING:
            return self.value_string
        elif self.field and self.field.field_type == FieldType.NUMBER:
            return self.value_number
        return None

    __table_args__ = (
        # Ensure each accession has at most one value per field
        UniqueConstraint('accession_id', 'field_id', name='uq_accession_field'),
        # Ensure only the correct value column is populated based on field type
        # This will be enforced in application logic since we can't reference field.field_type in a check constraint
    )
