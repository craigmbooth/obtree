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
from app.models import (
    User, Organization, OrganizationMembership, Project, Species,
    Accession, Plant, EventType, PlantEvent, EventFieldValue,
    LocationType, LocationTypeField, Location, LocationFieldValue
)
from app.models.membership import OrganizationRole
from app.models.project import ProjectStatus
from app.models.species import SpeciesStatus
from app.models.event_type_field import EventTypeField
from app.models.project_accession_field import FieldType
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


def create_accessions(db, species, users, projects):
    """Create accessions for species and link some to projects."""
    print("\nCreating accessions...")

    accessions = []
    # Create 2-3 accessions per species
    for i, sp in enumerate(species[:5]):  # First 5 species get accessions
        for j in range(2 if i % 2 == 0 else 3):
            accession = Accession(
                accession=f"{sp.genus[:3].upper()}-{sp.species_name[:3].upper()}-{(i*10)+j+1:04d}",
                species_id=sp.id,
                description=f"Sample accession for {sp.common_name} breeding program from Illinois Collection Site {i+1}",
                created_by=sp.created_by,
                created_at=datetime.utcnow() - timedelta(days=180 - (i * 10))
            )
            db.add(accession)
            accessions.append(accession)

    db.flush()  # Flush to get IDs

    # Link accessions to projects
    # Morton Arboretum accessions (first 3 species = 7 accessions) go to various projects
    morton_projects = [p for p in projects if str(p.organization_id) == str(species[0].organization_id)]

    if len(accessions) >= 7 and len(morton_projects) >= 3:
        # Oak Disease Resistance Program - gets Quercus alba and rubra accessions
        accessions[0].projects.append(morton_projects[0])  # QUA-ALB-0001
        accessions[1].projects.append(morton_projects[0])  # QUA-ALB-0002
        accessions[2].projects.append(morton_projects[0])  # QUA-RUB-0011
        accessions[3].projects.append(morton_projects[0])  # QUA-RUB-0012

        # Ash Tree Recovery Initiative - gets Fraxinus americana accessions
        accessions[4].projects.append(morton_projects[1])  # FRA-AME-0021
        accessions[5].projects.append(morton_projects[1])  # FRA-AME-0022
        accessions[6].projects.append(morton_projects[1])  # FRA-AME-0023

        # Elm Breeding for Urban Resilience - gets Ulmus americana accessions (if we get more)
        if len(accessions) >= 9:
            accessions[7].projects.append(morton_projects[2])

    db.commit()
    print(f"✓ Created {len(accessions)} accessions")
    print(f"✓ Linked accessions to projects")
    return accessions


def create_plants(db, accessions, users):
    """Create plants from accessions."""
    print("\nCreating plants...")

    plants = []
    # Create 2-4 plants per accession
    for i, acc in enumerate(accessions):
        num_plants = 2 if i % 3 == 0 else (3 if i % 3 == 1 else 4)
        for j in range(num_plants):
            plant = Plant(
                plant_id=f"{acc.accession}-P{j+1:02d}",
                accession_id=acc.id,
                created_by=acc.created_by,
                created_at=datetime.utcnow() - timedelta(days=150 - (i * 5))
            )
            db.add(plant)
            plants.append(plant)

    db.commit()
    print(f"✓ Created {len(plants)} plants")
    return plants


