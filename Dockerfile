# Use Python 3.11 slim image
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry (match version with local development)
RUN pip install --no-cache-dir poetry==2.1.4

# Configure Poetry to not create virtual environments (we're in a container)
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry
RUN poetry install --no-directory

# Copy application code
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY frontend ./frontend
COPY scripts ./scripts

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run injects PORT environment variable
ENV PORT=8080

# Expose port (documentation only, Cloud Run uses PORT env var)
EXPOSE 8080

# Start script that runs migrations, optional bootstrap, and starts the server
CMD alembic upgrade head && \
    ([ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ] && python scripts/create_admin.py --bootstrap || true) && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
