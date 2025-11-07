from datetime import datetime
import enum
import uuid as uuid_lib
from sqlalchemy import Column, DateTime, String, ForeignKey, Text, Boolean, Integer, Enum, CheckConstraint, Numeric
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.types import GUID


class FieldType(str, enum.Enum):
    """Type of custom field."""
    STRING = "string"
    NUMBER = "number"


class ProjectAccessionField(Base):
    """Custom field definition for project accessions."""

    __tablename__ = "project_accession_fields"

    id = Column(GUID, primary_key=True, default=uuid_lib.uuid4, index=True)
    project_id = Column(GUID, ForeignKey("projects.id"), nullable=False, index=True)
    field_name = Column(String(255), nullable=False)
    field_type = Column(Enum(FieldType), nullable=False)
    is_required = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)

    # Validation rules for string fields
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    regex_pattern = Column(Text, nullable=True)

    # Validation rules for number fields
    min_value = Column(Numeric, nullable=True)
    max_value = Column(Numeric, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(GUID, ForeignKey("users.id"), nullable=False)

    # Relationships
    project = relationship("Project", backref="custom_fields")
    creator = relationship("User")
    field_values = relationship("AccessionFieldValue", back_populates="field", cascade="all, delete-orphan")

    __table_args__ = (
        # Ensure field names are unique within a project (excluding deleted fields)
        CheckConstraint(
            "is_deleted = false OR (is_deleted = true)",
            name="check_unique_field_name_per_project"
        ),
    )
