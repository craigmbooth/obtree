from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.models import OrganizationRole


class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""
    description: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: Optional[str] = None
    description: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""
    id: UUID
    description: Optional[str] = None
    created_at: datetime
    created_by: UUID

    class Config:
        from_attributes = True


class OrganizationMembershipBase(BaseModel):
    """Base membership schema."""
    role: OrganizationRole


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member response."""
    id: UUID
    user_id: UUID
    email: str
    role: OrganizationRole
    joined_at: datetime

    class Config:
        from_attributes = True


class OrganizationDetailResponse(OrganizationResponse):
    """Schema for detailed organization response with members."""
    members: List[OrganizationMemberResponse] = []

    class Config:
        from_attributes = True
