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

    # Validate that either species_id OR hybrid parents are provided
    if accession_data.is_hybrid:
        # For hybrids, require both parent species
        if not accession_data.parent_species_1_id or not accession_data.parent_species_2_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both parent species are required for hybrid accessions"
            )
    else:
        # For non-hybrids, require species_id
        if not accession_data.species_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Species ID is required for non-hybrid accessions"
            )

    # Verify species exists and belongs to this organization (if provided)
    if accession_data.species_id:
        species = db.query(Species).filter(Species.id == accession_data.species_id).first()
        if not species:
            logger.warning("accession_create_species_not_found", species_id=accession_data.species_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Species not found"
            )

        if str(species.organization_id) != str(organization_id):
            logger.warning(
                "accession_create_species_org_mismatch",
                species_id=accession_data.species_id,
                species_org_id=species.organization_id,
                organization_id=organization_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Species does not belong to this organization"
            )

    # Verify hybrid parent species exist and belong to the organization
    if accession_data.is_hybrid:
        parent_species_1 = db.query(Species).filter(
            Species.id == accession_data.parent_species_1_id,
            Species.organization_id == organization_id
        ).first()
        parent_species_2 = db.query(Species).filter(
            Species.id == accession_data.parent_species_2_id,
            Species.organization_id == organization_id
        ).first()

        if not parent_species_1 or not parent_species_2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both parent species not found in this organization"
            )

    # Create new accession
    new_accession = Accession(
        accession=accession_data.accession,
        description=accession_data.description,
        species_id=accession_data.species_id if not accession_data.is_hybrid else None,
        is_hybrid=accession_data.is_hybrid,
        parent_species_1_id=accession_data.parent_species_1_id if accession_data.is_hybrid else None,
        parent_species_2_id=accession_data.parent_species_2_id if accession_data.is_hybrid else None,
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

    # Get all accessions for this species with parent species loaded
    from sqlalchemy.orm import joinedload
    accessions = (
        db.query(Accession)
        .filter(Accession.species_id == species_id)
        .options(
            joinedload(Accession.parent_species_1),
            joinedload(Accession.parent_species_2)
        )
        .all()
    )

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

        # Count plants for this accession
        plant_count = len(accession.plants)

        result.append(AccessionWithSpeciesResponse(
            id=accession.id,
            accession=accession.accession,
            description=accession.description,
            species_id=accession.species_id,
            is_hybrid=accession.is_hybrid,
            parent_species_1_id=accession.parent_species_1_id,
            parent_species_2_id=accession.parent_species_2_id,
            parent_species_1_name=accession.parent_species_1.formatted_name if accession.parent_species_1 else None,
            parent_species_2_name=accession.parent_species_2.formatted_name if accession.parent_species_2 else None,
            hybrid_display_name=accession.hybrid_display_name,
            created_at=accession.created_at,
            created_by=accession.created_by,
            species_genus=species.genus,
            species_name=species.species_name,
            species_variety=species.variety,
            species_common_name=species.common_name,
            project_id=project_id,
            project_title=project_title,
            field_values=field_values,
            plant_count=plant_count
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

    # Get the accession with parent species loaded
    from sqlalchemy.orm import joinedload
    accession = (
        db.query(Accession)
        .filter(Accession.id == accession_id)
        .options(
            joinedload(Accession.parent_species_1),
            joinedload(Accession.parent_species_2)
        )
        .first()
    )
    if not accession:
        logger.warning("accession_get_not_found", accession_id=accession_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accession not found"
        )

    # Verify species (only for non-hybrids)
    if not accession.is_hybrid:
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

    # Get species (only if not hybrid)
    species = None
    if accession.species_id:
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

    # Count plants in this accession
    plant_count = len(accession.plants) if accession.plants else 0

    # Transform to include species and project information
    result = AccessionWithSpeciesResponse(
        id=accession.id,
        accession=accession.accession,
        description=accession.description,
        species_id=accession.species_id,
        is_hybrid=accession.is_hybrid,
        parent_species_1_id=accession.parent_species_1_id,
        parent_species_2_id=accession.parent_species_2_id,
        parent_species_1_name=accession.parent_species_1.formatted_name if accession.parent_species_1 else None,
        parent_species_2_name=accession.parent_species_2.formatted_name if accession.parent_species_2 else None,
        hybrid_display_name=accession.hybrid_display_name,
        created_at=accession.created_at,
        created_by=accession.created_by,
        species_genus=species.genus if species else None,
        species_name=species.species_name if species else None,
        species_variety=species.variety if species else None,
        species_common_name=species.common_name if species else None,
        project_id=project_id,
        project_title=project_title,
        plant_count=plant_count,
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

    # Verify species (only for non-hybrids)
    if not accession.is_hybrid:
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

    # Validate hybrid updates if provided
    update_data_dict = accession_update.model_dump(exclude_unset=True, exclude={'project_id', 'field_values'})

    if "is_hybrid" in update_data_dict and update_data_dict["is_hybrid"]:
        # If setting to hybrid, ensure both parent species IDs are provided
        parent_1_id = update_data_dict.get("parent_species_1_id", accession.parent_species_1_id)
        parent_2_id = update_data_dict.get("parent_species_2_id", accession.parent_species_2_id)

        if not parent_1_id or not parent_2_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both parent species are required for hybrid accessions"
            )

        # Verify parent species exist and belong to the organization
        parent_species_1 = db.query(Species).filter(
            Species.id == parent_1_id,
            Species.organization_id == organization_id
        ).first()
        parent_species_2 = db.query(Species).filter(
            Species.id == parent_2_id,
            Species.organization_id == organization_id
        ).first()

        if not parent_species_1 or not parent_species_2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both parent species not found in this organization"
            )

    # Update fields (exclude project_id and field_values as they're handled separately)
    for field, value in update_data_dict.items():
        setattr(accession, field, value)

    # Clear parent species if is_hybrid is set to False
    if "is_hybrid" in update_data_dict and not update_data_dict["is_hybrid"]:
        accession.parent_species_1_id = None
        accession.parent_species_2_id = None

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
