"""Plant schemas for API request/response validation.

This module defines the Pydantic schemas used for validating and serializing
plant data in API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.plant_field_value import PlantFieldValueCreate, PlantFieldValueResponse
from app.schemas.location import LocationResponse


class PlantBase(BaseModel):
    """Base schema for plant data.

    Attributes:
        plant_id: User-provided string identifier for the plant.
        accession_id: UUID of the parent accession.
    """

    plant_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User-provided plant identifier",
    )
    accession_id: UUID = Field(
        ..., description="ID of the accession this plant belongs to"
    )


class PlantCreate(PlantBase):
    """Schema for creating a new plant.

    Includes optional field values for project custom fields and location.

    Attributes:
        location_id: Optional UUID of the location for this plant.
        field_values: List of custom field values.
    """

    location_id: Optional[UUID] = Field(
        None, description="Optional location ID for this plant"
    )
    field_values: Optional[List[PlantFieldValueCreate]] = Field(
        default_factory=list, description="Custom field values for this plant"
    )


class PlantUpdate(BaseModel):
    """Schema for updating a plant.

    All fields are optional for partial updates.

    Attributes:
        plant_id: Updated plant identifier.
        accession_id: Updated accession ID.
        location_id: Updated location ID (can be None to clear location).
        field_values: Updated custom field values.
    """

    plant_id: Optional[str] = Field(None, min_length=1, max_length=255)
    accession_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    field_values: Optional[List[PlantFieldValueCreate]] = Field(
        None, description="Custom field values for this plant"
    )


class PlantResponse(PlantBase):
    """Schema for plant response.

    Includes all base fields plus metadata and field values.

    Attributes:
        id: Unique identifier for the plant.
        created_at: Timestamp when the plant was created.
        created_by: User who created the plant.
        field_values: List of custom field values.
    """

    id: UUID
    created_at: datetime
    created_by: UUID
    field_values: List[PlantFieldValueResponse] = Field(
        default_factory=list, description="Custom field values for this plant"
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class PlantWithDetailsResponse(PlantResponse):
    """Schema for plant response with full details.

    Includes plant data plus species and accession information
    for the plant detail page.

    Attributes:
        accession: Accession identifier string.
        species_id: UUID of the species.
        species_genus: Genus of the plant's species.
        species_name: Species name.
        species_variety: Optional variety name.
        species_common_name: Optional common name.
        project_id: Optional project ID (inherited from accession).
        project_title: Optional project title.
        location: Optional location data.
    """

    accession: str
    species_id: UUID
    species_genus: str
    species_name: str
    species_variety: Optional[str]
    species_common_name: Optional[str]
    project_id: Optional[UUID] = None
    project_title: Optional[str] = None
    location: Optional[LocationResponse] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True
