"""Project plant field schemas for API request/response validation.

This module defines the Pydantic schemas used for validating and serializing
plant custom field definitions in API requests and responses.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.project_accession_field import FieldType


class ProjectPlantFieldBase(BaseModel):
    """Base schema for project plant field data.

    Attributes:
        field_name: Name of the custom field.
        field_type: Type of the field (STRING or NUMBER).
        is_required: Whether this field is required for plants.
        display_order: Display order for UI rendering.
    """

    field_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the custom field"
    )
    field_type: FieldType = Field(..., description="Type of the field (string or number)")
    is_required: bool = Field(default=False, description="Whether this field is required")
    display_order: int = Field(default=0, description="Display order for UI")


class ProjectPlantFieldCreate(ProjectPlantFieldBase):
    """Schema for creating a new plant custom field.

    Includes all base fields plus optional validation rules for both
    string and number field types.

    Attributes:
        min_length: Minimum length for string values.
        max_length: Maximum length for string values.
        regex_pattern: Regex pattern for string validation.
        min_value: Minimum value for numbers.
        max_value: Maximum value for numbers.
    """

    # Validation rules for string fields
    min_length: Optional[int] = Field(None, description="Minimum length for string values")
    max_length: Optional[int] = Field(None, description="Maximum length for string values")
    regex_pattern: Optional[str] = Field(None, description="Regex pattern for string values")

    # Validation rules for number fields
    min_value: Optional[Decimal] = Field(None, description="Minimum value for numbers")
    max_value: Optional[Decimal] = Field(None, description="Maximum value for numbers")

    @field_validator("min_length", "max_length")
    @classmethod
    def validate_string_constraints(cls, v, info):
        """Ensure string constraints are positive.

        Args:
            v: The field value.
            info: Field validation info.

        Returns:
            The validated value.

        Raises:
            ValueError: If value is negative.
        """
        if v is not None and v < 0:
            raise ValueError(f"{info.field_name} must be non-negative")
        return v

    @field_validator("max_length")
    @classmethod
    def validate_max_greater_than_min(cls, v, info):
        """Ensure max_length is greater than min_length if both are set.

        Args:
            v: The max_length value.
            info: Field validation info.

        Returns:
            The validated value.

        Raises:
            ValueError: If max_length < min_length.
        """
        data = info.data
        if v is not None and data.get("min_length") is not None and v < data["min_length"]:
            raise ValueError("max_length must be greater than or equal to min_length")
        return v

    @field_validator("max_value")
    @classmethod
    def validate_max_value_greater_than_min(cls, v, info):
        """Ensure max_value is greater than min_value if both are set.

        Args:
            v: The max_value.
            info: Field validation info.

        Returns:
            The validated value.

        Raises:
            ValueError: If max_value < min_value.
        """
        data = info.data
        if v is not None and data.get("min_value") is not None and v < data["min_value"]:
            raise ValueError("max_value must be greater than or equal to min_value")
        return v


class ProjectPlantFieldUpdate(BaseModel):
    """Schema for updating a plant custom field.

    All fields are optional for partial updates. Field type cannot be
    changed if the field is locked (has values).

    Attributes:
        field_name: Updated field name.
        is_required: Updated required status.
        display_order: Updated display order.
        min_length: Updated minimum string length.
        max_length: Updated maximum string length.
        regex_pattern: Updated regex pattern.
        min_value: Updated minimum numeric value.
        max_value: Updated maximum numeric value.
    """

    field_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_required: Optional[bool] = None
    display_order: Optional[int] = None

    # Validation rules can be updated
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex_pattern: Optional[str] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None


class ProjectPlantFieldResponse(ProjectPlantFieldBase):
    """Schema for plant custom field response.

    Includes all base fields plus metadata and validation rules.

    Attributes:
        id: Unique identifier for the field.
        project_id: ID of the parent project.
        is_deleted: Whether the field is soft-deleted.
        deleted_at: Timestamp when field was deleted.
        created_at: Timestamp when field was created.
        created_by: User who created the field.
        is_locked: True if field has values and type cannot be changed.
        min_length: Minimum string length constraint.
        max_length: Maximum string length constraint.
        regex_pattern: Regex pattern for string validation.
        min_value: Minimum numeric value constraint.
        max_value: Maximum numeric value constraint.
    """

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
        """Pydantic configuration."""

        from_attributes = True
