from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    """Base project schema."""
    title: str


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: UUID
    description: Optional[str] = None
    organization_id: UUID
    status: ProjectStatus
    created_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True
