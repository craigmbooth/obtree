#!/usr/bin/env python3
"""
Script to create a site admin user.
Run with: poetry run python scripts/seed_admin.py
"""
import sys
from getpass import getpass

# Add parent directory to path to import app modules
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash


def create_site_admin():
    """Create a site admin user interactively."""
    print("=== Create Site Admin User ===\n")

    # Get email
    email = input("Email: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        return

    # Get password
    password = getpass("Password: ")
    if not password:
        print("Error: Password cannot be empty")
        return

    password_confirm = getpass("Confirm Password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        return

    # Create database session
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"\nError: User with email '{email}' already exists")
            if existing_user.is_site_admin:
                print("(User is already a site admin)")
            else:
                # Optionally promote existing user to site admin
                promote = input("Promote existing user to site admin? (y/n): ").strip().lower()
                if promote == 'y':
                    existing_user.is_site_admin = True
                    db.commit()
                    print(f"\n✓ User '{email}' promoted to site admin")
                else:
                    print("Operation cancelled")
            return

        # Create new site admin user
        hashed_password = get_password_hash(password)
        new_admin = User(
            email=email,
            hashed_password=hashed_password,
            is_site_admin=True
        )
        db.add(new_admin)
        db.commit()

        print(f"\n✓ Site admin user created successfully!")
        print(f"  Email: {email}")
        print(f"  Site Admin: Yes")

    except Exception as e:
        db.rollback()
        print(f"\nError creating admin user: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_site_admin()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
