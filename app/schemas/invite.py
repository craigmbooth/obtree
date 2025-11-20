from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator

from app.models import OrganizationRole, InviteType


class InviteCreate(BaseModel):
    """Schema for creating a new organization invite."""
    organization_id: UUID
    role: OrganizationRole


class SiteAdminInviteCreate(BaseModel):
    """Schema for creating a new site admin invite."""
    # No fields needed - site admin invites don't have an organization or role
    pass


class InviteResponse(BaseModel):
    """Schema for invite response."""
    id: UUID
    uuid: str
    invite_type: str
    organization_id: UUID | None
    role: str
    created_by: UUID
    created_at: datetime
    expires_at: datetime
    is_active: bool
    used_by: UUID | None = None
    used_at: datetime | None = None

    class Config:
        from_attributes = True


class InviteValidateResponse(BaseModel):
    """Schema for invite validation response."""
    valid: bool
    invite_type: str | None = None
    organization_name: str | None = None
    role: str | None = None
    expires_at: datetime | None = None
    message: str | None = None
