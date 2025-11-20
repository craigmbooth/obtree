from datetime import datetime, timedelta
import enum
import uuid as uuid_lib
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.config import settings
from app.models.mixins import TableConfigMixin


class InviteType(str, enum.Enum):
    """Type of invitation."""
    ORGANIZATION = "ORGANIZATION"
    SITE_ADMIN = "SITE_ADMIN"


class Invite(Base, TableConfigMixin):
    """Invitation model for organization membership or site admin access."""

    __tablename__ = "invites"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    uuid = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    invite_type = Column(Enum(InviteType), nullable=False, default=InviteType.ORGANIZATION)
    organization_id = Column(GUID, ForeignKey("organizations.id"), nullable=True)
    role = Column(String, nullable=False)  # Will store OrganizationRole enum value or 'SITE_ADMIN'
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=settings.INVITE_EXPIRATION_DAYS),
        nullable=False
    )
    used_by = Column(GUID, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="invites")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_invites")
    user = relationship("User", foreign_keys=[used_by], back_populates="used_invites")

    @property
    def is_valid(self) -> bool:
        """Check if invite is still valid."""
        return (
            self.is_active
            and self.used_by is None
            and self.expires_at > datetime.utcnow()
        )

    # Table configuration for frontend display
    __table_config__ = {
        'columns': [
            {
                'field': 'id',
                'label': 'ID',
                'visible': False,
                'sortable': True,
                'formatter': 'plaintext'
            },
            {
                'field': 'uuid',
                'label': 'Invite Code',
                'visible': True,
                'sortable': False,
                'width': 280,
                'formatter': 'plaintext'
            },
            {
                'field': 'invite_type',
                'label': 'Type',
                'visible': True,
                'sortable': True,
                'width': 120,
                'formatter': 'badge'
            },
            {
                'field': 'organization_id',
                'label': 'Organization ID',
                'visible': False,
                'sortable': True,
                'formatter': 'plaintext'
            },
            {
                'field': 'role',
                'label': 'Role',
                'visible': True,
                'sortable': True,
                'width': 100,
                'formatter': 'badge'
            },
            {
                'field': 'expires_at',
                'label': 'Expires',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            },
            {
                'field': 'is_active',
                'label': 'Active',
                'visible': True,
                'sortable': True,
                'width': 100,
                'formatter': 'boolean'
            },
            {
                'field': 'used_at',
                'label': 'Used At',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            },
            {
                'field': 'created_at',
                'label': 'Created',
                'visible': False,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            }
        ],
        'default_sort': {'field': 'created_at', 'dir': 'desc'}
    }
