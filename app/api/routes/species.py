from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, Species, User
from app.schemas import SpeciesCreate, SpeciesUpdate, SpeciesResponse
from app.api.deps import get_current_user
from app.core.permissions import is_org_member, can_manage_organization
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=SpeciesResponse, status_code=status.HTTP_201_CREATED)
def create_species(
    organization_id: UUID,
    species_data: SpeciesCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new species in an organization (admin only)."""
    logger.info(
        "species_create_started",
        organization_id=organization_id,
        genus=species_data.genus,
        species_name=species_data.species_name,
        created_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "species_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can create species"
        )

    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("organization_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    new_species = Species(
        genus=species_data.genus,
        species_name=species_data.species_name,
        variety=species_data.variety,
        common_name=species_data.common_name,
        description=species_data.description,
        organization_id=organization_id,
        created_by=current_user.id
    )
    db.add(new_species)
    db.commit()
    db.refresh(new_species)

    logger.info(
        "species_created",
        species_id=new_species.id,
        genus=new_species.genus,
        species_name=new_species.species_name,
        organization_id=organization_id,
        created_by=current_user.id
    )

    return new_species


@router.get("/", response_model=List[SpeciesResponse])
def list_species(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List species in an organization."""
    logger.info("list_species", organization_id=organization_id, user_id=current_user.id)

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "list_species_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    species = db.query(Species).filter(Species.organization_id == organization_id).all()

    logger.info(
        "species_listed",
        organization_id=organization_id,
        species_count=len(species)
    )

    return species


@router.get("/{species_id}", response_model=SpeciesResponse)
def get_species(
    organization_id: UUID,
    species_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific species."""
    logger.info(
        "get_species",
        organization_id=organization_id,
        species_id=species_id,
        user_id=current_user.id
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_species_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    species = db.query(Species).filter(
        Species.id == species_id,
        Species.organization_id == organization_id
    ).first()

    if not species:
        logger.warning("species_not_found", species_id=species_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )

    logger.info("species_retrieved", species_id=species_id)
    return species


@router.patch("/{species_id}", response_model=SpeciesResponse)
def update_species(
    organization_id: UUID,
    species_id: UUID,
    species_update: SpeciesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a species (admin only)."""
    logger.info(
        "update_species_started",
        organization_id=organization_id,
        species_id=species_id,
        user_id=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "update_species_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can update species"
        )

    species = db.query(Species).filter(
        Species.id == species_id,
        Species.organization_id == organization_id
    ).first()

    if not species:
        logger.warning("species_not_found", species_id=species_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )

    # Update fields
    update_data = species_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(species, field, value)

    db.commit()
    db.refresh(species)

    logger.info("species_updated", species_id=species_id)
    return species


@router.delete("/{species_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_species(
    organization_id: UUID,
    species_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a species (admin only)."""
    logger.info(
        "delete_species_started",
        organization_id=organization_id,
        species_id=species_id,
        user_id=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "delete_species_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can delete species"
        )

    species = db.query(Species).filter(
        Species.id == species_id,
        Species.organization_id == organization_id
    ).first()

    if not species:
        logger.warning("species_not_found", species_id=species_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )

    db.delete(species)
    db.commit()

    logger.info("species_deleted", species_id=species_id)
