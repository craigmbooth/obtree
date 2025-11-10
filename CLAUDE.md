# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RedBuds App is a full-stack botanical specimen management system with multi-tenant organizations, hierarchical data (Organization → Project/Species → Accession → Plant), custom fields, and invite-based user management.

**Tech Stack**: FastAPI + SQLAlchemy (backend), Vanilla JS + TailwindCSS (frontend), SQLite (dev) / PostgreSQL (prod)

## Development Commands

```bash
# Setup
make install       # Install dependencies via Poetry
make db-create     # Create database (runs Alembic migrations)
make seed-admin    # Create initial site admin user

# Running
make run           # Start Uvicorn dev server (auto-reload on :8000)

# Database migrations
make migrate MSG="description"  # Create new migration
make upgrade                     # Apply pending migrations
make downgrade                   # Rollback last migration

# Database reset (WARNING: deletes all data)
make reset         # Requires confirmation
```

**Access Points**:
- Web App: http://localhost:8000
- API Docs: http://localhost:8000/docs
- API: http://localhost:8000/api/

## Git Workflow

**CRITICAL RULES:**
1. **Never commit without explicit user permission** - Do NOT run `git commit` unless the user explicitly says "commit"
2. **Never push without explicit user permission** - Do NOT run `git push` unless the user explicitly says "push"

**Workflow**:
1. Make code changes as requested
2. Wait for user to say "commit" before creating commits
3. When user says commit: stage files with `git add` and create commit with descriptive message
4. Wait for user to say "push" before pushing to remote
5. When user says push: run `git push` to publish commits

**Never assume the user wants to commit or push.** Always wait for explicit instruction.

## Architecture Patterns

### 1. Multi-Tenant Organization Pattern

Resources are scoped to organizations with three-tier RBAC:

- **Site Admin** - Global privileges, can create orgs, bypass org membership
- **Organization Admin** - Can manage org resources, invite users, see archived items
- **Organization User** - Can view active resources only

**Permission Check Pattern**:
```python
# In route handlers, always check permissions first
if not is_org_member(db, current_user, organization_id):
    raise HTTPException(403, "Not a member")

if not can_manage_organization(db, current_user, organization_id):
    raise HTTPException(403, "Admin access required")
```

Permission utilities in `app/core/permissions.py`:
- `is_site_admin()` - Global admin
- `is_org_admin()` - Organization admin role
- `is_org_member()` - Organization membership (includes site admins)
- `can_manage_organization()` - Site admin OR org admin

### 2. Nested Resource Hierarchy

API routes follow resource nesting:
```
/api/organizations/{org_id}
  /projects/{proj_id}
    /fields/{field_id}
  /species/{species_id}
    /accessions/{acc_id}
      /plants/{plant_id}
```

**Route handler pattern**:
1. Inject dependencies (`current_user: User = Depends(get_current_user)`, `db: Session = Depends(get_db)`)
2. Check permissions at start
3. Verify parent resources exist and belong to correct org
4. Perform operation
5. Log events with structlog
6. Return Pydantic response schema

### 3. Soft Delete Strategies

Three approaches used depending on context:

**Status Enum** (Project, Species):
```python
status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
# ACTIVE → ARCHIVED → DELETED
# Admins see archived, users see active only
```

**Timestamp** (OrganizationMembership):
```python
removed_at = Column(DateTime, nullable=True)
# Keeps membership history
```

**Boolean + Timestamp** (ProjectAccessionField):
```python
is_deleted = Column(Boolean, default=False)
deleted_at = Column(DateTime, nullable=True)
# Query filters exclude deleted by default
```

### 4. Custom Fields System (EAV Pattern)

Entity-Attribute-Value pattern for flexible project-specific fields on accessions:

- **Entity**: Accession
- **Attribute**: ProjectAccessionField (defines field: name, type, validation rules)
- **Value**: AccessionFieldValue (stores data: value_string or value_number)

**Key features**:
- Project-scoped field definitions
- Type-safe validation (STRING with regex/length, NUMBER with min/max)
- Required field enforcement (`validate_required_fields`)
- Field locking - can't change type if values exist (`is_field_locked`)
- Soft delete with history
- Validation logic in `app/core/field_validation.py`

**Creating custom field**:
```python
field = ProjectAccessionField(
    project_id=project_id,
    field_name="Harvest Date",
    field_type=FieldType.STRING,
    is_required=True,
    max_length=100,
    created_by=user_id
)
```

### 5. Backend-Driven Table Configuration

Tables use a "single source of truth" pattern:

