"""Plant schemas for API request/response validation.

This module defines the Pydantic schemas used for validating and serializing
plant data in API requests and responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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

    Inherits all fields from PlantBase.
    """

    pass


class PlantUpdate(BaseModel):
    """Schema for updating a plant.

    All fields are optional for partial updates.

    Attributes:
        plant_id: Updated plant identifier.
        accession_id: Updated accession ID.
    """

    plant_id: Optional[str] = Field(None, min_length=1, max_length=255)
    accession_id: Optional[UUID] = None


class PlantResponse(PlantBase):
    """Schema for plant response.

    Includes all base fields plus metadata.

    Attributes:
        id: Unique identifier for the plant.
        created_at: Timestamp when the plant was created.
        created_by: User who created the plant.
    """

    id: UUID
    created_at: datetime
    created_by: UUID

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class PlantWithDetailsResponse(PlantResponse):
    """Schema for plant response with full details.

    Includes plant data plus species and accession information
    for the plant detail page.

    Attributes:
        accession: Accession identifier string.
        species_genus: Genus of the plant's species.
        species_name: Species name.
        species_variety: Optional variety name.
        species_common_name: Optional common name.
    """

    accession: str
    species_genus: str
    species_name: str
    species_variety: Optional[str]
    species_common_name: Optional[str]

    class Config:
        """Pydantic configuration."""

        from_attributes = True
