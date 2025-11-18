from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, String, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class LocationType(Base, TableConfigMixin):
    """Location type model - defines location schemas at org level.

    Location types are scoped to organizations and define the structure
    of location data (e.g., nursery blocks, greenhouse sections, etc).
    """

    __tablename__ = "location_types"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    location_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    organization_id = Column(GUID, ForeignKey("organizations.id"), nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="location_types")
    creator = relationship("User")
    fields = relationship("LocationTypeField", back_populates="location_type", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="location_type")

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
                'label': 'Location Type',
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
