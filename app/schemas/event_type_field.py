from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.project_accession_field import FieldType


class EventTypeFieldBase(BaseModel):
    """Base schema for event type field data."""
    field_name: str = Field(..., min_length=1, max_length=255, description="Name of the field")
    field_type: FieldType = Field(..., description="Data type of the field (STRING or NUMBER)")
    is_required: bool = Field(default=False, description="Whether this field is required")
    display_order: int = Field(default=0, description="Order for displaying the field in forms")

    # String validation
    min_length: Optional[int] = Field(None, description="Minimum length for STRING fields")
    max_length: Optional[int] = Field(None, description="Maximum length for STRING fields")
    regex_pattern: Optional[str] = Field(None, description="Regex pattern for STRING field validation")

    # Number validation
    min_value: Optional[float] = Field(None, description="Minimum value for NUMBER fields")
    max_value: Optional[float] = Field(None, description="Maximum value for NUMBER fields")


class EventTypeFieldCreate(EventTypeFieldBase):
    """Schema for creating a new event type field."""
    pass


class EventTypeFieldUpdate(BaseModel):
    """Schema for updating an event type field."""
    field_name: Optional[str] = Field(None, min_length=1, max_length=255)
    field_type: Optional[FieldType] = None
    is_required: Optional[bool] = None
    display_order: Optional[int] = None

    # String validation
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex_pattern: Optional[str] = None

    # Number validation
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class EventTypeFieldResponse(EventTypeFieldBase):
    """Schema for event type field response."""
    id: UUID
    event_type_id: UUID
    is_deleted: bool
    is_locked: bool  # Computed property from model
    created_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True
