"""Plant API routes for managing plants within accessions.

This module provides CRUD endpoints for managing plants, which are nested
under accessions within the organization hierarchy.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.field_validation import (
    get_project_plant_fields,
    validate_field_value,
    validate_plant_required_fields,
)
from app.core.permissions import can_manage_organization, is_org_member
from app.logging_config import get_logger
from app.models import Accession, Plant, Species, User
from app.models.plant_field_value import PlantFieldValue
from app.models.project_accession_field import FieldType
from app.models.project_plant_field import ProjectPlantField
from app.schemas.plant import (
    PlantCreate,
    PlantResponse,
    PlantUpdate,
    PlantWithDetailsResponse,
)
from app.schemas.plant_field_value import PlantFieldValueResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=PlantResponse, status_code=status.HTTP_201_CREATED)
def create_plant(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_data: PlantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new plant for an accession (admin only).

    Args:
        organization_id: UUID of the organization.
        species_id: UUID of the species.
        accession_id: UUID of the parent accession.
        plant_data: Plant creation data.
        current_user: Currently authenticated user.
        db: Database session.

    Returns:
        PlantResponse: The created plant.

    Raises:
        HTTPException: If user lacks permissions, accession not found,
            or accession doesn't belong to the species/organization.
    """
    logger.info(
        "plant_create_started",
        organization_id=organization_id,
        species_id=species_id,
        accession_id=accession_id,
        plant_id=plant_data.plant_id,
        created_by=current_user.id,
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "plant_create_forbidden", organization_id=organization_id, user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create plants in this organization",
        )

    # Verify accession exists and belongs to the correct species
    accession = db.query(Accession).filter(Accession.id == accession_id).first()
    if not accession:
        logger.warning("plant_create_accession_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Accession not found"
        )

    if str(accession.species_id) != str(species_id):
        logger.warning(
            "plant_create_species_mismatch",
            accession_id=accession_id,
            accession_species_id=accession.species_id,
            requested_species_id=species_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession does not belong to this species",
        )

    # Verify species belongs to organization
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        logger.warning(
            "plant_create_org_mismatch",
            species_id=species_id,
            organization_id=organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found in this organization",
        )

    # Verify the provided accession_id matches the URL parameter
    if str(plant_data.accession_id) != str(accession_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession ID in request body must match URL parameter",
        )

    # Create new plant
    new_plant = Plant(
        plant_id=plant_data.plant_id,
        accession_id=accession_id,
        created_by=current_user.id,
    )

    db.add(new_plant)
    db.commit()
    db.refresh(new_plant)

    # Handle custom field values if provided
    if plant_data.field_values:
        # Get project_id from accession
        project_id = None
        if accession.projects:
            project_id = accession.projects[0].id

        if project_id:
            # Validate required fields
            field_values_dicts = [
                {"field_id": fv.field_id, "value": fv.value}
                for fv in plant_data.field_values
            ]
            validate_plant_required_fields(db, project_id, field_values_dicts)

            # Create field values
            for field_value_data in plant_data.field_values:
                # Get field definition
                field = (
                    db.query(ProjectPlantField)
                    .filter(
                        ProjectPlantField.id == field_value_data.field_id,
                        ProjectPlantField.project_id == project_id,
                        ProjectPlantField.is_deleted == False,
                    )
                    .first()
                )

                if not field:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field {field_value_data.field_id} not found in this project",
                    )

                # Validate value
                validate_field_value(field, field_value_data.value)

                # Create field value record
                new_field_value = PlantFieldValue(
                    plant_id=new_plant.id,
                    field_id=field.id,
                    value_string=(
                        str(field_value_data.value)
                        if field.field_type == FieldType.STRING
                        else None
                    ),
                    value_number=(
                        field_value_data.value
                        if field.field_type == FieldType.NUMBER
                        else None
                    ),
                )
                db.add(new_field_value)

            db.commit()

    logger.info(
        "plant_create_success",
        plant_id=new_plant.id,
        accession_id=accession_id,
        organization_id=organization_id,
    )

    return new_plant


