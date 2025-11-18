from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class PlantEvent(Base, TableConfigMixin):
    """Plant event model - records events that occur on plants.

    Events have a type (EventType) which defines what fields to track,
    an event date (when it occurred), and optional notes.
    """

    __tablename__ = "plant_events"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    plant_id = Column(GUID, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type_id = Column(GUID, ForeignKey("event_types.id"), nullable=False, index=True)
    event_date = Column(DateTime, nullable=False)  # When the event occurred (can be backdated)
    notes = Column(Text, nullable=True)  # Optional free-form notes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    plant = relationship("Plant", back_populates="events")
    event_type = relationship("EventType", back_populates="events")
    creator = relationship("User")
    field_values = relationship("EventFieldValue", back_populates="event", cascade="all, delete-orphan")

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
                'field': 'event_date',
                'label': 'Date',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            },
            {
                'field': 'event_type_name',
                'label': 'Event Type',
                'visible': True,
                'sortable': True,
                'width': 200,
                'formatter': 'plaintext'
            },
            {
                'field': 'notes',
                'label': 'Notes',
                'visible': True,
                'sortable': False,
                'width': 300,
                'formatter': 'plaintext'
            },
            {
                'field': 'created_at',
                'label': 'Recorded',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            }
        ],
        'default_sort': {'field': 'event_date', 'dir': 'desc'}
    }
