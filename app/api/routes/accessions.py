from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import can_manage_organization, is_org_member
from app.core.field_validation import validate_field_value, validate_required_fields, get_project_fields
from app.logging_config import get_logger
from app.models import User, Accession, Species, Organization, Project, projects_accessions, ProjectAccessionField, AccessionFieldValue
from app.schemas.accession import AccessionCreate, AccessionUpdate, AccessionResponse, AccessionWithSpeciesResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=AccessionResponse, status_code=status.HTTP_201_CREATED)
def create_accession(
    organization_id: UUID,
    species_id: UUID,
    accession_data: AccessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new accession for a species (admin only)."""
    logger.info(
        "accession_create_started",
        organization_id=organization_id,
        species_id=species_id,
        accession=accession_data.accession,
        created_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "accession_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create accessions in this organization"
        )

    # Verify species exists and belongs to this organization
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        logger.warning("accession_create_species_not_found", species_id=species_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )

    if str(species.organization_id) != str(organization_id):
        logger.warning(
            "accession_create_species_org_mismatch",
            species_id=species_id,
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
        species_id=species_id,
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
            logger.warning("accession_create_project_not_found", project_id=accession_data.project_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if str(project.organization_id) != str(organization_id):
            logger.warning(
                "accession_create_project_org_mismatch",
                project_id=accession_data.project_id,
                project_org_id=project.organization_id,
                organization_id=organization_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project does not belong to this organization"
            )

        # Add project association
        from datetime import datetime
        db.execute(
            projects_accessions.insert().values(
                project_id=accession_data.project_id,
                accession_id=new_accession.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        db.commit()

        # Handle custom field values if provided
        if accession_data.field_values:
            # Validate required fields
            field_values_dicts = [{"field_id": fv.field_id, "value": fv.value} for fv in accession_data.field_values]
            validate_required_fields(db, accession_data.project_id, field_values_dicts)

            # Create field values
            for field_value_data in accession_data.field_values:
                # Get field definition
                field = db.query(ProjectAccessionField).filter(
                    ProjectAccessionField.id == field_value_data.field_id,
                    ProjectAccessionField.project_id == accession_data.project_id,
                    ProjectAccessionField.is_deleted == False
                ).first()

                if not field:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field {field_value_data.field_id} not found in this project"
                    )

                # Validate value
                validate_field_value(field, field_value_data.value)

                # Create field value record
                from app.models.project_accession_field import FieldType
                new_field_value = AccessionFieldValue(
                    accession_id=new_accession.id,
                    field_id=field.id,
                    value_string=str(field_value_data.value) if field.field_type == FieldType.STRING else None,
                    value_number=field_value_data.value if field.field_type == FieldType.NUMBER else None
                )
                db.add(new_field_value)

            db.commit()

    logger.info(
        "accession_create_success",
        accession_id=new_accession.id,
        organization_id=organization_id,
        species_id=species_id,
        project_id=accession_data.project_id
    )

    return new_accession


@router.get("", response_model=List[AccessionWithSpeciesResponse])
def list_accessions(
    organization_id: UUID,
    species_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all accessions for a species (all org members can view)."""
    logger.info(
        "accession_list_started",
        organization_id=organization_id,
        species_id=species_id,
        user_id=current_user.id
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "accession_list_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view accessions in this organization"
        )

    # Verify species exists and belongs to this organization
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        logger.warning("accession_list_species_not_found", species_id=species_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found"
        )

    if str(species.organization_id) != str(organization_id):
        logger.warning(
            "accession_list_species_org_mismatch",
            species_id=species_id,
            species_org_id=species.organization_id,
            organization_id=organization_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Species does not belong to this organization"
        )

    # Get all accessions for this species
    accessions = db.query(Accession).filter(Accession.species_id == species_id).all()

    # Transform to include species and project information
    from app.schemas.accession_field_value import AccessionFieldValueResponse
    from datetime import datetime
    result = []
    for accession in accessions:
        # Get project association if exists
        project_id = None
        project_title = None
        if accession.projects:
            # Get the first project (accessions can have multiple projects, but we'll show the first one)
            first_project = accession.projects[0]
            project_id = first_project.id
            project_title = first_project.title

        # Get all project fields and merge with accession values
        field_values = []
        if project_id:
            # Get all fields for this project
            project_fields = get_project_fields(db, project_id, include_deleted=False)

            # Create a map of existing field values
            existing_values = {str(fv.field_id): fv for fv in accession.field_values}

            # For each project field, include it with value if exists, or null if not
            for field in project_fields:
                field_id_str = str(field.id)
                if field_id_str in existing_values:
                    fv = existing_values[field_id_str]
                    field_values.append(AccessionFieldValueResponse(
                        id=fv.id,
                        accession_id=fv.accession_id,
                        field_id=fv.field_id,
                        field_name=fv.field_name,
                        field_type=fv.field_type,
                        value=fv.value,
                        created_at=fv.created_at,
                        updated_at=fv.updated_at
                    ))
                else:
                    # Field exists in project but no value for this accession yet
                    field_values.append(AccessionFieldValueResponse(
                        id=None,
                        accession_id=accession.id,
                        field_id=field.id,
                        field_name=field.field_name,
                        field_type=field.field_type,
                        value=None,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ))
        else:
            # No project, just include existing field values
            for fv in accession.field_values:
                field_values.append(AccessionFieldValueResponse(
                    id=fv.id,
                    accession_id=fv.accession_id,
                    field_id=fv.field_id,
                    field_name=fv.field_name,
                    field_type=fv.field_type,
                    value=fv.value,
                    created_at=fv.created_at,
                    updated_at=fv.updated_at
                ))

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
            project_title=project_title,
            field_values=field_values
        ))

    logger.info(
        "accession_list_success",
        organization_id=organization_id,
        species_id=species_id,
        count=len(result)
    )

    return result


