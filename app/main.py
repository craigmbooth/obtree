import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, Response
from pathlib import Path
import structlog
from starlette.types import Scope, Receive, Send

from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.api.routes import (
    auth,
    organizations,
    invites,
    table_config,
    projects,
    species,
    accessions,
    org_accessions,
    project_fields,
    project_plant_fields,
    plants,
    org_plants,
    organization_event_types,
    project_event_types,
    plant_events,
    organization_location_types,
    locations,
)

# Configure logging first
configure_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)


# Middleware to handle X-Forwarded-Proto from Cloud Run proxy
@app.middleware("http")
async def proxy_headers_middleware(request: Request, call_next):
    """Handle X-Forwarded-Proto header from reverse proxy to ensure redirects use HTTPS."""
    # If behind a proxy that sets X-Forwarded-Proto, use that for scheme
    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    if forwarded_proto:
        # Override the request scope to use the forwarded protocol
        request.scope["scheme"] = forwarded_proto

    response = await call_next(request)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = time.time()

    # Log request
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None,
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )

    return response


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers - these must be registered before static files
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["organizations"])
app.include_router(invites.router, prefix="/api/invites", tags=["invites"])
app.include_router(projects.router, prefix="/api/organizations/{organization_id}/projects", tags=["projects"])
app.include_router(project_fields.router, prefix="/api/organizations/{organization_id}/projects/{project_id}/fields", tags=["fields"])
app.include_router(project_plant_fields.router, prefix="/api/organizations/{organization_id}/projects/{project_id}/plant_fields", tags=["plant_fields"])
app.include_router(species.router, prefix="/api/organizations/{organization_id}/species", tags=["species"])
app.include_router(org_accessions.router, prefix="/api/organizations/{organization_id}/accessions", tags=["accessions"])
app.include_router(accessions.router, prefix="/api/organizations/{organization_id}/species/{species_id}/accessions", tags=["accessions"])
app.include_router(org_plants.router, prefix="/api/organizations/{organization_id}/plants", tags=["plants"])
app.include_router(plants.router, prefix="/api/organizations/{organization_id}/species/{species_id}/accessions/{accession_id}/plants", tags=["plants"])
app.include_router(organization_event_types.router, prefix="/api/organizations/{organization_id}/event-types", tags=["event-types"])
app.include_router(project_event_types.router, prefix="/api/organizations/{organization_id}/projects/{project_id}/event-types", tags=["event-types"])
app.include_router(plant_events.router, prefix="/api/organizations/{organization_id}/species/{species_id}/accessions/{accession_id}/plants/{plant_id}/events", tags=["events"])
app.include_router(organization_location_types.router, prefix="/api/organizations/{organization_id}/location-types", tags=["location-types"])
app.include_router(locations.router, prefix="/api/organizations/{organization_id}/locations", tags=["locations"])
app.include_router(table_config.router, prefix="/api", tags=["tables"])


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(
        "application_started",
        app_name=settings.APP_NAME,
        debug=settings.DEBUG,
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("application_shutdown")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Mount static assets (js, css, images, etc.) at /static
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")


# Serve HTML pages directly as routes
@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the main index.html file."""
    return Path("frontend/index.html").read_text()


@app.get("/login", response_class=HTMLResponse)
def login_page():
    """Serve login page."""
    return Path("frontend/login.html").read_text()


@app.get("/signup", response_class=HTMLResponse)
@app.get("/signup/{invite_code}", response_class=HTMLResponse)
def signup_page(invite_code: str = None):
    """Serve signup page (with optional invite code in URL)."""
    return Path("frontend/signup.html").read_text()


@app.get("/profile", response_class=HTMLResponse)
def profile_page():
    """Serve profile page."""
    return Path("frontend/profile.html").read_text()


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    """Serve site admin dashboard."""
    return Path("frontend/admin.html").read_text()


@app.get("/organizations/{organization_id}", response_class=HTMLResponse)
def organization_page(organization_id: str):
    """Serve organization dashboard page."""
    return Path("frontend/organization.html").read_text()


@app.get("/organizations/{organization_id}/admin", response_class=HTMLResponse)
def org_admin_page(organization_id: str):
    """Serve organization admin page."""
    return Path("frontend/org-admin.html").read_text()


@app.get("/organizations/{organization_id}/projects", response_class=HTMLResponse)
def projects_list_page(organization_id: str):
    """Serve projects list page."""
    return Path("frontend/projects.html").read_text()


@app.get("/organizations/{organization_id}/species", response_class=HTMLResponse)
def species_list_page(organization_id: str):
    """Serve species list page."""
    return Path("frontend/species-list.html").read_text()


@app.get("/organizations/{organization_id}/accessions", response_class=HTMLResponse)
def accessions_list_page(organization_id: str):
    """Serve accessions list page."""
    return Path("frontend/accessions-list.html").read_text()


@app.get("/organizations/{organization_id}/projects/{project_id}", response_class=HTMLResponse)
def project_page(organization_id: str, project_id: str):
    """Serve project details page."""
    return Path("frontend/project.html").read_text()


@app.get("/organizations/{organization_id}/species/{species_id}", response_class=HTMLResponse)
def species_page(organization_id: str, species_id: str):
    """Serve species details page."""
    return Path("frontend/species.html").read_text()


@app.get("/organizations/{organization_id}/accessions/{accession_id}", response_class=HTMLResponse)
def accession_page(organization_id: str, accession_id: str):
    """Serve accession details page."""
    return Path("frontend/accession.html").read_text()


@app.get("/organizations/{organization_id}/plants/{plant_id}", response_class=HTMLResponse)
def plant_page(organization_id: str, plant_id: str):
    """Serve plant details page."""
    return Path("frontend/plant.html").read_text()


@app.get("/tables-demo.html", response_class=HTMLResponse)
def tables_demo_page():
    """Serve tables demo page."""
    return Path("frontend/tables-demo.html").read_text()
