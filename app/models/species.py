from datetime import datetime
import enum
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, String, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


class SpeciesStatus(str, enum.Enum):
    """Status of a species."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Species(Base, TableConfigMixin):
    """Species model - species belong to organizations."""

    __tablename__ = "species"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    genus = Column(String, nullable=False)
    species_name = Column(String, nullable=False)
    variety = Column(String, nullable=True)
    common_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    organization_id = Column(GUID, ForeignKey("organizations.id"), nullable=False)
    status = Column(Enum(SpeciesStatus), nullable=False, default=SpeciesStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="species")
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
                'field': 'genus',
                'label': 'Genus',
                'visible': True,
                'sortable': True,
                'width': 150,
                'formatter': 'plaintext'
            },
            {
                'field': 'species_name',
                'label': 'Species',
                'visible': True,
                'sortable': True,
                'width': 150,
                'formatter': 'plaintext'
            },
            {
                'field': 'variety',
                'label': 'Variety',
                'visible': True,
                'sortable': True,
                'width': 150,
                'formatter': 'plaintext'
            },
            {
                'field': 'common_name',
                'label': 'Common Name',
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
                'field': 'created_at',
                'label': 'Created',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            }
        ],
        'default_sort': {'field': 'genus', 'dir': 'asc'}
    }
