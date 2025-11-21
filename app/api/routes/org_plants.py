"""Plant API routes at organization level for simplified URL access.

This module provides endpoints for accessing plants directly at the organization level,
without requiring the full nested hierarchy (species/accession).
"""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.field_validation import get_project_plant_fields
from app.core.permissions import is_org_member, can_manage_organization
from app.logging_config import get_logger
from app.models import Accession, Plant, Species, User, Location, LocationType, LocationFieldValue, LocationTypeField
from app.schemas.plant import PlantWithDetailsResponse, PlantUpdate
from app.schemas.plant_field_value import PlantFieldValueResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("/accession/{accession_id}", response_model=List[PlantWithDetailsResponse])
def list_plants_by_accession(
    organization_id: UUID,
    accession_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all plants for an accession (all org members can view).

    Args:
        organization_id: UUID of the organization.
        accession_id: UUID of the accession.
        current_user: Currently authenticated user.
        db: Database session.

    Returns:
        List[PlantWithDetailsResponse]: List of plants with full details.

    Raises:
        HTTPException: If user lacks permissions or accession not found.
    """
    logger.info(
        "org_plants_list_by_accession_started",
        organization_id=organization_id,
        accession_id=accession_id,
        user_id=current_user.id,
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "org_plants_list_forbidden",
            organization_id=organization_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view plants in this organization",
        )

    # Get the accession and verify it belongs to the organization
    accession = (
        db.query(Accession)
        .filter(Accession.id == accession_id)
        .options(
            joinedload(Accession.species),
            joinedload(Accession.parent_species_1),
            joinedload(Accession.parent_species_2),
            joinedload(Accession.projects)
        )
        .first()
    )

    if not accession:
        logger.warning("org_plants_list_accession_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found"
        )

    # Verify accession belongs to organization (check via species or parent species for hybrids)
    if accession.is_hybrid:
        if accession.parent_species_1 and str(accession.parent_species_1.organization_id) != str(organization_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Accession not found in this organization",
            )
    else:
        if accession.species and str(accession.species.organization_id) != str(organization_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Accession not found in this organization",
            )

    # Get all plants for this accession with joined data
    plants = (
        db.query(Plant)
        .filter(Plant.accession_id == accession_id)
        .options(
            joinedload(Plant.location).joinedload(Location.location_type),
            joinedload(Plant.location).joinedload(Location.field_values).joinedload(LocationFieldValue.field)
        )
        .order_by(Plant.plant_id)
        .all()
    )

    # Get project_id for field values
    project_id = None
    project_title = None
    if accession.projects:
        first_project = accession.projects[0]
        project_id = first_project.id
        project_title = first_project.title

    # Get project plant fields once for all plants
    project_fields = []
    if project_id:
        project_fields = get_project_plant_fields(db, project_id, include_deleted=False)

    # Build response for each plant
    result = []
    for plant in plants:
        # Build field values for this plant
        field_values = []
        if project_id:
            existing_values = {str(fv.field_id): fv for fv in plant.field_values}
            for field in project_fields:
                field_id_str = str(field.id)
                if field_id_str in existing_values:
                    fv = existing_values[field_id_str]
                    field_values.append(
                        PlantFieldValueResponse(
                            id=fv.id,
                            plant_id=fv.plant_id,
                            field_id=fv.field_id,
                            field_name=fv.field_name,
                            field_type=fv.field_type,
                            value=fv.value,
                            created_at=fv.created_at,
                            updated_at=fv.updated_at,
                        )
                    )
                else:
                    field_values.append(
                        PlantFieldValueResponse(
                            id=None,
                            plant_id=plant.id,
                            field_id=field.id,
                            field_name=field.field_name,
                            field_type=field.field_type,
                            value=None,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                    )

        # Prepare location data if present
        location_data = None
        if plant.location:
            location_data = plant.location
            location_data.location_type_name = plant.location.location_type.location_name
            for field_value in location_data.field_values:
                field_value.field_name = field_value.field.field_name
                field_value.field_type = field_value.field.field_type.value

        # Get species info (handle hybrids)
        species_id = None
        species_genus = None
        species_name = None
        species_variety = None
        species_common_name = None

        if accession.is_hybrid:
            # For hybrids, use hybrid display name as species name
            if accession.parent_species_1 and accession.parent_species_2:
                species_genus = accession.parent_species_1.genus
                species_name = f"{accession.parent_species_1.species_name} × {accession.parent_species_2.species_name}"
        else:
            if accession.species:
                species_id = accession.species.id
                species_genus = accession.species.genus
                species_name = accession.species.species_name
                species_variety = accession.species.variety
                species_common_name = accession.species.common_name

        result.append(
            PlantWithDetailsResponse(
                id=plant.id,
                plant_id=plant.plant_id,
                accession_id=plant.accession_id,
                created_at=plant.created_at,
                created_by=plant.created_by,
                accession=accession.accession,
                species_id=species_id,
                species_genus=species_genus,
                species_name=species_name,
                species_variety=species_variety,
                species_common_name=species_common_name,
                project_id=project_id,
                project_title=project_title,
                field_values=field_values,
                location=location_data,
            )
        )

    logger.info(
        "org_plants_list_by_accession_success",
        accession_id=accession_id,
        plant_count=len(result)
    )

    return result


@router.get("/{plant_id}", response_model=PlantWithDetailsResponse)
def get_plant(
    organization_id: UUID,
    plant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single plant with full details (all org members can view).

    Args:
        organization_id: UUID of the organization.
        plant_id: UUID of the plant.
        current_user: Currently authenticated user.
        db: Database session.

    Returns:
        PlantWithDetailsResponse: Plant with species and accession details.

    Raises:
        HTTPException: If user lacks permissions or plant not found.
    """
    logger.info(
        "org_plant_get_started",
        organization_id=organization_id,
        plant_id=plant_id,
        user_id=current_user.id,
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "org_plant_get_forbidden",
            organization_id=organization_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view plants in this organization",
        )

    # Get the plant with joined accession, species, and location
    plant = (
        db.query(Plant)
        .filter(Plant.id == plant_id)
        .options(
            joinedload(Plant.accession).joinedload(Accession.species),
            joinedload(Plant.location).joinedload(Location.location_type),
            joinedload(Plant.location).joinedload(Location.field_values).joinedload(LocationFieldValue.field)
        )
        .first()
    )

    if not plant:
        logger.warning("org_plant_get_not_found", plant_id=plant_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found"
        )

    # Verify species belongs to organization
    # For hybrids, check parent species; for non-hybrids, check species
    if plant.accession.is_hybrid:
        if plant.accession.parent_species_2:
            species_org_id = plant.accession.parent_species_2.organization_id
        elif plant.accession.parent_species_1:
            species_org_id = plant.accession.parent_species_1.organization_id
        else:
            logger.error("org_plant_get_hybrid_missing_parents", plant_id=plant_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Hybrid accession has no parent species",
            )
    else:
        if not plant.accession.species:
            logger.error("org_plant_get_missing_species", plant_id=plant_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Accession has no species",
            )
        species_org_id = plant.accession.species.organization_id

    if str(species_org_id) != str(organization_id):
        logger.warning(
            "org_plant_get_org_mismatch",
            plant_id=plant_id,
            species_org_id=species_org_id,
            requested_org_id=organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found in this organization",
        )

    # Get project_id from accession for field values
    project_id = None
    project_title = None
    if plant.accession.projects:
        first_project = plant.accession.projects[0]
        project_id = first_project.id
        project_title = first_project.title

    # Get all project plant fields and merge with plant values
    field_values = []
    if project_id:
        # Get all fields for this project
        project_fields = get_project_plant_fields(db, project_id, include_deleted=False)

        # Create a map of existing field values
        existing_values = {str(fv.field_id): fv for fv in plant.field_values}

        # For each project field, include it with value if exists, or null if not
        for field in project_fields:
            field_id_str = str(field.id)
            if field_id_str in existing_values:
                fv = existing_values[field_id_str]
                field_values.append(
                    PlantFieldValueResponse(
                        id=fv.id,
                        plant_id=fv.plant_id,
                        field_id=fv.field_id,
                        field_name=fv.field_name,
                        field_type=fv.field_type,
                        value=fv.value,
                        created_at=fv.created_at,
                        updated_at=fv.updated_at,
                    )
                )
            else:
                # Field exists in project but no value for this plant yet
                field_values.append(
                    PlantFieldValueResponse(
                        id=None,
                        plant_id=plant.id,
                        field_id=field.id,
                        field_name=field.field_name,
                        field_type=field.field_type,
                        value=None,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )

    # Prepare location data if present
    location_data = None
    if plant.location:
        location_data = plant.location
        # Add denormalized location_type_name
        location_data.location_type_name = plant.location.location_type.location_name
        # Add field metadata to field values
        for field_value in location_data.field_values:
            field_value.field_name = field_value.field.field_name
            field_value.field_type = field_value.field.field_type.value

    # Build the detailed response
    # For hybrids, use parent_species_2 as the primary species
    if plant.accession.is_hybrid:
        species_ref = plant.accession.parent_species_2 or plant.accession.parent_species_1
    else:
        species_ref = plant.accession.species

    result = PlantWithDetailsResponse(
        id=plant.id,
        plant_id=plant.plant_id,
        accession_id=plant.accession_id,
        created_at=plant.created_at,
        created_by=plant.created_by,
        accession=plant.accession.accession,
        species_id=species_ref.id,
        species_genus=species_ref.genus,
        species_name=species_ref.species_name,
        species_variety=species_ref.variety,
        species_common_name=species_ref.common_name,
        project_id=project_id,
        project_title=project_title,
        field_values=field_values,
        location=location_data,
    )

    logger.info("org_plant_get_success", plant_id=plant_id)

    return result


@router.patch("/{plant_id}", response_model=PlantWithDetailsResponse)
def update_plant(
    organization_id: UUID,
    plant_id: UUID,
    plant_update: PlantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a plant (admin only).

    Args:
        organization_id: UUID of the organization.
        plant_id: UUID of the plant.
        plant_update: Plant update data.
        current_user: Currently authenticated user.
        db: Database session.

    Returns:
        PlantWithDetailsResponse: Updated plant with full details.

    Raises:
        HTTPException: If user lacks permissions or plant not found.
    """
    logger.info(
        "org_plant_update_started",
        organization_id=organization_id,
        plant_id=plant_id,
        user_id=current_user.id,
    )

    # Check if user is an admin
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "org_plant_update_forbidden",
            organization_id=organization_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can update plants",
        )

    # Get the plant
    plant = db.query(Plant).filter(Plant.id == plant_id).first()

    if not plant:
        logger.warning("org_plant_update_not_found", plant_id=plant_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found"
        )

    # Verify species belongs to organization
    accession = db.query(Accession).filter(Accession.id == plant.accession_id).first()

    # For hybrids, check parent species; for non-hybrids, check species
    if accession.is_hybrid:
        if accession.parent_species_2:
            species = accession.parent_species_2
        elif accession.parent_species_1:
            species = accession.parent_species_1
        else:
            logger.error("org_plant_update_hybrid_missing_parents", plant_id=plant_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Hybrid accession has no parent species",
            )
    else:
        species = db.query(Species).filter(Species.id == accession.species_id).first()
        if not species:
            logger.error("org_plant_update_missing_species", plant_id=plant_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Accession has no species",
            )

    if str(species.organization_id) != str(organization_id):
        logger.warning(
            "org_plant_update_org_mismatch",
            plant_id=plant_id,
            species_org_id=species.organization_id,
            requested_org_id=organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant not found in this organization",
        )

    # Update plant_id if provided
    if plant_update.plant_id is not None:
        plant.plant_id = plant_update.plant_id

    # Update location if provided (can be None to clear location)
    if hasattr(plant_update, 'location_id'):
        if plant_update.location_id is not None:
            # Verify location exists and belongs to org
            location = db.query(Location).filter(
                Location.id == plant_update.location_id,
                Location.organization_id == organization_id
            ).first()
            if not location:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Location not found in this organization"
                )
        plant.location_id = plant_update.location_id

    db.commit()
    db.refresh(plant)

    logger.info("org_plant_updated", plant_id=plant_id)

    # Return the updated plant using the GET endpoint logic
    return get_plant(organization_id, plant_id, current_user, db)
