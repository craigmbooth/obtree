"""Project plant field model for custom field definitions on plants.

This module defines the ProjectPlantField model which stores custom field
definitions (schema/template) for plants within a project. Works identically
to ProjectAccessionField but applies to plants instead of accessions.
"""

from datetime import datetime
import uuid as uuid_lib

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.project_accession_field import FieldType
from app.models.types import GUID


class ProjectPlantField(Base):
    """Custom field definition for project plants.

    Defines the schema/template for custom fields that can be added to plants
    within a project. Each field has a type (STRING or NUMBER) with optional
    validation rules. Fields can be marked as required.

    Attributes:
        id: Unique identifier (UUID) for the field.
        project_id: Foreign key to the parent project.
        field_name: Name of the custom field.
        field_type: Type of field (STRING or NUMBER).
        is_required: Whether this field is required for plants in the project.
        display_order: Order in which to display fields in UI.
        min_length: Minimum length for string fields.
        max_length: Maximum length for string fields.
        regex_pattern: Regex pattern for string validation.
        min_value: Minimum value for number fields.
        max_value: Maximum value for number fields.
        is_deleted: Soft delete flag.
        deleted_at: Timestamp when field was deleted.
        created_at: Timestamp when field was created.
        created_by: User who created the field.
        project: Relationship to the Project.
        creator: Relationship to the User who created the field.
        field_values: Relationship to PlantFieldValue records.
    """

    __tablename__ = "project_plant_fields"

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
    project = relationship("Project", backref="plant_custom_fields")
    creator = relationship("User")
    field_values = relationship(
        "PlantFieldValue", back_populates="field", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Ensure field names are unique within a project (excluding deleted fields)
        CheckConstraint(
            "is_deleted = false OR (is_deleted = true)",
            name="check_unique_plant_field_name_per_project",
        ),
    )

    def __repr__(self) -> str:
        """Return string representation of the field."""
        return f"<ProjectPlantField(id={self.id}, name={self.field_name}, type={self.field_type})>"
