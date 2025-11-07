#!/usr/bin/env python3
"""
Seed script to populate database with realistic woody plant breeding data.
Designed for Illinois region plant breeders.

Run with: poetry run python scripts/seed.py
"""
import sys
import os
import subprocess
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import User, Organization, OrganizationMembership, Project, Species, Invite
from app.models.membership import OrganizationRole
from app.models.project import ProjectStatus
from app.models.species import SpeciesStatus
from app.core.security import get_password_hash


def clear_database():
    """Clear the existing database and recreate tables."""
    print("Clearing existing database...")

    db_path = "obtree.db"

    # Remove the database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ Deleted existing database: {db_path}")

    # Run migrations to recreate tables
    print("Recreating database tables...")
    result = subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error running migrations: {result.stderr}")
        sys.exit(1)

    print("✓ Database tables recreated")


def create_users(db):
    """Create sample users for woody plant breeding program."""
    print("\nCreating users...")

    users_data = [
        {
            "email": "siteadmin@redbudsapp.com",
            "password": "siteadmin",
            "is_site_admin": True
        },
        {
            "email": "s@o.com",
            "password": "susie",
            "is_site_admin": True
        },
        {
            "email": "orgadmin@redbudsapp.com",
            "password": "orgadmin",
            "is_site_admin": False
        },
        {
            "email": "user@redbudsapp.com",
            "password": "user",
            "is_site_admin": False
        },
        {
            "email": "emily.brown@redbudsapp.com",
            "password": "password123",
            "is_site_admin": False
        },
        {
            "email": "robert.williams@redbudsapp.com",
            "password": "password123",
            "is_site_admin": False
        }
    ]

    users = []
    for user_data in users_data:
        user = User(
            email=user_data["email"],
            hashed_password=get_password_hash(user_data["password"]),
            is_site_admin=user_data["is_site_admin"],
            created_at=datetime.utcnow() - timedelta(days=365)
        )
        db.add(user)
        users.append(user)

    db.commit()
    print(f"✓ Created {len(users)} users")
    return users


def create_organizations(db, users):
    """Create organizations for breeding programs."""
    print("\nCreating organizations...")

    orgs_data = [
        {
            "name": "Morton Arboretum",
            "description": "Research-focused arboretum dedicated to the cultivation and conservation of trees and woody plants, with breeding programs for disease resistance and climate adaptation.",
            "creator_idx": 0  # admin user
        },
        {
            "name": "New Plant Development Program",
            "description": "Collaborative breeding program developing superior woody plant cultivars for the nursery and landscape industry with focus on ornamental and ecological value.",
            "creator_idx": 2  # orgadmin user
        }
    ]

    orgs = []
    for org_data in orgs_data:
        org = Organization(
            name=org_data["name"],
            description=org_data["description"],
            created_by=users[org_data["creator_idx"]].id,
            created_at=datetime.utcnow() - timedelta(days=300)
        )
        db.add(org)
        orgs.append(org)

    db.commit()
    print(f"✓ Created {len(orgs)} organizations")
    return orgs


def create_memberships(db, users, orgs):
    """Create organization memberships."""
    print("\nCreating memberships...")

    memberships = []

    # Admin user (users[0]) is admin in Morton Arboretum
    membership = OrganizationMembership(
        user_id=users[0].id,
        organization_id=orgs[0].id,
        role=OrganizationRole.ADMIN,
        joined_at=orgs[0].created_at
    )
    db.add(membership)
    memberships.append(membership)

    # Orgadmin user (users[2]) is admin in New Plant Development Program
    membership = OrganizationMembership(
        user_id=users[2].id,
        organization_id=orgs[1].id,
        role=OrganizationRole.ADMIN,
        joined_at=orgs[1].created_at
    )
    db.add(membership)
    memberships.append(membership)

    # Regular user (users[3]) is a regular user in Morton Arboretum
    membership = OrganizationMembership(
        user_id=users[3].id,
        organization_id=orgs[0].id,
        role=OrganizationRole.USER,
        joined_at=datetime.utcnow() - timedelta(days=200)
    )
    db.add(membership)
    memberships.append(membership)

    # Add cross-organization memberships (collaboration)
    cross_memberships = [
        (0, 1, OrganizationRole.USER),  # admin user in New Plant Development Program
        (2, 0, OrganizationRole.ADMIN),  # orgadmin user is ADMIN in Morton Arboretum
        (4, 0, OrganizationRole.USER),  # emily.brown in Morton Arboretum
        (5, 1, OrganizationRole.USER),  # robert.williams in New Plant Development Program
    ]

    for user_idx, org_idx, role in cross_memberships:
        membership = OrganizationMembership(
            user_id=users[user_idx].id,
            organization_id=orgs[org_idx].id,
            role=role,
            joined_at=datetime.utcnow() - timedelta(days=200)
        )
        db.add(membership)
        memberships.append(membership)

    db.commit()
    print(f"✓ Created {len(memberships)} memberships")
    return memberships


