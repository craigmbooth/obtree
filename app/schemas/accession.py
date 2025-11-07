from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AccessionBase(BaseModel):
    """Base schema for accession data."""
    accession: str = Field(..., min_length=1, max_length=255, description="Accession identifier")
    description: Optional[str] = Field(None, description="Optional description of the accession")
    species_id: UUID = Field(..., description="ID of the species this accession belongs to")


class AccessionCreate(AccessionBase):
    """Schema for creating a new accession."""
    project_id: Optional[UUID] = Field(None, description="Optional project ID to associate with this accession")


class AccessionUpdate(BaseModel):
    """Schema for updating an accession."""
    accession: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    species_id: Optional[UUID] = None
    project_id: Optional[UUID] = Field(None, description="Optional project ID to associate with this accession")


class AccessionResponse(AccessionBase):
    """Schema for accession response."""
    id: UUID
    created_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True


class AccessionWithSpeciesResponse(AccessionResponse):
    """Schema for accession response with species information."""
    species_genus: str
    species_name: str
    species_variety: Optional[str]
    species_common_name: Optional[str]
    project_id: Optional[UUID] = None
    project_title: Optional[str] = None

    class Config:
        from_attributes = True