@router.get("/{accession_id}", response_model=AccessionWithSpeciesResponse)
def get_accession(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single accession by ID (all org members can view)."""
    logger.info(
        "accession_get_started",
        organization_id=organization_id,
        species_id=species_id,
        accession_id=accession_id,
        user_id=current_user.id
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "accession_get_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view accessions in this organization"
        )

    # Get the accession
    accession = db.query(Accession).filter(Accession.id == accession_id).first()
    if not accession:
        logger.warning("accession_get_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found"
        )

    # Verify species
    if str(accession.species_id) != str(species_id):
        logger.warning(
            "accession_get_species_mismatch",
            accession_id=accession_id,
            accession_species_id=accession.species_id,
            requested_species_id=species_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession does not belong to this species"
        )

    # Get species
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found in this organization"
        )

    # Get project association if exists
    project_id = None
    project_title = None
    if accession.projects:
        first_project = accession.projects[0]
        project_id = first_project.id
        project_title = first_project.title

    # Get all project fields and merge with accession values
    from app.schemas.accession_field_value import AccessionFieldValueResponse
    from datetime import datetime
    field_values = []

    if project_id:
        # Get all fields for this project
        project_fields = get_project_fields(db, project_id, include_deleted=False)

        # Create a map of existing field values
        existing_values = {str(fv.field_id): fv for fv in accession.field_values}

        # For each project field, include it with value if exists, or null if not
        for field in project_fields:
            field_id_str = str(field.id)
            if field_id_str in existing_values:
                fv = existing_values[field_id_str]
                field_values.append(AccessionFieldValueResponse(
                    id=fv.id,
                    accession_id=fv.accession_id,
                    field_id=fv.field_id,
                    field_name=fv.field_name,
                    field_type=fv.field_type,
                    value=fv.value,
                    created_at=fv.created_at,
                    updated_at=fv.updated_at
                ))
            else:
                # Field exists in project but no value for this accession yet
                field_values.append(AccessionFieldValueResponse(
                    id=None,
                    accession_id=accession.id,
                    field_id=field.id,
                    field_name=field.field_name,
                    field_type=field.field_type,
                    value=None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ))
    else:
        # No project, just include existing field values
        for fv in accession.field_values:
            field_values.append(AccessionFieldValueResponse(
                id=fv.id,
                accession_id=fv.accession_id,
                field_id=fv.field_id,
                field_name=fv.field_name,
                field_type=fv.field_type,
                value=fv.value,
                created_at=fv.created_at,
                updated_at=fv.updated_at
            ))

    # Transform to include species and project information
    result = AccessionWithSpeciesResponse(
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
        project_title=project_title,
        field_values=field_values
    )

    logger.info("accession_get_success", accession_id=accession_id)

    return result


@router.patch("/{accession_id}", response_model=AccessionResponse)
def update_accession(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    accession_update: AccessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an accession (admin only)."""
    logger.info(
        "accession_update_started",
        organization_id=organization_id,
        species_id=species_id,
        accession_id=accession_id,
        updated_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "accession_update_forbidden",
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
        logger.warning("accession_update_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found"
        )

    # Verify species
    if str(accession.species_id) != str(species_id):
        logger.warning(
            "accession_update_species_mismatch",
            accession_id=accession_id,
            accession_species_id=accession.species_id,
            requested_species_id=species_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession does not belong to this species"
        )

    # Verify species belongs to organization
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found in this organization"
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
                logger.warning("accession_update_project_not_found", project_id=accession_update.project_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

            if str(project.organization_id) != str(organization_id):
                logger.warning(
                    "accession_update_project_org_mismatch",
                    project_id=accession_update.project_id,
                    project_org_id=project.organization_id,
                    organization_id=organization_id
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project does not belong to this organization"
                )

            # Add project association
            from datetime import datetime
            db.execute(
                projects_accessions.insert().values(
                    project_id=accession_update.project_id,
                    accession_id=accession_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )

        db.commit()

    # Handle custom field values if provided
    if accession_update.field_values is not None:
        # Get project_id from accession
        project_id = None
        if accession.projects:
            project_id = accession.projects[0].id

        if not project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update field values for accession without project association"
            )

        # Validate required fields
        field_values_dicts = [{"field_id": fv.field_id, "value": fv.value} for fv in accession_update.field_values]
        validate_required_fields(db, project_id, field_values_dicts)

        # Delete existing field values
        db.query(AccessionFieldValue).filter(
            AccessionFieldValue.accession_id == accession_id
        ).delete()

        # Create new field values
        for field_value_data in accession_update.field_values:
            # Get field definition
            field = db.query(ProjectAccessionField).filter(
                ProjectAccessionField.id == field_value_data.field_id,
                ProjectAccessionField.project_id == project_id,
                ProjectAccessionField.is_deleted == False
            ).first()

            if not field:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field {field_value_data.field_id} not found in this project"
                )

            # Validate value
            validate_field_value(field, field_value_data.value)

            # Create field value record
            from app.models.project_accession_field import FieldType
            new_field_value = AccessionFieldValue(
                accession_id=accession_id,
                field_id=field.id,
                value_string=str(field_value_data.value) if field.field_type == FieldType.STRING else None,
                value_number=field_value_data.value if field.field_type == FieldType.NUMBER else None
            )
            db.add(new_field_value)

        db.commit()

    logger.info("accession_update_success", accession_id=accession_id)

    return accession


@router.delete("/{accession_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_accession(
    organization_id: UUID,
    species_id: UUID,
    accession_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an accession (admin only)."""
    logger.info(
        "accession_delete_started",
        organization_id=organization_id,
        species_id=species_id,
        accession_id=accession_id,
        deleted_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "accession_delete_forbidden",
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
        logger.warning("accession_delete_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found"
        )

    # Verify species
    if str(accession.species_id) != str(species_id):
        logger.warning(
            "accession_delete_species_mismatch",
            accession_id=accession_id,
            accession_species_id=accession.species_id,
            requested_species_id=species_id
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accession does not belong to this species"
        )

    # Verify species belongs to organization
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species or str(species.organization_id) != str(organization_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Species not found in this organization"
        )

    # Delete the accession
    db.delete(accession)
    db.commit()

    logger.info("accession_delete_success", accession_id=accession_id)

    return None
