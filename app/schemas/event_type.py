from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.event_type_field import EventTypeFieldCreate, EventTypeFieldResponse


class EventTypeBase(BaseModel):
    """Base schema for event type data."""
    event_name: str = Field(..., min_length=1, max_length=255, description="Name of the event type")
    description: Optional[str] = Field(None, description="Optional description of the event type")
    display_order: int = Field(default=0, description="Order for displaying the event type")


class EventTypeCreate(EventTypeBase):
    """Schema for creating a new event type."""
    project_id: Optional[UUID] = Field(None, description="Optional project ID (NULL = org-level, set = project-level)")
    fields: Optional[List[EventTypeFieldCreate]] = Field(default_factory=list, description="Fields for this event type")


class EventTypeUpdate(BaseModel):
    """Schema for updating an event type."""
    event_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    display_order: Optional[int] = None
    fields: Optional[List[EventTypeFieldCreate]] = Field(None, description="Fields for this event type")


class EventTypeResponse(EventTypeBase):
    """Schema for event type response."""
    id: UUID
    organization_id: UUID
    project_id: Optional[UUID]
    is_deleted: bool
    created_at: datetime
    created_by: UUID
    fields: List[EventTypeFieldResponse] = Field(default_factory=list, description="Fields for this event type")

    class Config:
        from_attributes = True
