from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Invite, InviteType, Organization, User
from app.schemas import InviteCreate, SiteAdminInviteCreate, InviteResponse, InviteValidateResponse
from app.api.deps import get_current_user, get_current_site_admin
from app.core.permissions import can_manage_organization
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def create_invite(
    invite_data: InviteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new invite for an organization (site admin or org admin only)."""
    logger.info(
        "invite_create_started",
        organization_id=invite_data.organization_id,
        role=invite_data.role.value,
        created_by=current_user.id
    )

    # Check if organization exists
    organization = db.query(Organization).filter(
        Organization.id == invite_data.organization_id
    ).first()
    if not organization:
        logger.warning("invite_create_failed_org_not_found", organization_id=invite_data.organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user can manage this organization
    if not can_manage_organization(db, current_user, invite_data.organization_id):
        logger.warning(
            "invite_create_forbidden",
            organization_id=invite_data.organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create invites for this organization"
        )

    # Create invite
    new_invite = Invite(
        invite_type=InviteType.ORGANIZATION,
        organization_id=invite_data.organization_id,
        role=invite_data.role.value,
        created_by=current_user.id
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)

    logger.info(
        "invite_created",
        invite_id=new_invite.id,
        invite_uuid=new_invite.uuid,
        organization_id=new_invite.organization_id,
        role=new_invite.role,
        expires_at=new_invite.expires_at.isoformat()
    )

    return new_invite


@router.get("/organization/{organization_id}", response_model=List[InviteResponse])
def list_organization_invites(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active invites for an organization (site admin or org admin only)."""
    logger.info("list_invites", organization_id=organization_id, user_id=current_user.id)

    # Check if organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        logger.warning("list_invites_org_not_found", organization_id=organization_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if user can manage this organization
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning(
            "list_invites_forbidden",
            organization_id=organization_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view invites for this organization"
        )

    # Get all active invites
    invites = db.query(Invite).filter(
        Invite.organization_id == organization_id,
        Invite.is_active == True
    ).all()

    logger.info("invites_listed", organization_id=organization_id, invite_count=len(invites))

    return invites


@router.post("/site-admin", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def create_site_admin_invite(
    invite_data: SiteAdminInviteCreate,
    current_user: User = Depends(get_current_site_admin),
    db: Session = Depends(get_db)
):
    """Create a new site admin invite (site admin only).

    Site admin invites expire after 24 hours for security purposes.
    """
    from datetime import datetime, timedelta

    logger.info(
        "site_admin_invite_create_started",
        created_by=current_user.id
    )

    # Create invite with 24-hour expiration for security
    new_invite = Invite(
        invite_type=InviteType.SITE_ADMIN,
        organization_id=None,
        role="SITE_ADMIN",
        created_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)

    logger.info(
        "site_admin_invite_created",
        invite_id=new_invite.id,
        invite_uuid=new_invite.uuid,
        expires_at=new_invite.expires_at.isoformat()
    )

    return new_invite


@router.get("/site-admin/list", response_model=List[InviteResponse])
def list_site_admin_invites(
    current_user: User = Depends(get_current_site_admin),
    db: Session = Depends(get_db)
):
    """List all active site admin invites (site admin only)."""
    logger.info("list_site_admin_invites", user_id=current_user.id)

    # Get all active site admin invites
    invites = db.query(Invite).filter(
        Invite.invite_type == InviteType.SITE_ADMIN,
        Invite.is_active == True
    ).all()

    logger.info("site_admin_invites_listed", invite_count=len(invites))

    return invites


@router.get("/validate/{invite_uuid}", response_model=InviteValidateResponse)
def validate_invite(invite_uuid: str, db: Session = Depends(get_db)):
    """Validate an invite code (public endpoint)."""
    logger.info("validate_invite", invite_uuid=invite_uuid)

    invite = db.query(Invite).filter(Invite.uuid == invite_uuid).first()

    if not invite:
        logger.info("invite_validation_failed_not_found", invite_uuid=invite_uuid)
        return InviteValidateResponse(
            valid=False,
            message="Invite not found"
        )

    if not invite.is_valid:
        logger.info(
            "invite_validation_failed_expired",
            invite_uuid=invite_uuid,
            expires_at=invite.expires_at.isoformat(),
            is_active=invite.is_active,
            used_by=invite.used_by
        )
        return InviteValidateResponse(
            valid=False,
            message="Invite has expired or already been used"
        )

    # Handle site admin invites differently
    if invite.invite_type == InviteType.SITE_ADMIN:
        logger.info(
            "site_admin_invite_validated_success",
            invite_uuid=invite_uuid,
            role=invite.role
        )
        return InviteValidateResponse(
            valid=True,
            invite_type=invite.invite_type.value,
            organization_name=None,
            role=invite.role,
            expires_at=invite.expires_at,
            message="Site admin invite is valid"
        )

    # Handle organization invites
    organization = db.query(Organization).filter(
        Organization.id == invite.organization_id
    ).first()

    logger.info(
        "invite_validated_success",
        invite_uuid=invite_uuid,
        organization_id=invite.organization_id,
        role=invite.role
    )

    return InviteValidateResponse(
        valid=True,
        invite_type=invite.invite_type.value,
        organization_name=organization.name if organization else None,
        role=invite.role,
        expires_at=invite.expires_at,
        message="Invite is valid"
    )


@router.delete("/{invite_uuid}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invite(
    invite_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an invite (site admin or org admin only)."""
    logger.info("revoke_invite_started", invite_uuid=invite_uuid, user_id=current_user.id)

    # Find the invite
    invite = db.query(Invite).filter(Invite.uuid == invite_uuid).first()
    if not invite:
        logger.warning("revoke_invite_not_found", invite_uuid=invite_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )

    # Check if user can revoke this invite
    if invite.invite_type == InviteType.SITE_ADMIN:
        # Site admin invites can only be revoked by site admins
        if not current_user.is_site_admin:
            logger.warning(
                "revoke_invite_forbidden",
                invite_uuid=invite_uuid,
                invite_type=invite.invite_type.value,
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only site admins can revoke site admin invites"
            )
    else:
        # Organization invites can be revoked by site admins or org admins
        if not can_manage_organization(db, current_user, invite.organization_id):
            logger.warning(
                "revoke_invite_forbidden",
                invite_uuid=invite_uuid,
                organization_id=invite.organization_id,
                user_id=current_user.id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to revoke this invite"
            )

    # Revoke the invite by setting is_active to False
    invite.is_active = False
    db.commit()

    logger.info(
        "invite_revoked",
        invite_uuid=invite_uuid,
        organization_id=invite.organization_id,
        revoked_by=current_user.id
    )

    return None
