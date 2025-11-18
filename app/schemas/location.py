from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.location_field_value import LocationFieldValueCreate, LocationFieldValueResponse


class LocationBase(BaseModel):
    """Base schema for location data."""
    location_type_id: UUID = Field(..., description="ID of the location type")
    location_name: str = Field(..., min_length=1, max_length=255, description="Name for this specific location")
    notes: Optional[str] = Field(None, description="Optional free-form notes about the location")


class LocationCreate(LocationBase):
    """Schema for creating a new location."""
    field_values: Optional[List[LocationFieldValueCreate]] = Field(default_factory=list, description="Field values for this location")


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    location_type_id: Optional[UUID] = None
    location_name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    field_values: Optional[List[LocationFieldValueCreate]] = None


class LocationResponse(LocationBase):
    """Schema for location response."""
    id: UUID
    organization_id: UUID
    location_type_name: str  # Denormalized for convenience
    created_at: datetime
    created_by: UUID
    field_values: List[LocationFieldValueResponse] = Field(default_factory=list, description="Field values for this location")

    class Config:
        from_attributes = True
