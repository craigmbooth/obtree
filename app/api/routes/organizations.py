from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, OrganizationMembership, OrganizationRole, User
from app.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationDetailResponse,
    OrganizationMemberResponse,
)
from app.api.deps import get_current_user, get_current_site_admin
from app.core.permissions import is_org_member, can_manage_organization
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_site_admin),
    db: Session = Depends(get_db)
):
    """Create a new organization (site admin only)."""
    logger.info("organization_create_started", name=org_data.name, created_by=current_user.id)

    new_org = Organization(
        name=org_data.name,
        created_by=current_user.id
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    logger.info(
        "organization_created",
        organization_id=new_org.id,
        name=new_org.name,
        created_by=current_user.id
    )

    return new_org


@router.get("/", response_model=List[OrganizationResponse])
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all organizations the current user is a member of.

    Site admins see all organizations.
    """
    logger.info("list_organizations", user_id=current_user.id)

    if current_user.is_site_admin:
        # Site admins see all organizations
        organizations = db.query(Organization).all()
    else:
        # Regular users only see organizations they're members of
        memberships = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == current_user.id
        ).all()

        org_ids = [m.organization_id for m in memberships]
        organizations = db.query(Organization).filter(Organization.id.in_(org_ids)).all()

    logger.info(
        "organizations_listed",
        user_id=current_user.id,
        organization_count=len(organizations)
    )

    return organizations


@router.get("/{organization_id}", response_model=OrganizationDetailResponse)
def get_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organization details with members."""
    logger.info("get_organization", organization_id=organization_id, user_id=current_user.id)

    # Check if user is a member
    if not is_org_member(db, current_user, organization_id):
        logger.warning(
            "get_organization_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization"
        )

    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("organization_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Get all members (excluding site admins)
    memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == organization_id
    ).all()

    members = []
    for membership in memberships:
        user = db.query(User).filter(User.id == membership.user_id).first()
        # Don't include site admins in the member list
        if user and not user.is_site_admin:
            members.append(OrganizationMemberResponse(
                id=membership.id,
                user_id=user.id,
                email=user.email,
                role=membership.role,
                joined_at=membership.joined_at
            ))

    logger.info(
        "organization_retrieved",
        organization_id=organization_id,
        member_count=len(members)
    )

    return OrganizationDetailResponse(
        id=organization.id,
        name=organization.name,
        created_at=organization.created_at,
        created_by=organization.created_by,
        members=members
    )
