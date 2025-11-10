"""API routes for managing custom plant fields within projects.

This module provides CRUD endpoints for ProjectPlantField definitions,
allowing admins to create, read, update, and delete custom field schemas
for plants within a project.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.field_validation import get_project_plant_fields, is_plant_field_locked
from app.core.permissions import can_manage_organization, is_org_member
from app.logging_config import get_logger
from app.models import Project, ProjectPlantField, User
from app.schemas.project_plant_field import (
    ProjectPlantFieldCreate,
    ProjectPlantFieldResponse,
    ProjectPlantFieldUpdate,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[ProjectPlantFieldResponse])
def list_project_plant_fields(
    organization_id: UUID,
    project_id: UUID,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all custom plant fields for a project (all org members can view).

    Args:
        organization_id: Organization UUID.
        project_id: Project UUID.
        include_deleted: Whether to include soft-deleted fields.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List[ProjectPlantFieldResponse]: List of plant fields with is_locked flag.

    Raises:
        HTTPException: If project not found or doesn't belong to organization.
    """
    logger.info(
        "project_plant_fields_list_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id,
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    # Verify project exists and belongs to organization
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or str(project.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization",
        )

    # Get fields
    fields = get_project_plant_fields(db, project_id, include_deleted=include_deleted)

    # Build response list with is_locked flag for each field
    result = []
    for field in fields:
        field_dict = {
            "id": field.id,
            "project_id": field.project_id,
            "field_name": field.field_name,
            "field_type": field.field_type,
            "is_required": field.is_required,
            "display_order": field.display_order,
            "min_length": field.min_length,
            "max_length": field.max_length,
            "regex_pattern": field.regex_pattern,
            "min_value": field.min_value,
            "max_value": field.max_value,
            "is_deleted": field.is_deleted,
            "deleted_at": field.deleted_at,
            "created_at": field.created_at,
            "created_by": field.created_by,
            "is_locked": is_plant_field_locked(db, field.id),
        }
        result.append(ProjectPlantFieldResponse(**field_dict))

    logger.info(
        "project_plant_fields_list_success",
        organization_id=organization_id,
        project_id=project_id,
        count=len(result),
    )

    return result


@router.post(
    "", response_model=ProjectPlantFieldResponse, status_code=status.HTTP_201_CREATED
)
def create_project_plant_field(
    organization_id: UUID,
    project_id: UUID,
    field_data: ProjectPlantFieldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new custom plant field for a project (admin only).

    Args:
        organization_id: Organization UUID.
        project_id: Project UUID.
        field_data: Field creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        ProjectPlantFieldResponse: The created field.

    Raises:
        HTTPException: If user lacks permissions or field name conflicts.
    """
    logger.info(
        "project_plant_field_create_started",
        organization_id=organization_id,
        project_id=project_id,
        field_name=field_data.field_name,
        created_by=current_user.id,
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "project_plant_field_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to manage fields in this organization",
        )

    # Verify project exists and belongs to organization
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or str(project.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization",
        )

    # Check for duplicate field name (excluding soft-deleted fields)
    existing_field = (
        db.query(ProjectPlantField)
        .filter(
            ProjectPlantField.project_id == project_id,
            ProjectPlantField.field_name == field_data.field_name,
            ProjectPlantField.is_deleted == False,
        )
        .first()
    )

    if existing_field:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field with name '{field_data.field_name}' already exists in this project",
        )

    # Create new field
    new_field = ProjectPlantField(
        **field_data.model_dump(), project_id=project_id, created_by=current_user.id
    )

    db.add(new_field)
    db.commit()
    db.refresh(new_field)

    logger.info(
        "project_plant_field_create_success",
        field_id=new_field.id,
        project_id=project_id,
        organization_id=organization_id,
    )

    # Return response with is_locked flag
    field_dict = {
        "id": new_field.id,
        "project_id": new_field.project_id,
        "field_name": new_field.field_name,
        "field_type": new_field.field_type,
        "is_required": new_field.is_required,
        "display_order": new_field.display_order,
        "min_length": new_field.min_length,
        "max_length": new_field.max_length,
        "regex_pattern": new_field.regex_pattern,
        "min_value": new_field.min_value,
        "max_value": new_field.max_value,
        "is_deleted": new_field.is_deleted,
        "deleted_at": new_field.deleted_at,
        "created_at": new_field.created_at,
        "created_by": new_field.created_by,
        "is_locked": False,  # New field has no values
    }

    return ProjectPlantFieldResponse(**field_dict)


@router.patch("/{field_id}", response_model=ProjectPlantFieldResponse)
def update_project_plant_field(
    organization_id: UUID,
    project_id: UUID,
    field_id: UUID,
    field_update: ProjectPlantFieldUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a custom plant field (admin only).

    Field type cannot be changed if field is locked (has values).

    Args:
        organization_id: Organization UUID.
        project_id: Project UUID.
        field_id: Field UUID to update.
        field_update: Field update data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        ProjectPlantFieldResponse: The updated field.

    Raises:
        HTTPException: If user lacks permissions, field not found, or validation fails.
    """
    logger.info(
        "project_plant_field_update_started",
        organization_id=organization_id,
        project_id=project_id,
        field_id=field_id,
        updated_by=current_user.id,
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "project_plant_field_update_forbidden",
            organization_id=organization_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to manage fields in this organization",
        )

    # Get the field
    field = db.query(ProjectPlantField).filter(ProjectPlantField.id == field_id).first()
    if not field or str(field.project_id) != str(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Field not found"
        )

    # Verify project belongs to organization
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or str(project.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization",
        )

    # Check for name conflicts if name is being updated
    if field_update.field_name and field_update.field_name != field.field_name:
        existing_field = (
            db.query(ProjectPlantField)
            .filter(
                ProjectPlantField.project_id == project_id,
                ProjectPlantField.field_name == field_update.field_name,
                ProjectPlantField.is_deleted == False,
                ProjectPlantField.id != field_id,
            )
            .first()
        )

        if existing_field:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field with name '{field_update.field_name}' already exists in this project",
            )

    # Update fields
    update_data = field_update.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(field, field_name, value)

    db.commit()
    db.refresh(field)

    logger.info("project_plant_field_update_success", field_id=field_id)

    # Return response with is_locked flag
    field_dict = {
        "id": field.id,
        "project_id": field.project_id,
        "field_name": field.field_name,
        "field_type": field.field_type,
        "is_required": field.is_required,
        "display_order": field.display_order,
        "min_length": field.min_length,
        "max_length": field.max_length,
        "regex_pattern": field.regex_pattern,
        "min_value": field.min_value,
        "max_value": field.max_value,
        "is_deleted": field.is_deleted,
        "deleted_at": field.deleted_at,
        "created_at": field.created_at,
        "created_by": field.created_by,
        "is_locked": is_plant_field_locked(db, field.id),
    }

    return ProjectPlantFieldResponse(**field_dict)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_plant_field(
    organization_id: UUID,
    project_id: UUID,
    field_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete a custom plant field (admin only).

    Field is marked as deleted but values are preserved.

    Args:
        organization_id: Organization UUID.
        project_id: Project UUID.
        field_id: Field UUID to delete.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        None: No content on successful deletion.

    Raises:
        HTTPException: If user lacks permissions or field not found.
    """
    logger.info(
        "project_plant_field_delete_started",
        organization_id=organization_id,
        project_id=project_id,
        field_id=field_id,
        deleted_by=current_user.id,
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "project_plant_field_delete_forbidden",
            organization_id=organization_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to manage fields in this organization",
        )

    # Get the field
    field = db.query(ProjectPlantField).filter(ProjectPlantField.id == field_id).first()
    if not field or str(field.project_id) != str(project_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Field not found"
        )

    # Verify project belongs to organization
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or str(project.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in this organization",
        )

    # Soft delete the field
    field.is_deleted = True
    field.deleted_at = datetime.utcnow()

    db.commit()

    logger.info("project_plant_field_delete_success", field_id=field_id)

    return None
