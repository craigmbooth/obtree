import re
from decimal import Decimal
from typing import List, Dict, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.project_accession_field import ProjectAccessionField, FieldType
from app.logging_config import get_logger

logger = get_logger(__name__)


# Generic field validation (works for both accession and plant fields)


def validate_field_value(field: Union[ProjectAccessionField, Any], value: Union[str, Decimal]) -> None:
    """
    Validate a field value against the field's validation rules.

    Works for both ProjectAccessionField and ProjectPlantField since they
    have the same structure.

    Args:
        field: The field with validation rules (ProjectAccessionField or ProjectPlantField)
        value: The value to validate

    Raises:
        HTTPException: If validation fails
    """
    if field.field_type == FieldType.STRING:
        if not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field.field_name}' must be a string"
            )

        # Check min_length
        if field.min_length is not None and len(value) < field.min_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field.field_name}' must be at least {field.min_length} characters"
            )

        # Check max_length
        if field.max_length is not None and len(value) > field.max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field.field_name}' must be at most {field.max_length} characters"
            )

        # Check regex_pattern
        if field.regex_pattern:
            try:
                if not re.match(field.regex_pattern, value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field '{field.field_name}' does not match required pattern"
                    )
            except re.error as e:
                logger.error(f"Invalid regex pattern for field {field.id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid field validation pattern"
                )

    elif field.field_type == FieldType.NUMBER:
        if not isinstance(value, (int, float, Decimal)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field.field_name}' must be a number"
            )

        value_decimal = Decimal(str(value))

        # Check min_value
        if field.min_value is not None and value_decimal < field.min_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field.field_name}' must be at least {field.min_value}"
            )

        # Check max_value
        if field.max_value is not None and value_decimal > field.max_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field.field_name}' must be at most {field.max_value}"
            )


def validate_required_fields(
    db: Session,
    project_id: UUID,
    field_values: List[Dict[str, Any]]
) -> None:
    """
    Validate that all required fields are present in the field_values.

    Args:
        db: Database session
        project_id: ID of the project
        field_values: List of field value dicts with field_id and value

    Raises:
        HTTPException: If required fields are missing
    """
    # Get all required fields for this project
    required_fields = db.query(ProjectAccessionField).filter(
        ProjectAccessionField.project_id == project_id,
        ProjectAccessionField.is_required == True,
        ProjectAccessionField.is_deleted == False
    ).all()

    # Get set of provided field IDs
    provided_field_ids = {str(fv['field_id']) for fv in field_values if fv.get('field_id')}

    # Check for missing required fields
    missing_fields = []
    for field in required_fields:
        if str(field.id) not in provided_field_ids:
            missing_fields.append(field.field_name)

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )


def get_project_fields(db: Session, project_id: UUID, include_deleted: bool = False) -> List[ProjectAccessionField]:
    """
    Get all custom fields for a project.

    Args:
        db: Database session
        project_id: ID of the project
        include_deleted: Whether to include soft-deleted fields

    Returns:
        List of ProjectAccessionField objects
    """
    query = db.query(ProjectAccessionField).filter(
        ProjectAccessionField.project_id == project_id
    )

    if not include_deleted:
        query = query.filter(ProjectAccessionField.is_deleted == False)

    return query.order_by(ProjectAccessionField.display_order, ProjectAccessionField.field_name).all()


def is_field_locked(db: Session, field_id: UUID) -> bool:
    """
    Check if a field is locked (has values) and cannot have its type changed.

    Args:
        db: Database session
        field_id: ID of the field

    Returns:
        True if field has any values, False otherwise
    """
    from app.models.accession_field_value import AccessionFieldValue

    count = db.query(AccessionFieldValue).filter(
        AccessionFieldValue.field_id == field_id
    ).count()

    return count > 0


# Plant field validation functions


def validate_plant_required_fields(
    db: Session,
    project_id: UUID,
    field_values: List[Dict[str, Any]]
) -> None:
    """
    Validate that all required plant fields are present in the field_values.

    Args:
        db: Database session
        project_id: ID of the project
        field_values: List of field value dicts with field_id and value

    Raises:
        HTTPException: If required fields are missing
    """
    from app.models.project_plant_field import ProjectPlantField

    # Get all required fields for this project
    required_fields = db.query(ProjectPlantField).filter(
        ProjectPlantField.project_id == project_id,
        ProjectPlantField.is_required == True,
        ProjectPlantField.is_deleted == False
    ).all()

    # Get set of provided field IDs
    provided_field_ids = {str(fv['field_id']) for fv in field_values if fv.get('field_id')}

    # Check for missing required fields
    missing_fields = []
    for field in required_fields:
        if str(field.id) not in provided_field_ids:
            missing_fields.append(field.field_name)

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required plant fields: {', '.join(missing_fields)}"
        )


def get_project_plant_fields(db: Session, project_id: UUID, include_deleted: bool = False):
    """
    Get all custom plant fields for a project.

    Args:
        db: Database session
        project_id: ID of the project
        include_deleted: Whether to include soft-deleted fields

    Returns:
        List of ProjectPlantField objects
    """
    from app.models.project_plant_field import ProjectPlantField

    query = db.query(ProjectPlantField).filter(
        ProjectPlantField.project_id == project_id
    )

    if not include_deleted:
        query = query.filter(ProjectPlantField.is_deleted == False)

    return query.order_by(ProjectPlantField.display_order, ProjectPlantField.field_name).all()


def is_plant_field_locked(db: Session, field_id: UUID) -> bool:
    """
    Check if a plant field is locked (has values) and cannot have its type changed.

    Args:
        db: Database session
        field_id: ID of the field

    Returns:
        True if field has any values, False otherwise
    """
    from app.models.plant_field_value import PlantFieldValue

    count = db.query(PlantFieldValue).filter(
        PlantFieldValue.field_id == field_id
    ).count()

    return count > 0
