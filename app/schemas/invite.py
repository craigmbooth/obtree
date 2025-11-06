from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from app.models import OrganizationRole


class InviteCreate(BaseModel):
    """Schema for creating a new invite."""
    organization_id: UUID
    role: OrganizationRole


class InviteResponse(BaseModel):
    """Schema for invite response."""
    id: UUID
    uuid: str
    organization_id: UUID
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
    organization_name: str | None = None
    role: str | None = None
    expires_at: datetime | None = None
    message: str | None = None
