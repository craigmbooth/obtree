.PHONY: help install run migrate seed-admin shell upgrade downgrade reset db-create

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies via poetry"
	@echo "  make run          - Run the FastAPI server with uvicorn"
	@echo "  make migrate      - Create a new migration (usage: make migrate MSG='message')"
	@echo "  make upgrade      - Run pending migrations"
	@echo "  make downgrade    - Rollback last migration"
	@echo "  make seed-admin   - Create a site admin user"
	@echo "  make shell        - Open a poetry shell"
	@echo "  make db-create    - Create database tables (upgrade to latest migration)"
	@echo "  make reset        - Reset database (WARNING: deletes all data)"

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
	poetry run python scripts/seed_admin.py

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
