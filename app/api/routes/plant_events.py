from typing import List
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.api.deps import get_current_user, get_db
from app.core.permissions import is_org_member
from app.logging_config import get_logger
from app.models import (
    User,
    Plant,
    Accession,
    Species,
    EventType,
    EventTypeField,
    PlantEvent,
    EventFieldValue,
)
from app.schemas import (
    PlantEventCreate,
    PlantEventUpdate,
    PlantEventResponse,
)

logger = get_logger(__name__)
router = APIRouter()


def get_accessible_event_types(db: Session, plant: Plant, organization_id: UUID) -> List[EventType]:
    """Get all event types accessible to a plant.

    Returns org-level and project-level event types for the plant's accession's projects.

    Args:
        db: Database session.
        plant: Plant object.
        organization_id: Organization UUID.

    Returns:
        List[EventType]: Accessible event types.
    """
    # Get plant's accession's projects
    accession = plant.accession
    project_ids = [p.id for p in accession.projects]

    # Query event types: org-level OR in plant's projects
    query = db.query(EventType).filter(
        EventType.organization_id == organization_id,
        EventType.is_deleted == False,
        or_(
            EventType.project_id.is_(None),  # Org-level
            EventType.project_id.in_(project_ids) if project_ids else False  # Project-level
        )
    )

    return query.all()


