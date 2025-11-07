from datetime import datetime
from typing import Optional, Union
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.project_accession_field import FieldType


class AccessionFieldValueCreate(BaseModel):
    """Schema for creating/updating a field value."""
    field_id: UUID = Field(..., description="ID of the custom field")
    value: Union[str, Decimal] = Field(..., description="Value for the field")


class AccessionFieldValueResponse(BaseModel):
    """Schema for field value response with field metadata."""
    id: Optional[UUID] = None  # None for fields without values yet
    accession_id: UUID
    field_id: UUID
    field_name: str
    field_type: FieldType
    value: Union[str, Decimal, None]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