def create_projects(db, orgs, users):
    """Create breeding projects."""
    print("\nCreating projects...")

    projects_by_org = {
        0: [  # Morton Arboretum
            ("Oak Disease Resistance Program", "Breeding disease-resistant oak varieties with focus on oak wilt and anthracnose resistance for restoration and urban forestry."),
            ("Ash Tree Recovery Initiative", "Developing emerald ash borer resistant ash cultivars through selection and breeding of surviving trees."),
            ("Elm Breeding for Urban Resilience", "Creating Dutch elm disease-resistant cultivars adapted to Midwest urban environments."),
            ("Climate-Adapted Conifers", "Evaluating and selecting conifer species and provenances for future climate conditions in the Chicago region."),
            ("Native Plant Restoration Genetics", "Maintaining genetic diversity in native woody plant populations for ecological restoration projects."),
        ],
        1: [  # New Plant Development Program
            ("Ornamental Maple Cultivar Development", "Breeding compact, disease-resistant maple varieties with superior fall color for landscape use."),
            ("Flowering Crabapple Improvement", "Developing disease-resistant crabapples with extended bloom periods and improved fruit characteristics."),
            ("Hardy Hydrangea Selection", "Selecting cold-hardy hydrangea cultivars with enhanced flower production and novel colors."),
            ("Compact Lilac Breeding", "Creating dwarf lilac varieties with improved mildew resistance for small-space gardens."),
            ("Native Shrub Cultivar Development", "Developing superior cultivars of native shrubs for sustainable landscaping and pollinator support."),
        ]
    }

    projects = []
    # Map org index to creator user index
    org_creators = {
        0: 0,  # Morton Arboretum created by admin (users[0])
        1: 2   # New Plant Development Program created by orgadmin (users[2])
    }

    for org_idx, project_list in projects_by_org.items():
        org = orgs[org_idx]
        creator = users[org_creators[org_idx]]

        for i, (title, description) in enumerate(project_list):
            project = Project(
                title=title,
                description=description,
                organization_id=org.id,
                created_by=creator.id,
                status=ProjectStatus.ACTIVE if i < 4 else ProjectStatus.ARCHIVED,
                created_at=datetime.utcnow() - timedelta(days=250 - (i * 30))
            )
            db.add(project)
            projects.append(project)

    db.commit()
    print(f"✓ Created {len(projects)} projects")
    return projects


