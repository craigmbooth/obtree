from datetime import datetime
import enum
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, String, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class ProjectStatus(str, enum.Enum):
    """Status of a project."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Project(Base, TableConfigMixin):
    """Project model - projects belong to organizations."""

    __tablename__ = "projects"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(GUID, ForeignKey("organizations.id"), nullable=False)
    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    creator = relationship("User")

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
                'field': 'title',
                'label': 'Project Title',
                'visible': True,
                'sortable': True,
                'width': 300,
                'formatter': 'plaintext'
            },
            {
                'field': 'description',
                'label': 'Description',
                'visible': True,
                'sortable': False,
                'width': 400,
                'formatter': 'plaintext'
            },
            {
                'field': 'created_at',
                'label': 'Created',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            }
        ],
        'default_sort': {'field': 'created_at', 'dir': 'desc'}
    }
