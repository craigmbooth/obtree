from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.species import SpeciesStatus


class SpeciesBase(BaseModel):
    """Base species schema."""
    genus: str
    species_name: str


class SpeciesCreate(SpeciesBase):
    """Schema for creating a new species."""
    variety: Optional[str] = None
    common_name: Optional[str] = None
    description: Optional[str] = None


class SpeciesUpdate(BaseModel):
    """Schema for updating a species."""
    genus: Optional[str] = None
    species_name: Optional[str] = None
    variety: Optional[str] = None
    common_name: Optional[str] = None
    description: Optional[str] = None


class SpeciesResponse(SpeciesBase):
    """Schema for species response."""
    id: UUID
    variety: Optional[str] = None
    common_name: Optional[str] = None
    description: Optional[str] = None
    organization_id: UUID
    status: SpeciesStatus
    created_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True