def create_species(db, orgs, users):
    """Create species entries for woody plants common in Illinois breeding."""
    print("\nCreating species...")

    species_data = [
        # Morton Arboretum species - conservation and restoration focus
        {
            "genus": "Quercus",
            "species_name": "alba",
            "variety": None,
            "common_name": "White Oak",
            "description": "Premier timber species with strong wood and attractive fall color. Highly valued for both ecological and commercial purposes.",
            "org_idx": 0,
            "user_idx": 0
        },
        {
            "genus": "Quercus",
            "species_name": "rubra",
            "variety": None,
            "common_name": "Northern Red Oak",
            "description": "Fast-growing oak species prized for timber production. Adaptable to various soil conditions across Illinois.",
            "org_idx": 0,
            "user_idx": 0
        },
        {
            "genus": "Fraxinus",
            "species_name": "americana",
            "variety": None,
            "common_name": "White Ash",
            "description": "Important timber species threatened by emerald ash borer. Conservation program focuses on resistance breeding.",
            "org_idx": 0,
            "user_idx": 0
        },
        {
            "genus": "Ulmus",
            "species_name": "americana",
            "variety": "Princeton",
            "common_name": "American Elm",
            "description": "Iconic shade tree with vase-shaped form. Selected cultivar shows improved Dutch elm disease resistance.",
            "org_idx": 0,
            "user_idx": 0
        },
        {
            "genus": "Pinus",
            "species_name": "strobus",
            "variety": None,
            "common_name": "Eastern White Pine",
            "description": "Native conifer with soft needles and rapid growth. Important for reforestation and wildlife habitat.",
            "org_idx": 0,
            "user_idx": 0
        },
        {
            "genus": "Carya",
            "species_name": "ovata",
            "variety": None,
            "common_name": "Shagbark Hickory",
            "description": "Native hickory producing edible nuts. Important for wildlife and has excellent fall color.",
            "org_idx": 0,
            "user_idx": 0
        },
        {
            "genus": "Quercus",
            "species_name": "macrocarpa",
            "variety": None,
            "common_name": "Bur Oak",
            "description": "Large, long-lived oak with excellent drought tolerance. Native to Illinois prairies and savannas.",
            "org_idx": 0,
            "user_idx": 0
        },

        # New Plant Development Program species - ornamental focus
        {
            "genus": "Acer",
            "species_name": "rubrum",
            "variety": "October Glory",
            "common_name": "Red Maple",
            "description": "Adaptable maple with brilliant red fall color. Selected for consistent performance in urban landscapes.",
            "org_idx": 1,
            "user_idx": 2
        },
        {
            "genus": "Acer",
            "species_name": "saccharum",
            "variety": "Green Mountain",
            "common_name": "Sugar Maple",
            "description": "Iconic maple species selected for urban tolerance and reliable fall color. Heat and drought tolerant cultivar.",
            "org_idx": 1,
            "user_idx": 2
        },
        {
            "genus": "Malus",
            "species_name": "spp.",
            "variety": "Prairie Fire",
            "common_name": "Flowering Crabapple",
            "description": "Disease-resistant crabapple with deep pink flowers and persistent red fruit. Excellent for four-season interest.",
            "org_idx": 1,
            "user_idx": 2
        },
        {
            "genus": "Hydrangea",
            "species_name": "paniculata",
            "variety": "Limelight",
            "common_name": "Panicle Hydrangea",
            "description": "Hardy shrub with large lime-green flower panicles that age to pink. Excellent for northern gardens.",
            "org_idx": 1,
            "user_idx": 2
        },
        {
            "genus": "Syringa",
            "species_name": "vulgaris",
            "variety": "Bloomerang",
            "common_name": "Common Lilac",
            "description": "Compact reblooming lilac with excellent mildew resistance. Fragrant purple flowers in spring and fall.",
            "org_idx": 1,
            "user_idx": 2
        },
        {
            "genus": "Clethra",
            "species_name": "alnifolia",
            "variety": "Ruby Spice",
            "common_name": "Summersweet",
            "description": "Native shrub with fragrant pink flower spikes. Excellent for pollinators and shade tolerance.",
            "org_idx": 1,
            "user_idx": 2
        },
        {
            "genus": "Cornus",
            "species_name": "sericea",
            "variety": "Cardinal",
            "common_name": "Red Twig Dogwood",
            "description": "Native shrub with brilliant red winter stems. Adaptable to wet sites and provides wildlife habitat.",
            "org_idx": 1,
            "user_idx": 2
        },
        {
            "genus": "Viburnum",
            "species_name": "dentatum",
            "variety": "Chicago Lustre",
            "common_name": "Arrowwood Viburnum",
            "description": "Native shrub with glossy foliage and excellent fall color. Important food source for birds and pollinators.",
            "org_idx": 1,
            "user_idx": 2
        },
    ]

    species = []
    for sp_data in species_data:
        species_entry = Species(
            genus=sp_data["genus"],
            species_name=sp_data["species_name"],
            variety=sp_data["variety"],
            common_name=sp_data["common_name"],
            description=sp_data["description"],
            organization_id=orgs[sp_data["org_idx"]].id,
            created_by=users[sp_data["user_idx"]].id,
            status=SpeciesStatus.ACTIVE,
            created_at=datetime.utcnow() - timedelta(days=280)
        )
        db.add(species_entry)
        species.append(species_entry)

    db.commit()
    print(f"✓ Created {len(species)} species")
    return species


def seed_database():
    """Main seeding function."""
    print("=" * 60)
    print("RedBuds App Database Seeder - Illinois Woody Plant Breeding")
    print("=" * 60)

    # Clear and recreate database
    clear_database()

    db = SessionLocal()

    try:
        # Create data
        users = create_users(db)
        orgs = create_organizations(db, users)
        memberships = create_memberships(db, users, orgs)
        projects = create_projects(db, orgs, users)
        species = create_species(db, orgs, users)

        print("\n" + "=" * 60)
        print("✓ Database seeding completed successfully!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  Users: {len(users)}")
        print(f"  Organizations: {len(orgs)}")
        print(f"  Memberships: {len(memberships)}")
        print(f"  Projects: {len(projects)}")
        print(f"  Species: {len(species)}")
        print(f"\nDefault login credentials:")
        print(f"  Site Admin    -> username: admin    | password: admin")
        print(f"  Site Admin    -> username: s@o.com  | password: susie")
        print(f"  Org Admin     -> username: orgadmin | password: orgadmin")
        print(f"  Regular User  -> username: user     | password: user")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    try:
        seed_database()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)
