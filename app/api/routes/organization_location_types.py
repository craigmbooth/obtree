from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.permissions import is_org_member, can_manage_organization
from app.logging_config import get_logger
from app.models import User, Organization, LocationType, LocationTypeField
from app.schemas import (
    LocationTypeCreate,
    LocationTypeUpdate,
    LocationTypeResponse,
    LocationTypeFieldCreate,
    LocationTypeFieldUpdate,
    LocationTypeFieldResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[LocationTypeResponse])
def list_organization_location_types(
    organization_id: UUID,
    include_deleted: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all org-level location types (all members can view).

    Args:
        organization_id: Organization UUID.
        include_deleted: Whether to include deleted location types.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List[LocationTypeResponse]: List of organization location types.

    Raises:
        HTTPException: If user is not a member of the organization.
    """
    logger.info(
        "org_location_types_list_started",
        organization_id=organization_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "org_location_types_list_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query location types
    query = db.query(LocationType).options(
        joinedload(LocationType.fields)
    ).filter(
        LocationType.organization_id == organization_id
    )

    if not include_deleted:
        query = query.filter(LocationType.is_deleted == False)

    location_types = query.order_by(LocationType.display_order, LocationType.location_name).all()

    # Filter out deleted fields if not include_deleted
    if not include_deleted:
        for location_type in location_types:
            location_type.fields = [f for f in location_type.fields if not f.is_deleted]

    logger.info(
        "org_location_types_listed",
        organization_id=organization_id,
        count=len(location_types)
    )

    return location_types


@router.post("", response_model=LocationTypeResponse, status_code=status.HTTP_201_CREATED)
def create_organization_location_type(
    organization_id: UUID,
    location_type_data: LocationTypeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new org-level location type (admin only).

    Args:
        organization_id: Organization UUID.
        location_type_data: Location type creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        LocationTypeResponse: Created location type.

    Raises:
        HTTPException: If user lacks permissions or organization not found.
    """
    logger.info(
        "org_location_type_create_started",
        organization_id=organization_id,
        location_name=location_type_data.location_name,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "org_location_type_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can create location types"
        )

    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("organization_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Create location type
    new_location_type = LocationType(
        location_name=location_type_data.location_name,
        description=location_type_data.description,
        organization_id=organization_id,
        display_order=location_type_data.display_order,
        created_by=current_user.id
    )
    db.add(new_location_type)
    db.flush()  # Get ID for fields

    # Create fields if provided
    if location_type_data.fields:
        for field_data in location_type_data.fields:
            new_field = LocationTypeField(
                location_type_id=new_location_type.id,
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
    db.refresh(new_location_type)

    logger.info(
        "org_location_type_created",
        location_type_id=new_location_type.id,
        location_name=new_location_type.location_name,
        organization_id=organization_id
    )

    return new_location_type


@router.get("/{location_type_id}", response_model=LocationTypeResponse)
def get_organization_location_type(
    organization_id: UUID,
    location_type_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get location type details.

    Args:
        organization_id: Organization UUID.
        location_type_id: Location type UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        LocationTypeResponse: Location type details.

    Raises:
        HTTPException: If user is not a member or location type not found.
    """
    logger.info(
        "get_org_location_type",
        organization_id=organization_id,
        location_type_id=location_type_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_org_location_type_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query location type
    location_type = db.query(LocationType).options(
        joinedload(LocationType.fields)
    ).filter(
        LocationType.id == location_type_id,
        LocationType.organization_id == organization_id
    ).first()

    if not location_type:
        logger.warning("org_location_type_not_found", location_type_id=location_type_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location type not found"
        )

    logger.info("org_location_type_retrieved", location_type_id=location_type_id)
    return location_type


@router.patch("/{location_type_id}", response_model=LocationTypeResponse)
def update_organization_location_type(
    organization_id: UUID,
    location_type_id: UUID,
    location_type_update: LocationTypeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update location type (admin only).

    Args:
        organization_id: Organization UUID.
        location_type_id: Location type UUID.
        location_type_update: Update data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        LocationTypeResponse: Updated location type.

    Raises:
        HTTPException: If user lacks permissions or location type not found.
    """
    logger.info(
        "org_location_type_update_started",
        organization_id=organization_id,
        location_type_id=location_type_id,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "org_location_type_update_forbidden",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can update location types"
        )

    # Query location type
    location_type = db.query(LocationType).options(
        joinedload(LocationType.fields)
    ).filter(
        LocationType.id == location_type_id,
        LocationType.organization_id == organization_id
    ).first()

    if not location_type:
        logger.warning("org_location_type_not_found", location_type_id=location_type_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location type not found"
        )

    # Update basic fields
    if location_type_update.location_name is not None:
        location_type.location_name = location_type_update.location_name
    if location_type_update.description is not None:
        location_type.description = location_type_update.description
    if location_type_update.display_order is not None:
        location_type.display_order = location_type_update.display_order

    # Update fields if provided
    if location_type_update.fields is not None:
        # Get existing field IDs
        existing_field_ids = {f.id for f in location_type.fields}
        update_field_ids = {f.id for f in location_type_update.fields if f.id}

        # Mark fields for deletion if they're not in the update
        for field in location_type.fields:
            if field.id not in update_field_ids and not field.is_deleted:
                field.is_deleted = True
                field.deleted_at = datetime.utcnow()

        # Update or create fields
        for field_data in location_type_update.fields:
            if field_data.id and field_data.id in existing_field_ids:
                # Update existing field
                field = next(f for f in location_type.fields if f.id == field_data.id)
                field.field_name = field_data.field_name
                field.field_type = field_data.field_type
                field.is_required = field_data.is_required
                field.display_order = field_data.display_order
                field.min_length = field_data.min_length
                field.max_length = field_data.max_length
                field.regex_pattern = field_data.regex_pattern
                field.min_value = field_data.min_value
                field.max_value = field_data.max_value
            else:
                # Create new field
                new_field = LocationTypeField(
                    location_type_id=location_type.id,
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
    db.refresh(location_type)

    logger.info(
        "org_location_type_updated",
        location_type_id=location_type_id
    )

    return location_type


@router.delete("/{location_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization_location_type(
    organization_id: UUID,
    location_type_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete location type (admin only).

    Args:
        organization_id: Organization UUID.
        location_type_id: Location type UUID.
        current_user: Authenticated user.
        db: Database session.

    Raises:
        HTTPException: If user lacks permissions or location type not found.
    """
    logger.info(
        "org_location_type_delete_started",
        organization_id=organization_id,
        location_type_id=location_type_id,
        user_id=current_user.id
    )

    # Check admin permissions
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "org_location_type_delete_forbidden",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can delete location types"
        )

    # Query location type
    location_type = db.query(LocationType).filter(
        LocationType.id == location_type_id,
        LocationType.organization_id == organization_id
    ).first()

    if not location_type:
        logger.warning("org_location_type_not_found", location_type_id=location_type_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location type not found"
        )

    # Soft delete
    location_type.is_deleted = True
    location_type.deleted_at = datetime.utcnow()

    db.commit()

    logger.info(
        "org_location_type_deleted",
        location_type_id=location_type_id
    )
