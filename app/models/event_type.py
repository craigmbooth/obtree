from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, String, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class EventType(Base, TableConfigMixin):
    """Event type model - defines event types at org or project level.

    Event types can be scoped to either:    - Organization level (project_id is NULL) - available to all plants in the org
    - Project level (project_id is set) - available only to plants in that project
    """

    __tablename__ = "event_types"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    event_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(GUID, ForeignKey("organizations.id"), nullable=False)
    project_id = Column(GUID, ForeignKey("projects.id"), nullable=True)  # NULL = org-level, set = project-level
    display_order = Column(Integer, default=0, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="event_types")
    project = relationship("Project", back_populates="event_types")
    creator = relationship("User")
    fields = relationship("EventTypeField", back_populates="event_type", cascade="all, delete-orphan")
    events = relationship("PlantEvent", back_populates="event_type")

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
                'field': 'event_name',
                'label': 'Event Type',
                'visible': True,
                'sortable': True,
                'width': 200,
                'formatter': 'plaintext'
            },
            {
                'field': 'description',
                'label': 'Description',
                'visible': True,
                'sortable': False,
                'width': 300,
                'formatter': 'plaintext'
            },
            {
                'field': 'display_order',
                'label': 'Order',
                'visible': True,
                'sortable': True,
                'width': 100,
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
        'default_sort': {'field': 'display_order', 'dir': 'asc'}
    }
