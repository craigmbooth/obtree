from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.species import SpeciesStatus


class SpeciesBase(BaseModel):
    """Base species schema."""
    genus: str
    species_name: Optional[str] = None


class SpeciesCreate(SpeciesBase):
    """Schema for creating a new species."""
    subspecies: Optional[str] = None
    variety: Optional[str] = None
    cultivar: Optional[str] = None
    common_name: Optional[str] = None
    description: Optional[str] = None


class SpeciesUpdate(BaseModel):
    """Schema for updating a species."""
    genus: Optional[str] = None
    species_name: Optional[str] = None
    subspecies: Optional[str] = None
    variety: Optional[str] = None
    cultivar: Optional[str] = None
    common_name: Optional[str] = None
    description: Optional[str] = None


class SpeciesResponse(SpeciesBase):
    """Schema for species response."""
    id: UUID
    subspecies: Optional[str] = None
    variety: Optional[str] = None
    cultivar: Optional[str] = None
    common_name: Optional[str] = None
    description: Optional[str] = None
    organization_id: UUID
    status: SpeciesStatus
    created_at: datetime
    created_by: UUID
    formatted_name: str

    class Config:
        from_attributes = True
