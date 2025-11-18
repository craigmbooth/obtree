from datetime import datetime
from typing import Optional, List
from uuid import UUID
import json
from pydantic import BaseModel, Field, field_serializer, field_validator

from app.models.project_accession_field import FieldType


class LocationTypeFieldBase(BaseModel):
    """Base schema for location type field data."""
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

    # Select field options
    field_options: Optional[List[str]] = Field(None, description="List of valid options for SELECT fields")


class LocationTypeFieldCreate(LocationTypeFieldBase):
    """Schema for creating a new location type field."""
    id: Optional[UUID] = Field(None, description="Optional field ID for updates")


class LocationTypeFieldUpdate(BaseModel):
    """Schema for updating a location type field."""
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

    # Select field options
    field_options: Optional[List[str]] = None


class LocationTypeFieldResponse(LocationTypeFieldBase):
    """Schema for location type field response."""
    id: UUID
    location_type_id: UUID
    is_deleted: bool
    is_locked: bool  # Computed property from model
    created_at: datetime
    created_by: UUID

    @field_validator('field_options', mode='before')
    @classmethod
    def parse_field_options(cls, v):
        """Convert JSON string from database to list."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    class Config:
        from_attributes = True
