from datetime import datetime
import uuid as uuid_lib
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text
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
    """Accession model - accessions belong to species and can be associated with projects.

    Accessions can be hybrids, in which case they have two parent species instead of
    a single species.
    """

    __tablename__ = "accessions"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    accession = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    species_id = Column(GUID, ForeignKey("species.id"), nullable=True)  # Nullable for hybrids
    location_id = Column(GUID, ForeignKey("locations.id"), nullable=True)
    is_hybrid = Column(Boolean, default=False, nullable=False)
    parent_species_1_id = Column(GUID, ForeignKey("species.id"), nullable=True)
    parent_species_2_id = Column(GUID, ForeignKey("species.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    species = relationship("Species", back_populates="accessions", foreign_keys=[species_id])
    parent_species_1 = relationship("Species", foreign_keys=[parent_species_1_id])
    parent_species_2 = relationship("Species", foreign_keys=[parent_species_2_id])
    creator = relationship("User")
    location = relationship("Location", back_populates="accessions")
    projects = relationship("Project", secondary=projects_accessions, back_populates="accessions")
    field_values = relationship("AccessionFieldValue", back_populates="accession", cascade="all, delete-orphan")
    plants = relationship("Plant", back_populates="accession", cascade="all, delete-orphan")

    @property
    def hybrid_display_name(self) -> str:
        """Generate hybrid display name in the format 'Parent1 x Parent2'.

        Returns:
            str: Formatted hybrid name if this is a hybrid, empty string otherwise
        """
        if not self.is_hybrid or not self.parent_species_1 or not self.parent_species_2:
            return ""

        parent1_name = self.parent_species_1.formatted_name
        parent2_name = self.parent_species_2.formatted_name

        return f"{parent1_name} x {parent2_name}"

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
