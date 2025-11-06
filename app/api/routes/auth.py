from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Invite, OrganizationMembership, MembershipStatus
from app.schemas import UserCreate, UserLogin, UserResponse, Token
from app.core.security import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user, get_current_site_admin
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user, optionally with an invite code."""
    logger.info("signup_started", email=user_data.email, has_invite=bool(user_data.invite_code))

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning("signup_failed_duplicate_email", email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate invite code if provided
    invite = None
    if user_data.invite_code:
        logger.info("validating_invite_code", invite_code=user_data.invite_code)
        invite = db.query(Invite).filter(Invite.uuid == user_data.invite_code).first()
        if not invite:
            logger.warning("signup_failed_invalid_invite", invite_code=user_data.invite_code)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid invite code"
            )
        if not invite.is_valid:
            logger.warning(
                "signup_failed_expired_invite",
                invite_code=user_data.invite_code,
                expires_at=invite.expires_at.isoformat(),
                is_active=invite.is_active,
                used_by=invite.used_by
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite code has expired or already been used"
            )
        logger.info(
            "invite_validated",
            invite_code=user_data.invite_code,
            organization_id=invite.organization_id,
            role=invite.role
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_site_admin=False
    )
    db.add(new_user)
    db.flush()  # Flush to get the user ID

    logger.info("user_created", user_id=new_user.id, email=new_user.email)

    # If invite was used, create organization membership and mark invite as used
    if invite:
        membership = OrganizationMembership(
            user_id=new_user.id,
            organization_id=invite.organization_id,
            role=invite.role,
            status=MembershipStatus.ACTIVE
        )
        db.add(membership)

        invite.used_by = new_user.id
        invite.used_at = datetime.utcnow()
        invite.is_active = False

        logger.info(
            "invite_used",
            user_id=new_user.id,
            invite_code=user_data.invite_code,
            organization_id=invite.organization_id,
            role=invite.role
        )

    db.commit()
    db.refresh(new_user)

    logger.info("signup_completed", user_id=new_user.id, email=new_user.email)
    return new_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token."""
    logger.info("login_attempt", email=form_data.username)

    # Find user by email (OAuth2PasswordRequestForm uses 'username' field)
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        logger.warning("login_failed_user_not_found", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning("login_failed_invalid_password", user_id=user.id, email=user.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    logger.info("login_successful", user_id=user.id, email=user.email, is_site_admin=user.is_site_admin)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_site_admin),
    db: Session = Depends(get_db)
):
    """
    List all users in the system (site admin only).

    Returns user data formatted for table display using the User model's table configuration.
    """
    logger.info("list_users_requested", admin_user_id=current_user.id)

    users = db.query(User).all()

    # Use the model's to_table_dict method to return only visible fields
    users_data = [user.to_table_dict() for user in users]

    logger.info("list_users_completed", user_count=len(users_data))
    return users_data
