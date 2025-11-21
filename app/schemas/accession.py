from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.accession_field_value import AccessionFieldValueCreate, AccessionFieldValueResponse


class AccessionBase(BaseModel):
    """Base schema for accession data."""
    accession: str = Field(..., min_length=1, max_length=255, description="Accession identifier")
    description: Optional[str] = Field(None, description="Optional description of the accession")
    species_id: Optional[UUID] = Field(None, description="ID of the species (not required for hybrids)")


class AccessionCreate(AccessionBase):
    """Schema for creating a new accession."""
    project_id: Optional[UUID] = Field(None, description="Optional project ID to associate with this accession")
    is_hybrid: bool = Field(False, description="Whether this accession is a hybrid")
    parent_species_1_id: Optional[UUID] = Field(None, description="First parent species ID (required for hybrids)")
    parent_species_2_id: Optional[UUID] = Field(None, description="Second parent species ID (required for hybrids)")
    field_values: Optional[List[AccessionFieldValueCreate]] = Field(default_factory=list, description="Custom field values for this accession")


class AccessionUpdate(BaseModel):
    """Schema for updating an accession."""
    accession: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    species_id: Optional[UUID] = None
    is_hybrid: Optional[bool] = None
    parent_species_1_id: Optional[UUID] = None
    parent_species_2_id: Optional[UUID] = None
    project_id: Optional[UUID] = Field(None, description="Optional project ID to associate with this accession")
    field_values: Optional[List[AccessionFieldValueCreate]] = Field(None, description="Custom field values for this accession")


class AccessionResponse(AccessionBase):
    """Schema for accession response."""
    id: UUID
    is_hybrid: bool
    parent_species_1_id: Optional[UUID] = None
    parent_species_2_id: Optional[UUID] = None
    hybrid_display_name: str = ""
    created_at: datetime
    created_by: UUID
    field_values: List[AccessionFieldValueResponse] = Field(default_factory=list, description="Custom field values for this accession")

    class Config:
        from_attributes = True


class AccessionWithSpeciesResponse(AccessionResponse):
    """Schema for accession response with species information."""
    species_genus: Optional[str] = None
    species_name: Optional[str] = None
    species_variety: Optional[str] = None
    species_common_name: Optional[str] = None
    parent_species_1_name: Optional[str] = None
    parent_species_2_name: Optional[str] = None
    project_id: Optional[UUID] = None
    project_title: Optional[str] = None
    plant_count: int = Field(0, description="Number of plants in this accession")

    class Config:
        from_attributes = True
