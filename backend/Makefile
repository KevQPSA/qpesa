.PHONY: install dev test lint format typecheck security clean db-reset migrations

install:
	@echo "Installing backend dependencies..."
	poetry install

dev: install
	@echo "Starting development server..."
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test: install
	@echo "Running tests..."
	poetry run pytest tests/

lint: install
	@echo "Running linting (ruff)..."
	poetry run ruff check app/ tests/

format: install
	@echo "Running code formatter (black)..."
	poetry run black app/ tests/

typecheck: install
	@echo "Running type checker (mypy)..."
	poetry run mypy app/

security: install
	@echo "Running security scanner (bandit)..."
	poetry run bandit -r app/ -f json -o bandit_report.json

clean:
	@echo "Cleaning up build artifacts and cache..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -f bandit_report.json coverage.xml .coverage

db-reset:
	@echo "Resetting database (development)..."
	docker-compose -f ../docker-compose.dev.yml down --volumes
	docker-compose -f ../docker-compose.dev.yml up --build -d db
	@echo "Waiting for database to be ready..."
	sleep 5 # Give DB time to start
	poetry run alembic upgrade head
	poetry run python scripts/seed_database.py

migrations: install
	@echo "Generating database migration..."
	poetry run alembic revision --autogenerate -m "New migration"

upgrade-db: install
	@echo "Applying database migrations..."
	poetry run alembic upgrade head

# Comprehensive test suite
full-test: install
	@echo "Running full test suite..."
	poetry run python run_tests.py
