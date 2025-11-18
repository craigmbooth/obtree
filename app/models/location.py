from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, ForeignKey, Text, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class Location(Base, TableConfigMixin):
    """Location model - represents a specific location instance.

    Locations have a type (LocationType) which defines what fields to track.
    They can be assigned to plants or accessions.
    """

    __tablename__ = "locations"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    organization_id = Column(GUID, ForeignKey("organizations.id"), nullable=False, index=True)
    location_type_id = Column(GUID, ForeignKey("location_types.id"), nullable=False, index=True)
    location_name = Column(String(255), nullable=False)  # User-friendly name for this specific location
    notes = Column(Text, nullable=True)  # Optional free-form notes
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="locations")
    location_type = relationship("LocationType", back_populates="locations")
    creator = relationship("User")
    field_values = relationship("LocationFieldValue", back_populates="location", cascade="all, delete-orphan")
    plants = relationship("Plant", back_populates="location")
    accessions = relationship("Accession", back_populates="location")

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
                'field': 'location_name',
                'label': 'Location Name',
                'visible': True,
                'sortable': True,
                'width': 200,
                'formatter': 'plaintext'
            },
            {
                'field': 'location_type_name',
                'label': 'Type',
                'visible': True,
                'sortable': True,
                'width': 150,
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
                'label': 'Created',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            }
        ],
        'default_sort': {'field': 'location_name', 'dir': 'asc'}
    }