1. Models define `__table_config__` via `TableConfigMixin`:
```python
class MyModel(Base, TableConfigMixin):
    __table_config__ = {
        'columns': [
            {
                'field': 'created_at',
                'label': 'Created',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'
            }
        ],
        'default_sort': {'field': 'created_at', 'dir': 'desc'}
    }
```

2. Frontend fetches config: `GET /api/table-config/{model_name}`
3. `DataTable` class converts to Tabulator format
4. Consistent tables everywhere

**Whitelist pattern**: Only models in `ALLOWED_MODELS` dict (in `app/api/routes/table_config.py`) can be accessed via table config API.

**Available formatters**: plaintext, datetime, date, boolean, badge, email, link, money

### 6. Invite-Based Registration

UUID-based, time-limited, single-use invites:

**Flow**:
1. Admin creates invite → generates UUID, sets role and expiration
2. User validates: `GET /api/invites/validate/{uuid}` (public)
3. User signs up with invite code in request body
4. OrganizationMembership auto-created with specified role
5. Invite marked as used (`used_by`, `used_at`)

**Important**: Invites expire after `INVITE_EXPIRATION_DAYS` (configurable in `.env`)

### 7. Dependency Injection Pattern

FastAPI dependencies for cross-cutting concerns:

```python
# Database session (per-request)
db: Session = Depends(get_db)

# Authentication
current_user: User = Depends(get_current_user)

# Authorization (composes get_current_user)
current_user: User = Depends(get_current_site_admin)
```

All in `app/api/deps.py`. Use dependency composition for cleaner code.

### 8. Structured Logging

Use structlog for event-based logging (not print statements):

```python
from app.logging_config import get_logger
logger = get_logger(__name__)

# Event-based logging with context
logger.info(
    "accession_create_started",
    organization_id=org_id,
    species_id=species_id,
    created_by=user_id
)

# Log all key events: start, success, failure, warnings
logger.warning("accession_create_forbidden", user_id=user_id)
logger.info("accession_create_success", accession_id=acc_id)
```

**Never use print()** - always use logger.

### 9. Frontend State Management

**No framework** - Vanilla JS with utility classes:

- `ApiClient` (singleton: `api`) - All API calls, auto JWT injection
- `Auth` (static class) - LocalStorage auth state management
- `DataTable` - Tabulator wrapper with formatters
- `TableBuilder` - Helper functions for building tables

**State**: LocalStorage only (`token`, `user` JSON). No global state - pages fetch fresh data on load.

**Page pattern**:
1. Auth check: `Auth.checkAuth()` on load
2. Fetch data via `api.getSomething()`
3. Render with vanilla DOM manipulation or innerHTML
4. Event handlers for forms/buttons
5. Navigate via standard browser navigation

**Date formatting**: Backend sends UTC datetime strings. Frontend adds 'Z' suffix if missing and converts to user's local timezone. Use `formatDate()` from `utils.js` for consistency.

## Model Design Patterns

### UUID Primary Keys

All models use UUID via custom `GUID` type (`app/models/types.py`):
- Portable between SQLite/PostgreSQL
- No sequential integer exposure
- Safe for distributed systems

```python
from app.models.types import GUID
id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
```

### Standard Timestamps

```python
from datetime import datetime
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Important**: Use `datetime.utcnow` (naive UTC), not timezone-aware. Pydantic serializes to ISO 8601, frontend adds 'Z' suffix.

### Creator Tracking

```python
created_by = Column(GUID, ForeignKey("users.id"), nullable=False)
creator = relationship("User")
```

### Cascade Deletes

For child resources that should be deleted with parent:
```python
plants = relationship("Plant", back_populates="accession", cascade="all, delete-orphan")
```

## Adding New Features

### Adding a New Model

1. Create model in `app/models/` inheriting from `Base`
2. Add to `app/models/__init__.py` exports
3. Create Pydantic schemas in `app/schemas/` (Create, Update, Response)
4. Add to `app/schemas/__init__.py` exports
5. Create migration: `make migrate MSG="add model_name"`
6. Run migration: `make upgrade`
7. Add API routes in `app/api/routes/`
8. Register router in `app/main.py`
9. Add permission checks to route handlers
10. Add structured logging for key events
11. (Optional) Add `__table_config__` if needs table display

### Adding Table Support to a Model

1. Inherit from `TableConfigMixin`:
```python
from app.models.mixins import TableConfigMixin
class MyModel(Base, TableConfigMixin):
    __table_config__ = { ... }
