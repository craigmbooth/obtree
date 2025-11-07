import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import structlog

from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.api.routes import auth, organizations, invites, table_config, projects, species, accessions, org_accessions

# Configure logging first
configure_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)


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
app.include_router(species.router, prefix="/api/organizations/{organization_id}/species", tags=["species"])
app.include_router(org_accessions.router, prefix="/api/organizations/{organization_id}/accessions", tags=["accessions"])
app.include_router(accessions.router, prefix="/api/organizations/{organization_id}/species/{species_id}/accessions", tags=["accessions"])
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


@app.get("/login.html", response_class=HTMLResponse)
def login_page():
    """Serve login page."""
    return Path("frontend/login.html").read_text()


@app.get("/signup.html", response_class=HTMLResponse)
def signup_page():
    """Serve signup page."""
    return Path("frontend/signup.html").read_text()


@app.get("/organization.html", response_class=HTMLResponse)
def organization_page():
    """Serve organization page."""
    return Path("frontend/organization.html").read_text()


@app.get("/admin.html", response_class=HTMLResponse)
def admin_page():
    """Serve admin page."""
    return Path("frontend/admin.html").read_text()


@app.get("/tables-demo.html", response_class=HTMLResponse)
def tables_demo_page():
    """Serve tables demo page."""
    return Path("frontend/tables-demo.html").read_text()


@app.get("/profile.html", response_class=HTMLResponse)
def profile_page():
    """Serve profile page."""
    return Path("frontend/profile.html").read_text()


@app.get("/org-admin.html", response_class=HTMLResponse)
def org_admin_page():
    """Serve organization admin page."""
    return Path("frontend/org-admin.html").read_text()


@app.get("/project.html", response_class=HTMLResponse)
def project_page():
    """Serve project page."""
    return Path("frontend/project.html").read_text()


@app.get("/species.html", response_class=HTMLResponse)
def species_page():
    """Serve species page."""
    return Path("frontend/species.html").read_text()


@app.get("/accession.html", response_class=HTMLResponse)
def accession_page():
    """Serve accession page."""
    return Path("frontend/accession.html").read_text()
