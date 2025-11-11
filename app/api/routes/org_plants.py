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
from app.core.permissions import is_org_member
from app.logging_config import get_logger
from app.models import Accession, Plant, Species, User
from app.schemas.plant import PlantWithDetailsResponse
from app.schemas.plant_field_value import PlantFieldValueResponse

logger = get_logger(__name__)
router = APIRouter()


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

    # Get the plant with joined accession and species
    plant = (
        db.query(Plant)
        .filter(Plant.id == plant_id)
        .options(joinedload(Plant.accession).joinedload(Accession.species))
        .first()
    )

    if not plant:
        logger.warning("org_plant_get_not_found", plant_id=plant_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found"
        )

    # Verify species belongs to organization
    if str(plant.accession.species.organization_id) != str(organization_id):
        logger.warning(
            "org_plant_get_org_mismatch",
            plant_id=plant_id,
            species_org_id=plant.accession.species.organization_id,
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

    # Build the detailed response
    result = PlantWithDetailsResponse(
        id=plant.id,
        plant_id=plant.plant_id,
        accession_id=plant.accession_id,
        created_at=plant.created_at,
        created_by=plant.created_by,
        accession=plant.accession.accession,
        species_id=plant.accession.species.id,
        species_genus=plant.accession.species.genus,
        species_name=plant.accession.species.species_name,
        species_variety=plant.accession.species.variety,
        species_common_name=plant.accession.species.common_name,
        project_id=project_id,
        project_title=project_title,
        field_values=field_values,
    )

    logger.info("org_plant_get_success", plant_id=plant_id)

    return result