```

2. Add to whitelist in `app/api/routes/table_config.py`:
```python
ALLOWED_MODELS = {
    'MyModel': MyModel,
}
```

3. Frontend usage:
```javascript
const table = await buildTableFromConfig(
    '#my-table',
    '/api/my-endpoint',
    'MyModel'
);
```

### Adding Custom Validation

Add validation functions to `app/core/field_validation.py` or create new utility modules in `app/core/`. Keep business logic separate from routes.

### Adding Frontend Pages

1. Create HTML file in `frontend/`
2. Register route in `app/main.py`:
```python
@app.get("/mypage.html", response_class=HTMLResponse)
def my_page():
    return Path("frontend/mypage.html").read_text()
```

3. Use existing utilities (`api.js`, `auth.js`, `utils.js`)
4. Add auth check: `await Auth.checkAuth()`
5. Fetch data via `api` singleton
6. Use `formatDate()` for all timestamps

## Code Quality Guidelines

- **Docstrings**: Use Google-style docstrings for all public APIs (classes, functions, modules)
- **Permissions**: Always check permissions at start of route handlers
- **Logging**: Use structlog for all events (never print())
- **Validation**: Use Pydantic schemas for request/response validation
- **Error Handling**: Return appropriate HTTPException with clear messages
- **Database Sessions**: Always use `db: Session = Depends(get_db)`, never create sessions manually
- **Transactions**: Rely on FastAPI's session management; explicit commits only when needed
- **Type Hints**: Add type hints to all function signatures

## Common Patterns

### Creating a Route Handler

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.permissions import can_manage_organization
from app.logging_config import get_logger
from app.models import User, MyModel
from app.schemas.mymodel import MyModelCreate, MyModelResponse

logger = get_logger(__name__)
router = APIRouter()

@router.post("", response_model=MyModelResponse, status_code=status.HTTP_201_CREATED)
def create_my_model(
    organization_id: UUID,
    data: MyModelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new MyModel (admin only).

    Args:
        organization_id: Organization UUID.
        data: MyModel creation data.
        current_user: Authenticated user.
        db: Database session.

    Returns:
        MyModelResponse: Created model.

    Raises:
        HTTPException: If user lacks permissions.
    """
    logger.info("mymodel_create_started", organization_id=organization_id, user_id=current_user.id)

    # Permission check
    if not can_manage_organization(db, current_user, organization_id):
        logger.warning("mymodel_create_forbidden", user_id=current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    # Create model
    new_model = MyModel(**data.model_dump(), created_by=current_user.id)
    db.add(new_model)
    db.commit()
    db.refresh(new_model)

    logger.info("mymodel_create_success", model_id=new_model.id)
    return new_model
```

### Querying with Permissions

```python
# Always verify org membership
org = db.query(Organization).filter(Organization.id == org_id).first()
if not org:
    raise HTTPException(404, "Organization not found")

if not is_org_member(db, current_user, org_id):
    raise HTTPException(403, "Not a member")

# Filter by org and active status (if applicable)
items = db.query(MyModel).filter(
    MyModel.organization_id == org_id,
    MyModel.status == MyModelStatus.ACTIVE
).all()
```

## Testing

**Status**: No test suite currently implemented. When adding tests:
- Use pytest
- Create `tests/` directory
- Test all permission checks thoroughly
- Test validation rules
- Mock database with fixtures
- Test API endpoints via TestClient

## Security Considerations

- **Passwords**: Never log or return passwords; use bcrypt via passlib
- **JWT Tokens**: Expire after `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Permissions**: Always verify org membership before operations
- **SQL Injection**: Use SQLAlchemy ORM (never raw SQL)
- **XSS**: Frontend uses textContent/innerText where appropriate
- **CORS**: Currently allows all origins (change for production in `app/main.py`)
- **Secrets**: Never commit `.env` file; use strong `SECRET_KEY` in production

## Production Deployment

1. Switch to PostgreSQL: `DATABASE_URL=postgresql://user:pass@host:5432/db`
2. Generate strong secret: `openssl rand -hex 32`
3. Set `DEBUG=False` in `.env`
4. Configure CORS for specific origins in `app/main.py`
5. Run migrations: `make upgrade`
6. Use production server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`
7. Enable HTTPS via reverse proxy (nginx/traefik)

## Troubleshooting

**"Module not found" errors**: Run `make install` to ensure dependencies are installed

**Migration conflicts**: Check `alembic/versions/` for conflicting revisions; may need to merge branches

**Permission denied**: Check user's `is_site_admin` flag or organization membership/role

**Frontend 401/403 errors**: Check browser LocalStorage for valid token; may need to re-login

**Database locked (SQLite)**: Only one write at a time; use PostgreSQL for production

**Timestamps showing UTC**: Frontend should add 'Z' suffix and convert to local; check `formatDate()` usage
