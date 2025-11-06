from sqlalchemy.orm import Session
from app.models import OrganizationMembership, OrganizationRole, User


def is_site_admin(user: User) -> bool:
    """Check if user is a site admin."""
    return user.is_site_admin


def is_org_admin(db: Session, user: User, organization_id: int) -> bool:
    """Check if user is an admin of the specified organization."""
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.role == OrganizationRole.ADMIN
    ).first()
    return membership is not None


def is_org_member(db: Session, user: User, organization_id: int) -> bool:
    """Check if user is a member of the specified organization.

    Site admins are considered members of all organizations.
    """
    if is_site_admin(user):
        return True

    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.organization_id == organization_id
    ).first()
    return membership is not None


def can_manage_organization(db: Session, user: User, organization_id: int) -> bool:
    """Check if user can manage an organization (site admin or org admin)."""
    return is_site_admin(user) or is_org_admin(db, user, organization_id)
