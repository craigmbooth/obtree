from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.permissions import is_org_member, can_manage_organization
from app.logging_config import get_logger
from app.models import User, Organization, Location, LocationType, LocationTypeField, LocationFieldValue
from app.models.project_accession_field import FieldType
from app.schemas import LocationCreate, LocationUpdate, LocationResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[LocationResponse])
def list_locations(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all locations in an organization.

    Args:
        organization_id: Organization UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List[LocationResponse]: List of locations.

    Raises:
        HTTPException: If user is not a member of the organization.
    """
    logger.info(
        "locations_list_started",
        organization_id=organization_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "locations_list_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query locations
    locations = db.query(Location).options(
        joinedload(Location.location_type),
        joinedload(Location.field_values).joinedload(LocationFieldValue.field)
    ).filter(
        Location.organization_id == organization_id
    ).order_by(Location.location_name).all()

    # Add denormalized location_type_name for response
    for location in locations:
        location.location_type_name = location.location_type.location_name

    # Add field metadata to field values
    for location in locations:
        for field_value in location.field_values:
            field_value.field_name = field_value.field.field_name
            field_value.field_type = field_value.field.field_type.value

    logger.info(
        "locations_listed",
        organization_id=organization_id,
        count=len(locations)
    )

    return locations


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    organization_id: UUID,
    location_data: LocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new location.

    Args:
        organization_id: Organization UUID.
        location_data: Location creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        LocationResponse: Created location.

    Raises:
        HTTPException: If user is not a member or validation fails.
    """
    logger.info(
        "location_create_started",
        organization_id=organization_id,
        location_name=location_data.location_name,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "location_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Verify location type exists and belongs to org
    location_type = db.query(LocationType).options(
        joinedload(LocationType.fields)
    ).filter(
        LocationType.id == location_data.location_type_id,
        LocationType.organization_id == organization_id,
        LocationType.is_deleted == False
    ).first()

    if not location_type:
        logger.warning(
            "location_type_not_found",
            location_type_id=location_data.location_type_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location type not found"
        )

    # Validate required fields
    active_fields = [f for f in location_type.fields if not f.is_deleted]
    required_field_ids = {f.id for f in active_fields if f.is_required}
    provided_field_ids = {fv.field_id for fv in (location_data.field_values or [])}

    missing_required = required_field_ids - provided_field_ids
    if missing_required:
        logger.warning(
            "location_missing_required_fields",
            missing_fields=list(missing_required)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )

    # Create location
    new_location = Location(
        organization_id=organization_id,
        location_type_id=location_data.location_type_id,
        location_name=location_data.location_name,
        notes=location_data.notes,
        created_by=current_user.id
    )
    db.add(new_location)
    db.flush()

    # Create field values
    if location_data.field_values:
        for fv_data in location_data.field_values:
            # Verify field belongs to location type
            field = next((f for f in active_fields if f.id == fv_data.field_id), None)
            if not field:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field {fv_data.field_id} not found in location type"
                )

            # Create field value with appropriate type
            field_value = LocationFieldValue(
                location_id=new_location.id,
                field_id=fv_data.field_id,
                value_string=str(fv_data.value) if field.field_type == FieldType.STRING else None,
                value_number=float(fv_data.value) if field.field_type == FieldType.NUMBER else None
            )
            db.add(field_value)

    db.commit()
    db.refresh(new_location)

    # Add denormalized data
    new_location.location_type_name = location_type.location_name
    for field_value in new_location.field_values:
        field_value.field_name = field_value.field.field_name
        field_value.field_type = field_value.field.field_type.value

    logger.info(
        "location_created",
        location_id=new_location.id,
        location_name=new_location.location_name
    )

    return new_location


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(
    organization_id: UUID,
    location_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get location details.

    Args:
        organization_id: Organization UUID.
        location_id: Location UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        LocationResponse: Location details.

    Raises:
        HTTPException: If user is not a member or location not found.
    """
    logger.info(
        "get_location",
        organization_id=organization_id,
        location_id=location_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_location_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query location
    location = db.query(Location).options(
        joinedload(Location.location_type),
        joinedload(Location.field_values).joinedload(LocationFieldValue.field)
    ).filter(
        Location.id == location_id,
        Location.organization_id == organization_id
    ).first()

    if not location:
        logger.warning("location_not_found", location_id=location_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Add denormalized data
    location.location_type_name = location.location_type.location_name
    for field_value in location.field_values:
        field_value.field_name = field_value.field.field_name
        field_value.field_type = field_value.field.field_type.value

    logger.info("location_retrieved", location_id=location_id)
    return location


@router.patch("/{location_id}", response_model=LocationResponse)
def update_location(
    organization_id: UUID,
    location_id: UUID,
    location_update: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update location.

    Args:
        organization_id: Organization UUID.
        location_id: Location UUID.
        location_update: Update data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        LocationResponse: Updated location.

    Raises:
        HTTPException: If user is not a member or location not found.
    """
    logger.info(
        "location_update_started",
        organization_id=organization_id,
        location_id=location_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "location_update_forbidden",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query location
    location = db.query(Location).options(
        joinedload(Location.location_type).joinedload(LocationType.fields),
        joinedload(Location.field_values)
    ).filter(
        Location.id == location_id,
        Location.organization_id == organization_id
    ).first()

    if not location:
        logger.warning("location_not_found", location_id=location_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Update basic fields
    if location_update.location_name is not None:
        location.location_name = location_update.location_name
    if location_update.notes is not None:
        location.notes = location_update.notes

    # Update field values if provided
    if location_update.field_values is not None:
        active_fields = [f for f in location.location_type.fields if not f.is_deleted]

        # Delete existing field values and recreate
        for fv in location.field_values:
            db.delete(fv)
        db.flush()

        # Create new field values
        for fv_data in location_update.field_values:
            field = next((f for f in active_fields if f.id == fv_data.field_id), None)
            if not field:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field {fv_data.field_id} not found in location type"
                )

            field_value = LocationFieldValue(
                location_id=location.id,
                field_id=fv_data.field_id,
                value_string=str(fv_data.value) if field.field_type == FieldType.STRING else None,
                value_number=float(fv_data.value) if field.field_type == FieldType.NUMBER else None
            )
            db.add(field_value)

    db.commit()
    db.refresh(location)

    # Add denormalized data
    location.location_type_name = location.location_type.location_name
    for field_value in location.field_values:
        field_value.field_name = field_value.field.field_name
        field_value.field_type = field_value.field.field_type.value

    logger.info("location_updated", location_id=location_id)
    return location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    organization_id: UUID,
    location_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete location.

    Args:
        organization_id: Organization UUID.
        location_id: Location UUID.
        current_user: Authenticated user.
        db: Database session.

    Raises:
        HTTPException: If user lacks permissions or location not found.
    """
    logger.info(
        "location_delete_started",
        organization_id=organization_id,
        location_id=location_id,
        user_id=current_user.id
    )

    # Check permissions (can_manage_organization for delete)
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "location_delete_forbidden",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can delete locations"
        )

    # Query location
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.organization_id == organization_id
    ).first()

    if not location:
        logger.warning("location_not_found", location_id=location_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    # Hard delete (since it's not using soft delete pattern)
    db.delete(location)
    db.commit()

    logger.info("location_deleted", location_id=location_id)
