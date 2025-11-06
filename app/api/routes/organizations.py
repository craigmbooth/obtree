from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, OrganizationMembership, OrganizationRole, User
from app.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationDetailResponse,
    OrganizationMemberResponse,
    OrganizationMemberRoleUpdate,
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
        # Regular users only see organizations they're active members of (not removed)
        memberships = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.removed_at.is_(None)
        ).all()

        org_ids = [m.organization_id for m in memberships]
        organizations = db.query(Organization).filter(Organization.id.in_(org_ids)).all()

    # Calculate member counts for each organization
    result = []
    for org in organizations:
        # Only count active memberships (not removed)
        memberships = db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id == org.id,
            OrganizationMembership.removed_at.is_(None)
        ).all()

        # Count total members (excluding site admins)
        member_user_ids = [m.user_id for m in memberships]
        non_site_admin_users = db.query(User).filter(
            User.id.in_(member_user_ids),
            User.is_site_admin == False
        ).all()

        user_count = len(non_site_admin_users)

        # Count admins (excluding site admins)
        admin_count = sum(
            1 for m in memberships
            if m.role == OrganizationRole.ADMIN and any(u.id == m.user_id for u in non_site_admin_users)
        )

        result.append(OrganizationResponse(
            id=org.id,
            name=org.name,
            description=org.description,
            created_at=org.created_at,
            created_by=org.created_by,
            user_count=user_count,
            admin_count=admin_count
        ))

    logger.info(
        "organizations_listed",
        user_id=current_user.id,
        organization_count=len(result)
    )

    return result


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
            status = "Removed" if membership.removed_at else "Active"
            members.append(OrganizationMemberResponse(
                id=membership.id,
                user_id=user.id,
                email=user.email,
                role=membership.role,
                joined_at=membership.joined_at,
                removed_at=membership.removed_at,
                status=status
            ))

    logger.info(
        "organization_retrieved",
        organization_id=organization_id,
        member_count=len(members)
    )

    return OrganizationDetailResponse(
        id=organization.id,
        name=organization.name,
        description=organization.description,
        created_at=organization.created_at,
        created_by=organization.created_by,
        members=members
    )


@router.delete("/{organization_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    organization_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from an organization (site admin or org admin only)."""
    logger.info(
        "remove_member_started",
        organization_id=organization_id,
        user_id=user_id,
        removed_by=current_user.id
    )

    # Check if organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("remove_member_org_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user can manage this organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "remove_member_forbidden",
            organization_id=organization_id,
            user_id=user_id,
            removed_by=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to remove members from this organization"
        )

    # Find the membership
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.user_id == user_id
    ).first()

    if not membership:
        logger.warning(
            "remove_member_not_found",
            organization_id=organization_id,
            user_id=user_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization"
        )

    # Soft delete the membership by setting removed_at
    from datetime import datetime
    membership.removed_at = datetime.utcnow()
    db.commit()

    logger.info(
        "member_removed",
        organization_id=organization_id,
        user_id=user_id,
        removed_by=current_user.id
    )

    return None


@router.post("/{organization_id}/members/{user_id}/reactivate", response_model=OrganizationMemberResponse)
def reactivate_member(
    organization_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reactivate a removed member (site admin or org admin only)."""
    logger.info(
        "reactivate_member_started",
        organization_id=organization_id,
        user_id=user_id,
        reactivated_by=current_user.id
    )

    # Check if organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("reactivate_member_org_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user can manage this organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "reactivate_member_forbidden",
            organization_id=organization_id,
            user_id=user_id,
            reactivated_by=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to manage members in this organization"
        )

    # Find the removed membership
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.removed_at.isnot(None)
    ).first()

    if not membership:
        logger.warning(
            "reactivate_member_not_found",
            organization_id=organization_id,
            user_id=user_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Removed member not found in this organization"
        )

    # Reactivate the membership
    membership.removed_at = None
    db.commit()
    db.refresh(membership)

    # Get user email for response
    user = db.query(User).filter(User.id == user_id).first()

    logger.info(
        "member_reactivated",
        organization_id=organization_id,
        user_id=user_id,
        reactivated_by=current_user.id
    )

    return OrganizationMemberResponse(
        id=membership.id,
        user_id=user.id,
        email=user.email,
        role=membership.role,
        joined_at=membership.joined_at,
        removed_at=membership.removed_at,
        status="Active"
    )


@router.patch("/{organization_id}/members/{user_id}/role", response_model=OrganizationMemberResponse)
def update_member_role(
    organization_id: UUID,
    user_id: UUID,
    role_update: OrganizationMemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a member's role in an organization (site admin or org admin only).

    Users cannot change their own role.
    """
    logger.info(
        "update_member_role_started",
        organization_id=organization_id,
        user_id=user_id,
        new_role=role_update.role,
        updated_by=current_user.id
    )

    # Check if organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("update_member_role_org_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user can manage this organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "update_member_role_forbidden",
            organization_id=organization_id,
            user_id=user_id,
            updated_by=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to manage members in this organization"
        )

    # Prevent users from changing their own role
    if user_id == current_user.id:
        logger.warning(
            "update_member_role_self_change_attempted",
            organization_id=organization_id,
            user_id=user_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot change your own role"
        )

    # Find the membership
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.removed_at.is_(None)
    ).first()

    if not membership:
        logger.warning(
            "update_member_role_not_found",
            organization_id=organization_id,
            user_id=user_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active member not found in this organization"
        )

    # Update the role
    old_role = membership.role
    membership.role = role_update.role
    db.commit()
    db.refresh(membership)

    # Get user email for response
    user = db.query(User).filter(User.id == user_id).first()

    logger.info(
        "member_role_updated",
        organization_id=organization_id,
        user_id=user_id,
        old_role=old_role,
        new_role=role_update.role,
        updated_by=current_user.id
    )

    return OrganizationMemberResponse(
        id=membership.id,
        user_id=user.id,
        email=user.email,
        role=membership.role,
        joined_at=membership.joined_at,
        removed_at=membership.removed_at,
        status="Active"
    )


@router.patch("/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: UUID,
    org_update: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an organization (site admin or org admin only)."""
    logger.info(
        "update_organization_started",
        organization_id=organization_id,
        updated_by=current_user.id
    )

    # Check if organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("update_organization_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user can manage this organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "update_organization_forbidden",
            organization_id=organization_id,
            updated_by=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this organization"
        )

    # Update fields - only update if explicitly provided in request
    update_data = org_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)

    db.commit()
    db.refresh(organization)

    logger.info(
        "organization_updated",
        organization_id=organization_id,
        updated_by=current_user.id
    )

    return organization
