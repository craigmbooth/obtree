from datetime import datetime
from typing import Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, computed_field


class LocationFieldValueCreate(BaseModel):
    """Schema for creating/updating location field values."""
    field_id: UUID = Field(..., description="ID of the location type field")
    value: Union[str, float, int] = Field(..., description="Value for the field (string or number)")

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        """Ensure value is either string or number."""
        if not isinstance(v, (str, int, float)):
            raise ValueError('Value must be a string or number')
        return v


class LocationFieldValueResponse(BaseModel):
    """Schema for location field value response."""
    id: UUID
    location_id: UUID
    field_id: UUID
    field_name: str  # Denormalized for convenience
    field_type: str  # "string" or "number"
    value_string: Optional[str]
    value_number: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @computed_field
    @property
    def value(self) -> Union[str, float, None]:
        """Get the appropriate value based on field type."""
        return self.value_string if self.value_string is not None else self.value_number
