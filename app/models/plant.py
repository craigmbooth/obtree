"""Plant model for tracking individual plants within accessions.

This module defines the Plant model which represents individual plants
that belong to accessions. Each plant has a unique identifier and is
associated with both an accession and a species (inherited from the accession).
"""

import uuid as uuid_lib
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID


class Plant(Base):
    """Plant model representing individual plants within an accession.

    A plant represents a single physical plant that belongs to an accession.
    It inherits its species from the parent accession.

    Attributes:
        id: Unique identifier (UUID) for the plant.
        plant_id: User-provided string identifier for the plant.
        accession_id: Foreign key to the parent accession.
        created_at: Timestamp when the plant was created.
        created_by: User who created the plant record.
        accession: Relationship to the parent Accession.
        species: Relationship to the Species (via accession).
        creator: Relationship to the User who created the plant.
    """

    __tablename__ = "plants"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    plant_id = Column(String(255), nullable=False)
    accession_id = Column(
        GUID,
        ForeignKey("accessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    accession = relationship("Accession", back_populates="plants")
    creator = relationship("User")
    field_values = relationship(
        "PlantFieldValue", back_populates="plant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return string representation of the plant."""
        return f"<Plant(id={self.id}, plant_id={self.plant_id})>"
