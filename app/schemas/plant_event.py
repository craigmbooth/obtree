from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.event_field_value import EventFieldValueCreate, EventFieldValueResponse


class PlantEventBase(BaseModel):
    """Base schema for plant event data."""
    event_type_id: UUID = Field(..., description="ID of the event type")
    event_date: datetime = Field(..., description="When the event occurred (can be backdated)")
    notes: Optional[str] = Field(None, description="Optional free-form notes about the event")


class PlantEventCreate(PlantEventBase):
    """Schema for creating a new plant event."""
    field_values: Optional[List[EventFieldValueCreate]] = Field(default_factory=list, description="Field values for this event")


class PlantEventUpdate(BaseModel):
    """Schema for updating a plant event."""
    event_type_id: Optional[UUID] = None
    event_date: Optional[datetime] = None
    notes: Optional[str] = None
    field_values: Optional[List[EventFieldValueCreate]] = None


class PlantEventResponse(PlantEventBase):
    """Schema for plant event response."""
    id: UUID
    plant_id: UUID
    event_type_name: str  # Denormalized for convenience
    created_at: datetime
    created_by: UUID
    field_values: List[EventFieldValueResponse] = Field(default_factory=list, description="Field values for this event")

    class Config:
        from_attributes = True
