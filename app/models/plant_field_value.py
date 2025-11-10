"""Plant field value model for storing custom field values on plants.

This module defines the PlantFieldValue model which stores the actual values
for custom fields on individual plants. Works identically to AccessionFieldValue
but applies to plants instead of accessions.
"""

from datetime import datetime
from decimal import Decimal
from typing import Union
import uuid as uuid_lib

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID


class PlantFieldValue(Base):
    """Value for a custom field on a plant.

    Stores the actual data for custom fields defined in ProjectPlantField.
    Uses polymorphic storage with value_string for string fields and
    value_number for numeric fields.

    Attributes:
        id: Unique identifier (UUID) for the value.
        plant_id: Foreign key to the parent plant (CASCADE on delete).
        field_id: Foreign key to the field definition.
        value_string: String value (used when field_type is STRING).
        value_number: Numeric value (used when field_type is NUMBER).
        created_at: Timestamp when value was created.
        updated_at: Timestamp when value was last updated.
        plant: Relationship to the Plant.
        field: Relationship to the ProjectPlantField definition.
    """

    __tablename__ = "plant_field_values"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    plant_id = Column(
        GUID, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_id = Column(
        GUID, ForeignKey("project_plant_fields.id"), nullable=False, index=True
    )

    # Polymorphic value storage - only one should be set based on field type
    value_string = Column(Text, nullable=True)
    value_number = Column(Numeric, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    plant = relationship("Plant", back_populates="field_values")
    field = relationship("ProjectPlantField", back_populates="field_values")

    # Properties for response serialization
    @property
    def field_name(self) -> str:
        """Get the field name from the related field.

        Returns:
            str: The name of the custom field.
        """
        return self.field.field_name if self.field else ""

    @property
    def field_type(self):
        """Get the field type from the related field.

        Returns:
            FieldType: The type of the custom field (STRING or NUMBER).
        """
        return self.field.field_type if self.field else None

    @property
    def value(self) -> Union[str, Decimal, None]:
        """Get the value based on field type.

        Returns the appropriate value column based on the field's type.
        For STRING fields, returns value_string. For NUMBER fields,
        returns value_number.

        Returns:
            Union[str, Decimal, None]: The field value.
        """
        from app.models.project_accession_field import FieldType

        if self.field and self.field.field_type == FieldType.STRING:
            return self.value_string
        elif self.field and self.field.field_type == FieldType.NUMBER:
            return self.value_number
        return None

    __table_args__ = (
        # Ensure each plant has at most one value per field
        UniqueConstraint("plant_id", "field_id", name="uq_plant_field"),
        # Ensure only the correct value column is populated based on field type
        # This will be enforced in application logic since we can't reference field.field_type in a check constraint
    )

    def __repr__(self) -> str:
        """Return string representation of the field value."""
        return f"<PlantFieldValue(id={self.id}, plant_id={self.plant_id}, field_id={self.field_id})>"
