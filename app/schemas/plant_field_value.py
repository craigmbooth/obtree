"""Plant field value schemas for API request/response validation.

This module defines the Pydantic schemas used for validating and serializing
plant custom field values in API requests and responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.project_accession_field import FieldType


class PlantFieldValueCreate(BaseModel):
    """Schema for creating/updating a plant field value.

    Attributes:
        field_id: UUID of the custom field definition.
        value: Value for the field (string or number depending on field type).
    """

    field_id: UUID = Field(..., description="ID of the custom field")
    value: Union[str, Decimal] = Field(..., description="Value for the field")


class PlantFieldValueResponse(BaseModel):
    """Schema for plant field value response with field metadata.

    Includes the field value along with metadata about the field definition.

    Attributes:
        id: UUID of the value (None if field has no value yet).
        plant_id: UUID of the parent plant.
        field_id: UUID of the field definition.
        field_name: Name of the custom field.
        field_type: Type of the field (STRING or NUMBER).
        value: The field value (string, number, or None if not set).
        created_at: Timestamp when value was created.
        updated_at: Timestamp when value was last updated.
    """

    id: Optional[UUID] = None  # None for fields without values yet
    plant_id: UUID
    field_id: UUID
    field_name: str
    field_type: FieldType
    value: Union[str, Decimal, None]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True
