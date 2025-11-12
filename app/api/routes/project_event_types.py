from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.permissions import is_org_member, can_manage_organization
from app.logging_config import get_logger
from app.models import User, Organization, Project, EventType, EventTypeField
from app.schemas import (
    EventTypeCreate,
    EventTypeUpdate,
    EventTypeResponse,
    EventTypeFieldCreate,
    EventTypeFieldUpdate,
    EventTypeFieldResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[EventTypeResponse])
def list_project_event_types(
    organization_id: UUID,
    project_id: UUID,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all project-level event types (all members can view).

    Args:
        organization_id: Organization UUID.
        project_id: Project UUID.
        include_deleted: Whether to include deleted event types.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List[EventTypeResponse]: List of project event types.

    Raises:
        HTTPException: If user is not a member of the organization.
    """
    logger.info(
        "project_event_types_list_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "project_event_types_list_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Verify project exists and belongs to organization
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()
    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Query event types
    query = db.query(EventType).options(
        joinedload(EventType.fields)
    ).filter(
        EventType.organization_id == organization_id,
        EventType.project_id == project_id  # Project-level only
    )

    if not include_deleted:
        query = query.filter(EventType.is_deleted == False)

    event_types = query.order_by(EventType.display_order, EventType.event_name).all()

    # Filter out deleted fields if not include_deleted
    if not include_deleted:
        for event_type in event_types:
            event_type.fields = [f for f in event_type.fields if not f.is_deleted]

    logger.info(
        "project_event_types_listed",
        organization_id=organization_id,
        project_id=project_id,
        count=len(event_types)
    )

    return event_types


@router.post("", response_model=EventTypeResponse, status_code=status.HTTP_201_CREATED)
def create_project_event_type(
    organization_id: UUID,
    project_id: UUID,
    event_type_data: EventTypeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new project-level event type (admin only).

    Args:
        organization_id: Organization UUID.
        project_id: Project UUID.
        event_type_data: Event type creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        EventTypeResponse: Created event type.

    Raises:
        HTTPException: If user lacks permissions or project not found.
    """
    logger.info(
        "project_event_type_create_started",
        organization_id=organization_id,
        project_id=project_id,
        event_name=event_type_data.event_name,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "project_event_type_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can create event types"
        )

    # Verify project exists and belongs to organization
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()
    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Create event type
    new_event_type = EventType(
        event_name=event_type_data.event_name,
        description=event_type_data.description,
        organization_id=organization_id,
        project_id=project_id,  # Project-level
        display_order=event_type_data.display_order,
        created_by=current_user.id
    )
    db.add(new_event_type)
    db.flush()  # Get ID for fields

    # Create fields if provided
    if event_type_data.fields:
        for field_data in event_type_data.fields:
            new_field = EventTypeField(
                event_type_id=new_event_type.id,
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
    db.refresh(new_event_type)

    logger.info(
        "project_event_type_created",
        event_type_id=new_event_type.id,
        event_name=new_event_type.event_name,
        organization_id=organization_id
    )

    return new_event_type


@router.get("/{event_type_id}", response_model=EventTypeResponse)
def get_project_event_type(
    organization_id: UUID,
    project_id: UUID,
    event_type_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get event type details.

    Args:
        organization_id: Organization UUID.
        event_type_id: Event type UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        EventTypeResponse: Event type details.

    Raises:
        HTTPException: If user is not a member or event type not found.
    """
    logger.info(
        "get_org_event_type",
        organization_id=organization_id,
        event_type_id=event_type_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_org_event_type_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query event type
    event_type = db.query(EventType).options(
        joinedload(EventType.fields)
    ).filter(
        EventType.id == event_type_id,
        EventType.organization_id == organization_id,
        EventType.project_id == project_id
    ).first()

    if not event_type:
        logger.warning("project_event_type_not_found", event_type_id=event_type_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    logger.info("project_event_type_retrieved", event_type_id=event_type_id)
    return event_type


@router.patch("/{event_type_id}", response_model=EventTypeResponse)
def update_project_event_type(
    organization_id: UUID,
    project_id: UUID,
    event_type_id: UUID,
    event_type_update: EventTypeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update event type (admin only).

    Args:
        organization_id: Organization UUID.
        event_type_id: Event type UUID.
        event_type_update: Event type update data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        EventTypeResponse: Updated event type.

    Raises:
        HTTPException: If user lacks permissions or event type not found.
    """
    logger.info(
        "update_org_event_type_started",
        organization_id=organization_id,
        event_type_id=event_type_id,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "update_org_event_type_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can update event types"
        )

    # Query event type
    event_type = db.query(EventType).filter(
        EventType.id == event_type_id,
        EventType.organization_id == organization_id,
        EventType.project_id == project_id
    ).first()

    if not event_type:
        logger.warning("project_event_type_not_found", event_type_id=event_type_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    # Update fields
    update_data = event_type_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event_type, field, value)

    db.commit()
    db.refresh(event_type)

    logger.info("project_event_type_updated", event_type_id=event_type_id)
    return event_type


@router.delete("/{event_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_event_type(
    organization_id: UUID,
    project_id: UUID,
    event_type_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete event type (admin only).

    Args:
        organization_id: Organization UUID.
        event_type_id: Event type UUID.
        current_user: Authenticated user.
        db: Database session.

    Raises:
        HTTPException: If user lacks permissions or event type not found.
    """
    logger.info(
        "delete_org_event_type_started",
        organization_id=organization_id,
        event_type_id=event_type_id,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "delete_org_event_type_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can delete event types"
        )

    # Query event type
    event_type = db.query(EventType).filter(
        EventType.id == event_type_id,
        EventType.organization_id == organization_id,
        EventType.project_id == project_id
    ).first()

    if not event_type:
        logger.warning("project_event_type_not_found", event_type_id=event_type_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    # Soft delete
    event_type.is_deleted = True
    event_type.deleted_at = datetime.utcnow()

    # Soft delete all fields
    for field in event_type.fields:
        field.is_deleted = True
        field.deleted_at = datetime.utcnow()

    db.commit()

    logger.info("project_event_type_deleted", event_type_id=event_type_id)


@router.post("/{event_type_id}/fields", response_model=EventTypeFieldResponse, status_code=status.HTTP_201_CREATED)
def create_event_type_field(
    organization_id: UUID,
    project_id: UUID,
    event_type_id: UUID,
    field_data: EventTypeFieldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a field to an event type (admin only).

    Args:
        organization_id: Organization UUID.
        event_type_id: Event type UUID.
        field_data: Field creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        EventTypeFieldResponse: Created field.

    Raises:
        HTTPException: If user lacks permissions or event type not found.
    """
    logger.info(
        "create_event_type_field_started",
        organization_id=organization_id,
        event_type_id=event_type_id,
        field_name=field_data.field_name,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "create_event_type_field_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can create event type fields"
        )

    # Verify event type exists and belongs to org
    event_type = db.query(EventType).filter(
        EventType.id == event_type_id,
        EventType.organization_id == organization_id,
        EventType.project_id == project_id
    ).first()

    if not event_type:
        logger.warning("project_event_type_not_found", event_type_id=event_type_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    # Create field
    new_field = EventTypeField(
        event_type_id=event_type_id,
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

    logger.info("event_type_field_created", field_id=new_field.id, event_type_id=event_type_id)
    return new_field


@router.patch("/{event_type_id}/fields/{field_id}", response_model=EventTypeFieldResponse)
def update_event_type_field(
    organization_id: UUID,
    project_id: UUID,
    event_type_id: UUID,
    field_id: UUID,
    field_update: EventTypeFieldUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a field (admin only). Check field.is_locked before allowing field_type change.

    Args:
        organization_id: Organization UUID.
        event_type_id: Event type UUID.
        field_id: Field UUID.
        field_update: Field update data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        EventTypeFieldResponse: Updated field.

    Raises:
        HTTPException: If user lacks permissions, field not found, or field is locked.
    """
    logger.info(
        "update_event_type_field_started",
        organization_id=organization_id,
        event_type_id=event_type_id,
        field_id=field_id,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "update_event_type_field_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can update event type fields"
        )

    # Query field
    field = db.query(EventTypeField).join(EventType).filter(
        EventTypeField.id == field_id,
        EventTypeField.event_type_id == event_type_id,
        EventType.organization_id == organization_id,
        EventType.project_id == project_id
    ).first()

    if not field:
        logger.warning("event_type_field_not_found", field_id=field_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )

    # Check if trying to change field_type on locked field
    update_data = field_update.model_dump(exclude_unset=True)
    if 'field_type' in update_data and field.is_locked:
        logger.warning("field_locked", field_id=field_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change field type when field has existing values"
        )

    # Update fields
    for field_name, value in update_data.items():
        setattr(field, field_name, value)

    db.commit()
    db.refresh(field)

    logger.info("event_type_field_updated", field_id=field_id)
    return field


@router.delete("/{event_type_id}/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_type_field(
    organization_id: UUID,
    project_id: UUID,
    event_type_id: UUID,
    field_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a field (admin only).

    Args:
        organization_id: Organization UUID.
        event_type_id: Event type UUID.
        field_id: Field UUID.
        current_user: Authenticated user.
        db: Database session.

    Raises:
        HTTPException: If user lacks permissions or field not found.
    """
    logger.info(
        "delete_event_type_field_started",
        organization_id=organization_id,
        event_type_id=event_type_id,
        field_id=field_id,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "delete_event_type_field_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can delete event type fields"
        )

    # Query field
    field = db.query(EventTypeField).join(EventType).filter(
        EventTypeField.id == field_id,
        EventTypeField.event_type_id == event_type_id,
        EventType.organization_id == organization_id,
        EventType.project_id == project_id
    ).first()

    if not field:
        logger.warning("event_type_field_not_found", field_id=field_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )

    # Soft delete
    field.is_deleted = True
    field.deleted_at = datetime.utcnow()
    db.commit()

    logger.info("event_type_field_deleted", field_id=field_id)
