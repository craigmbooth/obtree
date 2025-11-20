.PHONY: help install run migrate seed-admin create-admin create-admin-env seed shell upgrade downgrade reset db-create
.PHONY: docker-up docker-down docker-restart docker-logs docker-logs-app docker-logs-db
.PHONY: docker-build docker-shell docker-db-shell docker-migrate docker-seed-admin docker-reset docker-clean

help:
	@echo "=== Local Development (Poetry) ==="
	@echo "  make install      - Install dependencies via poetry"
	@echo "  make run          - Run the FastAPI server with uvicorn"
	@echo "  make migrate      - Create a new migration (usage: make migrate MSG='message')"
	@echo "  make upgrade      - Run pending migrations"
	@echo "  make downgrade    - Rollback last migration"
	@echo "  make seed-admin      - Create a site admin user (legacy)"
	@echo "  make create-admin    - Create a site admin user (interactive, recommended)"
	@echo "  make create-admin-env - Create admin from ADMIN_EMAIL and ADMIN_PASSWORD env vars"
	@echo "  make seed            - Seed database with sample data (WARNING: clears existing data)"
	@echo "  make shell        - Open a poetry shell"
	@echo "  make db-create    - Create database tables (upgrade to latest migration)"
	@echo "  make reset        - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "=== Docker Compose ==="
	@echo "  make docker-up         - Start all Docker services"
	@echo "  make docker-down       - Stop all Docker services"
	@echo "  make docker-restart    - Restart all Docker services"
	@echo "  make docker-logs       - Show logs from all services"
	@echo "  make docker-logs-app   - Show app logs only"
	@echo "  make docker-logs-db    - Show database logs only"
	@echo "  make docker-build      - Rebuild app container"
	@echo "  make docker-shell      - Open shell in app container"
	@echo "  make docker-db-shell   - Open PostgreSQL shell"
	@echo "  make docker-migrate    - Run migrations in container"
	@echo "  make docker-seed-admin - Create admin user in container"
	@echo "  make docker-reset      - Reset Docker database (WARNING: deletes all data)"
	@echo "  make docker-clean      - Remove all containers and volumes"

install:
	poetry install

run:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a message. Usage: make migrate MSG='your message'"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(MSG)"

upgrade:
	poetry run alembic upgrade head

downgrade:
	poetry run alembic downgrade -1

seed-admin:
	@echo "⚠️  This command is deprecated. Use 'make create-admin' instead."
	poetry run python scripts/seed_admin.py

create-admin:
	poetry run python scripts/create_admin.py

create-admin-env:
	@if [ -z "$$ADMIN_EMAIL" ] || [ -z "$$ADMIN_PASSWORD" ]; then \
		echo "Error: ADMIN_EMAIL and ADMIN_PASSWORD environment variables must be set"; \
		echo "Usage: ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=password make create-admin-env"; \
		exit 1; \
	fi
	poetry run python scripts/create_admin.py --from-env

seed:
	poetry run python scripts/seed.py

shell:
	poetry shell

db-create: upgrade
	@echo "Database tables created successfully"

reset:
	@echo "WARNING: This will delete all data in the database!"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		rm -f obtree.db; \
		poetry run alembic upgrade head; \
		echo "Database reset complete"; \
	else \
		echo "Reset cancelled"; \
	fi

# ============================================
# Docker Compose Commands
# ============================================

docker-up:
	@if [ ! -f .env ]; then \
		echo "No .env file found. Copying .env.docker to .env"; \
		cp .env.docker .env; \
	fi
	@echo "Starting Docker services..."
	docker compose up -d
	@echo ""
	@echo "Services started!"
	@echo "App: http://localhost:8000"
	@echo "Database: localhost:5432"

docker-down:
	@echo "Stopping Docker services..."
	docker compose down

docker-restart:
	@echo "Restarting Docker services..."
	docker compose restart

docker-logs:
	docker compose logs -f

docker-logs-app:
	docker compose logs -f app

docker-logs-db:
	docker compose logs -f postgres

docker-build:
	@echo "Rebuilding app container..."
	docker compose build --no-cache app

docker-shell:
	docker compose exec app /bin/bash

docker-db-shell:
	docker compose exec postgres psql -U obtree_user -d obtree

docker-migrate:
	@echo "Running database migrations..."
	docker compose exec app alembic upgrade head

docker-seed-admin:
	@echo "Creating admin user..."
	docker compose exec app python -c "\
from app.database import SessionLocal; \
from app.models import User; \
from passlib.context import CryptContext; \
import uuid; \
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); \
db = SessionLocal(); \
existing = db.query(User).filter(User.email == 'admin@example.com').first(); \
if existing: \
    print('Admin user already exists'); \
else: \
    admin = User( \
        id=uuid.uuid4(), \
        email='admin@example.com', \
        hashed_password=pwd_context.hash('admin123'), \
        full_name='Site Administrator', \
        is_site_admin=True \
    ); \
    db.add(admin); \
    db.commit(); \
    print('Admin user created: admin@example.com / admin123'); \
db.close();"

docker-reset:
	@echo "WARNING: This will delete all Docker data!"
	@read -p "Are you sure? (type 'yes' to confirm): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down; \
		docker volume rm obtree_postgres_data 2>/dev/null || true; \
		echo "Database reset. Run 'make docker-up' to start fresh"; \
	else \
		echo "Reset cancelled"; \
	fi

docker-clean:
	@echo "WARNING: This will remove all containers, networks, and volumes!"
	@read -p "Are you sure? (type 'yes' to confirm): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v --remove-orphans; \
		echo "Cleanup complete"; \
	else \
		echo "Cleanup cancelled"; \
	fi
