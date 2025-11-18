from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, Project, ProjectStatus, User, Accession, Species
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    AccessionWithSpeciesResponse,
)
from app.api.deps import get_current_user
from app.core.permissions import is_org_member, can_manage_organization
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    organization_id: UUID,
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project in an organization (admin only)."""
    logger.info(
        "project_create_started",
        organization_id=organization_id,
        title=project_data.title,
        created_by=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "project_create_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can create projects"
        )

    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("organization_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    new_project = Project(
        title=project_data.title,
        description=project_data.description,
        organization_id=organization_id,
        created_by=current_user.id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    logger.info(
        "project_created",
        project_id=new_project.id,
        title=new_project.title,
        organization_id=organization_id,
        created_by=current_user.id
    )

    return new_project


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List projects in an organization based on user role.

    Regular users: only active projects
    Org admins: active and archived projects
    Site admins: all projects including deleted
    """
    logger.info("list_projects", organization_id=organization_id, user_id=current_user.id)

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "list_projects_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Filter projects based on user role
    query = db.query(Project).filter(Project.organization_id == organization_id)

    is_site_admin = current_user.is_site_admin
    is_org_admin = can_manage_organization(db, current_user, organization_id)

    if is_site_admin:
        # Site admins see all projects
        pass
    elif is_org_admin:
        # Org admins see active and archived projects
        query = query.filter(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED]))
    else:
        # Regular users see only active projects
        query = query.filter(Project.status == ProjectStatus.ACTIVE)

    projects = query.all()

    # Build response with accession counts
    from app.schemas.project import ProjectResponse
    result = []
    for project in projects:
        # Count accessions for this project
        accession_count = len(project.accessions)

        result.append(ProjectResponse(
            id=project.id,
            title=project.title,
            description=project.description,
            organization_id=project.organization_id,
            status=project.status,
            created_at=project.created_at,
            created_by=project.created_by,
            accession_count=accession_count
        ))

    logger.info(
        "projects_listed",
        organization_id=organization_id,
        project_count=len(result)
    )

    return result


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    organization_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project."""
    logger.info(
        "get_project",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_project_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()

    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Count accessions for this project
    accession_count = len(project.accessions)

    logger.info("project_retrieved", project_id=project_id)

    from app.schemas.project import ProjectResponse
    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        organization_id=project.organization_id,
        status=project.status,
        created_at=project.created_at,
        created_by=project.created_by,
        accession_count=accession_count
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    organization_id: UUID,
    project_id: UUID,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project (admin only)."""
    logger.info(
        "update_project_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "update_project_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can update projects"
        )

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()

    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Update fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    logger.info("project_updated", project_id=project_id)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    organization_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a project (admin only) - sets status to deleted."""
    logger.info(
        "delete_project_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "delete_project_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can delete projects"
        )

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()

    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Soft delete - set status to deleted
    project.status = ProjectStatus.DELETED
    db.commit()

    logger.info("project_deleted", project_id=project_id)


@router.post("/{project_id}/archive", response_model=ProjectResponse)
def archive_project(
    organization_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive a project (admin only)."""
    logger.info(
        "archive_project_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "archive_project_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can archive projects"
        )

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()

    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    project.status = ProjectStatus.ARCHIVED
    db.commit()
    db.refresh(project)

    logger.info("project_archived", project_id=project_id)
    return project


@router.post("/{project_id}/unarchive", response_model=ProjectResponse)
def unarchive_project(
    organization_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unarchive a project (admin only)."""
    logger.info(
        "unarchive_project_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Check if user can manage the organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "unarchive_project_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization admins can unarchive projects"
        )

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()

    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    project.status = ProjectStatus.ACTIVE
    db.commit()
    db.refresh(project)

    logger.info("project_unarchived", project_id=project_id)
    return project


@router.post("/{project_id}/undelete", response_model=ProjectResponse)
def undelete_project(
    organization_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Undelete a project (site admin only)."""
    logger.info(
        "undelete_project_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Only site admins can undelete
    if not current_user.is_site_admin:
        logger.warning(
            "undelete_project_forbidden",
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only site admins can undelete projects"
        )

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()

    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    project.status = ProjectStatus.ACTIVE
    db.commit()
    db.refresh(project)

    logger.info("project_undeleted", project_id=project_id)
    return project


@router.get("/{project_id}/accessions", response_model=List[AccessionWithSpeciesResponse])
def get_project_accessions(
    organization_id: UUID,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all accessions associated with a project.

    Args:
        organization_id: Organization UUID.
        project_id: Project UUID.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        List[AccessionWithSpeciesResponse]: List of accessions with species info.

    Raises:
        HTTPException: If user is not a member or project not found.
    """
    logger.info(
        "get_project_accessions_started",
        organization_id=organization_id,
        project_id=project_id,
        user_id=current_user.id
    )

    # Check if user is a member of the organization
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_project_accessions_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    # Verify project exists and belongs to organization
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization_id
    ).first()

    if not project:
        logger.warning("project_not_found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Get accessions with species information via the many-to-many relationship
    accessions = (
        db.query(Accession, Species)
        .join(Species, Accession.species_id == Species.id)
        .filter(Accession.projects.any(id=project_id))
        .order_by(Accession.accession)
        .all()
    )

    # Build response with species information
    result = []
    for accession, species in accessions:
        # Count plants for this accession
        plant_count = len(accession.plants)

        accession_data = AccessionWithSpeciesResponse(
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
            project_title=project.title,
            field_values=[],
            plant_count=plant_count
        )
        result.append(accession_data)

    logger.info(
        "project_accessions_retrieved",
        project_id=project_id,
        accession_count=len(result)
    )

    return result
