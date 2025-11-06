from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class User(Base, TableConfigMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_site_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization_memberships = relationship("OrganizationMembership", back_populates="user")
    created_organizations = relationship("Organization", back_populates="creator")
    created_invites = relationship("Invite", foreign_keys="Invite.created_by", back_populates="creator")
    used_invites = relationship("Invite", foreign_keys="Invite.used_by", back_populates="user")

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
                'field': 'email',
                'label': 'Email',
                'visible': True,
                'sortable': True,
                'width': 250,
                'formatter': 'email'
            },
            {
                'field': 'is_site_admin',
                'label': 'Site Admin',
                'visible': True,
                'sortable': True,
                'width': 120,
                'formatter': 'boolean'
            },
            {
                'field': 'created_at',
                'label': 'Created',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            },
            {
                'field': 'updated_at',
                'label': 'Last Updated',
                'visible': False,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            }
        ],
        'default_sort': {'field': 'created_at', 'dir': 'desc'}
    }
