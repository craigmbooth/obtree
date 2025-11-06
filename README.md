# OBTree - User Management WebApp

A full-stack web application with comprehensive user management, organization hierarchy, and invite-based registration system.

## Features

- **User Authentication**: JWT-based authentication with secure password hashing
- **Web Interface**: Clean, responsive UI built with vanilla HTML/CSS/JavaScript
- **Site Administration**: Site admins can create and manage organizations
- **Organizations**: Multi-tenant organization structure
- **Invite System**: UUID-based invite codes for organization membership
- **Role-Based Access**: Site admins and organization-level admins/users
- **RESTful API**: Clean API design with automatic OpenAPI documentation
- **Flexible Table System**: Reusable table components with pagination, sorting, and filtering powered by Tabulator

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLAlchemy (SQLite for development, PostgreSQL ready for production)
- **Migrations**: Alembic
- **Package Management**: Poetry
- **Server**: Uvicorn
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: Passlib with bcrypt

### Frontend
- **UI**: Vanilla HTML, CSS, JavaScript
- **Styling**: TailwindCSS (via CDN)
- **API Client**: Fetch API
- **State Management**: LocalStorage for auth tokens

## Project Structure

```
obtree/
├── app/
│   ├── api/
│   │   ├── routes/          # API route handlers
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── organizations.py
│   │   │   ├── invites.py
│   │   │   └── table_config.py  # Table configuration endpoints
│   │   └── deps.py          # Dependency injection (auth, permissions)
│   ├── core/
│   │   ├── security.py      # Password hashing, JWT tokens
│   │   └── permissions.py   # Permission checking utilities
│   ├── models/              # SQLAlchemy models
│   │   ├── mixins.py        # TableConfigMixin for table support
│   ├── schemas/             # Pydantic schemas
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI application
├── frontend/
│   ├── js/
│   │   ├── api.js           # API client
│   │   ├── auth.js          # Authentication utilities
│   │   ├── utils.js         # Helper functions
│   │   ├── table.js         # DataTable class (Tabulator wrapper)
│   │   └── tableBuilder.js  # Table builder utilities
│   ├── login.html           # Login page
│   ├── signup.html          # Signup page
│   ├── dashboard.html       # User dashboard
│   ├── organization.html    # Organization details (with tables)
│   ├── admin.html           # Site admin page
│   └── tables-demo.html     # Table component demo
├── scripts/
│   └── seed_admin.py        # Create site admin users
├── alembic/                 # Database migrations
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment variables
├── Makefile                 # Useful commands
└── pyproject.toml           # Poetry dependencies
```

## Getting Started

### Prerequisites

- Python 3.10+
- Poetry

### Installation

1. Clone the repository and navigate to the project directory

2. Install dependencies:
```bash
make install
```

3. Copy the example environment file and configure it:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Create the database tables:
```bash
make db-create
```

5. Create a site admin user:
```bash
make seed-admin
```

6. Run the development server:
```bash
make run
```

The application will be available at:
- **Web App**: `http://localhost:8000` (redirects to login or dashboard)
- **API Docs**: `http://localhost:8000/docs`
- **API**: `http://localhost:8000/api/`

## Using the Web Interface

### First Time Setup

1. After running the server, visit `http://localhost:8000`
2. You'll be redirected to the login page
3. Since you created a site admin with `make seed-admin`, login with those credentials
4. You'll be taken to the dashboard

### Site Admin Workflow

1. **Login** with your site admin account
2. Click **Admin** in the navigation bar
3. **Create an Organization** using the form
4. Click on the organization to view details
5. **Generate an Invite** by selecting a role (Admin/User) and clicking "Generate Invite"
6. **Copy the invite link** and share it with users
7. Users can signup using the invite link to automatically join the organization

### User Workflow

1. **Receive an invite link** from an organization admin
2. Click the invite link or paste the invite code during signup
3. The signup form will show which organization you're joining
4. **Complete signup** with your email and password
5. **Login** and access your organization dashboard
6. View organization details and members

### Organization Admin Workflow

1. **Login** and navigate to your organization
2. **View all members** and their roles
3. **Create invites** to add new members
4. **Manage invite codes** - copy links to share with new users

## Web Pages

- **`/login.html`** - User login
- **`/signup.html`** - User registration (with optional invite code)
- **`/dashboard.html`** - List of user's organizations
- **`/organization.html`** - Organization details, members, and invite management
- **`/admin.html`** - Site admin panel (create organizations)
- **`/tables-demo.html`** - Interactive demo of the table component system

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication (`/api/auth`)

