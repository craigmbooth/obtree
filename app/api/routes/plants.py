"""Plant API routes for managing plants within accessions.

This module provides CRUD endpoints for managing plants, which are nested
under accessions within the organization hierarchy.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.permissions import can_manage_organization, is_org_member
from app.logging_config import get_logger
from app.models import Accession, Plant, Species, User
from app.schemas.plant import (
    PlantCreate,
    PlantResponse,
    PlantUpdate,
    PlantWithDetailsResponse,
)

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

    logger.info(
        "plant_list_success",
        organization_id=organization_id,
        accession_id=accession_id,
        count=len(plants),
    )

    return plants


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

    # Update fields
    update_data = plant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plant, field, value)

    db.commit()
    db.refresh(plant)

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
