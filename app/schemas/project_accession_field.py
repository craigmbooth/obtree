from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.models.project_accession_field import FieldType


class ProjectAccessionFieldBase(BaseModel):
    """Base schema for project accession field data."""
    field_name: str = Field(..., min_length=1, max_length=255, description="Name of the custom field")
    field_type: FieldType = Field(..., description="Type of the field (string or number)")
    is_required: bool = Field(default=False, description="Whether this field is required")
    display_order: int = Field(default=0, description="Display order for UI")


class ProjectAccessionFieldCreate(ProjectAccessionFieldBase):
    """Schema for creating a new custom field."""
    # Validation rules for string fields
    min_length: Optional[int] = Field(None, description="Minimum length for string values")
    max_length: Optional[int] = Field(None, description="Maximum length for string values")
    regex_pattern: Optional[str] = Field(None, description="Regex pattern for string values")

    # Validation rules for number fields
    min_value: Optional[Decimal] = Field(None, description="Minimum value for numbers")
    max_value: Optional[Decimal] = Field(None, description="Maximum value for numbers")

    @field_validator('min_length', 'max_length')
    @classmethod
    def validate_string_constraints(cls, v, info):
        """Ensure string constraints are positive."""
        if v is not None and v < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        return v

    @field_validator('max_length')
    @classmethod
    def validate_max_greater_than_min(cls, v, info):
        """Ensure max_length is greater than min_length if both are set."""
        data = info.data
        if v is not None and data.get('min_length') is not None and v < data['min_length']:
            raise ValueError("max_length must be greater than or equal to min_length")
        return v

    @field_validator('max_value')
    @classmethod
    def validate_max_value_greater_than_min(cls, v, info):
        """Ensure max_value is greater than min_value if both are set."""
        data = info.data
        if v is not None and data.get('min_value') is not None and v < data['min_value']:
            raise ValueError("max_value must be greater than or equal to min_value")
        return v


class ProjectAccessionFieldUpdate(BaseModel):
    """Schema for updating a custom field (type cannot be changed if field is locked)."""
    field_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_required: Optional[bool] = None
    display_order: Optional[int] = None

    # Validation rules can be updated
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex_pattern: Optional[str] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None


class ProjectAccessionFieldResponse(ProjectAccessionFieldBase):
    """Schema for custom field response."""
    id: UUID
    project_id: UUID
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    created_by: UUID
    is_locked: bool = Field(description="True if field has values and type cannot be changed")

    # Validation rules
    min_length: Optional[int]
    max_length: Optional[int]
    regex_pattern: Optional[str]
    min_value: Optional[Decimal]
    max_value: Optional[Decimal]

    class Config:
        from_attributes = True