- `POST /api/auth/signup` - Register a new user (with optional invite code)
- `POST /api/auth/login` - Login and receive JWT token
- `GET /api/auth/me` - Get current user information
- `GET /api/auth/users` - List all users (site admin only)

### Organizations (`/api/organizations`)

- `POST /api/organizations` - Create organization (site admin only)
- `GET /api/organizations` - List user's organizations
- `GET /api/organizations/{id}` - Get organization details with members

### Invites (`/api/invites`)

- `POST /api/invites` - Create invite code (site/org admin)
- `GET /api/invites/organization/{id}` - List organization invites (admins only)
- `GET /api/invites/validate/{uuid}` - Validate an invite code (public)

### Table Configuration (`/api`)

- `GET /api/table-config/{model_name}` - Get table configuration for a model (User, Organization, OrganizationMembership, Invite)

## User Roles

### Site Admin
- Can create organizations
- Can invite users to any organization
- Has all organization admin permissions

### Organization Admin
- Can invite users to their organization
- Can view organization members
- Can manage organization invites

### Organization User
- Can view organization details
- Can view organization members
- Standard member access

## Table Component System

OBTree includes a flexible, reusable table component system built on [Tabulator](http://tabulator.info/) that makes it easy to display database objects with pagination, sorting, and filtering.

### Features

- **Backend-driven configuration**: Table columns and settings are defined in SQLAlchemy models
- **Frontend rendering**: Uses Tabulator.js for rich, interactive tables
- **Modern TailwindCSS styling**: Custom CSS that perfectly matches your site's design
- **Built-in formatters**: datetime, date, boolean, badge, email, link, money, and more
- **Pagination & sorting**: Client-side pagination and column sorting out of the box
- **Search & filtering**: Built-in search and column filtering capabilities
- **Responsive design**: Works seamlessly with TailwindCSS and mobile devices
- **Customizable**: Easy to add custom formatters and action columns

### Quick Start

#### 1. Add Table Configuration to a Model

```python
from app.models.mixins import TableConfigMixin

class MyModel(Base, TableConfigMixin):
    __tablename__ = "my_table"

    # ... your columns ...

    # Table configuration for frontend display
    __table_config__ = {
        'columns': [
            {
                'field': 'id',
                'label': 'ID',
                'visible': False,  # Hidden from table
                'sortable': True,
                'formatter': 'plaintext'
            },
            {
                'field': 'name',
                'label': 'Name',
                'visible': True,
                'sortable': True,
                'width': 200,
                'formatter': 'plaintext'
            },
            {
                'field': 'email',
                'label': 'Email',
                'visible': True,
                'sortable': True,
                'width': 250,
                'formatter': 'email'  # Renders as clickable mailto link
            },
            {
                'field': 'is_active',
                'label': 'Active',
                'visible': True,
                'sortable': True,
                'width': 100,
                'formatter': 'boolean'  # Renders as Yes/No
            },
            {
                'field': 'created_at',
                'label': 'Created',
                'visible': True,
                'sortable': True,
                'width': 180,
                'formatter': 'datetime'  # Formats datetime nicely
            }
        ],
        'default_sort': {'field': 'created_at', 'dir': 'desc'}
    }
```

#### 2. Add Model to API Route Whitelist

Edit `app/api/routes/table_config.py` and add your model to `ALLOWED_MODELS`:

```python
ALLOWED_MODELS = {
    'User': User,
    'Organization': Organization,
    'MyModel': MyModel,  # Add your model here
}
```

#### 3. Use in Frontend

##### Option A: Load from Backend Configuration

```javascript
// Fetches table config from model and data from API
const table = await buildTableFromConfig(
    '#my-table',           // Container selector
    '/api/my-endpoint',    // API endpoint for data
    'MyModel'              // Model name (must match ALLOWED_MODELS)
);
```

##### Option B: Manual Configuration

```javascript
const columns = [
    { field: 'name', label: 'Name', visible: true, sortable: true, formatter: 'plaintext' },
    { field: 'email', label: 'Email', visible: true, sortable: true, formatter: 'email' }
];

const data = [
    { name: 'John Doe', email: 'john@example.com' },
    { name: 'Jane Smith', email: 'jane@example.com' }
];

const table = buildTableManual('#my-table', data, columns);
```

#### 4. Add Tabulator to Your HTML

```html
<!-- In <head> -->
<link href="https://unpkg.com/tabulator-tables@6.2.5/dist/css/tabulator.min.css" rel="stylesheet">
<link href="/css/table-custom.css" rel="stylesheet"> <!-- Custom TailwindCSS styling -->
<script src="https://unpkg.com/tabulator-tables@6.2.5/dist/js/tabulator.min.js"></script>

<!-- Before your scripts -->
<script src="/js/table.js"></script>
<script src="/js/tableBuilder.js"></script>

<!-- In your page -->
<div id="my-table"></div>
```

### Available Formatters

| Formatter | Description | Example Output |
|-----------|-------------|----------------|
| `plaintext` | Plain text display | `Sample text` |
| `datetime` | Formatted date and time | `Jan 15, 2025, 10:30 AM` |
| `date` | Formatted date only | `Jan 15, 2025` |
| `boolean` | Yes/No display | `Yes` or `No` |
| `badge` | Colored badge | `admin` `user` `active` |
| `email` | Clickable mailto link | `user@example.com` |
| `link` | External link | `Link →` |
| `money` | Currency formatting | `$1,234.56` |

### Adding Custom Action Buttons

```javascript
const columns = [
    { field: 'name', label: 'Name', visible: true, sortable: true, formatter: 'plaintext' },
    {
        field: 'actions',
        label: 'Actions',
        visible: true,
        sortable: false,
        width: 180,
        formatter: (cell) => {
            const row = cell.getData();
            return `
                <div class="flex gap-2">
                    <button onclick="editItem(${row.id})" class="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                    <button onclick="deleteItem(${row.id})" class="text-red-600 hover:text-red-800 text-sm">Delete</button>
                </div>
            `;
        }
    }
];
```

### Demo Page

Visit `/tables-demo.html` to see live examples of:
- Simple tables with manual configuration
- Tables using all available formatters
- Tables loaded from backend configurations
- Tables with custom action buttons
- Code examples and best practices

### Files

**Backend:**
- `app/models/mixins.py` - TableConfigMixin for models
- `app/api/routes/table_config.py` - API endpoint for table configs
- `app/models/*.py` - Models with __table_config__ definitions

**Frontend:**
- `frontend/js/table.js` - DataTable class (Tabulator wrapper)
- `frontend/js/tableBuilder.js` - Helper functions for building tables
- `frontend/css/table-custom.css` - Custom TailwindCSS-themed table styling
- `frontend/tables-demo.html` - Interactive demo page

### Best Practices

1. **Only mark necessary fields as visible**: Hidden fields (visible: False) won't clutter the table but are still available in the data
2. **Use appropriate formatters**: Choose the right formatter for your data type for better UX
3. **Set reasonable widths**: Specify column widths to prevent layout issues
4. **Enable sorting where useful**: Make frequently-sorted columns sortable
5. **Whitelist models carefully**: Only add models to ALLOWED_MODELS that should be accessible via the table config API

## Workflow

### 1. Creating an Organization

1. Site admin logs in
2. Creates organization via `POST /api/organizations`
3. Automatically becomes admin of the organization

### 2. Inviting Users

1. Site admin or org admin creates invite via `POST /api/invites`
2. Receives UUID invite code
3. Shares invite code with user (e.g., via email)

### 3. User Registration with Invite

1. New user validates invite code via `GET /api/invites/validate/{uuid}`
2. User signs up with invite code via `POST /api/auth/signup`
3. User automatically becomes member of organization with specified role

## Makefile Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make run           # Run development server
make migrate       # Create new migration (usage: make migrate MSG='message')
make upgrade       # Apply pending migrations
make downgrade     # Rollback last migration
make seed-admin    # Create site admin user
make shell         # Open poetry shell
make db-create     # Create/update database tables
make reset         # Reset database (WARNING: deletes all data)
```

## Configuration

Edit `.env` file to configure:

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Secret key for JWT tokens (use a secure random key in production)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time
- `INVITE_EXPIRATION_DAYS` - Invite code validity period

## Development

### Creating Migrations

After modifying models:
```bash
make migrate MSG="description of changes"
make upgrade
```

### Running Tests

```bash
poetry run pytest
```

## Production Deployment

1. Update `.env` with production settings:
   - Use PostgreSQL instead of SQLite
   - Set strong `SECRET_KEY`
   - Set `DEBUG=False`
   - Configure proper CORS origins in `app/main.py`

2. Run migrations:
```bash
make upgrade
```

3. Use a production ASGI server (Uvicorn with workers or Gunicorn):
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Security Notes

- Never commit `.env` file to version control
- Use strong, random `SECRET_KEY` in production
- Always use HTTPS in production
- Configure CORS properly for production origins
- Regularly rotate invite codes and tokens
- Review and audit site admin permissions

## License

MIT
