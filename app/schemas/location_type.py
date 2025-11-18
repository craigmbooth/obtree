from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.location_type_field import LocationTypeFieldCreate, LocationTypeFieldResponse


class LocationTypeBase(BaseModel):
    """Base schema for location type data."""
    location_name: str = Field(..., min_length=1, max_length=255, description="Name of the location type")
    description: Optional[str] = Field(None, description="Optional description of the location type")
    display_order: int = Field(default=0, description="Order for displaying the location type")


class LocationTypeCreate(LocationTypeBase):
    """Schema for creating a new location type."""
    fields: Optional[List[LocationTypeFieldCreate]] = Field(default_factory=list, description="Fields for this location type")


class LocationTypeUpdate(BaseModel):
    """Schema for updating a location type."""
    location_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    display_order: Optional[int] = None
    fields: Optional[List[LocationTypeFieldCreate]] = Field(None, description="Fields for this location type")


class LocationTypeResponse(LocationTypeBase):
    """Schema for location type response."""
    id: UUID
    organization_id: UUID
    is_deleted: bool
    created_at: datetime
    created_by: UUID
    fields: List[LocationTypeFieldResponse] = Field(default_factory=list, description="Fields for this location type")

    class Config:
        from_attributes = True
