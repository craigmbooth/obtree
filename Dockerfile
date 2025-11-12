# Multi-stage build for optimized image size

# Stage 1: Build stage with Poetry
FROM python:3.11-slim as builder

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.8.3

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Export dependencies to requirements.txt (faster than using Poetry in runtime)
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from builder
COPY --from=builder /app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY frontend ./frontend

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run injects PORT environment variable
ENV PORT=8080

# Expose port (documentation only, Cloud Run uses PORT env var)
EXPOSE 8080

# Start script that runs migrations and starts the server
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
