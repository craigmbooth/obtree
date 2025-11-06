from datetime import datetime
import enum
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class OrganizationRole(str, enum.Enum):
    """Roles within an organization."""
    ADMIN = "admin"
    USER = "user"


class MembershipStatus(str, enum.Enum):
    """Status of an organization membership."""
    ACTIVE = "active"
    REMOVED = "removed"


class OrganizationMembership(Base, TableConfigMixin):
    """Association between users and organizations with roles."""

    __tablename__ = "organization_memberships"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    organization_id = Column(GUID, ForeignKey("organizations.id"), nullable=False)
    role = Column(Enum(OrganizationRole), nullable=False)
    status = Column(Enum(MembershipStatus), nullable=False, default=MembershipStatus.ACTIVE)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="organization_memberships")
    organization = relationship("Organization", back_populates="memberships")

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
                'field': 'user_id',
                'label': 'User ID',
                'visible': False,
                'sortable': True,
                'formatter': 'plaintext'
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
                'width': 120,
                'formatter': 'badge'
            },
            {
                'field': 'status',
                'label': 'Status',
                'visible': True,
                'sortable': True,
                'width': 120,
                'formatter': 'badge'
            },
            {
                'field': 'joined_at',
                'label': 'Joined',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            }
        ],
        'default_sort': {'field': 'joined_at', 'dir': 'desc'}
    }