@router.get("", response_model=List[PlantResponse])
def list_plants(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all plants for an accession (all org members can view).

    Args:
        organization_id: UUID of the organization.
        species_id: UUID of the species.
        accession_id: UUID of the parent accession.
        current_user: Currently authenticated user.
        db: Database session.

    Returns:
        List[PlantResponse]: List of plants for the accession.

    Raises:
        HTTPException: If user lacks permissions or accession not found.
    """
    logger.info(
        "plant_list_started",
        organization_id=organization_id,
        species_id=species_id,
        accession_id=accession_id,
        user_id=current_user.id,
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "plant_list_forbidden", organization_id=organization_id, user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view plants in this organization",
        )

    # Verify accession exists and belongs to the correct species/organization
    accession = db.query(Accession).filter(Accession.id == accession_id).first()
    if not accession:
        logger.warning("plant_list_accession_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Accession not found"
        )

    if str(accession.species_id) != str(species_id):
        logger.warning(
            "plant_list_species_mismatch",
            accession_id=accession_id,
            accession_species_id=accession.species_id,
            requested_species_id=species_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession does not belong to this species",
        )

    # Verify species belongs to organization
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found in this organization",
        )

    # Get all plants for this accession
    plants = db.query(Plant).filter(Plant.accession_id == accession_id).all()

    # Get project_id from accession for field values
    project_id = None
    if accession.projects:
        project_id = accession.projects[0].id

    # Build response with field values
    result = []
    for plant in plants:
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

        result.append(
            PlantResponse(
                id=plant.id,
                plant_id=plant.plant_id,
                accession_id=plant.accession_id,
                created_at=plant.created_at,
                created_by=plant.created_by,
                field_values=field_values,
            )
        )

    logger.info(
        "plant_list_success",
        organization_id=organization_id,
        accession_id=accession_id,
        count=len(result),
    )

    return result


@router.get("/{plant_id}", response_model=PlantWithDetailsResponse)
def get_plant(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single plant with full details (all org members can view).

    Args:
        organization_id: UUID of the organization.
        species_id: UUID of the species.
        accession_id: UUID of the parent accession.
        plant_id: UUID of the plant.
        current_user: Currently authenticated user.
        db: Database session.

    Returns:
        PlantWithDetailsResponse: Plant with species and accession details.

    Raises:
        HTTPException: If user lacks permissions or plant not found.
    """
    logger.info(
        "plant_get_started",
        organization_id=organization_id,
        species_id=species_id,
        accession_id=accession_id,
        plant_id=plant_id,
        user_id=current_user.id,
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "plant_get_forbidden", organization_id=organization_id, user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view plants in this organization",
        )

    # Get the plant with joined accession and species
    plant = (
        db.query(Plant)
        .filter(Plant.id == plant_id)
        .options(joinedload(Plant.accession).joinedload(Accession.species))
        .first()
    )

    if not plant:
        logger.warning("plant_get_not_found", plant_id=plant_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")

    # Verify plant belongs to the correct accession
    if str(plant.accession_id) != str(accession_id):
        logger.warning(
            "plant_get_accession_mismatch",
            plant_id=plant_id,
            plant_accession_id=plant.accession_id,
            requested_accession_id=accession_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plant does not belong to this accession",
        )

    # Verify accession belongs to the correct species
    if str(plant.accession.species_id) != str(species_id):
        logger.warning(
            "plant_get_species_mismatch",
            plant_id=plant_id,
            accession_species_id=plant.accession.species_id,
            requested_species_id=species_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession does not belong to this species",
        )

    # Verify species belongs to organization
    if str(plant.accession.species.organization_id) != str(organization_id):
        logger.warning(
            "plant_get_org_mismatch",
            plant_id=plant_id,
            species_org_id=plant.accession.species.organization_id,
            requested_org_id=organization_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found in this organization",
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

    # Build the detailed response
    result = PlantWithDetailsResponse(
        id=plant.id,
        plant_id=plant.plant_id,
        accession_id=plant.accession_id,
        created_at=plant.created_at,
        created_by=plant.created_by,
        accession=plant.accession.accession,
        species_genus=plant.accession.species.genus,
        species_name=plant.accession.species.species_name,
        species_variety=plant.accession.species.variety,
        species_common_name=plant.accession.species.common_name,
        project_id=project_id,
        project_title=project_title,
        field_values=field_values,
    )

    logger.info("plant_get_success", plant_id=plant_id)

    return result


@router.patch("/{plant_id}", response_model=PlantResponse)
def update_plant(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    plant_update: PlantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a plant (admin only).

    Args:
        organization_id: UUID of the organization.
        species_id: UUID of the species.
        accession_id: UUID of the parent accession.
        plant_id: UUID of the plant to update.
        plant_update: Plant update data.
        current_user: Currently authenticated user.
        db: Database session.

    Returns:
        PlantResponse: The updated plant.

    Raises:
        HTTPException: If user lacks permissions or plant not found.
    """
    logger.info(
        "plant_update_started",
        organization_id=organization_id,
        species_id=species_id,
        accession_id=accession_id,
        plant_id=plant_id,
        updated_by=current_user.id,
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "plant_update_forbidden", organization_id=organization_id, user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update plants in this organization",
        )

    # Get the plant
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        logger.warning("plant_update_not_found", plant_id=plant_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")

    # Verify plant belongs to the correct accession
    if str(plant.accession_id) != str(accession_id):
        logger.warning(
            "plant_update_accession_mismatch",
            plant_id=plant_id,
            plant_accession_id=plant.accession_id,
            requested_accession_id=accession_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plant does not belong to this accession",
        )

    # Verify accession belongs to species/organization
    accession = db.query(Accession).filter(Accession.id == accession_id).first()
    if not accession or str(accession.species_id) != str(species_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession does not belong to this species",
        )

    species = db.query(Species).filter(Species.id == species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found in this organization",
        )

    # Update fields (exclude field_values as it's handled separately)
    update_data = plant_update.model_dump(exclude_unset=True, exclude={"field_values"})
    for field, value in update_data.items():
        setattr(plant, field, value)

    db.commit()
    db.refresh(plant)

    # Handle custom field values if provided
    if plant_update.field_values is not None:
        # Get project_id from accession
        project_id = None
        if accession.projects:
            project_id = accession.projects[0].id

        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update field values for plant without project association",
            )

        # Validate required fields
        field_values_dicts = [
            {"field_id": fv.field_id, "value": fv.value}
            for fv in plant_update.field_values
        ]
        validate_plant_required_fields(db, project_id, field_values_dicts)

        # Delete existing field values
        db.query(PlantFieldValue).filter(PlantFieldValue.plant_id == plant_id).delete()

        # Create new field values
        for field_value_data in plant_update.field_values:
            # Get field definition
            field = (
                db.query(ProjectPlantField)
                .filter(
                    ProjectPlantField.id == field_value_data.field_id,
                    ProjectPlantField.project_id == project_id,
                    ProjectPlantField.is_deleted == False,
                )
                .first()
            )

            if not field:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field {field_value_data.field_id} not found in this project",
                )

            # Validate value
            validate_field_value(field, field_value_data.value)

            # Create field value record
            new_field_value = PlantFieldValue(
                plant_id=plant_id,
                field_id=field.id,
                value_string=(
                    str(field_value_data.value)
                    if field.field_type == FieldType.STRING
                    else None
                ),
                value_number=(
                    field_value_data.value if field.field_type == FieldType.NUMBER else None
                ),
            )
            db.add(new_field_value)

        db.commit()

    logger.info("plant_update_success", plant_id=plant_id)

    return plant


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plant(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    plant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a plant (admin only).

    Args:
        organization_id: UUID of the organization.
        species_id: UUID of the species.
        accession_id: UUID of the parent accession.
        plant_id: UUID of the plant to delete.
        current_user: Currently authenticated user.
        db: Database session.

    Returns:
        None: No content on successful deletion.

    Raises:
        HTTPException: If user lacks permissions or plant not found.
    """
    logger.info(
        "plant_delete_started",
        organization_id=organization_id,
        species_id=species_id,
        accession_id=accession_id,
        plant_id=plant_id,
        deleted_by=current_user.id,
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "plant_delete_forbidden", organization_id=organization_id, user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete plants in this organization",
        )

    # Get the plant
    plant = db.query(Plant).filter(Plant.id == plant_id).first()
    if not plant:
        logger.warning("plant_delete_not_found", plant_id=plant_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")

    # Verify plant belongs to the correct accession
    if str(plant.accession_id) != str(accession_id):
        logger.warning(
            "plant_delete_accession_mismatch",
            plant_id=plant_id,
            plant_accession_id=plant.accession_id,
            requested_accession_id=accession_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plant does not belong to this accession",
        )

    # Verify accession belongs to species/organization
    accession = db.query(Accession).filter(Accession.id == accession_id).first()
    if not accession or str(accession.species_id) != str(species_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession does not belong to this species",
        )

    species = db.query(Species).filter(Species.id == species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found in this organization",
        )

    # Delete the plant
    db.delete(plant)
    db.commit()

    logger.info("plant_delete_success", plant_id=plant_id)

    return None
