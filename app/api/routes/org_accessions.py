from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_current_user, get_db
from app.core.permissions import can_manage_organization, is_org_member
from app.logging_config import get_logger
from app.models import User, Accession, Species, Organization, Project, projects_accessions
from app.schemas.accession import AccessionCreate, AccessionUpdate, AccessionResponse, AccessionWithSpeciesResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[AccessionWithSpeciesResponse])
def list_all_accessions(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all accessions for an organization (all org members can view)."""
    logger.info(
        "org_accession_list_started",
        organization_id=organization_id,
        user_id=current_user.id
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "org_accession_list_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view accessions in this organization"
        )

    # Get all species for this organization
    species_list = db.query(Species).filter(Species.organization_id == organization_id).all()
    species_dict = {s.id: s for s in species_list}
    species_ids = list(species_dict.keys())

    # Get all accessions for all species in this organization
    accessions = db.query(Accession).filter(Accession.species_id.in_(species_ids)).all()

    # Transform to include species and project information
    result = []
    for accession in accessions:
        species = species_dict.get(accession.species_id)
        if not species:
            continue

        # Get project association if exists
        project_id = None
        project_title = None
        if accession.projects:
            first_project = accession.projects[0]
            project_id = first_project.id
            project_title = first_project.title

        result.append(AccessionWithSpeciesResponse(
            id=accession.id,
            accession=accession.accession,
            description=accession.description,
            species_id=accession.species_id,
            created_at=accession.created_at,
            created_by=accession.created_by,
            species_genus=species.genus,
            species_name=species.species_name,
            species_variety=species.variety,
            species_common_name=species.common_name,
            project_id=project_id,
            project_title=project_title
        ))

    logger.info(
        "org_accession_list_success",
        organization_id=organization_id,
        count=len(result)
    )

    return result


@router.post("", response_model=AccessionResponse, status_code=status.HTTP_201_CREATED)
def create_accession_for_org(
    organization_id: UUID,
    accession_data: AccessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new accession for the organization (admin only)."""
    logger.info(
        "org_accession_create_started",
        organization_id=organization_id,
        species_id=accession_data.species_id,
        accession=accession_data.accession,
        created_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "org_accession_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create accessions in this organization"
        )

    # Verify species exists and belongs to this organization
    species = db.query(Species).filter(Species.id == accession_data.species_id).first()
    if not species:
        logger.warning("org_accession_create_species_not_found", species_id=accession_data.species_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )

    if str(species.organization_id) != str(organization_id):
        logger.warning(
            "org_accession_create_species_org_mismatch",
            species_id=accession_data.species_id,
            species_org_id=species.organization_id,
            organization_id=organization_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Species does not belong to this organization"
        )

    # Create new accession
    new_accession = Accession(
        accession=accession_data.accession,
        description=accession_data.description,
        species_id=accession_data.species_id,
        created_by=current_user.id
    )

    db.add(new_accession)
    db.commit()
    db.refresh(new_accession)

    # Associate with project if provided
    if accession_data.project_id:
        # Verify project exists and belongs to this organization
        project = db.query(Project).filter(Project.id == accession_data.project_id).first()
        if not project:
            logger.warning("org_accession_create_project_not_found", project_id=accession_data.project_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if str(project.organization_id) != str(organization_id):
            logger.warning(
                "org_accession_create_project_org_mismatch",
                project_id=accession_data.project_id,
                project_org_id=project.organization_id,
                organization_id=organization_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project does not belong to this organization"
            )

        # Add project association
        db.execute(
            projects_accessions.insert().values(
                project_id=accession_data.project_id,
                accession_id=new_accession.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        db.commit()

    logger.info(
        "org_accession_create_success",
        accession_id=new_accession.id,
        organization_id=organization_id,
        species_id=accession_data.species_id,
        project_id=accession_data.project_id
    )

    return new_accession


@router.patch("/{accession_id}", response_model=AccessionResponse)
def update_accession_for_org(
    organization_id: UUID,
    accession_id: UUID,
    accession_update: AccessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an accession (admin only)."""
    logger.info(
        "org_accession_update_started",
        organization_id=organization_id,
        accession_id=accession_id,
        updated_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "org_accession_update_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update accessions in this organization"
        )

    # Get the accession
    accession = db.query(Accession).filter(Accession.id == accession_id).first()
    if not accession:
        logger.warning("org_accession_update_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found"
        )

    # Verify accession's species belongs to this organization
    species = db.query(Species).filter(Species.id == accession.species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found in this organization"
        )

    # Update fields (exclude project_id as it's handled separately)
    update_data = accession_update.model_dump(exclude_unset=True, exclude={'project_id'})
    for field, value in update_data.items():
        setattr(accession, field, value)

    db.commit()
    db.refresh(accession)

    # Handle project association update if project_id is in the update
    if 'project_id' in accession_update.model_dump(exclude_unset=True):
        # Remove all existing project associations
        db.execute(
            projects_accessions.delete().where(
                projects_accessions.c.accession_id == accession_id
            )
        )

        # Add new project association if provided
        if accession_update.project_id:
            # Verify project exists and belongs to this organization
            project = db.query(Project).filter(Project.id == accession_update.project_id).first()
            if not project:
                logger.warning("org_accession_update_project_not_found", project_id=accession_update.project_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

            if str(project.organization_id) != str(organization_id):
                logger.warning(
                    "org_accession_update_project_org_mismatch",
                    project_id=accession_update.project_id,
                    project_org_id=project.organization_id,
                    organization_id=organization_id
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project does not belong to this organization"
                )

            # Add project association
            db.execute(
                projects_accessions.insert().values(
                    project_id=accession_update.project_id,
                    accession_id=accession_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )

        db.commit()

    logger.info("org_accession_update_success", accession_id=accession_id)

    return accession


@router.delete("/{accession_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_accession_for_org(
    organization_id: UUID,
    accession_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an accession (admin only)."""
    logger.info(
        "org_accession_delete_started",
        organization_id=organization_id,
        accession_id=accession_id,
        deleted_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "org_accession_delete_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete accessions in this organization"
        )

    # Get the accession
    accession = db.query(Accession).filter(Accession.id == accession_id).first()
    if not accession:
        logger.warning("org_accession_delete_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found"
        )

    # Verify accession's species belongs to this organization
    species = db.query(Species).filter(Species.id == accession.species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found in this organization"
        )

    # Delete the accession
    db.delete(accession)
    db.commit()

    logger.info("org_accession_delete_success", accession_id=accession_id)

    return None