@router.get("/accessible-types", response_model=List[EventTypeResponse])
def get_accessible_event_types_for_plant(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all event types accessible to a plant.

    Returns org-level event types and project-level event types for projects
    that the plant's accession belongs to.

    Args:
        organization_id: Organization UUID.
        species_id: Species UUID.
        accession_id: Accession UUID.
        plant_id: Plant UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List[EventTypeResponse]: List of accessible event types.

    Raises:
        HTTPException: If user is not a member or plant not found.
    """
    logger.info(
        "get_accessible_event_types_started",
        organization_id=organization_id,
        plant_id=plant_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_accessible_event_types_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Get plant
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        logger.warning(
            "get_accessible_event_types_plant_not_found",
            plant_id=plant_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )

    # Get accessible event types
    event_types = get_accessible_event_types(db, plant, organization_id)

    logger.info(
        "get_accessible_event_types_success",
        plant_id=plant_id,
        event_type_count=len(event_types)
    )

    return event_types


@router.get("", response_model=List[PlantEventResponse])
def list_plant_events(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all events for a plant.

    Args:
        organization_id: Organization UUID.
        species_id: Species UUID.
        accession_id: Accession UUID.
        plant_id: Plant UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List[PlantEventResponse]: List of plant events.

    Raises:
        HTTPException: If user is not a member or plant not found.
    """
    logger.info(
        "list_plant_events_started",
        organization_id=organization_id,
        plant_id=plant_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "list_plant_events_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Verify plant exists and belongs to correct hierarchy
    plant = db.query(Plant).join(Accession).join(Species).filter(
        Plant.id == plant_id,
        Plant.accession_id == accession_id,
        Accession.species_id == species_id,
        Species.organization_id == organization_id
    ).first()

    if not plant:
        logger.warning("plant_not_found", plant_id=plant_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )

    # Query events
    events = db.query(PlantEvent).options(
        joinedload(PlantEvent.event_type),
        joinedload(PlantEvent.field_values).joinedload(EventFieldValue.field)
    ).filter(
        PlantEvent.plant_id == plant_id
    ).order_by(PlantEvent.event_date.desc()).all()

    # Build response with denormalized data
    result = []
    for event in events:
        # Build field values with field names
        field_values_response = []
        for fv in event.field_values:
            field_values_response.append({
                'id': fv.id,
                'event_id': fv.event_id,
                'field_id': fv.field_id,
                'field_name': fv.field.field_name,
                'field_type': fv.field.field_type.value,
                'value_string': fv.value_string,
                'value_number': fv.value_number,
                'created_at': fv.created_at,
                'updated_at': fv.updated_at
            })

        event_response = PlantEventResponse(
            id=event.id,
            plant_id=event.plant_id,
            event_type_id=event.event_type_id,
            event_type_name=event.event_type.event_name,
            event_date=event.event_date,
            notes=event.notes,
            created_at=event.created_at,
            created_by=event.created_by,
            field_values=field_values_response
        )
        result.append(event_response)

    logger.info(
        "plant_events_listed",
        plant_id=plant_id,
        count=len(result)
    )

    return result


@router.post("", response_model=PlantEventResponse, status_code=status.HTTP_201_CREATED)
def create_plant_event(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    event_data: PlantEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new plant event (all org members can create).

    Args:
        organization_id: Organization UUID.
        species_id: Species UUID.
        accession_id: Accession UUID.
        plant_id: Plant UUID.
        event_data: Event creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        PlantEventResponse: Created event.

    Raises:
        HTTPException: If user is not a member, plant not found, or validation fails.
    """
    logger.info(
        "create_plant_event_started",
        organization_id=organization_id,
        plant_id=plant_id,
        event_type_id=event_data.event_type_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "create_plant_event_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Verify plant exists
    plant = db.query(Plant).join(Accession).join(Species).filter(
        Plant.id == plant_id,
        Plant.accession_id == accession_id,
        Accession.species_id == species_id,
        Species.organization_id == organization_id
    ).first()

    if not plant:
        logger.warning("plant_not_found", plant_id=plant_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found"
        )

    # Get event type and verify it's accessible
    event_type = db.query(EventType).options(
        joinedload(EventType.fields)
    ).filter(
        EventType.id == event_data.event_type_id,
        EventType.organization_id == organization_id
    ).first()

    if not event_type:
        logger.warning("event_type_not_found", event_type_id=event_data.event_type_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event type not found"
        )

    # Verify event type is accessible to this plant
    accessible_types = get_accessible_event_types(db, plant, organization_id)
    if event_type not in accessible_types:
        logger.warning(
            "event_type_not_accessible",
            event_type_id=event_data.event_type_id,
            plant_id=plant_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Event type not accessible for this plant"
        )

    # Validate required fields
    required_fields = [f for f in event_type.fields if f.is_required and not f.is_deleted]
    provided_field_ids = {fv.field_id for fv in (event_data.field_values or [])}

    missing_fields = [f for f in required_fields if f.id not in provided_field_ids]
    if missing_fields:
        field_names = [f.field_name for f in missing_fields]
        logger.warning(
            "missing_required_fields",
            event_type_id=event_data.event_type_id,
            missing_fields=field_names
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required fields: {', '.join(field_names)}"
        )

    # Create plant event
    new_event = PlantEvent(
        plant_id=plant_id,
        event_type_id=event_data.event_type_id,
        event_date=event_data.event_date,
        notes=event_data.notes,
        created_by=current_user.id
    )
    db.add(new_event)
    db.flush()  # Get event ID

    # Create field values
    if event_data.field_values:
        for fv_data in event_data.field_values:
            # Get field to determine type
            field = db.query(EventTypeField).filter(
                EventTypeField.id == fv_data.field_id,
                EventTypeField.event_type_id == event_type.id
            ).first()

            if not field:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid field ID: {fv_data.field_id}"
                )

            # Create field value with appropriate type
            if field.field_type.value == 'string':
                value_string = str(fv_data.value)
                value_number = None
            else:  # number
                value_string = None
                value_number = float(fv_data.value)

            new_field_value = EventFieldValue(
                event_id=new_event.id,
                field_id=fv_data.field_id,
                value_string=value_string,
                value_number=value_number
            )
            db.add(new_field_value)

    db.commit()
    db.refresh(new_event)

    logger.info(
        "plant_event_created",
        event_id=new_event.id,
        plant_id=plant_id,
        event_type_id=event_data.event_type_id
    )

    # Return with denormalized data
    return PlantEventResponse(
        id=new_event.id,
        plant_id=new_event.plant_id,
        event_type_id=new_event.event_type_id,
        event_type_name=event_type.event_name,
        event_date=new_event.event_date,
        notes=new_event.notes,
        created_at=new_event.created_at,
        created_by=new_event.created_by,
        field_values=[]
    )


@router.get("/{event_id}", response_model=PlantEventResponse)
def get_plant_event(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get event details with all field values.

    Args:
        organization_id: Organization UUID.
        species_id: Species UUID.
        accession_id: Accession UUID.
        plant_id: Plant UUID.
        event_id: Event UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        PlantEventResponse: Event details.

    Raises:
        HTTPException: If user is not a member or event not found.
    """
    logger.info(
        "get_plant_event",
        organization_id=organization_id,
        plant_id=plant_id,
        event_id=event_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_plant_event_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query event
    event = db.query(PlantEvent).options(
        joinedload(PlantEvent.event_type),
        joinedload(PlantEvent.field_values).joinedload(EventFieldValue.field)
    ).join(Plant).join(Accession).join(Species).filter(
        PlantEvent.id == event_id,
        PlantEvent.plant_id == plant_id,
        Plant.accession_id == accession_id,
        Accession.species_id == species_id,
        Species.organization_id == organization_id
    ).first()

    if not event:
        logger.warning("plant_event_not_found", event_id=event_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    logger.info("plant_event_retrieved", event_id=event_id)

    # Build response
    field_values_response = []
    for fv in event.field_values:
        field_values_response.append({
            'id': fv.id,
            'event_id': fv.event_id,
            'field_id': fv.field_id,
            'field_name': fv.field.field_name,
            'field_type': fv.field.field_type.value,
            'value_string': fv.value_string,
            'value_number': fv.value_number,
            'created_at': fv.created_at,
            'updated_at': fv.updated_at
        })

    return PlantEventResponse(
        id=event.id,
        plant_id=event.plant_id,
        event_type_id=event.event_type_id,
        event_type_name=event.event_type.event_name,
        event_date=event.event_date,
        notes=event.notes,
        created_at=event.created_at,
        created_by=event.created_by,
        field_values=field_values_response
    )


@router.patch("/{event_id}", response_model=PlantEventResponse)
def update_plant_event(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    event_id: UUID,
    event_update: PlantEventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a plant event.

    Args:
        organization_id: Organization UUID.
        species_id: Species UUID.
        accession_id: Accession UUID.
        plant_id: Plant UUID.
        event_id: Event UUID.
        event_update: Event update data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        PlantEventResponse: Updated event.

    Raises:
        HTTPException: If user is not a member or event not found.
    """
    logger.info(
        "update_plant_event_started",
        organization_id=organization_id,
        plant_id=plant_id,
        event_id=event_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "update_plant_event_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query event
    event = db.query(PlantEvent).options(
        joinedload(PlantEvent.event_type)
    ).join(Plant).join(Accession).join(Species).filter(
        PlantEvent.id == event_id,
        PlantEvent.plant_id == plant_id,
        Plant.accession_id == accession_id,
        Accession.species_id == species_id,
        Species.organization_id == organization_id
    ).first()

    if not event:
        logger.warning("plant_event_not_found", event_id=event_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Update basic fields
    update_data = event_update.model_dump(exclude_unset=True, exclude={'field_values'})
    for field, value in update_data.items():
        setattr(event, field, value)

    # Update field values if provided
    if event_update.field_values is not None:
        # Delete existing field values
        db.query(EventFieldValue).filter(EventFieldValue.event_id == event_id).delete()

        # Create new field values
        for fv_data in event_update.field_values:
            field = db.query(EventTypeField).filter(
                EventTypeField.id == fv_data.field_id,
                EventTypeField.event_type_id == event.event_type_id
            ).first()

            if not field:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid field ID: {fv_data.field_id}"
                )

            if field.field_type.value == 'string':
                value_string = str(fv_data.value)
                value_number = None
            else:
                value_string = None
                value_number = float(fv_data.value)

            new_field_value = EventFieldValue(
                event_id=event_id,
                field_id=fv_data.field_id,
                value_string=value_string,
                value_number=value_number
            )
            db.add(new_field_value)

    db.commit()
    db.refresh(event)

    logger.info("plant_event_updated", event_id=event_id)

    return PlantEventResponse(
        id=event.id,
        plant_id=event.plant_id,
        event_type_id=event.event_type_id,
        event_type_name=event.event_type.event_name,
        event_date=event.event_date,
        notes=event.notes,
        created_at=event.created_at,
        created_by=event.created_by,
        field_values=[]
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plant_event(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete event (CASCADE will delete field_values).

    Args:
        organization_id: Organization UUID.
        species_id: Species UUID.
        accession_id: Accession UUID.
        plant_id: Plant UUID.
        event_id: Event UUID.
        current_user: Authenticated user.
        db: Database session.

    Raises:
        HTTPException: If user is not a member or event not found.
    """
    logger.info(
        "delete_plant_event_started",
        organization_id=organization_id,
        plant_id=plant_id,
        event_id=event_id,
        user_id=current_user.id
    )

    # Check org membership
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "delete_plant_event_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Query event
    event = db.query(PlantEvent).join(Plant).join(Accession).join(Species).filter(
        PlantEvent.id == event_id,
        PlantEvent.plant_id == plant_id,
        Plant.accession_id == accession_id,
        Accession.species_id == species_id,
        Species.organization_id == organization_id
    ).first()

    if not event:
        logger.warning("plant_event_not_found", event_id=event_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    db.delete(event)  # CASCADE will delete field_values
    db.commit()

    logger.info("plant_event_deleted", event_id=event_id)