def create_event_types(db, orgs, projects, users):
    """Create organization and project-level event types."""
    print("\nCreating event types...")

    event_types = []

    # Organization-level event types for Morton Arboretum (orgs[0])
    org_event_types = [
        {
            "event_name": "Height Measurement",
            "description": "Record plant height in centimeters",
            "org_idx": 0,
            "project_id": None,  # NULL = org-level
            "fields": [
                {"field_name": "Height (cm)", "field_type": FieldType.NUMBER, "is_required": True, "min_value": 0.0, "max_value": 10000.0}
            ]
        },
        {
            "event_name": "Disease Observation",
            "description": "Record disease symptoms and severity",
            "org_idx": 0,
            "project_id": None,  # NULL = org-level
            "fields": [
                {"field_name": "Disease Name", "field_type": FieldType.STRING, "is_required": True, "max_length": 200},
                {"field_name": "Severity (1-10)", "field_type": FieldType.NUMBER, "is_required": True, "min_value": 1.0, "max_value": 10.0}
            ]
        },
        {
            "event_name": "Flowering Date",
            "description": "Record when flowering begins",
            "org_idx": 0,
            "project_id": None,  # NULL = org-level
            "fields": [
                {"field_name": "Bloom Stage", "field_type": FieldType.STRING, "is_required": True, "max_length": 100}
            ]
        }
    ]

    # Project-level event types for Oak Disease Resistance Program (projects[0])
    project_event_types = [
        {
            "event_name": "Oak Wilt Assessment",
            "description": "Assess oak wilt resistance",
            "org_idx": 0,
            "project_idx": 0,
            "fields": [
                {"field_name": "Wilt Symptoms", "field_type": FieldType.STRING, "is_required": True, "max_length": 500},
                {"field_name": "Resistance Score", "field_type": FieldType.NUMBER, "is_required": True, "min_value": 0.0, "max_value": 100.0}
            ]
        }
    ]

    # Create org-level event types
    for et_data in org_event_types:
        event_type = EventType(
            event_name=et_data["event_name"],
            description=et_data["description"],
            organization_id=orgs[et_data["org_idx"]].id,
            project_id=et_data["project_id"],
            created_by=users[0].id,
            created_at=datetime.utcnow() - timedelta(days=120)
        )
        db.add(event_type)
        db.flush()  # Get the ID

        # Add fields
        for field_data in et_data["fields"]:
            field = EventTypeField(
                event_type_id=event_type.id,
                field_name=field_data["field_name"],
                field_type=field_data["field_type"],
                is_required=field_data["is_required"],
                min_value=field_data.get("min_value"),
                max_value=field_data.get("max_value"),
                max_length=field_data.get("max_length"),
                created_by=users[0].id
            )
            db.add(field)

        event_types.append(event_type)

    # Create project-level event types
    for et_data in project_event_types:
        event_type = EventType(
            event_name=et_data["event_name"],
            description=et_data["description"],
            organization_id=orgs[et_data["org_idx"]].id,
            project_id=projects[et_data["project_idx"]].id,
            created_by=users[0].id,
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        db.add(event_type)
        db.flush()

        # Add fields
        for field_data in et_data["fields"]:
            field = EventTypeField(
                event_type_id=event_type.id,
                field_name=field_data["field_name"],
                field_type=field_data["field_type"],
                is_required=field_data["is_required"],
                min_value=field_data.get("min_value"),
                max_value=field_data.get("max_value"),
                max_length=field_data.get("max_length"),
                created_by=users[0].id
            )
            db.add(field)

        event_types.append(event_type)

    db.commit()
    print(f"✓ Created {len(event_types)} event types")
    return event_types


def create_plant_events(db, plants, event_types, users):
    """Create plant events."""
    print("\nCreating plant events...")

    events = []
    # Create 2-3 events per plant
    for i, plant in enumerate(plants[:10]):  # First 10 plants get events
        # Use different event types
        for j in range(2 if i % 2 == 0 else 3):
            event_type = event_types[j % len(event_types)]

            event = PlantEvent(
                plant_id=plant.id,
                event_type_id=event_type.id,
                event_date=datetime.utcnow() - timedelta(days=90 - (i * 5) - (j * 2)),
                notes=f"Sample event {j+1} for {plant.plant_id}",
                created_by=plant.created_by,
                created_at=datetime.utcnow() - timedelta(days=90 - (i * 5) - (j * 2))
            )
            db.add(event)
            db.flush()  # Get the ID

            # Add field values
            for field in event_type.fields:
                if field.field_type == FieldType.NUMBER:
                    value = EventFieldValue(
                        event_id=event.id,
                        field_id=field.id,
                        value_number=50.0 + (i * 5.5) + (j * 2.3)  # Sample numeric value
                    )
                else:  # STRING
                    value = EventFieldValue(
                        event_id=event.id,
                        field_id=field.id,
                        value_string=f"Sample observation {i}-{j}"
                    )
                db.add(value)

            events.append(event)

    db.commit()
    print(f"✓ Created {len(events)} plant events")
    return events


def create_location_types(db, orgs, users):
    """Create organization-level location types."""
    print("\nCreating location types...")

    location_types = []

    # Tree Breeding Nursery location type for Morton Arboretum (orgs[0])
    location_type = LocationType(
        location_name="Tree Breeding Nursery",
        description="Location schema for tree breeding nursery with block, row, and coordinate data",
        organization_id=orgs[0].id,
        display_order=0,
        created_by=users[0].id,
        created_at=datetime.utcnow() - timedelta(days=120)
    )
    db.add(location_type)
    db.flush()  # Get the ID

    # Add fields for Tree Breeding Nursery
    fields_data = [
        {"field_name": "Blocks", "field_type": FieldType.STRING, "is_required": True, "max_length": 100, "display_order": 0},
        {"field_name": "Rows", "field_type": FieldType.NUMBER, "is_required": True, "min_value": 1.0, "max_value": 1000.0, "display_order": 1},
        {"field_name": "Row Feet", "field_type": FieldType.NUMBER, "is_required": False, "min_value": 0.0, "max_value": 10000.0, "display_order": 2},
        {"field_name": "Latitude", "field_type": FieldType.NUMBER, "is_required": False, "min_value": -90.0, "max_value": 90.0, "display_order": 3},
        {"field_name": "Longitude", "field_type": FieldType.NUMBER, "is_required": False, "min_value": -180.0, "max_value": 180.0, "display_order": 4},
    ]

    for field_data in fields_data:
        field = LocationTypeField(
            location_type_id=location_type.id,
            field_name=field_data["field_name"],
            field_type=field_data["field_type"],
            is_required=field_data["is_required"],
            display_order=field_data["display_order"],
            min_value=field_data.get("min_value"),
            max_value=field_data.get("max_value"),
            max_length=field_data.get("max_length"),
            created_by=users[0].id
        )
        db.add(field)

    location_types.append(location_type)

    db.commit()
    print(f"✓ Created {len(location_types)} location types")
    return location_types


def create_locations(db, location_types, orgs, users):
    """Create location instances based on location types."""
    print("\nCreating locations...")

    locations = []

    # Create locations for Tree Breeding Nursery location type
    if len(location_types) > 0:
        nursery_type = location_types[0]  # Tree Breeding Nursery

        # Get the fields for this location type
        blocks_field = None
        rows_field = None
        row_feet_field = None
        lat_field = None
        lon_field = None

        for field in nursery_type.fields:
            if field.field_name == "Blocks":
                blocks_field = field
            elif field.field_name == "Rows":
                rows_field = field
            elif field.field_name == "Row Feet":
                row_feet_field = field
            elif field.field_name == "Latitude":
                lat_field = field
            elif field.field_name == "Longitude":
                lon_field = field

        # Create several location instances
        # Base coordinates: 41.813400, -88.054775
        # 400 feet ≈ 0.00109 degrees latitude, 0.00145 degrees longitude (at this latitude)
        locations_data = [
            {
                "name": "North Field Section A",
                "notes": "Primary breeding block for oak varieties",
                "blocks": "Block A",
                "rows": 12,
                "row_feet": 150.5,
                "lat": 41.813500,
                "lon": -88.054900
            },
            {
                "name": "North Field Section B",
                "notes": "Secondary breeding block for ash varieties",
                "blocks": "Block B",
                "rows": 10,
                "row_feet": 125.0,
                "lat": 41.813650,
                "lon": -88.054650
            },
            {
                "name": "South Greenhouse Complex",
                "notes": "Climate-controlled environment for seedling development",
                "blocks": "GH-1",
                "rows": 8,
                "row_feet": 75.0,
                "lat": 41.813200,
                "lon": -88.054850
            },
            {
                "name": "East Propagation Area",
                "notes": "Rooting and grafting station",
                "blocks": "Block C",
                "rows": 6,
                "row_feet": 100.0,
                "lat": 41.813550,
                "lon": -88.054600
            },
        ]

        for loc_data in locations_data:
            location = Location(
                organization_id=orgs[0].id,
                location_type_id=nursery_type.id,
                location_name=loc_data["name"],
                notes=loc_data["notes"],
                created_by=users[0].id,
                created_at=datetime.utcnow() - timedelta(days=100)
            )
            db.add(location)
            db.flush()  # Get the ID

            # Add field values
            if blocks_field:
                field_value = LocationFieldValue(
                    location_id=location.id,
                    field_id=blocks_field.id,
                    value_string=loc_data["blocks"]
                )
                db.add(field_value)

            if rows_field:
                field_value = LocationFieldValue(
                    location_id=location.id,
                    field_id=rows_field.id,
                    value_number=float(loc_data["rows"])
                )
                db.add(field_value)

            if row_feet_field and loc_data.get("row_feet"):
                field_value = LocationFieldValue(
                    location_id=location.id,
                    field_id=row_feet_field.id,
                    value_number=loc_data["row_feet"]
                )
                db.add(field_value)

            if lat_field and loc_data.get("lat"):
                field_value = LocationFieldValue(
                    location_id=location.id,
                    field_id=lat_field.id,
                    value_number=loc_data["lat"]
                )
                db.add(field_value)

            if lon_field and loc_data.get("lon"):
                field_value = LocationFieldValue(
                    location_id=location.id,
                    field_id=lon_field.id,
                    value_number=loc_data["lon"]
                )
                db.add(field_value)

            locations.append(location)

    db.commit()
    print(f"✓ Created {len(locations)} locations")
    return locations


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
        accessions = create_accessions(db, species, users, projects)
        plants = create_plants(db, accessions, users)
        event_types = create_event_types(db, orgs, projects, users)
        plant_events = create_plant_events(db, plants, event_types, users)
        location_types = create_location_types(db, orgs, users)
        locations = create_locations(db, location_types, orgs, users)

        print("\n" + "=" * 60)
        print("✓ Database seeding completed successfully!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  Users: {len(users)}")
        print(f"  Organizations: {len(orgs)}")
        print(f"  Memberships: {len(memberships)}")
        print(f"  Projects: {len(projects)}")
        print(f"  Species: {len(species)}")
        print(f"  Accessions: {len(accessions)}")
        print(f"  Plants: {len(plants)}")
        print(f"  Event Types: {len(event_types)}")
        print(f"  Plant Events: {len(plant_events)}")
        print(f"  Location Types: {len(location_types)}")
        print(f"  Locations: {len(locations)}")
        print(f"\nDefault login credentials:")
        print(f"  Site Admin    -> username: siteadmin@redbudsapp.com | password: siteadmin")
        print(f"  Site Admin    -> username: s@o.com                  | password: susie")
        print(f"  Org Admin     -> username: orgadmin@redbudsapp.com  | password: orgadmin")
        print(f"  Regular User  -> username: user@redbudsapp.com      | password: user")
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
