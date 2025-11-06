from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class Organization(Base, TableConfigMixin):
    """Organization model for multi-tenancy."""

    __tablename__ = "organizations"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_organizations")
    memberships = relationship("OrganizationMembership", back_populates="organization")
    invites = relationship("Invite", back_populates="organization")

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
                'field': 'name',
                'label': 'Organization Name',
                'visible': True,
                'sortable': True,
                'width': 300,
                'formatter': 'plaintext'
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
                'field': 'created_by',
                'label': 'Creator ID',
                'visible': False,
                'sortable': True,
                'formatter': 'plaintext'
            }
        ],
        'default_sort': {'field': 'name', 'dir': 'asc'}
    }
