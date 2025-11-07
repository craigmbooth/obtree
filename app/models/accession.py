from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID
from app.models.mixins import TableConfigMixin


# Association table for many-to-many relationship between projects and accessions
projects_accessions = Table(
    'projects_accessions',
    Base.metadata,
    Column('project_id', GUID, ForeignKey('projects.id'), primary_key=True),
    Column('accession_id', GUID, ForeignKey('accessions.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
)


class Accession(Base, TableConfigMixin):
    """Accession model - accessions belong to species and can be associated with projects."""

    __tablename__ = "accessions"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    accession = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    species_id = Column(GUID, ForeignKey("species.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    species = relationship("Species", back_populates="accessions")
    creator = relationship("User")
    projects = relationship("Project", secondary=projects_accessions, back_populates="accessions")

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
                'field': 'accession',
                'label': 'Accession',
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
        'default_sort': {'field': 'accession', 'dir': 'asc'}
    }
