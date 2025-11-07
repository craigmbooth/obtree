from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import can_manage_organization
from app.core.field_validation import get_project_fields, is_field_locked
from app.logging_config import get_logger
from app.models import User, Project, ProjectAccessionField
from app.schemas.project_accession_field import (
    ProjectAccessionFieldCreate,
    ProjectAccessionFieldUpdate,
    ProjectAccessionFieldResponse
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[ProjectAccessionFieldResponse])
def list_project_fields(
    organization_id: UUID,
    project_id: UUID,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all custom fields for a project (all org members can view)."""
    logger.info(
        "project_fields_list_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Verify project exists and belongs to organization
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or str(project.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization"
        )

    # Get fields
    fields = get_project_fields(db, project_id, include_deleted=include_deleted)

    # Build response list with is_locked flag for each field
    result = []
    for field in fields:
        field_dict = {
            'id': field.id,
            'project_id': field.project_id,
            'field_name': field.field_name,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'display_order': field.display_order,
            'min_length': field.min_length,
            'max_length': field.max_length,
            'regex_pattern': field.regex_pattern,
            'min_value': field.min_value,
            'max_value': field.max_value,
            'is_deleted': field.is_deleted,
            'deleted_at': field.deleted_at,
            'created_at': field.created_at,
            'created_by': field.created_by,
            'is_locked': is_field_locked(db, field.id)
        }
        result.append(ProjectAccessionFieldResponse(**field_dict))

    logger.info(
        "project_fields_list_success",
        organization_id=organization_id,
        project_id=project_id,
        count=len(result)
    )

    return result


@router.post("", response_model=ProjectAccessionFieldResponse, status_code=status.HTTP_201_CREATED)
def create_project_field(
    organization_id: UUID,
    project_id: UUID,
    field_data: ProjectAccessionFieldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new custom field for a project (admin only)."""
    logger.info(
        "project_field_create_started",
        organization_id=organization_id,
        project_id=project_id,
        field_name=field_data.field_name,
        created_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "project_field_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create fields in this organization"
        )

    # Verify project exists and belongs to organization
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or str(project.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization"
        )

    # Check for duplicate field name (excluding deleted fields)
    existing_field = db.query(ProjectAccessionField).filter(
        ProjectAccessionField.project_id == project_id,
        ProjectAccessionField.field_name == field_data.field_name,
        ProjectAccessionField.is_deleted == False
    ).first()

    if existing_field:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{field_data.field_name}' already exists in this project"
        )

    # Create new field
    new_field = ProjectAccessionField(
        project_id=project_id,
        field_name=field_data.field_name,
        field_type=field_data.field_type,
        is_required=field_data.is_required,
        display_order=field_data.display_order,
        min_length=field_data.min_length,
        max_length=field_data.max_length,
        regex_pattern=field_data.regex_pattern,
        min_value=field_data.min_value,
        max_value=field_data.max_value,
        created_by=current_user.id
    )

    db.add(new_field)
    db.commit()
    db.refresh(new_field)

    logger.info(
        "project_field_create_success",
        field_id=new_field.id,
        organization_id=organization_id,
        project_id=project_id
    )

    # Build response with is_locked flag
    response_dict = {
        'id': new_field.id,
        'project_id': new_field.project_id,
        'field_name': new_field.field_name,
        'field_type': new_field.field_type,
        'is_required': new_field.is_required,
        'display_order': new_field.display_order,
        'min_length': new_field.min_length,
        'max_length': new_field.max_length,
        'regex_pattern': new_field.regex_pattern,
        'min_value': new_field.min_value,
        'max_value': new_field.max_value,
        'is_deleted': new_field.is_deleted,
        'deleted_at': new_field.deleted_at,
        'created_at': new_field.created_at,
        'created_by': new_field.created_by,
        'is_locked': False  # New field has no values
    }
    return ProjectAccessionFieldResponse(**response_dict)


@router.patch("/{field_id}", response_model=ProjectAccessionFieldResponse)
def update_project_field(
    organization_id: UUID,
    project_id: UUID,
    field_id: UUID,
    field_update: ProjectAccessionFieldUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a custom field (admin only). Type cannot be changed if field is locked."""
    logger.info(
        "project_field_update_started",
        organization_id=organization_id,
        project_id=project_id,
        field_id=field_id,
        updated_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "project_field_update_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update fields in this organization"
        )

    # Get the field
    field = db.query(ProjectAccessionField).filter(
        ProjectAccessionField.id == field_id
    ).first()

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )

    # Verify field belongs to this project
    if str(field.project_id) != str(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field does not belong to this project"
        )

    # Verify project belongs to organization
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or str(project.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization"
        )

    # Check if field name is being changed and if new name conflicts
    if field_update.field_name and field_update.field_name != field.field_name:
        existing_field = db.query(ProjectAccessionField).filter(
            ProjectAccessionField.project_id == project_id,
            ProjectAccessionField.field_name == field_update.field_name,
            ProjectAccessionField.is_deleted == False,
            ProjectAccessionField.id != field_id
        ).first()

        if existing_field:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field_update.field_name}' already exists in this project"
            )

    # Update fields
    update_data = field_update.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(field, field_name, value)

    db.commit()
    db.refresh(field)

    logger.info("project_field_update_success", field_id=field_id)

    # Build response with is_locked flag
    response_dict = {
        'id': field.id,
        'project_id': field.project_id,
        'field_name': field.field_name,
        'field_type': field.field_type,
        'is_required': field.is_required,
        'display_order': field.display_order,
        'min_length': field.min_length,
        'max_length': field.max_length,
        'regex_pattern': field.regex_pattern,
        'min_value': field.min_value,
        'max_value': field.max_value,
        'is_deleted': field.is_deleted,
        'deleted_at': field.deleted_at,
        'created_at': field.created_at,
        'created_by': field.created_by,
        'is_locked': is_field_locked(db, field.id)
    }
    return ProjectAccessionFieldResponse(**response_dict)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_field(
    organization_id: UUID,
    project_id: UUID,
    field_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a custom field (admin only). Values are preserved."""
    logger.info(
        "project_field_delete_started",
        organization_id=organization_id,
        project_id=project_id,
        field_id=field_id,
        deleted_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "project_field_delete_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete fields in this organization"
        )

    # Get the field
    field = db.query(ProjectAccessionField).filter(
        ProjectAccessionField.id == field_id
    ).first()

    if not field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )

    # Verify field belongs to this project
    if str(field.project_id) != str(project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field does not belong to this project"
        )

    # Verify project belongs to organization
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or str(project.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization"
        )

    # Soft delete the field
    field.is_deleted = True
    field.deleted_at = datetime.utcnow()

    db.commit()

    logger.info("project_field_delete_success", field_id=field_id)

    return None
