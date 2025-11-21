from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Organization, Species, User
from app.schemas import SpeciesCreate, SpeciesUpdate, SpeciesResponse
from app.api.deps import get_current_user
from app.core.permissions import is_org_member, can_manage_organization
from app.core.botanical_name_parser import parse_botanical_name
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ParseNameRequest(BaseModel):
    """Request schema for parsing a botanical name."""
    name: str


class ParseNameResponse(BaseModel):
    """Response schema for parsed botanical name components."""
    genus: Optional[str] = None
    species_name: Optional[str] = None
    subspecies: Optional[str] = None
    variety: Optional[str] = None
    cultivar: Optional[str] = None


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
        subspecies=species_data.subspecies,
        variety=species_data.variety,
        cultivar=species_data.cultivar,
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


@router.post("/parse-name", response_model=ParseNameResponse)
def parse_species_name(
    parse_request: ParseNameRequest,
    current_user: User = Depends(get_current_user)
):
    """Parse a botanical name into its components.

    This is a utility endpoint that parses a scientific name string into
    structured components (genus, species, subspecies, variety, cultivar).
    No database access required, just parsing logic.

    Args:
        parse_request: Request containing the name to parse.
        current_user: Authenticated user (required but not used).

    Returns:
        ParseNameResponse: Parsed name components.

    Examples:
        "Acer rubrum" -> genus="Acer", species_name="rubrum"
        "Acer rubrum var. trilobum" -> genus="Acer", species_name="rubrum", variety="trilobum"
        "Rosa 'Peace'" -> genus="Rosa", cultivar="Peace"
    """
    logger.info("species_name_parse_started", name=parse_request.name, user_id=current_user.id)

    parsed = parse_botanical_name(parse_request.name)

    logger.info(
        "species_name_parse_success",
        name=parse_request.name,
        genus=parsed.get('genus'),
        species=parsed.get('species_name')
    )

    return ParseNameResponse(**parsed)
