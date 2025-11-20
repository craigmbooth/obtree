#!/usr/bin/env python3
"""
Script to create a site admin user.

Usage:
  Interactive mode (local):
    poetry run python scripts/create_admin.py

  Environment variable mode (production):
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secure_password \
    poetry run python scripts/create_admin.py --from-env

  One-time bootstrap (creates admin only if no users exist):
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secure_password \
    poetry run python scripts/create_admin.py --bootstrap
"""
import sys
import os
import argparse
from getpass import getpass

# Add parent directory to path to import app modules
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash
from app.logging_config import get_logger

logger = get_logger(__name__)


def create_site_admin(email: str, password: str, db) -> bool:
    """
    Create a site admin user.

    Args:
        email: Admin email address
        password: Admin password (will be hashed)
        db: Database session

    Returns:
        True if created successfully, False otherwise
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.warning("admin_create_user_exists", email=email, is_admin=existing_user.is_site_admin)
            if existing_user.is_site_admin:
                print(f"User '{email}' already exists and is a site admin")
                return False
            else:
                # Promote existing user to site admin
                existing_user.is_site_admin = True
                db.commit()
                logger.info("admin_promoted", email=email)
                print(f"✓ User '{email}' promoted to site admin")
                return True

        # Create new site admin user
        hashed_password = get_password_hash(password)
        new_admin = User(
            email=email,
            hashed_password=hashed_password,
            is_site_admin=True
        )
        db.add(new_admin)
        db.commit()

        logger.info("admin_created", email=email)
        print(f"✓ Site admin user created successfully!")
        print(f"  Email: {email}")
        return True

    except Exception as e:
        db.rollback()
        logger.error("admin_create_failed", email=email, error=str(e))
        print(f"Error creating admin user: {e}")
        return False


def interactive_mode():
    """Create admin user interactively with prompts."""
    print("=== Create Site Admin User ===\n")

    # Get email
    email = input("Email: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        return False

    # Get password
    password = getpass("Password: ")
    if not password:
        print("Error: Password cannot be empty")
        return False

    password_confirm = getpass("Confirm Password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        return False

    # Create database session
    db = SessionLocal()
    try:
        return create_site_admin(email, password, db)
    finally:
        db.close()


def env_mode():
    """Create admin user from environment variables."""
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not email or not password:
        logger.error("admin_create_missing_env", has_email=bool(email), has_password=bool(password))
        print("Error: ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set")
        return False

    if len(password) < 8:
        logger.error("admin_create_weak_password", email=email)
        print("Error: Password must be at least 8 characters")
        return False

    db = SessionLocal()
    try:
        return create_site_admin(email, password, db)
    finally:
        db.close()


def bootstrap_mode():
    """
    Bootstrap mode: Create admin only if no users exist yet.
    This is safe to run on every deployment.
    """
    db = SessionLocal()
    try:
        # Check if any users exist
        user_count = db.query(User).count()

        if user_count > 0:
            logger.info("bootstrap_skipped", user_count=user_count)
            print(f"Bootstrap skipped: {user_count} user(s) already exist")
            return True

        logger.info("bootstrap_started")
        print("No users found. Creating initial admin user...")

        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")

        if not email or not password:
            logger.error("bootstrap_missing_env")
            print("Error: ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set for bootstrap")
            return False

        if len(password) < 8:
            logger.error("bootstrap_weak_password")
            print("Error: Password must be at least 8 characters")
            return False

        return create_site_admin(email, password, db)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Create site admin user")
    parser.add_argument(
        "--from-env",
        action="store_true",
        help="Read credentials from ADMIN_EMAIL and ADMIN_PASSWORD environment variables"
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Bootstrap mode: only create admin if no users exist (safe for automated deployment)"
    )

    args = parser.parse_args()

    try:
        if args.bootstrap:
            success = bootstrap_mode()
        elif args.from_env:
            success = env_mode()
        else:
            success = interactive_mode()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error("admin_create_exception", error=str(e))
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
